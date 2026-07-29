# Evidence — metric-id inventory for the §0/§1 rewrite

Prompt `P13-paper-intro-abstract`. Read-only survey; no section file was edited.
Every row carries a repo-relative path and a line number or JSON field.

Scope of the sweep: all 12 files in `papers/phase1-workshop/sections/*.md`,
regex `(?<![A-Za-z0-9])[A-Z]{1,4}-?[0-9]{1,3}(?![0-9A-Za-z])` (so hyphenated
`E-03` and bare `E3` are counted as different tokens), cross-checked against the
38 battery cards in `battery/artifacts/capability_spectrum.json` → `cards`.

---

## 0 · Headline findings, before the tables

1. **The battery's 38-metric vocabulary is never defined in the paper.** There is
   no glossary, no appendix, no definition table: `grep -n "glossar\|Appendix"`
   over `sections/*.md` returns nothing. 33 of the 38 metric ids are used; 8 get
   an inline parenthetical gloss at some point; the remaining 25 are bare
   symbols. The definitional wording exists only in the artefacts
   (`battery/artifacts/capability_spectrum.json` → `cards.<id>.definition`, and
   `battery/METRICS.md` L45–L162).
2. **K4 and K2 appear at `sections/01_intro.md:21`** — six sections before §7.4
   (`sections/07_battery.md:201`) does anything with them, and §7.4 does not
   define them either; it names them ("K4 evidence coverage", "K2 held-out
   accuracy") exactly as §1 already did.
3. **P3 — the metric §7.2 bolds as the battery's flagship — is never glossed
   anywhere in the paper.** It appears 10 times (first at
   `sections/07_battery.md:70`) and no line says what it measures. Its
   definition is `capability_spectrum.json` → `cards.P3.definition`: *"Fraction
   of steps that returned to the state two steps earlier — an undo."*
4. **`M<n>` carries three unrelated meanings in this paper.** A0 milestones
   (`01_intro.md:47,53,62`; `03_a0.md:8,10,15,20,23`), A2 loop-ledger beats
   (`05_a2.md:139,167` — M0, M5), and the battery's *mechanism* family
   (`07_battery.md:124,317,352,432`). §1's "built the A0 world at M1 and
   adjudicated it at M3" (`01_intro.md:62`) collides head-on with mechanism
   metrics M1 and M3. `M0` has no battery card at all.
5. **Hyphen-only disambiguation is load-bearing and undeclared.** `E-01`…`E-06`
   are A0/A1 expressivity-ledger entries (`03_a0.md:258`, `04_a1.md:92,112,133`,
   `10_limitations.md:42,43,46,155,162`); `E1`…`E7` are economy metrics. Nothing
   in the paper tells a reader the hyphen is the difference. Likewise `P-01`,
   `P-03`, `D-P8-004` (prompt/decision ids) against `P1`…`P5`, and `R-05`
   (a `THEORIZE_LOG.md` entry, `01_intro.md:33`) against no R family.
6. **`P6`/`P7` in the abstract are run-directory names**
   (`00_abstract.md:18,25`), not planning metrics. The planning family stops at
   P5, so there is no collision today, but the spelling is identical.

---

## 1 · Full inventory, sorted by first appearance

"Defined in paper" means: a phrase in the paper that tells a reader what the
metric measures. A bare code identifier or a two-word name is marked *weak*.
Section order is the assembly order in `papers/phase1-workshop/assemble.py`
(00 → 11), so first-appearance order is file order then line order.

| # | id | first appearance (file:line) | glossed in paper? (file:line) | first use precedes gloss? | artefact definition (`capability_spectrum.json` → `cards.<id>.definition`; also `battery/METRICS.md`) |
|---|---|---|---|---|---|
| 1 | **K4** | `sections/01_intro.md:21` | *weak* — name only, `01_intro.md:21` and `07_battery.md:203` | n/a (never truly defined) | "Mean coverage over clauses the manual annotates with one; the count of unannotated clauses is reported alongside, not folded in." (METRICS.md L157) |
| 2 | **K2** | `sections/01_intro.md:21` | *weak* — name only, `01_intro.md:21` and `07_battery.md:203` | n/a (never truly defined) | "Accuracy on state-action pairs the trace never covered. The metric replay cannot see." (METRICS.md L155) |
| 3 | M6 | `sections/01_intro.md:47` (milestone sense) | metric sense never glossed; metric use at `07_battery.md:124` | **yes** | "Mean share of the manual's theorems invalidated by one repair. A diagnostic…" (METRICS.md L128) |
| 4 | M4 | `sections/01_intro.md:53` (milestone sense) | never (metric sense never used) | — | "Mean environment actions until a changed rule first contradicts the manual…" (METRICS.md L126) |
| 5 | M5 | `sections/01_intro.md:53` (milestone sense) | never (metric sense never used) | — | "Fraction of injected rule changes the manual notices on the evidence it already holds." (METRICS.md L127) |
| 6 | M1 | `sections/01_intro.md:62` (milestone sense) | never (metric sense never used) | — | "Mean steps between a mechanism becoming visible and the arm first using it…" (METRICS.md L123) |
| 7 | M3 | `sections/01_intro.md:62` (milestone sense) | yes — "M3 cross-level transfer (claim C3)", `07_battery.md:432` | **yes** (metric use at `07_battery.md:124`) | "Mean first-use delay for mechanisms met again on a later level — does understanding travel? (Claim C3.)" (METRICS.md L125) |
| 8 | M2 | `sections/03_a0.md:15` (milestone sense) | never (metric sense never used) | — | "Fraction of annotated mechanisms the arm ever used." (METRICS.md L124) |
| 9 | (M0) | `sections/05_a2.md:139` (A2 beat) | n/a | — | **no battery card — M0 is not a metric** |
| 10 | P1 | `sections/07_battery.md:64` | yes — "(actions per model call)", `07_battery.md:272` | **yes** | "Successful environment actions per model call." (METRICS.md L71) |
| 11 | P2 | `sections/07_battery.md:65` | **never** | — | "Actions per model call in the run's second half minus the first half…" (METRICS.md L72) |
| 12 | E4 | `sections/07_battery.md:66` | yes — "a curvature fit over *context tokens* rather than over cost", `07_battery.md:178` | **yes** | "R^2 of a quadratic fit to context tokens per turn minus R^2 of a linear fit. Positive means context is accelerating." (METRICS.md L97) |
| 13 | X1 | `sections/07_battery.md:67` | **never** | — | "Fraction of observed states that had been visited before." (METRICS.md L45) |
| 14 | X4 | `sections/07_battery.md:68` | **never** | — | "Longest run of consecutive steps discovering no new state, as a fraction of the run's length." (METRICS.md L48) |
| 15 | X3 | `sections/07_battery.md:69` | **never** (called "the family's signature", `07_battery.md:135` — a role, not a definition) | — | "Novelty in the first quarter of a run minus novelty in the last quarter; the curve's shape as one number." (METRICS.md L47) |
| 16 | **P3** | `sections/07_battery.md:70` | **never** — and it is the bolded flagship | — | "Fraction of steps that returned to the state two steps earlier — an undo." (METRICS.md L73) |
| 17 | X2 | `sections/07_battery.md:71` | **never** | — | "Fraction of (state, action) transitions taken for the first time." (METRICS.md L46) |
| 18 | E2 | `sections/07_battery.md:124` | yes — "the front-load index", `07_battery.md:357` | **yes** | "Share of total cost spent in the first 25% of turns. High means front-loaded…" (METRICS.md L95) |
| 19 | E3 | `sections/07_battery.md:124` | **never** | — | "Fraction of the run's turns needed to reach 90% of its total cost. Low means the bill settled early." (METRICS.md L96) |
| 20 | K7 | `sections/07_battery.md:124` | **never** | — | "Concepts admitted despite a negative compression account. A diagnostic, not a score…" (METRICS.md L160) |
| 21 | K11 | `sections/07_battery.md:124` | **never** | — | "Manual revisions. The concept-birth timeline's coarse axis." (METRICS.md L151) |
| 22 | K12 | `sections/07_battery.md:124` | *weak* — "read six self-reported booleans", `07_battery.md:323` (describes the exploit, not the metric) | **yes** | "Share of the six repair beats — 打脸→定位→戳探→修订→重证→解出 — that closed." (METRICS.md L152) |
| 23 | P4 | `sections/07_battery.md:124` | yes — "`ok_steps / optimal`, direction `lower`", `07_battery.md:317` | **yes** | "Actual successful steps divided by the shortest known plan, over runs that reached the goal. 1.0 is optimal…" (METRICS.md L74) |
| 24 | E5 | `sections/07_battery.md:173` | yes — "(cost per action)", `07_battery.md:266` | **yes** | "Total cost divided by successful environment actions." (METRICS.md L98) |
| 25 | E1 | `sections/07_battery.md:173` | **never** | — | "Total model cost. Support for the shape metrics, not a ranking." (METRICS.md L94) |
| 26 | E6 | `sections/07_battery.md:173` | **never** | — | "Mean HTTP attempts the harness burned per logged environment step…" (METRICS.md L99) |
| 27 | E7 | `sections/07_battery.md:173` | **never** | — | "R^2 of a quadratic fit to prompt size per turn minus R^2 of a linear fit…" (METRICS.md L100) |
| 28 | P5 | `sections/07_battery.md:285` | *weak* — code name `step_failure_rate` at first use | no (gloss is at first use) | "Fraction of environment steps that failed outright. A diagnostic: it is the confound P1 and P2 are most exposed to." (METRICS.md L75) |
| 29 | K6 | `sections/07_battery.md:347` | **never** | — | "Mean compression gain per admitted concept, in bits. Positive means the concept paid for itself." (METRICS.md L159) |
| 30 | K14 | `sections/07_battery.md:347` | **never** | — | "Minimum per-concept compression gain in bits. The statistic K6's mean hides." (METRICS.md L154) |
| 31 | K5 | `sections/07_battery.md:347` | **never** | — | "Concepts admitted to the manual's word table." (METRICS.md L158) |
| 32 | K3 | `sections/07_battery.md:348` | **never** | — | "Invariants and theorems in the manual." (METRICS.md L156) |
| 33 | K8 | `sections/07_battery.md:390` | **never** | — | "Executable probes as a fraction of probe designs. Low means the probe machinery proposed experiments it could not run." (METRICS.md L161) |
| 34 | K10 | `sections/07_battery.md:390` | **never** | — | "Deadlock theorems: machine-checked proofs that a region of the search space can never reach the goal." (METRICS.md L150) |
| 35 | K13 | `sections/07_battery.md:451` | **never** | — | "Environment actions spent repairing, over the actions the original theory cost. Low means the repair was localised." (METRICS.md L153) |
| 36 | K1 | `sections/10_limitations.md:223` | **never** | — | "Full-history exact replay accuracy: the fraction of observed state-action pairs on which the manual agrees with the world." (METRICS.md L149) |

**Cards that exist and are never used in the paper:** `X5`, `X6`, `K9` (3 of 38).

**Count:** 33 distinct battery-metric ids used; 8 receive any gloss (P1, P4, P5,
E2, E4, E5, M3, K12 — three of those *weak*); **25 are bare symbols throughout**.
That is the lay reviewer's "~30 ids, ~8 glossed", confirmed exactly.

---

## 2 · Ids used in §0 abstract / §1 intro, with a gloss from the artefacts

`00_abstract.md` uses **no battery-metric id at all**. The only claim-family id
it uses is **C3** (`00_abstract.md:59`). `01_intro.md` uses **K4** and **K2**
(both `01_intro.md:21–22, 27`), plus milestone `M1/M3/M4/M5/M6` and the
non-metric ids `R-05`, `DC22`, `A0/A0′/A1/A2`.

### K4 — `01_intro.md:21`, `01_intro.md:27`

* **Exact definitional wording:** *"Mean coverage over clauses the manual
  annotates with one; the count of unannotated clauses is reported alongside,
  not folded in."*
* **Paths:** `battery/artifacts/capability_spectrum.json` → `cards.K4.definition`;
  `battery/METRICS.md` L157 (same string, plus `direction: higher`, `tier:
  reference`, `needs: theory`).
* **One-clause plain-English gloss (derived, not invented):** *how much of the
  manual's own evidence-annotated text is actually backed by a witness — a
  self-report about citations, not about truth.*
* **The reported value:** `capability_spectrum.json` → `runs["a0-base"].metrics.K4`
  = `{"value": 1.0, "support": {"annotated": 7, "min_witnesses": 1,
  "unannotated": 3}}`. Note the intro cites the 7 annotated clauses but **not the
  3 unannotated ones**, which the card's own definition says must travel
  alongside.

### K2 — `01_intro.md:21`, `01_intro.md:22`

* **Exact definitional wording:** *"Accuracy on state-action pairs the trace
  never covered. The metric replay cannot see."*
* **Paths:** `battery/artifacts/capability_spectrum.json` → `cards.K2.definition`;
  `battery/METRICS.md` L155.
* **One-clause plain-English gloss (derived):** *how often the manual is right
  about situations its own history never showed it.*
* **The reported value:** `capability_spectrum.json` →
  `runs["a0-base"].metrics.K2` = `{"value": 0.0, "support": {"agree": 0,
  "pairs": 3, "frame": "3 state-action pair(s) the full-history trace never
  covered out of 236 replayed pairs over 59 reachable states. Adversarial gaps
  left by the trace, not a sample drawn from the world -- not comparable with an
  exhaustive enumeration."}}`. The `frame` string is the v2.1 addition described
  at `sections/07_battery.md:231–241` and `battery/REPORT_V2.md:344–357`.
* **Constraint the paper states about the pair:** "K4 must never be reported
  without K2 beside it" (`sections/07_battery.md:221–222`, sourced to
  `battery/artifacts/gaming_audit.json` → `metrics.K4`, whose `defended` is
  `false`).

