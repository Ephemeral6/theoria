# 你点名的那个模式，又找到三处；其中一处**正典早就写好了、文件也 import 了，就是没用**

RES-3 / verify 赛道。回应监控 notice #1：
「凡是**某个工具的失败状态被当成了世界的性质**的地方，都值得你查一遍——
这个模式今晚已出现一次，多半不止一次。」

**你判断对了：不止一次。** 三路只读普查已回两路，扫约 100 处，判不安全 11 处。
下面三条我**逐行复核过**（标了怎么核的），其余在两份 SURVEY 报告里。
零 API、零网络、封存堆零接触、$0.00，**一个字节都没改**。

---

## U-1（最重，在放电，且已发布）：`engine-rig/tools/p13_fd_dividend.py:129`

```python
unsolvable=done.returncode == 12,
```

**裸退出码**——不看日志、不看档位、不看它自己已经读出来的 plan 文件。

而**同一个仓库的常量表**（`engines/fd_adapter/backends.py:74`）写的就是：

```python
FD_SEARCH_UNSOLVED_INCOMPLETE = 12
```

**最锋利的一点，我核过了**：正确的谓词**已经存在**，而且**这个文件已经 import 了它所在的模块**
（`p13_fd_dividend.py:53` 是 `from engines.fd_adapter import backends, search as fd_search`）。
那个谓词是 `backends.proves_unsolvable(tier, returncode, log)`，它的 docstring 逐字写着：

> "The whole unsolvability track hangs on this one bit, so it is decided **here
> rather than by string-matching at each call site**, and it is decided
> **conservatively** — the direction that can only ever refuse a real proof,
> never manufacture a false one."

**所以这不是"没人想过"，是"想过、写好了、放在正确的地方、然后在一个调用点绕开了"。**
一次属性访问的距离。

**它撑着什么**：`same_answer`（「死锁定理没有改变实例答案」那道守门）、
桩/FD 交叉复核的 `agree`、以及报告表与结论散文。
`runs/p13-fd-real/dividend.json` 里**已发布三行** `fd_exit_code: 12, fd_unsolvable: true`。

**减轻，要公道地说**：它只用完备的 `astar(blind())`，而且 BFS 桩在这三条上独立同意。
**所以方法不健全，而结论当前为真。** 修它便宜、且不会推翻任何已有结论——
但**在它被当成方法引用之前修**，比之后修便宜得多。

## U-2（在放电）：`worldgen/core/truth.py:279` —— 「查不了」默认成「成立」

```python
"invariants_all_hold": all(i.get("holds", True) for i in invariants),
```

纯散文不变量**根本没有 `holds` 键**，于是 `.get(..., True)` 把**「我没法验这条」**
静默变成**「这条成立」**。再经 `build.py:166` 升级成清单里的 `invariant_failures: []`。

**我独立数过**：`worldgen/out/**/ground_truth.json` 共 35 份，
其中 **13 份**带着没有 `holds` 键的不变量，却都报 `invariants_all_hold: true`。

**这一处的形状特别值得记**：**Markdown 渲染是诚实的**（人读的那份如实显示"未验证"），
**只有机器读的那个布尔在说谎**。而消费判决的是机器。
这与我今晚在封存审计上报的那条是同一个病的两个实例：
**散文诚实、布尔说谎，而只有布尔进得了退出码。**

`worldgen` 目前是我持有的领地（V16），但 V16 的范围是 `check_determinism`，
**我没有顺手改这一条**——那会让 V16 的验收线变成一件没人复核过的事。建议单开一件。

## U-3（潜伏）：`cold-start-a0/certify/fd_unsat.py` —— 就是我先前报的那条，但状态变了

普查员查出：**它的正则已经匹配不上上游改过的报错串了**，
所以 exit-12 那个分支**现在是死代码**；真正的主张走 `NoPlanExists`，
并配齐了零公理的 Lean 定理。**所以它比我先前报的更不紧急。**

但：**错误的常量仍在**，其**测试还把错映射写进了断言**（所以测试保护的是错的理解），
且 `release/MANIFEST.jsonl:290` 把它标为 releasable（sha256 逐位一致）。
**一条现在打不响的错枪，仍然是一条错枪**，而且它会随释出包发出去。

---

## 这对 C10 意味着什么（我认为这条改变了 C10 的形状）

C10 让我「**定**一条正典判据并写进 DECISIONS」。
**U-1 表明正典已经存在**——`backends.proves_unsolvable`，写得比我会写的更好
（三条路径、保守方向、明确拒绝在调用点做字符串匹配）。

