# S40 · 要求 1 的测量：`monitor/board.py` vs `fleetkit/fleetkit/board.py`

**逐条都是跑出来的**，不是读出来的：两个模块被拷进隔离临时目录、`FLEET_HOME`
各指一棵状态树、并排 import、喂同样的输入。两棵树都没有被修改。

## 0. 框住一切的那条来历事实

`fleetkit/fleetkit/board.py` 是 `monitor/board.py` 在 **`7b8d3d9b`（2026-07-29）
的逐字快照**，只有 5 处编辑：`locale.getpreferredencoding` 取代硬编码 `gbk`
（真改进）、`_PREFIX = ""` 取代字面量 `"TheoriaAgent-"`（**参数化了但从未接线**）、
`from fleetkit import config as _config`（**import 了，全文件再没引用过**）、
`HERE` 走 `FLEET_HOME`、`LANE_OWNER = {}` 加那句 docstring。

其余**逐字节相同**——包括模块 docstring 里仍然写着 `python monitor/board.py list`。

分叉基线有 18 个顶层函数，fleetkit 恰好有这 18 个、一个不多。**所以不存在
「简化」：没有任何东西是被有意去掉的。** monitor 那 18 个独有函数全是**上游漂移**
——S21/S27/S28/S29/S34/S35/S35a 都是分叉之后落在 `monitor/board.py` 上的
（7 个提交），而 fleetkit **一辈子只有 1 个提交**（`f42a498e`）。

## 1. 判据比对（不是 diff 行数）

**18 个共有函数：8 个行为一致、0 个 COSMETIC、10 个 DIVERGENT。**
（其中 8 个源码就不同；另 2 个源码逐字节相同、通过模块全局分叉。）

**这个计数是我自己跑出来后改过的**：派出去的测量 subagent 表里逐函数的判词是对的，
但它的汇总行写成「6 IDENTICAL / 12 DIVERGENT」，与它自己那张表对不上——
照表数是 8 个 IDENTICAL。我用 `ast` 逐函数比归一化源码复算：
shared 18、源码不同 8、源码相同 10（其中 2 个仍然行为分叉）。
**采信跑出来的数，不采信汇总的数。**

**「0 个 COSMETIC」是本次测量的头条**：没有任何一处只是措辞不同。凡是不逐字节
相同的，都存在一个能构造出来的输入让两边给出不同答案。

**而且有两个函数源码逐字节相同却仍然分叉**——`stale_lanes` 与 `territories_busy`
——它们通过 `LANE_OWNER` 这个模块全局分叉。**把两个文件并排读会把它们判成「一样」**，
这正是本条目要说的那种失败。

### 10 处分叉里最要命的四处

**(a) `cmd_sweep` 会把还在跑的工人的活抢走。** `_PREFIX = ""`（`board.py:31`）
在整个包里从未被赋值过（grep 核过），所以 `if ... and _PREFIX and _PREFIX in cols[0]`
（`:321`）**恒为假**，`live` **恒为空集**，于是每一条 `W-*` 认领都被判成孤儿。
实测（注入合成的 `schtasks` CSV，`TheoriaAgent-W-777`=Running、`W-888`=Ready）：
monitor 只释放 `W-888`，**fleetkit 两个都释放**。

这是 `fleetkit/KNOWN_TRAPS.md` 第 1 条**一字不差**（「每个工人都读成死的。板会释放
活的认领」）——潜伏在那个 ship 出这份警告的工具包自己身上。而
`config.py:78-83` 恰恰为此把 `task_prefix` 校验成非空，**`board.py` 从不读 config**。

**(b) `LANE_OWNER = {}` 让任何带 `lane:` 的条目由构造不可达。** 它被
`candidates()` 排除（`stale` 恒为 ∅）、不在 `list` 的 reserved 段
（`for lane in sorted(LANE_OWNER)` 迭代零次）、也不在其余任何段。实测：一个
`lane: campaign` 的条目 → `cmd_list()` 只打印 `=== available (通用工人可领 0) ===`
然后结束。**这个条目对任何有据可查的命令都不可见、不可领，而且没有任何出口**
（monitor 分叉前的兜底出口是「等 45 分钟主人心跳变陈」，可 `stale_lanes()`
恒返回 ∅，所以连那个都没有）。唯一的恢复手段是手改条目文件。

