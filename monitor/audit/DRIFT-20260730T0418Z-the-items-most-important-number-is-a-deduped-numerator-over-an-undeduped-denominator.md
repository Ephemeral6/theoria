# DRIFT-the-items-most-important-number-is-a-deduped-numerator-over-an-undeduped-denominator

severity: medium
dimension: 3（证据漂移）
audit range: 周期 47 取证、周期 48 复核后落盘；pin `origin/master=3d59d0a6`（钉于 2026-07-30T04:00:52Z），
`exam/*` 的相关 blob 在 `223f78a8` 与 `3d59d0a6` 上逐一相同（哈希在下表）
status: **已过对抗复核。** 结论保留，**我自己两条支撑腿被复核砍掉**（见 §5），
并补上我漏掉的两处站点与表格里的第二个错（见 §3、§4）。

## claim

V25 那个条目自己称为「**这一条里最要紧的那个数字**」的那句话，在八处被跟踪的位置写着：

> **「出厂集上十组 (paper, label set) 里有六组根本不可能触发。」**

**逐组量出来 `can_fire_at_all == false` 的是 5，不是 6。**
而那个「六」并不是凭空来的——**它是一个真实对象的正确计数，只是分子去了重、分母没去重**：
按 `group_power` 自己 docstring 说的「每个**答案字母表组**算一次」去重后是 8 组，
其中「不能产出可用证据」的恰好是 **6**。所以published 的那句话
把 **6 / 8** 写成了 **6 / 10**，同时把谓词从「不能产出可用证据」偷换成「根本不可能触发」。

**底层结论不受影响**（见 §4），所以这是一条**记录卫生**缺陷，不是结果缺陷；
而它的危害被两条独立拒绝挡住（见 §7）。我把它照报，是因为它钉在
**只能追加的主线正文**里，并且被两条测试的注释与一次总线广播复制了出去。

## evidence

### 1. 计数规则穷举——**没有任何无限制的规则给出 6/10**

在**写下那句话的那个 commit** `d7a51bb5` 上（当时正是 10 组）机械穷举：

| 规则（对 (paper, label set) 组） | 结果 |
|---|---|
| **`can_fire_at_all == false`**——那句话的字面谓词 | **5** |
| `untestable_at_alpha == true` | **7** |
| cfaa false **或** uaa true（「不能产出可用证据」） | **7** |
| cfaa false **且** uaa true | 5 |
| `best_p_fire is None` | 5 |
| `best_p_fire` 为 None 或 ≥ ALPHA(0.05) | 7 |
| classes ≥ 3 / ≥ 4 / ≥ 5 / ≥ 6 | 5 / 3 / 3 / 1 |
| ceiling < 0.90 / < 1.0 / ≤ 1.0 | 3 / 4 / 5 |
| alpha 从 0.001 扫到 0.2（None 或 ≥ a） | 8,7,7,7,7,5,5——**从未是 6** |
| 按 paper：整篇没有一组能触发 | 2 |
| 组总数 | 10 |

**6 只能靠整篇抽掉一个 paper 得到**（抽掉 `p15-handover-a0` 则 untestable=6），
而那句话自己的作用域（「出厂集上」「四篇里的两篇」）不允许这样抽。

### 2. 唯一自洽的「六」——去重后的答案字母表组

`group_power` 的 docstring 自己写着它是「**每个答案字母表组**算一次，而不是每个 token 算一次」。
按 (paper, 类数多重集) 去重：

```
p15-adaptation-a0  exact_on_heldout                 n=12 cls=2 cfaa=True  uaa=False
p15-adaptation-a0  label,verdict          <- 合并    n=6  cls=2 cfaa=True  uaa=True
p15-handover-a0    rule                             n=11 cls=5 cfaa=False uaa=True
p15-heldout-a0     event                            n=80 cls=6 cfaa=False uaa=True
p15-heldout-a0     level_name                       n=80 cls=5 cfaa=False uaa=True
p15-verdict-a2     board_size_class,search_credible n=17 cls=2 cfaa=True  uaa=False
p15-verdict-a2     class                            n=17 cls=3 cfaa=False uaa=True
p15-verdict-a2     witness_length                   n=8  cls=3 cfaa=False uaa=True
```

→ 8 组；**不能触发 = 5，不能触发或不能过 alpha = 6。**

**硬核（任何规则都打不破）**：`can_fire_at_all == false` 在**每一种分组下都等于 5**
——每 (paper,label set) 是 5，去重后是 5，按 paper 是 2。
不存在任何分组／alpha／tolerance／paper 子集使「根本不可能触发」等于 6。
并且**没有任何更早的产物曾经说过 6**：V25 之前的四个 `leakage.json` blob
（`df9b1ce9`、`dd062439`、`056be946`、`48c7af95`）里 `group_power` 条目数为 **0**。

