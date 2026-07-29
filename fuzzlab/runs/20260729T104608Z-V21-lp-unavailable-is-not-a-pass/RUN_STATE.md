# V-21 · `LpUnavailable` is not a pass — run state

Ticket: `monitor/board/claimed/V21-lp-unavailable-is-not-a-pass.RES-3.md`.
Branch `agent/v21-lp-unavailable-is-not-a-pass`; base `92b140db` (this branch
with `origin/agent/e15-solver-status-bit` merged in before any work — E-15 is
what makes `LpUnavailable` reachable at all, and what supplies the
`solver_options` the negative sample needs to drive a *real* solver limit).

Only `fuzzlab/` was written. `git diff --stat 92b140db HEAD -- engine-rig` is
empty (T8). No network, no `.env`, zero contact with the sealed pile. No
committed artifact was modified: every campaign ran under `--out` into this
directory.

Commits, in order:

| commit | what |
|---|---|
| `41e72b34` | the pre-registration and the before-measurement |
| `e1319503` | the fix: the catch, the taxonomy, the columns, `failures()` |
| `863e899d` | the counterfeit table, `minimize`'s cause axis, the docs |

`git merge-base --is-ancestor 41e72b34 e1319503` → true. The criteria in
`PREREGISTRATION.md` were on disk and committed before the fix existed and were
not edited afterwards; deviations are recorded below rather than by editing it.

---

## 1. What was actually wrong, measured before anything was changed

`before_probe.py` / `before.json`, run against unmodified `fuzzlab/`. 12
`jumpgraph` worlds, `lp_potential`, with the real `scipy.optimize.linprog`
starved to `maxiter=0` — a genuine HiGHS status 1, nothing stubbed:

| run | violated | raised | skipped | `invariant_worlds_evaluated`, each of 4 |
|---|---|---|---|---|
| normal | 0 | 0 | 28 | **5** |
| solver starved | 0 | **44** | 4 | **11** |

`finding.failures()` returned `[]` for the starved run.

The ticket's diagnosis was right and understated it. The defect is not only that
an unavailable solver looks like a pass — it is that **blinding the solver more
than doubled the coverage the battery reported**, 5 → 11. `skipped` is subtracted
from `invariant_worlds_evaluated`; `raised` is not. So the battery's honest
declines lower its coverage number and its blind spots raise it. Two campaign
artifacts side by side would have shown the starved run as the better-covered
one.

(11 and not 12: on one world HiGHS settles infeasibility in presolve and never
reaches its iteration budget, so that world is a genuine `no_linear_pagoda`. This
matters later — see §5.)

---

## 2. The four things the ticket asked for

### (1) `LpUnavailable` is a `skipped`, `cause="solver_unavailable"`, class `unavailable`

The full argument is `PREREGISTRATION.md` §1, written before the code. In short:

* **Not `violated`.** `violated` means the engine did something it says it does
  not do. An iteration limit is not the engine doing anything — under E-15,
  `LpUnavailable` *is* the engine refusing to launder a solver limit into a
  geometric fact. Filing it as a violation accuses the engine of the one
  behaviour E-15 was written to produce, and makes the gate red for something no
  engine change can clear. `test_finding_contract.py` states the rule against
  that in its own words: a gate whose failures are mostly false is a gate people
  learn to ignore.
* **Not a fourth `kind`.** `Finding.kind` is consumed by `campaign.py`,
  `mutation.py`, `minimize.py` and the archive, and every one of them branches on
  `SKIPPED` and treats everything else as evaluated. The *default* handling of an
  unrecognised fourth kind is therefore "counted as evaluated" — which is exactly
  the bug, reintroduced in every consumer not yet updated. A new kind buys a name
  and pays for it in silence.
* **`skipped` is right, and insufficient on its own.** "The property could not be
  evaluated here, with the reason" is literally what happened. But `skipped` was
  one integer over two questions with opposite answers, so the decision has three
  parts and the last two are what make the first honest: `cause` is a required
  keyword on `finding.skipped()`, every cause is declared in `CAUSE_CLASS`, and
  the classes are gated (§3).

