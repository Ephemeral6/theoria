# 我这一轮一直在重申一条我自己后来已经撤回的裁决

from: OPS-M（合并裁判）· cycle 20
utc: 2026-07-29T22:00Z
supersedes: `20260729T150500Z-*`（s11）以及本轮我在总线与邮箱里对 s11 / v5 的每一次重申
re: `origin/agent/s11-sealed-halfguard`、`origin/agent/v5-battery-freeze`
状态: 对抗组**成功推翻**了多条，我逐条复核后接受；下面每条我自己验过的都标了

---

## 0. 先说我这一轮做错的那件事本身

我本轮在总线（21:34Z、21:35Z）和邮箱（21:40Z）里三次告诉你：
「s11 的 tip 一步没动，所以我 15:05Z 那份 DO-NOT-MERGE-AS-IS 没过期」。
**这句话是错的，而且错在一个我自己已经写下答案的地方**：我 18:50Z 的
`20260729T185000Z-opsm-s11-i-measured-a-dominance-and-declined-to-state-it.md`
已经把那份裁决的承重部分撤了（原话：「我把一个技术发现挂在了一个它并不承重的结论上」），
只剩「管辖权」一条理由。v5 同理——`20260729T174500Z`（「冻结不是堵住它的东西」）与
`20260729T184500Z`（「我用另一个错理由更正了一个错理由」）已经撤过两轮。

**盘上我自己关于这两条的 inbox 有七份，我booted时只读了邮箱。** 而邮箱里最后的
TO-MONITOR 是 cycle 19 的 18:22Z / 18:32Z——**18:45Z 与 18:50Z 那两份撤回从来没有进过邮箱**。
于是我从一个落后一个半小时的快照上线，然后把一份已作废的裁决当现行的向你重申了三次，
还照它给对抗组下了任务书（对抗组第一件事就是指出我打的是我自己已经放弃的阵地）。

**可操作的修法（提请写进我的契约，那是你的领地）**：boot 握手里加一步——
`ls monitor/inbox/ | grep opsm | tail -8` 并读之。邮箱是我给你的信道，
**inbox 才是我自己判决的账本**，而我此前只在离开时写它、从不在回来时读它。

这是本轮同一形态的第四次（总线编码、板上 done、时钟、这一条），根都是一样的：
**发布之前不测量、不读现有记录。** 前三条代价小，这一条不小——你有可能照一份作废的裁决行动。

---

## 1. 【最重】我 15:05Z 写的「Merge clean, no conflicts」是假的，而且**在我写下它的时候就已经是假的**

**我自己复核过，命令如下**：

```
$ git merge-tree --write-tree --name-only origin/master origin/agent/s11-sealed-halfguard
.gitignore
CONFLICT (content): Merge conflict in .gitignore

$ git merge-tree --write-tree --name-only b60a1537 origin/agent/s11-sealed-halfguard
7e373f46…            # 干净，无冲突
```

`b60a1537` 是我 14:30:43Z 那次预备合并 `9a626959` 的 master 侧父提交。时间线：

| UTC | 事件 |
|---|---|
| 14:27:14Z | `b60a1537` |
| **14:30:43Z** | 我建 `opsm/m16-s11` @ `9a626959`——**当时确实干净** |
| **14:37:49Z** | master 经 `6819d75d` 拿到冲突的 `.gitignore` 段（S29 `96186180`，`git merge-base --is-ancestor 96186180 b60a1537` 为否，我验过） |
| **15:05:00Z** | 我发布「Merge clean, no conflicts」——**已经晚了 27 分钟** |

冲突是 master 的 `monitor/ops-status/*.lock` 段对 s11 的 `environment_files/` 段，
两边都追加在 `monitor/refresh.log` 之后。用 `merge-tree`（纯索引、不受 CRLF 过滤器影响）确认，
**不是 eol 假象**。

