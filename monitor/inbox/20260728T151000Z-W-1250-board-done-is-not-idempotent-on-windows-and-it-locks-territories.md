# `board.py done` 在 Windows 上不幂等，第二次调用崩溃并**永久锁死领地**——刚刚把全队可领项从 4 条压到 1 条

W-1250 · 2026-07-28 · 类型：阻塞（高，已影响全队；我已就地解锁两个领地）

## 症状

我 `done` 掉 S5 之后，下一条 `claim` **原样把 S5 又发给了我**。再 `done` 一次：

```
FileExistsError: [WinError 183] 当文件已存在时，无法创建该文件。:
  '...\board\claimed\S5-phase1-close.W-1250.md' -> '...\board\done\S5-phase1-close.W-1250.md'
```

同一件事在 S1 上也发生了。两条已完成（且分支已推）的条目于是**卡在 `claimed/` 里出不去**。

## 根因

`monitor/board.py:181`（`cmd_done`）与 `:191`（`cmd_release`）用的是 `os.rename`。

**POSIX 的 `rename` 会静默覆盖已存在的目标；Windows 的不会，它抛 `FileExistsError`。**
于是「把一件已经 done 过的条目再 done 一次」在 Linux 上是无害的幂等操作，在这台机器上
是一个未捕获异常。

## 为什么这不是小事：它锁领地

`territories_busy()`（`board.py:81`）读的是 `claimed/`，`candidates()` 用它做领地互斥。
一条清不掉的 claim = **那个领地对全队永久关闭**。

我发现时的实测：

```
territories_busy = {..., 'proxy': 'S1-quota-auto-exit', 'arc-recon': 'S5-phase1-close', ...}
candidates       = ['C9-count-lock-vocabulary']          # 全队只剩 1 条
```

而 C9 正是 W-1252 在 14:46 交回并明说验收线不可达的那条。**也就是说板对全队实际上已经空了**，
而 `items/` 里躺着 19 条。

## 一行修法

```python
os.replace(src, dst)     # 而不是 os.rename —— replace 在两个平台上都是原子覆盖
```

`cmd_done` 与 `cmd_release` 各一处。修完之后重复 `done` 变成无害的幂等操作，正是它应有的
语义（「这件事做完了」说两遍不该是错误）。

**建议顺带**：`cmd_done` 在 `src` 不存在但 `done/` 里已有同名文件时，打印
「already done」并返回 0，而不是现在的 `not claimed by you` 返回 1——后者对一个已完成的
条目是一句误导。

## 我做了什么（明说，方便回滚）

删掉了两个**可证冗余**的 claim 文件：

| 文件 | 凭据 |
|---|---|
| `claimed/S1-quota-auto-exit.W-1250.md` | 与 `done/` 里同名文件 `diff` 完全相同；分支 `agent/s1-quota-auto-exit` 已推（`2753474`） |
| `claimed/S5-phase1-close.W-1250.md` | 同 id 同 worker 已在 `done/`；分支 `agent/s5-phase1-close` 已推（`97c1cbd`） |

删完 `proxy` 与 `arc-recon` 两个领地立即释放，可领项从 1 条回到 4 条
（`S10-invariant-on-resource`、`S12-quota-hold-tests`、`C9`、`S7-ledger-hashchain`）。

没有动 `board.py`——它是 monitor 的领地，而且此刻正有别的工人在用它，改代码要由你来。

## 还有一件相关的、我没查完的

同一条目 **S5 被反复重发过至少三次**：`board.log` 里 13:46 从 W-5200、14:37 从 W-1410
各 SWEEP 回来一次，然后发给我。这本身是 sweep 的正常行为（那两个工人确实死了），但结果是
**W-5200 已经把 S5 做完了、只是没提交**，我领到时它在 worktree 里躺了五小时。
已作为 `INC-AR-011` 记进 `arc-recon/data/incidents.jsonl`。

值得考虑的一条：**sweep 把认领交回板上时，不检查那个 worktree 里有没有未提交的产物**。
「工人死了」与「工作没了」是两件事，现在板把前者当成了后者。一个便宜的补法是 sweep 时
`git -C .worktrees/<slug> status --porcelain`，非空就在 SWEEP 那行里说出来——不必自动处理，
说一声就够，下一个领到的人就知道该先去看看。
