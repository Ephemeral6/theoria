# 邮箱 · RES-1（在线战役研究员）

协议见 `PROTOCOL.md`。

## TO-MONITOR 2026-07-28T10:49Z
RES-1（campaign 赛道）已启动，契约与 CLAUDE.md 已读，心跳已写
（`monitor/ops-status/RES-1.json`，cycle 0 → 转 working）。

**领到的第一件**：`V4-exam-selftest`（p1，territory=exam，lane=campaign）。
计划：判卷器标定（满分/零分假被试）→ 三类判决题各一题 + 构造性依据 →
灵敏度/特异度矩阵 → 作弊者 subagent 对抗验收。零 API、零封存堆接触。

**一条给监控的事实**：我的主线 `A3-campaign-devpile`（p1, lane=campaign）
现在**领不到**——它的 territory `theoria-arm` 被 `E3-engines-online`（W-1521）
占着，board 的 territory 互斥把它从候选里滤掉了，`list` 的 available 段里不显示、
blocked 段里也不显示（blocked 只统计 deps），所以从板面上看它像凭空消失了。
不需要你现在做什么；E3 一 done 我就接。若 E3 长时间不落地，请考虑是否要把
A3 的 territory 与 E3 拆开（例如 E3 只写 `theoria-arm/engines/`），否则论文
WP3 这条 20% 权重的主线会一直排在别人后面。
