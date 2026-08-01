# GAPS — P-8's contract, line by line

What was asked, what was delivered, and where it fell short. A gap here is a
statement that something was **not** achieved; nothing in this file is a
softened pass.

---

## The target

> 把离线已四度证活的内环接到真 API 上——Theoria 臂的第一次在线对局，对象是开发堆
> `g50t-5849a774`。经 proxy 双代理走 observe→theorize→certify→probe→plan→commit；
> 引擎全部用 engine-rig 现成件，编译用 theory-compiler；theorize 的 LLM 调用过模型
> 代理入账。

| clause | status |
|---|---|
| inner loop connected to the live API | **done** |
| game `g50t-5849a774`, development pile | **done** |
| through the proxy — **environment side** | **done**; key injected inside the proxy, arm keyless, guard fingerprint verified |
| through the proxy — **model side** | **GAP**, see below |
| all six beats exercised | **partial**, see below |
| engines from `engine-rig`, unmodified | **done**; three dispatched, five declined with a reason each |
| compilation via `theory-compiler`, unmodified | **done** |
| constraint 8 has a measured bill | **done** |

---

## GAP 1 · The model side is recorded but not proxied

**Asked:** the theorize LLM calls go through the model proxy.
**Delivered:** they go through `claude -p` and are written into the same ledger
by the same frozen writer, carrying `proxied: false`.

**Why not:** established live, before the arm was written. The Claude Code CLI
authenticates with an OAuth bearer; `proxy/model_proxy.py` strips
`Authorization` by design and injects `ANTHROPIC_API_KEY`, which this repo's
`.env` does not contain. Every request returned `401 x-api-key header is
required`. Evidence: `evidence/model-proxy-401.jsonl`, 65 `model_call` records
at 401 and 66 `bypass_attempt` incidents.

**Why it was not fixed:** the two available fixes are (a) edit `proxy/`, which
belongs to another track and which CLAUDE.md puts off limits, or (b) obtain an
`ANTHROPIC_API_KEY`, which is not this arm's to obtain. The stripping is the
sealing property, not a defect.

**What is lost, precisely:** `request` is the prompt this arm sent the CLI, not
the `/v1/messages` body the CLI sent onward — the CLI adds a system prompt this
arm never sees. **No conclusion about input-token composition may be drawn from
this ledger.** Output usage, output cost and the per-call cost curve are
unaffected, because they come from the provider's own usage block copied
verbatim.

**What would close it:** an `ANTHROPIC_API_KEY` in `.env` and
`require_key=True`; nothing in this arm would need to change beyond pointing
`ModelDesk` at the proxy's base URL.

---

## GAP 2 · `plan` and `commit` were reached but rarely exercised

**Asked:** all five inner beats.
**Delivered:** theorize, certify and probe run every turn. `plan` runs every
turn and, on this world, almost always returns `no_goal_declared` — an ARC game
does not tell you what winning is, and a desk that has seen a few dozen
transitions honestly cannot say. With no goal, `is_goal` compiles to `False`,
no search can succeed, and `commit` has no script to execute.

**This is not a failure of the beats.** It is what the loop does when the
manual has not yet earned a winning condition, and the alternative — inventing
a goal so the planner has something to chew on — is exactly what constraint 5
forbids. `plan` reports `no_goal_declared` in language that cannot be mistaken
for unsolvability (constraint 6), and the arm falls through to probe.

**Consequence for the report:** the `execution_mismatch` surprise count is
structurally zero on this run, not measured-zero. A count of zero for a beat
that never ran is not evidence about the beat.

---

## GAP 3 · The expensive certify layer was never available

Lean's enumerative development decides every state in the kernel; a 64×64 grid
world is far past any ceiling. The pagoda development needs a LINE world and an
`lp_potential` certificate; this is a grid world with no state graph.
`certify.expensive` reports `available: false` with the state estimate that
caused it, and the run's `green` flag never goes true.

**Both of the framework's Lean routes are shut on a real ARC level.** This is
the most consequential limit met: `Theoria.md`'s two-layer truth regime — Lean
guarantees truth relative to the manual, probes test the manual against the
world — has only its second layer here.

