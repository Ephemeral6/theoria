# 领地：worldgen / fuzzlab

普查员 V-11，2026-07-28，worktree `.worktrees/v11-negative-control-census/`。
只读 + 在该 worktree 内实跑。所有「实测」都是本次跑出来的退出码。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据 |
|---|---|---|---|---|
| `worldgen/verify.py` | 是（读码） | 否（实测） | 部分（实测） | 本次实跑 `python -m worldgen.verify` → 打印 `green`，**退出码 0**，同时两道 QC 子闸各自返回非零（`QC.json` `family_verdict.pass=false`，`QC_MUTANTS.json` `mutant_verdict.pass=false`）。`verify.py:40-49` 把两道 QC 都标 `gating=False`，红只进 `notes` 不进 `failures`。没有任何测试演示过 `verify.py` 自己会红。 |
| `worldgen/build.py --check`（出厂闸 `gate_failures`） | 是（读码） | 是（读码） | 是（读码） | `build.py:200-228` 五道闸 + `:321-326` `BUILD GATE FAILED` → `return 1`。负控在 `worldgen/tests/test_build_gate.py:48-63`：合成 manifest 逐条违反每一道闸并断言必须被报出，且 `:70-80` 再断言真 `INDEX.json` 的 key 名与合成的一致（防「闸挂在真 manifest 从不发出的 key 上」）。 |
| `worldgen/build.py` 的 determinism 闸 `check_determinism` | 是（读码） | **否**（读码） | 是（读码） | `build.py:231-286` 起子进程换 `PYTHONHASHSEED` 重建再逐字节 diff，`:343-350` `NOT DETERMINISTIC` → `return 1`。但**没有任何测试故意改一个字节去证明它会红**。`worldgen/tests/test_determinism.py:57` 是 `_trace_bytes(id) == _trace_bytes(id)`（同进程），并在 docstring 里明说自己是「strictly weaker version」。425 个测试里零个提到 `check_determinism`。 |
| `worldgen/mutate.py` 的 `mutation_gate_failures`（MUTATION GATE） | 是（读码） | 部分（读码） | 是（读码） | `mutate.py:1375-1406`，`build.py:334-341` / `mutate.py:1453-1456` → `return 1`。**家族声明这一半有真负控**：`tests/test_mutate.py:527-548` 构造一个故意贴错标签的 `Edit`（把 `change_guard` 谎称成 `reversible_to_irreversible`）并断言 `check_family` 必须报问题。**可解性声明那一半没有负控**（`claimed != measured` 分支无人演示）。 |
| `worldgen/qc/run_qc.py`（三世界 QC 闸） | 是（实测） | 否（读码） | 是（实测） | 本次实跑：`t2-lock-fragile` 抛 `NoSeparatingGuard`，`family_verdict.pass=false`，`run_qc.py:371` → 退出 1。但这是一条**未修的长期红**，不是负控：425 个 worldgen 测试里**零个**引用 `run_qc` / `verdict` / `mutant_verdict` / `layer_one_two` / `layer_three`——整个 QC 判决器无测试覆盖。 |
| `worldgen/qc/run_qc.py --mutants`（预注册变异体套件） | **是（实测）** | 部分（实测） | 是（实测） | 见下「两条专查」。实跑退出码 **1**。 |
| `worldgen/tests`（pytest，425 项，verify 的 gating 阶段） | 是（实测，全绿） | 部分（读码） | 是 | 真负控只有三处：`test_build_gate.py`（双向）、`test_mutate.py:527`（贴错标签）、`test_gravity_landing.py:65`（negative half）。其余是正向断言。 |
| `worldgen/qc/diagnose_miner.py` | — | — | — | 不是闸：纯诊断打印，无判决分支，恒 0。列出以免被当成验收入口。 |
| `fuzzlab/verify.py` | 是（读码） | 否（读码） | 是（读码） | `verify.py:32-39` 三阶段全 gating，`:66-68` → `return 1`。红能传导（下条）。但没有任何东西演示过 `fuzzlab.verify` 会红。 |
| `fuzzlab/campaign.py` | 是（实测） | 否（读码） | 部分（实测） | 实测注入生成器故障 → **退出 1**（`campaign.py:202` 只认 `generator_errors`）。实测注入引擎故障使 5 个世界 15 条不变式全部 `violated` → **退出 0**，报告里 `"violated": 15`。这是写在 `:199-201` 的设计（「失败是战利品」），不是 bug，但一个只看 campaign 退出码的上游会把 15 条违反读成绿。 |
| `fuzzlab/tests/test_battery.py::test_short_campaign_finds_no_violation` | 是（实测） | **否**（实测+读码） | 是 | 这是 23 条不变式**唯一**的判决点（每引擎 25 世界）。它确实会因真违反而红——我用注入故障证过 `check()` 会吐 `violated`——但仓库里没有任何注入故障的构造。 |
| `fuzzlab/tests/test_oracles.py` | 是 | **是**（读码） | 是 | 真负控，但**是给 oracle 的，不是给不变式的**：`:98 test_holds_on_rejects_a_law_that_does_not_hold`、`:121/:127/:140/:146` 四条 `validate_plan` 拒绝路径、`:167` 「(None,True) 是证明、(None,False) 是超时」、`:43` 权重 vs 计数。它们证明「坏输入进 oracle 必须被拒」，不证明「坏引擎进不变式必须响」。 |
| `fuzzlab/tests/test_battery.py::test_distinct_indices_give_distinct_worlds` | 是 | 是（读码） | 是 | 反重言测试：注释直说「a generator that ignored its seed would pass everything else」。这是生成器的负控，不是不变式的。 |
| `fuzzlab/minimize.py` | 是（读码） | 否 | 是（读码） | `:179` 找不到复现体 → `return 1`。是搜索工具不是闸，退出 1 表示「没搜到」而非「有缺陷」。 |

