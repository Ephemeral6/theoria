# E16 · 算对了、发布了，然后不拿它把关

工人 W-1650 · 分支 `agent/e16-verdict-must-gate` · base `31bea46` · 2026-07-29T02:00Z
领地 `engine-rig` · 服务论文 WP1 / WP9 · 零 API、零网络、封存堆零接触、$0.00

机器可读的账在 `MANIFEST.json`；这里是叙述。

---

## 0. 开工即撞的事故：磁盘满，且它不长得像磁盘满

建完 worktree 跑基线 `pytest`，**退出码 0，输出只有一串点**，没有汇总行。看起来是绿的。
第二次跑才把真相抛出来：

> **更正（对抗复核指出，我复验属实）：「没有汇总行」不是磁盘满的征兆。**
> `pytest.ini` 里 `addopts = -q`，我再传一个 `-q` 就成了 `-qq`，而 `-qq` 本来就
> 不打汇总行——在健康磁盘上可稳定复现。所以当时那份「看起来是绿的」输出，
> **缺汇总行这件事是我自己的命令行造成的，不是事故的签名**。
> 事故本身（ENOSPC、fixture 被截成 0 字节）是真的；**由它推出的那条诊断法则是假的**，
> 而我一度把它当经验写进了 inbox。留在这里，因为「一次真事故 + 一条错推论」
> 正是本工单要防的形状：**结论算出来了，凭据却没人复核。**

```
OSError: [Errno 28] No space left on device      # df: 474G 474G 3.2M 100%
```

代价不止是跑不动测试。那次半途而废的写入把**被跟踪的** fixture
`fixtures/data/sokoban_domain.pddl` **截成了 0 字节**，于是
`test_deadlock_carver.py` 整个文件在 `parse_domain` 上炸开——一个看起来像是我改坏了
代码的失败，实际上是磁盘。

处理：`git checkout` 复原，`python -m fixtures.generate_all` 确认重生成后字节一致，
**然后才重新建立基线**。第一次那个「绿」在记录里作废。

清理只做了无风险的一档：`.worktrees/` 下 1475 个 `__pycache__` / `.pytest_cache`
（gitignore、纯生成物）加 `git worktree prune`，3.2 MB → 8.8 GB。
**没有动任何人的 worktree 源码**——那里可能有在飞的活，删了不可逆。
`.worktrees/` 约 100 个目录共 10G 的清理需要监控带清单裁决，已发 inbox 急件。

这件事本身就是本工单主题的一个实例：**退出码 0 是一个「判决」，而它当时是假的。**

---

## 1. `lp_potential`：头条字段是个字面量

`potential.py:296`（工单写的 `:255` 已漂）：

```python
"admissible": True,          # 不是算出来的
```

真正的可采纳性检查 `admissibility_report`（h 对真实最短路）**算了**，
由调用方在 `__init__.py:32` **事后**挂进同一份 payload 的 `admissibility_check`。
两者不可能一致或不一致——其中一个是常数。

**改法**：`as_json(admissibility_check=None)` 把检查**收进来**，头条与证据
由同一个表达式产出，另附 `admissible_basis` 交代凭据：

```
admissible = certificate.holds  AND  (没有一行 admissible=False)
```

证明侧取 `certificate.holds` 是有道理的，不是保守起见：界
`h = min_g ceil((pot(s) - pot(g)) / M)` 的论证**就是** `inv_closed` 加上 M 的定义。
经验侧只能**减分**——抽样能证伪，不能证成。`conditions` 为空（压根没验）也判假。

### 负样本：不是造的，是真的

工单只要求「`holds=False` 必须让该字段为假」。这一条容易满足，也确实做了两个。
但更值得记的是第三个——它一开始是个失败的尝试：

先试「把 M 缩小 8 倍」，报告**没有出现反例**。查下去发现 peg4 上
`admissibility_report` 覆盖的三个有限距离状态**势能全部等于目标势能**，于是
`required = 0`、`h ≡ 0`——**这份经验检查在这个 fixture 上近乎恒真。**

接着穷举 [-4,4] 的整数权重找「holds=True 但经验不可采纳」的向量：**0 个**。
这不是失败，是结果：**对完整 move 表，证书成立就蕴含启发式可采纳。**

真正的洞在别处。`check_exactly` 迭代的是**生产者递给它的那张 move 表**。于是：

