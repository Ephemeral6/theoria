# W-1671 · V22 收工附带的两条移交（都不在 battery 领地内，本件一字未动）

工单：`V22-battery-separated-zero-metrics`（cell V3，territory battery）。
分支 `agent/v22-battery-separated-zero-metrics` 已推。零 API、零封存堆接触。

下面两条是干活路上撞到的，**都不属于 battery，我没有动**，但都会让别人读错数。

## 1. `battery/artifacts/gaming_audit.json` 是陈的，而且已经骗到人了

committed 的这份产物仍写着 **9 条主表指标**（E2 E3 K11 K12 K7 M3 M6 P3 P4），
与现行代码 `battery.audit.gaming.tier_of` 在**这 9 条上全部不一致**。重算一遍
得到的是 `main = []`，与 `METRICS.md` 自己生成的 `**Main table (0):**` 一致，
也与 `STATUS.md` B17 记的「主表 → 0」一致。**那份产物停在 B17 之前。**

**为什么这条值得单独提**：本轮一个对抗复核 subagent 照这份产物读出了
「还剩 P3 一条主表指标有配对数据」，并据此写了一段论证。现行答案是**零**。
它不是读错了，是产物和代码不一致，而**产物看起来比代码更权威**。

我在 `battery/METRICS.md` 的生成段里用的是 `tier_of`（活代码），所以交付物
本身是对的；但只要那份 json 还躺在 `artifacts/` 里，下一个人还会踩。

## 2. committed 的 capability spectrum 在干净检出里重算不出来

`battery/artifacts/capability_spectrum.json` 的 `input_digests` 点名四个 shard
账本（`ledger.{ar25,g50t,sk48,tn36}.jsonl`），**在干净检出里一个都不存在**
（未被跟踪）。反过来，磁盘上确实有的 11 个 `ledger.a7-*` shard 贡献了
**17 个 run_id，在 committed 产物里一个都没有**——它们是在产物最后一次写盘之后
才提交的。

后果：**今天重算吃进去的是与 committed 数字不同的一批 run。** 本次
`battery/verify.py` 第 2 道闸实测 48 run，产物是 95。

`battery/verify.py` 的 `shipped_note` 已经把**条数差**打成 note（那是设计如此，
未跟踪输入本来就该缺），但**digest 对不上这件事没有任何东西在查**。这两件事
不一样：前者是「这台机器上材料少」，后者是「产物声称的输入和现存的输入不是
同一批」。

## 3. 顺带一条，属于 battery 但我按预注册纪律没改

`discrimination_arms.json` 的 `confounds` 记了 harness 混杂与「上游已发布材料」，
**没记「强臂其实是三个模型的混合」**：`claude_fable_opus` 在 ar25/g50t 用
`claude-opus-4-8`、在 sk48/tn36 用 `claude-fable-5`，另四次运行是 `gpt-5.6-sol`。
**这条梯度上的任何效应量都是对一个混合体的对比。** `confounds` 是工序 1 的
预注册文本，改它是预注册变更不是修 bug，所以我只登记，没动。
