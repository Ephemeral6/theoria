# RES-3 → 监控：两条查实的缺陷，都不在我能改的领地

2026-07-29T11:45Z，cycle 52。两条都已独立复核（不是 subagent 转述），请转给该改的人。

---

## 一、`release/MANIFEST.jsonl` 对 14 条 `figures/` 路径已陈旧（**这是 V20 真正的红**）

我在跑 `V20-figures-pipeline-red`（territory `figures`）。工单列的三条缺陷里，
**头两条已经过期**：

* `build_all.py` 现在退 0，`fig06_concept_timeline.py` 的 `EXPECTED_IDS` 已含 E-08/E-09；
  工单的预测在一个约 14.5 小时的窗口内是对的，`abd8d0cb` 已把它补上。
* `SOURCES.sha256` 今天是 **61 条、0 漂移**，不是「50 条里 13 条漂移」。
  那个 50/13 对得上两代之前的清单（`9239eb1c`），拿今天的字节重放得到 11 条，
  也对不上 13。**工单这两条应当作已闭合，不要再派人去修。**

但同一次核查查出另一处**当前真红**，工单没提：

```
release/MANIFEST.jsonl 里 figures/ 开头的行 57 条，其中 14 条哈希与盘上字节不符
```

逐条（全部是 DRIFT，无缺失）：`figures/SOURCES.sha256`、`figures/check_coverage.py`、
`figures/verify.sh`、`figures/fig06_concept_timeline.py`、
`figures/csv/fig02_bill_shape.csv`、`figures/csv/fig06_concept_timeline.csv`，
以及 fig02/fig06 的 light/dark × svg/png 共 8 张图版。

**裁决很清楚，不含糊**：`figures/verify.sh` 的 gate 6 会把**已提交的树**与一次全新构建
逐字节比对，今天它是绿的——也就是说盘上的图版就是源该产出的图版。所以是
**释出清单该重生成，不是图该重做**。`release/MANIFEST.jsonl` 上次重生成在 `6b095965`，
在此后两次图表重建之前。

我没有动它：`release/` 不是本条目的 territory。**这条服务 WP10（释出包可复现），
优先级不低——释出清单声称的哈希对不上盘，正是释出包最不该出的那种错。**

复核命令（我自己跑的，不是转述）：

```
python -c "import json,hashlib,os; ..."   # 逐行比对 sha256
# → figures rows: 57 stale: 14
```

---

## 二、`win_tighten` 在无 score 的游戏上会退化成「彻底禁胜」（territory `proxy/`）

这是 `V6-exam-on-sealed-dryrun` 封存彩排跑出来的，全文见
`exam/SEALED_DRILL.md` §4。

冻结算子库 `proxy.variants.LEGAL_OPERATORS` 的卖点是**与游戏无关**——
包裹层能对任何托管游戏做的改写。把五个算子全套到一个不是为它们设计的世界上，
四个活了下来，`win_tighten` 没有：

`proxy/variants.py:243-252` 把 `have is None` 与 `have < needed` 当成同一件事。
worldgen 世界不记分（轨迹只有 `{t, frame, action, win}`），于是 `score` 恒为 `None`，
于是**每一个 WIN 都被改写成 NOT_FINISHED，不论 require 的值是多少**。
它不是把胜利条件收紧了，是把胜利条件取消了。

三点，按要紧程度：

1. **不是 `proxy/variants.py` 的 bug。** 把「缺失」读成「未达标」是保守的那一侧；
   反过来会让一个从不报分的游戏白拿收紧后的胜利。**缺陷在于这个塌缩是静默的。**
2. **一局封存游戏报不报分，是协议问题不是机制问题，不破封存就能知道。**
   所以建议：**在对封存局用 `win_tighten` 之前先查它报不报分**，
   并让 `win_tighten` 把「缺失」与「未达标」分开，第一次因「缺失」改写 WIN 时出声。
3. **附带**：冻结的证书文法（`invariant` / `cut_set` / `counting`）没有一种形式
   能表达「因为游戏不报分所以胜利条件不可满足」，所以这道题**连真值自己都拿不满分**
   （神谕上限 0.95 而非 1.0）。这条是否要补第四种证书形式，请裁决——
   我在彩排里把它算出来并点名，没有假装它是 1.0。

我没有改 `proxy/` 下任何文件。
