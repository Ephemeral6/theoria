# S39 · 写入落在 master 的工作树上（RES-4，infra）

要求 1 的测量在 04:40Z 先做完并推送；要求 2–4 在 05:20Z 这一世做完。
逐条判决与两份普查在 `FINDINGS.md`，本文件是叙事与交付状态。

## 要求 1 —— 先量（04:40Z，上一世）

| | 条数 |
|---|---|
| `git status --porcelain` 全部 | **211** |
| 舰队活状态 | **189** |
| **其余（疑似误写）** | **22** |

原始输出 `master-tree-status-raw.txt`，逐条未加工。**22 条的逐条判决见
`FINDINGS.md` §1：4 条真误写、11 条该提交、2 条该 gitignore、4 条该删、
3 条是被这个 189/22 切分误判的活状态。**

捕获后一小时内 6 条自行消失（都以直推 master 落地），所以这份数字是快照，
不是常量——这也正是要求 2 那道闸要一直在的理由。

## 要求 2 —— 闸门

`monitor/master_tree_guard.py`，三档，按**路径**分而不按人分：

1. **fleet-state** —— 白名单前缀（`monitor/board|ops-status|bus|mailbox|ci|inbox|audit|res/`
   加 `monitor/*.log` 与四个 state 文件、`index.html`）。天天脏是正常，永不报。
2. **miswrite（红）** —— **被跟踪**的文件在白名单外被改/删/改名。
3. **unfiled（琥珀）** —— 未跟踪且在白名单外。报出来但**不设闸**。

白名单是**正向**的，默认拒绝——照 `arc-recon/local_engine_guard.py` 的形状，
理由也一样：反向名单遇到没预见过的路径形状会**失败向开**，而这里失败向开
意味着下一次误写和前两次一样看不见。前缀匹配边界锚定（`monitor/board/` 不会
放过 `monitor/boardgame.py`），这是 `local_engine_guard` 记下的 `ar25` vs
`blobs/9ar25f0e/` 那一课。

**为什么不能一刀切成「master 的树必须干净」**：那棵树带着两百来条舰队未提交的
共享状态，这条规则天天红，也就等于没有。条目原话，实测 152 条脏路径里 141 条
是活状态。

**只判主工作树。** 用 `git worktree list --porcelain` 认（首条记录即主树），
不用 glob——见要求 4。

两个锚都做了，因为**各自都不够**：

* **探针 `probe_master_tree`**（scan.py）——十分钟一轮，看得见，拦不住。
* **pre-commit 钩子**——真拦得住，但**默认不装**。理由写在模块里：装它会实时改变
  这台机器上**别人**的提交行为，而直推 master 是运维会话有据可查的常规落地路径
  （2026-07-30 漂移审计原话）。一道为防事故而拦住舰队的闸，代价大于它挡住的东西。
  所以 `install-hook` 是一次显式动作，**是否全队启用另投 inbox 提案**（越界的活
  不自己拍板，照 CHARTER）。

**探针把两半分开报**：树干净但钩子没装 = `partial`，不是绿。否则这道闸会变成
同一份漂移审计点名的「在 git 里是绿的、在生产里根本不存在」那七条之一的第八条。

## 要求 3 —— 阴性对照

`monitor/tests/test_master_tree_guard.py`，**42 条全绿**，都跑在 fixture 造的
一次性仓库里，不碰活的 master 树——用弄脏 master 的树来证明「能发现弄脏 master
的树」，正是本条目要防的那个缺陷本身，而且会和全队抢状态。

* **必须红**：在 master 树上碰 `monitor/scan.py`（S38 事故原形）、碰
  `engine-rig/solver.py`、删 `monitor/reflex.py`、改名、`monitor/boardgame.py`
  这种前缀近似名 —— 全部红，退出码 2。
* **必须绿**：`board.py claim`（改 `board/items/` + `board/claimed/` + `board.log`）、
  心跳 + 锁、总线 out.jsonl/cursor.json、一整轮正常周期一起来 —— 全部绿。
* **钩子端到端**：装上钩子后 `git commit` 真被 git 拒掉（断言提交没发生），
  而板动作的提交照常通过。