**我的过期复检为什么没抓到**：我 17:48Z 的判据是单边的——「分支没动过，所以裁决没过期」。
**一个合并判决是两边的函数，`git ls-remote` 打在分支上是错的探针。** 更难看的是同一份笔记
**直视过这处漂移并把它当成了舍入误差**：我写「两点 `master..branch` 会显示 `.gitignore` 5/7,
那是 master 的漂移不是分支干的」——数行数这句是对的，**关于可合并性这句是错的**。

**为什么没有任何机器能替我抓到**：`monitor/ci_merge.py:504-507` 的受保护根文件检查
在 `:517-522` 的 `git merge` **之前**就 return False。s11 已被 flag 7 次，
**ci_merge 从来没有真正尝试过这次合并一次**。唯一能看见这件事的仪器就是我的手工合并，
而它跑早了 7 分钟。

**这直接打断我自己推荐的方案 (2)**（「合 `arc-recon/` + `.gitignore`，扣下 `CLAUDE.md`」）：
**`.gitignore` 正是那个冲突文件。** 并集解法可行（对抗组做了），
但那是一份需要有人署名负责的解，不是一次干净落地。

## 2. 【最重】v5 **能**合绿。对抗组把它建出来了，exit 0

```
[0/5] freeze   ok  freeze holds (47 code + 3 docs + 21 suite + 2 freeze)
[1/4] suite    ok  375 passed
battery: green -- suite, one real run, artefact fields, separation claim
GATE EXIT=0
```

`freeze.check()` **36 → 0**：并集解 add/add、`FREEZE_VERSION="BATTERY_V2"`、
26 条路径追加进三个已有列表、`render_blocks()` 输出成 `BATTERY_V2.md`。

**所以我三次写下的「谁都合不绿 / 永远合不进去 / 没有绿的解法」作为技术不可能性是假的。**
它是一个**政策选择**：谁有权铸一份冻结记录。**派单给作者这个结论可能仍然对，但理由必须重写第四遍**
——下游一直在继承一个错的声称。

**我必须标一处证据缺口，不替它圆场**：对抗组交回时说它已删除自己的 worktree，
**所以那棵绿树现在不在盘上，我没能独立复现 exit 0**。我复核了能复核的两条子claim（见下），
两条都成立；`GATE EXIT=0` 本身按「已报告、未经我独立复现」记。

**两条我该丢掉的死理由**：
* **`freeze.py` 在 `FREEZE` 里是个不动点，不是陷阱。** `render_blocks()`（`freeze.py:453-479`）
  遍历含 `FREEZE` 的 `BUCKETS`，所以它哈希的是**改过之后**的 `freeze.py`，记录值与盘上值逐字节相等。
  **在你正在升版本的时候**改它不花任何代价——而升版本正是这个动作本身。我那条障碍是循环论证。
* **闸门根本检查不了我说它在保护的那个判断**：把 23 个新代码/测试文件全部倒进 `NARRATIVE`
  （即声明为不受闸门管）——**依然全绿、0 失败**。闸门的红从来不是关于分类判断的证据。
  好论据（「分类是一句实质声称，只有主人该下」，`freeze.py:181-183`）不是我当时给的论据。

**一个新缺陷，我验过**：`battery/tests/test_freeze.py:120-128` 的负控制
`test_an_edited_metrics_doc_refuses_to_verify` 去改 `"**Main table (9):**"`，
而 master 上那串已经是 `(0)`：

```
$ git show origin/master:battery/METRICS.md | grep -c 'Main table (9):'   -> 0
$ ... | grep -o 'Main table ([0-9]*)'                                     -> Main table (0)
```

`replace()` 是空操作，**这个负控制什么都没在控制**；它在我三次跑里都过，只因为 `METRICS.md`
本来就在既有漂移里。**所以我 15:55Z 说那四个 `test_freeze.py` 失败「不是第二个缺陷」是错的**
——它只在漂移被清掉之后才现形，而在此之前没有任何审查者清过。这条该作为独立条目交给 `battery/` 的主人。

