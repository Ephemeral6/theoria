# MUTATION — how much detection power the battery actually has

`BUGS.md` reports the campaign: 3000 worlds, six engines, 23 invariants, **0
violations**. It also says, in its own words, that the result "is real and it is
also weak", and lists three reasons. This file is about a fourth reason it does
not list, because nobody had measured it:

> An invariant that **can never fire** and an invariant that **is satisfied**
> produce the same line in `out/campaign.json`.

The campaign's number is a statement about the engines only to the extent that
the battery could have contradicted it. So: inject defects of known shape, and
see which invariants notice.

```bash
python -m fuzzlab.mutation                       # every engine, every mutant
python -m fuzzlab.mutation --engine zero_space
python -m fuzzlab.mutation --mutant zs-flip-law-value -v
python -m pytest fuzzlab/tests/test_mutation.py  # the harness's own negative control
```

Raw results: `out/mutation.<engine>.json`. Catalogues: `mutants/<engine>.py`.

---

## Where the defect goes, and why not into the engine

The house rule (`README.md`) is that `fuzzlab` never modifies `engine-rig`;
`rig.py` says the entire interaction is `sys.path`. A mutation harness that
edited engine source — or patched `sys.modules['engines.…']` and restored
afterwards — would break that rule in fact, because a crash mid-run leaves the
patched engine behind for whatever imports it next.

So the seam is **fuzzlab's own**. Every property module funnels its engine call
through one private helper (`props/zero_space.py:_analyse`,
`props/cegis_miner.py:_mine`, …), and the injection rebinds *that* attribute,
on the fuzzlab module, restoring it in a `finally`. The engine runs untouched
and returns its true answer; the lie is told between the engine and the
property.

That is the correct place for it regardless of the house rule. **What is under
test here is the property, not the engine.** A mutant is a claim of the form
*"suppose the engine had returned this instead"*, and a mutant that survives
means *"the property would not have noticed"*.

## What makes a mutant admissible

**It has to contradict something the engine actually claims.** Every `Mutant`
carries a `claim` field naming the promise it breaks and where that promise is
made; the constructor refuses a mutant without one. This is not paperwork. An
injected behaviour that no engine ever promised is not a defect, and an
invariant that lets it through is not weak — reporting it as a finding produces
a confident, wrong bug report, which `BUGS.md` names as the failure mode this
battery is most exposed to.

Three engines make this a live hazard rather than a hypothetical:

* **`lp_potential` is sound but incomplete** (`CLAUDE.md`). Failing to certify
  an unsolvable configuration is documented behaviour, not a bug. Only
  certifying a *solvable* one is a defect.
* **`fd_adapter` has three rungs** and `fd-satisficing` does not promise
  optimality. A non-optimal plan is a defect on one rung and correct on another.
* **`cegis_miner`** does not promise its guards are unique or minimal, so
  "different from what the oracle computed" is not by itself wrong.

## Three controls, because the obvious version of this measurement lies

**1. Expectations are pre-registered.** `expect_kill` lists the invariants that
*should* catch the mutant and is written before the driver runs; the
constructor refuses a mutant without it — or without `predicted_survivor=True`,
which pre-registers the opposite prediction for a mutant written specifically to
demonstrate a known blind spot. Without this, "the battery caught it" cannot be
distinguished from writing mutants until one trips something. A kill by an
invariant nobody predicted is itself reported (`unexpected_kills`) — it usually
means the invariants are less independent than their docstrings claim.

**What backs the word "before", and what does not.** The catalogues were written
and only then run, but they were untracked while both happened, so **there is no
commit ordering to appeal to, and the only evidence for "before" is this
sentence**; a reader should take it as an assertion, not a proof. That is the
same self-disclosure `worldgen/qc/PREREGISTERED_MUTANTS.md` makes about itself,
and an adversarial reviewer was right to raise it. `zs-drop-law` is the one
mutant marked **post-hoc** in its own `description`, because it was written after
`zero_space` had already been published as "0 survivors".

**2. Inert worlds leave the denominator.** A corruption is not always possible:
there is no law to drop from a world with no laws. `corrupt` raises
`mut.inert(reason)` in that case, and the driver also treats "applied but
changed nothing" as inert by comparing `repr` before and after. Counting those
worlds as *survived* is the easiest way to manufacture a frightening result —
the mutant never happened, and the invariant gets blamed for not seeing it.

A mutant that shadows a *method* rather than editing a field leaves the `repr`
identical, so it must call `mut.touched(result)`; otherwise it reads as inert on
every world and its invariant is silently left unmeasured while the table still
shows a row for it.

