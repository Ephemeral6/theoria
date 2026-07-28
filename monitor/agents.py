# -*- coding: utf-8 -*-
"""每个 agent 干了什么、干到哪了 —— 用人话，从 git 与工作板算出来。

监控页面的主视图问的不是「Phase 1 第几项绿了」，而是「我手下这些人各自
做了哪些事、进展如何」。这个模块回答后者：一个 agent 一张卡，卡上是
它交付过的东西（人话）、它此刻在做什么、以及它有多少产出。

数据只从可见接口来（隔离契约）：git 提交、分支、工作板的 claimed/done、
运维的心跳与报告文件。不读任何会话的对话。
"""

import json
import os
import re
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 工作板条目 → 人话（板上的 id 是坐标，卡片上要说人听得懂的）
PLAIN_ITEM = {
    "S2-canary-schedule": "把「金丝雀重放」做成每天自动跑的体检",
    "S3-spend-gate": "造出花钱的闸门（多个 AI 共用一份预算不再各算各的）",
    "V2-exam-on-worldgen": "让考卷跑在新造的 20 个练习世界上",
    "C1-worldgen": "世界工厂：7 类机制、20 个带标准答案的练习世界",
    "C4-deadlock-lean": "把死锁定理和不变量送进 Lean 做机器验证",
    "E2-fd-ladder-bench": "给专业规划器的三档性能定价",
    "E4-property-fuzz": "用 500 个随机世界轰炸六个引擎找 bug",
    "E6-engine-dividend": "量化引擎改进带来的实际红利",
    "P4-figures": "论文figures：把数据变成可复现的图",
    "P5-release": "释出包：陌生人一条命令复跑全部结果",
    "P6-paper-assembly": "把各处结果组装成论文正文",
    "S4-freeze": "起草大考前要封存的规则包",
    "S5-phase1-close": "Phase 1 收口：把地基验收单清干净",
    "A4-ablation-online": "对照版 AI（去掉证明能力）上线",
    "A4a-ablation-arm": "对照版 AI 的离线标定",
    "A6-transfer-protocol": "跨关迁移协议：把学到的知识带去下一关",
    "V3-battery-discrimination": "指标体系首次区分两组 AI 的能力差",
    "E3-engines-online": "让引擎在真游戏里供货（第二关）",
    "S6-merge-gate-509": "补上合并门的漏洞（六个目录 509 个测试从未跑过）",
    "A4a-ablation-build": "把对照版 AI 真正建起来",
    "A4b-ablation-calibrate": "对照版 AI 的离线标定",
    "C6-worldgen-mutate": "给世界工厂加「改一条规则」的变体生成",
    "A7-envelope-finish": "补齐对照组的成绩数据",
    "C7-dsl-v03-mentions": "语法 v0.3：把散落的提法收进契约",
    "P7-paper-section7": "论文第 7 节：相关工作",
    "A3-campaign-devpile": "开发堆在线战役：把 Theoria 臂推到退出条件",
    "P9-paper-to-submittable": "把论文推进到可投稿",
    "V4-exam-selftest": "考卷自检 + 出三类判决题（验判卷的人对不对）",
    "E5-cert-recheck": "证书独立复核器（不靠 Lean 一条路）",
    "P8-billshape-pipeline": "把论文「账单形状」图接上真数据管线",
    "S4-freeze-complete": "冻结清单 13 项补齐到可提交",
    "A6-transfer-protocol": "跨关迁移协议：把学到的知识带去下一关",
}

# 提交信息前缀 → 归属哪个 agent（人话名）
RES_META = {
    "RES-1": ("在线战役研究员", "常驻推进：Theoria 臂在真 API 上跑出结果（论文最大缺口）"),
    "RES-2": ("论文与释出研究员", "常驻推进：把已有结果写成能投出去的论文与释出包"),
}

