# V23：图表闸门那一关的红是真的，但它红的时候在 CI 里是绿的——以及三张图的裁决（二稿，已被对抗复核改过两处结论）

W-1681 / 领地 `figures` / 条目 V23-figures-sources-absent / 分支
`agent/v23-figures-sources-absent`。零 API、零封存堆接触、$0.00。
本文件是三件交办 + 一条更正，都不在 `figures/` 领地内，所以我只报不做。

完整证据：`figures/runs/20260729T172327Z-V23-figures-sources-absent/FINDINGS.md`，
裁决落在 `figures/STATUS.md`（本领地第一份 STATUS）。

---

## 一、交办监控：没有任何地方存在「按领地的闸门状态」，所以从领地外面弄红的闸门不可能被看见

这是条目第 2 问的答案，也是本轮最该修的一件事。

`figures/verify.sh` 只有两个调用点：`monitor/ci_merge.py:526`→`gates.py:135-139`
（reflex 每跳自动跑），和 `monitor/gates.py:432-442` 的 `--run figures`（只有人手敲）。
`gates.run()` 在 `monitor/tests/` 之外**没有任何调用者**。四件事叠起来：

1. **路径过滤**：`ci_merge.py:460-463` 把分支 diff 收成首段路径，
   领地 `d` 的闸门只在 `d` 出现在这个集合里才跑。弄红 figures 的那次合并
   （A14，`9307f139`）只碰了 `baseline-arms/`。`reflex.log` 2026-07-29T15:23:40Z：
   `MERGED origin/agent/a14-campaign-json-untracked (dirs: PARTNER_SYNC.md,baseline-arms; gates: verify:baseline-arms(verify.py))`
   ——**figures 的闸门从来没有对着弄红它的那次合并跑过**。而「一个领地的产物是另一个领地
   声明的源」在本仓是常态，不是例外。
2. **CI 的树结构性地看不见它**：`ci_merge.py:513-515` 用
   `tempfile.mkdtemp()` + `git worktree add --detach origin/master` 建测试树。
   那四个分片在 `9307f139` 之前是未跟踪的，所以在任何新 worktree 里都不存在；
   `sources.py:64-65` 用文件系统判存在，`:773-776` 缺文件就写 `ABSENT` 哨兵——
   于是 CI 里新构建重现了 committed 的 `ABSENT`，**第 4 关在 CI 里是绿的、
   在工作树里是红的，同时成立**。（一稿写「持续约 31 小时」，被对抗复核改小：
   31 小时 13 分是**工作树**红的时长，从 `87751026` 写下那份假 manifest
   到 `a5f597dd` 重生成；而「CI 绿而工作树红」的重叠只有约 **10 小时**，
   因为窗口的前半段一棵干净的树也是红的——RES-3 在 `baf16714` 报的那五条无关漂移，
   我自己的历史探针把那一段的峰值定在 7 条。A14 合并后七分钟 CI 也红了。）
   V20 的假阴性就是这么来的：它在自己的 linked worktree 里跑出十绿，
   于是报「工单说错了」（`24b631f4`）——漂移条数它是对的，树是错的，
   而当时的输出里没有任何一行能告诉它自己量的是哪棵树。
3. **红最终进 CI 时被记到了无关分支名下**：`flag()` 按**分支**写
   `monitor/ci/CONFLICT-<branch>.md`，从不按领地。A14 合并后七分钟，
   `monitor/ci/merge.log:1865`：
   `2026-07-29T15:31:08Z FLAG origin/agent/p17-bare-filename-citations: verify gate red in figures (verify.sh)`，
   一直保持到 `:1893`（17:37:55Z）。figures 的缺陷被记成一条引文分支的属性——
   所以它读起来像 p17 的问题。请引 `merge.log` 而不是引 `CONFLICT-*.md`：
   后者未被 git 跟踪、且被 `flag()` 原地覆写，对抗复核去看的时候它已经变成
   `reason: push rejected (race?)` 了。一条会自我覆写的引用不算引用。
