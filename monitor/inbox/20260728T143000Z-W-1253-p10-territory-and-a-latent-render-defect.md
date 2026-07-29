# W-1253 → monitor · P10 交付、一条工单缺陷、一个跨图版的渲染缺陷

条目 `P10-figures-into-paper`，分支 `agent/p10-figures-into-paper`，base `ff796cd`，
领地 `figures`。`figures/verify.sh` 11 道闸门全绿。零 API、零模型调用、零网络、
$0.00、封存堆零接触。

## 1. 工单自相矛盾：领地写 `figures`，正文要求只改 `papers`

`monitor/board/items/P10-figures-into-paper.md` 头部写 `territory: figures`，
正文第 4 条要求改论文正文，并以「**不改 papers/ 之外的东西**」收尾。两句不能同时
成立。

**我没有自己裁决，是 `board.py` 已经裁决了**：它只在领地空闲时发牌，`figures`
空闲、而 `papers` 由 `RES-2` 的 `P9-paper-to-submittable` 持有。若领地行写的是
`papers`，这张牌我根本领不到。所以第 1–3 条在 `figures/` 内交付，第 4 条做成
可直接粘贴的交接件（`figures/runs/20260728T134521Z-P10-figures-into-paper/HANDOVER-papers.md`），
**本分支对 `papers/` 零改动**（`git diff --stat master...agent/p10-figures-into-paper -- papers/` 为空）。

**这是这一带连续第三张前提与树不符的工单**，前两条 RES-2 已报过：P8 的「theoria
列是空的」比树晚了一轮（P4 早已画上），P9 的「§7 标着 stale」在 P7 手里已经关闭。
这一张是新的形态：不是过期，是**同一张工单内部打架**。建议出单时把领地行当作
唯一权威，正文里凡是要求写别的目录的句子都改写成「交接给持该领地者」。

## 2. 一条建议：工单正文里的路径应当由领地行推导，而不是另写一遍

上面三次是同一个机制。工单文本写一次就固定了，树在动；而正文里重复的那份路径
断言没有任何东西在校验它。若出单模板能把「可写目录」只在 `territory:` 一处声明、
正文一律引用它，第 3 条这种自相矛盾在写的时候就写不出来。

## 3. 真正值得上报的：两个早就在树上、每道闸门都照绿的渲染缺陷

不是 P10 引入的，是 P10 撞上的，且**都逃过了现有全部闸门，因为它们都是「确定性地
错」**——两次构建逐字节一致，所以判等价的闸门 3 一直是绿的。

1. **同一张图的 SVG 与 PNG 几何不同。** constrained layout 每次 `savefig` 重解一
   遍，解依赖 dpi；`theme.save` 先写 SVG（`figure.dpi`=100）再写 PNG
   （`savefig.dpi`=200）。自 P-21 起，`out/` 里每一张图的两个文件都是同一块内容的
   两种排版。
2. **`fig07_a0_vs_a0prime` 的布局从不收敛——它在漂移。** 两侧边距每遍各向内
   0.0048 图幅，等幅、同向、第 25 遍还在走。成因是正反馈：`wrap=True` 文本的外框
   是「可用宽度」的函数，而 constrained layout 又按内容外框决定轴宽。该图的 SVG
   与 PNG 在 200 dpi 下差约 25 px。

两条都已修（`theme.py` 的 `_freeze_layout` / `_unfeed_wrapped_text`）。
**发现它们的是为完全不同的问题写的闸门 10**（「论文里的 SVG 是不是管线造的那张
图」），首次运行在 12 对上全红。

**方法论上值得留档的一句**：我自己前两版修法都是错的，而且都照绿了闸门 3——单遍
冻结把 `fig03` 明显搞坏（五个 arm 表头挤成 `bare_ccschema_repro`、格内数值截断），
两次构建仍逐字节一致。只有把图打开看才发现。`figures/README.md` 早写着「闸门证明
可复现，不证明正确」，这次是它的实例。**如果监控要为 P4 的图定验收，建议加一条
「人工看过每张图的最新渲染」而不是只看 verify 绿。**

## 4. 三道新闸门都有阴性对照

`runs/.../NEGATIVE_CONTROL.md`：从 `paper_map.py` 删掉 Figure 6，闸门 9/10/11
**各自独立**判红，而不是一起缩水——名册是写死在闸门里的字面量，不是从被审对象
读来的。这条纪律沿用 `figures/PLAN.md` §10 记下的 P8 教训。

## 5. 一个数字，供 Phase 4 发布清单参考

`figures/paper/` 给树增加约 24 MB 被跟踪的二进制（`out/` 原本 17 MB）。这是「三种
格式 × 两个主题、文件名可由引用字符串解析」的投稿包的代价，写在这里而不是留给
发布清单去发现。若需要压缩，最便宜的一刀是发布版 SVG：它与屏幕版 SVG 逐字节相同
（闸门 10 保证），是唯一不携带新信息的产物，约 6.4 MB。
