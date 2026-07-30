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

---

## AMENDMENT 2026-07-30T04:13Z（周期 48，对抗复核回来了，**suggest 1 必须撤销**）

我在周期 47 就着这条记录的身份问题另立了
`DRIFT-20260730T0351Z-the-fallback-login-is-the-pool-account-the-pool-thinks-is-exhausted.md`，
并在那里说本文件 suggest 1 的方向是反的。**那份报告本轮被对抗复核了，结果比我原来的判断更硬：
本文件 suggest 1 不只是方向反了，它的两条备选补救措施照做下去都会造成实害。**
逐行裁决如下（哪几行错、哪几行仍然对，分开说，因为上一次我差点整条推翻）。

### 仍然成立的，不要动

* **`:13-14` 前半句「这条记录断言了一个树上无法佐证的身份等式」——仍然为真，予以确认。**
  证明那个等式需要 `~/.claude.json` 与 `~/.claude-accounts/{a,b}/.claude.json`，全在仓库之外；
  `monitor/accounts.json` 只有 `label`／`config_dir`／`note`。**我的证明本身是树外构造的**，
  所以它并不反驳这句话。（我上一轮的草稿差点「订正」这一行，那会是订正到一句真话上。）
* **`:74` 的观察成立，标签不成立。** 「发车 0 次却撞限 1 次」这个异常是真的，现在仍然是真的；
  错的是「不可证伪」这个认识论标签——它可被检验，而且已经被检验了。**留观察，删标签。**
* **`:75-76` 引用 `quota.py:284-286` 那句「归因错的代价是砍掉一半产能」——仍然是本文件最好的一句。**

### 错的一行

* **`:80-81`「限额属于机器默认登录，**不属于**池内账号 `b`」——假。**
  那是一个假二分：默认登录与 `b` 是**同一个订阅**（`oauthAccount` 的 7 个身份字段
  default~b 全同、default~a 全异、a~b 全异；符号链接／硬链接／字节复制／同源播种四种混淆
  已被逐一排除，且 a~b 本身是「同源但身份不同」的内部对照）。
  所以那次撞限**实质上确实是 b 的**，只是 `note_launch` 从未把回落的发车记到它头上。

### 两条备选补救措施，都会造成实害——**这是本次修订最要紧的一段**

* **`:81-83`「给默认登录一个显式池内身份（`accounts.json` 加一行 `default`，config_dir 指向 `~/.claude`）」
  ——会把熔断器整个关掉。** 链条是纯静态可判的：`quota.py:298` 仍然把
  `default(no-pool)` 这个日志头丢掉 → `mark_limited("default")` 永不执行 →
  `window_state("default")` 永远是 `open` → `:336` 的 `others` 永不为空 →
  `:337` 永远返回 `"rotated"` → `check():383-386` 因此返回 0，
  **`:390` 的全局 hold 再也不会被置上**。
  **实测后果**：两次**合法**的 hold（16:32:10Z 与 2026-07-30T01:17:09Z，
  两次都是两个账号同时关闭时的正确停机）会变成假的 `"rotated"` 判决，
  **朝两个都已耗尽的订阅发车**。原文还担心这样会把 `b` 重复入池——
  比重复入池严重得多的是这一条。
* **`:83`「或者把 `b` 那行清掉」——同样不能做，而且本文件与 0351Z 都没裁决过它。**
  清掉会擦掉一条**归因正确**的记录（见上：那次撞限实质上是 b 的）。
* **`:84`「不要让『发车 0 次、撞限 1 次』留在盘面上」——方向对，补救反了。**
  正确做法是**把回落的发车记到 `b` 头上**（让分子分母对齐），而不是把撞限那一次抹掉。

### 唯一安全的替代补救

在回落发生的地方留一条**具名记录**，让归因从相关性变成直接证据：在
`monitor/_runner.py:183-189` 的 `try` 之内加一行日志。
**注意 0351Z 给的那句一行代码写错了**：它写 `accounts.log(...)`，而该作用域里
`:185` 绑定的名字是 `import accounts as _acct`，`accounts` 从未绑定，
照抄会得到 `NameError`——必须写 `_acct.log("FALLBACK-DEFAULT %s" % pid_str)`，
并且必须在那个 `try` 内，否则池导入失败时这行日志自己就是崩溃点。

### 严重度

本文件的核心发现（**三条 `quota_state.json` history 记录是手写的**，`from` 值
`pool-rotation`／`monitor-false-positive-clear`／`monitor-clear-regression`
都不在 `check()` 能产出的词汇表里）**未被触动，本轮独立复现**，
所以 severity 仍是 medium。被撤销的只有 suggest 1 的两条补救措施与 `:80-81` 那句身份判断。
suggest 2（给手工订正一个入口命令 `quota.py note`）**反而因此更值得做**：
如果连订正都只能手改状态文件，那这三条手写记录还会继续出现。
