# P10 — figures into the paper

Worker `W-1253`, branch `agent/p10-figures-into-paper`, base `ff796cd`,
territory `figures`. **`verify.sh`: green, 11 gates.** Zero API calls, zero model
calls, zero network, zero spend, zero sealed-pile reads.

## What was asked, and what is here

| clause | state |
|---|---|
| 1. publication-spec SVG+PNG per figure, dual theme, accessible palette, named to match the § numbering | **done**, and a vector PDF besides — `figures/paper/{light,dark}/figureN_<slug>.{pdf,png,svg}`, PNG at 300 dpi |
| 2. a caption per figure naming the tree file and the run the data came from | **done**, generated — `figures/paper/captions/figureN.md` |
| 3. an index (number → generator → data source → sha256) and one command that rebuilds every figure | **done**, generated — `figures/paper/INDEX.md`, `index.json`; the command is `python figures/build_all.py` |
| 4. fill in the "see Figure X" places in the body; mark data-less figures `pending` | **half.** The `pending` marking is done and derived. The body edits are **not applied** — see below |

## The gap, stated plainly

**Clause 4 is not applied, and the reason is territory, not difficulty.**

The board item declares `territory: figures` and its body closes with
"不改 papers/ 之外的东西". Both cannot hold. `board.py` had already settled it
before I read the item: it hands out an item only when its territory is free,
`figures` was free, and **`papers` is claimed by `RES-2` under
`P9-paper-to-submittable`**. Had the territory line said `papers`, this item
would not have been claimable at all.
`.claude/skills/deterministic-figures/SKILL.md` says the same independently:
*"Figure work writes only inside `figures/`."*

So the body edits ship as `HANDOVER-papers.md` in this run directory: the three
missing citations (§6.2, §7.1, §7.8) as ready-to-insert Markdown matching the
paper's existing citation style, plus the two decisions that are the papers
holder's and not mine. **No file under `papers/` was modified by this branch** —
`git diff --stat master...agent/p10-figures-into-paper -- papers/` is empty.

The overlap is real and was checked, not assumed: `RES-2`'s own P9
reconnaissance names the figure wiring as *"real, and probably the largest
piece"* of P9, and they wired Figures 1–3 in `a636c0c` while this was being
built. **We assigned the same three numbers to the same three plates
independently**, which is the strongest evidence available that the mapping is
the right one.

## The substantial finding

Two things were wrong in the committed tree before this run, both invisible to
every existing gate because both were perfectly reproducible. `FINDINGS.md` has
the full account; in short:

1. **A plate's committed SVG and its committed PNG were different geometry.**
   Constrained layout re-solves on every `savefig` and the solve is dpi-
   dependent; `save()` wrote SVG at `figure.dpi` = 100 and PNG at `savefig.dpi`
   = 200. True since P-21.
2. **`fig07_a0_vs_a0prime`'s layout never converged — it drifted**, both margins
   moving inward by 0.0048 of the figure on every pass, forever. Cause: a
   `wrap=True` text's extent is a function of the width available to it, and
   constrained layout sizes axes from the extents of what they contain. Its SVG
   and PNG sat ~25 px apart.

Both are fixed in `theme.py` (`_freeze_layout`, `_unfeed_wrapped_text`). Found by
gate 10 — a gate written to ask whether the paper shows the plate the pipeline
built, which failed on all twelve pairs the first time it ran.

**Two wrong fixes shipped green before the right one.** Freezing the layout after
a single draw wrecked `fig03` visibly — headers colliding into
`bare_ccschema_repro`, in-cell values clipped — and was byte-identical across two
builds, so gate 3 was happy. Only looking at the plate found it. `README.md`
already said this: *gates prove reproducibility, not correctness.*

## What changed in the committed images

* All 12 SVGs changed — that is the fix.
* `fig03` and `fig06` PNGs are **byte-identical to the pre-P10 files** in both
  themes, which is the check that the shipped layout is the reviewed layout.
* `fig02`, `fig04`, `fig05`, `fig07` PNGs changed. All four were compared panel
  by panel against their pre-P10 renderings in both themes by two independent
  reviewers before being committed; all four came back clean, with no
  annotation, legend or label changing place.
* Three **pre-existing** cosmetic collisions were found during that review and
  deliberately not touched, because none is P10's to fix: fig02 panel B's
  "marker: game" legend overlays its trend lines; fig05 panel E's reference rule
  at x = 1.000 passes through its legend text; fig04 panel E's "3 supplied" label
  sits on a light hatch in the light theme only. Recorded here so the next
  author does not have to rediscover them.

## Gates

`verify.sh` grew three, all with their expectations written as **literals** in
the gate rather than read from the module they audit — `PLAN.md` §10 is the
record of what happens otherwise.

| gate | checks |
|---|---|
| 9 | 6 paper figures × 2 themes × 3 formats = 36 artefacts, + 6 captions + index |
| 10 | the publication SVG is byte-identical to the screen SVG of the same plate |
| 11 | every digest in `index.json` recomputed from disk; numbering 1..6 contiguous |

Gates 3 and 6 were extended over `paper/`, so the new profile gets no exemption
from the determinism check.

**Shown failing.** Deleting Figure 6 from `paper_map.py` turns gates 9, 10 and 11
red *separately* — 7 missing-artefact failures, 2 profile-divergence failures,
and "expected 6 paper figures, index declares 5" — rather than shrinking any of
them. Transcript in `NEGATIVE_CONTROL.md`.

## Cost

Zero. This pipeline reads tracked files and writes images. No API call, no model
call, no socket, no sealed-pile read. Every source is a self-built world or a
development-pile game, and `SOURCES.sha256` is unchanged by this branch —
gate 4 confirms it (50 sources, no diff).

## Repository size

`figures/paper/` adds ~24 MB of tracked binaries to a tree whose `out/` was
already 17 MB. That is the cost of a self-contained, correctly-named submission
bundle in three formats and two themes, and it is stated rather than left for
someone to discover in the Phase 4 release manifest. If it needs to come down,
the cheapest cut is the publication SVG: it is byte-identical to the screen SVG
by construction (gate 10), so it is the one artefact that carries no information
the tree does not already hold — about 6.4 MB.
