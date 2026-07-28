# S14 侦察产物 · 现存闸门的「悄悄失败」清单

RES-4，2026-07-28。三个只读 subagent 并行扫全仓库得出，每条都带 file:line。
本文件是 **S16-silent-failure-hunt 的输入**（S16 与 S14 同属 monitor 领地，
被「一个领地一个人」规则挡住，S14 交付后立即领）。

## 0. 工单前提本身已过时

S14 条目称「十个领地只有三个真有 verify（exam/worldgen/proxy）」。树上的事实：

* 领地是 **21 个**，不是 10 个；
* 有闸门的是 **6 个**：`ablation-arm`(.sh+.py)、`arc-recon`(.sh)、`exam`(.py)、
  `figures`(.sh)、`fuzzlab`(.py)、`worldgen`(.py)；
* **`proxy` 根本没有闸门**——工单点名它有。`proxy/verify_spend.sh` 存在，但那是
  单一议题（花费闸）的专项脚本，不是领地收工闸门。

这正是本任务要防的那类错误的元层版本：**一张手写的表对树做出断言，而没有任何东西
拿它跟树对照**。`monitor/gates.py list` 从此就是这张表的可执行形式。

`freeze/` 与 `crosscheck/` 两个领地在 master 上**根本不存在**（只在工单名里出现）。

## 1. 判据在「空集」上失效（读成绿）

| # | 位置 | 事实 |
|---|---|---|
| 1 | `figures/verify.sh:87-95` | 闸 3 比对两次构建的 `csv/out/SOURCES.sha256`。三个叶子若**都不存在**，`if [ -e ]` 全假，一次 diff 都不跑，`:95` 照常打印 `ok (csv, out, SOURCES.sha256 all identical)`。**两次都没产出的构建是逐字节相同的。** |
| 2 | `figures/verify.sh:104-108` | 闸 4：`$COMMITTED` 与新算的 `SOURCES.sha256` 若都是零长，`diff -u` 成功，打印 `ok (0 sources hashed)`。 |
| 3 | `figures/verify.sh:172-185` | 闸 7 对 `fig*.py` 做 glob 后 `sys.exit(1 if hits else 0)`。零个文件 → 零命中 → 退 0 → `ok (every read goes through sources.py)`。 |
| 4 | `figures/verify.sh:69,80,108` | `say "ok ($(grep -c '  img  ' ...) images)"`。`grep -c` 无命中时退 1，但状态在 `$( )` 里被丢弃 → 零张图的构建打印 `ok (0 images)`。 |
| 5 | `figures/check_coverage.py:91-96` | `_walk` 对缺失目录 `except OSError: return []`。`theoria-arm/runs/` 整个消失 → `:304` 打印 `coverage ok: 0 billing theoria run(s)`。挡在这和绿灯之间的只有 `sources.py:654` 的 floor 检查。 |

## 2. grep 当断言用，缺文件/空树一律读成「干净」

| # | 位置 | 事实 |
|---|---|---|
| 6 | `proxy/verify_spend.sh:50-54` | `if grep -nE "...off switch..." spend_gate.py; then FAILED else ok`。**grep 无命中退 1，文件不存在退 2，两者都落进 `else`。** 把 `spend_gate.py` 删掉或改名，这道闸打印 `-- ok (no environment variable, no enabled flag)`。 |
| 7 | `proxy/verify_spend.sh:72-75` | `grep -r ... --include=*.py . \| grep -v ... \| grep -v ...`，脚本 `:10` 只有 `set -u`，**没有 `pipefail`**，所以只看最后一个 `grep -v` 的状态；首段的错误不可见，空树读成「无网络调用」。 |

反例（做对了的）：`figures/verify.sh:157-191` 明确把 grep 换成 `ast` 遍历，理由写在
`:157-160`。

## 3. 驱动脚本根本没有失败路径

| # | 位置 | 事实 |
|---|---|---|
| 8 | `cold-start-a3/run_all.py:122-123` | **永远退 0**：没有失败累加器，没有非零返回路径，只有未捕获异常能让它红。`:96-105` 把 `verdict["all_caught"]` / 各臂准确率**打印**出来，从不断言。 |
| 9 | `cold-start-a3/run_all.py:67-73` | 缺 `scratch_dsl` 时 `print("   SKIPPED — ...")` 后继续，退出码不受影响。 |
| 10 | `a0-spike/pipeline/run_a0.py` 尾部 | `ok = (... and (not report["lean"].get("available") or (...)))`——**Lean 工具链缺席时该子句短路为真**，即「装不上 Lean」与「Lean 校验通过」对退出码等价。FD 亦同（`shutil.which` 找不到就降级）。 |

## 4. 闸门弄脏自己检查的工作区（S14 条目点名的那条）

