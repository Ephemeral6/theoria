# figures/PLAN.md — paper figure pipeline

Planning document, written before any figure code. Baseline: `Theoria.md` §3.2's
figure list. Scope: **six** figures, each produced by one **deterministic
generation script** through a **CSV intermediate layer**.

> **Provenance of this document.** §0–§8 are P-21's, written before P-21's code
> and left as written. P-21 never reached `master`: its work sat uncommitted in a
> worktree, and the `deterministic-figures` skill was distilled from it. **P4
> (`P4-figures`, worker W-1611) salvaged that pipeline rather than re-deriving a
> second, divergent one**, finished it, and added figure 4.
>
> Where P4 reversed a P-21 decision, the reversal is written **into the section
> that made it**, marked `P4 CORRECTION`, with P-21's reasoning left visible
> above it — a plan whose wrong turns have been quietly deleted teaches nobody.
> §9 is the full changelog.

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

> **P4 CORRECTION — both readings were wrong, because A0′ was not looked for.**
>
> A0′ is **`cold-start-a0/prime/`**, and it was on disk in P-21's own worktree
> while the section above was being written. The search went to `battery/`, found
> two battery runs whose ids looked like an A0 pair, and stopped.
>
> `a0-spike` is **not** A0′: it is a *separate* A0 cold start, on a *different*
> world, run by the *other track*
> (`papers/phase1-workshop/sections/03_a0.md`). `monitor/prompts/P-16` names
> `prime/A0P_REPORT.md` directly, and
> `papers/phase1-workshop/figures/data/fig2_coverage_accuracy.json` is an
> already-extracted form of the real contrast.
>
> The correction matters because the two readings say opposite things. Under the
> P-21 reading the story is *A0 has a coverage problem and A0′ does not*. Under
> the real pair it is **A0′ saw 46.9 % of the state-action pairs A0 saw
> (107/228 against 233/236) and was more accurate (1.000 against 0.987)** —
> re-witnessability beating coverage, which is what `A0P_REPORT.md` §1 says the
> experiment was built to show: *"The variable is not how much was seen. It is
> whether what was seen could be seen again."*
>
> The `a0-spike` numbers stay on the plate as a supporting panel, under
> `REPORT_V1`'s denominator warning — which is the reason the P-21 reading was
> unsafe even on its own terms: comparing a K2 of 0.000 over **3** adversarial
> gaps against a K2 of 1.000 over **39960** exhaustive cases is a comparison
> `REPORT_V1` explicitly forbids, and P-21's §2 planned to headline exactly that.

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

> **P8 CORRECTION.** There is no `--ledger` list and there never was: `fig02`
> has no `argparse` at all. P-21 described an interface it planned and did not
> build, and the sentence survived because nobody had reason to run the command
> it describes. What is true as of P8 is stronger — a shard dropped into
> `baseline-arms/out/shards/` is picked up by the `envelope_ledger` rule with no
> configuration and no code, including one whose filename nobody wrote down.

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

> **P4: the arm arrived, and the interface did not fit.** `theoria-arm/runs/`
> does carry cost data, and P4 draws it — the plate has two arms now. But the
> prediction above was wrong in a way worth recording: the theoria ledger is
> `LEDGER_FORMAT v1.0`, a **third record dialect** whose `model_call` rows carry
> no top-level cost at all (the dollars are nested under `response`). Adding it
> to `OPTIONAL_LEDGER_KEYS` would have made `_classify` accept a schema it was
> written to reject. The arm publishes `cost_curve.json` for exactly this
> purpose, so P4 reads that through a second loader and leaves `_classify`'s
> refusal intact. *One entry in `sources.py` and zero renderer changes* held for
> the renderer and not for the extractor.
>
> Three further things the second arm forced onto the plate, all in §8:
> the two arms' **costs are not the same quantity**; two attempts were **billed
> and abandoned** ($2.04) and their own manifests record `outcome: null`; and the
> arm's dollars and the repo's price table **disagree by −8.3 %**.

