# S28 条目 1、4、5 —— `board.py`

做的人：RES-4 主会话（本组两次派 subagent，两次都被 API 529 打死，未写一字）。
零 API 花费，封存堆零接触。所有取证都是只读或临时目录。

---

## 条目 1 · 领地互斥把条目从每一个分区里抹掉

`cmd_list` 印四段（available / reserved / blocked / claimed），而
`candidates()` 里的 `if m["territory"] in busy: continue` 把被领地互斥挡住的条目
从**每一段里都抹掉**。板于是读起来是「人人有活干」，而不是「卡住了」。

### 修之前（实测，真板）

拿真的 `items/` 与 `claimed/` 跑一遍旧 `cmd_list`，再和磁盘上的条目对账：

```
items/ on disk: 11
claimed: 5  ['A3-campaign-devpile', 'P19-P19',
             'S28-no-third-value-in-the-monitor', 'S4-freeze-complete',
             'V2-V25-leakage-loo-and-multiplicity']

=== partitions printed by `list` ===
   === available (通用工人可领 1) ===
   === reserved（有主，等其赛道研究员来领 2） ===
   === claimed ===
   === done (121) ===

ready items in items/ that `list` never prints: 8
   A16-A16-launch-gate-wired
   A3-campaign-level2
   A8-campaign-ledger-pipeline
   E3-engines-online
   R4-worktree-rescue
   S-S34-papers-owes-a-verify-gate
   V2-V25-verify-does-not-check-what-is-committed
   V6-V23-large-space-verdict-gap
```

**11 件条目里有 8 件一个字都不提，而表头写着 `available: 1`。**
条目原文估的是 6 件，实测 8 件。

### 修之后（新代码 + 同一份真数据）

```
=== available (通用工人可领 1) ===
  p1  V23-figures-sources-absent   cell=V5  territory=figures        unlaned
=== reserved（有主，等其赛道研究员来领 3） ===
  p1  E18-survey-numbers-reproducible lane=verify   owner=RES-3(2分钟前) territory=engine-rig
  p2  S-S34-papers-owes-a-verify-gate lane=paper    owner=RES-2(2分钟前) territory=papers
  p3  S22-access-check-close       lane=infra    owner=RES-4(14分钟前) territory=arc-recon
=== territory-blocked (7) ===
  p1  A3-campaign-level2           territory=theoria-arm    领地 theoria-arm 被 A3-campaign-devpile 占着
  p1  R4-worktree-rescue           territory=theoria-arm    领地 theoria-arm 被 A3-campaign-devpile 占着
  p2  A16-A16-launch-gate-wired    territory=theoria-arm    领地 theoria-arm 被 A3-campaign-devpile 占着
  p2  A8-campaign-ledger-pipeline  territory=theoria-arm    领地 theoria-arm 被 A3-campaign-devpile 占着
  p2  V6-V23-large-space-verdict-gap territory=exam           领地 exam 被 V2-V25-leakage-loo-and-multiplicity 占着
  p3  E3-engines-online            territory=theoria-arm    领地 theoria-arm 被 A3-campaign-devpile 占着
  p3  V2-V25-verify-does-not-check-what-is-committed territory=exam           领地 exam 被 V2-V25-leakage-loo-and-multiplicity 占着
```

（两次跑之间板动过：`P19` 交付了，`S-S34` 的赛道主人回来了，所以 8 → 7。）

**顺手读出来的一件事**：七件里有五件全在等**同一个**认领
（`A3-campaign-devpile` 占着 `theoria-arm`）。这正是条目要求「连同占住领地的那条
claim 一起列」的理由——不列出来，读板的人看不出瓶颈是一个人手上的一件活。

### 两个设计选择

* **用集合差，不逐条枚举原因。** 先算出已经印出去的 id，剩下的就是被 withheld 的，
  再去诊断为什么。将来 `candidates()` 多一条排除规则，这段不会跟着漏，
  只会把它诊断成 `原因不明 —— 排除规则变了而这段没跟上`。
  **「我不知道为什么」是一句要报的话，静默不是。** 有测试钉这条路径。
* **发现了第二类隐身，一并修了。** `reserved` 那段只遍历 `LANE_OWNER` 的键，
  所以一条**没有常驻研究员**的赛道上的活，两段都进不去。诊断里单列一条
  `赛道 X 没有常驻研究员`。

---

## 条目 4 · `heartbeat_age` 信任被 git 跟踪文件的 mtime

`heartbeat_age` 读 `ops-status/<编号>.json` 的 **mtime**，而那是一个被 git
**跟踪**的文件：任何 merge / reset / autostash 都能把一个死会话的心跳摸活。
条目记录的现场：`OPS-R.json` 自报 05:59Z，`heartbeat_age` 返回 12 分钟，
reflog 显示 10:19:43Z 有一次 reset 摸新了它。

**误差只朝一个方向走**：年龄偏小 → 主人算活着 → 赛道继续预留、领地继续上锁、
认领不被交回。这是本条目反复出现的形状：缺省值倒向好消息。

### 修

拆成 `heartbeat_evidence(agent) -> (分钟, 来源)`，`heartbeat_age` 变成薄封装
（契约不变：`None` 仍然表示从未启动；调用方遍布 board / scan / standing）。

