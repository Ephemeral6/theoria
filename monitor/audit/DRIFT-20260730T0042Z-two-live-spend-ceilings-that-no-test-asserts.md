# DRIFT-two-live-spend-ceilings-that-no-test-asserts

severity: low-to-medium（2026-07-30T04:08Z 由 medium 下调，理由见文末 AMENDMENT §A/§D/§G）
dimension: 7 (不可能变红的检查) + 5 (流程漂移)
status: **已复核并已修订（2026-07-30T04:08Z，周期 48）——先读文末的 AMENDMENT 再读正文。**
落盘时它未经对抗复核（那是它与同批其余五份的区别）；复核已于本轮完成，结果是：
**M5 被推翻为等价变异体**（得分 5/11=45%），**M8／M9 确认但三处引用有误**，
**§4「五次击杀全部来自同一个文件」是四中之四**，**suggest 1 照抄会在未变异的 master 上变红**，
而**真正的载荷是被排在第 3、4 位的 M10＋M11**。严重度随之由 medium 下调为 **low-to-medium**。
正文 §1-§6 一字未改，订正全部集中在文末，好让读过旧版的人看得出改了什么。

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

---

## AMENDMENT 2026-07-30T04:08Z（周期 48 落盘，取代第 5 行的「未经对抗复核」状态）

上一周期这份报告在最上面写了「**M5／M8／M9 在被 refuter 推过之前不作数**」，
并把「先给它们派 refuter」列成 suggest 7。**那次复核已经做完了**：refuter 重建了整套
变异谐架（392 条控制通过，15 个变异体里重跑 8 个，每个都带独立的活性断言并清 `__pycache__`），
八条判定全部复现。本节是它的结果，**本轮我逐条重新量过被引用的行号才写下来**（八处全部复现）。

**一句话：那个百分数变了，形状那句话错了一半，而真正的发现不是 M8／M9，是 M10＋M11。**

### A. M5 被推翻——它是等价变异体，得分降为 5 / 11 = 45%

- 报告 §5 说 M5 的非等价「已被构造出的输入证明」。**那个构造不复现**：
  原始与变异体都把另一个会话的 claim 留在 `held_usd=3.0`，两边一样。
- 原因在**上一行**：`proxy/runner.py:288` 的归属过滤
  `if (entry["holder"] or {}).get("run_id") != run_id: continue`
  已经先 `continue` 掉了，`expect_holder` 因此**永远不被查询**。
- 而报告声称的机制本身也是假的：`SpendGate.totals()` **确实拿 `_PoolLock`**
  （`proxy/spend_gate.py:681-684`），两次读都在锁内；且在一个只追加的账本里，
  对固定的 `reservation_id`，`holder` 是不可变的——
  **没有任何并发写入能造出报告设想的那种「快照与磁盘不一致」。**
- 更要紧的一点连 refuter 也没说：`runner.py:290-293` 的注释**自己就写着**
  「`expect_holder` restates the same claim … Belt and braces **on purpose**」。
  **代码作者预期的正是这种等价性。** 所以 M5 不是覆盖缺口，是一处刻意的冗余；
  而报告为它构造的那个「区分输入」，本身就是已经在跑的
  `proxy/tests/test_spend_gate_egress.py:183-231` 那条通过的测试。
- 按本报告 §3 自己的扣除规则，M5 必须扣除：**5 / 11 = 45%**，
  「活钱路径上的存活者」由 3 条降为 **2 条**。
- **suggest 2 撤回。**

### B. §4 的「形状」那句话是错的——是五中之四，不是五

「五次击杀**全部**来自 `test_spend_gate_egress.py` 里的同两条 S29 测试」：**假。**
**M7 在那个文件里一次都没死**——它死在 `test_e2e.py` 与 `test_variant_degeneracy.py`
的 **32 个 node** 上（用 `--ignore` 重跑验证）。正确的说法是**四中之四**。
同时 §4 的另一句「删掉那一个文件就只剩 1/12」**是对的**——
而报告从头到尾没有把这两句话对起来。（现在也应写成 1/11。）

### C. M8／M9 确认，但报告的三处引用要改

**确认的部分**：两条变异体确实活过 392 条测试；套件里确实没有第二条断言；
并且**在今天的真池子上后果是活的**——池内约 `$178.76` / `18,199` action 空闲，
所以一笔被放大成 `$50` / `6000` 的预留**今天会被批准**通过
（87 条 reserve 记录里写的都恰好是 `(5.0, 600)`）。

