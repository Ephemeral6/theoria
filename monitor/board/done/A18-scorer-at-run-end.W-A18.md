priority: 1
cell: A18
territory: theoria-arm
deps: none

# A18-scorer-at-run-end · 跑完一局即打分——p1-scorer 欠的最后一半

Phase 1 五层 (5) 的验收词是「账本分数与 scorecard 对账相等」加
Theoria.md:371 的「跑完一局即打分」。前一半已处处成立：monitor 复算 37 run
过冻结打分器 **26 PASS / 0 FAIL / 11 丢卡**（含 theoria 四条真腿全过，
`monitor/runs/2026-07-31T170455Z-P1REPLAYLIVE/score_corpus.json`）。
后一半从未发生：没有任何臂 harness 在 run_end 调过打分器，唯一经
`proxy/runner.py` 的活局在 run_end 前崩（S31）。事后批扫正是 371 禁的口径。

做三件（全在 theoria-arm 领地）：

1. `harness/run.py` 在 run_end 后调 `proxy.scoring.score_run`（正式路径**不带**
   `--no-incident --no-artifact`——对账失配本该报 incident；那两个旗标是审计
   专用，见 `proxy/DELIVERY_RULING.md` §5 的六条重复 incident 前车之鉴），
   并把对账判定写进 `runs/<id>/` 归档。
2. 顺手把 `DELIVERY_RULING.md` §4 axis 1 点名的**纯配置缺口**补上：
   `harness/run.py` 已收 `ledger_path` 参数而 `main()` 从不转发——转发它，
   让下一条真腿计费落共享账本（p1-same-shell axis 1 的 theoria 份）。
3. 负样本测试：塞一条分数对不上的 mock run，断言 run_end 打分把它标红。

验收：mock 整局跑通含 run_end 打分；下一条**真腿**（不由本件出资，等既有
战役续费）自然产出「跑完即打分」的第一条活证据。零花费即可交付本件。
绿了之后 `monitor/spec.py` p1-scorer 的收窄裁决问题自动消失——两半都真了。
