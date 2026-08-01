# RUN_STATE — P1PUSH4 · 所有者裁决落账 + 剩余四项的推进工单

分支 `closeout/p1-owner-ruling`，基 = 开工时最新 master（含 P1REPLAYLIVE 合并）。
本件是裁决与派单，不修任何领地代码；零 API、$0.00、零封存堆接触、无凭据值。

## 一 · 所有者裁决落账（p1-proxy-model 封存）

所有者 2026-08-01 会话内原话：「我这个全部都走的claude账号额度，剩下四个继续推」。
读法：不另配 ANTHROPIC_API_KEY，模型调用走 Claude 订阅额度——正是 D-P8-002 的
claude -p 订阅传输，由所有者认可为常态运行事实。据此执行 P1READJ
（2026-07-31T15:53Z）下一步的既定 else 分支「否则本项封存」：

* `monitor/spec.py` p1-proxy-model 注记追加【所有者裁决·2026-08-01】段：
  DUAL_PROXY §4 六步单转休眠档（非删除，出资改判即原样复活）；
  论文用 `verify-lab/DUAL_PROXY.md:122-134` 三句话原文。
* 板色保持 partial：封存 ≠ 达成，Theoria.md:290 原文未改；本条从开放决策点
  变为已裁的诚实披露。
* 若所有者本意并非如此，一句话即可回滚——本段与注记都写明了触发词。

## 二 · 四张推进工单上板（monitor/board/items/，generic 可领）

| 件 | 领地 | 推的是 | 要点 |
|---|---|---|---|
| A18-scorer-at-run-end | theoria-arm | p1-scorer 后一半 | run_end 调冻结打分器 + 转发 ledger_path（DELIVERY_RULING §4 axis 1 纯配置缺口）+ 负样本 |
| A19-bare-cc-seal-split | baseline-arms | p1-seal-test 左合取 | 照 b375a9bd 先例拆分凭据出臂进程；GAP-5 清账；恢复飞行资格 |
| A20-model-side-bypass-negative | proxy | p1-seal-test 右合取 | 订阅传输读法下的模型侧负样本：无供应商凭据变量 + 无凭据直连必 401 |
| A21-ablation-arm-name | proxy | p1-same-shell 分母 | proxy.ledger.ARMS 加 ablation 名（D-AB-004 的前提），inbox 通知属主 |

四件全部零花费可交付；A18 的活证据由既有战役的下一条真腿自然产出，不另出资。
`board.candidates()` 复算确认四件可领（A18/A19 priority 1，A20/A21 priority 2）。

## Inputs（全部只读）

proxy/DELIVERY_RULING.md §4/§5、baseline-arms/STATUS.md GAP-5、
ablation-arm/DECISIONS.md D-AB-004、verify-lab/DUAL_PROXY.md §3、
monitor/board/done/A10*（item 格式先例）、P1REPLAYLIVE 留痕（score_corpus.json）。

## Gate outputs, verbatim

* `python monitor/scan.py` exit 0，逐字
  `[2026-08-01 10:38:46] monitor/index.html written — Phase 1: 12/16 green`
  （绿数不变——裁决不改色，属预期）。
* `python -m pytest`（monitor）：**525 passed, 2 xfailed**，exit 0，与基线同。

## 验收例外披露（--allow）

同 P1REPLAYLIVE：spec/state/index 三路径命中的封存 id 皆基线既有
（p1-a2 展品标签、p1-cut 的 F-11 隔离登记），本分支加行计数为零；
三文件职责含登记污染裁决。id 本体不在此复写。

## 收口结论

剩余四个 partial 全部从「文档化的堵点」变成「板上可领的活」或「已裁的封存」：
p1-proxy-model 封存（所有者裁决在案）；p1-scorer → A18；p1-seal-test → A19+A20；
p1-same-shell → A18(axis1)+A21（axis 2 的活局在既有战役路径上）。钱门 12/16
照字面仍不满足，但不再有无主之欠。
