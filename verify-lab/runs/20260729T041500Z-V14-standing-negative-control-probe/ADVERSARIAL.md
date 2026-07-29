# ADVERSARIAL — 对 V14 负控判据的对抗性复核

**审计对象**：`verify-lab/negctl/{criterion,probe,calibrate}.py`
**审计树**：`.worktrees/v14-standing-negative-control-probe/`
**审计基线 commit**：`b6d8643` （见 §0 的重要说明：审计过程中树在我脚下变了一次）
**方式**：只读。跑了 `calibrate.py`、`probe.py --json` 和若干 `python -c` 的离线 AST 脚本；
没有跑仓库里任何领地的 runner / verify 脚本；没有改动除本文件以外的任何文件。

---

## 0. 一个必须先说的事实：审计中途树被改了

我第一次跑 `probe.py --json` 得到 **33 个 `present`**；约十分钟后同一条命令得到 **31 个**。
差的两条恰好是我当时正在核实的两个假阳。

原因不是探针不确定，而是**另一个会话在同一个 worktree 里提交了修复**：

```
a65ba9e verify-lab: the resolver was guessing when an import was ambiguous,
        and it guessed across territories
b6d8643 verify-lab: the pin's own header still quoted the pre-fix confusion counts
```

也就是说：本报告 §2.1 那两个假阳，我独立发现，并且在我写下它们的同时被上游修掉了。
我把它们仍然写进来，因为 (a) 它们证明这类缺陷**确实会发生且不易察觉**，
(b) 修复只堵住了一半（§2.2），(c) 它们是本次复核里最贵的证据。

**这件事本身对「该不该进闸」有独立的结论意义**：判据是**全树全局的**。
`ablation-arm/tests/` 的一次 import 决定了 `cold-start-a0/run_all.py` 的判决。
详见 §6。

---

## 1. 我核实了多少条、怎么抽的样

| 抽样面 | 数量 | 做法 |
|---|---|---|
| `measured=present` 的入口 | 33（修复前）/ 31（HEAD） | **全部**过一遍。逐条取 `evidence` 的 `test_file::func:lineno` |
| 打开逐行读的测试函数 | 21 | 优先读：(a) 只有 1 条证据的脆弱项；(b) 证据跨领地的；(c) calibrate 报的 FP/FN |
| calibrate 的分歧行 | 23（3 FP + 20 FN，HEAD） | 全看；其中 8 条追到源码核实 |
| 全树 import 绑定 | 770 条 | 机械扫描，标出 54 条跨领地绑定，逐条判断合法/误解析 |
| `_failure_assertion` 命中 | 464 次 | 按 reason 分桶统计；对每个可疑桶（exit code / not-in / verdict）取样读源码 |
| 枚举器 vs V11 普查 | 90 vs 141 | 求交集与两边的差集，逐个跑 `has_main_block` / `can_exit_nonzero` 解释成因 |
| `KNOWN_GAPS.json` 的 110 条 `absent` | 按领地聚合 + 6 条深挖 | 找「本领地明明大量写失败断言、这一条却 absent」的形状 |
| `.sh` 入口 | 7 个（全树） | 机械枚举，判断是否 gate 形状 |

**没做的**：没有实际逼红任何一道闸（那会写产物）；没有读封存堆相关的任何东西；
没有对 `figures/verify.sh` 之类的 shell 闸做语义分析，只做了形状统计。

---

## 2. 确证的假阳

### 2.1 【已被上游修复，但曾经是真的】解析歧义把负控算到了另一条赛道头上

**FP-A：`cold-start-a0/run_all.py`**

- 证据（修复前）：`ablation-arm/tests/test_exhibits.py::test_e2_sweep_is_reported_and_disarmed:87`
  与 `::test_e3_is_not_constructible_and_says_why:96`，两条都是 `assert <verdict> is False`。
- 该文件当时的**全部** 2 条证据都来自 `ablation-arm/` —— 同领地证据数 = 0。
- 那两个测试实际在断言什么：`ablation-arm/exhibits` 这个**包目录**里的展品 E2/E3
  的 `report["holds"] is False`。跟 `cold-start-a0/run_all.py` 一个字都不沾。
- 判据为什么错：`test_exhibits.py:18` 写的是
  `from exhibits import e1_a0, e2_a2, e3_charitable, run_all`。
  `run_all` 是 `ablation-arm/exhibits/` 包里的**函数**，但 `Index` 只索引 `.py` 文件，
  包目录不可见；`resolve("exhibits.run_all", ...)` 两级窄化都落空，退回全树 stem 表
  —— 仓库里有四个 `run_all.py`（cold-start-a0 / a2 / a3 / engine-rig/tools），
  与 importer 的共享前缀全是 0，`max` 的次序键 `-len(parts)` 把它交给了 `cold-start-a0/run_all.py`。

