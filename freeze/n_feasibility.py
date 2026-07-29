#!/usr/bin/env python3
"""格产出率与 ⟨n⟩ —— 把「每格重复数」和「有多少格真的出数」分开算。

## 这个文件的第一版是错的，错法值得留在开头

第一版（2026-07-29 早，RES-1）拿 `STATS_RULES.md` §5.2 发现三的 **47/48** 当
「基础设施死亡率」，乘出「q=0.979 下 n=2 只活 0.78/19 格、够到地板要 n≈63」，
据此宣布 ⟨n⟩ 买不到存活率。**对抗性复核当天把它推翻了**，两条都可从字节复核：

1. **47/48 不是死亡率，是 harness 自己的中止阈值命中率。** 那 47 集的
   `actions_failed` **恰好都是 10**（`bare_cc.play()` 的累计失败中止阈值），
   而它们每集在 API 上**成功**执行了 9–73 个动作（均值 30.3）；
   唯一那个非 `api_unusable` 的 episode 正是 48 集里唯一 `actions_failed = 8` 的。
   §5.2 发现二早已用这条阈值解释了「方差」，却没有用它解释同一批数据的「死亡率」——
   两者是同一只停表的两个读数。一个 70–81% 动作成功率的 episode 不叫 API 不可用。
2. **树上还有第二份已跟踪的测量，第一版没引。**
   `baseline-arms/runs/20260728T103135Z-a7/envelope.json`（阈值随预算缩放**之后**）
   的 9 格全部 `outcome: budget_exhausted`、`actions_failed: 0`、
   `action_success_rate: 1.0`——`api_unusable` **0/9**。
   把 0/9 的 95% CP 上端（0.3363）代进同一套算术，n=2 的过地板概率是 **0.985**。
   第一版只引悲观那一份，还称它「多半是上界」而不提乐观那一份存在：这不是保守，是选边。

**所以结论翻了个方向**：在树上最新的那份测量下，⟨n⟩ = 2 **够用**。
留着这段是因为错的形状本身有用——它示范了「拿一个 harness 常数当世界属性」
这一类错误，而这正是 §5.2 发现二自己警告过的那一类。

## 现在这个文件算什么

三件事，分开算，不合并：

* **格产出率**：一格 n 个 rep，至少一个**出数**的概率 = 1 − qⁿ，q = 单个 rep
  不出数的概率。⟨n⟩ 只在这里起作用。
* **判据是功效，不是期望。** 「预期活格数 ≥ 14」是**一半多一点**就成立的条件：
  q = 0.5130 时期望正好 14.00，而 P(活格数 ≥ 14) 只有 **0.617**。
  预注册要的是把握，所以本文的门槛按 **P(活格数 ≥ 地板) ≥ 0.80** 解，
  于是 n=2 的要求是 **q ≤ 0.4607**，不是 0.5130。
* **q 必须带出处。** 只接受树上两份已跟踪测量之一（见 `MEASUREMENTS`），
  拒绝任何来历不明的 q——第一版的错就是从一个没有被质疑过的 q 开始的。

## 还没有答案的那一格（本文最要紧的一句）

**「这一格出数了」在树上没有定义。** 一个在第 10 次失败动作上被中止、
但已经成功走了 30 个动作的 episode，很可能**照样给得出** E2 与 U3 的观测
（U3 从产出物裁，不要求通关）。所以 q 到底该数什么事件，取决于三个主终点各自
「一次观测算成立」的定义，而 `battery/` 里三个终点有两个还没有实现
（`launch_blockers.json` §9.14 / `MANIFEST_DRAFT.md` ⛔ 8-a、8-b）。
在那之前，本文能给的是**条件式**结论：给定 q 的定义与取值，n 够不够。
它给不出的是 q 本身。这条缺口登记为 `MANIFEST_DRAFT.md` ⛔ 缺 13-f。

用法：

    python freeze/n_feasibility.py            # 两份测量各算一遍
    python freeze/n_feasibility.py --verify   # 闸门
    python freeze/n_feasibility.py --json     # 机器可读（确定性）
"""

