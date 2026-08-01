# U3 census — the denominator was hand-typed, and it was missing sixteen books

## What I was sent to do, and why I did something else

The ticket said **"U3 has no implementation anywhere in the repo"** and asked
for one. That is no longer true. `freeze/u3.py` (813 lines, 29 tests) landed at
`6c4a0bb2` on 2026-07-31 and merged to master at `5adf4fcd`; it implements E1
against the frozen §1.2/§1.2.1 wording, including the non-triviality gate and
the `generated_l1_vacuous` negative control the freeze list names as a blocker.
Building a second one in `exam/` would have been the exact scattering the
ticket warned against.

So I verified what exists instead — and the verification found real defects.

## The hole that is actually open

E1 answers *"did this directory attain U3"*. Nothing answers *"which
directories are there"*. The 2026-07-31 sweep was invoked with a **hand-written
list of paths**:

```
$ python freeze/u3.py sweep <theoria-arm/runs> a0-spike cold-start-a0 \
      cold-start-a3/theory/generated_l1{,_vacuous} --probe
```

Its denominator was therefore whatever the author remembered to type. **Sixteen
of the twenty-four Lean developments on disk were never put in front of the
adjudicator** — every book in `cold-start-a2/`, four more in
`cold-start-a3/theory/`, three under `cold-start-a3/runs/`, two more in
`cold-start-a0/`, all four handover packages, and the `theory-compiler` Lean.

`exam/u3_census.py` is the missing half and only that half:

```
discovery + enumeration  -> exam/u3_census.py
the U3 judgment itself   -> freeze/u3.py, imported, never reimplemented
```

Every verdict in `census.json` is the return value of a `freeze.u3` function.
`test_census_delegates_every_verdict_to_freeze_u3` stubs the adjudicator and
asserts the census's answer changes completely — a census that kept judging
when the adjudicator was replaced would be a fork of a frozen endpoint.

### Two discovery defects in `freeze/u3.py`, reported not patched

**D1 — `u3.evaluate()` only looks for `<dir>/theory.lean`.** A development
named `Level.lean` (four of them, in `theory-compiler/handover_packages/`) or
`A0.lean` or `corner.lean` returns `no_evidence`, which is indistinguishable
from *"there was no proof layer"*. That is a false negative on a **primary
endpoint**, and it shrinks numerator and denominator together, so the ratio
does not move and nothing looks wrong.

**D2 — `u3.expand_targets()` descends exactly one level.** The three books at
`cold-start-a3/runs/<run>/generated/<variant>/` are unreachable.

Both have regression tests that assert the defect is *still real*
(`test_level_lean_book_is_discovered`, `test_deeply_nested_book_is_discovered`).
If freeze/ fixes them those tests go red, which is the correct signal.
`freeze/` is not this territory's file; the ask belongs in `monitor/inbox/`.

## Finding F1 — E1's (c) gate keys on theorem NAMES, and calls the miss `vacuous`

`u3.classify_theorem` is a prefix matcher over theorem names
(`inv_*` → invariant, `unsolvable|goal_break|no_goal` → unsolvable,
`prune|deadlock` → prune, everything else → unknown). `u3.judge_nonvacuity`
has no implemented check for `prune` or `unknown` and **fails closed** on both.

Failing closed is the right safety direction. What it costs is the **label**:

> `"why": "no executable §1.2.1 check implemented for kind `unknown` — fails closed"`

…is reported as verdict label **`vacuous`** — the word §1.2.1 reserves for a
manual that proved a tautology. *"We have no checker for this shape"* and
*"this manual proved nothing"* are rendered identically. In a Phase 4 paper
that difference is the whole claim.

**The case that makes this urgent.** `theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/verify/`:

| criterion | result |
|---|---|
| (a) compiles | **pass** |
| (b) axioms | **pass** — all nine theorems report an *empty* axiom set |
| (c) non-vacuous | **FAIL** — all nine, `kind: unknown`, "no executable check … fails closed" |

The file carries its own non-vacuity witnesses in source: `pat_witness` (a
well-formed state the pattern accepts) and `level_is_winnable` (a plan from
`s0` to a goal, so `dead` is a statement about the pattern and not about a
level lost from the start). And `STATS_RULES.md:123` names *this development*
as the paradigm of what U3 means:

> 它产出的、跨 28,672 个状态的死锁定理正是 U3 所指的那类非平凡定理

E1 labels it vacuous. Renaming its theorems `deadlock_*` would not help — the
`prune` kind fails closed too. **As E1 stands, a deadlock theorem can never
attain U3, whatever it proves.**

`test_FINDING_renaming_the_theorems_alone_flips_the_verdict` reduces this to
one fixture pair: the same manual, same definitions, same proofs, same axiom
sets, `inv_*` renamed to `frobnicate_*`. One attains; the other is `vacuous`.

**Risk to the sealed campaign.** If the arm's theorems are named outside the
matcher's prefixes, E1 reports U3 = 0/19 and the paper says the manuals were
vacuous. That is a naming-convention dependency in primary endpoint one.

`census.json → kind_coverage.kinds_that_can_never_attain` is the standing
instrument for this. Today: `["unknown"]`, 24 theorems, 0 ever passing (c).

## Finding F2 — the `unsolvable` (c) check has never once said yes

