# 对抗性复核：ENGINE_TABLE.md 的八行与它的生成器

**任务** 试图推翻 E9 的交付物（`engine-rig/ENGINE_TABLE.md` + `engine-rig/tools/engine_table.py`）。
**树** `.worktrees/e9-engine-paper-table/`，只读，本文件是本次复核唯一的写入。
无网络，未读 `.env`，封存堆零接触。所有实测在会话临时目录里做，脚本未入库；
唯一一次改动仓库文件（往 `ENGINE_TABLE.md` 尾部追加一行以测试 `--check` 的失效检测）
在同一条命令里恢复，`git status --porcelain` 复核前后一致。

**立场**：以下每一条「推不翻」都是在认真找过反例之后写的。

---

## 0. 判决摘要

| 被复核的主张 | 我的判决 | 强度 |
|---|---|---|
| **(a-1)** `mdl.verdict_flips` = 10 世界翻转压缩判决 | **推不翻**（数字与句子都对）；相邻句「Geometry is exact」**削弱**——漏掉 127/300 世界的对象分解是错的 | 实测+读码 |
| **(a-2)** `cegis.battery_green` = 「电池在全部 **188** 个**受影响**世界上零 finding」 | **削弱** — 188 是 72 + **全部 116** 个产 lifted 的世界；「受影响」的口径是 162。换了分母又套了小分母的谓语 | 实测 |
| **(a-3)** `zs.g50t_worst` = 「**最差**的一组是 370 特征 / 6 转移 / 366 维」 | **削弱** — 探针算的是**众数组**（`max` by count），不是最差组；而本仓唯一说「最极端」的来源（ADVERSARIAL-zero_space）指的是**另一组**：365 特征 / **5** 转移 / 362 维 | 实测 |
| **(a-4)** `lp.incomplete` 29.2 % 与 `lp.correct_decline` 24.0 pp 并置 | **削弱（分母切换）** — 46.6 % 与 24.0 pp 是 **N=500** 的数，29.2 % / 21.3 % 是 **N=3000** 的数；且「overstates by about 2×」只对 22.6 % 成立，对 29.2 % 是 1.6× | 实测+读码 |
| **(a-5)** `dl.candidates` = 「**17 theorems** in the committed candidate stream」 | **推翻** — 17 行里只有 **16** 条是定理；第 17 行是 `kind:"plan"` 的 `pruning_account`，`claim` 为空。E11 §1a 与 `STATUS.md:189` 都说 16 | 实测 |
| **(a-6)** `fd.crosscheck_agree` = 「**Every rung** is run against the others … 7/7 agree」 | **推翻** — `cross_check` 只有两个参与者（FD `astar(blind())` vs stub），7 是**实例数**不是 rung 对数；satisficing 一次都没参加。附带**削弱**：「three of them FD independently **proving** an UNSAT」，那三行的 `fd_exit_code` 全是 **12** | 实测 |
| **(a-7)** `pf.infinity_rows` = 「裸 `Infinity` **reaches** the shared candidate stream in 1633/4000 rows」 | **削弱** — 来源第 7 节明说「端到端跑批目前踩不到」，触发面限于直接调用方与 fuzz 语料。现在时叙述丢了这个限定 | 读码 |
| **(a-8)** `rig.unaudited_fields` = 「111 个字段里 **64** 个 asserted by no invariant」 | **削弱** — 来源的「被不变式断言」列是 **25**，所以「无不变式断言」的是 **86**；64 是「未被审」列，把 22 个「仅作索引/门控/聚合」的字段算到了「有断言」一侧。误差方向对仓库有利 | 实测 |
| **(b)** 有没有把「未测」写成「已测」 | **有一处，第 3 行 `zero_space`**：「Behaviour on any family but `parityworld` **and `g50t`** is 边界未测」把 g50t 放在了已测那一侧。本仓无任何 g50t 上的正确性测量，来源两次明写做不到 | 实测+读码 |
| **(b)** 第 7 行「across **the whole** unsolvability inventory, 50 CONFIRMED, 0 refuted」 | **削弱** — E11 §8 列出**至少 17 条**从未裁决的 unsolvability 主张（exam 9 条、proxy 3 条、a3 负控 1 条、ablation 复制品 2 条 …）。是「全部**已裁决**清单」，不是「全部清单」 | 读码 |
| **(b)** 第 8 行 `ic3_pdr` 的 **边界未测** | **推不翻** — 我逐项查了：`campaign.json` 6 个引擎无 ic3、`fuzzlab/props/` 无 ic3 模块、无 `mutation.ic3_pdr.json`、`candidates.jsonl` 恰 1 行。全对 | 实测 |
| **(b)** 有没有把「已测」写成「未测」 | **推不翻** — 五处 `边界未测` 逐一核对，无一处其实已被测量过 | 实测+读码 |
| **生成器**：ROWS 散文里「没有裸数字」（`RUN_STATE.md` 原话） | **推翻** — 至少 **28 个**实质裸数字不经任何探针；其中 `fd` 行的 `(all **four** are pinned…)` 与 `{fd.unaudited}` 手工耦合，`pf` 行的「entropy mismatches」复用了 `{pf.partition_mismatch}` | 实测 |
| **生成器**：非零退出真的接通了 | **推不翻** — 我自己另做四个 mutant，退出 1/1/3/3 全部如预期；`--check` 也真的抓到了我追加的一行 | 实测 |
| **生成器**：`--check` 的确定性与当前性 | **推不翻** — 118 facts verified，`ENGINE_TABLE.md` is current，exit 0 | 实测 |

一句话：**没有一个数字是编的——118 条 fact 我抽查了 8 条加若干旁证，位位对得上。
垮的是数字外面那一圈句子：两处分母切换、一处「17 theorems」是错的、一处「every rung」
是错的，以及一处把从未测过的 g50t 写进了已测那一侧。**

---

## 1. 抽样 8 个数字（assignment a）

抽样跨 8 行中的 7 行 + 一条跨引擎汇总，跨 6 个不同产物：4 份 E11 partial、
1 份 E11 ADVERSARIAL、`theoria-arm` 的 g50t `candidates.jsonl`、
`engine-rig/artifacts/candidates.jsonl`、`p13-fd-real/dividend.json`、
`V10/PUBLISHED_VS_AUDITED.md`。

### a-1 · `mdl.verdict_flips` = 10 — **推不翻**（但相邻句削弱）

表里的句子：

> correcting the 5.7 % undercharge makes **10 worlds stop beating the per-pixel
> baseline**, on this engine's own headline comparison.

来源 `partials/mdl_segmenter-via-reconstruction.md` §6 D1 原文：

> | worlds that stop beating the baseline once the id is honest | **10** (242 → 232 of 300) |
> …
> Ten worlds change verdict on the engine's own headline comparison.

数字、分母、以及「on this engine's own headline comparison」这半句**逐字来自来源**。
`5.7 %` 同样是原文（`9675 bits over 168 843 bits of script (5.7 %)`）。**推不翻。**

