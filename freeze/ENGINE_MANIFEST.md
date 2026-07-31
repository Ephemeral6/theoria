<!-- generated-from: 45cd6ebd0426f94c19b1fb4a109c2eac46aa5322 -->
# ENGINE_MANIFEST —— 冻结清单第 5 项：引擎清单与版本

**生成物。不要手改。** 由 `python freeze/build_engine_manifest.py` 写出；`--verify` 从 git 重算每一个哈希并逐行报漂移。

`Theoria.md:368` 第 5 项逐字是「**引擎清单与版本**」。本文是那份清单。它的存在理由是 `MANIFEST_DRAFT.md` §5 的 ⛔：在此之前，名册以散文形式存在于 `engine-rig/STATUS.md`，能力与边界表存在于 `engine-rig/ENGINE_TABLE.md`，而**版本一处都没有**。

## 哈希纪律

**本文全部哈希都是 `git rev-parse HEAD:<path>` 取的 git tree/blob sha1，没有一个取自工作树文件。** 理由是实测出来的，见 `MANIFEST_DRAFT.md`「哈希纪律」：仓库根没有 `text`/`eol` 规则，同一个文件在两个 checkout 里一个 CRLF 一个 LF，于是工作树哈希跨 checkout 不可复现——而失败模式是最坏的那种：`--verify` 会对一棵其实相同的树报红，撞上的人会去重生成清单把它弄绿。

`engine-rig/.gitattributes` 恰好钉了 LF，所以本子树本不会栽在这上面。规则照样遵守：一份因为某个子目录的性质才正确的清单，是靠运气正确的。

`git rev-parse HEAD:<path>` 读的是 **HEAD 而不是工作树**，所以即使 checkout 是脏的，这些哈希描述的仍是提交。这既是特性也是陷阱，因此 `engine-rig/` 的脏状态由生成器打在 stdout 上，**不写进本文**——写进来会让一次无关编辑看起来像哈希漂移。

## 0. 覆盖表 —— 每个引擎的版本钉住了吗

| # | 包 | 版本串 | 里程碑标签是否仍描述这些字节 | 结论 |
|---|---|---|---|---|
| 1 | `mdl_segmenter` | ⛔ 无 | ⛔ 不同 (`engine-rig-m2-mdl`) | ⛔ 未钉版 |
| 2 | `cegis_miner` | ⛔ 无 | ✅ 同 (`engine-rig-m3-cegis`) | ⚠ 仅标签，无版本串 |
| 3 | `zero_space` | ⛔ 无 | ⛔ 不同 (`engine-rig-m4-zerospace`) | ⛔ 未钉版 |
| 4 | `lp_potential` | ⛔ 无 | ⛔ 不同 (`engine-rig-m5-lp`) | ⛔ 未钉版 |
| 5 | `fd_adapter` | ⛔ 无 | ⛔ 不同 (`engine-rig-m6-fd`) | ⛔ 未钉版 |
| 6 | `probe_frontier` | ⛔ 无 | ⛔ 不同 (`engine-rig-m7-probe`) | ⛔ 未钉版 |
| 7 | `deadlock_carver` | ⛔ 无 | ⛔ 不同 (`engine-rig-m9-deadlock-ic3-probe`) | ⛔ 未钉版 |
| 8 | `ic3_pdr` | ⛔ 无 | ✅ 同 (`engine-rig-m9-deadlock-ic3-probe`) | ⚠ 仅标签，无版本串 |

**八个包，零个版本串，2/8 的里程碑标签仍与 HEAD 字节相同。**

扫描范围与结果，逐字：`git grep -E '__version__|SCHEMA_VERSION|ENGINE_VERSION|VERSION\s*=|version\s*=' HEAD -- 'engine-rig/*.py' 'engine-rig/*.toml' 'engine-rig/*.cfg'`，覆盖 **217** 个受版本管理的文件，命中 **5** 行：

* `engine-rig/bench/toolchain.py:59:_VERSION = re.compile(r"^(Fast Downward .+)$", re.M)`
* `engine-rig/bench/toolchain.py:130:        version = _VERSION.search(text)`
* `engine-rig/tools/survey_numbers/lp_incomplete.py:1640:            "numpy": numpy.__version__,`
* `engine-rig/tools/survey_numbers/lp_incomplete.py:1641:            "scipy": scipy.__version__,`
* `engine-rig/tools/survey_numbers/lp_incomplete.py:1721:            % (scipy.__version__, numpy.__version__, *sys.version_info[:3]),`

命中的两行都是 Fast Downward 自己的版本管道，**不是任何引擎的版本**。`engine-rig/` 里没有 `pyproject.toml`。所以：

> **⛔ 缺 5-b：八个引擎的版本串全部缺失，由 engine-rig 赛道在 `engine-rig/engines/<pkg>/__init__.py` 补（或在 `engine-rig/common/` 立一个单一来源）。**

**这个 code 是故意重用的，不是新开一个缺口。** `MANIFEST_DRAFT.md` §5 已经declare 了 `⛔ 缺 5-b「引擎带名字，不带版本」`；本文是同一个缺口的**实测**（扫描范围、命中行、里程碑标签的反证），因此在这里是一处**引用**而不是第二次声明——`freeze/residuals.py` 拒绝同一个 code 被声明两次，而「它被修好了吗」有两个答案正是它要防的事。行首刻意留了 `> `，所以 `residuals.py` 的 `DECL`（要求行首 `**⛔`）不会把它读成声明，而 `ANY_MARK` 仍然能看见它还开着。

在补上之前，本条唯一可引的版本把手是 **git tree sha1**（第 1 节）与**冻结提交本身**。里程碑标签**不是**把手：上表 6/8 的包在它自己的标签之后动过，所以「按 m8 冻结」或「按 m9 冻结」都盖不住 `engines/` 里的字节（`MANIFEST_DRAFT.md` 待办 5-d 的可执行形态）。