import argparse
import hashlib
import json
import math
import sys

#: 树上两份**已跟踪**的测量。q 只能取自这里，且每一份都带它测的是什么。
#: 键名进闸门的哈希，所以增删一份测量必须是一次显式改动。
MEASUREMENTS = {
    "S1-prefix-abort": {
        "hits": 47, "episodes": 48,
        "what": "累计失败动作触到 harness 阈值 10 而中止（`api_unusable`）的集数",
        "source": "baseline-arms/out/campaign/campaign_{ar25,g50t,sk48,tn36}.json"
                  "（已跟踪于 9307f139）",
        "caveat": "**不是**基础设施死亡率：47/47 的 actions_failed 恰好是 10，"
                  "且每集成功执行 9–73 个动作（均值 30.3）。同批数据测于 "
                  "INC-BA-003 争用期间，且中止阈值当时不随动作预算缩放。",
        "usable_as_q": False,
    },
    "A7-postfix": {
        "hits": 0, "episodes": 9,
        "what": "阈值随预算缩放后，9 格里 `api_unusable` 的格数",
        "source": "baseline-arms/runs/20260728T103135Z-a7/envelope.json",
        "caveat": "9 格全部 `budget_exhausted`、`actions_failed: 0`、"
                  "`action_success_rate: 1.0`。**ar25 的 3 格未重跑**"
                  "（该文件 `excluded` 字段自陈），所以这 9 格是 3 局而非 4 局。",
        "usable_as_q": True,
    },
    "A7-postfix-with-degraded": {
        "hits": 3, "episodes": 12,
        "what": "把 A7 排除掉的 3 格劣化 ar25 格算回来",
        "source": "同上 + `baseline-arms/out/campaign_cells.jsonl`（append-only）",
        "caveat": "悲观读法：把未重跑的 ar25 三格记为不出数。"
                  "**这一份决定裁定**——它的 CP 上端过不了 n=2 的门槛，"
                  "而 A7-postfix 过得了。差别只由 ar25 重跑与否决定。",
        "usable_as_q": True,
    },
}

#: 预注册地板。来源 `STATS_RULES.md` §1.2 / `CLAIMS_TEXT.md` C1。
#: 分母是 claim 层 19（F-11 隔离 ls20/ft09 之后），不是封存堆 21。
CLAIM_CELLS = 19
CLEAN_CELLS = 12
FLOORS = {
    "claim-14/19": (14, CLAIM_CELLS),
    "claim-hard-10/19": (10, CLAIM_CELLS),
    "clean-10/12": (10, CLEAN_CELLS),
    "clean-hard-7/12": (7, CLEAN_CELLS),
}

#: `FLOORS` 的封印。第一版声称「`FLOORS` 与 `EXPECTED` 同文件同闸门，改一处
#: 必然让另一处红」——**那句话是假的**，因为 `verify()` 当时把 14 硬编码了，
#: 于是把地板从 14 改成 10 闸门照样绿，还把 10/19 的门槛印在「14/19」的标签下。
#: 对抗性复核用一个变异体实测出来了（`runs/.../adversarial/mutant_floors.py`）。
#: 现在的做法：地板集的摘要**写死在这里**，且 `verify()` 的每个数都**从 `FLOORS`
#: 推**，不再有第二处 14。改地板 ⇒ 摘要不符 ⇒ 红。
FLOORS_DIGEST = "2c84a913533a3e79"

#: 裁定值（`STATS_RULES.md` §5.5）。本文不改它。
N_RULED = 2
#: 预注册功效门槛：P(出数格数 ≥ 地板) ≥ POWER。
POWER = 0.80


