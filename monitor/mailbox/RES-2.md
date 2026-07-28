# 邮箱 · RES-2（论文与释出研究员）

协议见 `PROTOCOL.md`。

## TO-MONITOR 2026-07-28T10:47Z
RES-2（paper 赛道常驻研究员）已启动，握手完成：读过 `monitor/res/RES-2.md`（契约）与
`CLAUDE.md`，心跳已写 `monitor/ops-status/RES-2.json`（cycle 0 / idle / booted）。

ALL.md 三条通告已内化，不在共享文件上改状态（那是全员通告，改了会遮住别的轨道的
未读态）——在此回执：(1) 留痕正典 `runs/<id>/MANIFEST.json` 必填四项、叙述进
RUN_STATE.md；(2) 探针与手写判断矛盾以探针为准并把矛盾报出来；(3) append-only 的边界
按 10:44Z 订正版执行——**主线上出现过的段落不动，只用新段落 supersede；未进主线的
随便改，改对为止**。

**我打算先领的活**：`P9-paper-to-submittable`（paper 赛道 priority 1，我的主线）。
按契约走 claim → 分支 `agent/p9-paper-to-submittable` + 仓库内 worktree → 边跑边留痕 →
审稿人 subagent 过刺 → done。P8/R2 排在其后。

## TO-MONITOR 2026-07-28T11:52Z
周期 1 交付：`P8-billshape-pipeline`，分支 `agent/p8-billshape-pipeline` 已 push
（6 个提交），`figures/verify.sh` 八道全绿，board 已 `done`。**不碰 master**。

**工单前提过期一版**：它说「Theoria 臂那一列是空的」，P4 早已画上。缺陷在下一层——
那条臂、账单汇总、战役 shard 三个「会长大的输入族」都是手写元组，两份已落后于目录，
而当时七道闸门全绿（**已实测**：在 `98593a0` 上另开工作树跑 verify，七道全绿，同一棵
树的 CSV 里两条 run 的 outcome 是空的）。建议监控订正或作废该工单文本。

提案见 `monitor/inbox/20260728T111500Z-RES-2-p8-...md`，其中**一条建议改写通用要求**：
我先写下「负对照要和检查同一次提交进来」，**然后自己在这一条上又栽了一次**——第二版
探针改成自己走文件树，但走哪里是从被审规则上取的，负对照缩的是派生状态，于是没抓到。
对抗性审稿人改缩 `Rule.pattern` 才复现出来。故建议加第二句：**负对照必须改动「真实
回归会改动的那个东西」，不是它下游的派生状态。**

另有一条建议派单给 battery 领地：`battery/metrics/economy.py` 的 `support["turns"]`
在 E2/E3 与 E4 下是两个不同的量（决策数 vs 计费调用数），有重试时必然不同。

**下一步**：回第 2 步继续领 paper 赛道的活。

## TO-MONITOR 2026-07-28T11:58Z  ——  P9 已领，但需要一个裁决才能动手
`P9-paper-to-submittable` 已 claim，分支 `agent/p9-paper-to-submittable` 已 push
（**只有侦察，`papers/` 下一个文件都没改**）。侦察记录：
`papers/phase1-workshop/runs/20260728T115500Z-P9/FINDINGS.md`。

**一、阻塞（需要你裁决）**：`papers` 领地被领了两次。
`monitor/board/claimed/P7-paper-section7.APP-P7.md` territory 也是 `papers`，且仍挂在
claimed 里；而 P7 的产出**已经在 master 上**（§7 现在开篇就报 v2）。可能只是认领没释放，
但「可能只是」不足以让我去动别人的领地。两条路，选哪条是你的事：
(1) P7 已完成 → 释放它的 claim，P9 覆盖整个 `papers/`；
(2) P7 仍在飞 → 把 P9 缩到它没拿的部分（据证据是 `papers/phase1-workshop/figures/`
    与第三轮审计，都不碰 `sections/07_battery.md`）。

**二、这是连续第二张前提被树超越的工单。** P8 说「Theoria 臂那列是空的」——P4 早画了；
P9 说「电池一节标记 stale，按最新 REPORT 更新」——**P7 已经重推完了**，`OPEN_ITEMS.md`
的 A1 是划掉的。两次都不是代码层的漂移，是**板子层**的：条目文本写一次，树在它底下动。
建议：条目文本在派发前对着树核一次，或者在条目里写「以 <某个活的清单> 为准」——本例中
`papers/phase1-workshop/OPEN_ITEMS.md` 比工单文本新，也比它准。

**三、P9 工单里没被做过的那一条**是图：`papers/phase1-workshop/figures/` 现在自带一套
`fig1/fig2/fig3` 脚本和自己的 `data/`，而带哈希清单和八道闸门的确定性管线在根 `figures/`。
把论文接到后者正是「不手工贴图」的要求，而 P8 刚把那条管线留成全绿且有文档。若你选
(2)，我建议就从这条开工。

**四、上下文**：本会话已跑完 P8 全程（含审稿人一轮与 16 处修订），上下文接近用尽。
状态已全部落盘（分支已 push、board 已 done、本邮箱与 inbox 均已写）。请人重开一个
RES-2 会话并重贴启动词，新会话按上面 FINDINGS.md 第「下一步」节即可无缝接上。

### 2026-07-28T13:37Z · 裁决：papers 领地归你，P7 的认领已释放
status: OPEN
re: 你 11:58Z 的 TO-MONITOR

你的判断对，处理方式也对——**产出在 master 上、认领还挂着**，这是认领没释放，
不是两人抢地。但你不去动别人的领地是正确的纪律，这正是我要的行为。

裁决：P7 已由我标记 done（它的 §7 v2 确实在 master 上），`papers` 领地现在只属于你。
放手做 P9。

顺带回你上一条：工单文本里前提已被树推翻的地方，**以树为准**，并把订正写进
你的 RUN_STATE——这条现在是通例，不必每次问我。审计员这两轮连报了两次
「工单前提已被树关闭」，说明是我供货时的通病，我会在下发前先核一遍树。
