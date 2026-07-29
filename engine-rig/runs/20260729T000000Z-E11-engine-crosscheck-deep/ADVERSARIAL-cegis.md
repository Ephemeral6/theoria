# 对抗性复核：cegis_miner 的假规则结论

**任务** RES-3 派出的对抗性复核 · **2026-07-29**
**树** `.worktrees/e11-engine-crosscheck-deep`
**纪律** 只读。`engine-rig/`、`fuzzlab/`、`CONTRACTS/` 一个字节未改。无网络，未碰 `.env`，
封存堆零接触。验证脚本在会话临时目录（`rebut_a.py` / `rebut_b.py` / `rebut_c.py`），未入库。
**立场** 我的任务是推翻。以下每一条「推不翻」都是在认真找过反例之后写的。

---

## 判决摘要

| 被复核的结论 | 我的判决 | 强度 |
|---|---|---|
| **F-1「effect 全错，1209 行假」** | **削弱（严重削弱）** — 数字全部复现，**定性错了**：1209 行是**关于另一个物体的真陈述**，不是假陈述。「P1 被证伪」这一条**推翻**。 | 实测 + 读码 |
| **F-2「lifted 规则 61% 不成立」** | **推不翻**（且比报告写的更强） — 91/149、342 行、90 世界逐位复现；但报告的机理描述「`act==?dir` 恒真」**是错的**，引擎自己的求值器里它**恒假**。修正机理后结论在**两种读法下都成立**。 | 实测 |
| **「162 个世界满绿」** | **推不翻**（更强） — 193 个可挖世界上电池返回 **0 条 finding**，不是 skipped 被误读。 | 实测 |

一句话：**报告的所有计数都是对的，F-2 站得住且该 escalate；F-1 的严重性被高估了一个量级，
按现在的措辞 escalate 会被打回来。**

---

## 1. P1 是承诺还是测试性质名

**判决：P1 是引擎写下的真承诺，但它的量化范围是 ledger，不是世界。F-1 因此不构成 P1 违反。**

### 1.1 原文与它的语境（读码）

`engines/cegis_miner/README.md:3-6`：

> Counterexample-guided synthesis of rules (guard + effect) against an exact
> ledger. Zero noise and a few dozen transitions, **so the ledger *is* the verifier**:
> a rule is right exactly when it fires on every transition carrying its effect and
> on no other.

`miner.py:1-8` 是同一句话的第二次书写：「**The ledger is the verifier**: zero noise, so a
rule is right exactly when it fires on every transition with its effect and on no other.」

它**不是**测试里的性质名——`fuzzlab/props/cegis_miner.py` 里四个不变量叫
`frontier_guards_are_consistent` / `applicable_equals_support` 等，没有一个叫 P1。
所以报告说「P1 是引擎写下的承诺」这半句我推不翻。

**但读全句。** 两处原文都以 `the ledger is the verifier` 作前提从句，紧跟 `so`。
这句话在定义**相对于 ledger 的正确性**：「carrying its effect」里的 *its effect* 指的是
**ledger 行里记录的那个 effect**。展开就是

> guard 的触发集 == ledger 中带该 effect 的行集

这**正好就是** `applicable == support`，正好就是电池已经在查、并且 932/932 通过的那条。
P1 承诺的是 guard 与 ledger 一致，**没有承诺 ledger 与世界一致**。

### 1.2 而且 README 明确把 ledger 的保真度推给了别人

报告自己列出的 **P6**（`README.md:10-12`）：

> Effects come from `mdl_segmenter`'s narration — the miner never re-derives
> *what happened* from pixels; it reads pixels only to evaluate guards.

这是一条**免责声明**：effect 的真假是分割器的事。而报告第 124-147 节自己承认
**分割器叙述对了**（`('obj1','move',{'dy':1,'dx':0})`）。于是链条上没有任何一环
违反了自己写下的承诺——缺陷在**没人写过承诺的那条缝上**。这跟报告的结论
「缺陷在接缝上」一致，但跟它的结论「**That is P1 falsified**」（第 151 行）矛盾。
**这一句要删。**