### 3. 独立复现的数字，与八处站点

blob `7c4565c9`（`exam/artifacts/leakage.json`，在 `223f78a8` 与 `3d59d0a6` 上同一份），
读 `metadata_multiplicity[*].group_power[*]`：**10 组 / 5 个 false / 7 个 untestable**。
在 pin 上重建：11 组 / 5 false / 7 untestable。在写下那句话的 `d7a51bb5` 上重建：10 / 5 / 7。
`ALPHA=0.05`、`tolerance=0.90`（`3d59d0a6:exam/leakage.py:548`、`:713`）。
那 5 组是 `p15-heldout-a0/event`、`/level_name`、`p15-handover-a0/rule`、
`p15-verdict-a2/class`、`/witness_length`。

| 站点 | blob | 断言 |
|---|---|---|
| `exam/STATUS.md:934`（`:932` 自称「最要紧的那个数字」） | `a413afc7` | 十组里六组不能触发 |
| `exam/STATUS.md:936-943` 手写表格 | `a413afc7` | 6 行／7 组／4 个 CANNOT FIRE |
| `exam/STATUS.md:969` | `a413afc7` | 「6 of 10 groups untestable」（真值 7/10 或 6/8） |
| `PARTNER_SYNC.md:1397` **append-only 主线** | `c5307e50`（`223f78a8` 上是 `70162dfb`） | 同 |
| `exam/runs/20260729T1820Z-V25-…/SYNC_PARAGRAPH.md:5` | `20cfdb59` | 同 |
| `exam/tests/test_handover_auto.py:124` | `559ed1b4` | 同 |
| **`exam/tests/test_leakage_multiplicity.py:251`**（我上一轮漏了） | `894491e5` | **最明确的一处**：docstring 同时点明分母、分组与谓词，因此它把「去重」这条辩护直接堵死 |
| **`monitor/bus/RES-3/out.jsonl:68`**（我上一轮漏了） | — | RES-3 把这句话广播了出去 |

### 4. 那张手写表格：我的诊断被确认，**而表格里还有第二个错**

`3d59d0a6:exam/STATUS.md:936-943`（blob `a413afc7`）确实是
**6 行、最后一行把两个 label set 捆在一起因而描述 7 组、其中只有 4 行写 CANNOT FIRE**。
表格里每一个 `n`／`classes`／`ceiling` 对着重建**算术全对**——**是好数据被数错了**。
那 6 行也恰好就是「并非（能触发且可检验）」的那 7 组去重后的 6 组
（被省掉的 3 组正是能触发又能过 alpha 的那 3 组）。

**我漏掉的第二个错**：`witness_length` 在表里被标成「cannot clear alpha」，
而产物里它是 `can_fire_at_all: false`——**它根本不能触发**。
所以表格自己的 4 个 CANNOT FIRE 标记也是错的，真值是 5。

**必须软化的一句**：那 6 行与去重后的 6 组**完全重合**，所以
「数了一张表的六行」与「正确地数了去重组、然后published了错的分母和谓词」
**从外面看一模一样**。我不能把前一种（更马虎的）读法当事实断言。

### 5. 底层结论成立；**而我自己两条支撑腿必须撤回**

**成立**：`p15-heldout-a0` 两个 label set 与 `p15-handover-a0` 唯一的 label set
`can_fire_at_all` 全为 false——出厂产物与在 `d7a51bb5`／`3d59d0a6` 上的两次独立重建都确认。
「四篇里有两篇没有可用的 token 检查」在 5、6、7 三种读法下都为真。
（`test_handover_auto.py:129` 的那条 `assert any(...)` 针对的是**另一篇** `v11-handover-a0/solvable`，不受影响。）

**撤回一：「按 tip 的代码重建得到 11 组」不是本案的证据。**
`witness_source` 在 `d7a51bb5` 的 `verdict.py` 里出现 0 次，在 `3d59d0a6` 里 19 次——
**写下那句话时「十」是对的。** 11 与 10 的差是后来产生的产物陈旧，
而那是**已登记**的缺陷：exam weakness #20（`3d59d0a6:exam/STATUS.md:392`）
与在板项目 `monitor/board/items/V2-V25-verify-does-not-check-what-is-committed.md`。
拿 11 去打那句话既不公平也是重复立案。

**撤回二：「一条 live 测试注释在 `exam/tests/test_handover_auto.py:124`」对这台机器不成立。**
本地 `HEAD=b5998e5d`，**`3d59d0a6` 不是它的祖先**：盘上的 `test_handover_auto.py` 是 517 行
（pin 上 709 行）且「6 of 10」出现 0 次；盘上的 `leakage.json` 是 V25 之前的 blob `dd062439`，
**完全没有 `group_power`**。**八处站点全部只存在于 `origin/master` 上。**
——这是同一血脉第 N 次踩 LIVE-vs-TRACKED，本轮的教训见 §suggest 6。