> **P8: the interface was the defect, not the arm.** P4's note above closes with
> the extractor being the part that did not generalise. It was worse than that.
> Both the roll-up list and the theoria run list were **hand-written tuples of
> source keys**, and by the time P8 listed the directories both had gone stale:
>
> * `ROLLUP_KEYS` named four of the six tracked `pilot_*.json` roll-ups. The two
>   it missed carry outcomes for `bare_cc-g50t-claude-sonnet-5-ddabe772`
>   (`budget_exhausted`) and `bare_cc-sk48-claude-sonnet-5-9022a076`
>   (`model_error`). Both runs were therefore drawn **dotted — "outcome unknown,
>   not 'fine'"** — while their outcomes sat committed in the repository, and one
>   of them should have been **dashed**, which is this plate's own warning that a
>   curve stopped because the API died rather than because the run was thrifty.
>   *The figure was withholding one of the two warnings it exists to draw.*
> * `THEORIA_RUNS` named three of the four run directories that carry a
>   `cost_curve.json`. The fourth is a preflight whose curve is empty — and
>   `_load_theoria_curves` already had a branch for exactly that case which had
>   **never once executed**, because the only run that reaches it was not in the
>   tuple. A hand-maintained list does not merely miss data; it leaves the code
>   for the missing case unexercised, so nobody finds out whether it was right.
>
> Both are the same shape as P4's three defects — *an upstream artefact moved and
> the figure code did not know* — which is the argument for fixing the shape
> rather than the two instances. `sources.py` now declares these three families
> **by rule** (`DISCOVERY`): a directory, a filename pattern, the members
> required inside it, and a **floor**. Every file a rule finds becomes a real
> `Source` and is hashed into `SOURCES.sha256` exactly as a hand-written one is,
> so nothing is read unhashed; what changed is only who enumerates the family.
>
> The floor is what keeps this honest. A glob that comes back empty is
> indistinguishable from a family that *is* empty, so each rule records how many
> members were on disk when it was written and `verify.sh` gate 0 fails below it.
> Absent-by-design members (the untracked envelope shards) stay declared through
> the rule's `expected` list, so `SOURCES.sha256` still *names* them as absent
> rather than forgetting the input was ever expected.
>
> **A gate cannot catch this class, so it got a probe.** Gates 1–7 were all green
> on the tree that had these two defects: both builds byte-identical, committed
> tree equal to a fresh build, every source hash unchanged. `check_coverage.py`
> (gate 8) walks the tree itself and asks whether what is on disk reached the
> picture. It runs its own negative control first — the roll-up rule narrowed
> back to the pre-P8 four, with the probe required to fail. That control earned
> its place immediately: **the probe's first version took its disk inventory from
> the same registry the figure reads, so narrowing the registry narrowed both
> sides at once and it stayed green over the exact defect it was written for.**
> An oracle that calls the thing it audits can only prove that thing
> self-consistent.

**The three shape metrics** — front-load index, convergence point, context
growth — are on the plate as of P8, and they are **read, not recomputed**. They
are `battery/metrics/economy.py`'s E2, E3 and E4, with anti-gaming floors
(`MIN_TURNS_FOR_SHAPE = 8`: a run that ended on turn four is trivially
front-loaded), and E2 is one of Phase 4's three primary endpoints. Their
published per-run values come out of `battery/artifacts/capability_spectrum.json`.
Writing a second implementation would be writing a second definition of a
primary endpoint, and two definitions of one number is the drift `SOURCES.md`
exists to prevent.

Where they are drawn:

* **E2 and E3 are read off panel B**, as the construction that defines them
  rather than as numbers in a corner. A vertical rule at the head boundary makes
  a curve's height *there* its front-load index; a tick on each curve marks the
  turn at which the bill reached 90 % of its total. The head boundary's position
  is derived from the battery's own `head_turns / turns` support — not copied
  from `FRONTLOAD_K`, because a hand-copied fact about another file is a fact
  that will go stale.
* **E4 gets panel D**, because it is the one shape metric that is not a share of
  this plate's money: it reads the *token* series, so it survives a change in the
  price list, and it is the metric that would catch Theoria failing to be what it
  claims. Plotted against run length, since the metric's own floor is a length.
