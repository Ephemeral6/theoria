# DRIFT-two-live-spend-ceilings-that-no-test-asserts

severity: medium
dimension: 7 (不可能变红的检查) + 5 (流程漂移)
status: **未经对抗复核——这是本文件与本周期其余五份的区别，必须写在最前面。**
它是 `owed_next_cycle[0]` 连续第四个周期的欠账，结果在我这一轮收工前才回来，
来不及派 refuter。**M5／M8／M9 三条在被 refuter 推过之前不作数**，
已写进 `state.json` 的 owed 清单要求下一轮先做这件事。
本文件先落盘，因为「只存在于上下文里的信息视同不存在」。

## claim

`proxy/runner.py` 的变异得分是 **5 killed / 12 scored = 42%**，
而比这个数更值得看的是它的**形状**：

**全部五次击杀都来自同一个文件里的同两条测试。删掉那一个文件，得分就是 1/12。**

并且有两条存活的变异体动的是**每一个调用者都会走**的默认花钱上限，
而它们的值**没有任何测试断言过**。

## evidence

### 1. 谐架与控制（先说这个，因为上一次这条欠账就是死在控制上）

```bash
git archive 794e5b46 proxy arc-recon/data | tar -x -C "$TEMP/mut"
cd "$TEMP/mut" && git init -q . \
  && git config user.email mut@local && git config user.name mut \
  && git add . && git commit -qm base
```

**那两行 `git config` 是对既有配方的必要补充**，交接件里没有：
没有本地身份，`git commit` 会以 `Author identity unknown` 失败，整棵树留在未提交状态，
**这是通向 `harness-invalid` 的第二条路**（V22 那次死在 `fatal: not a git repository`，是第一条）。
加上之后 `git check-ignore -q proxy/var/runs/probe.json` 返回 0，
`test_chain.py::test_the_runners_default_head_location_is_gitignored` 有真仓库可用。

**控制通过：392 passed in 74.59s。**

每个变异体的流程：还原原始 → 打补丁（单次出现的精确串替换，锚点不唯一即中止）→
`find . -name __pycache__ -prune -exec rm -rf`（**全树**）→
**活性断言**（另起 subprocess 从 pytest 用的同一 cwd import `proxy.runner`，
断言被改的子串在 `inspect.getsource` 里，并打印 `__file__`；
**每个变异体都报了 `LIVE` 且路径是临时目录**）→ 全量 392 条。
真仓库确认未动（`git status --porcelain -- proxy arc-recon` 为空）。

### 2. 结果

| # | 被改的决策 | 判定 |
|---|---|---|
| M1 | 清理快照过滤 `in before` → `not in before` | KILLED |
| M2 | 归属过滤 `!= run_id` → `== run_id` | KILLED |
| M3 | 删掉 `kwargs["run_id"] = run_id` | KILLED |
| M4 | 清理守卫 `declared is None` → `is not None` | KILLED |
| M7 | `reservation_owned = reservation is None` → `is not None` | KILLED（5 failed + 27 errors）|
| **M5** | 清理释放里删掉 `expect_holder={"run_id": run_id}` | **SURVIVED** |
| **M8** | 默认 USD 运行上限 ×10（$5 → $50） | **SURVIVED** |
| **M9** | 默认动作运行上限 ×10（600 → 6000） | **SURVIVED** |
| **M10** | `require_keys: bool = True` → `False` | **SURVIVED** |
| **M11** | `main()` 的 `if not args.game` 拒绝被移除 | **SURVIVED** |
| **M12** | `record["unknown_ledger_fields"] = dict(...)` → `= {}` | **SURVIVED** |
| **M14** | `"verdict": chain["verdict"]` → 硬编码 `"PASS"` | **SURVIVED** |
| M6 | 顺利路径释放 `if reservation_owned` → `if not ...` | SURVIVED（**扣除**）|
| M13 | `gate = spend_gate if ... else default_gate()` → 恒 `default_gate()` | SURVIVED（**扣除**）|
| E1 | `"undeclared": ... and ...` → `or` | SURVIVED（**事前排除**）|

### 3. 扣除，逐条给理由（上一周期就是在这里栽的）

- **E1 —— 等价，跑之前就排除出分母。** 全树在 `794e5b46` 上核对：
  **没有任何调用者传 `usd_cap` 或 `action_cap`**（唯一的调用点是 5 个测试、
  `verify.py` ×2、`main()` ×2、一个归档证据脚本，没有一个传这两个参数）。
  两者恒为 `None`，故 `and` 与 `or` 返回同一个值。
  **这就是上一周期那条 `usd_cap`/`spend_reservation` 发现，本轮再次确认，且这次不计分。**
