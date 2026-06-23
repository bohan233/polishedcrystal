---
description: "Fast team-builder step 2. Takes output from /team-build-candidates. Infers current EV distribution from actual in-game stats when present, then assigns/corrects EVs, held items, and finalizes moves. Add --vs-opponents to cross-check opponent movesets. Add --refresh-speed-tiers to rebuild the cached BT speed tier table. Saves a complete team report."
---

You are finalizing a Polished Crystal Battle Tower team (Lv50 cap). A previous `/team-build-candidates` run has already determined team composition, roles, abilities, and natures.

**Repo:** `/Users/bohaliu/Ebay/experiment/polishedcrystal`
- BT opponents (only if --vs-opponents): `data/battle_tower/parties.asm`
- Output: `bt-reports/team_<mons>_<YYYYMMDD>.md`

---

## Input

Parse from: $ARGUMENTS

Format: `<path_to_candidates_file> [T<n>] [--vs-opponents] [--refresh-speed-tiers]`

Examples:
- `bt-reports/candidates_20260617.md` → fast mode, cached speed tiers
- `bt-reports/candidates_20260617.md T1` → process only Team 1
- `bt-reports/candidates_20260617.md --vs-opponents` → also scan opponent movesets
- `bt-reports/candidates_20260617.md --refresh-speed-tiers` → rebuild `bt-reports/bt-speed-tiers.md` before tuning

Read the candidates file. It may contain `## EXISTING_TEAM:` blocks (mature teams with actual stats) and/or `## TEAM_N:` blocks (new proposals). Process ALL teams found unless a team number or label is specified.

If actual in-game stats (`Lv, HP, Atk, Def, SpA, SpD, Spe`) are present in the candidates file, they appear in the Actual Stats column of the team table. Extract them per mon — they drive EV inference in Step 1b.

If no candidates file is given and the argument contains Pokémon names inline, parse them directly (no actual stats available).

---

## Step 0 — Load or Build BT Speed Tier Table

**Do this before anything else.**

1. Check if `bt-reports/bt-speed-tiers.md` exists (use Glob: `bt-reports/bt-speed-tiers.md`).
2. If it **exists** and `--refresh-speed-tiers` is **not** in args → Read it. Hold the speed tier table in context. Skip to Step 1.
3. If it **does not exist** OR `--refresh-speed-tiers` **is** in args → Run the Speed Tier Scan below, save the result, then continue to Step 1.

### Speed Tier Scan (one subagent, runs once)

Spawn a subagent with this exact task:

