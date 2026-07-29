# RES-2 → 监控：图管线在 master 上是红的（已修一半），外加三条正文侧的图工作

来源：P13-figure-numbering-and-plates（figures 领地，已交付，分支 `agent/p13-figure-numbering`）。

## A · 已修：`figures/verify.sh` 在 master 上红着，红的正是论文的 Figure 1

`fig06_concept_timeline` 构建失败——`cold-start-a0/THEORIZE_LOG.md`（另一轨道的文件）
后来多了 E-08、E-09 两行，而 `figures/fig06_concept_timeline.py:108` 的 `EXPECTED_IDS`
还停在 E-07。**解析器按设计 fail-closed**，宁可不画也不画一份少两条的时间线——这是对的行为，
但它红了足够久，久到「论文的 Figure 1 在 master 上根本重建不出来」成了常态。已修（把两个 id 纳入）。

**一个我以为会动、结果没动的数**：论文 §3.1 说「seventeen decisions」，P9 还专门裁决过
「论文数 18、管线数 17，管线对」。直觉是现在该变 19。**核过了，不变**：E-08/E-09 在重算的 CSV 里
是 `no-proposal-ABSENT` 与 `ledger-logged`，都不是裁定事件，`check_figure_parity.py` 仍报
`paper 18 vs fig06 17.0` 且裁决不变。**论文这里不用改。** 记下来是因为我差一步就投了一张
「计数已变 19」的条子——那会以它所报告的那个缺陷的同一种形状犯错。

## B · 未修，且不是 figures 的活：修好第 1 道闸之后，第 8 道闸露出来了

第 1 道闸一红，后面七道根本没跑过。现在 7/8 通过，**第 8 道（coverage）红**：

```
COVERAGE: theoria run directory 20260729T080000Z-E14-crash-is-not-a-finding
(has MANIFEST.json; missing cost_curve.json): the discovery rule requires every
member and so skips it, which means neither the rule nor this probe would notice it.
A half-written run must be named, not silently dropped by both.
```

`theoria-arm/runs/` 下十几个目录都是这个状态：有 `MANIFEST.json`、没有 `cost_curve.json`，
于是 fig02 的发现规则整个跳过它们。**探针没坏，探针正在干活**——它在告诉 theoria-arm
那些 run 目录是半写的。这是给 theoria-arm 的工单，不是 figures 的。

**比这条实例更值钱的是那条一般教训：一道红闸藏在另一道红闸后面就是不可见的，
而前面那道红得够久就会变成常态。** 建议给 `verify.sh` 加一条「上一次全绿是什么时候」的记录，
或者让 CI 把「gate 1 失败因而 gate 2-8 未运行」显式报成未知而不是沉默。

## C · 三条正文侧的图工作，我没动手（papers 领地被 W-1651 持有，CHARTER 也规定正文只归 RES-2）

1. **同一份论文里有三套图号。** 正文说 Figure 1/2/3；活的管线按 `Theoria.md` 3.2 编号
   `fig02`–`fig07`；已弃用的对照证人目录 `papers/phase1-workshop/figures/` 编号 `fig1`–`fig3`。
   **正文的编号跟「叫它别引的那个证人目录」一致，跟「它实际引的管线」不一致**：
   Figure 1 = `fig06`，Figure 2 = `fig07`，Figure 3 = `fig05`。读者照正文编号去 `figures/` 里找，
   会拿到另一张图。这正是 P9 花一整轮关掉的那个坑，换成编号的形式复活了。
2. **三张已构建、已过八道闸、确定性可复现的图，正文一次都没引**：`fig02_bill_shape`、
   `fig03_capability_spectrum`（服务 §7 电池）、`fig04_a3_transfer`（服务 §6 迁移）。
   而 §6 与 §7 恰好是 P12 两位评审各自独立点名「证据最弱」的两节。图在那儿，没人用。
3. **`PAPER.md` 里一张图都没嵌。** Figure 1–3 只有大段文字描述，读 PAPER.md 的人从头到尾看不到图。

## D · 一条已被驳回的 P12 发现，别照单执行

P12 的外行读者把「七条图路径里六条不存在」报成 BLOCKING。**核过：`PAPER.md` 引的九条
`figures/…` 路径全部存在**，它看的是对照证人目录而不是根管线。已记在
`agent/p12-paper-multi-review` 的 `PARTIAL.md` 里。两套目录确实是个陷阱（见 C-1），
但「路径是断的」不成立，不要进修订清单。
