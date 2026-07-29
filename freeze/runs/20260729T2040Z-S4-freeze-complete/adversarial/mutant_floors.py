#!/usr/bin/env python3
"""⟨n⟩ 买不到的东西 —— 每格重复数与基础设施死亡率的算术。

`STATS_RULES.md` §5.5 裁定 ⟨n⟩ = 2，四条理由。其中**理由三**是：
47/48 的基础设施死亡率下 n=1 不可存活，所以要 n=2「让一格不至于因为一个
episode 死掉就整格作废」。

**把那个死亡率乘起来，理由三就不成立了**——不是方向错，是量级错。
每 episode 独立死亡概率 q = 47/48 = 0.979 时，一格 n 个 rep 全死的概率是 qⁿ：

    n=1 → 每格存活 2.1%，19 格里预期活 0.40 格
    n=2 → 每格存活 4.1%，19 格里预期活 0.78 格

n=2 与 n=1 一样是死的。要让预期活格数够到 C1 预注册地板 14/19，
在 q=0.979 下需要 **n ≈ 63**——`freeze/BUDGET_TABLE.md` 的天花板下买不到。
反过来解才是有用的那一半：**n=2 要够到 14/19，先得把 q 压到 0.513 以下。**

所以本文件的结论不是「改 ⟨n⟩」，而是：**⟨n⟩ 不是买存活率的工具，
基础设施死亡率才是**，而它是一条开跑前置条件（`launch_blockers.json` §9.11
包络重跑）。⟨n⟩ = 2 的裁定不变——它靠的是 §5.5 理由一与理由四
（三个主终点的方差从未被测到；「否则」涵盖未知）——但**理由三从今起只能被引作
「n=1 不可辩护」，不能被引作「n=2 买到了存活」**。后者是假的，而它读起来很像真的。

两处分寸，都必须跟着数字一起被引用：

1. **q = 0.979 不是关于世界的陈述。** §5.2 已查明这 48 集全部测于一次自己造成的
   双战役争用期间（INC-BA-003），所以它是**争用条件下**的死亡率，多半是上界。
   本文的结论是条件式的：*若 q 停在唯一被测过的那个量级附近，任何买得起的 n
   都到不了地板*。这句话的力量来自它可被推翻——重测出一个小 q 就推翻了它，
   而那恰好是我们想要的结果。
2. **独立性是对 n 最有利的假设。** `api_unusable` 在 episode 之间是正相关的
   （API 不可用时同格的 rep 一起死），正相关只会让 qⁿ 比独立情形更大，
   即 n 买到的更少。所以下表是 n 的**上界表现**，不是估计。

用法：

    python freeze/n_feasibility.py             # 打印表与结论
    python freeze/n_feasibility.py --verify    # 闸门：数字漂了就 exit 1
    python freeze/n_feasibility.py --json      # 机器可读（确定性）
"""

import argparse
import json
import math
import sys

#: 测量值，来自 `STATS_RULES.md` §5.2 发现三（`baseline-arms` 包络，48 episode）。
#: 改这三个数就是在改一个**测量结果**，必须同时改 §5.2 并说明来历。
DEATHS = 47
EPISODES = 48

#: 预注册地板，来自 `STATS_RULES.md` §1.2 / `CLAIMS_TEXT.md` C1。
#: 分母是 claim 层 19（F-11 隔离 ls20/ft09 之后），不是封存堆 21。
CLAIM_CELLS = 19
CLEAN_CELLS = 12
FLOORS = {
    "claim-14/19": (10, CLAIM_CELLS),
    "claim-hard-10/19": (10, CLAIM_CELLS),
    "clean-10/12": (10, CLEAN_CELLS),
    "clean-hard-7/12": (7, CLEAN_CELLS),
}

#: 裁定值（§5.5）。本文件不改它，只说明它买到与买不到什么。
N_RULED = 2

#: 闸门盯住的四个数。任何一个漂出容差，说明上面的测量值或地板被改过，
#: 而 §5.7 的结论是从它们算出来的，必须一起重做。
EXPECTED = {
    "q": 0.979167,
    "live_cells_at_n1": 0.395833,
    "live_cells_at_n2": 0.783420,
    "n_required_for_claim_floor": 63.44,
    "q_max_for_n2_claim_floor": 0.512989,
}
#: 容差收到 0.2%：这些数是闭式算出来的，不是估计，所以宽容差只会放过打字错误。
#: （第一版写 0.40 / 0.78 就被这一条抓住了——19 × 1/48 = 0.3958，不是 0.40。）
TOL = 0.002


def q_hat():
    return DEATHS / EPISODES


