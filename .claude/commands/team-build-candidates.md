---
description: "Fast team-builder step 1. Give Pokémon names (with or without movesets and stats). Assesses existing teams when Team column is present; builds new team proposals from the candidate pool. Outputs to bt-reports/candidates_<YYYYMMDD>.md. Feed that file into /team-build-stats-tune for EV/item tuning."
---

You are building and assessing Battle Tower teams for Polished Crystal (Lv50 cap, 7-win streak format).

**Repo:** `/Users/bohaliu/Ebay/experiment/polishedcrystal`
- Base stats + learnset: `data/pokemon/base_stats/<lowercase_name>.asm`
- Output: `bt-reports/candidates_<YYYYMMDD>.md`

---

## Input

Parse from: $ARGUMENTS

Accepted formats (flexible, mix allowed):
- Names only: `Crobat, Feraligatr, Scizor`
- Names + moves: `Crobat (Brave Bird, U-turn, Roost, Poison Jab)`
- CSV file path (ends in `.csv`): read it. Full column set (all optional except Name):
  ```
  Name, Move1, Move2, Move3, Move4, Lv, HP, Atk, Def, SpA, SpD, Spe, Team
  ```

**Column notes:**
- `Lv, HP, Atk, Def, SpA, SpD, Spe` — actual in-game stats at that level. Pass through to output verbatim; used by `/team-build-stats-tune` for EV inference.
- `Team` — slot assignment: `<Label>:<Slot>` (e.g. `Rain1:Lead`, `Sun1:2nd`, `TR1:Anchor`). Mons with this field belong to an **existing team** and are assessed as-is. Mons with an empty or absent Team field are the **candidate pool** for new team proposals.

---

## Step 0 — Classify Input

Before reading base stats, scan the CSV and split into two groups:

**A. Existing Teams** — mons with a non-empty `Team` column.
- Group by the label prefix (e.g. all `Rain1:*` form "Rain1").
- Sort within each group: Lead → 2nd → Anchor/3rd.
- Skip Step 3 (no new proposals) for these mons.

**B. Candidate Pool** — mons with empty or absent `Team` column.
- Feed into new team proposal logic (Step 3).

If ALL mons have Team flags → skip Step 3.
If NO mons have Team flags → skip existing team assessment in Step 4a.

---

## Step 1 — Read Base Stats (ALL IN PARALLEL)

For every unique Pokémon name across both groups, issue Read tool calls simultaneously — one per Pokémon. File path: `data/pokemon/base_stats/<name_lowercase>.asm` (try underscores for multi-word names, e.g. `porygon_z.asm`).

From each file extract:
- **Types** (line starting with `db`, e.g. `WATER, DARK`)
- **Base stats**: HP, Atk, Def, SpA, SpD, Spe (the `bst` line, non-FAITHFUL values if branched)
- **Abilities** (the `abilities_for` line — note all 3)
- **Learnset** (the `tmhm` line — this is the full list of learnable moves)

Do NOT read any other files in this step. This step should complete in one round of parallel reads.

---

## Step 2 — Per-Mon Analysis (pure reasoning, no more file reads)

For each candidate, derive all of the following from the data just read.
If actual in-game stats are present in the CSV, use them to confirm role inference (e.g. high actual Atk vs low actual SpA confirms physical attacker).

**2a. Type weaknesses, resistances, immunities**
Use the standard Polished Crystal type chart (Gen 6 rules). List:
- `Weak (2x):` [types]
- `Very Weak (4x):` [types] if any
- `Resists:` [types]
- `Immune:` [types]

**2b. Coverage**
Use moves provided by the user, unless they can be optimized in terms of coverage, power/stability, or compatibility with the role. Otherwise, derive the best 4 moves from the learnset.
State the types of offensive coverage the mon provides (e.g. "Water/Dark/Ice physical").

**2c. Role** — infer from base stats using these rough rules:
- Atk >> SpA → physical attacker/sweeper
- SpA >> Atk → special attacker/sweeper
- High HP + Def/SpD, low offenses → wall/support
- Very high Spe (120+) → speed-control / priority pivot
- Balanced with setup move in learnset → setup sweeper
- State one role in one line.