> **Task: Build BT Speed Tier Table**
>
> Read these two files in full:
> - `data/battle_tower/parties.asm`
> - `data/battle_tower/dvs.asm`
>
> **Step A — Decode DV spreads from dvs.asm:**
> Each `BTDVS_*` entry is 3 bytes: `hp:atk`, `def:spe`, `sat:sdf`.
> Each byte packs two 4-bit DVs: high nibble = first stat, low nibble = second stat.
> Speed DV = **low nibble of the 2nd byte** (`def:spe`).
> Decoding: `$ff`→15, `$f0`→0 (Trick Room spe), `$fe`→14, `$ef`→15, `$ee`→14, `$0f`→15, etc.
> Build a lookup: `BTDVS_NAME → SpeDV`.
>
> **Step B — Parse every Pokémon entry from parties.asm:**
> Format per entry:
> ```
> dp SPECIES, GENDER
> db ITEM
> db MOVE1, MOVE2, MOVE3, MOVE4
> db BTDVS_*
> db ABIL_* | NAT_*
> ```
> For each entry, record: species, item, moves (all 4), BTDVS ref, nature constant.
>
> **Step C — Identify relevant entries:**
> Keep a Pokémon if ANY of:
> - Its base Spe ≥ 80 (use your knowledge of Polished Crystal base stats)
> - Its item is `CHOICE_SCARF`
> - Any of its moves is a speed-boost setup: `DRAGON_DANCE`, `SHELL_SMASH`, `QUIVER_DANCE`, `AGILITY`, `ROCK_POLISH`, `SPEED_SWAP`, `TAILWIND`
>
> **Step D — Calculate Lv50 Spe stat per entry:**
> Formula (Gen 2 DVs, 0 stat exp, Lv50):
> ```
> Spe_base = Base_Spe + SpeDV + 5
> Nature: if NAT constant contains "SPE_UP"  → Spe = floor(Spe_base × 1.1)
>          if NAT constant contains "SPE_DOWN" → Spe = floor(Spe_base × 0.9)
>          otherwise                           → Spe = Spe_base
> ```
> Also compute:
> - `+Scarf` = `floor(Spe × 1.5)` — only if item is CHOICE_SCARF
> - `Post-setup (+1)` = `floor(Spe × 1.5)` — only if has a +1 speed setup move
> - `Post-setup (+2)` = `floor(Spe × 2.0)` — only if has Shell Smash (double boost)
>
> **Step E — Build the table:**
> - One row per unique species (keep the highest-speed variant if multiple sets exist)
> - Sort descending by "effective threat speed": use +Scarf if Scarfed, Post-setup if setup user, else base Spe stat
> - Include all columns: Pokémon, Base Spe, Spe DV, Nature mod, Spe stat, +Scarf, Setup move, Post-setup (+1), Post-setup (+2)
>
> **Step F — Save to `bt-reports/bt-speed-tiers.md`** using this header:
> ```
> # BT Speed Tier Table (Lv50)
> Source: data/battle_tower/parties.asm + data/battle_tower/dvs.asm
> Formula: Spe = BaseSpe + SpeDV + 5, then ×nature (±10%), no stat exp
> Note: regenerate with --refresh-speed-tiers when parties.asm is updated
> ```
> Then the full markdown table. Return the table content to the parent.

After the subagent returns: hold the table in context, continue to Step 1.

---

## Step 1 — Parse Teams from Candidates File

Read the file. For each team (existing or proposed), extract per mon:
- Type, role, ability, nature, moves
- **Actual stats** from the "Actual Stats" column if present: `Lv, HP, Atk, Def, SpA, SpD, Spe`
  - These may appear as `Lv50 HP:155 Atk:136 Def:95 SpA:95 SpD:100 Spe:116`
  - Parse into a per-stat map for each mon
  - If absent → mark as "no actual stats" and skip Step 1b for that mon

No base_stats file reads needed — the candidates file already has this information.

---

## Step 1a — Level Normalization (non-Lv50 mons)

**Run before Step 1b for every mon whose CSV `Lv` field is NOT 50.**
If `Lv = 50` already, skip directly to Step 1b — no normalization needed.

The Gen 3+ stat formula shares a level-independent **core term C = 2×Base + IV + floor(EV/4)**.
Extract C from the actual stat, then reproject to Lv50.

### Non-HP stats

```
inner_Lv   = floor(Stat_Lv / nature_mod)        # strip nature (try +1 if verify fails)
C_raw      = (inner_Lv − 5) × 100 / Lv         # float
C          = round(C_raw)                        # try floor/ceil if EV falls outside 0–252
floor(EV/4)= C − 2×Base − 31                    # assumes IV = 31
EV         = floor(EV/4) × 4                    # must be 0–252
Stat_50    = floor((floor(C / 2) + 5) × nature_mod)
```

### HP stat

```
C_raw      = (HP_Lv − Lv − 10) × 100 / Lv
C          = round(C_raw)
floor(EV/4)= C − 2×Base − 31
EV         = floor(EV/4) × 4
HP_50      = floor(C / 2) + 60
```

**Verify:** plug solved C back → `floor(C × Lv/100) + 5 × nature_mod` (non-HP) or `floor(C × Lv/100) + Lv + 10` (HP) must equal the original stat. If off by 1, adjust C by ±1.

