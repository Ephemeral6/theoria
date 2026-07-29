# 对抗性复核：负控普查

复核对象：`verify-lab/NEGATIVE_CONTROL.md`（正文）、本目录 `CENSUS_TABLE.md`、`partials/` 六份分表。
复核人：RES-3 派出的对抗性复核员。纪律：只读被复核文件；所有执行在 scratchpad 临时目录内进行；
零网络；封存堆零接触（下文出现的 `ls20-9607627b` 仅作为**字符串**写入临时账本，与仓库自身
`arc-recon/test_hygiene.py:419` 的既有用法完全一致，未读取任何封存局内容）。

## 判决摘要

| 被复核的结论 | 我的判决 | 强度 |
|---|---|---|
| 头条：真发生封存接触时 `arc-recon/verify.sh` 会报 `-- ok` 并以 `VERIFY: green` 结束 | **推翻** | 实测 |
| 头条子句："如果护栏被绕过，之后没有任何东西会变红" | **推翻** | 实测 |
| 窄版：`contamination.py:338` 的退出码只反映 `piles.json` 哈希 | **推不翻** | 实测 |
| 三层表中 "interception 层 = 全仓测得最好的东西"（RED-01…46 逐条构造） | **推翻**（46 条里 4 条无测试，其中 2 条 critical） | 实测 |
| "三类论文主张压在 verify 绿上" | **推翻**（论文全文零次提及 `verify.sh`） | 读码 |
| 共用 worktree 的污染只影响"运行后文件被改"类结论；退出码类结论不受影响 | **推翻**（退出码类同样被污染，已找到实例） | 实测 |
| `figures/check_coverage.py --self-test` 是真负控 | **推不翻** | 实测 |
| `exam` 标定是真负控 | **削弱**（8 个注入故障里 7 个转红，非全部） | 读码 |
| 表内算术（127 / 15 / 35 / 13 / 24 及六领地小计） | **推不翻** | 实测 |
| 六份分表之间无重复计数 | **推不翻** | 实测 |
| "有负控 = 是" 的判定口径六人一致 | **削弱**（四套口径；61 按严口径应为 51–54） | 读码 |
| "实测 24 行" | **削弱**（14 行靠两次聚合套件运行；诚实数 10–12） | 读码 |
| 127 作为分母 | **削弱**（含约 33 个本不需要负控的入口；且 127 行≈116 文件） | 读码 |
| worldgen 工作样例（`QC.json`/`QC_MUTANTS.json` 带 `pass: false` 却印 green 退 0） | **推不翻** | 实测 |

净结果：**推翻 5 条，削弱 4 条，推不翻 5 条。**
最重要的一条是第 1 节——头条结论是错的，而且错的方向是**高估了缺陷**。
次重要的是第 3 节——正文的污染分类漏了一整类，我找到了实例。

---

## 1. 头条结论（封存接触审计）

### 1.1 窄版成立：我复现了，且用比原普查更强的方法

原普查的复现方式是"**把临时账本加进 `OTHER_LEDGERS`**"（`partials/proxy-arcrecon.md:110`），
即**改了源码常量**。那只能证明函数行为，不能证明真实路径。

我改用不碰源码的做法：把 `arc-recon/` 整棵树复制到 scratchpad，在**默认账本路径**
`data/recon_ledger.jsonl` 末尾追加一行真实形状的封存请求，然后原样运行。

```
  ledger audit: arc-recon/data/recon_ledger.jsonl   1232 calls, sealed ADDRESSED: ls20-9607627b
  contamination.py exit=0
```

**`contamination.py:338` `return 0 if check["matches"] else 1` 只反映切分哈希——推不翻，实测确认。**
`arc-recon/verify.sh:18-28` 的 `step()` 也确实只看退出码，我读了，正文没写错。

### 1.2 但头条的因果链断在最后一步：verify.sh 不会绿，它会红

正文（`NEGATIVE_CONTROL.md:68-71`）：

> 所以一次真实的封存接触会打印自己的名字，然后被报告 `-- ok`，运行以 `VERIFY: green` 结束。

以及（`:83-84`）：

> *如果护栏曾被绕过，之后不会有任何东西变红。*

**这是错的。** 同一个 `verify.sh` 的**第 1 步**就是 `python -m pytest -q`，而
`arc-recon/test_hygiene.py` 里有两条断言直接压在真实账本上：

```python
def test_the_cross_track_audit_covers_more_than_our_own_ledger():
    audit = contamination.all_ledger_audit()
    ...
    assert audit["all_clean"] is True          # test_hygiene.py:400

def test_the_real_ledger_has_addressed_no_sealed_game():
    assert contamination.sealed_api_contacts()["clean"] is True   # test_hygiene.py:443
```

在**同一棵被植入的树**上实测：

```
2 failed, 80 passed        PYTEST EXIT=1
FAILED test_hygiene.py::test_the_cross_track_audit_covers_more_than_our_own_ledger
FAILED test_hygiene.py::test_the_real_ledger_has_addressed_no_sealed_game
```

再实测整脚本：

```
== offline test suite
-- FAILED (exit 1)
...
== pile cut, claim set and the sealed-contact audit
-- ok
VERIFY: RED          VERIFY_EXIT=1
```

正文预言的那一行 `-- ok` 确实出现了（第 53 行那一步照常撒谎），但**脚本以 `VERIFY: RED` 结束**。
所谓"绿灯"从来没亮过。

