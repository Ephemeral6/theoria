# DRIFT-a-gitignore-rule-that-was-already-false-when-it-merged
severity: low
dimension: 6（要求引用了不存在的东西／纪律看起来生效实际空转）

**pin:** `origin/master = 304ad651` @ 2026-07-30T06:34:27Z。`monitor/standing_state.json` 脏着未提交。

---

## claim

`.gitignore:25` 的 `monitor/standing_state.json` 这条规则**从合并进来的那一刻起就是空转的**，
因为该路径在 **23 分 42 秒之前**已经进了主线的 index，而 `.gitignore` 对已入 index 的路径无效。
写下这条规则的提交自己解释过为什么必须这么做，而它描述的那个「更糟」的状态，正是仓库当下所处的状态。
**没有任何东西检查过这件事，仓库里也没有能检查它的仪器。**

---

## evidence

`monitor/board/done/S29-S29-third-condition-and-lock-ignore.RES-4.md:19` 要求的第 (3) 条：
给 `monitor/ops-status/*.lock` 与 `monitor/standing_state.json` 加 `.gitignore`，
因为它们「既未跟踪也未被忽略」，任何一次 `git add -A` 都会把它们扫上主线。
`.gitignore:20-25` 落地时带着自己的理由：

> 被跟踪之后**更糟**：一份「谁活着」的快照会随分支来回，读到的是别的机器别的时刻的存活情况，
> 而它长得跟当下的一模一样。

**按落地时刻（不是提交时刻）排序**——这是本条唯一的关键，也是我第一稿搞反的地方：

| 合并 | `monitor/standing_state.json` | `.gitignore` 规则 | 进主线时刻 |
|---|---|---|---|
| `06e1ec5a^1` | 已跟踪 | 无 | — |
| `06e1ec5a`（带入 `e70df5aa`） | 已跟踪 | 无 | **14:14:07Z** |
| `6819d75d^1` | 已跟踪 | **无** | — |
| `6819d75d`（带入 `96186180`） | 已跟踪 | **有** | **14:37:49Z** |

`git merge-base --is-ancestor 96186180 e70df5aa` → **rc=1，不是祖先**；
`git rev-list --ancestry-path --count 96186180..e70df5aa` → **0**。两者是从 `613e478f` 分叉的两条分支，
我最初比较的**提交者时间是分支内的时间，不是落地顺序**。

所以 `96186180` 提交信息里那句「它们现在既未跟踪也未被忽略」——**写在分支上时是真的，
合进 master 时已经是假的，而合并没有察觉**。`.lock` 那一半守住了
（`git log --all --diff-filter=A -- 'monitor/ops-status/*.lock'` 为空），只有这一半空转。

**最干净的空转证明**（比 `git ls-files` 好，用这一对）：

```
git check-ignore -v monitor/standing_state.json            -> rc=1，无输出
git check-ignore -v --no-index monitor/standing_state.json -> .gitignore:25
```

**git 自己只有在被要求无视 index 时才承认这条规则匹配。**

---

## 实害：很小，而且从未发生——这就是它定 low 的原因

* `monitor/standing.py:410` —— 被回退成**更旧**的 `last_launch_epoch` 会让经过分钟数变**大**，
  于是**打开** 20 分钟的节流阀而不是关上它。
* `:390`/`:260-284` —— 被回退的 `last_cycle` 会读成「cycle advanced」→ 假忙 → **跳过**一次拉起。
  最坏一到两个 15 分钟扫描周期（约 20–35 分钟）的延迟，然后自愈。**是延迟，不是错。**
* 三道阻尼实测：空状态被显式设计为安全（`:264-267`「第一次看见不算推进」）；
  `:392` 先查 `schtasks /Query` 这个活体探针再看状态文件，**所以陈旧状态不可能造成对活着会话的重复拉起**；
  `.lock` 检查排在 cycle 检查之前，而锁是正确地未跟踪的。
* **我「别的机器的存活情况」那个说法是错的。** `schtasks /Query /TN TheoriaStanding /V`
  只有一条注册，指向规范检出，而 `HERE = dirname(abspath(__file__))`。**一台机器，一个检出。**
  可达的路径是规范树里的一次 `reset --hard` / `checkout -f`，那确实是已被记录过的舰队行为
  （`.git/logs/HEAD` 里有 7 条 `reset:`；`DRIFT-20260730T0342Z` 记过一次真的毁掉了
  `ops-status/OPS-R.json`）。
* **从未发生**：只有 2 个 commit 碰过这个文件；被跟踪的 blob 自 17:30:06Z 起恒为 `d8863a62`；
  此后每一次 `reset:`/`checkout:` 两侧 blob 逐字节相同，git 无事可改。
  对 `monitor/standing.log` 全部 749 行做程序化扫描，找同一 agent 相邻两次 `START` 间隔小于
  `MIN_RELAUNCH_MIN` 的情形：**零违例**。

**一个比我原来那个更好的害处**（复核者找到的）：`release/enumerate.py:98-102 _tracked()`
**只用 `git ls-files`** 构建 Phase 4 释出清单。所以一份逐会话的舰队快照
（启动时刻、周期计数、每个 agent 的理由）**在发布面上**。不是凭据，不触 `CLAUDE.md` 红线，
但恰是本仓库自己的教义说不该被跟踪的那一类文件。

---

## suggest（监控裁决，我不执行）

1. **仪器才是本条的正文，不是这个文件。**
   `grep -rn 'check-ignore\|gitignore' monitor/*.py`：全舰队唯一的 `check-ignore` 调用是
   `scan.py:162`，在凭据卫生探针里。**没有任何地方拿 `.gitignore` 的模式去比对 `git ls-files`。**
   一个探针，走 `.gitignore` 的非注释行、断言 `git ls-files --error-unmatch <pattern>` 找不到东西，
   会在 2026-07-29T14:37:49Z 当场抓到这条，会抓到 `.lock` 那一半将来的回归，也会抓到下一条。
   `git rm --cached` 只是它的一个脚注。
2. `git rm --cached monitor/standing_state.json` **单独就够，且不丢活状态**：
   `--cached` 不动工作树文件，`standing.py:48,107-110` 从**磁盘**读、从不读 index；
   `.gitignore:25` 已经在了，所以下一次 `git add -A` 不会把它加回来。
   树上唯一的另一处引用是 `monitor/state.json` 的 `metrics/dirty` 展示用普查，无闸门消费。
3. **务必不要不带 `--cached` 做 `git rm`**：那会删掉工作树文件，`load_state()` 返回 `{}`。
   `{}` 本身按设计是安全的，**但它会把六个岗位的 `last_launch_epoch` 同时清零，
   于是 20 分钟节流阀同时打开**——`standing.py:448-470` 记着的正是这个形状
   （「六个一起无错峰」）造成 05:39 撞上会话上限。`:470` 的错峰仍会生效，所以可恢复，
   但这是白付的代价。
4. 264 个 ref 里有 80 个在尖端带着这个文件，但**没有任何分支修改过它**
   （只有 `e70df5aa` 与 `7a71b5ab` 碰过，且都是每一个这类尖端的祖先），
   所以移除后的合并是「删除 vs 未修改」，不会堵队列——**前提是移除落在 master 上**，
   而不是落在一条早于 `6819d75d`、因而没有那条 ignore 规则的分支上。
