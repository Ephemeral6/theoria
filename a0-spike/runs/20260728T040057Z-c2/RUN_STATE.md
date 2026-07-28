# C2 · a0-spike, dsl_grammar v0.1 → v0.2 — run state

**Run** `20260728T040057Z-c2` · **prompt** `C2-semantics-migrate` ·
**branch** `agent/c2-semantics-migrate` · **measured on** `3205992` ·
**base_commit** `d55f072`

The run id keeps its opening timestamp. The branch was fast-forwarded from
`c47366c` to `3205992` early, and every number below was measured there. Master
then gained ten monitor/ops commits while this ran and was merged in, which is
why `base_commit` is a merge and not `3205992`. `git diff 3205992 e182c95 --
a0-spike/ theory-compiler/ CONTRACTS/` is **empty**, so none of those commits can
touch these numbers — but all three gates were re-run green on the merged tree
anyway rather than argued about, which is the cross-track integration check both
OPS-M and FINDING-6 say nothing else performs.

The plan this executed is `PLAN.md`, written at the opening of the run. It was
followed, with one change of method recorded as FINDING-2 and one self-caught
error recorded as FINDING-3b.

## Outcome

**Green.** `python -m pytest` → **44 passed, 0 failed, 0 error** (was 32
FAILED/ERROR, 6 passed). `python -m pipeline.run_a0` → exit 0, all four forms
regenerated, certify and the held-out check clean:

```
certify   1966 transitions replayed; exactly-one-successor=True, exact=True
certify*  1966 frames replayed through theory.dsl -> theory_exec.py; exact=True
held-out  39960 unobserved-inclusive states across 5 levels; mismatches=0
lean      compiles; sorry=False; axioms=[propext, Quot.sound]
lean=py   9408/9408 cases agree
prove     (box.row + box.col) mod 2 = 0  (conserved: True)
grade match     solvable predicted=True  actual=True  optimal_plan=True
grade mismatch  solvable predicted=False actual=False optimal_plan=True
```

## What was adjudicated

`theory/theory.dsl` gained a `semantics:` section declaring, for **this** world:

| statement | value | refuted alternative, on the cases that discriminate |
|---|---|---|
| `frame` | `persist` | `persist`-only wrong **0**; `reset`-only wrong **45,630** |
| `conflict` | `exclusive` | max rules claiming one object = **1** over all **47,040** pairs, both strata — and entailed level-independently by a 12-row truth table (T-11b) |
| `cascade` | `single_frame` | `single_frame`-only wrong **0**; `multi_frame`-only wrong **27,030** |

Full reasoning, both discharge routes for `conflict`, and the one place the
`cascade` refutation depends on a reading: `../../THEORIZE_LOG.md` **T-11**.
Machine output: `semantics_probe.json` (it attests *this* manual —
`section_supplied_by_probe: false`). Adversarial review of all three, filed
unedited: `ADVERSARIAL_REVIEW.md`. It confirmed all three values against the
world and landed four hits on the *evidence*, all accepted and acted on; the
header of that file lists what changed as a result.

These are the same three values `A0` and `A2` declare. v0.2's migration note
forbids copying them, so they were measured instead; T-11 is the difference.

## Findings

### FINDING-1 · The mechanical migration would have compiled a different world

The three-line fix does **not** produce a green tree. Measured, by putting the
migrated v0.2 manual through the pre-existing `gen_exec` (`git checkout HEAD --
a0-spike/pipeline/gen_exec.py`, everything else held):

```
27 FAILED/ERROR
RuntimeError: ambiguous successor for LEFT: ['push2','blocked_box_crossing','blocked_box_landing']
RuntimeError: ambiguous successor for UP: []
```

**Cause.** Under v0.2 a negated guard clause carries `negated` on the
`GuardPredicate` (E-01, revision item 2). Under v0.1 the parser folded it into a
`NameRef` holding the literal text `"not free(...)"`, and `gen_exec` read only
`clause.expr`. When the parser moved, nothing broke loudly — **the negation
simply stopped arriving**, and every `not` in the manual compiled to its own
opposite. `blocked_wall` became "the way ahead is clear **and** the box is there",
an unsatisfiable guard where the manual had written the exact complement.