## 点名：没有负控的闸门

- `worldgen/build.py::check_determinism` —— 全仓库最强的确定性主张（换 `PYTHONHASHSEED` 起子进程逐字节 diff 35 个世界 × 6 个产物 + 两张 roster）靠它，而它自己的 docstring 就写着「a gate that cannot fail is not a gate」——但没人演示过它会红。改坏一个字节使它红是十行的事。
- `worldgen/qc/run_qc.py`（含 `verdict` / `mutant_verdict`）—— 425 个测试零覆盖。这是决定「工厂出的世界能不能被上游流水线学会」的判决器，它今天是红的，但没有任何东西保证它是**因为该红的原因**红的；`verdict()` 里任何一处 `and` 写成 `or` 都不会被测试发现。
- `fuzzlab/props/*.py` 的 23 条不变式 —— 见下。
- `worldgen/mutate.py::mutation_gate_failures` 的可解性一半 —— 家族声明有负控，可解性声明没有。
- `fuzzlab/verify.py` / `worldgen/verify.py` 两个领地闸本身 —— 只演示过绿。

## 点名：退出码撒谎的闸门

- `worldgen/verify.py:55-78` —— **实测**：本次跑打印 `green` 并 `exit 0`，而同一次跑里 `QC.json` 的 `family_verdict.pass=false`（`t2-lock-fragile` 直接 `NoSeparatingGuard` 抛出，L1/L2/L3a 全 false）、`QC_MUTANTS.json` 的 `mutant_verdict.pass=false`。它确实在上一行打了 `MEASURED MISS: …`，两道 QC 也标的是 `miss` 不是 `FAIL`，所以文字层面没撒谎；但最后一个词是 `green`、退出码是 0，任何按退出码采信的上游都读到「worldgen 全绿」。这是 `verify.py:17-23` 明写的设计取舍，不是疏忽——但代价是这个领地的**验收入口对 QC 层的任何回归完全失聪**：QC 从今天的 pass=false 退化到全部崩溃，退出码仍是 0。
- `fuzzlab/campaign.py:202` —— **实测**：15/15 条不变式违反、报告里 `"violated": 15`、终端打印 `VIOLATED (15)`，退出码 **0**。同样是明写的设计（`:199-201`），且 `fuzzlab/verify.py` 靠 pytest 阶段（25 世界）而非 campaign 阶段捕捉违反，所以领地闸没漏；但 `campaign` 单独被调用时（README 第一行就教人这么调）打印 VIOLATED 而退 0。

