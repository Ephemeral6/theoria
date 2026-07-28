# C11 — 常设检查的标定：假阳、假阴，和它该不该进 CI

被标定的对象：`engine-rig/tools/check_solver_status.py`。
标定面：本分支工作树全仓 22 个领地的全部 `.py`（**只读**），外加 C11 修复前的
`tools/p13_fd_dividend.py`（从 `git show HEAD~2` 取出，作为已知阳性）。

用 `ast`，不用 grep。理由不是审美：`figures/verify.sh` 第 7 关的第一版正则就死在这上面，
而这里需要正则给不出的两件事——**这个比较的值有没有被绑定**，以及**绑给了谁**。

---

## 一、判据（写死在代码里的那条）

只找一个形状：**一个读取「工具状态」的比较表达式，其值被绑定到一个「断言世界」的名字上。**

```
unsolvable = done.returncode == 12          ← ERROR
ok         = proc.returncode == 0           ← NOTE
if proc.returncode != 0: raise              ← 不报（没绑给任何断言）
unsolvable = proves_unsolvable(rung, rc, log)  ← 不报（交给谓词裁决了）
```

绑定的形式覆盖：赋值、带注解赋值、关键字实参、字面 dict 的值、
以及一个名字本身就是断言的函数的 `return`。

三张词表，两级：

* `TOOL_STATUS_TOKENS`（强）：`returncode` / `exit_code` / `retcode` / `success` /
  `failed` / `timed_out` / `killed` / `crashed` …
* `WEAK_STATUS_TOKENS`（弱）：`status` / `rc` / `code` / `error` / `timeout` /
  `signal`。**只有与整数字面量比较时才算**——`== 12`、`!= 2` 是退出码和求解器状态码
  的真实形状，而 `self.status == REACHABLE` 是引擎在说自己的答案。
* 断言词表分两级：`VERDICT_TOKENS`（关于**世界**：unsolvable / unsat / proved /
  holds / valid / verified / reachable / deadlock …）判 **ERROR**；
  `SOFT_VERDICT_TOKENS`（关于**进程**：ok / green / pass / clean / agree …）判 **NOTE**，
  **永不使 CI 变红**。

匹配按 `_` 切出的**整词**，不按子串——否则 `status` 会在 `statustext` 里命中，
`rc` 会在 `src` 里命中。

**两级的划分不是先验设计，是标定逼出来的**：见下。

---

## 二、标定结果

### 第一版（单级，断言词表含 `ok`/`green`/`pass`，`status` 无整数限制）

全仓 **26 处命中**。逐处手判：

* 真阳性 3：`cold-start-a0/certify/fd_unsat.py:46`、`monitor/reflex.py:147`、
  `theoria-arm/inner/certify.py:247`
* 假阳性 22
* 无法判定 1（`release/checklist.py` 解析失败）

**假阳率 85%。** 而且在 `engine-rig` 自己家里就有 2 处假阳
（`engines/probe_frontier/reach.py:67` 的 `self.status == REACHABLE`、
`tools/run_all.py:198` 的 `p.reach.status == probe_frontier.UNREACHABLE`）——
两处都是引擎在读**自己的**答案，不是在读工具的退出码。
一条在自己领地上就 85% 假阳的检查，等于没有检查。

### 第二版（弱状态词要整数字面量；断言词表分两级）

| 级别 | 全仓命中 | 我判真 | 我判假 | 精确率 |
|---|---|---|---|---|
| **ERROR** | 4 | **3** | 1 | **75%** |
| NOTE | 22 | 1 | 21 | 5% |

`engine-rig` 领地：**ERROR 0、NOTE 0**（修复后）。修复前对同一文件重放，
ERROR 1（`p13_fd_dividend.py:129`），假阳 0。

#### ERROR 级四处，逐条

| 位置 | 代码 | 我的判定 |
|---|---|---|
| `cold-start-a0/certify/fd_unsat.py:46` | `return bool(match) and int(match.group(1)) == FD_UNSOLVABLE_EXIT` | **真阳。** 就是 SURVEY 的 U-3，独立命中，不是我喂进去的。 |
| `monitor/reflex.py:147` | `hold = q.returncode == 2` | **真阳**，但**命中理由是词形巧合，我要说清楚**：`hold` 进词表是因为「不变量 holds」，这里它是「暂停舰队」。语义上仍然对——熔断器崩溃退出 1 被读成「预算正常」——但如果检查是靠这种同音字吃饭的，它的召回不可信。 |
| `release/checklist.py:0` | 文件**根本不解析** | **真阳，而且是本次最意外的发现**：`git show HEAD:release/checklist.py` 的第 45 行里 `newline="\n"` 的 `\n` 被写成了**真正的换行**，`ast.parse` 与 `python release/checklist.py` 都会 `SyntaxError`。这是**已提交**的语法错误，不是检出产物。它之所以被报出来，是因为这个检查把「读不了的文件」当成「没检查过」而不是「干净」——那正是本工单在防的同一条错误，一层之上。**不是我的领地，写 inbox。** |
| `worldgen/qc/run_qc.py:118` | `result["schema_valid"] = validate.returncode == 0` | **假阳。** 形状确实是「校验器的退出码 = 产物的性质」，但方向是安全的那一侧：校验器崩了 → 非零 → `schema_valid: False` → 报警。按判据（失败→**肯定**断言才算不安全）不成立。**这是这条检查唯一的、真实的假阳性。** |