这两条测试不是我新加的：`git status arc-recon/` 为空（本工作树未改动），两条断言都在 `HEAD` 里
（`git show HEAD:arc-recon/test_hygiene.py` 命中 2 次），最后一次改动是 `81ea2fd`，**早于本次普查**。
更要命的是，`partials/proxy-arcrecon.md:9` 记录普查员**跑过这个文件**——
`pytest -q test_hygiene.py test_canary_schedule.py → 82 passed`——只是在干净树上跑的，
植入之后没有重跑。植入与重跑之间隔了一步，结论就反了。

### 1.3 第二、第三道会红的闸，以及它们的边界（正面证明，非"我没找到"）

我搜过的地方，逐一列出：

| 搜索 | 结果 |
|---|---|
| `grep -rn "sealed_api_contacts\|all_ledger_audit\|sealed_games_contacted" --include=*.py --include=*.sh --include=*.yml` 全仓 | 只有 `contamination.py` 自身 + `arc-recon/test_hygiene.py`（8 处） |
| 全仓 `*.yml` / `*.yaml` | **零个**。本仓库没有任何 CI 配置文件 |
| 全仓 `verify.sh` | 4 个：`ablation-arm/`、`arc-recon/`、`figures/`、`theory-compiler/runs/.../c7/` |
| `tools/ledger_invariants.py` | **不存在**（任务书假设的这个文件全仓无匹配） |
| `monitor/` 反射层与合并闸 | `monitor/ci_merge.py` 存在，见下 |

结果是**三道**独立的红：

1. **`arc-recon/test_hygiene.py:400,443`**（实测）——覆盖 `all_ledger_audit()` 的全部 3 条账本路径。
   由 `arc-recon/verify.sh` 第 1 步执行。
2. **`monitor/ci_merge.py`**（读码）——合并闸对"分支触碰到的每个顶层目录"跑 `pytest -q -x`
   （`:9`、`:32`、`gate_for()` `:62-77`：不再靠手写清单，而是扫树里有没有 `test_*.py`）。
   `arc-recon/` 有测试，所以**触碰 arc-recon 的分支在合并时也会撞上上面两条断言**。
   *边界*：只覆盖被触碰的目录。封存接触若只写进 `baseline-arms/ledger.jsonl` 而分支不碰
   `arc-recon/`，这道闸不会跑 arc-recon 的套件——这是真实的空隙。
3. **`theoria-arm/armtools/archive.py:256-258`**（读码）——每次收工按字节扫描记录，
   产出 `sealed_game_ids_found` / `sealed_pile_untouched`，且**自带构造式负控**：
   `theoria-arm/tests/test_arm.py:607-608` 植入一个封存 id，断言 `sealed_pile_untouched is False`。
   论文引用的正是这一份（见第 5 节）。
4. **`baseline-arms/harness/audit_cells.py`**（读码）——`:208-227` 逐格扫封存 id，
   `failed = ... or bool(sealed_hits) or ...`，`:236` `return 1 if failed else 0`。退出码诚实。

**所以头条应当降级为**：*"封存接触在 `contamination.py` 这一条线上到不了退出码；但同一个
verify.sh 的 pytest 步、合并闸、以及两个臂各自的收工闸都会变红。这是一条冗余链路上的断线，
不是唯一链路上的断线。"*

### 1.4 我另外发现的、比正文更严重的东西：审计有**覆盖洞**，不只是接线洞

`contamination.py:60-64` 的 `OTHER_LEDGERS` 是**硬编码的两条路径**，加上默认的
`recon_ledger.jsonl`，一共只扫 **3 个文件**。而树里实际存在的调用账本远不止：

* `theoria-arm/runs/*/ledger.jsonl` —— **8 份**（含 `20260728T015354Z-g50t-first-contact/ledger.jsonl`，47 行真实调用）
* `baseline-arms/out/shards/{ledger,probe_log}.a7-*.jsonl` —— **8 份**（`ledger.a7-g50t.jsonl` 183 行、`probe_log.a7-g50t.jsonl` 100 行）

这些**一份都不在扫描列表里**。而且它们不是无关紧要的临时文件——
`figures/SOURCES.sha256` 第 14-17 行**明确把 4 份 shard 账本钉为图管线的输入源**
（`[untracked]`），另有 4 份记为 `[absent-optional]`。图管线认得的数据源，封存审计不认得。

这一点正文完全没提。它比"退出码没接线"更难修：接线是一行代码，覆盖洞要重新定义"账本"是什么。
**修复建议：`OTHER_LEDGERS` 应改为 glob 发现 + 断言"发现到的账本数 ≥ 上次记录数"，
否则新增一个写账本的路径就是一个新盲区，而没有任何东西会说出来。**

---

## 2. 数字与口径

### 2.1 算术：推不翻（实测）

我把六领地小计逐列相加，与 `CENSUS_TABLE.md:143-168` 的合计**完全吻合**：

| 列 | 六领地相加 | 表内合计 |
|---|---|---|
| 入口数 | 20+19+14+10+32+32 = **127** | 127 ✓ |
| 能红 是/部分/否 | 103 / 6 / 15 | 103 / 6 / 15 ✓ |
| 有负控 是/部分/否 | 61 / 22 / 35 | 61 / 22 / 35 ✓ |
| 退出码诚实 是/部分/否 | 84 / 8 / 13 | 84 / 8 / 13 ✓ |
| 实测（混合） | 24（45） | 24（45） ✓ |

第 1 节表体实际行数也是 127。**算术没有问题，不重复计数的检查见 2.4。**

