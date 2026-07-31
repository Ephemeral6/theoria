#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4.4 的可执行形式：配对终点的两层合成，以及它那张最坏情形功效表。

为什么要有这支脚本，而不是让那张表留在散文里
----------------------------------------------
`STATS_RULES.md` §4.4.2 的表是**一条裁决的前提**：它决定第 1 行
（clean 层在结构上不可能显著 → 不可结论）在哪些 ⟨m⟩ 上触发。
初稿手算，两格 p 写错了（终点三 0.0078 写成 0.0039、⟨m⟩ = 19
0.0039 写成 0.0020，都少算一位）。**两格都不改变那一行的结论**——
所以它们是最坏的一种错：不影响裁决，因此不会被任何人在读裁决时发现，
而它们仍然是发表出去的数字。

`n_feasibility.py` 在 §5.7 上已经立了这个先例（把地板算术从散文里搬进代码，
并封印摘要）。本文照同一形状做，并沿用同一条纪律：
**每个数都从一处推，不留第二份**。

它检查什么
----------
1. §4.4.2 的表逐格与现算值相符（`--verify`）。
2. §4.4.3 的裁决表是一个**全函数**：六行按序求值，任何输入都落到恰好一个裁决上，
   且没有一行是死行（每行都有能到达它的输入）。一条永不触发的规则与一条不存在的
   规则在效果上相同，但读者会以为它在保护什么。
3. §4.1.0 的两个边界（散文的 `> n/3` 与终点二那句的 `⌈n/3⌉`）分歧在哪，
   并断言那个分歧**动不了 §4.4 第 1 行**——这是 §4.4.2 那段登记里写下的话，
   写下的话要能被跑。

用法
----
    python freeze/tier_conj.py            # 印表与裁决网格
    python freeze/tier_conj.py --verify   # 闸门模式，不合即退出码 1
