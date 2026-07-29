# 领地：实验臂（theoria-arm / ablation-arm / baseline-arms / cold-start-a0,a2,a3 / a0-spike）

普查员：RES-3 派出。工作副本 `.worktrees/v11-negative-control-census/`。
未修任何缺陷；未跑任何联网/花钱的入口。

| 领地 | 入口 | 能红 | 有负控 | 退出码诚实 | 证据 |
|---|---|---|---|---|---|
| theoria-arm | `harness/run.py`（活体臂主 runner，`python -m harness.run`） | 否（读码） | 否（读码） | 否（读码） | `theoria-arm/harness/run.py:211` — `main()` 恒 `return 0`；无任何非零路径。**未跑：会花钱/联网** |
| theoria-arm | `armtools/archive.py`（收工闸：对账 + 约束 8 + 成本双算 + 封存检查） | 否（读码） | 部分（读码） | 否（读码） | `theoria-arm/armtools/archive.py:412-419` — `main()` 恒 `return 0`。它**算得出**红：`constraint_8()['holds']`（:297）、`reconcile()` 的 `"MISMATCH"`（:78）、`sealing()` 的封存命中（:216-246）——全部只写进 MANIFEST.json，不影响退出码。负控只覆盖**另一份实现**：`tests/test_arm.py:137` / `:145` 打的是 `inner/surprise.py::Register.audit`，不是 `archive.constraint_8` |
| theoria-arm | `armtools/preflight.py` | 是（读码） | 否（读码） | 是（读码） | `theoria-arm/armtools/preflight.py:88` — `return 0 if out.get("reset_status") == 200 else 1`。**未跑：联网** |
| theoria-arm | `armtools/salvage.py` / `armtools/timeline.py` | 否（读码） | 否 | 否（读码） | `salvage.py:184`、`timeline.py:231` 恒 `return 0`（是报告工具，不是闸；列此以免被当成闸） |
| theoria-arm | `pytest`（`tests/test_arm.py`，51 项，纯离线） | 是（实测） | 是（读码） | 是（实测） | 实测 `cd theoria-arm && python -m pytest -q` → 51 passed，EXIT=0。负控：`test_arm.py:31`（`pytest.raises(arc.ShortIdRefused)`）、`:137`（脏账本必须判违约束 8）、`:145`（无意外的 model_call 必须判违规） |
| ablation-arm | `verify.sh` → `verify.py`（完工闸） | 是（实测走绿；红路径读码 `verify.py:361`） | **是**（读码，本次普查最强的一处） | 是（读码 + 实测绿） | 实测 `python ablation-arm/verify.py` → `GREEN`，EXIT=0，五个 stage 全 ok。负控：`ablation-arm/tests/test_verify.py:54-70` 用 4 组参数篡改 `run_all.json` 断言指定断言必须变红；`:73` 断言"字段缺失不得被读成闸门想要的值" |
| ablation-arm | `build_theory.py --check`（生成物 vs 上游重切） | 是（读码 `build_theory.py:340`） | **是**（读码） | 是（读码） | 负控：`tests/test_build_and_determinism.py:28`（手改一行必须被抓）、`:48`（放回 `[status: proven]` 必须**两条通道**都响：字节 diff + parser） |
| ablation-arm | `run_arm.py`（预注册像素数 + 上游只读钉） | 是（读码 `run_arm.py:714`） | **是**（读码） | 是（读码） | 负控：`tests/test_loop.py:84` 换成错的 trace → `pre_registered.holds is False`；`tests/test_readonly.py:72` `test_the_pin_can_see_a_change_at_all` |
| ablation-arm | `run_arm.py --twice`（两轮复跑比对） | 是（读码 `run_arm.py:678`） | 部分（读码） | 是（读码） | 无"注入不确定性必须变红"的测试；`tests/test_build_and_determinism.py:103` 断言两份 ledger 原始字节**必须不同**（否则测试自称无意义），算半个演示 |
| ablation-arm | `run_exhibits.py` | **否（实测）** | 是（读码，双向钉住） | **否（实测，且是刻意的）** | 见下节专查 |
| baseline-arms | `harness/audit_cells.py`（逐格账本审计 + 封存检查） | 是（读码 `audit_cells.py:236` / `:280`） | 部分（读码） | 是（实测走绿 + 读码） | 实测 `python -m harness.audit_cells --json` → EXIT=0，12 格、`sealed_hits: []`。负控只覆盖 `reached_api()` 分类（`tests/test_audit_pool.py:218-235`）；没有任何测试伪造一份对不上账的 ledger 逼它红 |
| baseline-arms | `harness/audit_pool.py`（花费池对账） | 是（读码 `audit_pool.py:284`） | **是**（读码） | 是（读码） | 负控齐全：`tests/test_audit_pool.py:61`（少记动作被抓）、`:76`（多记被抓）、`:101`（美元对不上被抓）、`:129`（预留未关被抓） |
| baseline-arms | `harness/merge_ledger.py --check` | 是（读码 `merge_ledger.py:91`） | 否（读码） | 是（读码） | `return 1 if bad else 0`，`bad` = 不可解析行数。无负控 |
| baseline-arms | `harness/run_campaign.py --gate-only`（战役闸） | 是（读码 `run_campaign.py:487`） | 部分（读码） | 是（读码，红=退出码 3） | `tests/test_spend_binding.py:272` 只断言"格上限就是闸的数字，不是新数字"，不是逼闸变红 |
| baseline-arms | `harness/transport_ab.py::assert_not_frozen`（跨轨冻结闸） | 是（读码 `transport_ab.py:72` `raise SystemExit(str)` → 退出 1） | 否（读码） | 是（读码） | **未跑：会花钱/联网**（`run_cell` 直接 `bare_cc.play`） |
| baseline-arms | `harness/campaign.py` / `run_campaign.py`（活体战役） | 是（读码，拒跑路径 `return 2`） | 否 | 是（读码） | **未跑：会花钱/联网** |
| baseline-arms | `pytest`（75 项，全部用 `tmp_path` 私有花费池） | 是（实测） | **是**（读码） | 是（实测） | 实测 75 passed，EXIT=0。`tests/conftest.py` 明确不碰真实 `proxy/var/spend_gate.jsonl` |
| cold-start-a0 | `run_all.py`（九步 + schema 校验） | 是（实测走绿；红路径读码 `run_all.py:97`） | **是**（读码） | 是（读码 + 实测绿） | 实测 `python run_all.py` → `all steps green`，EXIT=0。负控：`tests/test_a0.py:251` `test_mutants_are_caught`，四种突变（删门规则/删按钮规则/破传送/删门对象）必须被 replay 层抓成 `render_mismatch` / `unowned_pixel`，注释写着"绿只有在红可达时才有意义" |
| cold-start-a0 | `certify/score_vs_truth.py`（M6 对裁判打分） | **否（读码）** | 否 | **否（读码）** | `cold-start-a0/certify/score_vs_truth.py:169` — `main()` 恒 `return 0`。准确率再低也不会红。（不在 `run_all.py` 的步骤表里） |
| cold-start-a0 | `certify/fd_conformance.py` | 是（读码 `:211` `:225`；缺 FD 时 `sys.exit(12)`） | 否（读码） | 是（读码） | — |
| cold-start-a0 | `pytest`（56 项） | 是（实测） | **是**（读码） | 是（实测） | 56 passed，EXIT=0 |
| cold-start-a2 | `run_all.py`（13 步 + schema 校验） | 是（实测走绿；红路径读码 `run_all.py:105`） | 否（读码） | 是（读码 + 实测绿） | 实测 EXIT=0，全绿。每个子步骤的 `main()` 退出码都诚实（`certify_a2.py:153`、`plan.py:151`、`exhibit.py:172`、`refute.py:120`、`locate.py:208`、`repair.py:270`、`ledger.py:215` 全是 `return 0 if <green> else 1`）。但**没有**任何"故意坏掉的 manual/trace 必须让某一步变红"的可执行负控 |
| cold-start-a2 | `tools/verify_readonly.py`（上游树只读） | 是（读码 `:79`） | 否（读码） | 是（读码） | — |
| cold-start-a2 | `pytest`（44 项） | 是（实测） | 部分（读码） | 是（实测） | 44 passed，EXIT=0 |
| cold-start-a3 | `run_all.py`（七段，含第 5 段负控） | **否（实测）** | 是（负控本身存在） | **否（实测）** | 见下节点名。`cold-start-a3/run_all.py:123` — `main()` 恒 `return 0` |
| cold-start-a3 | `a3pipeline/negctl.py`（**两组负控本体**） | 是（读码 `negctl.py:153`） | **是（它就是负控）** | 是（读码） | 实测 `python -m a3pipeline.negctl` → 两组"世界被改过一处机制"的臂都 `caught=True outcome=replay_mismatch`，EXIT=0。`negctl.py:1-45` 说明为什么两组不是同一个测试 |
| cold-start-a3 | `tools/verify_readonly.py` | 是（读码 `:89`） | 否（读码） | 是（读码） | — |
| cold-start-a3 | `pytest`（47 项） | 是（实测） | **是**（读码） | 是（实测） | 47 passed。`tests/test_transfer.py:211` 断言两组负控都被抓且都没宣称胜利；`tests/test_world.py:101` `test_the_shipped_traces_are_byte_stable`（唯一的产物漂移闸，见下） |
| a0-spike | `pipeline/run_a0.py` | 是（读码 `run_a0.py:262`） | 是（读码） | 是（读码） | `return 0 if ok else 1`，`ok` 综合 grading/replay_exact/held_out/lean。负控：`tests/test_a0.py:203`、`:240`（生成器必须拒绝编不出的东西）、`:382`/`:415`/`:428`（注入一处世界改动，依赖追踪必须抓到并定位） |
| a0-spike | `runs/20260728T040057Z-c2/make_manifest.py --verify`（MANIFEST 摘要 vs git index） | **是（实测）** | 是（实测演示 + 文档记载曾真抓到 7/19） | 是（实测） | 实测原样 → `19 files; 0 mismatched`，EXIT=0；我把一条 sha256 改成全 0 后 → `MISMATCH ... 19 files; 1 mismatched`，EXIT=1，随后还原。**这是这些领地里唯一一道"提交的产物字节 vs 仓库存的字节"的闸** |
| a0-spike | `probes/semantics_probe.py` | 是（读码 `:467`；未知事件 `raise SystemExit`，`:97`） | 部分（读码） | 是（读码） | — |
| a0-spike | `pytest`（44 项） | 是（实测） | 是（读码） | 是（实测） | 44 passed，EXIT=0 |

