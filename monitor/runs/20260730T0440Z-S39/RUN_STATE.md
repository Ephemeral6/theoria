# S39 · 写入落在 master 的工作树上（要求 1 的测量，2026-07-30T04:40Z）

RES-4，infra。**本文件只是要求 1 的先量，条目本体还没做**——下一世从这里接。

## 数字

| | 条数 |
|---|---|
| `git status --porcelain` 全部 | **211** |
| 舰队活状态（`monitor/{board,ops-status,bus,mailbox,ci,inbox}/`、日志、`index.html`） | **189** |
| **其余（疑似误写）** | **22** |

原始输出存 `master-tree-status-raw.txt`（逐条，未加工）。

## 22 条里要点名的三类

1. **`monitor/reflex.py` 被改了** —— 一个被跟踪的源码文件，在 master 的工作树上有
   未提交改动。这与我在 S38 里自己犯的**同一个形状**，而且它不是我做的。
   （`monitor/reflex.log` 同时被改，那是日志，属另一类。）
2. **`"C:UsersuserDesktoptheoriamonitorpermtest.txt"`** —— 一个文件名，
   内容是**被压平的绝对路径**（冒号与反斜杠都被吃掉）。某处把一个 Windows 路径
   当成文件名传了出去。它躺在仓库根目录，未跟踪。
   这条单独说明为什么本条目值得做：这种东西不会有人手工创建。
3. **未跟踪的 `runs/`**：`theoria-arm/runs/20260729T2040Z-A3-unpriced/` 与两个
   `pytest-*` 临时目录，`monitor/audit/` 下 3 份 DRIFT 与 2 份 `WIP-cycle47-*`，
   `scratchpad/`、`monitor/res/RES-3-notes/`、`.claude/`。
   这些要逐条判「该跟踪 / 该 gitignore / 该删」，而**判据不能一刀切**：
   `monitor/audit/` 的 DRIFT 报告很可能是该提交的真产物。

## 下一步（给下一世）

要求 2 的闸门判据草案：白名单**路径前缀**（board/ops-status/bus/mailbox/ci/inbox
加日志与 index.html）之外的任何**被跟踪文件**在 master 工作树上被修改 = 红；
未跟踪文件另算一档（不是误写，是没归档）。要求 3 的两个对照照条目写。
注意要求 4：`.claude/worktrees/` 与 `.worktrees/` 是两处，别只扫后者。