**但同一格开头那句削弱。** 表说：

> **Measured.** Geometry is exact — **0 wrong cells in 506 302**

「0 wrong cells」对（§4 表格）。可 §8 第 6 条是这样写的：

> **173 / 300 worlds match ground truth in every frame; 5979 / 6993 frames (85.5 %)
> match; 127 worlds report more tracks than the world contains, worst case 40 tracks
> for 4 real objects.** … **Partition-correct and object-wrong are different things,
> and only ground truth separates them.**

也就是说：像素级几何是精确的，**对象分解在 127/300 个世界里是错的**。
来源专门写了一句话提醒不要把这两件事混为一谈，而表只留了前一半，
用「Geometry is exact」开头。这不是假话，是**选择性的真话**，且方向对引擎有利。

同理，§4 的另一个分母也没进表：**「worlds replayed pixel-exact on every frame:
121 / 300 (40.3 %)」**。表只用 cell 分母（3.5785 %）。来源自己讨论过这个张力
（"a much better position than '40 % of worlds fail' suggests"），所以表的取舍
有出处；但读者拿不到另一个分母。

### a-2 · `cegis.battery_green` = 188 — **削弱（分母/谓语错配）**

表里的句子：

> The fuzz battery returns **zero findings on all 188** affected worlds

探针取自 `ADVERSARIAL-cegis.md` 的 `battery verdict over the union : {'EMPTY': 188}`。
我读了那一节的**全文**（§5）：

> * 报告的 162 = 72（F-1）+ 90（有不成立 lifted 的世界）。我的 188 = 72 + 116
>   （**所有**产出 lifted 的世界）。口径不同，**188 ⊃ 162，所以报告的 162 满绿
>   a fortiori 成立**。

**188 的口径是「72 个 F-1 世界 + 全部 116 个产出 lifted 规则的世界」，
其中 116 里只有 90 个真的带着不成立的 lifted 规则。** 「affected」（受影响）
的口径是 162，不是 188。表拿了大数字，配上了小数字的谓语。

这正是工单点名的那种失败：**一个总体上算出的计数，被摆在另一个总体的名下。**
方向上它让「电池瞎」这个结论听起来覆盖面更广。修法只有两个，选一个：
把 `188` 换成 `162`（并换探针），或把 `affected` 换成
`worlds carrying an unaudited lifted rule or an all-`none` rule set`。

（顺带核了同格的 `1209`：表写「the **1209** resulting rows are *true statements
about that rock*」。这个定性**是对的**，而且是对抗复核推翻原报告后的正确版本
（`ADVERSARIAL-cegis.md` §1.3：72/72 世界里被挖物体全程零位移）。但探针的定位符是
`MOVE events in those worlds : (\d+)`——1209 是**该批世界里的 MOVE 事件数**，
不是「mined rows」数（那是 1595）。数字巧合相等是 §1.4 的发现本身，
不是同一个量。措辞上应写成「the 1209 transitions in which the world moved」。）

### a-3 · `zs.g50t_worst` — **削弱（「最差」不是探针算的量）**

表里的句子：

> on `g50t` the worst group is **370 features, 6 transitions, difference_rank 4,
> 366-dim law space**

探针（`engine_table.py:205-208`）算的是 `max(g, key=lambda k: g[k])`，即**出现次数最多的组**；
provenance 表自己也诚实地写着 `modal (…) group`。我自己重算了
`theoria-arm/runs/20260728T015354Z-g50t-first-contact/candidates.jsonl`：

```
1821 zero_space rows, 3 distinct groups
  732 rows  (370 features, 366 dim, rank 4, coverage 6/6)   <- modal, and what the table prints
  724 rows  (365 features, 362 dim, rank 3, coverage 5/5)
  365 rows  (370 features, 365 dim, rank 5, coverage 7/7)
```

按「律空间维数最大」读，众数组确实也是最大（366）。**但按「证据最薄」读，最差的是
5 条转移那一组**——而本仓唯一表态过哪一组最极端的文件，说的正是那一组。
`ADVERSARIAL-zero_space.md`「我另外发现的」：

> 最极端的一批在 `theoria-arm/runs/…g50t-first-contact/candidates.jsonl`
> ```
> coverage 5/5   space_dimension 362   n_features 365   difference_rank 3
> ```
> **365 个特征、5 条观测转移、报出 362 维"守恒律"**

它的 escalate 措辞也用的是这一组（「量级为 362 维 / 5 条转移」）。
所以表用「the **worst** group」这个词去指一个 `max-by-count` 的探针结果，
既与探针语义不符，又与来源的判断不符。**tripwire 也不保护这句**：
如果众数组以后变了而最差组没变，`expect` 会响；如果最差组变了而众数组没变，它不会响。

同一句里还有一处口径拼接：

> so a law resting on **6** transitions and one resting on **40** are indistinguishable

`6` 是 g50t 的数，`40` 是 **Fixture B** 的数（来自 ADVERSARIAL 的 escalate 段：
「'5 条转移支撑的 362 维空间'与'40 条转移支撑的 9 维空间'」）。
两个数来自两个世界族，被拼成一句读起来像同一份产物内部的对比。g50t 里
根本没有任何一条律靠 40 条转移——三个组的分母是 5、6、7。

### a-4 · `lp.incomplete` / `lp.correct_decline` — **削弱（N=500 与 N=3000 混用）**

表里的句子（一整段，连读）：

> Incompleteness is **639 / 2189 = 29.2 %** of genuinely unreachable worlds
> (**21.3** % of all **3000**). The **46.6 %** figure that circulates is the
> *no-certificate rate*, not the incompleteness rate: **24.0** pp of it is the engine
> correctly declining to prove a statement that is false. Quoting 46.6 % overstates
> the boundary by about 2×.

来源 `partials/lp_potential-via-exhaustive.md` §4.3，**分两个规模写的**：

> | **at N = 500 (campaign scale)** | share of all worlds |
> | no certificate, because the goal **is reachable** — *correct* | **24.0 %** |
> | no certificate on a genuinely unreachable world — *incompleteness* | 22.6 % |
> | **total "no certificate"** | **46.6 %** |
>
> **At N = 3000** the incompleteness rate is **639 / 2189 = 29.2 % of truly
> unreachable worlds** (21.3 % of all worlds). … Quoting 46 % as the incompleteness
> number overstates it by about 2×.

两处问题：

1. **分母切换。** `46.6` 和 `24.0` 是 N=500 的；`29.2` 和 `21.3` 是 N=3000 的。
   表把它们串成一句因果（「46.6 % 里有 24.0 pp 是……」）而不标规模。
   在 N=3000 上对应的数是 §4.1 的 **48.3 %** no-certificate，
   而 21.3 + 24.0 = 45.3 ≠ 48.3——按表面读法**算不平**。
