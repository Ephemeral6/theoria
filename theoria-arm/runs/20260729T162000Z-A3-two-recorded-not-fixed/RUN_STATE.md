# A3 · 上一轮「记下但没修」的那两条，修了

RES-1 cycle 30，2026-07-29。前情：`theoria-arm/runs/20260729T125500Z-A3-provenance-repair/`
的「Two things it found that are recorded but NOT fixed here」。两条原样引在下面。

## 一、`quota` 块里的 `null` 不是「不完整」，是**答错了**

> `runs/20260729T004020Z-leg01/MANIFEST.json` carries
> `quota.billed_actions_from_scorecard: null` while the recovered count of 9
> lives only in `scorecard_recovered_by`. ... The orphan flag was removed by
> this work; the number was not moved into the field whose job is to report it.

`quota()` 只看得见这一趟自己的记录，所以一个**死在关卡自己那张卡之前**的 run
拿到的是 `null`。上一轮把它读成「对帐是档案级性质、不是单份 manifest 的性质」，
所以只记不修。这一轮的判断不同：**那个 null 是错的，不只是缺的。**

卡是这个 run **自己开的**，`opaque` 里盖的是它自己的 `run_id`；salvage 只是
替它做了 close 那一次调用。API 手里**确实有这个 run 的数**。所以
`billed_actions_from_scorecard`（字段名说的是「从记分卡来的」，不是「从它自己
关的那张记分卡来的」）报 `null`，等于说「API 没有这个数」，而 API 有。

修法是填，但**绝不悄悄填**：

```json
"billed_actions_from_scorecard": [9],
"billed_actions_from_scorecard_via": {
  "closed_by": "20260729T004020Z-leg01-salvage#r-2c977116ab0e4382",
  "card_id": "2ec0e679-…",
  "why": "this run never made the closing call itself, so the count is read out
          of the ledger of the run that did. It is still this run's card and
          this run's actions -- the card carries this run's run_id in opaque."
},
"agree": true
```

`_via` 在，这一格就永远不会被读成「它自己关了卡」。附带的收获是 `agree`：
两侧的对帐从「只在档案级验证器的第 4 项里做过」变成**每份 manifest 自己就带**。

**并且没有把 salvage 那条免责词借过来。** salvage run 上「账本与 API 不一致」
是**预期**（卡是父 run 的，动作不是它花的）；父 run 上卡是自己的，两边数的是
同一件事，**不一致就是发现**——所以填进来的 `note` 是相反的措辞，并有专门的用例钉住。

## 二、指针指的是**目录**，而目录不是一个 run

> `_scorecard_recovered_elsewhere` reports the *directory name* as `slug` and
> does not partition by `run_id` ... Not triggered by anything in the archive today.

根因比「没按 run_id 分区」更早一步：`recovered_scorecards(records)` 拿到的是
**整个 ledger 文件**，而做 close 那一次调用的 run 的身份**记录本身是带着的**，
在这一步被丢掉了。`runs/a3-gate-mock/ledger.jsonl` 里就有三个 run_id。
**单 run 的 ledger 让「文件」和「run」重合，所以档案里看不出来。**

修法：新增 `recovered_scorecards_with_closer()` 保留 close 记录自己的 `run_id`，
`recovered_scorecards()` 改成在它之上实现（老调用方行为不变）。指针于是多两格：

```json
"closed_by_run_id": "r-2c977116ab0e4382",
"closed_by": "20260729T004020Z-leg01-salvage#r-2c977116ab0e4382"
```

`slug` 保留——它仍然是「你去哪个目录找」的答案，只是不再假装它是一个地址。

## 三、测试：七条，全部先验证过「不修就红」——但红的成色不一样

`tests/test_provenance_derivation.py` 追加 7 条，20 passed（arm 全量 242 passed）。
**把 `backfill.py` 换回修改前的版本，七条全红**（实测，不是推理）。

**订正上一条记录**：cycle 30 写的是「六条全红」，这话没错，但它藏了一件事，
cycle 31 复跑负对照时把失败原因逐条分了类：

| 红的原因 | 条数 |
|---|---|
| `AttributeError: 无 _quota_with_recovered` | 4 |
| `AttributeError: 无 recovered_scorecards_with_closer` | 1 |
| `KeyError: 'closed_by_run_id'`（**行为性**的红） | 1 |

也就是说六条里只有一条是因为**行为**不对而红，另外五条是因为**符号不存在**而红。
符号性的红对新函数是正常的，但它证不了一件要紧的事：**函数被接进 `build()` 了没有。**
把第 579 行的调用点删掉、函数原样留着，那六条**全绿**——
一个存在、正确、被测过、却从没被调用过的修复，长得和真修复一模一样。