## 1. 名册 —— 八个包，按包路径为键

**键是包路径，不是 `ENGINE` 常量。** 理由见第 2 节：两个包声明的是别人的名字，按枚举为键的清单会把八行静默并成六行。

| # | 包路径（模块路径） | tree sha1 @HEAD | 文件 | 枚举标签 `ENGINE` | `PRODUCER` | 版本串 | 专属测试 |
|---|---|---|---|---|---|---|---|
| 1 | `engine-rig/engines/mdl_segmenter` | `bd16096df21e7bc01e435b04d6aadcdba38bdf73` | 4 | `mdl_segmenter` | *（未设）* | ⛔ 无 | `test_mdl_segmenter.py` 14 条 |
| 2 | `engine-rig/engines/cegis_miner` | `6d5e00a93c372391eaf283025f0d268a13e8e2fc` | 4 | `cegis_miner` | *（未设）* | ⛔ 无 | `test_cegis_miner.py` 16 条 |
| 3 | `engine-rig/engines/zero_space` | `78ead9dd3e4874affe73333f171a05400da7cd25` | 4 | `zero_space` | *（未设）* | ⛔ 无 | `test_zero_space.py` 15 条 |
| 4 | `engine-rig/engines/lp_potential` | `f29152f2e95b18472d776df6e658d099a0f387a1` | 3 | `lp_potential` | *（未设）* | ⛔ 无 | `test_lp_potential.py` 26 条 |
| 5 | `engine-rig/engines/fd_adapter` | `4995715504229251a12ce947f40c28186eba6c9a` | 9 | `fd_adapter` | *（未设）* | ⛔ 无 | `test_fd_adapter.py` 18 条 |
| 6 | `engine-rig/engines/probe_frontier` | `f8e16e9b79b5780b43438798cea2fd05bf97fd51` | 6 | `probe_frontier` | *（未设）* | ⛔ 无 | `test_probe_frontier.py` 14 条 |
| 7 | `engine-rig/engines/deadlock_carver` | `d59ce5bfa1e873141b18d7e085c95615c4d76ecd` | 4 | `fd_adapter` | `deadlock_carver` | ⛔ 无 | `test_deadlock_carver.py` 19 条 |
| 8 | `engine-rig/engines/ic3_pdr` | `ea6ee43f4a2c29a4bdd59980a1f5febe939b908a` | 5 | `lp_potential` | `ic3_pdr` | ⛔ 无 | `test_ic3_pdr.py` 16 条 |

`engines/` 整个目录树：`01c562e7a2b767a790be4e4159013f2914c67255`（`engine-rig/engines`，40 个受版本管理的文件）。

「专属测试」只数 `engine-rig/tests/test_<pkg>.py` 里的 `^def test_`。第 3 节另列**引用**该引擎但属于别人的测试文件，**不计入**——按「提到它的文件」求和会让 `mdl_segmenter` 拿到 70 条（4 个文件），其中三份是别的引擎拿它当输入用的测试。一份高报自己覆盖率的清单，正是整套工具要防的那种假话。

**推导规则与它的界限，写明以便反驳**：「引用」= blob 里出现 `engines.<pkg>` 或 `from engines import … <pkg>`，即**模块级引用**。只按名字提到它的测试**不算**——例如 `test_integration.py:137` 以 `by_producer["ic3_pdr"]` 检查发射流、`test_engine_table.py:52-75` 整段盯着 `ic3_pdr` 那一行，两者都不导入该模块，因此都不出现在它的引用表里。这是「谁 import 了它」的清单，不是「谁间接练到了它」的清单。

逐文件 blob sha1 在第 10 节的机读块里，`--verify` 逐行核对。

## 2. 枚举撞名 —— 为什么这份清单不能按 `ENGINE` 为键

* `ENGINE = "fd_adapter"` 由 **2** 个包声明：`fd_adapter`、`deadlock_carver`。
* `ENGINE = "lp_potential"` 由 **2** 个包声明：`lp_potential`、`ic3_pdr`。

逐字，从各自的 `__init__.py` blob 里读出来的（不是 import 出来的）：

```
engine-rig/engines/deadlock_carver/__init__.py:43  ENGINE   = "fd_adapter"   # the frozen enum; see D-018
engine-rig/engines/deadlock_carver/__init__.py:44  PRODUCER = "deadlock_carver"
engine-rig/engines/ic3_pdr/__init__.py:51  ENGINE   = "lp_potential"   # the frozen enum; see D-018
engine-rig/engines/ic3_pdr/__init__.py:52  PRODUCER = "ic3_pdr"
```

冻结枚举 `ENGINES` 定义在 `engine-rig/common/candidates.py:27-34`，恰好六个名字。D-018 的裁定是：新引擎不改冻结契约，而是「emit under the enum member whose work it extends」，真实身份记在 `payload.producer`。

**后果，对任何消费者都成立：「八个引擎、八个标签」读不出来。**按 `engine` 分行的直方图恒为六行——`run_all` 的 `by_engine` 就是这么写的，而且 D-018 把这一点列为优点。所以本清单按包路径为键，把枚举标签作为一个**可能撞名的独立列**。

## 3. 每个引擎提出/证明什么，以及它的常设保留

「提出/证明」一行是判断，与保留一起作为字面量存在生成器里，所以可以被争论。保留里的每个数字都引自 `engine-rig/ENGINE_TABLE.md`——那是生成的、探针支撑的、由 `engine-rig/tests/test_engine_table.py` 盯住的，于是这些数字有一个**不是本文**的主人。

### 1. `mdl_segmenter`  ·  枚举标签 `mdl_segmenter`

