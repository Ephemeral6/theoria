# What the adversarial audit found, and what changed

The reviewer's report is `ADVERSARIAL-table-audit.md` in this directory. This
file records what was done about it. **Every finding was accepted. Nothing was
argued with.** Where the reviewer overturned a sentence I had written, the
sentence was replaced, not defended.

## The headline

> **8 of 8 sampled numbers transcribed correctly. 0 of 8 sentences fully clean.**

That is the right summary and it is the useful one. No number in the table was
fabricated or mis-copied — the reviewer recomputed the JSON-backed ones from the
artifacts rather than trusting the probes. What broke was the prose wrapped
around the digits: two sentences said something the artifact does not, four
switched denominators, and one boundary cell put an unmeasured thing on the
measured side.

**That is exactly the failure mode this item was told to guard against**, and I
did not catch it myself. The table's own defence — a probe per number — protects
the digit and does nothing for the sentence. That limitation is now written into
the generator's docstring rather than left implied.

## Accepted and fixed

### P0 — factually wrong, now corrected

| # | What was wrong | What it says now |
|---|---|---|
| 1 | `{dl.candidates} theorems in the committed candidate stream` printed **17**. 17 is the *row* count; row 41 is a `kind:"plan"` pruning account whose own `n_theorems` field says 16. E11 §1a and `STATUS.md:189` both say 16. | The probe now counts `producer == deadlock_carver AND kind == invariant` → **16**, and the cell says "16 theorems plus 1 pruning account (17 rows)". My own `RUN_STATE.md` had said "17 **rows**" correctly; the distinction was lost on the way into the table. |
| 2 | `Every rung is run against the others … 7/7 agree`. `p13/dividend.json`'s `cross_check` has exactly two participants — FD's `astar(blind())` and the bundled stub — and `search: "astar(blind())"` at top level. The satisficing rung never takes part. 7 is *instances*, not rung-pairs. And "three of them FD independently **proving** an UNSAT" contradicted the same cell's own "exit codes cannot separate a proof from a shrug" four sentences later: all three carry `fd_exit_code: 12`. | The cell now says two rungs on 7 instances, states that the ladder's third rung was not cross-checked, prints the exit code from a new probe, and attributes the confirmation to the bundled exhaustion that E11 reproduced independently. |
| 3 | **The one genuine "unmeasured written as measured".** `Behaviour on any family but parityworld **and g50t** is 边界未测` put g50t on the *measured* side. Nothing has ever checked `zero_space`'s correctness on g50t. Both sources say so outright — the partial: "对 ARC 真实轨迹的行为，本复核**没有证据**"; the adversarial review: deciding it "**离线做不到**". | g50t is now named as one of *two* unmeasured things in that cell, with the reason: every g50t figure in the table is a census of what was published, not a check that it holds. |

### P1 — denominator and scope switches, now corrected

* **`188 affected worlds`** → **162**, with its own probe. 188 is 72 + *all* 116
  lifted-emitting worlds; "affected" is 162. The superset is still quoted, now
  captioned as a superset, because it does strengthen the point.
* **`46.6 %` / `24.0 pp` are N=500; `29.2 %` / `21.3 %` are N=3000.** They were
  spliced into one causal sentence that does not reconcile (21.3 + 24.0 = 45.3
  against the actual 48.3), and "overstates by about 2×" was attached to 29.2 %
  where the true ratio is 1.6×. The 2× belongs to 46.6 against 22.6, both shares
  of all worlds. The cell now labels both scales and keeps the ratio inside its
  own.
* **`64 are asserted by no invariant`** → the census has three columns, and the
  asserted one is **25**. 64 is "never audited". The correct figure for the
  predicate as written is **86**. The error ran in the rig's favour. All three
  columns are now printed.
* **`the worst group`** → **`the modal group`**, matching what the probe computes
  (`max` by count). The only source that names an extreme names a *different*
  group (5 transitions / 362 dims), and the tripwire would not have fired if the
  worst group changed while the modal one did not.
* **`82 / 4000` and `1633 / 4000`** now carry the trigger-surface qualifier the
  source insisted on: corpus figures, and whether the repo's own end-to-end path
  reaches them is itself unconfirmed.

### P2 — boundaries that were measured and left out, or missing entirely

