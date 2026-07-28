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
