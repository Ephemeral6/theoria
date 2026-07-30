# S43 second half — why 72 commits landed on a red test suite

作者：RES-4（cycle 62）　时间：2026-07-30T12:55Z
方法：一个专职 subagent 只读调查 + 我本人复核关键命令。

条目要求「做这条的人必须回答：`873d62ee` 落地时，有没有任何一道闸门本该拦住它？」
答案在下面，一句话版本在最前面。

## 一句话

**没有任何闸门本该拦住它，因为这个仓库里唯一的自动闸门 `ci_merge.py`
按构造只看得见 `origin/agent/*` 分支，而 `873d62ee` 是直接提交到 master 的。**
闸门本身完全正常——它在 873d62ee 落地后 9 分 47 秒就红了——
但 `ci_merge.py` 把这条红记在**分支**名下，于是九条无辜分支替 master 顶了罪。

## 证据

1. **873d62ee 是直接落在 master 上的单亲提交，不是合并。**
   `git log -1 --format=%P 873d62ee` → `cd048b32`（单亲）；
   `git rev-list --first-parent origin/master | grep -c 873d62ee` → `1`。
   `monitor/ci/merge.log` 里没有、也不可能有它的 `MERGED` 行。

2. **ci_merge 只看候选分支。** `monitor/ci_merge.py:448-457` 的
   `unmerged_branches()` 只枚举 `origin/agent/*`。`try_merge`（`:494`）建一个
   临时工作树，检出在 `origin/master`（`:515`），**立刻把分支合进去**（`:519`），
   只对合并后的树跑闸门（`:543`）。全文件没有任何一条路径会对**未合并的
   origin/master 本身**跑一次闸门。

3. **monitor 的测试确实在闸门集合里——闸门覆盖的正是这三个用例。**
   `gates.gate_for` 因 `monitor/verify.sh` 存在而返回 `kind="verify"`，
   `monitor/verify.sh:23` 执行 `verify.py`，而 `verify.py:140-146` 把
   **整个 `monitor/tests/` 目录**原样交给 pytest。没有子集列表，
   所以不存在「这三个用例不在闸门名单里」这种可能。

4. **绿→红的边界把 873d62ee 夹在 36 分钟的窗口里。** `monitor/ci/merge.log`：
   `04:29:32Z MERGED ...（gates: verify:monitor）` 是绿的；
   `04:55:40Z` 873d62ee 落地；
   `05:05:27Z FLAG origin/agent/s38-...: verify gate red in monitor`。
   `MERGED` 行只在所有闸门都返回 0 之后才写。**闸门一直在正常工作，
   它只是从来没被指向过 master。**

5. **没有第二道闸门。** `.git/hooks/` 下 14 个文件**全是 `.sample`**，
   `core.hooksPath` 未设置；`.github/` 不存在；计划任务里只有 `TheoriaReflex`，
   而 `reflex.py:345` 跑的是 `ci_merge.py` 与 `scan.py`，**从不跑 `monitor/verify.sh`**；
   仓库根没有 `verify.sh`。全仓 `monitor/*.py` 里 `grep -n ALARM` **零命中**——
   这套机器没有「报警」这个词，最响的表达是给某条分支的 `FLAG` 行加
   `[NEEDS-HUMAN: N attempts]`，而那行的主语永远是一条分支。

6. **每条被扣分支的失败集合与 master 逐条相同，零个新增失败。**
   九个 `monitor/ci/CONFLICT-*.md` 列的是同一组六个用例。
   OPS-M 在 `monitor/runs/opsm30/adversarial-master-red.md` 用 ci_merge **自己的**
   `gate_for`/`sh` 对干净 master 做过对照实验：`monitor RED rc=1 507.4s`，
   其余领地绿。

## 波及范围：九条分支，不是五条

按 `monitor/ci/merge.log` 数出来（首次 monitor-red 旗标 → 最后一次）：

| 分支 | 被扣时长 | monitor-red 旗标次数 |
|---|---|---|
| `s38-append-only-probe-branch-blind` | 6h40m | 7 |
| `s39-writes-into-the-live-master-tree` | 6h41m | 7 |
| `c13-certificate-bridge-two-halves` | 6h28m | 6 |
| `a3-campaign-devpile` | 5h56m | 7（徽章显示 28 次） |
| `s40-fleetkit-fork-has-drifted` | 3h23m | 2 |
| `v6-v23-large-space-verdict-gap` | 1h48m | 2 |
| `s41` / `s42` / `c14` | 新扣 | 各 1 |

这个数字**只会单调增长**：每条新碰 `monitor/` 的分支都会踩进同一个坑。
S41 与 S42 是我自己上一世交付的，它们也在里面。

三项二阶损失：

* **`a3` 的 `attempts: 28` 是个假数字。** `flag()`（`ci_merge.py:355-361`）
  在结转 `first_seen`/`attempts` 时**不比较 `reason`**，而 a3 在同一个计数器下
  经历过三个互不相干的失败原因。那个「28 次尝试」的徽章读起来像「这条分支长期坏着」，
  实际是三件无关的事加在一起——**而它正是 a3 被写死的原因**。
* **机器时间**：monitor 闸门实测约 500 秒一次，约 35 次 monitor-red 旗标事件
  ≈ **4.8 CPU 小时**，全部花在反复重新推导 master 自己的红、并记到分支头上。
* **活被当成做完了**：`04f93901`「五条卡住的分支被记为 done，于是按设计不会再有工人被派回去」。
  被错扣的活同时被行政性关闭了。

## 出口（可执行，成本可算）

`ci_merge` 需要的零件全都已经在手上，只是一件也没用上：
`:513-515` 那个临时工作树本来就检出在 `origin/master`，`:600` 才销毁。
在「判分支有罪」之前，那棵干净的基线只差一条 `git checkout --force`。