## 专查：run_exhibits.py 证伪却 exit 0

**线索属实，且是写进文档的刻意设计。**

定位：
* `ablation-arm/run_exhibits.py:57` — `main()` 在打印完 `not holding: ...` 之后无条件 `return 0`。
  `--json` 分支 `:46` 同样恒 `return 0`。函数里不存在任何非零返回路径。
* 理由写在 `ablation-arm/run_exhibits.py:8-13` 的 docstring 里，原话：
  "Exit status is **0 even when an exhibit does not hold**, and that is deliberate. …
  a falsifier that turns the build red is a falsifier nobody will ever report."
* `ablation-arm/tests/test_exhibits.py:145` `test_a_falsifier_is_a_result_and_not_a_red_build`
  把这条行为**钉住**：`assert run_exhibits.main([]) == 0`。

实测：

```
$ python ablation-arm/run_exhibits.py
E1   holds=True   (i) small-space unsolvable -- exhaustive search is feasible
E2   holds=True   (iii) the specificity failure -- `unsolvable` on a solvable level
E3   holds=False  the adversarial-review control, not a verdict class

all hold: False
not holding: E3 -- ... a pre-registered falsifier is a result, not a red build
EXIT=0
```

它还是完工闸 `verify.py` 的第五个 stage（`ablation-arm/verify.py:71`），
所以在 `verify.py` 的 stage 表里 `run_exhibits` 永远显示 `ok`：

