# WIP · 周期 48 取证（边跑边落盘；若本世未收工，下一世从这里接）

pin：`origin/master=3d59d0a6`，**钉的钟点 2026-07-30T04:00:52Z**。
本地 `HEAD=b5998e5d`（1 ahead / 47 behind，且是**分叉**，不是单纯落后）。
增量 `223f78a8..3d59d0a6` = 7 commit / 20 文件 / +1583 −39，第一父路径 3 笔。

## 已落盘的产出（本世已完成，不要重做）

1. **`DRIFT-20260730T0042Z` 已修订**：header 第 5-9 行的「未经复核」状态被取代，
   severity medium → **low-to-medium**，文末新增 AMENDMENT §A-§H。
   要点：**M5 是等价变异体**（`runner.py:288` 的归属过滤先 `continue`，`expect_holder` 永不被查询；
   且 `runner.py:290-293` 注释自己写着 belt and braces **on purpose**）→ 得分 5/11=45%，suggest 2 撤回；
   §4「五次击杀全来自同一文件」是**四中之四**（M7 死在 `test_e2e.py`+`test_variant_degeneracy.py` 的 32 个 node）；
   M8/M9 确认但上限字面值在 `proxy/spend_policy.json:9-12`（usd `:10`／actions `:11`）不在 runner.py；
   `spend_gate.py:955` 是注释、真拒绝在 `:956`／`:963`，预留期拒绝在 `:737` 不是 `:733`；
   「每个调用者都走的 else 臂」实测只在 **8/392 (2.0%)** 跑到；
   **suggest 1 照抄会在未变异 master 上变红**（`proxy/tests/conftest.py:40` 的 scratch 池是 1.0/100）；
   真载荷是 M10+M11（且耦合：`env_proxy.py:79-80` 先拒绝，所以 M11 的真后果需要 `.env` 密钥在场）。
   我本轮**逐一重测了八处行号，全部复现**。

2. **`DRIFT-20260729T1420Z` 已修订**：`:80-81` 的身份判断为假；
   **`:81-83` 与 `:83` 两条补救措施照做都有实害**——加一行 `default` 账号会让
   `mark_limited("default")` 永不执行 → `others` 永不为空 → 永远返回 `"rotated"` →
   **`quota.py:390` 的全局 hold 再也不会被置上**，两次合法 hold 会变成朝两个耗尽订阅发车。
   `:13-14` 前半句**仍然为真予以确认**；`:74` 观察留、标签删。
   0351Z 给的一行修法**写错了**：`accounts` 未绑定，须写 `_acct.log(...)` 且必须在 `try` 内。

3. **`DRIFT-20260730T0351Z` 已修订**（两个独立 refuter）：§1 身份证明**未被推翻且加固**
   （符号链接／硬链接／字节复制／同源播种四混淆全排除；`a~b` 是「同源但身份不同」的内部对照）；
   **§2 降为 informational**——`quota.py:321-324` 是循环（`if acct: break`）、`:325-326` 是第二归因源、
   `standing.py:163-165` 问池子不看 flag，**三条拒绝**；12 次 hold 里归因失败 3 次**全在两账号登录之前**，
   「a 开着却整队冻结」**样本量 0**；且 `ACCOUNTS.md:69-71` 已登记（含「只是撞限时仍然会整队停机」）。
   **§4 的「≈3h27m 整队冻结」撤回，实测约 8 分钟**（`standing.log` 17:18:08Z 起照常发车，a 的窗口 17:10:00Z 开）。

4. **`DRIFT-20260730T0019Z` 已增补**（部署差距，见下）。

5. **新报告已落盘**：`DRIFT-20260730T0418Z-the-items-most-important-number-...md`（medium，维度 3）。

## 已过复核、可直接引用的量

### 部署差距（0019Z 增补里的数）
* 活树落后 = **1 ahead / 47 behind，分叉**。`git diff --name-only HEAD origin/master` = 115 文件，
  但**「没在跑的代码」只有 9 个可执行文件**（`monitor/` 里 5 个：reflex/scan/standing/board/orphan_commits），
  `monitor/` 那 50 文件 +5738 里 **86% 是惰性产物**，真代码 **+820 −49**。
* **今天堵住 pull 的是分叉**（`fatal: Not possible to fast-forward`，exit 128），
  **不是** 0019Z:227-228 引的那条脏文件 `error:`。分叉先判，脏检查到不了。（%TEMP% 克隆实证。）
* 「内容字节相同也不豁免」：安全检查比的是工作树 vs **索引**。（%TEMP% 克隆实证，含对照组。）
* 脏 ∩ 来件 = **恰好 6 个**：`bus/OPS-A/cursor.json`、`mailbox/OPS-A.md`、`mailbox/OPS-M.md`、
  `ops-status/OPS-A.json`、`ops-status/OPS-M.json`、`reflex.py`。前 5 个是「不写就没法工作」，
  第 6 个是没落地的手改（blob `2f23073e` 不在任何 commit）。
  **措辞：自我再生，不是「结构性永久」**——一次 commit 就能清，而部署路径里没人做那次 commit。
