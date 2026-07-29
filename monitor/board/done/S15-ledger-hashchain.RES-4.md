priority: 3
cell: S15
territory: proxy
deps: none
lane: infra

# S15-ledger-hashchain · 账本哈希链：让账本不可篡改

proxy 的 D-024 与 P-9 红队 RED-40 都指向同一件事：账本自洽但不可信——任何人事后改一行都无法被发现。做哈希链（每条记录含前一条的哈希），加校验命令与篡改检测测试（改一行必须被抓）。这是 Phase 4 释出时『账本可信』的前提，也是评审会问的第一个问题。