**所以 C10 的第 (1) 件应该从「定正典」改成「采纳已有的正典」**：
把它提升为全仓唯一入口，并让所有调用点**引用**它而不是各自判退出码。
这比新写一条判据好，因为：新写会产生第二条正典，而**两条正典正是这条工单要治的病**。

C10 的第 (2)、(3) 件不变，而且 (2) 我已经做完了大半——两份 SURVEY 报告就是那次全仓 grep。

**领地裁决仍未回**，所以 `cold-start-a0/` 我一个字节没动；
上面 U-3 全部来自只读。

---

两份完整报告（含「免疫样本」——约 45 处**正当**读退出码的写法，
以及「做对了的样板」）在分支 `agent/e11-engine-crosscheck-deep`：
`engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/SURVEY-solver-status.md`
与 `SURVEY-empty-as-negative.md`。第三路（环境事实被读成语义）还在跑。

---

## 追记：第三路（环境事实被读成语义）回来了，扫约 240 处判据点，判不安全 **37 处**

**你说的「多半不止一次」，最终是 11 + 37。** 四条最重的，形状一条比一条难看：

### E-1 `theoria-arm/inner/plan.py:172` + `certify.py:196,206` —— **崩得越多，健康证明越干净**

生成的 `step` 有**文档保证是全函数**，它**唯一声明的异常本身就是缺陷信号**。
而那个异常被吞掉之后，后继被静默剪掉，然后同一份报告宣布
**「穷举了整个可达集」**、**「无一对 admitted two rules」**。

**所以每一次崩溃都让健康证明看起来更好。** 这是今晚所有发现里方向最坏的一条：
不是"漏报"，是**证据与结论反向耦合**。

### E-2 `a0-spike/pipeline/stages.py:260` —— 崩溃与真实发现**在产物里完全同形**

裸 `except Exception:` 包住 CEGIS，崩溃即改判**「这类迁移没有单个合取 guard」**，
并据此产出**已发表的 DNF 规则集**。读产物的人分不出"挖不到"与"挖崩了"。

### E-3 `release/check_redlines.py:207` —— 读不开的文件让**封存红线**报干净

不可解析 / 非 UTF-8 的被跟踪文件 → `return []` → 封存堆红线于是报
「NO record pairs a sealed id with payload」。
**而同一个包里 `enumerate.py:220` 对同样的情形返回 `None` 并判 needs_human。**
一个包里两种处理，正确的那种就在隔壁。

### E-4 `engine-rig/tools/p13_fd_dividend.py:129` —— 回旋镖

同上文 U-1。普查员的原话值得留着：**E11 用一把好尺子量出别的赛道把「我放弃了」
写成「我证明了」，同一把尺子放到自己的 `tools/` 上，量到了同一个 12。**

## 穷举触顶：一个金标准、两个反例

**金标准**（照抄这个形状）：`bench/ladder.py:74-82,226` —— 触顶时写
`proved_unsolvable: False` **加** `error: over budget`，**把上限正面记进产物**；
以及 E11 那一路 lp_potential 的复核（505312 态全穷举、**报告了"无一触预算"**）。

**反例二**：`engines/zero_space/zerospace.py:141` —— 特征数 >8 时枚举**静默退化**，
却仍然发 `scope: global`。

**反例一，与我已发布的一个数字有关，所以我逐行核了**：
`engines/lp_potential/potential.py:169-170` 是

```python
if not result.success:
    return None
```

`result.success` 为假**同时**覆盖 status 2（真不可行 = 确实没有线性 pagoda）、
status 1（迭代上限）、3（无界）、4（数值困难）——**全部塌成同一个 `None`**。
所以**引擎自己分不出「不存在」与「我算不动」**。

**但这不构成对我已发布数字的更正**，我要说清楚：E11 那一路的复核员
**自己去取了 HiGHS 的 status**，实测 639 例沉默里 **638 例是 status 2**，
另 1 例是硬编码 `bound=10` 挡的。**所以 29.2% 那个不完备率仍然成立**——
它成立是因为**复核员重新推导了引擎丢弃的那一位**，不是因为引擎保留了它。
**任何不重新推导的人，拿不到这个数。** 这一条正是本轮模式的教科书形态。

## 一条收回

普查员**收回了交叉复核的一句转述**：原报告称 `p13:419` 会发表假负结果，
复核认为不成立（`%d % None` 会当场崩）；真正落地的是 `:400` 那行表格的
`None -> None … yes`，已按后者记。**记在这里是因为收回本身也要留痕。**

## 汇总

三路普查共扫约 **340 处**判据点，判不安全 **48 处**，
另列约 45 处**正当**读退出码的写法与若干"做对了的样板"作为免疫对照
（一份只报阳性、不报阴性对照的普查，读者无法判断它的判据严不严）。
三份报告在 `engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/SURVEY-*.md`。
