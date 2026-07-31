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

---

# V-13 — the invariants added because V-10 measured the blind spots

V-10's cross-cut (`runs/20260728T152000Z-V10-fuzz-mutation-power/PUBLISHED_VS_AUDITED.md`)
counted the six engines' published payloads at **111 leaf fields**, of which 25
were asserted by an invariant, 22 were read only as an index or a gate, and
**64 had never been touched**. It ranked what to fix. V-13 did the top two, plus
the coverage-accounting item V-10 booked and did not do.

Three invariants were added, taking the battery from 23 to 26. Each has mutants,
because **an invariant no mutant has ever killed and the blank it replaced are
the same thing in evidence**. Every number below is measured.

Reproduce: `python -m fuzzlab.mutation --engine cegis_miner --worlds 40` and
`--engine probe_frontier`. Raw JSON in
`runs/20260728T161127Z-V13-audit-the-published-surface/partials/`.

## `cegis_miner.effects_agree_with_the_evidence`

The gap, in V-10's words: all four existing invariants audit **guards** — *when*
a rule fires. None read `Rule.effect` at all. So a rule set with perfect guards
and inverted effects passed the entire battery clean, and `effect.*` is five
published fields that `cold-start-a0/prime/probe_runner.py:72` consumes
mechanically.

Truth comes from `fuzzlab/oracles/motion.py`, which reads the world's rendered
frames and imports nothing from `engines`. The tempting source —
`transitions[i].effect` — is `cegis_miner` repeating `mdl_segmenter`'s
narration, so comparing against it would have certified that the miner agrees
with the segmenter while staying blind to both being wrong the same way. The
oracle is checked against `gridworld.Rules.step` end to end in
`tests/test_oracles.py` — 4455 transitions over 200 worlds, zero disagreement,
zero unreadable — which is a check the campaign itself cannot perform.

40 worlds, campaign seed `0x00005eedc1e4f002`, measured after the corpus repair
described at the end of this section (`out/mutation.cegis_miner.json`):

| mutant | kind | eval | inert | result |
|---|---|---|---|---|
| `cm-flip-effect-delta` | unsound | 37 | 3 | **killed 37/37**, first world 1 |
| `cm-effect-none-becomes-move` | unsound | 36 | 4 | **killed 34/36**, first world 1 |
| `cm-drift-effect-destination` | unsound | 18 | 22 | **killed 18/18**, first world 1 |
| `cm-lift-admits-a-wrong-direction` | unsound | 32 | 8 | **killed 32/32**, first world 1 |
| `cm-freeze-lifted-direction` | unsound | 34 | 6 | killed 34/34 — **but see below** |
| `cm-drop-effect-destination` | incomplete | 18 | 22 | **SURVIVED — predicted** |

A kill count below the evaluated count — `cm-effect-none-becomes-move` at 34 of
36, `cm-relabel-rule-action` at 37 of 39 — is the subject gate, not a miss: the
mutant applied on a world where the invariant filed a `skipped` because the
mined track could not be established as the mover. The two columns disagreeing
is the accounting working; before this round they could not disagree, because
there was no gate.

**`cm-freeze-lifted-direction` does not measure what its name suggests, and an
adversarial review caught it.** It pins a lifted rule's `effect.direction` to a
concrete compass name — but the engine **never emits one**: a census of 357
rules found `effect.direction` taking only `{None, "?dir"}`. So the mutant is
the sole thing that can reach `_claimed_delta`'s `if direction in DELTA` branch,
and what it measures is the invariant's handling of a malformed field, not the
semantics of the variable. The decisive experiment, reproduced here: **delete
those two lines and the mutant survives at eval=34, killed=0.**

`cm-lift-admits-a-wrong-direction` was added to test the path the engine
actually produces — `?dir` resolved per witness to `DELTA[action]`. It widens a
lifted rule's support to a transition where the mover did not move at all, which
`miner.py:_normalise` forbids by construction, and it **still dies with the
`in DELTA` branch deleted**. That is the one that licenses any claim about
lifted rules being audited.

`cm-drift-effect-destination` and `cm-drop-effect-destination` are inert on 23
of 40 because `effect.to` is populated only where every witness agrees on a
landing cell, which most multi-witness rules do not. The two share an inert set
exactly, so the difference between their outcomes is the difference between the
defects and not between the worlds they met.

The lifted class is what V-10 called the largest single hole: before V-13 no
invariant iterated `result.all_rules`, so the **35 lifted rules in a measured
224 published (15.6%)** were not a field left unread but an entire class of
candidate nobody had looked at — and lifted rules are the *most* wanted kind,
being the generalised `push(?dir)` a playbook wants. The mutant that shows the
hole is closed is `cm-lift-admits-a-wrong-direction`, for the reason given
above; `cm-freeze-lifted-direction` does not show it.

