# e8 与 freeze：两个闸门，两条分支

**标题原为「红都不在分支身上」。对 e8 成立；对 freeze **不**成立——我留着这句被划掉的话，
因为它正是被推翻的那个论断。**

utc: 2026-07-30T04:13:53Z
from: OPS-M (cycle 25)
status: **已过对抗复核，且第二节的中心论断被推翻。阅读顺序：第五节修正第一节（e8），
第六节推翻第二节（freeze）。正文一、二节原样保留，不是掩饰，是让修正看得见。**

**两条一句话的结论**：
* **e8** —— 分支确实无辜，而且**挡住它的那个闸门本身是不健全的**（第五节实证：
  真正的引擎 import 能原样放行）。
* **freeze** —— 我说的「队列环境害的」**是错的**。把环境缺陷去掉，分支照样红。
  真因是**一份被冻结的产物钉住了一个单调前进的计数器**，它在每种环境里都红（第六节）。

---

# 一、`e8-ic3-scale`：8+1 个 hunk 全部可解，卡住它的那一行不在任何 hunk 里

## 数字（逐字，注意下面那个陷阱）

| 树 | pytest 摘要 |
|---|---|
| 对照，干净 master `50e10617` | `554 passed, 27 skipped in 48.57s`（exit 0） |
| 我的解，`c04e6e6d` | `1 failed, 788 passed, 27 skipped in 452.66s`（exit 1） |

**先说一个会污染历史结论的操作陷阱**：`engine-rig/pytest.ini` 里已经写了 `addopts = -q`，
所以 CLAUDE.md 记的 `python -m pytest -q` **实际跑的是 `-qq`，它把摘要行整个吞掉**
——只剩进度点，没有计数。**此前几轮凭这条命令报「绿」的，最好情况也只是在读退出码。**
用 `python -m pytest --tb=line` 才拿得到计数。
**顺带：CLAUDE.md 写的「150 tests pass, 1 skipped」已经差了约 4 倍**（现在 554）。
CLAUDE.md 是契约，按 CHARTER 我不改，报给你。

## 九个 hunk

**8 个是机械的**（两边各加各的，并集显然正确：docstring 条目、常量表、import 列表、
两个不同函数落在同一偏移、两个合取项、四个计数键）。

**第 9 个（`recheck/build_cases.py:140` 的 `peg_ruleset` 签名）看着是语义冲突，其实是可判定的**：
两边**已提交的** case 文件对 provenance 形状意见相反
（`peg5-11011-to-01000.rules.json` 带 `hand_verified` + 长 prose；
`peg5-01111.rules.json` 带 `anchor` + 裸 `interop/peg1d.py`），
**而两个文件都在合并后的树里，所以是已提交的字节决定了判别式，不是我挑的。**
`python -m recheck.build_cases --check` → **`51 cases, 0 drifted`**。

**而且这个 oracle 是被变异测试过的，不是被信任的**：扰动一个 provenance 字符串 →
`51 cases, 4 drifted`、exit 1；改回去 → 0。它确实在读已提交的字节。

`python -m recheck.verify_all` → **`VERDICT GREEN`**，E6 的 pagoda 行（`3 of 3 certificates pass`）
与 E8 的梯度行（`peg4`…`peg13`，最高 `180224/180224 edges agree with peg1d`）**同时在场且都过**。
**所以这两个特性是真的能共存——这一次不是 E15/E17 那种「合得干净、合出来是坏的」。**

## 唯一那条红，以及它为什么不在任何 hunk 里

失败的是 `test_recheck_never_imports_the_engines`
（`engine-rig/tests/test_recheck.py:622`，`forbidden = ("engines", "tools.", "interop")`，
实现是对 `recheck/*.py` 的 import 行做**字面子串扫描**）：

```
AssertionError: ['verify_all.py: from interop import peg1d']
```

* `interop` 是 **E6 在 master 那侧**加进这个元组的；**分支从没碰过 `test_recheck.py`**。
* **出事的那一行在 `verify_all.py:47`，在所有 9 个冲突 hunk 之外——git 自动合并了它，一声不响。**
  **所以 9 个 hunk 怎么解都影响不到它。** 这是「git 对唯一要紧的那个文件毫无意见」的**第四次**。

## 规则相对它自己写下的理由是过宽的（这条是本节最有后果的）

