# 引擎：mdl_segmenter

seam：`props/mdl_segmenter.py:_segment` —— 这是 property 模块里**唯一**调用引擎的
私有 helper（`engine.segment_trajectory(world.frames, background=…)`），四条不变式
全部经它取 `Segmentation`，所以一个 seam 就覆盖整块电池，没有第二个 seam 可选。
（`_foreground` 是纯本地重算，不碰引擎，不是 seam。）

世界数：40（`--worlds 40`，campaign seed `0x00005eedc1e4f002`，engine-rig head
`baf1671`）；每个变异体耗时约 0.2 s，没有减到 20 的必要。
基线：**干净** —— 驱动器未打印 `BASELINE NOT CLEAN`，JSON 里
`coverage.mdl_segmenter.baseline_dirty_worlds = 0`，`worlds_confounded = 0`。

原始产物：`fuzzlab/out/mutation.mdl_segmenter.json`。
11 个变异体，7 个被杀，4 个存活（全部为**预注册的预测存活**）。
`invariants_no_mutant_kills = []` —— 四条不变式**都**被证明能响，没有一条是哑的。

## 逐不变式检出力

| 不变式 | 变异体 | 预注册命中？ | killed/eval | 首杀世界数 | inert | raised-only |
|---|---|---|---|---|---|---|
| masks_partition_the_foreground | mdl-shift-track-rigidly（整轨刚性平移，只错位置） | 是（唯一命中） | 40/40 | 1 | 0 | 0 |
| masks_partition_the_foreground | mdl-duplicate-track（同一 track 列两遍，测重叠分支） | 是（唯一命中） | 40/40 | 1 | 0 | 0 |
| masks_follow_anchors | mdl-perturb-rel-cells（rel_cells 偏移 (+1,0)） | 是（唯一命中） | 40/40 | 1 | 0 | 0 |
| masks_follow_anchors | mdl-forget-anchor（丢 anchor 保留 mask） | 是 | 40/40 | 1 | 0 | 0 |
| events_agree_with_tracks | mdl-forget-anchor（同上，连带命中） | 是（预注册两条） | 40/40 | 1 | 0 | 0 |
| events_agree_with_tracks | mdl-flip-move-delta（move 事件 dy+1） | 是（唯一命中） | 39/39 | 1 | 1 | 0 |
| events_agree_with_tracks | mdl-drop-narration（删一条 move/appear/vanish） | 是 | 40/40 | 1 | 0 | 0 |
| script_bits_identity | mdl-drop-narration（同上，连带命中） | 是（预注册两条） | 40/40 | 1 | 0 | 0 |
| script_bits_identity | mdl-skip-transition-header（script_bits −8） | 是（唯一命中） | 40/40 | 1 | 0 | 0 |
| events_agree_with_tracks | mdl-spurious-free-move（插入 (0,0)、0 bit 的 move） | **否，存活** | 0/39 | — | 1 | 0 |
| script_bits_identity | mdl-misprice-event（事件 bits 与 script_bits 同幅下调） | **否，存活** | 0/40 | — | 0 | 0 |
| （无人读 `Track.color`） | mdl-flip-track-color | **否，存活** | 0/40 | — | 0 | 0 |
| （无人读 `baseline_bits`） | mdl-inflate-baseline-bits | **否，存活** | 0/40 | — | 0 | 0 |

两处 inert 都查明了原因，不是注入失效：

* `mdl-flip-move-delta` 的 1 个 inert 是**世界 7**：23 条 track、41 个事件，
  全是 appear/vanish，**一个 move 都没有**。这正是 `BUGS.md` B1 那条能力边界
  （mover 与相邻 obstacle 在 4-连通、颜色无关算子下并成一个分量，于是每次运动
  都被叙述成"死+生"而不是"移"）在本语料里的体现。没有 move 事件可翻，排除出分母是对的。
* `mdl-spurious-free-move` 的 1 个 inert 是**世界 2**：1 条 track、6 帧 5 个转移
  5 个事件 —— 每个转移都真的动了，没有"静止且无事件"的转移可供插入伪事件。

