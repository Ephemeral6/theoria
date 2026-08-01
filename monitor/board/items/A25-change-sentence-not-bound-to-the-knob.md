priority: 2
cell: A25
territory: theoria-arm
deps: none
spend: none

# A25-change-sentence-not-bound-to-the-knob · 一轮宣称改了什么，和它真正转发了什么，至今没有被绑在一起

证据是轮记录自己招的。`_rounds/20260801T001851Z-R1b/round.json`：

> `"change": "goal_protocol=propose, ACTUALLY APPLIED this time (R1 recorded the same sentence and forwarded no flag)."`

对照 `_rounds/20260731T231654Z-R1/round.json`：`change` 写着
`goal_protocol=propose`，而整份记录**没有 `knobs` 键**。R1 因此是一轮
「记着自己做了干预、实际跑的是基线」的确证轮——四条腿的钱照花
（R1 合计 $15.211947）。

`--knob` 已经补上了（`round.py:136-139`，`cmd += list(knobs or ())`，
`round.json` 落 `knobs`），所以**机制在了**。缺的是绑定：今天仍然可以写
`--change "goal_protocol=propose"` 而一个 `--knob` 都不给，记录照样生成、
照样看起来是一轮干预。`round.py:175-177` 的注释自己说 `knobs` 列表「是唯一能
抓住一个描述了未发生干预的 `--change` 的东西」——它能抓，但没有人在抓。

要做的：一个检查器（`round.py` 内联或姊妹工具都行），把 `change` 句子里出现的
旋钮名与 `knobs` 里实际转发的旗标对上；对不上就拒绝生成记录，或至少在
`round.json` 里落一条显式的 `change_knob_mismatch`。旋钮名的词表用
`harness/run.py` 已有的那四个开关（`--goal-protocol` / `--probe-economy` /
`--desk-diet` / `--frontier`），不要正则猜。

验收：新检查器跑过**归档里的两份真记录**——R1 必须红，R1b 必须绿。
历史自己提供了这个对照，不需要造。

负样本：`--change` 里根本不提任何旋钮名的一轮（例如只换了种子书）必须**通过**，
不能变成「每轮都必须带 knob」的新枷锁；以及 `--knob` 给了、`change` 不提的
一轮必须红——两个方向都要被看见说过话。
