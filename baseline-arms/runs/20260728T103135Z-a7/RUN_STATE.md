# A7 — finishing the variance envelope

Worker `APP-A7` · ticket `A7-envelope-finish` · territory `baseline-arms`
branch `agent/a7-envelope-finish` · base `979e0bc`

The narrative. `MANIFEST.json` is the provenance record and is canonical;
this file is what a person needs in order to read it.

---

## What this run was for

The variance envelope stopped at **1/4 games** (ar25 × haiku × 3, $2.5275),
tripped by G4 and ruled in `BUDGET_REPORT.md` §11 to be a real degradation
under `INCIDENTS.md` INC-BA-003's concurrent-campaign load. §11.5 named two
things that had to be fixed before a re-run. The ticket for this run says the
first is now landed (`proxy/spend_gate.py`) and asks for the remaining three
games — g50t, sk48, tn36 — at three repeats each, followed by the envelope
table and the variance estimate Phase 4 needs to fix its per-cell repeat
count ⟨n⟩.

---

## What had to be built before a single cell could run

Three findings, in the order they were found. Each is a decision record.

### 1. The shared gate was not on this track's spending path at all (D-017)

`proxy/spend_gate.py` had landed, and it is the right instrument — one pool,
one lock, one sum, fail-closed, visible across sessions. But it hangs off **the
proxy's egress path**, and `baseline-arms` uses neither half of it: `bare_cc`
drives `arc_client` straight at `three.arcprize.org`, and the model side is a
`claude -p` subprocess. The pool's own report showed this plainly and nobody
had read it that way:

```
by campaign:
  arc-recon-canary-quick      $0.0000    0 actions
  theoria:r-395ddce163d04d83  $0.0000    7 actions
  ...
```

Every campaign `baseline-arms` had ever run — including the $2.5275 envelope
this ticket is finishing, and the $103 S1 campaign of INC-BA-003 — appears
nowhere. **That is not a small number; it is no number.** The ticket's "every
egress must pass reserve/record" was therefore not a matter of remembering to
call it: there was nothing to call.

So `harness/spend.py` plugs both axes in, and both refusals are functions
rather than paragraphs: `ArcClient.request()` will not open a socket without a
claim, `bare_cc.play()` will not start without one. Charging is per **request**,
not per successful action, so D-005's 5–11× retry amplification is visible to
the pool instead of hidden behind it; and failed requests are charged, because
a 400 crossed the wire and counted against the rate limit.

One reservation **per cell**, not per campaign: the three repeats run
concurrently, and a shared claim would give three threads one set of counters
and leave no cell able to say what it had spent — INC-BA-003's third damage,
one level down.

### 2. The abort rule was not measuring what it claimed (D-016)

`BUDGET_REPORT.md` §11.2 had already done the diagnosis; this run acted on it.
`actions_failed >= 10`, cumulative and absolute, killed all three ar25 cells
with **exactly ten failures each, standard deviation zero**. At a 30-action
budget and ~0.6 action success rate, that verdict was guaranteed by
construction. §7 of the same document had described the rule as "ten
*consecutive* failures" — wrong about the code, and right about what the rule
should be.

Now two rules with two outcome names:

| rule | threshold | outcome | the claim it makes |
|---|---|---|---|
| consecutive | 10 | `api_unusable` | the API is unusable |
| cumulative | `max(10, budget)` | `failure_grind` | this arm fails a lot |

**§11.3 forbids exactly one move here** — raising a threshold so the gate goes
green — and the test it set is whether a real signal is silenced. Point by
point: the degradation those cells genuinely measured (success 0.595,
http/action 9.66, $/action +68%) is measured by **G5, G3 and G2**, and all
three are untouched and still armed. What was removed is an absolute constant
that did not scale with the quantity it judged. What was **added** is a
constraint that did not previously exist — a cumulative counter is never reset
by a success, so nothing had ever been watching whether failures came in a run.
`failure_grind` is deliberately not a dead outcome: a cell that spends its
budget and fails a lot is a *result*, and filing it as an API fault would put a
measurement into G4's streak and stop the campaign for having measured
something.

### 3. A gate that can only stop once cannot be re-adjudicated (D-018)

G4 was still red, and would have stayed red for ever: the gate had no way to
record that an adjudication had happened, so §11.5's "re-runs just append and
`--gate-only` can re-adjudicate at any time" was not reachable.
`out/campaign_barriers.jsonl` is that record. **BAR-001** adjudicates the three
ar25 cells and names its three remediations.