* **提出/证明**：提出 object_hypothesis：轨迹 → 对象与事件，按比特计价，描述最短者胜。不证明任何东西。
* **tree sha1**：`bd16096df21e7bc01e435b04d6aadcdba38bdf73`
* **版本串**：⛔ 无。里程碑 `engine-rig-m2-mdl` 的树 **不等于** HEAD。
* **专属测试文件**：`engine-rig/tests/test_mdl_segmenter.py` — `^def test_` **14** 条
* **另有 3 个测试文件引用它**（不计入上面的条数——它们是别的引擎的测试，把这个引擎当输入用）：
  * `engine-rig/tests/test_cegis_miner.py`（该文件自身 16 条）
  * `engine-rig/tests/test_probe_frontier.py`（该文件自身 14 条）
  * `engine-rig/tests/test_tool_failure_is_not_truth.py`（该文件自身 26 条）
* **常设保留**：**几何精确不等于对象正确。** 像素几何是精确的（506,302 格 0 错），但*分解*在 300 个世界里错了 127 个（最坏 4 个真实对象报 40 条轨迹），只有 173/300 逐帧与 ground truth 相符；`masks_partition_the_foreground` 在全部世界通过，因为「动体与障碍粘成一团」仍是一个合法划分。非均匀对象的逐格颜色根本不发布：18,118 格（3.5785 %）不可恢复。18 个发布字段里有 8 个没有任何不变量断言。

### 2. `cegis_miner`  ·  枚举标签 `cegis_miner`

* **提出/证明**：提出 rule_hypothesis：对精确账本做反例引导的带卫式规则合成，并给出证据尚不能分离的最小卫前沿。
* **tree sha1**：`6d5e00a93c372391eaf283025f0d268a13e8e2fc`
* **版本串**：⛔ 无。里程碑 `engine-rig-m3-cegis` 的树 **等于** HEAD。
* **专属测试文件**：`engine-rig/tests/test_cegis_miner.py` — `^def test_` **16** 条
* **另有 1 个测试文件引用它**（不计入上面的条数——它们是别的引擎的测试，把这个引擎当输入用）：
  * `engine-rig/tests/test_probe_frontier.py`（该文件自身 14 条）
* **常设保留**：**提升规则（lifted）是边界。** 149 条里 104 条带的卫是 `["act==?dir"]`，**91/149 在承诺的移动并未发生的转移上开火**（342 行），**131/149** 发布的 `applicable` 不能由它自己的卫推出。`transitions_from_segmentation` 默认取 `tracks[0]`，于是 **72/193 个世界挖的是一块静止障碍**。4 个及以上文字的最小卫、以及除网格外的任何世界族，均 **边界未测**。20 个发布字段里 14 个没有不变量断言。

### 3. `zero_space`  ·  枚举标签 `zero_space`

* **提出/证明**：提出 invariant：观测差分向量的 GF(2) 零空间 → 证据支持的线性守恒律，分为编码局部与世界层。
* **tree sha1**：`78ead9dd3e4874affe73333f171a05400da7cd25`
* **版本串**：⛔ 无。里程碑 `engine-rig-m4-zerospace` 的树 **不等于** HEAD。
* **专属测试文件**：`engine-rig/tests/test_zero_space.py` — `^def test_` **15** 条
* **另有 3 个测试文件引用它**（不计入上面的条数——它们是别的引擎的测试，把这个引擎当输入用）：
  * `engine-rig/tests/test_heldout.py`（该文件自身 17 条）
  * `engine-rig/tests/test_solver_status_bit.py`（该文件自身 15 条）
  * `engine-rig/tests/test_tool_failure_is_not_truth.py`（该文件自身 26 条）
* **常设保留**：**只在它自己声明的量词下成立（D-003）。** 量词是「观测到的轨迹」；把它加强成「世界的全部合法转移」，**200 个世界里 13 个的 102 条律不再成立**。留出验证（E17）：信息量非零的那一刀（整条操作留出）下律成立率 **13.1 %**；同时报出的 **100.0 %** 是一个**被证明为空洞的对照**（转移级留出下 0/2160 行是新的）。`scope` 声称了一种它从未核验的来源：1271 条 `cell_local` 里 **329 条**支撑集是真子集，且其中 **0 条**落在本引擎自己的编码律张成里。11 个发布字段里 5 个没有不变量断言。

### 4. `lp_potential`  ·  枚举标签 `lp_potential`

* **提出/证明**：证明 invariant + heuristic：用有理数精确验证的线性 pagoda 证明目标不可达，同一组权重兼作可采纳启发。
* **tree sha1**：`f29152f2e95b18472d776df6e658d099a0f387a1`
* **版本串**：⛔ 无。里程碑 `engine-rig-m5-lp` 的树 **不等于** HEAD。
* **专属测试文件**：`engine-rig/tests/test_lp_potential.py` — `^def test_` **26** 条
* **另有 7 个测试文件引用它**（不计入上面的条数——它们是别的引擎的测试，把这个引擎当输入用）：
  * `engine-rig/tests/test_heldout.py`（该文件自身 17 条）
  * `engine-rig/tests/test_interop.py`（该文件自身 13 条）
  * `engine-rig/tests/test_lp_incomplete_predicates.py`（该文件自身 15 条）
  * `engine-rig/tests/test_pagoda_reader.py`（该文件自身 25 条）
  * `engine-rig/tests/test_recheck.py`（该文件自身 47 条）
  * `engine-rig/tests/test_solver_status_bit.py`（该文件自身 15 条）
  * `engine-rig/tests/test_tool_failure_is_not_truth.py`（该文件自身 26 条）