2. **「about 2×」挂错了参照。** 来源的 2× 是 46.6 / 22.6 ≈ 2.06（都以「全部世界」为分母）。
   表把它紧贴在 29.2 %（以「不可达世界」为分母）后面，而 46.6 / 29.2 = **1.6×**。
   数字都是真的，比值不是从并排的这两个数来的。

修法：把「(21.3 % of all 3000)」之后那两句改成
「at the campaign's own N = 500 the same split is 46.6 % no-certificate = 22.6 %
incompleteness + 24.0 pp correct refusal, so quoting 46.6 % as the incompleteness
rate overstates it by about 2×」——即把 2× 留在它自己的规模里。

### a-5 · `dl.candidates` = 17 — **推翻（数字对，句子错）**

表里的句子（fixture 格）：

> sokoban `open4` / `open4far` / `ring` / `ringstuck`; **17 theorems** in the
> committed candidate stream

探针是 `count(payload.producer == deadlock_carver)`，我复算 = **17**，数字没问题。
但我把这 17 行逐行打出来了：

```
lines 25-32   kind=invariant  "every reachable state containing at(b1,cXY) is dead"   (8)
lines 33-40   kind=invariant  "…at(b1,cXY) AND at(b2,cZW) is dead"                    (8)
line  41      kind="plan"     claim=None   payload.form="pruning_account"
              rendering: "16 deadlock theorem(s) cut sokoban-open4far from 808
                          expansions to 571 (29.3% fewer), plan length 11 either way"
```

**第 17 行不是定理，是剪枝账目**，而且它自己的 `n_theorems` 字段就写着 **16**。
两份独立来源同意：

* `E11/partials/deadlock-via-reachability.md` §1a：`candidates.jsonl` **lines 25–32** 与
  **33–40**，共 16 条 deadlock 主张；
* `engine-rig/STATUS.md:189`：「All **18** `deadlock_carver` theorems recheck green …
  — **16 on `open4far`, 2 on `ringstuck`**」（那 2 条 ringstuck 的只在 `recheck/cases/`，
  §1a 明写 "not in `candidates.jsonl`"）。

E9 自己的 `RUN_STATE.md` 措辞是对的（「**17 rows** for `deadlock_carver`」），
到了表里变成「17 **theorems**」。**这是本次唯一一处数字被明确转述成了错误的事物。**
改成 `16 theorems + 1 pruning account in the committed candidate stream`，
或换探针为 `count(producer==deadlock_carver and kind=="invariant")`。

### a-6 · `fd.crosscheck_agree` = 7 / 7 — **推翻「every rung」，削弱「proving」**

表里的句子（复核格）：

> **Differential + independent checker.** **Every rung is run against the others on
> the same instance** — **7 / 7** agree on plan length and on unsolvability,
> **three of them FD independently proving an UNSAT** the bundled search found

我把 `runs/p13-fd-real/dividend.json` 整个打开了。`cross_check` 有 7 个条目，
每个条目的字段只有两组：`fd_*` 和 `stub_*`。同一文件顶层：

```
"search": "astar(blind())"
```

于是：

1. **「Every rung is run against the others」是错的。** 参与者恰好两个——
   FD 的 `astar(blind())` 与 bundled stub。三级梯子的第三级
   （`fd-satisficing` / LAMA）在 `cross_check` 里**一次都没出现**。
   而同一行的 solves 格正好在推销「a three-rung planner ladder」。
2. **7/7 是「7 个实例」，不是「7 组 rung 对比」。** 7 个实例是
   `a0-spike/{match,mismatch}`、`cold-start-a0{,/no-button}`、
   `cold-start-a2{,/holed,/repaired}`。表的措辞会被读成 7 次跨 rung 的比对。
   （同一行 fixture 格把这同一批 7 个叫「7 generated **cold-start** domains」——
   其中两个是 `a0-spike`，不是 cold-start。）
3. **「proving」削弱。** 那 3 个 `fd_unsolvable: true` 的条目，
   `fd_exit_code` **全部是 12**。而本仓自己的裁决是：

   > `runs/p13-fd-real/TOOLCHAIN_MANIFEST.md:229-241` … states that 12 is
   > `SEARCH_UNSOLVED_INCOMPLETE` and not 11, and says a caller
   > **"should treat 11 and 12 together as 'no plan found' and not read 12 as a
   > hard proof."**（转引自 `E11/partials/deadlock-via-reachability.md` §4）

   `backends.proves_unsolvable` 只在 optimal rung **且**日志含
   `Completely explored state space` 时才接受 12，`dividend.json` 不记录后半个条件是否满足。
   于是表在**同一个格子里**先说「three of them FD independently **proving** an UNSAT」，
   四句之后又说「**Exit codes cannot separate a proof from a shrug (D-024)**」。
   这两句互相打架，而第一句是这一行唯一的正面证据。

   最小修法：把「proving an UNSAT」改成「reporting an UNSAT the bundled exhaustion
   independently confirms」——后半句是真的（E11 §7.6 复现了 44 状态的穷举）。

### a-7 · `pf.infinity_rows` = 1633 / 4000 — **削弱（丢了可达性限定）**

表里的句子：

> Bare `Infinity`, which is not JSON, **reaches the shared candidate stream in
> 1633 / 4000** rows and the frozen contract's validator passes it.

数字对（`partials/probe_frontier-via-bruteforce.md` §6 E11-PF-3：「合成语料里
**1633/4000** 的发射行命中」）。但同一份 partial 的**第 7 节「打不出结论的地方」**
第 6 条，是专门为这句写的：

> * **E11-PF-1 / PF-3 在当前仓库调用点是否可达，未确认**：`tools/run_all.py` 与
>   `reach.py` 里代价来自计划长度 + `setup_cost=1.0`，恒 ≥ 1。两条缺陷是**公开
>   API 上的**，`fuzzlab` 的生成器已经在踩，**端到端跑批目前踩不到**。按"宁可少报"
>   记为：真缺陷，**当前触发面限于直接调用方与 fuzz 语料**。

表用的是现在时的 "reaches the shared candidate stream"，读者会理解为
`engine-rig/artifacts/candidates.jsonl` 里现在就躺着 `Infinity`。
来源说的是：在**合成语料**上会，在仓库的端到端路径上目前不会，而且这一点**未确认**。
同一句的 `82 / 4000` 有同样的问题。

这不是数字错，是**把一个被明确限定过触发面的缺陷，写成了无限定的现状陈述**。
加七个字即可：「… in 1633 / 4000 rows **of the fuzz corpus**（the repo's own
end-to-end path keeps cost ≥ 1 and does not currently reach it）」。

### a-8 · `rig.unaudited_fields` = 64 / `rig.published_fields` = 111 — **削弱（列语义）**

表里的句子：

> Of the **111** leaf fields the six engines publish into `candidates.jsonl`,
> **64** are **asserted by no invariant**.

来源 `V10/PUBLISHED_VS_AUDITED.md` 的合计行，列头是：

```
| 引擎 | 发布字段数 | 被不变式断言 | 仅作索引/门控/聚合 | 未被审 | … |
| **合计** | **111** | **25** | **22** | **64** | … |
```