For each normalized stat, record:
- `Stat_actual` (original in-game value at Lv_N)
- `Lv` (original level)
- `C` (solved core term)
- `EV_inferred` (from C)
- `Stat_50` (projected Lv50 value)

Replace the CSV stat values with `Stat_50` equivalents before feeding into Step 1b.

---

## Step 1b — EV Inference from Actual Stats

**Run for every mon where actual in-game stats are available. Skip for mons with no stats.**
**Input stats here are Lv50-equivalent** — either directly from CSV (if Lv=50) or normalized via Step 1a.

### Role → Relevant Stats

Determine which stats are "relevant" (expected to have significant EV investment) vs "untrained" (expected low due to role):

| Role | Relevant (infer EVs) | Untrained (skip, expected low) |
|------|---------------------|-------------------------------|
| Physical sweeper (no setup) | Atk, Spe, HP | SpA, sometimes Def/SpD |
| Physical sweeper (DD/SD) | Atk, Spe or HP | SpA |
| Special sweeper | SpA, Spe, HP | Atk |
| Priority attacker | Atk, HP | Spe, SpA |
| Physical wall | HP, Def, SpD | Atk, SpA |
| Special wall | HP, SpD, Def | Atk, SpA |
| Mixed sweeper | Atk, SpA, Spe, HP | — |
| Rain/Sun/Sand attacker | depends on sets | flag any surprises |

For **untrained** stats: write "untrained (expected for role)" in the config card — do NOT flag as an error or compute EVs.

### EV Inference Formula (Lv50, non-HP stats)

For each relevant stat (IV assumed 31):
```
inner(EV) = floor((2 × Base + 31 + floor(EV/4)) × 0.5) + 5
ref(EV)   = floor(inner(EV) × 1.1)   if +Spe/+Atk/etc. nature on this stat
           = floor(inner(EV) × 0.9)   if −Spe/−Atk/etc. nature on this stat
           = inner(EV)                 otherwise
```

For **HP stat** (no nature modifier):
```
ref(EV) = floor((2 × Base + 31 + floor(EV/4)) × 0.5) + 60
```

Compute ref at these EV breakpoints: **0, 4, 128, 252** (and 84, 96 if needed for specific speed thresholds).

### Matching Rules

Compare actual in-game stat to computed refs:

| Condition | Inference | Action in card |
|-----------|-----------|----------------|
| actual == ref(252) | ~252 EVs | ✓ if optimal, → Change if over-invested |
| actual == ref(128) | ~128 EVs | ✓ if optimal threshold met, else → Change |
| actual == ref(4) or ref(8) | ~4–8 EVs | Usually a dump stat, note value |
| actual == ref(0) | 0 EVs (untrained) | ★ Set if EVs needed |
| actual == ref(0) − 1 | ~0 EVs, IV ≈ 30 | Note: "likely IV 30 — shiny? hypertrain only if speed-critical" |
| actual == ref(0) − 2 | ~0 EVs, IV ≈ 29 | Note: "likely IV 29 — shiny? hypertrain only if tier matters" |
| actual < ref(0) − 2 | IV ≤ 28, not bred | Note: "IV ≤ 28 on relevant stat — consider rebreed if critical" |
| actual between two refs | partial EVs | Estimate and note approximate bucket |

**Shiny IV note policy:** If a relevant stat looks 1–2 points below perfect (suggesting IV 30 or 29), note it gently but do NOT recommend Hypertrain unless the exact stat point changes a speed tier matchup. Run the speed check math (Step 2b) with the actual stat value — if it still clears the relevant BT threshold, no Hypertrain needed.

### Output of Step 1b

Hold a per-mon EV inference map:
```
{
  Dragonite: {
    HP:  { actual: 155, inferred_EVs: "~128", note: "" },
    Atk: { actual: 136, inferred_EVs: "~252", note: "" },
    Def: { actual: 95,  inferred_EVs: "0",    note: "untrained (expected)" },
    SpA: { actual: 95,  inferred_EVs: "—",    note: "untrained (expected for role)" },
    SpD: { actual: 100, inferred_EVs: "0",    note: "" },
    Spe: { actual: 116, inferred_EVs: "~128", note: "" }
  },
  ...
}
```