**(c) `meta()` 的正则会凭空造出字段值。** ADV-1 那处修复没跟过来：
monitor 是 `r"^%s:[ \t]*(\S+)"`，fleetkit 是 `r"^%s:\s*(\S+)"`，而 `\s` **跨换行**。
实测 `priority: 2\nlane:\ncell: A3\n...` → monitor `lane=''`，**fleetkit `lane='cell:'`**；
`deps:\ncell: B1` → **fleetkit `deps=['cell: B1']`**，一条永远满足不了的依赖，
条目永久受阻。**于是 (b) 那个洞不需要谁真的写了 lane 就能掉进去**——
front matter 里留一个空字段就够了。

**(d) `cmd_claim` 没有 `lane_denied` 闸，一句自报的 `--lane` 就能拿走真金白银的活。**
实测：条目 `lane: campaign, spend: api`、无 `generic_ok`，`cmd_claim("W-9999","campaign")`
→ monitor 退出 **3** `LANE-NOT-YOURS`；**fleetkit 退出 0，认领成功。**

其余八处（`heartbeat_age` 不看 `.lock`、`candidates` 会重新发放已交付的活、
`cmd_list` 少了 territory-blocked 与 unreachable 两段、`cmd_release` 默认理由
`"unstated"` 且不写回条目文件、claim→release→claim 的活锁复现、
`except OSError` 吞掉 Windows 共享冲突造成**假的空板且 board.log 无痕**、
`main` 没有 reassign/reconcile）逐条输入与两边输出见本文件末的完整表。

## 2. 要求 3：`LANE_OWNER` 那句 docstring —— 条目的指控逐点成立

```python
#: Filled from fleet.json at import; empty means "no lane has an owner",
#: which is the correct behaviour for a fleet that has not declared any.
LANE_OWNER = {}
```
（`fleetkit/fleetkit/board.py:48-50`）

* 全包 4 处出现：1 处赋值（`:50`）、3 处读（`:77`、`:203`、`:206`）。
  **没有任何 write / `.update()` / `setdefault` / 猴补**——包括测试与 `verify.py`。
* **`fleet.json` 在整个仓库里根本不存在。** 它只被 `config.write_default` 写进
  临时目录，只被 `config.load` 读，而 **`board.py` 从不调用其中任何一个**。
* `from fleetkit import config as _config`（`:33`）**在全文件只出现这一次**
  ——接线被打算过、从没写。
* **就算接上了也填不出来**：`FleetConfig.lanes` 是 `List[str]`（只有 lane 名字），
  而 `LANE_OWNER` 要的是 `lane → owner` 映射，**config 的 schema 表达不了它**。

**所以那句话错了两遍**：机制不存在，而且数据源供不出这个形状。

reserved 段是「可达代码 + 不可达循环体」：`cmd_list` 每次都跑到 `:203`，
循环迭代零次，`reserved` 恒为 `[]`，`if reserved:` 恒假——**给定 `{}` 它什么都不打印**，
不是打印一个空标题。而它与 monitor 分叉前的版本逐字节相同，所以**并排读代码的人
看见一段眼熟的、看起来在工作的实现；跑 `list` 的人看见一块没有 reserved 的板**。
`heartbeat_age` 与 `LANE_OWNER[lane]` 在 `:206`/`:210` 一次都没有执行过。

`stale_lanes()` 同理：13 行函数、6 行 docstring 讲一次真实停摆，实为常函数返回 `set()`。

## 3. 要求 2 的证据基础：两份文档说了什么、没说什么

**关键否定事实：`README.md` 与 `KNOWN_TRAPS.md` 里没有 track / sync / drift /
diverge / fork / snapshot / upstream / in step 中的任何一个词。**（全量 grep。）

`README.md:23-32` 那张表给 `board.py` 的状态是：

> `| board.py | ~360 | ported: atomic claim, territory exclusivity, lanes, sweep |`

**而 `lanes` 与 `sweep` 两项，实测都是不工作的。** 紧接着的一段是：

> **Not yet ported**, and named so the gap is not mistaken for a decision:
> `dispatch.py`, `reflex.py`, `quota.py`, `assign.py`, `ci_merge.py`