### C3 — `00_abstract.md:59` (see §3 below for the full treatment)

* **One-clause plain-English gloss:** *the claim that once you carry the two
  books to a second level of the same game, the second level costs far less than
  the first.*

**Recommendation implied by the evidence, not a decision:** if the rewrite wants
to keep numbers in §1, K4 and K2 can be replaced by the same two figures already
present as prose — "evidence coverage 1.000 over 7 annotated clauses" and
"accuracy on the 3 never-covered pairs 0.000" — with the ids attached
parenthetically only if §7.4 is where they are first *named*. §1 already cites
`cold-start-a0/artifacts/score_vs_truth.json` → `held_out.accuracy` for the same
0.000, so the id is not load-bearing for the citation.

---

## 3 · C3 — what it is, where it is defined, and what "early read" means

### 3.1 Where C3 is defined — and where it is *not*

* **Definition (verbatim), `Theoria.md:361`:**
  `- C3 迁移:携两本书跨关,第二关边际成本 ⟨≪⟩(条件性,视关卡共享机制程度,Phase 1 核实);`
  — "C3 transfer: carry the two books across a level; the second level's marginal
  cost is ⟨≪⟩ (conditional, depending on how much mechanism the levels share;
  pinned down in Phase 1)."
* **Enclosing block:** the bullet list introduced at `Theoria.md:358`
  ("**Claim 菜单现在列死**" — the claim menu is fixed now), inside
  `## Phase 3 · 框架迭代(探索;只在开发堆)` which opens at `Theoria.md:334`.
  Sibling claims: C1 `Theoria.md:359`, C2 `:360`, C4 `:362`, C5 `:363`, and the
  weighting line at `:364` — "主骨 = C1+C4;签名证据 = C2;**C3 条件性**;C5 背景数字"
  (C3 is the conditional one).
