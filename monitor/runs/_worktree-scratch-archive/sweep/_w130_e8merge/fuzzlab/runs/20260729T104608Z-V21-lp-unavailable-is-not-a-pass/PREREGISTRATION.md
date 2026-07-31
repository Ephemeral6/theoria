# V21 — pre-registration

Written and committed **before** any change to `fuzzlab/props/`, `fuzzlab/campaign.py`
or `fuzzlab/tests/`. `git merge-base --is-ancestor <this commit> <the fix commit>`
is the check.

`before.json` / `before.stdout.txt` in this directory are a *measurement*, taken
first, on unmodified code. They are evidence, not criteria. The criteria are below.

---

## 0. What the measurement already showed, and it is worse than the ticket says

12 `jumpgraph` worlds, `lp_potential`:

| run | violated | raised | skipped | `invariant_worlds_evaluated` (each of 4) |
|---|---|---|---|---|
| normal | 0 | 0 | 28 | **5** |
| solver starved (`maxiter=0`, real HiGHS) | 0 | **44** | 4 | **11** |

`finding.failures()` returns `[]` for the starved run.

So the pathology is not merely "unavailable looks like a pass". **Starving the
solver of every iteration more than doubles the coverage the battery reports** —
5 → 11 — because `invariant_worlds_evaluated` subtracts `skipped` and only
`skipped`, and a `raised` world is counted as evaluated. The battery's honest
declines (`no_certificate`) lower the number; its blind spots raise it. That is
the coverage column running backwards.

(11 rather than 12: on one world HiGHS decides in presolve and never reaches its
iteration budget, so that world is genuinely `no_linear_pagoda`. Recorded so the
number is not mistaken for an off-by-one.)

---

## 1. The classification: `LpUnavailable` is a `skipped`, with a mandatory `cause`,
and `cause` is classified on a second axis

**Decision: `skipped`, `cause="solver_unavailable"`, cause-class `unavailable`.**

Not `violated`. `violated` is defined in `props/finding.py` as "the engine did
something it says it does not do". An iteration limit is not the engine doing
anything; under E15 the engine's `LpUnavailable` is the engine *refusing* to
launder a solver limit into a geometric fact. Filing that as a violation makes
the battery accuse an engine for the one behaviour this repo just paid an item to
get — and `BUGS.md` names the confident-wrong-bug-report as the failure mode this
battery is most exposed to. It would also make the gate red for something no
engine change can clear, and `tests/test_finding_contract.py` states the rule
against that in its own words: a gate whose failures are mostly false is a gate
people learn to ignore.

Not a fourth `kind`. `Finding.kind` is read by `campaign.py`, `mutation.py`,
`minimize.py`, the archive and `findings.jsonl`. Every one of those consumers
branches on `SKIPPED` and treats everything else as evaluated — so the *default*
handling of an unrecognised fourth kind is **"counted as evaluated"**, which is
the exact silence being removed. A new kind buys a name at the cost of
reintroducing the bug in every consumer that has not been updated yet.

`skipped` is the semantically correct bucket — "the property could not be
evaluated on this world, with the reason recorded" is literally what happened —
**and it is not sufficient on its own**, because `skipped` today is one
undifferentiated bucket in which "the engine legitimately declined" and "nobody
knows, the solver gave up" are the same integer. So the decision has three parts,
and the second and third are what make the first honest:

1. `finding.skipped(...)` gains a **required** `cause`, promoted from `data` to a
   first-class field of `Finding`. Required, not conventional: 6 of the 20
   existing `skipped` calls carried a `cause=` by convention and 14 did not, and
   a convention that is 30% adhered to is not a column anyone can read.
2. `finding.py` declares a taxonomy `CAUSE_CLASS` mapping each cause to
   **`declined`** (a fact about the configuration or the evidence — the property
   had nothing to judge and that is the correct state of the world) or
   **`unavailable`** (a fact about the tool, the budget or the arithmetic —
   nobody knows what the answer was). `solver_unavailable` is the first
   `unavailable`. `no_certificate` stays `declined`.
3. `campaign.json` reports both axes per invariant (§3), and a clean tree is
   **required to have zero `unavailable`** (§4, T5) — so the number is gated, not
   merely recorded.

The `unavailable` axis is the answer to "did you just hide it in another box".
`skipped` without it would be exactly that.

## 2. `failures()`: the code is widened, not the docstring

**Decision: `failures()` returns `VIOLATED + RAISED`, and the docstring is
rewritten to say precisely that and why.**

Both directions were live and both are argued, as the ticket requires.

*The case for narrowing the prose instead* — change the docstring to "violations
only", change no behaviour, zero risk of a spuriously red gate, one line. It is
the cheaper and safer edit, and if `raised` were routinely non-zero on a green
tree it would be the right one, because a gate that is red for documented
outcomes is worse than no gate.

*Why the code is widened anyway.* Three facts decide it:

* **`raised` is already `unexpected` by construction.** Every documented
  exception in this battery is caught at its property and converted to `skipped`
  — `NoSeparatingGuard`, `CertificateError`, `PddlError`, an unminable
  segmentation, and now `LpUnavailable`. What reaches `raised` is therefore, by
  the design of `props/`, an exception nobody wrote a policy for. The word
  "unexpected" in the docstring is load-bearing and the code was ignoring it.