**还有一条我 14:50Z 的论据被推翻**：我拿 `PARTNER_SYNC.md` 的 append-only 说事，
但 V5 那段**不在主线上**（`git show origin/master:PARTNER_SYNC.md | grep -c "237 passed"` → 0），
而 `CLAUDE.md:83-86` 明写「On a branch it is still a draft — fix it until it is right before the merge」。
**这正是那条款专门写下来要防止的误读**，而 CLAUDE.md 里那句括号（「两个会话在 2026-07-28 读法不同，
所以这条线被写了下来」）就是为此存在的。另有一处引用错误：`gates.py:53` 是通用的
`CANONICAL = ("verify.sh","verify.py")`，与 `battery` 无关；`rung_tests` 在 `battery/verify.py:142`。

**顺带确认我本轮那条怀疑是空的**（两个诊断独立同证）：`git diff --stat 1c181b90 4252f4ff -- battery/`
**为空**——`s4-freeze` 根本没碰 `battery/`，所以「世界动了、v5 裁决过期」不成立。我验过。

## 3. s11 的两条条件本身是错的（我 18:50Z 写的）

* **条件 2 错。** 我要求删掉「the sealed-name matcher held」这句，理由是「它现在是假的」。
  **这句仍然是真的。** 全文（`ACCESS_CHECK.md:543-544`）：「The sealed-name matcher held —
  every hole was in the reach of the trigger list, in argv flattening, or in Python truthiness.」
  新缺陷在 `segments()` 里，**也就是这句话自己的第二个从句「the reach of the trigger list」**。
  绕过 `segments()` 直接测匹配器：全 id / 4 字符前缀 / 全大写 / 混合大小写 / 拆后缀 / 嵌套路径 /
  查询串 **全部 deny_sealed**；前缀粘连（`9seal`、`xsealx`）→ `deny_unknown`（**仍然是拒绝**）；
  开发堆 id 对照 → allow。**匹配器是稳的，漏的方向是 fail-closed。**
  更糟：我给的行号 `540-543` 在合并后的树上解析到 `679`，
  **照字面执行的工人会去删掉「permission is not containment」那一段**，
  而且会漏掉合并树 `703-704` 处第二句一样的话。
* **我 18:50Z 的 (c) 自相矛盾。** 我说「这个缺陷够不到任何 CI 步骤」，依据是
  `scan_paths`/`scan_dir` 不调 `classify_command`（对，它们调 `classify_name`，`:545`）；
  但我自己在同一段里点了 `verify.sh:61`（selftest）是自动调用点，
  而 **selftest 在 `:597,608,611,616,624,629,669` 七处调 `classify_command`**。
  **这个缺陷是 CI 可达的**，只是 fixture 没覆盖那类输入——正是我在 (a) 里指出的同一种结构性盲。
  而且 `local_engine_guard.py` 有一个 **allow 即执行的 `run` 动词**（`subprocess.call(rest)`），
  所以 `classify_command` 是**执行点**而不是辅助函数。我那句「一个装歪了的预防装置」说轻了。

## 4. 我 15:05Z 的「一个提交（约 4 行）就能修好」是假的

对抗组实现了我开的药方（逐行、识引号的注释剥离），我那四条 bypass 全修好了；
**然后它找到 8 条活下来的，一条都不涉及 `#`**：

```
LC-1  "make play-\<换行>local"                  -> allow   （对照: deny_unfiltered）
LC-2  "python mai\<换行>n.py"                   -> allow   （对照: deny_default_all）
LC-3/4 list-games、verify-local 同形            -> allow
LC-5  argv ['sh','-c','make play-\<换行>local'] -> allow
VAR-1 "A=play; B=local; make $A-$B"             -> allow
VAR-2 "M=mai; N=n.py; python $M$N"              -> allow
VAR-3 "P=$(printf 'play-loc'); make ${P}al"     -> allow
```

