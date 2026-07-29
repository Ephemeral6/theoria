# 领地：figures / release

普查员：V11 负控普查 / RES-3 verify 赛道。工作树 `.worktrees/v11-negative-control-census/`（master，只读 + 实跑）。
`实测` = 我在本工作树里真跑过并观察到退出码；`读码` = 只读源码推断。

| 入口 | 能红 | 有负控 | 退出码诚实 | 证据 |
|---|---|---|---|---|
| `figures/verify.sh` | 是（实测） | 部分（实测） | 是（实测） | 本树实跑 `bash figures/verify.sh` → 第 1 关 fig06 抛 `ValueError: THEORIZE_LOG.md: entry ids do not match the declared set. unexpected=['E-08']`，脚本印 `FAIL: build pass A did not complete`，**exit=1**。九关中只有第 8 关自带负控。 |
| `figures/build_all.py` | 是（实测） | 否（读码） | 是（实测） | `build_all.py:141-143` 收集 `failures` 后 `return 1`；上面那次实跑就是它红的。无 self-test、无坏 fixture。 |
| `figures/check_coverage.py`（默认） | 是（读码） | 是（实测） | 是（实测） | `check_coverage.py:308-312` 有 failures 即 `return 1`。实跑 `python figures/check_coverage.py` → 绿，exit=0。 |
| `figures/check_coverage.py --self-test` | 是（读码） | 是（实测，**它本身就是负控**） | 是（实测） | 实跑 exit=0，输出：`coverage self-test ok: narrowed to the pre-P8 roll-up list, the probe reports both runs it was written to catch (bare_cc-g50t-claude-sonnet-5-ddabe772, bare_cc-sk48-claude-sonnet-5-9022a076)`。`self_test()` 在 `check_coverage.py:230-278`，负控没打中就 `return 1`（`main` 283-292）。 |
| `figures/manifest.py` | 否（读码） | 否 | 不适用 | `manifest.py:152-172` 只有 `return 0` 一条出口；它是 provenance 写入器，不是闸门，但也没有任何拒绝路径。 |
| `release/check_redlines.py`（`--mode generate` 默认 / `verify`） | 是（读码） | 否（读码） | 是（读码 + 实测绿路径） | `check_redlines.py:304-306`：`if total: print(...); return 1`。实跑 `--mode verify` → 0 violation，exit=0。**从未有人演示它会红**：release/ 下没有测试、没有故意埋钥匙/封存 payload 的 fixture。 |
| `release/enumerate.py`（`--dry-run`） | 是（读码） | 否（读码） | 是（读码；本树未触发红路径） | 红线不清时 `enumerate.py:294` 印 `ABORT: the red lines are not clear; no manifest generated.`，`enumerate.py:297` **`return 2`**。实跑 `--dry-run` 本树红线清白 → exit=0。 |
| `release/checklist.py`（`--dry-run`） | **否**（读码） | 否 | 不适用（永远绿） | `checklist.py:226-262` 全函数只有 `return 0`（256、260 两处）。ABSENT / 「no reason recorded — this needs one before release」都只是打印文字，不改退出码。 |
| `release/reproduce.py`（默认 / `--all` / `--list` / `--dry-run`） | **否**（实测） | 否 | **否**（实测） | 见下「退出码撒谎的闸门」。 |
| `release/bundle.py --check` | 不适用 | 不适用 | 不适用 | **该文件不存在。** 全仓 `find . -iname "*bundle*"` 只命中 `exam/handover_bundles/`。release/ 里只有 `check_redlines.py`、`enumerate.py`、`checklist.py`、`reproduce.py`。 |

## figures/verify.sh 逐关负控覆盖