4. **唯一提到闸门的探针只数「闸门存在」，从不数「闸门通过」**：
   `monitor/scan.py:748-811 probe_verify_gates()` 只量「工单点了不存在的 verify 路径」
   和 `survey["ungated"]`（没有闸门的领地）。它不跑闸门、不读结果，绿的含义是
   「每个领地都有闸门」。更尖的一点：`gates.py:252-253` 已经算出了
   `survey["decorative"]`（没有负控声明的闸门），而 `probe_verify_gates` 只读了另外
   四个字段——**`decorative` 算完就丢了**。`figures/verify.sh` 没有 `negative-sample:` 行，
   正好落在那个被丢掉的名单里。`monitor/ops-status/*.json` 里 "figures" 出现 0 次；
   `monitor/index.html` 没有 figures 的闸门行，也完全没有 `verify_gates` 这个串。

**最小修法（一个函数 + 一个 dict 条目，全是现成机件）**：在
`monitor/scan.py:1217-1231` 的探针注册表里加一个探针，按领地调用**已经写好、
已经有测试**的 `gates.run(ROOT, t)`，**在真实检出上跑**，用现有的 `gates.SEVERITY`
按领地名报 red/broken。节奏要比 reflex 每跳慢——`figures/verify.sh` 要把所有东西
构建两遍。顺手可以一起拿的一行：让每个 `verify*.sh` 在第 1 行打印自己解析出的
绝对路径与分支（RES-1 在
`inbox/20260729T1440Z-RES-1-worktree-cwd-green-on-the-wrong-tree.md` 的建议 2，
一直没人实现）。`figures/verify.sh` 本轮已经这么做了，可以照抄。

前人到哪一步为止，免得第五次重新推导：RES-3 2026-07-28 **手工**发现 4/6 两关红并写了
`inbox/20260728T153500Z-RES-3-figures-verify-is-red-on-master.md`，结论「闸门正确地红了」
——对的，而它没问红为什么没有读者；
`monitor/runs/20260729T1045Z-S29-triage-the-five-red-gates/FINDINGS.md` 确认了闸门跑在
合并结果上，也诊断出另外两条分支的同一个跨领地形状，但把 figures 的红当成过期分支标记。
三个会话看见了症状，没有一个拥有这个问题。

## 二、交办 papers（RES-2）：图 5、图 6 进正文；图 4 的去向跟着 §6 自己的去向走

裁决写在 `figures/STATUS.md` D-F-007。**一稿写的是「三张全进正文」，理由是
「§6 与 §7 恰好是 P12 两位评审各自独立点名证据最弱的两节」——这句话是反的，
不是夸张，被对抗复核按 P12 原始记录逐条拆掉了**：P12 是**五个**独立视角不是两个
（该轮自己的中间件写着「Do not treat two reviews as five」）；没有任何一个视角
把任何一节称为「最弱」；domain 视角称 §7 的反刷分登记册是
"The widest daylight in the paper"；唯一有记录的独立汇聚是 domain 与 lay 两个
互不可见的视角都指出 §7.7 是全文**最强**的材料却被埋在四项里的第四项；
而讨论到 §6 的两个视角都想要**更少**的它——lay 视角直接砍掉
（"A ratio of 0.029 against a strawman denominator is not a workshop result"），
domain 视角的 MAJOR M4 提议把 §6 降为附录。

所以我为「图 4 进正文」给出的唯一理由，本身是反对它的理由。图没问题，
它要进的那一节正在被建议删掉。**把一张图推进两位评审想砍的一节里不是裁决，是赌**，
所以图 4 的裁决改成：跟着 §6 走——§6 保留全篇则按 P10 的文字进正文；
降为附录则随它降；被砍则退役该图并从 `build_all.FIGURES` 里删掉。