**首杀世界数一律为 1，且 killed==eval（40/40、39/39）。** 也就是说：对这四条不变式，
只要缺陷是它们负责的形状，**第 1 个世界就抓到，并且每个世界都抓到**。标准战役的 500 个
世界不是为 mdl_segmenter 的检出力花的 —— 500 买的是**语料多样性**（world 7 那种 23 条
track 的合并世界、world 2 那种单物体世界），不是买灵敏度。反过来说，这也意味着这四条
不变式的 kill 曲线没有任何"稀有触发"结构：它们要么当场响，要么（见下）永远不响。

## 杀不死的变异体（逐个裁决）

- **mdl-spurious-free-move** —— 裁决：**不变式不够，能补**。
  依据：引擎两处承诺被同时违反 ——（1）`segmenter.py:_match_cost` 在
  `a.cells == b.cells and a.colors == b.colors` 时返回 `kind=None`，即**分量没变就不出事件**；
  （2）`costs.py:move_bits` = `b_evtype + b_objid + offset_bits(dy) + offset_bits(dx)`，
  最小也有 6 bit，**move 事件不可能是 0 bit**。所以"某 track 在某个静止转移上以 0 bit
  宣称移动了 (0,0)"是引擎绝不会产出的假叙述，而 script 的每条事件都会经 `to_payload`
  的 `events` 进入 candidates.jsonl、进而进入手册。
  为什么漏：`events_agree_with_tracks` 的 docstring 声称"双向"，但代码只有一个方向是完整的。
  anchors→events 方向完整（`expected not in kinds` 就报）；events→anchors 方向**只校验
  move 的 (dy,dx)**，而 (0,0) 与静止 anchor 天然一致，bits=0 又让 `script_bits_identity`
  的求和不动。两条不变式各自的盲区正好互补成一个洞。
  怎么补（局部、不需要 oracle）：在 `events_agree_with_tracks` 的转移循环里，除现有检查外
  再加两条 ——(i) `kinds ⊆ {expected}`（expected 为 None 时 kinds 必须为空），
  (ii) move 事件的 `(dy,dx) != (0,0)`。第 (i) 条对当前引擎是安全的：本次实测
  **829 个 (track, t) 对中 0 个带一个以上事件**，引擎的指派保证每条 track 每个转移最多一个事件。

- **mdl-misprice-event** —— 裁决：**不变式不够，能补**。
  依据：`costs.py` 开篇写明这是"One scheme, published (see this engine's README.md),
  simple enough to re-derive by hand"，`segment_trajectory` 把同一个数既写进 `Event.bits`
  又累加进 `script_bits`。把某个事件的 bits 砍半、同时把 `script_bits` 砍掉同样的数，
  恒等式两边同减，`script_bits_identity` **在构造上对这类缺陷封闭** —— 引擎可以把任何一条
  事件定错价，只要总账一起定错。也就是说，`script_bits_identity` 检的是"引擎自洽"，
  不是"引擎按公布的码长收费"。
  怎么补：新增 `event_bits_match_cost_model`，由 fuzzlab 自己的 oracle 从帧重算
  `bits_for/gamma_bits/offset_bits` 与 `b_evtype/b_objid/b_pos/b_color`（约 20 行，公式在
  engine README 与 `costs.py` docstring 里是公开的）。
  **注意房规张力**：这个 oracle 必须**重写**代价模型，不能 `import engines.mdl_segmenter.costs`
  —— 那就是让引擎给自己打分，违反 `README.md` 的"oracle 不得调用它所审判的引擎"。
  代价是要复刻 `max_objects`（每帧分量数的最大值），需要 oracle 侧自带一个连通分量实现。