**What would close it:** an invariant language that reaches beyond a LINE
world's pagoda, or a decomposition that gives Lean a small enough sub-world to
decide. Neither is in scope for a first contact, and both are real work.

---

## GAP 4 · `cegis_miner` contributed nothing, so rule mining was done by the desk

The miner's precondition — exactly one `move` event per transition — is a
substantive claim about a world, and this one does not satisfy it: single
commands change dozens of cells and return up to nine frames. Zero
`rule_hypothesis` rows were produced.

**The engine that generates the hypothesis frontier therefore did not run**, so
the probe frontier is built by ablating the desk's own manual
(`inner/probe.py`) rather than from mined alternatives. That is a legitimate
frontier and it is exact, but it can only contain hypotheses the desk already
thought of — which is precisely the weakness the miner exists to remove
(`Theoria.md` 1.10(b): "交出全体一致假设的前沿，不交点猜测").

Recorded, not worked around: reshaping the input until the miner answered would
have made it answer a question it was not asked.

---

## GAP 5 · Level progress: none

`levels_completed` stayed 0. Expected and stated in advance by the prompt
("不追求赢"), and consistent with the other arm: `bare_cc` has spent hundreds of
actions on this game across eleven episodes without clearing a level either.
No claim about capability is made from this run in either direction.

---

## GAP 6 · Determinism holds for everything except the desk