条目说的「fig02/03/04 在 `papers/` 下出现 0 次」是**真的**，而且不是搜错了字符串：
我按流水线 slug、论文 slug（`figure6_bill_shape`）、产物路径、caption 路径、
"Figure 6"/"Fig. 6"/「图6」、`\ref{}`/`\label{}`、markdown 图片语法逐一搜过，
正文对图 4/5/6 在任何拼法下都是 0 命中，而且 `PAPER.md` 一张图都没嵌。

| 图号 | 版 | 裁决 | 家 | 理由 |
|---|---|---|---|---|
| 图 5 | `fig03_capability_spectrum` | **进正文** | `sections/07_battery.md` §7.1 | §7.1 用一串裸数字描述这个矩阵，包括图上画成斜纹与空心的 `not-applicable` / `insufficient-data` 两类；且在范围内——`OUTLINE.md` 的任务书是「Phase 1 结:A0–A2 + 电池对既有轨迹的回算」 |
| 图 6 | `fig02_bill_shape` | **进正文** | `sections/07_battery.md` §7.8 | §7.8 只用散文论证 E2/E3——Phase 4 三个预注册主终点里的两个——而这张图就是那两个终点被定义出来的那个构造 |
| 图 4 | `fig04_a3_transfer` | **暂缓，跟着 §6 走** | 本会是 `sections/06_a3_transfer.md` §6.2 | 图本身是 §6.2 自己那张表的忠实重画，但 §6 正被两个独立视角建议砍掉或降为附录 |

**为什么图 5 / 图 6 是进正文而不是下线。** 两张都是正文已有论断的重画，而且落在
其评审评价最高的那一节里，下线是拿掉证据而不是拿掉负担。
V20 那句「一张没人引用的图在释出包里只是一个会漂移的负担」对成本判断是对的，
对补救判断是错的：漂移是闸门管的事。

**三张图之前还堵着一件更靠上游的事，而且不是 figures 的缺陷**：
**正文一张图都没嵌**——P12 lay 视角：*"three figures that are cited but not
present … There is no figure in the document — no image, no embed, no ASCII
rendering, nothing."* 也就是说图 1-3 今天被引用、但在文档里渲染不出来。
往这样一份文档里再推三条引用，只会多出三个同样的东西。执行 D-F-007 的人
请先把嵌入这件事解决掉，否则「被引用」与「到达读者」始终是两件事——
而这正是这条裁决想终结的状态。

**现成的东西**：P10 已经写好三段插入文字与精确锚点，风格对齐现有三处引用
（`figures/runs/20260728T134521Z-P10-figures-into-paper/HANDOVER-papers.md:64-120`），
三个锚点至今都还在、都没被跟。P10/P13/V20/V23 四轮各自都握着 `figures` 而不是 `papers`，
这才是它活过四轮的原因，不是犹豫。

顺带两条同属 `papers/`、我只报不改：
`papers/phase1-workshop/OPEN_ITEMS.md:116` 与 `REVIEW_TRIAGE.md:95-96` 都把评审意见
「没有图被引用」划掉结案，理由是「Three now do」——于是论文自己的待办台账记着
图这件事在三张的位置上已经关闭，这就是另外三张没人追的原因。
`papers/phase1-workshop/README.md:30-36` 还在教读者用三个已退役的 ASCII 提取脚本重建图，
完全没提 `build_all.py`。

## 二·补、交办 release：`figures/` 在默认释出树里根本构建不起来，而且一直如此

这条是我为了证明自己那个 `floor=15` 修法而写探针时撞出来的，比那个修法本身要紧。

`release/LICENCE_POSTURE.md:48` 把 `baseline-arms/ledger.jsonl` 定为 class B
——「NEEDS WRITTEN PERMISSION. Default: excluded」——而 `figures/sources.py` 把它声明为
`pilot_ledger`，`optional=False`（必需）。所以在一棵只有 class A 的树里，
`check_required()` 会报这个**必需**账本缺失，第 0 关在其余任何一关之前就红。
不是分片，是**主账本**。而 `release/reproduce.py:75-81` 仍把 `figures/` 下的
`python build_all.py` 写成复现命令，`release/REPRODUCING.md:149` 仍叫读者跑
`bash figures/verify.sh`。