Note what those two RuntimeErrors are: a manual that has just declared
`conflict exclusive`, whose compiled form both fires three rules at once *and*
fires none at all. The declaration and the artefact contradicted each other on
the first run. That is the whole argument for the section, arriving unprompted.

**Fixed** in `pipeline/gen_exec.py`: `_compile_clause` is the single place allowed
to read `negated`, and a clause arriving without the attribute is a hard error
rather than a default of `False` — a parser too old to carry the negation must
stop the build, not quietly compile a different world.

### FINDING-2 · The probe's state set was narrower than the contract asks, and widening it found 52

v0.2 §"Discharging `conflict`" route 2 is a sweep over **every state the level can
represent, not the reachable ones** (D-TC-012). The probe as first written
excluded states with an object standing on a wall — 7,080 of 47,040 pairs. That
exclusion was a reachability argument in disguise, which is the thing D-TC-012
forbids, so the sweep was widened to the full set.

Widening changed the `conflict` result **for the better**: max claimants stays 1
on the on-wall stratum too, so the discharge is now **unconditional** rather than
relative to an undeclared well-formedness condition. Under v0.2 a conditional
discharge is simultaneously a defect report; this one is not conditional.

Widening also surfaced **52 states where the manual mispredicts**, all of one
shape: **the box standing on a wall cell**. The world blocks the player at the
wall before it ever reaches the push branch (`world/sokoban2.py:142`); the manual
sees a box ahead and pushes it. Example — `match`, player (0,5), box (1,5), DOWN:
world leaves everything where it is, manual slides the box to (3,5) and the player
to (1,5).

**I then got the disposition of those 52 wrong, and the adversarial review caught
it.** My first account said they were excluded from the `frame` and `cascade`
verdicts because `render` paints the object over the wall, so such a state has no
frame of its own and there is nothing there for the manual to be wrong about.
**That is false.** Within one level the wall set is fixed and `render` writes
PLAYER and BOX at one cell each, so the map from representable states to frames is
injective — re-verified independently: **2,352 states of `match`, 2,352 distinct
frames, 0 collisions**. What the frame hides is the *wall*, which is level-static
data the compiled module already holds in `WALLS`. The states are observable, and
the manual really is wrong about them. It was a reachability argument wearing an
observability costume — T-9's own error, committed three paragraphs after citing
T-9 against it.

**The fix was to stop excluding anything and change the verdict rule instead.** A
statement is now adjudicated on the cases that **discriminate** between its two
readings: `persist`-only wrong **0**, `reset`-only wrong **45,630**;
`single_frame`-only wrong **0**, `multi_frame`-only wrong **27,030**. The 52 fall
out because *both* readings mispredict them, identically — re-verified, 52 of 52
agree — so they are evidence about neither statement. That is the property that
was wanted all along, and unlike a stratum filter it cannot be tuned.

What the 52 actually are is a **`push2` guard defect**, ledger **X-5**, and it is
not fixable in the v1 guard language: `free(Box.pos)` compiles to
`_free(state, state.box)`, unconditionally false, so no guard can say "the Box is
not on a wall". In v0.2's vocabulary this makes the `frame`/`cascade` discharge
**conditional on a well-formedness condition the manual does not declare**, which
§"Discharging `conflict`" says is simultaneously a defect report. Recorded as one.

`conflict` is unaffected and stays unconditional: it is a claim about the rule
set rather than about what succeeds what, so it is asked over all 47,040 pairs and
answered on all of them. Route 1 makes it level-independent besides (T-11b).

The counts are **reported, not filtered** — `semantics_probe.json` carries
`both_wrong`, the per-stratum breakdown, and eight witnesses. "Excluded as
non-discriminating" and "excluded because it would have failed" are the same
arithmetic and must not be allowed to become the same sentence; the first is
checkable from the JSON, which is the point of printing it.

