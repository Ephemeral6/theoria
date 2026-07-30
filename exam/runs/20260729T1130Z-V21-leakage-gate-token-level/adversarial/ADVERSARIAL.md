# V21 · 对抗审稿报告（回收重建）

**这份报告本来不存在。** 派出去做对抗复核的 subagent 在 2026-07-29T12:00Z 前后死掉了，
只在 `adversarial/` 里留下 12 个探针脚本、零份结论。RES-3 的下一世（cycle 64，15:30Z）
把那 12 个脚本逐个重跑，原始输出存为 `PROBE_OUTPUT.txt`
（sha256 前 16 位 `28936ffec1d75c0a`，382 行），本文件是对它的裁定。

**留这一段的理由**：交接文件当时写的是「对抗审稿的报告还没回收，交付前必须读完」。
如果那句话没写下来，这一世会直接提交一份自认为完成的活，而 12 个探针里有 4 个
指着我自己的测试说它们什么也没钉住。**扇出的产出不落盘就等于没做过。**

## 探针清单

| 脚本 | 问的是什么 |
|---|---|
| `a1_continue_kills_token_check.py` | 退化子集的 `continue` 是否跳过同字段的 token 检查 |
| `a2_real_papers_instrument.py` | 四份真卷子上，每个字段实际走的是哪条分支 |
| `a3_what_the_skip_hid.py` | 那个 skip 具体藏住了什么 |
| `a4_label_sets_before_after.py` | 60% 门槛改成 `MIN_LABELLED=4` 前后的标签集差 |
| `a5_metadata_fields_coverage.py` | 卷面上有多少字段根本不在检查名单里 |
| `a6_misses.py` | 七种构造出来的泄漏，闸门放过几种 |
| `a7_floor_contamination.py` | 前一个字段的 floor 能不能压掉后一个字段的真泄漏 |
| `a8_false_positive_rate.py` | 穷举枚举下的假阳性率随 n 怎么变 |
| `a9_permutation_null.py` | 打乱标签后，闸门在真卷子上多久响一次 |
| `a10_mutation_test.py` | 变异测试：每条测试到底钉住了什么 |
| `a11_test_quality.py` | 逐条查两条可疑测试的钉合力 |
| `a12_independent_audit.py` | 用留一法独立重审一遍，不看闸门的实现 |

## 一、对抗方推翻了我自己的两条测试（最重要的一节）

### `test_a_token_on_one_item_is_an_identifier_not_a_rule` 什么也没钉住

`a11` 把那条测试的 fixture 里每个单持有者 token 的得分算了出来：**全部是 0.583**，
而容差是 **0.900**。于是**把 `len(holders) < 2` 这道守卫整个删掉，那条测试照样绿**。
它断言的是容差的结果，不是守卫的结果。`a10` 的变异 E（删掉该守卫）证实：**10 条测试 0 条抓到**。

已修：fixture 换成 11 件答 `live`、唯一答 `dead` 的那件是 `ridge` 的唯一持有者。
留一法在唯一持有者上按算术必然完美——rate = (1 + 11)/12 = **1.000**，floor = 11/12 = **0.917**，
两个门都过，**守卫是唯一挡着它的东西**。测试里把这个算术也断言了一遍，
防的是 fixture 以后再退化成同义反复。变异 E 现在被抓。

### `test_a_subset_correction_does_not_desensitise_the_token_check` 钉的是拼写

那条测试是 `assert "floor = max(" not in src`。`a11` 列了同一个回归的六种拼法，
**四种绕得过去**：`floor = floor_here = max(...)`、`floor  =  max(...)`、`floor = max (...)`、
`floor += max(0.0, floor_here - floor)`。`a10` 的变异 R 就是其中一种，是真的行为回归。

已修：源码 grep 保留（它钉那个确切拼写，代价近零），另加
`test_a_subset_floor_from_an_earlier_field_cannot_suppress_a_later_leak`——
用 `a7` 的 50 件构造做行为断言：`points` 先被打分并算出 0.950 的子集 floor，
`tags` 里的 `ridge` 在全组上预测 0.940，真 floor 是 0.500。floor 一漏出去，
0.940 就被拿去和 0.950 比，真泄漏被静默压掉。

### 三条守卫此前完全没有测试

`a10` 的变异表里有四行是 **0/10**：

| 变异 | 修前 | 修后 |
|---|---|---|
| E：删掉 `len(holders) < 2` | 0/10 | 1/17（上面那条） |
| F：`MIN_TOKEN = 1` | 0/10 | 1/17（`test_short_tokens_are_dropped_as_punctuation_noise`） |
| H：`MIN_LABELLED = 1` | 0/10 | 1/17（`test_no_label_set_is_derived_that_cannot_then_be_scored`） |
| P：token 级 floor 比较从 `>` 弱化为 `>=` | 0/10 | 1/17（`test_a_token_rate_equal_to_the_floor_is_not_a_hit`） |