**FP-B：`cold-start-a2/a2pipeline/engines.py`** —— 更严重，因为 V11 明确说过这里**什么都没有**

- 证据（修复前）：`engine-rig/tests/test_bench.py:165/213`、`engine-rig/tests/test_ic3_pdr.py:74`，
  5 条证据同领地数 = 0。
- 判据为什么错：`engine-rig/tests/test_bench.py:19` 是 `from engines import deadlock_carver as dc`。
  `engine-rig/engines/` 是**包目录**，不可见；`bindings()` 的兜底
  `if local not in out: bind(local, mod)` 去解析裸名 `engines`，
  而全树只有 `cold-start-a2/a2pipeline/engines.py` 和 `cold-start-a3/a3pipeline/engines.py`
  两个同名 `.py`，于是 engine-rig 的测试被记到了 theory-compiler 赛道的 A2 冷启动头上。
- **为什么这条最贵**：`cold-start-a2/a2pipeline/engines.py` 不在 V11 普查的 127 行里，
  所以 **calibrate 永远看不见这个假阳**。而 V11 的正文第 218 行写得很清楚：
  > `cold-start-a2/run_all.py` 的 13 个子步骤 …… 没有一步有「故意坏掉的输入必须让它红」的负控。
  > 对照组就在隔壁：`cold-start-a0` 有 `test_mutants_are_caught`，`cold-start-a3` 有 `negctl.py`。
  > **A2 两样都没有。**

  我也机械确认了：`cold-start-a2/tests/test_a2.py` 从不 import `a2pipeline.engines`。
  即 A2 这条真空缺口，被 engine-rig 的测试凭同名文件盖住了，而标定矩阵对此完全无感。

上游 `a65ba9e` 的修法是：`shared(best) == 0` 时拒绝解析（宁可制造噪声，不制造沉默）。
**这个修法是对的**，且我的独立复核支持它。

### 2.2 【HEAD 仍然活着】单候选路径没有被这次修复覆盖

`Index.resolve` 的守卫只在 `len(cands) > 1` 之后才跑。**只有一个同名文件时，
`if len(cands) == 1: return cands[0]` 立刻返回，不做任何前缀检查。**

活的实例（HEAD `b6d8643` 实测，54 条跨领地绑定里）：

| importer | 绑定名 | 解析到 | 真实来源 |
|---|---|---|---|
| `a0-spike/tests/test_a0.py:203` | `generate` | **`worldgen/generate.py`** | `from pipeline.gen_exec import UncompilableTheory, generate` —— a0-spike 自己的函数 |
| `engine-rig/tests/test_fd_adapter.py` 等 6 个文件 | `fd_adapter` / `cegis_miner` / `mdl_segmenter` / `lp_potential` / `probe_frontier` / `zero_space`（共 14 条绑定） | **`fuzzlab/props/*.py`** | engine-rig 自己的 `engines/<name>/` 包目录 |
| `worldgen/tests/test_mutate.py` | `validate` | **`engine-rig/engines/fd_adapter/validate.py`** | worldgen 自己的校验函数 |

后果，实测：`worldgen/generate.py` 的 11 条证据里有 **3 条**（a0-spike 的三个
`pytest.raises(UncompilableTheory)`）根本不是 worldgen 的测试。
今天它没有翻转判决（另有 8 条同领地真证据），但 `--json` 打出去的 `evidence`
是错的，`render()` 里 NEW_OK 那行引用的也是它。
`fuzzlab/props/*.py` 今天不是枚举出的入口点 —— 哪天是了，engine-rig 的 43 条
失败断言就会白送给 fuzzlab。

**这是一个还没关的门，形状和已修的那个一模一样。**

### 2.3 【HEAD 活着，且是探针级的】函数粒度掩盖：`worldgen/build.py`

这是我找到的**最致命的活假阳**，因为它同时满足：入口点被枚举、pin 是 `present`、
探针永远沉默、而 V11 明确说这里有一个仓库级的空洞。

- pin：`worldgen/build.py` → `present`。
- 判据的证据：`worldgen/tests/test_build_gate.py:49 / :57`，打的是 `build.gate_failures()`
  —— 那部分是**真负控**，合成 manifest 逐条违反每道闸并断言被报出来。判据在这一点上没错。