#### NOTE 级 22 处：为什么它们只配当注解

22 处里 21 处是 `ok = proc.returncode == 0` 或 `"green": not failed` 这一族——
一个 gate 在读**自己刚跑的那条命令**回没回来。这**就是**正确写法。
其中三处（`cold-start-a0/certify/lean_check.py:97`、`cold-start-a2/…:119`、
`cold-start-a3/…:172`）还是 SURVEY 明确表扬过的五合取绿灯判据
（`returncode == 0` **且** 无 error **且** 无 `sorry` **且** 有 `axiom_reports`
**且** 全部零公理），`theory-compiler/tools/verify_c4.py` 三处同理。
把这些判红会立刻教会所有人无视这条检查。

剩下 1 处（`theoria-arm/inner/certify.py:247`，`report["ok"] = proc.returncode == 0`）
是真的——SURVEY-environment 乙组第 1 条：机器上没装 Lean 被 fire 成
`proof_failure`。**NOTE 级因此有一个已知假阴。** 我接受这个代价：为了捞它而把
`ok` 提到 ERROR 级，会连带把 21 处正确代码判红。

---

## 三、假阴（诚实的那一半）

**这条检查的召回很低，而且低得系统性。**

以本工单在 engine-rig 订正的 10 处站点为分母：**它只覆盖 1 处**（`p13:129`）。
另外 9 处它一处也抓不到，而且不是调参能解决的：

| 抓不到的站点 | 为什么抓不到 |
|---|---|
| `same_answer` / `agree` 的合取 | 参与的是 `plan_length` / `unsolvable`，不含任何工具状态词 |
| `if not result.success: return None` | 返回的是 `None` 不是布尔；缺陷在**调用方的 docstring 怎么读这个 `None`** |
| `len(indices) > 8` 的截断 | 是枚举上限改变了**分类**，语法上只是一个 `if` |
| IMPOSSIBLE 哨兵 | 缺陷在两个不同含义共用 `kind=None` |
| `Reachability` 产物缺预算 | 缺陷是**没写的字段**，AST 看不见「没有」 |
| `max_witnesses` 决定证书义务 | 是一个**展示**预算被读进判定，两个变量之间没有语法联系 |
| `guard_refused` 渲染成 `*refused*` | 缺陷在人看的 Markdown 措辞里 |

我试过把判据放宽到能覆盖其中几类（把 `return None`/`return False` 纳入、
把 `except` 块里的绑定纳入）。结果是全仓命中从 26 涨到 **200+**，
`engine-rig` 自己就有 30 多处，几乎全是正当代码。**那不是更好的检查，那是噪声。**

所以这条检查的诚实定位是：**它覆盖这一族里能从语法认出来的那一个子形状，
并且在文档里说清它不覆盖其余的。** 其余九处靠
`tests/test_tool_failure_is_not_truth.py` 的负样本按**行为**抓——那 18 条测试对
18 个变异体的击杀率是 18/18（见 `MUTATION.md`）。

---

## 四、我的建议：进不进 CI

**进 engine-rig 的 gate — 是。**
`monitor/gates.py` 把 engine-rig 解析成 `pytest`（这个目录没有 `verify.sh`），
所以我把它写成了一条测试（`test_the_standing_check_is_green_on_this_territory`）
而不是一个只在人想起来时才跑的脚本。**不是测试的检查等于不跑的检查。**
在本领地上它今天的成绩是：命中 0、假阳 0、对已知缺陷（修复前的 `p13:129`）命中 1。
维护成本约等于零，噪声为零。

**进全仓 CI — 现在不该。** 不是因为它不准（ERROR 级 75% 精确率是可以看的），
而是因为它今天会红，而红的三处里有两处不在任何人的当前工单里
（`cold-start-a0/certify/fd_unsat.py`、`release/checklist.py`），
一处在 monitor 自己家里（`reflex.py:147`）。
**一条从第一天起就红着的门禁，会在第二天被加进忽略列表。**
诚实的次序是：先把这三处作为 inbox 提案交给各自的轨道，**它们绿了之后**再把这条
检查提成全仓门禁。在那之前它应当作为**报告**（`python -m tools.check_solver_status <repo>`，
`--notes` 看第二级）由监控定期跑，而不是作为闸门。

**如果被要求现在就全仓上闸**，我的答复是：那就带着这三处已知红一起上，
并在忽略列表里**逐条写下红的理由和归属**——绝不是把判据调松到好看。
把 `hold`、`valid` 从词表里拿掉能让全仓立刻变绿，代价是这条检查再也抓不到
`fd_unsat.py` 那一类，也就是它唯一存在的理由。**那种绿是假的。**