OPS_META = {
    "OPS-A": ("漂移审计员", "每小时巡一遍全仓，专抓「说了没做」和「已经变绿却还报红」"),
    "OPS-B": ("浏览器专员", "需要真浏览器和登录态的活：官方条款、账户核查"),
    "OPS-M": ("合并裁判", "脚本合不动的冲突由它裁决；顺利合并早已自动化"),
    "OPS-R": ("回顾员", "从所有痕迹里挖跨轨道重复出现的失败模式"),
}


def sh(args, timeout=60):
    try:
        out = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=timeout)
        return out.stdout.decode("utf-8", "replace")
    except Exception:
        return ""


def board_state():
    done, claimed = {}, {}
    d = os.path.join(HERE, "board", "done")
    c = os.path.join(HERE, "board", "claimed")
    for f in (os.listdir(d) if os.path.isdir(d) else []):
        parts = f[:-3].split(".")
        if len(parts) >= 2:
            done.setdefault(parts[1], []).append(parts[0])
    for f in (os.listdir(c) if os.path.isdir(c) else []):
        parts = f[:-3].split(".")
        if len(parts) >= 2:
            claimed[parts[1]] = parts[0]
    return done, claimed


def task_running(name):
    out = sh(["schtasks", "/Query", "/TN", "TheoriaAgent-%s" % name, "/FO", "LIST"])
    return "Running" in out or "正在运行" in out


def ops_cards(meta=None, kind="ops"):
    cards = []
    for oid, (name, role) in (meta or OPS_META).items():
        path = os.path.join(HERE, "ops-status", "%s.json" % oid)
        beat, age = None, None
        if os.path.exists(path):
            try:
                beat = json.load(open(path, encoding="utf-8"))
            except Exception:
                beat = None
            age = int((time.time() - os.path.getmtime(path)) / 60)
        # 产出：审计报告 / 提案 / 提交
        reports = 0
        adir = os.path.join(HERE, "audit")
        if oid == "OPS-A" and os.path.isdir(adir):
            reports = len([f for f in os.listdir(adir) if f.startswith("DRIFT-")])
        idir = os.path.join(HERE, "inbox")
        if os.path.isdir(idir):
            reports += len([f for f in os.listdir(idir) if oid.lower() in f.lower()
                            or oid.replace("-", "").lower() in f.lower()])
        commits = len([l for l in sh(["git", "log", "--format=%s", "-200"]).splitlines()
                       if l.lower().startswith(oid.lower())
                       or (oid == "OPS-A" and l.startswith("audit:"))])
        cards.append({
            "id": oid, "name": name, "role": role, "kind": kind,
            "cycle": (beat or {}).get("cycle"),
            "state": (beat or {}).get("state", "未启动"),
            "age_min": age, "outputs": reports + commits,
            "note": (beat or {}).get("note", ""),
        })
    return cards


def worker_cards():
    done, claimed = board_state()
    ids = sorted(set(list(done.keys()) + list(claimed.keys())))
    cards = []
    for wid in ids:
        if wid.startswith("superseded"):
            continue
        finished = [PLAIN_ITEM.get(i, i) for i in done.get(wid, [])]
        now = claimed.get(wid)
        running = task_running(wid) if wid.startswith("W-") else False
        cards.append({
            "id": wid,
            "name": "研究工人" if wid.startswith("W-") else "手动会话",
            "kind": "worker",
            "finished": finished,
            "now": PLAIN_ITEM.get(now, now) if now else None,
            "running": running,
            "outputs": len(finished),
        })
    return cards


def collect():
    done, claimed = board_state()
    delivered = sorted({i for v in done.values() for i in v})
    return {
        "ops": ops_cards(),
        "standing": ops_cards(RES_META, "standing"),
        "workers": worker_cards(),
        "delivered_plain": [PLAIN_ITEM.get(i, i) for i in delivered],
        "delivered_ids": delivered,
        "in_progress_plain": [PLAIN_ITEM.get(v, v) for v in claimed.values()],
    }


if __name__ == "__main__":
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print(json.dumps(collect(), ensure_ascii=False, indent=2))