- 但同一个文件里还有第二道闸：`worldgen/build.py:231 check_determinism()`，
  `:344` 调用，`:347 NOT DETERMINISTIC` → `return 1`。
- 我机械查过全树：`check_determinism` 这个名字在整个仓库的 `.py` 里出现 **3 次**——
  定义（`build.py:231`）、调用（`build.py:344`），以及
  `worldgen/tests/test_determinism.py:10` 的一行 **docstring 提及**。
  **零个测试调用它。** V11 的原话：这是全仓库最强的确定性主张
  （换 `PYTHONHASHSEED` 起子进程逐字节 diff 35 个世界 × 6 个产物），
  而它自己的 docstring 就写着「a gate that cannot fail is not a gate」。

判据为什么错：**判据是文件粒度的，闸门是函数粒度的。**
一个文件里只要有一道闸有负控，整个文件就绿，另一道闸的空洞被同屋的邻居盖住。
`calibrate` 把这类算作「granularity_conflict」并在
`strict, no file shared` 那一行把它们踢出去 —— 踢出去之后 FP 归零，
但这不是「没有假阳」，是「把假阳从统计里删掉了」。

同形状、同样活着、同样被 pin 成 `present` 的还有：

- **`engine-rig/tools/run_all.py`**（pin `present`，唯一证据
  `test_integration.py:317 assert <exit code> == 2`，打的是「已存在文件不加 `--force`」这条 CLI 用法闸）。
  V11 原话：「负控只覆盖被调用的 validator，**无测试让 run_all 自己走 exit 1**」——
  即 `:260-264` 的 schema 失败红路径无人演示。探针沉默。
- **`arc-recon/contamination.py`**、**`arc-recon/precheck.py`**、**`ablation-arm/run_arm.py`**：
  都在 8 个 granularity_conflict 文件之列，都被 pin 成 `present`。

### 2.4 【判据级，非探针级】`assert <bad> not in <output>` 打在纯正控上

`theoria-arm/harness/run.py`，V11 gold = `否`，detector **AB** 判 `present`。
这就是标定表里 FP 从 3 涨到 4 的那第 4 个。

- 证据：`theoria-arm/tests/test_arm.py:687 test_the_shell_turns_end_to_end_against_the_mock`
- 该测试实际在断言什么：docstring 是
  「No key, no network, no model call, no quota -- and a full ledger」，
  它跑一次**成功**的端到端，然后断言 `summary["budget"]["actions_ok"] == 6`、
  `events[0] == "run_start"`、`seq` 稠密…… 最后一行是
  `assert DEFAULT_KEY not in json.dumps(everything)`。
- 为什么这是假阳：**没有人往里面种过密钥**。这是一条挂在绿色跑道尽头的卫生断言，
  不是「构造坏输入 → 断言闸变红」。判据把「输出里没有某个字符串」当成了失败断言，
  但它在这里断言的恰恰是**成功**。

值不值得开 `not in`？见 §4.3——不值得。

### 2.5 未确证但需登记的两个弱点（我不把它们算作假阳）

- **`theory-compiler/tools/build_handover_packages.py`**：唯一证据是
  `test_handover.py:199 test_one_board_is_refused`。那个 `pytest.raises` 打的是
  `handover.build_files(one)`；`builder`（= build_handover_packages）在这个测试里
  只被用来**提供好的 fixture**（`builder.cart_package()`）。
  判据的「targets」定义是「函数体里提到了这个绑定名」，所以**给夹具供货也算指向**。
  V11 也判 yes，我不推翻它，但这是一条真实的过度归因通道。
- **`arc-recon/client.py`**（V11 两行冲突：`load_api_key` 是，密钥落盘防线否）。
  V11 点名的空洞是「没有任何测试把密钥值植入 body / response_body / 其他 header
  再断言它不落盘」，而 `client.py:300` 只按 header 名替换。
  这条空洞被同文件 `load_api_key` 的 `pytest.raises` 盖住。
  该文件**不在枚举出的 141 个入口点里**（无 `__main__`），所以探针连问都不问它。
  ——这是 §4.5 的问题，不是判据的问题，但后果一样：仓库里安全性最高的那道防线，
  探针从头到尾没有意见。

---

## 3. 确证的假阴

### 3.1 `cold-start-a3/a3pipeline/negctl.py` —— **文件名叫 negctl，判据看不见**

