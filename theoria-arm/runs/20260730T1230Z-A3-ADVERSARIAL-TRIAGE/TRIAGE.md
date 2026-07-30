# cycle 49 对抗复核：三份报告的完整分诊

三个对抗性 subagent 各带一条视角攻 cycle 45–48 交付的六条论断
（迁移正当性 / 机器无关性与 check 10 / 过度声称）。**本文件是全部结论的落盘**——
上一世的复核 subagent 随会话死掉、结论蒸发过一次，这次先写盘再说。

**只存在于上下文里的信息视同不存在。** 下面每一条都带：判词、我是否独立复验、
本轮处置、以及没处置的话下一步该做什么。

## 本轮已修（4 条）

| # | findings | 复验 | 处置 |
|---|---|---|---|
| G1 | `flatten()` 对空容器不产生叶子 → 值为 `{}`/`[]` 的键对 added/removed/changed 三者同时不可见，包括**凭空发明一个顶层键** | 是，独立重现三个突变 | `7ee25bab`：修好的 flatten（空容器成叶子 + 元组路径 + 类型严格）重比七份，迁移干净；原脚本 docstring 加订正块 |
| G2 | `migrate_files_in_clone.py` 用集合比较 → 对顺序与重复失明 | 是 | 同上，按列表重测：顺序保持、无重复 |
| C10 | **check 10 是装饰性的**：改成 `for row in []` 后整套测试仍 272 passed；两条「守卫」测试一条抄函数体对副本断言、一条只断言检查名 | 是，亲自跑了 M-X 突变 | `2bf07d89`：重写为调用真 `run()` 读 check 10 判词；两个突变现在都被抓；顺带抓到我新测试自己的真空（fixture 不是 archive material） |
| A17 | 「67 个提交只经由 refs/stash」减法减错对象；点名的四个提交在 `refs/original/` 不在 stash；「4 个 arm version 只因 stash 而存在」实测 0 | 是，逐条复验 | `c5279081`：撤回，原文保留 + 顶部订正块，新目录带可重跑 `remeasure.json` |
| O12 | `0d88d423` 声称修掉的过度声称，原文仍逐字留在它编辑过的 `test_cost_shape.py:58-61` | 是 | 本提交：改正，并写明 `unpriced_usage_keys` 是冗余的那一个 |

## 未修，按严重度排（下一世从这里接）

### H1 —— `_files_the_clone_carries()` 仍以 `os.walk` 起手，只做减法
**实测**：往 `runs/20260729T004020Z-leg01/` 扔一个 `scratch_notes.txt`，
check 8 在那台机器上变红；删掉又绿。**同一个提交、同一份代码、两个答案**——
正是这条 leg 声称已经终结的那件事。函数只减掉「存在且被忽略」的文件，
从不问仓库「你到底装运什么」；一个未跟踪、又没被任何规则匹配的文件照样进 `files[]`。
仓库里没有任何被跟踪的 `.gitignore` 覆盖 `.DS_Store` / `Thumbs.db` / `*.orig` / `*~` / `*.swp`
（`git check-ignore -q` 对五者全部 rc=1）。
**所以 RUN_STATE:103 与 `backfill.py:1045` 的「答案不再取决于工作树」写大了**：
只关掉了「被忽略」那一类。
**正解**：`git ls-files`（仓库装运什么），不是 `os.walk` 减 `check-ignore`。
**代价**：`files[]` 会从「这个 run 的产物」变成「这个 run 被跟踪的产物」，
两个 gitignored 产物会整体离开清单——需要一个明确的判断，不是顺手改。

### H2 —— `core.excludesFile` 指向一个**被跟踪**文件可绕过 `-v` 守卫
`_rule_file_is_in_the_repository` 问的是「规则文件被跟踪吗」，
需要的性质是「这条规则一个克隆会不会应用」。两者不同：
`git config core.excludesFile myrules.txt`（`myrules.txt` 已提交）会让产物被静默
剔出 `files[]`，而该设置活在 `.git/config` 或 `~/.gitconfig`，不随克隆走。
**这正是 `6889b7e4` 声称消除的缺陷，经由它没枚举的第三条路。**

