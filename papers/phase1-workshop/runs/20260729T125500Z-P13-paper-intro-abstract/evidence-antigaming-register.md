# Evidence pack — the executable anti-gaming register

Prepared for the rewrite of §0 (abstract) and §1 (introduction) of the Phase-1
workshop paper. Every fact below carries its repo-relative path and the field or
line it was read from. Paths are relative to the repository root
(worktree: `.worktrees/p13-paper-intro-abstract`).

Two verification methods were used and are distinguished throughout:

* **A** — read directly out of a committed artefact (`battery/artifacts/*.json`,
  `battery/runs/**`). Verbatim-checkable.
* **R** — re-derived by running the battery's own code in this worktree
  (`python -c "from battery.audit.gaming import audit; audit()"`, 2.8 s, no
  network). Reproduced independently by a committed recompute in
  `battery/runs/20260729T025515Z-V18-battery-prereg-check/recompute/`.

---

## 0. The headline finding of this evidence pass, stated first

**`battery/artifacts/gaming_audit.json` — the artefact §7.7, §7.2a, §10.5 and the
abstract all cite — is one full audit round out of date, and the paper's lead
contribution is currently built on it.**

A later, harder, *blind* round (V9/B16, plus an adversarial re-review B17) is
committed in the repository, is not mentioned anywhere in the paper, and changes
the headline in the direction of a *stronger* result:

| quantity | published artefact (`battery/artifacts/gaming_audit.json`) | re-run of the same code today | V9 blind round |
|---|---|---|---|
| metrics in the **main table** | **9** (`main`) | **0** (R) | **0** (`verdict.main`, `battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json`) |
| exploits that still land | **34** of 38 | **33** of 38 (R) | 37 of 38 metrics gamed, 95 of 112 attacks landed |
| `n_disagreements` | **17** | **19** (R) | 9 metrics disagree with the B14 baseline |

Corroborating tracked files that already carry the newer number:

* `battery/METRICS.md` line 33: **`**Main table (0):** `** — the generated metric
  documentation, regenerated after V9, publishes an empty main table. Line 35
  lists all 38 metrics as `Reference`.
* `battery/STATUS.md` lines 23–24: milestone **B16** "(105 次盲攻击，37/38 刷得动)"
  and **B17** "(E1 被四个无意攻击打掉，M3 改记 `undetermined`，**主表 → 0**)".
* `battery/runs/20260729T025515Z-V18-battery-prereg-check/recompute/gaming_audit.json`:
  a committed recompute dated 2026-07-29T02:55Z with `main: []`,
  `n_disagreements: 19`, 33 exploits landing.

Why the published artefact is stale rather than wrong: `PREREG_V9.md` §5 says in
advance *"不修改任何已提交产物：`battery/artifacts/` 不重写"* — V9 deliberately did
not rewrite the artefact directory, and wrote its verdict to a separate file. So
the divergence is a declared policy, not a defect. **But it means §7.1's claim
that "artefacts regenerate with `python -m battery.run_battery`" is no longer
true of `gaming_audit.json`: a regeneration today changes `main` from nine
metrics to none.**

Everything below supports both readings, so the rewrite can choose which round to
lead with. Recommendation is in §5.

---

## 1. What the register actually is, mechanically

### 1.1 The object under audit: a prose register

`battery/audit/gaming.py` holds `GAMING_REGISTER`, a dict keyed by metric id
(38 keys). Each **entry** is four fields (see any entry, e.g. `K14` at
`battery/audit/gaming.py:348-358`):

| field | type | meaning |
|---|---|---|
| `how_to_game` | free text | one sentence on how an arm could reach a good score without the capability |
| `accidental` | bool, hand-set | would a real arm land here *without trying*? |
| `defence` | free text | the sentence describing the countermeasure |
| `defended` | bool, hand-set | is the countermeasure implemented? |

This is not advisory. `tier_of()` (`battery/audit/gaming.py:389-419`) runs a
mechanical rule over two of those booleans —
`accidental and not defended -> reference; else main` — and the resulting tier
decides whether a metric is allowed into the paper's "main table", i.e. into
ordering claims about arms.

The defect that motivated the work, in the code's own words
(`battery/audit/exploits/__init__.py:8-13`): *"A wrong `defended: True` keeps a
gameable metric in the main table and nothing in the suite notices —
`test_every_registered_metric_has_a_gaming_entry` checks that an entry
*exists*, never that it is *true*."*

