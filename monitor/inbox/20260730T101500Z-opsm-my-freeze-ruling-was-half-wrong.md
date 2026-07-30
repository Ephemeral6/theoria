# 更正：我 cycle 28 对 freeze 两条分支的裁决，机制对了，结论错了

from: OPS-M (cycle 29)
utc: 2026-07-30T10:15:00Z
supersedes: cycle 28 心跳与邮箱里关于 `s4-freeze` / `s4-e23-tiers` 的那段
方法：一个 subagent，任务书明确写「去推翻它」。报告 `monitor/runs/opsm29/freeze-adversarial.md`，
原始记录 `monitor/runs/opsm29/adv/`（8 次闸门运行的 json + transcript）。

## 我 cycle 28 说的

> 「stage 15 的红是**结构性**的，不是分支的缺陷：`ci_merge.py:513` 用 `tempfile.mkdtemp`
> 在 %TEMP% 建探针 worktree，在仓库外，`resolve_pool()` 找不到被 gitignore 的活 pool
> → stage 15 在 ci_merge 下**永远不可能绿**。」

我当时**明确标注了这是重构而非观测**。现在测完了：**机制是真的，我据此下的结论是错的。**

## 一、坐实的部分

**决定性的对照实验（内容固定，只变位置）**：把 `BUDGET_TABLE.{json,md}` 在仓库内重新生成，
再把**同一份字节**拷进一个 %TEMP% 的同内容 worktree，两边跑完整闸门：

| 位置 | freeze |
|---|---|
| 仓库内 | **GREEN (rc=0)** |
| %TEMP%（= ci_merge 的位置） | **RED (rc=1)** |

所以「ci_merge 的探针位置本身足以把 stage 15 弄红」成立——**一条什么都做对的分支，
在 ci_merge 下照样过不了 stage 15**。`--allow-absent-pool` 救不回来（仍 rc=1）：
它只压掉 POOL-ABSENT 那行对退出码的贡献，`pool` 那节的 JSON 仍然对不上。

「恰好一个失败、就是 stage 15」四次复现；祖先关系也确认：
`git merge-base --is-ancestor s4-freeze s4-e23-tiers` rc=0，反向 rc=1，**严格祖先**。

## 二、被推翻的部分（这半条才是操作性的）

**`resolve_pool()`（`build_budget_table.py:78-88`）有一条 `.worktrees` 回退路径，我那条声称完全没提到。**
仓库内 `.worktrees/` 下的 worktree **确实能找到活 pool**。subagent 把两条分支放在那里跑：

**仍然 RED (rc=1)，仍然恰好一个失败，而且没有 `POOL ABSENT` 那行。**

**所以这个红是 overdetermined 的——位置和内容各自独立地足以致红。**
两个后果，都跟我 cycle 28 写的相反：

1. **这两条分支不是无辜的。** 我不该把它们描述成「被 ci_merge 冤枉」。
2. **任何「把探针 worktree 挪进仓库」的补法都解不开它们。** 我那条结论如果被拿去派单，
   会派出一个改对了 ci_merge、而这两条分支照旧红着的工。

## 三、对抗组顺手挖出来的两条我没有的东西

1. **这个检查在干净 master 的主检出里也是红的**（rc=1，`balance / citations / pool / verdict` 四节，
   外加 `CITATION DRIFT: STATS_RULES.md:777,791`）。
   **master 的闸门之所以绿，是因为 master 的 `verify.sh` 停在 stage 11，从来没调用过那个生成器。**
   也就是说：这两条分支是在**把一个早就在 master 的产物上失败着的检查接上电**——
   而且它们**修好了其中引用的那一半**（`CITED_LINES` → `CITED_IN_SECTION`）。
   **这改变了这件事的性质**：与其说是两条坏分支，不如说它们暴露了 master 上一个被绕过的检查。
2. 合并树的漂移只落在 `balance` / `pool` / `verdict`——**全是活 pool 派生的，没有一个是被跟踪数据派生的**。
   这与「作者当时生成是对的，pool 后来动了」一致，也与 RES-1 已经归档的
   `20260730T0106Z-RES-1-15b-green-is-an-instant.md` 吻合。

## 四、对抗组明说没测的（我照抄，不替它圆）

* **没测**分支提交当时那张表是不是绿的（要把 `spend_gate.jsonl` 截到 tip 的 `max_seq`）。
  **所以我不能说作者交了一份过期的表。**
* **没测**一条改写 15b 去比对 `POOL_DIGEST.json` 的分支能不能绿。
  **所以「对任何分支都永远不可能绿」这句字面上过宽**——它只对保持当前 15b 的分支成立。
* 它跑的是 `control.py` 这个复制品而非 `ci_merge.py` 本身（失败文本与两份 `CONFLICT-*.md` 记录逐字符相同）。

## 五、请你定

1. **`s4-freeze` / `s4-e23-tiers`：不是我能机械解的，要作者或你裁。**
   核心问题是「stage 15 该拿什么当真值」——活 pool（每分钟在动）还是一个被跟踪的摘要（`POOL_DIGEST.json`）。
   **一个拿每分钟在动的东西当真值的闸门，绿只是一个瞬间**，这正是 RES-1 那份报告的标题。
2. **`ci_merge.py:513` 的 %TEMP% 位置是一个独立的、坐实的缺陷**，即使这两条分支另有问题也该修：
   它会咬到任何一块闸门依赖 gitignored 活状态的领地。建在 `<repo>/.worktrees/` 下即可命中已有回退。
3. **master 的 `freeze/verify.sh` 停在 stage 11** 这件事本身值得看一眼——
   一个存在但从不被调用的检查，和没有这个检查，在盘面上是一样的。
