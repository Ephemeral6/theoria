# A23 · The leg most likely to be drifting, measured at last — and the drift turns out to be periodic

`GAPS.md` GAP R2-1 named a trade and left it standing: keeping `--frontier
ablation` byte-identical means the anchor block is written only when a switch is
on, so **the legs most likely to be drifting are exactly the ones that cannot
report it**. R3 paid the forward half — every leg from now on writes
`anchor.jsonl`. This ticket pays the backward half, over eight legs that are
already on disk and will never run again.

The measurement costs two hashes: no action, no model call, no network, `$0.00`.

## The triple, eight legs

`probes` are designs that got a result. `drifted` is `predictions["inert"]` —
the frontier's anchor, the manual's rolled-forward state rendered unchanged —
disagreeing with the frame the world was actually showing. `drifted_and_off`
is those whose answer no hypothesis in the frontier named.

| leg | probes | drifted | drifted_and_off |
|---|---|---|---|
| `20260731T231654Z-R1-g50t-a` | 5 | **3** | 3 |
| `20260731T231654Z-R1-sk48-b` | 0 | 0 | 0 |
| `20260801T001851Z-R1b-g50t-a` | 14 | **9** | 9 |
| `20260801T001851Z-R1b-sk48-b` | 1 | 0 | 0 |
| `20260731T1240Z-A3-level2-carried` | 0 | 0 | 0 |
| `20260731T1310Z-A3-level2-carried-r2` | 8 | 7 | 7 |
| `20260731T1430Z-A3-level2-carried-r3` | 28 | 21 | 21 |
| `20260731T1500Z-A3-sk48-carried-l1` | 16 | 7 | 7 |
| **total** | **72** | **47** | **47** |

The bottom four are R2's; the top four had never had an anchor number taken at
all. The two `0 / 0 / 0` rows are **not** clean legs — they resolved no probe,
and their record says so in a `note` rather than leaving a zero to be misread.

## Three things the numbers say

**1. `drifted and ON frontier: 0 of 47`, and the base rate that makes it
readable.** R2 found all 35 of its drifted probes off-frontier and called it the
finding; on eight legs it is 47 of 47, with four legs R2 never saw. But the
sentence *"a drifted anchor is never recovered from"* needs the denominator
beside it, and R2 did not print it either: **only 5 of the 72 probes in this
archive ever landed on-frontier at all.** All five are on one leg
(`sk48-carried-l1`), all five were anchored, and all five were named by the
`manual` hypothesis — no probe in the archive has ever been answered by `inert`.

So the contrast is `5 of 25` anchored against `0 of 47` drifted (Fisher, one
tailed, p ≈ 0.004), and every unit of that contrast comes from a single leg: on
the other seven, on-frontier is 0 of 16 anchored *and* 0 of 40 drifted, a
difference of exactly zero. The implication is supported, it is not
demonstrated, and these controls cannot demonstrate it (GAP A23-3). What is
unambiguous is the converse being false: **20 of the 25 correctly anchored
probes were off-frontier too**, so anchoring is necessary and nowhere near
sufficient — the residue R2 filed as expressivity (GAP R2-2/R2-3).

**2. The anchor is re-seated by the theorize beat — the probe ids where it is
correct are *exactly* the turns a theorize call ran.** This started as an
observation that the anchored ids sit at ≡ 1 (mod 4) and looked like an
unexplained periodicity. It is not unexplained; it is
`MIN_NEW_FRAMES_BETWEEN_THEORIZE = 4` and `MAX_PROBES_BETWEEN_THEORIZE = 4`
(`inner/loop.py:86,114`), and each measured leg's own `turns.json` prints the
gate firing. Joined to the anchored ids:

| leg | anchored probe ids | theorize turns | equal |
|---|---|---|---|
| `R1-g50t-a` | 1, 5 | 1, 5 | **yes** |
| `R1b-g50t-a` | 1, 5, 9, 13, 17 | 1, 5, 9, 13, 17 | **yes** |
| `R1b-sk48-b` | 1 | 1 | yes (one probe) |
| `A3-level2-carried-r3` | 1, 5, 9, 13, 17, 21, 25 | 1, 5, 9, 13, 17, 21, 25 | **yes** |
| `A3-level2-carried-r2` | 5 | 1, 5 | no — turn 1 did not re-seat |
| `A3-sk48-carried-l1` | 1, 2, 3, 5, 6, 9, 13, 14, 15 | 1, 5, 9, 13 | no — it survives 1–2 turns past |