This map populates the "Current" column in Step 5 config cards.

---

## Step 2 — EV Distribution (role-based defaults and corrections)

For each mon, start from the inferred current EVs (Step 1b) if available, else use role templates below.

Determine the **recommended** EV spread. Compare to inferred current and flag differences.

| Role | Default EV Spread |
|------|------------------|
| Physical sweeper (no setup) | 252 Atk / 252 Spe / 4 HP |
| Physical sweeper (with DD/SD) | 252 Atk / 252 Spe / 4 HP — or 252 Atk / 128 Spe / 128 HP if bulky setup |
| Special sweeper (no setup) | 252 SpA / 252 Spe / 4 HP |
| Special sweeper (with setup) | 252 SpA / 252 Spe / 4 HP — or 252 SpA / 128 Spe / 128 HP if bulky |
| Priority attacker (Bullet Punch etc.) | 252 Atk / 252 HP / 4 SpD |
| Pivot / U-turn user | 252 Atk / 252 Spe / 4 HP (or replace Atk with SpA if special pivot) |
| Physical wall | 252 HP / 252 Def / 4 SpD |
| Special wall | 252 HP / 252 SpD / 4 Def |
| Mixed wall | 252 HP / 128 Def / 128 SpD |
| Setup sweeper (Shell Smash) | 252 Atk / 252 Spe / 4 HP |

Override the template if:
- Mon has Multiscale, Focus Sash, or Sturdy → consider 252 HP to maximize the ability value
- Mon has very low base Spe (<70) with a setup move → consider 0 Spe EVs for Trick Room compatibility
- Mon runs a mixed attacker set → split Atk/SpA as needed
- Inferred current EVs differ from template → evaluate whether the user's actual spread already clears the needed speed tier (via Step 2b) before recommending a change

---

## Step 2b — Speed EV Math (apply to every setup sweeper or speed decision)

**Do NOT skip this step for any mon with DD/Shell Smash/Quiver Dance or when nature is undecided.**
**When actual Spe stat is known: use it directly instead of computing from EV assumptions.**

### Formulas

**Player mon Spe (Lv50, Gen 3+ formula, 31 IVs):**
```
Spe_stat = floor((2 × BaseSpe + 31 + floor(EVs/4)) × 0.5) + 5
Nature:  × 1.1 (Jolly/Timid) | × 1.0 (neutral) | × 0.9 (−Spe)
```
If actual Spe stat is known from the CSV, skip this calculation and use the actual value directly.

**BT opponent Spe (Lv50, Gen 2 DVs, 0 stat exp):**
```
Spe_opp = BaseSpe + SpeDV + 5   [SpeDV = low nibble of dvs.asm 2nd byte, max 15]
Nature:  × 1.1 or × 0.9 if applicable
```
These are exact when the speed tier table is loaded.

**Post-boost multipliers:**
```
+1 stage (1 DD / Agility): × 1.5
+2 stage (Shell Smash):    × 2.0
+3 stage (3 DD):           × 2.5
Choice Scarf (opponent):   × 1.5 applied to Spe_opp
```

### How to use the speed tier table

For each setup sweeper, show a compact calculation block:

1. **Start from actual Spe** (from CSV) or compute at 0 / 128 / 252 EVs if no actual stats.
2. **Calculate post-boost Spe** at +1 and +2 stages.
3. **Find the cut-off row** — highest BT opponent Spe your post-boost speed outspeeds. Name it.
4. **Find the first row you lose to** — name it. State how the team handles it (priority, teammate).
5. **Check Scarf column** — if any Scarf holder's Spe > your post-boost Spe, name them.
6. **If two EV spreads clear the same cut-off**, the lower-Spe spread wins — show where freed EVs go.
7. **If actual Spe is already meeting the threshold** → recommend ✓ Keep; no change needed.
8. **State the final choice**: exact Spe stat, which opponents it outspeeds post-boost, which it can't.

