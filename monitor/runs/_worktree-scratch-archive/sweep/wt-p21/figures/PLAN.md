# figures/PLAN.md — P-21 paper figure pipeline

Planning document, written before any figure code. Baseline: `Theoria.md` §3.2's
figure list. Scope: five figures, each produced by one **deterministic generation
script** through a **CSV intermediate layer**.

```
data on disk  ──►  extract  ──►  figures/csv/<fig>.csv  ──►  render  ──►  figures/out/{light,dark}/<fig>.{svg,png}
   (read-only)      (script)        (the audit surface)      (script)
```

The CSV layer is not decoration. It is where a reviewer checks the number that
went into the picture without reading plotting code, and it is what makes the
byte-identity check meaningful: if the render is stable but the extract is not,
the CSV diff says so first.

---

## 0. Standing rules for every figure

| rule | why |
|---|---|
| **Read-only on every data source.** No script in `figures/` writes outside `figures/`. | Territory: P-21 owns `figures/` and nothing else. |
| **Every source is hashed.** `figures/SOURCES.sha256` records the sha256 of every input file, regenerated with the figures. | A figure whose input silently changed is a figure that lies. |
| **Two runs, byte-identical.** `figures/verify.sh` regenerates everything twice into separate trees and diffs. | The determinism requirement, made executable. |
| **Tracked sources only.** | The worktree checkout must be able to build the figures. `baseline-arms/out/shards/` and `out/campaign/` are **untracked** in `master` and therefore excluded — see §3. |
| **English labels.** | Font determinism: matplotlib's bundled DejaVu Sans has no CJK coverage, so CJK text renders as tofu boxes and the SVG path data depends on whatever system font is substituted. Prose stays bilingual; figures do not. |
| **No `not-applicable` cell is drawn as zero.** Absent is drawn as absent. | `battery/REPORT_V0.md`'s whole complaint: a metric can be perfect and still measure the wrong thing. Rendering a structural gap as a 0 bar is the graphical form of that error. |

### Determinism knobs (all in `figures/theme.py`)

* `mpl.rcParams['svg.hashsalt']` pinned — otherwise SVG element ids are salted per process.
* `svg.fonttype = 'path'` — glyph outlines embedded, no viewer-side font dependency.
* SVG saved with `metadata={'Date': None}` — matplotlib otherwise stamps `<dc:date>`.
* PNG saved with a fixed `Software` metadata string — no timestamp chunk.
* Fixed `figure.dpi`, `savefig.dpi`, figure size, and `Agg` backend.
* No `Date.now()`-equivalent anywhere in a figure script; the run stamp lives in
  `figures/runs/`, never inside an artefact.
* Dict iteration is never trusted for ordering — every series is explicitly sorted.

### Style

Accessible palette, two themes (`light`, `dark`), both emitted for every figure.
Palette requirement: distinguishable under deuteranopia/protanopia, and every
foreground/background pair at or above WCAG AA contrast. Categorical encoding is
never carried by colour alone — marker shape or hatch always doubles it.

---

## 1. `fig06_concept_timeline` — 图6 concept-birth timeline

**Claim it serves.** §3.2 item 6: *一个概念从证据到入册，带时间戳* — a concept's
path from evidence to admission, with timestamps.

**Sources**

| path | form | what is taken |
|---|---|---|
| `cold-start-a0/THEORIZE_LOG.md` | Markdown | §`Revision history` table (rev / when / trigger / change); the `O-`, `R-`, `L-`, `P-`, `E-` heading blocks, each carrying an id and a **verdict** (`accept` / `reject` / `entailed` / `probe-pending` / `admitted anyway`) |
| `cold-start-a0/artifacts/concept_accounts.json` | JSON | per-concept `verdict`, `script_delta_bits`, `laws_naming_it`, `rules_targeting_it` — the compression account behind each admission |
| `cold-start-a0/artifacts/candidates.jsonl` | JSONL | the 28 proposals as they arrived from the engines: the *evidence* end of the timeline |
| `git log --follow cold-start-a0/THEORIZE_LOG.md` | git | committer timestamps of the 5 revisions — the only real wall-clock axis this log has |

