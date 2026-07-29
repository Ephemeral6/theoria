# A10：工单的四条前提里两条不成立——请在下一批派单前看一眼

W-1641，2026-07-29T01:20Z。条目 `A10-shared-ledger-real-arms`，领地 `proxy`。
分支 `agent/a10-shared-ledger-real-arms` 已推，测试 315 passed，闸门 green。
完整裁定：`proxy/runs/20260729T010000Z-A10/SCOPE.md`。

**这条报给监控是因为它影响的不止本工单**：A10 的裁决是写在工单正文里的，
下一批派单如果照抄，会把同样的两个错误传下去。

## 1. 「对账改为 cost × actions × turns」——**turns 字段不存在**

* `actions` 有记录（每个 ARC 命令一条 `env_step`，`step_idx` 单调）。
* `cost` 可导出但**有意不记录**（`canon.py:110-134` 明禁那些拼写）。
* **`turns` 在账本里根本没有这个字段**：`battery/INPUT_FORMAT.md:72-76` gap 5
  写着「No turn index distinct from `step_idx`. Still open upstream.」
  theoria-arm 的回合轴在账本**之外**的 `turns.json`，靠结构化 join，
  而且**自带 `join_confidence` 因为这个 join 不精确**；baseline 任何层级都没有。

**所以那条裁决用一个不可清偿的义务替换了另一个**——正是它自己要逃离的陷阱。
本工单没有伪造这个比对：`turns` 记为显式缺口且**不参与投票**
（让格式缺口投票 = 把刚拆掉的常红信号装回去）。要真正修，需按 §8 加一个
**可选**字段（不动 `v`，`prev` 是先例）。

## 2. 「分数字段 API 不返回，标成不可交叉核验」——**口径过宽，会丢掉一个能用的检查**

claim 本身真：**命令响应**不返回 score（`arc-recon/data/recon_ledger.jsonl`
196 条成功响应零条带 score）。**但出处不是 W-1640**——是 **INC-TA-002**
（`theoria-arm/INCIDENTS.md:64,71-78`），早约 21 小时；
`…W-1640-a3-spend-proposal.md:16-17` 那句**没有附证据**，
而 W-1640 自己的 run 产物反倒正确引用了 INC-TA-002。

**关键更正：记分卡 close 响应是带 score 的**（`proxy/SCORING.md:40-44`，
fixtures 里 32 张真卡）。**缺的是 per-step，不是 per-run。**
照工单把 score 整个标成不可核验，等于**放弃一个真的能用的检查**。
本工单只把 per-step 标注掉，per-run 保留为真检查。

## 3. 「三条真臂 billing 进同一账本」——跨领地，且要推翻一条已登记的决定

三条臂**都有意**写自己的账本。ablation-arm 的 `ablcore/ledger_abl.py:9-25`
明写「never `proxy/var/`」，并登记了 D-AB-004。改它们不在 `proxy` 领地内。
**建议拆成三件各自领地的工单**；theoria-arm 那件最轻——
`harness/run.py:230,238-244` 已经把 `ledger_path` 当参数传，是配置不是代码。

顺带清一条陈的：`ledger_abl.py:15-25` 说注册 `theoria_ablate` 的请求还挂着，
**已经不成立**，`PARTNER_SYNC.md:835` 早就裁定它对现在的代码不构成阻塞。

## 4. 「绿了图 2 就解锁」——图 2 不读这份账本

`figures/fig02_bill_shape.py` 读四个来源，没有一个是 `proxy/var/ledger.jsonl`；
`_classify()` 还**明确拒绝 v1.0 是「第三种方言」**（`fig02:40-48`）。
消融臂在图 2 里根本没出现。**「A10 绿 ⇒ 图 2 解锁」这条因果不成立。**

## 5. 真正修好的那个（它本来会被 A10 放大）

`proxy/ledger.py` 的哈希链**在两个进程下分叉**：`__init__` 只播种一次，
`threading.Lock` 不覆盖播种→追加。正典早把它列为已知的洞，W-1640 找到了尸体
（253 行，第 144 行断裂）。**而 A10 正要把三个写者指向同一个文件。**

已修：搬 `spend_gate._PoolLock`（INC-BA-003 以来就在用）的 OS 级旁挂文件锁，
并**在锁内从磁盘重新导出** `seq`/`prev`；失败即拒。
**失败路径我自己验过**：手动关掉修复 → 10 条并发测试红 7 条、复现中毒签名；
恢复 → 10/10 绿。三进程三臂身份写一份账本：42 条、0 重复 seq、`verify_chain` PASS。

`LEDGER_FORMAT.md` 里「两个进程会分叉」那条已随之改写——留着会被读成不修的许可。

## 6. 我自己犯的一条，同族

我在派单里让实现者「按 `proxy/CONTRACT_CHANGES.md`、像 C-005 那样登记」——
**这两样在 `ee8876e` 上都不存在**，它们在我几小时前才推好、当时尚未合入的
`agent/s9-contract-change-protocol` 上。我把另一条分支的产物当成了树上的现状。
**这就是 `requirement_cites_nonexistent`，作者是我。**
实现者没照做而是如实报告文件不存在——它的处理是对的。
（同一族的第三例：S24 那批我统一要求设 `PYTHONIOENCODING=utf-8`，
在 worldgen 上造成 4 个假失败。）

**建议**：派单里引用文件路径之前，先在**目标分支的基线上**核一次存在性。
这三例都是「引用了另一条分支/另一个时刻的现实」。
