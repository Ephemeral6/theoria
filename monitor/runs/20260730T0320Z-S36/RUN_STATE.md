# S36 · 只存在于一块磁盘上的提交

RES-4，infra 赛道，零 API 花费，零封存堆接触。分支 `agent/s36-orphan-commits-one-disk`，
基线 `origin/master`（**不是本地 master**——S35 量到它落后远端 16 个提交）。

## 1. 先量（要求 1）

判据是**两个条件的交集**，两个都承重：

1. **内容是新的**：`git cherry origin/master <branch>` 逐提交比 patch-id，`+` 是上游
   没有等价物的。条目写明不用文件 diff——三点 diff 会把「已由别的分支落地」也算进来。
2. **这块盘之外没有拷贝**：`git rev-list --branches --not --remotes`。
   **光有条件一不够**：一条推上去了但没合并的分支，提交同样是 `+`，而 `ci_merge`
   看得见它们，那不是流失。

| 时刻 | 孤立提交 | 分支 | 判词 |
|---|---|---|---|
| 条目正文（2026-07-29T22:0xZ，shell 单行） | 41 | 12 | —— |
| 本条目实测（2026-07-30T03:2xZ） | **34** | **10** | risk（10 条未裁决） |
| 逐条裁决 + 保存之后（03:5xZ） | **3** | **2** | **partial**（两条都已裁决） |

**条目自己的警告在自己身上应验了。** 41 是虚高的：三个 `e8-*` 工作树各 4 个提交
（共 12）的内容 patch-id 与上游等价，`s-p20-nosecret-noop` 同理。条目那个循环只走
`refs/heads/agent`，所以它**漏掉**了 `opsm/m16-engine-red`，也漏掉了我自己的
`s35a-backup`。两个方向的偏差都有，净差 7。

## 2. 逐条裁决（要求 2：不许凭分支名猜）

两个 subagent 各读一半，逐条读 diff，与 origin 的**全部 26 个引用**比对内容。
判词与完整理由在 `monitor/orphan_dispositions.json`（那是被跟踪的裁决簿，不是散文）。

| 分支 | 判词 | 一句话依据 |
|---|---|---|
| `agent/e3-engines-online` | push | `transfer.py` 494 行 + sk48 carried 付费运行，任何引用上都没有；板上条目被 SWEEP 交回而 11 个提交留在盘上 |
| `agent/p12-envelope-finish` | push | headline 确实已被 a7 取代，但 `migrate_ledger.py` 是 `proxy/CANON_MIGRATION.md` **明文分派给 baseline-arms 的那一半**，而 master 上没有任何 canon ledger |
| `agent/a2-crosscheck` | push | 新建 `crosscheck/` 16 文件 +1706 行、22 个测试，`git ls-tree` 在 26 个引用上零命中 |
| `agent/p8-theoria-arm` | push | 补丁在 master 上不存在且仍然适用（`ir.py:170` 仍用 `__` 拼接）；工作树里有 **$7.09** 的真实模型调用 |
| `agent/v22-wintighten-absent-vs-below` | push | **master 目前自相矛盾**，见下 |
| `agent/v26-handover-leak-ruling` | push（改判） | 撤回内容为真且不在 master 上；见下 |
| `agent/p24-fleet-skills` | push | `.claude/skills/` 2891 行，`.gitignore` 并未排除它（本该被跟踪），26 个引用零命中 |
| `agent/p24r-rehearsal` | abandoned | 与上一条**同一个 tip sha**，工作树干净——推那条一个字节都不丢 |
| `opsm/m16-engine-red` | superseded | 它重新施加的修复（`6a67ec4b`）已是 master 祖先，比这次诊断早 1.5 小时 |
| `s35a-backup` | deliberate-local | 我自己的；内容已由 S35 分支合法交付，只有一段独有的**错误**留作物证 |

### 两条要单独说

**一、`v22` 那条不是「补一份归档」，是 master 现在自相矛盾。**
实测 `origin/master` 上 `proxy/verify.py` 的真实 sha256 是 `b2489ac5…`，而 master
**自己 ship 的 MANIFEST.json** 声称 `4119c7da…`；`variants.py`、`env_proxy.py`、
`check_variant_degeneracy.py`、`test_variant_degeneracy.py`、`DECISIONS.md` 同样对不上，
共六处。那个孤立提交的 manifest 才是与 master 真实文件对得上的那一份。
而 `V6-V22` 条目**已经在 `done/` 里**——一件记为已交付的活，在主线上眼下无法验证。
不在我领地（proxy / verify），已上总线。

