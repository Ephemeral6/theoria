# -*- coding: utf-8 -*-
"""Append the 2026-08-04 reconciliation section to each board item that moved.

Run once, from the repo root. Idempotent: refuses to append twice.
"""
import io
import os
import sys

MARK = "## 对账 2026-08-04（监控·board hygiene）"

APPENDS = {
"A29-theoria-arm-suite-red.md": """
## 对账 2026-08-04（监控·board hygiene）· 仍红，且两个数都往坏的方向动了

在 master `4846e66d` 的干净 worktree 里逐条复跑本件点名的两个测试：

```
FAILED tests/test_arm.py::test_the_archive_stays_accountable
FAILED tests/test_desk_gate.py::test_the_ceiling_table_still_covers_the_archive
E   AssertionError: claude-opus-5: ceiling $15.00 is below $18.7391, which is
E   what this table's own stated rule -- max(timeout x rate, 4x worst call) --
E   produces from the archive.
```

**本件正文里的那对数已经过期。** 写下时是「天花板 $12.00 低于归档隐含
$13.4480」；今天是 **$15.00 对 $18.7391**。两端都动了：天花板被抬过一次
（`harness/spend.py` 的注释记着 $5→$6→$7 的历史，现为 $15），而归档隐含值
被 R2b 的 g50t 腿（$18.736008，见 A30/A32 的表）推高。**记账追赶落地事实的
速度，慢于落地事实本身。** 这不改本件的判断，只把它加重：本件挂 p1 至今未被
认领，期间这个领地的任何 verify-gate 都过不了 tests 行，且缺口从 $1.45 扩到
$3.74。修的时候请按今天的数写，不要按正文那对。

（本节由 board hygiene 复算，零花费，未改臂的任何文件。）
""",

"A30-the-arm-spends-its-actions-on-probes-not-on-the-level.md": """
## 对账 2026-08-04（监控·board hygiene）· 测量交付了，三条验收一条都没落地——本件不关

2026-08-02 的 A25 交付（`theoria-arm/runs/20260802T131013Z-A25-action-economy/`，
合入 master 于 `83f2d8d0`，5 个源文件 + 494 行测试）**是本件的答案的一半**，
而且比本件问得更深：它把「每 4 个动作叫一次桌面」这个常数与实际比值分开，
量出 73 次判决 / 104 次计费调用 / 226 个计费动作 / $148.89，实际是
**每次判决 3.096 个动作、每次计费调用 2.173 个**。

**但本件写下的三条验收，master 上一条都没有：**

```
$ grep -n "probe_share\\|reserve_for_probes" theoria-arm/armtools/round.py
（无输出）
$ grep -c "46 条基线臂 run" monitor/spec.py     -> 1   （#14 原句未订正）
```

1. `round.json` 的 `legs[*]` **没有** `probe_share` 一列——那五条腿的 24/29
   仍旧只能由读者手算。
2. `reserve_for_probes` 仍是恒 0 的输出，不是被声明的输入。落地的是
   `harness/run.py:668` 的 `--action-economy`（`inner/economy.py` 的策略枚举），
   它是**判决节奏**的旋钮，不是**探针预算**的旋钮——两者不是同一件事，
   本件第 2 条不因它满足。
3. `spec.py:525` 的「15 条腿平均 15.3 个动作」与「46 条基线臂 run」**原字未动**。
   本件重算的 22 条腿 / 均值 11.32、以及 A33 重算的 43 条 run，至今没有一个
   进了登记簿。

**本件保持 open，范围收窄为这三条验收**（正文的测量部分已由 A25 的交付满足，
不必重做）。第 3 条与 A33 第 1 条、A34 验收的后半是同一句话的三处引用——
谁先动谁写，另外两处引它，不要并存两个版本。
""",

"A31-the-win-detector-has-never-fired-and-the-round-total-turns-absence-into-zero.md": """
## 对账 2026-08-04（监控·board hygiene）· 第二证人来了，`or 0` 还在——本件的核心一条未动

2026-08-02 的 A27 交付（`theoria-arm/inner/scoreboard.py` 718 行 + 659 行测试，
`runs/20260802T2100Z-A27-level-boundary-detector/`，合入 master 于 `3a1ee035`）
**推翻了本件的一条前提并交付了本件没要的一件好东西**：

* **前提修正。** 臂并非「看不见边界」——每一次 `_record` 都把信封的
  `levels_completed` 推进 `LevelLog.observe`（`inner/loop.py:443`），
  `state == "WIN"` 每回合检查。真正的盲点是**记分卡**：`score` /
  `level_scores` / `level_actions` / `level_baseline_actions` 不在任何对局
  响应上，全臂唯一一次取记分卡是 `_finish` 里的 `close_scorecard`，
  所以一条腿从来握不住自己的分母。
* **多出来的东西。** `ScoreWatch` 是第二个证人，`boundary_verdict()` 把
  `not_measured`（null）与 `measured_absent`（false）分开，十条负样本逐条列在
  `RUN_STATE.md`，其中一条正是本件第 3 条要的：记分卡说通了关而 `LevelLog`
  没说时，`corroborate` 报 `disagree` 而不是二选一。

**本件的核心一条没有动**，逐字复算：

```
$ grep -n "levels_completed" theoria-arm/armtools/round.py
104:        "levels_completed": levels.get("levels_completed"),
188:  "levels_completed": sum((l.get("levels_completed") or 0) for l in legs),
```

`round.py:188` 的 `or 0` 原样在树上。`theoria-arm/runs/*/levels.jsonl`
**22 个文件，非零字节 0 个**（本件复算，与正文逐目录点的结果一致）。所以
「缺席读成零」这件事今天仍然成立，A34 的负样本（造一条真通了关但
`levels.jsonl` 被截断的腿）今天仍然会红。

**本件保持 open，范围收窄为**：`round.py` 的 `totals` 在任一条腿缺 `levels_completed`
时落 `null` + `legs_missing_levels_completed` 计数；以及正文第 2 条的离线
mock 通关——`ScoreWatch` 的合成正样本证明**记分卡侧**能发信号，
`LevelLog` 侧仍未被任何一次执行走通。正文第 1、3 条与两条负样本原样保留。
另见新开的 A35：这条记录路径除了没发过，还只在腿末尾写一次。
""",

"A32-the-sk48-leg-pays-more-per-desk-call-and-moves-less.md": """
## 对账 2026-08-04（监控·board hygiene）· 两个候选都被判死了，第三个才是对的；两列仍未落地

2026-08-02 的交付（`theoria-arm/armtools/desk_yield.py` + `prompt_census.json`，
`runs/20260802T2100Z-R2b-DESK-YIELD/`，合入 master 于 `366174bc`）
**回答了本件「判到一个」的要求，而答案是「两个都不是」**：

| | g50t-a | sk48-b |
|---|---|---|
| 最大发出提示 | 128,759 字符 | **85,904 字符** |
| 最后一次写入时的手册 | 72,299 字符 | **32,522 字符** |

**sk48 发的提示更小，付的钱更多**——「提示更长」这个候选被反向证伪，
而不是被排除。leg 内部，提示长度对账单的解释力 `r² = 7.6e-6`（六次调用）。
真正的去处是**输出侧**：最小二乘从各腿自己的账单反解出费率
（g50t cache_write $10.65/Mtok、output $25.07/Mtok；sk48 $11.11 / $24.59，
最坏残差 $0.0045 / $0.0124），**输出 token 承担两条腿各 69% 的账单**；
耗时是输出 token 的线性函数（15 次调用相关 0.996，中位 86 tok/s），
那次 22 分钟的调用是 109,763 个输出 token，不是挂起也不是网络。

所以本件正文里的两个候选（提示更长 / 重试更多）**都不是主因**，第三个是：
sk48 的桌面在写长回复，而臂把这些回复扔了——它的钱花在桌面里，不在世界上。
这与裁决书那句散文一致，但现在有出处。

**未落地的是本件验收的后半**：

```
$ grep -n "usd_per_desk_call\\|usd_per_action" theoria-arm/armtools/round.py
（无输出）
```

`round.json` 的 `legs[*]` 仍然没有 `usd_per_desk_call` 与 `usd_per_action`
两列，本件那条负样本（`desk_calls = 0` 的腿必须读 `null` 不读 `0.0`）因此
也还没有被任何测试钉住。**本件保持 open，范围收窄为这两列与那条负样本**；
诊断部分已交付，不必重做，引 `runs/20260802T2100Z-R2b-DESK-YIELD/` 即可。
""",

"A33-forty-six-baseline-runs-scored-zero-is-wrong-three-times-over.md": """
## 对账 2026-08-04（监控·board hygiene）· 核对器落地了，被它订正的那句话没有

2026-08-02 的交付（`baseline-arms/harness/audit_zero.py` 241 行 +
`tests/test_audit_zero.py` 151 行 + `runs/.../audit_zero.json`，合入 master 于
`b27dd1e2`）**满足了本件验收的前半**，并且比正文多查了一层：分数不是没被读，
是**基线臂从不把权威分数写进自己的归档**——63 次观测（57 个 run_id）的记分卡
体全部 `score: 0.0`、`level_scores` 全零，所以零是真的；但
**43 份 `runs/bare_cc-*/run.json` 里 0 份持有那个分数**，下游读到的一直是
`levels_completed`。今天两者恰好都是零，这是巧合不是设计。交付把它记为 gap
而非 incident，理由是没有一个已发表的数是错的——这个界线划得对。

**未落地的是验收的后半**：

```
$ grep -c "46 条基线臂 run" monitor/spec.py     -> 1
```

`spec.py:525` 登记 #14 的原句一字未动，仍写着「46 条基线臂 run（裸 CC 三档
模型）最高分 0、通关 0」——本件正文逐条证伪的那句话。同一处还挂着 A30 证伪的
「15 条腿平均 15.3 个动作」。**本件保持 open，范围收窄为这一句的订正**
（正文「欠的是什么」第 1 条），以及第 2 条（给基线臂加 `score` 列或明写不可得
——`audit_zero.py` 已能恢复它，但 `run.json` 仍不持有它）。第 3 条那条 $8.95
的实验按 A34 的次序排在第 2 步，不由本件执行。

**认领冲突提醒**：本件在主树里已被 W-9207 认领（`monitor/board/claimed/`，
2026-08-04 未提交）。本节只对账不动状态；若 W-9207 正在做的就是上面这两条，
交付时把本节一并关掉即可。
""",

"V31-class-ii-cannot-be-built-and-the-request-to-build-it-was-never-boarded.md": """
## 对账 2026-08-04（监控·board hygiene）· 引的那段算术已经过时，缺的那张票还是没开

2026-08-02 的 V29 交付（`exam/state_space.py` 779 行 + `tests/test_state_space.py`
111 个测试，`exam/runs/20260802T0000Z-V29-class-ii-state-census/`，合入 master 于
`ceedfaf0`）**把本件引用的那句话变成了假的**。本件逐字引了
`exam/DECISIONS.md:1053`：

> The bound is arithmetic and **no class (ii) board has ever had its states
> counted**

现在数过了，而且是精确值：

| item | 状态空间 | 方法 |
|---|---|---|
| ii1 `vq-721d09813c` | **1.595e38** | 符号（BDD），精确 |
| ii2 `vq-6150a6eeb7` | 1.595e38 | 符号，精确 |
| ii4 `vq-2986ed8ffc` | 8.862e35 | 符号，精确 |
| ii3 `vq-ee54166153` | 1.661e37 .. 4.133e63 | 双侧包夹 |

四件全部存活，类不空；每个数都高出构造性下界 2^m（120 倍 / 120 倍 / 8÷3 倍），
ii3 连包夹的**下**侧都比此前发表的 2^60 高 19 个数量级。载重测试是：在穷举
跑得完的每个尺寸（k=2..6）上，普查与朴素穷举**必须逐位相等**。

**这改变了本件的论证，不改变本件的结论。** 本件的要害从来不是「没数过」，
是 `DRILL.json` 的 `classes_absent: ["large_unsolvable"]` 一个键背着两种意思，
而 `MAX_ENUMERATION` 不是旋钮。数出 1.595e38 只是把「naive 方法跑不动」从
推断变成了测量——**它恰好是本件那条负样本要钉的东西**（把上限抬到 10^7
再跑，`classes_absent` 必须仍含 `large_unsolvable`），现在有了精确的靶子。

**验收三条，一条都没落地**，逐条复算于 master `4846e66d`：
`DRILL.json` 的 `classes_absent` 未拆成 `absent_structural` / `absent_incidental`；
`exam/DECISIONS.md:1040` 那一节没有回指票号；**`monitor/board/items/` 里仍然
没有任何一件 worldgen 领地的票**。第三条是本件的第一交付物，也是本件的全部
意义所在——一个专门指出「说了 filed 其实没进盘」的记录，自己已经在盘上等了
四天而它要开的那张票还没开。

顺带一条给下一个认领人的证据：那封该被引用的请求就在
`monitor/inbox/20260730T0300Z-RES-3-worldgen-cannot-host-a-large-space-world.md`，
而按 `monitor/inbox_recon.py` 的对账，它属于 225 件**文件名里没有收件人**的
ask（新开的 S52 量了这件事）——所以 worldgen 从来没有任何机制会看见它。
开票时请一并在票里引它，不要再写一次 filed。

**本件保持 open，正文的算术段落按上表更新**（5e6 可承受 vs 1.33e36 的对比
应改为 vs 已数出的 1.595e38；473 B/state 与 N^1.49 两条未被本次交付触及，
仍然有效）。
""",
}


def main() -> int:
    root = os.path.abspath(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__))))
    base = os.path.join(root, "monitor", "board", "items")
    for name, text in APPENDS.items():
        path = os.path.join(base, name)
        if not os.path.exists(path):
            print("MISSING %s" % name)
            return 1
        with io.open(path, "r", encoding="utf-8") as fh:
            body = fh.read()
        if MARK in body:
            print("already reconciled, skipped: %s" % name)
            continue
        if not body.endswith("\n"):
            body += "\n"
        with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body + "\n---\n" + text)
        print("appended: %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