**Shape.** Horizontal swimlane / event timeline. One lane per concept
(`Button`, `Door`, `Cart`) plus a lane for the milestone axis (M1…M6). Events
are marks on the lane: *proposed* (engine emits candidate) → *adjudicated*
(verdict, with the verdict encoded by marker shape) → *admitted to the manual* →
*probed / obligation discharged*. Milestone boundaries are vertical rules; the
five git commit timestamps are ticks on a secondary axis underneath.

**The honest bit that must survive into the picture.** The log's own revision
table says the manual was revised **zero** times by `certify` — the loop was not
exercised. The three iterations that did happen were *compiler* defects, not
manual revisions. The figure draws those on a separate, visually subordinate
lane labelled as such. A timeline that showed three revisions without saying
they were the compiler's would overstate the loop.

**CSV** `csv/fig06_concept_timeline.csv` — columns
`lane, order, milestone, commit_ts, event_kind, concept, item_id, verdict, label, delta_bits`.

**Axis honesty.** Milestones M1…M6 are ordinal, not clock time; the git commits
are clock time but only cover the later edits. The figure therefore uses an
**ordinal event axis** with the commit timestamps annotated, and says so in the
caption rather than faking a linear clock.

---

## 2. `fig07_a0_vs_a0prime` — coverage × accuracy, A0 vs A0′

**Claim it serves.** The strongest controlled contrast the repository currently
holds, and the graphical form of `REPORT_V0.md`'s headline: *a metric can be
perfect and still be measuring the wrong thing.*

**Which pair is A0′.** Two readings were checked against the data:

* `a0-base` vs `a0-no-button` — a within-world ablation, but `a0-no-button`'s
  K2 is `insufficient-data`, so it yields **no** accuracy contrast. Rejected.
* `a0-base` (A0) vs `a0-spike` (A0′) — both score **K4 = 1.000**; K1 replay
  0.987 vs 1.000; K2 held-out **0.000 vs 1.000**. This is the contrast.

**Sources**

| path | what is taken |
|---|---|
| `battery/artifacts/capability_spectrum.json` | `runs.{a0-base,a0-spike,a0-no-button,a2-*}.metrics.{K1,K2,K4,K5,K14}` with their `support` blocks (`agree`/`pairs`, `annotated`/`unannotated`/`min_witnesses`) |
| `cold-start-a0/artifacts/score_vs_truth.json` | the 233/236 agreement and the three pairs R-05 named |
| `battery/REPORT_V1.md` | the sampling-frame caveat, quoted verbatim into the caption |

**Shape.** Coverage–accuracy plane: x = K4 evidence coverage, y = accuracy, with
**two accuracy series** plotted per run — K1 (replay, on-trace) and K2 (held-out,
off-trace) — joined by a vertical drop line. The drop line *is* the finding: on
A0 it falls from 0.987 to 0.000 at x = 1.000. All theory-bearing runs are
plotted; A0 and A0′ are emphasised.

**Non-negotiable annotation.** `REPORT_V1.md` states that A0's K2 denominator is
**3** adversarially-chosen uncovered pairs and A0′'s is **39960** exhaustively
enumerated pairs, and that comparing the two numbers directly is wrong. Each
point is therefore labelled with its `n`, and the caption carries the caveat.
A figure that showed 0.000 beside 1.000 without the denominators would be the
most misleading object this pipeline could produce.

**CSV** `csv/fig07_a0_vs_a0prime.csv` — columns
`run, arm, metric, value, status, agree, pairs, annotated, unannotated, frame_note`.

---

## 3. `fig02_bill_shape` — 图2 bill shape (first cut)

**Claim it serves.** §3.2 item 5: *图 2 账单形状（三臂逐回合成本曲线）* — the
per-turn cost curve for three arms. C2's signature: understanding is bought
early and spent late.

**Sources**

| path | form | what is taken |
|---|---|---|
| `baseline-arms/ledger.jsonl` | JSONL, 560 records, **tracked** | model-call records (`usage` present): `run_id`, `game_id`, `model`, `step_idx`, `total_cost_usd`, `usage.{input,output,cache_creation,cache_read}_tokens`, `timestamp` |
| `baseline-arms/out/pilot_*.json` | JSON, **tracked** | per-run roll-ups: `cost_usd`, `model_calls`, `actions_ok`, `actions_failed`, `outcome`, `budget` — used only to cross-check the curve's endpoint against the ledger's own total |

