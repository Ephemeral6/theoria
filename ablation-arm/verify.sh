#!/usr/bin/env bash
# 消融臂的收工闸门 —— 工单 A4a-ablation-build 点名要它，工作做完了、入口没造，
# 由监控补上（审计员第六维度：要求引用了不存在的东西）。
#
# 绿的含义：测试全过 + 能在 A0 与 A2 世界跑完全环 + 产出的账目带着与全量臂
# 并排比较所需的字段（意外计数、回路是否转起来、判决）。
set -euo pipefail
cd "$(dirname "$0")"

echo "== 1/3 测试套件 =="
python -m pytest -q

echo "== 2/3 全环实跑（消融臂的两个展品世界）=="
# 产物写临时目录：本臂有一条测试专门守「全环只在自己领地内写」，
# 闸门若往 artifacts/ 落文件，会把那条测试自己弄红（第一次跑就撞了）。
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT
# PYTHONIOENCODING 必须显式给：Windows 下重定向时 stdout 退回系统 GBK，
# 而报告里有中文，读的时候就会炸在一个与消融臂毫无关系的地方。
PYTHONIOENCODING=utf-8 python run_arm.py --world a0-base --json > "$OUT/a0.json"
PYTHONIOENCODING=utf-8 python run_arm.py --world a2-holed --json > "$OUT/a2.json"

echo "== 3/3 账目可比性 =="
VERIFY_OUT="$OUT" python - <<'PY'
import json
import os
import sys

out = os.environ["VERIFY_OUT"]
for name in (os.path.join(out, "a0.json"), os.path.join(out, "a2.json")):
    blob = json.load(open(name, encoding="utf-8"))
    # 找到那层带 verdict 的记录（结构随世界略有差异，按字段找而不是按路径找）
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "verdict" in node:
                found.append(node)
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(blob)
    if not found:
        sys.exit("闸门失败：%s 里没有任何带 verdict 的记录" % name)
    rec = found[0]
    holes = [k for k in ("verdict", "world") if k not in rec]
    if holes:
        sys.exit("闸门失败：%s 的记录缺 %s" % (name, holes))
    inner = json.dumps(rec, ensure_ascii=False)
    if "surprises" not in inner:
        sys.exit("闸门失败：%s 没有意外计数——消融臂的全部意义就是与全量臂"
                 "逐项对照，缺了它这次跑等于没跑" % name)
    print("%-10s verdict=%s world=%s"
          % (os.path.basename(name), rec["verdict"], rec["world"]))
PY

echo "VERIFY-OK ablation-arm"
