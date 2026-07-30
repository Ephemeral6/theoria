priority: 2
cell: S20
territory: monitor
deps: none
lane: infra

# S20-gate-negative-sample · 闸门验收通用要求：每个闸门必须附一个会让它变红的负样本

审计员给 S13 的附带建议，采纳为通用要求：**每个新装的收工闸门都要附一个能让它变红的负样本**，否则装了等于没装——这与我给 cmd_sweep 提的要求是同一条。做三件：(1) 在 monitor/gates.py 的判据里加一列「有无负样本」，无负样本的闸门标为 decorative；(2) 给现有闸门（exam/worldgen/proxy/ablation-arm/monitor）各补一个负样本测试；(3) 写进 METHOD.md 的收工闸门一节与工单标准尾——新建闸门时负样本是验收的一部分。判据来源：漂移第 7 维第二句「这个检查还有没有会让它变红的负样本」。
