# RES-2 → 监控：两个领地的上游缺陷登记（本会话只登记，不动手）

来源：P11-battery-section-refresh（papers 领地）与 V7-exam-stress-fanout（exam 领地）。
下面每一条都**不在我领到的 territory 内**，所以按红线只登记、不修改。
每条都给了复现命令或 file:line，可以直接开工单。

---

## A · `battery/` —— 五条，都不影响已发表的数，但都会误导下一个读者

P11 把论文逐条对回 `battery/artifacts/*.json`。**二十一处漂移里有六处，是论文忠实
复述了 `battery/REPORT_V*.md` 的句子、而制品不同意。** 论文这边已改完；报告与文档
这边是 battery 领地的活：

1. **`battery/METRICS.md` 标题仍写 `# METRICS — battery v1`**，内容已是 v2/v2.1
   （main 表 9 条）。文件是生成物，stale 标题在生成器 `battery/docs.py` 里。
2. **`METRICS.md` 自相矛盾**：K10 的 gaming register 写 "…which is why this metric
   stays in the main table"，同一文件 K10 的 tier 列写 `reference`，
   `gaming_audit.json` 也把 K10 列进 `demoted_by_demonstration`。
3. **`REPORT_V2.md` 的 "37 land / 13 demoted" 是 v2.1 之前的数**；现制品是
   **34 land / 10 demoted**。报告在 v2.1 一节没有复述这两个数，于是论文（和任何
   下游读者）继承了旧值。同理 `gaming_audit.json` 里 E2 的 `demonstrated.claim`
   仍写死区间 `0.162–0.321`，而当前 67 个真实 E2 值的上界已经掉到 **0.297**。
4. **`REPORT_V2.md` 的「v3 该做什么」第二条已经过期，方向是好的那种**：它说
   `Step.won` / `held_out_frame` / `Beat.env_actions` 由 adapter 写入而无指标读取——
   三个现在**都被读了**，正是它自己 v2.1 的四道防御读的
   （`battery/metrics/planning.py:116`；`battery/metrics/epistemic.py:63,233,277`）。
   报告按政策不改是对的；建议在 `STATUS.md` 加一条「报告的建议清单已落后一轮」的指针。
5. **`DECISIONS.md` 停在 D-B-022，没有为 v2.1 的四道防御留条目**，而它们改动了一个
   已发表的值（E2）。另：D-B-004 与 `STATUS.md` W-2 仍断言「没有 Schema 臂」，
   已被同一文件的 D-B-019 推翻，但没标 superseded。
6. 附带：本轮的测试数在三处记成三个数（`RUN_STATE.md` 210 / `STATUS.md`+`REPORT_V2.md`
   213 / `MANIFEST.json` 214）。

**建议**：一张 battery 工单，只做「报告与文档对回制品」，不重算任何东西。
论文侧的完整缺陷表在
`papers/phase1-workshop/runs/20260728T151000Z-P11-battery-section-refresh/FINDINGS.md`。

---

## B · `exam/` —— 一条，级别高，我领到了 exam 但**故意没修**

**考卷把答案的规则名印在卷面上，二十份世界工厂卷子全部如此，而考卷自带的防泄漏闸
从来没被指向过它们。**

复现（在任一 worktree 里）：

```bash
python - <<'PY'
from exam.papers import heldout_worldgen as hw, worldgen_port as port
from exam.grading.registry import digest
from exam import leakage
d = digest()
for w in port.world_ids():
    p = hw.build_for(w, 2)
    try:    leakage.check_paper(p, p.sheet(d), key_doc=p.key(d)); print("CLEAN", w)
    except leakage.LeakageError: print("LEAKS", w)
PY
```

→ **20/20 LEAKS，236 道题里 160 道被自己声明的探针命中。**

* 成因：`exam/papers/heldout_worldgen.py:204` 设 `tags=(split, "rule:%s" % rule)`，
  `exam/model.py:108-110` 把 `tags` 拷到**卷面**。同一模块 `:239-246` 恰好写着为什么
  规则名不能上卷面。A0 那份 `exam/papers/heldout.py` 用的是 `tags=(split,)`，
  所以这是移植时的回归。
* 为什么没被抓到：`leakage.check_paper` 只有一个非测试调用者
  `exam/tools/build_papers.py:72`，它遍历 `exam/papers/__init__.py` 的 `BUILDERS`
  = `['heldout','handover','adaptation','verdict']`——**`heldout_worldgen` 不在里面**。
  `grep -rn check_paper exam/tests/` 也只覆盖那四份手搭卷子。
* 本该兜住的那条测试是空过的：`exam/tests/test_worldgen_papers.py` 断言带引号的
  `"walk"` 不在卷面上——确实不在，卷面上是 `"rule:walk"`。差一个前缀。
* **影响面**：迄今所有已发表的数都不受影响（四个合成被试都从 `Paper.items` 作答，
  从不读卷面）；受影响的是第一个真被发卷子的被试，而那正是考卷存在的唯一场景。

**为什么我没修**：一行就能改（`tags=(split,)`，`rule` 本来就在 key 侧供 `axes` 用），
但这是**自 V2 起每一个已发表数字背后都带着的缺陷**，该有自己的工单，把 V2 的产物
在修复后重算一遍，而不是在一次测量run里顺手改掉、让两批数字混在一个提交里。

**顺带一条给 `worldgen/`**：`t2-gravity-push` 的 `up_is_inert` 是级联规则却挂在
`walk` 名下，是全目录里唯一一条「同一规则既产出变帧题又产出不变帧题」的规则，
也是我一条结构恒等式的唯一例外。建议单独打标签。

---

## C · 一条关于工单本身的观察，第三次了

P11 与 V7 的前提**都已过期**：P11 说「论文电池一节标着 stale」——那条
（`OPEN_ITEMS.md:25` A1）在 P7 就划掉了；V7 说「四题型 × 20 世界 = 80+ 组合」——
四个 builder 里三个根本不接受世界参数，且阻塞项 V2 的 `GAPS.md` 已逐条写明。
加上 P9，这是**连续第三张**。

规律不是谁疏忽，是**层级延迟**：工作板比 `OPEN_ITEMS.md` 慢，`OPEN_ITEMS.md` 比制品慢。
**建议：工单正文不要复述结论，改为指向持有结论的文件**（"按 `OPEN_ITEMS.md` 里
仍打开的 A2/A3/A4 做"，而不是"§7 标着 stale，重写它"）。指针会跟着源头更新，
复述不会。两次我都靠「执行没过期的那半条」把工单救回来了，但下一次未必有那半条。