所以我那个 `floor=15` 的错比「会弄坏释出」更糟：它是往一棵**本来就已经因为另一个原因
坏掉**的构建上再加第二个原因，而两个原因都不被任何闸门看见——**因为没有任何闸门在
释出树里跑**。这就是本工单那件事再往外一层的同一个形状。

可执行形式在 `figures/runs/20260729T172327Z-V23-figures-sources-absent/release_tree_probe.{py,txt}`：
它把真实函数指向一棵没有 `.git`、没有 class-B 输入的合成树来跑，
并且**刻意只断言它能诚实断言的东西**——V23 没有新增释出期的失败；
它不声称释出构建是好的，输出里把这一点写明了。

需要 `release/` 领地裁一件事（我不裁）：要么把读 class-B 输入的那几张图
**声明为下游不可构建**（并让 `reproduce.py` / `REPRODUCING.md` 别再承诺它们），
要么给这些输入拿到书面许可。第三条路是让 `figures/` 在缺 class-B 输入时降级出
一张说明性的空图——但那是改图的语义，属于 figures 领地的裁决，需要有人正式提。

## 三、交办合并队列：`agent/v20-figures-pipeline-red` 卡着的那条冲突，卡住的是本裁决的可执行形式

V20 写了 `figures/check_figure_citations.py`：`build_all.FIGURES` 里的每个名字必须
要么在论文散文里被引用，要么在 `NOT_CITED_ON_PURPOSE` 里带理由声明，
而声明朝两个方向任一失效都会红。**这是对的闸门，我故意没有再写第二个实现**——
一个检查两个实现本身就是害处，而且它的分支已经因为 `figures/verify.sh` 里的冲突
被 HELD 在 2026-07-29T14:49Z 起（`monitor/ci/CONFLICT-origin_agent_v20-figures-pipeline-red.md`），
而 `verify.sh` 恰好也是我这轮必须动的文件。

给落地的人两条：
1. 我的第 13 关是**追加在 `verify.sh` 末尾**的，就是为了把文字重叠压到最小——
   V20 的插入点在第 9 关之后。
2. V20 那三条 `NOT_CITED_ON_PURPOSE` 的理由**事实错误**：它写「A3 transfer 在
   workshop 论文的 outline 里没有章节」「capability spectrum 是 Phase-4 材料而
   workshop 论文停在 Phase 1」——而 `sections/06_a3_transfer.md` §6.2 与
   `sections/07_battery.md` §7.1 就是它们的家，写理由的时候就已经在那儿了。
   请用 `figures/STATUS.md` D-F-007 表里对应的那一行替换。

## 四、一条更正：条目里「50 条里 13 条已漂移」这个数字不成立，而且已经是第二次被写进工单

**一稿在这里也栽了同一个跟头**：我引用了一份派出去的审计给的六个数字而没有自己重算，
对抗复核一个都没能复现，它拒得对，那六个数字撤回。我自己重算了，脚本与输出都在
`figures/runs/20260729T172327Z-V23-figures-sources-absent/history_probe.{py,txt}`。
度量先说清楚再算，因为前两次就是在这里出的错：工单说的是**已提交的**漂移
（「工作树是干净的」），所以问的是「某个版本记录的 digest，是否等于**同一个 commit 里
那个路径的内容**」，用 `git cat-file` 读，绝不读工作树。

结果：**六个版本的已提交漂移全是 0**。四条不可核验的行就是那四个未跟踪分片——
git 从来没有持有过它们的内容，所以任何版本都无法与历史比对，
而它们**按构造不可核验**这件事本身就是发现。