* **常设保留**：**CLAUDE.md 的「sound but incomplete」两句都成立，但作为冻结条目它不完整——补齐的两条都会咬封存战役。**
  1. **不完备是真的，且有量级。** `0111` 确实不可解而无线性 pagoda 证明它（D-014，用测试而不是注释断言）；E11 在 N=3000 上量到**639/2189 = 29.2 %** 的真不可达世界拿不到证书。流传的 **46.6 %** 是 N=500 下的*无证书率*，不是不完备率，高估约 2×。
  2. **「sound」只在它被交付的移动表之上成立。** E17 每次留出一条 jump 几何：回来的 1408 张证书里只有 **26.4 %** 在被留出的几何上仍满足 `inv_closed`，**58 张对完整移动集下的 BFS ground truth 是彻头彻尾的假**。最小见证可手算：`peg4`、目标 `0100`、起点 `0011`、留出 `jump(3,2,1)`——三个条件在有理数下全部精确为真，而 fixture 自己手验的表说该目标**可达**。发射门 `premises_against_graph` 拦不住：交给它一个「部分证据调用者真正持有」的图时，**1408 张全部发射，含那 58 张假证书**，每张都带着 `holds: true` 与 `sound_over_graph: true` 进入共享候选流。**臂按构造就是一个部分证据调用者。**
  3. **第三条限定，写在代码里**（`potential.py:282-289`）：`no_linear_pagoda` 是 `|w_i| <= bound` 盒子**之内**的不可行；`bound=10` 是求解器参数而非 pagoda 定义的一部分，E11 在 3000 个世界里找到 1 个 pagoda 落在盒外。另有 **638** 个世界的「不存在线性 pagoda」只是 HiGHS 返回的浮点不可行，**没有精确 Farkas 对偶**——那是求解器的说法，不是证明。
  4. 可用之处也多半空洞：**65.1 %** 的可用状态 `h = 0`，**579/1550** 个世界里 `h` 在每个这样的状态上都是 0。锐度不被主张（D-008）。

### 5. `fd_adapter`  ·  枚举标签 `fd_adapter`

* **提出/证明**：提出 plan：一个 `solve(domain, problem)` 接口覆盖三级规划器阶梯（自带 BFS / Fast Downward 最优 / LAMA 满意），并裁定「无计划」何时可以读作证明。
* **tree sha1**：`4995715504229251a12ce947f40c28186eba6c9a`
* **版本串**：⛔ 无。里程碑 `engine-rig-m6-fd` 的树 **不等于** HEAD。
* **专属测试文件**：`engine-rig/tests/test_fd_adapter.py` — `^def test_` **18** 条
* **另有 8 个测试文件引用它**（不计入上面的条数——它们是别的引擎的测试，把这个引擎当输入用）：
  * `engine-rig/tests/test_audit_claim.py`（该文件自身 9 条）
  * `engine-rig/tests/test_audit_verify.py`（该文件自身 19 条）
  * `engine-rig/tests/test_bench.py`（该文件自身 59 条）
  * `engine-rig/tests/test_deadlock_carver.py`（该文件自身 19 条）
  * `engine-rig/tests/test_fd_ladder.py`（该文件自身 33 条）
  * `engine-rig/tests/test_probe_reach.py`（该文件自身 13 条）
  * `engine-rig/tests/test_sokoban_fixture.py`（该文件自身 9 条）
  * `engine-rig/tests/test_tool_failure_is_not_truth.py`（该文件自身 26 条）
* **常设保留**：**三级阶梯是真的，回落是真的，但「静默回落」有条件，而「3 个测试跳过」已过期。**
  1. 阶梯：`backends.py:33-36` `TIERS = ("stub-bfs", "fd-optimal", "fd-satisficing")`。真实构建：FD 24.06+ `7120aa01`，winlibs GCC 16.1.0，235 targets，无补丁。
  2. **`.toolchain/` 按设计 gitignore**（`TOOLCHAIN_MANIFEST.md:290`），所以没有构建的机器上会回落到自带 BFS。**但回落只在调用者不指名档位时是静默的。**`choose_tier` 第 2 条（`backends.py:170-182`）在指名 FD 档而没有可达构建时**抛 `FastDownwardMissing`**，理由逐字写在 docstring 里：「asking for a named planner and silently getting another one is how a benchmark lies」。静默回落是第 4 条（`:186-188`），即 `prefer=None`——而 `theoria-arm/inner/plan.py:112` 正是这样调的（本清单 待办 7-a）。还有一处**结构性**静默回落，第 3 条（`:184-185`）：带 `prune=` 或纯内存实例时强制 stub，**在有构建的机器上也一样**，fuzz 电池因此从未跑过任何 FD 档。
  3. **「3 个测试跳过」是 P-13 时代的数字，已过期。** 本机实测（无 FD）：**554 passed, 27 skipped**（581 收集）。27 跳过里 **15 条是 FD 的**，另 **12 条**是 `test_tool_failure_is_not_truth.py:349`，与 FD 无关。`STATUS.md:71-74` 记的 483/27 计数已过期且把「跳过全是 FD 的」写错了；`STATUS.md:384` 仍在引 P-13 的 252+3，那就是 CLAUDE.md「3」的来源。
  4. **产物路径按设计钉死在 stub 上**（D-025，`__init__.py:36` `ARTIFACT_TIER = backends.STUB`），所以 `artifacts/candidates.jsonl` 在有无规划器的机器上字节相同。**这也意味着提交流里没有一行来自真实 FD。**
  5. 退出码分不开证明与放弃（D-024）：exit 12 是 `SEARCH_UNSOLVED_INCOMPLETE`，不是 11 `SEARCH_UNSOLVABLE`。跨赛道审计发现 `cold-start-a0` 曾仅凭异常字符串把 12 读成证明。

### 6. `probe_frontier`  ·  枚举标签 `probe_frontier`