| 关 | 它检查什么 | 有负控吗 | 证据 |
|---|---|---|---|
| 0 | 每个声明的必需数据源在位；且每条 discovery 规则达到自己的 floor（`sources.check_required()` / `floor_violations()`） | 否（读码） | 无 self-test、无坏 fixture。**机制我在内存里单独验过（实测）**：把 `pilot_rollup` 规则的 pattern 改成 `pilot_ZZZZ-*.json` 后 `floor_violations()` 返回 1 条、`check_required()` 报 1 个 missing——说明能红。但这是我临时做的探针，仓库里**没有**任何常驻负控。侧证：`check_coverage.self_test` 特意把 floor 一起降下去，注释说「否则第 0 关先抓到、探针就没被问过」——即作者知道第 0 关会响，但从未把它写成可执行负控。 |
| 1 | 构建 pass A 全部完成 | 部分（实测，属**意外**而非设计） | 本树实跑就红了（fig06 `ValueError`，exit=1）。这是真实缺陷偶发触发，不是负控：没有任何「故意坏的输入必须让 pass A 红」的可执行断言。 |
| 2 | 构建 pass B 全部完成 | 否（读码） | 与第 1 关同码路径，但本次实跑在第 1 关就 `exit 1`，第 2 关根本没执行。 |
| 3 | A 与 B 逐字节相同 | **否**（读码） | 无任何注入非确定性的负控。反证很硬：`figures/RUN_STATE.md:63-66` 与 `figures/README.md:96-101` 都记录了 mathtext 缺陷「*deterministically* wrong, so both builds carried it and **gate 3 stayed green**」——即这一关被记录为**曾经该红而未红**，且至今没有一次演示它会红。 |
| 4 | 重算的数据源哈希 == 已提交的 `figures/SOURCES.sha256` | 否（读码） | 无负控，也无历史红记录。本次实跑未到达该关。 |
| 5 | 每个声明产物存在且非空（N 图 × 2 主题 × 2 格式 + N CSV） | 部分（读码） | 曾**意外**红过：`RUN_STATE.md:79-82` 记 `build_all.py --list` 输出 CRLF，导致「gate 5 built paths with a trailing carriage return and declared every artefact missing」。是缺陷触发的真红，不是常驻负控。 |
| 6 | 已提交的 `figures/csv`、`figures/out` == 新鲜构建 | **否**（读码） | 只有**反事实**记录，没有演示：`RUN_STATE.md:67-70` 说 SVG CRLF「a fresh checkout plus a Windows rebuild **would have** failed gate 6」——是虚拟语气，缺陷在到达该关前就被修掉了。没有任何「故意改一个 committed 产物、要求第 6 关必须红」的脚本。 |
| 7 | 没有 fig*.py 绕过 `sources.py` 直接碰文件系统（AST 解析 `open()` / `os.walk` 等） | 部分（读码） | 只有一次**假阳性**的历史触发：`verify.sh:170-174` 自述第一版用正则，「its first finding was the phrase "never ``open()``" inside a docstring」。改成 AST 后**从未演示过真阳性**（没有一个故意写 `open()` 的坏 fixture）。 |
| 8 | 磁盘上的东西是否真的进了图（`check_coverage.py`）；**先跑负控** | **是**（实测） | `verify.sh:205-210` 把 `check_coverage.py --self-test` 放在前面且非可选，负控不响就 `fail`。我单跑 `python figures/check_coverage.py --self-test` → exit=0 且明确点名它必须抓到的两个 run。负控本身还抓到过探针自己的两版错误（`check_coverage.py` docstring 33-51、`RUN_STATE.md:206`、`RUN_STATE.md:283-287`）。**这是全仓样板，但它只覆盖第 8 关自己。** |

**结论：九关里只有第 8 关自带可执行负控；第 3、4、6 关——恰恰是「两次构建逐字节相同」和「committed 树 == 新构建」这两条最常被引用的确定性承诺——一次都没有被演示为会红。** 第 3 关还有书面记录说明它曾对一个真实缺陷保持绿灯。

## 点名：没有负控的闸门

* `figures/verify.sh` 第 **0、2、3、4、6、7** 关 —— 零可执行负控。其中第 3、6 关是对外宣传的核心确定性主张。
* `figures/build_all.py` —— 能红（实测），但没有任何「坏输入必须红」的断言。
* `release/check_redlines.py` —— 全仓最敏感的闸门（凭据泄漏 + 封存堆）。`return 1` 路径存在（304-306），但**没有任何人演示过它会红**：release/ 下无测试、无埋雷 fixture。RES-2 的交付记录只写「两条都实测清白」，那是绿灯证据，不是负控。
* `release/enumerate.py` —— ABORT 路径退出码正确（读码），但同样从未被演示触发过。
* `release/checklist.py` —— **不是「没有负控」，是根本不能红**（见下）。

## 点名：退出码撒谎的闸门（行号 + 实测退出码）