### H3 —— check 10 的判据是 `os.path.exists`，不是「在克隆里」
一条 present-but-untracked 的路径在这里过、在克隆里悬空。
**这道为终结「两台机器不一致」而写的检查，自己是机器相关的，同一个机制。**
今天只有一条列出路径处于该状态且恰好被规则覆盖，两棵树才一致——那是运气。
另：路径逃逸（`../../armtools/backfill.py`）、绝对路径、目录、
`C:\Windows\win.ini` 全部通过。

### H4 —— check 10 的作用域名不副实
自称「every file a manifest lists」，实际只看 `archive_material` 的 12/35 个目录，
**33 条列出路径从不被检查**。这是 `verify_provenance` 全文件的设计
（每道检查都有这个过滤），不是 check 10 独有——但**名字**说大了。
且 `20260729T080000Z-E14-crash-is-not-a-finding` 的 23 条路径全部不满足 check 10
的判据（它们是仓库根相对的，check 10 硬编码 `os.path.join(run_dir, p)`，
不知道归档里存在第二种路径约定）——它绿只是因为它没看。
**要么改名，要么扩覆盖，且必须先处理两种路径约定。**

### M5 —— 那条 `git diff` 引证什么也没证
`58e4de9f` 与 `RUN_STATE:270-272` 说「上面那条 `git diff` 的输出里就印着它们」，
但上面那条是 `git diff 53e6ea0b^ 53e6ea0b`，**零条删除行**（`grep -c` = 0）。
两个 sha256 在**另一个提交** `46612a9c` 的删除 hunk 里。
底层事实是真的；把它从「断言」升级为「可复核事实」的那句话，
递给读者的命令核不了任何东西。同一个提交里两段互相打架（「zero removals」/「the removal hunk」）。
**修法**：改引证为 `git diff 46612a9c^ 46612a9c`。（两个摘要已在 `7ee25bab` 里
写进被跟踪树，所以这条现在只剩引证本身要改。）

### M6 —— 「等价克隆里 270 passed」不可复现
`RUN_STATE:218-220` 与 PARTNER_SYNC 把「`.worktrees/res1c45-clone2` 里 10 checks + 270 passed」
写成本 leg 的**验收判据**。但该克隆 pin 在 `46612a9c`（reflog 只有一条，从未移动），
而 `46612a9c` 早于 `6889b7e4`——**同一段落称为「机器无关性那一半」的那个修法**，
也正是把 267 抬到 270 的那三条测试。该克隆里实测 **267**。
`10 checks` 复现，`270 passed` 不复现。
**修法**：要么在克隆里 `git fetch && git checkout` 到分支尖端重跑并更新数字，
要么把判据改写成它实际验的那件事。**别只改数字**——判据的意义是「在造出产物的机器
之外也绿」，而当时那棵树不含它被引为验收的那个修法。

### M7 —— 「不对称已被机器钉住」没被钉住
`0d88d423` 说三个采纳键的不对称「pinned in a test rather than left in prose」。
支撑第二半的断言只有 `assert "unmeasured_calls" not in report` /
`assert "missing_usage_keys" not in report`——那钉的是**一个 dict 顶层的键名缺席**，
不是「没有任何字段计算这个信息」。复核把 `costs()` 包一层、用别的名字暴露这两个量
（不对称因此为假），测试原样通过。
另：单次调用形状下 `unmeasured_calls` 可由 `model_calls - from_price_table.model_calls`
精确恢复；只有混入一个 unpriced **model** 时才不可恢复——注释没带这个 caveat。
**修法**：要么把断言改成对信息可恢复性的断言，要么把注释降级为「顶层键名唯一」。

### M8 —— 「23.6 小时、重试 20 次」归因到一个当时还不存在的成因
`71b882c8`（被指为成因）写于 2026-07-29T18:06:10Z，
而 `merge.log` 里该分支的 FLAG **有 18 条早于它**、16 条晚于它。
「20 attempts」来自 `[NEEDS-HUMAN: 20 attempts since 2026-07-29T04:14:01Z]`，
窗口比成因早开约 14 小时。真正的因果窗口是 13.05 小时。
且 `merge.log:1876` 是 OPS-M 就同一个计数器说过「the NEEDS-HUMAN counter overstates it…
aggregate at least three distinct causes across the day」。
`23.6` 也对不上任何一行日志（第 20 次时经过 22.6 小时）。
**修法**：改成因果窗口 13.05 小时，并注明计数器混合成因。