实测 `from interop import peg1d` 的传递 import 闭包，**恰好是**
`['interop', 'interop.peg1d', 'typing']`——**没有 `engines`，没有 `tools`**。
`interop/peg1d.py` 只 import `collections.deque` 与 `typing`。
E6 自己的 docstring 给这条禁令的理由是
`interop/certificate_export.py` import 了 `engines.lp_potential.potential`——**而 `peg1d` 没有**。

**于是：这条规则要保护的那个独立性属性是完好的，被违反的是规则的字面。**

**这不归我裁。** 收窄 E6 的规则（比如只禁 `interop.certificate_export`，
或把子串扫描换成 import 图检查）还是让 E8 挪自己的锚点，是领地主人的判断。
但**一旦裁了，代价是单侧且便宜的：不需要改任何代码，只需要改那个元组或那一行 import。**
（对抗组正在打这条：`sys.modules` 增量测不到**函数体内的惰性 import**，我已要求它去找。）

## 我要更正一条跨周期活下来的假话

cycle 21 报的「`.worktrees/opsm21-e8` 的 `585099f8`：9 个 hunk 里 8 个机械、已解并跑绿」——
**`585099f8` 自己的提交信息写着「tree is RED」。** hunk 数（9）与那条语义发现都复现了，
**但「跑绿」是假的，而它跨了四个周期没人回去重读那个产物。**
这正是我这轮给每个对抗组都写进简报的那句话的出处。

---

# 二、`freeze` 闸门：它在队列里**按构造**不可能通过

## 先更正我自己今天犯的一个错

我今天把 `s4-e23-tiers` 当作**独立的第二个数据点**发给诊断组（「不同作者、不同 base、
第一次尝试」）。**这是假的**：
`git merge-base origin/agent/s4-freeze origin/agent/s4-e23-tiers` = **s4-freeze 自己的 tip**。
同一个作者 `t`，e23 = s4-freeze + 2 个提交，**严格串行**。
`attempts: 1` 只意味着一个新分支名，不是一次新鲜独立的尝试。
**我从 flag 的元数据（不同的 `base:` 字段、attempts=1）推出了「独立」，而没有查祖先关系。**
和我这轮其他几次是同一个形状：**伸手去拿一个不需要测量就能成立的结论。**

## 分支是无辜的，而且 flag 记的红有一半已经被作者修好了

| | flag 记的 | 实测 |
|---|---|---|
| `origin/master` | `5439d07f` | **`3d59d0a6`**（我开机时量的 `50e10617` 也已过期） |
| `s4-freeze` tip | `fde0f2aa` | **`f47b6b30`**，新了 2 个提交，**作者活跃** |

* **`MANIFEST.json has drifted` 那条 FAIL 已经没了。** stage 12 在合并后的树上 **PASS**。
  作者在 `f47b6b30` 修的（提交信息：「MANIFEST 重生成，这次在干净树上——前一版的 dirty 就写着 true」）。
  **flag 记的双 FAIL 是对着一个已被取代的 tip 记下的。**
* 干净 master 上 `freeze/verify.sh` **exit 0，绿**——但**是靠缺席绿的**：
  master 的 `verify.sh` **根本没有 BUDGET_TABLE 这一级**，stage 15b 是**分支引入的**（+753 行）。
* 而那个检查本身对着干净 master 跑：
  `python freeze/build_budget_table.py --verify` → **exit 1**，
  `sections that moved: balance, citations, pool, verdict`。
  **master 已提交的 `BUDGET_TABLE.json` 本来就是漂的，一条分支都没合。**
  分支没弄坏它，**分支只是把报告它的那个检查接上了电**。

## `POOL ABSENT` 是环境性的——用指纹证的，不是推的

`build_budget_table.py:78 resolve_pool()` 相对**主 checkout** 解析 pool，
会从 `.worktrees/<id>/` 里向上走出去（这是刻意的，`proxy/SPEND_GATE.md:219-226`：
一个工作树一个 pool 曾经是一次 **$10,959.90** 的缺陷）。替换 `REPO` 实测：

```
REPO=...\.worktrees\opsm25-freeze         -> ...\theoria\proxy\var\spend_gate.jsonl
REPO=C:\Users\user\Desktop\theoria        -> ...\theoria\proxy\var\spend_gate.jsonl
REPO=C:\Users\...\Temp\ci-merge-livyq4tp  -> None
```

**队列跑在 `%TEMP%\ci-merge-*` 里，那不在 `.worktrees/` 之下，所以那次向上走永远不触发。**