The mechanism follows: `_roll_forward` starts from `initial_state()` with
whatever manual is current, so re-theorizing produces a different roll, and on
these legs it lands back on the world's frame. **The manual's state is correct
when it is freshly written and wrong by the next probe.**

That is a smaller claim than "an unexplained period" and a more useful one, and
it sharpens what remains genuinely open — the two exceptions, which the schedule
does not explain. On `r2` a theorize call ran at turn 1 and the anchor was
*still* wrong; on `sk48-carried-l1` the anchor survives one or two probes past
each re-seat. Filed as **GAP A23-2**. It also corroborates R3 from a second
series: R3 refuted *"one mispredicted transition desynchronises permanently"* by
counting 8 recoveries per certify beat; this sees the recoveries per probe and
identifies what causes them.

**3. Every experiment in this archive is a two-way split.** `frontier_width_distinct`
is `2` on all 72 probes, against 9–24 hypotheses. R2 reported this for its four;
it holds for all eight without exception.

### 16 of the 72 rows are the same experiment run twice

Comparing designs on `(action, predictions)`, sixteen are byte-identical repeats
of one already run on the same leg — 4 on `r2`, 4 on `r3`, **8 of the 16 on
`sk48-carried-l1`**. So the archive holds **56 distinct experiments, not 72**,
and 14 of the 47 drifted rows are repeats: de-duplicated the triple is
**56 / 33 / 33**. On `l1` — the one leg carrying the entire on-frontier contrast
above — 6 of its 7 drifted rows are repeats.

This is not a new discovery, it is a known defect these legs predate:
`inner/probe.py` names `r3`'s `P-25`/`P-27` and `P-26`/`P-28` explicitly, and
`inner/loop.py` gained an unconditional refusal for it afterwards — which is why
R1/R1b carry zero repeats and unrunnable rows instead. **The arm as it stands
today would refuse to run 16 of the 72 rows counted here.** The headline triple
is left at 72 because that is what the legs did; the de-duplicated one is stated
so nobody has to rediscover that a third of `l1` is one experiment.

### And one number that is a transport artefact, not a finding

`R1b-sk48-b P-01` has `observed: "none"` — status 400, zero frames, the action
never ran. It is correctly `drifted: false` (its anchor genuinely did match:
`predictions["inert"]` and the step's `before_hash` are both
`05615f3d5f835100`), but its `off_frontier: true` means only that nothing was
there to match. That leg's whole record is `1 / 0 / 0`, which reads like *one
probe, cleanly anchored*; what happened is that it designed 5 probes, 4 were
ruled unrunnable, and the one sent came back 400 with a vacuous frontier. The
tool now says so in its `note` and counts `probes_without_an_answer` — the same
discipline that stops an empty triple reading as a clean one has to cover this
shape too.

Reading the R1/R1b legs honestly: **19 answered probes, 19 off-frontier, 12
drifted**, plus one probe the world never answered.

### What "drifted" is a claim about: the frame, not the state

The anchor is a *rendered frame* hash, so `drifted` asks whether the frontier
was seated on the frame the world was showing — which is the right question,
because every prediction in the frontier is a frame hash. It is **not** a
measure of whether the manual's internal bookkeeping had desynchronised. Those
come apart whenever two different states render to the same grid, and this
archive is full of that: `sk48-carried-l1` runs 16 probes over 11 distinct world
frames, and 10 of its probes sit on a frame the run had already shown. A stale
roll-forward that happens to render to the frame the world is currently showing
scores `drifted: false` here and is right to — the frontier really is anchored —
while the manual really is lost. So **47 is the frame-level count and a lower
bound on state-level desynchronisation.** Filed as **GAP A23-4**; R3's
`inner/anchor.py::divergence` measures the state-level quantity and the two have
never been joined.