- V11 gold = 是（「它就是负控」）。判据 = absent。
- 真负控长什么样：整个模块就是负控。它用**未经修改的** transfer 臂跑两个被改过一处机制的世界
  （`a3-l2-oneway` 删掉传送腿使关卡不可解；`a3-l2-rewired` 保留腿但落到另一格），
  两者都必须被 replay 层抓成 `caught=True`。
  `main()` 是 `return 0 if verdict["all_caught"] and verdict["none_claimed_a_win"] else 1` ——
  红路径诚实。V11 称它是「这个仓库里最好的负控」。
- 判据为什么瞎：**detector B 只匹配函数名，不匹配文件名。**
  `_SELFTEST_NAMES` 里明明写着 `"negctl"`，而 `scan_selftests` 拿它去比 `node.name`
  （这里是 `run_all` / `main`），永远不会匹配 `negctl.py` 这个文件名。
  一行之差。detector A 也瞎，因为 `cold-start-a3/tests/` 没有 import 它。

### 3.2 `monitor/tests/mutants.py` —— **仓库里最好的变异控制被当成了「缺负控的闸门」**

- pin：`absent`，note 写「not surveyed by V11; the criterion finds no negative control.」
- 它实际是什么：一个完整的变异测试台。docstring：
  「Put each fixed defect back, in a scratch copy, and check a test goes red…
  A mutant that survives means the test covering it is decorative.」
  `MUTANTS` 表把每个已修缺陷原样塞回临时副本，跑套件，存活即失败，`main()` 走 `return 1`。
- 判据为什么瞎：双重盲。detector A 不看它（文件名不是 `test_*.py`，
  `is_test_file` 只认 basename）；detector B 不看它（函数名是 `run_one` / `main`，
  不含 `_SELFTEST_NAMES` 任一词）。于是它被**枚举成一个入口点**，
  再被判定为**没有负控**，登记进 KNOWN_GAPS —— 完全颠倒。
- 佐证这不是孤例：整个 `monitor` 领地在判据眼里有 **0 条**失败断言边，
  而它有 12 个入口点全部 `absent`。

### 3.3 `exam/tools/run_selftest.py` —— 薄 CLI 包在一个一流负控库外面

- V11 gold = 是（8 个故障注入 + 6 个变异体）。判据 = absent。
- 真负控在哪：`exam/tests/test_selftest.py`，其 docstring 就是这份工作的宣言——
  「a mutant that cannot be made to fail is not a mutant, so each one is shown
  failing against a marker broken on purpose」。里面是
  `assert not result["checks"]["drop_exact"]["passed"]` 这种一等一的负控。
- 判据为什么瞎：那些测试 import 的是 `exam/grading/selftest.py`（库），
  入口点是 `exam/tools/run_selftest.py`（CLI 壳）。
  按 import 绑定解析**完全正确**地把证据记到了库上；
  而库本身连入口点都不是（无 `__main__`，见 §4.5），于是证据落进虚空，
  壳子读 absent。
- **这是一个系统性 FN 生成器**，不是个案：「薄 CLI + 有测试的库」在这个仓库里到处都是。
  机械佐证：110 个 `absent` 入口点里，**63 个**所在领地拥有 ≥1 条失败断言边
  （`theory-compiler` 有 193 条边、仍有 6 个 absent 入口；`proxy` 137 条边、1 个 absent）。

### 3.4 `ablation-arm/run_exhibits.py` —— 和 FP-A 是同一个缺陷的两面

- V11 gold = 是，证据是 `test_exhibits.py:96/102` 双向钉住 E3
  （`assert report["holds"] is False`，pre-registered 的证伪）。
- 修复前：那两条断言被记到了 `cold-start-a0/run_all.py`（= FP-A）。
- 修复后：绑定被拒绝解析，那两条断言**谁也不记**，`run_exhibits.py` 仍是 absent。
- 根因不是 tie-break，是**包目录不被索引**：`ablation-arm/exhibits/` 是个包，
  `from exhibits import run_all` 的 `run_all` 是包里的函数，索引里没有对应条目。
- 值得注意：**一个解析缺陷同时制造了一个假阳和一个假阴，方向相反，跨赛道**。
  这是本次复核里信息量最大的一条。

### 3.5 `monitor/gates.py` —— 词表覆盖不到这条赛道的说法

`monitor/tests/test_gates.py` 里有货真价实的负控：

```
def test_nothing_to_run_says_so_rather_than_looking_like_a_pass(tmp_path):
    (tmp_path / "t").mkdir()                      # 一个什么都没有的领地
    row = gates.gate_for(str(tmp_path), "t")
    assert row["kind"] == "none"
    assert "nothing checking it" in row["why"]
```