**Explicitly excluded, and why.** `baseline-arms/out/shards/ledger.*.jsonl` (the
envelope campaign ledgers) are **untracked in `master`**. A figure built on them
could not be rebuilt from a clean checkout, which fails the determinism rule at
its root. They are named in `SOURCES.md` as a known-absent input with the exact
path to drop in, and the extractor takes a `--ledger` list so adding them is
configuration, not code.

**Shape.** Cumulative cost (USD) against turn index, one line per run, grouped
and coloured by model (haiku / sonnet / opus) — the model ladder is v0's
substitute for the missing Schema arm (`battery/DECISIONS.md` D-B-004, and
`REPORT_V0`'s note that this substitute is weaker). Faceted by game. A second
panel gives the same curves normalised to fraction-of-total-spend against
fraction-of-run, which is the shape E2's front-load index reads.

**Two warnings drawn, not buried.**
1. Runs that ended on `model_error` or `api_unusable` are drawn dashed. A curve
   that stops at turn 1 because the API died is not a cheap run.
2. `REPORT_V0`: 27–45% of pilot steps failed outright, and E5 cost-per-action is
   a price list (δ = +1.000 tracking token pricing, nothing else). The panel
   carries the failure rate as a rug along the x-axis so the reader meets the
   confound before the curve.

**Interface left open for the theoria arm.** The extractor's arm axis is a
column, not a hard-coded triple: `arm` comes from the record. `theoria-arm/runs/`
carries no cost ledger yet; the moment it does, adding it is one entry in
`sources.py` and zero changes to the renderer. This is stated in the script
docstring so the next author does not rewrite it.

**CSV** `csv/fig02_bill_shape.csv` — columns
`arm, game_id, model, run_id, turn, cost_usd, cum_cost_usd, frac_of_run, frac_of_spend, failed_step, outcome`.

---

## 4. `fig03_capability_spectrum` — 图3 capability spectrum (first cut)

**Claim it serves.** §3.2 item 5: *图 3 电池能力谱*. The family × arm matrix from
the battery report.

**Sources**

| path | what is taken |
|---|---|
| `battery/artifacts/capability_spectrum.json` | `cards` (id, family, direction, tier, definition, unit), `runs.*.metrics.*` (value + status), `coverage.*.by_status`, `provenance` |
| `battery/artifacts/arm_contrast.json` | which of the 38 metrics have cross-arm overlap (7 of 38) and the control arm |
| `battery/artifacts/gaming_audit.json` | tier demotions — K4 must never be rendered without K2 beside it |

**Shape.** Heatmap: rows = metrics grouped by family (economy / epistemic /
planning / exploration / metacognition per the `family` field), columns = arms
(`bare_cc`, `theoria_a0`, `theoria_a0_spike`, `theoria_a2`). Cell = arm-median of
the metric, normalised **within a row** (metrics have incompatible units) and
oriented by the card's `direction` so that "further right on the colour ramp" is
always "better".

**Four things the cell encoding must distinguish** — this is why it is not a
plain heatmap:

| cell state | encoding |
|---|---|
| `ok` | colour on the sequential ramp |
| `not-applicable` (structural absence) | hatched, no colour |
| `insufficient-data` | outlined, no fill |
| metric demoted to reference tier by the gaming audit | row label carries a marker and the tier is a row-group band |

Coverage counts (`n` runs contributing) are printed in-cell. The 31 of 38
metrics with no cross-arm contrast are visually banded — `arm_contrast.json`
puts a number on the missing Schema arm and the figure should show it.

**CSV** `csv/fig03_capability_spectrum.csv` — columns
`family, metric, tier, direction, arm, n_runs, median, normalised, status, note`.

---

## 5. `fig05_a2_repair_loop` — 图5 the DC22 case: six-beat repair account

**Claim it serves.** §3.2 item 5: *图 5 DC22 案例（那条类型检查通过而对世界为假的
定理，及其修复回路）*. This repository's DC22 exhibit is `cold-start-a2` — a
self-built world isomorphic to DC22's failure structure (the `loop_ledger.json`
`authority` field records the INC-004 ruling and states no upstream DC22 artefact
was read; the pile seal is intact).

**Sources**

