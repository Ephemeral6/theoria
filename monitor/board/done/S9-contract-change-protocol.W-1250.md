priority: 1
cell: S1
territory: proxy
deps: none

# S9 · 契约改动必须先通告：一次悄悄的字段封闭吃掉了 $2.695

W-1521 报的实盘事故（已在其轨道修完，协议部分它做不了）：`LEDGER_FORMAT.md` §4 把
`model_call` 的字段集**封闭**，而 P-8 早已在用 `beat`/`proxied`/`transport` 五个字段
——`beat` 正是让**约束 8 可以从账本上核**而不是只写在散文里。封闭发生在 P-8 落地之后，
在线臂按设计把 `proxy/` 当库 import，于是**这次改动在它从未碰过的提交上悄悄到达**。
后果：第一次 desk 调用付了钱（$2.695），`model_call` 记录数 = 0，回复被丢弃。
若不是它当场停跑，$15 会照这个样子烧完。

做三件：(1) `proxy/canon.py` 的字段集校验改为**加法安全**——未知字段告警并保留，
不拒收（拒收让付过钱的记录彻底丢失，这是最糟的失败模式）；(2) 把 `beat`/`proxied`/
`transport`/`label`/`proxy_gap` 正式纳入 `LEDGER_FORMAT.md` §4（它们有真实用途，
不是随手加的）；(3) 写 `proxy/CONTRACT_CHANGES.md`：凡收紧共享格式的改动，必须先在
PARTNER_SYNC 发一段通告并等一个周期，且给出兼容窗口——**收紧是破坏性变更，加字段不是**。