以及 `test_a_directory_that_does_not_exist_is_not_a_crash`、
`assert row["canonical"] is False`。
判据全部看不见：`"none"` 不在 `_RED_WORDS`；`"canonical"` 不在 `_VERDICT_WORDS`；
`row["why"]` 不在 `_PROBLEM_WORDS`。
这是纯词表问题，也说明**词表是按 proxy / worldgen 的口音调的**。

### 3.6 `theory-compiler/tools/probe_mentions.py`

V11 gold = 是：`EXPECTATIONS` 是预注册的期望值（`sokoban2_x5 / first_argument / off_wall`
必须在 376 步上失配、`declared / on_wall` 必须 52 步全对），
「哪条读法算错了就红」，`:404-408` 失败 `return 1`。
判据瞎的原因是**预注册的期望值不是 pytest，也不是名字含 self_test 的函数**——
它的执行者是 `theory-compiler/runs/20260728T102343Z-c7/verify.sh` 里的 heredoc，
即 §4.6 的范围外空洞。这是 criterion.py docstring 自己承认的一类，我只是确认了它是真的。

---

## 4. 六个特别点，逐个结论

### 4.1 `_EXIT_WORDS` 里的 `"rc"` / `"code"` —— **找到了，而且比预想的糟**

`_looks_like_exit_code` 对 `ast.Subscript` 用的是**子串**匹配
（`any(w in low for w in _EXIT_WORDS)`），不是相等。实测：

```
x["search_timeout"]  -> True   （"sea rc h_timeout" 里的 rc）
x["source"]          -> True   （sou rc e）
x["arc_calls"]       -> True   （a rc _calls）
x["n_forced"]        -> True   （n_fo rc ed）
```

真实误命中，`theoria-arm/tests/test_arm.py:471`：

```
assert register.counts()["search_timeout"] == 1
```

这被判据读成 `assert <exit code> == 1`。它实际断言的是**一个计数器等于 1**
（`surprise.Register` 里 `search_timeout` 这一族记了一条）。
这正是 `_looks_like_exit_code` 的 docstring 声称已经修掉的那个 bug
（`assert len(rows) == 6` 类），只是换了个入口：`ast.Name` 走的是相等/前后缀匹配，
`ast.Subscript` 走的是裸子串匹配，两条路的严格度不一致。

另外 `proxy/tests/test_migration.py:75 assert failed["http"]["status"] == 400`
也被判为失败断言，而它实际在断言**迁移保真**：v0 ledger 里一条失败的 step
在 lift 之后仍然保留它的 400 和 reason。这不是负控，是保真测试。

今天没有入口点因为这条误命中而翻绿（`theoria-arm/inner/*` 和
`proxy/tools/upgrade_ledger.py` 都不在 141 个枚举入口里），
但这是一颗上了膛的枪：任何一个名字里带 rc / code / status 子串的字典键 + 非零整数，
都会被算成红。

### 4.2 `_VERDICT_WORDS` 里的 `matches` / `caught` / `agree` —— **没找到**

我机械统计了全树所有 `assert not <verdict>` 的命中（29 次），按触发词分桶：

```
ok 8   clean 5   green 5   passed 5   succeeded 4   holds 4
```

`matches` / `match` / `caught` / `all_caught` / `agree` / `same_answer` /
`identical` / `deterministic` / `sound` / `complete` / `accepted` / `allowed` /
`permitted` / `calibrated` / `reproduced` **一次都没有触发**。
所以这几个词今天是死词，不是误报源。诚实的结论：**这一点我没打穿**。
（顺带：它们是死词也意味着它们没有被任何证据支持地留在词表里。）

### 4.3 `assert <bad> not in <output>` —— **找到了，而且这条规则应该关掉**

criterion.py 的说法是「这是 `proxy/` 写红线的主要方式」。实测不是。

全树有 **118 个** test 函数**只因为**这条规则才被算作含失败断言（`A` 判是、`A-` 判否）。
按领地分布：

```
theory-compiler 26   exam 21   proxy 14   engine-rig 9   battery 7
arc-recon 6   worldgen 6   ablation-arm 5   baseline-arms 5
cold-start-a2 5   cold-start-a3 5   cold-start-a0 4   theoria-arm 3   monitor 2
```

**proxy 只占 14/118 = 12%。** 剩下 88% 里，随手取样即见纯正控：