### 1.3 关键攻击点：`blocked_*` / effect `none` 到底假不假（实测）

我直接查了：在那 72 个世界里，被挖的那个 track 在**每一帧**的像素集合是否完全相同。

```
F-1 worlds examined                       : 72
tracked object motionless in EVERY frame  : 72
tracked object NOT motionless             : 0
```

**72/72。** 被挖的物体在整条轨迹里一个像素都没动过。

再看 `transitions_from_segmentation` 怎么产生 `none`（`__init__.py:45-47`）：

```python
events = [e for e in seg.events_at(t) if e.track == track.track_id]
if not events:
    effect = Effect(type="none")
```

`effect: none` 的语义是**逐 track 的**：「这个 track 在这一步没有事件」。它从来不是
「世界没有变化」。所以 `blocked_DOWN: act==DOWN ∧ … → none` 读出来是

> 按下 DOWN 时，**这块石头**不动。

**这是一句真话。** 1209 行里的每一行都是真的——关于石头。guard 也是真的：
`free(strip(DOWN))` 求值在**石头的 anchor** 上，意思是「石头下方那格是空的」。
整套规则内部自洽、外部也不假，只是**讲的不是我们期待的那个物体**。

**所以 F-1 必须从「1209 行是假的」降级为「1209 行讲的是另一个物体，而载荷从不说是哪个」。**

### 1.4 独立预言机判假的判据里藏着什么（实测）

我量了那 72 个世界里**整帧发生变化**的 transition 数：

```
frame-level changes across those worlds   : 1209
MOVE events in those worlds               : 1209
```

**1209 = 1209 = 报告判假的行数。** 也就是说，报告的像素预言机对 `none` 的判据就是
**「整帧变了，所以 none 是假的」**，一行不多一行不少。它隐含假设了 effect 是
**帧级/mover 级**的陈述，而引擎的 effect 是 **track 级**的。这正是本次复核最该拿分的地方，
拿到了。

### 1.5 那 F-1 还剩下什么（仍然成立的部分）

降级不等于清零。剩下的是真缺陷，只是**性质不同**：

1. **默认值武断且无文档。** `track = track or seg.tracks[0]`（`__init__.py:36`）。
   我 grep 了整个 engine-rig：`tracks[0]` 只出现在这一处生产代码里，
   **没有任何文件声明 tracks[0] 是 mover**（`mdl_segmenter/README.md:88` 只是把
   `seg.tracks[0]` 当例子用，反而加固了这个不成文的习惯）。
2. **载荷丢了物体绑定，而同一批引擎的另一个载荷没丢。** `mdl_segmenter` 的
   `object_hypothesis` 载荷第一个字段就是 `"object_id": track.track_id`
   （`mdl_segmenter/__init__.py:20`）。`cegis_miner` 的 `rule_hypothesis` 载荷
   **没有任何 track / object 字段**——我把 payload 和 candidate 的键全列出来实测确认：

   ```
   payload keys : action cegis_guard cegis_iterations cegis_trace effect frontier
                  frontier_max_size frontier_size frontier_truncated guard
                  guard_cost_bits lifted_from name
   ANY track/object identifier -> NONE
   ```

   **这才是 F-1 的可辩护形式，而且它是读法无关的：** 同一条 `candidates.jsonl` 里，
   物体假设带 `object_id`，规则假设不带。裁决的 LLM 拿到
   `{"name":"blocked_DOWN","effect":{"type":"none"}}` **在结构上无法知道它说的是谁**，
   默认会读成「按 DOWN 什么都不会发生」，然后写进 manual。
   （补充：`CONTRACTS/candidates_schema.md` 把 payload 形状完全下放给各引擎 README，
   所以这不构成冻结契约的违反——是设计缺口，不是违约。这条也削弱严重性。）
3. **认证路径确实走的是坏默认。** 五个调用点里，`fuzzlab/props/cegis_miner.py:85`
   （给这个引擎发证的那个）不传 track。这条报告说得对。

**但报告漏掉的一个反向事实，对 escalate 很重要：真正的下游消费者做对了。**
`theoria-arm/world/adapt.py:192-197` 是 `for track in seg.tracks:` 显式逐 track 传入的。
所以「不安全默认是生产路径」这句站不住。