```
== stages
  build_theory --check   ok
  pytest                 ok
  run_arm                ok
  run_arm --twice        ok
  run_exhibits           ok
GREEN   (EXIT=0)
```

**但要说公道话，这个洞比线索听上去小，有两道旁路把它堵了一半：**

1. E1/E2 不是靠退出码守的。它们喂进 `verify.py` 的断言 `P-5(correct)` 和 `P-6`
   （`verify.py:132`、`:143`），任一被证伪，闸整个变红（`verify.py:361` `return 1`）。
   真正"证伪却 exit 0"只对 **E3** 成立。
2. E3 被**双向**钉在 pytest 里：`tests/test_exhibits.py:96` 断言
   `constructible is False and holds is False`；`:102` 的断言信息写着，如果哪天
   D-A2-006 的 workaround 又起作用了，"重建 E3 并重写这个测试，而不是放宽它"。
   所以 E3 的状态**翻转**（无论朝哪个方向）都会让 pytest 红 → verify 红。
   逃出监视的只有一种情形：E3 保持"不成立"，而不成立的**原因**变了。

## 专查：产物漂移有没有闸门会红

**总答：几乎没有。七个领地里只有三道半，而且没有一道覆盖本臂的主产物集。**

我做了一次决定性的实测：在这份**干净的** worktree 副本里，只跑各臂自己的
离线 runner，然后看 `git status`。