### 2.2 「80% 是读码」不准确；但「实测 24」反过来是**被高估**的那个数

先纠正提法：表自己写得更细（`CENSUS_TABLE.md:153`）——`实测` 24 行是**三列全实测**，
另有 `混合` 45 行是**至少一列有实测**，纯 `读码` 55 行。所以"至少有一处实际执行"的行是
**69/127 = 54%**，纯读码 43%，不是 80%。这一点表比任务书严谨。

**但 24 这个数本身经不起 `实测` 的字面定义。** 两位普查员写明了自己的定义
（`partials/figures-release.md:4`"我在本工作树里真跑过并观察到退出码"、
`partials/worldgen-fuzzlab.md:4`"所有「实测」都是本次跑出来的退出码"），
而 `partials/proxy-arcrecon.md:7-9` 只跑了**两次整套件**
（`proxy` → 259 passed；`arc-recon` → 82 passed），然后把 `实测` 标签**逐行**贴给了
控制位于这两个套件内部的行。核对全部 24 行：

* **10 行有真正的逐行执行证据**（命令 / 输出 / 退出码），例如
  `:16` bench/verify.py"`LADDER.md` 尾部加一行 → sha256 不符 exit 1"、
  `:28` handover_exam.py"一个答案改成 `ZZZ-nonsense` → exit 1"、
  `:57` run_qc.py --mutants"实跑 exit 1"、`:66` figures/verify.sh、`:74` reproduce.py、
  `:99`/`:100` contamination.py、`:132` cold-start-a3、`:137` make_manifest.py。
* **14 行只列了测试文件行号**（`:76`–`:82`、`:88`、`:94`、`:95`、`:97`、`:104` 等，
  全部来自 proxy/arc-recon），靠的是那两次聚合套件运行。

被引的行号我抽查后**都真实存在且内容属实**（`test_redteam.py:523`、`test_seal.py:51`、
`test_canary_schedule.py:429`、`test_hygiene.py:95` 确实断言退出码 0→1），
所以**底层主张是可靠的，被夸大的是标签**。
按 figures/worldgen 的定义，诚实的 `实测` 数是 **10–12，不是 24**。
这也解释了为什么 proxy 有 14 个实测行而 arms 只有 2、worldgen 只有 1——
**那是标注习惯的差异，不是严谨程度的差异**，不该被读成"proxy 领地查得最实"。

### 2.3 口径不一致：**削弱**，且方向是高估"有负控"

抽查跨全部六领地的 20 条 `有负控=是` 行、并逐条回去读被引用的测试代码后，
至少存在**四套口径**：

**(a) 严格构造式（正文声称的标准："负控是一个输入，不是一个断言"）——多数行属实**
逐条读码核实为真的样本：`engine-rig/tests/test_fd_ladder.py:59-96`（假 FD 二进制，
`FAKE_FD_MODE` ∈ exhausted/structurally_unsat/translate_unsat/incomplete/crash，
`:266-322` 断言每种坏行为必须抛）、`theory-compiler/tests/test_gen_lean_deadlock.py:140`
（monkeypatch 把每个 `push` 分支重写成 `=> s`，要求 `DeadlockLeanError`）、
`worldgen/tests/test_build_gate.py:48`（参数化遍历 `GATE_KEYS` 喂合成 manifest）、
`proxy/tests/test_guard.py:19`（篡改 `piles.json` → `PilesIntegrityError`）、
`ablation-arm/tests/test_verify.py:54`（篡改 `run_all.json` 四个字段，断言**具体哪几条**变红）、
`cold-start-a0/tests/test_a0.py:251`（四处源码变异必须显形为 `render_mismatch`/`unowned_pixel`）、
`exam/tests/test_worldgen_papers.py:237`（抽掉 `legal_cells` 后断言 `verdict == "wrong"`）。
**这一类站得住，我原以为 `pytest exam/tests` 属于"采信自我描述"，回读代码后收回——它是真构造式。**

**(b) "对抗性测试存在，但没有任何东西会红"——记成了 `是`（最清楚的误计）**
- `CENSUS_TABLE.md:47` `pytest battery/tests`（214 项）、`:49` `battery/metrics/*`，
  证据栏都是"`test_metrics.py` 全是手算已知输入→已知输出；`battery/audit/exploits/*`
  造出专门骗某个 metric 的合成 run 并断言确实被骗到"。
  回读代码：`battery/tests/test_metrics.py` **零个 `pytest.raises`**，全是正向手算断言；
  exploit 测试（如 `battery/tests/test_exploits_economy.py:26`）断言的是
  **`assert exploit.succeeded`——即断言 metric 确实被骗到**，三个文件共 35 处。
  这是对一个已知弱点的 characterization test，**没有任何地方会变红**。
  按严格口径这两行应为 `否` 或 `部分`。

**(c) "产物本身就是控制 / 有测试钉住行为"——也记成 `是`**
- `:117` `ablation-arm/run_exhibits.py`：`:46,57` 两个分支都无条件 `return 0`；
  被引作负控的 `ablation-arm/tests/test_exhibits.py:145` 断言的是 `main([]) == 0`
  ——**钉住"永远绿"，是负控的反面**。
- `:133` `cold-start-a3/a3pipeline/negctl.py`：证据栏写"（它就是负控）"——构造上循环，
  没有任何东西证明**它自己**能红。