这正是 A16 要在花钱路径上堵的那个形状（闸写好了、没人调）。所以本轮补第七条：

| 用例 | 钉的是什么 |
|---|---|
| `test_the_quota_fill_is_wired_into_build_not_merely_available` | 走公开路径 `build()`：临时档案里造一个死掉的 leg + 一个另建目录的 salvage，断言 manifest 的 quota 块真的被填上 |

实测：删掉第 579 行的调用点，只有这一条红，报的是
`build() left the quota block reporting None -- the helper is not on the path that writes manifests`；
其余六条照绿。**这一条是这次修复唯一的接线证据。**

夹具里有一处值得记：scorecard 的 open 在真 ledger 里记的是 `env_meta` 而不是
`env_step`（`runs/20260729T004020Z-leg01/ledger.jsonl` 实查），第一版夹具照 `env_step` 写，
于是 open 被算成一次动作、`agree` 变成 false。夹具照着真账本改了——
**夹具写错会把「修好了」测成「修坏了」，这次是反向，下次不一定。**

### 原六条

| 用例 | 钉的是什么 |
|---|---|
| `test_the_closing_run_is_kept_not_just_the_file_it_was_logged_in` | close 记录的 `run_id` 不许被丢；且老 reader 行为不变 |
| `test_a_pointer_into_a_multi_run_ledger_names_the_run` | **档案里没有的那个缺陷，造出来**：三个 run 共一份 ledger，只有第二个关了死掉那个 run 的卡 |
| `test_a_recovered_count_lands_in_the_quota_block_not_only_in_the_pointer` | 数落进该报它的字段，且必须说出是从谁的账本里读的 |
| `test_a_recovered_count_that_disagrees_is_a_finding_here` | salvage 的免责词不许被借用 |
| `test_a_run_that_closed_its_own_card_is_left_alone` | **阴性对照**：自己关了卡的 run 不许被覆写 |
| `test_no_pointer_and_no_count_leave_the_null_alone` | 没有可填的东西时，null 保持 null（不许编） |

第二条值得单说：上一轮的记录写着「今天的档案里不触发」，所以**这条缺陷没有
被任何真实数据证明过**。不造夹具就修，等于修一个没人见过的东西——
夹具是这条修复唯一的证据。

## 四、档案重新导出，以及它自己的检验

`python -m armtools.backfill --all`：3 份 manifest 变化。

* `20260729T004020Z-leg01` —— quota 块 `null → [9]` + `_via` + `agree: true`，指针加两格；
* `20260728T012311Z-g50t-first-contact-aborted` / `…014402Z-…-aborted` —— **只有指针加两格**。
  这两份是 `archive.py` 写的形状，**根本没有 `quota` 块**，所以第一条修复对它们不适用；
  记在这里，免得后人看见「三份变了、只有一份 quota 动了」以为漏改。

验收：

* `python -m pytest`（arm 全量）→ **242 passed**（cycle 31 补第七条后；cycle 30 时为 241）；
* `python verify.py` → **exit 0**（三段：suite / 一次离线真跑 / 产物自检）；
* `python -m armtools.verify_provenance` → **9/9 PASS**，其中两条正对着本轮：
  「billed actions reconcile: ledgers vs closed scorecards」账本 32 = 6 张卡 32，
  以及「re-deriving every manifest reproduces it byte for byte」12 份全部字节稳定。
* cycle 31 复跑 `python -m armtools.backfill --all` → **零新增改动**（三份之外无变化），
  即重新导出是幂等的，不是每跑一次就换一次样。

零 API、零美元、封存堆零接触（sealing 检查全清）。

## 五、这份记录跨了两条命

工作在 cycle 30 做完，但那个会话在提交之前就死了——磁盘上留下的是改好的代码、
写好的测试、写好的这份 RUN_STATE，**和一个没有 MANIFEST.json 的 runs/ 目录**。
cycle 31 接起来时干的是：复跑全部验收（不采信上一世的数字，全部重测）、
把负对照的成色查清楚并补上第七条、补 MANIFEST.json、然后才提交。

留给后人的一句：**「写完但没提交」和「没写」在 git 里看起来一样，在磁盘上不一样。**
接续的第一步是看工作区，不是看 log。

## 六、A3 本身仍未完

本轮修的是上一轮的欠账，不是 A3 的主线。A3 仍卡在：**在线 leg 的
`$4.00 unpriced` 占位（bus seq 7418）等监控裁**。那一条动的是钱，不自决。
