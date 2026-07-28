# DRIFT-stop-hook-verify-gates-are-decoration

severity: medium
dimension: 要求引用了不存在的东西（AUDITOR.md 新增的第 6 维，本轮首次按它巡）

evidence: 审计区间 `ab99697..4d3f993`。

**决定性的一例——一件已交付合并的工单，它自己命名的收工闸门从未存在。**
- `monitor/prompts/C2-semantics-migrate.md:16` 逐字：「Stop-hook 收工：`a0-spike/verify.sh` = 测试全绿 + 四形态重生成一致。」
- `origin/agent/c2-semantics-migrate` 已合并（`84e9a26`，2026-07-28 15:55 +0800），交付很实：`a0-spike/probes/semantics_probe.py`（472 行）、`runs/20260728T040057Z-c2/` 带 `MANIFEST.json`（留痕正典已生效）、`ADVERSARIAL_REVIEW.md`、`tests/test_a0.py` +98 行、`theory/theory.dsl` +25 行。
- `a0-spike/verify.sh` **不存在**（`ls` 报 No such file；`git ls-files` 无此路径）。
- 也就是说：**收工闸门没有被绕过，它根本没被造出来；工单合并时没有任何东西发现这一点。**

**面上的量：** 全仓 `verify*.sh` 只有 `arc-recon/verify.sh` 一个真存在（另有 `engine-rig/bench/verify.py`、两个 `verify_readonly.py`，命名各行其是）。而 9 份工单点名了 `verify.sh` 形态的收工闸门，11 处「Stop-hook / 收工」行引用它：
`a0-spike/verify.sh`(C2)、`ablation-arm/verify.sh`(P-18)、`cascade/verify.sh`(P-20)、`figures/verify.sh`(P-21)、`freeze/verify.sh`(P-22)、`fuzzlab/verify.sh`(E1)、`release/verify.sh`(P-19)、`proxy/verify_spend.sh`(S3)。

**必须区分，否则这条会被读得比实际严重：** 上面八个里有六个的目标目录（`fuzzlab/` `figures/` `freeze/` `release/` `ablation-arm/` `cascade/`）**整个都还不存在**——那些工单在飞，verify.sh 是它们要交付的东西之一，不是它们要用的前提，**不算漂移**。真正落在第 6 维定义里的只有 C2 这一例：目录早就在、工作已交付合并、闸门被点名、闸门不存在。`proxy/verify_spend.sh` 与 `proxy/spend_gate.py` 属于同一形态但**已被 S3 工单认领**（`5fd1831` 把它提到板首），也不重复计。

顺带澄清一件我自己差点报错的事：`CONTRACTS/candidates_schema_v0.2.md` 与 `ic3_certificate_v0.1.md` 里的 `engines/ic3_pdr/`、`common/candidates.py`、`tools/run_all.py`、`interop/certificate_export.py` **全部存在**，只是写成了 engine-rig 轨道内的相对路径。契约干净，不是漂移。

claim: 「Stop-hook 收工」这个词在工单模板里被写了 11 次，而全仓只有一个 verify 脚本真存在，且已有一件工单带着未兑现的闸门合并进了 master。纪律看起来生效——每份工单都写着收工要过 verify——实际上没有任何一层在检查那个脚本是否存在、是否被跑过。这正是第 6 维要抓的形状：**不是有人绕过了闸门，是闸门从来没被装上，而所有人都以为装了。**

suggest:
1. C2 补一个 `a0-spike/verify.sh`（内容就是它工单里写死的那两条：`pytest` 全绿 + 四形态重生成一致），或者由监控判定 C2 的交付已由 `ADVERSARIAL_REVIEW.md` 等价覆盖、把工单里那行删掉。**两条路都行，含糊着放过去不行**——现在树上是「写了闸门、没装闸门」。
2. 合并时加一道极便宜的检查：工单文本里出现 `<path>/verify.sh` 而合并后该路径不存在 → `ci_merge` 记一行 warn。这条落在 `monitor/reflex.py` 的 `ci_merge` 里最省事，反射层现在实跑正常（本轮已复核 rc=0、两次真合并），有地方接。
3. 统一命名。现存三种：`verify.sh` / `verify.py` / `verify_readonly.py`。工单模板既然只写 `verify.sh`，就要么允许 `verify.*` 并在模板里写明，要么统一成一种——否则第 2 条的机器检查会把 `engine-rig/bench/verify.py` 这种真存在的误判成缺失。
