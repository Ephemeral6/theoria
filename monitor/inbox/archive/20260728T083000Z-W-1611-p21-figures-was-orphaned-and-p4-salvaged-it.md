# W-1611 → 监控：P-21 的 figures/ 流水线是孤儿，P4 已捞回；另有三处产物漂移

工单 `P4-figures`（cell V5, territory `figures`）。分支 `agent/p4-figures`，base `1e7002d`。

## 一、发现：P-21 干完了大半，一个字节也没进 master

`figures/` 在 master 上不存在，但在 `.worktrees/wt-p21/figures/`（分支
`agent/p21-figures`）里**未提交地**躺着一整套：`theme.py`(15KB)、`sources.py`、
`build_all.py`、`manifest.py`、`verify.sh`、`PLAN.md`、`SOURCES.md`，外加两个图
脚本（`fig02` 建过，`fig03` 没建成）。

关键：仓库里的 `deterministic-figures` skill **就是从这套代码里提炼的**——它逐条
记录的正是这份契约。我若从零重写，会得到第二份与 skill 不一致的契约，而下一个人
读的是 skill。**所以 P4 选择捞回而不是重写**，捞回清单逐项记在
`figures/runs/20260728T082401Z-P4-figures/MANIFEST.json` 的 `salvage` 字段。

判断 P-21 已死的依据：worktree HEAD 停在 `dc9fad1`（落后很多），且工作板把同一件
事重新派成了 `P4-figures`。**若 P-21 其实还活着，这是一次撞车，请裁决**——我只动
`figures/`，未碰任何其他领地。

**建议**：`.worktrees/wt-p21/` 与另外约 20 个 `.claude/worktrees/*` / `.worktrees/*`
里可能还压着别的未提交成果。P-21 这一份是靠 skill 的一句 "Distilled from P-21
(`figures/`)" 才被发现的，纯属侥幸。建议派一件"孤儿工作树普查"：逐个 worktree 跑
`git status --porcelain`，把未提交产物列成清单交给板。**这类损失是静默的**。

## 二、三处产物漂移（不是我造成的，是被我撞见的）

都是同一个形状：某个产物重算了，依赖它的东西没跟着改，且没人报错。

1. **`battery/artifacts/arm_contrast.json` 已过期。** 它认 4 个臂，
   `capability_spectrum.json` v2 记 5 个（多了 `schema_repro`）。P-21 的 fig03 拿
   它当列轴权威，于是**整张图建不出来**。已改为以
   `capability_spectrum.provenance.arms` 为轴、以
   `validation_material.json` 的 `control_arms` 字段定对照/处理划分，并把
   `arm_contrast.json` 的分歧**报出来而不是吸收掉**。
   → 建议 battery 领地的人重算 `arm_contrast.json`，或在文件里标注它已被 v2 取代。

2. **`battery/README.md:25` 仍称 `REPORT_V1.md` 是"当前重算结果"；
   `battery/METRICS.md` 标题仍是 "battery v1"**，但内容是 v2.1 重生成的。
   两处指针都会把读者引向旧报告。→ 建议 battery 领地修指针。

3. **`cold-start-a0/THEORIZE_LOG.md` 的 O-04 分表与
   `artifacts/concept_accounts.json` 数字不一致**：日志说 Cart +2967 / Button −17
   / Door −13（像素基线），JSON 与 `theory.dsl` 说 +2125 / −5 / −1（责任完备基线，
   `7cc02a9` 重新计价）。日志没跟着改。图 6 用 JSON 并标明基线、同时把分歧写进
   notes。→ 属 theory-compiler 轨道，**我不动**，仅报告。

## 三、一个可复用的坑，已做成闸门

fig02 的图面注释里我自己写了 `$0.9025 ... against $0.1459`，matplotlib 把
`$...$` 当 mathtext 解析，实际渲染成斜体 `0.9025...against0.1459`——两个美元符号
消失、两个数字连在一起。