* **提出/证明**：提出 probe_design：选下一个实验——按预测观测切分存活假设，按单位成本信息增益排序动作。
* **tree sha1**：`f8e16e9b79b5780b43438798cea2fd05bf97fd51`
* **版本串**：⛔ 无。里程碑 `engine-rig-m7-probe` 的树 **不等于** HEAD。
* **专属测试文件**：`engine-rig/tests/test_probe_frontier.py` — `^def test_` **14** 条
* **另有 2 个测试文件引用它**（不计入上面的条数——它们是别的引擎的测试，把这个引擎当输入用）：
  * `engine-rig/tests/test_probe_reach.py`（该文件自身 13 条）
  * `engine-rig/tests/test_tool_failure_is_not_truth.py`（该文件自身 26 条）
* **常设保留**：**算术干净，边界全在退化与接缝上。** 0 个切分不符、0 个熵不符（最大偏差 1.11e-15）、4000 个世界 0 次真实换序。但零成本无用动作得分 `inf`、排第一，并让 `best_probe` 返回 `None`——**4000 个 fuzz 世界里 82 个因此丢掉一个可用的 1 比特实验**；同一个包里对「成本 0 的价值」有两个相反定义（`inf` 与 `0.0`）。裸 `Infinity`（不是合法 JSON）在 **1633/4000** 发射行里进入共享候选流，而冻结契约的校验器放行。规划器支撑的那条路径（`run_with_planner` / `ExecutableProbe`）**没有任何暴力对照——边界未测**，因为它需要真实 FD 构建。29 个发布字段里 19 个没有不变量断言。

### 7. `deadlock_carver`  ·  枚举标签 `fd_adapter`  ·  `PRODUCER = "deadlock_carver"`

* **提出/证明**：证明 invariant（+ plan 账）：条件式微型不可解定理 `pattern AND not-goal => dead`，由基化任务上的局部枚举加 h² 互斥证出；同一条定理既是候选也是规划器剪枝。
* **tree sha1**：`d59ce5bfa1e873141b18d7e085c95615c4d76ecd`
* **版本串**：⛔ 无。里程碑 `engine-rig-m9-deadlock-ic3-probe` 的树 **不等于** HEAD。
* **专属测试文件**：`engine-rig/tests/test_deadlock_carver.py` — `^def test_` **19** 条
* **另有 4 个测试文件引用它**（不计入上面的条数——它们是别的引擎的测试，把这个引擎当输入用）：
  * `engine-rig/tests/test_audit_claim.py`（该文件自身 9 条）
  * `engine-rig/tests/test_bench.py`（该文件自身 59 条）
  * `engine-rig/tests/test_probe_reach.py`（该文件自身 13 条）
  * `engine-rig/tests/test_tool_failure_is_not_truth.py`（该文件自身 26 条）
* **常设保留**：**真值干净，速度红利在真实规划器上不成立。** 被裁决的库存 **50 CONFIRMED / 0 refuted**（本引擎自己的数是 recheck 列的 **36/36**；那个 50 跨四条赛道八个生产者，不是本引擎的分数）。完备性被证据封顶：`MAX_PATTERN = 2` 就是 h² 互斥的宽度，`open4far` 的死状态覆盖 55.9 %，**44.1 % 死于没有 2 原子模式能陈述的理由**。**Theoria 1.9 的加速那一半没活过真实规划器**：`far6` 上对 blind 搜索 3070→2762（−10.0 %），对 `lmcut` **47→47**、对 `ipdb` **18→18**；M9 记的 `ringstuck` 44→22 是关于自带 BFS 的事实，真实 FD 两边都是 0→0。**边界未测**：所有定理都出自四个 sokoban 实例，换域后 `MAX_PATTERN = 2` 买到或赔掉什么，没人测过。

### 8. `ic3_pdr`  ·  枚举标签 `lp_potential`  ·  `PRODUCER = "ic3_pdr"`

* **提出/证明**：证明 invariant：LP 不可行处的后备归纳不变式，回答 lp_potential 的未了之事，报同样的三个条件。
* **tree sha1**：`ea6ee43f4a2c29a4bdd59980a1f5febe939b908a`
* **版本串**：⛔ 无。里程碑 `engine-rig-m9-deadlock-ic3-probe` 的树 **等于** HEAD。
* **专属测试文件**：`engine-rig/tests/test_ic3_pdr.py` — `^def test_` **16** 条
* **另有 4 个测试文件引用它**（不计入上面的条数——它们是别的引擎的测试，把这个引擎当输入用）：
  * `engine-rig/tests/test_ic3bounds_emit.py`（该文件自身 22 条）
  * `engine-rig/tests/test_ic3bounds_harness.py`（该文件自身 25 条）
  * `engine-rig/tests/test_ic3bounds_reencode.py`（该文件自身 32 条）
  * `engine-rig/tests/test_ic3bounds_worldgen.py`（该文件自身 23 条）
* **常设保留**：**边界未测，整条。** 提交流里 **1** 张证书，在 **1** 个 16 状态 fixture 的 **1** 个配置（`peg4` `0111`）上。没有状态空间阶梯、没有谓词数阶梯、没有超时、没有失败形态普查。**fuzz 电池里根本没有它的性质模块**——`fuzzlab/props/` 覆盖六个引擎而它不在其中，战役里 **0** 行属于它，所以 60 世界战役、64 个变异体、111 字段发布审计一条都碰不到它。**论文可以说 LP 的缺口在 `0111` 上被覆盖，不可以说它被覆盖。**未结工单：`monitor/board/items/E8-ic3-scale.md`——「只有一个点，画不出线」。

## 4. 提交候选流普查 —— 撞名的解法**没有写下来**

`engine-rig/artifacts/candidates.jsonl`，44 行（确定性模式，D-015）：

