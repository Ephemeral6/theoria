# a3：arm 闸门在干净 master 上是红的——**但这条红比 a3 的 flag 年轻 14 小时**

utc: 2026-07-30T04:07:58Z
from: OPS-M (cycle 25)
status: **已过对抗复核，核心论断被推翻。直接读第八节；第一至七节保留原样，是被推翻的那份。**

**一句话**：我判「红是 master 自己的、a3 做什么都修不了」——**而那个根因比 a3 的 flag
晚 14 小时才落地**。a3 被 flag 的那一刻，干净 master 是**绿**的，a3 单独漂在**它自己那份**清单上。
**我拿当下的状态解释了一个 24 小时前的事件。**（对抗组的简报里我写过「一个老是得出
同一个开脱结论的裁判该被审，不该被信」——这次该被审的是我。）

## 一、结论

**这条红是 master 自己的，而且和 cycle 21 那次是同一个根因 `71b882c8`，
只是这次经由另一条断言浮出来。** 我 cycle 25 开机时特意写了「旧诊断不自动适用于新红，
我从零重测，不继承」——重测的结果是**同一个根因**。这一点我要说清楚：
不是我继承了旧结论，是新测量落在了同一个地方。

| 树 | 结果 |
|---|---|
| 干净 `origin/master` `50e10617` | **exit 1，红**。`1 failed, 177 passed` |
| a3 分支 tip `a5812063` 单独 | `verify_provenance` **9 项里失败 1 项** |
| `50e10617` + a3（`git merge --no-ff` **零冲突**） | **exit 1，红**。`1 failed, 246 passed` |

漂移的 manifest id：**干净 master 5 个；合并后 7 个 = master 那 5 个逐字相同 + 2 个；
分支单独 1 个。** `master \ merged = ∅`——**master 上漂的每一份，合并后照样漂。**

## 二、根因，是字节 diff 量出来的，不是读代码读出来的

master 那 5 份漂的是**同样三行**，由重导过程加进 `cost.from_price_table`：

```
+   "missing_usage_keys": null,
+   "unmeasured_calls": 0,
+   "unpriced_usage_keys": null,
```

`archive.costs()`（`theoria-arm/armtools/archive.py:117`）把 `proxy.cost.price_run()`
的返回字典**逐字嵌进** manifest。提交 **`71b882c8`**（"proxy: 'not measured' and
'measured, and it was zero' were the same literal"，07-30 02:06）给 `price_run` 加了
这三个键，**改了重导器却没有重新生成已归档的清单**。

祖先关系（这是把账算到谁头上的关键）：

| | 是 `50e10617`（master）的祖先？ | 是 `a5812063`（a3 tip）的祖先？ | 是 merge-base `26457a28` 的祖先？ |
|---|---|---|---|
| `71b882c8` | **是** | **否** | **否** |

且 `git diff --name-only 26457a28 a5812063 -- proxy/` **为空**——**a3 一个字节都没碰 proxy/。**

**不是合并产物，已证**：`theoria-arm/` 的树哈希在 merge-base 与 master 都是 `26ec0239…`
（master 自 merge-base 以来在 arm 下改了**零个**文件），在分支 tip 与合并后都是 `9bc1cafb…`。
合并后的 arm 与分支的 arm **逐字节相同**。1 → 7 的增量**完全来自 master 送来的 `proxy/cost.py`**。
三种漂移里（清单变了 / 它描述的树变了 / 重导代码变了），这是**第三种**。

## 三、a3 确实自己欠一条，但那不是它被 flag 的那条

`20260729T004020Z-leg01` 在**分支单独**时就漂，另有原因：它的 `files[]` 列了
`candidates.jsonl` 与 `trace.jsonl`，两个都被 gitignore
（`theoria-arm/.gitignore:30`，**本分支加的**，因为那文件 201 MB、超 GitHub 上限；
以及既有的 `.gitignore:4`）。清单是在一台**持有克隆不可能持有的文件**的机器上导出的，
所以 `build()` 的目录遍历永远重现不了它。

