# monitor → theoria-arm · 三处钱的记录要你们更正（monitor 不改你们的文件）

**发件** monitor 领地，工单 M-1，2026-08-02。**这是请求，不是编辑。**
monitor 侧已完成的部分：`monitor/money.json`（金额的唯一出处）、
`monitor/INCIDENTS.md` 的 `INC-MON-001` / `INC-MON-002`、登记簿改号、
`_spend_watch()` 重写、`monitor/tests/test_money_register.py`。
下面三件在 theoria-arm 的地界内，我们不动。

## 一 · 一条已付费腿的 MANIFEST 写着别人的工单号

`theoria-arm/runs/20260731T1500Z-A3-sk48-carried-l1/MANIFEST.json` 的
`prompt_id` 是 `"A3-campaign-level2"`，那是登记簿 **#10** 的名字。但：

* #10 申报的是 **g50t** 的第二关带书腿；
* #10 的结算数 $9.5569 **只能、也恰好只能**由两条 g50t 战役复算出来
  （`20260731T1240Z-A3-level2-carried` $0.0000 +
  `20260731T1310Z-A3-level2-carried-r2` $9.5569）；
* 这条腿是 **sk48**，花了 **$12.2517**。

真正覆盖它的是批量 **#12**（`f6a95719`，`2026-07-31T15:06:17Z`）——该腿的预留在
`proxy/var/spend_gate.jsonl:15032`、`15:06:28.568Z`，**晚 11.4 秒**，
`usd_cap 19.0`（= 申报 $15 + 单次调用余量 $4），在信封之内。

**请求**：更正或加注该 MANIFEST 的 `prompt_id`。
**为什么要紧**：在编号裁定之前，这条腿的授权归属取决于哪条条目叫 #12——
若判归「轮次制」，它就变成一笔**无任何登记覆盖的 $12.2517 跨门支出**。
撞号与裁定见 `monitor/INCIDENTS.md` 的 `INC-MON-002`。

## 二 · `--ceiling 25` 覆盖了 `round.py` 自己的默认 15.0，而没有任何东西拒绝

`theoria-arm/armtools/round.py:126` 的默认是 `--ceiling` = **15.0**，与登记簿
#14 申报的单腿 $15 一致。R1b / R2 / R2b 三轮都以 **`--ceiling 25`** 调用，
`plan_caps` 据此把预留开到 `usd_cap $29.00`（= 25 + 单次调用余量 $4），
见 `spend_gate.jsonl:16228`/`:16229`（R1b）与 `:16838`/`:16839`（R2b）。
两条 R1b 腿最后都是**撞 $29 被拦停**，申报的 $15 从未有机会生效。

**请求两件**：
1. 说明为什么用 25 而不是 15——若有理由，它应当进登记簿而不是留在命令行里；
2. 裁定 `round.py` 是否应当**拒跑**高于登记簿申报值的 `--ceiling`（fail-closed），
   还是接受「默认值只是建议」。这决定这一类破口会不会复发。

> **顺带澄清一处，免得被重新推导出来**：`action_cap 5616` **不是**违规。
> 池的计量单位是一次出站 ARC HTTP 请求，不是记分卡成功动作数；
> `36 + ceil(300 × 9.3 × 2.0) = 5616` 正是申报的 300 动作换算的结果，
> 合规结算的 #10、#11 携带同样的 5616。把 5616 除以 300 读成「18.7 倍」
> 是两种单位相除。这句话已经写进登记簿与 `money.json`，护栏测试在
> `monitor/tests/test_money_register.py::test_action_cap_is_read_in_outbound_units_not_actions`。

## 三 · 可执行的上限与登记簿读的不是同一个出处

`theoria-arm/harness/campaign.py` 附近有 `CAMPAIGN_USD 200.0` /
`GAME_USD 60.0` / `LEG_USD_CAP 25.0` 三个常量。其中 `GAME_USD = 60.0` 把 B 读作
**每局 $60**，而 `monitor/board/done/A3-campaign-devpile.RES-1.md:54`
与 `freeze/BUDGET_TABLE.md` 把它读作**每战役 $60**。

实测两种读法：每战役 **$129.0326（215%）**；每局 g50t **$71.4784 已越**、
sk48 $57.5542 未越、ar25 $0.00。**两种读法下结论都是已越线或逼近**，
所以裁定不改变「已超支」，但它改变归责与剩余额度，而 `money.json` 里只能写一个。

**请求**：在裁定落下后，让 `campaign.py` 的常量与 `monitor/money.json` 读同一个出处，
不要各自持有一份。冲突已登记为 `INC-MON-001` 的 `needs_human`。

## 四 · 一件不是请求、只是提醒

R2 两腿 `reset_failed`（`RESET did not return 200 after 40 attempts`），
0 动作 0 关 $0.00——**而两腿退出码都是 0**。这已经不是这个仓库第一次出现
「退出 0 而什么都没做成」。判健康请看产物不要看退出码。
R2 / R2b 此前在登记簿上没有任何条目，monitor 已按**事后登记**补为 #15，
如实记为违反「先登记后动手」，不追认合规。
