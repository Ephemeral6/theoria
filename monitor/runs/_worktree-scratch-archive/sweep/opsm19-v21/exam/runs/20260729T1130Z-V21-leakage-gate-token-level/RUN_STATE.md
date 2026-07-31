# V21 · 泄漏闸门是「通过」，不是「有效」 —— 过程记录

条目 `V21-leakage-gate-token-level`（p1，cell V2，territory `exam`，lane `verify`），RES-3。
分支 `agent/v21-leakage-gate-token-level`。结论写进了 `exam/STATUS.md` 的
「V21 — the leak gate was passing, not checking」一节，本文件只记过程与判断。

## 工单报的那条，逐行核实属实

`metadata_hits` 按 `canonical(value)` 整值分桶，再把只装一件的桶全部丢掉。
于是**值里任何一个唯一 token**——一个 `level:` 标记、一个逐题 id——就让每个桶都成为单例，
于是什么都没被打分，于是一条与值的其余部分共享的真泄漏**在结构上不可见**。

代码原本的注释为「丢单例」给的理由是对的（一个只出现一次的值背后没有第二件可以用来检验规则），
**但那个理由只对「整值当规则」成立**。`tags: [..., "dead"]` 里，整个 tag 列表逐题不同，
而 `dead` 恰好只落在答案是 `dead` 的那些题上——那是印在卷面上的答案键。

## 修法分两半，且刻意保留了旧的那一半

* **token 级**：每个值再切成 token，每个 token 当一条二元规则检验——
  「带着它」能不能预测答案。只落在一件上的 token 是标识符不是规则，
  落在每件上的 token 什么也不预测，两者都跳过——**这正是让检查不乱叫的部分，
  而一个乱叫的检查会被关掉**。
* **整值分桶保留为第二道，不是被替换掉**。原始的 `points` 2-vs-3 泄漏（可解题值 3、
  不可解题值 2，17/17 被作弊者读走）**在 token 级根本抓不到**——那些 token 太短，
  切完就没了。两道网眼形状不同，缺一不可。
* 单例桶仍然不打分（没有第二件可检验），但**不再被静默丢弃**：
  `metadata_coverage()` 报出每个字段有多少个值因此没被打分。
  **「没有命中」和「什么都没检查」印出来一模一样，含义相反。**

## 重审四份卷子时，查出比工单所报更大的一条

`derive_label_sets` 要求某个真值字段覆盖 **60% 的题目**，才把它当作「本卷的答案类」。
**一份由多个题族拼成的卷子没有这种字段。** 于是：

| 卷子 | 修前推出的标签集 | 修后 |
|---|---|---|
| `p15-adaptation-a0` | **0** | 3 |
| `p15-handover-a0` | **0** | 1 |
| `p15-heldout-a0` | 2 | 2 |
| `p15-verdict-a2` | 3 | 4 |

**四份卷子里有两份推不出任何标签集，于是 metadata 检查跑在零个标签上——
186 题里的 89 题，绿是因为没看。** 那道门槛问的是「这是不是*本卷的*类」，
而真正该问的是「这够不够得上被检验」；**只落在一个题族里的泄漏仍然是泄漏。**
门槛改为 `MIN_LABELLED = 4`，与 `_metadata_hits_within` 自己在打分前已经要求的最小件数一致。

**审计结果——这才是工单第 4 件事要的东西**：在 token 检查加宽网眼之后，
四份卷子**全部推得出标签集，且全部干净、两类命中都是零**。
所以卷子本来就是干净的；缺的是「看过」。
`test_every_shipped_paper_derives_at_least_one_label_set` 从此守着这条：
哪份卷子再出现「绿是因为没检查」，它就红。

## 第三条：不是工单报的，是加宽网眼自己撞出来的

放宽后全量测试红了一处，查下去是一个**先前就存在**的缺陷：
丢掉单例桶之后，**剩下被打分的那个子集可能只剩一种答案**。
此时「预测率」按算术必然是 1.0——每个桶的多数就是它的全部——
而 floor 仍然按整组算，于是一个字段因为「预测了唯一还剩下的那个答案」而被判泄漏。
`v11-handover-a0` 就是活的例子：三个 tag 桶各两件，全部 `solvable: true`，
被以 1.000 对 0.750 判红。