## 两条专查的结论

**worldgen 变异体套件是否真判决：是（真会红，真退非零），但它不是「负控」。**

实跑（worktree 内，已删除临时报告）：

```
$ python -m worldgen.qc.run_qc --mutants --report QC_MUTANTS_CENSUS.json
== v-ce732813 (base t1-walk-maze)      L1=True L2=True L3a=True  held_out=0.666667 (base 1.0, delta -0.333333)
== v-707a64ad (base t1-switch-toggle)  L1=True L2=True L3a=True  held_out=0.737705 (base 0.773333, delta -0.035628)
== v-efe43df1 (base t2-switch-push)    L1=False L2=False L3a=False  ERROR: NoSeparatingGuard: no literal separates transition 95 from the positives
== v-a3446614 (base t1-portal-oneway)  L1=True L2=True L3a=True  held_out=0.586207 (base 0.548387, delta 0.03782)
mutant verdict: {"failed": ["v-efe43df1"], "pass": false, "passed": [...], "sampled": 4}
EXIT=1
```

所以它**不是**「只报告不判决」的套件：`run_qc.py:435` 的 `return 0 if mutant_verdict["pass"] else 1` 真的执行，退出码真的是 1，`pass:false` 真的写进了 `QC_MUTANTS.json`。这一点上它比仓库里多数闸门诚实。

但它作为负控有三处不成立，须一并记录：

1. **它扰动的是世界，不是被测的闸。** 预注册变异体证明的是「变异后的世界仍能跑通上游流水线」，不是「QC 的四层判决在有缺陷时会响」。没有任何变异体是针对 `verdict()` / `layer_one_two()` / `layer_three()` 的。要让 L2 或 L3a 该红时真红，需要的是一个故意坏的 mined rule set，仓库里没有。
2. **唯一那一条红，红错了原因，而这是文件自己承认的。** `PREREGISTERED_MUTANTS.md:59-91` 的 postscript 写明：`v-efe43df1` 崩流水线，**它的 base `t2-switch-push` 也崩**，原因是 `a0_relational_v1` 的词汇表表达力不足（与 `t2-lock-fragile` 同因），与突变层无关。该文件同时承认自己第 1 条规则写错了（绝对形 vs 「its base survives」形），并明确记录「bar 没有重写、样本没有换、pass 保持 false」。这份坦诚是真的；但结论是：这条红是一个**未修的上游缺口**，不是一次「我们证明了闸会响」的演示。
3. **它的红被上一层吞掉。** `worldgen/verify.py:47-48` 把这条 stage 标成 `gating=False`，所以 `--mutants` 的 exit 1 在领地闸里变成 `[miss]` 和 exit 0（本次实测）。

**fuzzlab 不变式是否有负控：无（推翻不了 RES-3 的判断，确认之）。**

搜索证据（`grep -rniE "mutant|mutation|inject|fault|self.?test|deliberately (broken|bad)|broken engine" fuzzlab`）：

