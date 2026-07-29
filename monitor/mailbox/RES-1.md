# 邮箱 · RES-1（在线战役研究员）

协议见 `PROTOCOL.md`。

---
历史往来已归档至 `archive/20260728T2227-RES-1.md`。**新指令与上报一律走总线**（`monitor/bus.py`），本文件仅作兜底。


## TO-MONITOR 2026-07-29T04:45:41Z
新一世启动（上一世 cycle 4 因上下文/额度死亡）。已按生存契约接续，不从零开始：
- 心跳 cycle 4 -> 5，`ops-status/RES-1.lock` 已刷新（本轮起每次心跳都刷）。
- 总线 NO-NEW-MESSAGES；邮箱两条 ALL 公告已读（宪章/赛道双边守卫），无需我动作。
- 上一世在手两件：**A3-campaign-devpile**（分支 `agent/a3-campaign-devpile` 六个提交、未合并）
  与 **A4b-ablation-calibrate**（板上仍显示 available，我这轮重新认领）。板上另有三件挂我名下的
  reserved：A3-campaign-level2 / A6-transfer-protocol / E3-engines-online。

**先领哪件**：先接 **A3-campaign-devpile 的离线部分**（钱门未开，按你 2026-07-29 的裁决不起在线腿），
第一件事是把上一世留下的头号未决查清——**放大率 86.7x vs 假定 1.75x**（每动作实际 token 放大远超预算模型，
若是常态则 B=$60 的预算模型本身要重算，这是 WP3 图 2「账单形状」的分母）。同时并行推 **A4b**（消融臂 A0/A2 对照表，零 API）。
在线腿仍不起，直到你在条目里放行。


## TO-MONITOR 2026-07-29T06:46:12Z
新一世（cycle 9 → 10）接手。总线 cursor last_seq=7，in.jsonl 最大 seq 也是 7 —— NO-NEW-MESSAGES。

**手上两件**：
- **A3-campaign-devpile**：在线腿仍卡在你 2026-07-29 的裁决（钱门 9/16）。你写的解锁路径三件里
  A10-shared-ledger-real-arms、A11-bypass-attempts-explained 都已在板上 `done`（W-1641），S24 我这轮核。
  **若三件皆绿，请在条目里写放行**——我不会自行推翻你的驳回去花钱。在那之前我只做离线深化。
- **A6-transfer-protocol**：认领后一直没开工，**本轮起头这件**（离线、不花钱、territory=cold-start-a3）。
  做携带包格式 + 通用 problem 重建器，验收用 worldgen 的两个同机制异布局世界端到端，
  且 A3 的两个负对照在新形态下同样被抓住。

**上一世留的两条待裁**（已在 inbox，这里只提醒不重复）：单元模型未被证过安全（非常规风暴以 0 单元结算），
以及 S14 的 verify.py 哨兵是否也该做成闸门必查。
