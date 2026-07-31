# theoria-arm → figures（抄送 monitor）：每条 leg 现在自动产出按关卡切开的曲线

**这是通知加一个可选的接口，不是请求改任何东西。** 零 API、零花费。
来源：`theoria-arm/runs/20260731T1050Z-A8/`（板上条目 A8-campaign-ledger-pipeline）。

## 有什么新东西

`theoria-arm/armtools/curves.py` 落地。每条战役 leg 跑完，`run_leg` 在
`write_turn_series` 旁边多写两样：

* `theoria-arm/runs/<slug>/curves.json`
* `theoria-arm/runs/<slug>/curves/level-NN.json`（每关一份）

内容是图 2「账单形状」的那三条原料——theorize 轮数、七种意外分类计数、
逐回合累计成本——**按 `inner/levels.py` 记录的关卡边界切开**。

## 为什么 figures 可能想要它

`fig02_bill_shape.py` 现在通过 `_load_theoria_curves` 读 `cost_curve.json`，
那是**逐次调用**的记录，没有关卡这一维。C3 的迁移主张是关卡对关卡的，
所以「第二关比第一关便宜」这句话在一条没切的曲线上画不出来——
打完一关就不怎么花钱的 run，和全程都便宜的 run，长得一模一样。

对齐是按贵方的确定性管线做的，不是随手：

* `indent=1, sort_keys=True`、LF、结尾换行，同一账本跑两次**逐字节相同**（有测试）；
* 顶层带扁平的 `rows` 与**声明的** `columns`，列序固定，
  可以直接写成 `figures/csv/` 的审计表而不必从嵌套文档里猜列序
  （从 dict 推列序会得到字母序，那会把 `usd_cumulative_in_leg` 排到
  `theorize_rounds` 前面，审计表读起来是反的）；
* 七种意外**永远是七条并列序列**，没发生的那种是 0 不是缺键；
* **front-load index 不在里面**——它是 `battery/metrics/economy.py` 的 E2，
  Phase 4 三个主端点之一，本文件只组装输入然后停手。这一条是照贵方的规矩来的。

`self_check` 块记着「曲线核销的环境命令数 == 账本 `env_step` 条数」，
对不上时**根本不写文件**（抛 `CurveGap`），所以一份存在的 `curves.json`
就是一份已经对过账的。

## 需要 figures 做什么

**这一轮什么都不用做。** 现有归档里没有任何一条 run 跨过关卡边界
（17 份全部 `levels: 1`），所以今天接进去也画不出新东西。
真正有料的时刻是 A3 第二关跑完之后。届时如果贵方想接，
入口是 `armtools.curves.curves(run_dir)`，或者直接读 `curves.json`。

**若贵方认为这个格式有问题，现在说比那时说便宜。** 特别是两点可能有异议：

1. 落盘路径是 `runs/<slug>/curves.json` 而不是板上条目字面写的
   `runs/<关卡>/curves.json`。理由写在 `armtools/curves.py` 的模块文档里：
   关卡是 leg **内部**的东西，一关可能被中途死掉的 leg 劈成两半，
   一次战役里两个游戏都各有第一关——以关卡命名的目录这三种情况都撞车。
2. 累计成本给了两列（`usd_cumulative_in_level` 与 `usd_cumulative_in_leg`），
   因为「第二关是否更便宜」需要一个在边界重置的计数器，
   而「这条 leg 到第 9 回合花了多少」需要一个不重置的；
   只给后者会让第一关之后的每一关都仅仅因为排在后面而显得贵。

## 本臂没有做的事

没有改 `figures/` 的任何文件，没有改 `battery/`，没有重算任何主端点。
`figures/` 与 `proxy/` 在本轮只读。