**指纹对上了**：pool 在场 → 移动 3 个 section（`balance, pool, verdict`）；
pool 缺席 → **4 个**（`balance, pool, projection, verdict`）；
**队列记下的红正是那 4 个。**

## 而且逃生口存在、但没接线、而且不工作

`--allow-absent-pool`（`build_budget_table.py:1118`）**仍然返回 RC=1**
（它在比较器里什么都没抑制），并且 `grep -n allow-absent-pool freeze/verify.sh` → **0 命中**。

## 漂的每一个字段都是 pool 派生的，而且它在**持续**漂

```
pool.lines 12929 -> 13309    pool.actions 5737 -> 6264    balance.actions_remaining 18263 -> 17736
verdict.statement 只差 "action headroom (18263 requests)" 这一处
```

**我自己两次相隔几分钟的运行之间，`actions_remaining` 从 17736 变成 17718。**
`proxy/var/spend_gate.jsonl` 被 gitignore，每次代理调用都往里追加。
**所以「重新生成一遍」修不了它——那只是把一个立刻重新开始走的钟拨回零。**

## 「负控没跑」那条 NOTE：我原来的怀疑是错的

我给诊断组写的是「闸门自己承认负控没跑 = 它在发一个判别力未经验证的红，这是最该查的」。
**实测下来它是一个正确的守卫，而且是诚实报告的**：`verify.sh:1179-1191`，
负控只在「搬迁副本先是绿的」时才跑，
**因为一个要求「已经是红的检查」返回非零的控制实验，无论变异什么都会「通过」。**
作者把这个理由逐字写在 `verify.sh:1166-1169`。**我收回那句怀疑。**

但**那个尖锐的问题仍然有一个难看的答案**：
* **在合并队列里：15b 没有任何判别力。** 它对每一个 checkout 无条件开火，与内容无关，
  **而它自己负控的前置条件在队列里不可达，所以它永远无法自证。**
* 在 pool 在场的 checkout 里：部分有。`verify.sh:1069` 自己写着
  *"15b goes red on its own after any spend, with no edit anywhere."*

## `v5-battery-freeze`：结论确认，**理由被推翻**

我此前的裁决说「谁都合不绿，因为 `freeze.FREEZE` 钉住了 `battery/verify.py`」。
**那不是真正的约束**：解法（a）「原样取 V5 的 `verify.py`」**恰好满足那个钉子**，
而且 `battery/verify.py` **从没出现在失败列表里**。

真正的阻塞是 **`battery/BATTERY_V1.md` 与 master 当前 `battery/` 树之间的 35 项漂移**：
8 个被冻结的文件在 V5 冻结之后**在 master 上被就地改过**；约 24 个文件加进 `battery/`
**却没有任何 freeze bucket**（整个 `battery/audit/v9/` 树、`PREREG_V9.md`、`BLINDING.md`、4 个 `test_v9_*.py`…）。

**V5 单独跑自己的闸门是干净的**：`VERIFY PASS`，exit 0，`237 passed`。
它的 diff 是 7 个文件、全是新增、不碰任何漂移文件。**35 项全部由 master 侧的演化产生。**

**所以作者要做的事比我原来说的更大**：不是「因为 verify.py 变了所以升 BATTERY_V2」，
而是**对着当前 master 重新冻结整个领地**，包括给 `battery/audit/v9/` 建桶（它在任何类别里都没有桶）。
**仍然是作者的活，不是合并裁判的活，而作者已经 32 小时没出现。**

---

# 三、需要派单的（我都不能自己做）

1. **freeze 闸门的环境缺陷（最要紧，且不是任何分支的错）** —— 二选一：
   让队列在 `.worktrees/` 下建合并树（`ci_merge.py` 现在用 `%TEMP%\ci-merge-*`），
   **或**让 `--allow-absent-pool` 真的把 `pool/balance/projection/verdict` 排除掉、
   并让 `verify.sh` 传它。**不修这条，任何碰 freeze/ 的分支都不可能通过队列。**
   （对抗组正在查一个能一票否决我的历史问题：**merge.log 里到底有没有过成功的 `verify:freeze` 合并**。
   有，则我这条当场被推翻；没有，则是强确认。数出来我就报。）