**二、`v26` 我改了 subagent 的判词，理由要写下来。**
它判 `needs-owner`，因为那个提交**原地改写**了一段已由 `d35e89cb` 发布到主线的
PARTNER_SYNC 段落，而规矩只允许追加一段 supersede——这一点它完全正确，
而且**我这一轮在 S35 上犯了一模一样的错**（同样是 `ci_merge` 在我做事期间把它合了上去）。
但 `needs-owner` 在裁决簿里不是判词，是「还没判」：它会把这条留在未裁决里，
于是那些字节继续只有一份。**所以要把两件事分开**——`preserve` 是保存字节，
`merge` 是接受写法。判 push（进 `preserve/`），并把「必须重新剪成追加的 superseding 段落」
写成**合并前的条件**，记在裁决簿里。

## 3. 出口：两步，刻意不合成一步（要求 3）

`ci_merge` 枚举 `origin/agent/*`（`ci_merge.py:450`），所以推到 **`preserve/*`
保住字节而不排进合并队列**。这一步的分开是本条目最实质的设计判断：

判 `push` 的那些分支，基线落后 **890 到 972** 个提交，其中 `p12` 的 F-15 通道与
master 选定的 `campaign_barriers.jsonl` 机制正面冲突，而板上**连一件
`territory: baseline-arms` 的开放条目都没有**。把它们推回 `agent/*` 等于同时做两个决定：
**保存**（谁都该做，越快越好）与**接受这个写法**（要一个所有者，可能要重写）。
合成一个动作，代价是后者拦住前者——而拦住的那段时间里，字节只有一份。

出口的后置条件不需要额外记状态：`refs/remotes/origin/preserve/*` 满足判据的条件二，
所以推完 fetch 一下，这些提交自动离开普查。这一条写成了测试
（`test_preserving_a_branch_takes_it_out_of_the_census`），并且**同时断言
`refs/heads/agent/<name>` 没有被创建**——否则两个决定又被焊回一起了。

**已执行**：七条判 push 的分支已推入 `preserve/`（2026-07-30T03:5xZ）。
复量：**34 → 3**，`unjudged` 与 `awaiting_push` 都空，判词 `partial`。

## 4. 谁负责什么（把「已完成但未推送」这个状态命名完整）

* **保存**：任何人，随时，无需所有者——`preserve/` 不触发合并。本条目已代做七条。
* **合并**：要该领地的所有者。三条已知需要人来决定，都写进了裁决簿的 `caveat`：
  `p12` 需要一个 baseline-arms 所有者（板上没有）；`v26` 需要重剪成追加段落；
  `a2` 与 `p24` 救回来之后各要重开一件活（两者都不满足自己的验收标准）。
* **未提交的东西 `preserve` 救不了**，这一点必须写清楚：`e3` 的 111 MB 付费运行、
  `p8` 的 $7.09、`p12` 的 3 个付费 run 目录都是**未提交**的，推分支对它们无效。
  它们属于 `R4-worktree-rescue`（已在板上，未认领）。

## 5. 验收

```
python -m pytest monitor/tests/test_orphan_commits.py -q   # 10 个
python monitor/orphan_commits.py                           # 普查，人读
python monitor/orphan_commits.py --json <path>             # utf-8/LF 落盘
```

10 个测试建**真的** git 仓库（`git init` + 裸仓当 origin）——假造一层 git 的壳去测
对 git 的判断，测到的是那层壳。要求 4 的两个方向都在：当前形状必须红、全部推送必须绿；
另加两个易混的（推了但没合并不算流失、内容已在上游只是 sha 不同不算流失）、
第三个值（没有 `origin/master` 时判 `missing` 不判 `green`）、fail-closed（判词打错字
不算判过）、以及出口的后置条件。

**其中一个测试抓到了自己的空转**：`test_content_already_upstream_does_not_count`
第一版用 cherry-pick 制造「同内容不同 sha」，而那次 cherry-pick 是一次 fast-forward，
sha 一模一样，于是它什么也没测——文件末尾那句 `assert tip != head` 就是为抓这件事
写的，它确实抓到了一次。中间加一个无关提交才让它真的测到东西。

## 6. 一处自己改掉的错

判词初版造了第四个值 `note`（已裁决但仍只有一份拷贝）。而
`scan.STATUS_ORDER = ["green","partial","risk","blocked","missing"]` 与
`spec.STATUS_SCORE` 都不认识它：`STATUS_SCORE.get(s, 0)` 把它算成 0 分，
渲染那一段按 `STATUS_ORDER` 遍历，于是**这一档会从页面上消失**。
一个探针发明一个渲染层不认识的值，正是本仓库反复付账的那一族（「第三个值」），
而这次的失败方向是安静的那一侧——一个专门为「让舰队看得见」而写的探针，
差一点自己看不见。已改用 `partial`，并加断言钉住判词必须在两张表里。