Engine dispatch, all four generators and the planner are deterministic and
byte-stable. `claude -p` exposes no sampling seed, so the desk's text is not
reproducible. The manifest records `seed: null` with that reason rather than
inventing one, and every prompt and reply is archived verbatim as the
substitute — the same trade `LEDGER_FORMAT.md` §4 makes for model calls
generally ("model calls are not replayable, so the full text is the
substitute").

---

## GAP 7 · Numbers this run cannot claim

* **HTTP amplification and wall clock are confounded** by a concurrent
  `baseline-arms` campaign on the same game (`INC-TA-001`). They are upper
  bounds on this arm's cost, not measurements of it.
* **The score reconciliation was not performed**, because the API returns no
  score to reconcile (`INC-TA-002`). `levels_completed` and the action count
  were reconciled instead.
* **Constraint 9 was checked by sampling**, over the states the run visited,
  not proved over all states. The report says `scope: sampled`.
* **The cache-read column of `Theoria.md` 1.12 is not measurable from this
  arm.** Every `claude -p` call is a fresh process, so cache reads are zero by
  construction of the transport, not by any property of the framework
  (`INC-TA-005`). What the run reports instead is input tokens re-sent per
  turn, which is what cache reads are the price of and which does not depend on
  the transport.
* **`zero_space`'s laws are correlations, not conservation laws**, at this
  evidence volume, and the arm says so in `evidence_adequacy.verdict` rather
  than passing them on at face value.

---

## Not a gap, but worth stating: the cost of first contact

Two live runs were aborted on defects in **this arm**, not in the world, at 11
actions and $2.05: a level generator that never placed the landmarks the
grammar card invited, and a desk that had tools and spent its only turn writing
its answer to a file. Neither was caught by four offline proof runs, 46 tests
and two mock dry runs — the first because the offline worlds are too small to
need a landmark, the second because the dry runs used a cheaper model than the
live run and that model answered in text.

The full account is in `INCIDENTS.md` INC-TA-004 and in the two
`runs/*-aborted/ABORTED.md` files, which are kept rather than deleted.

---

# GAPS — E3's contract, line by line

> E3 · 引擎在线供货：Theoria 臂第二局
>
> P-8 已交付首个在线对局（g50t）。第二局要证的是不同的东西：**引擎在线供货链路稳定
> + 跨关迁移在真 API 上成立**。选 sk48 或 tn36（预检 PASS），携第一局的两本书进场，
> 度量 theorize 轮数、意外七种计数、逐回合成本曲线（C2 账单形状的真数据）。动作预算
> ≤120，先算后花；账本经 proxy，用共享花费闸门（S3 落地后必须用）。

| clause | status |
|---|---|
| a second online game, sk48 or tn36 | **done** — sk48; tn36 is unplayable by this arm and the reason is mechanical (D-E3-009) |
| carry the first game's two books in | **done** — and one defect found doing it (INC-TA-007) |
| engine supply chain holds up online | **done**, with a finding that matters more than the pass |
| **cross-game transfer holds on the real API** | **GAP — the strongest claim E3 asked for is not established.** See GAP E3-1 |
| theorize rounds measured | **done** |
| the seven surprises counted | **done** |
| per-turn cost curve, real C2 data | **done**, and it refutes the projection it was measured against |
| action budget ≤ 120 | **done** — never approached; cost binds first, by design and by measurement |
| compute before spending | **done** — `BUDGET_PLAN.json` predates the first action |
| ledger through the proxy | **done** for the environment side; the model side carries P-8's standing gap, plus a new one (INC-TA-006) |
| **use the shared spend gate** | **GAP — the gate does not exist.** See GAP E3-2 |

---

## GAP E3-1 · Cross-game transfer is *not* established, and this run could not have established it

This is the headline clause and it is not delivered. The mechanism was built and
ran; the claim was not tested.

**What was delivered.** A manual written for g50t was carried into sk48,
compiled against sk48's *computed* level, and certified over sk48's frames
before any model call. That machinery works, costs nothing, and is what a
transfer experiment needs.

**Why it tested nothing.** The carried manual's generated `ACTIONS` is
`[('key', 5)]` and all three of its rules open with
`if action != ('key', 5): return False`. sk48's `available_actions` is
`[1, 2, 3, 4, 6, 7]` — **there is no ACTION5**. So every rule was unreachable,
`step` was the identity for every action this arm can send, and the replay
result was evidence about that mismatch rather than about the manual's content.
A manual whose action vocabulary does not intersect the new game's cannot be
tested on it.

**A second reason, independent of the first.** The cold certify's headline
number was read as a test of the manual's render-accounting formula. It is not
one: `cells_unexplained` is identically `D0 − covered_by_objects` given how
`problem_from_frames` builds the board and how the generated `render` paints, so
the prediction error is identically `K − covered_by_objects` and D0 cancels. The
formula's own qualifier — already written in the carried manual one theorem
below it — predicts the observed 72 exactly. Full account: `DECISIONS.md`
D-E3-012, and the superseded reading is kept verbatim in the run's
`RUN_STATE.md`.

**What was done about it.** `transfer.action_overlap` now computes the
intersection at the cold beat, for free, and the cold report leads with
`carried_theory_is_testable_on_this_game`. This does not turn the gap into a
pass — it makes the next carry able to see the gap before it spends anything.

**What would close it.** A carry between two games whose action vocabularies
overlap, so the carried rules can fire and be confirmed or refuted. Nothing in
the pile cut prevents that; it simply was not true of g50t → sk48, and nothing
checked before the run.

## GAP E3-2 · The shared spend gate does not exist, so this run could not use it

E3 requires `proxy/spend_gate.py` "once S3 has landed". It has not:
the file does not exist on this commit and `agent/s3-spend-gate` carries nothing
matching `*spend*` under `proxy/`. `armtools/spend_check.gate_status()` looks
for it every run, would load and `reserve()` against it if present, and records
`absent` with no reservation held otherwise — never as a pass, and a test pins
that.

So this run budgeted against its own arithmetic and **could not see what a
concurrent session was spending against the same Anthropic bill.** One half of
S3's stated premise has since been refuted by browser-ops — ARC has no quota at
all, a key's only permission dimension is the game set — so the contention that
remains is the model bill, which is the whole of E3's $18.

> **Closed 2026-07-31, when this work was ported onto master.** The gate exists.
> `proxy/spend_gate.py` and `theoria-arm/harness/spend.py` landed with
> A3-campaign-devpile: every desk call now brackets itself with a reservation on
> the shared pool, and `ModelDesk.binding()` **raises** `NoSpendBinding` rather
> than permitting an ungated call, so an unbracketed desk call is no longer a
> degraded mode of this arm — it is impossible. INC-BA-003 is the incident that
> made the case: the single live g50t run spent $6.317658 while the pool's
> report showed this arm's campaigns at $0.00, which is the sentence above
> measured rather than predicted.
>
> The gap paragraph is **kept, not rewritten**. E3's two paid legs really did
> spend ~$8.40 outside any pool's sight, and this is the only place in the
> repository that says so. What changed is the code, not what happened.

## GAP E3-3 · The bill's basis was wrong by 2.1×, and the projection is superseded by its own run

`BUDGET_PLAN.json` projected from P-8's measured $1.2635 per desk call that $18
buys about 14 calls and 29–61 actions. The first live sk48 call cost **$2.695** —
2.1× the basis — because the prompt now carries a 21 KB inherited manual on top
of the frames and the engine report. So $18 buys about 6–7 calls, not 14.

The projection was not wrong to be made; it was made from the only measurement
available and it is what makes the deviation legible. But a carried run's cost
basis is not a cold run's, and the next projection should say so.

## GAP E3-4 · `zero_space` is the arm's wall-clock bottleneck and is slowest when least informative

Not a shortfall against the brief — the brief asked whether the supply chain
holds, and it does — but the number belongs here because it bounds everything
this arm can do next. `zero_space` was 99.9% of a 348-second engine dispatch,
and its cost tracks the **null-space dimension**, which is largest exactly when
the transitions are too few to constrain the features and its own verdict is
THIN. Benchmarks and the live numbers are in the run's `RUN_STATE.md`. It is
engine-rig's territory; this is a report, not a request.

## GAP A3-B-1 · Change B is prepared, not adopted, and nothing live has run under it

`inner/goal.py` ships with the default rung `off`, which writes no key and
changes no decision. Every claim about how `record` and `propose` behave is
made from unit tests, from a `proxy/mock` run that makes no model call, and
from real `plan()` reports over real compiled books — never from a live leg.
Specifically not established:

* that a **live** carried manual, on the `record` rung, would report
  `exploring_no_goal` for a whole leg. The mock cannot show it: offline means
  no desk call, so no compiled manual, so the honest mode is `no_manual`
  throughout. The mode is exercised in unit tests and in the scoreboard
  evidence, not by a loop that played a game.
* that the rider changes anything. Whether a goal request riding on a paid
  theorize call comes back as a goal clause, an argued refusal, or silence is
  the three-way outcome `answer_proposal` records, and no live call has ever
  carried one. The rider's text is written and tested; its effect is unknown.
* that the criterion's constants are right. Four new distinct states and three
  proposals per leg are judgement calls argued from what the two live manuals
  said they were waiting for. Nothing has been run that would calibrate either,
  and a criterion whose thresholds are guessed can be too slow as easily as too
  fast.

## GAP A3-B-2 · Naming the state is not the same as ending it

Change B makes the arm know it is exploring, gives it a criterion for asking,
and makes its record say so. It does **not** make the arm complete a level, and
it does not establish that a goal would be signed if asked. The two live
manuals declined to name one with arguments this ticket found good; the honest
prediction is that a rider might well get a fourth and fifth refusal, and the
record would then carry `declined_with_argument` twice instead of nothing at
all. That is a better record and it is not a level.

## GAP A3-B-3 · `verify_provenance` check 8 is red on any fresh worktree, for a reason unrelated to any of this

Reproduced on a clean, unmodified `master` worktree before change B was
touched: the four legs' `env_proxy.log` was written with CRLF in the main
checkout, `theoria-arm/.gitattributes` pins `* text eol=lf`, so a fresh
worktree normalises the file to LF and the `files[].sha256` recorded in each
manifest no longer matches. 437 bytes and 4 CRLF in the main tree; 433 bytes
and 0 in any worktree. Change B touches none of those files. Filed here rather
than fixed, because the fix is a decision about four archived manifests and
belongs to whoever owns them.

## GAP R2-1 · A leg on the default cannot see its own drift

The measurement that decided R2 -- does the frontier's anchor equal the frame
the world is showing? -- costs nothing: two hashes, no action, no call. But
keeping `--frontier ablation` byte-identical means the anchor block is written
only when the switch is on, so the legs most likely to be drifting are the ones
that cannot report it. Byte-identity was chosen over the diagnostic because a
round measuring an A/B needs the A leg to be the arm it thinks it is. If a
later round decides the diagnostic is worth a byte, this is the trade it is
reversing.

## GAP R2-2 · The unnameable cell can now be predicted and still cannot be written down

`edge_advance` and `world_inert_plus_edge` are the first hypotheses in this arm
that can be right about a board cell. If one of them survives a probe, the arm
has learned something true that **has no home in the DSL**: the manual cannot
state a rule about a cell it has no instance on, and `arc-instances: all`
cannot seat one on a cell the board explains
(`20260731T1430Z-...-r3`'s `i_cannot_manufacture_an_instance_on_a_cell_that_
has_never_changed` rejects the workarounds one at a time). So a confirmed edge
hypothesis is currently a fact the arm can hold but not compile. That is a
grammar change and belongs to `theory-compiler`; it is filed here because R2
made it reachable rather than hypothetical.

## GAP R2-3 · 9 of the 47 are still missed, and 3 of them are the honest kind

Six are opening probes (`P-01`–`P-04` of r2 and r3, steps 6–9): too little
history for an edge chain, and three of them a 71-cell cascade with zero virgin
cells that the transplanted manual delta does not reproduce. Generation needs
evidence; on turn one there is none.

The other three -- `sk48-l1 P-03/P-06/P-09` -- are mid-leg, **correctly
anchored**, 13-cell delta with exactly one virgin cell each, and the edge this
arm extrapolates lands on a *different* board cell than the world burned.
Raising the chain cap catches more of them and costs every other action some
split entropy; four edges is where the replay stops paying for itself. The
residue is real and is not closed here.


## GAP R3-1 · The transport is diagnosed and not repaired

11 archived desk replies begin somewhere other than `=== THEORY ===`, which is
the first thing the theorize contract asks for. `harness/modelcall.py:561`
reads `envelope["result"]` -- the CLI's LAST assistant message -- so a reply
that spans messages arrives with its front torn off. $31.05 of a $108.54
lifetime desk bill, 28.6%; $19.70 of R1b's own $35.14.

`armtools/replyloss.py` **detects** it, over the archive, with a structural
discriminator and negative controls. It does not fix it. The two candidate
fixes -- `--output-format stream-json`, or accumulating messages inside
`_invoke` -- both change what comes back from a live subprocess and neither can
be validated without one. Filed rather than attempted, and the detector is
deliberately in `armtools/` rather than in the live path: a change to
`modelcall.py` that nothing offline can exercise is a change nobody can check.

**Consequence for every A/B this arm has run.** `20260801T001851Z-R1b-sk48-b`
lost 5 of its 6 desk replies. Any knob under test on that leg would have
"failed", and the round record attributes its outcome to `goal_protocol`. No
comparison across R1/R1b legs is safe until this is closed.

## GAP R3-2 · The desk's refusal is a grammar finding this territory cannot act on

`R1b-g50t-a` declined a goal three times, each time with a refutation of all
four forms the goal section admits, each time resting on the same fact: the
cells that name the winning position have never changed, so they are board, so
`arc-instances: all` seats no instance on them, so no `count(<Type>, ...)`
ranges over them and no landmark denotes them.

That is `20260801T0900Z-R2-frontier-by-generation`'s GAP R2-2 arriving from the
other direction -- 12 of 47 off-frontier probes missed by exactly one
never-before-changed cell. Probe expressivity and goal expressivity are one
missing feature seen twice, and it belongs to `theory-compiler`. Nothing in
this territory can close it; the rider's third channel only makes the arm able
to *record* what it cannot compile.

## GAP R3-3 · The third channel is unjudged

`inner/goal.prompt_rider` now offers a third answer. Its reading half is
fixture-tested and its base rate is measured from the archive (the desk
produced the artefact unprompted on 2 of 2 legs that got that far). Whether a
desk given somewhere to put its target uses it is **not** settled and cannot be
settled offline. One carried `g50t-5849a774` leg at leg ceiling $25 -- $17-25,
~9 desk calls, ~25 ARC actions -- would settle it. None was run.
