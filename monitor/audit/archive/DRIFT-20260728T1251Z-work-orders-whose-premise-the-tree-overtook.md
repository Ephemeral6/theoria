# DRIFT-work-orders-whose-premise-the-tree-overtook

severity: medium
dimension: 流程漂移（工单要求做的事已经做完了——第 6 维「要求引用了不存在的东西」的镜像）

evidence: 审计区间 `1a8ed00..9e61399`（9 个提交、64 文件）。两例，我逐例独立复核过，不转述孤证。

**例一（P9，本轮）：工单说 §7 陈旧，而 P7 已经把它重推过了。**
- 工单要求：「the battery section is marked stale — update it to the latest REPORT」（`papers/phase1-workshop/runs/20260728T115500Z-P9/FINDINGS.md:15` 引原文）。
- 树上：`papers/phase1-workshop/OPEN_ITEMS.md:25` 的 A1 条目**整条被删除线划掉**，后接 **「Closed at P7 — §7 re-derived against `battery_version: "v2"`, every number read from `battery/artifacts/*.json` rather than from report prose」**；`sections/07_battery.md` 开篇也确实是 v2 口径。
- 我自己复核了这两处文件，与 P9 的陈述一致。

**例二（P8，上一件）：工单说图 2 的 theoria 列是空的，而 P4 已经画好了。**
- P9 的报告称 P8 的工单如此写（`FINDINGS.md:19-21`）。**我没有只信这一句**，去树上验了：
  `figures/fig02_bill_shape.py` 在树且引用 theoria，`figures/csv/fig02_bill_shape.csv` 在树，
  `figures/out/{dark,light}/fig02_bill_shape.{png,svg}` 已渲染；而 `figures/runs/` 里
  `20260728T082401Z-P4-figures` **早于** `20260728T110000Z-P8-billshape-pipeline`。
  P4 先画完，P8 才被派去画。例二成立。

**P9 自己的结论（`FINDINGS.md:19-24`）我认为判得准，照录：**
> 「Both are the same failure at the level of **the board rather than the code**: an item's text is written once and the tree moves under it. Reported to the monitor rather than silently reinterpreted, because the next researcher will read the same text.」

claim: 连着两件工单的前提在派发时就已经被树推翻了。这是第 6 维的镜像——第 6 维是「工单要求用的东西不存在」，这条是「工单要求做的事已经做完」——但代价形态不同：第 6 维让纪律空转（不花钱），这条**每中一次就烧掉一个研究员会话的开场**：它启动、读工单、去核、发现前提是空的，然后只能把这件事本身当产出报回来。P9 这一跑的全部实质产出就是这份 FINDINGS。

根因与我第四轮报的盘面陈旧是**同一个**：手写的项目视图落后于合并队列。上次它表现在**显示**层（页面上的数字），这次表现在**派发**层，而派发层的陈旧比显示层贵得多——显示层错了只是看错，派发层错了要花掉一个会话。

suggest:
1. **派发前对树核一次前提**，哪怕只核一句。这两例的判据都在树上、一条命令可得：例一是 `OPEN_ITEMS.md` 里那条已划掉的 A1，例二是 `figures/runs/` 里 P4 的目录早于 P8。建议工单模板加一行 **`前提：<一句可证伪的陈述> —— 核于 <commit>`**，派发时由作者填，探针可以在派发后比对该 commit 与当前 HEAD 的距离。
2. 更省事的机械化：工单若引用某个文件「陈旧/为空/未做」，探针在派发那一刻检查该文件的最后修改提交是否**晚于**工单文本的写就提交——晚于就报 note。这不需要理解语义，只比时间戳，能抓住这两例中的两例。
3. P9 报的第二件事（`papers/` 被两次认领：`claimed/P7-paper-section7.APP-P7` 与刚派给 P9 的同一领地）请一并裁——它没有编辑别人领地，处理得对，但两张单子同指一处需要监控解开。

（本轮其余复核，一并记此免得另开文件：**`TERRITORIES` 已改为 `_discover_territories()`**，我上轮的主建议全额采纳；**`verify_gates` 的扫描范围仍只有 board 三个目录**，`monitor/prompts/**` 未加，因此 `a0-spike/verify.sh` 仍在探针视野之外——**该文件已欠 4 个周期**，且现在既不在板上也不被任何探针记着，建议要么补要么把 C2 工单那行删掉，别再挂着；**`theoria-arm` 仍是 11 run / 4 MANIFEST**，未补。另：`figures/verify.sh` **已在树上**——新交付的活确实带上了自己的 verify 脚本，这条约定在成形。）