### FINDING-3 · a0-spike's backends did not read the section they now require

Before this run, `grep -rn semantics a0-spike/pipeline/` returned **nothing**. The
migration would have satisfied the parser and changed no generated byte — which is
v0.2 revision item 10's hazard exactly ("declaring the fact buys nothing if a
generator reads the declaration and encodes a different world anyway"), the same
defect `gen_pddl` was caught in while v0.2 was being finalised.

`gen_exec._check_semantics` now refuses any declared value it does not implement,
naming the value; three negative tests cover `frame reset`, `conflict priority:`
and `cascade multi_frame`.

The adversarial review found the second half of this: the *generated* `step()`
declared `exclusive` and did not enforce it. It compared successors and let two
rules through whenever they happened to agree — which reads like enforcement,
passes every test while the guards really are disjoint, and stops being true the
moment a rule is added. Demonstrated by splicing a duplicate rule into `RULES`:
two rules fired, no exception. `step` now raises on more than one rule firing
regardless of agreement, and distinguishes "none fired" from "several fired" (the
old code reported both as `ambiguous successor`). Pinned by a test.

The residue is ledger **X-2**: `pddl_gen` builds its
domain from level data and `artifacts/A0.lean` is checked in rather than
generated, so neither reads the manual and neither can be guarded. That is the
honest scope of "四形态同源" in this directory and it is recorded, not papered over.

### FINDING-3b · I cited another directory's ledger as this one's, and it was wrong

Caught after the first commit, while trying to *close* X-3. T-11a and X-3 both
said `frame persist` lets a0-spike drop "the eleven `*_still_*` no-op rules R-07
rejected". **a0-spike has no R-07** — its log runs T-1…T-11 with no R-series. The
claim came from `cold-start-a0/proposals/dsl_grammar_v0.2_semantics.md`, which
describes *`cold-start-a0`'s* ledger, and I carried it across without checking it
transfers. A migration entry about not assuming another manual's facts, resting
on another manual's fact.

The correction is worth more than the error. In a0-spike the three `blocked_*`
rules emit `stayed(Player)` and are the **only** rules covering their guard
region, so they are what makes the rule set total. Measured — strip them, compile,
and `step` raises `no rule fired for UP ... the rule set is not total`. The frame
axiom retires a clause only when *some other rule already fires* and merely fails
to mention the object; it has nothing to say when no rule fires at all.
cold-start-a0's eleven were redundant in the first sense; a0-spike's three are
load-bearing in the second. Same axiom, opposite consequence.

X-3 is rewritten around the real obligation — "for each rule whose event writes
nothing, is its guard region covered by another rule?" — which is sharper than
what it replaced and is something `certify` already has the machinery for. Both
the error and the correction are left visible in T-11a rather than edited out.

### FINDING-4 · `find_lean` reported a hard failure where a working Lean was one directory away

`elan` installs a shim named `lean` on PATH which dispatches to the configured
default toolchain. With toolchains installed and **no default set** — this
machine — the shim is on PATH, is executable, and fails every invocation with
`no default toolchain configured`. `shutil.which` cannot tell that apart from a
working binary, so `find_lean` returned it and the Lean stage raised
`RuntimeError` where the two honest answers were a working Lean (there was one,
under `~/.elan/toolchains/`) or a clean skip. Presence was never the right
question; `find_lean` now asks the binary. No global toolchain state was changed.

### FINDING-5 · a0-spike had no `.gitattributes`, and its artefacts churn under autocrlf

`core.autocrlf=true` here. `theory_exec.py`, `domain.pddl` and
`problem_match.pddl` showed as `M` in `git status` with an **empty** `git diff`
after regeneration — a pure line-ending translation. CLAUDE.md makes
byte-reproducibility a requirement and `engine-rig/.gitattributes` exists for this
exact reason; a0-spike simply never got one. Added, same line, same reason.

With it in place the four forms regenerate byte-identically. The **only** content
change across the whole regeneration is one field of `a0_report.json`: the
absolute path of the Lean binary that ran. That field is machine-dependent and is
ledger **X-4** — recorded, not fixed, because changing it is a schema decision.

