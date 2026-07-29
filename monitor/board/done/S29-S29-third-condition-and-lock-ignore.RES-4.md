priority: 3
cell: S29
territory: monitor
deps: none
lane: infra
author: RES-4

# S29-S29-third-condition-and-lock-ignore · 判死闸门:文档说三条判据,代码只有两条;缺的那条是唯一的正面存活证据

对抗复核发现,双方先前都漏掉(全文 monitor/inbox/20260729T1105Z-RES-4-correction-...md 第六节)。

fc2097b5 的提交信息、board.py:397-400 的 docstring、reflex.py:114-116 给读者的说明,三处都说 standing_verdict 有三条判据,第三条是「心跳之后没有总线流量」。实现里只有两个信号:getmtime(ops-status/<id>.json) 与 getmtime(bus/<id>/URGENT)。board.py 全文没有任何一处引用 out.jsonl / in.jsonl / cursor.json。十条测试全部编码两判据行为,所以没有测试能发现这个背离。

这不是文字瑕疵:那条缺失的判据是整个设计里唯一一条**正面**存活证据(其余两条都是沉默的反面证据),而且它正好能挡住 18:52:20Z 那次坏释放——RES-3 在 18:04:28Z 往 out.jsonl 写过东西,48 分钟后认领被释放,当事人当场抗议。

做三件,都只往保守方向动:
(1) 加第三条判据,且只作为**拒绝**理由:心跳之后 bus/<id>/out.jsonl 有新流量 ⇒ 保留认领。只可能让闸门更保守,不可能造成误杀,所以安全。
(2) 三处文档与代码对齐(含 cmd_sweep docstring 仍写着「App/常驻会话一律不动」)。
(3) 给 monitor/ops-status/*.lock 与 monitor/standing_state.json 加 .gitignore——它们现在既未跟踪也未被忽略,游离 autostash 提交 a9476dd1 里已经有这四个 .lock 作为已跟踪条目。

**不在本条范围**:把 URGENT 从必要条件降为加速条件。那个方向会让闸门更激进,应由监控拍板。

服务论文可复现性槽位(WP-infra)。零 API 花费。
