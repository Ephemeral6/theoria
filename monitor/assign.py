# -*- coding: utf-8 -*-
"""把一句话变成一件有人做的活 —— 监控的下发入口。

    # 研究任务 → 工作板（研究员自助领取）
    python monitor/assign.py research S3 proxy "给账本加哈希链" --priority 2 --body "..."

    # 运维指令 → 邮箱（对应运维下个周期读到并回执）
    python monitor/assign.py ops OPS-A "下一跑专查我宣布过已修的每一条"

    # 紧急研究任务：置顶 + 若额度允许立刻起一个研究员
    python monitor/assign.py research V3 battery "修好区分力口径" --urgent

设计要点：
* 研究任务落 `board/items/<id>.md`，带 priority / cell / territory / deps 前言，
  由长时研究员原子领取——**监控不再逐件派单，只负责供货**；
* 运维指令落 `mailbox/<ID>.md` 的 OPEN 条目，运维每周期先读邮箱再干活，
  执行后改 ACK 并回执，形成闭环；
* 领地互斥由工作板保证：同一目录同时只有一个人写，冲突在下发时就被挡住。
"""

import argparse
import datetime
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ITEMS = os.path.join(HERE, "board", "items")
CLAIMED = os.path.join(HERE, "board", "claimed")
MAILBOX = os.path.join(HERE, "mailbox")

OPS = {"OPS-A": "漂移审计员", "OPS-B": "浏览器专员",
       "OPS-M": "合并裁判", "OPS-R": "回顾员"}


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def slug(text, n=5):
    """英文标题取词；中文标题没有可用词根，交由 --id 指定或退回时间戳。"""
    words = re.findall(r"[a-z0-9]{2,}", text.lower())
    return "-".join(words[:n]) if words else datetime.datetime.now().strftime("%H%M")


def territory_busy(terr):
    if not os.path.isdir(CLAIMED):
        return None
    for f in os.listdir(CLAIMED):
        head = open(os.path.join(CLAIMED, f), encoding="utf-8").read(400)
        m = re.search(r"^territory:\s*(\S+)", head, re.M)
        if m and m.group(1) == terr:
            return f[:-3].split(".")[0]
    return None


SELF_SUPPLY_CAP = 3          # 每条赛道同时未完成的自供条目上限


def self_supplied_pending(author):
    n = 0
    for d in (ITEMS, CLAIMED):
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".md") and ("author: %s" % author) in                     open(os.path.join(d, f), encoding="utf-8").read(400):
                n += 1
    return n


def add_research(cell, territory, title, body, priority, deps, urgent,
                 name="", lane="", author=""):
    os.makedirs(ITEMS, exist_ok=True)
    if author and author.startswith("RES-"):
        pending = self_supplied_pending(author)
        if pending >= SELF_SUPPLY_CAP:
            sys.exit("%s 已有 %d 件未完成的自供条目（上限 %d）——"
                     "先交付再供货。" % (author, pending, SELF_SUPPLY_CAP))
    busy = territory_busy(territory)
    if busy:
        print("注意：领地 %s 正被 %s 占用；此条目会排队，等它交付后才可领取。"
              % (territory, busy))
    iid = "%s-%s" % (cell, name or slug(title))
    path = os.path.join(ITEMS, iid + ".md")
    if os.path.exists(path):
        iid += "-b"
        path = os.path.join(ITEMS, iid + ".md")
    text = ("priority: %d\ncell: %s\nterritory: %s\ndeps: %s\n\n# %s · %s\n\n%s\n"
            % (1 if urgent else priority, cell, territory, deps or "none",
               iid, title, body or title))
    open(path, "w", encoding="utf-8", newline="\n").write(text)
    print("已下发研究任务：%s（领地 %s，优先级 %s）"
          % (iid, territory, 1 if urgent else priority))
    if urgent:
        print("已置顶：下一个空闲研究员会先领它。")
    return iid


def add_ops(oid, instruction, ref):
    if oid not in OPS:
        sys.exit("未知运维：%s（可用：%s）" % (oid, ", ".join(OPS)))
    path = os.path.join(MAILBOX, "%s.md" % oid)
    entry = ("\n### %s · %s\nstatus: OPEN\n%s\n%s\n"
             % (utc(), instruction.split("。")[0][:40],
                "re: %s" % ref if ref else "re: 用户经监控下发",
                instruction))
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(entry)
    print("已下发给 %s（%s）：它下个周期读邮箱时会执行并回执。"
          % (oid, OPS[oid]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="kind", required=True)

    r = sub.add_parser("research")
    r.add_argument("cell")
    r.add_argument("territory")
    r.add_argument("title")
    r.add_argument("--body", default="")
    r.add_argument("--priority", type=int, default=3)
    r.add_argument("--deps", default="")
    r.add_argument("--urgent", action="store_true")
    r.add_argument("--id", default="", help="人读的短名，如 merge-gate-509")
    r.add_argument("--lane", default="", help="赛道：campaign / paper")
    r.add_argument("--author", default="", help="自供者编号，如 RES-1")

    o = sub.add_parser("ops")
    o.add_argument("who")
    o.add_argument("instruction")
    o.add_argument("--ref", default="")

    a = ap.parse_args()
    if a.kind == "research":
        add_research(a.cell, a.territory, a.title, a.body, a.priority,
                     a.deps, a.urgent, a.id, a.lane, a.author)
    else:
        add_ops(a.who, a.instruction, a.ref)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