**它是确定性地错**：两遍构建字节相同，determinism 闸门全绿，diff 里也看不出来。
这是个花钱的仓库，图面上写美元金额是常态。已在 `figures/theme.py` 加
`check_no_mathtext()`，`caveat()` 每次调用先过它，撞上就 raise。建议其他画图的地
方也照做。

## 四、范围申明

- 只写 `figures/`；`baseline-arms/`、`battery/`、`cold-start-a0/`（含 `prime/`）、
  `cold-start-a2/`、`cold-start-a3/`、`theoria-arm/` 全程只读。
- 封存堆 21 局零接触：图只读开发堆四局（ar25 / g50t / sk48 / tn36）的产物，
  `capability_spectrum.json` 的 `provenance.cut.piles_sha256` 已记进图面出处。
- 零 API 调用、零花费，因此未触发花费闸门。
- 未碰 master；合并交给 ci_merge。

---

## 五、收工补记（09:05Z，交付后）

分支 `agent/p4-figures` 已推送，六张图全绿，`figures/verify.sh` 七道闸门全过。

**再补两处上游漂移**（读的时候撞见，均不在本领地，未动）：

4. **`cold-start-a3/A3_REPORT.md` 的头条数字跨了计量线。** 报告写「347 → 10 是
   头条，332 → 0 才是要紧的那个」。但 347 是 `l2_from_scratch` 的 `world_frames`，
   10 是 `l2_transfer` 的 `world_actions`——**两条不同的计量线**；而 332 → 0 是
   l1 对 l2 的**跨关卡**比较，`bill_table.json` 自己的 `note` 恰好警告过这一点。
   图 4 两个都不画，改画同关同线的 347→11 与 346→10，以及关内的 336→0。
   这不是错误，是**头条比数据松**；建议 A3 领地的人决定要不要收紧措辞。

5. **`cold-start-a3` 内部有一处数字冲突**：`A3_REPORT.md` 说 `l2-rewired`
   「solvable in 15」，`DECISIONS.md` D-A3-010 说 14，**两个数都不在任何 JSON 里**。
   图 4 一个都不画，并在 CSV 里记明拒画理由。

## 六、一条给所有画图/出产物的人的经验（这条最值钱）

**确定性闸门证明的是可复现，不是正确。** 本轮六张图全部建绿、两遍构建逐字节
相同之后，我自己写的图面注释里有三处**确定性地错**，闸门全程绿灯：

1. `$0.9025 ... against $0.1459` 被 matplotlib 当 mathtext 解析，渲染成斜体
   `0.9025...against0.1459`——美元符号消失、两个数字连在一起。两遍构建都这么错，
   所以 diff 是空的。已加 `theme.check_no_mathtext()`。
2. matplotlib 用文本模式句柄写 SVG：本机 CRLF、Linux LF，而 `.gitattributes`
   存 LF。**干净检出后在 Windows 重建会挂「已提交树 vs 新构建」那道闸门，却没有
   任何缺陷可查。** 已在写入端钉死 newline。
3. `svg.hashsalt` 钉不住被**路径**裁剪的图元 id——matplotlib 对这类 id 取的是
   `id(clippath)`，即内存地址，盐够不着。一张图里有一个 id 在两遍构建之间变了。
   已在 `theme.save` 里把生成 id 规范化成稳定序列。

另有两个只让**闸门本身**不可靠、图其实没问题的坑：`build_all.py` 往被重定向的
stdout 打了个 `†`，Python 回退到区域编码（本机 GBK）直接崩——交互跑绿、
`verify.sh` 跑挂；`--list` 输出 CRLF，导致闸门拼出带回车的路径，把刚写好的产物
全判成「缺失」。

**结论：每一张图都要渲染出来用眼睛看。** 六张里有两张的排版问题（文字压文字、
右边缘截断）是任何闸门都不会提的，只能看出来。
