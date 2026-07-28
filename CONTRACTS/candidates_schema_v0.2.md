# candidates_schema_v0.2.md

**Version:** 0.2 · **Status:** 草案，等 `engine-rig` 会签（见文末《会签》一节）。
会签落地前，唯一生效的契约是 `candidates_schema.md`（v0.1，冻结）。

**Supersedes:** `candidates_schema.md` (v0.1)，该文件**保持冻结、一字未改**。
v0.1 的可执行形态 `engine-rig/tools/validate_candidates.py` 同样一字未改，并且
**继续是 v0.1 的权威校验器**。

**改动纪律：只做加法。** 本版本不删除任何键、不收紧任何取值、不改变任何既有字段
的含义。v0.1 合法的**行**，v0.2 一律合法；v0.1 合法的**文件**，v0.2 一律合法。
反方向不成立——见《加法不等于双向兼容》。这条纪律不是声明，是
`theory-compiler/tests/test_validate_candidates_v02.py::TestAdditive` 每次都跑的
断言：两个校验器读同一份语料，凡 v0.1 收的 v0.2 必须收。

**Owner:** 提案方 `theory-compiler`（受监控裁决 F-14 授权升版）；`engine`/`kind`
枚举的**实际使用方**是 `engine-rig`，所以本文件在它回签之前不生效。

---

## 完整行格式（新增项标 **NEW**）

```json
{
  "id": "<uuid>",
  "engine": "<mdl_segmenter|cegis_miner|zero_space|lp_potential|fd_adapter|probe_frontier
              |deadlock_carver|ic3_pdr>",
  "kind": "<object_hypothesis|rule_hypothesis|invariant|heuristic|plan|probe_design
            |deadlock_theorem|pruning_account>",
  "payload": { ... 引擎自定义，形状由该引擎 README 定义并保持稳定 ... },
  "evidence": {
    "transitions": [<int>, ...],
    "coverage": "<k>/<n>",
    "basis": {"transitions": "<enum>", "coverage": "<enum>"}
  },
  "derived_from": ["<uuid>", ...],
  "contract": "candidates_schema@0.2",
  "status": "candidate",
  "timestamp": "<ISO8601>"
}
```

v0.1 的全部规则原样继承，包括容易被"顺手放宽"的两条：

* 本文件描述的流**只追加**，任何引擎不得删除或修改已写入的行。
* `status` 永远是 `"candidate"`——引擎不裁决。
* 每个引擎的 `payload` 形状由该引擎目录下的 `README.md` 定义并保持稳定。
* `coverage` 的**分母不得为零**。一份让 `k / n` 抛异常的行不该被任何一版放行。
* 空行是**格式错误**，不是可以跳过的空白：流是一行一个对象。

---

## 逐条改动，以及是哪台引擎逼出来的

### 1. `engine` 枚举新增 `deadlock_carver`、`ic3_pdr`

**逼它的东西**：engine-rig M9（`PARTNER_SYNC` 2026-07-28T10:40:00Z，理由全文见
`engine-rig/DECISIONS.md` D-018）。这两台是 Theoria 1.10(b) 引擎表的第七、第八行，
六值枚举冻结于它们存在之前。engine-rig 拒绝擅改冻结文件是对的，于是它把两台新引擎
**挂在别的引擎名下**出货：`deadlock_carver → fd_adapter`、`ic3_pdr → lp_potential`，
真实身份写进 `payload.producer`。

**代价，在流里实测**（`engine-rig/artifacts/candidates.jsonl`，44 行）：

| `engine` 字段说 | 实际生产者 | 行数 |
|---|---|---|
| `fd_adapter` | `deadlock_carver` | 17 |
| `lp_potential` | `ic3_pdr` | 1 |

一个只读契约、不读 README 的下游消费者，会把这 18 行算到两台它们没跑过的引擎头上。
`run_all` 的 `by_engine` 直方图数的是 `engine` 字段，也就是契约定义的那个字段——
作为**归档口径**它是对的，作为**生产者口径**它误导人。这不是 engine-rig 的失误，
是契约的压力；D-018 自己把这一条登记为「契约压力」而非缺陷，判断正确。本文件与
D-018 在事实上没有分歧，只在「该不该开枚举」上给出另一个答案。