**When actual Spe is present and 1–2 pts below expected max (IV 29–30):**
Run the speed check with the actual value. If it still clears the relevant BT threshold → "no Hypertrain needed — threshold met." If it misses by 1–2 → flag: "Hypertrain would help here — gains [X] speed, clears [opponent]."

**Example output format:**
```
Speed check — Dragonite (actual Spe: 116, Adamant, base 80):
  Actual stat: 116 → inferred ~128 EVs, IV=31
  Post +1 DD: 174   Post +2: 232

  BT speed tier table (relevant rows):
    Electrode:     170 Spe (raw, no setup)
    Crobat:        165 Spe (raw)
    Aerodactyl:    165 Spe (raw)
    Jolteon:       163 Spe (raw, no Scarf in BT)
    Tauros:        195 Scarf

  Post-DD 174 beats: Electrode (170) ✓, Crobat/Aerodactyl (165) ✓, Jolteon (163) ✓
  Cannot outspeed: Tauros Scarf (195) → handled by ExtremeSpeed priority

  → Current 128 Spe EVs is optimal. No change needed.
```

> If the speed tier table is not loaded (Step 0 skipped), fall back to:
> `130 base ≈ 200 no-Scarf, 300 +Scarf | 120 base ≈ 189 | 110 base ≈ 178`
> and note: "run `--refresh-speed-tiers` for exact BT opponent speeds."

---

## Step 3 — Held Item Assignment

Assign one item per mon based on role + ability interaction. Use ★ prefix if item was blank.
If item is already known (e.g. from a mature team), confirm it or suggest change.

| Role | Item options | Notes |
|------|-------------|-------|
| DD/SD sweeper (frail) | Lum Berry | Prevents status on setup turn |
| DD/SD sweeper (tanky) | Life Orb | More damage after setup |
| Bulk-up sweeper | Leftovers | Sustain during setup |
| Choice attacker | Choice Band (physical) / Choice Specs (special) | Commit to one move |
| Priority anchor | Assault Vest | No setup needed, tanky |
| Shell Smash sweeper | White Herb | Cancels stat drops = net +2/+2/+2 |
| Pivot / U-turn | Black Sludge (Poison) / Leftovers (others) | Longevity for repeated pivoting |
| Glass cannon | Life Orb | Max damage, no bulk to save |
| Rain sweeper | Choice Specs / Life Orb | Maximize Swift Swim damage |
| Sun sweeper | Choice Specs / Life Orb | Maximize Chlorophyll damage |
| Trick Room setter | Mental Herb / Lum Berry | Prevent Taunt/status blocking TR |

Avoid giving the same item type to all three mons (e.g. three Life Orbs = whole team shredded by chip).

---

## Step 4 — Move Finalization

For each mon, confirm or adjust the 4 moves. Rules:
- Keep moves the user specified unless they conflict with the item
- Ensure at least one STAB move
- Ensure coverage for the team's "not covered" types where possible
- Priority moves (Bullet Punch, Aqua Jet, ExtremeSpeed, Sucker Punch) are very valuable — include when role-appropriate
- Note any move renamed in the CSV (e.g. "Fire Blitz" → "Flare Blitz")
- For weather teams: ensure the weather setter (Drizzle/Drought/Sand Stream/Snow Warning) is the lead and moves support the weather condition

**With `--vs-opponents` flag only:** spawn one subagent to scan `data/battle_tower/parties.asm`. Ask:
> "For a team of [Mon A / Mon B / Mon C], find the top 5 opponent sets that threaten this team, and identify any move slots where switching to [coverage move X] would directly counter a dangerous opponent."

Use the subagent result to make 1–2 targeted adjustments only. Don't redesign the team.

---

## Step 5 — Output: Per-Mon Configuration Cards

For each team, output one configuration card per Pokémon.