**3. `raised` is not `violated`.** `props/finding.py` keeps the three outcomes
apart and so does this. A mutant that makes a property *crash* has been detected
only in the weak sense that something went wrong: the report carries no
statement of *what*, and a battery whose kills are mostly crashes is one
refactor away from silence. Headline kills count `violated` only; crashes are
reported in a separate `raised_only` column.

**And the baseline runs first.** A world already violating an invariant with no
mutant applied cannot say anything about the mutant, and is dropped with a loud
note (`worlds_confounded`) rather than counted as a kill.

## The columns, and what each licenses

| column | what it is for |
|---|---|
| `killed` | the headline: worlds where the invariant returned `violated`. |
| `raised_only` | detection in the weak sense; see control 3. |
| `worlds_to_first_kill` | what licenses the campaign's **size**. Killing on world 1 means the standing 500 are not being spent on that invariant; needing 300 means 500 is a number it earned. Both are useful and they point opposite ways. |
| `worlds_inert` | worlds where the defect could not apply. Out of the denominator. |
| `worlds_confounded` | worlds already dirty at baseline. |

## What `worlds_to_first_kill` does **not** measure — stated before the results

Every kill recorded so far, across four engines, happened on the **first
evaluated world**, at a 100 % kill rate. The tempting reading is that the
standing campaign's 500 worlds are not being spent on invariant sensitivity.
That reading is half right and the other half is an artefact of how these
mutants are built, so it has to be said here rather than in a footnote.

**The mutants are unconditional.** `corrupt` fires on every world where the
defect can apply at all. A defect present in every world is, of course, seen in
the first one. So `worlds_to_first_kill = 1` means:

> *given* that the defect is present, one world is enough for the invariant to
> notice.

It does **not** mean 500 worlds are wasted. The thing 500 worlds buys is the
chance that a *rare structural condition* occurs at all — the obstacle-bearing
grid, the jumpgraph with a deep reachable set, the segmentation with a
disappearing object. G1–G4 in `BUGS.md` are exactly that story: the first
campaign was green because the corpus contained no obstacles, not because the
invariants were insensitive. A corpus-diversity failure and an invariant-
sensitivity failure are different failures, and **this experiment measures only
the second**.

Measuring the first needs *conditional* mutants — a defect injected only when
some rare structural predicate holds — so that `worlds_to_first_kill` becomes
the number of worlds needed to surface the condition. That is the natural next
experiment and it is not done here.

**And the adversarial pass showed the artefact is worse than the paragraph
above admits.** Several `corrupt` functions *search* for their injection point
using the invariant's own criterion for a violation — `zs-add-bogus-basis-vector`
walks features until it finds one the oracle says is outside the span, and then
inserts exactly that. The kill is then true **by construction**: the mutant was
built to be the thing the invariant looks for. Such a kill establishes that the
reporting path works end to end — which is not nothing, and is precisely what
caught `partition_matches_truth` — but it is **not** evidence about sensitivity
to a defect the engine would plausibly have.

So the honest form of the conclusion is narrower than "500 worlds are a luxury":

> Every invariant has a working detection path, demonstrated. **How sensitive
> each is to a realistic defect is not measured by this run**, and
> `worlds_to_first_kill = 1` is largely a property of how the mutants were
> written rather than of the invariants.

## `worlds_inert` turns out to measure something the campaign gets wrong

An unintended result, and the one with the most direct consequence for anything
that quotes the campaign.

`campaign.py`'s docstring lists three things the driver refuses to do. The third:

> **it does not count a world as covered unless an invariant actually ran on
> it.** `worlds_generated` and `worlds_checked` are reported separately, per
> engine, and they are allowed to differ.

The implementation computes it as `n_worlds` minus the number of `skipped`
findings that invariant emitted. That sees an invariant which *declares* it
cannot judge this world. It cannot see an invariant that simply returns.

All four `lp_potential` invariants open with a bare early exit —
`props/lp_potential.py:99-100, 131-132, 178, 214` — when the engine issued no
certificate:

```python
if cert is None:
    return []                       # no claim made; incompleteness is allowed
```

The comment is right: `lp_potential` is sound but incomplete, and declining to
certify is documented behaviour, not a defect. But the *bookkeeping* is wrong.
An invariant that returns an empty list because it checked and found nothing
wrong, and an invariant that returns an empty list because it never looked, are
the same value. So `out/campaign.json` reports:

