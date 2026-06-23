#!/usr/bin/env python3
"""
speed_ev_audit.py — Polished Crystal BT Speed EV optimizer

Flow per mon:
  actual stat @ Lv_N  →  solve C  →  Lv50 stat projection
  →  current Speed EV  →  min EV to beat SpeTarget50  →  freed EVs → HP

Usage:
  python speed_ev_audit.py                           # all rows with SpeTarget50 filled
  python speed_ev_audit.py --rows 5-13               # specific CSV rows (1-indexed, row 1 = header)
  python speed_ev_audit.py --targetSpeed 170         # override all SpeTarget50 values
  python speed_ev_audit.py --rows 5-13 --targetSpeed 195
  python speed_ev_audit.py --output bt-reports/custom.md

SpeTarget50 column in CSV: the raw Lv50 Speed of the BT opponent you want to outspeed
(pick from bt-reports/bt-speed-tiers.md). Leave blank and use --targetSpeed to test
a single threshold across all mons at once.
"""

import argparse
import csv
import math
import re
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent
USE_FAITHFUL = False

# ── Nature speed modifier ─────────────────────────────────────────────────────
SPE_UP   = {"Timid", "Jolly", "Hasty", "Naive"}
SPE_DOWN = {"Brave", "Quiet", "Relaxed", "Sassy"}

def spe_mod(nature: str) -> float:
    if nature in SPE_UP:   return 1.1
    if nature in SPE_DOWN: return 0.9
    return 1.0

# ── Setup moves → post-boost multiplier ──────────────────────────────────────
SETUP_BOOST: dict[str, float] = {
    "Dragon Dance": 1.5,
    "Agility":      2.0,
    "Rock Polish":  2.0,
    "Shell Smash":  2.0,
    "Quiver Dance": 1.5,
}

# ── Items that multiply Speed ─────────────────────────────────────────────────
SPEED_ITEMS: dict[str, float] = {
    "Choice Scarf": 1.5,
}

WEATHER_SPEED_ABILITIES: dict[str, tuple[str, float]] = {
    "Swift Swim":  ("Rain", 2.0),
    "Chlorophyll": ("Sun", 2.0),
    "Sand Rush":   ("Sand", 2.0),
    "Slush Rush":  ("Hail", 2.0),
}

TEAMFLAG_WEATHER_PREFIXES: dict[str, str] = {
    "TRain": "Rain",
    "TSun":  "Sun",
    "TSand": "Sand",
    "THail": "Hail",
}

WEATHER_LABELS: dict[str, str] = {
    "Rain": "rain",
    "Sun":  "sun",
    "Sand": "sand",
    "Hail": "hail",
}

BT_SPEED_TIERS = REPO / "bt-reports" / "bt-speed-tiers.md"
MOVES_ASM = REPO / "data" / "moves" / "moves.asm"
TYPE_CHART_ASM = REPO / "data" / "types" / "type_matchups.asm"

MOVE_LINE_RE = re.compile(
    r'^\s*move\s+([A-Z0-9_]+)\s*,\s*[^,]+,\s*(-?\d+)\s*,\s*([A-Z_]+)\s*,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*([A-Z_]+)'
)
TYPE_LINE_RE = re.compile(r'^\s*db\s+([A-Z_]+)\s*,\s*([A-Z_]+)\s*;\s*type', re.MULTILINE)
TYPE_MATCHUP_RE = re.compile(r'^\s*db\s+([A-Z_]+)\s*,\s*([A-Z_]+)\s*,\s*([A-Z_]+)')

MOVE_NAME_OVERRIDES = {
    "DazzlingGleam": "DAZZLINGLEAM",
    "HealingLight": "HEALINGLIGHT",
    "Acqua Jet": "AQUA_JET",
    "Hidden Power(Ice)": "HIDDEN_POWER",
    "Hidden Power(Fairy)": "HIDDEN_POWER",
    "Hidden Power(?)": "HIDDEN_POWER",
}

TYPE_MULTIPLIER = {
    "NO_EFFECT": 0.0,
    "NOT_VERY_EFFECTIVE": 0.5,
    "SUPER_EFFECTIVE": 2.0,
}

CHARGE_MOVES = {"Solar Beam"}

COUNTER_SCORE_MIN = 15000
THREAT_SCORE_MIN = 15000

# ─────────────────────────────────────────────────────────────────────────────
# Base-stat loader  (reads data/pokemon/base_stats/*.asm once at startup)
# ─────────────────────────────────────────────────────────────────────────────
_BST_RE = re.compile(
    r'\bbst\s+\d+\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)'
)