**「被不变式断言」是 25。** 64 是「未被审」列。中间那 22 个字段的定义是
「不变式只把它当索引/门控/聚合来读」——即不变式**读**它但**不断言**它。
按表自己那句话的字面（asserted by no invariant），正确的数是 **111 − 25 = 86**。

64 也是一个真数，但它对应的是另一个谓语（「未被审」）。差的这 22 个
**方向对仓库有利**——它让「无证据字段」的规模看起来小了三分之一。
两个改法都行：把数字换成 86，或把谓语换成「are not audited」并保留 64。

（同格另一处小账：「refuses all but **2**; **the one** that works is `delete-the-rule`」。
`recheck_report.json` 的 31 条 attempt 我全打开了：`n_accepted = 2`，
一条是 `delete-the-rule`（`expected: NOT-CAUGHT`），另一条是一个
`expected: ACCEPT-QUALIFIED` 的 dead-region。后者不是「骗过去了」，是**声明的预期结果**。
所以「all but 2 / the one that works」这两个数在同一句里指的不是同一类东西。
另注：`STATUS.md:218` 说的是「**25 forgeries**, 24 refused and one that works」——
仓库内部本来就有 25 与 31 两个口径，表取了 JSON 的 31，这一步是对的。）

---

## 2. 逐行边界审计（assignment b）

对每一行，我读了对应 partial **最后一节**（"Where I could not reach a conclusion" /
「打不出结论的地方」/ "Where this could not reach a verdict"）的**全部条目**，
再回来问：有没有哪一条被提升成了确定的边界。

### 行 1 `mdl_segmenter` — 无「未测写成已测」，有一处实质遗漏

`§9` 五条，逐条对照：

| §9 条目 | 表里怎么处理的 |
|---|---|
| 「My bit check is code-independent, **not doc-independent**」 | 复核格诚实地写了「re-derived from the **README's** bit table, not imported from `costs.py`」，读者能看出来源是文档。**没有提升。** 但边界格以 **Measured.** 开头，未带这条循环性。 |
| 「`recolor` is untested by reconstruction … unmeasured either way」 | 表未提；也未反向宣称 recolor 已测。**没有提升。**（"all 6939 events are re-priced" 为真：0 条 recolor 事件发生过。） |
| 「**Item 6 is not a defect claim**」（127 个膨胀轨道世界） | 表**完全没写**，且用「Geometry is exact」开头。见 a-1。**这是遗漏，不是提升。** |
| 「Whether D1/D2 should be fixed … is an adjudication call」 | 表只报 D1 的量（5.7 %、10 个世界），不下修法。**正确。** |
| 「One world in 300 shipped with `obstacles_dropped: true` … the sample is not quite the drawn distribution」 | 表未提。影响可忽略。 |

**判决：没有把未测写成已测。** 要补的是 §8.6（对象分解在 127/300 世界里是错的），
它比 §9 里任何一条都更该进这一格，因为它是**已经测出来的**边界，而表里没有。

### 行 2 `cegis_miner` — 边界未测用得**对**

`§6` 五条：

* 「**Depth.** …4+ 字面量未检；`C(|V|,4)` ≈ 635 k；**我选择不采样，因为部分扫描
  报成 pass 会声称它没有的覆盖**」→ 表逐字承接：「Minimal guards of 4+ literals …
  are **边界未测**：`C(64,4)` is ~635 k subsets per rule and a sampled sweep reported
  as a pass would claim coverage it does not have.」**这是全表最好的一处转写。**
* 「**Family coverage.** `gridworld` + Fixture A only. Nothing here generalises past
  the grid family.」→ 表：「and every world family but the grid, are **边界未测**」✓
* 「My pixel oracle is genuinely ambiguous」→ 表未提；但这一条已被
  `ADVERSARIAL-cegis.md` §6.2 彻底接管（「零分歧因此不是证据」），而表采用了
  对抗方的结论（1209 行是关于石头的**真**陈述）。**正确路由。**
* 「Whether F-1 is filed against `cegis_miner` or its callers」→ 表采用对抗方的
  可辩护形式（「the defect is that `rule_hypothesis` carries no object binding
  while `object_hypothesis` beside it does」）。**正确。**
* 「`teleport` naming … 没有承诺可证伪」→ 表未提，正确。

**判决：没有把未测写成已测；`边界未测` 的两处用法都站得住。**
唯一问题是 a-2 的 188 口径。

（表未承接、但对抗方认为「比 F-1 原文更严重」的一条：`theoria-arm/world/adapt.py`
只给第一个不报前置条件错的 track 发布权，而静止物体永不报错——「一颗尚未引爆的雷」。
不是边界问题，但如果这张表要给论文用，这条比 1209 行更该出现。）

### 行 3 `zero_space` — **这里有本次唯一一处「未测写成已测」**

表里那一句：

> {zs.unaudited} of 11 published fields are asserted by no invariant.
> **Behaviour on any family but `parityworld` and `g50t` is 边界未测.**

这句话把 `parityworld` **和 `g50t`** 一起放在了「已测」那一侧。
两份来源都明说 g50t 没有被测过：

`partials/zero_space-via-lp.md`「打不出结论的地方」第 1 条：

> * **只覆盖了 `parityworld`**。`gridworld` / `blockworld` / `hypset` / `jumpgraph` 未测——
>   电池里也不喂给 `zero_space`。**对 ARC 真实轨迹的行为，本复核没有证据。**

同一节第 4 条：

> * **不知道有没有伪律流到下游**。没有检查任何 arm 的 `candidates.jsonl` 里是否已经
>   躺着这类律 …

`ADVERSARIAL-zero_space.md`「我另外发现的」（它去查了下游，但明确停在了判定之前）：

> 我**没有**去判定这 573 条 global 律里具体哪些是伪律——那需要 ARC 世界的可达性枚举，
> **离线做不到**，也超出复核范围。**我断言的只是：证据饥饿的签名在产物里客观存在。**

**表里所有 g50t 的数字（1821 行、370/6/366、coverage 恒 k=n）都是对已发布行的
描述统计，不是任何一次正确性测量。** 把 g50t 与 parityworld 并列写在
「边界未测」的**排除项**里，等于说「在 g50t 上它的行为已经测过了」。没有。

**这一处必须改。** 最小修法：

> Behaviour on any family but `parityworld` is **边界未测** — including `g50t`
> itself: the rows quoted here are a census of what was published, not a check that
> it holds; deciding that needs reachability enumeration over the live game, which
> is offline-impossible.

**同一行还有第二处过度断言**，方向不同：

> Under the engine's declared quantifier (the observed trajectory) **the output is
> correct everywhere**.

