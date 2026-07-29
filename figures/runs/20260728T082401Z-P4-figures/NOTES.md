# P4-figures — run notes (W-1611)

Branch `agent/p4-figures`, base `1e7002d`. Territory: `figures/` only. Every
data directory read is read-only; nothing outside `figures/` is written.

## The first decision: salvage, not re-derive

`figures/` did not exist on `master`, but it existed uncommitted in
`.worktrees/wt-p21/` on branch `agent/p21-figures` — `theme.py` (15 KB),
`sources.py`, `build_all.py`, `manifest.py`, `verify.sh`, `PLAN.md`,
`SOURCES.md`, and two figure scripts, of which one had ever been built.

The `deterministic-figures` skill is *distilled from that code* — it documents
that contract, knob for knob. Re-deriving the pipeline would have produced a
second contract that disagreed with the skill in small ways, and the skill is
what the next author will read. So P4 salvaged it, verified it, corrected it,
and finished it. `MANIFEST.json` lists exactly what was carried over.

P-21 is not a live session: its worktree HEAD is `dc9fad1`, many commits behind,
and the board re-dispatched the same work as `P4-figures`. Recorded to
`monitor/inbox/` so the monitor can confirm rather than discover it.

## What was wrong in the salvaged pipeline

Three defects, all of the same shape — an artefact drifted and the figure code
did not know:

1. **`fig03` could not be built at all.** Its column axis came from
   `battery/artifacts/arm_contrast.json`, which is v1-era and knows four arms;
   battery v2 scores five (`schema_repro` was ingested). The guard refused to
   guess the axis — correctly — but the authority was wrong. Fixed: axis from
   `capability_spectrum.provenance.arms`, control/treatment split from
   `validation_material.json`'s declared `control_arms`, and the stale artefact's
   disagreement *reported* rather than absorbed.

2. **`fig03`'s banner asserted a falsehood.** It drew "NO SCHEMA ARM
   (`SCHEMA_LOCATE.md`, which says there may never be one)" across the plate.
   `battery/REPORT_V2.md` records the Schema arm as ingested — 8 runs, 4
   development-pile games × 2 upstream collections — pairing against `bare_cc`
   **by game**, which controls for the world. Rewritten, and the world-confound
   claim confined to the Theoria columns where it still holds.

3. **`fig07` had the wrong A0′.** `PLAN.md` §2 identified A0′ as the battery run
   `a0-spike`. A0′ is `cold-start-a0/prime/`, which was on disk in P-21's own
   worktree. `a0-spike` is a separate A0 cold start on a different world run by
   the other track. The two readings say opposite things, and the P-21 reading
   would have headlined a comparison `battery/REPORT_V1.md` explicitly forbids
   (K2 0.000 over 3 adversarial gaps against K2 1.000 over 39960 exhaustive
   cases). Retargeted; the correction is written into `PLAN.md` §2 with P-21's
   reasoning left visible.

## What P4 added

* **`fig02` gains the theoria arm.** P-21 predicted this would be "one entry in
  `sources.py` and zero renderer changes". It was zero renderer changes and
  *not* one entry: the theoria ledger is `LEDGER_FORMAT v1.0`, a third dialect
  whose `model_call` rows carry no top-level cost (dollars nested under
  `response`). Folding it into `_classify` would have meant teaching that
  function to accept a schema it was written to reject. The arm publishes
  `cost_curve.json` for this purpose; a second loader reads that.

  Three things this forced onto the plate: the arms are **not priced in the same
  unit** (5 desk calls covered 7 actions; the panel-A gap is not a markup); two
  attempts were **billed and abandoned**, USD 2.038212, their manifests
  recording `outcome: null`; and the arm's dollars and the repo price table
  **disagree by −8.3 %**, USD 0.4368 of it a known table defect.

* **`fig04_a3_transfer`** — P-21 declared 图4 out of scope; P4's brief puts it
  back in and the data has been finished since P-17.

* **`theme.check_no_mathtext`.** P4's own first draft of fig02's caveat read
  `$0.9025 ... against $0.1459` and rendered as italic `0.9025...against0.1459`
  — matplotlib parses `$...$` as mathtext and eats the dollar signs. It is
  *deterministically* wrong, so two byte-identical builds both carry it and gate
  3 stays green. Now a raise, for every figure.

* **`verify.sh` gate 7** — no figure script reaches the filesystem directly. A
  bare `open()` is an unhashed read, and a figure with an unhashed read keeps
  building green while its input drifts.

## Status

All six green; `verify.sh` green on all seven gates. Narrative and the full gap
list are in `figures/RUN_STATE.md`.

| figure | state |
|---|---|
| `fig02_bill_shape` | green, two arms |
| `fig03_capability_spectrum` | green, 38 × 5 = 190 cells |
| `fig04_a3_transfer` | green, 9 meter lines |
| `fig05_a2_repair_loop` | green, 6 beats + 2 prelude |
| `fig06_concept_timeline` | green, 25 adjudications over 6 lanes |
| `fig07_a0_vs_a0prime` | green, retargeted to `cold-start-a0/prime` |

## Three more defects, found in P4's own work after the figures built

The determinism gate was green through all of these. It proves reproducibility,
not correctness — the plates had to be rendered and read.

1. **A caveat rendered as mathtext** (`theme.check_no_mathtext`, above).
2. **SVG newlines were platform-dependent.** matplotlib writes SVG through a
   text-mode handle: CRLF here, LF on Linux. `.gitattributes` stores LF, so a
   fresh checkout plus a Windows rebuild would have failed gate 6 with nothing
   to fix. `theme.save` pins the newline at the writer.
3. **One clip-path id moved between builds.** `svg.hashsalt` pins most
   generated ids, but for an artist clipped by a *path* matplotlib keys the id
   on `id(clippath)` — a memory address the salt cannot reach. One id in one
   figure differed; `theme.save` now canonicalises generated ids to a stable
   sequence.

And two that made `verify.sh` itself unreliable rather than the figures:
`build_all.py` printed a `†` through a stdout that falls back to the locale
codec when redirected, so the gate died on a zh-CN box while an interactive run
succeeded; and `--list` emitted CRLF, so gate 5 built paths with a trailing
carriage return and reported every artefact missing while the build had just
written it. Gate 7's first version was a regex whose first finding was the
phrase "never ``open()``" in a docstring — it parses the AST now.