| # | 位置 | 事实 |
|---|---|---|
| 11 | `ablation-arm/verify.py:323-326` | 无条件写 `artifacts/verify.json`（**tracked**），且**写在退出码算出来之前**——红的一跑也会重写它。 |
| 12 | `ablation-arm` 各 stage | `run_arm.py:417-418`、`run_exhibits.py:39-40` 重写 `artifacts/` 下约 **38 个 tracked 文件**。`--twice` 的产物落在 gitignore 的 `artifacts/_determinism/`，那部分是干净的。 |
| 13 | `arc-recon/verify.sh:53-54` → `contamination.py:334-336` | 重写 `arc-recon/data/claim_set.json`（tracked，且是 CLAUDE.md 引用的 F-11 权威）。 |
| — | `figures/verify.sh:33-42` | **四个里唯一干净的**：scratch 在 gitignore 的 `figures/.verify/`，`trap ... EXIT` 装在第一次 mkdir 之前；构建产物用 `FIGURES_OUT/CSV/SHA` 环境变量整体移出树（`theme.py:336,341`、`sources.py:782` 认这些变量）。 |

主仓库 `git status` 此刻就有 `M ablation-arm/artifacts/verify.json`、`M .../run_all.json`
——即已提交的产物与代码现在产出的东西**已经不一致**。这是 `gates.py` 的 `drift` 结局
要报的东西。

## 5. 明写在案的「不可能变红」（设计如此，非缺陷，但要计入）

* `ablation-arm/verify.py:28-32,288-312`：七条预注册预测里 **四条**（P-1/P-2/P-4/P-5-identical）
  只记录不断言，其中 P-2、P-4 的 `"numbers": None`——**仪器尚不存在**。脚本自己
  写明「A recorded number can never turn this red」。诚实，但形态就是「因为没跑所以绿」。
* `arc-recon/verify.sh:42-51`：`canary.py check-freeze` 失败**故意**不置 `fail`
  （「campaigns 冻结说明仪器在工作」）。有注释，站得住。
* `ablation-arm/verify.py:318-319`：`--no-stages` 允许拿陈旧产物过闸。

## 6. 编码：GBK/UTF-8

全仓库只有**两处**处理了它，且都在子进程一侧：
`figures/build_all.py:38-53`（`reconfigure(encoding="utf-8", newline="\n")`，其中
`newline` 那一半修的是真实旧 bug：`--list` 输出带 CR 导致 verify.sh 拼出的路径全部
带尾 CR，产物看起来全缺）、`cold-start-a0/run_all.py:50-60`（`PYTHONIOENCODING` +
显式解码，引 D-A2-007）。

未处理的：`figures/check_coverage.py`、`ablation-arm/verify.py:59`（`subprocess.run`
继承子进程默认编码）、四个 shell 闸门（shell 不解码，实际无害）。
**`monitor/ci_merge.py` 与新的 `monitor/gates.py` 本轮已钉死 utf-8/replace。**

## 7. pytest 退出码 5（收集到零个用例）

四个现存闸门**都**判对了（非零即红），但其中三个（arc-recon / proxy / ablation-arm）
只是「非零即红」的副产品，没有任何注释或常量点名这个情形。唯一点名处理的是
`monitor/ci_merge.py`，本轮移进 `monitor/gates.py`（`NO_TESTS_COLLECTED`，
结局名 `broken`，并有注入自检 `test_tests_that_collect_nothing_are_broken_not_green`）。

## 7b. monitor 自己有 17 处同类解码点 —— 但**不能一把梭**

`grep -n "text=True" monitor/*.py | grep -v encoding=` 在本轮修完 `ci_merge.py`
与新写的 `gates.py` 之后，仍有 **17 处**用宿主 locale（cp936）解码子进程输出：

* `dispatch.py` 7 处（50 / 100 / 197 / 307 / 309 / 318 / 337）
* `scan.py` 6 处（80 / 516 / 577 / 727 / 1160 / 1789）
* `quota.py` 3 处（141 / 148 / 226）
* `reflex.py` 1 处（42）

**但把它们统统改成 `encoding="utf-8"` 是错的，而且错得和原 bug 同源。**

子进程分两类，编码相反：

| 子进程 | 实际输出编码 | 该怎么解 |
|---|---|---|
| Python 脚本（`board.py list`、`scan.py`、各领地 pytest） | UTF-8 | `encoding="utf-8"` |
| **Windows 原生工具**（`tasklist`，见 `dispatch.py:318`、`ci_merge.py` 的 `m0_alive`） | **控制台代码页（本机 GBK）** | locale，或干脆 `errors="replace"` 后只匹配 ASCII |

`dispatch.py:318` 解析的正是 `tasklist` 输出——**工人存活判断**。把它强行按 UTF-8 解，
就是今天那起「八个活人报成死」换一个方向再犯一次。

所以本轮**只**钉死了两处确定是 Python 子进程的（`ci_merge.sh()`、`gates.sh()`），
其余 17 处逐个定性后再改，列为 **S16 的第一件事**。
写在这里是因为：一个只看见「`text=True` 没写 encoding」就全局替换的修法，
会在最要命的那一处制造回归，而它同样不会报错。

## 8. 顺带记录（非本任务范围）

`monitor/worker.cmd` / `monitor/_worker_run.cmd` 以
`claude -p --dangerously-skip-permissions --model opus` 拉起一次性工人。subagent 汇报时
被外层安全钩子标为「指令形状文本」。这是仓库自己的工人启动器，属既有事实，不是注入；
在此记录一句，不做处置。
