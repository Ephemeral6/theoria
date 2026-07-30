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
   加 `monitor/*.log` 与逐个核过写入者的九个生成/活状态文件）。天天脏是正常，永不报。
   代码后缀（`CODE_SUFFIXES`）在目录前缀之前判，所以白名单目录洗不白源码。
2. **miswrite（红）** —— **被跟踪**的文件在白名单外被改/删/改名。措辞见文末第 3 条：
   准确含义是「无主的源码停在会被裹走也会被抹掉的地方」，出路是进分支**或**提交。
3. **unfiled** —— 未跟踪且在白名单外。单独计数（补救方式不同），但**照样设闸**。
   初版这里是「琥珀、不设闸」，被对抗性复核推翻了，见文末第 1 条。

白名单是**正向**的，默认拒绝——照 `arc-recon/local_engine_guard.py` 的形状，
理由也一样：反向名单遇到没预见过的路径形状会**失败向开**，而这里失败向开
意味着下一次误写和前两次一样看不见。前缀匹配边界锚定（`monitor/board/` 不会
放过 `monitor/boardgame.py`），这是 `local_engine_guard` 记下的 `ar25` vs
`blobs/9ar25f0e/` 那一课。

**为什么不能一刀切成「master 的树必须干净」**：那棵树带着两百来条舰队未提交的
共享状态，这条规则天天红，也就等于没有。条目原话，实测 155 条脏路径里 143 条
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

`monitor/tests/test_master_tree_guard.py`，**49 条全绿**，都跑在 fixture 造的
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
dirty paths: 155  (fleet state 143, unfiled 9, miswrites 3)
RED（被跟踪）:  M monitor/spec.py
                M release/runs/20260728T234923Z-S23/{before,after}/contamination.planted.txt
RED（未跟踪）:  9 条，含 monitor/res/RES-3-notes/ 与
                theoria-arm/runs/20260729T2040Z-A3-unpriced/
                ——这两条正是 FINDINGS.md 判过的真误写，初版看不见它们