def preprocess_asm(text: str, use_faithful: bool = USE_FAITHFUL) -> list[str]:
    lines = text.splitlines()
    out: list[str] = []
    stack: list[dict[str, bool]] = []

    def is_active() -> bool:
        return all(frame["active"] for frame in stack)

    for raw in lines:
        stripped = raw.strip()
        if stripped.startswith("if DEF(FAITHFUL)"):
            stack.append({"active": use_faithful, "truth": use_faithful})
            continue
        if stripped.startswith("if !DEF(FAITHFUL)"):
            stack.append({"active": not use_faithful, "truth": not use_faithful})
            continue
        if stripped == "else":
            frame = stack[-1]
            frame["active"] = not frame["truth"]
            continue
        if stripped == "endc":
            stack.pop()
            continue
        if is_active():
            out.append(raw)

    return out


def load_base_stats() -> dict[str, dict[str, int | bool | tuple[str, str]]]:
    """Parse data/pokemon/base_stats/*.asm → {stem: species speed metadata}."""
    base_dir = REPO / "data" / "pokemon" / "base_stats"
    result: dict[str, dict[str, int | bool | tuple[str, str]]] = {}
    for f in base_dir.glob("*.asm"):
        text = "\n".join(preprocess_asm(f.read_text(errors="ignore")))
        m = _BST_RE.search(text)
        if m:
            type_match = TYPE_LINE_RE.search(text)
            result[f.stem] = {
                "base_hp": int(m.group(1)),
                "base_atk": int(m.group(2)),
                "base_spa": int(m.group(4)),
                "base_spe": int(m.group(6)),
                "can_agility": bool(re.search(r"\bAGILITY\b", text)),
                "types": (type_match.group(1), type_match.group(2)) if type_match else ("NORMAL", "NORMAL"),
            }
    return result


def species_stem(name: str) -> str:
    """'Charizard(Shiny)' → 'charizard',  'Porygon-Z' → 'porygon_z'."""
    name = re.sub(r'\(.*?\)', '', name).strip()      # drop parenthetical
    return name.lower().replace('-', '_').replace(' ', '_').replace('.', '')


def display_name_candidates(name: str) -> list[str]:
    raw = name.strip()
    suffixes = [
        ("-P-Fire", "_paldean_fire"),
        ("-P-Water", "_paldean_water"),
        ("-A", "_alolan"),
        ("-G", "_galarian"),
        ("-H", "_hisuian"),
        ("-P", "_paldean"),
    ]

    if raw.endswith(" (Red)") or raw.endswith(" (Koga)"):
        raw = raw.rsplit(" (", 1)[0]

    for suffix, form_suffix in suffixes:
        if raw.endswith(suffix):
            base = raw[:-len(suffix)]
            stem = species_stem(base)
            return [stem + form_suffix, stem + "_plain", stem]

    stem = species_stem(raw)
    return [stem, stem + "_plain"]


def move_const(name: str) -> str:
    cleaned = MOVE_NAME_OVERRIDES.get(name, name)
    cleaned = re.sub(r'\(.*?\)', '', cleaned).strip()
    cleaned = re.sub(r'([a-z])([A-Z])', r'\1_\2', cleaned)
    cleaned = cleaned.replace("'", "")
    cleaned = re.sub(r'[^A-Za-z0-9]+', '_', cleaned)
    return cleaned.strip('_').upper()


def load_move_data() -> dict[str, dict[str, int | str]]:
    moves: dict[str, dict[str, int | str]] = {}
    for raw in preprocess_asm(MOVES_ASM.read_text(errors="ignore")):
        m = MOVE_LINE_RE.match(raw)
        if not m:
            continue
        moves[m.group(1)] = {
            "power": int(m.group(2)),
            "type": m.group(3),
            "category": m.group(4),
        }
    return moves


def load_type_chart() -> dict[tuple[str, str], float]:
    chart: dict[tuple[str, str], float] = {}
    for raw in preprocess_asm(TYPE_CHART_ASM.read_text(errors="ignore")):
        stripped = raw.strip()
        if stripped == "db $fe" or stripped == "db $ff ; end":
            break
        m = TYPE_MATCHUP_RE.match(stripped)
        if not m:
            continue
        mult = TYPE_MULTIPLIER.get(m.group(3))
        if mult is not None:
            chart[(m.group(1), m.group(2))] = mult
    return chart