def floors_digest():
    payload = json.dumps({"floors": FLOORS, "power": POWER,
                          "n_ruled": N_RULED}, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def q_of(name):
    m = MEASUREMENTS[name]
    return m["hits"] / m["episodes"]


def _binom_sf(k, cells, p):
    """P(X >= k), X ~ Binom(cells, p)。闭式求和，不依赖 scipy——
    冻结件不该因为一个可选依赖不在就算不出自己的门槛。"""
    total = 0.0
    for i in range(k, cells + 1):
        total += math.comb(cells, i) * p ** i * (1.0 - p) ** (cells - i)
    return min(1.0, max(0.0, total))


def cp_upper(hits, episodes):
    """Clopper–Pearson 95% 双侧上端。0/N 时闭式 = 1 − 0.025^(1/N)。
    非零用 Beta 分位数——scipy 在就用它，不在就二分 Beta 的 CDF 反函数。"""
    if hits == episodes:
        return 1.0
    if hits == 0:
        return 1.0 - 0.025 ** (1.0 / episodes)
    try:
        from scipy import stats
        return float(stats.beta.ppf(0.975, hits + 1, episodes - hits))
    except Exception:
        lo, hi = hits / episodes, 1.0
        for _ in range(200):
            mid = (lo + hi) / 2.0
            # P(X <= hits | p=mid) = 0.025 处
            if _binom_sf(hits + 1, episodes, mid) < 0.975:
                lo = mid
            else:
                hi = mid
        return lo


def cell_yield(n, q):
    """一格至少一个 rep 出数的概率。独立是**对 n 最有利**的假设：
    共同冲击（associated）下 P(全死) = E[Qⁿ] ≥ (E[Q])ⁿ = qⁿ（Jensen），
    对一切 n 成立，**前提是边际 q 固定**——不固定边际则两种情形无从比较。
    （第一版把这一条写成「逐对正相关」，对 n ≥ 3 as-written 不成立。）"""
    return 1.0 - q ** n


def power_at(n, q, floor_k, cells):
    return _binom_sf(floor_k, cells, cell_yield(n, q))


def q_max_for_power(n, floor_k, cells, power=POWER):
    """给定 n，q 必须压到多少以下才有 `power` 的把握过地板。"""
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if power_at(n, mid, floor_k, cells) >= power:
            lo = mid
        else:
            hi = mid
    return lo


def compute():
    rows = []
    for name in sorted(MEASUREMENTS):
        m = MEASUREMENTS[name]
        q = q_of(name)
        qhi = cp_upper(m["hits"], m["episodes"])
        rows.append({
            "measurement": name,
            "hits": m["hits"], "episodes": m["episodes"],
            "q_point": round(q, 6), "q_cp95_upper": round(qhi, 6),
            "usable_as_q": m["usable_as_q"],
            "expected_live_of_19_at_n_ruled": round(
                CLAIM_CELLS * cell_yield(N_RULED, qhi), 4),
            "power_claim_floor_at_n_ruled_using_cp_upper": round(
                power_at(N_RULED, qhi, 14, CLAIM_CELLS), 6),
            "clears_at_cp_upper": bool(
                power_at(N_RULED, qhi, 14, CLAIM_CELLS) >= POWER),
        })
    thresholds = []
    for label, (k, cells) in sorted(FLOORS.items()):
        thresholds.append({
            "floor": label, "k": k, "cells": cells,
            "q_max_n1": round(q_max_for_power(1, k, cells), 4),
            "q_max_n2": round(q_max_for_power(2, k, cells), 4),
            "q_max_n3": round(q_max_for_power(3, k, cells), 4),
        })
    return {"n_ruled": N_RULED, "power": POWER,
            "floors_digest": floors_digest(),
            "measurements": rows, "thresholds": thresholds,
            "verdict": (
                "在 A7-postfix（0/9，CP 上端 0.3363）下 n=2 的过地板概率 0.985，"
                "⟨n⟩ = 2 够用；在把未重跑的 ar25 三格算回来的 "
                "A7-postfix-with-degraded（3/12，CP 上端 0.5719）下过不了 0.80 的门槛。"
                "**决定它的不是 ⟨n⟩，是 ar25 那三格重跑没重跑**——"
                "launch_blockers.json §9.11 的剩余半边。")}


def verify():
    fails = []
    if floors_digest() != FLOORS_DIGEST:
        fails.append(
            "FLOORS/POWER/N_RULED 被改过（摘要 %s ≠ 封印 %s）。"
            "地板是预注册值，改它是 incident，不是编辑："
            "改完请同时改 STATS_RULES.md §1.2、CLAIMS_TEXT.md C1 与本文封印。"
            % (floors_digest(), FLOORS_DIGEST))

    # 每个数都从 FLOORS 推，不再有第二处 14。
    for label, (k, cells) in sorted(FLOORS.items()):
        for n in (1, 2, 3):
            qm = q_max_for_power(n, k, cells)
            got = power_at(n, qm, k, cells)
            if abs(got - POWER) > 0.01:
                fails.append("%s n=%d：qᵐᵃˣ=%.4f 处的功效算得 %.4f，应为 %.2f"
                             % (label, n, qm, got, POWER))

    # 第一版被推翻的那条不许悄悄回来：47/48 不得被当作 q 使用。
    if MEASUREMENTS["S1-prefix-abort"]["usable_as_q"]:
        fails.append("S1-prefix-abort 被标成可用作 q —— 它是 harness 中止阈值"
                     "命中率，不是 rep 不出数的概率（本文开头两条依据）")

    # 结构性检查，两个方向都要能红：
    #  (a) 乐观那份测量若不再过门槛，结论「⟨n⟩=2 够用」失效；
    #  (b) 悲观那份若已经过门槛，则 ar25 重跑不再是决定项，本文该重写。
    q_opt = cp_upper(*[MEASUREMENTS["A7-postfix"][k]
                       for k in ("hits", "episodes")])
    q_pes = cp_upper(*[MEASUREMENTS["A7-postfix-with-degraded"][k]
                       for k in ("hits", "episodes")])
    if power_at(N_RULED, q_opt, 14, CLAIM_CELLS) < POWER:
        fails.append("A7-postfix 的 CP 上端 %.4f 下 n=2 已过不了 0.80 —— "
                     "「⟨n⟩=2 够用」这句话失效，重写 §5.7" % q_opt)
    if power_at(N_RULED, q_pes, 14, CLAIM_CELLS) >= POWER:
        fails.append("A7-postfix-with-degraded 的 CP 上端 %.4f 下 n=2 已过门槛 —— "
                     "ar25 重跑不再是决定项，重写 §5.7 与 §9.11" % q_pes)
    return fails


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    data = compute()
    fails = verify()

    if args.json:
        json.dump({"data": data, "failures": fails}, sys.stdout,
                  ensure_ascii=False, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 1 if (args.verify and fails) else 0

    print(f"判据：P(出数格数 ≥ 地板) ≥ {data['power']:.2f}，"
          f"⟨n⟩ = {data['n_ruled']}（地板封印 {data['floors_digest']}）\n")
    print(f"{'测量':>28} {'命中/集':>9} {'q 点估':>8} {'CP 上端':>8} "
          f"{'n=2 功效':>9} {'可用作 q':>8}")
    for r in data["measurements"]:
        print(f"{r['measurement']:>28} {r['hits']:>4}/{r['episodes']:<4} "
              f"{r['q_point']:>8.4f} {r['q_cp95_upper']:>8.4f} "
              f"{r['power_claim_floor_at_n_ruled_using_cp_upper']:>9.4f} "
              f"{'是' if r['usable_as_q'] else '否':>8}")
    print()
    print(f"{'地板':>18} {'n=1 需 q≤':>10} {'n=2 需 q≤':>10} {'n=3 需 q≤':>10}")
    for t in data["thresholds"]:
        print(f"{t['floor']:>18} {t['q_max_n1']:>10.4f} "
              f"{t['q_max_n2']:>10.4f} {t['q_max_n3']:>10.4f}")
    print(f"\n{data['verdict']}")
    if fails:
        print("\n不合项：")
        for f in fails:
            print(f"  ✗ {f}")
        return 1 if args.verify else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