| | |
|---|---|
| 权重 | `[-4, 0, -4, -4]` |
| move 表 | peg4 四条里的**三条**，漏掉 `jump(3,2,1)` |
| 三个条件 | `inv_init` ✓ `inv_closed` ✓ `goal_break` ✓ —— 精确有理数 |
| 启发式说 | `h = inf` 于状态 `0011` 与 `1101` |
| 真实距离 | **1 步** 与 **2 步** |

`h = inf` 是一条 per-state **不可达**断言。改之前，这份 payload 会带着
`"admissible": true` 发布这条假断言。**soundness 住在枚举的完整性里，不在算术里**
——这正好是第 3 项要写的 D-035 site 1，于是负样本和边界叙述是同一个东西。

---

## 2. `deadlock_carver`：carve → report → emit，中间没有 `if`

`PruningReport.same_answer` 问的是唯一能在操作上证伪定理的问题——*剪枝有没有改变
这个实例的答案*。它被算出来、序列化成 `plan_length_unchanged`，
**然后和它刚证伪的那批定理并排发布**。读者拿到一条定理和一份说它不可靠的报告，
摆在一起，没有谁压过谁。

**改法**：`candidates()` 先读判决再建行。

| 情形 | `invariant` 行 | `plan` 行 |
|---|---|---|
| 没跑报告 | 照发 | 无 `refuted` 键 |
| 判决通过 | 照发 | 无 `refuted` 键 |
| 被证伪，`"withhold"`（默认） | **一行不发** | `refuted` / `invariants_withheld` / `on_refutation` |
| 被证伪，`"mark"` | 照发，每行带 `refuted`+`refutation` | 同上，`invariants_withheld: 0` |

三个设计选择值得记：

* **失效标记是字段，不是散文。** 要遵守它的下游是 `bench/dividend.py:868`，它读字段。
  写在 `rendering` 字符串里的警告不是闸，是对读者的期望。
* **压下去的要计数。** 只是不发的话，被证伪的一轮和「什么都没刻出来」的一轮
  长得一模一样，而「无事可报」是错误的读法。
* **`refuted` 缺席，而不是 `false`**，当没有取过判决时。「没人问」「问了通过」
  「问了不过」是三种状态。搜索没跑完时 `UnfinishedComparison` 直接抛出
  `candidates()`——照常压制等于凭一次没答案的搜索给定理记一次不可靠，
  照常发布等于凭同一个没答案清白。

### 一个必须写下来的自我限制

**这道闸是单向的。** `same_answer` 为假证伪；为真**什么也不证**——
一条只切到「同长度的另一条最优解」上的不可靠定理，`solved` 和 `length` 都不动，
照样过闸。所以它**压制它抓到的，不对它放过的作任何声明**。
把过闸写成清白，就是在上一层重演本工单要修的缺陷。已写进 D-034 与 README。

### 顺带查实的一件事

`tools/run_all.py:152` **本来就**查 `report.same_answer` 并 `raise`。
但它查在 `dc.run(...)` 已经把被证伪的定理写进磁盘之后。
**写之后的闸不是闸。**另：`deadlock_carver` 全仓只有一个 `emit(` 点，
且经过 `candidates()`，所以候选流这条路是关严了的。

---

## 3. 「验了一道」和「用独立的东西验了一道」

RES-3 的 §4 标题写「六处」，底下**只列了三条**，并称细节「报告里分开列了」——
而它所引的 `SURVEY-success-as-truth.md` 在那个 run 目录下**不存在**。
缺的三处是本轮独立找的。六处全部成表进 `DECISIONS.md` **D-035**，每行点名共享的前提：

| 站点 | 校验器没 import | 但共享 |
|---|---|---|
| `lp_potential` `check_exactly` | LP | `Certificate.moves` |
| `ic3_pdr` `check.py` | `pdr` | `System.transitions` |
| `interop/certificate_export.verify` | — | 生产者自己列的 witness |
| `zero_space` `verify()` | 消元 | 拟合所用的同一条轨迹 |
| `deadlock_carver` 裁判 + `same_answer` | carver 的证明 | `ground_actions`/`strip_static` |
| `fd_adapter` `validate_plan` | `search` | `ground_actions` |

**六处没有一处是「漏了检查」。** 每一处都有校验器，且多数是刻意不 import 生产者
建起来的——那是真功夫，也真的买到了东西。买不到的是周围散文声称的那个东西。
对应六段措辞就地改掉（不是加注），最钝的一处：

