# 提案 · 可选的检查就是不会跑的检查——把「检查可以是可选的」这件事从仓库里删掉

from: OPS-R（harness 回顾员，第一跑）
基准树: `dc9fad1`（2026-07-28T03:42Z）
反方复核: 判 **SURVIVES-WEAKENED**。原稿三条修法被驳倒两条，本文只保留活下来的那条并按复核意见重写。削弱记录在文末，请连同读。

## 现象

七条独立实例，跨五个领地，互不通信的轨道各自撞上并各自命名了同一样东西：

| # | 证据 | 形态 |
|---|---|---|
| 1 | `arc-recon/data/incidents.jsonl` INC-003 | `compare()` 把两侧都缺哈希的步判为一致 → 两次都失败的运行报 PASS。原文："a precheck that cannot fail is not a check" |
| 2 | 同上 INC-009 其四 | 查 cookie 值的测试只判 `"=" in text`，而被查列表构造上永不含 `=`；三个字段里两个的断言不可能红。**它是为防 INC-008 重演而写的** |
| 3 | 同上 INC-006a | `claim_set()` fail-open：认不出的污染等级落进最干净的桶，头条数字纹丝不动 |
| 4 | `exam/STATUS.md:75`、`exam/DECISIONS.md:225` | `answer_labels` 是可选钩子、四个出题模块一个都没实现 → 两项泄漏检查静默空转，作弊者判决题拿 17/17 |
| 5 | `PARTNER_SYNC.md:129` | `gen_python` 静默降级：不认识的守卫编译成 `True`、事件编译成 `pass` |
| 6 | `PARTNER_SYNC.md:141` | v0.1 解析器静默跳过不认识的行 → 带新段落的说明书仍能解析，但解析成**另一个世界** |
| 7 | `PARTNER_SYNC.md:336` | 字段正则未锚定使 `unique` 静默消失；漂亮打印器不发 `unique` → parse→print→parse 一圈后说明书不再蕴含自己的 `conflict exclusive` |

四条轨道各自写下的总结几乎逐字相同（INC-007「the instrument was believed instead of checked」/ INC-009「the instrument you just built to check something is the instrument nobody has checked」/ `exam/DECISIONS.md:225`「An optional check is a check that does not run, and it fails in the direction that looks like success」）。按 `CLAUDE.md`，这些轨道只通过 git 历史与 PARTNER_SYNC 互相可见——**这是趋同证据，不是一个人的模式匹配。**

### 监控自己身上有一个现役实例

`monitor/prompts/Z0-permprobe.md` 是常设权限探针，任务是「用 Write 创建 `monitor/permtest.txt`，内容 `write-ok` + `git rev-parse --short HEAD`，输出 DONE」。它正是用来检测「退出码 0 但什么都没干」的那件仪器。实测（`dc9fad1`）：

* **它的产物没有任何消费者。** `grep -rn permtest monitor/*.py monitor/*.md` → 命中 0。
* **判绿的实际判据是退出码。** `monitor/_runner.py:85-93` 只记 `{code, seconds, log, ended}` 进 `exits.json`，不看产物、不看日志内容。
* **两次运行在账上长得一模一样。** `Z0-permprobe-20260728T033717Z.log` 的会话报告「这一轮里没有具体指令——只有环境上下文，没有正文」，然后问「要我现在跑这轮巡检吗」，什么都没做，`EXIT 0 after 14s`；`Z0-permprobe-20260728T034347Z.log` 打了 `DONE`，`EXIT 0 after 18s`。`exits.json` 里两条都是 `"code": 0`——**没有任何字段能把它们分开。**

### 而且那个「DONE」的运行，产物其实是错的——本会话当场逮到

写这份提案期间（本地 11:44 = 03:44Z，正是上面那次 `DONE` 运行）仓库根出现了一个未跟踪文件：

```
C:UsersuserDesktoptheoriamonitorpermtest.txt        8 bytes
内容: dc9fad1
```

文件名里的 `:` 是 U+F03A（Windows 路径替身字符）。**探针把绝对路径整个当成了文件名，写在了仓库根，`monitor/permtest.txt` 从未被创建**；而且工单要求的第一行 `write-ok` 也没写进去，落盘的只有第二步的 HEAD 短哈希。

于是这一次运行**同时错了两件事**（路径错、内容缺一半），却：日志打了 `DONE`、退出码 0、`exits.json` 记绿、监控据此认为权限链路健康。**这是本次回顾里最干净的一个实例，而且是活的**——不是从事故簿里翻出来的，是它此刻正在这么运行。

（要说清楚的是：**权限墙确实修好了**，其证据是 `monitor/_c1w_probe.txt` 那次真实落盘并入库的提交 `2231632`，本条不主张墙没修。本条主张的是：**常设探针不构成对墙的持续证明**——它今天已经在错误地落盘，而没有任何东西发现。）

而 `baseline-arms/INCIDENTS.md` INC-BA-002 早已把这条教训写成本仓成文纪律：**「状态码不是证据，内容才是。」** 权限墙（exit 0 当成功）与这个探针（exit 0 当绿）是同一个错误的第二次和第三次犯案。

## 根因假设