- **M6 —— 在钱的方向上等价，扣除。是量出来的不是假设的**：M6 下一次跑完的 mock run
  留下 `held_usd=0, free_usd=10.0, live=0`——与原始完全相同，
  `run_game` 自己的 `finally` 回收了同一笔 claim。
  唯一残留差别是 gate 账本的 `reason` 字段（原始写 `run r-… finished`，
  M6 写 `run ended without releasing its claim`），
  而唯一碰这个字段的测试是 `test_spend_gate.py:484 assert after[-1]["reason"]`——
  **只断言真值，不断言内容**。所以 `runner.py:146-148` 买不到任何可观测的东西，
  **也没有任何测试能区分「干净释放」与「崩溃释放」。**
- **M13 —— 死分支，扣除。** `spend_gate is not None` 那条臂没有任何调用者会执行：
  两个传 `spend_gate=` 的测试把 `_run_game` monkeypatch 掉了，
  `verify.py` 走 `set_default_gate()` 而不是这个参数，
  而 `theoria-arm/DECISIONS.md` D-P8-001 记着那唯一的真 arm **刻意完全不调用 `proxy.runner`**。

**得分：5 / 12 = 42%。** 它量的是什么，说清楚：
十二次决策翻转，是我**读完测试之后**挑的、偏向钱与拒绝方向，五次变红。
**这既量测试的覆盖，也量我的准头，所以不得与上一周期 `cost.py`／`reconcile.py` 的数字相比**
——选法不同、分母约定不同。（上一周期正是这个比较被 refuter 删掉的。）

### 4. 真正的发现是形状，不是那个百分数

**五次击杀全部来自 `test_spend_gate_egress.py` 里的同两条 S29 回归测试。**
（M7 之所以死，只是因为 `None.reservation_id` 抛异常——那是崩溃，不是检查。）
**删掉那一个文件，`runner.py` 钱方向的故障检出能力就只剩 1/12。**

### 5. 活钱路径上的存活者

**M5 —— 活钱路径，真存活，非等价已被构造出的输入证明。**
拒绝行在 `spend_gate.py:846-857`：
`if expect_holder: … raise NoReservation("refusing to release a claim this caller does not hold")`。
该块可达且**确实被执行**（M1–M4 全死在它里面）。
消费者：`gate.release(...)` → **REFUSE**。
区分输入（`$TEMP/m5_probe.py`）：让快照的持有者视图与磁盘上的持有者不一致——
这正是「在池锁**之外**做快照、而 `release` 在锁**之内**重读」的读者眼中一次并发账本写入的样子。
原始：另一个会话的 claim 存活，`held_usd=3.0`；M5：被释放，`held_usd=0`。
`test_release_refuses_a_claim_the_caller_does_not_hold` 直接测那个机制，
所以缺口很窄很具体：**没有任何东西测「runner 确实把它传了进去」。**

**M8／M9 —— 活钱路径，无人断言。** 它们改的是 `else` 臂，
**100% 的调用者都走它**，在 392 条里每一条会玩游戏的测试里都被执行——
与 E1 的死臂**范畴不同**。消费链：
`gate.reserve(usd_cap, action_cap)` → **REFUSE**（`spend_gate.py:733` 池上限检查）
→ `Reservation.usd_cap/action_cap` → `env_proxy.py:309` / `model_proxy.py:357` `gate.permit(...)`
→ `SpendPermit.check()` → `SpendGate.check()` → **REFUSE** 于
`entry["usd"] + usd > entry["usd_cap"]`（`spend_gate.py:955`）与动作孪生条件，
**就在 `forward()` 打开套接字之前**。
所以这两个变异体挪动的是一条**有真拒绝在读**的活天花板。
实测原始 reserve 记录：`usd_cap=5.0, action_cap=600`。
**pytest 里没有任何东西断言过其中任何一个**：`record["spend"]` 由 runner 写、
在整个测试套件里**无人读取**，而 `verify.py:422` 只检查 `"spend"` 这个键**存在**，从不看值。
**两个变异体，一个洞：对 reserve 记录加一条断言就同时补上。**

**M10 —— 只在生产（CLI 真 API 分支）活，而那个默认值零覆盖。**
拒绝：`env_proxy.py:80` / `model_proxy.py:75` 的 `load_key(…, required=require_key)`，缺密钥即抛。
消费者：**每一个测试与 `verify.py` 的两级都显式传 `require_keys=False`**，
所以 `True` 这个默认被 **0** 条测试走过。
它唯一的消费者是 `runner.main()` 的非 `--mock` 分支，而那里不传这个参数——
**即：那条唯一会碰真 API 的路径所依赖的 fail-closed 默认值，正是没有覆盖的那一个。**