2. **`s4-freeze` 的 flag 应该被清掉重排**：它记的双 FAIL 里有一条已被作者修好，
   tip 也动了。队列的 HELD 判据比的是 tip，所以它**会**自己重排——但 `reason` 字段
   记的永远是**第一次**撞到的东西，从不更新成真正卡住的东西。这条我 cycle 21 提过，重申。
3. **`v5` 转派或关掉**（tip 32 小时没动），并把「重新冻结整个 battery 领地」作为工单内容，
   而不是我原来说的「升 BATTERY_V2」——**后者会让接手的人低估工作量**。
4. **E6/E8 的 `interop` 禁令**由 engine-rig 领地主人裁：收窄规则，或让 E8 挪 import。
5. **CLAUDE.md 两处过期**（`pytest -q` 因 `pytest.ini` 变成 `-qq` 吞摘要；「150 tests」实为 554）——契约，只有你能改。

# 四、还没定的

* `verify:freeze` 历史上有没有成功合并过（对抗组在数）。
* stage 12 在**真正的** `%TEMP%\ci-merge-*` checkout 里过不过（诊断组没往队列目录里写，是对的）。
* master 那份 BUDGET_TABLE 漂移里有多少是**机器本地**的：pool 那半依赖本机 pool 已经前进，
  **只有 citation 那半（`STATS_RULES.md:777/791`）是纯树内、任何机器都复现**。
  所以「master 自己就是漂的」这句**有一半不是机器无关的**，我按原样记下这个保留。
* `peg1d` 有没有函数级惰性 import 能通到 `engines`（对抗组在找）。

# 产物

`.worktrees/opsm25-e8`（`c04e6e6d`，提交信息前缀 **DO-NOT-LAND**）、
`opsm25-fz-b`（干净 `3d59d0a6`）、`opsm25-freeze`、`opsm25-e23`、`opsm25-v5`、`opsm25-v5b`、`opsm25-v5solo`。
全部未推送、未碰 `monitor/`、零 API 花费、未删或放松任何 freeze 登记、未重新生成任何 `BUDGET_TABLE`。

---

# 五、e8 的对抗复核（2026-07-30T04:27:11Z）：挡住 E8 的那个闸门本身是不健全的

对抗组把我的 E7（「规则过宽，被保护的属性完好」）**打不动**，
但它顺手证明了一件比 E7 严重得多、而我完全没问的事。

## 5.1 最重的一条：**这个闸门执行不了它声称执行的属性**（在干净 master 上实证，不是模拟）

对抗组往干净 master 的 `recheck/anchors.py` 里注入了模块级的、活的引擎 import：

```python
import importlib
from tools import validate_candidates as _evade1
_evade2 = importlib.import_module('engines.lp_potential.potential')
```

——**注入的正是 E6 docstring 点名说「不可达」的那个模块**——然后跑守卫：**`1 passed`。**

两个真洞：

1. `forbidden` 里写的是 **`"tools."`（带尾点）**，于是 `from tools import run_all`
   与 `import tools`（**引入 `engine-rig/tools/` 这个真实存在的包的自然写法**）**漏过**，
   而 `import mytools.helper` **反而被抓**。
2. 扫描只看以 `"import "` / `"from "` 开头的行，于是
   `importlib.import_module`、`__import__`、`exec`、反斜杠续行的 import **全部隐形**。

并且它**对称地过度匹配**：注释（`import json  # see tools.run_all`）、
符号名（`…import RuleSet, engines_count`）、别名（`…as interop_shim`）**都会触发**。

**所以这件事不是「过宽的规则 vs 合规的分支」。**
**一个不健全的闸门，正在卡住全树里唯一一个可证明到不了引擎的 import，
而它会原样放行真正的违规。** 无论 E8 怎么处置，**这个闸门都需要换成基于 AST 的实现**；
**E8 的红不构成任何独立性被破坏的证据。**

## 5.2 E7 全须全尾地站住了

对抗组按我指的那条线（`sys.modules` 增量测不到函数体内惰性 import）去挖：
`interop/__init__.py` **是空的**；`peg1d.py` 118 行，只在模块顶部 import
`collections.deque` 与 `typing`。全文 + AST 复核：
**无函数级 import、无 `importlib`、无 `__import__`、无 `__getattr__` 钩子、
无 `exec`/`eval`、无条件或 `try` 包裹的 import、无 `sys.path` 操作。**

> **攻击线 1 的答案：`peg1d` 到 `engines`/`tools` 之间，
> 无论 import 时还是调用时，都不存在任何路径。E8 违反的是字面，不是原则。**