### FINDING-7 · The manifest pinned bytes no checkout would ever reproduce

Found by checking rather than by anything failing. `MANIFEST.json` digests the
files it lists; built naively it digests the **working copy**, and on Windows
with `core.autocrlf=true` the working copy is CRLF while git stores LF. **7 of 19
entries did not match the committed blob** — `THEORIZE_LOG.md` at 28,453 bytes in
the manifest against 28,005 committed, and six more. Nothing reported it: both
files were perfectly valid, and the mismatch is invisible unless you compare the
digest to `git show`.

That is worse than having no manifest. Its whole job is to let a later reader
confirm the artefacts are the ones the run measured, and a digest that no clone
can reproduce answers a question nobody asked while looking exactly like
verification. It is also the same root cause as FINDING-5 one layer up, which is
why `.gitattributes` alone was not enough: that fixes what *checkout* writes, not
what an editor writes afterwards.

Fixed twice over — the working tree is normalised to LF (no content changed; `git
diff --numstat` is empty across all 22 files) and `make_manifest.py --verify`
now compares every recorded digest against `git show :<path>`, so the failure
mode is detectable instead of merely absent today:

```bash
python runs/20260728T040057Z-c2/make_manifest.py --verify   # 19 files; 0 mismatched
```

### FINDING-6 · The gate that would have caught this does not exist, confirmed a second time

OPS-M's conflict note ends with an instrument observation for monitoring:
`monitor/ci_merge.py` runs the tests for *the directories a branch touched*, no
branch had touched `a0-spike`, so nine branches merged green onto a tree with two
red directories. This run is the second data point and it is the same shape from
the other side: **a0-spike was red on master for an unknown number of commits and
nothing reported it**, because nothing runs the whole suite on the merged tree.

Worth adding to the record because the two data points differ in an informative
way. OPS-M found it by hand-running after a merge wave. I found it because a
dispatch pointed me at it. Neither is a gate. The cheap version is not a new
harness: it is `python -m pytest` in each track directory, on master, on a timer —
this run's entire root cause would have surfaced the first time it fired, and
FINDING-1 says the tree would have stayed red under the obvious three-line fix,
so a *periodic* gate would also have caught the naive repair that a per-branch
gate waves through.

## Reproducing

```bash
cd a0-spike
python -m probes.semantics_probe --out runs/20260728T040057Z-c2   # the adjudication
python -m pytest -q                                              # 44 passed
python -m pipeline.run_a0                                        # four forms + certify
python runs/20260728T040057Z-c2/make_manifest.py --verify        # 19 files, 0 mismatched
```

All four exit 0, and `semantics_probe` exits non-zero unless every one of the
three statements is decided — so a green run of it is the adjudication holding,
not merely the script finishing.

`probes/semantics_probe.py` uses ground truth only to grade, never to predict —
the standing rule in `pipeline/stages.py`. It is deterministic; no seed, no clock,
no network.

## Not done, and why

* **X-1 (compound `slid`)** and **X-2 (two forms not derived from the manual)**
  are reported to the `theory-compiler` track via PARTNER_SYNC rather than fixed
  here. X-1 needs a grammar change, which is that track's to make and explicitly
  not something to hand-edit into a frozen contract. X-2 needs real Lean and PDDL
  generators, which is a sprint.
* **X-5 (box-on-wall)** is a real defect in `push2` and is **not fixed**: the fact
  it needs is not expressible in the v1 guard language, so fixing it means either
  a guard predicate over level-static data or a `unique`-style declaration — both
  grammar changes, both the other track's. The 52 states are unreachable in play,
  which T-9 is this repository's own standing argument against treating as a
  defence.
* **X-3** wants a `certify` obligation and **X-4** a schema decision; both are
  smaller than their blast radius and neither blocks this migration.
* `theory-compiler/`, `cold-start-a0/` and `engine-rig/` were read but never
  written. Territory held.
