# DRIFT-the-money-paths-can-go-red-but-nothing-says-at-what-number

severity: medium
dimension: 7（会失败的样本 —— `proxy/DECISIONS.md` D-014 的口径）

**这是欠账交付，不是新发现。** `monitor/audit/state.json` 的 `owed_next_cycle[0]` 是我自己上一周期登记的：「`proxy/cost.py` / `reconcile.py` / `runner.py` 变异测试」。**按「欠账已还」读，不要按新漂移读**——把它当新案报，就是我自己重报自己的债。

---

## evidence

代码钉在 `c54954d6`，副本在 `%TEMP%`，仓库只读。基线 **392 passed**。
配方补正（上一世交下来的那份不完整）：`mkdir -p .git` **不够**——`test_chain.py` 会 shell 出去跑 `git check-ignore`，必须 `git init -q . && git add . && git commit -qm base`。

每个变异体在全套件下复验，**且变异体之间清 `__pycache__`**（见文末方法警告）。

### R5 —— 唯一有牙的一条

`reconcile.py:234` `if not calls and declared in (None, 0):` → `if not calls:`，**存活**（392 passed）。

零条 `model_call` 记录 + `run_end` 声明 4 次，两个方向都复现：

```
原始   verdict: FAIL   cost leg: DISAGREE      declared: 4     on disk: 0
       problems: ['C-2: run_end declares 4 model_call(s) and the ledger holds 0; ...']
变异   verdict: PASS   cost leg: NOT_APPLICABLE  declared: None  on disk: 0
       problems: None
```

现存的负样本 `test_reconcile.py:209` 覆盖的是「2 条记录 vs 声明 7」，即 `calls` **非空**。**空 `calls` + 非零声明，是唯一没被写过的组合**，而 `:234` 恰好在 C-2 检查之前返回。

### C4 —— 不是「没测」，是「容差 1.67 倍且无人声明」

`cost.py:173` `chars / 3.0` → `/ 4.0`，**存活**（392 passed）。

但 `test_spend_gate_egress.py:71-79` **确实在测量级**（`test_the_ceiling_is_pessimistic_about_the_input_side`）。实测它的真实容差边界：

| 除数 | ceiling | real | 测试 |
|---|---|---|---|
| 3.0（树上） | 0.052615 | 0.037500 | pass |
| **4.0（C4）** | 0.043211 | 0.037500 | **pass** |
| 5.0 | 0.037569 | 0.037500 | pass |
| 5.02 | 0.037479 | 0.037500 | **fail** |

**阈值 = 5.0153 字符/token，即 3.0 可以退化到 5.01 而不被发现——1.67 倍的松弛。** 而这个松弛是**意外产生的**：它来自断言两端基准不同（代码 3.0 / 测试硬写 4），外加 1.25 的缓存乘数只加在上限那一端。**没有任何人写下过「1.67 倍容差可以接受」。**

**今天就成立、不是假想的那一半**：`cost.py:173` 用字面量 `3.0` 计算，`cost.py:180` 又把 `"chars_per_token_assumed": 3.0` 作为**第二个各自独立的字面量**上报。改一个，另一个照旧上报——**记录会对自己描述的计算说谎**。

### 可达性（本条的限定，也是它只值 medium 的原因）

* **`reconcile_run` 没有任何生产调用方。** 全部导入点是 `test_e2e.py:17`、`test_reconcile.py:33`、`test_redteam.py:47`，加一个 CLI。`runner.py` **不调它**（`record["reconciliation"]` 来自 `scoring.score_run`，另一个模块）。`proxy/verify.py`（`monitor/gates.py:53` 认定的合并闸门）不跑它。全仓**无任何被跟踪产物含 `reconciliation_key`**——**没有它跑过的痕迹**。
  → R5 的后果收窄成：**一个没有痕迹表明跑过的 CLI，把 FAIL 算成了 PASS。**
* **C4 相反，完全可达且承重**：`model_proxy.py:218` 用上限当放行额度（无上限则 402 `NO_COST_CEILING` 拒绝），`:230-231` 把 `usd=ceiling["usd"]` 交给 `_forward`，`:296-303` 在响应**没有可用 usage 块**时按上限扣池，逐字理由是 *"the response carried no usable usage block, so the call is charged at its pre-flight ceiling"*。**没有第二兜底，不重算，不归零。**

---

## claim

`proxy/` 的钱路径**缺的不是「会失败的样本」，是有量级的失败样本**：对账器的美元额在全部 18 个测试里恒为 **0.0**——`test_reconcile.py:78` 唯一的模型 `mock-model-1` 在 `pricing_v1.json` 里定价 `{"input": 0.0, "output": 0.0}`，于是 `is not None`（`:264`）就是 `usd_total` 受到的最强断言；预检上限唯一的量级断言是一个两端基准不同的单向 `>=`，容差 1.67 倍且无人声明。

前者的后果被可达性挡住（一个没跑过痕迹的 CLI），**后者没有**——上限既是放行额度，又是无 usage 时的扣池金额。

---

## suggest