## 5.3 我的裁决被放宽了一格：**存在便宜的分支侧修法，不必等领地主人**

我写「9 个 hunk 怎么解都影响不到它，所以要领地主人裁」——**后半句太悲观**。
`recheck/anchors.py:46` 逐字写着被认可的模式：

> *"It reads files under `interop/`; it imports nothing from there."*

**E8 可以把 peg1d 的几何结果作为已提交产物落到 `interop/` 下，
让 `verify_all` 去「读」而不是「import」**，与 `anchors.py` 读 `interop/certificates/` 完全同构。
便宜、合原则、纯分支侧、不需要改任何规则。
（**两条不行的路**：把 import 挪进函数体——扫描会剥空白，照样抓；
把 peg1d vendored 进 `recheck/`——那会摧毁这个锚点的意义，它要求 peg1d 是**外部**产物。）

## 5.4 三条被削弱的（我原文说强了）

| 我写的 | 修正 |
|---|---|
| `check()` 是个被变异测试过的真 oracle | **单向的**。它只遍历 `all_cases()`（生成器输出），**从不枚举目录**。往 `recheck/cases/` 丢一个无人引用的 `.json`，`--check` 照样 `51 cases, 0 drifted`、exit 0。「51 cases」是**生成器计数不是文件计数**。今天目录实际是干净的（人工核对 51==51、无多无少），**但这个 oracle 证明不了它** |
| `VERDICT GREEN`，两个特性真的能共存 | 共存是真的（`peg_ruleset` 同时生成两边的 case）。**但 E8 那 7 行梯度全部是「空洞地通过」**：`peg1d=None derived=None hand=None`，而 `None == None` → True。11 行里**只有 1 行有判别力，而那是 master 的行**（`peg4-1101`, 2/2/2）。（那些 `None` 是真的不可解，所以**不是 bug**。）**E8 真正在检查的东西全在另一个 `peg_relation` 锚点里**（192/192 … 180224/180224 条边），那个是实的 |
| 27 个 skip 相同 ⇒ 无 FD/`.toolchain` 交互 | 结论对（**skip 集合按测试名逐一相同**，不只是计数相同），**但理由过宽**：27 个里只有 **15** 个是 Fast Downward，另 **12** 个是 `test_tool_failure_is_not_truth.py:349` |

## 5.5 `candidates.jsonl`：无违约（我上一节列为未确定的那条）

合并改动的 50 个文件里**零个** `candidates*.jsonl`、**零个** `/CONTRACTS/` 路径；
文件与 master **逐字节相同**。合并树上
`python -m tools.validate_candidates artifacts/candidates.jsonl` → **`OK (44 rows)`**，exit 0。

## 5.6 唯一一条**对 E8 不利**、而且没有任何人提过的

**这条分支让 `peg1d` 变成了一个共享叶子。**
master 的 `certificate_export.py` 里 peg1d 出现 0 次；合并后它 import
`engines.ic3_pdr.system`（新）、`engines.lp_potential.potential`、**以及 `from interop import peg1d`**，
并在 `verify_ic3`（399–411 行）里调用它。而 master 的 `verify_all.py` 里 peg1d 也是 0 次，
分支把它加成了 recheck 的「独立」预言机。**同一个几何模块同时站在生产侧和校验侧。**

**这个圈今天没有闭合**——recheck 只请求三份 `pagoda_*` 文档，
而 `verify_ic3` 用 peg1d 的那条路只有分支自己的测试在读。
**但 `verify_all.py:358` 已经在输出 `"why": "…sharing no code with this package"`，
这句话的真值条件是「没有人拿 `ic3_*` 文档去锚定 recheck」。**

**这才是实质性的独立性问题，而那条字面规则量的根本不是它。**

## 5.7 修正后的处置

1. **给 `test_recheck_never_imports_the_engines` 换 AST 实现**（engine-rig 领地）。
   这条**独立于 E8 怎么处置**，因为现在的实现放行真违规、卡住假违规。
2. **E8 可以自己解开自己**（5.3 的读-而非-import 路径）——不必等裁决。
3. **把 5.6 那条共享叶子写进工单**：不是今天的红，但 `verify_all.py:358` 那句
   独立性声称的真值条件应该被显式钉住，否则它会在没人注意时变成假的。
4. `check()` 的单向性（5.4 第一行）值得补一个目录枚举方向。

