priority: 2
cell: A8
territory: theoria-arm
deps: none
lane: campaign

# A8-campaign-ledger-pipeline · 战役记账管线：让每关自动产出图2原料

战役跑起来后最容易丢的不是分数，是记账。做一条管线：每关结束自动从账本抽出三条曲线（theorize 轮数、七种意外分类计数、逐回合累计成本），落 theoria-arm/runs/<关卡>/curves.json，格式与 figures/ 的确定性管线对齐，让图2「账单形状」可以直接读而不必事后重算。附一个自检：曲线的回合数必须与账本的 env_step 数一致，对不上即报错——事后发现记账缺口就来不及了。