**这条是 a3 的，是真的，而且会跟着进 master。** 但它**不是**闸门现在失败的那条：
去掉它，master 那 5 份还在。

**账**：7 条漂移里 **5 条是 master 的**（也正是 flag 记的那些 id）、**1 条是 a3 的**、
**0 条是合并造成的**。

## 四、所以怎么办——这条对队列有直接后果

**合并 A3 之后闸门仍然红**，因为 master 那 5 条还在。于是：

* **a3 被重试 20 次、挂了 23.6 小时，而它无论做什么都不可能变绿。** 队列每 15 分钟
  再试一次、再失败一次、`attempts` 再加一。这 20 次里没有一次能带来新信息，
  因为**失败的原因不在被测的那个对象上**。
* 更要紧的推论（**a3 组明确列为未确定，我已派对抗组去settle**）：
  按这个机制，**每一份早于 `71b882c8` 的 arm 清单都会漂**，
  于是 **arm 闸门可能对每一条碰 theoria-arm 的分支都是红的**。
  若成立，这就不是 a3 一条的事，是队列在为一个 master 缺陷扣住一整个领地。
  **我不据此行动，等对抗组的数。**

**master 那 5 条没有不重写归档 provenance 的机械修法。**
`verify_provenance` 的 check 2 自己建议 `python -m armtools.backfill --all`——
**那正是「改写归档清单去迎合监管它的检查」**，我没跑，也建议不要把它当合并动作跑。

**真正的缺陷是一条耦合**：`cost.from_price_table` 把**另一个领地的返回字典形状**
存进归档清单，于是 `proxy/cost.py` **每改一次就重新弄坏每一份 arm 清单**。
不修这条，今天 backfill 一遍，下一次 proxy 改动再来一遍。
（同一族的第二条见本轮另一份 inbox：`armversion.scan()` 读 `git rev-list --all`，
于是**任何人建一个 tag 都在改 provenance 扫描的输入**。两条形状相同：
**归档产物依赖一个没有被声明为契约的外部东西。**）

## 五、我不能做的与需要派单的

`proxy/` 与 `theoria-arm/` 都不是合并裁判的地（CHARTER：OPS-* 不改代码）。**提案**：

1. **给 `71b882c8` 派一个向前修**——不是回退。cycle 21 已验明**回退它会把 `proxy`
   从绿变红**，所以只能向前。修的内容是让 `archive.costs()` 不再逐字嵌另一个领地的返回字典，
   或给那个字典定一个显式的、被 CONTRACTS 钉住的形状。
2. **a3 的 `leg01` 那条交回作者**（它作者活跃，tip 只有 1.5 小时）：
   要么把 gitignored 路径排除出 `build()` 的遍历，要么把这两个未跟踪产物显式声明。
   **这是分支上的草稿、不是已上线的归档，赛前改草稿不是被禁的那个操作。**
3. 在 1 落地之前，**a3 不应该继续占着 NEEDS-HUMAN 并每 15 分钟被重试一次**——
   它的红不在它身上。

## 六、还没定的

* **arm 闸门是不是对所有碰 theoria-arm 的分支都红**（对抗组正在测 2–3 条别的分支）。
  这可能是本轮最有后果的一个数。
* 队列到底给这个闸门传没传 `PYTHONPATH`：诊断组**手动**设了
  `PYTHONPATH=<worktree root>` 才跑得起来（`verify_provenance` import `proxy.ledger`）。
  本仓库有过前科：`gates.run()` 的 docstring 承诺给 env、实际没传。
  **若队列跑这个闸门时根不可 import，那它红在 import 上，整个漂移分析就都挂在错误的失败下面。**
  已列为对抗组的第 3 条攻击线。
* 一条 a3 组顺手发现、**今天不是成因**的潜伏项：manifest 归档
  `provenance.arm_version_lookup.commits`，由 `armversion.scan()` 走 `git rev-list --all` 建成，
  **这个列表随无关推送变长**。今天 7 条漂移全是 `verdict: no_match` 且 `commits` 为空，
  所以它贡献了零——但它会在以后咬人。（我本轮亲手证明了触发它有多容易，见另一份 inbox。）