`metadata_hits` 本来就写着「一种可能的答案不成其为问题」并据此提前返回，
**只是那条规则从没被套用到它最终真正打分的那个子集上**。
现在 floor 按被打分的项重算，且退化子集直接跳过。

## 负控两条，两个方向都测

工单第 3 件事要求的两条都在 `exam/tests/test_leakage_tokens.py`：
带 `tags: dead` 式泄漏的卷子**必须变红**（并另有一条测试**演示**旧的整值检查
在同一份卷子上产生十二个单例桶、什么都不打分），干净的卷子**必须仍然绿**。
另加常量 token、单件 token、退化子集三条，防的是同一件事：
**把闸门修成一律拒绝，等于把闸门关掉。**

## 复跑

```bash
python -m pytest exam/tests/test_leakage_tokens.py -q   # 8 passed
python -m pytest exam/tests -q                          # 349 passed, 2 xfailed
python -m exam.verify
```

## 产物只提交了一份，另外十四份复原了

`python -m exam.verify` 退 0（GREEN），但它照例把一批被跟踪产物改脏了。逐份归因之后：

* **`exam/artifacts/leakage.json` 提交了**——它是这道门自己的报告，而这次改动正是
  改变它内容的原因。diff 里没有一行 `rubric_digest`，改的全是
  `label_sets_checked: [] -> ["rule"]` 这类东西，也就是「这份卷子现在真的被检查了」
  这件事本身。**不提交它，committed 的那份就会继续声称 handover 的 label_sets 是空的，
  而那句话已经不真了**——那正是本轮在治的病。
* **其余十四份复原了**（`calibration` / `exam_summary` / 四份 papers / 四份 truth /
  `matrix` 两份 / `selftest` / `build_manifest`）。它们的 diff **只有 `rubric_digest`
  那一行**：`e06bdf52` → `63ce1eab`，是 V6 已经查实并归档的既有陈旧
  （`exam/SEALED_DRILL.md` §4c，提案在 `monitor/inbox/20260729T1120Z-RES-3-proposal-V24-*`），
  与本件无关，不该混进这个 diff 里被埋掉。
  `build_manifest.json` 另有一层理由：它嵌绝对路径，提交它等于把本机路径写进产物。

判据很简单：**产物的变化如果是本次改动造成的，就该提交；如果是别处的陈旧顺路被冲刷出来，
就该复原并留给它自己的工单。** 两者混在一个 diff 里，谁也说不清哪一半是谁做的。

---

## 第二遍（cycle 65，2026-07-29T15:30–16:00Z）—— 对抗审稿回收之后

上面那一节是第一遍写的，它说「复跑 8 passed / 349 passed」。那两个数已经不对了：
第一遍收尾时我从对抗方的脚本名反查出自己两条缺陷并补了两条测试（10 / 352），
而这一遍读完对抗方的完整输出后又改了两轮（先 19 / 361，收尾补第 20 条测试后
**20 / 363**；变异 23 条）。
**报告里的数字必须跟着重跑走，不能跟着记忆走**——这正是隔壁 E18 那张票的病。
交付前的最后一次串行复跑就是为了这个：上一世写下 19 / 361 时那是真的，
交付时它已经不是了，而**一份写着旧数字的报告和一份没跑过的报告一样不可信**。

### 报告是重建的，不是收回来的

派出去的对抗 subagent 在 12:00Z 前后死了，`adversarial/` 里留下 12 个探针脚本、
零份结论。这一世把 12 个脚本逐个重跑，原始输出存 `adversarial/PROBE_OUTPUT.txt`
（382 行，sha256 前 16 位 `28936ffec1d75c0a`），裁定写 `adversarial/ADVERSARIAL.md`。

**这件事本身是本轮最该记下的一条**：扇出的结论如果只活在 subagent 的上下文里，
它死了就等于没做过。交接文件里那句「对抗审稿的报告还没回收，交付前必须读完」
是唯一让这 12 个脚本没被当成已完成工作埋掉的东西。