| path | what is taken |
|---|---|
| `cold-start-a2/artifacts/loop_ledger.json` | `beats[]`: `beat` (M0, M5, L1…L6), `name`, `claim`, `status`, `detail{}`, `evidence[]` — the account itself |
| `cold-start-a2/artifacts/repair_report.json` | what the repair changed |
| `cold-start-a2/artifacts/probe_report.json` | L3's 5 designed / 4 executed / 4 refuted / 1 not-separable |
| `cold-start-a2/artifacts/refutation.json` | L1's solved 18-action episode against the `unsolvable` theorem |
| `battery/artifacts/capability_spectrum.json` | K12 (6/6 beats closed on `a2-probed`, 0/6 on `a0-spike`) and K13 (0.262 patch vs 1.095 rebuild) — the two numbers that turn the story into a measurement |

**Shape.** Left-to-right beat flow: M0 → M5 → L1 → L2 → L3 → L4 → L5 → L6, each
beat a node carrying its status and its one decisive number
(`plan: SAT/UNSAT`, `replay: 184`, `located_at: 11`, `probes 5→4 executed, 4
refuted`, `stale died / new theorem: pocket_unreachable`, …). Below the flow, an
**account strip**: environment actions spent per beat, ending in K13 = 0.262 —
localised repair cost a quarter of what the theory cost. The a0-spike rebuild
strategy (K13 = 1.095, 0/6 beats) is drawn as a contrast bar so the reader sees
what the six beats buy.

**The exhibit's point must be legible without the caption**: at M5 the manual
replays the play record at 100% *and* Lean signs an axiom-free `unsolvable`
theorem *and* the world contradicts it. Those three facts are drawn together on
the M5 node, because their co-occurrence is the entire DC22 phenomenon.

**CSV** `csv/fig05_a2_repair_loop.csv` — columns
`order, beat, name_en, status, claim, key_metric, key_value, actions_spent, evidence`.

---

## 6. Build and verification

```
figures/
  PLAN.md            this file
  README.md          how to build, how to read each figure
  SOURCES.md         every input path, tracked/untracked, and what depends on it
  SOURCES.sha256     generated: sha256 of every input, regenerated with the figures
  theme.py           palette, dual theme, save(), determinism knobs
  sources.py         path registry + hashing + repo-root resolution
  build_all.py       runs every figure script in a fixed order
  fig02_bill_shape.py
  fig03_capability_spectrum.py
  fig05_a2_repair_loop.py
  fig06_concept_timeline.py
  fig07_a0_vs_a0prime.py
  csv/               generated intermediate layer
  out/{light,dark}/  generated SVG + PNG
  runs/<UTC>-p21/    this run's trace
```

`figures/verify.sh` is the Stop-hook gate and does exactly this:

1. build everything into a scratch tree (pass A);
2. build everything again into a second scratch tree (pass B);
3. `diff -r` A against B — **any** difference fails;
4. recompute `SOURCES.sha256` and diff it against the committed copy — a source
   that moved under the figures fails;
5. verify every declared artefact exists: 5 figures × 2 themes × 2 formats = 20
   images, plus 5 CSVs.

Exit non-zero on any failure, with the offending path named.

## 7. Order of work

1. `theme.py` + `sources.py` + `build_all.py` + `verify.sh` — the contract.
2. The five figure scripts, in parallel, each against that contract.
3. `verify.sh` green, twice.
4. `README.md`, `SOURCES.md`, `RUN_STATE.md`, `MANIFEST`, `PARTNER_SYNC`.

## 8. Known limits, declared up front

* **The three-arm bill shape has two arms.** There is no Schema arm
  (`baseline-arms/SCHEMA_LOCATE.md`) and the theoria arm has no cost ledger yet.
  Figure 2 ships as `bare_cc` × model-ladder and says so on its face.
* **Every Theoria run is a self-built world.** Arm and world are perfectly
  confounded in every cross-arm comparison (`REPORT_V1.md`). Figure 3 carries
  this as a banner, not a footnote.
* **图4 (transfer) is not in scope.** `cold-start-a3` holds the transfer work;
  P-21's brief names figures 2, 3, 6 plus the A0/A0′ and A2 figures. Figure 4 is
  left to the arm that owns the data.
* **Timestamps are coarse.** The concept timeline's only wall-clock source is git
  committer time on five commits; the rest is milestone ordinal.
