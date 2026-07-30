# -*- coding: utf-8 -*-
"""监控与 App 会话之间的消息总线 —— 可确认送达、可配对回复、可打断。

监控侧：
    python -m fleetkit bus send RES-1 order "把 A3 战役推进到第二关"
    python -m fleetkit bus send RES-1 urgent "立刻停手，配额要满了"
    python -m fleetkit bus status                # 谁读到哪了、谁欠我回复

会话侧（写进契约，每个循环都跑）：
    python -m fleetkit bus read RES-1            # 取未读；有 urgent 会置顶
    python -m fleetkit bus ack RES-1 7 "已照办：分支 agent/xxx 已 push"
    python -m fleetkit bus say RES-1 "板上这条的前提已被树推翻，建议作废"

为什么不是原来的 markdown 邮箱：邮箱只能追加，我无法知道它**读没读**，
也无法把一条回复对上一条指令。总线用三个文件解决：

    bus/<AGENT>/in.jsonl     监控写，只追加，每条带 seq
    bus/<AGENT>/out.jsonl    会话写，只追加，回复带 ref=seq
    bus/<AGENT>/cursor.json  会话每次读完写，记 last_seq —— 这就是送达回执，
                             它的修改时间同时是「最后一次露面」的证据

urgent 类消息额外落 `bus/<AGENT>/URGENT`（一个存在即真的空文件），
会话在**每个工具调用间隙**都可以零成本 stat 一下它——这是打断通道。
"""

import argparse
import datetime
import json
import os
import sys
import time

#: Overridable so a test -- or a second fleet on the same machine -- points
#: at its own tree instead of inheriting the one this file sits in.
HERE = os.environ.get("FLEET_HOME") or os.path.dirname(os.path.abspath(__file__))
BUS = os.path.join(HERE, "bus")
AGENTS = ["OPS-A", "OPS-B", "OPS-M", "OPS-R",
          "RES-1", "RES-2", "RES-3", "RES-4"]


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def paths(agent):
    d = os.path.join(BUS, agent)
    os.makedirs(d, exist_ok=True)
    return (os.path.join(d, "in.jsonl"), os.path.join(d, "out.jsonl"),
            os.path.join(d, "cursor.json"), os.path.join(d, "URGENT"))


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def append(path, obj):
    with open(path, "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def cmd_send(agent, kind, body, ref=None):
    inbox, _out, _cur, urgent = paths(agent)
    seq = len(read_jsonl(inbox)) + 1
    append(inbox, {"seq": seq, "ts": utc(), "kind": kind, "body": body,
                   "ref": ref})
    if kind == "urgent":
        open(urgent, "w", encoding="utf-8").write(str(seq))
    print("已发给 %s：#%d（%s）" % (agent, seq, kind))
    return 0


def cmd_read(agent, mark=True):
    inbox, _out, cursor, urgent = paths(agent)
    rows = read_jsonl(inbox)
    last = 0
    if os.path.exists(cursor):
        try:
            last = json.load(open(cursor, encoding="utf-8")).get("last_seq", 0)
        except Exception:
            last = 0
    unread = [r for r in rows if r["seq"] > last]
    urgent_first = [r for r in unread if r["kind"] == "urgent"] + \
                   [r for r in unread if r["kind"] != "urgent"]
    if not urgent_first:
        print("NO-NEW-MESSAGES")
    for r in urgent_first:
        print("--- #%d [%s] %s" % (r["seq"], r["kind"], r["ts"]))
        print(r["body"])
        if r.get("ref"):
            print("(回应你的 #%s)" % r["ref"])
    if mark and rows:
        json.dump({"last_seq": rows[-1]["seq"], "read_at": utc()},
                  open(cursor, "w", encoding="utf-8"))
    if os.path.exists(urgent):
        os.remove(urgent)
    return 0


def cmd_ack(agent, seq, body):
    _in, out, _c, _u = paths(agent)
    append(out, {"ts": utc(), "kind": "ack", "ref": int(seq), "body": body})
    print("已回执 #%s" % seq)
    return 0


def cmd_say(agent, body, ref=None):
    _in, out, _c, _u = paths(agent)
    append(out, {"ts": utc(), "kind": "say", "ref": ref, "body": body})
    print("已上报")
    return 0


def cmd_status(agent=None):
    """监控视角：每个会话读到哪了、欠我几条回执、多久没露面。"""
    for a in ([agent] if agent else AGENTS):
        inbox, out, cursor, urgent = paths(a)
        rows = read_jsonl(inbox)
        outs = read_jsonl(out)
        last = 0
        seen = None
        if os.path.exists(cursor):
            try:
                last = json.load(open(cursor, encoding="utf-8")).get("last_seq", 0)
            except Exception:
                pass
            seen = int((time.time() - os.path.getmtime(cursor)) / 60)
        acked = {r.get("ref") for r in outs if r.get("kind") == "ack"}
        owed = [r["seq"] for r in rows
                if r["kind"] in ("order", "question") and r["seq"] not in acked]
        print("%-6s 已发 %2d · 已读到 #%-2d · 欠回执 %s · 上报 %d 条 · %s%s"
              % (a, len(rows), last, owed or "无", len(outs),
                 ("%d 分钟前露面" % seen) if seen is not None else "从未读取",
                 # U+26A0 是 GBK 编不出来的字符，而这行是给 cp936 控制台印的：
                 # 只要有一个 URGENT 没取，status 就会以 UnicodeEncodeError
                 # 死在半路——正好死在最需要它说话的时候。
                 "  URGENT 未取" if os.path.exists(urgent) else ""))
    return 0


def cmd_outbox(agent=None, n=10):
    """监控视角：读它们说了什么（未读的在前）。"""
    for a in ([agent] if agent else AGENTS):
        _in, out, _c, _u = paths(a)
        rows = read_jsonl(out)[-n:]
        if not rows:
            continue
        print("=== %s ===" % a)
        for r in rows:
            ref = (" →#%s" % r["ref"]) if r.get("ref") else ""
            print("[%s]%s %s" % (r["kind"], ref, r["body"][:300]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("send"); s.add_argument("agent"); s.add_argument("kind")
    s.add_argument("body"); s.add_argument("--ref")
    r = sub.add_parser("read"); r.add_argument("agent")
    a = sub.add_parser("ack"); a.add_argument("agent"); a.add_argument("seq")
    a.add_argument("body")
    y = sub.add_parser("say"); y.add_argument("agent"); y.add_argument("body")
    y.add_argument("--ref")
    st = sub.add_parser("status"); st.add_argument("agent", nargs="?")
    ob = sub.add_parser("outbox"); ob.add_argument("agent", nargs="?")
    ns = ap.parse_args()
    if ns.cmd == "send":
        return cmd_send(ns.agent, ns.kind, ns.body, ns.ref)
    if ns.cmd == "read":
        return cmd_read(ns.agent)
    if ns.cmd == "ack":
        return cmd_ack(ns.agent, ns.seq, ns.body)
    if ns.cmd == "say":
        return cmd_say(ns.agent, ns.body, ns.ref)
    if ns.cmd == "status":
        return cmd_status(ns.agent)
    if ns.cmd == "outbox":
        return cmd_outbox(ns.agent)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
