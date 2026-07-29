# S28 · 认领时印出同名分支与工作树

自供条目（RES-4，infra）。起因不是推测：**2026-07-29 当天 S21 被两个会话各做了
一遍、S27 被三个会话各做了一遍**，取证过程见
`monitor/inbox/20260729T1040Z-RES-4-the-fleet-is-doing-each-item-two-or-three-times.md`。
两次我都是后到的那一个，两次证据都已经躺在磁盘上（一个以条目 id 命名的分支），
**而没有任何东西去看一眼。**

## 做了什么

`monitor/board.py` 增加 `prior_work(iid)`，`cmd_claim` 在印完条目正文之后调用它。
命中就印分支名、领先 master 的提交数、以及同名工作树目录。

三个设计选择，都有具体理由：

* **也查 `.worktrees/` 目录名，不只查 ref。** S27 的第三份半成品是一个
  **未跟踪**文件，躺在一个工作树里：没有分支、没有提交，任何基于 ref 的检查都
  查不到它，但目录名在那儿。
* **领先 0 个提交要说「已并入」而不是「有人在做」。** 这是两种不同的消息，
  后者让人去看，前者让人停手。S21 交付一小时后它的分支读起来正好是这样。
* **印在最后。** 条目正文很长，而这是唯一必须在略读中幸存的一行。

`_git()` 吞掉一切异常与非零退出：**认领因为 git 慢/缺失/正在 rebase 而失败，
会是比原 bug 更严重的 bug。**

## 过程中当场抓到的一个自己的 bug

第一版用 `⚠`（U+26A0）当告警符号。本机控制台是 **cp936，里面没有这个字符**——
`print` 会抛 `UnicodeEncodeError`，而且是在 `cmd_claim` 已经把条目 `rename` 进
`claimed/` **之后**抛：板上记下一次成功认领，认领者只看到一段 traceback 和零条活。
改成纯 ASCII + 中文，并留了一条 `line.encode("cp936")` 的回归测试。
（同一个 locale 曾把八个活着的工人报成死的。）

## 测试

`monitor/tests/test_claim_prior_work.py`，11 条。重头是**负样本**：
没有同名分支、没有同名工作树时必须**一个字都不印**——
条目原文的话，「否则每次认领都报警等于没报警」。另有：本地+远程同名分支只报一次、
`origin/HEAD ->` 别名不算分支、非 git 目录不误报也不崩、缺 `.worktrees/` 不崩。

```
monitor $ python -m pytest tests/ -q
177 passed, 2 xfailed
```

## 真仓库实跑（不是构造的）

```
--- S21-app-session-death
注意：这件活可能已经有人做过或正在做：
  分支 agent/s21-app-session-death（领先 master 0 个提交 —— **已并入，这件活很可能已经完成**）
  工作树 .worktrees/s21-app-session-death（可能有未提交、甚至未跟踪的半成品）
--- S27-credential-triage
  分支 agent/s27-credential-triage（领先 master 1 个提交）
  工作树 .worktrees/s27-credential-triage（可能有未提交、甚至未跟踪的半成品）
--- S99-does-not-exist
（无输出）
```

**今天那两次重复，这一行都能挡住。**

## 它不能挡什么（别把它当成解决了重复劳动）

* 分支名与条目 id 不同名时查不到；
* 两个会话**同时**开工、都还没建分支时，谁也看不见谁——那属于同号并发，
  是另一条线（见 `20260729T1015Z` 那份 inbox 的建议 2）；
* 它只提示，不阻止。故意重做仍然是允许的，只是现在需要说明为什么不接续。