* **`arc-recon/data/claim_set.json` does NOT define C3.** Its top-level keys are
  `['claim_set', 'claim_set_size', 'clean', 'cross_track_api_audit', 'gate',
  'needs_adjudication', 'piles_hash', 'quarantined',
  'retained_above_material_level', 'retained_with_sensitivity_analysis', 'rule',
  'sealed_api_audit', 'sealed_pile_size', 'source', 'unrecognised_claim_state']`,
  and `claim_set` is a list of **19 game ids** (`bp35-0a0ad940` … `wa30-ee6fef47`,
  `claim_set_size: 19`). `grep -n "C3" arc-recon/data/claim_set.json` returns
  nothing. Two different senses of "claim set" — the C1–C5 claim *menu* is
  `Theoria.md` only; `claim_set.json` is the set of sealed **games** still
  claimable after F-11 quarantined `ls20`/`ft09`.
* **Citation defect to fix in the rewrite:** `sections/06_a3_transfer.md:6` says
  "In the claim menu of `Theoria.md` §3.2 this is C3". §3.2 is
  `Theoria.md:410` ("逐节骨架", the paper skeleton). The claim menu is at
  `Theoria.md:358–364`, under Phase 3. The correct citation is
  `Theoria.md` Phase 3, "Claim 菜单现在列死", L361.

