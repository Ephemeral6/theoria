# figures/ — RUN_STATE

Narrative for `P4-figures` (worker `W-1611`, branch `agent/p4-figures`, base
`1e7002d`). The machine-readable record is
`figures/runs/20260728T082401Z-P4-figures/MANIFEST.json`; this file is the part
a manifest cannot carry.

## Where it stands

Six figures, two themes, SVG and PNG — 24 images and 6 CSVs. `verify.sh` is
green on all seven gates: two builds byte-identical, sources unchanged, the
committed tree equal to a fresh build, every artefact present, and no figure
script touching the filesystem outside `sources.py`.

| figure | what it shows |
|---|---|
| `fig02_bill_shape` | per-turn cost, `bare_cc` × model ladder **and** the theoria arm |
| `fig03_capability_spectrum` | battery v2, 38 metrics × 5 arms, 190 cells |
| `fig04_a3_transfer` | carrying the book vs starting again, nine meter lines |
| `fig05_a2_repair_loop` | the DC22 case: six beats, two prelude beats |
| `fig06_concept_timeline` | 25 adjudications over 6 lanes, ordinal axis |
| `fig07_a0_vs_a0prime` | coverage down, accuracy up |

## The decision this run turned on

`figures/` was not missing. It was **orphaned** — a nearly complete pipeline
sitting uncommitted in `.worktrees/wt-p21/` on `agent/p21-figures`, found only
because the `deterministic-figures` skill happens to say it was "distilled from
P-21 (`figures/`)".

Salvaging it rather than re-deriving was the call, and the reason is not
economy. The skill documents *that* code — its determinism knobs, its
`build()` contract, its absence encodings, knob for knob. A fresh
implementation would have been a second contract, subtly disagreeing with the
one the next author will read. Two contracts is worse than one imperfect one.

What the salvage cost: P-21's code carried three defects, and finding them took
longer than writing the equivalent would have. What it bought: the skill is
still true.

## What was wrong, and the shape it had

All three defects were the same shape — **an upstream artefact moved and the
figure code did not know**:

1. `fig03` could not build at all, because it took its column axis from
   `arm_contrast.json`, which knows four arms where battery v2 scores five. The
   guard refused to guess, which was right; it just asked the wrong authority.
2. `fig03` drew "NO SCHEMA ARM … there may never be one" across the plate.
   `REPORT_V2` had already ingested one, and pairs it against `bare_cc` **by
   game** — the world-controlled contrast v1 could not do.
3. `PLAN.md` §2 identified A0′ as `a0-spike`. A0′ is `cold-start-a0/prime/`,
   which was on disk in P-21's own worktree. The two readings say opposite
   things, and the P-21 one would have headlined a comparison `REPORT_V1`
   explicitly forbids.

That shape is why `SOURCES.md` no longer carries a table of source paths, and
why the fig03 subtitle now computes its own column count instead of stating
one. A hand-copied fact about another file is a fact that will go stale.

## Three defects found in P4's own work, worth recording

* **A caveat rendered as mathtext.** `$0.9025 … against $0.1459` came out as
  italic `0.9025…against0.1459` — matplotlib eats `$…$`. It is *deterministically*
  wrong, so both builds carried it and gate 3 stayed green. `theme.check_no_mathtext`
  now raises. **Gates prove reproducibility, not correctness.** Every plate in
  this run was rendered and read; two of the six needed layout passes that no
  gate would ever have asked for.
* **SVG newlines.** matplotlib writes SVG through a text-mode handle, so it
  emitted CRLF here and LF on Linux. `.gitattributes` stores LF, so a fresh
  checkout plus a Windows rebuild would have failed gate 6 with nothing to fix.
  `theme.save` now pins the newline at the writer.
* **One clip-path id moved between builds.** `svg.hashsalt` pins most generated
  ids, but for an artist clipped by a *path* matplotlib keys the id on
  `id(clippath)` — a memory address the salt cannot reach. `theme.save`
  canonicalises generated ids to a stable sequence.

