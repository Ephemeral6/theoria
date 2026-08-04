# INCIDENTS — monitor

Things that went wrong in this territory, or that make a number the monitor
publishes mean less than it appears to. Numbered `INC-MON-nnn`. An incident is
recorded when it is noticed, not when it is resolved.

The prefix is deliberate: `arc-recon` uses `INC-00n` / `INC-AR-0nn`,
`baseline-arms` uses `INC-BA-0nn`, `theoria-arm` uses `INC-TA-0nn`. **This
territory never edits another territory's incident book** — something the
monitor needs another track to do goes through `monitor/inbox/` or
`PARTNER_SYNC.md`.

The monitor holds the money, so a money record that is wrong is this
territory's incident even when the spending happened elsewhere.

---

## INC-MON-001 · 开发堆配额 B = $60 被超到 $129.03，而仪表在整个过程中是绿的

**发现** 2026-08-02，工单 M-1。**状态** 开放——超支已成事实，不可撤销；本条登记
它，并修掉那个让它无声发生的仪表。

**事实，全部由 `proxy/var/spend_gate.jsonl` 现算**（17,329 行，最后一行
`2026-08-02T12:19:04.949Z`；口径：`kind == "spend"` 且 `campaign` 含
`A3-campaign-devpile`，共 6,757 行 / 37 个战役）：

> **B 实花 $129.0326，是 $60 的 215%。**

逐腿（美元，全部可复算）：

| 腿 | $ |
|---|---|
| `20260801T044640Z-R2b-sk48-b` | 20.3032 |
| `20260801T044640Z-R2b-g50t-a` | 18.7360 |
| `20260801T001851Z-R1b-g50t-a` | 17.7491 |
| `20260801T001851Z-R1b-sk48-b` | 17.3907 |
| `20260731T1430Z-A3-level2-carried-r3` | 13.4399 |
| `20260731T1500Z-A3-sk48-carried-l1` | 12.2517 |
| `20260731T1310Z-A3-level2-carried-r2` | 9.5569 |
| `20260731T231654Z-R1-sk48-b` | 7.6085 |
| `20260731T231654Z-R1-g50t-a` | 7.6034 |
| `20260729T0035Z-a3-desk-live-proof2` | 4.3932 |

分局：`g50t-5849a774` $71.4784、`sk48-d8078629` $57.5542、`ar25-0c556536` $0.00。
池全量（不限开发堆）**$160.9480**。

> **计费口径，写下来是因为它自己就差过一次。** 计入 `kind == "spend"`（扣款）与
> `kind == "price_correction"`（对已扣价格的修正），不计 `reserve` / `release`
> （簿记，各自合计恰为 0，计进去是重复计数）与 `trip`（事件）。只算 `spend` 得
> $160.7917，全量求和得 $160.9480，差 **$0.1563 全部是 `price_correction`**。
> 本工单一度同时引用过这两个数。B 的 $129.0326 在两种口径下相同（开发堆没有价格修正行）。

**两条越线，各有确切的位置：**

* **G1 $50** 越于 `spend_gate.jsonl:16157`，`2026-07-31T23:54:45.969Z`，
  在 `20260731T231654Z-R1-g50t-a` 中途，累计 `49.78684 → 51.509416`。
* **B $60** 越于 `spend_gate.jsonl:16346`，`2026-08-01T00:48:42.766Z`，
  在 `20260801T001851Z-R1b-sk48-b` 中途，累计 `59.086316 → 62.448327`。

**为什么没有任何东西报警——这半才是本条的正文。** `monitor/scan.py:1248-1277`
的 `_spend_watch()`：

1. `:1268` 把 `ENVELOPE` **硬编码为 200.0**，而 B 是 60；
2. `:1265-1266` 对账本**全量求和、不按 `kind` 过滤、不按战役过滤**；
3. `:1270` 把这个数标称为「开发堆战役包」——**它不是**，它是池；
4. `:1275` 只在 `left < 40` 时转红。

结论：**B 不是这个仪表能表达的量。** 它不是漏报了一次，它在结构上从来就没有在
看 B。看板因此在 B 越线之后仍然发绿，而那条绿正好守着刚刚变负的那个量。

**处置（本工单）：** `monitor/money.json` 成为金额的唯一出处，`_spend_watch()`
改为逐 allocation 比对，`monitor/tests/test_money_register.py` 让「B 超支」这件事
能把测试打红。**修好仪表不等于修好超支**——钱已经花掉了，本条不因仪表修复而关闭。

**未决，需人裁：B = $60 是「每战役」还是「每局」？**
`monitor/board/done/A3-campaign-devpile.RES-1.md:54`（blob
`3b04548c9a39499c94b7152cbd7128c3cb69100d`）与 `freeze/BUDGET_TABLE.md` 读作
**每战役**（$129.0326 = 215%）；`monitor/loop_state.json:58` 与
`theoria-arm/harness/campaign.py:93` 的 `GAME_USD = 60.0` 读作**每局**
（g50t $71.4784 超，sk48 $57.5542 未超）。**两种读法下都已越线或逼近**，所以裁定
不改变「已超支」这个结论——但它改变归责与剩余额度，而 `money.json` 里只能写一个。
登记为 `needs_human`。

> ⚠ 不要编辑 `monitor/board/done/A3-campaign-devpile.RES-1.md`。
> `freeze/build_budget_table.py:538` 按 `(文件, 第 54 行, "B = $60")` 行锚引用它，
> `freeze/verify.sh` 第 [15b] 阶段会跑。任何让第 54 行移位的编辑都会让 freeze 为一个
> 它没有的缺陷变红。要引用就指过去，不要动它。

