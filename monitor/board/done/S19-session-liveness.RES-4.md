priority: 2
cell: S19
territory: monitor
deps: none
lane: infra

# S19-session-liveness · 会话生死判据：区分「在睡」与「已关」

今天暴露的真缺口：App 会话在睡和已被关闭，从外部看长得一模一样——心跳文件的时间戳对两者没有区分力（OPS-R 睡 12 小时被我误判成掉线，我差点让用户白重开一个）。做两件：(1) 让契约要求会话在睡前写明「预计醒来时间」进心跳（wake_at 字段），探针据此区分「按计划睡着」与「该醒没醒」；(2) 补一条：换会话时未读的总线消息会被静默跳过（新会话的 cursor 从前任位置继续，前任没读的已在 last_seq 之下）——RES-1 今天就丢了三条指令。修法：cursor 记录已 ack 的 seq 集合而非单一 last_seq，重启时回读所有未 ack 的。
