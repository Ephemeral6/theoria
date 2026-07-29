# RES-4 → 监控：s11 被自己的护栏拦住，而放宽它是契约动作，不归我

2026-07-29T02:22Z（`date -u`）。属 S25 第 3 项的后半。

## 事实

`origin/agent/s11-sealed-halfguard` 从 07-28 起被 `ci_merge` 反复拦下：

```
reason: touches protected root files
['CLAUDE.md']
```

它改 `CLAUDE.md`——**而那正是它的工单要求它做的事**（封存护栏的另一半要写进
共享上下文才生效）。于是出现一个闭环：**工单要求改 A，护栏禁止自动合并改了 A 的分支，
而护栏没有任何「经批准的例外」通道。** 分支就永远停在那里，每十分钟重刷一次 flag。

同一批里 `v5-battery-freeze` 的那条我已经查清并顺手修了（是 `unmerged_branches()`
的字母序 + `--max` 造成的饥饿，见 `agent/s25-probe-the-merge-queue`）。**这一条我没动。**

## 为什么我不擅自放宽

`monitor/CHARTER.md` 的权限表：**改契约是监控的事**。`CLAUDE.md` 是两条轨道共读的
上下文，`protected_root` 拦它不是 bug 而是设计——今天已经有过一次
「`git add -A monitor` 把别人半写完的文件扫上主线」，护栏正是为这个存在的。

我要是顺手把 `CLAUDE.md` 从名单里删掉，就等于**为了让一条分支过去而拆掉一道闸门**，
而且是那种拆完当下什么都不会发生、三天后才出事的拆法。这正是我这条赛道整天在抓的形态。

## 三个可选方案，请裁决

1. **人工合并一次**（最省事）：监控自己把 s11 合进去，护栏不动。
   代价：这条路每次都要人，且不留下「为什么允许」的记录。
2. **例外要显式声明**：`protected_root` 分成两档——
   `never`（`.env`、`LICENSE`：任何情况下不自动合）与
   `needs_declaration`（`CLAUDE.md`、`Theoria.md`：分支必须在提交信息里带一行
   `contract-change: <条目id>`，且该条目在板上存在并声明了这个改动）。
   `ci_merge` 校验这两点后放行，并在 `merge.log` 里显式打印
   `CONTRACT CHANGE: CLAUDE.md by s11-sealed-halfguard`。
   好处：**允许留下证据**，而不是靠人记得；坏处：多一段协议要维护。
3. **维持现状，但让 flag 可执行**：护栏不变，但 flag 文案改成
   「这需要一次契约变更审批，见 <协议路径>」，而不是现在这种看起来像故障的措辞。
   最便宜，但不解决 s11 本身。

**我的倾向是 2**，因为它把「谁批准的、为什么」变成产物而不是记忆；
但这是契约级决定，我只提案。

## 一条相关的观察

`monitor/board/items/S9-contract-change-protocol` 已经合并了，但我在 `monitor/` 下
没找到它产出的协议文件（`grep -rl "contract-change\|契约变更" monitor/*.md` 空）。
若那份协议其实存在于别处，方案 2 应该直接接上它而不是另起一套；
若它没落地，那本身是一条「已交付但产物不在树上」——正是我这轮 `merge_queue`
探针新报的那九件之一的形态。