---

## INC-MON-002 · 登记簿有两个 #12，而其中一个是某条已付费腿的唯一覆盖凭据

**发现** 2026-08-02，工单 M-1。**状态** 编号已在本工单更正；覆盖归属待人裁。

**事实。** 登记簿是 `monitor/spec.py` 中 `p3-gate-exception` 条目的单个字符串
（`note`，sha256[:16] = `f51b4aaa1e515e88`，逐字复制于 `monitor/state.json`
的 `_note` 与 `note`、以及 `monitor/index.html`）。从中抽取申报编号得到：

```
3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 11, 12
```

**#12 出现两次**，且 #11 申报在 #13 之后：

| 位置 | 标题 | 落盘提交 | UTC |
|---|---|---|---|
| `spec.py:522` | **#12 Phase 3 轮次制** | `af138a0d` | 2026-07-31T23:16:47Z |
| `spec.py:531` | **#12 Phase-3 加速迭代战役** | `f6a95719` | 2026-07-31T15:06:17Z |

**为什么这不只是排版。** `theoria-arm/runs/20260731T1500Z-A3-sk48-carried-l1/`
的 `MANIFEST.json` 写着 `prompt_id: "A3-campaign-level2"`，那是登记簿 **#10** 的
名字；但 #10 申报的是 **g50t** 的第二关带书腿，而 #10 的结算数 $9.5569 只能、也恰好
只能由两条 **g50t** 战役复算出来。这条腿是 **sk48**、花了 **$12.2517**。

真正覆盖它的是 `:531` 的批量 #12：该条落盘于 `2026-07-31T15:06:17Z`，而这条腿的
预留在 `spend_gate.jsonl:15032`、`15:06:28.568Z`——**晚 11.4 秒**，`usd_cap 19.0`
（= 申报 $15 + 单次调用余量 $4），在信封之内。

**于是编号裁定不是排版问题，它决定一条已付费的腿有没有授权：**
若 #12 判归「轮次制」，这条腿就变成**无任何登记覆盖的 $12.2517 跨门支出**；
若判归「加速迭代战役」，它是被覆盖的，只是 MANIFEST 写错了名字。

**本工单的处置。** 按 `baseline-arms/INCIDENTS.md:7-13` 的先例——**保号给已被外部
引用的那条，另一条原地改号，撞号本身记为事件而不是抹平**：`PARTNER_SYNC.md:1898`
与 `monitor/runs/20260731T155302Z-P1READJ/RUN_STATE.md:18` 两处引用都写在
`af138a0d` 之前、都指向加速迭代战役，所以 **`:531` 保 #12，`:522` 改为 #14**，
位置不动，段落不重排。

**仍需人裁两件：**（a）确认上述保号方向；（b）`theoria-arm` 侧那份写错 `prompt_id`
的 MANIFEST 由谁更正——已走 `monitor/inbox/` 请求，本领地不直接编辑对方文件。

**为什么此前没有任何东西发现它。** `monitor/tests` 39 个文件里没有一个匹配
`spend_gate` / `gate-exception` / `登记簿`。登记簿上每一个数字都是人手打的句子，
没有任何测试能让它变红——**一本没有测试能打红的登记簿是装饰品**。本工单新增
`monitor/tests/test_money_register.py`，其第一条断言（编号唯一、无缺号）正是能抓到
本条的那一条。

### 补记 2026-08-02 · 同一个撞号在修它的过程中复发了一次

本条的修法（`:522` 的 #12 改为 #14）写完并推送之后，`git fetch` 发现 master 上
另一个会话已用 **`b4540026`** 新增了一个 **#14**（「通关阻塞实验 / A26 长腿实验」）。
两边都看不见对方：那个会话在 master 上，本工单在 `agent/m-1-money-single-truth` 上，
**分支隔离让编号分配没有任何共同的仲裁点**。

**这不是一次巧合，是本条描述的缺陷的第二个实例**，间隔数小时。它把本条的结论从
「一次疏忽」升级为「登记簿的编号分配没有互斥」：只要两个会话同时在册，
**下一次撞号只是时间问题**。

处置：按同一先例连锁让号——已发布的 `b4540026` 的 #14 保号，本工单的轮次制条目
再让一号改为 **#15**，起草时编为 #15 的 R2/R2b 顺延为 **#16**。合并后的申报序列为
`3,4,5,6,7,8,9,10,15,14,13,11,12,16`，唯一、无缺号（顺序不升序是先例要求的
「原地改号、绝不重排」的结果）。

**这也是本工单那条测试的第一个真实战果**：合并时
`test_register_ids_are_unique_and_have_no_gap` 会把两个 #14 打红，
而在它存在之前，两个 #12 在树上活了整整一天没有任何东西发现。

**第三例（2026-08-04，合并 agent/m-1-money-single-truth 时）**：本分支按上文让号定为 #15 之后、合并之前，master 又以 c42f5ad4 发布了 #15（池上限上调 $214.90→$700）。同一先例第三次执行：已发布的 #15 保号，轮次制条目定为 **#17**（#16 已被 R2/R2b 占）。合并后申报序列 `3,4,5,6,7,8,9,10,15,14,13,11,12,17,16`（含转录行 #15），唯一、无缺号。三例间隔各数小时——编号互斥的 needs_human 判断由此更硬。

**未决（升级为 needs_human）**：编号分配需要一个互斥点。可选项——由 `money.json`
持有 `next_id` 并要求申报者先取号；或规定编号只在 master 上分配、分支一律用
占位符。本领地不代拍。