也就是说：**文档对「模块级」缺口明确、诚实、每轮打印；对「已移植模块内部的
判据漂移」一个字都没有。** README 把抽取叙述成一件完成了的过去的事
（extracted / ported），既没说它跟着 monitor 走，也没说它是有意的简化。

**条目那句「第三种状态」的诊断，文档本身就是证据。**

## 4. 测试情况

**没有任何一处比较过两个实现。** `grep -rn "monitor" fleetkit/` 只有 1 处命中
（`README.md:4` 一句来历散文）。反向也没有。

`fleetkit/tests/` 只有一个文件、6 个测试，全部用**front matter 填满、无 lane、
无 spend、无 released_by、无 done/ 残留**的条目，而且**从不调用 release / sweep / list**
——所以上面 12 处分叉**全部在套件之外**。`_put_item` 支持写 `lane:` 字段，
**但没有一个测试传 `lane=`**；传了就会失败，因为带 lane 的条目在 fleetkit 里领不走。

`fleetkit/verify.py` 的 `UNPORTED` 追的是**整模块没移植**，判据是
`os.path.exists(fleetkit/<name>.py)`（`:214`）——**所以 `board.py` 落后 18 个函数
这件事，它按设计就看不见。**

顺带两条：`verify.py:172-176` 会因生成的 `task_prefix` 为空而判红，
而 `board.py:31` 无条件 ship `_PREFIX = ""`——**闸门在检查一个代码从不读的副本**。
以及 **`fleetkit/fleetkit/__main__.py` 不存在**，所以 `README.md:13` 与
`__init__.py:8` 的第一行命令 `python -m fleetkit init --prefix MyFleet-`
直接报 `No module named fleetkit.__main__`（实测）；`verify.py` 绕过 CLI 直接调
`config.write_default()`，于是闸门在一个坏掉的入口之上是绿的。

## 5. 要求 2 的可行性约束（做「跟着走」需要面对什么）

* **判据函数本身已经是干净的、也正是天然的切口**：`meta`/`item_id`/`done_ids`/
  `claimed_map`/`territories_busy`/`candidates`/`released_by`/`offers`/`lane_denied`/
  `reachable_ids`/`unreachable_ids`/`withheld_items`/`held_by`/`delivered_map`/
  `resurrected` 都是「文件系统 + 模块常量」的纯函数，不碰 git、不碰 schtasks、
  不碰 spec、不含硬编码路径。真正绑死仓库的是 `prior_work`/`_git`（git 布局）、
  `cmd_sweep` 的存活探测（Windows）、`standing_verdict`（bus 布局）——
  **这三个都是「动作」不是「判据」，可以各留各的。**
* **四个模块常量必须变成参数而不是全局**（`LANE_OWNER`/`STALE_MIN`/`HOLD_CAP`/
  任务前缀）。12 处分叉里有 2 处正是**源码逐字节相同、纯粹通过全局分叉**的；
  共享模块若保留全局，会立刻复现同一个静默分裂。
* **`LANE_OWNER` 要有能表达它的数据源**：`FleetConfig.lanes` 是 `List[str]`，
  改成 `Dict[str,str]` 会动 `THEORIA_EXAMPLE` 与 `REQUIRED_CONFIG`。这是
  要求 3 「让那句话变成真的」那条路的前置成本，不免费。
* **`monitor/board.py` 被 8+ 个活模块 import**（`scan.py` 4 处、`standing.py:51`、
  `reflex.py` 2 处、`ci_merge.py:480`，另有 6 个测试文件），其中若干按名字依赖
  `STALE_MIN` 与 `heartbeat_age`。任何共享模块都必须从 `monitor/board.py` 原名
  再导出，否则活舰队当场停摆。
* **行尾**：`monitor/board.py` 是 CRLF，fleetkit 那份是 LF。裸 `diff` 报 714 行不同，
  归一化后是 5 处。**任何比文本的检查必须先归一化，否则落地当天 100% 假阳。**
* **要求 4 的阴性对照是现成的、不用编**：`5c872888` 与 `f069284a` 就是历史里
  真实的「monitor 改了、fleetkit 没改」事件，逐函数一致性检查可以回溯验证。