I did not adopt the dispatcher's stated leaning on faith; it happens to be where
the argument lands, and the reasons above are mine. Where I did diverge is the
number of classes — see §4.

### (2) `failures()` — the code moved, not the docstring

`failures()` returns `VIOLATED + RAISED`. Both directions are argued in
`PREREGISTRATION.md` §2 and in the function's own docstring, as the ticket
required. The three facts that decided it:

* `raised` is `unexpected` **by construction**: every documented outcome in this
  battery is caught at its property and converted to a `skipped` with a cause, so
  an exception reaching `raised` is one nobody wrote a policy for. The word
  "unexpected" was load-bearing and the body was ignoring it.
* `raised` was **measured at zero** across all six engines before the widening
  (§6), so the gate cannot go red for a documented outcome.
* Narrowing the prose instead would have written *a crashing property is not a
  failure* into the contract of the same battery whose `test_finding_contract.py`
  records an incident where a dead reporting path turned every violation into a
  `raised` while "0 violations" stayed true.

**The fact that decided how much work this needed**: `failures()` had **zero
callers** anywhere in the repository. A function with a wider docstring than body
and no invocations is the worst of the three arrangements — nothing could observe
the discrepancy, and the first person to import it imports the prose. So it is
now *called*:
`test_battery.py::test_short_campaign_passes_the_gate_the_docstring_describes`,
per engine. Aligning a docstring with a function nobody invokes fixes a sentence,
not a gate.

`skipped` is still not a failure. A world nobody judged is not a world the engine
got wrong — that is the coverage column's question, and it has its own gate.

### (3) The coverage count separates them

`campaign.json`, per engine, three numbers not derivable from one another:

* `invariant_worlds_evaluated` — worlds the invariant judged (definition
  unchanged);
* `invariant_worlds_unavailable` — worlds not judged because a **tool** could not
  compute;
* `skips_by_cause` / `skips_by_cause_class` — `{invariant: {cause: n}}`, so
  `no_certificate` and `solver_unavailable` are separate integers.

Plus `totals.unavailable`, and a `unavail=` column in the per-engine console
line. `_tally_causes` keys the top-level roll-up **cause-class first**
(`unavailable.lp_potential.three_conditions_hold.solver_unavailable`), so
grepping one prefix is the whole audit.

"Checked and found nothing" is a non-zero `invariant_worlds_evaluated` with no
violation. "The solver could not compute" is a non-zero
`invariant_worlds_unavailable`. Different fields, and neither reconstructible
from the other. That is V-13's rule applied to the new entrance.

### (4) The negative sample, and the proof it does not idle

`fuzzlab/tests/test_solver_unavailable.py`, 7 tests. The lever is
`solver_options={"maxiter": 0}` passed to the **real** `linprog` through E-15's
own hook, injected at `props/lp_potential._solve` — fuzzlab's own seam, the one
the mutation battery uses, so `engine-rig` is untouched in fact and not only in
intent.

What is asserted, on the starved run: every invariant reports **0** worlds
evaluated; every invariant files at least one `solver_unavailable`; the skip
carries the `LpOutcome`'s `status`/`solver_status`/`decided`/`bound`/`margin`;
`failures()` is empty **and** no `violated` was filed (a solver limit must not
become a false accusation); and — the regression stated in the direction the
defect ran — the starved run's coverage is **strictly less** than the live run's,
where before the fix it was strictly greater.

`test_the_starved_solver_really_is_a_real_highs_limit` guards against the whole
file going vacuous: it asserts the outcomes are `status == "budget"`,
`solver_status == 1`, `decided is False`. If a scipy upgrade ever made `maxiter=0`
stop producing a real iteration limit, that test goes red instead of everything
quietly passing for the wrong reason.

**Non-vacuity** is `test_removing_the_catch_lets_the_starved_solver_through`:
`_skip_solver_unavailable` is rebound to re-raise, which is precisely the pre-fix
control flow (`except LpUnavailable: return <re-raises>` propagates). It asserts
the whole pathology returns — `raised > 0`, `unavailable == 0`, no
`solver_unavailable` in any cause row, and every invariant back to counting
worlds as evaluated — plus that `failures()` now catches it a second way. See
also §5 for the independent, wider version of this proof.