def type_effectiveness(move_type: str, defender_types: tuple[str, str],
                       chart: dict[tuple[str, str], float]) -> float:
    mult = 1.0
    for defender_type in defender_types:
        mult *= chart.get((move_type, defender_type), 1.0)
    return mult


def load_bt_threats(base_stats: dict, move_data: dict, type_chart: dict) -> list[dict]:
    threats: list[dict] = []
    for raw in BT_SPEED_TIERS.read_text(encoding="utf-8").splitlines():
        if raw.startswith("## Trick Room Users"):
            break
        if not raw.startswith("|") or raw.startswith("| Rank") or raw.startswith("|------"):
            continue
        parts = [p.strip() for p in raw.strip().strip("|").split("|")]
        if len(parts) != 13 or not parts[0].isdigit():
            continue

        name = parts[1]
        candidates = display_name_candidates(name)
        meta = None
        for candidate in candidates:
            if candidate in base_stats:
                meta = base_stats[candidate]
                break
        if meta is None:
            continue

        nums = [int(v) for v in parts[5:9] if v != "—"]
        if not nums:
            continue

        threats.append({
            "name": name,
            "speed": max(nums),
            "threat_mode": parts[9],
            "ability": parts[10],
            "item": parts[11],
            "moves": [m.strip() for m in parts[12].split(",")],
            "types": meta["types"],
            "base_atk": int(meta["base_atk"]),
            "base_spa": int(meta["base_spa"]),
        })

    return threats


def best_attack_option(moves: list[str], attacker_types: tuple[str, str], atk_stat: int,
                       spa_stat: int, defender_types: tuple[str, str],
                       move_data: dict[str, dict[str, int | str]],
                       type_chart: dict[tuple[str, str], float]) -> dict | None:
    best = None
    for move in moves:
        if move in CHARGE_MOVES:
            continue
        const = move_const(move)
        if const not in move_data:
            continue
        info = move_data[const]
        power = int(info["power"])
        category = str(info["category"])
        if power <= 1 or category == "STATUS":
            continue
        move_type = str(info["type"])
        eff = type_effectiveness(move_type, defender_types, type_chart)
        if eff == 0:
            continue
        stab = 1.5 if move_type in attacker_types else 1.0
        offense = atk_stat if category == "PHYSICAL" else spa_stat
        score = power * eff * stab * offense
        option = {
            "move": move,
            "power": power,
            "type": move_type,
            "category": category,
            "effectiveness": eff,
            "stab": stab,
            "score": score,
        }
        if best is None or option["score"] > best["score"]:
            best = option
    return best


def is_meaningful_counter(option: dict | None) -> bool:
    if not option:
        return False
    if option["effectiveness"] > 1 and option["power"] >= 60:
        return True
    if option["stab"] > 1 and option["power"] >= 70:
        return True
    return option["score"] >= COUNTER_SCORE_MIN


def is_meaningful_threat(option: dict | None) -> bool:
    if not option:
        return False
    return option["effectiveness"] > 1 and option["power"] >= 60 and option["score"] >= THREAT_SCORE_MIN


def select_auto_target(name: str, base_stats: dict, move_data: dict, type_chart: dict,
                       threats: list[dict], base_key_candidates: list[str], moves: list[str],
                       atk_stat: int, spa_stat: int, nat_mod: float,
                       current_sources: list[tuple[float, str]], item: str,
                       can_agility: bool) -> dict | None:
    meta = None
    for candidate in base_key_candidates:
        if candidate in base_stats:
            meta = base_stats[candidate]
            break
    if meta is None:
        return None

    my_types = meta["types"]
    feasible: list[dict] = []
    skipped: list[str] = []
    base_spe = int(meta["base_spe"])

    for threat in threats:
        if threat["threat_mode"] == "Agility":
            skipped.append(f"{threat['name']} (Agility-based speed skipped)")
            continue

        their_move = best_attack_option(
            threat["moves"], threat["types"], threat["base_atk"], threat["base_spa"],
            my_types, move_data, type_chart,
        )
        if not is_meaningful_threat(their_move):
            continue

        my_move = best_attack_option(
            moves, my_types, atk_stat, spa_stat, threat["types"], move_data, type_chart,
        )
        if not is_meaningful_counter(my_move):
            skipped.append(f"{threat['name']} ({their_move['move']}: no strong return hit)")
            continue

        min_ev, _, post_boost_min = min_ev_to_beat(
            threat["speed"], base_spe, nat_mod, boost_total(current_sources)
        )
        if post_boost_min <= threat["speed"]:
            fallback = suggest_speed_plan(
                threat["speed"], base_spe, nat_mod, current_sources, item, moves, can_agility
            )
            if fallback["post_boost"] <= threat["speed"]:
                skipped.append(f"{threat['name']} ({their_move['move']}: too fast)")
                continue
        else:
            fallback = None

        feasible.append({
            "name": threat["name"],
            "speed": threat["speed"],
            "threat_move": their_move["move"],
            "counter_move": my_move["move"],
            "fallback": fallback,
            "label": f"{threat['name']}({their_move['move']})",
        })

    if not feasible:
        return {"skipped": skipped}

    chosen = max(feasible, key=lambda threat: threat["speed"])
    chosen["skipped"] = skipped[:5]
    return chosen