- `fuzzlab/tests/test_battery.py` 命中的是 `test_short_campaign_finds_no_violation` 的注释与 `test_distinct_indices_give_distinct_worlds`（生成器反重言），**没有任何故意坏的引擎**；
- `fuzzlab/campaign.py` 命中的是 `generator_errors`（fuzzlab 自己造不出世界）的处理，与不变式无关；
- `fuzzlab/props/*.py`、`fuzzlab/worlds/*.py` 的命中全是 `hypothesis`（probe_frontier 的假设集）这个词的误命中；
- `fuzzlab/archive/cegis_miner.frontier_guards_are_consistent.skipped.json` 是一个 **skipped** 的最小复现体，不是 violated；
- `fuzzlab/props/__init__.py:10` 声称 `fuzzlab/props/test_<engine>.py` 是 pytest/hypothesis 前端 —— **这些文件不存在**（`ls fuzzlab/props/` 只有六个引擎模块 + `finding.py`）。`fuzzlab/conftest.py` 注册了三档 hypothesis profile，而全仓 fuzzlab 里**零个 `@given`**。所以 23 条不变式的 pytest 前端实际只有 `test_battery.py` 里那一条「25 世界无违反」的断言。

我自己做了一次一次性注入实验（纯内存，未写任何文件、未改任何源码），只为区分「无负控」与「不变式是死码」：

```
$ python -c "…把 zero_space 的 basis 多塞一个伪向量…"
clean findings: []
injected-fault findings: 3
   [violated] zero_space.law_space_is_complete -- engine returned a basis vector that is not a conserved law
   [violated] zero_space.rank_nullity          -- basis has 6 vectors but dimension reports 5
   [violated] zero_space.membership_agrees     -- contains() is False for one of the engine's own basis vectors
```

结论：不变式**不是**死码，注入故障时会响；但这条演示是我临时造的，**仓库里没有任何可执行物做这件事**，也没有任何 CI/脚本会重跑它。按本仓库的方法论，23 条不变式目前是 23 盏「没被演示过会红」的绿灯。

最接近负控的既有物是 `fuzzlab/runs/20260728T085448Z-E4-property-fuzz/GENERATOR_AUDIT.md` + `BUGS.md` 的语料功率审计（「`gridworld` 3200 个世界里 0 个障碍物」→ 三个生成器被修）。那是**语料功率**的负控（证明第一次全绿「certified nothing」），不是不变式灵敏度的负控——`BUGS.md` 自己就把这一点写在最前面。另有历史证据表明不变式确实响过：`test_oracles.py:1-18` 记载两次**假指控**（probe_frontier 120/120、fd_adapter 13 个计划），说明不变式会响、且响的是 oracle 的错——但那两次的修复产物是 oracle 的测试，不是不变式的负控。

## 我不确定的

- `worldgen/verify.py` 该不该算「退出码撒谎」有解释空间：它打了 `MEASURED MISS`、把 QC 标成 `miss` 而非 `FAIL`、并在 docstring 里写清了理由（「不能因为答案不好看就降 bar，也不能悄悄把退出码变绿」）。我按「报告 mismatch 的路径退出码必须非零」的字面标准判为 `部分`，但如果本次普查的标准是「文字与退出码是否一致」，它应判 `是`。这一条建议由 RES-3 定调。
- `fuzzlab/campaign.py` 的 exit 0-on-violation 同理：设计上是对的（违反是产品），且领地闸靠 pytest 阶段兜住了。我判 `部分` 是因为 README 第一行就教人单独跑 campaign。
- 我没有实跑 `fuzzlab/verify.py` 全程（第三阶段要跑 engine-rig 全套件），只跑了它的第一阶段（`pytest fuzzlab/tests -q`，56 项全绿，exit 0）与 campaign 的注入实验。`fuzzlab.verify` 会因 pytest 阶段变红这一点是**读码**结论。
- `worldgen/out/qc/` 下若干 `candidates.jsonl` / `engines_report.json` 被本次实跑改写（worktree 内，未提交）；这是运行 QC 的必然副作用，不是我写的文件。我另创的 `QC_MUTANTS_CENSUS.json` 已删除。
- 领地边界：`exam/guard.py` 会消费 `worldgen` 的 `INDEX.json` 并有自己的闸，但它在 `exam/` 领地，本次未查。