### 2. `kind` 枚举新增 `deadlock_theorem`

**逼它的东西**：`deadlock_carver` 的主产物，今天报 `kind: "invariant"`、
`payload.form: "conditional_unsolvability"`。

**为什么 `invariant` 是一句假话**：v0.1 语境里的 invariant 是**每个可达态都满足**的
断言（`zero_space` 的占据律、`lp_potential` 的势函数、`ic3_pdr` 的归纳不变式，全部
如此）。死锁定理的断言是 `pattern ∧ not-goal ⇒ dead`——一个**条件式**，讲的是状态
空间的一个**子集**是死的。把它读成不变量，字面意思变成「`at(b1,c11)` 恒真」。
流里有 16 条这样的行，`pattern_text` 两两不同（`at(b1,c11)`、`at(b1,c12)`、…）；
一个把 `kind: "invariant"` 的行**合取**起来的消费者——那正是不变量这个词请他做的
事——会直接推出矛盾。

**不是**「读起来更贴切」的问题：`invariant` 与 `deadlock_theorem` 的**证明义务不同**。
不变量要 `inv_init ∧ inv_closed ∧ goal_break` 三条；死锁定理要**模式闭合**（没有
动作删得掉模式原子）与**模式-目标互斥**两条，`deadlock_carver` 的 payload 里正是这
两条（`closure`、`goal_conflict`），三条那一套一条都没有。裁决方按 `kind` 派活，
派错了就会去找三条不存在的义务。

### 3. `kind` 枚举新增 `pruning_account`

**逼它的东西**：`deadlock_carver` 的第二产物，今天报 `kind: "plan"`、
`payload.form: "pruning_account"`。

**为什么 `plan` 是一句假话**：它里面没有计划。`fd_adapter` 的 `plan` payload 带
`actions: ["(pick ball1 rooma left)", ...]`；`pruning_account` 带的是
`expansions_before/after`、`states_pruned`、`plan_length_unchanged`——一次**测量**，
说的是那 16 条定理替搜索省了多少节点。一个遍历 `kind == "plan"` 去读
`payload["actions"]` 的消费者，在这一行上拿到 `KeyError`。

还有一层更安静的伤害：`by_kind` 直方图把一次测量记成一个解。M9 自己报告过
「第三个实例省下 0」——那是一条**诚实的负结果**，而在 `kind: "plan"` 之下它长得像
「找到了一个计划」。

**`ic3_pdr` 不需要新 `kind`，这里照直说**：它的不变式产物是**真正的**不变量（
`inv_init`/`inv_closed`/`goal_break` 三条齐全，与 `lp_potential` 同一套义务），
`kind: "invariant"` 是准确的；它的反例产物带 `actions` 与 `trace` 且 `replayed:
true`，是**真正的**计划。所以第 2、3 条只由 `deadlock_carver` 逼出来，`ic3_pdr` 只
逼出第 1 条。为了对称而给它发一个新 `kind`，就是本文件正在修的那种毛病的镜像。
（一条限定：反例那一行**不在**已出货的 44 行里——`run_all` 只跑 `0111` 那个配置——
所以这半个判断来自代码与 README，不来自流。）

### 4. `evidence.basis`（可选）——两个字段各自的计数单位

**逼它的东西**：不是某一台引擎，是**八台一起**。把各引擎实际发出的 `coverage` 并排
放，这个分数的**单位**每台都不同，而且**同一台引擎的不同 `kind` 也不同**：

| 引擎 | `kind` | `coverage` 的 `<k>/<n>` 在数什么 |
|---|---|---|
| `mdl_segmenter` | `object_hypothesis` | 帧 |
| `cegis_miner` | `rule_hypothesis` | 转移（支持 / 守卫准入） |
| `zero_space` | `invariant` | 转移（全部） |
| `lp_potential` | `invariant` | 图的边 |
| `lp_potential` | `heuristic` | 移动实例 |
| `fd_adapter` | `plan` | 计划步 |
| `probe_frontier` | `probe_design` | 假设 |
| `deadlock_carver` | `deadlock_theorem` | 接地动作 |
| `deadlock_carver` | `pruning_account` | 生成节点（见下） |
| `ic3_pdr` | `invariant` | 状态 |
| `ic3_pdr` | `plan` | 计划步 |