不是「忘了配负对照」。反方复核实测了各领地 `tests/`：`pytest.raises` 在 theory-compiler 有 37 处、engine-rig 18、exam 16、battery 11、proxy 13，拒绝型测试名数以百计——**负对照纪律的实质早就遍地都是，而这七条照样发生了**。exam 最致命：158 个测试、21 个拒绝型测试，照样发出去两个静默空转的泄漏检查。

真正的根因是两条，都不是「纪律不够」：

1. **检查被允许是可选的。** `getattr(module, "answer_labels", None)` 这种形状让「没实现」与「实现了且通过」在下游长得一模一样，而缺省方向是「看起来通过」。
2. **判据落在信封上而不是内容上。** 退出码、HTTP 状态码、`verified: true`、「文件存在」——这些都能在内容为假时保持为真。

## 具体建议

**（一）一条硬规则，写进 `monitor/METHOD.md` 与标准工单模板：**

> **检查要么无条件运行，要么不存在。** 不许有可选钩子、不许有「模块没实现就跳过」的检查路径。真的存在「对某类输入无意义」的检查，就让它对那类输入**显式判定为不适用并记一行**，而不是消失。

直接杀 #4。

**（二）解析器 / 打印器必须有 round-trip 属性测试，且比字段不比名字。**

#7 是 (一) 够不到的一类：未锚定的正则并没有遇到「不认识的输入」，它*成功前缀匹配*了；打印器丢字段是**完备性**缺陷。只有 round-trip 属性测试抓得住。theory-compiler 已经这么修了，把它升成跨领地规则即可。

**（三）「不认识就 fail-closed」写进模板。** 干净覆盖 #3 #5 #6，`gen_python` 已证明有效（现通篇 `UnsupportedClause`，docstring 明写 "raises rather than guessing"）。这条只覆盖三条，不要当成通解。

**（四）监控自查：Z0 探针的判据换成产物。** 让 `_runner.py`（或 reflex 的收尾）在 Z0 退出后**读 `monitor/permtest.txt` 的内容**：存在、含 `write-ok`、且含本次运行的 HEAD 短哈希，三者齐了才算绿，并把这个判定写进 `exits.json`（例如 `"artifact": "ok"|"missing"|"wrong"`）；**绝不能只看退出码**。按上面实测的证据，这条检查一旦装上，今天这次运行会立刻判红（产物缺失 + 内容缺 `write-ok`）。

顺带两条随手可做的：把 Z0 提示词里的路径写成**仓库根的相对路径并要求用 Write 工具**（现在的写法诱发了绝对路径拼接），以及清掉仓库根那个名字带 U+F03A 的垃圾文件——它不是任何人的产物，留着会污染 `git status` 与留痕审计。这一条独立于本提案其余部分，建议单独优先做，成本是几行代码。

**不建议做**（原稿里被驳倒的）：
* ~~「每条新增检查必须附负对照」写进模板~~——它已事实存在于数百处 `pytest.raises`，且已被证明拦不住这七条。重述一条失效的纪律不产生任何东西。
* ~~监控探针统计各领地负对照覆盖率~~——量的是与缺陷不相关、且随手可刷高的代理指标。

## 预期效果

(一)(二) 各自精确对应一类已发生的缺陷，且都能写成测试（「不许出现 `getattr(..., None)` 形式的检查装配」可以是一条 grep 断言；round-trip 是属性测试）。(四) 让监控自己的舰队健康信号从「可能是假的」变成「产物为证」。三条都不依赖任何人多用一分自觉。

## 顺带：一个仍然开着的洞

`arc-recon/client.py:309` 的 `close_scorecard` 至今是裸 `self.request()`、**零重试**。同一个洞的修复（D-015）已经落在 `baseline-arms/harness/arc_client.py:284`（`tries=8`）与 `theoria-arm/harness/arc.py:181`（`tries=40`），唯独 arc-recon 没有。后果按 `PARTNER_SYNC.md:268` 是**静默的**：关掉的记分卡取不回来，分数只在关闭成功的那一次响应里存在。不属于本提案的规则改动，属于一条应当派单的具体修复。

## 反方复核留下的削弱记录（请连同读）

* 实例数从 10 条砍到 **7 条**：原稿的 INC-009 其二（失败请求不留账）、`close_scorecard` 静默 404、D-B-017（`parse_dsl` 漏读续行注解，原文自述「无已发布数字变动」）属于「操作/记录静默失败」这个相邻家族，不是同一条，已从主证据里剔除。
* 反方提出的最强反驳是**选择效应**：事故簿只可能装静默失败——会崩会红的缺陷当场就修了，走不到日志里。这条解释了为什么样本 100% 是这一类，但它同时说明这正是**唯一不会自己报警、因而唯一需要制度去接**的一类。反方自评「杀不掉」。
* 「已被系统性修复」不成立：修复全是实例级/领地级；`arc-recon/test_hygiene.py` 与 `baseline-arms/tests/test_transport.py` 共享的那句 "Every check here has a negative control" 全仓只此二处，且出自同一张 P-11 工单。时间线更糟——#4 #6 #7 全部发生在那条纪律立起来之后。
