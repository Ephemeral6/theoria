priority: 2
cell: S3
territory: theoria-arm
deps: none

# S8 · 给花过钱的那条臂补留痕

探针视野打开后（TERRITORIES 改为从树上推导）第一眼就看见：`theoria-arm` 有 11 个
run 目录，**只有 4 个带 MANIFEST.json**——而这是唯一真花过 ARC 动作配额的臂。
Phase 4 要靠 runs/ 档案追回每一个数字，缺留痕的花费在释出时是无法回溯的。

做三件：(1) 逐个 run 判定性质——真实验 / pytest 夹具 / 中途夭折，夹具类移出 `runs/`
（它们不该混在档案里），真实验补 `MANIFEST.json`（必填 prompt_id / branch /
base_commit / utc；花过配额的补上动作数与 scorecard 引用，可从账本反查）；
(2) 无法回溯的如实标 `provenance: incomplete` 并写明缺什么——**不许编**；
(3) 在 `theoria-arm/RUN_STATE.md` 写一段「哪些 run 可用于论文、哪些只能作过程记录」。

注：`baseline-arms` 同样零 `runs/` 档案且同样花过钱，但它此刻有会话在跑，
留给它自己的下一件工单清偿；本条只管 theoria-arm。
