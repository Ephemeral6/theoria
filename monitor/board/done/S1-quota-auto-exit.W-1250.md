priority: 1
cell: S1
territory: proxy
deps: none

# S1-quota-auto-exit · 配额熔断加自动出口

OPS-M 两轮连报、今天实际造成六个工人停摆两小时：monitor/quota.py 的 hold 是单向闩——check() 会把 mode 置 hold，但没有任何自动路径调用 resume()，窗口恢复后舰队仍冻着，直到人工干预。做三件：(1) reflex 每跳在 hold 态下先 ping，OPEN 即自动 resume（错峰、半池起步）；(2) resume 后把 requeue 里的工人按优先级重发，并在 reflex.log 记明是自动恢复；(3) 补测试：模拟 hold→窗口恢复→自动出闩的全链路，断言不需要人工介入。注意 quota.py 的 ping 会花一次 haiku 调用，hold 期间的 ping 频率不要高于每 20 分钟。
