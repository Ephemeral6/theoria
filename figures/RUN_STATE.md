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