* `cold-start-a0`：`python run_all.py` → `all steps green`，EXIT=0，
  但留下 3 个已跟踪文件被改：`artifacts/unsolvable_report.json`、
  `theory/generated/theory.md`、`theory/generated_no_button/theory.md`。
* `cold-start-a2`：`python run_all.py` → `all steps green`，EXIT=0，
  留下 12 个已跟踪文件被改。
* `cold-start-a3`：`run_all.main()` → EXIT=0，留下 14 个已跟踪文件被改。
* 三个臂**改完之后再跑 pytest，全部依旧全绿**（a0 56 passed / a2 44 passed /
  a3 47 passed，EXIT 均为 0）。

漂移分两种，必须分开说，否则会夸大：

* **环境性**（不算缺陷，但也说明字节复现从一开始就做不到）：
  `loop_ledger.json`、`upstream_pin.json` 里嵌了绝对路径；
  `ablation-arm/artifacts/*` 的全部 10 处改动都只是
  `"artifacts\\a0-base\\theory.py"` → `"ablation-arm\\artifacts\\a0-base\\theory.py"`
  这种 cwd 相对路径差和 ledger 的 `ts`。
* **真·代码与产物不一致**：`cold-start-a0/a2/a3` 三个臂的
  `theory/generated*/theory.md` 都长出了一整节 "How a Turn Works"（约 +8 行）——
  提交在库里的那份是**旧生成器**的输出，当前生成器已经不这么写了。
  `cold-start-a3/artifacts/arm_l2_transfer.json` 甚至把这件事记了下来：
  `"theory.md": 4733` → `5380`。**没有任何闸门读这个数字并和提交值比较。**

逐领地一句话：

* **theoria-arm — 没有。** `armtools/archive.py` 写的 MANIFEST 里 `files` 只是**文件名列表**，
  连 `sha256` 字段都不带（`archive.py:392-395`）；`_bootstrap.upstream_pin()` 确实算了
  上游 sha256 并写进 manifest，但**没有任何代码把它和后来的实际字节比一次**。
* **ablation-arm — 有半道，且是七个领地里最像样的一道。**
  `build_theory.py --check` 会把 `theory/*.dsl` 重切一遍和磁盘逐字节 diff，
  红了退 1，而且有两个负控演示它抓得住手改和放回证明标记。
  但它只管 `theory/`：`artifacts/run_all.json`、`verify.json`、`episode.jsonl`、
  `run_report.json` **没有任何比对**——`run_arm.py` 直接覆盖写，
  `--twice` 比的是**两次新跑之间**，不是新跑 vs 提交值。
* **baseline-arms — 没有。** `fetch_schema_traces.py` 会把 sha256 写进 MANIFEST
  （`:227`、`:304`），但仓库里没有任何东西回头校验它。活体战役的产物本来就不可复现，
  这一格在这个臂上大概也不该有——但那就意味着"确定性是要求"在这里没有可执行形式。
* **cold-start-a0 — 没有。** `tests/test_a0.py:83` 的
  `test_explorer_is_reproducible_and_covers_the_mechanisms` 只在**同一进程内**跑两遍探索比对，
  完全不看磁盘上提交的 `raw_trace.jsonl`。
* **cold-start-a2 — 没有。** `tests/test_a2.py:372` 只断言 `upstream_pin.json` 的
  `missing == []` 且每个 sha256 非空——**从不比对具体值**。
* **cold-start-a3 — 有一道，但只盖住 4 个文件。**
  `tests/test_world.py:101` `test_the_shipped_traces_are_byte_stable`：
  先对 `artifacts/*_sweep.jsonl` 和 `*_solved.jsonl` 取 sha256，
  调 `ground_truth.build()` 重生成，再逐一比对。这是**真正意义上的漂移闸**。
  但 `artifacts/` 下另外约 40 个文件（含 `arm_*.json`、`bill_*.json`、
  `engines_report_*.json`、`theory/generated*/`）一个都没盖到，
  上面那次实测里被改的 14 个文件正是它盖不到的那批。
