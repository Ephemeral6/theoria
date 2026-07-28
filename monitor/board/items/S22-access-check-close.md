priority: 3
cell: S22
territory: arc-recon
deps: none
lane: infra

# S22-access-check-close · 接入核查清尾：跨会话残留与配额口径

Phase 1「一件接入核查」还剩两项未结：(1) 全量跨会话残留——RESET 是否真的全量复位，用金丝雀序列跨会话跑两遍逐帧比对（动作预算 ≤12）；(2) 速率与配额的官方口径——browser-ops/TERMS.md 已有官方侧摘录，与 baseline-arms 的实测口径（失败 400 不计费、total_actions = 成功动作数）交叉核对后落一行结论进 arc-recon/README。这两项结掉，Phase 1 验收单就只剩三臂同壳那一项。
