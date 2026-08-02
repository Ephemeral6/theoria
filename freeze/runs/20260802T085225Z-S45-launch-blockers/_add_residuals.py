"""Add the RESIDUALS.json entries for the three blocker rows S45 registered.

`freeze/residuals.py` check 6 is a two-way cross-check: a row in
`launch_blockers.json` with no claimant here is a hard failure, and a claimant
pointing at a row that does not exist is too.  So the rows and these entries
have to land in the same commit.

Note `state` stays "open", not "cleared", for all three -- and that is not
sloppiness.  Check 5 (`residuals.py:220-224`) refuses an entry marked `cleared`
while the document still declares the gap, and §9 MUST keep declaring these
rows as 开跑前置条件 or `launch_gate.py` stops evaluating them at all.  Row 9.11
is the precedent: `implemented` and CLEAR in the gate, `open` here.

Run from the repo root.  Idempotent.
"""

import collections
import io
import json

P = "freeze/RESIDUALS.json"


def entry(code, row, declared_at, kind, territory, who, why, paths,
          statement, clears_when):
    return collections.OrderedDict([
        ("clears_when", clears_when),
        ("code", code),
        ("declared_at", declared_at),
        ("kind", kind),
        ("landing", collections.OrderedDict([
            ("exists_at_head", True),
            ("path", "freeze/launch_blockers.json")])),
        ("launch_blocker_row", row),
        ("owner", collections.OrderedDict([
            ("doc_says", None), ("territory", territory),
            ("who", who), ("why", why)])),
        ("paths", paths),
        ("severity", "launch_blocker"),
        ("state", "open"),
        ("statement", statement),
    ])