## Why this is a measurement and not a story

**Two readers, 52 probes, row for row, and the row *sets* compared as sets.**
R2 read the recorded `before_hash` field out of the trace row.
`armtools/anchor_drift.py` throws that field away: it hands `trace.jsonl` to
`world.frames.load_store`, which never reads it and rebuilds the anchor from the
frames themselves (`FrameStore.add` assigns
`before_hash = grid_hash(self.current)`). The two paths agree on all 52 probes,
per leg and per probe, on all three totals, and on which 52 probes there are —
`CROSSCHECK.json`: `equal: true`, `probes_compared: 52`,
`probes_only_this_reader_has: []`, `probes_only_the_other_reader_has: []`.

**Two different things are being called agreement here, and only one of them is
a second reader.** R2's tool against this one is a genuine
independent-implementation crosscheck: different author, no shared line, same
52 rows, same answer. `recorded_vs_recomputed_disagreements: 0` is **not** that.
`to_jsonl` writes the `frames` column and the `before_hash` column off the same
`Step` objects, and `load_store` replays `FrameStore.add` over them using the
same production `add`/`current`/`grid_hash` — so the two agree *by construction*
and there is no input on which they can differ unless the file was edited after
it was written. What that rules out is post-hoc tampering with the hash column,
frames dropped or reordered in serialisation, and JSON round-trip corruption.
What it does not touch: a bug in `add`/`current`/`grid_hash` (identical code
both times reproduces its own bug exactly), whether the frames were ever what
ARC returned, or whether `current` — *the last step whose cascade was
non-empty* — is the right reading of "the frame the world was showing". It is a
tamper check, and an earlier draft of this file called it more than that.

**Nine negative controls, all held** (`NEGATIVE_CONTROLS.json`). A drift
detector only ever watched saying *"drifted"* is a function that returns
positive numbers — and `drifted == 0` alone is not the opposite of that, because
`drifted` counts only `True` and folds an *unknown* anchor into the same zero.
Rename the trace's notes so the join misses and a leg that measured nothing
would pass a bare `drifted == 0`. So every control asserts `anchor_unknown == 0`
and the exact set of drifted probes, not a sign.

| control | manual | required | got |
|---|---|---|---|
| self-consistent | `A3-level2-carried-r2` rev11 | drift set == `[]` | `[]` |
| mispredicting | same manual, transition out of frame 2 broken | drift set == `[P-04, P-05]` | `[P-04, P-05]` |
| cascade (4 frames/step) | same manual | triple unmoved from the flat leg | unmoved |
| self-consistent | `A3-sk48-carried-l1` rev19 | drift set == `[]` | `[]` |
| mispredicting | same manual, same break | drift set == `[P-04, P-05]` | `[P-04, P-05]` |
| cascade (4 frames/step) | same manual | triple unmoved | unmoved |
| trace absent, as in a clone | — | all `null`, and the status names *the trace* | `NO_TRACE` |
| probes absent | — | all `null`, a *different* status | `NO_PROBES` |
| directory absent | — | all `null`, a *different* status | `NO_LEG` |

The required drift set is derived (`_expected_drifted`), not remembered: the
roll before probe *t* consumes actions 1..*t*−1, so freezing frame *k* breaks
probes *t* ≥ *k*+2 and no others. The earlier `drift > 0` predicate would have
accepted the check firing in the wrong place, and did — a comment in this
directory predicted `P-03` onward while the file's own output said `P-04`,
`P-05`.

The synthetic legs are not simulations of the arm. The world **is** a leg's own
compiled `theory.dsl` rolled forward; the trace is written by
`world.frames.FrameStore`; the frontier by `inner.probe.build_hypotheses`; the
rolled state by `inner.loop._roll_forward` itself. Both legs of a pair share one
namespace and one action list and write byte-identical traces: the only
difference between them is the wrapper.

**What the mispredicting control is wrong about, and what it therefore cannot
witness.** It is one wrong *transition*, not one wrong *call*: the no-op returns
the frozen state, so that state is absorbing and every later action is wrong
too — 3 firings inside the rolls, 63 counting the hypotheses' own predictions.
That is the mechanism under study (`_roll_forward` is open-loop, so a
mispredicted transition is *supposed* to carry forward), but "wrong once" was
the wrong sentence and this directory used it.