| `engine` | `payload.producer` | `kind` | 行数 |
|---|---|---|---|
| `cegis_miner` | *（缺）* | `rule_hypothesis` | 10 |
| `fd_adapter` | *（缺）* | `plan` | 1 |
| `fd_adapter` | `deadlock_carver` | `invariant` | 16 |
| `fd_adapter` | `deadlock_carver` | `plan` | 1 |
| `lp_potential` | *（缺）* | `heuristic` | 1 |
| `lp_potential` | *（缺）* | `invariant` | 1 |
| `lp_potential` | `ic3_pdr` | `invariant` | 1 |
| `mdl_segmenter` | *（缺）* | `object_hypothesis` | 1 |
| `probe_frontier` | *（缺）* | `probe_design` | 3 |
| `zero_space` | *（缺）* | `invariant` | 9 |

**26/44 行没有 `payload.producer`。** 只有那两个后来的包设了这个常量（`git grep -n '^PRODUCER' HEAD -- 'engine-rig/engines/*'` 恰好两行）。

**这 26 行的 `engine` 全部是六个冻结引擎之一**（26/26 行如此），对它们来说枚举名本身就是生产者，字段缺失不是遗漏、是无话可说。带 producer 的 18 行则全部出自后来的两个包（`deadlock_carver`、`ic3_pdr`）。所以 D-018 那句「`payload.producer` is never absent」**在它所说的那批行上成立**，不必据此指控它。

**真正的缺口是解析规则没写下来。** 撞名可解——缺失 ⇒ 枚举名就是生产者——但这句话在任何文件里都找不到，于是**一行缺 producer 的记录在字节层面无法区分**「六个冻结引擎之一发的」与「某个新引擎忘了设 `PRODUCER`」；而 `by_engine` 与 `by_producer` 两个 histogram 会在新引擎的行上给出不同的答案。冻结前二选一：把「缺失 ⇒ 自指」写成契约的一句话，或让六个冻结引擎也设 `PRODUCER`。

## 5. 测试计数 —— 从 git 推导的与实测的，分开报

第 3 节每个引擎的条数是 `^def test_` **对 blob 计数**，所以在一台跑不动 pytest 的机器上也能从 git 复现。**它不是 pytest 的收集数**（参数化会让两者不同），因此实测值单独报，并标明它是一次测量而不是一个哈希：

| 量 | 值 | 条件 |
|---|---|---|
| 收集 | 581 | 本机，`python -m pytest --collect-only -q` |
| 通过 | 554 | 本机，**无** Fast Downward 构建 |
| 跳过 | 27 | 其中 15 条是 FD 的，12 条是 `test_tool_failure_is_not_truth.py:349` |

留痕：`freeze/runs/20260729T2040Z-S4-freeze-complete/item05/pytest-no-fd.txt`。

**三处已知过期的计数，都不要引：** `CLAUDE.md`「150 tests pass, 1 skipped」；`engine-rig/STATUS.md:71-74`「483 passed, 27 skipped … the skips are all FD's」（计数过期，且归因错误——12 条与 FD 无关）；`engine-rig/STATUS.md:384`「255 / 252+3」（P-13 时代）。

## 6. 外部工具链 —— 身份钉在受版本管理的字节上，东西没有

| 字段 | 值 | 由受版本管理的文件断言 |
|---|---|---|
| `binary_sha256` | `645671ae40d825478a043a9f94c856dc6130a11c166b3393837c153c5020aee1` | ✅ `engine-rig/bench/toolchain.py` |
| `fd_commit` | `7120aa01704bfe8e3b9b92c062a4f775bc89c7bd` | ✅ `engine-rig/bench/toolchain.py` |
| `fd_version` | `Fast Downward 24.06+` | ✅ `engine-rig/bench/toolchain.py` |

溯源：`engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`（URL / 版本 / 大小 / sha256 / 构建命令 / 实际用到的工具版本）。可执行形态：`engine-rig/bench/toolchain.py` 的 `EXPECTED`，它在运行时从活体二进制重新导出 `--version`、git revision 与 binary sha256 并比对，所以一份漂了的溯源文档会表现为 mismatch。

**是否可从受版本管理的文件复现：期望可以，产物不可以。**`.toolchain/` 按设计 gitignore（约 1.6 GB），那个 280,538,976 字节的二进制不在仓库里，也不能由仓库重建。`bench/toolchain.py:8-16` 自己就这么写：「Every Fast Downward number in this run was produced by a binary that is not in the repository and cannot be reconstructed from it.」换来的不是可复现性而是**可反驳性**：重建出不同哈希，是一个可以被追问的问题。

**因此，一条只写「fd-optimal」而不记录实际答题档位的冻结行，是一句假话。**阶梯有三级，`choose_tier` 第 4 条在 `prefer=None` 时按 `$FAST_DOWNWARD` 是否可达在 `fd-optimal` 与 `stub-bfs` 之间切换，而 `theoria-arm/inner/plan.py:112` 就是不传 `prefer=` 的（`MANIFEST_DRAFT.md` 待办 7-a）。冻结行必须同时记：(i) 请求的档位，(ii) 实际答题的档位，(iii) `bench/toolchain.py` 的 `matches_p13_manifest` 与 `available`。

## 7. 伴生文件（本条的落点闭合到这些字节）