```

三条都经过独立判决（`FINDINGS.md` §1）：`spec.py` 的家确实是 master（该提交），
两个 `contamination.planted.txt` 是 A13 `1050b001` 落地后漂掉的黄金 fixture（该提交）。
**所以红的含义是「无主的工作停在会被裹走也会被抹掉的地方」，两个合法出路是
「进分支」或「提交」，不是只有前者**——人类可读输出里两条都写了。

## 验收

* `python -m pytest monitor/tests/` —— **449 passed, 2 xfailed**（复核前 439）
* `python monitor/verify.py` —— **GREEN**（tests / board states disjoint / real run / artifact fields）
* 上面这两行是**对抗性复核的全部修改都落盘之后**才量的。
* 本分支工作树在提交前只含本条目的四个文件，`out_dir` 机制确认 verify 实跑没弄脏树。

## 没做什么

* **没装钩子。** 见要求 2。
* **没改 `board.py:prior_work`、没改根 `.gitignore`、没清理那 22 条路径。**
  判决在 `FINDINGS.md` 里逐条给了，执行是别人的领地或另一件活；本条目要的是
  「一道闸 + 一次测量」，不是替所有人收拾桌子。

---

## 对抗性复核（交付前必须做的那一步，它推翻了不少东西）

按契约派了一个专职**推翻**这道闸的 subagent。它提了 11 条，**9 条是真的**，
其中第一条是硬伤。全部已修，下面按严重程度记，因为这些缺陷本身比闸门更有信息量。

**1（硬伤）· 这道闸抓不到催生它的那次事故。** S38 的原话是「`monitor/scan.py`
**加两个新文件**」——**新文件是未跟踪的**，而初版把未跟踪判成琥珀、不设闸、退出 0。
复核把 S39 **自己的三个交付物**摆在 master 的树上重放：`red=False, miswrites=0, 退出 0`。
干活的 agent 建文件远多于改文件，所以初版放过的是这类事故的大多数。
**而我为此写下的理由本身是错的**：我写「未跟踪文件不会被别人一次 `git add <path>`
裹走」——`git add -A`、`git add .`、`git commit -a` 都裹，而本仓已经有一个提交
就叫 **"On master: autostash"**。
**改法**：两档都设闸。而那个「未跟踪设闸会天天红」的顾虑**我从来没量过**；
现在量了：活树上 9 条未跟踪非白名单路径，`FINDINGS.md` 里逐条独立判过，
**没有一条是正当在途的**——全是该提交／该忽略／该删／该在分支上。
所以它今天红是因为真有东西要收拾，收拾完就绿，这才叫闸。

**2 · 白名单目录会洗白源码。** `_under_prefix` 是裸 `startswith`，于是
`monitor/board/helper.py`、`monitor/ci/patcher.py`、`monitor/audit/drift_tool.py`
全判成 fleet-state，**在任何一档都不出现**。已加 `CODE_SUFFIXES`：代码后缀
在目录前缀之前判，白名单目录装的是 `.md/.json/.jsonl/.log`，从不装代码。

**2b · 同一个洞的第二身costume（我自己跑测试撞出来的）**：git 把整个未跟踪目录
折叠成一条，于是**整目录未跟踪的 `monitor/ci/`** 会被白名单整块放过、连同里面的
代码。已改为把「白名单会放过的未跟踪目录」用 `-uall` 限定重列、逐条判——
只展开白名单目录，绝不展开 `.claude/`（那会枚举出一百个完整检出）。

**3 · 判词过头。** 活树上三条红（`spec.py` + 两个 `contamination.planted.txt`）
在 `FINDINGS.md` 里都判的是 SHOULD-BE-COMMITTED，不是 MISWRITE。**闸门叫它们
「误写」是过头话**；准确的说法是「无主的源码停在会被裹走也会被抹掉的地方」，
两个合法出路是进分支**或**提交。人类可读输出与探针文案都已按这个改。

**4 · 钩子只看树、不看分支。** 初版在主检出里对**任何**分支上的提交都拒——
包括 agent 被抓到之后「我这就建分支好好提交」这个**正确的补救动作**。
另外 merge/rebase/cherry-pick/revert/amend 一律被拒，而冲突合并被拒时打印的建议
（`git restore --staged`）**会毁掉冲突解决**。已改为：只在 HEAD 就是 `master`
且没有 merge/rebase/cherry-pick/revert 在途时才判。

**5 · 干净的 `git merge --no-ff` 绕过钩子**（git 走的是 `pre-merge-commit`）。
**不补这个洞，改成明写不管**：合并正是分支工作**应该**进 master 的路径。
现在「冲突合并被拒、干净合并放行」这个任意的不一致没有了——两者都不管。

**6 · 缺 python 时钩子失败向闭**，与它自己写的契约相反。`exec python` 在
只有 python3 的机器、或 Windows 上 `python.exe` 是应用商店别名时返回 127，
git 挡住**每一次**提交，包括纯心跳提交。已改为装钩子时把 `sys.executable`
烧进去，再退 `python3`/`python`/`py`，全找不到就放行并说明。

**7 · 监控自己的活状态文件误报红。** `history.jsonl`、`crashes.jsonl`、
`loop_state.json`、`accounts.json` 都是每轮被重写的，不在白名单里。已逐个查
写它们的代码后加进去（`scan.py:1621`/`:3082`、`reflex.py:28`、`accounts.py`）。
**复核多报了两个，没照单全收**：`monitor/app.html` 是 `scan.py` 只读不写的
前端源码、`monitor/orphan_dispositions.json` 是 S36 手写的裁决簿——两者都该在
未提交时报红，因为跟生成物住同一个目录就放过它们，正是这张表存在的理由的反面。

**8 · `hook_path` 犯了它 docstring 里声称要避免的那个错。** 相对的
`core.hooksPath` 被拼到 `--show-toplevel` 上，而那在 linked worktree 里是**那个
worktree 的根**——从 worktree 装钩子会装进 worktree，然后 `hook_installed()`
对一个已装的钩子报 False。**而那个以此命名的测试之所以通过，是因为 fixture
从没设过 `core.hooksPath`，它走的是 fallback 分支**。已改为对主工作树解析。

**9 · 探针文案算错了。** 「%d 条脏路径全是舰队活状态，另有 %d 条未跟踪」——
琥珀本来就算在 total 里，加了两遍，实测说成「153 条全是活状态，另有 9 条」，
真相是 141/9/3。三个数是同一个总数的划分。已改，并且 green 分支不再把琥珀名单
整个丢掉。

**10 · 测试自己的问题四条，全改：** `test_live_master_tree_is_judgeable`
**是空过的**（`total >= 0` 恒真，分档求和对任何分类器都成立——复核把 `classify`
改成全返回 fleet-state，它照样绿）；`test_untracked_scratch_is_amber_not_red`
**把 bug 写成了需求**（断言的是实现行为不是条目要求）；
`test_probe_returns_missing_rather_than_raising` 的 `or "无法断言"` 恒真
（那串就硬编码在唯一的 missing 模板里）；`test_probe_never_emits_amber`
迭代一个单元素元组、只覆盖 risk 一支。

**11 · 顺手修的小项**：`_run` 没有 timeout（挂死的 git 会挂死整个扫描，而探针
跑在十分钟循环里）；`report()` 一次 spawn 三个 `git worktree list --porcelain`
（221 个 worktree 上 0.85s，而真正干活的 `git status` 只要 0.12s），改成解析一次。

**复核攻了但没攻破的**：`-z` 对活树那个 U+F03A 文件名的解析、两个解析器的
rename 源字段消费、边界锚定、**部分提交**（`git commit -- <path>` 会走 git 的临时
索引，一条只含板动作的部分提交正确放行，而真索引里同时躺着源码文件）、
子目录里发起的提交、`git commit -a`、装钩子时拒绝覆盖别人的钩子、
GBK 严格流下的 `_emit_human`、linked worktree 的两个方向、探针的状态词表与只读性。

**复核的两条我没照办，理由写在上面**：第 3 条我改的是措辞而不是判据（那三条确实
不该无主地停在那里），第 5 条我选择明写「合并不在管辖范围」而不是补 `pre-merge-commit`。

## 复核后的最终验收

* `python -m pytest monitor/tests/` —— **449 passed, 2 xfailed**（改前 439）
* `python monitor/verify.py` —— **GREEN**
* 活树实跑：155 条脏路径 = 143 活状态 + 9 未跟踪 + 3 被跟踪源码，退出 2。
  **两条此前看不见的、`FINDINGS.md` 判过的真误写现在都被抓到了**：
  `monitor/res/RES-3-notes/` 与 `theoria-arm/runs/20260729T2040Z-A3-unpriced/`。
  `monitor/index.html` 曾因 `.html` 是代码后缀而误报，已按「显式命名的生成物
  优先于后缀启发式」修好。
