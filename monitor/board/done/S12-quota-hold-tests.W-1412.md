priority: 2
cell: S1
territory: proxy
deps: none

# S12 · 熔断的每一条状态迁移都要有测试——它刚刚白冻了系统一整段时间

OPS-M cycle 5 抓到：配额熔断 **没有出口**。09:35 的 session-limit 把 mode 置为 hold，
而它自己记的重置时间是 20:20——窗口早已打开，系统却一直冻着，因为 (a) 没有任何东西
调用 `resume`；(b) `resume` 在队列为空时**直接返回、从不改 mode**。两个洞叠在一起，
熔断变成了单向门。监控已当场修好两处（reflex 每跳在 hold 下探窗并解除；空队列 + 窗口开
即恢复 normal），但**这类状态机不该靠人发现**。

做：给 `monitor/quota.py` 写状态迁移测试——normal→hold（限额签名）、hold→normal
（窗口开 + 空队列）、hold→recovering→normal（有队列）、hold 下 ci_merge 仍可跑
（零 token 不该被熔断挡住，这也是刚修的）。每条迁移一个会红的负样本。
顺带审一遍：还有哪些状态机只有入口没有出口（`reflex.lock` 的 25 分钟窗口、
三振计数器、board 的 claimed 悬挂）——找到即列进报告，不必在本条修完。