**——不过我在那里发现了更严重的东西，见第 7 节。**

---

## 2. tracks[0] 因果链（我重算了什么）

**判决：三步全部成立，72/193 逐位复现。这条链我推不倒。**

| 环节 | 我的验证 | 结果 |
|---|---|---|
| `transitions_from_segmentation` 默认取 `seg.tracks[0]` | 读码 `__init__.py:36` | ✅ 原文 `track = track or seg.tracks[0]` |
| `mdl_segmenter` 按栅格序排组件 | 读码 `segmenter.py:156` | ✅ `return sorted(out, key=lambda comp: comp.cells)`；`cells` 已 `sorted`，故按最小格的栅格序 |
| frame 0 的组件顺序决定 track 顺序 | 读码 `segmenter.py:246-250` | ✅ `for idx, comp in enumerate(per_frame[0]): new_track(...)`，`order.append(tid)`，`tracks=[tracks[tid] for tid in order]` |
| 72/193 | **实测**，seeds 1–200，复用 `props._mine` 的算子顺序 | ✅ **精确复现** |

实测全表（seeds 1–200）：

```
total seeds        : 200      unminable          : 7        judged             : 193
track0 NOT mover   : 72       track0 static      : 72       all-none rule sets : 72
all-none AND moved : 72       obstacle-bearing   : 115      multi-track        : 115
total transitions  : 4277     total ground rules : 932      total lifted       : 149
transitions in all-none+moved worlds: 1595   MOVE events in those worlds: 1209
```

报告的每一个数字——193 / 7 / 72 / 4277 / 932 / 149 / 1595 / 1209——**一个不差**。
「72 个里 tracks[0] 是静止障碍物」也确认：72 个全部 `track0_static == True`。

顺带实测了「传 mover track 是否就好了」：64 个世界里 mover 的 track 存在，
其中 **51 个**换成 mover track 后挖出 `push_*`（真 move 规则），13 个抛
`ValueError`（touching-objects 缺口）。所以「传对 track」不是一个完整的修复，
报告第 6 节把归属留给设计方是对的。

---

## 3. `?dir` 是否恒真（谁会绑定它）

**判决：报告的机理描述错了——在引擎自己的求值器里 `act==?dir` 恒假，`free(strip(?dir))` 直接抛异常。
但修正机理后 F-2 反而更强：它在两种读法下都成立。**

实测（`engines.cegis_miner.atoms.evaluate`，引擎唯一的求值器）：

```
act==?dir              -> {'UP': False, 'DOWN': False, 'LEFT': False, 'RIGHT': False}
!act==?dir             -> {'UP': True,  'DOWN': True,  'LEFT': True,  'RIGHT': True}
free(strip(?dir))      -> RAISES ValueError: ?dir
in_bounds(strip(?dir)) -> RAISES ValueError: ?dir
clear(strip(?dir))     -> RAISES ValueError: ?dir
```

读码对得上：`_evaluate_positive` 里 `if kind == "act": return action == arg`，
而 `action` 只会是 UP/DOWN/LEFT/RIGHT，永远不等于字符串 `"?dir"`。
`strip_cells` 的最后一行是 `raise ValueError(direction)`。

**谁会绑定它？我把 `?dir` 的所有消费者查了一遍：**

| 消费者 | 会不会绑定 `?dir` |
|---|---|
| `atoms.evaluate` / `atom_masks` / `_mask_of` | **不会**。lifted 规则从不回到求值器 |
| `fuzzlab/props/cegis_miner.py::_fires_on` | **不会**，而且只遍历 `result.rules`，够不着 lifted |
| `engine-rig/tests/test_cegis_miner.py` | **不会**。全仓只有一行提到 lifted（`:39` 断言 `lifted_from` 列表），从不求值它的 guard |
| `theoria-arm/world/adapt.py` | **不会**。只把 `[a.name for a in r.guard]` 转成字符串写报告 |
| **`candidates.jsonl` 的读者（裁决 LLM）** | **只有它会**，而且**必须**会——`?dir` 不绑定就没有任何意义 |