### 3.2 What "early read" means, concretely

Three concrete senses, each with a path:

1. **Not a mandated acceptance.** `Theoria.md:294` lists "**三件离线验收**" —
   three offline acceptances — and names exactly A0 (`:295`), A1 (`:296`),
   A2 (`:297`). The Phase 1 acceptance checklist at `Theoria.md:305` says
   "A0、A1、A2 绿". The string `A3` occurs **zero times in `Theoria.md`**
   (`grep -c "A3" Theoria.md` → 0). So §6 reports work the mandate never asked
   for at this phase.
2. **The claim it answers belongs to a later phase's menu.** C3 sits in the
   Phase 3 claim menu (`Theoria.md:334`, `:361`) whose ⟨≪⟩ placeholder the same
   line says is to be pinned down in Phase 1 — so an early *read* is licensed,
   an early *verdict* is not.
3. **The read is deliberately the weakest one the wording licenses.**
   `sections/06_a3_transfer.md:10–13`: "A3 answers it for two levels of one game,
   which is the weakest interesting reading of C3 and the one the framework's own
   wording licenses. Anything stronger needs a different experiment, and
   `cold-start-a3/A3_REPORT.md` §6 says so before we do." The measured quantity
   is the like-for-like bill (`sections/06_a3_transfer.md:42–50`, sourced to
   `cold-start-a3/artifacts/bill_table.md`): world actions 346 → 10 (ratio
   0.029), engine stages 1 → 0, candidates adjudicated 35 → 0. And the honest
   limit is stated at `sections/06_a3_transfer.md:133`: "The induction is free;
   the [verification is not]" — verification is paid in full and at the same rate.
   The battery's own view is the counterweight: `sections/07_battery.md:432`,
   "**M3 cross-level transfer (claim C3)** | still no multi-level run, and M3 is
   additionally known to have no reachable value at all".