---

## 3. The answer to "did you hide it in another box"

The honest risk with `skipped` is that a number in an artifact that nothing
asserts on is a number nobody reads. Three things stand against it:

1. `invariant_worlds_unavailable` is its own column, not a share of `skipped`.
2. `test_battery.py::test_nothing_went_unjudged_because_a_tool_could_not_compute`
   requires it to be **zero** for every invariant of every engine. The class is
   gated, not filed.
3. That gate is **pre-registered as able to fail for a non-defect**. If HiGHS
   hits numerical difficulties on some future world it goes red, and no engine
   change will clear it. That is intended: it means the run did not measure what
   its coverage column claims, and the response is to look at the toolchain. It
   is deliberately not a `violated` — nobody is accused — which is why it is a
   separate test with its own message.

---

## 4. Deviation from the pre-registration: three classes, not two

`PREREGISTRATION.md` §1 promised `CAUSE_CLASS` would map each cause to
`declined` or `unavailable`. The implementation ships **three**: `declined`,
`budget`, `unavailable`. Recorded here rather than by editing the
pre-registration.

It was found while classifying the 20 existing `skipped` call sites. Several are
neither: `SWEEP_BUDGET`, `STATE_BUDGET`, the `cegis_miner` frontier-enumeration
bound and the oracle BFS budget are *this battery* declining to pay a cost, on a
threshold it chose in advance and can quote. They are facts about tooling rather
than about the world, so a two-class table puts them in `unavailable` — and they
fire routinely, which would make the `unavailable` gate red on a green tree from
day one. A gate that is red for a designed behaviour is a gate people learn to
ignore, which is the failure this item is trying not to commit.

**Does the third class weaken the gate?** It would, if `solver_unavailable` could
have been parked in `budget`. It cannot, and the distinction is stated in the
taxonomy: `budget` means *we chose not to pay*, `unavailable` means *nobody
knows*. The counterfeit table tests exactly that boundary —
`c-relabel-as-budget` files the solver limit as `sweep_budget`, keeping it out of
`declined` and out of the gate. It was **killed** by two tests. The third class
narrows what `unavailable` means without giving a solver failure anywhere else to
hide.

---

## 5. The counterfeit table — wider than the tests, on purpose

`counterfeits.py`, 17 injected defects against the new machinery, each applied in
a fresh subprocess and run against the V-21 gate set. `COUNTERFEITS.json`,
`COUNTERFEITS.stdout.txt`.

C-11's lesson is that N mutants matching N tests measures the tests. So the table
was written against the **code paths** — the catch, what it files, the taxonomy,
`failures()`, the three campaign columns — and **9 of the 17 had no dedicated
test written for them**.

**16 killed, 1 survivor.**

The survivor was `c-drop-the-outcome-payload`: file the skip, attribute it
correctly to the solver, and drop the `LpOutcome` payload. Every count stays
right. What is lost is the ability to tell status 1 (raise the budget) from 3
(the model is wrong) from 4 (go and look at the arithmetic) — an unavailability
that is attributable but not diagnosable.

It has been closed, and the record is explicit about the order: the assertion in
`test_a_starved_solver_is_attributable_not_merely_absent` carries a comment
saying it came *after* the survivor and did not predict it. Re-run in
`COUNTERFEITS-recheck.json`: killed, 1 failing test. The pre-registration
committed me to not retro-fitting a survivor with a test and presenting it as
foresight; closing the hole is fine, claiming I saw it coming is not.

**My pre-registered prediction was wrong.** I named
`c-relabel-as-no-certificate` — a solver failure filed as the engine's own
documented decline — as the one I expected to survive, since both are skips and
every column except `skips_by_cause` is identical between them. It was killed by
two tests. Wrong in the safe direction, and it is the strongest single piece of
evidence that the `cause` column is load-bearing rather than decorative:
`c-relabel-as-no-certificate`, `c-relabel-as-budget` and
`c-unavailable-is-declined` all leave the world correctly *skipped* and are all
caught anyway, purely on which cause was written down.

---

## 6. What was run, and the raw numbers