* 优先读 `ops-status/<编号>.lock`——**未被跟踪且已被忽略**（根 `.gitignore` 第 24 行，
  这一半上游已经做掉了），所以 git 碰不到它。这也是 `standing.py` 的
  `occupied()` 一直在用的判据（锁新鲜度 + 单调 cycle）。
* 锁不存在时仍回落到 json 的 mtime，**但来源会说出来**（`mtime-touchable`），
  `cmd_list` 把它印成 `13分钟前(mtime，可被 merge 摸新)`。
  这里的第三个值不是一个数字，**是那个数字的出处**。

### 阴性样本

`test_the_lock_is_preferred_over_the_tracked_file` 复刻那次事故：
锁 200 分钟前、json 的 mtime 被摸到**现在**。旧代码返回 0 分钟（活着），
新代码返回 ≥199 分钟（停摆）。

另有 `test_stale_lanes_now_rests_on_the_untouchable_signal`：`stale_lanes()` 是
这条修复最要紧的消费者——它决定一条赛道的活是否对通用工人开放。

---

## 条目 5 · 裸 `except OSError` 把任何 rename 故障变成 `BOARD-EMPTY`

`cmd_claim` 的认领 rename 原来是：

```python
try:
    os.rename(src, dst)                # atomic: first one wins
except OSError:
    continue
```

`continue` 走完循环就印 `BOARD-EMPTY`，而**工人被告知那意味着「收尾退出」**。
异常被丢弃，`note()` 只在成功路径调用，所以一次假的 BOARD-EMPTY 在 `board.log` 里
零痕迹。触发条件比看上去常见：监控自身持续在 open 这些文件，而 Windows 的
**WinError 32 是 OSError 的子类**。对照组是 `cmd_done` / `cmd_release`——
同一个 rename，它们完全不捕获。

### 修

只捕获 `FileNotFoundError`（docstring 说那才是唯一预期的竞态——另一个工人抢先了），
其余照抛。

### 阴性样本

* `test_a_locked_file_no_longer_becomes_board_empty`：`os.rename` 抛
  `PermissionError(32)`，必须**抛出来**，不许印 BOARD-EMPTY；
* `test_a_genuine_claim_race_is_still_swallowed`（阴性对照）：抛
  `FileNotFoundError` 时必须照旧静默并印 BOARD-EMPTY——否则板上每一个繁忙时刻
  都会变成一次崩溃。

---

## 写测试时顺带抓到的第四个（同一个病，已修）

`meta()` 解析条目头部字段用的是 `r"^%s:\s*(\S+)"`。**`\s*` 跨行**，所以一个
**空**的 `lane:` 字段会把下一行的第一个非空白 token 吃进来当值。实测：

```python
head = 'priority: 1\nterritory: t1\nlane: \n\n# ORPHAN-1\n'
re.search(r'^lane:\s*(\S+)', head, re.M).group(1)   ->  '#'
```

一个**没填**的字段静默变成一个**看起来合理**的值（`lane="#"`），
于是那个条目会被当成「属于赛道 `#`」——而 `#` 没有主人，条目从此谁也领不到。
这就是本条目的病症：「没写」和「写了这个」编码成同一个东西。
改成 `[^\S\n]*`（只吃行内空白），并留了一条正负成对的测试。

**这个 bug 是我的测试夹具逼出来的**：夹具写了一个空 `lane:`，两条测试因此变红。
我先怀疑是自己的新代码，查下去才发现是 `meta()` 十几个提交前就有的行为。
记下来是因为它说明一件事——**这类 bug 只在有人构造异常输入时才现形，
而这个仓库的测试此前从没给过任何字段一个空值。**

---

## 测试

`monitor/tests/test_board_no_third_value.py`，15 条，全绿：

```
monitor $ python -m pytest tests/test_board_no_third_value.py -q
...............                                                          [100%]
```

阴性对照，逐条对应：

* `test_nothing_withheld_prints_no_new_partition` —— **本组最重要的一条**。
  没有被挡住的条目时，新分区**一个字都不许印**：它排在 122 行的 done 列表上方，
  而「每次都报警等于没报警」在这个位置代价最低；
* `test_a_dependency_blocked_item_is_not_double_reported` —— `blocked` 已经报过的
  条目不许被第二段重复报，否则两个计数都在说谎；
* `test_never_started_is_still_none` / `test_a_live_session_reads_fresh` ——
  契约不变，且活会话不许被判死；
* `test_a_genuine_claim_race_is_still_swallowed` —— 真竞态必须照旧静默；
* `test_an_empty_metadata_field_does_not_borrow_the_next_line` 里的
  `territory` 仍须正常解析；
* `test_the_new_partition_survives_a_cp936_console` —— 逐行 `encode("cp936")`。
  一次早先的修复就是在**已经把条目 rename 进 `claimed/` 之后**才抛
  `UnicodeEncodeError`：板上记下一次成功认领，认领者只看到 traceback 和零条活。

## 安全线

`board.py` 是活代码，舰队此刻正在从主检出调用它。本组**没有**对主检出跑过任何
会改板的命令（claim / done / release / sweep）；改板的测试全在临时目录里做。
取证那两次 `cmd_list` 是只读的，其中「新代码 + 真数据」那次是把模块的
`ITEMS/CLAIMED/DONE/OPS_STATUS` 指到主检出后**只读**调用。