P 那条值得单说：把 `>` 改成 `>=` 对现有每条测试都是不可见的，因为它们用的 token
要么明显超过 floor，要么根本过不了容差。要钉住它需要一个 rate **恰好等于** floor
而又高于容差的构造：20 件、19 答 `live`、`ridge` 落在 10 件 `live` 上，
rate = (10 + 9)/20 = 0.950 = floor，超过 0.900 容差但不该算命中。

## 二、修完第一遍之后仍然存在的一条：报告读不出「没检查」

`a2` 逐字段跑了四份真卷子，`p15-verdict-a2` 那一段是这样的：**四个标签集 × 三个字段，
十二格全是 `constant-field  token-check SKIPPED`。** 也就是说这份卷子的 metadata 检查
**一格都没打分**，17 件全绿，而绿的含义是「这里没有东西可查」。

这是对的——常量字段确实不可能预测任何东西。**但它印出来和「查过且干净」一模一样，
而那正是 V21 这张票在治的病。** 第一遍加了 `metadata_coverage()` 来报单例数，
可是**除了测试没有任何地方调用它**，`exam/artifacts/leakage.json` 里一个字都没多。
判据跑了、绿了、被当成证据用了——**同一个形状，出现在这次修复自己身上。**

已修三处：

1. `metadata_scan()` 成为唯一的遍历，`metadata_hits` / `metadata_coverage` 降为它的两个投影。
   要同时拿判决和覆盖率的调用方（`check_paper` 就是）不能再从两次可能互相矛盾的遍历里取。
2. 常量字段与缺失字段**记入 declined** 并标出 `"constant"` / `"absent"`；
   整组不可打分（不足 4 件、只有一种答案）也记入，`"field": None`。
3. `check_paper` 把它写进 `report["metadata_unscored"]`，于是 `leakage.json` 里
   每个字段要么被打分、要么带着理由出现。
   `test_a_field_that_was_never_scored_says_so_in_the_report` 守着这条。

## 三、`a6` 构造的七种泄漏，闸门放过五种

| 构造 | 闸门 | 裁定 |
|---|---|---|
| M6 整值 `points` 2-vs-3（**对照，应红**） | **RED** | 正确。`STATUS.md` 关于「整值那道网不能撤」的说法属实 |
| M7 floor 污染 | **RED** | 已修（第一节） |
| M1b / M1c `item_id` 里印答案 | GREEN | **已修**，见下 |
| M1 名单外字段 | GREEN | 设计如此，见下 |
| M2 短于 3 字符的 token | GREEN | 声明为已知限度 |
| M3 两字段合取 / XOR | GREEN | 声明为已知限度 |
| M4 列表长度（`pad` 出现两次 vs 一次） | GREEN | 声明为已知限度 |
| M5 单持有者 | GREEN | 声明为已知限度，**且不打算修** |

**`item_id` 已修。** `a5` 的普查显示 `item_id` 在每份卷子上都是逐件唯一且**不在检查名单里**。
构造一份 id 读作 `q-dead-01` 的卷子，闸门直接放行。整值分桶永远查不了这个字段——
逐件唯一意味着每个桶都是单例——**是 token 检查让它第一次变得可查的**，所以现在才加。
四份真卷子加上它之后全部仍然绿（`test_the_shipped_papers_stay_green_with_item_id_checked`），
所以这份覆盖率是白拿的。

**M5 单持有者不修，理由要写清。** 落在唯一一件上的 token，如果那件属于少数类，
留一法预测率按算术**必然是 1.000**（with 取 1，without 取 n−1）。于是「修好」M5
等于让**每一个逐件标识符**在少数类那件上开火——`level:00`、`q07`、任何唯一 tag。
这不是收紧闸门，是把它变成一个乱叫的检查，而乱叫的检查会被关掉。
`a12` 的留一法审计走的是另一条路（显式特征族 + 基线差），那才是解决这一类的正道，
不是放宽守卫。**留作独立工单，不塞进 V21。**

**M1 名单外字段是设计，不是遗漏。** `METADATA_FIELDS` 是**非题面内容**字段的白名单。
`a5` 列出的 `board` / `definition` / `state` / `prompt` / `win_requires` 等等**就是题目本身**，
题目的特征预测答案叫做「这道题可解」，不叫泄漏。`a12` 独立审计正好撞在这上面：
它报 `count:board` 以留一法 **1.000** 预测 `v11-handover-a0` 的 `truth:solvable`（基线 0.750），
又报 `token:definition=name` 以 0.900 预测 `truth:class`（基线 0.600）。
**两条都落在题面内容字段上，因此两条都不是泄漏**——那是解题的样子。
`item_id` 之所以不同，是因为它是记账字段，不是题目。

## 四、加宽网眼的代价：假阳性率被测出来了，之前没人报过

把 `derive_label_sets` 的门槛从「60% 的题」改成 `MIN_LABELLED = 4`，
买到的覆盖率是真的（`a4`：`p15-adaptation-a0` 0→3、`p15-handover-a0` 0→1、
`v11-handover-a0` 0→4、`p15-verdict-a2` 3→4），**代价此前没有量过**。

