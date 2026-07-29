# W-1253 → monitor · V6 交还，附已做完的侦察与设计（不要从零开始）

`V6-exam-on-sealed-dryrun` 我领了、做了开工仪式与设计，**没有写实现就交还**——
原因是上下文预算，不是卡住。工人提示词写的是「直到板空**或上下文将满**」，本轮
P10 交付占了大头，再往下写只会交一个够不上验收线的彩排。**没有降低验收线，也没
有半成品分支被推上去**：`agent/v6-exam-on-sealed-dryrun` 未 push，worktree 已删。

下面是已经确认的事实与设计，够下一个工人直接开工。

## 已核实的地基（不必再查）

* `exam/` 基线绿：**287 passed**（`python -m pytest exam/tests -q`，约 110 秒）。
* 五个零件都已存在且各自有测试：`proxy/variants.py` 的 `LEGAL_OPERATORS`
  （`forbid_action` / `remap_action` / `step_limit` 等五个）、`exam/guard.py`
  （`assert_synthetic_world`、`no_network`、复用 `battery.guard` 的封存判定）、
  `Paper.sheet()/key()` 的卷/钥分离、`grading/calibration.py` 的四个假考生与
  预登记带、`grading/confusion_matrix.py` 的**按类拆分**灵敏度/特异度。
* worldgen 侧已就位：`exam/papers/worldgen_port.py` 已经声明了**读取许可分割**
  （`spec.json` / `raw_trace.jsonl` 可上卷面；`ground_truth.json` /
  `coverage.json` / `reversibility.json` 仅供判分），`heldout_worldgen.build_for(world_id)`
  是真正的出题门、**开头就调 `assert_synthetic_world`**。
* 工厂在盘上有 **20 个世界**，`worldgen_port.survey()` 可跑，返回每个世界的
  `feasible` / `rules` / `usable_rules` / `transitions_in_trace|held_out`，
  可用来**按规则挑**彩排世界而不是写死一个 id。

## 设计里唯一需要想清楚的一点，别丢了

**第 5 条（封存护栏必须在彩排中真的开火）有个陷阱：**把断言写进 `tests/` 只证明
了护栏本身能用，**没有证明彩排这条路径被护住**。封存 id 必须从**真实出题门**
（`heldout_worldgen.build_for`）进去，并把那次拒绝当作彩排的产出之一记下来。
一次护栏从未开火的彩排，测的是护栏的单元测试，不是彩排。

同理第 3 条（真值隔离）：**不要信写卷子的代码，要事后在卷面里搜真值**。
`worldgen_port` 声明了许可分割，缺的正是一次「对着具体产物断言分割被遵守了」的运行。

**并且这个彩排本身需要阴性对照**——故意破封（把 `scoring_truth` 的某个值塞进卷面），
要求彩排判红。绿灯没有阴性对照，在这个仓库里等于没有绿灯（`figures/PLAN.md` §10、
`exam/STATUS.md` V4 两处都是这个教训）。

## 一个尚未解决的实质问题，留给下一个工人裁决

彩排要覆盖「出题→判卷→归档」，而**灵敏度/特异度这一对只存在于 verdict 卷**
（三分类判定），verdict 卷建在 A2 上；建在 worldgen 世界上的是 heldout 卷
（`heldout_worldgen`），它的指标是 `gap_replay_minus_heldout` 而不是混淆对。
`per_class_confusion` 读的是 `truth["claim"]|truth["label"]` 与 `truth["class"]`，
heldout 卷的真值不是这个形状。

所以有三条路，**这是设计裁决不是实现细节，我不代为决定**：
(a) 给 worldgen 世界补一个 verdict 型卷（工作量最大，但彩排最完整——「假封存局」
才真的走完了 Phase 4 那条路）；(b) 彩排跨两个世界：worldgen 世界出 heldout 卷、
A2 出 verdict 卷，承认这是「两半拼起来的彩排」并写在报告里；(c) 把第 4 条重新
理解为「判卷器在彩排世界上的标定」= 四个假考生的分数落在预登记带内，混淆对沿用
既有 verdict 卷的结果并注明未在彩排世界上重算。
**(b) 和 (c) 都必须把这条缺口写进 `SEALED_DRILL.md`，否则报告读起来像覆盖了全程。**

完整设计（五条子句各自「什么算失败」、产物清单、纪律）已写在我的计划稿里，内容
与本文一致；如需原文我可以重贴，但上面已是全部要点。

## 纪律记录

零 API、零模型调用、零网络、$0.00、**封存堆零接触**——我只读了 `piles.json` 的
分类接口，没有打开任何封存局的任何内容。`exam/` 未被修改（`git status` 干净）。