Everything below is post-review, against the corrected code. Raw output in
`campaign/campaign.json`, `campaign.stdout.txt`, `PYTEST.stdout.txt`,
`VERIFY.stdout.txt`, `COUNTERFEITS.json`, `COUNTERFEITS.stdout.txt`.

**`python -m pytest fuzzlab` → exit 0, 130 passed** (baseline at `92b140db`: 90).

**`python -m fuzzlab.campaign --worlds 500 --out …` → exit 0.** 3000 worlds, 26
invariants:

```
totals: violated 0, raised 0, skipped 1142, unavailable 0, generator_errors 0
```

| engine | evaluated / 500 | worlds skipped | unavailable |
|---|---|---|---|
| `mdl_segmenter` | 500 | 0 | 0 |
| `cegis_miner` | **465** | 35 | 0 |
| `zero_space` | 500 | 0 | 0 |
| `lp_potential` | **267** | 233 | 0 |
| `fd_adapter` | 500 | 0 | 0 |
| `probe_frontier` | 500 | 0 | 0 |

The two published coverage figures — `lp_potential` 267/500 and `cegis_miner`
465/500 — are **unchanged**, which is the check that this item added columns
without moving any existing reading. `raised == 0` across all six engines is the
measurement the `failures()` widening rests on (T7). Every `..._worlds_...` value
lies inside `[0, 500]`, which is the post-BLOCKER invariant. Grepping the
top-level `skips_by_cause` for the `unavailable.` prefix returns nothing — the
whole audit, as advertised.

Ten of the eighteen declared causes never fire on this corpus
(`certificate_error`, `bfs_budget`, `sweep_budget`, `no_state_list`,
`ground_bfs_budget`, `no_states`, `feature_sweep_over_budget`,
`frontier_size_over_budget`, `evidence_not_alignable`,
`effects_not_readable_as_translation`). They are reachable paths this corpus does
not reach, not dead code — the adversarial pass forced `frontier_size_over_budget`
by lowering its threshold, which is how the BLOCKER was found. Recorded because a
declared-and-never-observed cause is exactly the shape `certificate_error` had
when it was misclassified for a release.

**`python -m fuzzlab.verify` → exit 1.** Stages 1 and 2 (fuzzlab's tests, the
six-engine campaign smoke) are `ok`. Stage 3 — `engine-rig`'s own suite — fails,
for a reason that is not this item's and that this item may not touch. See §8.

---

## 7. Adversarial review — it overturned the arithmetic under the new column

`ADVERSARIAL.md`, verbatim as written, not edited. Its scratch scripts are in
`adversarial/`. Its headline is that (a) and (c) held — it could not find a box
the problem was hidden in, and it built both worlds itself and confirmed
`campaign.json` distinguishes them from the artifact alone — and that what it
broke was **the arithmetic underneath the new column**, plus a regression I had
shipped in `863e899d` and several sentences of mine that were wider than the code.

That last category is worth naming plainly: **this item shipped, twice, the
defect it exists to remove.** Finding 5 caught three docstrings claiming "the
suite fails on it" when only a 25-world pytest run did; finding 4 caught a help
string documenting the inverse of what the code did. In an item whose subject is
prose wider than code, that is not an irony to note and move past — it is
evidence that the discipline has to be a mechanism and not an intention.

### Disposition