`a8` 穷举枚举了两符号字母表下所有答案向量 × 所有 token 子集：

| n | P(假阳性 \| 随机 token，全部被打分子集) | 均衡切分下 |
|---|---|---|
| 4 | 0.1429 | 0.2000（2/2） |
| 5 | 0.0667 | 0.0800（3/2） |
| 6 | 0.0323 | 0.0357（3/3） |
| 8 | 0.0079 | 0.0081（4/4） |
| 12 | 0.0020 | 0.0064（6/6） |

**而真卷子上最小的被打分组正好落在这个区间**：`v11-handover-a0` 的 `why` n=5、
`plan_len` n=6，`p15-adaptation-a0` 的 `label` / `verdict` n=6。
一个 `tags` 字段带 t 个独立 token，就有 t 次独立机会。

`a9` 用置换零假设在真卷子上直接测了这件事——打乱标签，看闸门多久响一次：

| 卷子 | 标签字段 | n | 真实命中 | P(响 \| 标签打乱) |
|---|---|---|---|---|
| `v11-handover-a0` | `solvable` | 8 | 0 | **0.117** |
| `p15-adaptation-a0` | `exact_on_heldout` | 12 | 0 | 0.013 |
| 其余 11 个字段 | — | — | 0 | 0.000 |

**裁定：门槛留在 4，但把这两个数写进 `exam/STATUS.md`。** 理由是覆盖率的价值高于
这点假阳性——「绿是因为没看」比「偶尔误报一次」贵得多，而且闸门抛 `LeakageError`
的语义本来就是「停下来让人裁定」，不是「已判定为泄漏」。
但**这个数必须跟着闸门一起公布**：以后 `v11-handover-a0` 的 `solvable` 真报一次红，
读它的人有权知道那有 11.7% 的概率是巧合，而正确的下一步是重跑 `a9_permutation_null.py`。
乘数校正（Bonferroni 或按 token 数的置换校正）留作独立工单。

## 四之二、`item_id` 上线第一件事：在我们自己的夹具里找到一处真泄漏

把 `item_id` 加进白名单之后，`exam/tests/test_core.py` 有两条测试立刻变红。
**不是误报。** `_labelled` 这个夹具从 P-15 起就把件的 id 造成
`solvable-0` / `unsolvable-1`——**答案原文印在每一件的 id 里**，
而那正是当初用来测 `points` 泄漏的那份夹具。整值分桶按构造永远看不见它
（每个 id 唯一 ⇒ 每个桶都是单例），所以它躺了一整个里程碑没人碰。

夹具已换成中性 id（`q-00`…）。**旧形状保留为
`test_the_old_labelled_fixture_was_itself_an_item_id_leak`**：
悄悄修好的夹具什么也教不了人，而这条检查开机第一件事就是抓到一个
它正是为之而加的真实实例，这件事值得留在测试里而不是留在提交信息里。

（顺带说明为什么先前的经验检查没发现：我只在**四份出厂卷子**上测了
`item_id` 会不会误报，没在测试夹具上测。四份卷子确实全绿——
是全量测试套件抓到了这个，不是我。）

## 四之三、变异表自己有一个盲点，已修

第一遍的变异 K 报 `PATCH DID NOT APPLY`，因为我把 `singletons` 改名成了 `declined`。
第二遍轮到 O：我改了 `METADATA_FIELDS` 的字面量，它也失配了。
**一条补丁失配的变异只打印一行安静的字，读起来和一行普通的表格一样无害**——
它测了零个东西，却不长得像一个洞。

`a10_mutation_test.py` 现在在表格底部把两类洞分别汇总（`STALE` / `UNPINNED`）
并据此设退出码。**判据自己也需要一个判据**，否则「变异表全绿」这句话
和这份报告里所有其他「绿了但没量对东西」是同一种绿。

## 五、变异表全文

`MUTATION_TABLE.txt`（本目录）是 `a10` 在修完之后的重跑。23 条变异 × 20 条测试，
**每一条变异都至少被一条测试抓到**。第一遍时 K 那条因为我把 `singletons` 改名成 `declined`
而变成 `PATCH DID NOT APPLY`——**一条不再适用的变异会安静地报成一行空白，
看起来和「被抓到」一样无害**，所以 K 的补丁文本已按新源码刷新，
并补了 K2–K5 覆盖这一遍新加的四处（常量字段记账、整组不可打分记账、
报告里的 coverage、`item_id` 在名单里）。

## 六、还没做完的，留给谁

| 遗留 | 性质 |
|---|---|
| M5 单持有者 / `a12` 的留一法框架 | 需要显式特征族 + 基线差，而不是放宽守卫。独立工单 |
| M3 两字段合取 | 当前检查逐字段独立，抓不到 XOR |
| M4 列表长度 | 切成 set 的 tokenise 按构造销毁重数 |
| M2 短 token | `MIN_TOKEN = 3` 之下的泄漏不可见 |
| 小 n 的乘数校正 | 上一节，数已测出，校正未做 |