The consequence matters more than the wording. At the frozen state every
hypothesis that consults `step` returns the frozen frame, so the frontier
collapses from 2 distinct predictions to **1**. The drifted probes on that leg
are off-frontier because their frontier is a point, not because their anchor
moved — **so these controls cannot confirm the archive's `drifted ⇒
off_frontier` implication, and this run does not claim they do.** On the toy
manual the collapse is measurably *wider* than the drift: `P-03` is collapsed
while still correctly anchored, `P-04` is both. Filed as **GAP A23-3** and
asserted in `test_the_mispredicting_leg_cannot_test_the_archives_implication`,
because a collapse nothing looks at is one the next reader will mistake for a
result.

## Absence is recorded as absence

`theoria-arm/.gitignore` excludes `runs/*/trace.jsonl`, so in a clone the frames
are simply gone. Every leg is then **refused by name** and measured `null` —
never `0` — and a refused leg contributes nothing to the totals rather than a
zero. Run in a fresh checkout this whole measurement prints eight refusals and a
`null` triple, and four tests skip themselves saying why. That is the correct
output, not a degraded one.

## What could not be delivered as asked, and the measurement that decided it

The ticket asked for the triple to be written **into each measured leg's own
`runs/` directory**, reasoning that a new file changes no byte the published
manifest covers. Measured, it does:

```
backfill._files_the_clone_carries("runs/20260731T1240Z-A3-level2-carried")
  before  37 files
  after   38 files      (ANCHOR_DRIFT.json enters files[])
  list changed: True
```

`backfill.build()` re-derives `files[]` by walking the directory, so
`backfill.render(build(...))` stops matching the manifest on disk and
`armtools.verify_provenance` check 8 — *"re-deriving every manifest reproduces
it byte for byte"* — goes red for a live-spend archive record. Absorbing the new
file would mean regenerating four archived manifests, which is what both R2 and
R3 explicitly listed under `not_changed` ("any `runs/` directory whose name
contains R1"), and which collides with the standing GAP A3-B-3 (check 8 is
already CRLF-red on a fresh worktree for exactly these legs).

So each leg still gets its own file — `ANCHOR_DRIFT.<leg>.json`, eight of them —
filed under the run that took the measurement rather than inside the run it
describes. `GAPS.md` **GAP A23-1** records the collision and the evidence, so
whoever owns those four manifests can reverse the trade knowingly.

## Files

| file | what |
|---|---|
| `ANCHOR_DRIFT.json` | all eight legs, per probe and in total |
| `ANCHOR_DRIFT.<leg>.json` | one per leg (8), so a leg's triple is addressable alone |
| `CROSSCHECK.json` | this module against R2's `MEASUREMENT.json`, per leg and per probe |
| `NEGATIVE_CONTROLS.json` | the five controls and their verdicts |
| `measure_anchor_drift.py` | the driver that writes the three above |
| `negative_controls.py` | the driver that writes the fourth |
| `GATES.txt` | suite, collection delta, provenance, spend — verbatim |
| `RUN_STATE.md` | the narrative |
| `MANIFEST.json` / `make_manifest.py` | provenance |

The tool itself is `theoria-arm/armtools/anchor_drift.py` (library + CLI) and
`theoria-arm/tests/test_anchor_drift.py` (27 tests). It takes leg names, never a
glob — a live round may be writing into `runs/` alongside it.

## Reproduce

```bash
cd theoria-arm/runs/20260802T1031Z-A23-anchor-drift-on-the-default-leg
python measure_anchor_drift.py       # eight refusals in a clone; the table above with traces
python negative_controls.py          # five controls, all held, no traces needed
cd ../.. && python -m pytest tests/test_anchor_drift.py -o addopts= -q
```

## Spend

Zero ARC actions, zero model calls, zero network, `$0.00`. Zero sealed-pile
contact — development pile only (`g50t-5849a774`, `sk48-d8078629`), read from
artefacts already on disk. No credential value in any tracked file.