* **The turn axes are checked, not assumed.** The battery counts turns in
  model-call order (`battery/INPUT_FORMAT.md` gap 5); this plate counts
  `step_idx`. E3's crossing is marked only where the two coincide, and the check
  is reported either way. It currently agrees on all 12 markable runs — stated as
  a checked result, because that agreement is the licence to draw the marks.

**What is on the plate when the Theoria column fills in.** The theoria arm draws
a *bill* today and has **no E2/E3/E4 at all**: battery v2's five arms are
`bare_cc`, `schema_repro`, `theoria_a0`, `theoria_a0_spike` and `theoria_a2`, and
the live ARC theoria run is none of them. That is drawn as an absence carrying
its reason, never as a low score. When a battery run for the live arm lands:

1. **Nothing in `figures/` changes.** The three shape metrics are keyed on
   `run_id`; a theoria run scored by the battery attaches to its curve at the
   next build, and panel D's `other arm, scored (0)` becomes a non-zero count.
2. **Panel D gains hollow marks** and the absence column loses its `3 run(s): no
   battery run at all` line. Both counts are computed, not written down.
3. **Panel B's E3 ticks stay conditional.** The theoria arm's step axis is
   sparse — 5 desk calls across 7 actions, so 2 of 7 turns bought anything — so
   `axis_agrees` will very likely be false for it and its E3 crossing will be
   *reported and not marked*. That is the intended behaviour and not a gap to
   close: marking it would put a fraction-of-decisions on an axis of
   fraction-of-actions.
4. **The caveat's arithmetic follows automatically** — arm roster, unscored
   counts and the mismatch list are all rendered from the data.

What *would* need a decision, and is therefore not pre-decided here: whether a
theoria E2 may be compared to a `bare_cc` E2 at all, given that the two arms'
turns are not the same purchase. The plate's standing caveat says they are not,
and a front-load index computed over each arm's own turns inherits that
difference rather than cancelling it.

**CSV** `csv/fig02_bill_shape.csv` — columns
`arm, game_id, model, run_id, turn, cost_usd, cum_cost_usd, frac_of_run, frac_of_spend, failed_step, outcome`
plus, as of P8, the per-run shape block: `e2_frontload_index, e2_status,
e3_convergence_point, e3_status, e4_context_growth, e4_status, battery_turns,
turn_axis_agrees`. Each metric carries **both** a value and a status, because a
blank with `insufficient-data` and a blank with `no-battery-run` are different
facts and one empty cell for both is how an absence becomes a zero.

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

> **P4 CORRECTION — the column axis and the "no Schema arm" banner.** P-21 took
> the arm axis from `arm_contrast.json` and refused to draw at all if it
> disagreed with the spectrum. It does disagree: `arm_contrast.json` is a v1-era
> artefact that knows four arms, and battery **v2 ingested a fifth,
> `schema_repro`** — so the plate could not be built. The guard was right to
> refuse to guess and wrong about who the authority is. P4 takes the axis from
> `capability_spectrum.provenance.arms` (the artefact actually being drawn) and
> the control/treatment split from `validation_material.json`'s declared
> `control_arms` field, and reports `arm_contrast.json`'s staleness as a note
> instead of being vetoed by it. Cross-arm overlap is recomputed from the cells
> for the same reason.
>
> That fifth arm also falsified the banner. P-21 drew "NO SCHEMA ARM
> (`SCHEMA_LOCATE.md`, which says there may never be one)" across the plate;
> `REPORT_V2.md` records the Schema arm as ingested — 8 runs, 4 development-pile
> games × 2 upstream collections — and pairs it against `bare_cc` **by game**,
> which controls for the world. The banner now says that, and confines the
> world-confound claim to the Theoria columns where it still holds.

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

## 5a. `fig04_a3_transfer` — 图4 transfer: carrying the book (added by P4)

P-21 declared figure 4 out of scope (§8). P4's brief puts it back in, and the
data has been sitting finished in `cold-start-a3/artifacts/` since P-17.

**Claim it serves.** C3: the manual is `domain` and travels between levels; the
level layout is `problem` and does not. Transfer is *the domain being carried*.

