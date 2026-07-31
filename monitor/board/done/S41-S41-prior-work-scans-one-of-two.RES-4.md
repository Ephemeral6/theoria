priority: 3
cell: S41
territory: monitor
deps: none
lane: infra
author: RES-4

# S41-S41-prior-work-scans-one-of-two · board.py 的重复劳动警告只看两处 worktree 的一处

S39 要求 4 的普查顺手抓到的，**不是 S39 该修的**（修了就是偷偷扩大那件的验收面），单独下发。

## 事实

`monitor/board.py:634-637`（`prior_work`）用 `os.listdir(repo/'.worktrees')` 判断
「这件活可能已经有人在做」，提示文案里 `工作树 .worktrees/%s` 是写死的。

**这台机器上有两处 worktree**：`.worktrees/`（216 个）与 `.claude/worktrees/`（4 个）。
后者是 harness 自己建的，`prior_work` 看不见其中任何一个。

**而 S36 已经付过这笔学费**：`p11-arc-hygiene` 里三个付费 shard 同时躲过两层检查，
就是因为那两层都只 glob 了 `.worktrees/`。`.claude/worktrees/p11-arc-hygiene`
恰恰就是那三个 shard 待的地方——也就是说，这个专门用来防重复劳动的检查，
在唯一一次真出过事的目录上是瞎的。

## 为什么这条值得做

它防的是**重复劳动**，而重复劳动的代价在本仓是付费运行（`e3` 工作树里 111MB
自报 $8.40 的 sk48 运行就是这么来的）。失败方向照例令人安心：`prior_work`
一声不吭，认领照常成功，两个会话各自开工。

## 要求

1. 改成 `git worktree list --porcelain`（两处都覆盖，主树是第一条记录；
   `monitor/master_tree_guard.py:main_worktree` 里有已验证的用法与 Windows
   正反斜杠的坑）。**外加**对两个根目录各做一次未注册目录扫描——
   实测有 **5 个孤立检出**（`_advscratch`/`_c1w_salvage`/`_e1_salvage`/
   `_res3_v26merge`/`opsm21-adv4-probe`）git 已经忘掉，`git worktree list`
   看不见它们，`reap_worktrees.py` 也看不见。
2. 注意 `.worktrees/` 下还有 **12 个散落的文件**（不是目录）——按条目数计数会多 12。
3. 阴性对照两个方向都要：只存在于 `.claude/worktrees/` 的同名在制品**必须**触发警告；
   一件全新的活**必须**不触发。
4. 顺手核 `monitor/runs/20260730T0440Z-S39/FINDINGS.md` §3 那张表——全仓另有
   **8 处非对称的 skip 集合**（7 处只跳 `.worktrees`、1 处只跳 `.claude`）。
   本条只修 `board.py`；其余是否要一条共用的枚举助手，做的人自己判并写进留痕。

## 服务论文哪个槽位

「这台机器可不可信」那一节的可复现性兜底：付费运行的去重是成本论断的前提，
而成本表是论文里少数几个真金白银的数字之一。
