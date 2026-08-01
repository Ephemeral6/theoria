# 20260801T1200Z · figures · the rename hid seven billing legs

## What the figures did not know

`theoria-arm` renamed its per-call cost record. Everything written after
`20260729T105729Z-leg01` is a `bill_shape.json`; `figures/sources.py`'s
`theoria_run` rule required a `cost_curve.json`, and a rule keyed on a
**filename** rather than on a **role** stopped seeing every leg written since.

Seven billing legs, all tracked, all committed, together **USD 85.600207**, were
read by nothing:

| leg | outcome | calls | USD |
|---|---|---|---|
| `20260731T1310Z-A3-level2-carried-r2` | spend_gate_tripped | 5 | 9.556852 |
| `20260731T1430Z-A3-level2-carried-r3` | spend_gate_tripped | 8 | 13.439862 |
| `20260731T1500Z-A3-sk48-carried-l1` | spend_gate_tripped | 9 | 12.251719 |
| `20260731T231654Z-R1-g50t-a` | spend_gate_tripped | 4 | 7.603419 |
| `20260731T231654Z-R1-sk48-b` | spend_gate_tripped | 3 | 7.608528 |
| `20260801T001851Z-R1b-g50t-a` | spend_gate_tripped | 9 | 17.749106 |
| `20260801T001851Z-R1b-sk48-b` | spend_gate_tripped | 6 | 17.390721 |

Two more legs of the same generation billed nothing and are now drawn as no
curve with that reason attached (`20260728T072604Z-E3-sk48-carried`,
`20260731T1240Z-A3-level2-carried`), which is the plate's standing rule that a
run with no calls is not a zero-cost run.

**The coverage probe did fire, and it named the wrong cause.** Before this
change `figures/check_coverage.py` reported all seven as *"its own MANIFEST
reports spend, and the cost curve that spend would be recorded in is absent"* --
a true sentence about a file that was, in fact, there under another name. The
probe's literal inventory is what saved it from silence: had `THEORIA_MEMBERS`
been read off `sources.DISCOVERY`, the rename would have narrowed the oracle in
the same motion and the probe would have reported nothing at all. That is the
third time this file's inventory has had to be kept out of the thing it audits,
and it is the first time the separation has paid.

## What was built

* `sources.Rule` grows `alternates` -- per member, the other filenames that
  satisfy the same role. Resolution is **first declared, first present**, never
  newest-on-disk, so which file a build reads depends on the declaration and on
  what is committed and on nothing else. Every present candidate is *declared*,
  not only the winning one, so both land in `SOURCES.sha256` and the
  cross-check below reads a declared source rather than a raw path.
* `theoria_run` declares `cost_curve.json` first with `bill_shape.json` as its
  alternate. `cost_curve.json` winning is deliberate: the one directory carrying
  both (`20260728T083400Z-E3-sk48-carried-v2`) keeps the file it has always been
  drawn from, and **no already-published curve moved** (verified: 5 theoria runs
  drawn before, 12 after, 0 changed value). Floor 4 → 16.
* `fig02` reads the two dialects apart -- `cost_curve.json` is the bare list,
  `bill_shape.json` wraps it in a document with `totals` and a `reading`. A
  third shape raises rather than being guessed at, which is the rule this file
  already applies to the two ledger dialects.
* `bill_shape.json` carries no per-call `model`, so the model comes from the
  manifest's own `cost.from_price_table.per_model` -- a second reading of one
  fact, named as such in the notes. A run naming two models still stops the
  build.
* `_theoria_dialect_crosscheck` re-tests the alternation on **every build**
  rather than citing this document: on the only run carrying both spellings they
  agree on 30 calls, an identical `step_idx` sequence and `USD 8.404868` to the
  cent. That agreement is what licences the alternation; a disagreement would be
  reported and not reconciled.
* `check_coverage.py`'s inventory becomes an alternation, still as literals, and
  gains a second negative control (`_rename_control`) that removes
  `bill_shape.json` from the rule and requires all seven legs to be reported
  **by name**. It was checked for discrimination, not just for firing: adding a
  `cost_curve.json` run to the victim list makes the control fail, so it is
  keyed on what the rename actually hid.

## What the plate now says about C2

`_c2_verdict` computes two descriptive quantities off the drawn points -- front-half
share of spend, and last billed step over peak -- for every theoria leg with at
least 4 distinct billed steps. They are **not** E2: E2 is the battery's, is
defined on a different axis, and is ABSENT for every live theoria leg because
battery v2 does not score this arm.

| leg | steps | front-half share | tail/peak | outcome |
|---|---|---|---|---|
| `20260728T083400Z-E3-sk48-carried-v2` | 7 | 1.00 | 0.00 | budget_exhausted |
| `20260731T1430Z-A3-level2-carried-r3` | 8 | 0.50 | 0.88 | spend_gate_tripped |
| `20260731T1500Z-A3-sk48-carried-l1` | 4 | 0.44 | 0.82 | spend_gate_tripped |
| `20260801T001851Z-R1b-g50t-a` | 6 | 0.46 | 0.64 | spend_gate_tripped |

