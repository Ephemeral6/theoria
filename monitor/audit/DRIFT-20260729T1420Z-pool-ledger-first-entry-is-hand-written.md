# DRIFT-pool-ledger-first-entry-is-hand-written

severity: medium
dimension: 3（证据漂移）——兼 1（生成物被手改）
audit range: `9bc8c880..ad778386`（3 提交），周期 37，OPS-A
utc: 2026-07-29T14:20Z

## claim

账号池账本上**唯一一条记录**——`b` 被关到 15:00Z——不是轮换器写的，是手写的；
而 `quota_state.json` 的 `note` 把它叙述成「**this is the first real use of the pool**」。
被关的这个账号**从未发过一次车**：它的行里没有 `launches` 键，全树 228 份
dispatch 日志里没有任何一份带 `account=b`。这条记录同时还断言了一个树上无法佐证的
身份等式：「`b`（the machine default）」——而池子的代码恰恰把机器默认登录命名为
`default(no-pool)`，**就是为了把它和池内账号区分开**。

## evidence

**一、轮换器在那个时刻不可能算出 `b`**

`accounts.log` 全文三行，第三行：
```
2026-07-29T14:03:03Z LIMITED b until 2026-07-29T15:00:00Z (You've hit your session limit · resets 11pm (Asia/Shanghai))
```
`mark_limited` 的账号只有一个来源：`account_of_log()`（`quota.py:278-301`），它读日志头
`account=(\S+)`，读不出来返回 `None`；`_rotate_on_limit` 归因不出就
`return "no-pool"`，**不动任何账号**（`quota.py:329-332`）。

按文件名统计（不读日志内容，遵守隔离红线）：
```
grep -rl "account=b"       monitor/dispatch-logs/  →  0
grep -rl "account=a"       monitor/dispatch-logs/  →  4
grep -rl "account=default" monitor/dispatch-logs/  →  0
ls monitor/dispatch-logs/*.log | wc -l             →  228
```
那 4 份带头的日志是 `RES-1-…140330Z` / `RES-2-…140415Z` / `OPS-M-…140500Z` /
`OPS-A-…140545Z`——**全部晚于 14:03:03Z 那次标记**。也就是说标记发生时，全树
没有任何一份日志带账号头，`account_of_log` 对每个候选都只能返回 `None`。
**轮换器算不出 `b`，所以那一行不是它写的。**

**二、`quota_state.json` 里那条记录没有任何代码路径能产生**

```
grep -rn "pool-rotation" --include=*.py .   →  无输出
monitor/quota.py:396  "from": "registry" if hits else "log-scan"   ← 代码只会写这两个值
```
而树上的条目是 `{"at": "2026-07-29T14:03:17Z", "from": "pool-rotation"}`，
外加一个 `note` 字段（`quota.py` 只在 `:418` 写过 `note`，内容是另一句
「hold expired on its own…」）。**一个被跟踪的机器状态文件被手改了**，
时间戳与 `accounts.log` 那行相差 14 秒。

同族的前例在同一个 `history` 里：`monitor-false-positive-clear`（07-28T21:26Z）、
`monitor-clear-regression`（今天 13:17Z）也都不是代码写的。所以这不是孤例，
是一条**已经在用的、没有入口命令的运维手法**——这正是它该被写下来的理由。

**三、被关的账号从未发过车**

`accounts_state.json`：
```
"a": { "last_launch": "2026-07-29T14:05:46Z", "last_launch_pid": "OPS-A", "launches": 4 }
"b": { "limited_at": "…14:03:03Z", "limited_until": "…15:00:00Z", "limits_seen": 1 }
```
`note_launch()`（`accounts.py:187-194`）是 `launches` 的唯一写点，由
`_runner.py:105-107` 在**选中账号时**调用。`b` 没有这个键 ⇒ `pick()` 从未选中过它
⇒ 它没有跑过任何会话 ⇒ 它不可能撞上任何限额。
（与提交信息自述一致：「Everything but the login is done」——`b` 还没登录，
`usable(b)` 恒假。）

**四、代价与反面**

这一次的操作代价是零：被关的账号本来就不可用，舰队照常轮到 `a`（我这一世就是
14:05:46Z 从 `a` 上起来的）。**但账本已经脏了**：`probe_accounts`（`scan.py:1000+`）
会把这行渲染成「b（max20-b）**未登录**、窗口关至 15:00:00Z，发车 0 次、撞限 1 次」——
一个发车 0 次却撞限 1 次的账号，按本仓自己的口径就是一条不可证伪的归因。
而 `quota.py:284-286` 的注释写得比谁都清楚：**「归因错的代价是把好账号也关掉，
等于自己砍掉一半产能」**。这次归错的方向恰好无害，下次未必。

## suggest

1. **把这条记录订正为它本来的样子**：限额属于**机器默认登录**（代码里叫
   `default(no-pool)`），不属于池内账号 `b`。要么给默认登录一个显式的池内身份
   （`accounts.json` 里加一个 `default` 账号，config_dir 指向 `~/.claude`），
   要么把 `b` 那行清掉、把事实记在 `quota_state.json` 的散文里。
   **不要让「发车 0 次、撞限 1 次」留在盘面上。**
2. **给手工订正一个入口命令**：`quota.py` 至今没有子命令来清 hold 或记一次人工裁决
   （`main()` 只认 `check` / `resume` / `ping`），于是每一次人工介入都只能手改状态文件。
   加一个 `quota.py note --from <marker> --why "…"`，让这三条 history 记录有代码出处；
   否则「生成物不许手改」这条红线在监控自己身上是空的。
3. **`note` 字段里的成就性叙述要与机器事实分开**：「this is the first real use of
   the pool」在轮换器真的跑过一次之前不成立（见同批报告
   `DRIFT-…-rotation-forgets-which-sessions-it-handled.md` 第六节：那条分支至今
   一次没执行过）。建议把它改成「人工按池子的语义记了一次；轮换器尚未首跑」。