1. `test_reconcile.py` 加两条：一条 `model_calls=0` + `run_end` 声明非零（R5 的洞）；一条用 `claude-opus-5` 而非 `mock-model-1` 写两次调用，断言 `usd_total` 的**数值**。
2. `cost.py:173` 与 `:180` 的 `3.0` 提成一个模块级常量，让上报的 basis 与计算同源。
3. `test_the_ceiling_is_pessimistic_about_the_input_side` 把容差写成显式断言（如 `ceiling >= real * STATED_MARGIN`），不要靠缓存乘数与基准差意外产生。
4. **不新开板件。** 把 `owed_next_cycle[0]` 里的 `reconcile.py` / `cost.py` 划掉，**`runner.py` 保留**（见下）。

---

## 立案过程留痕：对抗者砍掉了什么

它**独立重跑了五个变异体**（每个之间清 `__pycache__`），五个都确认存活——机械部分不是编的。然后它拆掉了三条框架：

* **「预检上限的量级没测过」——假。** 它测过，只是容差 1.67 倍。**我的 gatherer 把「测得松」写成了「没测」**——这是本轮我最该避免的那种夸大。对抗者还测出了精确阈值 5.0153，这是原稿完全没有的东西。
* **U5 与 U1 是等价变异体。** `usd_cap` 与 `spend_reservation` **没有任何调用方传过**，值域是 `{None}`，`None or caps["usd"]` 与原式逐字节等价。它们是**潜在陷阱，不是缺陷**。（顺带一条 gatherer 没找到的、更有分量的：`arc-recon/canary_schedule.py:300` 真的在 `gate.reserve(campaign, usd_cap=0.0, ...)`——那个「零被当假」的写法在本仓是活的，只是不走这条被变异的线。）
* **U1 根本不是未测不变式。** `test_spend_gate.py:523 test_a_declared_budget_is_not_replaced_by_the_default` 已经逐条钉住了同一个失败态（`spend_reservation_owned is False`、`len(live) == 1`）。`runner.py:75` 是一个被测过两次的写法的第三份拷贝。
* **`runner.py` 没有测试文件 ≠ 没被执行。** `run_game` 由 `test_e2e.py:27/:284`、`test_variant_degeneracy.py:87`、`test_spend_gate_egress.py:178/:226` 驱动，**并且 `proxy/verify.py` 第三级在每次 proxy 合并时真跑一局 mock**。所以 `runner.py` 在合并时会执行，只是从不带那三个参数执行。
* **45% 这个数不该出现。** 排除两个等价变异体后是 **9/18 = 50%**；而且它是自选样本——**先读了测试再挑靶子**，拿它跟上一周期 `spend_gate.py` 的 8/8（另一个自选样本）并列比较是误导。已删。
* **U7（`ledger_head` 硬编码 `"verified"`）的语义半部已登记两次**：`proxy/STATUS.md:112-131` 与 `REDTEAM.md:427-445` 逐字写着「No gate compares a run's head to a tracked manifest… **Do not read the chain's 28 green tests as this line being closed.**」——按我自己的规矩，那是**文档化限制**。只有机械细节是新的：`ledger_head` 不在 `verify.py:85-87` 的 `RUN_REQUIRED` 里，而 D-032a 把 `variant_degeneracy` **特意加了进去**，无人解释这个不对称。**作为一行交叉引用记在这里，不单独立案。**

**支持这条的最强依据是仓库自己写的**：`proxy/DECISIONS.md` D-014（`:153-157`）逐字说 *"The replay and reconciliation tests each have a companion that forges the ledger and asserts the check goes red. **A check that has never been observed to fail is not evidence that anything passed.**"* ——本条报的正是这句话在两处没有兑现。`DECISIONS.md` 里**没有**任何关于 `runner.py` 不单测、reconcile 测试策略、chars/token、或 `mock-model-1` 零定价的豁免条目。

### 一条给继任者的方法警告（对抗者在本会话里被它咬了一次）

**`3.0` → `5.0` 是等长编辑，`cp` 可能落在同一秒的 mtime 上，于是 Python 的 `.pyc` 校验（mtime + size）通过，跑的是陈旧字节码。** 对抗者亲眼看到 `chars_per_token_assumed: 3.0` 由一段正在用 `chars/5.0` 计算的代码印出来。**任何在这棵树上的变异测试都必须在变异体之间清 `__pycache__`。**

**后果是我 gatherer 的另外 15 个变异体判定不可信**——对抗者只复验了 6 个，其余的存活/被杀结论以及「9 killed」这个分子都未经独立验证。**下一世若要用那张表，先重跑。** 本仓已有先例：`proxy/runs/20260729T125103Z-.../mutants.json` 是 `{"verdict": "harness-invalid"}`，控制组死于 `fatal: not a git repository`，M31/M32（runner.py 的两个）**从未被评分**——那正是这份配方警告的同一个坑。

**因此 `owed_next_cycle` 里 `runner.py` 那一项不划掉**：它的两个历史变异体从未被评分，本轮针对它的三个变异体又有两个是等价体。它仍然是未变异的。

对抗者未能验证：其余 15 个变异体；gatherer 的靶子是在读测试之前还是之后选的（这决定 50% 这个数有没有意义）；`python -m proxy.reconcile` 是否曾被人手敲过（能证明无自动调用、无被跟踪产物，不能证明无人手动跑过）；`usd_cap` / `spend_reservation` 是否是留给未来调用方的公开 API——`DECISIONS.md` 两边都没写，**而这决定了该补测还是该删参数**。