- `:132` `cold-start-a3/run_all.py`：`有负控=是`，但同一行的 `能红=否(实测)`，
  证据栏还记着"把 `negctl.run_all` 打桩成 `all_caught=False, claimed_a_win=True` 仍然 `EXIT=0`"。
  给一个控制已被证明与退出码断开的闸记 `是`，与 `:113` 的 `是` 不是同一回事。
- `:63`、`:64`（worldgen/fuzzlab）：审计员**在同一格里自己写明**控制打的是别的靶子——
  "是生成器的负控，不是不变式的" / "证明「坏输入进 oracle 必须被拒」，
  不证明「坏引擎进不变式必须响」"。诚实，但 `是` 照样落进 61 里。

**(d) "有测试就算"（3 行，只出现在 arms）**
`:128` `cold-start-a0` pytest、`:139` `a0-spike` pytest 的整个证据栏就是 `56 passed，EXIT=0` /
`44 passed，EXIT=0`；`:124` `baseline-arms` pytest 的证据是"conftest 不碰真实
`spend_gate.jsonl`"——那是**测试卫生，不是负控**。这三条**事实上**可救
（套件里确有 `test_a0.py:251` 等真控制），但格子里没有证据，而且把已经记给工具行的控制
再记给套件行，正是 2.4 说的粒度重复。

**口径分布**：proxy/arc-recon 最严——`partials/proxy-arcrecon.md:85` **明确拒绝**把纯正向断言算作负控
（"`verify_piles_hash()` —— 只有正向断言……被篡改的切分文件必须 MISMATCH 这一条没有被演示过"，判 `否`）；
engine-rig/theory-compiler、figures/release 严；worldgen/fuzzlab 严但有两行自认打错靶；
exam/battery 对 `exam/*` 严、**对 `battery/*` 掉到 (b)**；arms 混用四套。

**结论：61 这个数按正文自己宣布的严格口径应落在 51–54。**
约 7 行（47、49、63、64、117、132、133）撑不过严格口径，另 3 行（124、128、139）无证据。
**方向很重要：35 这个 `否` 不受影响——普查在对自己论点有利的方向上没有多报。**

### 2.4 重复计数：分表之间没有，分表内部有粒度膨胀

**分表之间：干净。** 六份分表主表行数 arms 32 / engine-rig-theory-compiler 20 /
exam-battery 19 / figures-release 10 / proxy-arcrecon 32 / worldgen-fuzzlab 14 = **恰好 127**，
与合并表逐领地一一对应，合并时没有增删。四个重名 basename 经磁盘核对全是**不同文件**：
`verify.sh` ×4（669 / 9802 / 2095 / 3568 B）、`run_all.py` ×4（4041 / 4977 / 5328 / 10235 B）、
`guard.py` ×3（6894 / 6975 / 16564 B）、`verify.py` ×5、`campaign.py` ×2。
`CENSUS_TABLE.md:298-303` 记的两处边界声明也各只计一次。

**但 127 行只覆盖约 116 个不同文件**，因为"一行 = 什么"六人不一致：
`proxy-arcrecon.md` 把 `arc-recon/contamination.py` 拆成 **3 行**（L35/36/37）、
`arc-recon/canary.py` 拆成 **3 行**（L31/32/33），另有 `proxy/guard.py`、`proxy/spend_gate.py`、
`arc-recon/precheck.py`、`arc-recon/client.py` 各拆 2 行——32 行 / 28 个文件；
`worldgen-fuzzlab.md` 14 行 / 11 文件；而 `figures-release.md` 10 行 / 9 文件，基本一文件一行。

**后果：proxy/arc-recon 的 32 与 arms 的 32 不是同一种单位。**
proxy 数的是"保证"，figures 数的是"可执行文件"。127 是被评估的**主张数**，不是入口数。
按领地比较覆盖率（第 2 节小计表最容易被这样读）是不成立的。

### 2.5 第 3 节点名清单与第 1 节计数对不上（新发现）

第 3 节的三张点名清单不能由第 1 节的计数 1:1 推出：
「没有负控的闸门」**32 条** vs 35 个 `否`（有的条目一次捆 2–4 个入口，例如 `:222` 一条列了四个）；
「退出码撒谎」**19 条** vs 13 个 `否`（它还把 `部分` 行也拉了进来）；
「构造上不可能红的死闸」**17 条** vs 15 个 `否`。
三张清单之间还**互相重复**：`theoria-arm/harness/run.py`(:211)、
`cold-start-a0/certify/score_vs_truth.py`(:169)、`theoria-arm/armtools/salvage.py`(:184)、
`timeline.py`(:231) 各自同时出现在「退出码撒谎」和「死闸」里。
不是表的计数错，但**任何人去数条目都会得到与第 2 节不同的数**。

### 2.5 正文的强断言 vs 数据

正文（`:36-43`）说"六个领地群里同一个形状反复出现……**几乎每一例**中检测函数都是对的，
缺的是接线"。数据是 `退出码诚实=否` **13/127 = 10%**（另有 22 条不适用/未答）。
"几乎每一例"描述的是 10% 的条目。**这是修辞层面的高估**，虽然被点名的那几条个个真实。
建议正文把"the same shape recurs"换成带数字的说法。

---

## 3. 共用 worktree 的污染范围 —— 正文的分类不完整，这是本次最实的一击

正文（`:178-182`）把结论分成两类，并明确宣布：

> **不受污染：** 一切靠读源码确立的东西，以及每一条证据是**命令退出码**而非树内文件改动的 `实测` 结论。
> `contamination.py` ……、**`figures/verify.sh` 在源漂移时 exit 1**、`reproduce.py` ……——
> 这些都不依赖别的东西在往这棵 checkout 里写。