The scope rule is stated once rather than discovered one gate at a time. The
eight thresholds are two kinds:

* **condition clocks** — G4 (consecutive dead cells) and G6a (real time since
  the first cell started). Both claim something about *now*. A barrier restarts
  both, because a campaign that ran 24 minutes, stopped on a correct refusal,
  was diagnosed, and resumed sixteen hours later has neither a live failure
  streak nor a day of running behind it; it has a **gap**, and counting the gap
  is the same unit error that split G6 into two clocks in the first place.
* **cumulative sums** — G1, G1b, G2, G3, G5, G6b, G7. Every one keeps summing
  every cell ever recorded. The $2.5275 is not forgiven and never will be.

The load-bearing test is the negative one: `test_a_barrier_moves_g4_and_nothing_else`
asserts the dollar total is **unchanged** across the barrier. A test that only
checked "the gate goes green" would pass for the forbidden change too.

**BAR-001 explicitly does not**: re-run the ar25 cells, delete them,
reclassify them, or move any threshold in order to make them pass. Their
`degraded` standing is unchanged and they are excluded from the envelope by
name, with the reason printed next to the table.

### One incidental fix

`load_api_key()` looked for `.env` only in the importing checkout, while
CLAUDE.md instructs every agent to work in `.worktrees/<id>/` — where the file
does not exist, because it is gitignored and does not travel with a branch. A
worktree now falls back to the main checkout, the same resolution
`spend_gate.py` already uses for the pool ledger. The key is still read only
from a gitignored file and is still not copied anywhere.

---

## The smoke test, and what it found

$0.05 of insurance before twelve cells went through new wiring
(`smoke.py`, one action on g50t). It verified the gate end to end — the pool
went 48 → 51 actions, with a ledger line per request carrying path, status and
reservation id — and it **failed its own final assertion**, correctly:

```
"error": "You've hit your session limit · resets 8:20pm (Asia/Shanghai)"
"outcome": "model_error",  "model_calls": 3,  "cost_usd": 0.0
```

Two things came out of that:

