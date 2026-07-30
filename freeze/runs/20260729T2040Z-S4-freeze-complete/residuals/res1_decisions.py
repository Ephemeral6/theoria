#!/usr/bin/env python3
"""RES-1 对 RESIDUALS.json 的逐条判断 —— 映射给不出的那些。

`merge_owners.py` 按 CHARTER 的分工表把 owner 查出来；剩下这些需要判断，
所以写成一个可审的脚本而不是手改 json：每条决定都带理由，且可重跑。
"""
import json, os, sys

P = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))), "RESIDUALS.json")

#: 同一处缺陷有两个 id（散文一个、§9 一个）。记等价，否则一边关了另一边看着还开。
EQUIV = {"8-a": "9.14", "13-c": "9.11"}
ROWS = {"9.2": "9.2", "9.11": "9.11", "9.14": "9.14"}

#: 「⛔ 就不许开跑」这句话的执行体不存在（LG-1），所以这三条按**冻结**阻塞记。
#: 不是降级：冻结在开跑之前，`Theoria.md:368` 要求清单在首局前提交并哈希，
#: 所以挡住冻结就挡住了开跑。夸大成 launch_blocker 反而会让 launch_gate 与
#: RESIDUALS 长期对不上，而对不上的表没人会修。
DOWNGRADE = {
    "5-a": "engine 清单已由 freeze/ENGINE_MANIFEST.md 落地，剩下的是版本串（5-b）",
    "5-b": "版本串缺失挡冻结（清单不可复现），不在 §9 的开跑前置条件表里",
    "8-b": "判决题终点有实现但在 exam 轨道、没有 battery id；挡冻结不挡花钱",
}

NEW = [
    {
        "code": "13-f",
        "statement": "「这一格出数了」在树上没有定义：⟨n⟩ 的可行性需要一个 q"
                     "（单个 rep 不出数的概率），而三个主终点各自「一次观测何时算成立」"
                     "的判据有两个没有实现（8-a / 8-b）。后果实测过——§5.7 第一版正因如此"
                     "把一个已被 D-016 删除的 harness 中止常数当 q 用了一整轮。",
        "kind": "fix_code", "severity": "freeze_blocker", "state": "open",
        "declared_at": "freeze/MANIFEST_DRAFT.md:13-f",
        "paths": ["battery/metrics/__init__.py", "freeze/n_feasibility.py",
                  "freeze/STATS_RULES.md"],
        "owner": {"territory": "battery",
                  "who": "W-* build lane（8-a/8-b）+ RES-1（接线）",
                  "why": "判据随终点实现一起写；freeze 侧只负责从那里取 q 的定义",
                  "doc_says": None},
        "landing": {"path": "battery/metrics/__init__.py", "exists_at_head": True},
        "clears_when": "8-a 与 8-b 清除后，每个主终点各有一句「一次观测何时算成立」，"
                       "且 freeze/n_feasibility.py 的 MEASUREMENTS 从那里取定义而非常数",
    },
    {
        "code": "LG-1",
        "statement": "`MANIFEST_DRAFT.md:5`「只要还有一项是 ⛔ 缺，就不该开跑封存战役」"
                     "没有执行体：`launch_gate.py` 只读 `STATS_RULES.md` §9 与 "
                     "`launch_blockers.json`，从不读 MANIFEST_DRAFT.md，"
                     "所以 13 项里的 ⛔ 一个也拦不住花钱。",
        "kind": "fix_code", "severity": "freeze_blocker", "state": "open",
        "declared_at": "freeze/MANIFEST_DRAFT.md:5",
        "paths": ["freeze/launch_gate.py", "freeze/MANIFEST_DRAFT.md",
                  "freeze/residuals.py"],
        "owner": {"territory": "freeze", "who": "RES-1",
                  "why": "freeze 套件内，且是这句话自己的执行体",
                  "doc_says": None},
        "landing": {"path": "freeze/launch_gate.py", "exists_at_head": True},
        "clears_when": "二选一并落地：(a) launch_gate 读 RESIDUALS.json，"
                       "任一 severity=freeze_blocker 且 state=open 即拒绝开跑；"
                       "或 (b) 把 MANIFEST_DRAFT.md:5 改写成「⛔ 挡冻结」"
                       "并说明冻结如何挡开跑。两者都要有负对照。",
    },
    {
        "code": "E-WORDING",
        "statement": "三主终点的措辞在 STATS_RULES.md 与 CLAIMS_TEXT.md 之间有 13 处分歧，"
                     "5 处会改变公布出去的数：终点二在两份文件里都没有分母与分析单元；"
                     "裁决用符号检验而claim 正文写 Wilcoxon；`theoria − 消融臂` 在一份里是"
                     "claim 的合取项、在另一份里是探索性；C2 结局 B-2 增加了第四个同 α 检验。"
                     "另有一处最贵的钻法：§2「弃权计错」这条封堵与它自己点名的实现"
                     "（exam/grading/mark.py 的 confusion()，弃权 continue 掉）相反，"
                     "于是「只答有把握的题」代价为零。",
        "kind": "write_document", "severity": "freeze_blocker", "state": "open",
        "declared_at": "freeze/runs/20260729T2040Z-S4-freeze-complete/endpoints/WORDING_AUDIT.md",
        "paths": ["freeze/STATS_RULES.md", "freeze/CLAIMS_TEXT.md",
                  "exam/grading/mark.py"],
        "owner": {"territory": "freeze", "who": "RES-1（措辞）+ W-* build lane（exam 侧语义）",
                  "why": "两份冻结文档是 freeze 领地；弃权语义在 exam 领地，需下发",
                  "doc_says": None},
        "landing": {"path": "freeze/STATS_RULES.md", "exists_at_head": True},
        "clears_when": "verify.sh 接入 stage 16（endpoints/verify_sh_stage16.snippet.sh，"
                       "27 个探针、两个负对照已验）且全绿；"
                       "弃权/未定义特异度的语义在 exam 侧钉住并有一条两靶子检查。",
    },
]


def main():
    with open(P, encoding="utf-8") as fh:
        doc = json.load(fh)
    by = {e["code"]: e for e in doc["residuals"]}
    for code, row in ROWS.items():
        by[code]["launch_blocker_row"] = row
    for code, row in EQUIV.items():
        by[code]["launch_blocker_row"] = row
        by[code]["same_defect_as"] = row
    for code, why in DOWNGRADE.items():
        by[code]["severity"] = "freeze_blocker"
        by[code]["severity_note"] = (
            "散文（MANIFEST_DRAFT.md:5）把任一 ⛔ 读成开跑阻塞，但那句话没有执行体"
            "（见 LG-1）。按冻结阻塞记，不是降级：冻结在开跑之前。" + why)
    by["9.12"]["owner"]["territory"] = "exam"
    by["9.12"]["owner"]["who"] = "W-* build lane（exam 领地）"
    by["9.12"]["owner"]["why"] = "阴性对照要接进 exam 自己的门，那是 exam 的代码"
    for e in NEW:
        by[e["code"]] = e
    doc["residuals"] = sorted(by.values(), key=lambda e: str(e["code"]))
    doc["_res1_decisions"] = (
        "launch_blocker_row / 等价 id / 三条按冻结阻塞记 / 9.12 归 exam / "
        "新增 13-f、LG-1、E-WORDING —— 理由见 "
        "freeze/runs/20260729T2040Z-S4-freeze-complete/residuals/res1_decisions.py")
    with open(P, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    print(f"{len(doc['residuals'])} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
