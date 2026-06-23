#!/usr/bin/env python3

import math
import re
from dataclasses import dataclass
from pathlib import Path


REPO = Path(__file__).resolve().parent
BT_PARTIES = REPO / "data" / "battle_tower" / "parties.asm"
BT_DVS = REPO / "data" / "battle_tower" / "dvs.asm"
BASE_STATS_DIR = REPO / "data" / "pokemon" / "base_stats"
OUT = REPO / "bt-reports" / "bt-speed-tiers.md"

USE_FAITHFUL = False

SETUP_BOOSTS = {
    "AGILITY": 2.0,
    "DRAGON_DANCE": 1.5,
    "QUIVER_DANCE": 1.5,
    "ROCK_POLISH": 2.0,
    "SHELL_SMASH": 2.0,
}

ITEM_SPEED_BOOSTS = {
    "CHOICE_SCARF": 1.5,
}

WEATHER_ABILITY_BOOSTS = {
    "SWIFT_SWIM": ("RAIN_DANCE", 2.0, "Rain"),
    "CHLOROPHYLL": ("SUNNY_DAY", 2.0, "Sun"),
    "SAND_RUSH": ("SANDSTORM", 2.0, "Sand"),
    "SLUSH_RUSH": ("HAIL", 2.0, "Hail"),
}

FORM_SUFFIXES = {
    "ALOLAN_FORM": "_alolan",
    "GALARIAN_FORM": "_galarian",
    "HISUIAN_FORM": "_hisuian",
    "PALDEAN_FORM": "_paldean",
    "TAUROS_PALDEAN_FIRE_FORM": "_paldean_fire",
    "TAUROS_PALDEAN_WATER_FORM": "_paldean_water",
    "GYARADOS_RED_FORM": "",
    "ARBOK_KOGA_FORM": "",
}

DISPLAY_FORM_SUFFIXES = {
    "ALOLAN_FORM": "-A",
    "GALARIAN_FORM": "-G",
    "HISUIAN_FORM": "-H",
    "PALDEAN_FORM": "-P",
    "TAUROS_PALDEAN_FIRE_FORM": "-P-Fire",
    "TAUROS_PALDEAN_WATER_FORM": "-P-Water",
    "GYARADOS_RED_FORM": " (Red)",
    "ARBOK_KOGA_FORM": " (Koga)",
}

MANUAL_FILENAME_OVERRIDES = {
    ("FARFETCH_D", None): "farfetch_d_plain",
    ("MR__MIME", None): "mr__mime_plain",
    ("ZAPDOS", None): "zapdos_plain",
    ("TAUROS", None): "tauros_plain",
}

MANUAL_DISPLAY_NAMES = {
    "FARFETCH_D": "Farfetch'd",
    "MR__MIME": "Mr. Mime",
    "MR__RIME": "Mr. Rime",
    "PORYGON_Z": "Porygon-Z",
}

BST_RE = re.compile(
    r"\bbst\s+\d+\s*,\s*(\d+)\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*(\d+)"
)
RAWCHAR_RE = re.compile(r'rawchar "([^"]+)"')
ABILITY_LABEL_RE = re.compile(r"^(\w+):\s+rawchar\s+\"([^\"]+)@\"")

SPECIAL_TOKEN_NAMES = {
    "DAZZLINGLEAM": "Dazzling Gleam",
    "DRAININGKISS": "Draining Kiss",
    "DOUBLE_EDGE": "Double-Edge",
    "U_TURN": "U-turn",
    "WILL_O_WISP": "Will-O-Wisp",
    "HI_JUMP_KICK": "Hi Jump Kick",
    "X_SCISSOR": "X-Scissor",
    "THUNDERPUNCH": "ThunderPunch",
    "THUNDERSHOCK": "ThunderShock",
    "POISONPOWDER": "PoisonPowder",
    "NO_MOVE": "No Move",
}

ABILITY_NAME_MAP: dict[str, str] | None = None


@dataclass
class Entry:
    species: str
    form: str | None
    item: str
    moves: list[str]
    dvs: str
    ability: str
    nature: str