* **It is measured, not assumed**: the normal 12-world run above has `raised: 0`,
  and the full-campaign artifact must confirm `raised == 0` across all six engines
  before this lands (§4, T7). Widening a gate whose input is already zero cannot
  make a green tree red for a non-defect.
* **The narrowing option ratifies this very item.** `test_finding_contract.py`
  records an incident where a dead reporting path turned every violation into a
  `raised` and the headline "0 violations" stayed true. Editing the docstring
  down would write "a crashing property is not a failure" into the contract on
  purpose, one file away from an item whose whole subject is a silent non-failure.

`failures()` has **zero callers** today — it is dead code with a wider docstring
than its body, which is the most dangerous arrangement, because the first person
to import it will import the prose. So widening it is not enough on its own: it
is **wired into the suite** (§4, T6), which is what turns the alignment from a
comment into a gate.

## 3. What `campaign.json` must be able to say

Per engine, per invariant, three numbers that cannot be reconstructed from each
other:

* `invariant_worlds_evaluated` — worlds the invariant actually judged (unchanged
  definition: worlds minus every skip);
* `invariant_worlds_unavailable` — worlds not judged because a tool could not
  compute (cause-class `unavailable`);
* `skips_by_cause` — the full `{invariant: {cause: n}}` breakdown, so
  `no_certificate` and `solver_unavailable` are separate integers and a new cause
  cannot be introduced without appearing here.

Plus `skips_by_cause_class` and a top-level `totals.unavailable`. "Checked and
found nothing" is `invariant_worlds_evaluated` with no violation; "the solver
could not compute" is a non-zero `invariant_worlds_unavailable`. Different
fields, different numbers, neither derivable from the other.

## 4. Criteria — each one passes or the item does not land

* **T1** Every `finding.skipped(...)` call site in `fuzzlab/props/` passes a
  non-empty `cause`, enforced by the signature (a missing `cause` is a
  `TypeError`) **and** by an `ast` guard over `props/*.py`, in the idiom of
  `test_finding_contract.py`.
* **T2** Every declared cause appears in `CAUSE_CLASS`; an undeclared cause
  raises. A test shows the guard failing on an undeclared cause.
* **T3** All four `lp_potential` invariants catch `LpUnavailable` and file
  `cause="solver_unavailable"` carrying the outcome's `status`, `solver_status`,
  `bound` and `margin`.
* **T4 (the negative sample)** With the real HiGHS starved to `maxiter=0` through
  E15's `solver_options`, injected at fuzzlab's own seam:
  - `invariant_worlds_evaluated[name] == 0` for all four — **no world is recorded
    as judged**;
  - `skips_by_cause[name]["solver_unavailable"] > 0`;
  - `invariant_worlds_unavailable[name] > 0`;
  - the starved run's evaluated count is **strictly less** than the live run's
    (pre-fix it was strictly *greater*: 11 vs 5).
* **T4′ (non-vacuity of T4)** With the catch removed — `_skip_solver_unavailable`
  rebound to re-raise, which is precisely the pre-fix control flow — the same
  starved run must reproduce the pathology: `raised > 0`,
  `invariant_worlds_evaluated[name] == worlds` for all four,
  `skips_by_cause` carrying no `solver_unavailable`. A test that cannot be made to
  fail is not a test, and this is the form of that proof.
* **T5** A clean short campaign has `invariant_worlds_unavailable == 0` for every
  invariant of every engine. **Pre-registered as able to go red for a non-defect**:
  if HiGHS ever hits numerical difficulties on a real world, this fails. That is
  intended and is the point — it means the run did not measure what it claimed
  to, and the correct response is to investigate the toolchain, not to lower the
  number.
* **T6** `failures()` is wired: the short campaign asserts `failures()` is empty,
  so a `raised` fails the suite.
* **T7** `python -m pytest fuzzlab -q` green (baseline: 90 passed) and
  `python -m fuzzlab.verify` exit 0; a full `--out`-redirected campaign has
  `totals.raised == 0` and `totals.violated == 0`.
* **T8** No byte of `engine-rig/` is modified by this item. `git diff --stat
  <base>..HEAD -- engine-rig` must be empty apart from the E15 merge brought in
  before work started.

## 5. Counterfeits — the surface must be wider than the tests

C11's lesson is that N mutants matching N tests measures nothing. So the
counterfeit table (`counterfeits.py`) is written to be **wider than the test
set**, and it includes shapes for which no test was written in advance. Survivors
are reported as survivors, in `RUN_STATE.md`, without being retro-fitted with a
test that makes them look predicted.

Recorded before running: I expect the cause-relabelling counterfeit
(`solver_unavailable` rewritten to `no_certificate`) to be the hardest, because
both are skips and every count except `skips_by_cause` is identical between them.
If it survives, that is a finding against §1 and must be written up as one.

The engine-seam mutant catalogue (`mutants/lp_potential.py`) is deliberately
**not** extended. `MUTATION.md` requires every mutant to carry a `claim` naming an
engine promise it breaks, and states that "a mutant that pushes worlds into
`skipped` has *unmeasured* them, not survived them". A mutant that raises
`LpUnavailable` breaks no engine promise — the engine is entitled to decline — so
it is inadmissible there by the catalogue's own rule, and `expect_kill` cannot
express "the `cause` column should differ". Forcing it in would corrupt the
mutant contract to get a number.

## 6. Boundaries

Only `fuzzlab/` is written. No network, no `.env`, zero contact with the sealed
pile. No committed artifact is overwritten: the campaign runs under `--out` into
this directory.