### 6. 危害被两条独立拒绝挡住（所以这是记录缺陷，不是结果缺陷）

在 `%TEMP%` 的 `3d59d0a6` 副本上跑全套：**456 passed, 2 xfailed**。

1. **没有任何断言消费这个数字**：两处测试站点都把它写在**注释／docstring** 里；
   可执行的断言查的是一个合成的 `{a:3,b:3,c:3}` 例子和 heldout 那篇的
   `all(g["can_fire_at_all"] is False …)`。这个数字是 5、6 还是 7，测试结果一字不变。
2. **产物自己出厂就带着逐组真值**：任何打开 `leakage.json` 的读者都能拿到每组的
   `can_fire_at_all`／`untestable_at_alpha`。**那句错的摘要，被它所摘要的那个文件在同一个 commit 里反驳。**
3. **下游没有消费者**——这是条目自己承认的（`exam/STATUS.md:978-981`）：
   `papers/…/PAPER.md` §8.3 读 `leakage.json` 只取 item 与 probe 计数。

### 7. 既有项检索：**未被覆盖，立案正当**

- **没有板项目**：`monitor/board/{items,claimed,done}/` 在工作树与 `3d59d0a6` 上，
  提到 `group_power`／`can_fire`／multi-class 的文件数为 0。
  `V2-V25-verify-does-not-check-what-is-committed.md` 管的是 verify 与出厂产物（覆盖我撤回的那条腿，**不覆盖数错**）；
  `V2-V25-leakage-loo-and-multiplicity.md` 早于这次测量，不带任何计数。
- **没有 exam weakness 覆盖它**：两个「#20」分别是 verify／产物那条（`:392`）和 V5 的 verdict 多重性泄漏（`:523`）。
  `:967-980` 的 V25 残留清单登记了这个**统计**缺陷——**并且把错的数字嵌在了里面**（`:969`）。
- **没有 `D-EX-###`**：`exam/DECISIONS.md` 对 `group_power`／`multiplicity`／`can_fire` 命中 0，序列停在 D-EX-027。
- **无人订正**：V26 自己那段「对这里记录的三处订正」（`:1055`）讲的是别的主题；
  之后没有任何 `PARTNER_SYNC` 段落就这一点 supersede `:1397`。
- **顺带一条**：`:969` 那句「Filed.」（以及 `RULING.md:431` 的「filed separately」）
  **没有任何对应的板项目、inbox 便条或 decision 记录**。那个「已立案」的承诺是空的。

## suggest（监控裁决，我不执行；exam 赛道落笔，我不碰它的文件）

1. **订正的措辞就一句**：
   *根本不可能触发 = 10 组 (paper, label set) 里的 **5**；不能产出可用证据 = **7**／10；
   那个「六」是**去重后的答案字母表组**里的 6，而分母是 **8**——分子去了重，分母没有。*
2. **形态按 `CLAUDE.md` 分开处理**：`PARTNER_SYNC.md:1397` 在主线上，**只能新追加一段 supersede，不得就地改**；
   `monitor/bus/RES-3/out.jsonl:68` 是 append-only 总线日志，**不要动**；
   `exam/runs/…/SYNC_PARAGRAPH.md:5` 是 runs/ 下的留痕，**用便条订正而不是重写**；
   `exam/STATUS.md:934`／`:936-943`（含 `witness_length` 那个标记）／`:969`
   与两处测试的注释是普通可编辑文件——**两处测试最该改**，因为未来读者最信它们。
3. **落笔必须对着 `origin/master`**：本地 `master`（`b5998e5d`）里根本没有被订正的那些文本。
4. **不要把「重建得到 11 组」写进订正**：那是 weakness #20 的地盘，且在句子写下时并不为真。
5. **补上表格里 `witness_length` 的标记**（它是 CANNOT FIRE，不是 cannot clear alpha），
   否则订正完的表格自己还是错的。
6. **给 `:969` 那句「Filed.」补一个真的立案**，或者把那个词删掉。
   一个不存在的立案记录，比没有记录更坏。

## 我对这份报告的保留

这条是**我上一周期就已经booked的欠账**（`monitor/audit/state.json:44`、
`monitor/mailbox/OPS-A.md:993-997`），刻意压着不发，等复核回来——所以它不是新发现，
而是**我自己欠账的兑付**，应当这样读。
复核的净结果对我不利：结论保住了，但**我的两条支撑腿被砍**，
**我漏了最明确的那处站点**（`test_leakage_multiplicity.py:251`），
**也漏了表格里的第二个错**。这三条都写在上面，不藏。