1. **The assertion was wrong, not the code.** It demanded `after.usd >
   before.usd`. All three model retries were refused and billed nothing, and a
   refused call that cost nothing is a *priced* call worth zero — which is what
   the gate recorded, exactly as `spend_gate`'s own docstring says it should
   ("a model legitimately priced at $0.00 with a complete usage block is
   priced, not blind"). The assertion now checks that the pool and the episode
   *agree*, and that no call went unpriced.
2. **The arm's model side was unavailable.** Not a budget gate and not an API
   fault: the 5-hour session window, which `SPEND_GATE.md` §5 lists explicitly
   as a resource the shared pool does not watch. Nothing could be measured
   until it reset, so `await_quota.py` waited for it — itself gated, because a
   probe is a real `claude -p` call and this ticket's rule has no exceptions.

---

## Cells

Nine, all three games, three repeats each. Budget 30 actions, haiku-4.5,
cookie jar on. Every cell audited before the next game started.

| game | rep | outcome | ok | fail | longest run | http/a | $ | wall s |
|---|---|---|---|---|---|---|---|---|
| g50t | 1 | budget_exhausted | 30 | 0 | 0 | 1.00 | 1.1468 | 1038 |
| g50t | 2 | budget_exhausted | 30 | 0 | 0 | 1.00 | 1.0675 | 848 |
| g50t | 3 | budget_exhausted | 30 | 0 | 0 | 1.00 | 1.1277 | 991 |
| sk48 | 1 | budget_exhausted | 26 | 4 | 2 | 2.50 | 1.3138 | 1412 |
| sk48 | 2 | budget_exhausted | 28 | 2 | 1 | 1.61 | 1.3441 | 1396 |
| sk48 | 3 | budget_exhausted | 27 | 3 | 2 | 1.93 | 1.3897 | 1513 |
| tn36 | 1 | gave_up | 23 | 5 | 2 | 3.35 | 1.0127 | 1001 |
| tn36 | 2 | gave_up | 24 | 5 | 2 | 2.96 | 1.0948 | 1109 |
| tn36 | 3 | budget_exhausted | 24 | 6 | 2 | 3.21 | 1.0393 | 1026 |

**Nine live cells, zero dead.** `levels_completed` is 0 in all nine, as it was
in all twelve pilot cells — 30 actions is not enough to finish a level in any
of these games, and that fact is the single most important thing in this report
(see ⟨n⟩ below).

Totals for this run: **$10.5364 · 242 ok / 25 failed · 477 gameplay HTTP ·
2.87 compute-hours · 504 pool actions.**

### The audits

Two per game, both required to pass before the next game started, plus one
independent adversarial review of g50t.

* `audit_cells` — cell summary vs harness ledger vs API scorecard, plus a
  sealed-pile sweep over every record. **9/9 clean**, sealed check PASS across
  1111 records. All nine scorecards reconcile as *successful actions only*,
  which raises BUDGET_REPORT §4.1's sample for that finding from 4 to 13.
* `audit_pool` — the new one (D-017 created the obligation). **9/9 clean.**
  The pool's $10.5364 equals the cells' $10.5364 exactly, and the action
  identity closes on every cell.

Both audits found real defects, which is the only reason to run them:

1. **`audit_pool --game` filtered the record, not the view.** Auditing sk48
   reported g50t's three reservations as ORPHAN — "unattributable spend", the
   most serious verdict the tool has — because `--game` had removed their cells
   from the comparison. Attribution is a property of the whole campaign or it is
   nothing. `--game` is now a focus on what is printed; the count of what was
   hidden travels with the verdict.
2. **`audit_cells` read a model's decision as a server's refusal.** The two
   `gave_up` tn36 cells reported "actions_failed: summary 5, ledger 6". The
   summary was right. A GIVE UP is written `failed=True` with a null frame
   because it produced no frame (D-006) — but it never reached the server, so it
   is not what `actions_failed` counts and it says nothing about the API. Same
   distinction D-016 drew between `api_unusable` and `failure_grind`, one level
   down. Fixed at read time (the ledger is append-only and the evidence — an
   absent `http_status` — was already in the record), and new records now state
   `reached_api` outright so no future reader has to infer it.
3. **The adversarial review of g50t found D-019**, below, which is the largest
   finding of the run.

---

## The result: within-cell spread is small, and between-game spread is not

Pooled within-cell coefficient of variation, 3 games × 3 repeats, 6 df:

| metric | CV | n for ±10% CI | n for ±20% CI | n to detect 25% | n to detect 50% |
|---|---|---|---|---|---|
| action_success_rate | 0.018 | 3 | 2 | 3 | 3 |
| actions_ok | 0.021 | 3 | 2 | 3 | 3 |
| usd_per_action | 0.033 | 3 | 3 | 3 | 3 |
| cost_usd | 0.035 | 3 | 3 | 3 | 3 |
| wall_seconds | 0.067 | 5 | 3 | 4 | 3 |
| http_per_action | 0.096 | 7 | 4 | 5 | 3 |
| **levels_completed** | **—** | **—** | **—** | **—** | **—** |

**⟨n⟩ = 3 for the economic metrics, 5–7 if `http_per_action` has to be pinned
down.** The two-sample columns are the ones Phase 4 actually needs — the
envelope is not bought so a bare-CC mean can be quoted, but so a bare-CC cell
and a Theoria cell can be told apart — and they say **n = 3 per arm** detects a
25% difference in cost or success rate at 80% power.

Three things that must travel with that number or it will be misused:

1. **`levels_completed` has no CV, and that is not a formality.** It is
   identically zero in all nine cells and was zero in all twelve pilot cells. It
   is the metric Phase 4 would most want to compare, and at a 30-action budget
   **no repeat count whatsoever makes it comparable** — n does not fix a metric
   with no signal. If Phase 4 intends to compare capability rather than
   economics, it needs a larger action budget first, and this envelope says
   nothing about the variance it would then have.
2. **Between-game spread dwarfs within-cell spread.** actions_ok runs 30 / 27 /
   23.7 across the three games and http_per_action runs 1.00 / 2.01 / 3.17 —
   between-game ratios of 3× against within-cell CVs under 0.10. Repeats are
   cheap insurance; **game coverage is where the uncertainty actually lives.**
   Three repeats on four games is a better buy than nine on two.
3. **Six degrees of freedom.** A CV from three samples is a noisy estimate of a
   CV, and these are pooled from three of them. The n values are the right order
   of magnitude, not three significant figures.

---

## Stop conditions and what actually happened

**Nothing tripped. The campaign ran to completion and stopped because it was
finished.**

| gate | limit | final | |
|---|---|---|---|
| G1 campaign cost | $50.00 | **$13.0639** | 26% |
| G1b haiku tier | $20.00 | $13.0639 | 65% |
| G2 cell cost | $3.078 | max $1.3897 | 45% |
| G3 http/action | 20.0 | 3.15 | |
| G4 consecutive dead | 2 | **0** | nine live cells |
| G5 action success | ≥ 0.35 | 0.839 | |
| G6a elapsed | 8 h | 1.2 h | |
| G6b compute | 20 h | 3.8 h | |
| G7 sealed contact | any | **none** | 1111 records swept |

Shared pool after the run: **$10.5564 of $214.90, 587 of 24,000 actions**, no
live reservations. The theoria arm was drawing on the same pool throughout and
is visible in the same report — which is the whole of what INC-BA-003 could not
do.

The one thing that did stop this run was not a gate: the `claude -p` **session
window**, which cost 105 minutes between the smoke test and the first cell. It
is not in the pool and cannot be, and `SPEND_GATE.md` §5 already says so. If a
future campaign is scheduled rather than run by hand, that window is the
constraint to schedule around.

---

## D-019 — the finding that changes numbers outside this run

The adversarial review was asked to falsify "30 successful actions, 0 failed",
a result too good against ar25's 0.595. It found no mechanism for silently
dropping failures — `resilient()`, the action loop and `request()` all account
honestly, and 99 of 99 g50t HTTP calls really did return 200. It found the
cause instead:

| transport | calls | 200 | 400 | 404 | 500 | error |
|---|---|---|---|---|---|---|
| jar **off** — M4 pilot + ar25, all history | 1922 | 249 | 1315 | 147 | 208 | 3 |
| jar **on** — this campaign | 99 (g50t) | 99 | 0 | 0 | 0 | 0 |

`arc_client.py` stated that `cookies=False` was kept precisely so
BUDGET_REPORT's figures would stay re-derivable. The constructor had defaulted
to `cookies=True` since the jar landed six hours before these cells ran, and no
caller but `transport_ab` overrode it. **The campaign changed transport
mid-flight and the docstring asserted it had not.** Nothing in the harness
would have caught this; only an audit told to disbelieve a good result did.

Consequences, kept apart rather than blended:

* **ar25 vs the rest is separated by two variables, not one** — contention *and*
  transport. They are not separable. This strengthens the exclusion of ar25
  rather than weakening it.
* **The envelope is unaffected.** All nine cells share the jar, and the question
  is within-cell spread.
* **BUDGET_REPORT §2.1 and every extrapolation on it are stale.**
  `http_per_action` is 1.00–3.17 on the jar, against a pilot figure of 7.11. The
  §3 HTTP and action-quota numbers (87k–175k requests) are high by roughly 2–7×.
  Dollars do not move with it — model pricing is transport-independent. Logged
  here; re-deriving §3 is not this ticket's call.

---

# 收工后追加的工作（工单之外，人工直接指示）

工单 A7 到「包络跑完 + ⟨n⟩」为止就交付了，工作板也已 `done`。
以下四件事是之后由人工逐条指示的，**不在工单范围内**，记在同一个 run 目录里
是因为它们全部由 D-019 引出、共用同一批账本与同一个共享池。

## 1. §2.1 单价重测（$19.83）

D-019 说 §2.1 描述的是一个已不存在的传输层。重测三档。

**重测没有重买**：便宜档的 jar-on 一行本来就已付过钱——包络九格同预算、同局、
jar 开——所以只买了真正没测过的 opus 与 sonnet 各三格。事前估 $20.28，
实花 **$19.83**。

新表（`harness/unit_prices.py`，比较范围限定在两种传输层都跑过的三局）：

| 档位 | $/成功动作 | $/模型调用 | HTTP/动作 | 墙钟 s/动作 | 成功率 |
|---|---|---|---|---|---|
| haiku-4.5 | $0.0435 | $0.0392 | 1.97 | 42.7 | 0.906 |
| opus-5 | $0.1460 | $0.1168 | 3.11 | **19.8** | 0.800 |
| sonnet-5 | $0.1793 | $0.1143 | 4.46 | 55.3 | 0.722 |

**限定范围不是小事**：不限定的话，「HTTP/动作 从 7.11 掉到 1.97」里会混进
「两边平均的是不同的局」——而该指标的局间散布是 3 倍，比被声称的效应还大。

## 2. §3 外推与 §6 建议重算

§3 新增 §3.5（S1 / S2 / 单档 / 双档），§0、§4、§4.1 同步。
**S1 三档 $1,111.56 · 28,754 HTTP · 24.7 h 四路**。对照旧版：
**钱 +6%、HTTP −67%、墙钟 −45%**。

§6 五条：**两条撤销、两条保留（一条换理由一条换数字）、一条不变、新增一条**。
两条撤销的要点名：

* **「先问清 ARC 配额口径」不再是阻塞项**——样本 19，悲观上界降到 28,754。
* **「墙钟别低估，四路也要 45 小时」说反了**——实测 24.7 h，且
  **opus 现在是最快的一档**（16.6 h 独跑 vs haiku 35.7 h），旧表里两者相当。
  **若约束是时间不是钱，该选 opus**，与旧建议相反。

§6 建议 2（砍 sonnet）**保留但理由变了**：原因是「3/4 格 `model_error`」，
那个故障**没有复现**（三格全部跑完）；新依据是它比 opus 贵 23%、慢 2.8 倍、
成功率更低。**理由换了而结论没换，必须说明白**，否则下一个读者会以为旧理由
被证实了。

## 3. `$/调用` 悬项：复测并查清（$1.36）

这是我自己写进 §6 的建议 6，人工要求执行。**开跑前先把三个判据写死**，
免得事后挑一个顺眼的解释：涨幅仍在 = 落在 [0.0330, 0.0413]；回落 = 接近 0.0225；
含混 = 约 0.0298。

**实测 0.0453——落在预设三个分支之外，在高的那一侧**，比包络均值高 6 个标准差。
**这一条照实登记：我预设的分支集合不完备，漏了「还在继续涨」。**

成因查清（§14.2），四条证据合起来只剩一个解释：

1. 对 17 个 haiku 格最小二乘反解每 token 单价，**输出 = $5.00/Mtok，R²=0.99998**
   ——公开价。**计价没动过。**
2. 本 harness 送出的 prompt **没变大**（`prompt_chars` +1.9%）。
3. 计费的 cache-write/调用三档全涨：haiku +27%、opus +52%、sonnet +105%。
4. 5,500 字符约 1,500 token，而 cache-write 一万以上——**差额不可能来自我们**。

结论：**是 `claude -p` 自己的系统提示与工具定义变大了**。
**限度写明**：看不到 CLI 的前缀本身，这是排除法推断，不是直接观测。

**方向要说反过来**：§3.5 的钱数是**下界**，不是高估。批预算按 **+15–20%** 留余量。
我最初把建议 6 写成「可能是系统性高估」，那是写反了。

## 4. 三个工具在被信任之前先被证伪

`audit_pool` 与 `audit_cells` 在这段工作里各自被自己抓到一次缺陷，
两次都是「误报最严重的那句话」，也就是最容易让人从此不再读审计的那一类：

* `audit_pool --game` 先是**过滤了记录而不只是视图**，把 g50t 的三个 reservation
  报成 ORPHAN（「无法归属的花费」）；修完又**过度矫正**成读取全部战役的格，
  于是审计一场战役时拿另一场的格去比这一场的池，报出九条幻影问题。
  最终口径：**归属以战役为单位**，`--game` 只收窄打印。
* `audit_cells` 把模型的「放弃」读成服务器的「拒绝」，在两个 `gave_up` 格上
  报「summary 5, ledger 6」。**summary 是对的。** 修在读取端
  （账本 append-only，且判据——没有 `http_status`——本来就在记录里）。
* `summarise_envelope` 的 `n_for_precision` 定点迭代**不收敛**，会返回一个
  比自己的不等式差四倍的 n。测试先抓到，改成上行搜索并校验它报告的条件。

三处都补了回归测试，且**先确认负面对照真的会失败**，再确认修复挡住它。

---

## 收工时的状态

* **测试 80 passed。**
* **账本三场战役各自对齐**：`audit_pool` 包络 12 格 / 重测 6 格 / 复测 1 格，
  全部 clean；`audit_cells` **19/19 clean**，封存堆检查 PASS（1449+ 条记录）。
* **共享池 $41.57 / $214.90**，无存活 reservation，三场战役分账可见。
* **封存堆零接触**，密钥零泄漏（对抗性审计单独查过）。
* 分支 `agent/a7-envelope-finish` 已推送；工作板 `A7-envelope-finish` 已 `done`。

**留给下一个人的三件事**（都已登记，都不由本工单裁决）：

1. `$/调用` 的上涨对**任何走 `claude -p` 的臂**都成立，Theoria 臂的成本口径
   要按上调后重算。三臂对比不受偏袒。
2. **27 格 `levels_completed` 全为 0。** S1 的前提「给够动作就能打完 30 关」
   没有任何一格支持。§3.5 两个情景都是成本下界，不是能力预测。
3. ⟨n⟩ = 3 只对经济类指标成立。**若 Phase 4 要比能力，先加动作预算**，
   本包络对那时的方差一无所知。