| # | severity | finding | disposition |
|---|---|---|---|
| 1 | **BLOCKER** | `invariant_worlds_evaluated` / `invariant_worlds_unavailable` count skip **findings**, not worlds. Equal only while no property files two skips per world; `cegis_miner.frontier_is_complete_to_size` files one per rule, and with its budget forced low the column read **−56 of 12 worlds**. | **Accepted and fixed.** `campaign.py` now counts distinct seeds for every `..._worlds_...` column; `skips_by_cause` keeps counting findings and says so; `invariant_worlds_skipped` and `skip_worlds_by_cause_class` are published so the two quantities are visible side by side rather than assumed equal. The reviewer's own `adversarial/multiskip.py` now reports **0** where it reported −56. New counterfeit `c-worlds-columns-count-findings` restores the defect; killed. Note the bug predates V-21 — the `ran` expression is V-13's — but V-21 replicated its shape into a new column and asserted "worlds" in a docstring, so it is this item's to fix. |
| 2 | MAJOR | `test_the_skip_breakdown_reconciles_with_the_skip_count`'s second assertion was `x == x` (both sides re-derived from the same findings) and passed on the −56 report. | **Accepted and fixed.** Replaced with comparisons between quantities that are genuinely computed differently — findings against distinct seeds, plus range bounds. Added `test_many_skips_on_one_world_do_not_send_the_coverage_column_negative`, which drives eight skips per world per invariant through the real `run_engine`. |
| 3 | MAJOR | `certificate_error` is classified `declined`; by the taxonomy's own words it is `unavailable` — HiGHS returns status **0**, the rational snap then fails exact re-checking, and nobody knows whether a pagoda exists. | **Accepted and fixed.** Reclassified to `unavailable`, with the argument in `CAUSE_CLASS`. The reviewer is right and the point is sharp: *documented* is not the same as *a fact about the configuration*, and I had used the first to justify the second — the exact conflation this item removed one `except` clause below. It reads 0 on 500 worlds, so it was latent, which is precisely how the `LpUnavailable` hole sat until E-15 made it reachable. The reviewer's full 18-row audit of `CAUSE_CLASS` against call sites is in `ADVERSARIAL.md` §3; it found no other misfiling, and flags `evidence_not_alignable` / `effects_not_readable_as_translation` as grey rather than wrong. |
| 4 | MAJOR | I broke `minimize --kind skipped`: `signature()` became four-part for skips while `want` stayed three-part unless `--cause` was passed, so 13 reproducers in 25 seeds became **0**, and the help text documented the inverse. The committed archive's three-part signature could no longer be re-derived. | **Accepted and fixed.** A bare `--kind skipped` now matches any cause (prefix match), which is also its pre-V-21 meaning; `--cause` narrows. Help text corrected. Verified: the committed `cegis_miner.frontier_guards_are_consistent.skipped` reproducer re-derives, 3 hits in 25 seeds. |
| 5 | MAJOR | "gated, not merely filed" was true of a 25-world pytest run and false of the 500-world artifact: `campaign.main` exited 0 with every world unjudged, and `verify.py` printed the warning then printed `green`. | **Accepted, and fixed by moving the code rather than the prose.** `campaign.main` now exits non-zero on `totals.unavailable`, which carries the gate to the 500-world artifact and to `verify.py`. That is consistent with the exit code's stated meaning — it is about the instrument, not the reading, and a tool that did not compute is an instrument fault. A *violation* still exits 0. The three overclaiming docstrings were rewritten to describe both gates. New counterfeit `c-campaign-exit-ignores-unavailable`. |
| 6 | MAJOR | `mutation.py` was not updated: before V-21 an `LpUnavailable` under a mutant surfaced as `raised_only`; after, it is a skip, invisible, counted in `worlds_evaluated`, and printed as `SURVIVED`. The fix turned a weak signal into no signal. | **Accepted and fixed.** `run_mutant` drops worlds carrying an `unavailable` skip from the denominator and reports `worlds_unavailable` as its own column. No current mutant can raise `LpUnavailable`, so no published number moves — verified — and the hole is closed before the first one that can. |
| 7 | MAJOR | Three committed files pointed at a `RUN_STATE.md` that did not exist, reproducing `BUGS.md` incident R5 in the same directory in the same week. | **Accepted.** This file. It did not exist when the reviewer looked because it was written after the review was dispatched; that is an ordering mistake, not a disagreement — the references should not have been committed ahead of the target. |
| 8 | MAJOR | The two-class → three-class deviation had no deviation record, and `budget` is ungated, so the gate covers 1 cause of 18. | **Accepted; recorded in §4 above** (also written after the review was dispatched). The reviewer agrees the third class is right on the merits and says so. Its sharper point stands and is not fixed: `bfs_budget` is the *oracle* not deciding, routed away from the gate because the threshold was chosen in advance. That is a real narrowing and §4 now states it. Whether the oracle's own budget should be gated is a separate item, not this one. |
| 9 | MINOR | `failures()`'s widening rests on "every documented exception is caught at its property", asserted in three docstrings and enforced nowhere; no `ast` guard as there is for `cause`. | **Accepted, not fixed.** Correct and worth doing; it is a guard over `except` clauses rather than call sites and is a different shape of check from `test_finding_contract.py`'s. Filed here rather than attempted at the end of this item. The net that exists — `test_short_campaign_passes_the_gate_the_docstring_describes` — is real, which is why the reviewer rated it MINOR. |
| 10 | MINOR | `fuzzlab/out/` is schema-stale (pre-V-21) and `README.md` described fields absent from the only `campaign.json` in the repo. | **Accepted; fixed by documenting rather than regenerating.** The item's boundary forbids modifying committed artifacts, so `README.md` now says `out/` is a snapshot from whichever item last ran without `--out`, states exactly what it lacks, and points at this run's `campaign/`. |
| 11 | MINOR | Commit `863e899d` swept the reviewer's own scratch directory into the branch unread. | **Accepted, correct, and the mechanism is the one CLAUDE.md warns about one directory down.** The files are kept — they are the review's evidence and belong with it — but they were committed by `git add fuzzlab` without being read first, which is the hazard whether or not the contents turn out to be fine. |
| 12 | NIT | `test_a_starved_solver_judges_nothing`'s `== 0` would go red if a future scipy presolve ever *certified* a world at `maxiter=0`. | **Accepted, deliberately not weakened.** A solver certifying at zero iterations would be an anomaly worth a red test, and the comparison form the reviewer prefers already exists beside it in `test_blinding_the_solver_lowers_coverage_it_does_not_raise_it`. Keeping both is the point: one states the strong property, one states the robust one. |
| 13 | NIT | `data["lp_status"] == "budget"` sits beside `cause_class == "unavailable"` — two meanings of "budget" in one record, one of them the class the record is deliberately not in. | **Accepted and fixed.** Renamed to `highs_status_word`. |
| 14 | NIT | Nothing demonstrates the `unavailable` gate going red at 25 worlds on a natural run. | **Accepted, no change.** The gate is shown failing by the starved-solver tests and by two counterfeits; the reviewer calls the coverage adequate and raises it only against the gate docstring's wording. |

