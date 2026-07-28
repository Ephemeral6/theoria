priority: 3
cell: P5
territory: release
deps: none
lane: paper

# P5 · 释出包：陌生人一条命令复跑（Schema 地板对齐）

清单器枚举全部应释出物（账本、两本书四形态、Lean 证明、候选箱、探针日志、电池代码与结果、incident 台账、runs 档案），逐文件 sha256 落 release/MANIFEST.jsonl，对照 Theoria.md 释出清单逐项打勾/标缺。`release/reproduce.py` 按领地重跑确定性产物并与哈希比对，出 REPRODUCTION_REPORT.md，跑不了的（需 API/需真值）如实分级。REPRODUCING.md 写完后**派一个全新 subagent 当陌生人**照文档执行一遍，卡住即改文档不改人。红线自检：释出集内无 .env 值、无封存局帧数据。
