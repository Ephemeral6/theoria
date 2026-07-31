# Six specifics for the abstract / §1 rewrite — evidence

Prompt: P-13 (paper intro + abstract). Worktree:
`.worktrees/p13-paper-intro-abstract`. Read-only pass; no section file was edited.
All paths repo-relative. Line numbers are as of this worktree's HEAD.

---

## 1 · The title problem

### 1.1 The title, and the §2.3 passage that contradicts it

Title — `papers/phase1-workshop/sections/00_abstract.md` L1:

> # Certifying a world theory against something other than its own past

§2.3 — `papers/phase1-workshop/sections/02_framework.md` L65–85, verbatim
(L65–78 setting up the two layers, L80–85 the decisive part):

> ### 2.3 The inner loop, and the word *certify*
>
> `Theoria.md` §1.10d: **theorize → certify → probe → plan → commit.**
>
> `certify` is used here in a narrower sense than the field's. It is two layers,
> and both must pass:
>
> * the **cheap** layer — full-history replay through the generated predictor,
>   scored at the pixel, with every pixel the responsibility of the board or of
>   some object;
> * the **expensive** layer — the declared laws discharged in Lean, with
>   `#print axioms` inspected. An empty axiom list is the pass condition; `sorry`,
>   `native_decide` and `ofReduceBool` are all failures.

`sections/02_framework.md` L79–85:

> The two layers do different jobs and the paper turns on the difference. Replay
> certifies *against the past*. Lean certifies *relative to the manual* — it can
> sign a theorem that is false of the world, and §5 is a worked exhibit of exactly
> that, as two files a reader can diff. Neither layer certifies the manual against
> the world. That is what `probe` is for: an experiment, chosen by the engine for
> how many bits it splits, whose prediction is written down *before* the action is
> taken (`Theoria.md` §1.10e, constraint 7).

The load-bearing sentence is `sections/02_framework.md` L82–83:
**"Neither layer certifies the manual against the world."**

### 1.2 In what way the title overclaims — precisely

The word `certify` in the title is the paper's own narrow, defined sense (§2.3:
two layers, replay + Lean). The title asserts that this `certify` is run
"against something other than its own past". §2.3 states that:

* layer 1 (replay) certifies **against the past** — i.e. exactly what the title
  says the paper goes beyond;
* layer 2 (Lean) certifies **relative to the manual** — i.e. against the theory's
  own statement of itself, which is a *narrower* reference class than the past,
  not a wider one. A Lean pass is compatible with the theorem being false of the
  world, and §5 is the constructed exhibit of that.

So both implemented certification layers are self-referential, and §2.3 names the
one mechanism that would discharge the title — `probe` — as a *different beat of
the loop*, not part of `certify`. The title therefore attributes to `certify` a
property that §2.3 explicitly withholds from both of its layers.

Two further facts make the overclaim sharper rather than merely verbal:

* the probe beat is barely exercised. `sections/03_a0.md` L118 (§3.3 table):
  A0 emitted **0** executable probes; A0′ emitted **13**.
* the live run's probe/commit beats were "reached but barely exercised"
  (`sections/09_preflight.md` L155–159), with `probe_actions: 0` in
  `theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json` L14.

The honest statement the paper *does* support is the negative one: that the two
certification layers it implements are both against-the-past or
against-the-manual, and that the gap between them and the world is exhibitable as
a diffable artefact.

### 1.3 Three candidate replacement titles

Each is true of what the paper actually does, and each is checked against
`sections/02_framework.md` L82–83.

1. **"Neither layer certifies the manual against the world: a Phase-1 instrument
   for the replay-invisible failure"**
   — *Why §2.3 does not contradict it:* the title is §2.3's own sentence quoted
   verbatim, so consistency is definitional; the paper's contribution is then
   correctly framed as the instrument, not the certification.

2. **"Full-history replay passes, the theory is false: two certification layers
   and the gap neither closes"**
   — *Why §2.3 does not contradict it:* §2.3 asserts exactly this structure
   (replay ⇒ against the past; Lean ⇒ relative to the manual; neither ⇒ against
   the world), and the title claims only that the gap is *shown*, never closed.

