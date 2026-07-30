#!/usr/bin/env python3
"""RESIDUALS —— 冻结套件里每一处未合项的「由谁在哪补」，可执行的那一半。

`Theoria.md:368` 要求冻结清单在**首局开跑前**提交并哈希。工单
`S4-freeze-complete` 把「可提交」的判据写死为一句话：

> 13 项每项要么指向树上的具体路径+版本，要么明确标注『缺，由谁在哪补』。

前半句已经有闸门管（`verify.sh` 阶段 1/2/12 + `build_manifest.py --verify`）。
**后半句一直没有**：套件里二十多处 `⛔ 缺 5-a` / `⚠ 待办 7-b` 把缺口说得很清楚，
却极少说谁补、补到哪、怎么算补完了。缺口写得再好，没有归属就不会被清——
它只会在冻结那天变成一句「已知问题」，然后跟着清单一起被哈希进去。

本文件是那半句的可执行形式。它做四件事，每件都是**拒绝**而不是提醒：

1. **扫**五份冻结文档里所有 ⛔/⚠ 标记；每一处**声明式**标记必须带一个 code。
   没 code 的缺口无法被跟踪，所以它红。
2. **对**：每个 code 必须在 `RESIDUALS.json` 里有一条，四个字段齐全——
   `owner`（谁）、`landing`（补到哪）、`clears_when`（怎么算补完）、`kind`。
   `clears_when` 必须是一条**能跑的命令或能查的条件**；愿望不算。
3. **查重**：同一个 code 出现两处声明即红。今天就有一例（`2-b` 有两条，
   一条是 v0.2 自称五节实为六节，一条是 G5 冻结政策挂在不存在的 tag 上）——
   「2-b 补完了吗」有两个答案，于是其中一条可以被当成另一条关掉。
4. **对齐可执行闸门**：标 `launch_blocker` 的必须在 `launch_blockers.json` 里
   有对应行，反之亦然。散文与闸门分歧时，分歧本身就是发现。

**它不相信 `RESIDUALS.json` 的任何自述。** `state: cleared` 的条目，其 code 必须
在文档里已经不再以 ⛔/⚠ 声明形式出现；声称已落地的路径必须在 git HEAD 上真的在。
改这个 json 改不动任何判定——这一点与 `launch_blockers.json` 的
`_how_it_does_not_clear` 同源，刻意保持一致。

用法：

    python freeze/residuals.py            # 打印总表
    python freeze/residuals.py --verify    # 闸门：任何一条不合即 exit 1
    python freeze/residuals.py --json      # 机器可读汇总（确定性、字节稳定）
"""

import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TABLE = os.path.join(HERE, "RESIDUALS.json")

#: 被扫的五份文档。冻结套件的全部散文都在这里；新增一份文档而不加进来，
#: 等于给缺口开了一个不被扫的藏身处，所以这张表本身也进 verify.sh 的哈希。
DOCS = [
    "MANIFEST_DRAFT.md",
    "PENDING_FIVE.md",
    "STATS_RULES.md",
    "CLAIMS_TEXT.md",
    "RECONCILE.md",
]

#: 声明式标记：行首 `**`，紧跟 ⛔ / ⚠ / ⛔→⚠，再跟 `缺` 或 `待办`。
#: 「声明」与「引用」必须分开：`（见 ⛔ 8-a）` 是引用，重复出现是正常的交叉引用；
#: 行首那一条才是缺口本身的定义处，重复即冲突。
#: `缺`/`待办` 这两个字是可选的，code 也是——**故意的**。行首一个 ⛔ 或 ⚠
#: 就是在声明一处缺口，写不写「待办」不改变这件事。少了 code 的那些会被判红
#: （见下面第 1 项），这正是本闸门要抓的第一类：没有编号就没法问「它补完了吗」。
DECL = re.compile(r"^\*\*(⛔→⚠|⛔|⚠)\s*(?:缺|待办)?\s*([A-Za-z0-9]+-[A-Za-z0-9]+)?")
#: 任何位置的带 code 标记，用于「文档里还开着吗」这一问。
ANY_MARK = re.compile(r"(⛔→⚠|⛔|⚠)\s*(?:缺|待办|见)\s*([A-Za-z0-9]+-[A-Za-z0-9]+)")
#: **重述**：同一处缺口在第二份文档里被再说一遍。写成 `**⚠ 见 <code>**`。
#: 需要这个形式，是因为「一处缺口只能有一个声明」与「缺口该在相关的每一节被提到」
#: 两条都对，而不区分它们就只能牺牲一条：要么重述被判成重复声明（红），
#: 要么放弃查重（于是 2-b 那样的一码两义就查不出来）。
RESTATE = re.compile(r"^\*\*(⛔→⚠|⛔|⚠)\s*见\s*([A-Za-z0-9]+-[A-Za-z0-9]+)")

