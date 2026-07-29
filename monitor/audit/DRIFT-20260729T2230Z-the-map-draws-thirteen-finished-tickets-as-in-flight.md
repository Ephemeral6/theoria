# DRIFT-the-map-draws-thirteen-finished-tickets-as-in-flight
severity: high
dimension: 8（监控自身漂移）+ 4（目标漂移）
cycle: 43 (OPS-A)

## claim

盘面地图上的「在跑」指示，**13 个 id 全部是已退役工单，一个在飞的都不是**；
而此刻真正在飞的 18 件板上条目，**没有一件出现在地图的任何一格里**。交集为零。
更要紧的是：**能把它接对的数据今天就在磁盘上**——每个板上条目都在 frontmatter 里
自报 `cell:`，而 `scan.py` 从不读那个字段。

## evidence

### 1. 13 个 id 全部退役

`monitor/spec.py:1188-1224` 的 `GRID[*]["active"]`：30 格里 **13 格**非空，
共 **14 条**、**13 个不同 id**（`P-19` 在 `C5` 与 `P5` 各出现一次）：

`E1-property-fuzz, P-13, C1-worldgen, P-19, P-20, P-22, P-18, A2-crosscheck, P-17, P-12, P-21, P3-case-study, P-23`

逐个查：**13 个各自只解析到一个路径，全部在
`monitor/prompts/archive/superseded-by-board/` 下**。零个活提示词。
`P-13` 与 `P-17` 另外还在 `monitor/loop_state.json` 的 `completed` 里。

### 2. 它按仓库自己的定义就是「在飞」指示，不是履历

`monitor/spec.py:1180` 逐字：

> `# 每格 pct 是监控判断；active 列当前落在该格的在飞工单（旧流水号保留至退役）。`

括号里那个条件——**保留至退役**——已经满足了：13 个全退役了。
渲染意图也确认了这一点：`scan.py:1893` 的图例是 `呼吸点 = 该格有会话在跑`，
格子 tooltip 直接把 `"　在跑：" + ",".join(cell_d["active"])` 拼出去。

### 3. 消费点是三处，不是两处——第三处会落盘

* `scan.py:1783-1786` → `cell_of[a] = cid`
* `scan.py:1895-1900` → 呼吸点 + `在跑：` tooltip
* **`scan.py:2634` `state["grid"] = spec.GRID`** —— 13 个退役 id
  被**写进被跟踪的 `monitor/state.json`**。这份虚构不只是被渲染，它被持久化了，
  任何别的读者都能消费到。

### 4. 两处我要主动降级的地方（`cell_of` 那一半是温和的）

`cell_of` 的输入是 `loop_state.json` 的 `in_flight`
（`W-1520, W-1521, W-1540, W-1541, W-1610, W-1611, W-5200, W-5201, APP-V3`，9 个会话），
与 `GRID.active` 交集为零，所以 `scan.py:1826` 对全部 9 个返回 `—`。
**它优雅降级**：不崩、不误归格，只是徽章空着，而表头承诺的是
`徽章 = 它点亮地图上的哪一格`。**所以假断言全在地图那一侧**
（13 个呼吸点 + 13 条 `在跑：` tooltip），不在 `cell_of`。

### 5. 真数据在磁盘上，地图拒绝读它（这一条比上面都重）

18 件在飞条目（`monitor/board/items/` 13 + `claimed/` 5）**每一件都在 frontmatter 里声明 `cell:`**，
其中 **10 件声明的坐标在 30 格 GRID 里真实存在**（S2、A3×2、S4×2、V2×2、S1、P5、E3）。
`scan.py` 从不读这个字段：`grep -n '"cell"'` 在主线 `scan.py` 上只命中
`:1826, :1829, :1906, :1924`，全是 `cell_of` 那条路。
**所以「画不出真在跑的」说轻了：数据在一个有文档的字段里，地图选择不读。**

### 6. 而坐标约定本身也漂了——所以naive 接线会留下 8 件放不下

`GRID_COLS` 是 5 列，合法格是 字母+1..5。但 18 件里 **8 件声明的不是坐标**：
`P17`、`A16`、`A8`、`E18`、`P18`、`S22`、`V6`，以及一个裸 `S`。
`spec.py:1180` 的规则「新工单编号即坐标（如 A3-xxx）」与
`scan.py:1893` 的 `"%s%d" % (rkey, ci)` 循环都被这 8 件破掉。
**这解释了为什么没人顺手接上它**：接上去会有 8 件无处安放，
于是那件事一直没做，而地图就一直画着旧的。

## 我起草时的两个数字是错的（留痕）

* 我最初写「12 格 / 13 个 id」——实为 **13 格 / 14 条 / 13 个不同 id**。
* 我最初写在飞条目 16 件（12+4）——那是**本地 HEAD 的陈旧计数**。
  主线上是 **18 件（13+5）**。**我自己被这轮反复强调的那个陷阱抓了一次**：
  活体盘面要用工作树，但板目录的**内容**在主线上已经变了，而我拿本地数目去配主线代码。
* 没有重复立案：32 份现存 + 归档的 `DRIFT-*` 里，地图 staffing 层零命中；
  `S28` 的 11 条也不含它。

## suggest（监控裁决，我一行代码都没动）

1. **立刻可做、零风险**：把 13 格的 `active` 清空。**画错的在跑点比不画差**——
   现在盘面告诉你 13 件事正在推进，而它们全都完成了。清空之后地图诚实地空着。
2. **正确修法**：`active` 不再手写，改从板上条目的 `cell:` frontmatter 现算。
   10 件能立刻落格。
3. **然后才是**：给那 8 件非坐标条目裁一个归属（或裁定坐标约定作废、
   换成显式 `cell:` 字段为唯一真源）。**顺序很重要**：先清空、再现算、最后补约定，
   每一步都独立可交付。
4. **`state["grid"]` 落盘这件事值得单独裁一句**：手写虚构进了被跟踪文件，
   下游任何消费者都会继承它。要么清空，要么在落盘前标注「hand-maintained, may be stale」。

## 复核命令

```bash
sed -n '1180p;1188,1224p' monitor/spec.py
for id in E1-property-fuzz P-13 C1-worldgen P-19 P-20 P-22 P-18 A2-crosscheck P-17 P-12 P-21 P3-case-study P-23; do
  git ls-tree -r --name-only origin/master | grep -i "prompts.*$id"; done      # 全部 archive/superseded-by-board/
git ls-tree -r --name-only origin/master monitor/board/items monitor/board/claimed | wc -l   # -> 18
git grep -n "cell:" origin/master -- monitor/board/items monitor/board/claimed
git show origin/master:monitor/scan.py | grep -n '"cell"'                      # 只有 cell_of 那条路
git show origin/master:monitor/scan.py | sed -n '2634p'                        # state["grid"] = spec.GRID
```