When actual in-game stats are available (from Step 1b), populate the "Current" column with actual values and inferred EVs. When absent, show `—`.

```
### [Pokémon Name]  — [Team Label], [Slot]

| Field    | Current (actual / inferred)     | Final Recommended      | Action      |
|----------|---------------------------------|------------------------|-------------|
| Nature   | Adamant (+Atk/−SpA)             | Adamant                | ✓ Keep      |
| Ability  | Multiscale                      | Multiscale             | ✓ Keep      |
| Item     | Lum Berry                       | Lum Berry              | ✓ Keep      |
| Move 1   | Dragon Dance                    | Dragon Dance           | ✓ Keep      |
| Move 2   | Outrage                         | Outrage                | ✓ Keep      |
| Move 3   | ExtremeSpeed                    | ExtremeSpeed           | ✓ Keep      |
| Move 4   | Fire Punch                      | Fire Punch             | ✓ Keep      |
| HP EVs   | ~128 (stat 155)                 | 128                    | ✓ Keep      |
| Atk EVs  | ~252 (stat 136)                 | 252                    | ✓ Keep      |
| Def EVs  | 0 (stat 95)                     | 0                      | ✓ Keep      |
| SpA EVs  | untrained — expected for role   | 0                      | ✓ Keep      |
| SpD EVs  | 0 (stat 100)                    | 0                      | ✓ Keep      |
| Spe EVs  | ~128 (stat 116)                 | 128                    | ✓ Keep      |

**Action legend:** ✓ Keep | → Change | ★ Set (new) | ⚠️ Rebreed recommended

**Notes:** [per decision — why this spread, why this item, any speed tier result, any IV/shiny note]
```

**IV / shiny notes in config card:**
- If a relevant stat is 1–2 pts below expected max and the threshold is still met → "Spe 116: meets speed threshold (post-DD 174 > Electrode 170) — no Hypertrain needed."
- If a relevant stat is 1–2 pts below AND the threshold is missed → "Spe 115: misses Electrode threshold by 1 (post-DD 172 < 170 ✗). Hypertrain to fix, or accept the coin-flip."
- If a non-relevant stat is low → no note needed.

---

## Step 6 — Team Play Summary

After all config cards for a team:

```
### How to Play: [Team Label]
- **Lead with [Mon]:** [why]
- **2nd [Mon]:** [when to bring in]
- **Anchor [Mon]:** [what it cleans up]
- **Key danger:** [the one thing that can go wrong]
- **Safeguard:** [what to do about it]
```

For weather teams, also note:
- **Weather condition:** [Rain/Sun/Sand/Hail — who sets it, how many turns, Swift Swim/Chlorophyll mons]
- **Weather counter risk:** [opposing weather setters or Cloud Nine/Air Lock]

---

## Step 7 — Save File

1. Run `date +%Y%m%d` for date stamp (e.g. `20260617`)
2. Filename:
   - Single team: `bt-reports/team_<Mon1>_<Mon2>_<Mon3>_<YYYYMMDD>.md`
   - Multiple teams: `bt-reports/team_multi_<YYYYMMDD>.md`
   - Existing team label known: `bt-reports/team_<Label>_<YYYYMMDD>.md` (e.g. `team_Rain1_20260617.md`)
3. Write full output using Write tool
4. Tell user: "Report saved to `bt-reports/<filename>`"

---

## Speed Rules

- Step 0: ONE file read (cached) or ONE subagent (rebuild) — never both
- Step 1: reads candidates file only — no base_stats reads
- Step 1a: pure arithmetic — fast, no file reads; skip entirely if all mons are Lv50
- Step 1b: pure arithmetic — fast, no file reads
- Steps 2–6: pure reasoning — fast
- `--vs-opponents`: ONE targeted subagent call only
- `--refresh-speed-tiers`: ONE targeted subagent call, result cached for all future runs
- Keep config cards concise — one table + brief notes per mon, no paragraphs