* **a0-spike — 有一道，最强，但是孤立的。**
  `runs/20260728T040057Z-c2/make_manifest.py --verify` 把 MANIFEST 里 19 条 sha256
  和 **git index 里的 blob**（`git show :<path>`）逐条比。我实测它会红（改一条 → EXIT=1）。
  它比其他所有闸都强，因为它比的是"一个新 clone 会收到的字节"，
  而不是"我这台机器工作区里的字节"——docstring `:63-75` 记着它当年正是这样抓到
  `core.autocrlf` 造成的 7/19 条不匹配。
  代价：它**不在任何 runner、任何 pytest、任何 CI 路径上**，只是某一次 run 目录里的一个手动脚本，
  而且只管那一次 run 列出的 19 个文件。

**结论：** 除了 `ablation-arm/theory/`（生成物 vs 上游重切）、
`cold-start-a3` 的 4 个 trace 文件、和 a0-spike 那 19 个手动核验的文件，
"确定性是要求不是可选" 在这些领地里**没有可执行形式**。
主产物集（`artifacts/**` 的绝大多数、所有 `theory/generated*/`、
所有 `MANIFEST.json`）复跑后哈希变了，不会有任何闸门报红。

## 点名：没有负控的闸门

按"能红但从没人演示过它红"排序，最上面的最该补：

1. **`theoria-arm/armtools/archive.py`** —— 收工闸，四项义务全在这里算
   （对账 / 约束 8 / 成本双算 / 封存）。它连"能红"都不算（见下节），
   但即便只看它算出的 `holds` 布尔值，也没有任何测试伪造一份违规 ledger
   逼 `archive.constraint_8` 判 False。`tests/test_arm.py:137` 打的是
   `inner/surprise.py::Register.audit` —— **同一条约束的第二份实现**。
   两份实现，一份有负控，另一份是真正写进 MANIFEST 的那份。
2. **`baseline-arms/harness/audit_cells.py`** —— 这是唯一一道会看
   "封存堆的 game id 有没有出现在账本里"的闸（`audit_cells.py:222-233`），
   而没有任何测试往账本里塞一个封存 id 看它是不是真的红。
   隔壁 `audit_pool.py` 的四项负控（少记/多记/钱对不上/预留未关）做得很齐，
   对比之下这一处的空缺更显眼。
3. **`cold-start-a2/run_all.py` 的 13 个子步骤** —— 每一步的退出码都诚实，
   但没有一步有"故意坏掉的输入必须让它红"的负控。
   对照组就在隔壁：`cold-start-a0` 有 `test_mutants_are_caught`（四种突变），
   `cold-start-a3` 有 `negctl.py`（两个被改过机制的世界）。A2 两样都没有。
4. **`ablation-arm/run_arm.py --twice`** —— 不确定性从没被注入过一次。
5. **`cold-start-a2/tools/verify_readonly.py` 和 `cold-start-a3/tools/verify_readonly.py`**
   —— 上游只读钉，都没有"故意写一个字节进上游树"的演示。
   对照：`ablation-arm/tests/test_readonly.py:72`
   `test_the_pin_can_see_a_change_at_all` 做了，而且就是这么做的。
6. `baseline-arms/harness/merge_ledger.py --check`、
   `baseline-arms/harness/transport_ab.py::assert_not_frozen`、
   `cold-start-a0/certify/fd_conformance.py`、
   `baseline-arms/harness/run_campaign.py --gate-only`。

## 点名：退出码撒谎的闸门

1. **`cold-start-a3/run_all.py`（`:123`）—— 本次最严重的一处，实测。**
   它的第 5 段就是这个仓库里最好的负控（两个被改过一处机制的世界），
   打印 `all caught: X | none claimed a win: Y`，然后 `main()` 无条件 `return 0`。
   `negctl.py:153` 自己的 `main()` 是诚实的（`return 0 if all_caught and none_claimed_a_win else 1`），
   但 `run_all.py:91` 调的是 `negctl.run_all()`（库函数），不是 `negctl.main()`。
   实测演示：我在临时脚本里把 `negctl.run_all` 打桩成
   `all_caught=False, claimed_a_win=True`，再调 `run_all.main()` ——
   打印照常、表照常生成、`run_all.main() returned: 0`、`EXIT=0`。
   第 6 段的 `score_mod.run_all()`（对裁判的准确率）和第 7 段的账单同样只打印不判决。
   幸而 `tests/test_transfer.py:211` 读 `artifacts/negative_controls.json` 会红——
   **但那要求有人去跑 pytest，而不是跑那个名字叫 `run_all` 的东西。**