### 对抗方推翻了什么（详见 ADVERSARIAL.md）

两条是我自己的测试：

* `test_a_token_on_one_item_is_an_identifier_not_a_rule` 的 fixture 里，
  单持有者 token 得分 **0.583**，容差 **0.900**——**把它名义上守着的那道守卫删掉，
  测试照样绿**。变异测试证实：10 条测试 0 条抓到。它断言的是容差的结果，不是守卫的结果。
* `test_a_subset_correction_does_not_desensitise_the_token_check` 是源码 grep，
  同一个回归的六种拼法**四种绕得过去**。

三条守卫此前完全没有测试（`MIN_TOKEN`、`MIN_LABELLED`、token 级 floor 的严格性），
对应变异全部 0/10。四条都已补。

一条是第一遍自己的病：`metadata_coverage()` 加了，**除测试外无人调用**，
`leakage.json` 里一个字没多。**判据跑了、绿了、被当成证据用了——
同一个形状出现在治它的那次修复自己身上。** 已改为 `metadata_scan()`
单次遍历 + `check_paper` 写 `report["metadata_unscored"]`，常量字段 / 缺失字段 /
整组不足 4 件全部带理由记账。

由此看见的一条：**`p15-verdict-a2` 的 metadata 检查在四个标签集上一格都没打分**
（三个字段全是常量）。那个绿是诚实的，但它此前和「查过且干净」印出来一样。

### 这一遍新做的判断

* **`item_id` 加入 `METADATA_FIELDS`。** 探针构造了 id 读作 `q-dead-01` 的卷子，
  闸门放行。整值分桶永远查不了逐件唯一的字段，**是 token 检查让它第一次可查的**。
  四卷加上它仍全绿，所以这份覆盖率是白拿的。
* **单持有者（M5）不修，并写明理由。** 落在唯一一件少数类上的 token，
  留一法按算术必然 1.000，「修好」它等于让每个逐件标识符开火。
  乱叫的闸门会被关掉。留作独立工单。
* **名单外字段不是遗漏。** `board` / `definition` / `state` 就是题目，
  题目特征预测答案叫解题。独立留一法审计正好撞在这儿——
  它报 `count:board` 以 1.000 预测 `solvable`（基线 0.750），那是解出来的样子。
* **加宽网眼的假阳性率量出来了，并写进 STATUS.md。**
  n=4 均衡切分 0.20、n=5 0.08、n=6 0.036，而真卷子最小的被打分组正是 n=5、n=6。
  置换零假设：`v11-handover-a0` 的 `solvable`（n=8）**0.117**，
  `p15-adaptation-a0` 的 `exact_on_heldout` 0.013，其余 11 个字段 0.000。
  **门槛留在 4**（「绿是因为没看」比偶尔误报贵），但这个数必须跟闸门一起公布。

### 变异表刷新时撞到的一条，值得单记

第一遍的变异 K 这次报 `PATCH DID NOT APPLY`——因为我把 `singletons` 改名成了
`declined`，补丁文本对不上了。**一条不再适用的变异会安静地报成一行空白，
看起来和「被抓到」一样无害。** K 已按新源码刷新，另补 K2–K5 覆盖这一遍新增的
四处记账。23 条变异现在每一条都至少被 20 条测试中的一条抓到（`adversarial/MUTATION_TABLE.txt`）。

### 复跑

```bash
python -m pytest exam/tests/test_leakage_tokens.py -q   # 20 passed
python -m pytest exam/tests -q                          # 363 passed, 2 xfailed
python -m exam.verify
python exam/runs/20260729T1130Z-V21-leakage-gate-token-level/adversarial/a10_mutation_test.py
```

### 第二遍收尾时又抓到三条

1. **`item_id` 上线后 `test_core.py` 两条变红——是真泄漏，不是误报。**
   `_labelled` 夹具从 P-15 起把 id 造成 `solvable-0` / `unsolvable-1`，
   答案原文印在每一件的 id 里，而那正是用来测 `points` 泄漏的夹具。
   已换中性 id，旧形状留作
   `test_the_old_labelled_fixture_was_itself_an_item_id_leak`。
   **我先前的经验检查漏掉它，是因为我只在四份出厂卷子上测了误报，没测夹具**——
   抓到它的是全量套件，不是我。
