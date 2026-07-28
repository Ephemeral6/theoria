priority: 2
cell: P8
territory: papers-figs
deps: none
lane: paper

# P8-billshape-pipeline · 把账单形状图接上真数据管线

论文图2『账单形状』是主轴签名证据（C2），现在图的管线在 figures/ 已可复现出图，但数据源只有 baseline 的裸 CC 曲线，Theoria 臂那一列是空的。做两件：(1) 写好数据适配器，让 theoria-arm/runs/*/ 的账本一落盘就能自动进图，不需要人改代码——开发堆战役随时会产出第一条真曲线；(2) 用 baseline 已有的三档模型数据先把图画完整（前载指数、收敛点、上下文增长拟合都标出来），并写清楚 Theoria 列到位后图会怎么变。领地是 papers/figures/ 子目录，与 P7 正文不冲突。