Also fixed: `build_all.py` printed a `†` through a stdout that falls back to the
locale codec when redirected, so `verify.sh` died on a zh-CN box while an
interactive run succeeded; and `--list` emitted CRLF, so gate 5 built paths with
a trailing carriage return and declared every artefact missing while the build
had just written it.

## What is drawn that could mislead, and is therefore said on the plate

* **fig02's two arms are not priced in the same unit.** A `bare_cc` turn buys
  one model call that picks one action; a theoria turn buys a desk call that
  theorises across the run — 5 calls covered 7 actions. The vertical gap is not
  a markup. Two theoria attempts were billed and abandoned (USD 2.038212), and
  their own manifests record `outcome: null`.
* **fig04's bottom three meter lines save nothing** (1:1, 3:3, 1:1) and are
  drawn for that reason; two of the control arm's five theorize rounds were
  toolchain tax, not world-learning.
* **fig05's ledger holds eight beats and summarises 8/8**; the loop is six, and
  the plate never shows the 8-beat summary.
* **fig06's manual was revised zero times by `certify`.** The three iterations
  that happened were compiler defects, on a subordinate lane that says so.
* **fig07 is confounded by construction**, and the objection that bites is
  analytic, not statistical.

## Gaps, honestly

* **fig02 has no Schema arm** and cannot get one: `REPORT_V2`'s Schema material
  is upstream trajectory collections, which carry no cost. A Schema *capability*
  column exists; a Schema *bill* does not.
* **`baseline-arms/out/shards/` and `out/campaign/` are untracked**, so ~2 000
  cost rows and USD 48.39 of campaign spend are declared-and-absent rather than
  drawn. `fig02` picks them up automatically if they are ever committed.
* **fig06's clock covers one milestone of eight.** `sources.git_log` follows
  only `THEORIZE_LOG.md`; six columns are labelled `no commit ts`, and the axis
  is ordinal and says so.
* **fig07 cannot put A0′ in its battery panel** — `battery/adapters/` has no
  prime adapter, so A0′ has no battery run. Drawn as a gap, with the reason.
* **Two numbers are named on plates as unreadable** rather than drawn: A0's
  executable-probe count and its manual's object count are prose-only in
  sources this pipeline does not declare.

## Reported to the monitor, not fixed here

`monitor/inbox/20260728T083000Z-W-1611-p21-figures-was-orphaned-and-p4-salvaged-it.md`
— the orphaned worktree (and the recommendation to sweep the other ~20 for
uncommitted work), plus four upstream drifts found while reading: the stale
`arm_contrast.json`, `battery/README.md` and `METRICS.md` still pointing at v1,
`cold-start-a0/THEORIZE_LOG.md`'s compression table never re-priced after
commit `7cc02a9`, and `A3_REPORT.md`'s headline pairing two different meter
lines. All belong to other territories. None was touched.

## Discipline

Zero API calls, zero model calls, zero network, zero spend — so no spend gate
was engaged. Sealed pile untouched: every source is a self-built world or one of
the four development-pile games, and `fig03` stamps the pile-cut sha256 from the
battery's own provenance. Writes confined to `figures/`, plus one inbox file and
one `PARTNER_SYNC.md` paragraph. `master` untouched; merging is `ci_merge`'s.

---

# figures/ — RUN_STATE, P8

Narrative for `P8-billshape-pipeline` (researcher `RES-2`, branch
`agent/p8-billshape-pipeline`, base `98593a0`). Machine record:
`figures/runs/20260728T110000Z-P8-billshape-pipeline/MANIFEST.json`.

## What the work order asked for, and what was actually wrong

Two things: an adapter so a theoria-arm ledger enters figure 2 the moment it
lands, and the front-load index / convergence point / context-growth fit drawn
from the baseline's three-model data.

Its premise — "the Theoria column is empty" — was one revision stale. P4 had
already drawn that arm. **The defect was one level down**: the arm was declared
as a hand-written tuple of source keys, and so were the roll-ups, and both
tuples had fallen behind their directories.

## The two drifts, and why they are the same drift