**Sources.** `bill_table.json` (the like-for-like level-2 block, with `ratio` and
`saved` precomputed and a cross-level warning in its own `note` field),
`score_vs_truth.json` (accuracy with real n), `bill_l2_transfer.json` /
`bill_l2_from_scratch.json` (the bills as event sequences),
`provenance_l2_transfer.json` (6 derived / 3 supplied),
`negative_controls.json` (the safety valve).

**The comparison is `l2_from_scratch` vs `l2_transfer`** — same level, books or no
books. `l1_cold_start` is a *different level*; `bill_table.json`'s own `note`
says ratios against it "compare across levels and therefore mix in whatever
differs between them", so it is banded off if drawn at all.

**The honest bits that must survive into the picture.**

* **The bottom three meter lines do not move**: compile 1:1, certify 3:3, plan
  1:1. `A3_REPORT.md` says a table showing savings there "would be measuring
  something other than transfer". They are drawn. Their flatness is the result's
  honest half, and an axis that hides it is the wrong axis.
* **Two of the control arm's five theorize rounds were toolchain tax**, not
  world-learning — 40 % of its adjudication budget. The 5 → 0 bar overstates the
  saving by that much, and says so.
* **n = 1 per arm**, no replication, no variance. The only real sample size on
  the plate is the accuracy row: n = 248 / 252 / 252 pairs. No error bars.
* **The carrier wrote the books**, and **the blind was partially broken and
  recorded as an incident** — object names and the law's name are contaminated,
  so no cross-arm naming agreement may be claimed.
* **Levels, not games.** The two levels share a mechanism set by construction.
* **The bill is structural, not economic**: it does not price model calls, the
  largest term in a real C3 bill. The zeros are the right shape and are not
  dollars.
* `first_mismatch: null` on both negative controls and
  `also_derivable.goal_cell: null` are **absent**, not zero.

**CSV** `csv/fig04_a3_transfer.csv` — meter line, both arms, ratio, saved, and a
`note` column carrying the per-row caveat.

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
  fig04_a3_transfer.py
  fig05_a2_repair_loop.py
  fig06_concept_timeline.py
  fig07_a0_vs_a0prime.py
  csv/               generated intermediate layer
  out/{light,dark}/  generated SVG + PNG
  runs/<UTC>-<id>/   the run trace