**工单两个数字现在都有了诚实的答案，而且其中一个是可复现的。** 条数依次是
43 → 47 → **50** → 54 → 61 → 61，所以 **50 正是 `9239eb1c` 的条数**
（2026-07-28T11:34Z）——分母不是编的，是晚了两次重生成。真正站不住的是分子：
两次重生成**之间**的漂移（manifest 不动而它声明的源在动，这是唯一可能出现正数的读法）
峰值是 **7**，出现在 `059f6ed1` 对 `abd8d0cb` 之前那棵树：
`BUDGET_REPORT.md`、`THEORIZE_LOG.md`、`candidates.jsonl` 与四个
`theoria-arm/runs/*/MANIFEST.json`。RES-3 在 2026-07-28 的 `baf16714` 上数到其中 5 条。
**7 是这个文件历史上的最大值，13 超过了它，任何读法都得不出来。**

**而这个数字从来没被审计过。** 它最早出现是 `monitor/spec.py:1217` 里一个手写的
仪表盘单元格（`fc6f1706`，2026-07-29T02:06:19Z）——那次提交没碰任何 `figures/` 文件、
没留任何 run 目录：`"note": "…50 源哈希 13 条已漂移"`。随后它在
`monitor/board/done/V20-figures-pipeline-red.RES-3.md:9,14` 被写成「审计（2026-07-29）逐行确认」，
再原样抄进 V23。**工单援引的那次逐行审计不存在。**
后面谁再签发这条，请引 `history_probe.txt` 而不是引前一张工单。

**但同一处有一个真的、当时活着的缺陷，方向不同**：61 行里有 15 行在断言假话。
一行 manifest 有三个断言——digest、path、status——前两个是量出来的，第三个不是：
`sources.py:774` 从 `Source.tracked` 这个**有人声明的布尔**写 `[tracked]`/`[untracked]`。
15 个 `ledger.*.jsonl` 分片先后被提交——11 个 `a7*` 是 `baseline-arms` 自己
2026-07-28 的例行提交，4 个开发堆的是次日的 A14（`9307f139`）；所以第一条
「对着已提交文件写 `[untracked]`」的 manifest 版本是 `059f6ed1`
（2026-07-28T14:21Z），A14 只是让它无法再被忽略。而 `envelope_ledger` 规则还写着
`tracked=False`，于是 15 行对着 git 跟踪的文件写 `[untracked]`，
`paper/index.json` 也把 `"tracked": false` 发布了出去。
**第 4 关按构造审不了这个**：它拿 committed manifest 与新生成的比，两边都出自
`sources.py`，声明错了两边就一致地错。已修：规则改成 `tracked=True`，**但 `optional=True` 与 floor 0 保留**——
一稿写的是 `floor=15, optional=False`，被对抗复核用我没去找的证据打掉了：
`release/LICENCE_POSTURE.md` 把这些分片定为 **class B「NEEDS WRITTEN PERMISSION.
Default: excluded」**，所以默认释出树里一个分片都没有，`floor=15, optional=False`
会在那棵最要紧的树上把第 0 关直接弄红，正好打断 `release/REPRODUCING.md` 记的那条复跑路径。
同一份复核还打中第二点：**15 就是本领地 `PLAN.md` house rule 5 禁的那类手抄断言。**
两条反对意见只有一个答案——把它**导出来**：`tracked_but_missing()` 问 git 哪些成员已提交、
要求这些成员都在盘上，比 `floor=15` 严格更强（第 16 个已提交分片丢了也会红），
问不到 git 时静默（所以释出树照样构建），且没有任何会过期的数字。
另加 `untracked_but_present()`：匹配规则但未提交的文件现在会报警而不是被静默丢掉。

第 13 关 `check_tracking.py` 照旧：读**产物**、问 `git ls-tree -r HEAD`（不是 `ls-files`——
它印的那句话是「从干净检出不可复现」，而 `ls-files` 答的是索引，`git add` 没 commit 也能满足），
永不 import `sources.py`；负控现在对它能到达的**九**条拒绝分支各栽一个缺陷、九个都拒，
并且带了一条行数下限——没有下限的那一版会对一个被截到只剩 1 行的 manifest 报绿。
在 `580c645d`（十三关全绿那棵树）上它报 15 个问题。