**2d. Recommended Ability & Nature**
Pick the best ability (from the 3 listed) and nature for the inferred role. One line each.
No math needed — just use knowledge of ability effects and nature boosts.

---

## Step 3 — New Team Proposals (Candidate Pool only)

Skip entirely if the candidate pool is empty (all mons have Team flags).

**If candidates ≥ 3:** build teams using the provided candidates AS MUCH AS YOU CAN. A mon can appear in multiple teams. Fill slots from the Polished Crystal Pokédex when needed.

**If candidates < 3:** fill missing slots from the Pokédex (use your knowledge — no file reads). Pick mons that cover the candidate's weaknesses.

**Pairing logic (fast heuristic, no brute force):**
1. For each candidate, list what types it is weak to
2. Find other candidates (or picks) that resist or are immune to those types AND have different offensive types
3. A good pair covers each other's weaknesses AND doesn't share them
4. A good team of 3 has: at least one setup sweeper OR priority user, physical + special mix (or strong single-dimension with priority), no shared 4x weaknesses

Produce **2–4 proposals**, ranked best to worst. Label each: ⭐ Best / Good / Situational.

---

## Step 4 — Output Format

Print to the conversation AND save to file.

### 4a — Existing Teams

For each existing team (from Step 0 Group A), output:

```
## EXISTING_TEAM: [Label]  — e.g. "Rain Team 1"

| Slot   | Pokémon | Type | Role | Ability | Nature | Moves | Actual Stats |
|--------|---------|------|------|---------|--------|-------|--------------|
| Lead   | ...     | ...  | ...  | ...     | ...    | ...   | Lv50 HP:155 Atk:136 Def:95 SpA:95 SpD:100 Spe:116 |
| 2nd    | ...     | ...  | ...  | ...     | ...    | ...   | ... |
| Anchor | ...     | ...  | ...  | ...     | ...    | ...   | ... |

**Coverage:** [offensive types]
**Not covered:** [gap types]
**Shared weaknesses:** [shared danger types — danger zone]
**Resistances provided:** [types at least one mon resists or is immune to]
**Assessment:** [1–2 sentences: overall strength and key concern or improvement area]
```

If actual stats are absent for a mon, show `—` in the Actual Stats column.

### 4b — New Team Proposals

For each proposed team (from Step 3):

```
## TEAM_[N]: [Mon A] / [Mon B] / [Mon C]  — Rating: [S/A/B]

| Slot | Pokémon | Type | Role | Ability | Nature | Suggested Moves |
|------|---------|------|------|---------|--------|-----------------|
| Lead | ...     | ...  | ...  | ...     | ...    | ...             |
| 2nd  | ...     | ...  | ...  | ...     | ...    | ...             |
| 3rd  | ...     | ...  | ...  | ...     | ...    | ...             |

**Coverage:** [offensive types this team hits]
**Not covered:** [types this team struggles to hit]
**Shared weaknesses:** [types all three are weak to — danger zone]
**Resistances provided:** [types at least one mon resists or is immune to]
```

### 4c — Candidate Summary (always append, covers all mons)

```
## CANDIDATE_SUMMARY

| Mon | Types | Role | Ability | Nature | Key Weaknesses | Key Resistances | Team Slot | Actual Stats |
|-----|-------|------|---------|--------|----------------|-----------------|-----------|--------------|
```

`Team Slot`: e.g. `Rain1:Lead`, `T1:Lead / T2:2nd`, or `—` if unassigned.
`Actual Stats`: compact — `Lv50 HP:155 Atk:136 Spe:116` (key stats only), or `—`.

---

## Step 5 — Save File

1. Run `date +%Y%m%d` via Bash for date stamp (e.g. `20260617`)
2. Write full output to `bt-reports/candidates_<YYYYMMDD>.md`
3. Tell user: "Saved to `bt-reports/candidates_<YYYYMMDD>.md` — run `/team-build-stats-tune bt-reports/candidates_<YYYYMMDD>.md` to tune EVs/items."

---

## Speed Rules

- All base_stats reads happen in ONE parallel batch (Step 1)
- Steps 2–4 are pure reasoning — zero file reads
- No parties.asm scan in this skill (that's `/team-build-stats-tune --vs-opponents`)
- Keep output tight — one table per team, one row per candidate