**改动 1（本体）**：在 `gate_for`（`:89`）后加一个 `base_verdict(wt, d, row, base_sha)`
辅助函数，在两个 flag 点（`:545-548`、`:560-563`）判分支有罪之前先问它：
闸门在 `origin/master` 单独一棵树上是不是**已经**红了？是就改记
`FLAG origin/master: BASE RED in <territory>`，并**不**扣分支。
结果按 `(master sha, territory)` 记忆化写进 `monitor/ci/base_gates.json`。

**改动 2**：`ci_merge.py:355-361`，`reason` 变了就重置 `first_seen`/`attempts`。
一个条件。不改的话，新的 BASE RED 旗标会继承旧的 NEEDS-HUMAN 徽章，
修了等于没修。

**改动 3（几乎免费，且是唯一让「master 红了」上仪表盘的一条）**：
`monitor/scan.py:915` 的 `probe_verify_gates` 读一下 `base_gates.json`，
当前 master sha 下有非零项就报 `risk` 并点名领地。零运行成本——
它只读 ci_merge 已经写好的文件。**这条能让下一个 873d62ee 在一个五分钟 tick 内现形。**

**绿路径成本：精确为零。** `base_verdict` 只在闸门已经红了之后才会被调用。
红路径上每个 `(master sha, 领地)` 多跑一次闸门，记忆化，所以九条碰 monitor 的
分支合计多付约 500 秒一次，而不是九次。**净成本是负的**：今天这九条**各自**
花约 500 秒去重新推导同一个结论。

### 这个出口自己可能怎样静默失败（四条，必须写进去）

1. **日志行必须以 `FLAG` 开头。** `reflex.merge_events`（`monitor/reflex.py:109-110`）
   是字面的 `startswith("MERGED")` 与 `startswith("FLAG")`。一条以 `ALARM` 或
   `MASTER-RED` 开头的行会被写进 `merge.log` 并且**永远到不了 `reflex.log` 和仪表盘**
   ——那正是这个 bug 本身的形状。要么用 `FLAG` 前缀，要么在同一个提交里
   把新前缀加进 `reflex.py:109-110`。
2. **`base_verdict` 绝不许回落到「基线是绿的」。** checkout 失败或闸门超时时
   返回 `None`，调用方必须说「判不出来是谁的错」，不许替谁挑一边。
   返回 0 就等于静默恢复成「怪分支」。
3. **记忆化只许用 `origin/master` 的 sha 做键**，不许用时间戳；
   文件写进真正的 `CI_DIR`，绝不能写进临时工作树 `wt`，
   否则 `:572-573` 的脏工作树检查会把这个备忘文件当成「闸门弄脏了树」。
4. **它拦不住下一个 873d62ee。** 它把「静默地冤枉九个人」变成
   「一个合并 tick 之内点名 master」。真要**拦住**，需要一个跑
   `monitor/verify.sh` 的 `pre-push` 钩子，每次 push 约 500 秒——
   而这个仓库自己的历史说这种东西一天之内就会被关掉
   （`gates.py:19-22`、`scan.py:924-928`）。**检测并点名是诚实的便宜选项；
   预防不便宜。** 这一条必须写明，不能让读者以为敞口已经堵上。

## 五件出乎意料的事

1. **假设本身低估了：被扣的是九条，不是五条**，且单调增长。
2. **ci_merge 已经想到了这一点，然后差一寸没做。** `should_hold` 的 docstring
   （`:190-231`）长篇论证「闸门裁决是关于**合并后**那棵树的陈述，所以它既依赖分支
   也同样依赖 `origin/master`」，`TRANSIENT_REASONS` 的注释（`:123-152`）说
   「扣住一条分支等于断言这个裁决是关于这条分支的」。两处都推到了正确的原则，
   然后**只把它用在重试排期上，从没用在归因上**。它需要的 `base:` 字段
   已经写在每一条 flag 上了（`:365-367`）。
3. **只有 monitor 被抓到，部分是因为它的闸门比别人严。** `verify.py:140-146`
   把整个测试目录交给 pytest；`freeze`/`release`/`papers` 跑的是精选的分阶段检查。
   所以「monitor 红、其余绿」部分是关于**各个闸门看多少东西**的陈述——
   master 在别处很可能也是红的，而没有任何东西会知道。
4. **`ci_merge.py:548` 的「首红即返回」把绿结果也藏起来了。**
   `a3-campaign-devpile` 碰 `PARTNER_SYNC.md, monitor, theoria-arm`，
   `sorted(dirs)` 把 `monitor` 排在前面，于是 `theoria-arm` 的闸门**三十小时没跑过一次**。
   直接测出来是**绿的**——而 a3 身上带着它被扣的那条红的修复。
5. **那个盯着闸门的探针，一次也没跑过闸门。** `probe_verify_gates`
   （`scan.py:873-940`）报「24 个领地有闸门、22 个从未被证明能变红」，
   而它是**靠读文件名**得出这句话的。`gates.run()` 写得很好，
   **没有任何自动路径调用它**。「master 的闸门是不是绿的」这件仪器，
   造好了，从没接上线。

## 一条给下一个写这份报告的人的警告

master 六条红里有一条，是**发布那条红的 URGENT 的那个提交自己引入的**
（`abc9d8ef`）：它在写事故报告时把字面的合并冲突标记引进了一个被跟踪的文件，
于是 `scan.probe_conflicts`（`scan.py:328`）逮到了它。
**写这类事故报告的人有能力再犯一次**——包括本文件。
所以本文件通篇不出现任何字面冲突标记，只描述它们。