所以「恒真」这个说法**只在唯一有意义的那个读者眼里成立**，而那个读者是人/LLM，不是代码。
报告第 92 行自己标注了「the only reading under which `act==?dir` is not meaningless」，
所以它不是造假，是**机理句写歪了**（第 166 行「`act==?dir` fires on all of it」、
第 178 行「is a tautology」在描述代码行为时是错的）。

**修正后为什么更强：** P1 要求「guard 恰好触发在带该 effect 的行上」。对 lifted 规则

* **绑定读法**：`act==?dir` admits 每一行，包括 mover 没动的 noop 行 → 触发在**不带**该 effect 的行上 → **P1 假**；
* **引擎求值器读法**：guard 触发在 **∅** 上 → 没能触发在**任何**带该 effect 的行上 → **P1 也假**。

**两条路都到 P1 假。** 这是 F-2 相对 F-1 的关键优势：F-1 的证伪依赖一个引擎从未做出的
物体承诺，F-2 不依赖任何读法选择。

**还有一条读法无关、且我认为该写进 escalate 的度量**（实测）：

```
lifted rules whose published `applicable` != the guard's firing set : 131 / 149
```

不管你怎么读 `?dir`，**149 条 lifted 规则里有 131 条的 `applicable`（进而 `coverage`）
不是从它自己发布的 guard 算出来的**。`applicable` 是各 member 的并集
（`miner.py:246`），而 README:96-99 定义 `evidence.coverage` 为
`<supporting>/<admitted by the guard>`。这两句直接冲突。
（`DECISIONS.md` D-006 写了「Coverage of the lifted rule is the sum over directions」，
所以这是 **README 与 DECISIONS 互相矛盾**，不是无人声明的缺口——escalate 时要说清是哪一条。）

**顺带：电池就算改成遍历 `all_rules` 也修不好。** `_fires_on` 会在
`free(strip(?dir))` 上抛 `ValueError`，被 `run_invariants` 捕成 `raised`，
再对 `act==?dir` 报出一条「触发集为空 ≠ support」的**假阳性 violated**。
修复必须先给 lifted guard 一个求值语义。这一点报告没提，我认为该提。

---

## 4. lifted 到底发不发布

**判决：发布，而且是**明文的设计决定**。F-2 的严重性不降反升。**

实测（seed 6，`engine.candidates(result)`）：

```
ground rules=6 lifted=2  -> candidates emitted=8
candidates with action=='?dir': 2
{"name":"push","action":"?dir","guard":["act==?dir"],
 "effect":{"type":"move","direction":"?dir"},"lifted_from":["push_DOWN","push_RIGHT"],
 "cegis_guard":[],"cegis_iterations":0}
  evidence: {'transitions': [0,2,8,10,11,14,15], 'coverage': '7/7'}  status: candidate
```

读码：`__init__.py:86` `for rule in result.all_rules`，`all_rules = rules + lifted`
（`miner.py:276-277`）。`DECISIONS.md` **D-006** 白纸黑字：

> Both the per-direction rules and the lifted schema are emitted as candidates.

所以这**不是**疏忽，是刻意的。而 `fuzzlab/props/cegis_miner.py` 的四个不变量
全部只遍历 `result.rules`（`:127, :161, :209, :236`）。
**刻意发布 + 从不审计 = 报告说的那个洞，确认存在。**

我还核了报告关于 frontier 泄漏的说法，成立。seed 6 第二条 `push` 的发布载荷：

```json
"frontier":[["act==?dir","free(strip(?dir))"],["act==?dir","in_bounds(strip(?dir))"],
            ["!in_bounds(strip(UP))","act==?dir"],["!free(strip(UP))","act==?dir"],
            ["act==?dir","at(0,1)"],["!at(1,0)","act==?dir"]]
```

`UP` 是模板 `push_UP` 的具体方向，被原样留在一条声称对**所有**方向成立的规则里
（`substitute_direction` 只替换 `arg == 模板自己的方向` 的原子，`atoms.py:64-68`）。
`at(0,1)` 同理。同一个世界里两条规则都叫 `push`，名字碰撞确认
（我全表测得 **33** 个世界存在重名，报告写 27，口径是「都叫 push」，
差异不影响结论，但 escalate 时用哪个数要说明口径）。

