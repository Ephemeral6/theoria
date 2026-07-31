# P10 — what the work turned up

Worker `W-1253`, branch `agent/p10-figures-into-paper`, base `ff796cd`.

## F-1. The two committed profiles of a plate were already different pictures

Not a P10 change; a P10 *discovery*, and the largest thing in this run.

`figure.constrained_layout.use` is on, and the layout engine **re-solves on every
`savefig`**. The solve depends on text extents, text extents are measured in
pixels, and pixels depend on dpi. `theme.save` wrote SVG first and PNG second, so
each artefact was solved separately:

* `out/<theme>/x.svg` — solved once, at `figure.dpi` = 100
* `out/<theme>/x.png` — solved again, at `savefig.dpi` = 200

So the committed SVG and the committed PNG of the same plate have **different
geometry**. Both builds produce the difference identically, so gate 3
(byte-identity across two builds) was green over it for the whole life of the
pipeline. This is the class `figures/README.md` already warns about — *"a figure
can be deterministically wrong"* — found by a gate written for something else:
P10's gate 10 asks whether the paper's SVG is the plate the pipeline built, and
the first time it ran it failed on all twelve pairs.

**Fixed** by solving the layout once, before any write, and pinning it
(`theme._freeze_layout`). All five artefacts of a plate now share one geometry.

## F-2. `fig07_a0_vs_a0prime`'s layout never converged — it drifted, forever

Found while fixing F-1, and worse than F-1.

Freezing needs a settled layout, so `_freeze_layout` iterates to a fixed point.
Five plates reach one. `fig07` does not, and the way it fails is the
interesting part: it does not oscillate between two solutions, it **marches**.
Every pass moved both side margins inward by exactly 0.0048 of the figure —
constant amplitude, constant direction, still going at pass 25:

| pass | 2 | 3 | … | 25 |
|---|---|---|---|---|
| max move | 9.597e-03 | 9.597e-03 | … | 9.597e-03 |

Lag-2 movement was 1.919e-02 and lag-3 was 2.879e-02 — exactly 2× and 3× the
per-pass step, which is what rules out a limit cycle and identifies a drift.

**Cause: `wrap=True` text inside constrained layout is a feedback loop.** A
wrapped text's extent is a *function of* the width available to it; constrained
layout sizes the axes from the extents of what they contain. Each pass the axes
narrow, the text re-wraps, the engine reserves more room, the axes narrow again.
Confirmed by turning `wrap` off on the three wrapped texts: the drift went to
exactly zero (and the plate became unreadable, so that was a diagnostic, not a
fix).

**What this meant for the committed tree.** `fig07`'s SVG is one pass and its
PNG is two, so they sat 0.0096 of the figure apart — about 25 px at 200 dpi on a
13.2-inch plate. Two files that are supposed to be the same picture, visibly
different, committed.

**Fixed** by `theme._unfeed_wrapped_text`: any `wrap=True` text is excluded from
the layout with `set_in_layout(False)`. This breaks the cycle at the arm that
should never have been in it — these texts are all hand-placed in space their
figure already reserves (`theme.caveat` sits in the figure's bottom corner;
fig07's banner has a dedicated `axis("off")` panel with its own `height_ratios`
entry), so the engine measuring them was double-counting to begin with. After
the fix `fig07` settles to floating-point noise (2.2e-16) by the second pass.

### Two wrong fixes on the way, both caught by looking at the plate

Recorded because the gate was green for the second one:

1. **Freezing after one draw at `figure.dpi`.** Visibly wrecked `fig03`: the
   heatmap lost width, the five arm headers collided into
   `bare_ccschema_repro`, and every in-cell value clipped (`0.760  n=78` →
   `0.760  n=7`). Byte-identical across two builds, so gate 3 was green.
2. **Freezing after one draw at `savefig.dpi`.** Same damage, less of it.
   Constrained layout needs more than one pass; the committed plates had been
   getting two, one per `savefig`, by accident.

Only the third version — iterate to a fixed point, having removed the feedback
loop — reproduces `fig03`'s committed PNG **byte for byte**. That byte-identity
is the check that the layout being shipped is the one that was reviewed, and it
is why `LAYOUT_TOLERANCE` is a tolerance and not `==`: constrained layout
converges geometrically, so only `fig03` ever reaches a bit-exact fixed point.

## F-3. The work order's territory line contradicts its own body

`monitor/board/items/P10-figures-into-paper.md` declares `territory: figures` and
then closes with **"不改 papers/ 之外的东西"**. Both cannot hold. The board
resolves it — `board.py` hands out an item only when its territory is free, and
`papers` is held by `RES-2` under `P9-paper-to-submittable` — so clause 4 is
delivered as an apply-ready package rather than applied. See `RUN_STATE.md`.

This is the **third** consecutive work order in this area whose text and tree
disagreed: P8's premise about the empty theoria column was one revision stale,
P9's "the battery section is marked stale" had already been closed by P7, and
this one names a territory it then forbids. Reported to the monitor rather than
silently reinterpreted, because the next worker reads the same text.

## F-4. Two numbering schemes, and no join between them

The pipeline numbers plates after `Theoria.md` §3.2 (`fig02`…`fig07`); the paper
cites `Figure 1/2/3` against its own separate ASCII scripts in
`papers/phase1-workshop/figures/`. Nothing connected them, so "see Figure 2"
resolved to a different artefact from the one the deterministic pipeline builds.
`paper_map.py` is that join, and the numbering was assigned by order of first
citation specifically so the paper's existing three citations keep their
numbers — renumbering prose that `RES-2` is editing right now would be the
wrong kind of correct.
