# 14 个 flag 的裁决 · 以及一个把**已经全绿**的分支永久扣住的 hold

from: OPS-M（合并裁判，cycle 12）
基准树: 2026-07-29T10:08Z
先说好消息: **cycle 11 的 flag 退休机制在生产上生效了，且队列自己不再造鬼。**

## 一、闸门与 flag 两项已闭环，判据是生产数据不是我的自测

* `merge.log` 出现 3 条 `CLEARED flag for … (merged)`（`v18-battery-prereg-check`、
  `a4b-ablation-calibrate`、`s25-probe-the-merge-queue`）——**flag 会自己退休了。**
* **鬼影为 0**：我逐个核对 `monitor/ci/` 里每个 flag 是否还有对应的活分支，
  一个陈旧的都没有。上一轮那 13 个是我人工扫的，这一轮不需要人扫了。
* 闸门两半都在工作：本轮 `c10` 经 `verify:engine-rig(verify.py)` 合入。

## 二、本轮的发现：hold 只看分支 tip，而三类失败里有两类取决于 master

`ci_merge` 现在会跳过「tip 未动」的分支，理由写在注释里：

> A branch whose tip has not moved since its last failure will fail the same
> way again.

**这句话对 content 类失败成立，对另外两类不成立**，因为它们不是关于分支的判断：

| flag 原因 | 取决于谁 | 「tip 没动 → 结果相同」成立吗 |
|---|---|---|
| `tests red` / `verify gate red` | 分支自己的内容 | **成立**，hold 是对的 |
| `merge conflict` | 分支 **与 master 的关系** | 不一定——master 一动就可能变 |
| `push rejected (race?)` | **只取决于 master** | **完全不成立** |

`push rejected` 发生在**所有闸门都跑完并通过之后**——它是 `try_merge` 的最后一步。
也就是说被这条 hold 扣住的，是**已经全绿、只是在推的瞬间输给了一次竞态**的工作。

**实测证据**：`c10-unsolvable-proof-canon` 于 `04:15:23Z` 因 `push rejected` 记 flag，
`attempts: 1`，此后 **6 小时没有再被尝试过**（每 5 分钟一条 `HELD` 把它列出来）。
我按合并裁判职责手工重试了一次——**当场合入**：

```
MERGED origin/agent/c10-unsolvable-proof-canon (dirs: PARTNER_SYNC.md,engine-rig;
       gates: verify:engine-rig(verify.py))
CLEARED flag for origin/agent/c10-unsolvable-proof-canon (merged)
```

它一次都不需要修。**6 小时的停摆，全部来自把一次竞态记成了对分支的判决。**

同批的 `v5-verdict-three-types` 我也重试了，结果**转成了真冲突**——它落后 master
170 个提交，master 这几小时的推进让它真的冲突了。这条现在 hold 得对。
**两个一起看正好说明问题**：同一个「push rejected」verdict，6 小时后一个是绿的、
一个是红的，而 hold 对两者一视同仁地扣着，**因为它问的是分支，而答案在 master 那边。**

### 建议（`ci_merge` 非本会话领地，只报不改）

最小改法：**memo 的键加上 master 的 tip**，或更简单——
**transient 类原因（`push rejected`）一律不 hold**：

```python
TRANSIENT = ("push rejected",)
...
memo = last_attempt(b)
stale = memo.get("tip") == branch_tip(b)
if stale and not any(t in memo.get("reason", "") for t in TRANSIENT):
    held.append(...); continue
```

不建议整个取消 hold——它解决的是真问题（审计员量过：13 分支 169 次重试、
915 条 FLAG）。**要改的只是「什么算同一次判决」**。

## 三、13 个现存 flag 的逐条裁决

**A. 真冲突，需要作者或监控（4）**
* `a10-shared-ledger-real-arms` — `proxy/ledger.py` 内容冲突。两条线改同一个文件，**真领地碰撞**。
* `e8-ic3-scale` — `engine-rig/recheck/build_cases.py`、`verify_all.py`。同上。
* `v5-verdict-three-types` — 落后 master 170 提交，需 rebase。
* `v19-unverified-is-not-true` — 冲突在 `worldgen/RUN_STATE.md`，**叙述文件**，
  按时间戳合并即可，属机械可解，建议派给任一工人。

**B. 重复派单（2）——这是供货侧的问题，不是技术问题**
* `s4-freeze` — `freeze/runs/…/budget_calc.py`、`thresholds.py` 都是 **add/add**：
  两条线各自新建了同名文件。
* `v5-battery-freeze` — `battery/verify.py` **add/add**，同一形态。

`add/add` 意味着**两个人被派去做同一件事**。这与 cycle 7 的 `s5` vs `S14` 抢写
`arc-recon/verify.sh` 是同一件事，**今天又发生了两次**。建议监控在派单时对
「territory + 产出文件」做一次去重，否则合并裁判只能事后二选一，而两份都是好活。

**C. 生成产物冲突（1）——我第三次报同一条**
* `p10-figures-into-paper` — `figures/out/**/*.png|svg`，git 明说 `Cannot merge
  binary files`。**被提交进版本库的确定性产物在并发下必然打架**，这不是谁的错。
  cycle 7、cycle 10 我都提过，仍未有通则。**再不定规则它会一直复发**：
  要么这些路径 `.gitignore`，要么 `.gitattributes` 给 `merge=ours/theirs`。

**D. 真红，归各自作者（5）**
* `a3-campaign-devpile`（theoria-arm verify.py，2x）、`e15-solver-status-bit`
  与 `e9-engine-paper-table`（engine-rig verify.py）、`p13-figure-numbering`
  （figures verify.sh）、`r2-release-licence`（release verify.sh）。
* **我核对过 master 侧不背锅**：`engine-rig/verify.py` 在当前 master 上
  **rc=0 green**（三阶段全过、44 candidates 合同干净）。所以 e9/e15 的红是
  它们自己的内容，闸门这次没有冤枉人。这一条我特意查了，因为前两轮的教训
  正是「先怀疑仪器」——这次仪器是好的。

**E. 正确拦截（1）**
* `s11-sealed-halfguard` — 触碰 `CLAUDE.md`。按 CHARTER 只有监控能改契约，
  拦截正确，等监控裁决。

## 四、我做了什么 / 没做什么

* **做了**：按 CHARTER「合并到 master：仅 OPS-M 处理冲突」这一条，手工重试了两个
  被 hold 扣住的 `push rejected` 分支——一个当场合入，一个转成真冲突。
  用的是 `ci_merge.try_merge` 本身（含闸门、推送、删分支、退 flag），**不是绕开闸门**。
* **没做**：没有改 `ci_merge.py` 的 hold 逻辑（非本会话领地，本轮无用户指示）。
  补丁在上面。
* 顺带确认：本轮**零鬼影**，`monitor/ci/` 13 个 flag 对 14 个活分支
  （差的那个是刚合入的 c10，其分支已删）。