- `proxy/tests/test_ledger.py:11 test_lines_are_canonical_and_newline_terminated` —— 格式正控
- `worldgen/tests/test_door_under_agent.py:53 test_the_agent_is_never_inside_a_solid_cell` —— 不变量正控
- `engine-rig/tests/test_bench.py:200 test_the_original_init_reaches_the_planner_byte_for_byte` —— 保真正控
- `exam/tests/test_adaptation.py:139 test_the_world_is_synthetic_and_neither_pile_is_touched` —— 卫生正控

标定说打开这条 FP 从 3 涨到 4，**那第 4 个就是 §2.4 的 `theoria-arm/harness/run.py`**，
而它是一条挂在成功跑道尽头的密钥卫生断言。
**结论：不值。`AB` 相对 `A-B` 换来的 FNR 从 30.2% 降到 27.0%，
代价是把 118 个正控当成红线，其中一个已经被证实制造了假阳。
出厂选 `A-B` 是对的，`AB` 不该被当成可选项摆在 `--detector` 里。**

### 4.4 同名文件解析被解错 —— **找到了三个真实的，且有一个还活着**

见 §2.1（`run_all` 四选一、`engines` 二选一，已修）和
§2.2（`generate` / `fd_adapter` / `validate` 等单候选路径，**HEAD 仍然活着**）。

补一句方法论上的观察：criterion.py 的 docstring 说
「A binding is resolved against the importing file's own ancestry … **that is what
the interpreter does at run time**」。这句话不对。
解释器做的是按 `sys.path` 顺序找，而这些测试文件全都在做
`sys.path.insert(0, <自己的领地根>)`；「与 importer 共享最长路径前缀」
只是这件事的一个近似，并且在**包目录**这个最常见的情形下彻底失效
（`engines/`、`exhibits/`、`harness/`、`pipeline/`、`recheck/` 全是包）。
真正稳的做法是把包目录（含 `__init__.py` 的目录，或任何目录）也进索引，
并把测试文件里的 `sys.path.insert` 参数解析出来当搜索路径。

### 4.5 `can_exit_nonzero` 枚举器从没标定过 —— **漏得比多收得严重**

| | 数量 |
|---|---|
| 枚举出的入口点 | 141 |
| V11 普查里能定位到 `.py` 文件的闸门 | 90 |
| 两者交集 | 67 |
| **V11 认作闸门、枚举器漏掉** | **23（26%）** |
| 枚举出但 V11 从没查过 | 74 |

**漏掉的 23 个，成因我逐个跑过**，全部是这两类：

- **无 `__main__`，靠 raise 拒绝的库型闸**（13 个）：
  `proxy/guard.py`、`exam/guard.py`、`battery/guard.py`、`proxy/redact.py`、
  `proxy/ledger.py`、`arc-recon/client.py`、`exam/leakage.py`、
  `exam/grading/selftest.py`、`exam/grading/calibration.py`、
  `theoria-arm/armtools/archive.py`（**V11 最锋利的那条发现所在的文件**）等。
  枚举器的定义（有 `__main__` **且**能非零退出）在结构上排除了整整一类闸门。
- **有 `__main__` 但确实恒 return 0**（10 个）：
  `proxy/spend_gate.py`、`proxy/env_proxy.py`、`proxy/model_proxy.py`、
  `proxy/cost.py`、`proxy/tools/upgrade_ledger.py`、`theoria-arm/harness/run.py` 等。
  这一类枚举器**判对了**——它们本来就不能红，这恰好是 V11「能红」那一列判否的同一批。

多收的部分（74 个里我人工过了一遍），至少 **17 个不是验收入口**：

- `runs/` 冻结产物里的一次性脚本 **5 个**：
  `a0-spike/runs/…/make_manifest.py`、`arc-recon/runs/…/proposed/board_log_invariants.py`、
  `…/concurrency_invariants.py`（**名字里就写着 proposed**）、
  `baseline-arms/runs/…/await_quota.py`、`engine-rig/runs/…/manifest.py`
- 世界定义 **4 个**：`cold-start-a0/world/ground_truth.py`、`cold-start-a0/prime/world/ground_truth.py`、
  `cold-start-a2/a2world/ground_truth.py`、`cold-start-a3/a3world/ground_truth.py`
- 报表脚本 **3 个**：`baseline-arms/harness/summarise_campaign.py`、`summarise_pilot.py`、`campaign_status.py`
- 包 `__init__` **1 个**：`proxy/scoring/__init__.py`
- 测试台 **1 个**：`monitor/tests/mutants.py`（见 §3.2，被彻底判反了）
- 展品 **3 个**：`ablation-arm/exhibits/e{1,2,3}_*.py`