**这个二分法本身是错的：漂移闸的退出码就是树状态的函数。** 只要闸的输入是树，
另一个普查员往树里写就会直接改变它的退出码。这不是理论担忧，我找到了实例。

### 3.1 实测：三个被 `figures/SOURCES.sha256` 钉死的源，被另一个普查员改了

`figures/verify.sh` 第 4 关比对"重算的数据源哈希 == 已提交的 `figures/SOURCES.sha256`"。
我把该文件钉住的 54 个路径与本工作树 52 个已改动的已跟踪文件求交集：

```
COLLISION: cold-start-a2/artifacts/exhibit_report.json
COLLISION: cold-start-a2/artifacts/loop_ledger.json
COLLISION: cold-start-a2/artifacts/repair_report.json
```

逐个核对哈希：

| 文件 | 钉住值 | 磁盘上 | HEAD 上 |
|---|---|---|---|
| `cold-start-a2/artifacts/exhibit_report.json` | `905c6a21…` | `7e81f693…` **不符** | `905c6a21…` 符 |
| `cold-start-a2/artifacts/loop_ledger.json` | `8d711fab…` | `6cef91f3…` **不符** | `8d711fab…` 符 |
| `cold-start-a2/artifacts/repair_report.json` | `246b7415…` | `96f725d6…` **不符** | `246b7415…` 符 |

**钉住值与 HEAD 完全一致，与磁盘不一致。** 也就是说：在干净树上第 4 关是绿的，
现在它是红的，**红的唯一原因是 `arms` 普查员在这棵共用工作树里跑了
`cold-start-a2/run_all.py`**（`partials/arms.md` 自述留下 12 个已跟踪文件改动，
`git status cold-start-a2/` 实测正是 12 个）。

这正是任务书假设的形状，而且它落在正文亲手划进"**不受污染**"那一类的入口上。
本次没有酿成错误结论，纯属侥幸：`figures/verify.sh` 在**第 1 关**就因 fig06 的 `E-08`
退出了，根本没走到第 4 关（`CENSUS_TABLE.md:335` 自述）。
**换句话说，正文的分类之所以看起来成立，是因为另一个缺陷提前中止了脚本。**

### 3.2 顺带澄清一条普查员自己的不确定（结论对普查有利）

`CENSUS_TABLE.md:336`：

> `figures/verify.sh` 在 master 上当前是红的……我不确定这个红是 master 本身就有，还是本工作树被并发会话改动所致。

**可以确定：是 master 本身的缺陷，不是污染。**
`git status cold-start-a0/THEORIZE_LOG.md figures/` 为空（未改动），
且 `git show HEAD:cold-start-a0/THEORIZE_LOG.md | grep -c E-08` = 2。
E-08 在提交里，第 1 关的红是真的。这一条普查员多虑了，可以放心引用。

### 3.3 还有一类正文没数到：**读码结论也被污染**

正文说"一切靠读源码确立的东西"不受影响。但本工作树里有 **10 个生成物
`theory/generated*/theory.md` 被改写**（`cold-start-a0/a2/a3` 各若干），
它们是"四种共导出形式"之一，是会被人**读**的产物。
`partials/arms.md` 就报告了"`theory/generated*/theory.md` 都长出一整节 How a Turn Works，
提交在库里的那份是旧生成器的输出"——这是一条**读**出来的结论，而它读的是一棵
被并发写过的树。正文把它归进"不受污染"，不成立。

（公平地说：本次每个普查员的改动基本都被其**本人**正确认领了——
`cold-start-a0` 3 / `a2` 12 / `a3` 15 / `worldgen` 10 / `ablation-arm` 10 / `exam` 1，
合计 52，与 `arms.md` 自述的 3/12/14 及各表自述吻合。所以归因错乱没有实际发生，
`engine-rig-theory-compiler.md` 那份"51 个文件不是我改的"的警报，答案是"是别人改的，
而别人认领了"。**正文对这一点的处理是对的，我推不翻。**）

### 3.4 正确的分类应当是

不是"退出码 vs 树改动"，而是：

* **不受污染**：闸的输入完全在进程内构造（临时目录、fixture、注入）——如 `contamination.py`
  那两次复现、`reproduce.py` 的 `OUT` 指向 scratchpad。
* **受污染**：闸的输入是**工作树本身**——一切漂移闸、确定性闸、`--check` 闸、
  哈希钉闸（`figures/verify.sh` 第 3/4/6 关、`refresh_manifest.py --check`、
  `verify_readonly.py`、`build_theory.py --check`），以及一切读生成物的结论。

---

## 4. 三个"好样板"核实

### 4.1 `figures/check_coverage.py --self-test` —— 推不翻（实测）

全部属实，且比正文说的更强。`--self-test` 在 `:283`；`:224` 把发现规则收窄为
`_PRE_P8_PATTERN = "pilot_????-*.json"`，`:252-260` 重跑发现，`:276-278` 在 `finally` 里还原；
`:269-275` **点名两个必须被抓到的 run**，抓不到就 `NEGATIVE CONTROL FAILED`；
`:285-288` `return 1`。还防了"空重建"——收窄后若不是恰好 4 个 roll-up 就直接失败（`:262-267`）。
挂在 `figures/verify.sh:205`，**跑在真检查（`:211`）之前**。实跑 exit 0 且确实报出两个 victim。