| kind | theorems seen | (c) passed | check implemented |
|---|---|---|---|
| `invariant` | 50 | 41 | yes |
| `unsolvable` | 14 | **0** | yes |
| `unknown` | 24 | 0 | **no — fails closed** |

Every one of the fourteen attainments on disk came through an `invariant`-kind
theorem. The `unsolvable` sub-checks (c) and (d) require `trace_transitions > 0`
and a `solvable_witness` **from the run record**, which a bare Lean book never
carries — so for a book on disk, unsolvable-kind theorems always fail. This is
not obviously wrong (the frozen text does want run evidence) but a check with
a 0/14 yes-rate deserves to be seen before 开跑, not after.

## Finding F3 — a book-only census flatters itself

The four live carried legs of 2026-07-31 have `certify.json` and **no `.lean`**.
A census that only enumerates books cannot see them, so an arm that stops
emitting manuals makes the attainment rate go *up*. `discover_claimants` adds a
second pass over certify-bearing run dirs with **its own denominator**; the two
are never folded, because "no book" and "a book proving a tautology" fail U3
for different reasons. Three tests hold that line.

## The numbers, with their denominators attached

**Books: 14 / 24 attained.** `discharged 14, vacuous 9, failing_obligation 1`.

**Runs that reached certify with no book: 15, of which 0 attained.**
`no_evidence 8, declared_refusal 6, no_proof_layer 1` — including all four of
today's live legs, every one `declared_refusal`.

> Neither number is `STATS_RULES.md` §1.2's rate. §1.2's denominator is fixed
> at 19 sealed games (12 clean), with no exclusions and no cap. **Nothing on
> disk today is a sealed game**, so the frozen rate is not computable from this
> census, and `attainment_rate()` carries that sentence inside the JSON so it
> travels with the number.

**For Phase 3's exit condition (U3 达成 ≥ k 局): still 0.** No live arm run has
reached the proof layer. The fourteen attainments are cold-start material —
synthetic worlds with discharged Lean proofs. They prove the evaluator's
positive path works; they are not a dev-pile game.

One thing did move since the 2026-07-31 sweep, which had noted *"re-run after
the legs finish"*: `20260731T1500Z-A3-sk48-carried-l1` read `no_proof_layer`
then and reads `declared_refusal` now. The leg finished.

## Negative controls

The ticket asked for two. There are seven, because a check never seen to say no
has not been shown to check anything.

| control | must | result |
|---|---|---|
| tautology manual (`def I _ := true`) | NOT attain | `vacuous` ✓ |
| real discharged obligation | attain | `discharged` ✓ |
| the pair differs only in `I` | (a),(b) identical both sides | ✓ |
| all-`sorry` manual | NOT attain | `axiom_violation` ✓ |
| `generated_l1_vacuous` on disk | NOT attain | `vacuous` ✓ |
| `Level.lean` book | be discovered, not `no_evidence` | ✓ |
| adjudicator stubbed out | census answer changes completely | ✓ |

Two notes on making the controls honest:

* **Sorrying one theorem is not a control for (b).** §1.2 asks for *at least
  one* machine-checkable theorem, so a manual with one hole and two clean
  proofs still attains — correctly. `SORRIED_MANUAL` holes every theorem.
* **The negative control alone proves nothing.** A (c) check that rejected
  everything would pass it. That is what the positive control is for, and
  `test_the_two_controls_differ_only_in_the_invariant` asserts (a) and (b) are
  identical across the pair so the verdict difference can only come from (c).

The kind-coverage table caught a bug in my own code while I wrote it: it read
`per_theorem` from the row instead of from `row["criteria"]`, returned `{}`,
and rendered as *"no kind is unreachable"* — a clean bill of health produced by
a lookup miss. The test asserts on a **populated** table, not on the absence of
problems.

## Gates

* `exam` suite: 510 passed, 2 xfailed (baseline was 489 + 2; +21 new).
* `python -m exam.verify`: GREEN.
* Full census wall-clock: 4m47s (Lean 4.9.0 compiles every book).

## Residual gaps, stated plainly

* **F1 is reported, not fixed.** The fix — a distinct `unclassified` label, or
  a (c) check for the prune/deadlock kind — belongs to `freeze/`. Until then
  `vacuous` in any E1 output may mean either thing, and `kind_coverage` is the
  only way to tell which.
* **D1/D2 are reported, not patched**, for the same territory reason. The
  census routes around them; `freeze/u3.py`'s own `sweep` still cannot reach
  those books.
* **`--probe` was not used for the archived census.** Verdicts rest on the
  static `def I` / `def Goal` constancy scan, so every row carries
  `"constancy probe not run (static scan only)"` in `c_residuals`. The probe
  path is implemented in `freeze/u3.py` and exercised by its own tests; it is
  substantially slower and was not needed for the findings here. A pre-开跑
  census should run with `--probe`.
* **§1.2.1's full two-witness predicate is still deferred** — `freeze/u3.py`'s
  own §9.2 residual, unchanged by this work. A syntactically disguised constant
  invariant would still pass (c). Carried in `c_residuals` on every row, never
  silently dropped.
* **The census counts directories, not games.** §1.2 counts games. The two
  never meet in this file and must not be made to.
* **Zero sealed-pile contact.** Every book adjudicated is a synthetic
  cold-start world or a dev-pile artefact; no sealed game id appears in
  anything written here.
