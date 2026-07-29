# E15-solver-status-bit — run narrative

Ticket `monitor/board/claimed/E15-solver-status-bit.RES-3.md`, verify lane.
Branch `agent/e15-solver-status-bit`, worktree `.worktrees/e15-solver-status-bit`,
base commit `e942ee6d1ea6109175032a0af67adda357ea1f0c`. Python 3.13.13, scipy
1.17.1, numpy 2.4.4. Zero API calls, zero network, zero sealed-pile contact;
nothing outside `engine-rig/` was written.

The machine-readable provenance is `MANIFEST.json`. This file is the narrative
and does not replace it.

## What was wrong, stated so it cannot be misread

`lp_potential` is **sound but incomplete**, and that is a documented boundary
(`CLAUDE.md`), not a defect. On many genuinely unsolvable configurations no
linear pagoda exists and the engine correctly declines. Nothing in this item
treats that silence as a bug, and no acceptance criterion here improves if the
silence rate falls.

What was wrong is one level down: the engine could not tell a reader **which
kind** of silence it had produced. `if not result.success: return None` folded
HiGHS status 2 (proved infeasible — an answer about the configuration) together
with statuses 1, 3 and 4 (iteration limit, unbounded relaxation, numerical
difficulties — answers about HiGHS) into one value, and the caller's contract
reads that value as "no linear pagoda separates the goal from the start". The
same shape sat in `zero_space`: above 8 colours per cell the subset enumeration
degrades, and the laws it could no longer classify still went out labelled
`scope: "global"`, i.e. as facts about the world.

The published 29.2 % incompleteness rate was never in doubt. What was wrong with
it is that E11's reviewer had to rebuild the LP and read HiGHS's status
themselves to get it. A number a reader can only believe by re-deriving it does
not belong in a paper.

## Order of work

1. `PREREGISTRATION.md` committed first (`72b4eb8`), before anything was run, so
   `git merge-base --is-ancestor 72b4eb8 HEAD` is checkable. It fixes the
   expected integers, names E11's hand derivation as authoritative on any
   disagreement, and lists what is out of scope so it cannot be claimed later.
2. Items 1 and 3 — the engine changes (`9920447`).
3. Item 2 — the census and the reconciliation (`RECONCILIATION.md`).
4. Item 3's verification half (`P3-VERIFICATION.md`).
5. Item 4 — the two controls, and the measured non-vacuity (`NONVACUITY.md`).
6. The mutation battery (`MUTATION.json`), then the adversarial review
   (`ADVERSARIAL-REVIEW.md`), then the corrections it forced.

## Results, one line each

| item | where | result |
|---|---|---|
| 1 — the status bit survives to the caller | `engines/lp_potential/potential.py`, `.../lp_potential/__init__.py` | `LpOutcome` with six status words; `run` branches by name; only HiGHS 2 is `no_linear_pagoda` |
| 2 — the 639 re-issued | `census.jsonl`, `SUMMARY.json`, `RECONCILIATION.md` | 639/639 rows agree with E11; every pre-registered integer matches; 29.2 % is a tally of the engine's own `status` strings |
| 3 — `zero_space` says when it degraded | `engines/zero_space/zerospace.py`, `P3-VERIFICATION.md` | truncated runs publish `undetermined`, never `global`, and carry the cap; the pinned artifact's sha256 is unchanged |
| 4 — two negative controls | `tools/check_status_bit.py`, `controls/*.py`, `NONVACUITY.md` | both exit 0 as committed, both exit 1 against the reverted engine |

## Reading 29.2 % off the artifact

```bash
cd engine-rig
python - <<'PY'
import json
rows = [json.loads(l) for l in open(
    "runs/20260729T044500Z-E15-solver-status-bit/census.jsonl", encoding="utf-8")]
unreachable = [r for r in rows if r["goal_truly_unreachable"]]
silent = [r for r in unreachable if r["engine"]["status"] != "certified"]
print(len(silent), "/", len(unreachable),
      "= %.1f%%" % (100.0 * len(silent) / len(unreachable)))
PY
```

`639 / 2189 = 29.2%`. No LP is re-solved. `bound` and `margin` travel on every
row, so the figure states the box it holds in — before E15 neither was readable
off any artifact.

**What that command reads, exactly.** The **numerator** is the engine's own
`status` string. The **denominator** — 2189 genuinely unreachable worlds — is the
harness's independent forward BFS over `spec.triples`, not an engine field. And
`artifacts/candidates.jsonl` carries no `lp_potential` status at all (`grep -c
"no_linear_pagoda\|lp_outcome\|solver_status"` → 0), because a declined LP emits
no candidate row by design.

So the honest claim is narrower than "the rate is a tally of the engine's status
strings": the rate is a tally of the engine's status strings **over a set the
harness computed**, and it lives in `census.jsonl`, a run artifact pairing the
engine's word with an independent oracle. What actually changed is the half that
was missing: before E15 the numerator was not readable off anything and a
reviewer had to rebuild the LP to get it. See `RECONCILIATION.md` §3.1.

## The mutation battery, and its survivors

**31 mutants, 28 killed, 3 survived, 0 not applied**, against 28 collected test
cases plus two standing controls — deliberately not a one-to-one mirror (C11's
finding was 18 mutants matching 18 tests, which measures the author's
imagination). Judges are kept separate so the report can say *which* defence
caught what: `tools.check_status_bit`, `tests/test_solver_status_bit.py`, and
C11's older `tests/test_tool_failure_is_not_truth.py`.