2. **`theoria-arm/armtools/archive.py`（`:412-419`）—— 实测未跑，读码确凿。**
   `reconcile()` 会产出字符串 `"MISMATCH"`、`constraint_8()` 会产出 `holds: False`、
   `sealing()` 会产出封存命中——三者都只落进 MANIFEST.json，`main()` 恒 `return 0`。
   活体臂的收工闸，四项义务，零个非零退出码。
3. **`theoria-arm/harness/run.py`（`:211`）** —— 活体 runner 恒 `return 0`。
   这一条和上一条合起来意味着：theoria-arm 里除了 `preflight.py` 和 pytest，
   **没有任何入口能以非零码结束**。
4. **`ablation-arm/run_exhibits.py`（`:57`）** —— 见专查。
   列在这里是因为它符合"报告证伪却退 0"的形状，
   但它是**唯一一处把理由写下来、并用测试钉住这个选择**的，
   而且 E3 的翻转仍会被 pytest 抓住。性质和上面三条不同。
5. **`cold-start-a0/certify/score_vs_truth.py`（`:169`）** ——
   M6 对裁判打分，`main()` 恒 `return 0`，准确率再低也不红。
   （它被刻意排除在 `run_all.py` 之外，理由是不让默认回路看见答案，
   这个理由成立；但它自己作为一个可调用入口，退出码是无意义的。）
6. `theoria-arm/armtools/salvage.py:184`、`armtools/timeline.py:231`、
   `cold-start-a0/pipeline/engines_stage.py:390` —— 恒 0。
   这三个更像报告工具而非闸，列出只为免得被误当成闸。

## 我不确定的

1. **`baseline-arms` 的活体入口我一行都没跑。**
   `campaign.py` / `run_campaign.py` / `transport_ab.py` / `probe_api.py` /
   `probe_action_variants.py` / `fetch_schema_traces.py` / `bare_cc.py` 都会
   `urllib.request` 打 `https://three.arcprize.org`（`arc_client.py:88`）并花钱。
   它们的"能红/退出码"全部是读码结论。`theoria-arm/harness/run.py`
   和 `armtools/preflight.py` 同理。
2. **`ablation-arm/run_arm.py --twice` 的"部分负控"是我的判断，可能偏宽。**
   `test_the_ledger_differs_only_in_its_wall_clock` 断言两份 ledger 原始字节必须不同，
   我把它算作"比较器确实看得见差异"的半个演示。严格说它不是对
   `determinism()` 这个函数的负控。
3. **我没有为每一道闸都尝试实际逼红。** 只对
   `a0-spike/.../make_manifest.py --verify`（改摘要）和
   `cold-start-a3/run_all.py`（打桩负控）做了主动的逼红实验。
   其余"能红"列的 `读码` 项，我读的是返回语句本身，没有构造坏输入。
4. **cold-start-a0 / cold-start-a2 属于 theory-compiler 轨。**
   CLAUDE.md 写着 `/cold-start-a0/` 对 engine-rig 轨"off limits"。
   本次任务点名要求普查它们，我只在一次性 worktree 副本里**读代码 + 跑离线 runner 和
   pytest**，没有修改任何东西、没有向主工作树写入。若这仍越界，请以纪律为准而非以本报告为准。
5. **`theory/generated*/theory.md` 那一节 "How a Turn Works" 的多出**
   我判定为"提交的是旧生成器输出"。也可能是我这份 worktree 的
   `theory-compiler` 状态比这些臂上次生成时新——两种解释在"没有闸门会因此报红"
   这个结论上是一样的，但归因不同，我没有去查 `theory-compiler` 的提交历史来分辨。
6. **`ablation-arm/artifacts/**` 的 10 处改动我判定为纯路径 + `ts`**，
   是抽样看了 `a0-base/run_report.json` 和 diff 统计得出的，没有逐个文件核对。