- **mdl-flip-track-color** —— 裁决：**不变式不够，能补**。
  依据：`segment_trajectory` 里 `color=comp.uniform_color`，定义在
  `Component.uniform_color`（`colors[0] if len(set(colors)) == 1 else None`），
  并由 `engines/mdl_segmenter/__init__.py:to_payload` 以 `"color": track.color` 发布进
  object_hypothesis payload —— 这是**离开引擎、进入手册**的字段。改成另一个调色板颜色
  之后四条不变式全部沉默（连 raised 都没有）。
  这**不是**能力边界：`props/mdl_segmenter.py` 的 docstring 明确列出它**故意不断言**的两件事
  （帧级 round-trip、压缩率保证），颜色不在其中；`BUGS.md` 的 B1/B2 先例是"引擎从没承诺过的
  行为"，而颜色是引擎明确承诺过的。
  怎么补：`tracks_report_their_colour` —— 对每个在场帧，用 `world.frames` 直接读该 mask 覆盖
  的格子颜色，断言"这些颜色唯一 ⟺ `track.color is not None`，且等于它"。纯本地重算，不调引擎。

- **mdl-inflate-baseline-bits** —— 裁决：**不变式不够，能补**（但这条我给出反方读法）。
  依据：`baseline_bits` 是 `Σ_t cost.baseline_transition_bits(|changed_pixels(f_t, f_{t+1})|)`，
  `costs.py` 的 docstring 亲自点名要防的失败模式是"Rigging the comparison by choosing units"。
  把它翻倍，`gain_bits` 与 `compression_ratio` 就都虚高一倍，而这两个数正是 D-005 验收阈值所用的单位。
  **反方读法（我认为不成立，但必须写下来）**：props 已经明确拒绝断言 `script_bits < baseline_bits`
  （那是 Fixture A 的结果不是契约），有人可以主张"整个 baseline 只服务于那个被拒绝的比较，
  所以它的取值在被测契约之外"。我不采纳，理由是可验证的：`to_payload` 把
  `mdl.baseline_bits / gain_bits / ratio` 写进**每一条** candidate，这个数无论 fuzzlab 断不断言比较
  都会离开引擎。被拒绝的是"谁更小"这个**比较**，不是"baseline 是这段帧的价格"这个**恒等式**。
  怎么补：`baseline_bits_identity`，与 `script_bits_identity` 对称，由 oracle 重算 changed_pixels
  与 `b_header + n_changed*(b_pos+b_color)`。同样受上面那条房规张力约束（必须重写、不得 import）。

四个存活体的 `survived_all_detection` 均为 `true` —— 不是"崩溃式检出"，是**完全无声**。

## 构造上不可证伪的检查

我逐条逐分支看了四条不变式，**没有**找到 zero_space `rank_nullity` 第三项那种
"永远为假"的分支（那种情形要有一个 property 与它的 `len()` 自证）。四条不变式的每个
report 分支都在本次运行中被某个变异体实际点亮过。以下是两处**次一等**的死分支，性质不同，
分开写：

* `events_agree_with_tracks`：move 事件校验里的 `here is None or there is None`
  （props/mdl_segmenter.py:159）。要在 `here`/`there` 有一个为 None 时还能走到这个循环，
  该 (track, t) 必须**同时**带 expected 那个 kind 与一个 move 事件，即一个转移上有两个事件；
  `segment_trajectory` 的指派保证每条 track 在每个转移上恰好落入 pairs / gone / born 之一，
  **最多一个事件**。实测：829 个 (track, t) 对里 0 个带多于一个事件。
  所以它对**引擎能产出的任何输出**都是死的，也没有被我 11 个变异体中的任何一个点亮。
  区别于 zero_space 那条：它不是逻辑上不可能为真（一个"两 anchor 皆 None 却带 move 事件"
  的注入能点亮它），只是引擎的构造让它永不发生 —— 我据此**没有**把它报成不可证伪，只报成死码。
* `script_bits_identity` 的 `max(0, seg.n_frames - 1)`：`gridworld` 的 `n_frames ∈ [6,40]`，
  且 `Segmentation.n_frames = len(frames)`，`max(0, …)` 的 0 分支在本族语料上恒不取。无害。

另外一件更重要的、不是"分支"而是"字段"的事实（读代码可核，本次实测确认）：
**`Track.color`、`Track.shape`、`Track.first_frame`、`Segmentation.baseline_bits`
没有任何一条不变式读过；`Event.params` 只有 move 的被读（`appear` 的 `at` 从不校验）；
`Event.bits` 只以求和形式被读。** 四个存活体里有三个正是打在这个面上。
`appear` 事件的 `at` 参数我没有写变异体：本语料里 appear 大量存在（world 7 有 20 个），
所以它是**可以**测的，只是我没测，不敢当作已测报出。

