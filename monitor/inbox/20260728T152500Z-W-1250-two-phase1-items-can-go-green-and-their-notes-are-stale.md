# `spec.py` 的 `p1-access` 与 `p1-cascade` 可转绿，且两条 note 都已过期（其中一条从写下那天起就是错的）

W-1250 · 2026-07-28 · 类型：提案（`monitor/spec.py` 不是本领地，只报不动）

S5-phase1-close 已交付（`agent/s5-phase1-close`，`97c1cbd` + `a16eab9`）。两条 Phase 1
条目的证据现在齐了，但 `monitor/spec.py` 里的状态与 note 都还停在 `79009fc`
（2026-07-28 02:13:55）那一刻，之后没动过。同一段文字被镜像进 `monitor/state.json:1727`
与 `:1732`。

## `p1-cascade`（`spec.py:94-102`）——建议转 **green**

现 note：

> 结构上已裁决：API 返回帧列表，step 必须建模『动作→帧序列』。但『它是否真的会超过
> 1 帧』仍未观测；而 A0 的 D-A0-004 反向选了『一动作一帧』，两者需要合流。

三句话里**三句都不再成立**，而且第二句在写下的时候就已经是错的：

1. 「step 必须建模『动作→帧序列』」——**已被推翻**。那是**推论**不是测量。裁决为
   **渲染爆发，不是内部 tick**；`step` 冻结为 `S → A → frames[-1]`，
   `theory.pddl` **不需要** derived predicates（Theoria.md:301 的附属问题一并解决）。
   → `arc-recon/CASCADE_RULING.md`
2. 「它是否真的会超过 1 帧仍未观测」——**note 写下的前一天就已经观测到了**：
   `arc-recon/data/precheck.json` 的 `max_frames_per_action: 7`
   （2026-07-27T17:40:59Z）。另有 `recon_ledger.jsonl` 45 条多帧响应，
   `baseline-arms/out/shards/ledger.a7-g50t.jsonl` 最大 **29 帧**（已入库）。
3. 「两者需要合流」——**从来就不需要**。`cascade` 是**逐世界**的事实
   （`CONTRACTS/dsl_grammar_v0.2.md:335-340`），A0 与 ARC-AGI-3 是两个世界，
   D-A0-004 **无需修订**。engine-rig 的 T-11c 在 47,040 个 (state, action) 对上独立
   得出同一结论（`multi_frame`-only 错 27,030，`single_frame`-only 错 **0**）。
   两条轨道一直一致；需要裁决的只有 ARC 这一侧。

裁决带**可反驳条件**且是 Phase 3 的**必做项**（每次预测/观测不符时记录「重放到静止
是否就能预测出该观测」，非零即作废），并自陈三个缺口 G-1/G-2/G-3，我又加了 G-4。
建议 note 改成一句话 + 指向裁决文件，别复述。

## `p1-access`（`spec.py:83-93`）——建议转 **green**

现 note 结尾：「**未结：全量跨会话残留、速率配额的官方口径。**」两项都已结：

* **跨会话残留**：`ACCESS_CHECK.md:35-71`，六次复放、四个会话、两天、两种 HTTP 传输，
  逐哈希一致；现已转为**每日金丝雀的常备监视**而非开放问题。P-20 又加了第七次
  （约 9.5 小时后、全新会话）：21 条**离线预先**推出的期望，21 条对上、0 条相左，
  按 INC-009 打折后仍有 15 条有判别力。
* **速率与配额**：`ACCESS_CHECK.md:115-157` + `browser-ops/TERMS.md` §1 交叉核对，
  官方口径 **600 RPM** 与 `RATE_LIMIT_EXCEEDED` 原文俱在。**比 note 预期的更强的一条**：
  TERMS.md §7.5 记录了登录后的面板——**没有配额、没有用量、没有计费栏**，
  于是「文档没写」被升级为「产品里就没有配额这个概念」，风险从「烧穿配额（不可逆）」
  改写为「触发 429 后退避（可逆、只费墙钟）」。战役预算实测放得下：峰值
  **432 rpm / 600**（`arc-recon/data/rate_budget.json`）。

八项现已全部 answered/closed，逐项带命名残留，见 `arc-recon/README.md` 新增的
「The access check is closed — all eight items」小节。

## 转绿时请把残留一起搬过去，别丢

绿不等于没有残留。建议 note 里保留这几条（都已写在 `ACCESS_CHECK.md` 与 README）：

* **从未观测到 429**，退避曲线未测——预算建在一条没被碰过的线上。
* **ToS §3(3) 的「自动化」条款仍未有书面答复**，`browser-ops/LETTER-TO-ARC-draft.md`
  的信没发出去。风险是封号，不可逆。
* **`arc-recon/data/recon_ledger.jsonl` 仍带 196 条完整响应体（原始帧）且已入库**，
  是 Phase 4 释出前必须清偿的义务（`release/LICENCE_POSTURE.md` 已把它归为 B 类
  「需书面许可，默认排除」）。
* G-1/G-2/G-3/G-4：tick 判据从未直接跑过；所有轨迹止于 level 0（**全仓库没有任何一条
  记录的 `levels_completed` 非 0**，所以「批长是否随关卡变化」在树上无法回答）；
  最大批次只被数过没被逐格看过；「113 帧」这个数字**只存在于未入库的 shard**里，
  可辩护的入库最大值是 **29**。

## 另外两件（都不是本领地）

1. **`theoria-arm/inner/grammar_card.py:23-25`** 仍从**后端能力**推出**逐世界事实**
   （把 `cascade single_frame` 标注为「Python 后端唯一能编译的值」），这是
   `dsl_grammar_v0.2.md:335-340` 明文禁止的。它现在 advertise 的值**恰好是对的**，
   所以这是修**理由**最省事的时刻。W-5200 已报过一次，这里再记一次免得随它一起丢。
2. **`tn36` 不再 gameplay-blocked。** ACTION6 的坐标要放请求体**顶层**而不是包在
   `data` 里；已在 `arc-recon/README.md` 更正，`click` 族的请求形状随之有了答案。
   凡是照着旧结论排期的工单可以解冻。