NEW = [
    entry(
        "LB-9.25", "9.25", "freeze/STATS_RULES.md §2.3.3", "fix_code", "exam",
        "exam 轨道：次序在 exam/endpoint.py:adjudicate，freeze 裁规则不改它的代码；"
        "已按跨领地纪律走 monitor/inbox/",
        "§2.3.3 裁定 5 是 freeze 的裁量（它是统计裁决规则），实现是 exam 的领地",
        ["freeze/STATS_RULES.md", "freeze/launch_blockers.json",
         "exam/endpoint.py"],
        "覆盖率闸排在 BA 地板之前，而覆盖率破闸走不可结论、BA 破闸走不成立，"
        "且覆盖率先退出后 BA 根本不评。于是一个注定按 BA 判不成立的臂，弃答第 (ii) 类"
        "即换到不可结论。实测 35/270 种能力配置可用，所需弃答题数随 ⟨c_min⟩ 升高而"
        "下降（0.25 要 4 题、1.0 只要 1 题），即抬高地板反而把逃生门开大；且代价严格"
        "为零——弃权计错已把弃答记成 fn，对本来就答错的臂三个受闸的数一位不动。"
        "这是 §9.18/§9.20/§9.21 同一系统性缺陷的第四例。",
        "exam/endpoint.py:adjudicate 的求值次序改为 特异度 → BA → 理由 → 覆盖率，"
        "即所有走「不成立」的闸排在走「不可结论」的覆盖率闸之前；验收：一份 BA 低于"
        "地板、且弃答全部第 (ii) 类的答卷必须退 3（不成立），退 4 即闸未改。"
        "launch_blockers.json 的 9.25 条目 state=implemented 且带命令与两个靶子，"
        "python freeze/launch_gate.py 对该行报 clear。"),
    entry(
        "LB-9.26", "9.26", "freeze/STATS_RULES.md §2.3.4", "fix_code", "exam",
        "exam 轨道：exam/endpoint.py 与新增的 mute-oracle 对照；exam 自己在 "
        "2026-08-01 的 ask §5 里说明它不该从自己领地内部裁这条，freeze 已在 §2.3.4 "
        "裁为 (a)",
        "§2.2 是 freeze 的文件，加地板是 freeze 的裁量；写代码与造对照是 exam 的领地",
        ["freeze/STATS_RULES.md", "freeze/CLAIMS_TEXT.md",
         "freeze/launch_blockers.json", "exam/endpoint.py"],
        "终点二分不出「附证书的正确判决」与「无理由的正确判决」：oracle 与 "
        "cheater-v4 在每一个受闸的数上逐位相同（1.000/1.000/1.000/1.000），都判成立、"
        "都退 0，唯一分开它们的 certified_share（1.000 对 0.000）正是 §2.2 降为探索性"
        "的那一列。§2.3.2 的三条裁定全部只封覆盖率那条路，没有一条封理由那条路。"
        "裁定为 (a) 加地板，决定性理由是 CLAIMS_TEXT.md C4 成立版 585-587 行已经逐字"
        "印着这个对比却没有任何闸能使它为真或为假，而机械规程要求成立版照抄不改一个字。",
        "STATS_RULES.md §2.3.4 裁定 6 的理由地板在 exam/endpoint.py 落地（判据数个数"
        "不数比例、阈值 0 不可调、路由不成立、排在覆盖率闸之前），且两个附条件同时"
        "满足：新增一个可重生的合成对照（mute-oracle：判决全对、一条证书不交），"
        "以及 reason_quality 按类拆分到第 (i) 类。验收：负靶 cheater-v4 从退 0 变退 3，"
        "python freeze/launch_gate.py 对 9.26 报 clear。"),
    entry(
        "LB-9.28", "9.28", "freeze/STATS_RULES.md §9", "fix_code", "freeze",
        "freeze 轨道（与 battery 协同）：tier_conj.py 已经把下游合成规则实现成布尔，"
        "缺的是生产那两个布尔的上游；battery/audit/stats.py 有符号检验但没有 "
        "Wilcoxon，且它自陈 there is no game to pair on",
        "§2.2/§2.2.1 是 freeze 的条款，聚合器是它的可执行半边，"
        "与 launch_gate.py 之于 §9 同型",
        ["freeze/STATS_RULES.md", "freeze/launch_blockers.json",
         "freeze/tier_conj.py", "battery/audit/stats.py"],
        "主终点二的确证统计量（逐局 BA → 跨 ⟨m⟩ 局配对检验 → clean 层复算 → Holm）"
        "在树上没有任何实现：判决题样卷是硬编码的一份、没有代码算逐局 BA；全仓 "
        "def wilcoxon 零命中；唯一的符号检验跑的是电池指标且自陈无法按局配对；"
        "freeze/tier_conj.py:134 把 claim_sig/clean_sig 当布尔输入收下、docstring "
        "写着「本函数不做统计」，而那两个布尔没有任何东西生产。与 §9.14 对终点一记的"
        "是同一个缺陷，而 §9 此前没有对应的行。",
        "一个聚合器存在并被哈希：输入逐臂的逐局 BA 向量，输出配对检验统计量、p、"
        "以及 §4.4.3 六行所需的 claim_sig/clean_sig，§9.13 的 method 在那份代码里钉死，"
        "用合成向量跑通并带一个阴性对照（构造成不显著的向量必须不得报显著）。"
        "本条不要求开跑前算出真数据——Theoria.md:372 禁止提前研究 ⟨m⟩ 局，那样要求"
        "自相矛盾；要的是验收形状。"),
]


def main():
    with io.open(P, encoding="utf-8") as fh:
        doc = json.load(fh, object_pairs_hook=collections.OrderedDict)
    have = {e.get("code") for e in doc["residuals"]}
    added = [e for e in NEW if e["code"] not in have]
    doc["residuals"].extend(added)
    doc["residuals"].sort(key=lambda e: str(e.get("code")))
    with io.open(P, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    print("added: %s | total residuals: %d"
          % ([e["code"] for e in added], len(doc["residuals"])))


if __name__ == "__main__":
    main()