在**声明的量词下**输出并非处处正确。`partials/zero_space-via-lp.md` 的 X-2 测出：
200 个世界的 1271 条 `cell_local` 律里，**329 条支撑集是真子集，其中落在引擎自己的
`cell_local_subspace()` 张成内的是 0 条**——`scope` 这个**已发布字段**断言了一个
它没验过的出处，而这与量词无关。对抗复核把这组数字**逐位确认**
（「1271/942/329/0 完全相同」），只推翻了原报告给的**理由**（「15 个测试全在 Fixture B」
实际是 10/15），结论保留：「**没有任何测试对 `scope` 标签的语义做断言**」。

而这张表的 solves 格恰好在推销这个分类：
「…split into **encoding-local and world-level**」。被 X-2 打的就是这条分割线，
表里一个字都没有。

**第三处，较轻**：表写「**102 laws** … stop holding」。partial 的最后一节写着
「**102 这个数是下界**，用强量词只会更多」；对抗复核另把「91 条反例起点在轨迹上」
更正为 100/102。表没写 91，但也没写「下界」。

### 行 4 `lp_potential` — 两处 `边界未测` 用得对，但**少了一处**

`§7` 六条：

| §7 条目 | 表 |
|---|---|
| 「"No linear pagoda exists" **rests on HiGHS** … 是 solver claim，不是 proof」 | **逐字承接**，且标 `边界未测`：「for the other **638** worlds … rests on HiGHS returning float infeasibility — no exact Farkas dual was produced, so that is a solver's claim and not a proof」。**全表第二好的一处转写。** |
| 「`n_pos ≤ 9` is the whole corpus … 外推不成立」 | 承接并标 `边界未测` ✓ |
| 「**Only the `jumpgraph` family.**」 | **表没写。** 第 2、3 行都为「其他世界族」标了 `边界未测`，第 4 行没有。而 `lp_potential` 同样硬编码跳棋几何（partial 共享依赖 #2：「四份同一约定的拷贝，仓库内不可检」）。**这是应标未标。** |
| 「The 27 % reachable worlds are **barely tested**」 | 表提了 811 个可达世界拿不到 heuristic（§5.4），但没提这 811 个世界上复核几乎无从下嘴。 |
| 「I did not vary `DENOMINATOR_LIMIT`」 | 未提。轻。 |
| 「**Sharpness has no baseline**」 | 未提。而 §4.5 有一个**已经测出来**的难看数字：**65.1 %** 的可用状态上 `h = 0`，且 **579 / 1550（37.4 %）** 的世界里 `h` 在**每一个**这样的状态上都是 0——「an admissible bound that never once says anything」，来源还专门加了一句「**Nobody currently measures this**」。表以 **Measured.** 开头却没有它。 |

**判决：没有把未测写成已测**（两处 `边界未测` 都精确）。
缺的是一处该标未标（family），和一处已测但没写的难看数字（sharpness）。

另外 §5.1 那条——**把 `lp_potential.run` 换成 `return None, None`，整条属性电池
以字节相同的输出通过**——表也没写。它比「14 of 26 published fields are asserted by
no invariant」强得多，而且是同一个方向的事实。

### 行 5 `fd_adapter` — (b) 意义上**全表最好的一行**

两处 `边界未测`，我逐一去查了底层，两处都对：

* 「The property battery has **never run against any Fast Downward rung** …
  `choose_tier`'s third clause forces `stub-bfs` for that call shape — a
  ***structural* fall-back, not an environmental one, so it holds on a machine that
  does have a build**」——`fuzzlab/MUTATION.md:453-464` 逐字支持
  （「So the fall-back is **structural, not environmental**」），
  `E11/partials/deadlock-via-reachability.md` §7.6 独立确认同一件事。
  **「结构性而非环境性」这个区分是这一格最值钱的东西，而且它是对的。**
* 「Of {fd.mutants} mutants one is `undetermined` — **it never ran** — and that column
  exists only because an adversarial pass found `survived` did not require the mutant
  to have executed」——`fuzzlab/out/mutation.fd_adapter.json` 实测 6 个 mutant、
  1 个 `undetermined` ✓。**主动把自己的 mutation score 拆开报，是自伤的写法，站得住。**
* 「4 of 7 published fields are asserted by no fuzz invariant（**all four are pinned by
  engine-rig unit tests**）」——括号里那句是无探针的，但 `PUBLISHED_VS_AUDITED.md:43`
  的「别处有审吗」列写着「4 个全部有 fixture 单测（`test_fd_adapter`/`test_fd_ladder`）」✓
  **有出处，只是没接探针**（见 §3）。

**唯一的伤在复核格**，即 a-6：「every rung」与「proving」。

### 行 6 `probe_frontier` — 无「未测写成已测」，但丢了三处限定

`§7` 六条：

| §7 条目 | 表 |
|---|---|
| 「`run_with_planner` / `ExecutableProbe` 的排序**没有暴力对照**：那条路要真 Fast Downward 构建」 | **逐字承接并标 `边界未测`** ✓ 连理由（needs a real FD build）都对。 |
| 「**E11-PF-1 / PF-3 在当前仓库调用点是否可达，未确认**……端到端跑批目前踩不到」 | **丢了。** 见 a-7。这一条最要紧，因为它改变 `82/4000` 与 `1633/4000` 的严重性读数。 |
| 「**`evaluate` 的正确性没有独立验证**（共享依赖 #1）。**整个第 5 节建立在它之上。** 若它错，交叉一致性会假报通过」 | **丢了**，而表把第 5 节的结果（teleport 21→18、argmax 移 16 个状态）当已测量引用。 |
| 「**"可区分世界数"只在我穷举出的状态空间里成立**：12×12、(2,3) 物体、**单**障碍」 | **丢了。** 表写「`teleport`'s **21 guards are only 18 distinguishable worlds**」无任何范围限定。（来源同时说多障碍只会让差值变小、不会消失，所以方向是安全的——但限定还是掉了。） |
| 「5.2 的 MDL 先验是我选的，仓库里没有规范先验」 | 表只说「`Hypothesis.weight` is always 1.0, so cegis's MDL prior over guards is **discarded**」——**不宣称正确答案是别的**。✓ 处理得对。 |
| 「没有跑 `engine-rig` 的 pytest 套件」 | 与本表无关。 |

**判决：没有把未测写成已测**（`边界未测` 那一处精确）。丢的是三处范围限定，
其中第二条（PF-1/PF-3 的触发面）是实质性的。

### 行 7 `deadlock_carver` — **「the whole inventory」过度取范围；且这一行没有任何 `边界未测`**

`§8「Where this could not reach a verdict」`：

* 「**`deadlock_carver` completeness is measured, not adjudicated.** 44.1 % …
  are dead for reasons no 2-atom pattern can state. That is the documented ceiling
  of h² …，**not a defect**」→ 表：「Completeness is capped by the evidence, not by a
  budget … Widening it means implementing h^m, which is a different engine.」
  **精确承接，包括「不是缺陷」这个定性。** 55.9 / 44.1 我逐位核过 ✓
  （表把来源的「and half of `ringstuck`'s」丢了，轻）。