### 1.2 What makes it executable: an `Exploit`

`battery/audit/exploits/` (three modules: `economy.py`,
`exploration_planning.py`, `mechanism_epistemic.py`) turns each register entry
into a demonstration. An **exploit** is a zero-argument module-level function
named `exploit_<METRIC_ID>` that constructs, in pure Python, a `Run` — the
battery's normalised trajectory dataclass from `battery/model.py` (`Run`, `Step`,
`Call`, `Theory`, `Concept`, `Clause`, `Repair`, `Beat`, `Truth`) — designed so
that the metric scores well on it while the run demonstrably contains none of the
capability the metric names.

Worked example, `battery/audit/exploits/mechanism_epistemic.py:670-713`
(`exploit_K12`): it builds six `Beat(closed=True, env_actions=0)` records inside
one `Repair(beats_required=6)`, with `changed_clause=None`. K12 ("repair loop
closure") scores **1.000** — the same score the real A2 refutation run earns —
from six booleans a producer set, with zero environment actions behind them.

The function returns an `Exploit` dataclass
(`battery/audit/exploits/__init__.py:43-121`) carrying `metric_id`, the `run`,
a one-line `claim` (what score it reached and what it did not have), and
`succeeded` / `accidental` / `defence` / `defended`.

**"Executable" means three specific things:**

1. **`succeeded` is recomputed from the metric, not asserted.**
   `Exploit.__post_init__` (`battery/audit/exploits/__init__.py:75-104`) calls
   `battery.metrics.evaluate(self.run)[self.metric_id]` and ANDs the stored flag
   with `value.ok and value.value is not None`. Land a defence and the exploit
   flips to `False` by itself — the package is the regression test for its own
   findings. This is not hypothetical: it fired when V9's D3 defence closed E1's
   exploit (§2.3 below).
2. **`defended` means the code refuses the attack**, not that a defence is
   imaginable (`battery/audit/exploits/__init__.py:24-26`).
3. **`proposed_tier`** (`battery/audit/exploits/__init__.py:106-121`)
   reimplements `tier_of`'s rule over the *demonstrated* fields rather than
   importing it, so a disagreement between demonstration and prose is
   representable at all.

`accidental` stays a hand-set judgement — "would a real arm do this without
trying" is not decidable from a `Run` — but each exploit's docstring is required
to argue it from a named file in the repository
(`battery/audit/exploits/__init__.py:28-32`).

### 1.3 What running it produces

`battery/audit/gaming.py:446-519` (`audit()`) walks all 38 register entries,
attaches the demonstrated fields, records a per-metric `status`
(`"register confirmed by demonstration"` / `"register contradicted on <fields>"`),
and emits `battery/artifacts/gaming_audit.json` via
`battery/run_battery.py:345`. The artefact's top-level fields are
`rule`, `n_demonstrated`, `n_prose_only`, `n_disagreements`, `disagreements[]`,
`demoted_by_demonstration[]`, `main[]`, `reference[]`, `metrics{}`.

A reader who has never seen the repo can state what was run as:
*for each of a battery's 38 metrics, someone wrote a small program that
fabricates a trajectory object; the battery's own scoring code is then run on
that object, and the score it returns — not the author's expectation — decides
whether the metric is reported as trustworthy.*

### 1.4 The blind round (V9/B16), which the paper does not mention

`battery/audit/v9/` re-does the same process under three disciplines the first
round lacked (`battery/PREREG_V9.md` §0):

* **Blind.** Six mutually invisible attackers each got a copy of the repository
  *outside* the repo containing only `battery/model.py`, the five metric modules,
  the certificate checker, and a bare threshold table. Every docstring and
  comment was mechanically stripped via `ast.unparse` round-trip; seven
  intent-leaking runtime reason strings were neutralised;
  `battery/audit/gaming.py`, `battery/audit/exploits/`, `METRICS.md`,
  `battery/artifacts/` and the tier assignments were **not given**
  (`battery/BLINDING.md` §1–§2). `BLINDING.md` §4 states plainly why the first
  round was not blind: the exploit authors could read `gaming.py`, which lists
  `how_to_game` and `defence` for every metric.
* **Pre-registered success criterion.** `battery/PREREG_V9.md` §1 fixes
  S1 (the metric answered `ok`) ∧ S2 (the value reached a numeric target fixed
  per metric in `battery/audit/v9/prereg.py::TARGETS`, generated by a
  value-range rule declared in §1.2 before the table) ∧ S3 (a mechanical
  "poverty certificate", `battery/audit/v9/check.py`: the attack must be a
  deterministic zero-argument function with no file I/O, no loops, no recursion
  and no calls outside a whitelist — *"攻击只准摆数据，不准算东西"*, §2 C3).
  Ancestry of the pre-registration commit is proved with
  `git merge-base --is-ancestor` and the transcript is kept at
  `battery/runs/20260729T021247Z-V9-battery-gaming-audit/RUN_STATE.md:42-44`.
* **Mutation testing on the defences**: a defence that would promote a metric
  must carry more refuted attack variants than tests (`PREREG_V9.md` §3 R2).

---

## 2. Every headline number, checked

### 2.1 "34 of 38 executable exploits still score a metric at or near its best value…"

Appears in: `papers/phase1-workshop/sections/00_abstract.md` result (5);
`papers/phase1-workshop/sections/07_battery.md:306-309`.

* **The count 34 is correct against the published artefact.** (A)
  `battery/artifacts/gaming_audit.json`: `n_demonstrated` = 38; counting
  `metrics[*].demonstrated.succeeded == true` gives **34**. The four that do not
  land are **E2, K12, M3, P4** (three closed by the v2.1 defences, M3 never
  landed because it never returns a value).
* **The count is 33 today.** (R) Re-running `audit()` in this worktree gives 33;
  the same is recorded in the committed recompute
  `battery/runs/20260729T025515Z-V18-battery-prereg-check/recompute/gaming_audit.json`.
  The metric that changed is **E1**: V9's D3 defence ("an unpriced model call is
  not a free one") makes the economy family refuse a partial bill, so E1's
  exploit run now returns nothing instead of `$0.0102`. The exploit's own claim
  string changed with it (`$0.0102` → `$0.0000`), which is the
  recompute-on-construction machinery working as designed.
* **"38 exploits exist" is imprecise.** (R) `collect_all()` finds **39 exploit
  functions covering 38 metrics** — E2 carries two (`exploit_E2`,
  `exploit_E2_length`, `battery/audit/exploits/economy.py:141,194`). The
  artefact's `n_demonstrated: 38` counts *metrics with an exploit*, not exploits.
  Safer wording: "one executed demonstration for each of the 38 metrics
  (39 in total; E2 carries two)".
* **"at or near its best value" is NOT mechanically checked for 11 of the 38.**
  This is the most load-bearing softening this pack asks for.
  - `mechanism_epistemic.py` (20 metrics: K1–K14, M1–M6) computes `succeeded`
    through `_verdict(run, id, target, mode)`
    (`battery/audit/exploits/mechanism_epistemic.py:59-74`), an explicit
    directional threshold.
  - `economy.py` (7 metrics: E1–E7, 8 functions) computes `succeeded` against an
    explicit inline threshold each time (`economy.py:120, 173, 238, 293, 354,
    404, 459, 518`).
  - `exploration_planning.py` (11 metrics: X1–X6, P1–P5) passes a **hard-coded
    `succeeded=True`** in all eleven cases (`exploration_planning.py:109, 151,
    202, 246, 285, 335, 383, 444, 491, 550, 596`). For these, after
    `__post_init__`, `succeeded` reduces to *"the metric returned a number at
    all"*. The package's own docstring admits this
    (`battery/audit/exploits/__init__.py:48-53, 80-94`) and treats the stored
    `True` as "the auditor's threshold judgement". Note also that
    `battery/audit/exploits/__init__.py:57` refers to a field
    `declared_succeeded` that **does not exist** on the dataclass — the original
    value is overwritten in place, so the pre-defence value is not recoverable
    from the object.
  - Separately, 7 of the 38 metrics are direction-`neutral` diagnostics
    (E1, E6, K7, K11, X5, M6, P5 — from `battery.metrics.REGISTRY`), for which
    "best value" is undefined by construction. Their exploit claims read e.g.
    "K11 = 42 from a one-line header comment" and "X5 = 24 distinct states on an
    arm that never left one game state" — these are *controllability*
    demonstrations, not best-score demonstrations. And 19 of the 38 metrics are
    unbounded `higher` counts, where "near its best value" has no referent.
  - **Honest replacement wording:** "…still reach a score the metric's own
    direction calls good — or, for the direction-less diagnostics, a reading of
    the attacker's choosing — while possessing none of the capability the metric
    claims to measure."

### 2.2 "17 written register entries, 14 of them defence claims, contradicted by their own demonstration"

Appears in: `00_abstract.md` result (5); `07_battery.md:307-309`;
`10_limitations.md:246-249`.

* **17: correct against the artefact, and it survives the recompute if you
  define it as field contradictions.** (A/R)
  `battery/artifacts/gaming_audit.json` `n_disagreements` = **17**, and the
  per-metric `status` counts are `register confirmed by demonstration` 21,
  `register contradicted on accidental, defended` 12,
  `register contradicted on accidental` 3, `register contradicted on defended` 2
  → 12+3+2 = **17**. The recompute produces *the identical status counts*
  (21/12/3/2), so the substantive claim is unchanged.
* **But the cited field now reads 19.** (R) `n_disagreements` counts a
  disagreement when `tier != register_tier` **or** a field differs
  (`battery/audit/gaming.py:493-500`). After V9 demoted every metric, **M3** and
  **P3** — whose demonstrations *confirm* their register entries — became tier
  disagreements with no field deltas, so `n_disagreements` = 19 while the number
  of contradicted *entries* stays 17. If the paper cites the field name, cite it
  as it stood in the artefact and say so; if it cites the claim, prefer "17 of
  the 38 register entries state something their own demonstration contradicts".
* **14 defence claims: correct.** (A) Counting `disagreements[*]` whose
  `fields_contradicted` contains `"defended"` gives **14** (12 that contradict
  both fields + 2 that contradict `defended` alone). `"accidental"` is
  contradicted 15 times.
* Supporting numbers in `07_battery.md:308-315` also check out against the
  artefact: `main` 9, `reference` 29, `demoted_by_demonstration` 10, and
  `register_tier == "main"` for exactly **19** metrics — which is the "fell from
  19" endpoint. The intermediate "6" is not in the artefact; `battery/REPORT_V2.md:83`
  names the six by hand (E3, K11, K7, M3, M6, P3), exactly as §7.7 already says.
* One further mismatch already handled correctly by the paper, noted here so the
  rewrite does not reintroduce it: `battery/REPORT_V2.md:204` says **"38
  exploits, 37 land"**. That is the pre-v2.1 number; three defences then flipped
  three exploits (`REPORT_V2.md:342`: "the four exploits flip — 3 of 4"),
  giving the artefact's 34. §7.7 is right to cite 34 and not 37.

### 2.3 "the exploration family's declared signature separates the one gradient the design specifies backwards"

Appears in: `00_abstract.md` result (5); `07_battery.md:135-147`;
`10_limitations.md:249-250`.

**Fully supported.** (A) `battery/artifacts/discrimination_arms.json`,
`metrics.X3`:

* `cliffs_delta: -0.5625`, `direction: "higher"`,
  `agrees_with_declared_direction: false`, `family: "exploration"`
* `medians: {bare_cc: 0.014987662, schema_repro: -0.007395678}` — the stronger
  arm's novelty front-load index is **negative**
* `warning: "separates the gradient strongly (|d| = 0.562) but in the opposite
  direction to the one declared. Either the definition is measuring something
  else, or the declared direction is wrong. Do not use until resolved."`
  (the paper quotes this verbatim and correctly)
* the gradient is the specified one: same file, `gradient: "bare_cc (weaker) vs
  schema_repro (stronger), paired by game"`,
  `specified_by: "Theoria.md Phase 2 process 1 -- CC vs Schema"`
* "the family's declared signature" is sourced:
  `battery/REPORT_V2.md:92-94` — *"X3 is falsified, and it was the family's
  signature … X3 — novelty front-loading — is the exploration family's declared
  signature"*; and `battery/REPORT_V1.md:49` — X3 was the one metric v1 reported
  as separating as declared.

**Two caveats that must travel with it if it enters the abstract**: the same
artefact records `verdict: "underpowered"` and `sign_test: {wins: 0, losses: 3,
ties: 1, n: 3, p_value: 0.25, min_attainable_p: 0.25}`; and `confounds[0]` says
the Schema side is another team's agent on another team's infrastructure, so the
separation bundles capability with plumbing. Note this is a **process-1**
(discriminative-power) finding, not a register finding — it does not belong in
the same clause as the exploit counts if the rewrite wants the register to be one
clean claim.

### 2.4 How many metrics, how many families

**38 metrics over 5 families.** (R, from `battery.metrics.REGISTRY`; matches
`battery/artifacts/gaming_audit.json` `metrics` having 38 keys and
`battery/METRICS.md`):

| family | n |
|---|---|
| epistemic | 14 |
| economy | 7 |
| exploration | 6 |
| mechanism | 6 |
| planning | 5 |

Directions: 19 `higher`, 12 `lower`, 7 `neutral`.

### 2.5 The V9 numbers, if the rewrite chooses to lead with the blind round

All from `battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json`,
field `verdict` unless stated:

| claim | field | value |
|---|---|---|
| metrics | `n_metrics` | 38 |
| attacks executed | `n_attacks` | **112** (105 blind + 7 from the non-blind adversarial re-review, `attacks/a7_review.py`) |
| metrics attacked | `n_attacked` | 38 (`unattacked` = []) |
| attacks that landed (S1∧S2∧S3) | summed over `metrics[*].attacks[*].succeeded` | **95** |
| metrics gamed to the pre-registered target | `gameable` | **37** |
| metrics not gamed | `not_gameable` | **0** |
| M3 | `undetermined` | `["M3"]` — it answered *no* attack, because `cross_level_first_use_delay` never calls `ok(...)`; recorded as "withheld, not survived" |
| main table after V9 | `main` | **[]** (0 metrics) |
| reference | `reference` | 37 |
| prior main table | `b14_baseline_main` | `["E2","E3","K7","K11","K12","M3","M6","P3","P4"]` (9) |
| disagreements with the sighted round | `disagreements_with_b14` (top level) | 9 |
| attackers | `battery/BLINDING.md` §1 | 6, mutually invisible, each seeing only a subset of metrics |
| defences landed | `battery/audit/v9/REPORT.md` §4 | 3 (D1/D2/D3); **none rescued any metric into the main table** |

Cross-checks: `battery/runs/.../RUN_STATE.md:8,11` ("六个互不可见的盲攻击者",
"112 次攻击，覆盖 38/38 条指标，95 次落地"); `battery/audit/v9/REPORT.md` §0
("38 条指标，37 条被刷到了预注册门槛；95 次攻击落地。主表从 9 条变成 0 条");
`battery/STATUS.md` B16/B17.

**One internal inconsistency in the V9 report, for the record:** §0 and the run
state say 95 landed attacks, while §6/§7 of `battery/audit/v9/REPORT.md` say
"91 条落地攻击里 51 条捏造生产者侧记录". The artefact says 95. Do not quote 91.

---

## 3. What the result licenses, and what it does not

### 3.1 The strongest honestly supportable claim

Not "these 38 metrics are gameable" as a statement about agent evaluation
generally, and not merely "a self-check". The defensible statement is:

> **A metric battery, audited against its own executable exploit register, found
> almost none of its metrics safe — and when the same audit was re-run by six
> blind attackers against pre-registered thresholds, 37 of 38 metrics were
> reached without the capability and the battery's main table went to zero.**

Scoped to **this** battery. Nothing here licenses a claim about ARC-AGI scoring,
about other agent benchmarks, or about metrics in general. What generalises is
the *method* — write the exploit register as code, recompute `succeeded` from the
scorer, and let the tier fall out — plus the observation that the prose register
written by the metrics' own author was wrong about 17 of its 38 entries and
14 of its 19 defence claims, which is a statement about the reliability of
hand-written threat registers, not about the metrics of other people.

### 3.2 Scope and sample limits, all of which must survive the rewrite

1. **The exploits are constructed objects, not agent behaviour.** Every exploit
   run is a `Run` dataclass assembled in Python
   (e.g. `battery/audit/exploits/mechanism_epistemic.py:689-713`). No game was
   played, no model was called, no API was touched. The paper's §7.7 phrase "an
   actual run" is defensible only because the battery scores `Run` objects and
   these are real `Run` objects; a referee will read "run" as "episode". Say
   "a constructed trajectory" or "a fabricated ledger".
2. **This is a demonstration of *reachability*, not of *behaviour*.** Nobody
   showed an arm actually doing this. `accidental` — the field that decides
   whether a metric falls — is the one hand-set judgement left in the pipeline
   (`battery/audit/exploits/__init__.py:28-32`; `PREREG_V9.md` §1).
3. **The threat model is not layered.** `battery/audit/v9/REPORT.md` §7: of the
   91–95 landed attacks, **51 fabricate producer-side records**. Whether an *arm*
   could reach that state and whether an *adapter* wrote that value are different
   questions, and the battery trusts both equally. K12's demotion is producer-side;
   P4's was confirmed arm-side by the adversarial reviewer (§9(a)).
4. **The V9 thresholds are not calibrated against honest data.**
   `battery/PREREG_V9.md`, 未修订段: of 31 directional metrics, **15 already have
   an honest run that reaches the "gamed" threshold** (X6 65/71, X2 59/87,
   P3 47/85, P4 1/1). For those, S2 measures *attainability*, not *gameability*.
   The report grades the nine demotions strong/medium/weak accordingly
   (`REPORT.md` §9(c)): **strong** = E2, E3, K12; medium = P3, P4, E1;
   **weak** = K7, K11, M6 (these three rest entirely on the §1.1 controllability
   criterion, which is near-automatic for counting diagnostics).
5. **The poverty certificate has zero demonstrated selectivity.**
   `REPORT.md` §7 and §9(a): it passed **105/105** attacks and has never rejected
   one. "These are all cheats and not real work" is held up by attacker
   discipline, not by the checker. Two holes were found and fixed by the
   adversarial reviewer (a closure escape; lambdas/conditional comprehensions).
6. **The blind is procedural, not enforced.** `BLINDING.md` §3.4: the attackers
   were sub-sessions on the same filesystem, held only by written instruction.
   §3.5: the aggregator was not blind. A full-corpus check for leaked repo proper
   nouns found zero hits (`REPORT.md` §9(d)), with one registered leak: K2's
   `thin()` string literally contains `39960` and "3 adversarial gaps", which two
   attacks used (`BLINDING.md` §3.7) — the report argues the attack does not
   depend on it.
7. **The surrounding pilot certifies nothing statistically.** 95 runs, 5 arms
   (`bare_cc` 80, `schema_repro` 8, `theoria_a2` 4, `theoria_a0` 2,
   `theoria_a0_spike` 1), 4 development-pile games
   (`battery/artifacts/capability_spectrum.json`, `runs`). A two-sided sign test
   over 4 paired games has a smallest attainable p of 0.125
   (`battery/REPORT_V0.md`, quoted at `07_battery.md:248-252`). **This bound does
   not apply to the register result** — the exploit finding is existential
   ("here is a run that scores 1.000 with nothing behind it"), so it needs no
   power at all. Do not let the two claims contaminate each other in the abstract.
8. **The published artefact does not regenerate.** §0 above. If the abstract
   cites 34/17/9, it cites a file the repository's own code no longer produces.

### 3.3 The ordering question: was the register written before or after the metrics?

This matters most, and the answer is layered. **It is not a pre-registration in
the sense §1.1 of the paper uses for A0.**

| layer | when | who | independence |
|---|---|---|---|
| the 38 metrics | v0–v1 | the battery's author | — |
| the prose `GAMING_REGISTER` | written **with/after** the metrics, by the same author, as part of process 4 | same author | none. `battery/STATUS.md` W-1, quoted at `07_battery.md:196-199`: "the author built the metric definitions, and a definition can be tuned toward a hoped-for result… neither substitutes for a second pair of eyes" |
| the executable exploits (B14/B15) | **after** the metrics and after the prose register | three independent adversarial audits | partial. `battery/BLINDING.md` §4: `gaming.py` was in the same tree and lists `how_to_game` and `defence` per metric, so *"B14 的 38 个 exploit 至少有一部分是按登记簿的提示去实现的，而不是独立发现的"* |
| the V9 blind round (B16/B17) | **after** everything, with success criteria committed **before any attack ran** | 6 mutually invisible attackers who never saw the register, the exploits, the artefacts, or the tier assignments | strong. Ancestry proved by `git merge-base --is-ancestor` with the transcript in the run directory |

So: **the register post-dates the metrics** — it is a self-check in origin. What
upgrades it beyond a self-check is (a) `succeeded` being read from the scorer
rather than asserted, which makes the *entries* falsifiable, and (b) the V9
round, where the attack criterion was fixed in advance and the attackers were
blinded to the design intent. The honest framing is: **the first round is a
self-audit made falsifiable; the second is a blinded, pre-registered adversarial
round that overturned the first round's surviving nine.**

One breach to disclose if V9 is used: `PREREG_V9.md` 修订 1 records that
`verdict.py` — the adjudication implementation — was **not** in the
pre-registration commit (only `check.py` and `prereg.py` were), and that the
`NOT defended` clause was collapsed after results were seen. The direction of the
change was stricter, and it is recorded as an appended revision rather than an
edit, per the file's own protocol. The report calls this *"本轮预注册最实的一处
失守"*.

---

## 4. The honest one-sentence versions

Pick one. All three are checked against the artefacts above.

**(a) Conservative — cites only the published artefact, survives even if the
staleness is not addressed:**

> Every one of this battery's 38 metrics was given an executable exploit — a
> fabricated trajectory the battery's own scorer grades — and 34 of them scored
> the metric well while containing none of the capability it names, contradicting
> 17 of the 38 hand-written register entries, 14 of those on the claim that a
> defence was implemented
> (`battery/artifacts/gaming_audit.json`).

**(b) Recommended — leads with the blind round, is the stronger result, and is
the one the repository's current state supports:**

> When the battery's anti-gaming register was rewritten as executable
> demonstrations and then re-attacked by six blind attackers against thresholds
> fixed in advance, 37 of its 38 metrics were driven to a "good" score by a
> trajectory with none of the capability behind it, the 38th only because it
> never returns a value at all — and the table of metrics the battery considers
> safe to rank arms with went from nine to zero
> (`battery/runs/20260729T021247Z-V9-battery-gaming-audit/v9_gaming_audit.json`,
> `verdict.gameable`, `verdict.main`; `battery/METRICS.md`).

**(c) The version a skeptical referee cannot shoot down at all** — every clause is
a fact about code that ran, with no generalisation:

> An anti-gaming register that is executed rather than written is falsifiable,
> and executing this one falsified 17 of its own 38 entries.

Avoid, in the abstract: "these metrics are gameable" without "this battery's";
"an arm could game them" (nothing was shown about arms); any pairing of the
exploit counts with the p = 0.125 power floor, which belongs to a different
process; and the current numbers 34 / 17 / 9 without either regenerating the
artefact or saying which round they come from.

---

## 5. Recommendation for the rewrite

1. **Lead with the register, as the reviewers converged on — but lead with the
   blind round.** The paper's §7.7 stops at B14/B15. B16/B17 are committed,
   documented (`battery/PREREG_V9.md`, `battery/BLINDING.md`,
   `battery/audit/v9/REPORT.md`), provenance-stamped, and strictly stronger:
   pre-registered criteria, blinded attackers, mutation-tested defences, and an
   adversarial re-review that overturned two of the aggregator's own conclusions.
   A blinded pre-registered adversarial audit is a far better lead contribution
   than a self-audit, and the repository already has it.
2. **Either regenerate `battery/artifacts/gaming_audit.json` or state its date.**
   Right now the abstract, §7.7, §7.2a and §10.5 print a nine-metric main table
   that `battery/METRICS.md` line 33 contradicts in the same repository. Whatever
   else the rewrite does, that has to stop being true. (Note `PREREG_V9.md` §5
   deliberately froze the artefact directory; §7 of the V9 report also registers
   that a bare `run_battery` would overwrite it. A regeneration is a decision,
   not a chore.)
3. **Fix "at or near its best value."** For 11 of 38 metrics that condition is
   unchecked (hard-coded `succeeded=True`), and for the 7 neutral diagnostics it
   is undefined. The V9 formulation — "reached a threshold fixed before the
   attack" — is both stronger and true of all 38.
4. **Split the X3 clause out of the register sentence.** It is a process-1
   discrimination finding, carries `verdict: underpowered` and an arm/harness
   confound, and dilutes an otherwise power-free existential result.
5. **Keep §7.7's honest edges in the intro**, not just in §10: `accidental` is
   still a human judgement; 51 of the landed attacks fabricate producer-side
   records; 15 of 31 directional thresholds are already reached by honest runs;
   the poverty certificate has never rejected anything.