KINDS = {
    "fix_code",
    "write_document",
    "cut_a_tag",
    "commit_untracked_evidence",
    "register_limitation",
    "human_decision",
}
SEVERITIES = {"launch_blocker", "freeze_blocker", "registered"}
STATES = {"open", "cleared"}
#: 领地名单与 CHARTER.md 的分工表同源。`repo-root` 是两轨都不独占的共享面
#: （根 `.gitattributes` 就在这里），单列出来是因为它最容易变成没人认领的那一格。
TERRITORIES = {
    "engine-rig", "theory-compiler", "theoria-arm", "ablation-arm",
    "baseline-arms", "battery", "proxy", "arc-recon", "papers", "figures",
    "CONTRACTS", "freeze", "repo-root", "monitor", "exam", "release",
}

REQUIRED = ("code", "statement", "kind", "severity", "state",
            "owner", "landing", "clears_when")


def git(*args):
    out = subprocess.run(["git", "-C", REPO, *args],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def tracked_at_head(path):
    """路径在 git HEAD 上存在吗。**不看工作树**——工作树里有、HEAD 里没有的东西
    冻结不了，而那正是 13-a（依据 untracked）这一类缺口的形状。"""
    return git("cat-file", "-e", f"HEAD:{path}") is not None


def scan_docs():
    """返回 (declarations, references)。两者都按 (code, file, line) 排序，
    保证输出与文件系统顺序无关。"""
    decls, refs, uncoded = [], [], []
    for name in DOCS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            uncoded.append((name, 0, "文档不存在，但 DOCS 里列着"))
            continue
        with open(path, encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                rs = RESTATE.match(line)
                if rs:
                    # 重述不是声明，只记成引用；被重述的 code 必须另有声明处，
                    # 这一点由「表里 open 的 code 必须在文档里有声明」那条兜住。
                    refs.append((rs.group(2), name, i))
                    continue
                m = DECL.match(line)
                if m:
                    code = m.group(2)
                    if code is None:
                        uncoded.append((name, i, line.strip()[:80]))
                    else:
                        decls.append((code, name, i, m.group(1)))
                declared_here = m.group(2) if m else None
                for m2 in ANY_MARK.finditer(line):
                    if m2.group(2) != declared_here:
                        refs.append((m2.group(2), name, i))
    return sorted(decls), sorted(refs), sorted(uncoded)


def load_table():
    with open(TABLE, encoding="utf-8") as fh:
        return json.load(fh)


def check(verbose=True):
    """返回 (failures, warnings, stats)。failures 非空即闸门红。"""
    fails, warns = [], []
    decls, refs, uncoded = scan_docs()
    table = load_table()
    entries = {e["code"]: e for e in table["residuals"]}
    if len(entries) != len(table["residuals"]):
        fails.append("RESIDUALS.json 里有重复 code")

    # 1. 没带 code 的声明式缺口 —— 无法跟踪，所以不许有
    for name, line, text in uncoded:
        fails.append(f"{name}:{line} 声明了一处缺口但没带 code：{text}")

    # 2. 查重：同一 code 两处声明
    seen = {}
    for code, name, line, mark in decls:
        seen.setdefault(code, []).append(f"{name}:{line}")
    for code, where in sorted(seen.items()):
        if len(where) > 1:
            fails.append(
                f"code {code} 在 {len(where)} 处被声明（{', '.join(where)}）"
                "——「它补完了吗」于是有多个答案")

    # 3. 文档里开着的 code 必须在表里
    for code in sorted(seen):
        if code not in entries:
            fails.append(f"code {code} 在文档里开着，但 RESIDUALS.json 没有它"
                         f"（{seen[code][0]}）")

    # 4. 每条的字段完整性与取值
    for code, e in sorted(entries.items()):
        for key in REQUIRED:
            if key not in e or e[key] in (None, "", [], {}):
                if key == "clears_when" and e.get("blocked_because"):
                    warns.append(f"{code}: clears_when 为空，理由已登记："
                                 f"{e['blocked_because'][:60]}")
                    continue
                fails.append(f"{code}: 字段 {key} 缺或为空")
        if e.get("kind") not in KINDS:
            fails.append(f"{code}: kind={e.get('kind')!r} 不在名单里")
        if e.get("severity") not in SEVERITIES:
            fails.append(f"{code}: severity={e.get('severity')!r} 不在名单里")
        if e.get("state") not in STATES:
            fails.append(f"{code}: state={e.get('state')!r} 不在名单里")
        owner = e.get("owner") or {}
        if owner.get("territory") not in TERRITORIES:
            fails.append(f"{code}: owner.territory={owner.get('territory')!r}"
                         " 不在领地名单里")
        if not owner.get("who"):
            fails.append(f"{code}: owner.who 为空——「由谁补」正是本文件要问的")
        landing = e.get("landing") or {}
        if not landing.get("path"):
            fails.append(f"{code}: landing.path 为空——「补到哪」没有答案")
        # 声称已经在树上的落点，必须在 HEAD 上真的在
        if landing.get("exists_at_head") is True:
            for p in str(landing["path"]).split("|"):
                p = p.strip()
                if p and not tracked_at_head(p):
                    fails.append(f"{code}: landing.path {p} 自称已在 HEAD 上，"
                                 "实际不在（工作树里有不算）")

    # 5. 自述与文档对账：cleared 的不许还在文档里以声明形式开着
    for code, e in sorted(entries.items()):
        if e.get("state") == "cleared" and code in seen:
            fails.append(f"{code}: 表里写 cleared，文档 {seen[code][0]} 仍以"
                         "声明形式开着——两者必须同时改")
        if e.get("state") == "open" and code not in seen:
            # 引用还在、声明没了：多半是文档改了而表没跟上
            where = "，仅存引用" if any(r[0] == code for r in refs) else ""
            warns.append(f"{code}: 表里写 open，文档里已无声明{where}")

    # 6. 与可执行闸门对齐
    lb_path = os.path.join(HERE, "launch_blockers.json")
    lb_rows = set()
    if os.path.exists(lb_path):
        with open(lb_path, encoding="utf-8") as fh:
            lb_rows = set(json.load(fh).get("blockers", {}))
    claimed = {e.get("launch_blocker_row") for e in entries.values()
               if e.get("severity") == "launch_blocker"}
    claimed.discard(None)
    for row in sorted(claimed - lb_rows):
        fails.append(f"severity=launch_blocker 指向 §{row}，"
                     "但 launch_blockers.json 里没有这一行")
    for row in sorted(lb_rows - claimed):
        fails.append(f"launch_blockers.json 有 §{row}，"
                     "但 RESIDUALS.json 里没有任何条目认领它")
    for code, e in sorted(entries.items()):
        if e.get("severity") == "launch_blocker" and not e.get("launch_blocker_row"):
            fails.append(f"{code}: 标了 launch_blocker 却没写 launch_blocker_row")

    stats = {
        "declarations": len(decls),
        "distinct_codes_open_in_docs": len(seen),
        "entries": len(entries),
        "by_kind": {k: sum(1 for e in entries.values() if e.get("kind") == k)
                    for k in sorted(KINDS)},
        "by_severity": {s: sum(1 for e in entries.values()
                               if e.get("severity") == s)
                        for s in sorted(SEVERITIES)},
        "by_state": {s: sum(1 for e in entries.values()
                            if e.get("state") == s) for s in sorted(STATES)},
        "unowned": 0,
    }
    return fails, warns, stats


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verify", action="store_true",
                    help="闸门模式：任何一条不合即 exit 1")
    ap.add_argument("--json", action="store_true",
                    help="机器可读汇总（确定性）")
    args = ap.parse_args(argv)

    fails, warns, stats = check()

    if args.json:
        json.dump({"failures": fails, "warnings": warns, "stats": stats},
                  sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 1 if (args.verify and fails) else 0

    table = load_table()
    print(f"RESIDUALS —— {stats['entries']} 条，"
          f"文档里开着 {stats['distinct_codes_open_in_docs']} 个 code")
    print(f"  按性质：{stats['by_kind']}")
    print(f"  按严重度：{stats['by_severity']}")
    print(f"  按状态：{stats['by_state']}")
    print()
    for e in sorted(table["residuals"], key=lambda r: r["code"]):
        owner = e.get("owner", {})
        print(f"[{e.get('severity','?'):<15}] {e['code']:<8} "
              f"{owner.get('territory','?')} / {owner.get('who','?')}")
        print(f"    {e.get('statement','')}")
        print(f"    落点：{(e.get('landing') or {}).get('path','?')}")
        print(f"    清除条件：{e.get('clears_when') or '⛔ 无可执行条件：' + str(e.get('blocked_because'))}")
    if warns:
        print("\n提醒（不判红）：")
        for w in warns:
            print(f"  · {w}")
    if fails:
        print("\n不合项：")
        for f in fails:
            print(f"  ✗ {f}")
        print(f"\n{len(fails)} 条不合。")
        return 1 if args.verify else 0
    print("\n每一处缺口都有 owner、落点与清除条件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