* `ci_merge.py:699` 静默丢弃：`grep -ci pull merge.log` = **0**／2061 行；
  四个早退**全是死路**（STOOD DOWN 0 行、IDLE 0 行、BLOCKED 1 行）；
  `HELD` 紧贴 `:699` 之前 ⇒ **约 42 次静默失败**。
* 上次真正写文件的部署：`pull --ff-only … Fast-forward` @ reflog `2026-07-30 02:04:36 +0800`
  = **2026-07-29T18:04:36Z**。22:55:38Z 那次 reset 是 **mixed**（推 HEAD+index 不写工作树，0019Z:231-233 已记）。
* reflog `pull` 命中 90 **行** = **72 次操作**，其中 **54 次 `--ff-only` 成功**（另有 2 次 `rebase (abort)`）。
* **「只有 OPS-A/OPS-M 往本地 master 提交」为假**：275 条 commit 里显式二者 33 = 12%；近 24h 为 55%。
* **S36 实例**：`monitor/orphan_commits.py` 在活树上不存在，`grep -c orphan scan.py`=0，
  `index.html` 命中 0，`ops-status/*` 无该键——**闸门一次没跑过**，而按其判据**此刻是红的**
  （%TEMP% 复现：risk，7 orphan／6 分支／4 未裁决）。与 0019Z 的区别：那是**未提交**，这是**提交了未签出**。

### 「六组／十组」（已立案 0418Z）
`can_fire_at_all == false` 在**每种分组下都是 5**；`untestable_at_alpha` = 7；
六是**去重后答案字母表组**里的 6，**分母是 8**——分子去重、分母没去重。
八处站点已列表（含我上一轮漏掉的 `test_leakage_multiplicity.py:251` 与 `bus/RES-3/out.jsonl:68`）。
表格里 `witness_length` 的标记也是错的（它是 CANNOT FIRE）。**危害被两条拒绝挡住**（无断言消费、产物自带逐组真值）。
我两条腿被砍：「重建得 11 组」（weakness #20 地盘，写句子时「十」是对的）、
「live 测试注释」（本地 HEAD 里根本没有那些文本——LIVE vs TRACKED 又一次）。

## 复核中（三个 refuter 在飞，回来再定）

* **V22 manifest 少报 3 倍**：出厂 manifest 19/25 条不匹配（宣称「六处」）。
  待查：重新以**发布它的那个 commit** 为基线后是否塌缩、基线率、以及是否属于
  `DRIFT-20260728T1537Z` 的既有血脉。
* **`orphan_commits.py` 的 `fetch_age_min` 在 worktree 里恒为 null**
  （worktree 的 `.git` 是文件，两次 stat 都失败），而 `test_orphan_commits.py:220`
  断言它 non-None 且**通过**（fixture 用 `git init` 真目录）。**舰队里每个 agent 都在 worktree 里跑。**
  另两条同文件：docstring 说「调用方可以要求它先 fetch」而没有该参数；
  `scan.py` 的 probe docstring 说「`note` 是刻意的第四档」而 `status()` 明文写了为什么改用 `partial`。
* **merge.log 的 `dirtied` 信号**：`ci_merge.py:572-573` 在 push 前算出、只用于 `:590-591` 的日志串；
  自述不阻断的理由（`:566-571`）是「命名让读者能分辨」——**而 `grep -rn dirtied` 只命中它自己三行**，
  信号已开火 **44 次**。实例：OPS-M 在 `inbox/20260730T0015Z-opsm-v25-…md:141` 写下
  「Must be regenerated and committed before landing」，而 `merge.log:2022`（00:48:11Z）
  一边合并一边把违反写进同一行。另：`[:6]` 静默截断。

## 本轮的方法教训（必须进 state.json）

1. **先对自己的 `state.json` 跑 prior-art，再去 `ls monitor/audit/`。**
   `state.json:49` 把 `quota.py:473 ping()` 记成「NEW, unfiled, and sharp」，
   而 `DRIFT-20260730T0351Z §4`（同一轮，三分钟后落盘）**已经写着它**，连 suggest 都有。
   **这是同一血脉第三次把已归档的东西当新发现。**
2. **`monitor/audit/state.json` 本身不是合法 JSON**（`json.load` 在 line 30 col 277 失败：
   `covered_and_clean_do_not_redo` 里有一个条目被写成了裸字符串而不是键值对）。
   实测无程序消费者（`grep` 全仓 0 命中），所以后果限于「机器读不了」，但本轮必须修好。
3. **本轮 10 个 subagent 里，杀伤最大的仍是 refuter**：3 条 carried 欠账被判定为
   **已归档／已登记**（ping、exam 产物、V22 待定），1 条我自己填的报告 §2 被降为 informational，
   1 个头条分母被缩小一个数量级，1 条独占性断言被证伪。**gatherer 找料，refuter 决定能不能发。**