3. **"An artefact that produces the replay-invisible failure on demand: Phase 1
   of Theoria"**
   — *Why §2.3 does not contradict it:* the title makes no certification claim at
   all, so §2.3's restriction on `certify` has nothing to bite on; it also matches
   the abstract's own closing scope sentence (`sections/00_abstract.md` L123–125,
   "Phase 1 establishes that the instrument exists, that it produces the failure
   mode on demand, and that the loop closes on it — not a result about world
   models") and §11.3 L242–244.

(A fourth, if a shorter head is wanted: **"Certifying against the manual is not
certifying against the world."** Same argument as (1).)

### 1.4 The subtitle: "a transfer result" and "an examination instrument"

Subtitle — `sections/00_abstract.md` L3–5:

> ### Phase 1 of Theoria: three offline acceptances and a transfer result, a
> ### passive metrics battery, an examination instrument, and a live run that
> ### spent nothing

§10.5 disclaims **both** in one sentence —
`papers/phase1-workshop/sections/10_limitations.md` L252–253:

> Everything else in `Theoria.md` — the ordering claim, the bill shape, transfer,
> the exam, the cost magnitude — is unevidenced here and is not claimed.

Supporting, in the body:

* transfer — `sections/00_abstract.md` L58–61 already calls §6 "a fourth section
  reporting an early read on claim C3 that the mandate does not list as an
  acceptance"; `sections/06_a3_transfer.md` L10–13: "A3 answers it for two levels
  of one game, which is the weakest interesting reading of C3 … Anything stronger
  needs a different experiment".
* the exam — `sections/08_exam.md` L1: "## 8 · The exam — four papers, one sat,
  and a check that did nothing"; L53: "### 8.2 The marker is calibrated; three of
  the four papers have never been sat".

So the subtitle advertises two deliverables that §10.5's closing sentence names as
"unevidenced here and … not claimed". This is a direct internal contradiction, not
a matter of emphasis.

---

## 2 · The 98.98 denominator

The intro's hook — `papers/phase1-workshop/sections/01_intro.md` L3–7:

> A world model can replay every frame of its own history without a single error and
> still be bankrupt as an account of the world. The claim is not new — it is the
> constructive gap `Theoria.md` §1.3 states, and the reason that document gives for
> why a score of 98.98 on replayed history (`Theoria.md` §3.1) stopped resolving
> anything about understanding.

The source, `Theoria.md` §3.1, L393 (Chinese; the only place §3.1 states the
number):

> **第二波:程序世界模型。** LLM 让"把世界写成代码"变得可行:WorldCoder 让 agent 以写
> Python 的方式学环境模型并边玩边改;RAP 一类把 LLM 自身当世界模型来规划。Schema 把这
> 条路在 ARC-AGI-3 上推到顶:世界模型是一份可编辑、可执行的程序,对全部已录历史重放当
> 检验——98.98%,+56pp 全部来自过程而非权重。

The only other §3.1 occurrence, `Theoria.md` L395:

> 分数一路暴涨,检验制度却停在"对过去成立":这就是 98.98 之后测量真空的来源,也是分数
> 失去分辨率的原因。

And in the bets table, `Theoria.md` §1.12 L271:

> | Schema(复现口径) | 98.98%(上游)/ ⟨复现值⟩ | ~10⁸(实测 2.04–3.41 亿) | world_model.py(重放级) |

The paper's own §11.1 already characterises it —
`papers/phase1-workshop/sections/11_related.md` L49–52:

> And the 98.98 % and +56pp figures that `Theoria.md` §3.1 quotes are self-reported
> on the public set and are `Theoria.md`'s summary of prior work, not a measurement
> of ours.

### Answers

| question | answer | source |
|---|---|---|
| 98.98 of **what** | a **score** (ARC-AGI-3 scoring), not a replay-fidelity figure | `Theoria.md` L393, L271 |
| **on** what | ARC-AGI-3 (`在 ARC-AGI-3 上`), the **public set** | `Theoria.md` L393; `sections/11_related.md` L50–51 |
| **by whom** | Schema — canonically **Zeng et al.**, self-reported | `Theoria.md` L393; `sections/11_related.md` L47–51 |
| **units** | percent — the source writes `98.98%` | `Theoria.md` L393, L271 |
| **denominator** | **NOT ESTABLISHED.** `Theoria.md` §3.1 gives no set size, no game count, no per-game breakdown, and no definition of what the percentage is averaged over. `Theoria.md` §1.12 L271 repeats the bare `98.98%(上游)` in a table column headed 分数. Nothing in the repository states a denominator. | — |

**Two corrections the rewrite must make.**

1. **"on replayed history" is a misattribution.** In `Theoria.md` L393, replay
   (`对全部已录历史重放当检验`) is Schema's *verification regime*; 98.98% is its
   *game score*. The intro fuses the two. The nearest thing to a
   replay-fidelity denominator anywhere in the sources is `Theoria.md` §3.2 L412
   — "19 局满分只有 14 局真的复现了历史" (of 19 games at full marks, only 14
   actually replayed the history) — which is a *different* statistic, is not
   attached to the 98.98 figure, and carries no citation of its own.
2. **The rewrite cannot state a denominator.** It can state: units (percent),
   attribution (Schema / Zeng et al., self-reported), set (ARC-AGI-3 public set),
   and provenance (`Theoria.md` §3.1's summary of prior work, not a measurement
   of ours). It must not invent "of N games" or "of N frames".

This is already logged as an open item: this run's
`evidence-review-todo.md` **T19** ("The paper's 'hook' number, 98.98, has no
denominator" — lay reviewer 2.7), marked **Fixed? NO**.

---

## 3 · §10.5 in full, and §11.3's instruction about the abstract

### 3.1 `papers/phase1-workshop/sections/10_limitations.md` L236–253, verbatim

```
236	### 10.5 The one thing this paper claims
237	
238	That the pipeline runs end to end on self-built deterministic worlds; that on
239	those worlds a manual can be perfect on replay and wrong about the world in a way
240	that was predicted in advance and later measured; that reversibility of a
241	mechanism mattered more than breadth of trajectory in the one controlled
242	comparison run; that a machine-checked impossibility can be produced whose
243	weights crossed a data boundary between two independently developed tracks and
244	whose empty axiom list is a check that has been made to fail on purpose; that the
245	refutation loop closed on a false theorem in six recorded beats; and that a
246	passive metrics battery over existing trajectories, once its anti-gaming register
247	was made executable rather than written, contradicted 17 of its own register
248	entries by demonstration — 14 of them defence claims
249	(`battery/artifacts/gaming_audit.json`) — and found the exploration family's
250	declared signature separating the specified gradient backwards.
251	
252	Everything else in `Theoria.md` — the ordering claim, the bill shape, transfer,
253	the exam, the cost magnitude — is unevidenced here and is not claimed.
```

Note that §10.5 is itself under three live retractions (P12 review-d-adversarial
§3, `runs/20260728T173000Z-P12-paper-multi-review/review-d-adversarial.md`
L133–171): "the one **controlled** comparison run", "two **independently
developed** tracks", and "**predicted in advance and later measured**" are each
contradicted elsewhere in the same paper. The abstract was fixed; §10.5 and §1.3
were not.

### 3.2 §11.3 — the sentence about how the abstract should read

`papers/phase1-workshop/sections/11_related.md` L241–244:

> **"Prediction perfect, understanding broken" is this framework's own premise, not a
> finding.** §5's procedure is to take a certified manual, delete a rule that never
> fires in the retained history, and observe that replay over that history does not
> notice — which is analytically guaranteed by the construction. The exhibit has
> value as a teaching object and as a test of the instrument. It is not evidence
> about anything, and the abstract should not read as though it were.

The operative clause is L244: **"It is not evidence about anything, and the
abstract should not read as though it were."** It is scoped to the §5 (A2)
exhibit — the deleted-teleport pair — not to the whole paper. Abstract item **(4)**
(`sections/00_abstract.md` L79–86) is the passage it governs.

Its immediate neighbour, §11.3 L225–237, does the same for the A0/A0′ finding:
"'Reversibility beats coverage' is close to the reset assumption in active
automata learning."

---

## 4 · The uncited decisive artefact

**Path:** `cold-start-a0/artifacts/trace_summary.json`

**Relevant fields (key `a0-base`), verbatim from the file:**

| field | value | line |
|---|---|---|
| `coverage` | `"233/236"` | L6 |
| `covered_pairs` | `233` | L7 |
| `state_action_pairs` | `236` | L22 |
| `frames` | `276` | L16 |
| `transitions` | `275` | L23 |
| `reachable_states` | `59` | L21 |
| `uncovered_pairs` | `["cart=(2,2) pressed=0 act=DOWN", "cart=(3,1) pressed=0 act=RIGHT", "cart=(4,2) pressed=0 act=UP"]` | L24–28 |

Key `a0-no-button` records the unsolvable variant: `coverage "92/92"`,
`uncovered_pairs: []` (L37–51).

**The weaker artefact the intro actually cites** —
`cold-start-a0/artifacts/score_vs_truth.json`, cited at
`sections/01_intro.md` L19 as "field `held_out.accuracy`":
`base.behavioural.accuracy 0.987288`, `agree 233`, `disagree 3`, `pairs 236`
(L4–7, L60); `base.held_out.accuracy 0.0`, `agree 0`, `disagree 3`,
`held_out_pairs 3` (L63–66, L120). Its `held_out.examples` (L67–119) are the same
three configurations, in structured form.

**Why `trace_summary.json` is decisive and `score_vs_truth.json` is weaker (two
sentences).** The claim has two halves — "the manual replays its own history
perfectly" and "is wrong on pairs the history never contained" — and
`score_vs_truth.json` establishes only the second half plus a *label*: it reports
accuracy 0.0 on three pairs it calls `held_out`, but the file is a scoring output
and never measures the trajectory, so "held out" is the scorer's own naming rather
than a measured property of the history. `trace_summary.json` is the only artefact
that measures the *trace*: its `covered_pairs: 233` of `state_action_pairs: 236`
and its explicit `uncovered_pairs` list, item for item identical to
`score_vs_truth.json`'s three `held_out.examples`, is what turns "the manual is
wrong on three pairs" into "the manual is wrong on exactly the three pairs the
history could never have contained" — the identity of the two triples *is* the
finding.

**Status.** `trace_summary.json` for A0 is cited **nowhere in `sections/`**
(grep over `papers/phase1-workshop/sections/`: the only hits are
`cold-start-a2/artifacts/trace_summary.json` in `05_a2.md` L52, L68). It appears
in `PROVENANCE.md` L35 only for "A0 world size · 59 reachable states, 276 frames".
`CITECHECK.md` L68 flags the bare filename as ambiguous across three files.
This run's `evidence-review-todo.md` **T18** records the reviewer's version —
"That file is the strongest evidence in §3 and the paper does not cite it. This is
the binding rule failing on the paper's best number." — marked **Fixed? NO**.

One caveat the rewrite should not trip over: `REVIEW.md` L436 notes that both the
233 and the 236 descend from `cold-start-a0/world/explorer.py`, so citing
`trace_summary.json` makes the identity *auditable*, not *independent*.

---

## 5 · The live-run / preflight conflation

Abstract result (8) — `sections/00_abstract.md` L110–112:

> **(8)** A live run against the real API that exercised the whole
> credential path — key injected in one place, sealed pile untouched by a check on
> the bytes — for zero billable actions.

The reviewer is right: **this is two runs**.

### 5.1 Run A — the preflight

`theoria-arm/runs/preflight-20260728T012057Z/` (§9.1,
`sections/09_preflight.md` L26–36).

From `theoria-arm/runs/preflight-20260728T012057Z/MANIFEST.json`:

| field | value | line |
|---|---|---|
| `budget.commands_sent` | `18` | L14 |
| `budget.actions_ok` / `actions_failed` | `0` / `0` | L10, L12 |
| `budget.resets` | `1` | L19 |
| `cost.cli_reported_usd` | `0.0` | L32 |
| `cost.model_calls` | `0` | L39 |
| `reconciliation.successful_actions` | `0` | L118 |
| `reconciliation.env_steps` | `18` (of which `env_steps_ok: 1`) | L111–112 |
| `ledger.records` | `23` | L56 |
| `game_id` | `null` (the game is in the ledger; §9.1 names `g50t-5849a774`) | L52 |
| `sealing` block | `bypass_attempts 0`, `credential_in_body 0`, `guard_blocks 0`, `incidents 0`, `redacted_markers 0`, `sealed_pile_requests 0` — **and nothing else** | L122–130 |

**The preflight's `sealing` block has no `sealed_game_ids_found`, no
`sealed_pile_untouched`, no `cut_integrity`, and no
`game_ids_anywhere_in_the_records`.** There is no byte scan. §9.2 says so
itself — `sections/09_preflight.md` L89–90:

> The preflight manifest predates that scan and carries only the counters.

### 5.2 Run B — the first-contact run

`theoria-arm/runs/20260728T015354Z-g50t-first-contact/` (§9.2 L80–90, §9.4
L151–159).

From `theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json`:

| field | value | line |
|---|---|---|
| `cost.cli_reported_usd` | `6.317658` | L47 |
| `cost.from_price_table.usd_total` | `5.795338` (`delta_usd: -0.52232`, "the price table and the provider's own arithmetic DISAGREE by -8.3%") | L62, L48, L77 |
| `cost.model_calls` | `5` | L64 |
| `budget.actions_ok` | `7` | L9 |
| `budget.commands_sent` | `40` | L11 |
| `reconciliation.successful_actions` / `scorecard_total_actions` | `7` / `7` | L193, L192 |
| `scorecard.score` / `levels_completed` | `0.0` / `0` | L251, L272 |
| `sealing.game_ids_anywhere_in_the_records` | `["g50t-5849a774"]` | L279–281 |
| `sealing.sealed_game_ids_found` | `[]` | L285 |
| `sealing.sealed_pile_untouched` | `true` | L287 |
| `sealing.cut_integrity` | `true` | L278 |

§9.2 L80–90 attributes the byte scan to this run explicitly:

> **The sealed pile was not touched, and here the check is real.** The
> first-contact manifest carries a byte scan of the records rather than the guard's
> opinion of what it blocked: `game_ids_anywhere_in_the_records:
> ["g50t-5849a774"]`, `sealed_game_ids_found: []`, `sealed_pile_untouched: true`,
> `cut_integrity: true`
> (`theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json`).

### 5.3 Exactly which run did what

| | preflight `012057Z` | first-contact `015354Z` |
|---|---|---|
| exercised the full credential path | **yes** | yes |
| billable ARC actions | **0** | **7** |
| commands sent | 18 | 40 |
| model calls | **0** | **5** |
| model spend | **$0.00** (`cli_reported_usd 0.0`) | **$6.317658** CLI-reported (price table says $5.795338) |
| byte-level sealed-pile scan | **NO** — counters only | **YES** — `sealed_game_ids_found: []`, `sealed_pile_untouched: true`, `cut_integrity: true` |
| credential injected in one place | yes (construction + mock test; §9.2 L70–78: "**no executable check scans the live ledger for the credential**") | yes, same basis |

Note two independent precision points for the rewrite. First, the $6.32 is
**model** spend (`cli_reported_usd`), not ARC quota; the ARC cost of run B is the
7 actions. Second, "key injected in one place" is *not* byte-verified on either
run — §9.2 L70–78 says the arm's archiver "advertises that check in its docstring
and does not implement it", and the byte-scanning test "runs against the mock". So
the abstract's dash-clause fuses three things, not two: a zero-spend run, a
byte-scanned sealed pile from a different run, and a credential claim that rests on
construction plus a mock test on both.

§9.4's own closing paragraph (`sections/09_preflight.md` L170–173) commits the same
fusion and should be fixed in the same pass:

> What the preflight does establish is narrow and worth having: the live chain
> runs end to end, the credential is injected in one place and the arm never holds
> it, the sealed pile is untouched by a check on the bytes rather than on the
> guard's self-report, and the whole thing cost zero billable actions.

### 5.4 One sentence true of both, without fusing them

> Two live runs against the real API exercised the whole credential path on one
> development-pile game: a preflight that sent 18 commands, spent zero billable
> actions and zero dollars, and a first-contact run that spent 7 actions and
> $6.32 in model calls and whose manifest carries the byte-level scan showing
> `sealed_game_ids_found: []`.

(Shorter, if the abstract cannot afford the clause: *"Two live runs on one
development-pile game — a preflight for zero billable actions and zero dollars,
and a first-contact run of 7 actions and $6.32 whose manifest byte-scans its own
records and finds no sealed game."*)

---

## 6 · The A0/A0′ contrast — "controlled" is wrong

### 6.1 The uncorrected §1.3 text

`papers/phase1-workshop/sections/01_intro.md` L97–101:

> 1. **A cold-start pipeline run end to end on self-built worlds**, from pixels
>    through engine proposals, adjudication, four co-derived forms, certification
>    and planning — with a controlled A0/A0′ contrast in which the second world's
>    manual reaches 228/228 = 100 % on 47 % of A0's state-action coverage
>    (`cold-start-a0/A0_REPORT.md` §8).

### 6.2 The corrected abstract wording (already on file)

`papers/phase1-workshop/sections/00_abstract.md` L66–72:

> **(2)** A second world, in
> which an irreversible latch is replaced by a reversible toggle and the explorer
> is truncated to under half the state-action coverage, yields a manual that is
> 228/228 correct. Reversibility of a mechanism mattered more than breadth of
> trajectory — **a design lesson demonstrated by construction rather than a
> hypothesis tested.**

The correction has two moves: the word "controlled" is **gone**, and the
epistemic status is stated as *demonstrated by construction rather than a
hypothesis tested*.

### 6.3 What makes the contrast uncontrolled — source on file

`papers/phase1-workshop/sections/03_a0.md` L91–101 (§3.3 body — note the heading
itself still says "controlled", which is a third unfixed site):

> ### 3.3 The controlled contrast
>
> A0′ is the same instance's second self-built world. The advertised change is that
> the Button's irreversible latch is replaced by a re-witnessable toggle, and the
> explorer is then *weakened* on purpose — two variables, not one. It is worth
> being blunt that they are not the only two: A0's manual has 3 objects and 7
> rules, A0′'s has 3 objects and 21, the worlds have 59 and 57 reachable states and
> 236 and 228 state-action pairs, and the mechanism object is a Button in one and a
> Switch in the other (`cold-start-a0/theory/theory.dsl`,
> `cold-start-a0/prime/theory/theory_prime.dsl`). "Identical except" would be a
> false description and is not used here.

`sections/03_a0.md` L145–155 (the sharper objection — analytic entailment):

> What kind of experiment this is should be stated plainly, and the usual
> disclaimer is not the one that bites. "**n = 1 per arm**, on worlds built by the
> same instance that theorized them" covers sampling error. The sharper objection is
> **analytic entailment**: A0′'s toggle was *designed* so that every
> direction-by-polarity combination would have its own witness
> (`cold-start-a0/prime/THEORIZE_LOG.md` R-03, sixteen clauses each at coverage
> 1/1). The adjudication rule — admit a generalisation iff every case is witnessed —
> then mechanically admits what it mechanically rejected in A0. The outcome follows
> from the construction; nothing was learned that was not built in.
>
> So this contrast **demonstrates the mechanism rather than tests it** …

**The finding that forced the correction** — `papers/phase1-workshop/REVIEW.md`
L196–213, issue 8:

> ### 8 · [SHOULD FIX] §3.3 — the "controlled contrast" changes more than one variable, and the abstract says so while §3.3 denies it
> …
> It is worse than two. `cold-start-a0/theory/theory.dsl` has 3 objects and **7 rules**;
> `cold-start-a0/prime/theory/theory_prime.dsl` has 3 objects and **21+ rules** …
> And the outcome is entailed by the construction rather than discovered by it. … The
> adjudication rule (admit a generalisation iff every case is witnessed) then
> mechanically admits what it mechanically rejected in A0. Nothing was learned that
> was not built in.

`papers/phase1-workshop/REVIEW_TRIAGE.md` L59 (why writing alone cannot fix it):

> | 8 | §3.3 — the "controlled contrast" changes more than one variable, and the abstract says so while §3.3 denies it | **W** | 7 vs 21 rules, 59 vs 57 states, 236 vs 228 pairs, Button vs Switch. The body is now honest; the abstract is not. **Writing closes the contradiction; it does not make the contrast controlled** — a genuinely single-variable A0/A0′ pair would be an `X`, and is not proposed |

`papers/phase1-workshop/OPEN_ITEMS.md` L43 (item C1):

> | **C1** | "Controlled contrast" changes at least two variables (7 vs 21 rules, 59 vs 57 states, 236 vs 228 pairs, Button vs Switch), and the outcome is analytically entailed by the construction. §3.3's body is now honest; the abstract is not. |

The P12 adversarial pass then found the fix had been applied to the abstract only —
`runs/20260728T173000Z-P12-paper-multi-review/review-d-adversarial.md` L157–163:

> **Status:** **partially logged, and the residue is the worst part.**
> `OPEN_ITEMS.md` C1 flags "controlled contrast" … but both are scoped to *the
> abstract*, and `REVIEW_TRIAGE.md` §B issue 8 records "The body is now honest; the
> abstract is not." The abstract has since been fixed. Nobody checked §10.5, or §1.3
> L232 (`sections/01_intro.md` L99, "a controlled A0/A0′ contrast"), or the §3.3
> **heading** itself (PAPER.md L485, `sections/03_a0.md` L91, "The controlled
> contrast"). The fix was applied to the place the reviewer named and not to the
> class of error.

Same file, L166–171, the proposed minimal edit for §10.5 and the sweep instruction:

> **Minimal edit.** In `sections/10_limitations.md` L238–245: "controlled comparison run"
> → "one paired comparison, whose outcome §3.3 shows is entailed by the construction" …
> Then sweep `sections/01_intro.md` L99 and `sections/03_a0.md` L91 for "controlled".

Also `runs/.../review-d-hostile.md` L210–220 lists the three surviving sites and
concludes: "The paper demolishes the word 'controlled' in §3.3 and then keeps it in
the [abstract/intro/heading]."

### 6.4 A second, independent error in the same §1.3 sentence

"**47 % of A0's state-action coverage**" is wrong as arithmetic, not just as
framing. The 47 % is A0′'s coverage of **A0′'s own** 228 pairs, per
`sections/03_a0.md` L116:

> | state-action coverage | 233/236 = **99 %** | 107/228 = **47 %** |

107/228 = 46.9 %. It is not 47 % *of A0's* coverage (233 pairs); A0's coverage is
99 %. The correct statement is that A0′'s explorer was truncated to 40 % of the
exhaustive walk (`sections/03_a0.md` L115) and covered 107/228 = 47 % of its own
world's state-action pairs.

### 6.5 Accurate replacement phrasing for §1.3 item 1

> 1. **A cold-start pipeline run end to end on self-built worlds**, from pixels
>    through engine proposals, adjudication, four co-derived forms, certification
>    and planning — with a paired A0/A0′ contrast, uncontrolled by construction
>    (the two worlds differ in mechanism, rule count, state count and explorer
>    budget), in which the second world's manual reaches 228/228 = 100 % while
>    covering only 107/228 = 47 % of its own state-action pairs. §3.3 shows the
>    outcome is entailed by the construction rather than discovered by it, so this
>    is a design lesson demonstrated by construction, not a hypothesis tested
>    (`cold-start-a0/A0_REPORT.md` §8; `cold-start-a0/prime/A0P_REPORT.md` §1).

Shorter variant, if §1.3's list must stay one sentence per item:

> … — with a **paired, uncontrolled** A0/A0′ contrast in which the second world's
> manual reaches 228/228 = 100 % on 47 % coverage of its own 228 pairs; §3.3 shows
> the outcome follows from the construction rather than testing a hypothesis.

Two companion edits belong in the same pass, since they are the same error class:
`sections/03_a0.md` L91 (the §3.3 heading, "The controlled contrast" → e.g. "The
paired contrast, and why it is not controlled") and `sections/10_limitations.md`
L241–242 ("in the one controlled comparison run").
