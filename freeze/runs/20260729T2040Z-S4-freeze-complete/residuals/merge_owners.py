#!/usr/bin/env python3
"""把 extracted.json（subagent 抽的原料）+ 领地→owner 映射，合成 freeze/RESIDUALS.json。

**为什么是脚本而不是手打**：owner 的分配不是审美判断，是查表——
`monitor/CHARTER.md` 的分工表已经写死了谁能改哪块。手打二十多条会引入
「这条我记得是谁」的记忆误差，而脚本让映射本身可被审：改一次映射，
全表跟着变，且 diff 看得见。

个别需要人判断的（映射给不出、或跨两个领地），脚本标 `NEEDS-RES1`，
由 RES-1 逐条填，不允许静默默认——沉默的默认值正是「没人认领」的来源。

用法：python merge_owners.py [--write]
"""

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FREEZE = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
EXTRACTED = os.path.join(HERE, "extracted.json")
OUT = os.path.join(FREEZE, "RESIDUALS.json")

#: 领地 → 谁改。依据 `monitor/CHARTER.md` 的硬边界表：
#: RES-1 只在自己领地内改代码且是唯一能花 API 钱的；RES-2 独占论文正文；
#: W-* 一次性工人在领到的领地内改代码；契约与 monitor/ 归监控；
#: 另一轨（theory-compiler）的文件谁都不许代改，只能走 PARTNER_SYNC 提案。
OWNER_BY_TERRITORY = {
    "freeze": {"who": "RES-1", "how": "本套件即 RES-1 的领地，自己改"},
    "baseline-arms": {"who": "RES-1（花钱的部分）/ W-* build lane（纯代码）",
                      "how": "重跑包络要花 API 钱，按 CHARTER 只有 RES-1 能花；"
                             "不花钱的代码修正可下发 W-*"},
    "battery": {"who": "W-* build lane", "how": "监控按 board 下发，battery 领地"},
    "proxy": {"who": "W-* build lane", "how": "监控按 board 下发，proxy 领地"},
    "engine-rig": {"who": "W-* build lane（engine-rig 领地）",
                   "how": "engine-rig 是 engine-rig 轨的目录；"
                          "本仓当前由一次性工人在该领地内施工"},
    "theoria-arm": {"who": "RES-1", "how": "theoria-arm 是 campaign 赛道的领地"},
    "ablation-arm": {"who": "W-* build lane", "how": "监控下发"},
    "theory-compiler": {"who": "theory-compiler 轨（另一轨，不代改）",
                        "how": "CLAUDE.md 明令不许编辑另一轨的文件；"
                               "只能在 PARTNER_SYNC.md 追加一段请对方处理"},
    "CONTRACTS": {"who": "监控", "how": "CHARTER 分工表：改契约只有监控可以"},
    "repo-root": {"who": "监控", "how": "仓库根是两轨共享面，无人独占；"
                                       "按 CHARTER 只有监控能裁"},
    "arc-recon": {"who": "W-* build lane", "how": "arc-recon 是共享地，非赛道"},
    "monitor": {"who": "监控", "how": "monitor/ 只有监控写"},
    "papers": {"who": "RES-2", "how": "CHARTER：论文正文只有 RES-2 下笔"},
    "figures": {"who": "W-* build lane", "how": "监控下发"},
}

NEEDS = "NEEDS-RES1"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                    help="写 freeze/RESIDUALS.json；否则只打印")
    args = ap.parse_args(argv)

    if not os.path.exists(EXTRACTED):
        print(f"缺 {EXTRACTED} —— 抽取还没落盘", file=sys.stderr)
        return 2
    with open(EXTRACTED, encoding="utf-8") as fh:
        raw = json.load(fh)
    records = raw["residuals"] if isinstance(raw, dict) else raw

    out, flagged = [], []
    for r in records:
        terr = r.get("territory")
        owner = OWNER_BY_TERRITORY.get(terr)
        entry = {
            "code": r.get("code"),
            "statement": r.get("statement"),
            "kind": r.get("kind"),
            "severity": r.get("severity"),
            "state": r.get("state", "open"),
            "declared_at": f"{r.get('file')}:{r.get('line')}",
            "paths": r.get("paths", []),
            "owner": {
                "territory": terr,
                "who": (owner or {}).get("who", NEEDS),
                "why": (owner or {}).get("how", NEEDS),
                "doc_says": r.get("doc_says_owner"),
            },
            # 「补到哪」= 这条残余点名的第一个路径。抽取记录里 `paths` 是
            # 从文档原文取的，所以落点也就有了出处，不是我现填的。
            "landing": r.get("landing") or {
                "path": (r.get("paths") or [NEEDS])[0].split(":")[0],
                "exists_at_head": None,
            },
            "clears_when": r.get("clears_when"),
        }
        if r.get("launch_blocker_row"):
            entry["launch_blocker_row"] = r["launch_blocker_row"]
        if r.get("blocked_because"):
            entry["blocked_because"] = r["blocked_because"]
        if NEEDS in json.dumps(entry, ensure_ascii=False) or not entry["clears_when"]:
            flagged.append(entry["code"])
        out.append(entry)

    out.sort(key=lambda e: str(e["code"]))
    doc = {
        "_what": "冻结套件里每一处未合项的 owner / 落点 / 可执行清除条件。"
                 "由 freeze/residuals.py 校验；改本文件改不动任何判定。",
        "_authority": "缺口本身的权威是那五份文档；本文件只记『由谁在哪补』。"
                      "owner 的分配依据 monitor/CHARTER.md 的分工表。",
        "_written": "2026-07-29, S4-freeze-complete, RES-1",
        "residuals": out,
    }
    if args.write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2, sort_keys=True)
            fh.write("\n")
        print(f"写了 {OUT}：{len(out)} 条")
    else:
        print(json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True)[:2000])
    if flagged:
        print(f"\n需 RES-1 逐条填的（{len(flagged)}）：{', '.join(map(str, flagged))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