1. **`release/reproduce.py:351` —— `return 0` 无条件。**
   `main()` 里没有任何一条依据 grade 的失败出口：`drifted`、`command-failed`、`manifest-stale` 全部走到同一个 `return 0`（`reproduce.py:348-351`）。
   **实测（本工作树，master）**——为不覆写被跟踪的 `release/REPRODUCTION_REPORT.md`，我把 `reproduce.OUT` 指到 scratchpad 后原样调用 `reproduce.main([])`：

   ```
   cd .worktrees/v11-negative-control-census
   python -c "import sys; sys.path.insert(0,'release'); import reproduce; \
   reproduce.OUT=r'<scratchpad>/REPRO.md'; rc=reproduce.main([]); print('MAIN RETURNED:', rc); sys.exit(rc)"
   ```

   实际输出：

   ```
   1/9 reproduced; wrote ...\REPRO.md
     command-failed       figures
     manifest-stale       papers/phase1-workshop
     reproduced           engine-rig
     declared-not-run     battery
     declared-not-run     exam
     needs-api            baseline-arms
     needs-api            theoria-arm
     needs-api            arc-recon
     needs-ground-truth   baseline-arms/schema_traces
   MAIN RETURNED: 0
   exit=0
   ```

   **九个目标里只有一个复现成功、论文图表territory 直接 `command-failed`，退出码仍然是 0。** 任何 CI 接它都拿绿灯。
   （等价直跑命令为 `python release/reproduce.py; echo "exit=$?"`，会覆写 `release/REPRODUCTION_REPORT.md`，故未采用；代码路径完全相同。）

2. **`release/reproduce.py:343-345` —— `--dry-run` 也是 `return 0`。**
   实测：`python release/reproduce.py --dry-run; echo "exit=$?"` → `dry run: nothing written` / **exit=0**。
   `--dry-run` 下所有非 slow 目标被 `continue` 跳过（`reproduce.py:335-336` 上方的循环），什么都没检查也是绿——这一路「跑了」和「根本没跑」外观相同。
   `--list` 同样 exit=0（实测），符合预期。

3. **`release/checklist.py` —— 一个原理上不能红的闸门。**
   `main()`（226-262）只有 `return 0` 两处。实测 `python release/checklist.py --dry-run; echo "exit=$?"` → `7 present, 3 withheld, 0 absent`，**exit=0**。即便某项 ABSENT、即便触发 `"no reason recorded — this needs one before release"` 这句自述的阻断条件，退出码依旧是 0。按本次方法论：**一盏后面没有东西的绿灯。**

**对已知报告的一处更正（重要）**：任务书里「某个 `--dry-run` 打印 ABORT 却 exit 0」在本树**复现不了**。全 release/ 只有 `enumerate.py:294` 一处打印 `ABORT`，其紧邻的 `enumerate.py:297` 是 `return 2`；`git log -p -- release/enumerate.py` 显示该文件只有一次提交（`ef4e188`），且那次引入的就是 `return 2`——ABORT 路径**从来没有**返回过 0。原报告（`monitor/inbox/20260728T160000Z-RES-2-...md`）把两件事写在同一个 bullet 里，可核实的那一半是 `reproduce.py` 的 drifted → exit 0，已在上面 1、2 条坐实。

## 我不确定的

* **`enumerate.py` ABORT 路径我没有实测触发。** 触发需要一棵红线不清的树（缺 `.env` 或树里真有封存 payload）。本工作树位于主仓 `.worktrees/` 下，`load_api_key` 沿父目录找到了主仓的 `.env`，所以 `--mode generate` 一路绿。（我只看到并只在此复述仓库自己的掩码形式 `7171...05dd (len 36)`，**未读取、未打印任何密钥明文**。）故第 297 行的 `return 2` 是 `读码`。
* **verify.sh 第 2–8 关本次未执行**：第 1 关就 `exit 1` 了，所以第 3/4/5/6/7 关的「能红吗」全是 `读码`；只有第 8 关我单独跑通了（`实测`）。
* **verify.sh 在 master 上当前是红的**，原因是 fig06 的 `THEORIZE_LOG.md` 多了一个 `E-08` 条目。这本身是 figures 领地的一个现存缺陷（按纪律我没有修），也顺带证明第 1 关是活的。我**不确定**这个红是 master 本身就有，还是本工作树被并发会话改动所致——见下条。
* **本工作树 `git status` 里有 8 个 `worldgen/out/qc/**/candidates.jsonl`、`engines_report.json` 处于 modified 状态**，内容级差异（非行尾）。我跑过的命令没有任何一条会写 worldgen；怀疑是同一 V11 普查里另一个领地的普查员共用了这棵工作树。我没有动它们，也没有回滚。若本次普查的多个普查员确实共享此工作树，则「实测」结果之间可能互相污染，这一点需要 RES-3 确认。
* `reproduce.py` 的 `_git_restore` 在我那次实跑后确实把 figures/papers 的产物还原干净了（`git status` 里无 figures/、release/、papers/ 改动）。