* 「**The speed-up half of the deadlock story was not re-measured** [in this lane]
  … That is E7's audit」→ 表把 speed-up 的四个数全部从 **E2 的 `dividend.json`** 取，
  不从这条 lane 取。我把 E2 的 JSON 整个打开逐行核对：
  `far6/singleton/blind 3070→2762` ✓、`far6/singleton/lmcut 47→47` ✓、
  `far6/singleton/ipdb 18→18` ✓、`far6/indexed/lmcut 47→66` ✓、
  `ringstuck4/singleton/blind 0→0` ✓、`far6/full/lmcut` 的 `guard_refused` 全文
  含 `This configuration does not support axioms!` ✓、−10 % = 308/3070 ✓。
  **路由正确，数字位位对。**「its translator settles the instance before search」
  也不是编的——`STATUS.md:96-101` 原话「FD's translator settles the instance by
  relaxed reachability before search begins (`No relaxed solution! …`)」。
* **但**：§8 还列了一串**从未裁决**的 unsolvability 主张：
  `exam/…/p15-verdict-a2.truth.json` 的 **9** 条（5 条可暴力、4 条 2^60–2^120 不可）、
  `proxy/variants/v00{1,2,3}.json` **3** 条（需要实时游戏）、
  `cold-start-a3` 的 `a3-l2-oneway` 负控 **1** 条、
  `ablation-arm` 的 **2** 条复制品。至少 **17** 条。

  而表写的是：

  > Truth is clean — **across the whole unsolvability inventory**, **50 CONFIRMED, 0 refuted**.

  「the whole unsolvability inventory」把「全部**已裁决**的清单」说成了「全部清单」。
  来源自己在 §8 里把没裁的都列了出来，正是为了不让人这么读。
  改成「across the 50 claims this lane adjudicated」即可。

* 另外，`50` 这个数**跨了七八个生产者**（`lp_potential` U1/U2、`ic3_pdr` U3、
  `fd_adapter` U4、`probe_frontier` U7、`a0-spike` Lean U8、`cold-start-a0` U9、
  `cold-start-a2` U10、`worldgen` U11–U14），却坐在 **`deadlock_carver` 的边界格里**。
  复核格里的 `36 of 36` 才是这个引擎自己的数。有 hedge（"across the whole unsolvability
  inventory"），但一个扫表的读者会把 50 记在这一行头上。

* **这一行没有任何 `边界未测`**，而它的全部证据只来自 **4 个 sokoban 实例**。
  第 2 行为「grid 以外的世界族」标了未测，第 3 行为「parityworld 以外」标了未测，
  第 7 行对「sokoban 以外」一个字没有。`MAX_PATTERN = 2` 的效果在别的域上是什么，
  仓库里没有任何测量。**建议补一处 `边界未测`。**

### 行 8 `ic3_pdr` — **推不翻。我认真打了，没打动。**

这是表里唯一整格 `边界未测` 的一行，也是我最想找到「其实测过」的一行。逐项实测：

| 表里的断言 | 我怎么查的 | 结果 |
|---|---|---|
| 「exactly **1** certificate in the committed stream」 | 数 `payload.producer == "ic3_pdr"` | **1** ✓ |
| 「**no property module in the fuzz battery at all** — `fuzzlab/props/` covers six engines and this is not one of them」 | 列 `fuzzlab/props/`；数 `campaign.json` 的 engines | 6 个引擎，无 ic3_pdr ✓ |
| 「the campaign contains **0** rows for it」 | `count(engines[*].engine == ic3_pdr)` | **0** ✓ |
| 「none of the 500-world campaign, none of the **55** mutants … touches it」 | 六份 `mutation.<engine>.json` 求和 | 55 个 mutant、15 survived、1 undetermined，**无 `mutation.ic3_pdr.json`** ✓ |
| 「none of the **111**-field publication audit touches it」 | `PUBLISHED_VS_AUDITED.md` 合计行的六行引擎 | 无 ic3 行 ✓ |
| 「a **2**-row differential — **ACCEPT against peg4-0111, REJECT against peg4-1101**」 | `recheck_report.json` 的 matrix | 恰 2 行 ic3，verdict 与 ruleset 逐字相同 ✓ |
| 「E11 re-checked the CNF against its own successor relation over all **16** states」 | `E11/partials/deadlock-via-reachability.md` §6b | 原文「re-checked from the CNF alone against my own successor relation over all 16 states: 8 satisfying states … **closed under every jump from every satisfying state (not merely reachable ones)**」✓ |
| 「Until it runs, the paper may say the LP's gap is *covered on `0111`*, and may not say it is covered.」 | — | 这句话没有任何可推翻的成分，而且它是全表最该被抄走的一句。 |

**判决：推不翻。这一行是全表的锚。**

### 反向检查：有没有把「已测」写成「边界未测」？

五处 `边界未测`（cegis 深度+族、zs 族、lp 的 Farkas + n_pos、fd 的电池对真 FD、
pf 的 planner path、ic3 整格）我逐一去仓库里找过反证：

* cegis 4+ 字面量：无任何更深的枚举记录。cegis 的非 grid 族：partial 明说
  `hypset/jumpgraph/parityworld/blockworld` 不喂 `cegis_miner`。**确实未测。**
* zs 非 parityworld：`fuzzlab` 只喂 parityworld。**确实未测**（g50t 那半句见上，
  错在把它划到了已测一侧，不是把已测划成未测）。
* lp 的 638 条 Farkas：partial §7 明说没做 exact dual。**确实未测。**
* fd 电池对真 FD：`MUTATION.md` 与 E11 §7.6 双份确认是结构性不可达。**确实未测。**
* pf 的 planner path：partial §7 明说本机无 `.toolchain/`。**确实未测。**
* ic3 整格：上表八项。**确实未测。**

**没有一处 `边界未测` 是把已有测量说成没有的。** 这个方向我推不翻。

---

## 3. 生成器：散文里有多少数字没有探针管

`RUN_STATE.md` 写着：

> * Every cell value is **probed** out of an artifact … The prose in `ROWS`
>   contains `{fact.key}` placeholders **and no bare figures**.

**这句话是假的。** 我把 `ROWS` 里的 `{…}` 占位符掩掉之后逐格扫，实质裸数字如下
（"值对不对" 一列是我去来源核过的）：