```
lp_potential  checked=500  skipped=0
   certificate_implies_unreachable   500
   three_conditions_hold             500
   heuristic_is_admissible           500
   infinite_means_unreachable        500
```

— four invariants, each credited with 500 worlds of coverage.

**The mutation run measures the real figure without needing new instrumentation.**
A mutant whose defect can only be injected where a certificate exists raises
`mut.inert` everywhere else, so `worlds_inert` *is* the count of worlds on which
the invariant had nothing to say. For `lp_potential` that is roughly **46 % of
the corpus** (the per-engine partial reports 21 of 40 worlds carrying a
certificate; 108 of 200 on a wider sweep). `heuristic_is_admissible` is thinner
still — its comparison loop reaches only about 8 % of the states it walks.

So the honest restatement is:

> `lp_potential`'s four invariants are evaluated on ~270 of the standing 500
> worlds, not 500, and `campaign.json` cannot currently say so.

This is a defect in `fuzzlab`, not in any engine, and it is in this territory.
The fix is to replace each bare `return []` with a `finding.skipped(...)`
carrying its reason — which is what `finding.py` exists for and what the other
engines' properties already do. It is **not** applied here, deliberately: it
changes the campaign's published counts, so it belongs with a campaign re-run
and a superseding section in `BUGS.md`, not folded into a mutation item's diff
where nobody would look for it. Registered as follow-up rather than done
quietly.

The general form is worth stating because the same shape was found in six other
territories on the same day: **a silent no-op counted as coverage**. Here the
driver's own docstring promises exactly the guarantee the code does not deliver.

## The harness has its own negative control

The failure mode of a mutation harness is loud in the direction of *more*
findings: if injection silently stopped working, every mutant would be reported
as a survivor and the output would read as a devastating result about the
battery. So `tests/test_mutation.py` pins the machinery against the same
standard this repository applies elsewhere — a probe that cannot be shown
failing is a green light with nothing behind it. It checks that the seam is
restored after an exception in the body, that a no-op mutant is reported inert
rather than surviving, that `touched()` reaches the driver, that a mutant
missing `claim` or `expect_kill` is refused, and — the load-bearing one — that a
known defect produces a known verdict: baseline clean, exactly one named
invariant fires, and the other three do not.

---

## Results

### `zero_space` — 4 invariants, 5 mutants, 0 survivors

Every pre-registered prediction held; no unexpected kills.

| mutant | kind | invariants that fired | predicted |
|---|---|---|---|
| `zs-drop-basis-vector` | incomplete | `law_space_is_complete`, `rank_nullity` | ✓ both |
| `zs-add-bogus-basis-vector` | unsound | `law_space_is_complete`, `rank_nullity` | ✓ both |
| `zs-flip-law-value` | unsound | `laws_hold_on_trajectory` | ✓ and nothing else |
| `zs-bump-difference-rank` | inconsistent | `rank_nullity` | ✓ |
| `zs-contains-always-true` | unsound | `membership_agrees` | ✓ |

25 worlds, 0 inert, baseline clean. All four `zero_space` invariants are
load-bearing: each one has at least one defect that only it catches, and
`zs-flip-law-value` — a law that is still conserved but reports the wrong
constant — is caught by `laws_hold_on_trajectory` **alone**, which is the
sharpest evidence that soundness is being checked separately rather than
inferred from the completeness comparison.

**One check inside a live invariant is nevertheless dead.** `rank_nullity`'s
third branch reads

```python
if len(result.basis) != result.dimension:
```

and `ZeroSpaceResult.dimension` is `@property … return len(self.basis)`
(`engines/zero_space/zerospace.py`). The two sides are the same expression, so
the branch is false for every possible input — **not weak, unfalsifiable**. No
mutant can reach it and none was written to try. The invariant as a whole is
fine: its other two branches are killed by two different mutants. This is worth
recording because it is the shape the census in `V11` found across six other
territories — a verdict computed correctly and wired to nothing.

### All six engines

54 mutants over six engines, one catalogue per engine, run at 25–40 worlds each.
Baseline clean everywhere. Per-engine detail is in `runs/…/partials/`.

| engine | invariants | mutants | survivors | undetermined | invariants no mutant could kill |
|---|---|---|---|---|---|
| `mdl_segmenter` | 4 | 11 | 4 | 0 | none |
| `cegis_miner` | 4 | 8 | 3 | 0 | none |
| `zero_space` | 4 | 6 | 1 | 0 | none |
| `lp_potential` | 4 | 6 | 1 | 0 | none |
| `fd_adapter` | 3 | 6 | 1 | 1 | none |
| `probe_frontier` | 4 | 18 | 5 | 0 | none — **after the fix below** |
| **total** | **23** | **55** | **15** | **1** | |