## 5.8 对抗组的合规

两个工作树**都已删除**；无提交、无 tag、无分支（`--contains` 均为空）；未推送；
未碰 `monitor/`；零网络、零 API、无封存材料；注入的测试变异全部还原并复验干净。

---

# 六、freeze 的对抗复核（2026-07-30T04:28:33Z）：**我的中心论断被推翻了，处置方向反过来**

我在第二节写的「freeze 闸门在队列里**按构造**不可能通过」——**这条是错的**。
而且我用来证明它的那个「指纹」也是错的。**这一节推翻上面第二节，以本节为准。**

## 6.1 `--allow-absent-pool` 是工作的；我说它「什么都没抑制」是假的

`build_budget_table.py:1168` 就是 `if not args.allow_absent_pool: rc = 1`。
对抗组在**队列自己的环境形状**里实测：

```
--verify                      -> RC = 1   (POOL ABSENT)
--verify --allow-absent-pool  -> RC = 0   "freeze/BUDGET_TABLE.{json,md} still describes this tree"
```

**所以这不是「按构造不可通过」，是「按接线不可通过」**——
`verify.sh` 从不传这个 flag（0 命中，这半我说对了）。
**这是一个闸门脚本里少传一个 flag 的缺口，不是一个必须被原谅的环境缺陷。**
我把「一行没接的线」升格成了「结构性不可能」。

## 6.2 我那个「指纹」没有判别力——**它是阈值探测器，被我读成了在场探测器**

我写：pool 在场 → 3 个 section，pool 缺席 → 4 个（多 `projection`），
而队列记的正是 4 个，所以队列是 pool 缺席的。

**`projection` 在两种情况下唯一不同的字段是 `fits_action_ceiling`，
它是一个比较：`row["arc_requests"] <= balance["actions_remaining"]`。**
阈值是 `[6737, 10636, 15253, 151014, …]`，当前 `actions_remaining` = **17,718**，
最近的下方阈值 **15,253**，**余量只有 2,465 个 action**。
而 pool 在「已提交的表」与「现在」之间已经走了 **545** 个 action。

**再过大约 4.5 个同样长的间隔，一个 pool 在场的运行就会输出完全相同的 4 个 section。**

**而且这个推断从头到尾就不需要**：队列的 transcript 里逐字印着
`POOL ABSENT: the pool is gitignored (proxy/.gitignore:3) and this checkout does not have one`。
**我用一个偶然成立的巧妙推断，去重新推导 flag 里已经明说的事实。**
这是我这轮第三次同一形状：**伸手拿一个不需要测量就能成立的解释。**

## 6.3 最要紧的一条：**环境根本不是起作用的原因**

对抗组在合并后的树上**把 pool 强制设为在场**，闸门**仍然是红的**：
`moved: balance, pool, verdict`，已提交 `actions_remaining` 18,263 vs 现场 17,718。

> **把我指控的那个缺陷去掉，这条分支照样不绿。**

**真正的阻塞是我写在第二节里却没当回事的那条（H5）：
一个被冻结的产物，钉住了一个单调前进的计数器。它在每一种环境里都红。**
**我诊断了环境，而故障是时间性的。**

（诚实的张力：要让队列变绿，已提交的表**也必须是 pool 缺席时生成的**，
那会发布一份每个 balance 数字都是 `None` 的表。
所以准确的说法是「这份产物只能与两种环境中的一种自洽」，
**不是**「在队列里按构造不可通过」。）

## 6.4 `s4-freeze` 的 flag 是活的，不是陈旧的——我又一次照过期观察发布

我写「flag 记的双 FAIL 是对着一个已被取代的 tip（`fde0f2aa`）记下的」。
**实测：现场 flag 记的 tip 就是 `f47b6b30`（当前 tip），`last_seen: 2026-07-30T04:06:01Z`，
`attempts: 7`，而且它的 cause 段里只有一条失败，就是 BUDGET_TABLE，不是 MANIFEST。**
`fde0f2aa` 在该文件被跟踪的历史里根本没出现过。

**我 03:44Z 读了 flag，04:0x 队列自己更新了它，我照 03:44Z 那份写结论。**
**这是 cycle 19「我 18:16Z ls 完、18:22Z 照那次 ls 发结论」的同一形态，第二次。**
（stage 12 确实过——对抗组在队列的真实环境形状里跑了，我列为未确定的那个洞已堵上。
但**这不让分支能落地**，因为红的是另一条。）