# ─────────────────────────────────────────────────────────────────────────────
# Core formula helpers
# ─────────────────────────────────────────────────────────────────────────────
def _verify_c(c: int, stat: int, level: int, nat_mod: float, is_hp: bool) -> bool:
    if c <= 0:
        return False
    if is_hp:
        return math.floor(c * level / 100) + level + 10 == stat
    return math.floor((math.floor(c * level / 100) + 5) * nat_mod) == stat


def solve_c(stat: int, level: int, nat_mod: float, is_hp: bool) -> tuple[list[int], bool]:
    """
    Reverse the Gen 3+ formula to find all valid C = 2*Base + IV + floor(EV/4).

    At non-Lv50 levels, the floor(C × Lv/100) step can collapse adjacent C values
    to the same stat — e.g. at Lv82, both C=255 and C=256 give Spe=214.
    This makes EV inference inherently ambiguous from one stat alone.

    Returns (valid_cs, ambiguous):
      valid_cs   — sorted list of all C values that reproduce stat exactly
      ambiguous  — True when len(valid_cs) > 1 (EV cannot be pinned to a single value)
    """
    if is_hp:
        inner = stat - level - 10
        c_raw = inner * 100 / level
    else:
        if nat_mod == 1.0:
            inner = stat
        else:
            inner = math.floor(stat / nat_mod)
            if math.floor(inner * nat_mod) != stat:
                inner += 1
            if math.floor(inner * nat_mod) != stat:
                return [], False
        c_raw = (inner - 5) * 100 / level

    # Search a window around C_raw wide enough to catch all collapsed duplicates.
    # At Lv50 the window is always ≤1; at lower levels it can be up to ⌈100/Lv⌉.
    window = math.ceil(100 / level) + 1
    lo = max(1, math.floor(c_raw) - 1)
    hi = math.ceil(c_raw) + window
    valid = [c for c in range(lo, hi + 1) if _verify_c(c, stat, level, nat_mod, is_hp)]
    return valid, len(valid) > 1


def stat_at_lv50(c: int, nat_mod: float, is_hp: bool) -> int:
    """Project core term C → Lv50 stat."""
    if is_hp:
        return math.floor(c / 2) + 60
    return math.floor((math.floor(c / 2) + 5) * nat_mod)


def min_ev_to_beat(target: int, base_spe: int, nat_mod: float,
                   boost: float) -> tuple[int, int, int]:
    """
    Scan EV 0..252 (step 4) for minimum that makes floor(spe_lv50 * boost) > target.
    Returns (min_ev, spe_lv50, post_boost).
    """
    for ev in range(0, 253, 4):
        c = 2 * base_spe + 31 + ev // 4
        spe = stat_at_lv50(c, nat_mod, is_hp=False)
        post = math.floor(spe * boost)
        if post > target:
            return ev, spe, post
    # max EVs still can't beat target
    c = 2 * base_spe + 31 + 63
    spe = stat_at_lv50(c, nat_mod, is_hp=False)
    return 252, spe, math.floor(spe * boost)


def team_weather(team_flag: str) -> str | None:
    prefix = team_flag.split(":", 1)[0].strip()
    for key, weather in TEAMFLAG_WEATHER_PREFIXES.items():
        if prefix.startswith(key):
            return weather
    return None