| 行 | 格 | 裸数字 | 值对不对 |
|---|---|---|---|
| 1 mdl | fixture | `6993` frames | ✓（partial §3） |
| 1 mdl | boundary | `18` published fields | ✓（V10 表） |
| 2 cegis | fixture | `49` transitions、`9` ground、`1` lifted、`4277` transitions | ✓（partial §3 表） |
| 2 cegis | boundary | `C(64,4)`、`~635 k`、`20` published fields | ✓ |
| 3 zs | fixture | `16` features | ✓ |
| 3 zs | boundary | `6` transitions、`40` transitions、`11` published fields | 6 ✓；**`40` 来自 Fixture B，不是 g50t**（见 a-3） |
| 4 lp | fixture | `16` states | ✓ |
| 4 lp | boundary | `bound=10`、`512` states、`2×`、`26` published fields | 值 ✓；`2×` 的参照错（见 a-4） |
| 5 fd | fixture | `4` levels、`7` cold-start domains | 7 ✓ 但其中 2 个是 `a0-spike`，不是 cold-start |
| 5 fd | recheck | `three` of them | ✓（3 行 `fd_unsolvable`） |
| 5 fd | boundary | `7` published fields、**`all four are pinned`** | ✓ 但 **`four` 与 `{fd.unaudited}` 手工耦合** |
| 6 pf | fixture | `9` rules、`~550 k` evaluations | ✓ |
| 6 pf | boundary | `5` ULP、`1-bit`、`0.0`、`16` states、`1.0`、`29` fields | ✓ |
| 7 dl | boundary | `MAX_PATTERN = 2`、`2-atom`、`Theoria 1.9`、`−10 %`、**`M9's 44 → 22`** | 全 ✓（`carve.py:61` 确有 `MAX_PATTERN = 2`；44→22 在 `STATUS.md:37` 与 E11 §7.4） |
| 8 ic3 | boundary | `six` engines、`one` configuration | ✓ |
| render() | 正文 | 「It covers **six** of the eight」 | ✓ 但 `len(campaign.engines)` 本可探针化 |

**三条值得单独说：**

1. **`(all four are pinned by engine-rig unit tests)` 与 `{fd.unaudited}` 手工耦合。**
   `fd.unaudited` 今天探出 `4`，散文里写死 `four`。若 `PUBLISHED_VS_AUDITED.md`
   把 fd 的未审字段改成 5，tripwire 会响（好），但**如果作者照着新数字更新 `expect`
   而忘了改 `four`**，表就会印出「5 of 7 … (all **four** are pinned)」。
   这是表里唯一一个「数字-数词」耦合点。

2. **`{pf.partition_mismatch}` 被复用去表示 entropy mismatch。**
   `ROWS[5].boundary`：

   ```
   "{pf.partition_mismatch} partition mismatches, {pf.partition_mismatch} entropy mismatches"
   ```

   来源 §4A 是**两行不同的表格行**（「划分 = 预测表分组 | **0**」与
   「熵 = 独立公式（bits） | **0**（最大偏差 `1.11e-15`）」），今天都恰好是 0。
   **entropy mismatch 的计数没有任何探针。** 若来源那一行变成非 0，
   表会照旧印 0 而 tripwire 不响——这正是这个文件在文档里立誓要防的那件事
   （"a verdict computed correctly and then wired to nothing"）。
   加一条 `pf.entropy_mismatch` 探针即可，正则现成
   （`\| 熵 = 独立公式（bits） \| \*\*(\d+)\*\*`）。

3. **`zs.g50t_worst` 的探针语义与散文的形容词不一致**（a-3）。
   provenance 表写 `modal (…) group`，散文写 `the worst group`。
   这一处 tripwire 在「最差组变了但众数组没变」时不会响。

---

## 4. 我攻击了但没打倒的

具体写清楚攻法，否则「没打倒」不值钱。

1. **非零退出是不是真接通了。**
   我把 `engine_table.py` 复制到临时目录做了四个 mutant，再逐个以
   `tools/_tmp_*.py` 临时投放、跑完立刻删除（`ls tools/ | grep tmp` 复核为空）：
   * 把 `lp.certificates` 的 `expect` 从 `1550` 改成 `1551` → **exit 1**，
     stderr 打印了 key、artifact 的实际值、以及探针的 `where`；
   * 把同一条的正则换成一个不存在的模式 → **exit 3**；
   * 在散文里塞一个 `{lp.nonexistent_key}` → **exit 3**，
     `PROBE FAILED: table references unknown fact`；
   * 往 `ENGINE_TABLE.md` 尾部追加一行再 `--check` → **exit 1**（`is stale`），
     恢复后 `--check` 回到 0。
   四种失败模式全部命中，**1 与 3 确实分开**（D-024/D-031 的那条规矩落实了）。
   E9 自己的 `measured/negative-controls.txt` 另有五条，与我的四条独立且一致。
   **推不翻。**

2. **`--check` 会不会对当前树说谎。**
   直接跑：`118 facts verified; ENGINE_TABLE.md is current`，exit 0。
   我另外把 8 条抽样 fact 全部用自己的脚本从产物重算，**没有一条与表里印的不同**。
   **推不翻。**

3. **`zs.g50t_rows = 1821` 与 `zs.g50t_coverage_full = True`。**
   我最想打这一条，因为它是唯一一条来自实时游戏产物的数。
   自己解析 `candidates.jsonl`：1851 行总数，1821 行 `engine == zero_space`，
   逐行核 `coverage` 的分子分母，**1821/1821 全部 k == n**。
   **推不翻**（而且探针用的是 `all(...)`，不是抽样）。

4. **`rig.mutants = 55` / `rig.survivors = 15`。**
   这两条的探针有点狡猾——挂在 `mutation.cegis_miner.json` 上但 `fn` 忽略参数、
   自己去读另外六个文件。我怀疑它会漏读或重复读，就自己把六份 JSON 求和：
   cegis 8/3、fd 6/1、lp 6/1、mdl 11/4、pf 18/5、zs 6/1 → **55 / 15**，一致。
   **推不翻**（但这个探针的 `where` 字符串对读者是误导的：它写
   `fuzzlab/out/mutation.cegis_miner.json :: sum over the six …`，
   而实际会因另外五个文件缺失而抛 `FileNotFoundError` 而非 `ProbeError`——
   那会是一个未捕获的异常，退出码 1 而不是 3。小瑕疵，归到 §5。）

5. **`e5.*` 四条与 `dl.recheck_dead_regions = 18`。**
   打开 `recheck_report.json`：`green: true`、`counts.matrix_rows: 22`、
   `counts.forgeries: 31`、`forgeries.n_accepted: 2`；matrix 22 行里含 `dead` 的
   恰 **18** 行（16 open4far + 2 ringstuck），**全部 ACCEPT**，所以「green」这个词也对。
   **推不翻。**

6. **deadlock 的四个 dividend 数字。**
   我原以为最可能中招的是「47 → 47 against `lmcut`」被从别的 guard 编码里挑出来。
   把 `E2/dividend.json` 的 far6 全部 12 行打印出来逐一对照：三个「零红利」数
   全部取自 `singleton` guard、`47 → 66` 取自 `indexed`，**与表的叙述分工完全一致**
   （表确实区分了「natural guard」与「STRIPS `indexed` re-encoding」）。
   `full` guard 的 `guard_refused` 全文含 `This configuration does not support axioms!`，
   支持「`lmcut`/`ipdb` refuse the task outright」。**推不翻。**

7. **「边界未测」有没有被滥用成挡箭牌。**
   五处逐一去仓库里找反证（§2 末）。没找到。**推不翻。**