2. **变异 K3（整组不可打分记账）0/19，无人钉住。** 已补
   `test_a_group_too_small_to_score_is_recorded_rather_than_skipped`。
   我第二遍新加的四处记账里，有一处自己没测——和第一遍
   `metadata_coverage()` 加了没人调用是同一种手滑。
3. **变异表自己有盲点。** 补丁失配只打印一行安静的字，看起来和一行正常表格一样无害，
   却测了零个东西（第一遍 K，第二遍 O）。`a10` 现在汇总 `STALE` / `UNPINNED`
   并据此设退出码。**判据自己也需要一个判据。**

### 一条方法教训（下一个人可以省下）

**同一个领地不要并发跑测试。** 我同时跑 `a10_mutation_test.py`（它在进程内
逐个执行测试函数）和 `pytest exam/tests`，得到一条
`test_spec_files_are_byte_identical_across_builds` 失败——**单跑即过**。
那不是 flaky，是我自己造的并发踩踏，和交接里记的
「两个 `verify.sh` 抢同一个 `.verify/`」是同一类。
差别在于这一次它伪装成了一条真缺陷，而我差点把它写进报告。
本轮之后 a10 与 pytest 一律串行跑。

## 收尾（cycle 69，串行复跑）

前一世死在「核数 → 复跑 → 提交」之间。这一世接上，全部串行跑，没有并发踩踏：

```
a10_mutation_test.py      OK: 23 mutations, every one caught by at least one test   (exit 0)
pytest exam/tests -q      363 passed, 2 xfailed (139s)
python -m exam.verify     GREEN — build_papers / pytest / run_exam --calibrate /
                          run_selftest / determinism 全 ok，两个 hash seed 摘要一致
```

RUN_STATE 与 ADVERSARIAL 里写的三处数字（**23 条变异 × 20 条测试 / 363 全量**）
与重跑输出逐字相符，无需修正。

### 提交范围：为什么只有 `leakage.json`

`exam.verify` 跑完之后工作树脏了 15 个 artefact。逐个查过，其中 14 个与 V21 无关：

* `build_manifest.json` 里存的是**绝对路径**，还指着 `.worktrees/v4-exam-selftest/`；
* 其余 13 个的全部差异是同一行 `rubric_digest`：
  committed `e06bdf52…` → rebuilt `63ce1eab…`。

**这不是我的改动，是仓库里本来就有的漂移。** 判据不是眼力，是实验：在
`.worktrees/_v21_clean` 上 detach 出 `agent/v21-leakage-gate-token-level` 的干净 HEAD
（**不带任何 V21 改动**），只跑一次 `python -m exam.tools.build_papers`，
同样的 9 个文件同样变脏，`rubric_digest` 同样从 `e06bdf52…` 变成 `63ce1eab…`。
所以这 14 个已 `git checkout --` 还原，提交里只有 `leakage.json`
（已确认零绝对路径，diff 全部是 token 检查与 `item_id` 带来的真实内容）。

### 顺手撞出的一条缺陷，比还原动作本身值钱

上面那个实验顺带证明了：**`python -m exam.verify` 报 GREEN，并不意味着仓库里
签入的 artefact 就是这份代码产出的东西。**

`build_papers` 是**就地覆盖**；而 determinism 那一级比的是**两次新构建之间**
（`PYTHONHASHSEED` 7 对 99）——`verify.py:60-80` 全程只在内存里算摘要，
**从头到尾没有任何一级把构建结果和已签入的文件比过一次**。
于是签入的四份卷子、四份答案、calibration 与 build manifest，是一份
**已经不存在的 rubric** 生成的，而闸门这段时间一直是绿的。

这与 V21 本身同形，只是高一层：检查跑了、绿了、被当成证据用了，
而它量的不是它名字声称在量的东西。已写进 `exam/STATUS.md` 弱点第 20 条，
并自供工单 `V25-verify-does-not-check-what-is-committed` 去修——
不在 V21 范围内（V21 的格子是泄漏闸门），但留着不说等于把它埋了。
