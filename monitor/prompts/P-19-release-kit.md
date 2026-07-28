# P-19 · 释出包：任何陌生人一条命令复跑（WP10，Schema 地板对齐）

基准 `Theoria.md`（Phase 4 释出清单 + 「规模与开放性够到 Schema 的地板」）。开工仪式：读 `CLAUDE.md`、PARTNER_SYNC 尾十段、各领地 README，绿了开工。先出计划：`release/PLAN.md` 列出 Theoria.md 释出清单的每一项对应树上哪个路径、缺什么。
分支制：`agent/p19-release-kit` + 独立 worktree；push 分支不碰 master。领地：新建顶层 `release/`。

目标：把「可复现」从口号变成一条命令。

1. **artifact 清单器**：脚本枚举全部应释出物（账本、两本书四形态、Lean 证明、候选箱、探针日志、电池代码与结果、incident 台账、runs 档案），逐文件 sha256 落 `release/MANIFEST.jsonl`；对照 Theoria.md 释出清单逐项打勾/标缺。
2. **一条命令复跑**：`release/reproduce.py`——按领地依次重跑确定性产物（fixtures、engines、四形态编译、A0/A2 全环、battery 回算），与 MANIFEST 哈希比对，出 `REPRODUCTION_REPORT.md`。跑不了的（需 API/需真值）如实分级标注。
3. **REPRODUCING.md**：陌生人视角的复跑指南（环境、顺序、预期时长、每步的判据）。写完用一个**全新 subagent 当陌生人**照文档执行一遍，卡在哪改哪——文档失败改文档，不许口头解释。
4. 凭据与封存红线自检：清单器必须证明释出集里无 .env 值、无封存局帧数据。

前沿工具要求：清单/复跑/文档三线子代理并行；Stop-hook 式收工——`release/verify.sh`（复跑一遍 + 哈希全对 + 红线自检绿）不绿不收工；把「复跑验证」沉淀成 `.claude/skills/reproduce-check`；对抗措辞照用：让陌生人 subagent 『prove to me this works』。

留痕：边跑边落盘（`release/runs/<UTC>-p19/`），复跑报告的失败与成功同等归档。
收工：RUN_STATE + MANIFEST(prompt_id: P-19) + PARTNER_SYNC + push 分支。全程自主，不停下来问。
