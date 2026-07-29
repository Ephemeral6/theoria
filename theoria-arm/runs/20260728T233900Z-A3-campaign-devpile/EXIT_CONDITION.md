# What "push the Theoria arm to the exit condition" actually asks for

Source: `Theoria.md` line 357, quoted verbatim:

> `- **退出条件现在写死**:开发堆 U3 达成 ≥⟨k⟩ 局 + 分数落 ⟨Δ⟩ 内 + 账单形状可见;或预算 ⟨B⟩ 顶到——先到为准。`

A three-way conjunction (U3 on ≥k games AND score within Δ AND bill shape
visible), OR budget exhaustion, whichever lands first.

## The bar is structurally complete and numerically empty

The section header says 现在写死 — "fixed now". It is not. `k`, `Δ` and `B` are
all still angle-bracket placeholders in the same sentence, and line 383 lists
them among the five things explicitly deferred to freeze time:

> `**冻结前待定五项**:⟨公开集总局数 N⟩、⟨开发堆局数(建议 3–5)⟩、⟨模型配对版本串⟩、⟨预算 B 与 Δ, k, m, n⟩、⟨目标会议与死线⟩。`

A repo-wide search binds none of them. `monitor/state.json` independently
records the same hole:

> `退出条件（U3 达成 ≥k 局 + 分数落 Δ 内 + 账单形状可见，或预算 B 顶到）里的 k/Δ/B 也还没定。`

**Consequence for this ticket.** "Push the arm to the exit condition" cannot
mean "cross the line", because the line has no coordinates. It can only mean
*produce the evidence the three conjuncts are made of*, and pin what is
pinnable. Claiming exit against unbound placeholders would be the exact
dishonesty the ticket's own last sentence forbids.

### The three conjuncts, and what each would need

**U3** is defined once, at line 262: `证得动吗` — third rung of a four-rung
ordinal ladder (U1 manual matches the past / U2 checkable text not prose / U3
provable / U4 repairs well when falsified). Two problems with using it as a
gate:

* Theoria.md gives **no per-game rubric** for scoring U3 — no judge, no
  threshold, no definition of what counts as 证得动. The only mechanizable
  proxy in the document is `certify`'s expensive layer (line 227): all universal
  assertions discharged, no-ambiguity obligations cleared, playbook
  theorem-grade entries hold relative to the manual, dependency assumptions
  empty.
* Lines 262 and 332 both say the U ladder is **rank-only, not evidence**
  (`两器合一才是完整评测协议;U 阶梯仍只排座次`) — yet line 357 and line 373 both
  lean on it as a gate and a primary endpoint. That tension is in the source
  document, not introduced here.

**Δ** — the deeper hole: *Δ from what baseline?* The only place a baseline is
named is the bet table at lines 268–272, where the Theoria cell reads
`⟨目标:基线 −Δ 内⟩`. The word 基线 is never disambiguated. Two readings:

* **Schema's reproduced dev-pile value** (`⟨复现值⟩`, line 271) — the strong
  reading, and the one that makes the claim non-trivial. Line 309 says the score
  ceiling is already at 98.98 and `天花板上没有分辨率`; line 274 says Theoria
  concedes score and buys understanding. So Δ measures how much score Theoria is
  *allowed to give up* against Schema.
* **Bare CC's 42.83%** — ruled out: "within baseline − Δ" against 42.83 would be
  a floor, not a bar.

Note the `—(基线口径)` on line 270 attaches to the *cache-read* column, not the
score column, so it does not settle the referent. The acceptance bar's
denominator is not written down anywhere in the repo. Pinning it is a decision
that belongs to whoever owns Phase 4's freeze, not to a worker session; this run
records it as a gap and adopts the strong reading provisionally, labelled as
provisional.

**账单形状可见** is the one conjunct that is fully specified as *measurables*,
even without a numeric threshold. Line 319's 经济 battery family names four:

> `| 经济 | 逐回合成本曲线、前载指数(前 k% 回合花掉的成本占比)、收敛点、上下文增长的二次/线性拟合 | 账单形状——无知的仪表 |`

plus the predicted shape at line 59 (`前重…后轻…收敛后趋零`, against Schema's
flat curve) and claim C2 at line 360. The 前载指数 is promoted to a Phase 4
**primary endpoint** at line 373. Line 274 adds the hygiene cut that decides
whether the shape counts as evidence at all: diff-and-objectify saves money from
turn one and that is 工程省 which anyone can copy; only savings bought by
understanding count, and separating the two is the ablation arm's job.

**So the tractable target for this ticket is the third conjunct**: the per-turn
cost curve, the front-load index, the convergence point, and the context-growth
fit — measured on the dev pile, per turn, with the seven surprise counters and
theorize rounds beside them. That is exactly what the ticket calls "figure 2's
entire raw material", and unlike k and Δ it needs no absent decision.

## Hard rules this campaign is bound by

* **The money gate (line 305).** The Phase 1 acceptance list must be *all* green
  before game money may be burned — the sentence is literally
  `全绿才准烧游戏钱(Phase 3 的门)`. Verified separately before any spend; see
  `PHASE1_GATE.md` in this run dir.
* **Game IDs never enter model context (line 353).** `硬规:游戏 ID 永不进模型
  上下文,全程匿名化`. This is one of four overfitting channels sealed by name.
  Same line: prompts must contain no game-specific content, prompt iteration
  happens only in the self-built A0 world family, and each iteration gets a diff
  review.
* **Sealed pile, zero contact (line 311/303)**, including upstream artifacts.
* **Action quota may bind before tokens (line 299)** — and probes and
  prefix-replay teleports both consume the action budget (line 208).
* **Constraint 8 (line 246):** no surprise ⇒ no model call; execute, certify and
  the engines make zero calls throughout. A campaign whose execute phase calls
  the model has broken a constraint, not merely overspent.
* **Reconciliation (line 291):** ledger-derived score must equal the API
  scorecard score; unequal = incident. One scorecard per game; probes get a
  separate probe-marked scorecard so they do not pollute the main run's counts.
* **One change at a time (line 336):** `禁忌:一次改多件(归因毁),对单局差分做
  决策(方差骗人)`.
* **Stop-loss still ships (line 381):** if a stop-loss triggers, the level's unit
  is still delivered — `沉没的工作不许搁浅`. This is the ticket's "hand in the
  partial result" clause, and it is in the design document, not just the board.

## The seven surprises, for the counters

Line 124/233, in order. Empirical family (five, all amend the **manual**):
重放失配, 渲染失配, 证明失败, 戳探打脸, 执行失配. Computational family (two, both
amend the **playbook**): 搜索超时, 启发失准.

Bookkeeping subtlety that is easy to get wrong and that the counters must
respect (line 124): a proof failure on a *playbook* theorem-grade entry is still
counted under 证明失败 (#3), but the ledger record must carry a **book label** —
`玩法书定理条目的证明失败随证明失败计,记账带书别标签`.

## The five beats, which may not be touched

Line 222: `theorize → certify → probe → plan → commit`. Line 355 puts them on
the do-not-touch list along with the ten constraints, the three division laws,
co-derived multi-form, the shell and the ledger. Movable in Phase 3: theorize
prompts and dispatch strategy, DSL expressiveness, probe strategy, the
segmentation operator space, the engine roster.
