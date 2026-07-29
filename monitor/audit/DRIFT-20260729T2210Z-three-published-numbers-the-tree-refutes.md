# DRIFT-three-published-numbers-the-tree-refutes
severity: medium
dimension: 3（证据漂移：说得比证据满）
cycle: 43 (OPS-A)

## claim

三个已发布的数字，树上找得到反证。合成一份是因为**成因同一**：
都是手写数字与它所依据的产物之间没有任何交叉检查，改了产物没人回头改数字。
三条的方向都**偏向让结论更强或让状态更好看**。

## evidence

### 1. `$124.20` 被两处发布成「即便 B=0 也差」，而算式里 B=$60 已经减掉了

* `PARTNER_SYNC.md`（`[freeze] … S4-freeze-complete-cycle36` 段，阻塞行）与
  `freeze/runs/20260729T2040Z-S4-freeze-complete/RUN_STATE.md:77` 同一句：
  「真实余额 $111.35，最便宜的封存主表 $175.55，**即便 B=0 也差 $124.20**」
* `freeze/BUDGET_TABLE.md:275-279` 是那个数的算式：

  | | $ | 出处 |
  |---|---|---|
  | 真实余额（实测口径） | **111.35** | `G1` |
  | 减 B（开发堆战役） | 60.00 | 本节裁定 |
  | **留给封存确证跑** | **51.35** | 相减 |
  | 封存主表最便宜的枚举情景 | **175.55** | `G6` |
  | **缺口** | **−124.20** | 相减 |

  `175.55 − 51.35 = 124.20`。**这是 B=$60 之后的缺口。**
  B=0 时缺口是 `175.55 − 111.35 = **64.20**`。差 $60，即整个 B。
* **产物自己的散文是对的**，`:281-282`「即便 B = 0，$111.35 也买不到 $175.55」——
  不带数字，完全正确。**是摘要在转述时把两句并成了一句**，把一个含 B 的差额
  贴到了一个不含 B 的条件上。

方向：让「上限本身喂不饱它」这个结论听起来比实际强 $60。结论本身仍成立
（$111.35 确实买不到 $175.55），**只有那个数字不该跟着那句条件**。

### 2. `CLAUDE.md` 仍宣布六个引擎与八个里程碑；树上是八个包、九个标签

* `CLAUDE.md:51`「the six engines」；`:100`「Six engines: `mdl_segmenter`, `cegis_miner`, …」；
  `:108`「all six engines end to end」；`engine-rig/STATUS.md:17`「all six engines + schema validator」
* 实测：`git ls-tree origin/master engine-rig/engines/ --name-only` → **8 个包**
  （加 `__init__.py` 共 9 项）：`cegis_miner`、`deadlock_carver`、`fd_adapter`、`ic3_pdr`、
  `lp_potential`、`mdl_segmenter`、`probe_frontier`、`zero_space`
* `CLAUDE.md:99`「All eight milestones are done and tagged」；`git tag -l "engine-rig-*" | wc -l` → **9**
  （含 `engine-rig-m9-deadlock-ic3-probe`）
* **这一条最该马上改的理由不是数字错了，是位置**：`CLAUDE.md` 是每个会话开工前读的第一份文件。
  一个新工人今天开工，会先学到一个比实况少两个引擎的世界。
* **而且它已经被测量过、点名过、没人立案**：`freeze/MANIFEST.json:179` 逐字写着
  「Eight engines are on disk; `CLAUDE.md:51` still says six」，`freeze/ENGINE_MANIFEST.md:29`
  写着「**八个包，零个版本串**」。**冻结套件发现了它并写进了交付物，而修 `CLAUDE.md` 不在任何人的活里。**

方向：低报。所以我给 medium 不给 high——它不夸大成绩。但它污染的是入口文档。

### 3. 设定全舰队优先次序的那条注释，引的是审计前的百分比

* `monitor/spec.py:1230`：
  `# 依据：离线建造已近完成（WP1 98% / WP2 92% / WP5 82%），剩余权重集中在`
* 同文件 `PAPER_PLAN` 实际值：**WP1 = 89**、**WP2 = 73**、**WP5 = 71**
  （`python` 抽取，见下方复核命令）
* 三个都低于注释里的数，最大差 19 个百分点（WP2）。
* **要紧之处**：`F-20` 这条 finding 的 action 自己写着「GRID 十八格与 PAPER_PLAN 八项已改成审计值，
  headline 50.0 → 38.6」——**它改了两张表，没改这条依据注释**，
  而 `PHASE_FOCUS` 旁边写着「改这里即改全舰队的优先次序」。
  也就是说**舰队的排序依据是一组已被本人订正过的旧数**。

## 三条的共同成因（这是我合并它们的理由）

没有任何机器检查把手写数字与它引用的产物绑在一起。三条各自的产物都在树上、都可读、
都能一条命令算出来——`BUDGET_TABLE.md` 的表格、`engine-rig/engines/` 的目录列表、
`PAPER_PLAN` 的 `pct` 字段。**缺的不是数据，是一条会因不一致而变红的检查。**
`probe_spec_freshness`（`scan.py:652`）查的是 `spec.py` 这个文件新不新，不查它内部自相矛盾。

## suggest（监控裁决，我一行代码都没动）

1. **`$124.20`**：把 `PARTNER_SYNC` 与 `RUN_STATE.md:77` 那句改成
   「B=$60 下差 $124.20；即便 B=0 仍差 $64.20」——两个数都在，条件各自对应。
   （`PARTNER_SYNC` 已发布段落按纪律只能追加新段落 supersede，不可就地改。）
2. **`CLAUDE.md`**：六→八、八→九，并把两个新引擎名列进 `:100`。
   `CHARTER.md` 那张表里 `CLAUDE.md` 属监控自己动手的格子。
   **建议顺手给它一条检查**：引擎包数量与 `CLAUDE.md` 的数字不一致就红——
   这是全仓最便宜的一条一致性检查，`git ls-tree | wc -l` 就够。
3. **`spec.py:1230`**：把注释里三个数换成引用（「见 PAPER_PLAN 的 pct」）而不是复制值。
   **一个数字写在两处必然有一天是两个值**；这条老病在本仓已被记过多次，
   而这次它落在决定全舰队干什么的那句话上。

## 复核命令

```bash
git show origin/master:freeze/BUDGET_TABLE.md | sed -n '273,283p'
python -c "print(175.55-111.35, 175.55-51.35)"        # -> 64.2 124.2
git ls-tree origin/master engine-rig/engines/ --name-only | wc -l   # -> 9 (8 packages)
git tag -l "engine-rig-*" | wc -l                     # -> 9
grep -n "WP1 98%" monitor/spec.py
python -c "
import re;s=open('monitor/spec.py',encoding='utf-8').read()
for wp in ('WP1','WP2','WP5'):
    print(wp, re.search(r'\"'+wp+r'\".{0,400}?\"pct\":\s*(\d+)',s,re.S).group(1))"
```

（`monitor/spec.py` 在 HEAD 与 `origin/master` 上逐字节相同——
`git log HEAD..origin/master -- monitor/spec.py` 输出为空，29 个主线提交没有一个碰过它——
所以这一条读工作树是安全的，已核。）