**Two of these numbers were different an hour ago, and the corrections came
from the adversarial pass rather than from me.** Both are recorded in place
rather than silently absorbed, because a table that only ever moved in the
flattering direction is not evidence of anything. `runs/…/ADVERSARIAL-1.md` is
the reviewer's own report.

* **`zero_space` was published as "5 mutants, 0 survivors"** and read as the one
  fully-covered engine. It was a sampling result. The reviewer wrote a sixth
  mutant — drop one `Law`, leave `basis` untouched — and it survives 25/25,
  because `candidates()` publishes `result.laws` while the completeness
  invariant audits `result.basis`. I re-ran it independently and confirm the
  survival. `zero_space` has the same blind spot as the other three; it was
  hidden by which mutants happened to get written.
* **`fd_adapter` was published as "2 survivors"**, one of which had
  `worlds_evaluated = 0`. The reviewer found that `survived` did not require the
  mutant to have run at all, so a `corrupt` that never applied printed as
  `SURVIVED` — the most misleading row this tool could emit, since every row is
  an accusation. `undetermined` is now a separate column and the driver prints
  `UNDETERMINED (never ran)`. **The negative-control test that was supposed to
  catch exactly this did not**: `test_a_mutant_that_changes_nothing_is_inert_and_not_a_survivor`
  asserted the inert counts and never asserted `survived is False`. It passed
  while the property in its own name was false. Both are fixed and the test now
  asserts what it is called.

**Every one of the 23 invariants is killed by at least one mutant — now.** One
of them was not, before this run changed it, and that is the single most useful
thing the exercise produced.

#### `partition_matches_truth` could never have reported a violation

`props/probe_frontier.py:91` built its finding as

```python
finding.violated(ENGINE, "partition_matches_truth", world, detail,
                 action=action, engine=normalised, truth=expected)
```

and `finding.violated(engine, invariant, world, detail, **data)` has already
bound `engine` positionally. The call raises `TypeError: violated() got multiple
values for argument 'engine'`. **The only path that could report this invariant
could not report it**, for as long as the invariant has existed.

Nothing caught it, and the reasons are the whole point:

* the line runs only when the engine partitions *wrongly*, and it never did — so
  the defect was never executed;
* had it executed, `run_invariants` would have caught the `TypeError` and filed
  a `raised`. The battery would have reported a crash where it meant to report a
  violation, and **`BUGS.md`'s headline "0 violations" would have remained
  literally true** while a real engine defect went past;
* the campaign counted this invariant as checked on 500 worlds. It ran on 500
  worlds. It could not have said no on any of them.

Measured, before and after the one-word fix:

| | partition mutants killed | outcome |
|---|---|---|
| before | **0 / 4** | all four `raised` |
| after | **4 / 4** | first world, 100 % |

Fixed here — `fuzzlab` is this item's territory and the defect is `fuzzlab`'s,
not an engine's. A guard now refuses the shape by parsing the property modules
(`tests/test_finding_contract.py`), and the guard has its own negative control:
it reconstructs the pre-fix line and is required to see it.

#### The 15 survivors sort into six kinds of blindness

Each survivor was adjudicated by its analyst as either *the invariant is
insufficient* or *the mutant was not a real defect*, against the engine's
documented promises. Grouped by what they have in common:

**1. The battery audits less than the engine publishes.** Found independently on
**four** engines — three analysts who could not see each other's work, plus the
adversarial reviewer who found the fourth while trying to overturn the first
three: `mdl_segmenter`'s `Track.color` and `Segmentation.baseline_bits`,
`cegis_miner`'s lifted `all_rules` (four invariants iterate `result.rules`, while
`candidates()` publishes `all_rules`), `probe_frontier`'s `ProbeValue.partition`
and reported `cost`, and `zero_space`'s `result.laws` — the payload is built from
the laws, and the completeness invariant audits the basis. **These fields reach
`candidates.jsonl`, and from there the manual, and from there the LLM's beliefs
about the world** — carrying no evidence at all, seated next to fields that carry
some. This is the most consequential group and it was nobody's hypothesis going
in.

**Measured, once the pattern was visible.** The survivors said the gap exists;
a separate pass walked the whole publication surface and sized it
(`runs/…/PUBLISHED_VS_AUDITED.md`, audit side measured with an in-process
attribute-access recorder rather than by reading):

