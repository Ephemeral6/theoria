# C11-tool-failure-as-truth — 运行叙述

领地 `engine-rig`。零网络、零 API、封存堆零接触、$0.00。
主工作树与其它 worktree 全程只读或未碰；`cold-start-a0/` 一个字节没动。

**它吸收了 `monitor/board/items/E12-adopt-the-unsolvable-canon.md`**——那条写的正是
`p13_fd_dividend.py` 那一处 + 全 engine-rig 扫查 + 负样本，是 C11 的真子集，已被涵盖。
**不要另开分支做 E12。**

## 做了什么

工单三件：

1. **逐处订正**：SURVEY 在本领地点名 **11 处 + 一族（5 个调用点）**，我逐处在当前树上重核，
   **方向判定 11 处全部成立**，**10 处已修**，1 处（`bench` 的 `guard_refused`）未改并写下理由。
   逐处见 `CORRECTIONS.md`。
2. **补上没被调用的正典**：`backends.proves_unsolvable` 早就写好、`p13_fd_dividend.py`
   第 53 行早就 import 了、`log` 早就在手边，差的只是一次属性访问。
   负样本 `tests/test_tool_failure_is_not_truth.py`（77 条），见 `MUTATION.md`。
3. **常设检查**：`tools/check_solver_status.py`（`ast`，不是 grep），
   两级、全仓标定、假阳假阴逐条报出，见 `CALIBRATION.md`。
   它以一条 pytest 跑在 engine-rig 的 gate 里——`monitor/gates.py` 把本领地解析成 pytest，
   不是测试的检查等于不跑的检查。

对账见 `RECONCILIATION.md`：**结论未变、方法已修。** 不是抓到了什么。

## 对抗复核推翻了什么

`ADVERSARIAL.md` 是复核员自己写的全文，未经转述。它**没有**推翻方向判定
（11 处逐条独立复核、全部同意）和对账（三点独立复算、数字全对，并确认我把工单说的
「三行」纠正成「五处分在两张表里」是对的）。**它推翻了三件事，三件我都接受并已修：**

| 被推翻的 | 我原来写的 | 实际 |
|---|---|---|
| **#9 的定性** | 「渲染层的措辞问题」 | **判定层的不健全**：`dividend.py:874` 的 `continue` 在 `failures()` 里，而 `failures()` 定 bench 的退出码（`tests/test_bench.py:622` 的原话）。FD 超时 → 该行整个退出健全性判据 → bench 仍退 0 |
| **#8 的修复** | 「部分修：`basis`/`budget` 上对象」 | **惰性的**：零负样本 + 一个不可达的 else 分支（记录一个不可能发生的二选一）+ 字段不进产物 = 只改了注释。已重修为在下判断处 `raise` |
| **「负样本构造上必然会红」** | 18/18 击杀、0 逃逸 | 复核做 36 个，**31 杀 5 逃**。我的 18 个是我自己测试的镜像，度量的是自洽不是覆盖 |

另外三条它是对的、我已订正：漏了第 12 处（`deadlock_carver.same_answer`，与 p13 同形，
而我当时用了双重标准）；编码一族**实修 5 处却自报 4 处**；
常设检查的 ERROR 精确率按它自己的分级判据是 **50% 不是 75%**，
且分级**由变量名决定**而不是由代码做了什么决定。

被推翻的原文全部保留并标了 `[OVERTURNED]`，没有静默重写。

## 复核员**没能**查的面（原样搬过来，这是这份复核的边界）

1. **本机没有 Fast Downward 构建**（`.toolchain/` 按设计 gitignore）。所以 p13 无法重跑，
   `bench/` 的 FD 路径——**包括推翻 #9 的那条 `guard_refused` 链路**——只有读码论证，
   **没有实跑证明一次真超时确实会让 bench 退出 0**。全套 23 条 skip 里有几条是 FD 相关的。
2. **推翻 #9 的严重性没有被量化**：E2 已发布的 `dividend.json` 里有几行 `guard_refused`
   非空、那几行是不是本来就会被健全性判据放过——没算。论证的是**机制**，不是**已放电**。
3. **只做了 36 个变异体**，且集中在本次改动的 11 处。没有对 `bench/`、`recheck/` 其余部分、
   `cegis_miner`、`ic3_pdr` 做变异。「31 杀 5 逃」是这 36 个上的数，不是杀伤率的估计。
4. **常设检查的假阳假阴是构造的**，不是在真实提交历史上跑出来的。ERROR 四处逐条看了源码，
   NOTE 22 处只抽看了 `CALIBRATION.md` 点名的那几处。
5. **`cegis_miner` 那条「我判它不成立」它没有独立复核**——要判「frontier 承诺的是同长枚举
   还是深度 ≤3 枚举」得读 `enumerate_frontier` 的全部调用方和 E11 的
   `partials/cegis_miner-via-bruteforce.md`，超出它的预算。**它既不背书也不反对。**
6. **并发**：它复核期间我仍在写这个目录，`MANIFEST.json` 的 18 条 `sha256` 里有 1 条不符
   （`CORRECTIONS.md`，manifest 停在 `base_commit: b0d3d3d` 而 `e392d46` 又改了它）。
   **已在最后一次提交前重算。**
7. 没跑 `python -m tools.run_all`、没做 `fixtures.generate_all` 的字节稳定性复核、
   没验 `artifacts/candidates.jsonl` 的 sha256 与 `release/MANIFEST.jsonl:667` 是否仍相符
   （只核了「加字段会改 id」这个推理的结构前提）。

## 我自己没能查的面

* 与上面第 1、2 条相同：**无 FD 构建**，所以 `p13_fd_dividend.py` 的修改**从未在真 FD 上跑过**。
  它的负样本用的是一个打印固定日志、返回固定退出码的假 FD（`.py`，走
  `sys.executable` 分支，与真 `fast-downward.py` 同一条路径），这能证明判据，
  **不能证明与真 FD 的集成**。
* **三处新字段扣在 payload 外**（`zero_space.scope_exhaustive`、
  `SearchResult.max_expansions/exhaustive`、`Reachability.basis/budget`）——
  因为 `artifacts/candidates.jsonl` 的 sha256 被 `release/MANIFEST.jsonl:667` 钉住、
  候选 id 是内容寻址。**SURVEY 抱怨的「产物不足」因此仍未消除**，见 `INBOX-proposals.md` 提案 4。
* `bench/` 领地内 #9 未改；`runs/20260728T141724Z-E5-cert-recheck/manifest.py` 未改
  （冻结的运行记录，改它会falsify provenance）。两者都只登记。

## 命令

```bash
cd engine-rig && python -m pytest -q                    # 全套（FD 相关 skip 属预期）
cd engine-rig && python -m tools.check_solver_status    # 常设检查，退出 1 即有 ERROR
cd engine-rig && python -m tools.check_solver_status .. --notes   # 全仓报告（只读）
```