def camel_to_constant(label: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", label).upper()


def preprocess_asm(text: str, use_faithful: bool) -> list[str]:
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


def asm_ident_to_name(ident: str) -> str:
    if ident in MANUAL_DISPLAY_NAMES:
        return MANUAL_DISPLAY_NAMES[ident]
    words = ident.split("_")
    compact = [w for w in words if w]
    return " ".join(word.capitalize() for word in compact)


def species_display_name(species: str, form: str | None) -> str:
    base = asm_ident_to_name(species)
    if form:
        return base + DISPLAY_FORM_SUFFIXES.get(form, f" ({form})")
    return base


def species_filename(species: str, form: str | None) -> str:
    override = MANUAL_FILENAME_OVERRIDES.get((species, form))
    if override:
        return override
    stem = species.lower()
    suffix = FORM_SUFFIXES.get(form, "") if form else ""
    candidate = stem + suffix
    if (BASE_STATS_DIR / f"{candidate}.asm").exists():
        return candidate
    plain_candidate = f"{stem}_plain"
    if (BASE_STATS_DIR / f"{plain_candidate}.asm").exists():
        return plain_candidate
    if (BASE_STATS_DIR / f"{stem}.asm").exists():
        return stem
    raise FileNotFoundError(f"No base stat file for {species} form={form}")


def load_base_stats() -> dict[tuple[str, str | None], int]:
    result: dict[tuple[str, str | None], int] = {}
    for species_file in BASE_STATS_DIR.glob("*.asm"):
        lines = preprocess_asm(species_file.read_text(errors="ignore"), USE_FAITHFUL)
        text = "\n".join(lines)
        m = BST_RE.search(text)
        if not m:
            continue
        result[(species_file.stem, None)] = int(m.group(2))
    return result


def load_ability_names() -> dict[str, str]:
    global ABILITY_NAME_MAP
    if ABILITY_NAME_MAP is not None:
        return ABILITY_NAME_MAP
    result: dict[str, str] = {}
    ability_names = REPO / "data" / "abilities" / "names.asm"
    for raw in ability_names.read_text(errors="ignore").splitlines():
        m = ABILITY_LABEL_RE.match(raw.strip())
        if m:
            result[camel_to_constant(m.group(1))] = m.group(2)
    ABILITY_NAME_MAP = result
    return result


def parse_dv_map() -> dict[str, int]:
    lines = preprocess_asm(BT_DVS.read_text(errors="ignore"), USE_FAITHFUL)
    spe_dvs: dict[str, int] = {}
    names = [
        "BTDVS_PERFECT",
        "BTDVS_TRICK_ROOM",
        "BTDVS_HP_FIGHTING",
        "BTDVS_HP_FLYING",
        "BTDVS_HP_POISON",
        "BTDVS_HP_GROUND",
        "BTDVS_HP_ROCK",
        "BTDVS_HP_BUG",
        "BTDVS_HP_GHOST",
        "BTDVS_HP_STEEL",
        "BTDVS_HP_FIRE",
        "BTDVS_HP_WATER",
        "BTDVS_HP_GRASS",
        "BTDVS_HP_ELECTRIC",
        "BTDVS_HP_PSYCHIC",
        "BTDVS_HP_ICE",
        "BTDVS_HP_DRAGON",
        "BTDVS_HP_DARK",
    ]
    idx = 0
    for raw in lines:
        stripped = raw.strip()
        if not stripped.startswith("db "):
            continue
        if idx >= len(names):
            break
        parts = [p.strip() for p in stripped[3:].split(",")]
        def_spe = int(parts[1].replace("$", ""), 16)
        spe_dvs[names[idx]] = def_spe & 0xF
        idx += 1
    return spe_dvs


def parse_ability_nature(token_line: str, ability_names: dict[str, str]) -> tuple[str, str]:
    parts = [part.strip() for part in token_line.split("|")]
    ability_token = next(part for part in parts if "ABIL_" in part)
    nature = next(part for part in parts if "NAT_" in part)
    ability_token = ability_token.replace("SHINY_MASK", "").strip(" |")
    ability_token = ability_token.removeprefix("ABIL_")
    ability = ability_token
    for candidate in sorted(ability_names, key=len, reverse=True):
        if ability_token.endswith(candidate):
            ability = candidate
            break
    nature = nature.removeprefix("NAT_")
    return ability, nature


def parse_entry(lines: list[str], i: int, ability_names: dict[str, str]) -> tuple[Entry, int]:
    dp = lines[i].strip()
    item = lines[i + 1].strip().removeprefix("db ")
    moves = [move.strip() for move in lines[i + 2].strip().removeprefix("db ").split(",")]
    dvs = lines[i + 3].strip().removeprefix("db ").strip()
    ability, nature = parse_ability_nature(lines[i + 4].strip().removeprefix("db ").strip(), ability_names)

    body = dp.removeprefix("dp ")
    parts = [part.strip() for part in body.split(",")]
    species = parts[0]
    form = None
    if len(parts) > 1 and "|" in parts[1]:
        _, form = [p.strip() for p in parts[1].split("|", 1)]
    elif len(parts) > 2 and parts[2].startswith("|"):
        form = parts[2].replace("|", "").strip()
    elif len(parts) > 2:
        form = parts[2]

    return Entry(species=species, form=form, item=item, moves=moves, dvs=dvs, ability=ability, nature=nature), i + 5


def parse_bt_entries() -> list[Entry]:
    lines = preprocess_asm(BT_PARTIES.read_text(errors="ignore"), USE_FAITHFUL)
    ability_names = load_ability_names()
    entries: list[Entry] = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not stripped.startswith("dp "):
            i += 1
            continue
        entry, i = parse_entry(lines, i, ability_names)
        entries.append(entry)
    return entries


def nature_mod(nature: str) -> float:
    if "SPE_UP" in nature:
        return 1.1
    if "SPE_DOWN" in nature:
        return 0.9
    return 1.0


def format_nature(nature: str) -> str:
    if "SPE_UP" in nature:
        return "SPE_UP"
    if "SPE_DOWN" in nature:
        return "SPE_DOWN"
    return "neutral"


def format_token(token: str) -> str:
    if token in SPECIAL_TOKEN_NAMES:
        return SPECIAL_TOKEN_NAMES[token]
    if token == "HIDDEN_POWER":
        return "Hidden Power"
    if token.endswith("_M"):
        token = token[:-2]
    return token.replace("__", ". ").replace("_", " ").title()


def format_item(item: str) -> str:
    return format_token(item)


def format_move(move: str) -> str:
    return format_token(move)


def hidden_power_type(dvs: str) -> str | None:
    prefix = "BTDVS_HP_"
    if not dvs.startswith(prefix):
        return None
    return format_token(dvs.removeprefix(prefix))


def format_move_for_entry(move: str, dvs: str) -> str:
    if move == "HIDDEN_POWER":
        hp_type = hidden_power_type(dvs)
        if hp_type:
            return f"Hidden Power({hp_type})"
    return format_move(move)


def format_ability(ability: str) -> str:
    return load_ability_names().get(ability, format_token(ability))


def effective_speed_sources(entry: Entry, raw_spe: int) -> tuple[int, list[str], str, int | None, int | None, int | None]:
    scarf = None
    plus1 = None
    plus2 = None
    labels: list[str] = []
    best = raw_spe
    threat = "Fast"

    if entry.item in ITEM_SPEED_BOOSTS:
        scarf = math.floor(raw_spe * ITEM_SPEED_BOOSTS[entry.item])
        if scarf > best:
            best = scarf
            threat = "Scarf"
            labels = [format_item(entry.item)]

    for move in entry.moves:
        if move in SETUP_BOOSTS:
            boosted = math.floor(raw_spe * SETUP_BOOSTS[move])
            if SETUP_BOOSTS[move] == 1.5:
                plus1 = max(plus1 or 0, boosted)
            else:
                plus2 = max(plus2 or 0, boosted)
            if boosted > best:
                best = boosted
                threat = format_move(move)
                labels = [format_move(move)]

    weather = WEATHER_ABILITY_BOOSTS.get(entry.ability)
    if weather and weather[0] in entry.moves:
        boosted = math.floor(raw_spe * weather[1])
        plus2 = max(plus2 or 0, boosted)
        if boosted > best:
            best = boosted
            threat = f"{format_ability(entry.ability)} {weather[2]}"
            labels = [weather[2], format_ability(entry.ability)]

    return best, labels, threat, scarf, plus1, plus2


def relevant(entry: Entry, base_spe: int) -> bool:
    if base_spe >= 80:
        return True
    if entry.item == "CHOICE_SCARF":
        return True
    if any(move in SETUP_BOOSTS for move in entry.moves):
        return True
    weather = WEATHER_ABILITY_BOOSTS.get(entry.ability)
    return bool(weather and weather[0] in entry.moves)


def load_base_spe(species: str, form: str | None) -> int:
    stem = species_filename(species, form)
    text = "\n".join(preprocess_asm((BASE_STATS_DIR / f"{stem}.asm").read_text(errors="ignore"), USE_FAITHFUL))
    m = BST_RE.search(text)
    if not m:
        raise ValueError(f"Could not parse base stats for {species} form={form}")
    return int(m.group(2))


def build_report() -> str:
    dv_map = parse_dv_map()
    entries = parse_bt_entries()

    by_species: dict[str, dict] = {}
    trick_room_rows: list[dict] = []

    for entry in entries:
        base_spe = load_base_spe(entry.species, entry.form)
        if not relevant(entry, base_spe):
            if entry.dvs == "BTDVS_TRICK_ROOM" or "TRICK_ROOM" in entry.moves:
                spe_dv = dv_map[entry.dvs]
                raw_base = base_spe + spe_dv + 5
                raw_spe = math.floor(raw_base * nature_mod(entry.nature))
                trick_room_rows.append({
                    "name": species_display_name(entry.species, entry.form),
                    "moves": ", ".join(format_move_for_entry(m, entry.dvs) for m in entry.moves),
                    "ability": format_ability(entry.ability),
                    "item": format_item(entry.item),
                    "nature": format_nature(entry.nature),
                    "raw_spe": raw_spe,
                })
            continue

        spe_dv = dv_map[entry.dvs]
        spe_base = base_spe + spe_dv + 5
        raw_spe = math.floor(spe_base * nature_mod(entry.nature))
        effective, _, threat, scarf, plus1, plus2 = effective_speed_sources(entry, raw_spe)

        row = {
            "name": species_display_name(entry.species, entry.form),
            "base_spe": base_spe,
            "spe_dv": spe_dv,
            "nature": format_nature(entry.nature),
            "spe_stat": raw_spe,
            "scarf": scarf,
            "plus1": plus1,
            "plus2": plus2,
            "threat": threat,
            "ability": format_ability(entry.ability),
            "item": format_item(entry.item),
            "moves": ", ".join(format_move_for_entry(m, entry.dvs) for m in entry.moves),
            "effective": effective,
        }

        current = by_species.get(row["name"])
        if current is None or row["effective"] > current["effective"]:
            by_species[row["name"]] = row

        if entry.dvs == "BTDVS_TRICK_ROOM" or "TRICK_ROOM" in entry.moves:
            trick_room_rows.append({
                "name": row["name"],
                "moves": row["moves"],
                "ability": row["ability"],
                "item": row["item"],
                "nature": row["nature"],
                "raw_spe": raw_spe,
            })

    rows = sorted(by_species.values(), key=lambda r: (-r["effective"], -r["spe_stat"], r["name"]))
    trick_room_rows = sorted(trick_room_rows, key=lambda r: (r["raw_spe"], r["name"]))

    lines = [
        "# BT Speed Tier Table (Lv50)",
        "Source: data/battle_tower/parties.asm + data/battle_tower/dvs.asm",
        "Formula: Spe = BaseSpe + SpeDV + 5, then ×nature (floor ×1.1 SPE_UP / ×0.9 SPE_DOWN), 0 stat exp",
        "Note: regenerate with `python3 generate_bt_speed_tiers.py` when parties.asm is updated",
        "",
        "Sorted by **effective threat speed** (post-Scarf, post-setup, or post-self-weather when applicable).",
        "One row per unique species/form threat. Fastest variant kept when multiple sets exist.",
        "",
        "| Rank | Pokemon | Base Spe | Spe DV | Nature | Spe stat | +Scarf | +1 Speed | +2 Speed | Threat | Ability | Item | Moves |",
        "|------|---------|----------|--------|--------|----------|--------|----------|----------|--------|---------|------|-------|",
    ]

    for idx, row in enumerate(rows, start=1):
        lines.append(
            f"| {idx} | {row['name']} | {row['base_spe']} | {row['spe_dv']} | {row['nature']} | {row['spe_stat']} "
            f"| {row['scarf'] if row['scarf'] is not None else '—'} "
            f"| {row['plus1'] if row['plus1'] is not None else '—'} "
            f"| {row['plus2'] if row['plus2'] is not None else '—'} "
            f"| {row['threat']} | {row['ability']} | {row['item']} | {row['moves']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Trick Room Users",
        "These mons either run `BTDVS_TRICK_ROOM` or explicitly carry `Trick Room`.",
        "",
        "| Pokemon | Raw Spe | Nature | Ability | Item | Moves |",
        "|---------|---------|--------|---------|------|-------|",
    ]

    seen_tr: set[tuple[str, str, str, str, str]] = set()
    for row in trick_room_rows:
        key = (row["name"], row["moves"], row["ability"], row["item"], row["nature"])
        if key in seen_tr:
            continue
        seen_tr.add(key)
        lines.append(
            f"| {row['name']} | {row['raw_spe']} | {row['nature']} | {row['ability']} | {row['item']} | {row['moves']} |"
        )

    lines += [
        "",
        "---",
        "",
        "## Key Notes",
        "",
        "- `Threat` reflects the fastest realistic speed mode from that exact BT set: raw, Choice Scarf, setup, or self-enabled weather ability.",
        "- Weather ability boosts are included only when that same set can self-enable the weather with `Rain Dance`, `Sunny Day`, `Sandstorm`, or `Hail`.",
        "- `+1 Speed` covers moves like `Dragon Dance` and `Quiver Dance`; `+2 Speed` covers `Agility`, `Rock Polish`, `Shell Smash`, and self-weather x2 ability lines.",
        "- The detailed `Ability`, `Item`, and `Moves` columns show exactly what to watch out for on the fastest kept variant for each threat.",
    ]

    return "\n".join(lines) + "\n"


def main() -> None:
    OUT.write_text(build_report(), encoding="utf-8")
    print(f"Saved → {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