唯一吹毛求疵：它重建的是 pre-P8 的**发现规则**，不是"整棵 pre-P8 的树"。代码自己在 `:218-223`
说明了这一点。正文是在引 `verify.sh` 的原话，不算失实。

### 4.2 `proxy/` 红线套件 —— **推翻**（实测）

正文（`:78`）：

> RED-01…46，**每一条**都断言一个特定攻击被挡住，含短 id 形式。259 个 proxy 测试全绿。
> ——"sound, and the best-tested thing in the repository"

核实：

* "259 个测试全绿"：**准确**。`pytest --collect-only -q` 恰好 259。
* "构造式而非确认式"：**准确**。42 个测试函数里约 22 个是端到端（起 loopback `Sink`、
  真 `env_proxy`/`model_proxy`、经 HTTP 发攻击、断言上游没收到），约 19 个是把恶意输入喂给真组件
  （`guard.check_request(...)["decision"] == "deny"`、对真账本写入器 `pytest.raises`、
  `reconcile_run(...)["verdict"] == "FAIL"`）。基本没有"断言一个常量"的。
  最弱的是 `test_red18`（`:474-484`），唯一不带 `tmp_path`、不起 proxy 的，首断言只是
  `split["a"] + split["b"] != secret`。
* **"RED-01…46 每一条都是一个测试"：假。**
  `proxy/REDTEAM.md` 里 46 个 id 连续无缺号；`test_redteam.py` 只有 **42 个 `def test_red*`**。
  **RED-24 / 25 / 26 / 27 四条没有任何可执行测试**——它们的测试体被压成了
  `proxy/tests/test_redteam.py:564-583` 的一段注释，parametrize 表格还以散文形式留在里面
  （`# ... game_id=ls20-9607627b` / `# application/x-www-form-urlencoded ...`），
  紧接着的下一个 `def` 就是 `test_red28`。全 `proxy/tests/` 树内搜不到 `%2F`、
  urlencoded body、unicode 混淆字符、`/api/scorecard/<sealed>` 任何一例。

  这四条里 **RED-24 和 RED-25 被红队自己评为 critical，且都属于封存护栏类**：
  RED-24 是"路径里任意位置的封存 id（含 `%2F`）原样转发"，
  RED-25 是"guard 只看 `json.loads(raw)`，解析失败就什么都看不见，而 `_forward` 照发原始字节"。

  `git log -S "def test_red24"` **无任何提交**，且 `test_redteam.py` 只有一次提交（`2d00f25`）——
  这四条**从来没被写过**，不是被删掉的。
  而 `proxy/REDTEAM.md:16-17` 写着"Every one of them is a test in `proxy/tests/test_redteam.py`"，
  `:385-388` 写着"All 46 attacks are now blocked … 没有 xfail 标记残留"。
  **"没有 xfail"是真的，但原因是那四条测试不存在，而不是它们被修好了。**

**这一击的分量**：正文用 proxy 套件当"你构造 X、在 X 上跑闸、断言非零退出"的**标杆**，
而恰恰在最该构造的两条 critical 封存攻击上，没有人构造 X。
三层表里"interception 层 sound"这一格应当改成"42/46，缺的两条是 critical 封存类"。
——而这**加强**了普查的总论点，只是普查把这个例子放错了栏位。

### 4.3 `exam/` 标定 —— 削弱（读码）

大体属实：`--calibrate` 在 `exam/tools/run_exam.py:91`；预注册假被试带正文说的确切阈值，
`exam/grading/calibration.py:72-84` 明确标注 "Pre-registered"：
`("heldout","oracle"): Band(1.0, 1.0, ...)`、`("heldout","null"): Band(0.0, 0.0, ...)`，
`handover`/`adaptation`/`verdict` 三卷同样；退出码接线在 `run_exam.py:126`
`return 0 if payload["calibrated"] else 1`，且 `--calibrate` 走同一条 `run()` 路径，不绕过；
是 `exam/verify.py:88` 的 gating 阶段。注入故障是**提交在库的产物**而非散文：
`exam/grading/selftest.py:482-491` 八个真 monkeypatch，检测矩阵 `:535-574`，
结果落在 `exam/artifacts/selftest.json`。

**两处应当收紧**：
1. 提交的矩阵显示 **8 个注入故障里 7 个**导致标定失败，`truncates_partial` **不会**。
   而且 exam 自己把这钉成了刻意发现——`exam/tests/test_selftest.py:113-117` 断言
   `calibration["calibrated"] is True`，并附注"如果现在能抓到了，是发现变了，
   要改注释而不是放松这条断言"。诚实，但正文该写"8 个里 7 个"。
2. 故障是在 `run_selftest` 下注入的，不是在 `run_exam --calibrate` 进程里。
   观测点是 `calibrate_all()`——确实是驱动 `run_exam` 退出码的同一个函数，机制成立，
   但正文"observed turning `run_exam --calibrate` red"的**入口名写松了**。

---

## 5. 论文主张核实 —— **推翻，这一节是稻草人**

正文（`:136-141`）称三类论文主张"backed by 'the verify script is green'"。

**论文全文 2512 行，`verify` 只命中一次，且是无关的另一个意思**：
`papers/phase1-workshop/PAPER.md:726`（= `sections/04_a1.md:60`）里
"producer's own `verify()`" 指的是 Lean 证书生产者的一个函数。
`verify.sh` 在 `sections/`、`PAPER.md`、`PROVENANCE.md`、`README.md`、`OPEN_ITEMS.md` 里
**零命中**。整个 `papers/` 树里唯一一次提到 `figures/verify.sh` 的是**规划文档** `OUTLINE.md:62`，
不是稿件。论文里所有 "green/GREEN"（`PAPER.md:181,397,504,573,606,868,892,895,…`）
指的都是世界模型的 certify / Lean / replay 判定，没有一处是 `verify.sh`。