| | fields |
|---|---|
| leaf fields the six engines publish into the payload | **111** |
| asserted by at least one invariant | 25 |
| read only as an index, a gate, or inside an aggregate | 22 |
| **never audited by any invariant** | **64** |

The sharpest instance is not any of the survivors. **`cegis_miner` publishes
`effect.*` and no invariant has ever looked at it.** All four audit the *guard* —
when a rule fires — and none compares the rule's stated effect against what the
transition actually did. So a rule set with perfect guards and wrong effects
passes the entire battery cleanly, is published as causal law, and is consumed
mechanically downstream at `probe_runner.py:72`. On one 39-world sample the
engine published 224 rules, 35 of them lifted and outside every invariant's
reach.

One published field turns out to be **false rather than merely unaudited**:
`mdl_segmenter`'s `segment_operator` is written as a constant, so two
segmentations of the same world cutting 23 tracks and 6 tracks emit an identical
payload string naming the same operator.

**One qualification the adversarial pass forced, and it matters.** "Nobody
audits these" is too strong for `cegis_miner`: `engine-rig`'s own unit tests do
cover part of the lifted rule set. The precise claim is **`fuzzlab` does not
audit them**, and the distinction is not pedantic — `fuzzlab`'s house rule is
that an oracle may not call the engine it judges, and `engine-rig`'s tests are
under no such constraint. Coverage by a test that shares the engine's own
assumptions is worth less than coverage by an independent oracle, but it is not
zero, and reporting it as zero would be the same error this file warns about in
the other direction.

**2. The oracle shares machinery with the engine it judges.** `fd_adapter`'s
`_model` builds the oracle's truth table with the engine's own
`ground_actions()`. A deliberately-designed negative-control mutant
(`fd-shared-grounder-blind-spot`, 30 worlds evaluated, 0 kills) demonstrates the
consequence rather than asserting it: **detection power against any parse or
grounding defect is exactly zero**, because the oracle inherits the same
mistake. The house rule — an oracle may not call the engine it judges — is kept
at the *search* layer and not at the *grounding* layer. That is a defensible
trade (there is no independent grounder to hand) but it is currently unstated,
and `README.md`'s statement of the rule reads as though it were absolute.

**3. Same-source comparison.** `lp_potential`'s `three_conditions_hold` checks
`cert.weights` against `cert.moves` — both the engine's own report. A certificate
that omits a move which would raise the potential is invisible.

**4. A tolerance floor, now measured.** `probe_frontier`'s entropy invariant
uses an absolute `EPS = 1e-9`. Injected shifts of 1e-3, 1e-6 and 2e-9 are caught
100 %; 1e-9 is on the boundary and caught about two thirds of the time; 1e-12
and 1e-16 survive. The observed float noise floor is ~2.2e-16, so **the
threshold discards roughly seven orders of magnitude of available resolution**.
Whether that matters depends on what an entropy error of 1e-12 would mean for a
probe ranking — probably nothing — but the number was previously unknown and is
now on the record.

**5. Self-exempting clauses.** `cegis_miner` skips consistency checking when
`frontier_truncated` is set, and the flag is never itself verified: two mutants
injecting the *same* defect differ only in setting the flag, and go 16/16 → 0/16.

**6. One instrument artefact, not a blindness.** `fd-solve-seam-is-dead`
evaluated 0 worlds — `props/fd_adapter.py:_solve` is dead code, the three
invariants call the engine directly at lines 104/131/165. The mutant proves the
seam is unused; it says nothing about the battery. Reported as a survivor and
excluded from any count of blind spots, because conflating the two is how a
mutation score gets inflated.

#### `fd_adapter` has never been fuzzed on Fast Downward

Not a mutation result, but found while choosing the seam, and it limits every
`fd_adapter` row above. `props/fd_adapter.py` calls `engine.solve_parsed(domain,
problem)` with in-memory parsed objects, and `choose_tier`'s third clause
(`backends.py:152-154`) forces `stub-bfs` for exactly that case — *"Fast
Downward reads files and has no pruning hook, so this is a fact about the
backend rather than a choice."*

So the fall-back is **structural, not environmental**: it is not that this
machine lacks an FD build, it is that this call shape can never reach one.
Everything the campaign reports about `fd_adapter` is about the BFS stub. One
consequence runs the other way and is worth stating in the engine's favour: a
"returns a valid but non-optimal plan" mutant is a *real* defect here rather
than a false positive, because `stub-bfs` does promise optimality where
`fd-satisficing` would not.
