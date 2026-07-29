# E6 done — §3 的表已装配；两处提醒，一处缺口

工人 W-130，分支 `agent/e6-engine-dividend-v2`（已 push）。
交付物 `engine-rig/ENGINE_DIVIDEND.md`，由 `python -m tools.engine_dividend_table`
从三份产物装配，`--check` 防陈旧。

**注意分支名带 `-v2`**：`agent/e6-engine-dividend` 已存在但无任何提交（W-1611 被扫时
全部未提交、且基线过时），所以从当前 master 另开。旧分支与旧 worktree 可回收。

## 给写论文 §3 的人的硬提醒

**`ENGINE_DIVIDEND.md` §A 不可单独引用。** 三条理由都在文件里，但值得在这里重复：

1. §A 两列（bundled BFS 与 `astar(blind())`）**都是无启发式的对照**，不是梯子会选的档。
   真正会跑到的档收益小得多。
2. `ipdb` 列已被 E7 降级为「测了但不作证据」。
3. **guard 的选择带符号**：同一批定理换 `indexed` 编码，`far5` 盲搜 958→**1159**，
   倒亏 21%。「红利是真的」对印出来的那列成立，对本可以印的另一列不成立。

另：定理数不等于**到达规划器**的定理数——`singleton` guard 在 `far7` 上只表达 8/40，
所以表里有 `carried` 列。

## 两件早已做完，本条目引用而不重跑

E6 三件事里 (A) 死锁红利与 (C) 三档梯子 E2 已测、E7 已审。真正缺的是 (B)：E5 自己
在 RUN_STATE §7 写明 pagoda 证书没被复核。**这类重叠值得监控在派单前扫一眼**——本条目
花在划界上的时间是省下来的，不是浪费的。

## 一条值得单独派单的缺口

`bench.verify` **指不了 dividend-only 的 run**：它要求 `ladder.json`（本 run 不产出），
且检查只覆盖梯子行、不覆盖任何红利字段。目前 manifest 哈希能验、`--check` 覆盖装配表、
pytest 覆盖新代码，但**没有单一的 `verify <本 run>` 入口**。建这个入口不在 E6 范围内。

## 一条方法论，已写进 D-033

装配器**读裁决，不重新推导裁决**。理由是第一版重新推导了 §C 的最优性一致性，把
「没有已知最优解」算成「不一致」，对 `lmcut`/`ipdb`/bundled BFS 印出 **no**——在一份
专门用来被论文引用的文件里，诬告三个可采纳规划器返回了非最优计划。E2 的产物里
`agreement_ok: true` 明摆着。

同一形状的缺陷还有三个：**列读了不存在的键，渲染成一张全是 `--` 的合法表格**
（`config`/`rung`、`plan_unchanged`/`plan_length_unchanged`、`n_region`/`n_satisfying`、
`dividend_min`/`guards.<guard>.dividend_min_pct`）。**重渲染再 diff 的 `--check` 一个都抓不到**
——它只证明文件与渲染器一致，不证明渲染器读对了字段。其中 plan 那列最糟：
`stub.get("plan_unchanged", True)` 会给一个改变了计划的 guard 印上 `unchanged`，
**把一条可靠性断言默认成真**。现在每一列都由「钉住真实测量值 + 扰动一个字段要求对应
单元格移动」的测试盯着。**别的条目若也在渲染汇总表，建议照此自查。**

验收：`python -m pytest` **407 passed**；`--check` ok；`python -m recheck.verify_all`
**VERDICT GREEN**（42 条伪造全部按声明，其中 2 条是**声明的漏网**而非捕获——
`delete-the-rule` 是任何证书检查器都看不见的一类攻击，把它算成捕获就是把已承认的
盲点粉饰成功劳）；`python -m bench.verify <E2 run>` ok。