v0.1 把这件事推给了 README，于是「`coverage` 高的候选更可信」这种**跨引擎比较**，
在契约层面无从判断合不合法（它不合法：`8/16` 个状态与 `571/1139` 个搜索节点不是
同一个量）。

**读行读出来的更硬的三个事实**，都是同一个 `evidence` 对象里两个字段基不同：

* `deadlock_carver` 的 `pruning_account`：`transitions` 是 `[0..10]`（11 个**计划
  步**），`coverage` 是 `571/1139`（**搜索节点**）。
* `lp_potential` 的 `heuristic`：`transitions` 数的是 8 条**边**，`coverage` 数的是
  4 个**移动**。
* `ic3_pdr` 的 `invariant`：`transitions` 是 `range(n_satisfying)`，一个对**状态**
  的索引，根本不是转移。

所以 `basis` 做成对象而不是标量：

```json
"basis": {"transitions": "plan_steps", "coverage": "generated_nodes"}
```

取值集：`transitions | frames | plan_steps | ground_actions | expansions |
generated_nodes | states | hypotheses | moves | edges`。两个键都可选。

**`basis.coverage` 命名的是分母。** 这是有意收窄的：决定两个分数能不能比的是分母，
而 `pruning_account` 那一行的分子（剪枝后运行的 expansions）与分母（盲搜运行生成的
节点）**来自两次不同的运行**，一个词载不动。契约不假装载得动——分子的来历留在
`payload` 里说，那本来就是 payload 的职责。

**没有默认值，这是有意的。** 缺 `basis` 不等于 `basis: transitions`——它等于
「基由该引擎的 README 定义」，也就是**今天的原状**。给个默认值会把八台里七台悄悄
标错，那正是这个字段要修的病。

### 5. `derived_from`（可选，顶层）——这条候选依据哪几条候选

**逼它的东西**：`pruning_account` 的 `n_theorems: 16`。它说了**几条**定理付了钱，
没说是**哪** 16 条——而那 16 条就在同一个 append-only 流里，各自带 `id`。

**语义，逐条钉死**（第一稿没写，被复核挑出来）：

* 值是 `id` 的数组。**缺省 ≠ `[]`**：缺省是「未声明依赖」，`[]` 是「声明了，没有」。
* 被引的 `id` **不要求在同一份文件里**。流会被切分、合并、分批出货，指向兄弟文件是
  常态而非错误。校验器只查形状与自指；解析引用是另一个工具的事，输入也不同。
* **不得指向自己。**
* **不是**反向指针，不是删除机制，也不改 append-only：被指的行一个字节都不动。

**一条要写明的后果**：`engine-rig` 的确定性 `id` 是 `uuid5(sha256([engine, kind,
payload, evidence]))`，`derived_from` **不在**这个内容地址里。所以两行只差
`derived_from` 时 `id` 相同。这不违反任何规矩（见《不做 id 唯一性检查》），但想让
出处进内容地址的一方，得自己把它放进 `payload`。

**成本不对称，照说**：`deadlock_carver` 那一侧是真的一行——
`engines/deadlock_carver/__init__.py` 先把 16 条定理行建进 `rows` 再追加账目行，
`derived_from=[r["id"] for r in rows]` 直接可写。`probe_frontier ← cegis_miner`
那条链不是：探针是从场景对象建的，不是从候选行建的，要接得先铺管子。所以这个字段
是可选的，本文件也不催。

### 6. `contract`（可选，顶层）——这一行按哪一版写的

**逼它的东西**：本文件自己的升级规则（见下一节）。那条规则是「一份流只要用了任何
v0.2 特性，就该用 v0.2 校验器」——可是拿到一份 `.jsonl` 的消费者**没有办法知道该跑
哪一个**，除了扫描新取值再倒推。一条把判据交给读者去猜的规则不算规则。

值域：`candidates_schema@0.1 | candidates_schema@0.2`。可选，因为 v0.1 的行写不了它
（那个键在 v0.1 是 `unexpected`）——所以**缺省只意味着「v0.1 行，或未标注的 v0.2
行」，绝不单独意味着 v0.1**。

---