The P4 section above records three defects as one shape — *an upstream artefact
moved and the figure code did not know*. These are that shape a fourth and fifth
time, and both were found by listing a directory and diffing it against a tuple.

**D-1. Two tracked roll-ups were never read.** `ROLLUP_KEYS` named four of the
six `pilot_*.json` files in `baseline-arms/out/`. The two it missed hold the
outcomes for `bare_cc-g50t-claude-sonnet-5-ddabe772` (`budget_exhausted`) and
`bare_cc-sk48-claude-sonnet-5-9022a076` (`model_error`). Both runs were drawn
**dotted** — the plate's encoding for *outcome unknown, not 'fine'* — while
their outcomes sat committed in the repository. The second should have been
**dashed**, and dashed is this plate's own warning that *a curve which stops
early stopped because the API died, not because the run was thrifty*. The figure
was withholding one of the two warnings it exists to draw, on evidence it
already had.

**D-2. A fourth theoria run directory was never read.** Nine directories under
`theoria-arm/runs/`, four with a `cost_curve.json`, three in the tuple. The
missing one is a preflight whose curve is empty — and `_load_theoria_curves`
already carried a branch for exactly that case which had **never executed**,
because the only run that reaches it was not in the list. That is the part worth
keeping: a hand-maintained list does not just miss data, it leaves the code for
the missing case unexercised, so nobody ever finds out whether it was right.

## The fix is a shape, not two patches

`sources.py` now declares those three families **by rule** (`DISCOVERY`):
directory, filename pattern, required members, and a floor. Every file a rule
finds becomes a real `Source` and is hashed into `SOURCES.sha256` exactly as a
hand-written one is — nothing is read unhashed, and the registry's contract is
unchanged. What moved is who enumerates the family.

The floor is what keeps it honest. A glob that comes back empty looks exactly
like a family that is empty, so each rule records how many members were on disk
when it was written and gate 0 fails below it. Absent-by-design members stay
declared through the rule's `expected` list, so the untracked envelope shards
keep their `ABSENT…` lines instead of vanishing from the manifest.

## Gates cannot see this class of failure, so it got a probe

Every one of gates 1–7 was green on the tree that had both drifts: two builds
byte-identical, committed tree equal to a fresh build, every source hash
unchanged. That is the whole lesson. **Determinism gates prove that the picture
is reproducible and current; they say nothing about whether it is complete.**

`check_coverage.py` is gate 8. It walks the tree itself and asks four questions:
is every rule at its floor; is every cost-bearing theoria run either drawn or
named as billing nothing; does every run with a roll-up on disk carry its
outcome onto the plate; does every shape absence carry a reason.

**Its negative control is not optional, and it fired immediately — at the probe.**
The first version took its disk-side inventory from `sources.discovered(...)`,
the same registry the figure reads. When the control narrowed that registry back
to the pre-P8 roll-up list, *both* sides narrowed together, and the probe
reported nothing over the exact defect it had been written to catch. It is
`fuzzlab`'s house rule turning up in a new place — the judge may not call the
engine it is judging — and the only reason it surfaced is that the control was
written before the probe was believed. The probe now walks the filesystem with
`os.listdir` and takes its verdict from the registry, which is the one place in
`figures/` where reaching past `sources.py` is the method rather than the bug.

## The three shape metrics: read, not recomputed

E2 (front-load index), E3 (convergence point) and E4 (context growth) already
exist in `battery/metrics/economy.py`, with anti-gaming floors, and E2 is one of
Phase 4's three primary endpoints. Figure 2 reads their published per-run values
from `battery/artifacts/capability_spectrum.json`. A second implementation would
be a second definition of a primary endpoint, and two definitions of one number
is precisely the drift this pipeline exists to prevent.

Three consequences, all on the plate rather than only here:

* **E2 and E3 are drawn as the constructions that define them.** A vertical rule
  on panel B at the head boundary makes a curve's height there *be* its
  front-load index; a tick marks the turn at which each bill reached 90 %. The
  head boundary's position is derived from the battery's own `head_turns /
  turns` support, not copied from `FRONTLOAD_K` — a hand-copied fact about
  another file is a fact that will go stale, which is `SOURCES.md`'s own rule.