### 3.3 The count verdict: "three plus an early read on C3" is CORRECT

* **Against the mandate:** `Theoria.md:294` — three offline acceptances, A0/A1/A2.
  No A3. **Verdict: three is correct; "four offline acceptances" was wrong.**
* **The correction is already recorded as a decision**, with the reasoning:
  `papers/phase1-workshop/runs/20260728T151000Z-P11-battery-section-refresh/FINDINGS.md:107`
  — "**`Theoria.md:294` says 三件离线验收, and the string "A3" appears in
  `Theoria.md` zero times.** … A3 is claim C3 answered early — the paper's own §6
  says so. My edit made 'that unit and nothing more' self-falsifying"; same run's
  `FINDINGS.md:93` and `RUN_STATE.md:94–95` record the original contradiction
  (abstract said four, §2.5 said three).

**Sections that still say the old thing: none.** Sweep of `sections/*.md` for
acceptance counts:

| file:line | text | state |
|---|---|---|
| `sections/00_abstract.md:3` | "three offline acceptances and a transfer result" | correct |
| `sections/00_abstract.md:57` | "three acceptances on self-built deterministic worlds" | correct |
| `sections/00_abstract.md:58–59` | "the three `Theoria.md` Part 2 names, A0, A1 and A2 — plus a fourth section reporting an early read on claim C3 that the mandate does not list as an acceptance" | correct |
| `sections/02_framework.md:104` | "pass three offline acceptances" | correct |
| `sections/02_framework.md:118, 121–122` | "It reports the three acceptances … and, in §6, an early read on claim C3 that the mandate does not list as an acceptance at all" | correct |
| `sections/10_limitations.md:40` | "across the three acceptances" | correct |
| `papers/phase1-workshop/PAPER.md:5, 59, 372, 386` | assembled copy, all "three" | correct (regenerate after any edit) |