三条主张论文**确实都做了**，但每一条压的都是**具名产物**，不是绿灯：

| 主张 | 论文实际引什么 |
|---|---|
| 产物确定性 | `PAPER.md:1297-1302`：两次重算逐字节一致 + `battery/artifacts/capability_spectrum.json` 的 `provenance.input_digests`。**并且紧接着 `:1304-1307` 自打折扣**："确定性*测试*跑的是合成 fixture，不是已发布产物"（引 `battery/DECISIONS.md` D-B-008） |
| 封存零接触 | `PAPER.md:1918-1923`：**明确拒绝用护栏的意见**——"manifest 带的是记录的字节扫描，而不是护栏自称挡了什么"，引 `theoria-arm/runs/20260728T015354Z-g50t-first-contact/MANIFEST.json` 的 `sealed_game_ids_found: []` / `sealed_pile_untouched: true`。`:252-253` 又补了限制，§10.1（`:2089-2095`）记 INC-BA-001 九局知识污染 |
| 图与源一致 | `PAPER.md:417-420`、`:428-430`：引**第二份独立实现**与 `papers/phase1-workshop/figures/PARITY.md`，而且**报告的是一处分歧**而非一片绿。`:494-497` 更是反着来：某个数不在源登记表里、不被哈希，于是那格**留空**，而不是印一个 0 |

论文自己写明的证据规则（`PAPER.md:35-44`）是**逐条引产物路径**，由
`PROVENANCE.md` 索引、`CITECHECK.md` 与 `REVIEW.md` 审计——**不是一个脚本**。

**判决：这一节攻击的是论文没有的依赖。** 有意思的是，论文引的那份封存证据
（`theoria-arm` 的字节扫描）恰恰**自带构造式负控**（`tests/test_arm.py:607-608`）——
即普查标准下的合格品。这一节应当整节重写或删除。

---

## 6. 诚实的分母

127 里有相当一部分入口，问"它有没有负控"是**范畴错误**。逐条清点后我的分类：

**(a) 不是闸，是工具/报表/生成器/探索脚本（18 条）**
`engine-rig/bench/__main__.py`(3)、`engine-rig/tools/p13_fd_dividend.py`(5)、
`fixtures/generate_all.py`(7)、`exam/tools/archive_run.py`(30)、`battery/docs.py`(36)、
`battery/metrics/*`(37)、`worldgen/qc/diagnose_miner.py`(47)、`fuzzlab/minimize.py`(53)、
`figures/build_all.py`(55)、`proxy/spend_gate.py __main__`（自述"池子报表"）(77)、
`proxy/tools/upgrade_ledger.py`(79)、`proxy/cost.py`/`runner.py`（库）(80)、
`arc-recon/recon.py`/`probe_stickiness.py`/`precheck_resume.py`（侦察）(95)、
`theoria-arm/armtools/salvage.py`/`timeline.py`(99)、`ablation-arm/run_exhibits.py`(105)、
`baseline-arms/harness/campaign.py`/`run_campaign.py`（活体战役运行器）(111)、
`a0-spike/probes/semantics_probe.py`(126)、`figures/manifest.py`(58)。

**(b) 根本不存在的入口（1 条）**
第 39 行 `battery 的「一条命令总闸」`，证据栏原文就是"**不存在**"。它不该占分母。

**(c) pytest 套件本身（11 条）**
`engine-rig`(6)、`theory-compiler`(17)、`exam`(31)、`battery`(35)、`worldgen`(46)、
`theoria-arm`(100)、`baseline-arms`(112)、`cold-start-a0`(116)、`a2`(119)、`a3`(123)、`a0-spike`(127)。
套件**就是**负控的载体；问"这个套件有没有负控"只有在变异测试的意义上才成立，
而没有一个普查员是按变异测试判的。

**(d) 单条测试函数被当成入口（3 条）**
`fuzzlab/tests/test_battery.py::test_short_campaign_finds_no_violation`(50)、
`test_oracles.py`(51)、`test_distinct_indices_give_distinct_worlds`(52)。
（其中 50 值得保留——"跑了一小会儿没发现违例"正是典型的空绿灯。）

另外，2.4 已经指出 **127 行只覆盖约 116 个不同文件**（proxy 把 `contamination.py`
拆成 3 行、`canary.py` 拆成 3 行等），所以分母在"文件"意义上还要再打一折。

**我认为诚实的分母：约 94**（127 − 18 − 1 − 11 − 3 = 94），
其中约 7 条流水线运行器（`tools/run_all.py`、`run_battery.py`、`harness/run.py`、
`cold-start-a0/a2/a3 run_all.py`、`a0-spike/run_a0.py`）介于闸与运行器之间，
按严格口径还可再减，下限约 **87**。

同样地，**"35 个入口没有负控"应降到约 23**：那 35 条里，
`p13_fd_dividend.py`、`exam/tools/archive_run.py`、`fuzzlab/minimize.py`、
`figures/build_all.py`、`figures/manifest.py`、`proxy/spend_gate.py __main__`、
`theoria-arm/armtools/salvage.py`/`timeline.py`、`theoria-arm/harness/run.py`、
`baseline-arms/harness/campaign.py`、`theory-compiler/conftest.py`、
`theory-compiler/tools/handover_exam.py mark`、`cold-start-a2/run_all.py`
这 12 条不是需要负控的验收闸。