---

## 5. 满绿是绿还是 skipped

**判决：真绿。报告没有把 skipped 读成绿。这条推不翻，而且实测比报告说的更彻底。**

实测：对 seeds 1–200 逐个调 `props.cegis_miner.check(world)`，按 `finding.kind` 分类。

```
F-1 worlds (all-none rules, world moved) : 72
worlds emitting lifted rules             : 116
union                                    : 188   (重叠 0)
battery verdict over the union           : {'EMPTY': 188}
global finding-kind counts over 193 judged worlds : {}        <- 一条 finding 都没有
```

* **188 个世界全部返回空列表**，不是 `skipped`，不是 `raised`，不是 `violated`。
* 报告的 162 = 72（F-1）+ 90（有不成立 lifted 的世界）。我的 188 = 72 + 116
  （**所有**产出 lifted 的世界）。口径不同，**188 ⊃ 162，所以报告的 162 满绿
  a fortiori 成立**。
* **反证 skipped 机制没坏**：那 7 个 unminable 世界上电池确实吐出
  `{('skipped','unminable'): 28}`（7 世界 × 4 不变量）。所以「空」是真的空，
  不是 skipped 被当成绿。`props/finding.py` 的三分法工作正常。

---

## 6. 共享依赖里的致命项

报告 1.1 节列了六项。我逐项打，**打中一项**。

| # | 依赖 | 我的判决 |
|---|---|---|
| 1 | `fuzzlab/worlds/gridworld.py` 作第二预言机 | **打不倒它「标签错了」，但打中了它「独立」这个说法** — 见下 |
| 2 | `mdl_segmenter` + `transitions_from_segmentation` | 报告自己说这就是 F-1 本体，不构成盲区。同意 |
| 3 | `engines.cegis_miner` | 受审对象，不适用 |
| 4 | `atoms.py`「只读定义、不执行」 | **这一条报告吃亏了**：不执行 `evaluate` 正是它把 `act==?dir` 说成恒真的原因。执行一次就会发现是恒假 |
| 5 | `fuzzlab/props/cegis_miner.py` 只用于记录电池判决 | 我独立重跑过，判决一致。同意 |
| 6 | Fixture A truth file | 只用于确认对象，不参与判断。同意 |

### 6.1 生成器的标签会不会本身就错（我最想打的一条）

**打不倒「标签错了」。** 读码 `gridworld.py`：`Rules.step(anchor, action)` 一次调用
同时返回 `(next_anchor, event_label)`；`generate` 用返回的 anchor 序列
`frames = [rules.render(a) for a in anchors]` **渲染出帧**。
所以标签不是从帧上事后推出来的——**帧和标签是同一次调用的两个返回值**，
帧是标签的下游。要让标签错，得让 `step` 的两个返回值互相矛盾，
而报告的像素预言机正好能抓到这种矛盾，实测 `eff_wrong_both = 0` 无分歧。
这一项是我打过最结实的一环，**推不倒**。

### 6.2 但「两个独立预言机零分歧」这句话是空的（打中）

`world.events` 描述的是 **mover**；`my_effect(f_t, f_{t+1})` 描述的是**整帧**。
引擎的 effect 描述的是 **track**。两个预言机确实互相独立地实现，但它们
**共享同一个解释前提：effect 是关于 mover / 整帧的陈述**。
在争议点（「effect 是关于谁的」）上，它们不可能分歧——**零分歧因此不是证据**。

第 1.4 节的实测把这一点钉死了：帧变化数 = 1209 = 判假行数 = mover 移动数，
三个数完全相等。报告写的「两个独立预言机同时判假，零分歧」在修辞上很强，
**在逻辑上只是同一个前提被数了两遍**。

**这就是那项「如果本身有缺陷会让结论变成假报」的依赖**——不是生成器坏了，
而是**两个预言机的解释层级都比被审对象高一级**。它没有让 F-2 变成假报
（F-2 不依赖预言机，只依赖 ledger 内部的 effect 字段），
但它让 **F-1 的「假」字失去支撑**。