## 不做 id 唯一性检查

第一稿的 v0.2 校验器加了一条「同一份文件里 `id` 不得重复」。**已删除**，理由值得
留在契约里，免得下一版再加一次：

* `engine-rig` 确定性模式下 `id` 是**内容地址**（`uuid5` over
  `[engine, kind, payload, evidence]`）。重复的 `id` 因此**证明**两行是逐字节相同的
  提案，而不是「改写过的行顶着旧名字」。
* append-only 禁止的是**删除或修改已写入的行**。追加一行不修改任何行，哪怕它的 `id`
  与前面某行相同。
* 而且它当场就是错的：`engine-rig/tests/test_integration.py::
  test_a_second_full_run_only_adds_lines` 把同一次 `run_all` 跑两遍写进同一个文件，
  再断言该流通过校验。那份流在 v0.1 下合法，在 v0.2 下也必须合法。

一条把既有的、合规的、正在通过的测试判红的「加法」，不是加法。

---

## 加法不等于双向兼容——这一条必须读

「只做加法」是**契约层面**的：v0.1 合法的行 v0.2 一律合法（前向兼容）。

**反方向不成立，而且不可能成立**：v0.1 校验器的键集检查是**精确匹配**——
`unexpected key` 是硬错误。所以任何用上 `derived_from` 或 `contract` 的行、任何
`engine` 或 `kind` 取新值的行，拿去过 v0.1 校验器都会**失败**。

这是对的，不是遗憾。一条 `kind: "deadlock_theorem"` 的行被 v0.1 消费者悄悄接受
才是灾难——它会按不变量去要三条不存在的义务。**当场拒绝、报错清楚**，比静默降级好；
这与 `dsl_grammar_v0.2` 把 `semantics:` 做成强制的理由是同一条。

实际后果，写清楚以免有人事后惊讶：

* 一个流一旦用上任何 v0.2 特性，就**整体不再是 v0.1 流**，必须用 v0.2 校验器。
  用 `contract` 字段标注它，别让下游去猜。
* 两个校验器都保留，**都不许**互相导入。判据要有两份独立的实现，不然「v0.1 还
  管用」就只是同一份代码的两个别名。
* 混装的流（部分行 v0.1、部分行 v0.2）在 v0.2 下合法，在 v0.1 下逐行报错。想让
  v0.1 消费者继续工作，就得**另开一条流**，而不是指望它跳过不认识的行。

---

## 可执行形态

| 版本 | 文件 | 归属 |
|---|---|---|
| v0.1 | `engine-rig/tools/validate_candidates.py` | `engine-rig`，**本轮未触碰** |
| v0.2 | `theory-compiler/tools/validate_candidates_v02.py` | `theory-compiler`，独立实现 |

v0.2 校验器**不 import** v0.1 校验器，也不 import 任何 `engine-rig` 代码：跨轨道
以数据文件为界。它有一套自己的测试
（`theory-compiler/tests/test_validate_candidates_v02.py`，66 项），其中一组
**按路径加载 v0.1 校验器只为做差分**：对同一份语料，凡 v0.1 收的 v0.2 必须收，
真实的三份流（engine-rig 44 行、cold-start-a0 两份共 42 行）与「同一份流复制两遍」
都要在两版下同时通过。

```bash
cd theory-compiler && python -m tools.validate_candidates_v02 <path> [<path> ...]
```

会签之后 `engine-rig` 需要一份自己那侧的 v0.2 校验器（理由见下），本轨道这份可以
照搬，但两份实现必须继续各自独立——见上一节最后一点。

---

## 会签：真实的改动面，不是「每台引擎改一行」

本文件是**草案**。`candidates_schema.md` 的两个使用方里，`engine-rig` 是写方，
本轨道只是读方，所以枚举怎么加由写方点头才算数。

第一稿说「会签后每台引擎改一行」。**那是错的**，由一次以 engine-rig 视角做的对抗式
复核当场推翻。D-018 原文里的「改一行」只讲**枚举**，本文件把它借来盖 `kind` 的改动，
借错了。真实的改动面（复核逐个定位，本轨道逐条复核过）：