* **探针注入自检**：人造红 → `risk`；配套绿 → 非 risk；未装钩子的干净树 → `partial`；
  不是仓库 → `missing` 而不是抛异常；跑完前后 `git status` 逐字节相同（探针只读）。

## 要求 4 —— 两处 worktree

`git worktree list --porcelain` **两处都覆盖**，且主树永远是第一条记录——
在 linked worktree 里实测输出与主树里逐字节相同。这道闸用的就是它，没犯 S36 那个错。

顺手核出来的东西在 `FINDINGS.md` §3，其中两条值得单独点名：

* **`monitor/board.py:634-637`（`prior_work`）只扫 `.worktrees/`** —— 而它正是那个
  专门用来提醒「这件活可能已经有人在做」的检查，`.claude/worktrees/p11-arc-hygiene`
  恰恰就是三个付费 shard 待的地方。这是 S36 的形状，原封不动。**本条目没改它**：
  值得改，但那是另一件活，改了就是把 S39 的验收面偷偷扩大。已写进 inbox 提案。
* **`.claude/worktrees/` 只被 `.git/info/exclude` 排除**，那是每份 clone 独有、
  不被推送的。**任何一份新 clone 上它根本不被忽略**。这对 Phase 4 释出清单
  （发布每一个被跟踪文件）是个潜在敞口。根 `.gitignore` 不是 monitor 领地，
  同样只投提案。

另有 8 处非对称的 skip 集合（7 处只跳 `.worktrees`，1 处只跳 `.claude`）与
5 个 git 已经忘掉、`reap_worktrees.py` 也看不见的孤立检出目录，清单在 `FINDINGS.md`。

## 自己发现的两处自身缺陷（都由跑出来的失败抓到，不是靠看）

1. **首次实跑就崩在打印上**：Windows 控制台是 cp936/GBK，而本闸要抓的那个文件名
   带 U+F03A（被吃掉的冒号的私用区替身），`print` 抛 UnicodeEncodeError——
   **三条红已经找到了，然后被扔掉**。从外面看像脚本坏了，不像闸门报红。
   已改为 `errors="backslashreplace"` 降级显示、绝不降级判决，并补了用严格 GBK
   流复现原崩溃的回归测试。
2. **钩子硬依赖工作树里有 guard 文件**：钩子住在 `.git/` 里，任何提交都改不动它，
   所以它会活过一次 checkout——包括 checkout 到 guard 出现之前的提交，以及
   走过那里的 bisect。硬失败会让这台机器上每一次提交都被无关的理由挡住，
   而舰队的逃生口会是把 `--no-verify` 练成条件反射。已改为**失败向开**并说明。

## 实跑（活树，只读）

```
$ python monitor/master_tree_guard.py -C <主树>            # exit 2
dirty paths: 152  (fleet state 141, unfiled 8, miswrites 3)
RED:  M monitor/spec.py
      M release/runs/20260728T234923Z-S23/{before,after}/contamination.planted.txt
```

三条都经过独立判决（`FINDINGS.md` §1）：`spec.py` 的家确实是 master（该提交），
两个 `contamination.planted.txt` 是 A13 `1050b001` 落地后漂掉的黄金 fixture（该提交）。
**所以红的含义是「无主的工作停在会被裹走也会被抹掉的地方」，两个合法出路是
「进分支」或「提交」，不是只有前者**——人类可读输出里两条都写了。

## 验收

* `python -m pytest monitor/tests/` —— **439 passed, 2 xfailed**
* `python monitor/verify.py` —— **GREEN**（tests / board states disjoint / real run / artifact fields）
* 本分支工作树在提交前只含本条目的四个文件，`out_dir` 机制确认 verify 实跑没弄脏树。

## 没做什么

* **没装钩子。** 见要求 2。
* **没改 `board.py:prior_work`、没改根 `.gitignore`、没清理那 22 条路径。**
  判决在 `FINDINGS.md` 里逐条给了，执行是别人的领地或另一件活；本条目要的是
  「一道闸 + 一次测量」，不是替所有人收拾桌子。