---

## 7. 我另外发现的（比 F-1 原文更严重）

**F-1 的真实爆炸半径在 `theoria-arm`，不在 fuzzlab——而且路由不是 `tracks[0]`。**

`theoria-arm/world/adapt.py::mine`（192-222 行）做对了一件事、做错了一件事：

```python
for track in seg.tracks:                      # 对：显式逐 track
    transitions, ms, err = _timed(cegis_miner.transitions_from_segmentation,
                                  grids, actions, seg, track, store.background())
    if err: ...continue                       # 前置条件失败 -> 跳过
    result, ms2, err2 = _timed(cegis_miner.run, transitions,
                               out_path=out_path if mined is None else None)
    ...
    if mined is None:
        mined = result                        # 错：第一个成功的 track 独占发布权
```

`out_path` **只给第一个通过前置条件的 track**。而**静止物体永远不会触发前置条件失败**
——它没有事件，`events` 为空，直接落进 `Effect(type="none")` 分支，
`ValueError` 那条路根本走不到。**于是静止障碍物在这场竞争里是不败的**：
只要它在 `seg.tracks` 里排在 mover 前面（即帧 0 栅格序更靠前，实测 193 个世界里占 72 个），
写进 `candidates.jsonl` 的 `rule_hypothesis` 就全是它的。

这比报告写的更糟三点：

1. 它**绕过了**报告提出的修复。报告把 F-1 归因于「默认 `tracks[0]` 不安全」，
   并推测「传 `track=` 就能修」。`adapt.py` **已经传了 `track=`**，照样中招——
   因为选择逻辑变成了「第一个不报错的」，而静止物体恰恰是最不容易报错的。
2. 它落在**论文路径**上，不是 fuzz 路径上。`theoria-arm` 是要产出结果的那条臂。
3. `mdl_segmenter` 的 `object_hypothesis` 会带 `object_id` 一起写进同一个
   `candidates.jsonl`，而 `rule_hypothesis` 不带——两种载荷**并排躺在同一个文件里，
   一个有物体身份一个没有**，裁决的 LLM 无法把规则接回物体。

**现状缓解（必须一起写进 escalate，否则是危言耸听）：**
`theoria-arm/THEORIZE_LOG.md:185` 记录实际跑出来是 **Zero `rule_hypothesis` rows** ——
在真实 ARC 帧上所有 track 的前置条件都失败了。所以**今天没有污染任何已产出的 artifact**。
这是一颗**尚未引爆**的雷：一旦有一个世界能被挖，它就会挑错物体，且无人察觉。

---

## 8. 我打不倒的（以及为什么）

1. **全部计数。** 193 / 7 / 72 / 4277 / 932 / 149 / 104 / 91 / 342 / 90 / 1595 / 1209 —
   我用独立写的脚本重跑 seeds 1–200，**逐位相同**。没有一个数字是凑的。
2. **tracks[0] 因果链三步。** 读码逐行核对，实测复现。见第 2 节。
3. **lifted 规则被发布。** 不但发布，D-006 明文规定要发布。见第 4 节。
4. **162 世界满绿。** 我扩到 188 个世界，`{'EMPTY': 188}`，且证明了 skipped 机制本身没坏。
5. **F-2 的实质。** 我试了三条推翻路径，全部失败：
   - 「`?dir` 有绑定语义所以不恒真」→ 查遍所有消费者，**没有任何代码绑定它**；
     且不绑定时 P1 也假（触发集为空）。两条路都到 P1 假。
   - 「lifted 只是候选，LLM 会裁决」→ 挡不住：`evidence.coverage` 是裁决者依赖的字段，
     而 131/149 条的 `applicable` 不是从发布的 guard 算出来的。
     发给裁决者的证据本身与它的文档定义不符。
   - 「生成器标签可能错」→ 帧由标签的同一次调用渲染，标签是帧的上游。打不倒。
6. **生成器不是污染源。** 见 6.1。
7. **报告的自我克制是真的。** 它主动把 F-3 降级为文档缺陷（P3 实测 0 违反），
   主动声明像素预言机有歧义因而只用「不在任何解释里」这个弱判据，
   主动说明深度 3/2 的覆盖边界。这些自限我核过，都成立，没有虚报覆盖。