def live_cells(n, q=None, cells=CLAIM_CELLS):
    """一格 n 个 rep 至少活一个的概率 × 格数。独立假设是对 n 最有利的那一侧。"""
    q = q_hat() if q is None else q
    return cells * (1.0 - q ** n)


def n_required(floor_k, cells, q=None):
    """要让预期活格数 ≥ floor_k，需要多大的 n。"""
    q = q_hat() if q is None else q
    need = floor_k / cells
    if need >= 1.0:
        return math.inf
    return math.log(1.0 - need) / math.log(q)


def q_max(floor_k, cells, n=N_RULED):
    """给定 n，q 必须压到多少以下才够到地板。这是可执行的那一半。"""
    need = floor_k / cells
    return (1.0 - need) ** (1.0 / n)


def compute():
    q = q_hat()
    rows = [{"n": n,
             "cell_survival": round(1.0 - q ** n, 6),
             "live_of_19": round(live_cells(n), 4),
             "live_of_12": round(live_cells(n, cells=CLEAN_CELLS), 4)}
            for n in (1, 2, 3, 5, 10, 20, 64)]
    floors = []
    for name, (k, cells) in sorted(FLOORS.items()):
        floors.append({
            "floor": name,
            "k": k, "cells": cells,
            "n_required_at_measured_q": round(n_required(k, cells), 2),
            "q_max_at_n2": round(q_max(k, cells, 2), 4),
            "q_max_at_n3": round(q_max(k, cells, 3), 4),
        })
    return {
        "measured": {"deaths": DEATHS, "episodes": EPISODES, "q": round(q, 6),
                     "condition": "INC-BA-003 争用期间；多半是上界，不是世界属性"},
        "n_ruled": N_RULED,
        "rows": rows,
        "floors": floors,
        "verdict": (
            "⟨n⟩ = 2 不变（§5.5 理由一、理由四），但理由三只能支撑「n=1 不可辩护」，"
            "不能支撑「n=2 买到了存活」：q=0.979 下 n=2 预期活 0.78/19 格。"
            "买存活的是把 q 压下来，那是 launch_blockers.json §9.11。"),
    }


def verify():
    q = q_hat()
    got = {
        "q": q,
        "live_cells_at_n1": live_cells(1),
        "live_cells_at_n2": live_cells(2),
        "n_required_for_claim_floor": n_required(14, CLAIM_CELLS),
        "q_max_for_n2_claim_floor": q_max(14, CLAIM_CELLS, 2),
    }
    fails = []
    for key, want in sorted(EXPECTED.items()):
        have = got[key]
        rel = abs(have - want) / max(abs(want), 1e-9)
        if rel > TOL:
            fails.append(f"{key}: 算得 {have:.4f}，§5.7 写的是 {want:.4f}"
                         f"（相对差 {rel:.1%} > {TOL:.1%}）")
    # 结构性检查：裁定值 n=2 在测得的 q 下必须**够不到**任何地板。
    # 这一条是本文件的论点本身；它若不再成立（因为 q 被重测小了），
    # §5.7 必须重写，所以让它红。
    if live_cells(N_RULED) >= 14:
        fails.append(f"n={N_RULED} 在 q={q:.4f} 下已能达到 14/19 —— "
                     "§5.7 的论点前提变了，重写它")
    return fails, got


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    data = compute()
    fails, _ = verify()

    if args.json:
        json.dump({"data": data, "failures": fails}, sys.stdout,
                  ensure_ascii=False, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 1 if (args.verify and fails) else 0

    m = data["measured"]
    print(f"基础设施死亡率 q = {m['deaths']}/{m['episodes']} = {m['q']:.4f}"
          f"  （{m['condition']}）")
    print(f"裁定 ⟨n⟩ = {data['n_ruled']}\n")
    print(f"{'n':>4}  {'每格存活':>10}  {'19 格预期活':>12}  {'12 格预期活':>12}")
    for r in data["rows"]:
        print(f"{r['n']:>4}  {r['cell_survival']:>10.4f}  "
              f"{r['live_of_19']:>12.2f}  {r['live_of_12']:>12.2f}")
    print()
    print(f"{'地板':>18}  {'q=0.979 下需 n':>14}  {'n=2 需 q≤':>10}  {'n=3 需 q≤':>10}")
    for f in data["floors"]:
        print(f"{f['floor']:>18}  {f['n_required_at_measured_q']:>14.1f}  "
              f"{f['q_max_at_n2']:>10.4f}  {f['q_max_at_n3']:>10.4f}")
    print(f"\n{data['verdict']}")
    if fails:
        print("\n不合项：")
        for f in fails:
            print(f"  ✗ {f}")
        return 1 if args.verify else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