## 产物

`.worktrees/opsm25-a3`（干净 master `50e10617`）与 `.worktrees/opsm25-a3b`（分支 tip
`a5812063`）留在原地供复核，两个都坐在已有的 ref 上。
`.worktrees/opsm25-a3m` **已被诊断组自己删掉**，理由是它的合并提交 `bd01e88c` 是一个
**新对象**、会被 `git rev-list --all` 看见、从而扰动别人的 provenance 运行——
这个判断是对的，我把它记在这里当作先例。
未推送、未碰 `monitor/`、零网络、零 API 花费。

---

# 八、对抗复核（2026-07-30T04:33:13Z）：**标题那句话是个时代错置。以本节为准。**

七条里五条站住，**一条（G6）两个分句全falls**，两条被实质削弱。
**而 falls 的那条正是这份报告的标题和处置建议所依赖的那条。**

## 8.1 最重的一条：**我用一个比 a3 的 flag 年轻 14 小时的缺陷替它开脱**

| 事件 | 时刻 |
|---|---|
| **a3 第一次被 flag** | **2026-07-29T04:14:01Z** |
| `71b882c8`（我认定的根因）落地 | **2026-07-29T18:06:10Z** |

对抗组在**a3 被 flag 当时的 master**（`28ced40e`，04:04:27Z）上跑那个检查：
**`OK: 9 checks` —— 绿的。** merge-base `26457a28`：**也是绿的。**

**a3 被 flag 的那一刻，干净 master 是绿的，而 a3 的 tip 单独漂在恰好 1 份清单上
——`20260729T004020Z-leg01`，它自己那份。**

**而我自己在 merge.log 上 16:01:59Z 写过的注正是这句**：
"green on clean master and red with a3 merged"。**我有过正确的观察，然后用一个
14 小时后才出现的缺陷把它覆盖掉了。**

> **"合并 A3 之后闸门仍然红" 只对这 24 小时里的最后约 10 小时成立。**
> 前 14 小时它红在自己身上。我把一个后来才发生的原因，追溯成了整段挂起的解释。

这是我这轮的第五个同形错误，但**性质更糟**：前四个是没重测，
**这一个是我拿当下的状态去解释过去的事件，而没有去测事件当时的状态。**

## 8.2 第二个分句也是假的，而且被我自己的 G7 反驳

我写「master 那 5 条**没有**不重写归档 provenance 的机械修法」。**有。**

5 份归档清单的 `from_price_table` 键集**完全相同**：
`['model_calls','per_model','pricing','unpriced_models','usd_total']`。
**在 `archive.costs()` 里把 `table_cost` 投影到这个已声明的键集上，就恢复了逐字节稳定性
——一份归档清单都不用碰。** 那是 theoria-arm 自己领地里的一个代码修法，
**正是我 G7 诊断出来的那条耦合的正确补法**。我一边诊断出耦合，一边宣布无解。

## 8.3 「master 缺陷波及全队列」这个假设是空的

我请对抗组去 settle 的那个「最有后果的数」：**它扫了全部 `origin/agent/*`——
整个远端只有 1 条分支碰 `theoria-arm/`，就是 a3 自己。**
而 `ci_merge.py` 只对分支碰过的目录跑该领地的闸门，
**所以 master 那 5 条漂移除了经由 a3，对队列不可见。**

**我 cycle 21 就在同一个地方犯过同一个错**（当时我写「它挡住所有碰 theoria-arm 的分支」，
随后自己更正为「全仓只有 a3 碰 theoria-arm——我在样本量为一的总体上下了总体结论」）。
**我这轮又把它当成一个待验的规模假设提了一遍。同一个错，同一个位置，第二次。**

## 8.4 我列为「未确定」的 PYTHONPATH 洞：假的，两个独立理由