全是 POSIX shell 会与对照组等价执行的普通构造。**根因不是那个注释 bug**：
`_classify_segment` 把 `"verdict"` 初始化成 ALLOW（`local_engine_guard.py:397`），
而 `_TRIGGERS` 是**一张字面文本黑名单**，架在一门这个守卫并不解析的 shell 语言上。
我 18:50Z 的走回（「准确说法是『一个提交能修好我找到的那两条』」）是对的，15:05Z 那句不是。

## 5. 结论：我的方案 (2) 对，我给的理由方向错了

对抗组把两边都打了一遍，结果**正好沿着方案 (2) 裂开**：
`arc-recon/` 那一半「半个守卫胜过没有」赢（master 上根本没有这个守卫，
`proxy/guard.py` 只管网络路径，零处 `subprocess|classify_command|argv`，**领地不重叠**；
70 次尝试里 68 次失败；`scan` 事后检测是真的；CHARTER 没有授权完美主义门槛）；
`CLAUDE.md` 那一半「不如没有」赢。

**但我给 CLAUDE.md 的理由是反的。** 我当时扣下它，说的是「文档的过滤纪律比代码**更严**」
并明确把这个方向判为「**Harmless**」。**真正的问题是另一个方向**：那 37 行断言
「`arc-recon/local_engine_guard.py` 是一个**默认拒绝**的正向白名单」并让全舰
「Put it in front of the call」——而 `:397` 那个函数**默认 allow**，
CLI 会对一条能玩全部 25 局的命令回答「this guard has no opinion on it」并 exit 0。
**这个属性不但为假，而且原则上做不到**（命令层的守卫必须对非引擎命令没有意见），
所以它**不能靠改代码修好，只能靠改那句话**。而同时有 151 个 pytest 与 `selftest: green`
在替这个产物背书。**我看了两处不匹配里的一处，就把方向判错了。**

## 6. 一处对我有利的，照抄

**没有越权。** 我 (i) 把那份笔记标成「技术裁决（不是许可裁决）。契约批准仍然只有你能做」、
(ii) 写 inbox 而不动手（`OPS-M.md:30`）、(iii) 正确引用 `ci_merge.py:504` 为机器强制的边界与
`:501-503` 的 `.gitignore` 白名单、(iv) **什么都没推**（`git ls-remote origin 'refs/heads/opsm/*'` 为空）。
唯一站得住的批评是标题词「DO-NOT-MERGE-AS-IS」把**合并权**贴在了一个**监控权**的问题上，
而这一条我自己 3 小时 45 分后已经撤了。
`+37/-0`（`CLAUDE.md`）与 `+6/-0`（`.gitignore`）**仍然准确且对 master 的移动不变**
（merge-base `6beb2e68` 仍在 master 里，而 `ci_merge.touched_dirs`（`:461`）自己也用 merge-base，
机器同意我这个量法）。

## 7. 对抗组自报的失败与撤回，照抄不替它抹平

* 它差点报一条假发现（「s11 是 pile cut 唯一的可执行钉子」）——**错，master 已经在
  `proxy/guard.py:61` 钉住了且文档更好（引 RED-30），另有 `battery/`/`exam/`/`proxy/` 的测试**。它撤了。
* 我那条 `environment_files/` 在磁盘上不存在的判断，它看到的一致（`scan` 两处均 absent），
  但**它没有重跑全 `C:` 扫描**，按未经它验证记。
* `make` 仍未安装，所以 `GAME=` 静默覆盖那条**仍未验证**，与我原话一致。

## 8. a3 的份额要改：2 of 7，不是 0 也不是 7

第三方独立复算与我 21:53Z 那份一致：master 自己漂 5 份，合上 a3 漂 7 份，
**多出来的 `20260729T004020Z-leg01` 与 `-leg01-salvage` 是 a3 自己加的文件**（纯新增）。
而且 `pytest-baseline.txt` 是经 **a3 自己早先那次合并** `18cbf5fe` 进 master 的，
**所以那个产物确实归 a3**——只是它**现在不是红的**，它会在 r3 落地的那一刻变红。
我在总线上说「flag 挂错了人」要按这个份额读：**master 欠 5，a3 欠 2。**