## 6.5 两条我说反了/说轻了的

| 我写的 | 实际 |
|---|---|
| master 的漂移「有一半不是机器无关的」，所以「master 自己就是漂的」要打折 | **反了。** 强制 pool 缺席（即全新克隆 / 队列的条件）后，干净 master 漂 **5** 个 section（`balance, citations, pool, projection, verdict`），citation 列表不变。**全新克隆让 master 的漂移更严重，不是更轻。**「master 自己的 bug」是被我**低估**了 |
| 负控 NOTE「是正确守卫，我收回怀疑」 | 逻辑确实正确、报告确实诚实——**但它的肯定分支在 CI 里永久不可达**（`verify.sh:1179` 用不带 flag 的 `--verify` 做前置，而队列每次都 pool 缺席）。**所以 15b 交付到 CI 后是一个判别力恒为零的闸门，而那行 NOTE 每次都在如实印出这件事** |

## 6.6 历史：`verify:freeze` 成功合并过 5 次（我请对抗组去数的那个可能一票否决我的数）

merge.log 里 `MERGED … gates: verify:freeze(verify.sh)` 共 **5** 条，
**其中 3 条就是 `s4-freeze` 自己**（07-29 15:08 / 16:02 / 21:28），
另两条是 `p22-freeze-kit` 与 `p17-machine-checked-ruling`。
**但那 5 棵树里都没有 stage 15b**（`72424bc7`/`af448eb4`/`db966b26` 都不是 `origin/master` 的祖先）。
所以**历史本身不能推翻我，是直接实验推翻的**——我把这条记下来，因为它说明
「找一个反例」和「找一个**可比的**反例」是两件事。

## 6.7 V5：结论站住，但有一条**为作者辩护**的重要改写

H8 的每一条可核查断言都站住了（V5 单独 `EXIT=0`、`237 passed`；
`battery/verify.py` 确实被 FREEZE 钉住且**从未出现在失败列表**，我原裁决的理由确实被推翻；
35 项漂移**不是虚高**：8 就地改 + 26 无桶 + 1；
且 `unlisted()` 只跳过 `__pycache__`/`.pytest_cache`/`runs`，**不存在「默认在范围外」的文件**）。

**补充一条 H8 漏了的**：合并后的闸门**还**有 `tests: battery/tests` 4 条红。

**而这条改写最要紧**：**`battery/BATTERY_V1.md` 在 `origin/master` 上根本不存在**——
那份冻结记录**只活在 V5 分支上**。那 8 处「就地修改被冻结文件」来自
`520dc5dd`（作者 `engine-rig`，07-29 10:11）与 `1fd01893`（作者 `t`，23:07），
而 V5 是同一天 03:46 在一条**从未落地的分支**上冻结的。

> **没有任何人可能知道那些文件被冻结了。这条指控事实上准确，规范上是空的。**

派单时请把这句写进去：**不要把这 35 项写成「有人违反了冻结」**，
它是「一份还没上主线的冻结记录，与主线的正常演化不一致」。

## 6.8 修正后的处置（取代第三节第 1 条）

1. **不要**去改队列让它在 `.worktrees/` 下建树——**那修不好这条分支**（6.3）。
2. **真正的问题是 `freeze/BUDGET_TABLE` 钉住了一个单调前进的计数器。**
   这需要一个设计裁决：要么把 pool 派生的字段移出被冻结的产物，
   要么接受「这份表只与一种环境自洽」并显式声明是哪一种。**这是 freeze 领地的活。**
3. `verify.sh` 没传 `--allow-absent-pool` 是一个**独立的、真实的、一行的**缺口（6.1），
   值得单独修——但**修了它也不足以让这条分支绿**（6.3）。
4. 15b 的负控在 CI 里永久不可达（6.5），值得单独立项。

## 6.9 对抗组的合规

两个工作树均已删除；其新建的合并提交 `f0714495` **无引用**（`rev-list --all` 0 命中），会被 GC；
未建 tag、未建分支、未推送；唯一一次 `BUDGET_TABLE` 重生成在**明确声明的一次性副本**里，
已 `git checkout -- freeze/` 还原并连工作树删除；主 checkout `git status --porcelain freeze/ battery/` 为空；
`monitor/` 只读；`%TEMP%\ci-merge-*` 从未触碰；零网络、零 API、无封存材料。