```

`figures/verify.sh` is the Stop-hook gate and does exactly this:

1. build everything into a scratch tree (pass A);
2. build everything again into a second scratch tree (pass B);
3. `diff -r` A against B — **any** difference fails;
4. recompute `SOURCES.sha256` and diff it against the committed copy — a source
   that moved under the figures fails;
5. verify every declared artefact exists: 6 figures × 2 themes × 2 formats = 24
   images, plus 6 CSVs. The count is read from `build_all.py --list`, so adding
   a figure never means editing the gate;
6. diff the **committed** tree against the fresh build — a stale committed
   figure must not be able to hide behind a green determinism check;
7. *(P4)* no figure script reaches the filesystem directly. `sources.py` exists
   so that every input lands in `SOURCES.sha256`; a bare `open()` in a figure is
   an unhashed read, and a figure with an unhashed read keeps building green
   while its input drifts underneath it.

Exit non-zero on any failure, with the offending path named.

## 7. Order of work

1. `theme.py` + `sources.py` + `build_all.py` + `verify.sh` — the contract.
2. The five figure scripts, in parallel, each against that contract.
3. `verify.sh` green, twice.
4. `README.md`, `SOURCES.md`, `RUN_STATE.md`, `MANIFEST`, `PARTNER_SYNC`.

## 8. Known limits, declared up front

*P-21's list, with P4's amendments marked.*

* **The three-arm bill shape has two arms** — ~~one~~. There is still no Schema
  arm in the cost ledger (`baseline-arms/SCHEMA_LOCATE.md`), so the model ladder
  stands in for it. **P4:** the theoria arm is now drawn, and the two arms are
  **not priced in the same unit** — a `bare_cc` turn buys one model call that
  picks one action; a theoria turn buys a desk call that theorises across the
  whole run (5 calls covered 7 actions). The vertical gap in panel A is not a
  like-for-like markup and the plate says so. The comparison that does survive is
  per successful action: USD 0.9025 against USD 0.1459 — one theoria run against
  a pilot.
* **Two theoria attempts were billed and abandoned** (USD 2.038212 together).
  Their own manifests record `outcome: null`. They are drawn as outcome-absent
  and their cost is in the arm's total; omitting them would understate the arm.
* **The theoria arm's dollars are contested by USD 0.52 (−8.3 %).** The plate
  uses the provider's own arithmetic; the repo's price table recomputes lower,
  USD 0.4368 of it a known table defect (1-hour cache writes priced at the
  5-minute multiplier). That is a finding about `proxy/pricing/pricing_v1.json`,
  not about the run, and it is reported rather than averaged away.
* **Every Theoria run is a self-built world.** Arm and world are perfectly
  confounded in every Theoria-vs-control comparison (`REPORT_V1.md`). Figure 3
  carries this as a banner, not a footnote. **P4:** this no longer covers the
  whole plate — battery v2's Schema arm pairs against `bare_cc` *by game*, which
  does control for the world. The banner now distinguishes the two cases.
* ~~**图4 (transfer) is not in scope.**~~ **P4: in scope and shipped** as
  `fig04_a3_transfer` — see §5a. The data had been finished in
  `cold-start-a3/artifacts/` since P-17.
* **Timestamps are coarse.** The concept timeline's only wall-clock source is git
  committer time on five commits, four of which touch only the expressivity
  ledger; the rest is milestone ordinal. The axis is ordinal and says so.
* **31 of 38 battery metrics have no cross-arm contrast at all.** The matrix is
  not dense, and the band that marks it is part of the result.

---

## 9. P4 changelog

`P4-figures`, worker `W-1611`, branch `agent/p4-figures`.

**Salvaged, not re-derived.** P-21 built `theme.py`, `sources.py`,
`build_all.py`, `manifest.py`, `verify.sh`, this plan, and two figures, and none
of it reached `master` — it sat uncommitted in `.worktrees/wt-p21/`. Since the
`deterministic-figures` skill was distilled from that code, re-deriving would
have produced a second contract disagreeing with the documented one.

| # | change | why |
|---|---|---|
| 1 | `fig03` column axis taken from `capability_spectrum.provenance.arms` + `validation_material.control_arms` | `arm_contrast.json` is v1-era and vetoed the whole plate; §4 |
| 2 | `fig03` banner rewritten | it asserted there was no Schema arm; v2 has one; §4 |
| 3 | `fig03` cross-arm overlap recomputed from the cells | same staleness, same reason |
| 4 | `fig02` gains the theoria arm | the ledger the brief asked for exists; §3 |
| 5 | `fig07` retargeted from `a0-spike` to `cold-start-a0/prime` | P-21 had the wrong A0′; §2 |
| 6 | `fig04_a3_transfer` added | §5a |
| 7 | `fig05`, `fig06`, `fig07` written | P-21 planned them and did not reach them |
| 8 | `theme.check_no_mathtext` | a caveat reading `$0.90 against $0.15` renders as italic `0.90against0.15`: matplotlib eats `$...$` as mathtext. Deterministically wrong, so it survives a determinism check, and invisible in a diff. Found in P4's own first draft of fig02's caveat |
| 9 | `verify.sh` gate 7 | see §6.7 |

---

## 10. P8 changelog

`P8-billshape-pipeline`, researcher `RES-2`, branch `agent/p8-billshape-pipeline`.

The work order asked for two things: a data adapter so a landed ledger enters
figure 2 without anyone editing code, and the front-load index / convergence
point / context-growth fit drawn from the baseline's three-model data. Its stated
premise — that the theoria column is empty — was one revision stale; P4 had
already drawn that arm. The defect was one level down, in *how* the arm was
declared, and that is where the work went.

| # | change | why |
|---|---|---|
| 1 | `sources.DISCOVERY`: three declaration rules replacing three hand-written key tuples | a run that lands on disk must reach the picture without a code edit; §3 |
| 2 | each rule carries a **floor**, checked by gate 0 | a glob that finds nothing looks exactly like a family that is empty |
| 3 | absent-by-design members stay declared via `expected` | `SOURCES.sha256` must still *name* the untracked shards, not forget them |
| 4 | duplicate-path guard at registry import | a path declared twice is hashed twice, and the second line reads as drift |
| 5 | two roll-ups now read: `pilot_g50t_sonnet_rerun`, `pilot_sk48_sonnet_rerun` | drift D-1 — two runs drawn *outcome unknown* with outcomes committed on disk, one of them a `model_error` the plate exists to warn about |
| 6 | a fourth theoria run directory now read | drift D-2 — and it is the run that finally exercises the empty-curve branch |
| 7 | the cost-basis caveat picks its run **by rule**, not by name | a caveat anchored to a run id keeps describing that run after a better one lands |
| 8 | E2 / E3 / E4 read from `capability_spectrum.json`, never recomputed | a second implementation of a Phase 4 primary endpoint is a second definition |
| 9 | panel D added; panel B gains the E2 head boundary and E3 crossings | the three metrics the work order asked for, drawn as the constructions that define them |
| 10 | turn-axis agreement checked per run, reported either way | the battery counts decisions, this plate counts `step_idx` |
| 11 | `check_coverage.py` + `verify.sh` gate 8, with a mandatory negative control | gates 1–7 were green on the tree that had both drifts |
| 12 | CSV gains 8 shape columns, value **and** status for each metric | one empty cell for two different absences is how an absence becomes a zero |
| 13 | a `tracked=True` rule discovers only what git tracks; `build_all.py` warns when git cannot say | discovery widens an untracked file's blast radius — a stray `pilot_scratch.json` was invisible to a four-name list and would be hashed and read by a bare glob, on one machine and not on a clean checkout. Demonstrated with a scratch file that the rule correctly refused |
| 14 | `manifest.py` takes `--prompt-id` / `--worker` | they were constants, so a second run's manifest would have declared itself P4's, and a provenance record naming the wrong prompt reads as authoritative |

**Three things found while doing it, none of them in this territory, none
touched.** (i) `battery/metrics/economy.py` fills E4's `support["turns"]` from
`len(run.calls)` while E2/E3 fill the same key from `len(run.turn_costs())` —
billed calls against decisions, which differ exactly when a decision was
retried, and they differ on `bare_cc-g50t-claude-sonnet-5-ddabe772` (24 against
20). Panel D's axis is therefore labelled with what E4 actually counts, and the
disagreement is a note rather than a silent reconciliation. (ii) The board item's
premise about the empty theoria column was stale. (iii) The untracked
`baseline-arms/out/shards/` and `out/campaign/` remain untracked, so ~2 000 cost
rows and USD 48.39 of campaign spend are still declared-and-absent — the rule now
picks up *any* shard dropped in, including ones nobody wrote down.

**And one found in P8's own work, twice, which is the part worth reading.** The
coverage probe's first version was green and worthless: it took its disk-side
inventory from `sources.discovered(...)`, the same registry the figure reads, so
when its negative control narrowed that registry back to the pre-P8 roll-up
list, *both* sides narrowed together and the probe reported nothing over the
exact defect it had been written to catch. It is `fuzzlab`'s house rule in a new
place — the judge may not call the engine it is judging — and it was caught only
because the negative control was written before the probe was believed.

The second version was wrong the same way and was **not** caught by that
control. It walked the filesystem itself, which felt like the fix, but took the
root and the pattern it walked *from the rule it was auditing*, and the control
narrowed `DISCOVERED` — derived state nobody edits — rather than the `Rule`. An
adversarial reviewer narrowed the `Rule.pattern` instead, which is what a real
regression looks like, and reproduced drift D-1 with the probe silent: both runs
back to dotted, their outcomes committed on disk, every gate green. **An oracle
can be captured through an argument as easily as through a function call**, and
"it walks the filesystem itself" was never the property that mattered — *where*
it walks was. The probe now states root, pattern and member filenames as
literals, and the control narrows the rule. `figures/RUN_STATE.md` records the
full review round and the fifteen other defects it found.
