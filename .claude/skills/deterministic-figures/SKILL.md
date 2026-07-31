---
name: deterministic-figures
description: Build paper figures that are byte-identical across runs, from a declared+hashed data registry through a CSV audit layer, with one accessible palette in light and dark. Use when adding or changing a figure in figures/, when a figure must be reproducible for a release manifest, or when a figure's numbers need to be auditable without reading plotting code. Triggers on "figure", "plot", "chart", "图2/图3/图5/图6", "capability spectrum", "bill shape", "regenerate figures", "verify.sh".
---

# Deterministic paper figures

Distilled from P-21 (`figures/`). The problem this solves is specific to this
repository: **determinism is a requirement, not a nicety** (`CLAUDE.md`), and the
Phase 4 release manifest publishes every tracked file — so a figure that changes
when nothing changed is a defect, and a figure whose inputs are unhashed is a
figure that can go stale silently.

## The pipeline, and why each stage exists

```
data on disk  ──►  extract  ──►  figures/csv/<fig>.csv  ──►  render  ──►  out/{light,dark}/<fig>.{svg,png}
   (read-only)                      (the audit surface)
```

The **CSV layer is not decoration.** Two jobs:

1. A reviewer checks the number that went into the picture without reading
   plotting code.
2. It localises determinism failures. If images differ but CSVs match, the bug
   is in the renderer; if the CSVs differ, extraction is not deterministic.
   Without the layer you get "the PNG changed" and no idea why.

## Adding a figure — the checklist

1. **Plan before code.** One entry in `figures/PLAN.md`: the claim it serves
   (cite `Theoria.md` §3.2), a table of source paths with what is taken from
   each, the shape, the CSV columns, and — separately — *what must survive into
   the picture*. That last item is where the honesty goes; see below.
2. **Declare every source** in `figures/sources.py`. Never `open()` a path in a
   figure script. An undeclared read is an unhashed read.
3. **Write the module** against the contract:
   ```python
   NAME = "figNN_slug"          # must equal the filename
   def build() -> dict:         # writes CSV, then 2 themes x 2 formats
       return {"csv": path, "images": [...4...], "notes": [...]}
   ```
4. **Register it** in `build_all.py`'s `FIGURES` tuple — explicit order, never
   filesystem discovery.
5. **Run `figures/verify.sh`** until green, and commit `figures/SOURCES.sha256`.

## Determinism: the knobs that actually bite

All already pinned in `figures/theme.py`; this is the list so you recognise a
regression.

| trap | fix |
|---|---|
| SVG `<dc:date>` — matplotlib stamps wall-clock | `fig.savefig(..., metadata={"Date": None})` |
| SVG element ids salted per process | `rcParams["svg.hashsalt"]` pinned |
| System font substitution changes glyph path data | `font.sans-serif = ["DejaVu Sans"]` (bundled) + `svg.fonttype = "path"` |
| PNG `Software` chunk carries the matplotlib version | fixed `metadata={"Software": ...}` |
| `bbox_inches="tight"` makes output size depend on text extents | never use it; use constrained layout |
| `path.simplify` is threshold-dependent | `False` |
| dict / set iteration order | sort every key list explicitly |
| `datetime.now()`, `time.time()`, `random` | banned in figure scripts. Run stamps live in `figures/runs/`, never inside an artefact |
| machine-local absolute paths leaking from JSON artefacts into CSV | strip to repo-relative before writing |
| CRLF rewriting on Windows checkout | `figures/.gitattributes` pins LF on `*.csv`, `*.svg` |

Verify by building twice into separate trees and `diff -r`. That is gate 3 of
`verify.sh`. Gate 6 additionally diffs the *committed* tree against a fresh
build, so a stale committed figure cannot hide behind a green determinism check.

## Style: one system, two themes

`figures/theme.py` is the only place style lives. Import it; do not set
rcParams in a figure script.

* `apply_theme("light"|"dark")` → returns that theme's palette and applies it.
  Build the figure **fresh per theme**; never reuse a `Figure`.
* `save(fig, NAME, theme)` → SVG + PNG, deterministic metadata, closes the fig.
* `write_csv(NAME, header, rows)` → LF newlines, `None` → empty string.
* Categorical hues are assigned in **fixed slot order, never cycled**.
  `series_colours(theme, n, all_pairs=True)` **raises above 3** — past three
  slots a form where every pair is simultaneously visible (scatter, bubble,
  small multiples) cannot clear the colour-vision-deficiency floors under any
  ordering. Fold the tail into "other", facet, or add secondary encoding.
* Identity is never colour-alone: pair colour with `series_marker(i)` /
  `series_hatch(i)`, and a legend is present for ≥ 2 series.
* Text wears text tokens (`ink`, `ink_secondary`, `muted`), never a series
  colour.
* `STATUS` colours are reserved and always ship with a text label.
* Sequential = one hue light→dark; diverging = two hues with a **neutral** grey
  midpoint. Never a rainbow, never a hue at the diverging midpoint.
* `sequential_steps(theme, n, ordinal=True)` clamps the end nearest the surface
  so the palest (light) / darkest (dark) step still clears 2:1.

## The rule that matters more than any of the above

**Never render an absent value as zero.** `battery/REPORT_V0.md`'s entire
complaint is that a metric can be perfect and still measure the wrong thing; a
structural gap drawn as a `0` bar is the graphical form of exactly that error.

`theme.ABSENCE` and `theme.absence_handles()` give the three distinct states the
battery actually distinguishes:

| state | encoding |
|---|---|
| `ok` | colour on the ramp |
| `not-applicable` (structural absence) | hatched, no fill |
| `insufficient-data` | outlined, no fill |

And the caveats that must not travel separately from the number go on the
figure's face via `theme.caveat(fig, text, theme=...)` — not into a caption
somebody will drop. Precedents worth copying:

* a K2 of `0.000` beside `1.000` is meaningless without `n = 3` and `n = 39960`
  printed next to them (`battery/REPORT_V1.md`);
* K4 evidence coverage is never shown without K2 held-out accuracy beside it
  (`battery/METRICS.md`, gaming audit);
* a cost curve that stops at turn 1 because the API died is not a cheap run —
  draw those runs dashed and say why;
* a cross-arm comparison in which every Theoria run is a self-built world is
  confounded by construction — banner, not footnote.

## Territory

Figure work writes **only** inside `figures/`. Every data directory
(`battery/`, `baseline-arms/`, `cold-start-a0/`, `cold-start-a2/`, `a0-spike/`,
`theoria-arm/`) is read-only, and `cold-start-a0/` belongs to the other track.
Read the pile cut in `CLAUDE.md` before adding a source: no figure may read
anything belonging to a sealed game, including upstream artefacts.