| 路径 | blob sha1 @HEAD | 是什么 |
|---|---|---|
| `engine-rig/ENGINE_TABLE.md` | `66eea5e10dd08e4f7b5c6919525f8aa77cef0e54` | **名册与边界的现有权威**，`python -m tools.engine_table` 生成（`--check` 只核不写），由 `engine-rig/tests/test_engine_table.py`（9 条）盯住每个数字仍由其探针支撑；180 条事实带逐条来源表。它有八行、有「它解决什么」、有 fixture、有复核方式、有永不留空的边界列。**它没有：模块路径、哈希、版本串、测试条数、枚举标签、工具链身份。**所以钉住它是必要而不充分的——它是本条的「清单」那一半，不是「与版本」那一半。 |
| `engine-rig/STATUS.md` | `cc0e43359aa813bde8d189e9206dfb13f7eeb44c` | 里程碑表（**九个**标签，不是八个）与测试套件计数。两处计数互相矛盾且都已过期，见 fd_adapter 的保留第 3 条。 |
| `engine-rig/DECISIONS.md` | `07ee795a05a674030661277abe6b3aa4c4054012` | D-018（枚举撞名）、D-014（pagoda 不完备用测试断言）、D-025（产物钉在 stub）、D-024（退出码不是证明）、D-008（不主张锐度）的落点。 |
| `engine-rig/common/candidates.py` | `38113dbd617ed058119f74587db6c626d9487567` | **冻结枚举 `ENGINES` 的唯一定义**（`:27-34`，恰好六个名字）与 `KINDS`。 |
| `engine-rig/artifacts/candidates.jsonl` | `43f80fbaa2c81c3e4548df7b43f6371126c90373` | 提交的候选流，确定性模式（D-015），44 行，本清单第 4 节对它做普查。 |
| `engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md` | `3b64bde6f5519806b1cc5ac105142e105e4422ec` | 外部工具链溯源：URL / 版本 / 大小 / sha256 / 构建命令 / 工具版本。 |
| `engine-rig/bench/toolchain.py` | `5e291a29bfa9041cf777b1f386a43a1558ed2a01` | **工具链身份的可执行形态**：`EXPECTED`（`:42-47`）持有期望的 binary sha256 / FD commit / FD version，并在运行时从活体二进制重新导出比对，所以一份漂了的溯源文档会表现为 mismatch 而不是被当成仍然为真来引用。 |

里程碑标签，全部 9 个 `engine-rig-*`：`engine-rig-m1-fixtures`、`engine-rig-m2-mdl`、`engine-rig-m3-cegis`、`engine-rig-m4-zerospace`、`engine-rig-m5-lp`、`engine-rig-m6-fd`、`engine-rig-m7-probe`、`engine-rig-m8-integration`、`engine-rig-m9-deadlock-ic3-probe`。

**九个，不是八个。** `CLAUDE.md` 说「all eight milestones」，而承载 `deadlock_carver` 与 `ic3_pdr` 的正是第九个 `engine-rig-m9-deadlock-ic3-probe`。

## 8. 与 `freeze/MANIFEST.json` 的对接

`build_manifest.py` 的第 5 项按内容 sha256 钉 `engine-rig/engines`；本文按 git tree sha1 钉同一个路径。两者用不同的算法，所以必须显式对接，否则一份漂了而另一份没看见。本行由本生成器调用 `build_manifest.hash_path` 重算，`--verify` 会连它一起核：内容 sha256 = `6c6101f678034d9a78c58eb01584e29fa89d2f6993b1b16124c0be5367ea902f`（git-blob，40 个文件），git tree sha1 = `01c562e7a2b767a790be4e4159013f2914c67255`。

## 9. 本清单**没有**钉住什么

* **版本串。** 八个全缺，见第 0 节的 ⛔ 5-b。
* **Fast Downward 二进制。** 只有身份，没有产物（第 6 节）。
* **Python 与库。** 全仓没有任何依赖锁（无 `requirements.txt` / `poetry.lock` / `uv.lock` / 环境导出），所以「全部哈希」对解释器与库不成立。这条与 `build_manifest.py` 的 X-2 同源。
* **fuzzlab 与 `runs/` 下的度量产物。** `ENGINE_TABLE.md` 的 180 条事实来自十个来源目录；本文钉的是那张表的 blob，不是它读的每一个产物。
* **`ic3_pdr` 的任何边界。** 不是本文的疏漏，是树上就没有（第 3.8 节）。

## 10. 机读钉住块

`--verify` 逐行读这个块并与 git 重算的结果比对，所以漂移报告能点出**哪一个文件**动了，而不是只说「清单变了」。