`MUTATION.json` now carries a `tree` block naming the HEAD it was run against and
whether `engines/`/`tools/`/`tests/` were dirty. The reason is a finding: an
earlier copy of that file reported **30 / 26 / 4** with `M30` as a *survivor*,
three minutes before `potential.py` was changed to close exactly that hole, and
nothing on its face said the counts were stale. A reader trusting the
machine-readable artifact over the prose beside it would have got a wrong answer
about the code they were about to merge. Regenerated at
`af884509a7067a5419b851dbed814b56ff685fcb`, clean tree.

### The pre-registered P5 criterion, and how it was actually scored

`PREREGISTRATION.md` §P5 says the battery must contain "strictly more mutants
than the number of **assertions** written for this item". **That criterion fails
as literally written** and is recorded as failing: 31 mutants against 122
assertions (82 `assert` statements in `tests/test_solver_status_bit.py`, 11
`check()` calls in each standalone control, 18 `failures.append` conditions in
`tools/check_status_bit.py`).

It passes under the reading actually used — **31 mutants against 28 collected
test cases** — which is the criterion C11's finding was about (a battery whose
members correspond one-to-one with the tests measures nothing). That reading is
the better one, but substituting *test cases* for *assertions* is a change of
yardstick after the fact, so it is stated here rather than absorbed: the
pre-registration is left exactly as written and this paragraph is the correction,
in the same shape P3.3's unsatisfiable literal condition was handled.

Counting assertions was the wrong pre-registration to write. An assertion is not
a unit of coverage — `test_every_way_the_solver_can_stop_gets_its_own_word` makes
four assertions about one behaviour, and padding a test with more `assert` lines
would have made the criterion *harder* to meet while testing nothing new. The
criterion should have been about correspondence, not counts, and the honest
report is that the number it named was not met.

The survivors are reported rather than deleted:

* `M25` — gating the degradation keys on the *run* (`scope_exhaustive`) instead
  of on the *label* (`scope == undetermined`). This is the design alternative,
  not a defect: it would put the budget on cell-local rows too. Expected to
  survive and recorded as such.
* `M27` — `STATUS_MEANINGS[BUDGET]` rewritten to read like a verdict. The prose a
  human reads is unasserted; only the status word is.
* `M29` — renaming `CELL_LOCAL`. Caught by `tests/test_zero_space.py`, which is
  not one of this battery's three judges. A survivor of *this* battery, not of the
  suite.
`M30` and `M31` are **killed**, and the story of how is why the battery paid for
itself. `M30` — dropping the `result.success` / status-table disagreement guard —
survived its first run. Chasing why nothing exercised the branch showed the guard was
  *one-directional*: it caught `status != 0` with `success` true, and let the
  converse through. `status == 0` with `success` false fell past it into
  `result.x` and minted a `Certificate` out of whatever a failed solve had left
  behind — which `check_exactly` would then reject as a `CertificateError`,
  i.e. as **weights that did not survive re-checking**. That sentence reads as
  *the engine tried and the geometry refused*. No solve had succeeded at all.
  The engine would have told a confident, specific, wrong story about the
  configuration, which is this item's own thesis turned against it.

  The guard is now symmetric, and the refusal carries a **rebuilt `undecided`
  outcome** rather than the classified one. That second half was found by the
  test rather than by the fix: the first version attached `outcome` as
  classified, so a caller catching a refusal on status 0 or 2 could read
  `decided is True` off it — the collapse removed from the return path,
  reappearing on the error path. `solver_status` is preserved, so the
  contradiction stays diagnosable without being quotable.

Honest limit: with real HiGHS the branch remains unreachable, so the guard is
defended by `_Contradictory`, a synthetic result. The battery did not prove the
defect can fire in production; it proved the code would have believed the wrong
thing if it did. `M31` was added afterwards for the one-directional variant — the
shape the guard had before — and is killed too.

One mutant, `M02` (collapsing `solve_certificate` back to `None`), is killed
**only** by C11's older file. That is worth seeing rather than averaging away:
this item added no coverage of its own for the narrow wrapper.

`not_applied: 0` — every anchor matched exactly once. A patch that silently fails
to apply is the most flattering possible result and the easiest to miss, so it is
counted separately and never as a kill.

## What this does not establish

* **"No linear pagoda exists" is still a HiGHS claim, not a proof.** No exact
  rational infeasibility certificate (Farkas dual) is produced for the 638
  genuinely incomplete worlds; E11 §7 said the same. Separating status 2 from
  status 1 makes the claim *attributable*, not *proved*.
* **The corpus exercises two of the six status words.** `budget`, `unbounded`,
  `numerical` and `undecided` occur 0 times in 3000 worlds. The census is
  evidence they do not fire there and no evidence at all that they are handled
  correctly when they do — that is what the controls are for.
* **The default box is unchanged.** `bound=10` stays; the wider-box columns are a
  diagnostic kept out of every headline count.
* **`jumpgraph` only, `n_pos <= 9` only.** Exhaustive BFS is what buys the ground
  truth, and `MAX_POSITIONS = 9` is a generator constant.