* **The turn axes are checked rather than assumed.** The battery counts turns in
  model-call order; this plate counts `step_idx`. E3's crossing is marked only
  where the two coincide. They agree on all 12 markable runs — and that is
  *reported as a checked result*, because the agreement is the licence to draw
  the marks at all.
* **The theoria arm has no shape metrics.** Battery v2's arms are `bare_cc`,
  `schema_repro`, `theoria_a0`, `theoria_a0_spike`, `theoria_a2`; the live ARC
  theoria run is none of them. Drawn as an absence with its reason. A reader who
  saw a gap where an arm's front-load index should be would read it as a bad
  score, and it is not a score at all.

## What happens when the Theoria column fills in

Nothing in `figures/` changes. The metrics key on `run_id`, so a theoria run
scored by the battery attaches to its curve at the next build; panel D's `other
arm, scored (0)` becomes non-zero and the absence column loses its `no battery
run at all` line, both computed rather than written down. Panel B's E3 tick will
most likely still *not* be drawn for that arm — its step axis is sparse (5 desk
calls across 7 actions, 2 of 7 turns bought anything), so `axis_agrees` will be
false and the crossing will be reported and left unmarked. That is intended: the
alternative is putting a fraction-of-decisions on an axis of
fraction-of-actions. `PLAN.md` §3 carries the same four points where the next
author will look for them.

## Three drifts found, none in this territory, none touched

* **`battery/metrics/economy.py`'s `support["turns"]` means two things.** E2 and
  E3 fill it from `len(run.turn_costs())` (decisions); E4 fills it from
  `len(run.calls)` (billed calls). They differ exactly when a decision was
  retried, and on `bare_cc-g50t-claude-sonnet-5-ddabe772` they are 20 against 24.
  Found by widening the turn-axis check to use E4's count, which made figure 2
  report an axis mismatch that does not exist — the two numbers were never the
  same measurement. Panel D's axis is now labelled with what E4 actually counts.
* **The board item's premise was stale**, as above.
* **`baseline-arms/out/shards/` and `out/campaign/` are still untracked** — ~2 000
  cost rows and USD 48.39 of campaign spend, declared-and-absent. The rule now
  picks up any shard dropped in, including one whose filename nobody wrote down.

## The adversarial review, and the blocker it found in the probe

An adversarial reviewer was run over the finished branch on three axes —
evidence, reproducibility, novelty — instructed to refute rather than to
approve. It could not refute the six load-bearing claims (it re-derived each
from the tree: the two unread roll-ups and their line styles from `98593a0`'s
`fig02_bill_shape.py`, the unreachable empty-curve branch, that no figure
recomputes E2/E3/E4, that the head boundary is derived, that the live theoria
arm has no battery run, and the E4 support-key disagreement). It found sixteen
defects. The one worth reading is the first.

**BLOCKER — the negative control was still auditing through the thing it
audits.** The probe walked the filesystem, but took the *root* and the *pattern*
it walked from `sources.rule(...)` — the registry under audit — and the
self-test narrowed `sources.DISCOVERED`, which is derived state that nobody
edits by hand. So the control exercised the one narrowing the probe already
survived. Narrowing the **`Rule`** instead — a tightened pattern, which is what
a real regression actually looks like — reproduced drift D-1 exactly and the
probe reported nothing: both runs back to dotted, outcomes committed on disk,
gate green.

That is the *same* finding as the one this run had already congratulated itself
for fixing, one level up. The first version called the registry as a function;
the second took its parameters from it. **An oracle can be captured through an
argument as easily as through a call**, and "I walk the filesystem myself" was
not the property that mattered — *where* it walks was. The probe now states its
root, pattern and member filenames as literals, deliberately duplicating
`sources.DISCOVERY`. Duplication is wrong everywhere else in this directory and
right here: two independently written descriptions of one tree can disagree, and
the disagreement is the finding. One description checked against itself cannot
disagree with anything.

The other fifteen, all applied:

* **The plate contradicted itself.** The caveat asserted `THE TURN AXES DIFFER`
  in capitals and then reported `0 run(s) disagree`. It now states the checked
  result in whichever direction the check came out.
* **Both examples under that rule were wrong, and wrong in the flattering
  direction** — they made a true mechanism look like it had instances it does
  not have. `ddabe772` *agrees* on the turn axis and its E3 crossing is marked;
  its 20-against-24 is the E4 support-key finding, a different thing.
  `9022a076` has no battery turn count at all. Corrected next to the claim
  rather than deleted, and the claim itself stands.
* **Five numbers were literals on the plate, two of them duplicating numbers the
  same build computes.** `USD 0.9025` and `-8.3 %` are now derived from the
  basis run's manifest — they reproduce the literals exactly, which is the
  point: they were right, and they were a second definition. The three that
  cannot be computed here (`USD 0.1459`, and the two failure bands) are now
  **declared sources**, so a number quoted on the plate is a hashed number.
* **The plate drew a refuted bound alone.** `REPORT_V0`'s 27-45 % is recomputed
  as 28.3-45.1 % in `papers/phase1-workshop/REVIEW.md`, which records that the
  27 % lower bound does not reproduce. Both now travel, and the red-ink
  threshold in panel C's gutter moved off the refuted number — no run on this
  build sits between the two, which is the reason to move it now rather than
  after one does.
* **`8` was hand-copied where `0.25` was derived.** The short-run floor is now
  quoted from the battery's own reason string in the hashed artefact.
* **`fnmatch` is case-insensitive on win32 and case-sensitive on POSIX**, so the
  same tree could have been inventoried differently by operating system. Now
  `fnmatchcase`. A real determinism defect, invisible on any single machine.
* **`SOURCES.md` claimed no script in `figures/` opens an undeclared path.**
  False as of this run, and false in a way that matters: the probe is exactly
  such a script, on purpose. Rewritten to say which two files are outside gate
  7's scope and why that is the correct scope.
* **The untracked-shard exposure is now named rather than left to surface as an
  unexplained hash diff.** `build_all.py` prints a `WARN` per folded-in
  untracked shard, demonstrated with a scratch file. Two of this territory's own
  numbers come from that tree and are marked as not checkable from a clean
  checkout.
* **The probe's stated question was wider than the one it asked** — it skipped
  half-written run directories on the same predicate the rule uses, so a run
  landing with a cost curve and no manifest would have been invisible to both at
  once. Now named as a failure. None exist today; the class is watched.
* **`manifest.py`'s flags were made required rather than defaulted.** Leaving
  `P4-figures` as a default would have left the trap armed for whoever ran the
  command without reading the comment explaining the trap.
* **A newly landed malformed run would have killed the build of all six figures
  with a bare `KeyError`.** It now raises naming the directory and the missing
  fields.
* **P-21's claim that the extractor takes a `--ledger` list** is false — there is
  no `argparse` in `fig02` — and gets a `P8 CORRECTION` in place, per this
  plan's own convention.
* Two docstring overclaims and one count in `README.md` were narrowed to what is
  actually true.

And two layout defects that the longer text introduced, caught by looking at the
plates rather than by any gate: panel C's title ran off the right edge, and
panel D's x-label printed through the first two lines of the caveat. Both were
byte-identical between builds and green on all eight gates. That is the third
time in two runs that the thing no gate can see was a rendering fault found by
opening the picture.

## Discipline

Zero API calls, zero model calls, zero network, zero spend. Sealed pile
untouched: every source is a self-built world or one of the four
development-pile games. Writes confined to `figures/`, plus one inbox file and
one `PARTNER_SYNC.md` paragraph. `master` untouched; merging is `ci_merge`'s.

Both plates were rendered and read at each iteration, and that mattered: the
first layout put panel D's absence text under the axes, where it landed on top
of the caveat — unreadable, byte-identical between builds, green on every gate.
The second starved panels A and B, because the new legend labels were long
enough for `constrained_layout` to take the width from the axes. Neither is a
failure any gate in this directory would ever have mentioned.