* Row 1 led with "Geometry is exact" and omitted §8.6: **127/300 worlds report
  more tracks than the world contains** (worst case 40 for 4), and
  `masks_partition_the_foreground` passes on all of them. Partition-correct and
  object-correct are different properties. Now in the cell.
* Row 4 gained a **边界未测** for world families — rows 2 and 3 both had one and
  `lp_potential` hard-codes peg-jump geometry just as narrowly — and gained §4.5's
  unflattering sharpness measurement: `h = 0` on **65.1 %** of usable states, and
  identically 0 on every such state in **579/1550** worlds.
* Row 7 gained a **边界未测** for domains outside sokoban, and now states plainly
  that the **50** confirmed claims span eight producers across four tracks and are
  *not* this engine's score — **36 of 36** is.
* Row 3 gained X-2: of **1271** `cell_local` laws, **329** have a proper-subset
  support and **0** of those lie in the engine's own encoding-law span, with no
  test asserting anything about what `scope` means — while that row's `solves`
  cell advertises exactly that split. The 102 figure is now marked a lower bound.
* Row 6 gained the shared dependency its analyst named as the largest
  (`atoms.evaluate` on both sides) and the scope limit on the distinguishable-world
  count.

### Generator defects

* **`{pf.partition_mismatch}` was printed twice**, once captioned as the *entropy*
  mismatch count. Two different source rows that both happen to be 0 today. The
  entropy figure was published and verified by nothing — precisely what this
  file's docstring swears to prevent. It has its own probe now.
* **`(all four are pinned…)` was hand-coupled to `{fd.unaudited}`.** Now "all of
  them".
* **`rig.mutants` / `rig.survivors` read five files through a bare `read_text()`**,
  so a missing one raised `FileNotFoundError` and exited **1** instead of the
  contracted **3** — the same proof/shrug confusion D-024 exists to prevent, in
  the tool that lectures about it. Both now go through `_load_json`, and **NC7**
  in `measured/negative-controls.txt` pins it.
* **`RUN_STATE.md` claimed the row prose contains "no bare figures".** False:
  ≥28 unprobed numerals. 9 more are now probed; the rest are identifiers and code
  constants, exempted **by name** in `test_engine_table.py` so that adding one is
  a visible decision. The claim in `RUN_STATE.md` is corrected rather than deleted.

## What the reviewer attacked and could not break

Recorded because "could not break" is only worth something with the attack named.

* **`ic3_pdr`'s entire 边界未测 row.** All eight of its assertions were checked
  against `campaign.json`, six mutation catalogues, `props/`, the V10 census,
  `recheck_report.json` and E11 §6b. Every one holds. The reviewer calls it the
  anchor of the table.
* **All five other uses of 边界未测.** Each was searched for a hidden measurement
  that would make it false. None exists. **No boundary is marked unmeasured that
  has in fact been measured** — the error only ever ran the other way, once.
* **The exit codes.** The reviewer built four independent mutants and got
  1/1/3/3, plus `--check` catching a tampered table — arrived at separately from
  this item's own five controls, and agreeing with them.
* **`zs.g50t_rows = 1821` and `coverage` k = n on every row** — reparsed
  independently, 1821/1821.
* **`rig.mutants = 55` / `rig.survivors = 15`** — the six catalogues re-summed by
  hand: 8/3, 6/1, 6/1, 11/4, 18/5, 6/1.
* **The four deadlock dividend numbers**, attacked specifically on the suspicion
  that "47 → 47 on `lmcut`" had been cherry-picked from a different guard
  encoding. All twelve `far6` rows were printed and compared: the three
  zero-dividend figures are all `singleton`, the 47 → 66 is `indexed`, and the
  table's narration already distinguished them.
* **`fd_adapter`'s structural-versus-environmental distinction** and
  **`lp_potential`'s Farkas / `n_pos` caveats** were checked against source and
  called the two best transcriptions in the table.

## After the fixes

143 facts, 19 artifacts, 6 negative controls, 319 passed / 9 skipped,
`ENGINE_TABLE.md` byte-identical across two runs
(`sha256 a57e7310…04d47b5b`).

## What is still true and worth saying

The reviewer's one structural observation is the one to carry into the paper: a
per-number tripwire protects digits, not claims. Six of the eight rows changed
here without a single probe firing, because every digit in them was already
right. The defence against that is an adversarial reader, not a better script.
