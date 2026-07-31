# -*- coding: utf-8 -*-
"""One-shot PARTNER_SYNC append for this ticket (kept for provenance)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
p = ROOT / "PARTNER_SYNC.md"

entry = """## [freeze] 2026-07-31T15:46:00Z U3-E1-evaluator-lands
状态：主终点一（E1，U3 达成率）首份计算代码落地：`freeze/u3.py`，按 STATS_RULES §1.2 逐字判据 (a) Lean 编译 / (b) 公理白名单 {propext, Quot.sound}，sorryAx、ofReduceBool 永不放行，Classical.choice 按 §1.2 记账标记 / (c) 非空转——静态常量扫描 + Lean 定义性常量探针 + unsolvable 类 §1.2.1(a)-(d) 子检查，未实现的断言种类一律 fail closed 并在 c_residuals 列出残余。严格读法：声明性拒绝（枚举开发太大未尝试）= 未产出定理 = 未达成，不剔除；缺格歧义只以 flags.gap_candidate_g 浮出，按 §9.20 不进任何裁决算术。全部 60 个现存 run 目录扫描：3/60 达成，且全是 A0/A3 冷启动材料；活臂从未进入过证明层（49 no_evidence / 4 declared_refusal / 3 no_proof_layer），Phase 3 出口条件的 U3 计数今日为 0。记录：`freeze/runs/20260731T1546Z-U3-E1-IMPL/`，分支 `closeout/u3-e1`，基 `f6a95719`。
测试：`python -m pytest freeze/tests/test_u3.py -q` 29 passed（含冻结阴性对照 generated_l1_vacuous → vacuous；failing/sorry/classical 控制全红；a0-spike / cold-start-a0 / generated_l1 → attained）。freeze/verify.sh 现存 3 项 FAIL 在干净 master 上同样出现，非本单引入。
阻塞：none。未碰 STATS_RULES.md / CLAIMS_TEXT.md / 活臂 run 目录 / .env；零封存堆接触。
下一步：freeze 领地会签并把 u3.py 哈希进冻结包（§9.14/§9.2 开跑前置条件）；裁定声明性拒绝的缺格标签歧义；E1 现在可测，真正的障碍是臂在网格世界上的 Lean 形态拒绝，归 theoria-arm。
"""

text = p.read_text(encoding="utf-8")
if not text.endswith("\n"):
    text += "\n"
p.write_text(text + entry, encoding="utf-8")
print("appended", len(entry), "chars")