---

## 9. 如果要 escalate，诚实的措辞应该是什么

**替 RES-3 写的两句。两句都已按上面的实测校准过，可直接用。**

> **F-1（严重性：中；类别：接缝规格缺失 + 载荷溯源丢失，不是假规则）**
> `cegis_miner.transitions_from_segmentation` 默认 `track = seg.tracks[0]`，而
> `mdl_segmenter` 按帧 0 栅格序排 track；193 个 gridworld 里 **72 个**因此挖的是静止障碍物。
> 挖出的 1209 行 **不是假陈述——它们是关于那块石头的真陈述**（实测：72/72 世界里被挖物体
> 全程零位移，`effect:none` 逐行为真）；真正的缺陷是 **`rule_hypothesis` 载荷不含任何
> `object_id`，而同一条 `candidates.jsonl` 里 `mdl_segmenter` 的 `object_hypothesis` 含**，
> 于是裁决的 LLM 在结构上无法知道一条规则在讲谁，默认会把它读成关于 mover 的。
> **注意两条纠正**：(a) 这**不构成 P1 违反**——P1 的原文以 `the ledger is the verifier` 为前提，
> 量化范围是 ledger 行而非世界，`applicable == support` 实测 932/932 成立；
> (b) 「传 `track=` 即可修」不成立——`theoria-arm/world/adapt.py` 已经逐 track 显式传入，
> 但只给**第一个不报前置条件错**的 track 发布权，而静止物体永远不报错，因此照样中招；
> 该路径当前实测产出 0 条 `rule_hypothesis`，所以**尚未污染任何 artifact**，是未引爆的雷。

> **F-2（严重性：高；类别：发布未经验证的泛化，且证据字段与其文档定义不符）**
> `lift` 把模板 guard 里的方向替换成 `?dir` 后**从不对合并后的支撑集重新验证**
> （`miner.py:241-246`），149 条 lifted 规则中 **104 条的 guard 退化为 `["act==?dir"]`**；
> 按 `?dir` 绑定到该行动作这个**唯一有意义的读法**，其中 **91 条（61%）在承诺的移动
> 并未发生的 transition 上触发（342 行、90 个世界）**，而这些规则经 `all_rules` 全部
> 写入 `candidates.jsonl`（D-006 明文要求），四个不变量却只遍历 `result.rules`，
> 162 个受影响世界上电池实测返回 **0 条 finding**。
> **一处机理更正**：`act==?dir` 在引擎自己的求值器里**恒假**而非恒真
> （`atoms._evaluate_positive` 做的是 `action == "?dir"`，`free(strip(?dir))` 直接抛
> `ValueError`）——但这不削弱结论，反而使其读法无关：不绑定则 guard 触发集为空、
> 无法覆盖任何带该 effect 的行，绑定则触发到不带该 effect 的行，**两种读法下 P1 都假**。
> 最该单独列出的一条读法无关度量：**149 条 lifted 里 131 条的 `applicable`（进而 `coverage`）
> 不是由它自己发布的 guard 算出的**，而 README:96-99 定义 `coverage` 的分母为
> 「admitted by the guard」（与 `DECISIONS.md` D-006 的「sum over directions」互相冲突）。
> 修复不能只是让电池遍历 `all_rules`——`_fires_on` 会在 `free(strip(?dir))` 上抛异常并
> 对 `act==?dir` 报出假阳性；**必须先给 lifted guard 定义求值语义**。

---

## 10. 复现

```bash
# 会话临时目录，未入库；只读 engine-rig/ 与 fuzzlab/
python rebut_a.py   # seeds 1-200 全表计数（第 2 节）
python rebut_b.py   # ?dir 求值语义、candidates() 发布路径、电池判决（第 3/4/5 节）
python rebut_c.py   # F-1 静止性判据、F-2 绑定读法独立计数（第 1.3/3 节）
```

`gridworld.generate(seed)` 是 seed 的纯函数，以上每个数都锚定在 seeds 1–200。