**`runs/` 那 5 个是 CI 上的定时炸弹**：`runs/<id>/` 每做一次实验就多一个，
里面放一个带 `main() -> return 0 if ok else 1` 的脚本是这个仓库的常规做法
（`MANIFEST.json` 那条约定鼓励它）。每个这样的新目录都会触发一次 `NEW_GAP` = 红。

### 4.6 `.sh` 全部在范围外 —— 空洞比声明的大

全树 7 个 `.sh`，**7 个全是 gate 形状**（有 `exit <非零>` 或 `set -e`）：

```
figures/verify.sh                                225 行
proxy/verify_spend.sh                            111 行
monitor/verify_quota_exit.sh                     112 行
theory-compiler/runs/20260728T102343Z-c7/verify.sh  88 行
arc-recon/verify.sh                               74 行
ablation-arm/verify.sh                            14 行
monitor/verify.sh                                 11 行
```

三点评估：

1. **数量小，位置贵。** 7 vs 141 看起来是 5%，但 `monitor/verify.sh` 是 monitor
   这条赛道的**规范闸**，`figures/verify.sh` 是 criterion.py 自己 docstring
   引用为「gate 7 的教训来源」的那个文件，`proxy/verify_spend.sh` 是 V11 记录的
   「文档说这是查池子是否超限的办法、而它超限也退 0」的那条。
2. **`monitor/gates.py` 自己写着**规范的领地闸名是 `verify.sh` 或 `verify.py`
   （`test_a_gate_under_another_name_is_found_and_said_to_be_unusual`）。
   也就是说，这个仓库对「一道闸」的**自己的定义**里，shell 是头等公民，
   而探针的范围把头等公民整个切掉了。
3. **最好的负控之一藏在 shell 里**：`theory-compiler/runs/…/verify.sh` 的 heredoc
   跑 `probe_mentions` 的预注册期望（§3.6）。范围外 ≠ 不重要，
   在这里是「范围外 = 恰好把最难自动化的那批负控全排除了」。

---

## 5. 对判据的总判决

**标定出来的 FPR ≈ 8.8% 是不可信的，真实 FPR 比它高。** 三条理由：

1. **样本框错了。** 标定跑在 V11 的 103 行上；探针跑在 141 个入口点上，
   其中 **74 个 V11 从没查过**。我确证的最贵假阳
   （`cold-start-a2/a2pipeline/engines.py`）就落在那 74 个里，
   **标定矩阵在结构上不可能看见它**。
2. **「no file shared」那一行把假阳定义没了。** `strict, no file shared: FP=0`
   之所以是 0，是因为 3 个 FP 全是 granularity_conflict 文件，被剔除了。
   但函数粒度掩盖是真实的漏检机制，不是统计噪声：
   `worldgen/build.py::check_determinism`（全仓库最强的确定性主张，零测试调用）
   和 `proxy/spend_gate.py::__main__`（文档说它是查超限的办法，超限也退 0）
   都因此被探针判绿。把它们从分母里删掉，等于把这个失效模式定义成不存在。
3. **黄金标准本身是 photo，不是 oracle。** V11 自己在 §352 承认
   「我没有为每一道闸都尝试实际逼红……其余读码项，我读的是返回语句本身，
   没有构造坏输入」。用它算出的 FPR，误差棒里同时含有判据的错和普查的错。
   我读了 3 个「假阳」的源码，**其中 2 个（`worldgen/build.py --check` 一半、
   `proxy/spend_gate.py` 的 SpendGate 一半）判据是对的，V11 的那一行是对另一个函数说的**。

**FNR ≈ 31.8%（HEAD）是可信的，甚至偏乐观。** 我核实的 6 个假阴全部是真的，
而且根因各不相同（文件名 vs 函数名、CLI 壳 vs 库、包目录不索引、词表口音、
非 pytest 负控、shell 负控）。分母只有 103，而 141 个入口点里
110 个是 `absent`，其中 63 个所在领地明明在大量写失败断言。
真实的 FNR 我估计在 **35–45%** 之间，但我没有独立黄金标准可以证明这个数，
所以这是一个判断，不是一个测量。

**判据本身的质量评价**：写得比它的标定表现好。
`_looks_like_exit_code`、`_is_verdict`、`_is_problem_bag` 这三层区分
（计数 vs 退出码、正控 vs 负控、findings 袋 vs 判决词）都是对的方向，
每一层的 docstring 都指名了它修掉的那个具体误报——这是很高的工程标准。
它的失败不在判断逻辑，在**两个前置层**：解析（哪个文件）和枚举（哪些是闸）。
这两层都没有标定，而它们的错误会直接变成判断层的输入。