Nothing in the report was rejected. Five of the fourteen are defects I introduced
(1's replication, 2, 4, 5, 13); four are things I should have written down and had
not yet (7, 8, 11, and 10's caveat).

---

## 8. What is still open

* **Finding 9** — no `ast` guard that a documented engine exception is caught and
  converted rather than allowed to escape. The next documented exception can
  re-open V-21 at a new entrance; the 25-world `failures()` gate is the only
  thing that would notice.
* **Finding 8's residue** — `budget` is ungated, and `bfs_budget` in particular is
  the oracle not knowing. Defensible, stated, not resolved.
* **`fuzzlab/out/`** is schema-stale by design of this item's boundary. Whoever
  merges should regenerate it deliberately.
* **`python -m fuzzlab.verify` exits 1 on this branch, for a reason that is not
  mine.** Stage 3 runs `engine-rig`'s own suite, and 5 tests in
  `engine-rig/tests/test_heldout.py` fail with
  `TypeError: Law.__init__() got an unexpected keyword argument 'scope_exhaustive'`.
  This is a **semantic merge conflict between E-15 and E-17**, not a fuzzlab
  defect and not something this item may touch (house rule):

  | tree | `Law.scope_exhaustive` |
  |---|---|
  | `613e478f` (this branch before the merge) | a dataclass **field**, `scope_exhaustive: bool = True` |
  | `92b140db` (after merging `origin/agent/e15-solver-status-bit`) | a derived **property**, `def scope_exhaustive(self)` |

  E-17's `engine-rig/heldout/zero_space_heldout.py:80` constructs
  `Law(..., scope_exhaustive=not truncated)`. Git merged the two textually clean —
  they touch different files — and the result does not run. `engine-rig` alone:
  **5 failed, 548 passed, 27 skipped**, all five the same `TypeError`.
  `git diff --stat 92b140db HEAD -- engine-rig` is empty, so none of it is mine.
  fuzzlab's own two `verify` stages are `ok`. **Whoever merges E-15 into a tree
  containing E-17 inherits this**, and it should be its own ticket.
