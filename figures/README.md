# figures/ — the paper plates, and the pipeline that guarantees them

Six figures for the Phase-1 write-up. Each is produced by one deterministic
script, through a CSV intermediate layer, into two themes and two formats.

```
data on disk  ──►  extract  ──►  figures/csv/<fig>.csv  ──►  render  ──►  out/{light,dark}/<fig>.{svg,png}
   (read-only)                      (the audit surface)
```

## Build

```bash
python figures/build_all.py               # all six, into figures/{csv,out}
python figures/build_all.py --list        # the fixed build order
python figures/build_all.py --only fig03_capability_spectrum
bash    figures/verify.sh                 # the gate: build twice, diff, check
python  figures/manifest.py --run-dir figures/runs/<UTC>-<prompt-id>
```

`verify.sh` is the thing to run before committing. It builds everything twice
into separate trees and requires the results to be **byte-identical**, checks
the committed tree against a fresh build so a stale figure cannot hide behind a
green determinism check, re-hashes every declared input, and refuses a figure
script that touches the filesystem outside `sources.py`.

## The six

| figure | claim it serves | the thing it must not let you conclude |
|---|---|---|
| `fig02_bill_shape` | C2: understanding is bought early and spent late | that theoria costs 6× more per turn. **The two arms are not priced in the same unit** — a `bare_cc` turn buys one model call that picks one action; a theoria turn buys a desk call that theorises across the run. 5 calls covered 7 actions. |
| `fig03_capability_spectrum` | the battery's family × arm matrix | that an empty cell is a bad score. 96 of 190 cells are `not-applicable` — structural, drawn hatched — and 9 are `insufficient-data`, drawn outlined. Neither is ever a zero. |
| `fig04_a3_transfer` | C3: the domain is what travels between levels | that transfer saved 97 % of everything. The bottom three meter lines are 1:1, 3:3, 1:1 and are drawn for that reason; two of the control arm's five theorize rounds were toolchain tax, not world-learning. |
| `fig05_a2_repair_loop` | the DC22 case: a machine-checked theorem false of the world, and its repair | that the loop scored 8/8. `loop_ledger.json` holds eight beats; the loop proper is six. M0 and M5 are prelude and are drawn as prelude. |
| `fig06_concept_timeline` | a concept's path from evidence to admission | that the repair loop was exercised. The manual was revised **zero** times by `certify`; the three iterations that happened were compiler defects, and they live on a subordinate lane that says so. |
| `fig07_a0_vs_a0prime` | reversibility beats coverage | that this is a controlled test. It is confounded by construction: two variables changed, not one, and the objection that bites is analytic — A0′'s toggle was *designed* so every case would have a witness. It demonstrates the mechanism; it does not test it. |

Each row's right-hand column is on the figure's face, via `theme.caveat`, not in
a caption. That is deliberate: captions get dropped when a plate is pasted into
slides, and every one of those caveats is the difference between the figure
being informative and being misleading.

## How to read the CSV layer

`figures/csv/<fig>.csv` holds every number in the corresponding picture. It
exists so a reviewer can check the figure without reading plotting code, and so
that a determinism failure localises: if the images differ but the CSVs match,
the bug is in a renderer; if the CSVs differ, extraction is not deterministic.

Several of the CSVs carry a state column (`value_kind`, `value_state`, or
`status`) distinguishing a **measured zero** from a **structural absence** from
**insufficient data** from a value this pipeline could not source at all. That
column is the point. `battery/REPORT_V0.md`'s complaint is that a metric can be
perfect and still measure the wrong thing; a structural gap rendered as a `0`
bar is the graphical form of exactly that error, and the CSV is where the
distinction is checkable rather than merely drawn.

## Adding a figure

1. Plan it in `PLAN.md` first — the claim it serves, the sources, the shape, the
   CSV columns, and separately **what must survive into the picture**.
2. Declare every source in `sources.py`. Never `open()` a path in a figure
   script; `verify.sh` gate 7 will catch you, and the reason is that an
   undeclared read is an unhashed read.
3. Write the module against the contract: `NAME` matching the filename, and
   `build() -> {"csv": ..., "images": [...4...], "notes": [...]}`.
4. Register it in `build_all.py`'s `FIGURES` tuple. Explicit order, never
   filesystem discovery.
5. Run `verify.sh` until green; commit `SOURCES.sha256`, the CSVs and the images.

Style lives in `theme.py` and nowhere else. Import it; do not set `rcParams` in
a figure. Figure text is **English** — matplotlib's bundled DejaVu Sans has no
CJK coverage, so CJK renders as tofu and the SVG path data starts depending on
whatever system font gets substituted. Bilingual strings survive in the CSVs.

## Determinism, and the failure that survives it

Every knob that would let matplotlib stamp a timestamp, salt an element id, or
reach for a system font is pinned in `theme.py`; `PLAN.md` §0 has the table.

Worth knowing about the one class of bug the byte-identity gate cannot catch: a
figure can be **deterministically wrong**. P4's first draft of fig02's caveat
read `$0.9025 ... against $0.1459`, and matplotlib parsed `$...$` as mathtext —
it rendered as italic `0.9025...against0.1459`, dollar signs gone, two numbers
run together. Both builds produced that identically, so gate 3 stayed green.
`theme.check_no_mathtext` now raises on it. Gates prove reproducibility, not
correctness; look at the plates.

## Territory and discipline

This directory writes only inside itself. Every data directory is read-only, and
`cold-start-a0/` (including `prime/`) belongs to the theory-compiler track.

No figure reads anything belonging to a **sealed-pile** game. Sources are
self-built worlds or the four development-pile games; `fig03` stamps the pile
cut's sha256 from the battery's own provenance block. `SOURCES.md` records what
is absent and why, and where two artefacts disagree about a number — in three
places they do, and in all three both numbers travel.