**`cm-drop-effect-destination` is the designed negative control.** `mine()`
populates `effect.to` only when every witness agrees on a landing cell, so
`to = None` is a documented refusal to claim; the invariant therefore asserts
against `to` only where the engine states one. Clearing it is a real omission
this invariant will not catch, it was pre-registered as a survivor, and it
survived. That is the measured size of the remaining gap rather than a sentence
claiming the gap is small.

**Why none of these kills is a tautology.** The V-10 adversarial pass caught
`cm-weaken-ground-guard` selecting its injection point with
`_fires_on(weaker) > support` — the very predicate its target invariant
evaluates — making its death circular. Every mutant above picks its target
**structurally** ("the first ground rule whose effect is a move", "the first
lifted rule"), none imports `oracles/motion.py`, and none asks whether the value
it writes would trip anything. What licenses the kills is the **baseline**: on
the clean tree the invariant returns nothing on every world it judges, so the
oracle and the engine already agree there, and the mutant is the only thing that
changed.

## `cegis_miner.rules_fire_on_the_action_they_name`

`action` was on V-10's unaudited list. `mine()` groups on
`(transition.action, effect.key())`, so a rule naming an action asserts the
whole group took it; a rule filed under the wrong one is a true statement about
the world attached to the wrong lever.

| mutant | kind | eval | inert | result |
|---|---|---|---|---|
| `cm-relabel-rule-action` | unsound | 39 | 1 | **killed 37/39**, first world 1 |

Deliberately kept apart from the effect mutants: a ground rule's `dy`/`dx` are
explicit, so re-filing it under another direction leaves
`effects_agree_with_the_evidence` reading exactly the same claim, and only the
action invariant can see it. The clean single-invariant attribution is the
evidence that the two are independent rather than one check written twice.

## `probe_frontier.costs_are_the_world's`

V-10 ranked this second and the reason survives contact: `value_bits_per_cost`
is this engine's whole output semantics — it exists to answer "which experiment
next" — and `cost` was read by exactly one invariant, as a **sort key only**.
`ranking_is_sound` asserts that `(-value, -entropy, cost, action)` ascends, and
a uniformly wrong cost still ascends.

| mutant | kind | eval | inert | result |
|---|---|---|---|---|
| `pf-flatten-reported-costs` | inconsistent | 35 | 5 | **killed 35/35** (V-10: survived) |
| `pf-scale-reported-costs` | inconsistent | 40 | 0 | **killed 40/40**, first world 1 |
| `pf-zero-cost-value-is-zero` | unsound | 11 | 29 | **killed 11/11** — survives the guard this invariant first shipped |

**This invariant shipped with a hole in it and a docstring saying otherwise.**
The zero-cost branch — `value` is `inf`, not a quotient — was excluded by an
`if expected > 0` guard while two docstrings said it was "checked below". 27.6%
of `hypset` worlds carry a free action, generated deliberately
(`worlds/hypset.py:21`: "Zero is not a hypothetical -- the ranking divides by
it"). `pf-zero-cost-value-is-zero` is the negative control for the repair:
against the shipped guard it **survives** at eval=11, against the fixed one it
is **killed 11/11**. Both measured. See `BUGS.md` § S7 R1.

`pf-flatten-reported-costs` was V-10's pre-registered expected survivor against
`ranking_is_sound`, and it survived: an engine silently degraded to cost-blind
entropy ranking, with `value_bits_per_cost` wrong for every non-unit-cost
action, invisible to a green campaign. Its `expect_kill` now names
`costs_are_the_world's` and it dies.

**`pf-scale-reported-costs` is the stronger of the two.** Scaling every cost by
a positive constant divides every `value` by that constant and preserves the
engine's own sort order *on every world*, so no ranking check could ever have
caught it on any input. A kill there is the cost comparison and nothing else.

## Two V-10 predictions this run refutes

1. **`cm-shrink-lifted-support` is no longer a survivor.** V-10 pre-registered
   it as one on the ground that "every invariant iterates `result.rules`, never
   `result.all_rules`, while `candidates()` publishes `all_rules`". V-13 moved
   `applicable_equals_support` to `all_rules` — `lift()` builds both sets as
   unions over members whose own two sets are equal, so the claim is exactly as
   true of a lifted rule and is published in the same `coverage` string — and
   the mutant now dies **34/34**. V-10's prediction was correct about the
   battery as it stood and is no longer true of it.

   Scope did **not** move uniformly, and each exception is a decision rather
   than an oversight: `guards_partition_the_evidence` must stay on `rules`,
   because a lifted rule covers exactly the transitions of the ground rules it
   collapses and mutual exclusion is therefore false of `all_rules` by
   construction; both `frontier_*` invariants must stay too, because a lifted
   guard's atoms carry the direction variable and evaluating `act==?dir` against
   a concrete action is not a question with an answer.

2. **`pf-flatten-reported-costs` is no longer a survivor**, as above.

`cm-empty-frontier` and `cm-truncation-alibi` remain survivors, exactly as V-10
predicted and for the reason it gave: `frontier_is_complete_to_size` opens with
`if rule.frontier_truncated or not rule.frontier: continue`, so both are exempt
by construction. V-13 did not touch that and does not claim to have.

## A corpus defect found by trying to file a false accusation

The first version of `effects_agree_with_the_evidence` reported **21 violations
across 60 worlds**. `fuzzlab/README.md` says to check the oracle before filing.
The oracle was right; the **subject** was wrong.

`transitions_from_segmentation` takes the track to mine as a parameter and falls
back to `seg.tracks[0]` — the segmenter's first component in raster order.
`props/cegis_miner.py:_mine` had always taken that fallback, and **21 of the 57
minable worlds were mining a static obstacle**. A rock yields one `blocked_<D>`
rule per action with `effect: none`, guards that are trivially mutually
exclusive and trivially complete: all four guard invariants pass, on a rule set
that says nothing ever happens. Those rules are *true of the rock*, so this is
not an engine defect. It is 37% of this engine's corpus not testing it — the
same shape of defect `worlds/gridworld.py:_place_obstacles` documents, where an
unsatisfiable acceptance test produced 0 obstacles in 3200 worlds and a fully
green campaign that certified nothing.

`_mine` now selects the track whose anchors match `oracles/motion.py`'s
pixel-derived mover trajectory, **and prefers the segmentation operator that
keeps the mover in one piece** — committing to the first operator that merely
mined *something* was the other half of the same defect. Over the standing 500-world
campaign the subject-unknown count falls **54 → 15**, the unminable count is
**unchanged at 20**, and all six invariants now report a uniform **465 of 500**.

That is *lower* than the 480/500 the four guard invariants used to claim, and
the drop is the finding: those 480 included worlds whose entire rule set was
`blocked_<D>` rules saying nothing ever happens. All six invariants are now
gated on the subject being established, because "I could not check this world"
and "I checked it and found nothing" must not be the same answer in one module
after this round spent a section removing exactly that from another
(`BUGS.md` § S7).

The remaining 15 are **not** this engine's fault and not the oracle's: in 14 of
them `mdl_segmenter` produces a track with the mover's exact bounding box whose
`anchors` list carries `None` on some frames. Written up as `BUGS.md` § S5.

The repair also moved the *older* mutants' denominators, which is the clearest
statement of what mining a rock was costing. Against `tracks[0]`,
`cm-drop-frontier-guard` and `cm-truncation-alibi` were inert on 16 of 40
worlds; against the mover they are inert on 7, because a rock's rule set rarely
has a rule with two frontier guards to drop. `cm-shrink-lifted-support` went
from 23 evaluated to 32 — a rock generates almost no lifted rules, having
nothing to generalise. Those nine or sixteen worlds were not measuring the
battery either, and no column said so.

**This is why a mutant is not a substitute for a real defect, and vice versa.**
A mutant proves an invariant *can* fire; only a real defect proves it fires *in
the right place*. Here the second kind of evidence arrived first, and reading
the 21 findings instead of counting them is what turned a bad invariant into a
corpus repair.

---

## V-21 · why the `lp_potential` catalogue was *not* extended

V-21 closed a hole in `props/lp_potential.py`: `LpUnavailable` — the engine
declining because HiGHS stopped without deciding — was caught nowhere, escaped as
a `raised`, and was counted as an evaluated world. The obvious reflex is a new
mutant. It would have been the wrong instrument, for two reasons that come
straight out of this file.

**A mutant must contradict something the engine claims.** Raising `LpUnavailable`
contradicts nothing: `lp_potential` is entitled to decline, and E-15 added the
exception precisely so that declining is *not* mistaken for an answer. An
injected behaviour no engine ever promised to avoid is not a defect, and an
invariant that lets it through is not weak — reporting it would produce the
confident, wrong bug report `BUGS.md` names as this battery's characteristic
failure. The section above says the same thing about the missing certificate, and
this is the same argument one status code over.

**`expect_kill` cannot express the property under test.** The defect V-21 fixed
does not change any invariant's verdict; both before and after, no invariant
returns `violated`. What changes is which *column* the world lands in —
`invariant_worlds_evaluated` against `skips_by_cause.solver_unavailable`. A
catalogue whose only verdict is "which invariants killed it" is blind to that by
construction, and the mutant would have been recorded as a survivor, meaning
nothing.

So the measurement went into a **counterfeit table** instead:
`runs/20260729T104608Z-V21-lp-unavailable-is-not-a-pass/counterfeits.py`. Same
method — inject a defect of known shape, see who notices — but the subject is the
classification machinery (`props/finding.py`, `campaign.py`, the catch itself)
rather than an engine's answer, and the observable is "does the V-21 gate go
red", not `expect_kill`. Results and survivors in `COUNTERFEITS.json` and that
directory's `RUN_STATE.md`.