**One residual, outside the sections:**
`papers/phase1-workshop/OUTLINE.md:18` — "**The four acceptance reports** and
`REPORT_V0.md` are read-only sources." This is the process document's red-line
list, and it is counting *source report files* (A0, A1, A2, A3 reports), not
mandated acceptances. It is not a body claim, but it is the last place in the
tree where "four" and "acceptance" sit adjacent, and a reader who greps will
find it. Recommend either leaving it (it is provably about files) or changing
"four acceptance reports" → "the four cold-start reports".

---

## 4 · P3 — the two statistics, and the honest sentence

### 4.1 Current wording

* **§7.2 table row, `sections/07_battery.md:70`:**
  `| P3 | planning | −0.375 | 0.130 / 0.001 | yes | **main** | 8 of 8 |`
* **§7.2 pull-quote, `sections/07_battery.md:87–89`**, attributed to
  `battery/REPORT_V2.md`: "**P3 is the only metric in the battery that is both in
  the main table and validated on the specified gradient.**" Source line:
  `battery/REPORT_V2.md:80`.
* **§7.2a heading, `sections/07_battery.md:91`:** "The effect sizes are not
  paired, and on P3 the two statistics disagree".
* **§7.2a body, `sections/07_battery.md:104–110`:** "**On P3 the two statistics
  point opposite ways.** Its δ of −0.375 is recorded with
  `agrees_with_declared_direction: true`, while its paired sign test over the same
  four games is **1 win, 2 losses, 1 tie, p = 1.0**
  (`battery/artifacts/discrimination_arms.json`, `metrics.P3`). The unpaired
  comparison says the direction held; the paired one, on the same data, has the
  metric losing twice as often as it wins. X2 sits in the same position. Whatever
  'validated on the specified gradient' means for P3, it cannot mean that the
  gradient's own paired test agreed."
* **§7.2a precision note, `sections/07_battery.md:112–116`:** every δ at n = 4 per
  side is a multiple of 1/16, so "−0.562" and "−0.188" print three decimals onto a
  quantity with seventeen reachable values.

So §7.2a is already correct and already in the draft. What the abstract and intro
must not do is inherit §7.2's flagship sentence without §7.2a's correction.

### 4.2 Artefact paths for both statistics

