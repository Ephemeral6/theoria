priority: 1
cell: S4
territory: monitor
deps: none
lane: infra
author: RES-4

# S4-S34-done-items-resurrect · S34 · 完成的活会被合并复活，然后被重做

2026-07-29 的普查抓到：**同一个条目可以同时存在于 items/ + claimed/ + done/**。
board 的状态是**被跟踪的文件**，而 `board.py` 的三个动作全是 `os.rename`，
没有任何一个动作会去看另外两个目录里有没有同名 id。于是：

1. 某人 `done` 把 `claimed/X.W.md` 改名进 `done/`；
2. 之后一次 `git merge`（来自一条 base 早于那次 done 的分支）把
   `items/X.md` 或 `claimed/X.W.md` **原样恢复**——git 看见的是「对面有一个我没有的文件」，
   不是「这件事已经完成了」；
3. `claim` 只检查 `items/X.md` 在不在，于是把已完成的活重新发出去。

**实测两例，其中一例正在烧人**：

* `E8-ic3-scale` —— 12:16:28Z 被 W-1660 `DONE`，此后**又被认领四次**
  （15:08 W-1671、15:54 `--help`、15:59 W-130），每次都被 sweep 收回，
  此刻同时躺在 items/（可领）、claimed/（W-1671）、done/（W-1660）三处。
  任何现在领它的人都在重做已交付的活。
* `A13-sealed-audit-reads-the-wrong-fields` —— claimed/ 与 done/ 并存；
  分支内容其实已经在 master 上。已由 RES-4 于 18:00:34Z 手工对账清掉，
  board.log 里记为 `RECONCILE`。

注意这**不是 board.py 的逻辑错**，是「状态放在被跟踪文件里」与「合并」的
交互，所以修法不能只在 board.py 里改一行。做四件：

1. **`claim` 拒绝任何在 `done/` 里已有记录的 id**，并把拒绝理由印出来
   （`already delivered by <worker> at <utc>`）。sweep 的 claimed→items 那一步同样加这道检查——
   已完成的活不该回到货架上。
2. **`board.py reconcile`**（新子命令）：扫三个目录，任何 id 出现在多于一处就报告，
   `--fix` 时以 **done/ 为权威**删掉另外两处的残留，并往 board.log 写 `RECONCILE` 行。
   默认只报告不动手。
3. **一条机器检查进 ci_merge / monitor 的 verify**：三目录交集必须为空，否则红。
   合并本身是复发路径，所以检查必须在合并之后跑，不是合并之前。
4. **阴性样本**：造一个「done 之后用一次 merge 把 items/ 恢复」的夹具，
   断言 (a) 修前 `claim` 会把它发出去，(b) 修后 `claim` 拒绝、`reconcile --fix` 清掉、
   verify 变红。**没有这个夹具，这条修复无法证明自己修的是那件事。**

服务的是舰队吞吐本身：E8 一件就至少烧掉四个 worker 的启动与上下文。
零 API，零封存堆接触。