### L9–L13 —— 描述性/来源缺失（低，但都是真的）
* **L9**：444 行 diff 用「删掉 `base_commit` / `base_commit_check` / 整个 `budget` 块」
  描述，实际是 16 处顶层结构变化：`base_commit` 是**键存活、值变 null**（不是删除），
  另有 8 个顶层键被整体删除、8 个新增、28 个叶子改变，散文一个没提。结论（分流是对的）成立，证据描述是选择性的。
* **L10**：`46612a9c` 说「Nineteen tests across two files」。该提交新增 10 条
  （257→267 与它自己的通过数一致），两个文件合计 20 条。19 两头不靠。
* **L11**：「让论文的账单图把地板印成总额」说过头了。
  `figures/fig02_bill_shape.py:500-506` 的图注已经标明该数是重算值、
  与 CLI 数字交叉核对过、并写明画的是哪一个。行号引证与 `proxy/cost.py:186` 的引证都准确，
  升格的修辞不准确。
* **L12**：无产物支撑的数字：11 个突变表（无突变 harness、无输出文件）、
  「干净 master 漂 5 份」、scratch repo 的 `--no-index` 测量（repo 未保留）、
  CRLF 测量、「23 条测试」（已过时，现 24）。
  RUN_STATE §7 明写自己是「把断言升级为可核事实」的一节，这些没升级。
* **L13**：44/264 个 `upstream_pin` 值是字面量 `<redacted:key-shaped>` 而非十六进制摘要
  ——凭据脱敏器吃掉了形状像密钥的 sha256。**这条不在任何人的视角里，是顺带发现的，
  可能是本表最实的一条**，因为它意味着归档里有 44 个 provenance pin 是空的。

## 三条复核**攻不动**的（记下来，免得下一世重攻）

* 「21 added lines, three per manifest, zero removals」——精确。
* `migration.json` 七条记录的 `manifest_sha256_after` 与 `53e6ea0b` 提交文件的
  sha256 全部相等，7/7。
* `unpriced_usage_keys` 与 `usage_keys_the_table_cannot_price` 确实冗余——
  两个生产者都是同一批记录上同一次 `table.cost()` 的 `sorted(...) or None`，
  复核构造不出把它们分开的输入。
* `except OSError` 分支**确实朝安全方向失败**：git 缺席时 `files[]` 不是空的，
  是全量 walk 的超集（over-list，吵闹而非静默），端到端两道检查都变红、`main()` 返回 1。
  **唯一 caveat**：`_RULE_FILE_CACHE` 在 `OSError` 时缓存 `tracked=False` 且永不失效，
  一次瞬时的进程创建失败会在该进程剩余时间里把真 `.gitignore` 变成「未跟踪」。
  方向仍安全（over-list），但答案成了一个瞬时量的函数。

## 元教训（本轮第三次撞同一堵墙）

**给缺陷类命名不能防止它。** 本 leg 我三次做了这件事：
(1) 上一轮诊断「归档依赖未声明的外部形状」，同轮用一个克隆没有的
`.git/info/exclude` 重新引入它；
(2) 上一轮在 RUN_STATE §四写下「测试不能把期望值从被测代码里读出来」，
同轮交付了一条把 check 10 函数体抄一遍对副本断言的测试；
(3) 上一世心跳里写「**在它回来之前我已经自己攻掉两条**」——
而这三份报告里最严重的四条，一条都不在我自攻的范围内。

**自攻的价值是提前修，不是替代对抗复核。** 自己攻自己抓不到的正是自己的盲区，
而这一轮盲区恰好落在我攻过的那个函数里（空容器）、我没想到要攻的同源脚本里
（`migrate_files_in_clone`）、和我刚加的那道闸门里（check 10）。