**但这不救结论。** 剩下的 23 条里仍然坐着
`arc-recon/redact_ledger.py --check`（`verify.sh` 的一整步）、
`arc-recon/client.py` 的密钥密封、`arc-recon/cut_piles.py` 的拒绝二次切分、
`release/reproduce.py`、`exam/verify.py::_determinism`、
`worldgen/verify.py`、`fuzzlab/verify.py`、两个 `verify_readonly.py`、
`baseline-arms/harness/merge_ledger.py --check`、`transport_ab.py::assert_not_frozen`。
**分母该缩，结论的方向不变，只是没有"127 里 35 个"听起来那么惨。**

---

## 我另外发现的问题

1. **封存审计的覆盖洞**（详见 1.4）——`OTHER_LEDGERS` 硬编码 3 条路径，
   树里另有 **16 份**真实调用账本（`theoria-arm/runs/*/ledger.jsonl` 8 份、
   `baseline-arms/out/shards/*.jsonl` 8 份）从未被扫。其中 4 份还被
   `figures/SOURCES.sha256:14-17` 当作图管线的正式输入源钉着。
   **这比正文的头条更严重，也更难修。**

2. **`proxy/REDTEAM.md` 的自述失实**（详见 4.2）——`:16-17` 与 `:385-388` 声称
   46 条攻击每条都是一个测试、没有 xfail 残留。实为 42 条，缺的 4 条含 2 条 critical
   封存类，且**自首次提交起就不存在**。这是一份"文档里的绿灯，后面没有东西"，
   与普查的主题完全同构——普查却把它引为正面样板。

3. **正文的复现方法弱于它本可以做的**——`partials/proxy-arcrecon.md:110` 的复现是
   **改源码常量** `OTHER_LEDGERS`。普查的自定标准是"负控是一个输入，不是一个断言"；
   改常量既不是输入也不是断言，是改被测物。我用不碰源码的方式复现了同一结论（1.1），
   建议正文换成这个证据。

4. **`monitor/ci_merge.py` 的按目录选闸是真实空隙**（1.3 第 2 条）——
   合并闸只跑分支触碰到的目录的套件。跨领地不变量（"任何账本里都没有封存 id"）
   天然不属于任何单个目录，因此可以被一个不碰 `arc-recon/` 的分支绕过。
   这类不变量需要一道**无条件**执行的闸。

---

## 我打不倒的（以及为什么）

* **`contamination.py:338` 的退出码只反映切分哈希** —— 实测复现，且用了比原普查更干净的方法。
  这条是真的，值得修，正文点名正确。
* **`verify.sh` 的 `step()` 只看退出码** —— 读了 `:18-28`，正文没写错。
* **表内算术** —— 六领地小计逐列相加与合计完全吻合，127 行也对得上。找不到毛病。
* **分表之间的重复计数** —— 六份分表行数相加恰为 127，四个重名 basename
  经磁盘核对全是不同文件，边界处两次单向声明各计一次。合并过程没有增删。
  （分表**内部**的粒度不统一是另一回事，见 2.4，那不是重复计数。）
* **被引用的测试行号** —— 抽查 `test_redteam.py:523`、`test_seal.py:51`、
  `test_canary_schedule.py:429`、`test_hygiene.py:95` 等，全部真实存在且内容与证据栏相符。
  普查的**事实层**很扎实；被我打掉的都是**推论层**和**标签层**。
* **`figures/check_coverage.py --self-test`** —— 实跑通过，接线完整，还防了空重建。
  这是全仓最好的负控，正文引对了。
* **worldgen 工作样例** —— `worldgen/out/qc/QC.json` 的 `family_verdict.pass = False`、
  `QC_MUTANTS.json` 的 `mutant_verdict.pass = False`（实测读取），
  而 `worldgen/build.py:354-357` 印 `green` 后 `return 0`。正文的简写（"both carry `pass: false`"）
  在嵌套一层的意义上准确。这两个文件本身不在本工作树的改动清单里，读数稳定。
* **共用 worktree 的归因错乱没有实际发生** —— 52 个改动文件按领地拆开
  （a0 3 / a2 12 / a3 15 / worldgen 10 / ablation-arm 10 / exam 1），与各分表自述吻合，
  每个普查员都认领了自己的那份。`engine-rig-theory-compiler.md` 那声"51 个不是我改的"警报，
  答案是"别人改的，而别人认了"。正文对这一点的处理是对的。
* **"负控是一个输入，不是一个断言"这条方法论本身** —— 我试着找反例（有没有哪种闸
  天然只能靠断言而不能靠构造输入来演示），没找到。冻结哈希、只读树、
  确定性、漏题、封存护栏，每一类都能构造出坏输入。这条标准立得住。

---

## 给 RES-3 的三条建议

1. **头条必须改写。** 现在的写法（"会绿"）是可证伪的，而且已被证伪。
   改成"冗余链路上的一条断线 + 一个覆盖洞"既准确，也依然值得修。
   照现状发论文或据此给别的领地派单，第一个跑一遍 `verify.sh` 的人就会推翻它。
2. **第 5 节（对论文的代价）整节删或重写。** 论文没有那个依赖。
3. **第 4.2 的样板换栏位。** proxy 套件不该当"好样板"，它应该进"点名清单"：
   REDTEAM.md 声称 46/46，实为 42/46，缺的两条是 critical 封存类。