def detect_boost_sources(moves: list[str], item: str,
                         ability: str, team_flag: str) -> list[tuple[float, str]]:
    """Return all active speed multipliers from the current setup."""
    sources: list[tuple[float, str]] = []

    weather = team_weather(team_flag)
    if ability in WEATHER_SPEED_ABILITIES and weather:
        ability_weather, mult = WEATHER_SPEED_ABILITIES[ability]
        if ability_weather == weather:
            sources.append((mult, f"×{mult} {ability} in {WEATHER_LABELS[weather]}"))

    if item in SPEED_ITEMS:
        sources.append((SPEED_ITEMS[item], f"×{SPEED_ITEMS[item]} {item}"))

    for mv in moves:
        if mv in SETUP_BOOST:
            sources.append((SETUP_BOOST[mv], f"×{SETUP_BOOST[mv]} {mv}"))

    return sources


def boost_total(sources: list[tuple[float, str]]) -> float:
    return math.prod(mult for mult, _ in sources) if sources else 1.0


def boost_label(sources: list[tuple[float, str]]) -> str:
    return "raw" if not sources else " + ".join(label for _, label in sources)


def suggest_speed_plan(target: int, base_spe: int, nat_mod: float,
                       current_sources: list[tuple[float, str]], item: str,
                       moves: list[str], can_agility: bool) -> dict:
    """Try incremental speed changes in order until the target is cleared."""
    trial_nat = nat_mod
    trial_sources = list(current_sources)
    changes: list[str] = []

    def snapshot() -> dict:
        total = boost_total(trial_sources)
        min_ev, min_spe_lv50, post_boost = min_ev_to_beat(
            target, base_spe, trial_nat, total
        )
        return {
            "changes": list(changes),
            "nat_mod": trial_nat,
            "boost_mult": total,
            "boost_label": boost_label(trial_sources),
            "min_ev": min_ev,
            "min_spe_lv50": min_spe_lv50,
            "post_boost": post_boost,
        }

    if trial_nat < 1.1:
        trial_nat = 1.1
        changes.append("SPED_UP nature")
        plan = snapshot()
        if plan["post_boost"] > target:
            return plan

    if item != "Choice Scarf":
        trial_sources.append((1.5, "×1.5 Choice Scarf"))
        changes.append("Choice Scarf")
        plan = snapshot()
        if plan["post_boost"] > target:
            return plan

    if can_agility and "Agility" not in moves:
        trial_sources.append((2.0, "×2.0 Agility"))
        changes.append("Agility")
        plan = snapshot()
        if plan["post_boost"] > target:
            return plan

    return snapshot()


def format_change_needed(plan: dict | None) -> str:
    if not plan or not plan.get("changes"):
        return "None"
    ev_text = f"{plan['min_ev']} Spe EVs"
    return f"{' + '.join(plan['changes'])}; {ev_text}"


def infer_ev(c: int, base: int, iv: int = 31) -> int:
    """EV from C; clamp to [0, 252]."""
    return max(0, min(252, (c - 2 * base - iv) * 4))


# ─────────────────────────────────────────────────────────────────────────────
# Report formatting
# ─────────────────────────────────────────────────────────────────────────────
def fmt(v) -> str:
    return "—" if v is None else str(v)