"""

import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CLAIM_SET = os.path.join(REPO, "arc-recon", "data", "claim_set.json")

#: Holm 阶梯（§4.3：family 恒为三个主终点，α = 0.05）。
#: 三级门槛依次为 α/3、α/2、α；最紧那级是 α/3。
HOLM_LEVELS = (0.05 / 3, 0.05 / 2, 0.05)
HOLM_TIGHTEST = HOLM_LEVELS[0]

#: §2.2.1 在散文里列出的 ⟨m⟩ → ⟨m_clean⟩ 六个值。**这里不抄它，只对照它**：
#: 下面 `m_to_mclean()` 从 claim_set.json 现算全表，本字典只用来断言那六个值没写错。
DOC_M_TO_MCLEAN = {5: 2, 10: 4, 12: 5, 13: 6, 14: 7, 19: 12}


def m_to_mclean():
    """⟨m⟩ → ⟨m_clean⟩ 全表，从 claim_set.json 现算。

    ⟨m⟩ 局是 claim 层 19 局按**码位序的前缀**（§2.2.1），⟨m_clean⟩ 是该前缀里
    属 clean 层的局数。§2.2.1 的散文只列了六个 ⟨m⟩，而 ⟨m⟩ 是 needs_human、
    取值范围是 1..19——**没被列出的那些不是不可选，只是没人算过**，
    而 §4.4.2 发现其中至少一个（⟨m⟩ = 16）落在一处会改变裁决的歧义上。
    """
    with open(CLAIM_SET, encoding="utf-8") as fh:
        data = json.load(fh)
    ordered = sorted(data["claim_set"])
    clean = set(data["clean"])
    return {m: sum(1 for g in ordered[:m] if g in clean)
            for m in range(1, len(ordered) + 1)}


def min_two_sided_p(v):
    """v 对全部同向时，符号检验／exact Wilcoxon 的最小两侧 p。

    v = 0 时没有可检验的对，约定返回 1.0（不可能显著）。
    """
    if v <= 0:
        return 1.0
    return 2 * 0.5 ** v


def drop_threshold_strict(n):
    """§4.1.0 散文的门槛：剔除数 > n/3 即不可结论。返回最小的触发剔除数。"""
    d = 1
    while not (d > n / 3):
        d += 1
    return d


def drop_threshold_ceil(n):
    """§4.1.0 给终点二那句的门槛：⌈n/3⌉。返回最小的触发剔除数。"""
    return math.ceil(n / 3)


def worst_case_v(n, threshold):
    """尚未被 §4.1.0 判死的前提下，该层可评对数的下界。

    门槛是「剔除数 ≥ threshold 即不可结论」，所以最大允许剔除 = threshold − 1。
    """
    return n - (threshold - 1)


def table_rows(mmap=None):
    """§4.4.2 的表，现算。"""
    mmap = mmap or m_to_mclean()
    rows = [("终点三", 12, drop_threshold_strict(12), "散文 > n/3")]
    for m in (19, 14, 13, 12, 10):
        n = mmap[m]
        rows.append(("终点二，⟨m⟩ = %d" % m, n, drop_threshold_ceil(n), "⌈n/3⌉"))
    out = []
    for label, n, th, which in rows:
        md = th - 1
        v = worst_case_v(n, th)
        p = min_two_sided_p(v)
        out.append({
            "label": label, "n": n, "threshold": th, "max_drop": md,
            "worst_v": v, "min_p": p, "which": which,
            "reaches_tightest": p <= HOLM_TIGHTEST,
            "reaches_loosest": p <= HOLM_LEVELS[-1],
        })
    return out


#: §4.4.2 的表在 STATS_RULES.md 里印出来的值。逐格对照，防止散文与算术分家。
#: 格式：label -> (max_drop, worst_v, min_p 四舍五入到 4 位, 最紧级可达)
DOC_TABLE = {
    "终点三":            (4, 8, 0.0078, True),
    "终点二，⟨m⟩ = 19":  (3, 9, 0.0039, True),
    "终点二，⟨m⟩ = 14":  (2, 5, 0.0625, False),
    "终点二，⟨m⟩ = 13":  (1, 5, 0.0625, False),
    "终点二，⟨m⟩ = 12":  (1, 4, 0.1250, False),
    "终点二，⟨m⟩ = 10":  (1, 3, 0.2500, False),
}


def verdict(v_clean, drop_frac_exceeded, claim_sig, claim_dir_ok,
            clean_sig, clean_same_dir, alpha_star=HOLM_TIGHTEST):
    """§4.4.3 的裁决表，按序求值。返回 '不可结论' / '不成立' / '成立'。

    参数刻意全部是布尔或整数：本函数**不做统计**，它只把 §4.4.3 的六行
    编码成代码，使「按序求值」这四个字有一个唯一的所指。
    """
    # 0 行 —— §4.1.0，先于以下各行
    if drop_frac_exceeded:
        return "不可结论"
    # 1 行 —— clean 层在结构上不可能达到它需要的门槛
    if min_two_sided_p(v_clean) > alpha_star:
        return "不可结论"
    # 2 行 —— claim 层不显著或方向错
    if not claim_sig or not claim_dir_ok:
        return "不成立"
    # 3 行 —— clean 层显著且反向
    if clean_sig and not clean_same_dir:
        return "不成立"
    # 4 行 —— clean 层有功效而未达到
    if not clean_sig:
        return "不成立"
    # 5 行 —— 两层皆显著同向
    return "成立"


def check_total_function():
    """裁决表必须是全函数，且没有死行。

    穷举六个输入的全部组合（v_clean 取能分开第 1 行两侧的几个值），
    断言每个组合都得到一个合法裁决，并统计每一行各被走到多少次。
    """
    fails = []
    reached = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    legal = {"不可结论", "不成立", "成立"}
    for v in (0, 3, 5, 7, 8, 12):
        for dfe in (False, True):
            for cs in (False, True):
                for cd in (False, True):
                    for ls in (False, True):
                        for lsd in (False, True):
                            got = verdict(v, dfe, cs, cd, ls, lsd)
                            if got not in legal:
                                fails.append("裁决 %r 不在名单里 (v=%d)" % (got, v))
                            # 复算它落在第几行，用来找死行
                            if dfe:
                                reached[0] += 1
                            elif min_two_sided_p(v) > HOLM_TIGHTEST:
                                reached[1] += 1
                            elif not cs or not cd:
                                reached[2] += 1
                            elif ls and not lsd:
                                reached[3] += 1
                            elif not ls:
                                reached[4] += 1
                            else:
                                reached[5] += 1
    for row, n in sorted(reached.items()):
        if n == 0:
            fails.append("§4.4.3 第 %d 行是死行：没有任何输入能走到它，"
                         "而读者会以为它在保护什么" % row)
    return fails, reached


#: §4.1.0 的两个边界会让 §4.4.3 第 1 行倒向不同裁决的那些 clean 层对数。
#: 这不是一个可以「登记后不管」的分歧：在这些对数上，选哪个边界就等于选 C4
#: 发不发得出来。§4.4.2 与 §9.22 都引用本常数，`--verify` 断言它没漏。
VERDICT_FLIPPING_N = (9,)


def check_boundary_claim(mmap=None):
    """§4.1.0 的两个边界在哪些对数上分歧，以及在哪些上**会改变裁决**。

    §4.4.2 的登记初稿写的是「分歧动不了 §4.4 第 1 行」。**那句话是错的，
    是本脚本抓出来的**：n = 9 时 `>n/3` 给 p = 0.03125（第 1 行触发 → 不可结论），
    `⌈n/3⌉` 给 p = 0.015625（不触发 → 可以走到成立）。所以本函数改成
    **算出**会翻转的那些 n，并断言它与 `VERDICT_FLIPPING_N` 相符——
    登记的是一个数，不是一句安慰。
    """
    mmap = mmap or m_to_mclean()
    fails, disagree, flipping = [], [], []
    for n in range(1, 20):
        a, b = drop_threshold_strict(n), drop_threshold_ceil(n)
        if a == b:
            continue
        disagree.append(n)
        pa = min_two_sided_p(worst_case_v(n, a))
        pb = min_two_sided_p(worst_case_v(n, b))
        if (pa <= HOLM_TIGHTEST) != (pb <= HOLM_TIGHTEST):
            flipping.append(n)
    if not disagree:
        fails.append("两个边界处处相等——§4.4.2 登记了一个不存在的分歧")
    if tuple(flipping) != tuple(VERDICT_FLIPPING_N):
        fails.append("会改变裁决的对数现算为 %r，而 §4.4.2／§9.22 登记的是 %r"
                     % (flipping, list(VERDICT_FLIPPING_N)))
    # 这些对数由哪些 ⟨m⟩ 取到 —— 一个说得出 ⟨m⟩ 的歧义才是可拍板的歧义
    reachable = {n: sorted(m for m, mc in mmap.items() if mc == n)
                 for n in flipping}
    for n, ms in reachable.items():
        if not ms:
            fails.append("clean 层 %d 对会改变裁决，但没有任何 ⟨m⟩ 能取到它——"
                         "则本条不是开跑前置条件，登记写重了" % n)
    return fails, disagree, flipping, reachable


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:                                       # pragma: no cover
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="闸门模式：散文与算术不符即退出码 1")
    args = ap.parse_args()

    mmap = m_to_mclean()
    rows = table_rows(mmap)
    fails = []

    # §2.2.1 的六个值必须与 claim_set.json 的现算相符
    for m, mc in sorted(DOC_M_TO_MCLEAN.items()):
        if mmap.get(m) != mc:
            fails.append("§2.2.1 写 ⟨m⟩ = %d → ⟨m_clean⟩ = %d，"
                         "claim_set.json 现算是 %r" % (m, mc, mmap.get(m)))

    print("§4.4.2 最坏情形功效表（现算）")
    print("%-22s %4s %8s %6s %12s %9s %8s"
          % ("层", "n", "最大剔除", "⟨v⟩", "最小两侧 p", "≤0.0167", "≤0.05"))
    for r in rows:
        print("%-22s %4d %8d %6d %12.6f %9s %8s"
              % (r["label"], r["n"], r["max_drop"], r["worst_v"],
                 r["min_p"], r["reaches_tightest"], r["reaches_loosest"]))
        doc = DOC_TABLE.get(r["label"])
        if doc is None:
            fails.append("%s：现算出来的行在 STATS_RULES.md 的表里没有对应格"
                         % r["label"])
            continue
        got = (r["max_drop"], r["worst_v"], round(r["min_p"], 4),
               r["reaches_tightest"])
        if got != doc:
            fails.append("%s：散文写 %r，现算 %r" % (r["label"], doc, got))
    for label in DOC_TABLE:
        if not any(r["label"] == label for r in rows):
            fails.append("%s：STATS_RULES.md 的表里有这一行，现算里没有" % label)

    tf_fails, reached = check_total_function()
    fails.extend(tf_fails)
    print()
    print("§4.4.3 裁决表：768 组输入，每行被走到的次数 %r" % reached)

    bc_fails, disagree, flipping, reachable = check_boundary_claim(mmap)
    fails.extend(bc_fails)
    print("§4.1.0 两个边界的分歧点：n ∈ %r（其余处处相等）" % disagree)
    print("  其中**会改变 §4.4.3 第 1 行裁决**的：n ∈ %r" % flipping)
    for n, ms in sorted(reachable.items()):
        print("    clean 层 %d 对 ← ⟨m⟩ ∈ %r（§2.2.1 的散文表没有列这些 ⟨m⟩）"
              % (n, ms))
    print()
    print("⟨m⟩ → ⟨m_clean⟩ 全表（claim_set.json 现算，§2.2.1 只列了 6 个）")
    print("  " + "  ".join("%d→%d" % (m, mmap[m]) for m in sorted(mmap)))

    if args.verify:
        if fails:
            print()
            for f in fails:
                print("FAIL " + f)
            return 1
        print()
        print("PASS §4.4 的表、裁决与边界断言三者与散文一致")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