**Effect size and paired test, process 1 (bare_cc vs Schema — the "specified
gradient"):** `battery/artifacts/discrimination_arms.json` → `metrics.P3`:

```
cliffs_delta                     -0.375
agrees_with_declared_direction   true
direction                        "lower"
medians                          bare_cc 0.129786631 / schema_repro 0.00093633
n_high_games 4, n_low_games 4, n_paired_games 4
sign_test  { wins 1, losses 2, ties 1, n 3, p_value 1.0, min_attainable_p 0.25 }
verdict    "underpowered"
note       "3 paired games cannot reach p<0.05 however cleanly the metric
            separates (smallest attainable two-sided p is 0.2500).
            The effect size stands; the test does not."
```
Gradient declared at the same file's `gradient` field: `"bare_cc (weaker) vs
schema_repro (stronger), paired by game"`; `specified_by`: `"Theoria.md Phase 2
process 1 -- CC vs Schema"`; `power`: `"a two-sided sign test needs 6 non-tied
paired games to be able to reach p<0.05 at all; the pilot has 4"`.

**Second, independent pass (the model ladder):** `battery/artifacts/discrimination.json`
→ `metrics.P3`: `cliffs_delta −0.333333333`, `agrees_with_declared_direction
true`, 3 games, `sign_test { wins 0, losses 2, ties 1, n 2, p_value 0.5,
min_attainable_p 0.5 }`, `verdict "underpowered"`. **On the ladder P3 does not
win a single paired game.** The paper does not currently report this second row
for P3; it is a strictly harsher number than the one §7.2a already concedes.

**How the two statistics are computed:** `battery/audit/stats.py`, `cliffs_delta`
= `P(high > low) − P(high < low)` over all cross-arm pairs of the four per-game
values — it never matches a game against itself. Only the sign test pairs. Stated
at `sections/07_battery.md:96–102`.

**Definition, never given in the paper:** `battery/artifacts/capability_spectrum.json`
→ `cards.P3.definition` = "Fraction of steps that returned to the state two steps
earlier — an undo."; `direction: "lower"`; `needs: ["steps","observations"]`;
`battery/METRICS.md` L73 adds `tier: reference` and "79 control runs over 4 games
… process 1: underpowered".

### 4.3 The honest summary of P3, as one sentence

> **P3 — the undo rate, the fraction of steps that return to the state two steps
> earlier — is the only battery metric that is both in the main table and
> nominally validated on the gradient the design specifies, and that validation
> rests on an unpaired statistic: Cliff's δ = −0.375 in the declared direction,
> while the paired sign test over the same four games is 1 win, 2 losses, 1 tie,
> p = 1.0 (and 0 wins, 2 losses, p = 0.5 on the model ladder), with a verdict of
> `underpowered` recorded in the artefact itself.**

Shorter, if the abstract needs one clause: *the battery's one validated
main-table metric is validated only by the statistic that does not pair; the
paired test on the same four games loses twice as often as it wins.*

Three things that sentence must not say, each with the artefact that forbids it:
* not "P3 separates the arms" — `verdict: "underpowered"`,
  `discrimination_arms.json` → `metrics.P3.verdict`;
* not "significant" or "p < 0.05" — `min_attainable_p` is 0.25 here and the file's
  `power` field says 6 non-tied paired games are needed to reach 0.05 at all;
* not "−0.375" to three decimals without the n = 4 caveat — `sections/07_battery.md:112–116`.

---

## 5 · Ids in §0/§1 that are not metrics, for completeness

| id | where in §0/§1 | defined where | note |
|---|---|---|---|
| C3 | `00_abstract.md:59` | `Theoria.md:361` | §3 above; not in `claim_set.json` |
| A0, A1, A2 | `00_abstract.md:58`; `01_intro.md:12,70,120` | `Theoria.md:295,296,297` | named in §0 as "the three `Theoria.md` Part 2 names" |
| A3 | `00_abstract.md:16` (v0.2 note) | **not in `Theoria.md`** (0 hits) | defined only by `cold-start-a3/A3_REPORT.md` and §6 |
| A0′ | `01_intro.md:99,120` | `cold-start-a0/prime/A0P_REPORT.md` | prime notation never expanded in §1 |
| R-05 | `01_intro.md:33,40,43,46,49` | `cold-start-a0/THEORIZE_LOG.md` entry R-05 | glossed in place ("entry R-05 of …") — good model for how ids should enter |
| DC22 | `01_intro.md:87` | `Theoria.md:36` | §1 gives the shape but never says DC22 is a *game id*; the sealed-pile caveat follows at `01_intro.md:88–91` |
| M1, M3, M4, M5, M6 | `01_intro.md:47,53,62` | A0 milestone scheme; nearest text `cold-start-a0/THEORIZE_LOG.md` | **collide with mechanism metrics M1/M3/M4/M5/M6** — finding 4 above |
| P6, P7 | `00_abstract.md:18,25` | run directory names | look like planning metrics |
| V0, V2 | `01_intro.md:28,115,124` | `battery/REPORT_V0.md`, `battery/REPORT_V2.md` | battery report versions, fine |

---

## 6 · Commands used

```bash
# id sweep over the sections
cd papers/phase1-workshop/sections
grep -oEn '\b[A-Z]{1,3}-?[0-9]+[a-z]?\b' *.md | ...   # family discovery
# per-id first appearance (regex excludes hyphenated and suffixed forms)
python -c "... (?<![A-Za-z0-9_-])([XPEMK])(\d{1,2})(?![0-9A-Za-z]) ..."
# card definitions
python -c "import json; json.load(open('battery/artifacts/capability_spectrum.json'))['cards']"
# both P3 statistics
python -c "... battery/artifacts/discrimination_arms.json -> metrics.P3 ..."
python -c "... battery/artifacts/discrimination.json      -> metrics.P3 ..."
grep -c "A3" Theoria.md          # -> 0
grep -n "C3" arc-recon/data/claim_set.json   # -> no match
```

No section file was modified by this survey.
