# S31 真臂探针已打：双轴见证，2 动作，$0.00

rung 1，2026-07-31T12:19Z，spec.py #9 先登记后动手。共享账本
`proxy/var/ledger.jsonl` 新增 `run_start`（env_upstream =
https://three.arcprize.org）与 `env_step`（arm = bare_cc）——
2026-07-29 审计红下的那句「共享账本零真臂记录」自此不再为真。

花费：2 次 ARC 请求、$0.00、预留 `res-6ff9e720…` 干净释放（上限
$0.05/10 动作）。坠机为 rung 1 回环 MockProvider 在 decide 时断连，
发生在两条见证落笔**之后**，不涉真实链路；`credential_in_body` 事故
裁定为 card_id GUID 与钥匙同形的形状撞车（值命中会拒绝而非放行）。
详见 `proxy/runs/20260731T104757Z-S31/FIRED.md`。

两件移交：(1) proxy 领地——body 守卫该认识 card_id 字段的 GUID，
否则每次 RESET 都要空响一次；(2) mock 供应端的断连缺陷，rung 1 复打
前修。三臂常态接线（DELIVERY_RULING §4）仍开放。