**要改的三处**：
1. **那两个上限不在 `runner.py` 里。** `proxy/runner.py:77` 读的是
   `gate.policy.default_run_caps`；字面值住在 `proxy/spend_policy.json:9-12`
   （`usd` 在 `:10`，`actions` 在 `:11`）。我上一轮的欠账便条把它记成 `:10-13`，
   这里一并订正。顺带说一句值得记的：那个文件 `:14` 用整段 `provenance` 写明了
   为什么是 $5／600——**这两个数有作者写下的理由，只是没有测试**。
2. **三个被引用的行号指向的不是代码。** 报告 §5 写「`spend_gate.py:955`」与
   「`spend_gate.py:733`」：`:955` 是一行注释（`# -- and this reservation's own caps`），
   真正的两条拒绝在 **`:956`**（`entry["usd"] + usd > entry["usd_cap"]`）与
   **`:963`**（action 孪生条件）；`:733` 是 `with _PoolLock(...)` 那一行，
   预留时的池上限拒绝在 **`:737`**（`if usd_cap > totals.free_usd`）。
3. **「`else` 臂 100% 的调用者都走、每一条会玩游戏的测试都执行」量错了。**
   插桩实测：它在 **392 条里跑 8 条（2.0%）**。
   尤其讽刺的是，**那两条 S29 egress 测试把 `_run_game` monkeypatch 掉了，根本到不了这里**——
   也就是说，本报告 §4 认定为唯一战力的那两条测试，恰好不经过 §5 认定为最活的那一行。

### D. suggest 1 —— 照它写的抄下去，会在**未变异的** master 上直接变红

`proxy/tests/conftest.py:30-41` 有一个 session 级 autouse 的 scratch 池，
`:40` 写着 `"default_run_caps": {"usd": 1.0, "actions": 100}`。
所以在测试里断言 `usd_cap == 5.0` **在原始代码上就会失败**——
这条「投入产出比最高」的建议会被当成一条假红提交上去。
**正确写法二选一**：写成相对式 `== gate.policy.default_run_caps["usd"]`，
或在该测试内装一个 5.0/600 的池。两种都仍然同时杀掉 M8 与 M9。
（这也顺带解释了 M8／M9 为什么能活：套件里的默认上限根本不是生产的那一对。）

### E. 排序错了：真正的载荷是 M10＋M11，而它们被排在第 3、第 4 条

- `require_keys=` 的**每一个**调用点都传 `False`，所以那个 fail-closed 的 `True` 默认值
  **被零条测试走过**；而 `proxy.runner.main` 在全仓**没有任何调用者**，
  一句裸的 `python -m proxy.runner` 会把 `game_id=None` 发往真的 `UPSTREAM_ARC`。
- **报告没说的是这两条是耦合的**：若 `require_keys=True` 而没有密钥，
  `proxy/env_proxy.py:79-80` 会先拒绝——所以 **M11 的真后果需要 `.env` 里的密钥在场**，
  也就是这台机器的**正常状态**。两条一起看，才是这份报告里唯一能碰到真网络的路径。
- evidence 与 suggest 都没有记下这个交互。**下一次由监控排序时，这两条在最前面。**

### F. 报告漏掉的「第二条断言」，以及它为什么不算

`freeze/BUDGET_TABLE.json:148-149` 把 `600` 与 `5.0` 钉住了，
`freeze/build_budget_table.py:979-997` 的 `--verify` 在漂移时 exit 1。
**但 `freeze/verify.sh` 从不调用它**——所以它是一条命令，不是一道闸门。
「没有任何东西断言过这两个值」这句话因此**仍然成立**，只是理由要换成这一条。

### G. `ledger_head`（M14）是既有结论，不重复立案；严重度下调

`proxy/STATUS.md:113-133` 与 `proxy/REDTEAM.md:427-445` 已登记，
而我们自己的 `DRIFT-20260729T2350Z:83` 明文写过「作为一行交叉引用记在这里，不单独立案」。
按那条自家裁决，M14 在本报告里也只能是交叉引用。
**综合 A（分子少一）＋ D（首条建议不可用）＋ G（一条是既有项）：
本报告严重度由 medium 下调为 low-to-medium。** 未下调为 low，因为 E 的两条仍是活的。

### H. 对本文件的机械改动，声明在此

第 5-9 行的「未经对抗复核」状态已被本节取代；除此之外**正文一字未改**，
所有订正都写在这里，不回填进 §1-§6，这样读过旧版的人能看出改了什么、为什么。
suggest 7（「下一轮先派 refuter」）**已履行并关闭**。