def render_md(results: list[dict], csv_arg: str, rows_arg: str | None,
              target_override: int | None) -> str:
    today = date.today()
    src = f"`{csv_arg}` rows {rows_arg or 'all'}"
    tgt_note = (f"global `--targetSpeed {target_override}`"
                if target_override else "per-mon `SpeTarget50` column")

    lines = [
        f"# BT Speed EV Audit — {today}",
        "",
        f"Source: {src}  |  Target: {tgt_note}",
        "",
        "| Mon | Lv | Spe@Lv | Lv50Spe | CurSpeEV | Boost | PostBoost |"
        " Target | TargetMon | MinEV | PostBoostMin | FreedEV | HPGain | Change Needed | Verdict |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]

    for r in results:
        if "error" in r:
            lines.append(f"| {r['name']} | — | — | — | — | — | — | — | — | — | — | — | — | — | ❌ {r['error']} |")
            continue
        lines.append(
            f"| {r['name']} | {r['lv']} | {r['spe_actual']} | {r['spe_lv50_display']} "
            f"| {r['ev_display']} | {r['boost_label']} | {r['post_boost_cur']} "
            f"| {fmt(r['target'])} | {fmt(r.get('target_mon'))} | {fmt(r.get('min_ev'))} "
            f"| {fmt(r.get('post_boost_min'))} | {fmt(r.get('freed_ev'))} "
            f"| {fmt(r.get('hp_gain'))} | {fmt(r.get('change_needed'))} | {r['verdict']} |"
        )

    lines += ["", "---", "", "## Per-Mon Detail", ""]
    for r in results:
        if "error" in r:
            lines += [f"### {r['name']}", f"> ❌ {r['error']}", ""]
            continue

        ambig_note = (
            f"\n  > ⚠ **EV ambiguity (Lv{r['lv']} ≠ 50):** stat {r['spe_actual']} is consistent"
            f" with EV {r['ev_display'].replace(' ⚠ambig', '')} and Lv50 Spe {r['spe_lv50_display']}."
            f" Verify with in-game Judge or Hypertrain confirmation."
        ) if r.get("spe_ambiguous") else ""

        lines += [
            f"### {r['name']}  (Lv{r['lv']})",
            f"- **Actual Spe:** {r['spe_actual']}  →  **Lv50 Spe:** {r['spe_lv50_display']}"
            f"  (C={r['c_spe']}, base={r['base_spe']}, nature={r['nature'] or 'neutral'})"
            + ambig_note,
            f"- **Current Speed EV:** {r['ev_display']}"
            f"  |  Post-boost ({r['boost_label']}): **{r['post_boost_cur']}**",
        ]

        if r.get("target") is not None:
            beat = "✓ beats" if r['post_boost_cur'] > r['target'] else "✗ misses"
            lines += [
                f"- **Target:** {r['target']}  ({beat})",
                f"- **Target Mon:** {r.get('target_mon', '—')}",
                f"- **Min EV to beat target:** {r['min_ev']}"
                f"  (Lv50 Spe={r['min_spe_lv50']}, post-boost={r['post_boost_min']})",
                f"- **Change needed:** {r['change_needed']}",
                f"- **Freed Speed EVs:** {r['freed_ev']}"
                f"  →  redirected to HP: **+{r['hp_gain']} HP stat** at Lv50",
            ]

            if r.get("target_reason"):
                lines.append(f"- **Why this target:** {r['target_reason']}")
            if r.get("skipped_threats"):
                lines.append(f"- **Skipped faster threats:** {'; '.join(r['skipped_threats'])}")

            if r.get("fallback_plan"):
                fp = r["fallback_plan"]
                lines.append(
                    f"- **Fallback if 252 Spe EV still misses:** {' + '.join(fp['changes'])}"
                    f"  →  Lv50 Spe={fp['min_spe_lv50']}, post-boost={fp['post_boost']}"
                    f" using {fp['boost_label']}"
                )
            elif r.get("fallback_failure"):
                ff = r["fallback_failure"]
                tried = " + ".join(ff["changes"]) if ff.get("changes") else "no extra speed options"
                lines.append(
                    f"- **Fallback ceiling:** {tried} only reaches post-boost {ff['post_boost']}"
                    f" using {ff['boost_label']}"
                )

        if r.get("hp_lv50") is not None:
            lines.append(
                f"- **HP:** actual={r['hp_actual']} → Lv50={r['hp_lv50']}"
                f"  (cur HP EV≈{r['cur_hp_ev']},"
                f" with freed EVs≈{r['cur_hp_ev'] + r.get('freed_ev', 0)},"
                f" HP gain +{r.get('hp_gain', 0)})"
            )

        lines += [f"- **{r['verdict']}**", ""]

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="BT Speed EV Auditor")
    ap.add_argument("--csv",         default="bt-assess/my-team.csv")
    ap.add_argument("--rows",        default=None,
                    help="Row range to process e.g. '5-13' (1-indexed; row 1 = header)")
    ap.add_argument("--targetSpeed", type=int, default=None,
                    help="Override every SpeTarget50 with this single Lv50 speed value")
    ap.add_argument("--output",      default=None,
                    help="Output .md path (default: bt-reports/speed_ev_audit_YYYYMMDD.md)")
    args = ap.parse_args()

    csv_path = REPO / args.csv
    out_path = REPO / (args.output or
                       f"bt-reports/speed_ev_audit_{date.today().strftime('%Y%m%d')}.md")

    # Parse row range
    row_lo = row_hi = None
    if args.rows:
        m = re.fullmatch(r'(\d+)\s*-\s*(\d+)', args.rows.strip())
        if not m:
            sys.exit(f"Invalid --rows format {args.rows!r}; expected e.g. '5-13'")
        row_lo, row_hi = int(m.group(1)), int(m.group(2))

    # Load base stats (fast one-pass at startup)
    base_stats = load_base_stats()
    move_data = load_move_data()
    type_chart = load_type_chart()
    bt_threats = load_bt_threats(base_stats, move_data, type_chart)

    # Read CSV
    all_rows: list[tuple[int, dict]] = []
    selected: list[tuple[int, dict]] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for i, row in enumerate(reader, start=2):   # row 2 = first data row
            all_rows.append((i, row))
            if row_lo is not None and not (row_lo <= i <= row_hi):
                continue
            selected.append((i, row))

    if not selected:
        sys.exit("No rows matched. Check --rows range.")

    # Process each mon
    results: list[dict] = []
    auto_target_updates: dict[int, tuple[int, str]] = {}
    for row_num, row in selected:
        name    = row["Name"].strip()
        lv      = int(row["Lv"])
        spe_act = int(row["Spe"])
        hp_act  = int(row["HP"])
        atk_act = int(row["Atk"])
        spa_act = int(row["SpA"])
        nature  = row.get("Nature", "").strip()
        ability = row.get("Ability", "").strip()
        item    = row.get("Item",    "").strip()
        moves   = [row.get(f"Move{j}", "").strip() for j in range(1, 5)]
        team_flag = row.get("TeamFlag", "").strip()

        nat_mod = spe_mod(nature)
        boost_sources = detect_boost_sources(moves, item, ability, team_flag)
        boost_mult = boost_total(boost_sources)
        boost_label_text = boost_label(boost_sources)

        # Lookup base stats
        stem = species_stem(name)
        # Try exact stem, then common variant suffixes
        base_hp = base_spe = None
        can_agility = False
        for candidate in [stem, stem + "_plain"]:
            if candidate in base_stats:
                meta = base_stats[candidate]
                base_hp = int(meta["base_hp"])
                base_spe = int(meta["base_spe"])
                can_agility = bool(meta["can_agility"])
                break

        if base_spe is None:
            results.append({"name": name, "error": f"base stats not found (tried stem={stem!r})"})
            continue

        # ── Solve Speed ───────────────────────────────────────────────────────
        valid_cs, spe_ambiguous = solve_c(spe_act, lv, nat_mod, is_hp=False)
        if not valid_cs:
            results.append({"name": name,
                            "error": f"Cannot solve C for Spe={spe_act} lv={lv} nat={nat_mod}"})
            continue

        # Use the MAX valid C (highest EV) as the conservative estimate.
        # At Lv50 there is no ambiguity; at other levels multiple C values can
        # produce the same stat — the true EV cannot be determined from the stat
        # alone. We default to the max (most EVs) to avoid false "over-invested"
        # verdicts, and flag the ambiguity in the report.
        c_spe = valid_cs[-1]
        c_spe_min = valid_cs[0]   # lowest possible C (fewest EVs)

        cur_spe_ev     = infer_ev(c_spe, base_spe)
        cur_spe_ev_min = infer_ev(c_spe_min, base_spe)
        spe_lv50       = stat_at_lv50(c_spe, nat_mod, is_hp=False)
        spe_lv50_min   = stat_at_lv50(c_spe_min, nat_mod, is_hp=False)
        post_boost_cur = math.floor(spe_lv50 * boost_mult)

        # ── Solve HP (best-effort) ────────────────────────────────────────────
        valid_cs_hp, _ = solve_c(hp_act, lv, 1.0, is_hp=True)
        c_hp      = valid_cs_hp[-1] if valid_cs_hp else None
        cur_hp_ev = infer_ev(c_hp, base_hp) if c_hp else None
        hp_lv50   = stat_at_lv50(c_hp, 1.0, is_hp=True) if c_hp else None

        # ── Target & recommendation ───────────────────────────────────────────
        target = args.targetSpeed
        target_mon = (row.get("SpeTargetMon") or "").strip() or None
        target_reason = None
        skipped_threats: list[str] | None = None
        had_manual_target = bool((row.get("SpeTarget50") or "").strip())
        if target is None:
            raw = (row.get("SpeTarget50") or "").strip()
            target = int(raw) if raw else None

        if target is None and args.targetSpeed is None:
            auto_target = select_auto_target(
                name, base_stats, move_data, type_chart, bt_threats,
                [stem, stem + "_plain"], moves, atk_act, spa_act, nat_mod,
                boost_sources, item, can_agility,
            )
            if auto_target and auto_target.get("speed") is not None:
                target = int(auto_target["speed"])
                target_mon = auto_target["label"]
                target_reason = (
                    f"fastest threat this mon can realistically answer: "
                    f"outspeed {auto_target['name']} and punish with {auto_target['counter_move']} "
                    f"before/through {auto_target['threat_move']}"
                )
                skipped_threats = auto_target.get("skipped") or None
                auto_target_updates[row_num] = (target, target_mon)
            elif auto_target:
                skipped_threats = auto_target.get("skipped") or None

        # Build EV / Lv50-Spe display strings (show range if ambiguous)
        if spe_ambiguous:
            ev_display  = f"{cur_spe_ev_min}–{cur_spe_ev} ⚠ambig"
            lv50_display = (f"{spe_lv50_min}" if spe_lv50_min == spe_lv50
                            else f"{spe_lv50_min}–{spe_lv50}")
        else:
            ev_display   = str(cur_spe_ev)
            lv50_display = str(spe_lv50)

        entry: dict = {
            "name": name, "lv": lv,
            "spe_actual": spe_act, "spe_lv50": spe_lv50, "spe_lv50_display": lv50_display,
            "c_spe": c_spe, "base_spe": base_spe, "nature": nature,
            "cur_spe_ev": cur_spe_ev, "ev_display": ev_display,
            "spe_ambiguous": spe_ambiguous,
            "boost_label": boost_label_text, "post_boost_cur": post_boost_cur,
            "hp_actual": hp_act, "hp_lv50": hp_lv50, "cur_hp_ev": cur_hp_ev,
            "target": target, "target_mon": target_mon,
            "target_reason": target_reason, "skipped_threats": skipped_threats,
            "manual_target": had_manual_target,
        }

        if target is None:
            entry["change_needed"] = "—"
            entry["verdict"] = "No target — set SpeTarget50 in CSV or use --targetSpeed"
        else:
            min_ev, min_spe_lv50, post_boost_min = min_ev_to_beat(
                target, base_spe, nat_mod, boost_mult
            )
            freed_ev = max(0, cur_spe_ev - min_ev)
            hp_gain  = freed_ev // 8   # 8 EVs = +1 HP stat at Lv50

            entry.update({
                "min_ev": min_ev, "min_spe_lv50": min_spe_lv50,
                "post_boost_min": post_boost_min,
                "freed_ev": freed_ev, "hp_gain": hp_gain,
            })

            if post_boost_cur <= target:
                if post_boost_min > target:
                    entry["change_needed"] = f"Raise to {min_ev} Spe EVs"
                    entry["verdict"] = (
                        f"⚠ Under-target: post-boost {post_boost_cur} ≤ {target} "
                        f"— need {min_ev} Spe EVs"
                    )
                else:
                    fallback = suggest_speed_plan(
                        target, base_spe, nat_mod, boost_sources, item, moves, can_agility
                    )
                    if fallback["post_boost"] > target:
                        entry["fallback_plan"] = fallback
                        entry["change_needed"] = format_change_needed(fallback)
                        entry["verdict"] = (
                            f"⚠ Under-target: current max {post_boost_min} ≤ {target} "
                            f"— need {entry['change_needed']}"
                        )
                    else:
                        entry["fallback_failure"] = fallback
                        tried = "+".join(fallback["changes"]) if fallback["changes"] else "no extra speed options"
                        entry["change_needed"] = (
                            f"Unreachable: {tried} maxes at {fallback['post_boost']}"
                        )
                        entry["verdict"] = (
                            f"⚠ Under-target: current max {post_boost_min} ≤ {target} "
                            f"and fallback max {fallback['post_boost']} ≤ {target}"
                        )
            elif freed_ev > 0:
                entry["change_needed"] = f"Drop to {min_ev} Spe EVs"
                entry["verdict"] = (
                    f"→ Over-invested by {freed_ev} EVs: drop to {min_ev} Spe EVs "
                    f"(still post-boosts to {post_boost_min}>{target}) "
                    f"and gain +{hp_gain} HP"
                )
            else:
                entry["change_needed"] = "None"
                entry["verdict"] = f"✓ Optimal ({cur_spe_ev} EVs, post-boost {post_boost_cur}>{target})"

        results.append(entry)

    if auto_target_updates and fieldnames:
        for row_num, row in all_rows:
            update = auto_target_updates.get(row_num)
            if not update:
                continue
            target_value, target_name = update
            if not (row.get("SpeTarget50") or "").strip():
                row["SpeTarget50"] = str(target_value)
            if not (row.get("SpeTargetMon") or "").strip():
                row["SpeTargetMon"] = target_name
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows([row for _, row in all_rows])

    # Write output
    md = render_md(results, args.csv, args.rows, args.targetSpeed)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(md, encoding="utf-8")
    print(f"Saved → {out_path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