## 预测错的地方

**没有预测错的方向性错误**：`unexpected_kills` 全部为空（11/11），没有任何一条不变式
杀死了我没预注册的变异体 —— 这一点值得记下，因为它说明 mdl_segmenter 的四条不变式
**彼此独立性很好**，比 module docstring 声称的还干净：刚性平移只碰 partition、
rel_cells 只碰 follow_anchors、事件参数只碰 events_agree、账目只碰 script_bits。
唯一的跨条命中是 `mdl-drop-narration`（events_agree + script_bits）与 `mdl-forget-anchor`
（follow_anchors + events_agree），两个都是**预注册就写了两条**的，而且
`props/mdl_segmenter.py` 的 docstring 本来就声明了这层耦合（"an unnarrated change is also
an under-priced script"）—— 这次给它配上了 40/40 的实测数。

`predicted_but_missed` 有 4 条，全部来自 4 个**预测存活体**。这需要说清楚，否则读 JSON
的人会以为我预测错了 4 次：`Mutant.__post_init__` 要求 `expect_kill` **非空**，
而这四个变异体的诚实预注册应当是"没有任何不变式该抓到它 —— 这正是发现本身"，框架无法表达。
我的处理是：给它们填上**邻近的**那条不变式，并在 `description` 里以 `PREDICTED SURVIVOR:` 开头
写明"我在跑之前就预测它活下来，以及为什么"。这四条 `predicted_but_missed` 应读作
"预测的存活得到确认"，不是"预测失败"。

## 我不确定的 / 框架挡住我的地方

1. **框架挡住的（唯一一处，建议统一处理）**：`expect_kill` 不允许为空。
   一个诚实预注册为"应当无人抓到"的变异体无法表达，只能借用邻近不变式的名字，
   代价是 `predicted_but_missed` 这一列同时装了两种语义完全相反的东西
   （真的漏杀 / 预测中的存活）。建议（**我没有改，也不会改**）：允许
   `expect_kill=()` 配一个必填的 `expect_survive_because: str`，或加一个
   `predicted_survivor: bool` 字段，让驱动器把这类条目从 `predicted_but_missed` 里分出去。
   在此之前，读 mdl_segmenter 这份 JSON 必须配着 `description` 的 `PREDICTED SURVIVOR:`
   前缀读。
2. **`HEADER_BITS = 8` 在 props 里是硬编码的**，不是从 `CostModel.b_header` 读的
   （我的变异体文件里也照抄了这个常数，并注明了原因）。这不是本次测出来的缺陷，
   但意味着：若引擎某天改了 `b_header`，`script_bits_identity` 会对一个**正确**的引擎报红。
   这是一条潜在假阳性通道，不是检出力问题，交给 RES-3 判断要不要单开条目。
3. **`mdl-duplicate-track` 保留了同一个 `track_id`**，为的是让它只打中 partition 的重叠分支
   （换新 id 会连带打中 events_agree，变宽）。它模拟的是 `order` 列表里同一个 tid 被 append 两次
   （`tracks=[tracks[tid] for tid in order]`）。我认为这是一个真实可能的 bug 形状，
   但它比另外几个变异体更"假想"一些，如果对抗性复核认为 id 重复不构成引擎可能的输出，
   这一条应被降级 —— 不影响结论，因为 partition 的重叠分支已被它以 40/40 证明可响。
4. **只跑了 40 个世界，且全是 `gridworld`**（该 property 模块的 `FAMILY`）。
   40 个世界足以支撑"首杀=1、killed==eval"这个结论（信号极强），但不足以支撑任何关于
   稀有触发的否定性结论。四个存活体我认为是**结构性**存活（读代码可证，与世界数无关），
   不是"再多跑几个世界就会被抓到"—— 但这句话的依据是代码，不是 40 这个数。
5. 我**没有**测 `appear` 事件的 `at` 参数、`Track.shape`、`Track.first_frame`。
   由代码可读出没有不变式读它们，但我没有为它们写变异体，因此不把它们计入"已测"。