---

## 6. 该不该进 CI 合并闸

**结论：现在不该。可以以「报告不阻塞」的形式常驻，并给它三个必须先修的前置条件。**

### 反对现在进闸的理由

1. **枚举器未标定，而 `NEW_GAP` 直接吃它的输出。** `probe.py` 的 docstring 已经
   诚实地说了「Gating on an uncalibrated enumerator is the mistake this lab exists
   to name」，然后让 `NOT_A_GATE` 不阻塞——但 **`NEW_GAP` 阻塞，而它 100% 由同一个
   枚举器决定**。这条豁免只挡住了枚举器的一半错误方向。
   实测：26% 的 V11 闸门被漏掉，≥17 个非闸门被多收，`runs/<id>/` 每新增一次实验
   就可能红一次。这不是理论风险，是这个仓库的日常。
2. **FNR 32%，且每个假阴都是一次逼人加豁免的误报。** 32% 的意思是：
   三分之一的新闸门带着真负控进来，探针照样红。第一次是讨论，第三次是
   往 KNOWN_GAPS 里加一行，第十次是把探针关掉。
   `monitor/tests/mutants.py` 已经是活生生的例子：仓库里最好的变异测试台
   被登记成「缺负控的闸门」。
3. **判据是全树全局的，闸是按 PR 局部的。** 这是我在审计中亲身撞上的（§0）：
   `ablation-arm/tests/` 的一行 import 决定了 `cold-start-a0/run_all.py` 的判决。
   在 CI 里这意味着 **A 赛道的一次提交可以让 B 赛道的入口点变红**，
   而 B 赛道什么都没改。对一个明文规定「两条赛道互不通信、只提交自己路径」
   的仓库，这是一个会制造归属争议的耦合。
4. **解析层还有一个没关的门**（§2.2 单候选路径），形状与刚修掉的那个完全一致。
   在这个门关上之前，任何一次「某领地新增一个与他领地同名的 `.py`」
   都可能悄悄把负控记错家。

### 支持它常驻（不阻塞）的理由

- 它是**目前唯一**能把 V11 那张照片变成可重算判断的东西，而照片必然过期。
- `REGRESSION`（pin 里 `present` 变 `absent`）这一类，误报机制比 `NEW_GAP` 少得多：
  它要求这个文件**曾经**被判据看见过负控，也就是说这个文件已经过了解析层和枚举层的关。
  **如果一定要今天就进闸，只让 `REGRESSION` 阻塞、`NEW_GAP` 只报告**，
  是我能支持的最激进方案。
- pin 文件的写法是对的（每条带 owner + note，假阴显式标注「这是判据的已知假阴，
  不是领地的缺口」），这让「加豁免」这个动作留下的是知识而不是噪声。

### 进闸前必须做的三件事（按优先级）

1. **标定枚举器。** 拿 V11 那 90 行当黄金标准跑一次 `can_exit_nonzero` 的混淆矩阵，
   把结果和判据的矩阵并列写进 `CALIBRATION.md`。今天这个数是 67/90 召回，
   它必须像 FNR 一样被印在文档最显眼的位置。同时把 `runs/**` 和 `**/ground_truth.py`
   排除出枚举范围，或者要求入口点必须在 git 追踪的非 `runs/` 路径下。
2. **关掉单候选解析漏洞**，并把包目录纳入索引。
   `if len(cands) == 1: return cands[0]` 之前也要过 `shared() > 0` 那道关
   （或至少：跨领地时降级为「不解析」）。
3. **把 detector B 从「函数名」扩到「文件名」**，这一改直接收回
   `cold-start-a3/a3pipeline/negctl.py`；再把 `_shape_of_selftest` 里
   「任何 `.append` 调用都算」收紧——现在 `criterion.py::scan_selftests` 自己
   因为函数名含 `selftest`、函数体里有 `edges.setdefault(...).append(...)`
   而被判为「自带 in-tree self-test」。判据给自己发了一张它自己不该认的证书。

最后一条不是要求，是建议：**把 `--detector AB` 从 CLI 里拿掉**。
§4.3 的数据说明这条规则在 proxy 之外大面积误命中（118 中 104 在 proxy 之外），
把它留作一个开关，等于把一个已知会制造假阳的选项摆在别人手边。