> `interop/README.md`：「`verify()` recomputes **everything from the document's own
> contents**」——「文档自己的内容」正是缺陷本身，那些内容由生产者挑选。

`zero_space` 的最锋利：按 GF(2) 构造，观测差分零空间里的向量在观测轨迹上**恒定
是定义使然**，那句 `AssertionError` 几乎不可能触发。它独立于**消元**，不独立于**证据**。

### 这一项反过来削弱了工单自己的开场白

E16 开篇的好消息里，**无条件调用那一半是真的，我复验了**：
`fd_adapter/__init__.py:140` 确实无条件调 `validate_plan()`，三档全过含真 FD。

**「结构保证」那一半弱一个函数。** `validate.py` 与 `search.py` 共享
`pddl.ground_actions`——而它（`pddl.py:304`）**不是 parser**：它在实例化时做静态
前条件过滤、决定哪些实例「有可能触发」，就是后继生成层。所以搜索器的
frontier / 排序 / 去重出错抓得住，**grounder 里少一条 delete effect 两边同时错**。
原 docstring 那句

> `The only code shared with the planner is the parser.`

**是假的**，已改。更刺的是它举的例子（"a forgotten delete effect, say"）
正好是它抓不住的那一类。引用这条作正面结论的下游（WP1/WP9）需按此边界重述。

**不主张的部分**：这六处不是「把每个校验器都做成独立的」就该修的缺陷——
对多数站点那等于把引擎写两遍。`recheck/` 是全仓唯一付全价的地方
（从规则集 grounding、拒收自带 `transitions` 的证书、不 import `engines/`、
外加一个共享零前提的可达性 BFS 作第二意见）。**决定是让别处都说清自己是什么**，
好让 `recheck/` 那份更强的保证保持可辨认。

---

## 4. 验收

```
python -m pytest                                    492 passed, 27 skipped, 0 failed
python runs/20260729T020000Z-E16-verdict-must-gate/verify.py    29/29 ALL CHECKS PASS
python -m tools.run_all --out artifacts/candidates.jsonl --deterministic --force
                                                    44 行不变，仅 heuristic 一行有差异
python -m fixtures.generate_all                     fixtures/ 字节不变
```

`verify.py` 与测试套件重叠是故意的：本工单的缺陷就是判决活在没人读的地方，
一个「我跑的时候是绿的」的 run 目录是同一个形状。它另外还断言四段过度措辞
确实从文件里消失了——措辞修复同样需要一道能失败的检查。

产物变动只有 `artifacts/candidates.jsonl` 一行（heuristic 行增 `admissible_basis`，
内容寻址的 `id` 随之改变），用文档命令重生成，**未手改**。

## 5. 未做 / 已知边界

* 本闸单向，见上；`with_report=False` 不是绕过，是**没有判决**，按缺席记录。
* `admissibility_report` 只遍历有限 `distance_to_goal` 的状态——对「真实距离无穷
  而 h 给出有限界」的方向结构上看不见。本轮没扩，记在此。
* **`cold-start-a0/` 的两条同族：登记的内容是「查不到」。** RES-3 把它们列在
  「三条我不确定的」里（**非确诊**），细节推给 `agent/e11-engine-crosscheck-deep`
  分支上的 `SURVEY-success-as-truth.md`。查证：**该远端分支不存在**
  （`git branch -r | grep e11` 为 0），已并入 master 的同名 run 目录里
  （`runs/20260729T000000Z-E11-engine-crosscheck-deep/`）**也没有这个文件**——
  只有 `CROSSCHECK.md`、两份 `ADVERSARIAL-*.md`、`MANIFEST.json`、`partials/`。
  于是对 `cold-start-a0/` 自有源码（排除 `.toolchain/` 里 vendored 的 Fast Downward
  与 mingw python）做只读扫描：**没有一处「判决字面量」形状**。
  结论：这两条要么是别的形状，要么已不成立；**不能从任何可达产物里认定**，
  需由拥有该目录的 theory-compiler 轨道认领。engine-rig 未动手，也不越界断言。
* RES-3 的行号漂移与「六处实为三处」已另发 inbox
  `20260729T024000Z-W-1650-e16-three-corrections-to-the-ticket.md`。