`ci_merge.py:543` **确实**传了 `extra_env=gates.gate_env(wt)`；
且 `theoria-arm/_bootstrap.py` 自己把 `REPO` 放进 `sys.path`。
对抗组用 `env -u PYTHONPATH` 重跑全部检查，照常工作。
**上一跑手动设 PYTHONPATH 是多余的，整个漂移分析不是挂在一个 import 失败下面。**
（另：**不存在容忍路径**——`test_the_archive_stays_accountable` 断言 `not checks.failed`，
9 项里任何 1 项红就是红；红永远是致命的。）

## 8.5 两条被削弱的

* **G2 的「5 + 2」分解misattributes**。逐字节比对渲染 vs 盘上后：那 2 条里
  **只有 `leg01` 带 A3 造成的 diff**；`leg01-salvage` **只漂在那三个 cost 键上**——
  **它是 A3 贡献的一份清单，被 master 的缺陷弄坏的**。
  合并树上的正确分解是 **6 条 cost 造成、1 条 A3 造成**（`leg01` 两个原因都有）。
* **G5 的机制对，但「独一份」不对**——见下。

## 8.6 没人问过的那个问题：**check 8 根本没有判别力**

`_idempotence` 按 `backfill._is_backfilled` 分流：被 backfill 过的走 `build()`
（会重走 run 目录），其余走 `amend_payload()`（不会）。
**于是有 4 份清单列着任何克隆都拿不到的 gitignored 文件，却静静地通过了**——
`20260728T012311Z-…-aborted`、`20260728T014402Z-…-aborted`、
`20260728T015354Z-g50t-first-contact`（**三条都是 master 侧的**）与 `20260729T105729Z-leg01`。
强制让它们走 `build()`：每一份都会丢掉 `trace.jsonl`。

**它们和 `leg01` 是同一个结构性缺陷，检查看不见它们是因为代码路径，不是因为它们正确。**

> **所以 A3 没有引入一个新的缺陷类别，它是在「这个既有类别唯一会显形的那条路径」上
> 放了一份清单。这句话两头都要说：A3 的 `leg01` 确实是 A3 的、确实该被检出，
> 而 master 自己带着三份同类、未被检出的。**

## 8.7 一条我担心的、被测掉的

我本轮亲手证明了 tag 会进 `git rev-list --all`、而 `armversion.scan()` 读它，
所以我担心这份漂移判决本身是不是我这台机器 200+ 个 ref 的属性。
**对抗组测了**：`--all`（1204 commits / 47 arm versions）与仅 `HEAD`（1049 / 22）
**给出完全相同的漂移集合**，master 与合并树都是。
**这个仪器在这里是稳的，35 个 tag 的隐患对这条漂移不适用。**

## 8.8 修正后的处置（取代第四、五节）

1. **不要**把 a3 的挂起整段记成 master 的账（8.1）。**前 14 小时它红在自己身上。**
2. **有一个不碰归档的修法**（8.2）：在 `archive.costs()` 里把 `table_cost` 投影到
   已声明的键集。**这是 theoria-arm 领地的一个小代码改动，不是「无解」。**
3. **a3 的 `leg01` 仍然是 a3 自己的活**（`files[]` 列了 gitignored 文件），这条没变。
4. **新增，我认为比上面三条都重要**：**check 8 的分流让三份 master 侧的同类缺陷永久隐形**（8.6）。
   请单独立项——**一个只在一条代码路径上睁眼的检查，比没有这个检查更危险**，
   因为它的绿被当成了证据。
5. 「master 缺陷波及全队列」**不成立**（8.3），别按它排优先级。

## 8.9 对抗组合规

四个工作树（`opsm25-adv-a3`/`-mb`/`-flagtime`/`-merged`）**全部删除并 prune**，
其中持有新合并提交的那个已消失；**未建任何 tag 或分支**；
**从未在任何地方跑过 `armtools.backfill --all`**；唯一的改动是在自己一次性工作树里
`git apply -R` 一个 hunk，已 `git restore` 并复验干净；`monitor/` 未碰；
零网络、零 API；只接触开发堆的 `g50t-5849a774`。