**M11 —— 只在 CLI，零覆盖。** `runner.main()` 在全仓除了自己的 `__main__` 守卫外无人调用；
`verify.py:34-35` 明文说它**不**跑 `runner.main`。`main()` 完全没有测试覆盖。
被移除的那条拒绝守的是一次真网络调用：M11 之下一句裸的
`python -m proxy.runner` 会把 `game_id=None` 发往 `UPSTREAM_ARC`。

**M12 —— 「覆盖得松」不是「没覆盖」，这条必须说准**（这正是上一周期被点名的过度陈述）：
计数机制本身在下一层有真实的非空覆盖——
`test_canon.py:38/47/290` 断言 `run.unknown_fields == {"env_step.my_own_idea": 1}` 等。
存活的是 **runner 把它接进 `record` 的那段接线**：
runner 层唯一的断言是 `test_e2e.py:55 assert record["unknown_ledger_fields"] == {}`，
**它钉住的正是变异体硬编码的那个空值**。
拿一份带未登记字段的账本跑一次 `run_game` 就能杀掉它。

**M14 —— 只写不读的字段，较小的那个发现。**
`verify_chain.verify` 自身覆盖良好（`test_chain.py`，compute）。
但 `record["ledger_head"]` **没有任何可执行的东西读它**：
它不在 `verify.py` 的 `RUN_REQUIRED` 里，
而被文档化的消费者——「arm 把 `ledger_head` 提进它被跟踪的 `runs/<slug>/MANIFEST.json`」
（`LEDGER_FORMAT.md:133-143`、`DECISIONS.md` D-029，runner 自己的注释里也重述了一遍）——
**不存在**：全仓提到 `ledger_head` 的非 `proxy/` 文件只有一份归档的 monitor inbox 便条，
而 D-P8-001 说那个 arm 不调用 runner。
所以 runner 那句注释「`"unchained"` 绝不可在后来被读成 `chain verified`」
**由任何东西强制，也不会被任何东西读到。**

### 6. 两条给账本的note

- `runner.py` 三个跑后报告块分得很干净：`variant_degeneracy` **真的被断言**
  （`test_variant_degeneracy.py:318-326`，verdict／eligibility／count／rule 四项）；
  `unknown_ledger_fields` 只在空值上被钉住；
  **`ledger_head` 与 `spend` 在任何地方都没有被断言。**
- `runner.py` 是那个「被设计成入口、而没有任何生产消费者使用」的东西：
  非测试调用者只有 `proxy/verify.py`（在 `testpaths` 之外的闸门脚本，故不在 392 之内）与它自己的 CLI。
  **这不为存活者开脱**（M8／M9 那一行在每个测试里都跑），但它界定了这个 42% 说的是什么。

## suggest（监控裁决，我不执行）

1. **对 reserve 记录加一条断言**（`usd_cap == 5.0`、`action_cap == 600`）——
   一条断言同时杀掉 M8 与 M9，而它们改的是每个调用者都走的活天花板。
   这是本报告投入产出比最高的一条。
2. **补一条测试断言 runner 在清理释放时传了 `expect_holder`**（M5）。
   机制本身已有测试，缺的是「调用者确实用了它」。
3. **给 `require_keys=True` 这个默认值一条覆盖**（M10）——
   现在唯一碰真 API 的路径依赖一个零测试的 fail-closed 默认。
4. **`main()` 需要至少一条测试**（M11）；现在它一条都没有，
   而它是那个会把 `game_id=None` 发出去的地方。
5. **要么给 `ledger_head` 一个真消费者，要么把它和那段文档一起删掉**（M14）：
   `LEDGER_FORMAT.md:133-143` 与 D-029 描述的消费者不存在。
6. **把 `git config user.email/user.name` 写进变异配方**——
   缺它是通向 `harness-invalid` 的第二条路，而交接件只记了第一条。
7. **下一轮先给 M5／M8／M9 派 refuter**，本文件在那之前不是终稿。

## 我对这个数字的保留

`AUDITOR.md` 要求报告少而实，而这份报告的核心数字（42%）
**是我自己选的十二个变异体的函数**，选法本身带偏。
所以本报告的结论不放在那个百分数上，而放在两件可独立复核的事上：
**（一）击杀全部集中在一个文件的两条测试上；
（二）`record["spend"]` 与 `record["ledger_head"]` 这两个字段被写入、被无人读取，
而其中一个承载着两条活的花钱天花板。**
这两条不依赖我的选样。
