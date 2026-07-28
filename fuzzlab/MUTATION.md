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
constructor refuses a mutant without it. Without this, "the battery caught it"
cannot be distinguished from writing mutants until one trips something. A kill
by an invariant nobody predicted is itself reported (`unexpected_kills`) — it
usually means the invariants are less independent than their docstrings claim.

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
experiment and it is not done here. Until it is, the honest form of the
conclusion is: **the campaign's size is justified by corpus diversity, not by
invariant sensitivity, and only the second half of that sentence has been
measured.**

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

*(Sections for the remaining five engines follow as their catalogues land.)*
