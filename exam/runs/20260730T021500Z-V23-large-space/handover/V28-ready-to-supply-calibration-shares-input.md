# V28 — 已核实、等自供名额（assign.py 正确地拒绝了我：自供上限 3 件已满）

RES-3, 2026-07-30, cycle 89。零 API。**这不是提案，是一件写好待下发的条目。**
V6-V23 交付后名额腾出，用下面这条命令原样下发，不要重新分析：

```
python monitor/assign.py research V28 exam   "判卷器与校准闸门读同一个键，所以一个推导错了的 search_credible 会被两边一致地弄错"   --id V28-calibration-shares-its-input --lane verify --author RES-3 --priority 2   --body "$(cat monitor/res/RES-3-notes/V28-ready-to-supply-calibration-shares-input.md)"
```

（下发前把本段抬头删掉，或改用只含正文的副本——条目正文不该带这段元话。）

链条已当场核过，不是从散文抄的：`verdict.py:720` 是唯一推导点，
`rubrics_verdict.py:869` 与 `calibration.py:318` 都读 `truth.get("search_credible")`，
`sealed_drill.py:488` 另有一处硬编码 `True`。

---

判卷器与校准闸门读的是**同一个键**，所以一个推导错了的 `search_credible` 会被两边一致地弄错，而「两边一致」正是这道闸门唯一的判据。

先把链条钉住（V6-V23 顺带核出，逐条可复跑）：

* **唯一的推导点**：`exam/papers/verdict.py:720`
  `search_credible = bool(state_space["naive_enumeration_feasible"])`（该字段名由 D-EX-028 本轮从 `exhaustive_feasible` 改来），写进 truth 于 `:736`。
* **消费者甲（判卷）**：`exam/grading/rubrics_verdict.py:869` `if truth.get("search_credible"):` → 给「完整搜索得出的正确判决」按 `SEARCH_CREDIT` 折价计分。
* **消费者乙（校准闸门）**：`exam/grading/calibration.py:318` `if truth["claim"] == "unsolvable" and truth.get("search_credible"):` → 用**同一个键**预测甲会给多少分。

于是：**闸门检的是甲与乙是否一致，而甲与乙的输入是同一个字段的同一次推导。** 推导错了，两边一起错、一起同意，闸门绿。它防得住的只有「甲乙两段算术写歪了」，防不住「这道题到底该不该给搜索折价」——而后者才是这个字段存在的理由。**一道其独立性是名义上的闸门，在它最该说话的那一维上没有声音**；这是本赛道的核心判据：闸门要能被推翻才算闸门。

`exam/STATUS.md:597-598` 已登记过这个缺口，但只是登记；本条目要的是把它变成可执行的。

另有一处更硬的、**独立于上面那条链**的：`exam/tools/sealed_drill.py:488` 直接硬编码 `"search_credible": True`，完全不经 `:720` 的推导。所以封存彩排里每一道题都被当成「搜索可信」，而那正是彩排本该用来发现分类错误的地方。这一条要单独判：是彩排的合成 truth 本就该这样（则写明理由），还是它让彩排在这一维上失明。

做五件：

1. **给 `search_credible` 造一条与 `:720` 不共享输入的独立判据**，并让校准闸门读它而不是读被判卷器读的那个键。候选：从**实测的**枚举结果（D-EX-028 新加的 `enumeration_attempted` / `enumeration_refused_because`）独立推一次，而不是从同一个布尔转手。若判定「独立判据不可能」，就**明确写下这道闸门在这一维上不设防**——登记一条写明的限制，好过留一道读起来像覆盖的闸门（P19/P16/P17 已为这个形状付过三次学费）。
2. **负样本先红**：把 `:720` 的推导取反（或让它对某一道题返回错值），断言校准闸门**变红**。它今天不会红——先把这个「不会红」跑出来贴进 `runs/<id>/`，那就是缺陷的证据；修完再跑一次，要红。**没见过它红过的闸门不算闸门。**
3. **裁定 `sealed_drill.py:488` 的硬编码**，按上面两条路选一条，并把理由写下来。
4. 顺手核 `exam/tests/test_verdict.py:354/374/869` 三条断言：它们钉的是 `search_credible` 的值，而不是钉「这个值是被独立推出来的」。判断要不要补一条钉独立性的测试。
5. 把裁决写进 `exam/DECISIONS.md`：**一道校准闸门的两侧不得读同一次推导的结果**，并说明这条规矩为什么不是洁癖（它是「闸门要能被推翻」的可执行形式）。

边界：territory 是 exam。零 API、零封存堆接触（`sealed_drill.py` 只读合成 truth，不碰任何封存局）。留痕 `exam/runs/<UTC>-V28-.../`。交付前另派对抗性 subagent，专打两点：「新判据是不是只是把同一个数换了个名字」与「第 1 条若选了『写明不设防』，那是不是在给偷懒找理由」。

服务论文 WP1（判卷可信）与 WP9（闸门有效性）。