Theoria.md 1.6 predicts 前重后轻，收敛后趋零. **The plate shows no convergence,
and the caption now says so rather than leaving the reader to infer it.** Of the
four legs long enough to have a shape, one is front-heavy and three are flat to
back-heavy; `r3`'s eight desk calls cost 1.55, 1.88, 1.57, 1.67, 1.69, 1.91,
1.49, 1.68 USD, which is as flat as a bill gets.

The single leg that *does* taper to zero is `E3-sk48-carried-v2`, whose own
manifest records `budget_exhausted`: its zero-cost steps are the run still
acting after the money stopped. **A budget cutoff drawn on a cost axis is
indistinguishable from convergence, and it is not convergence.** That sentence
is on the plate.

Every other leg ends `spend_gate_tripped`. Not one stopped because it ran out of
surprises, so C2 is UNCONFIRMED here — and the reason is where the legs were cut
off, not what they showed before that. Settling it needs a leg allowed to run
past the gate; **no such run was made, and none was priced, because this session
has zero spend authority.**

## Numbers that moved

| quantity | before | after |
|---|---|---|
| theoria run directories discovered | 7 | 16 |
| theoria curves drawn | 5 | 12 |
| theoria arm total on the plate | USD 23.855414 | **USD 109.455622** (4.6×) |
| `fig02` CSV rows | 2842 | 2868 |
| declared sources in `SOURCES.sha256` | 68 | 87 |
| cost-basis run (chosen by rule: largest billed total with a game_id) | `E3-sk48-carried-v2` | `20260801T001851Z-R1b-g50t-a` |
| theoria per-successful-action price in the caveat | USD 0.2802 (30 actions) | **USD 0.7100** (25 actions) |
| gate 9 UNCORROBORATED | 28 | 37 |

The per-action line is the one a reader will quote. Against the baseline
comparator it carries (`USD 0.1459`, bare_cc opus, `baseline-arms/BUDGET_REPORT.md`
2.1), the theoria arm's markup on the plate goes from about 1.9× to about 4.9×.
That is not a new measurement — it is the same measurement stopping being taken
on the cheapest leg in the set because the six more expensive ones were
invisible. The basis is chosen by rule, not by name, and the rule did not
change.

Gate 9's UNCORROBORATED rising by 9 is the seven new curves plus two: theoria
legs have no baseline roll-up to corroborate against, so they are recorded
uncorroborated rather than agreed. Absence, not zero.

## Two things fixed in passing, and one refused

* `figures/SOURCES.sha256` and `figures/paper/` were stale against six
  `baseline-arms/out/pilot_*.json` roll-ups that another territory regenerated
  and committed. Gates 4, 6 and 14 were **red on master before this branch was
  cut** for that reason alone. Regenerating the manifest closes all three; no
  baseline number was touched, only the digests recording them.
* The C2 verdict is written in ASCII on the plate although Theoria.md 1.6's own
  phrasing is Chinese. matplotlib's SVG writer does not carry those code points
  through intact on this host and what reaches the file depends on the machine's
  codepage — a determinism defect wearing a typography costume. The claim is
  glossed and cited on the plate; the Chinese lives in this file, which nobody
  renders.
* **Refused:** re-anchoring the plate's x-axis on `bill_shape.json`'s game
  `turn` instead of `step_idx`. The new file carries both and `turn` is the more
  honest number, but switching would move every already-published curve for a
  cosmetic gain. Recorded here as a deliberate non-change, not an oversight.

## Gates

`cd figures && bash verify.sh` → **green**, all 15 gates. Gate 3 (two builds,
byte-for-byte) green, which is the territory's rule and the one this change was
most likely to break: 60 images, `csv`, `out`, `paper` and `SOURCES.sha256` all
identical across passes A and B.

## Residual gaps

1. **C2 is unsettled, not settled negatively.** Four legs is a small n, and none
   of them was permitted to run to convergence. The plate reports that; it does
   not resolve it.
2. **`_C2_MIN_BILLED_STEPS = 4` is this plate's own floor** and is not derived
   from anything. It excludes eight drawn legs. A different floor would give a
   different denominator; the excluded legs are listed by name so the choice is
   auditable, but it is a choice.
3. **The alternation is tested on exactly one run.** Only
   `E3-sk48-carried-v2` carries both spellings. If the arm renames again the
   cross-check has nothing to compare and the next rename is caught only by
   `check_coverage.py`'s literals — which is the design, but it is one instrument
   rather than two.
4. **`turn` vs `step_idx` remains unreconciled** (see above), and the plate's
   x-axis is therefore a step index that the arm's own newer artefact does not
   consider the turn number.
5. **Nothing here was measured against a live run.** The seven legs are archive.
