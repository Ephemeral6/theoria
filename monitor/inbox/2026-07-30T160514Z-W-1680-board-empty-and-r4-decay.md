# W-1680 · 板对我为空（属实），但 R4 在被挡的这 35 小时里已经烂掉一角

- 工人：`W-1680`
- 时刻：2026-07-30T16:05:14Z
- base_commit：`4a511d7e`
- 领地：无（未持有任何认领；本文件是 inbox，是我唯一被允许写的地方）
- 结论一句话：**BOARD-EMPTY 这次是真话，不必查；但 R4-worktree-rescue 的三个
  救援目标里，第 2 个的前提已经不成立了，它现在没有任何 GC 根。**

---

## 1 · 板对我确实是空的，这不是缺陷

`python monitor/board.py claim W-1680` → 退出码 3，**裸的** `BOARD-EMPTY`
（没有「N 件被扣下」那一段，即没有任何东西是专门对我隐藏的）。

三个独立探针都说板是干净的，不是卡住的：

| 探针 | 结果 |
|---|---|
| `board.py sweep --dry` | `no orphaned claims`（10 个持有者的计划任务都在跑） |
| `board.py reconcile` | `RECONCILE-CLEAN` |
| `board.py list` 的 unreachable 段 | 未打印（8 件全部有出口＝等邻居交付） |

所以**不需要**为这次 BOARD-EMPTY 排查 S28 那条被吞掉的 `OSError`，也不需要
怀疑 resurrected。就是我来晚了：`board.log` 显示 15:59:27–28Z **两秒内六条
CLAIM**（W-1691/1702/1693/1690/1682/1681/1710），我 46 秒后到，货架上剩下的
全被领地互斥挡住。

## 2 · 现在的吞吐上限是「空闲领地数」，不是人头数

在飞的 10 件认领占了 **10 个互不相同的领地**（theoria-arm / engine-rig /
papers / proxy / verify-lab / monitor / figures / worldgen / fuzzlab / exam）。
货架上的 8 件只落在 **3 个领地**，且这 3 个全被占：

| 领地 | 货架件数 | 被谁占着 |
|---|---|---|
| theoria-arm | **6** | `A3-campaign-devpile` / RES-1 |
| monitor | 1 | `S44-monitor-suite-outgrew-its-gate` / W-1690 |
| exam | 1 | `V27-V27-manifest-absolute-paths` / RES-3 |

RES-1 心跳 0 分钟（来源 `lock`），活着，而 `A3-campaign-devpile` 自
**2026-07-29T04:46:23Z** 领走，已 ~35 小时——它是一件 `spend: api` 的多关战役，
长本来就是它该有的样子。**问题不在 RES-1，在于 theoria-arm 是个粗领地，一个
人在里面跑战役，另外 6 件就一起排在门外。**

对监控的用处只有一句：**此刻再加通用工人，得到的是立刻退出的启动**。要提吞吐，
杠杆在出题（拆领地 / 出别的领地的题），不在人头。

## 3 · R4-worktree-rescue（p1，无赛道）：第 2 项的前提已经不成立

R4 写的是「唯一的 GC 根就是那棵树」。**那棵树已经没了。** 逐条实测（16:0xZ）：

| R4 的目标 | 实测 |
|---|---|
| ② `.worktrees/opsm-push` | **目录不存在**；`git worktree prune --dry-run -v` 无输出（注册表也已清） |
| ② 提交 `a59d5dc0` | 仍在（packed object，`git cat-file -t` → `commit`），"Merge branch 'opsm/m16-v5v' into HEAD"，2026-07-29 22:40:42 +0800；**`git branch -a --contains` 为空，`git reflog --all` 命中 0** |
| ① sk48 在线对局目录 | 仍在，**145 个文件、MANIFEST.json 缺失**、`git log --all --diff-filter=A -- <path>` 为空（从未进过任何 ref） |
| ③ V8 分检官独有 calib | 仍在：`61417` 字节，`.claude/worktrees/agent-a84bd79e7c2e1dca9/exam/runs/20260729T082000Z-V8-judge-trust-audit/probe/calib.json` |

②现在的状态比工单写的时候**更糟一档**：那时它有一个根（工作树），现在**一个
根也没有**，只剩一个不可达对象。

**还没丢，别慌**：它是 packed 而非 loose，默认 `gc` 保留不可达对象约两周；
`git count-objects -v` 报 216 个松散对象，离 `gc.auto` 的阈值很远，所以不会
自动触发。**会立刻杀掉它的只有一条**：有人显式跑 `git gc --prune=now`。

**出口是一条命令**：`git branch rescue/opsm-push a59d5dc0`。

**我没有跑它，理由说清楚**：我不持有 theoria-arm 的认领；而且 `A3-A17` 这件
公开工单说的正是「任何人建一个 tag、推一条分支，都在改 `armversion.scan()` 的
输入（`git rev-list --all`）」——**用建 ref 去救 R4，恰好扰动 A17 正在盯的那个
东西**。这个取舍该由监控拍，不该由一个没认领的工人顺手拍。A17 自己也记着本轮
`--all` 与 `HEAD` 给出相同漂移集、7 条全 `no_match`，所以实际影响多半为零——
但「多半为零」不是我的判断权限。

**请在数天内给个说法，不是数周。**

## 4 · 一条提案（只是提案，我没有验它成不成立）

R4 是 p1，题面是「救出只存在于工作树里的东西」，而它被排在同领地一件多日
付费战役后面——**它防的那类事故（清理 / prune / clean），恰恰是别的工人随时
可能干的**。可考虑把 R4 挪出 `theoria-arm`（例如独立的 `rescue` 领地），让它
和战役并行。

**我没有核实 R4 的写集与战役的写集是否真的不相交**（R4 要写 MANIFEST 并入库，
落点大概率在 `theoria-arm/runs/` 之下，与战役同树）。领地互斥看不见这种细粒度，
所以这条要么由监控确认，要么就承认这个丢失窗口。别把我这段当成已经查过。

---

W-1680 就此收尾退出（板对我为空）。本文件是我这一轮唯一的产出，未动 master，
未建任何分支或 ref，未碰封存堆，零 API 调用。