<!-- ENGINE-HASHES:BEGIN -->
```
blob 07ee795a05a674030661277abe6b3aa4c4054012  engine-rig/DECISIONS.md
blob 66eea5e10dd08e4f7b5c6919525f8aa77cef0e54  engine-rig/ENGINE_TABLE.md
blob cc0e43359aa813bde8d189e9206dfb13f7eeb44c  engine-rig/STATUS.md
blob 43f80fbaa2c81c3e4548df7b43f6371126c90373  engine-rig/artifacts/candidates.jsonl
blob 5e291a29bfa9041cf777b1f386a43a1558ed2a01  engine-rig/bench/toolchain.py
blob 38113dbd617ed058119f74587db6c626d9487567  engine-rig/common/candidates.py
tree 01c562e7a2b767a790be4e4159013f2914c67255  engine-rig/engines
tree 6d5e00a93c372391eaf283025f0d268a13e8e2fc  engine-rig/engines/cegis_miner
blob 96188bb7b9e20770344eb5fe03eebcd03fedc2df  engine-rig/engines/cegis_miner/README.md
blob 750107f22d1fef7ea961d8e91b06fb9ce60805e1  engine-rig/engines/cegis_miner/__init__.py
blob 2cabacfd470f7371405b21982b65d055e6fc0fad  engine-rig/engines/cegis_miner/atoms.py
blob 7fe0e1f18755cb091d32ae0cb185cf8c3c4634fb  engine-rig/engines/cegis_miner/miner.py
tree d59ce5bfa1e873141b18d7e085c95615c4d76ecd  engine-rig/engines/deadlock_carver
blob 73a50a8c100d9ecabfe9698658849462b5c4624f  engine-rig/engines/deadlock_carver/README.md
blob fa5c29d2eec40b1ce7a4a2236111b1531e3a63d2  engine-rig/engines/deadlock_carver/__init__.py
blob fee48595cae08fffc74d2a20e5495f050821753e  engine-rig/engines/deadlock_carver/carve.py
blob 8a6c90bf522b16ffb8a5b992e47ccedf9b262758  engine-rig/engines/deadlock_carver/mutex.py
tree 4995715504229251a12ce947f40c28186eba6c9a  engine-rig/engines/fd_adapter
blob 1d6c40c1f909dbed1296a27740ab92fe864fcc34  engine-rig/engines/fd_adapter/README.md
blob dc8eee51cba38276d084f5e5e0a6ff429f2ade15  engine-rig/engines/fd_adapter/__init__.py
blob 5a5609328ef0b64973a81e88d0309eb4e824c9f8  engine-rig/engines/fd_adapter/backends.py
blob 97852cd810fb6a7017307385e21dc0c5a2ff8aea  engine-rig/engines/fd_adapter/domain.pddl
blob b566a6c4f1f48f1c63ed4137389657a8c93937e1  engine-rig/engines/fd_adapter/fuzz.py
blob e56c5f11f7d43517899b844cc0e6f8c4f62df93e  engine-rig/engines/fd_adapter/pddl.py
blob 98b5c1bdb9967927062cf8afe15d0e7b6566f6d6  engine-rig/engines/fd_adapter/problem.pddl
blob a0a9afdb748d3d807e952667c18ea71abd1860d6  engine-rig/engines/fd_adapter/search.py
blob 68859e49a567785ffa972bd4dc016e9de6003074  engine-rig/engines/fd_adapter/validate.py
tree ea6ee43f4a2c29a4bdd59980a1f5febe939b908a  engine-rig/engines/ic3_pdr
blob c0c705000e19215a90658664173cd3f032ce9809  engine-rig/engines/ic3_pdr/README.md
blob 7124b8cc249af116a84e9cb7493c140c2ec96e54  engine-rig/engines/ic3_pdr/__init__.py
blob 45e3b09275812ccdd404237d359a0e180426456d  engine-rig/engines/ic3_pdr/check.py
blob b79f76cb57b81a82a3a8b7acc5a8df5ac7a21901  engine-rig/engines/ic3_pdr/pdr.py
blob c91e8a06c06522c743fb5da0f44b6650c4f2030a  engine-rig/engines/ic3_pdr/system.py
tree f29152f2e95b18472d776df6e658d099a0f387a1  engine-rig/engines/lp_potential
blob 1fc5b8edd2cd604c47a6507ce8077c873bb5f227  engine-rig/engines/lp_potential/README.md
blob dc5979a9f54e8400245c3e74ca4b244491a5c750  engine-rig/engines/lp_potential/__init__.py
blob d776c603f13397bf202c3aaae021651d18e53676  engine-rig/engines/lp_potential/potential.py
tree bd16096df21e7bc01e435b04d6aadcdba38bdf73  engine-rig/engines/mdl_segmenter
blob b02081dd65b974c866dfa9e523c21b570e3df97b  engine-rig/engines/mdl_segmenter/README.md
blob 2c42598923fcb5bc43108c8ff6bd50aab9ed01ff  engine-rig/engines/mdl_segmenter/__init__.py
blob defc9909d404855db5b083b70b683b6daff94eff  engine-rig/engines/mdl_segmenter/costs.py
blob be6914a73a2b075bbc67b1868658c94b23a3a5f0  engine-rig/engines/mdl_segmenter/segmenter.py
tree f8e16e9b79b5780b43438798cea2fd05bf97fd51  engine-rig/engines/probe_frontier
blob e7078ea27de6560927ac8fc864f2996f37aa2bf4  engine-rig/engines/probe_frontier/README.md
blob d3a32ab832c88c627365a706c894930660147c78  engine-rig/engines/probe_frontier/__init__.py
blob b3874d8d56aea6d9814512d4bc095c20012f92e7  engine-rig/engines/probe_frontier/frontier.py
blob 3406db94365c6eeb6f550a7dc69d88dd0f4bf991  engine-rig/engines/probe_frontier/reach.py
blob fb0a444f67b75505e02bdcb38ce063731d531798  engine-rig/engines/probe_frontier/scenario.py
blob 9617874e5ef90f7bdfcefab26d398bdc6a5364f7  engine-rig/engines/probe_frontier/sokoban_probe.py
tree 78ead9dd3e4874affe73333f171a05400da7cd25  engine-rig/engines/zero_space
blob ac640a9d2050094dd59913e0a7ba310eb9909f56  engine-rig/engines/zero_space/README.md
blob 11975ddfc6101bdb918ab2963d6c8a7958bb42f0  engine-rig/engines/zero_space/__init__.py
blob 86597ad7de8078c31dc303cbb9a3d9d8afeb4aab  engine-rig/engines/zero_space/gf2.py
blob 2ca804e5770c6916200034e08748e0752881e01a  engine-rig/engines/zero_space/zerospace.py
blob 3b64bde6f5519806b1cc5ac105142e105e4422ec  engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md
```
<!-- ENGINE-HASHES:END -->

---

*生成：`freeze/build_engine_manifest.py`。工单 S4-freeze-complete 第 5 项，RES-1，2026-07-29。*
*基准：本文哈希取自生成时的 HEAD；冻结定稿时必须在真正的冻结提交上重跑 `--verify`，并把提交号回填到 `MANIFEST_DRAFT.md` 开头的 `⟨FREEZE_COMMIT⟩`。*