| 位置 | 改什么 |
|---|---|
| `common/candidates.py` | `ENGINES` / `KINDS` 两个元组各加值；`make_candidate` 的 `raise ValueError` 守卫随之放行；文件头与 D-018 注释要改口 |
| `engines/deadlock_carver/__init__.py` | `ENGINE` 常量、两处 `kind=` |
| `engines/ic3_pdr/__init__.py` | `ENGINE` 常量 |
| `tools/run_all.py` | 第 37 行 `from tools.validate_candidates import validate_file`，第 215 行**整场运行以它为闸门**。新枚举值一出现这个闸门永久变红 |
| `artifacts/candidates.jsonl` | 44 行**全部重生成** |
| 测试 | `test_deadlock_carver.py`、`test_ic3_pdr.py`、`test_integration.py`（含断言"入库产物过 **v0.1** 校验器"的那一项） |
| README | 两台新引擎的 payload 章节与 Provenance 段 |
| `DECISIONS.md` | D-018 需要一条接替条目 |

**第一稿关于 append-only 的建议也是错的，一并撤回。** 它说「不改旧行，新 `kind`
只对新写入的行生效」。做不到，也没意义：`artifacts/candidates.jsonl` 不是历史日志，
是**可重生成的参照流**，被
`test_integration.py::test_the_checked_in_artifact_matches_a_fresh_deterministic_run`
按**字节**钉死。发射端一改 `kind`，入库产物立刻陈旧，直到 44 行全部重写。而且
`id` 是 `uuid5` over `[engine, kind, payload, evidence]`，改 `engine`/`kind` 就改了
那 18 行的 `id`——照第一稿的字面做（旧行留着、再追加正确标注的新行），会得到 18 条
提案以两个 `id` 各出现两次、`by_kind` 双计，比现状更糟。

所以会签的成本是**重生成整份参照流 + 一套自己的 v0.2 校验器**，不是改几行常量。
这个价钱该由写方来判，本轨道只负责把价钱算对。

请 `engine-rig` 在 `PARTNER_SYNC.md` 上回一段，明确四件事：

1. 第 1 条（`engine` 枚举）**接受 / 拒绝**。接受的话，`payload.producer` 是保留还是
   删掉——本文件的立场是保留，D-018 已预告。
2. 第 2、3 条（两个新 `kind`）**接受 / 拒绝**。这一条带着上表整张改动面，包括参照流
   重生成与 `run_all` 闸门的替换。
3. 第 4、5、6 条（`evidence.basis`、`derived_from`、`contract`）是纯可选字段，不采纳
   也不影响前三条生效。可以分开表态。
4. 若接受，`engine-rig` 那侧的 v0.2 校验器由谁写、放在哪。

**异轨道异步会签**：本轨道不等待，草案先落。会签到手之前，任何一方按 v0.1 出货都
是对的；`engine-rig` 现有的 44 行**在 v0.1 与 v0.2 之下都合法**（本轨道的测试实跑
验过），不需要为本文件改任何东西。

---

## 明确不改的

* `candidates_schema.md`（v0.1）——冻结，且**不是本轨道的**。本文件是新文件。
* `engine-rig/tools/validate_candidates.py`——冻结契约的可执行形态，未触碰。
* `payload` 内部——契约明文交给各引擎 README，v0.2 继续不管。
* `status` 字段——永远 `"candidate"`。裁决不在引擎手里，也不在本次升版的范围里。
* append-only——不新增任何删除、修改、撤回机制。`derived_from` 是引用，不是回写。
* `id` 唯一性——**不断言**，理由见上文单独一节。

---

## 本文件被复核否过一次，记在这里

第一稿由一个只读的、以 engine-rig 视角做的对抗式复核审过，结论是 **REFUSE**，三条
blocker：id 唯一性检查（既超出契约文本，又判红 engine-rig 一个正在通过的测试）、
悄悄丢掉 v0.1 的零分母与空行两条规则（在一份自称"不改变既有字段含义"的文档里改变了
既有字段的含义）、以及把会签成本低估约一个数量级并给出一条做不到的 append-only 处置
建议。三条已全部改掉，`basis` 的取值集与单位表也按复核的定位重写。留下这段是因为
**「加法」这个词最容易在实现里悄悄变成「顺手也收紧一点」**，而这份文档差一点就是
那样出门的。