8. **表会不会对 `ic3_pdr` 过度悲观**（即把测过的说成没测）。
   查了 `fuzzlab/props/`、`campaign.json`、六份 mutation JSON、V10 的字段普查、
   `recheck_report.json`、E11 §6b。**它确实只有一个点。推不翻。**

---

## 5. 需要的修改，按优先级

**P0 — 事实错误，必须改**

1. **行 7 fixture：`{dl.candidates} theorems` → 16 theorems。**
   17 行里第 17 行是 `kind:"plan"` 的 `pruning_account`（其自身 `n_theorems: 16`）。
   改探针为 `count(producer==deadlock_carver and kind=="invariant")`，
   或把散文改成 `16 theorems and 1 pruning account in the committed candidate stream`。
   （E9 自己的 `RUN_STATE.md` 措辞是对的——「17 **rows**」——只是表里丢了这个区分。）

2. **行 3 boundary：把 `g50t` 从「已测」一侧移出。**
   现文「Behaviour on any family but `parityworld` **and `g50t`** is 边界未测」
   声称了一次从未发生的测量。两份来源都明写 g50t 上的正确性判定离线做不到。

3. **行 5 recheck：`Every rung is run against the others` → 两条 rung。**
   `p13/dividend.json` 的 `cross_check` 只有 `fd_*` 与 `stub_*` 两组，
   顶层 `search: "astar(blind())"`，satisficing 从未参加；`7` 是实例数。
   同句 `three of them FD independently **proving** an UNSAT` 改成
   `reporting an UNSAT the bundled exhaustion independently confirms`——
   那三行 `fd_exit_code` 都是 12，而本仓自己的 manifest 说 12 不得读作硬证明，
   与同格四句之后的「Exit codes cannot separate a proof from a shrug」直接冲突。

**P1 — 分母/口径，会误导**

4. **行 2 boundary：`188` 与 `affected` 二选一。**
   188 = 72 + 全部 116 个产 lifted 的世界；「受影响」的口径是 162。

5. **行 4 boundary：给 `46.6 %` / `24.0 pp` 标上 N=500，或整段改写。**
   现在 N=500 与 N=3000 的数被串成一句因果，且 `about 2×` 挂在了 29.2 % 后面
   （实为 1.6×；2× 是对 22.6 % 说的）。

6. **`rig.unaudited_fields` 那句：`64 are asserted by no invariant` → 86，
   或把谓语改成 `are not audited`。** 来源的「被不变式断言」列是 25。

7. **行 3 boundary：`the worst group` → `the modal group`，或换探针。**
   并把「one resting on 40」标明来自 Fixture B（g50t 的分母只有 5/6/7）。

8. **行 6 boundary：给 `82 / 4000` 与 `1633 / 4000` 加回触发面限定。**
   来源明写「端到端跑批目前踩不到」「触发面限于直接调用方与 fuzz 语料」，且这一点本身「未确认」。

9. **行 7 boundary：`across the whole unsolvability inventory` →
   `across the 50 claims this lane adjudicated`。** E11 §8 列出至少 17 条从未裁决的。

**P2 — 该补的边界 / 该补的探针**

10. **行 4 补一处 `边界未测`：`jumpgraph` 以外的世界族。**
    第 2、3 行都有，第 4 行没有，而 `lp_potential` 同样硬编码跳棋几何。

11. **行 7 补一处 `边界未测`：sokoban 以外。** 整行证据只有 4 个 sokoban 实例。

12. **行 1 boundary 补 §8.6：** 127/300 世界的轨道数多于世界里的对象（最坏 40 对 4），
    `masks_partition_the_foreground` 全绿。这是**已经测出来的**边界，
    而「Geometry is exact」现在读起来把它排除了。

13. **行 4 boundary 补 §4.5：** 65.1 % 的可用状态 `h = 0`，
    579/1550（37.4 %）的世界上 `h` 恒为 0，来源注明「Nobody currently measures this」。

14. **行 3 boundary 补 X-2：** 1271 条 `cell_local` 里 329 条是真子集、
    0 条落在引擎自己的编码律张成内，且无任何测试对 `scope` 的**语义**做断言——
    而这一行的 solves 格正在推销这条分割线。
    并把「102 laws」标成下界。

15. **给 `pf` 的 entropy mismatch 加一条独立探针。**
    现在它复用 `{pf.partition_mismatch}`，是这张表里唯一一个「印出来但没人验」的数字。

16. **把 `(all four are pinned by engine-rig unit tests)` 里的 `four` 拆掉**
    （改成 `all of them`），解除与 `{fd.unaudited}` 的手工耦合。

17. **`rig.mutants` / `rig.survivors` 的探针**：另外五个 `mutation.*.json` 走的是
    裸 `read_text()`，缺文件会抛 `FileNotFoundError` 而不是 `ProbeError`，
    退出码会是 1（未捕获异常）而不是约定的 3。走 `_load_json` 即可。

18. **`RUN_STATE.md` 两处自陈与交付物不符**：
    「98 facts, 19 artifacts, 6 runs」（现在是 **118** facts），
    以及「The prose in `ROWS` … contains **no bare figures**」（见 §3，至少 28 处）。

---

## 6. 复现

```bash
# 只读核对（不改仓库）
cd .worktrees/e9-engine-paper-table/engine-rig && python -m tools.engine_table --check
```

八条抽样与全部旁证是用会话临时目录里的一次性脚本重算的（未入库），
数据源全部是仓库内已落盘的产物：

* `engine-rig/artifacts/candidates.jsonl`（44 行；producer 计数、第 41 行的 kind）
* `theoria-arm/runs/20260728T015354Z-g50t-first-contact/candidates.jsonl`（1821 行 zero_space；三组分布）
* `engine-rig/runs/p13-fd-real/dividend.json`（`cross_check` 7 项、`search` 字段）
* `engine-rig/runs/20260728T072633Z-E2-fd-ladder-bench/dividend.json`（far6 全 12 行、ringstuck4、`guard_refused` 全文）
* `engine-rig/runs/20260728T141724Z-E5-cert-recheck/recheck_report.json`（22 行 matrix、31 条 forgery attempt）
* `fuzzlab/out/campaign.json` + 六份 `fuzzlab/out/mutation.*.json`
* `fuzzlab/runs/20260728T152000Z-V10-fuzz-mutation-power/PUBLISHED_VS_AUDITED.md`
* E11 的六份 partial + 两份 ADVERSARIAL（**每一份的最后一节都通读了**）
* `engine-rig/STATUS.md`、`fuzzlab/MUTATION.md`、`engine-rig/engines/deadlock_carver/carve.py:61`

生成器的四个 mutant 在临时目录构造，投放后立即删除；
`--check` 的失效测试对 `ENGINE_TABLE.md` 的追加在同一条命令里恢复。
复核前后 `git status --porcelain` 均只有一项：
`?? engine-rig/tests/test_engine_table.py`（本次复核之前就存在，非我所写）。
