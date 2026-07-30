# V6 · 封存彩排 —— 过程记录

条目 `V6-exam-on-sealed-dryrun`（p3，cell V4，territory `exam`，lane `verify`），RES-3。
分支 `agent/v6-exam-on-sealed-dryrun`，base `c1a60420`。结论与证据在
[`exam/SEALED_DRILL.md`](../../SEALED_DRILL.md)，机器可读的一份在 `DRILL.json`，
本文件只记过程与判断。

## 先查了「这件事是不是已经有人做过」

三路只读 subagent 扇出（exam 领地机器、封存纪律与护栏、worldgen 世界与算子库），
结论是彩排的**多数零件已经在盘上**：护栏、算子库、双哈希登记、sheet/key 分离、
`per_class_confusion` 的三类灵敏度特异度表，全都存在且有测试。

所以本件没有重建它们。**重建等于把已有的东西再抄一遍，还多出一份会漂移的副本。**
真正缺的一块是：现行 verdict 卷面**全部建在 `a2`** 上（`exam/papers/verdict.py:80`），
那是作者从第一天就完全理解的世界，而 Phase 4 的处境正相反。V6 的做法是把
worldgen 的世界当假封存局，于是能问出 a2 问不出的那个问题——
**构造性依据说的话，和穷举真值一致吗**。真封存局上这个问题永远无法回答。

## 一个设计判断：驱动真的算子库，不再写一遍

包裹层把 worldgen 的 `GridWorld` **向上适配**到 proxy 的 `{state, frame, score}`
协议，然后让**真的** `proxy.variants.VariantRuntime` 跑在上面，
`before`/`after` 的组合照抄 `proxy/env_proxy.py:374-402`。

理由：彩排若自己实现一遍包裹语义，彩排的是那份实现，冻结的那份仍然没被跑过，
第一次真用还是第一次。这条也决定了几个语义细节不由我裁量——
「被禁的命令不计步」「refusal 不走 `after`」「`win_tighten` 比的是 `body["score"]`」
都是冻结代码说的，不是我写的。§4 那条发现正是这样掉出来的。

## 自测抓到我自己三处缺陷

按顺序，都在 `SEALED_DRILL.md` §7 有完整写法：

1. **护栏证据把封存 id 写进了产物。** `SealedPileError` 的消息里带着它拒绝的那个 id，
   照抄进 evidence 就等于把封存局的名字写进被跟踪文件——护栏要防的那件事，
   从「证据」这扇门进来了。`test_no_sealed_id_is_written_into_the_run` 抓到。
2. **spec 路径把运行目录写进了真值文件。** 相对仓库记路径，运行写到仓库外时
   落成 `..\..\..\Temp\...`，于是字节可复现的产物依赖于它被写在哪。
   `test_the_run_is_byte_reproducible` 抓到。
3. **组合搜索不终止。** `VariantRuntime.commands` 无论有没有 `step_limit` 都在加，
   原样进节点键就让一个只有三个可达格的世界长出无穷图。

第 1 条是最该记住的一条：**任何记录「拒绝」的地方，都要把被拒的东西脱敏。**

## 一处我先写错、后改对的论证

`drill_wrapper` 的第一版 docstring 说 RESET 被排除是因为「它会让任何 step_limit
被免费绕过，于是所有变体都会变成可解」。**这是错的**：RESET 确实重置计数器，
但同时也把 agent 送回起点，所以比距离更短的预算并不能靠 RESET 绕过（测试里跑过）。
排除 RESET 的真正理由窄得多——判决题问的是**单局之内**是否可解。已改，
并在 docstring 里写明前一版论证错在哪。

## 已知的、不由本件承担的红

* `exam.leakage.check_paper` 今天在 20/20 worldgen 卷上都 raise（V7 §1 已归档，未修，
  成因是 `heldout_worldgen` 不在 `BUILDERS` 里）。本彩排自带探针自查，**不改 `BUILDERS`**，
  并把这条当作已知缺口写进 `SEALED_DRILL.md` §5，而不是静默绕过。
* `verdict.py::_emit_spec` 的并发写缺陷（已 xfail 钉住）：本彩排写自己的 spec 目录，
  不与 verdict 卷共享路径。
* `win_tighten` 的那条发现属于 `proxy/`，**不是本件的领地**，只报不改（§4 末尾）。

## 复跑

```bash
python -m exam.tools.sealed_drill                    # exit 0
python -m pytest exam/tests/test_sealed_drill.py -q  # 52 passed
python -m pytest exam/tests -q                       # 394 passed, 2 xfailed
```

字节可复现由 `test_the_run_is_byte_reproducible` 守：两次全新解释器、
`PYTHONHASHSEED` 7 与 99，产物逐字节相同。

## 对抗审稿（九个可复跑的攻击脚本，全部留在 `adversarial/`）

一条阻塞、五条 serious、五条 minor。**除一条外全部已修**，未修的那条转为限制写进
`SEALED_DRILL.md` §5。

阻塞的那条值得对着我自己写的话读一遍：`drill_certificates.py` 的 docstring 说
「两份实现同一套文法必然漂移，而漂移的那一份正是会放行不该放行的东西的那一份，
所以键集是从那个模块 import 的，不是在这里重述的」。**键集确实是 import 的。
检查是重写的**——而重写漏掉了 `rubrics_verdict.py:521-525`：每个 cut 格必须是
该变体真的宣告为致命的格。于是一张随便点两个分割格的 cut_set，被当成一个
**完全没有 observation_loss 的变体**的不可解证明收下了，四个探针里三个把
神谕十步就赢的世界证成了不可解。它还在本文件宣称「谁都拿不到」的那道题上买到了满分，
于是 0.95 的上限根本不是上限。

**本该拦住它的测试拦不住**：`test_the_reason_vocabulary_matches_the_frozen_rubric`
比的是五个字符串字面量，一点语义都没比。所以 `sealed_drill.py` 说
「两者被测试钉在一起，不会静默漂移」——**那句话当时是假的**。两处都已修。

顺带修掉的：题目顺序（原本 U,S,U,S… 交替，光凭 1-based 序号就能答对 10 题里的 9 题——
`exam/papers/verdict.py:96-106` 记过同一个信道，只是当时在 `points` 上）；
护栏只探了 21 个封存 id 里的 1 个（对抗方构造了一个只拒那一个、放行其余二十个
外加全部四个 dev 局的护栏，而报告照样 `fired: true`）；判卷器遇到敌意提交是
抛 `AttributeError`/`KeyError` 而不是打分（**一份畸形答卷会打断所有人的判卷**），
且没有见证长度上限，而冻结的 rubric 有 `MAX_WITNESS = 5000`；边界条件读
`spec.families` 这个自我声明而非 `GridWorld` 真正绑定的机制；被篡改的 cut 会让整个
run 以 traceback 死掉、连一份 RED 报告都写不出；两条 file:line 引用写错
（在两个以出处为立身之本的模块里）；以及卷面的 provenance 块把四个 dev 局 id 都印了出去。

**没修的那条，照实写进限制**：对抗方造了一个只读算子形状与 `board.start`/`board.goal`、
**从不碰 `board.grid`** 的考生，10 题的判断全对，得 0.80，
且灵敏度 1.0 / 特异度 1.0——与真值同一对数字。它的证书推理其实站得住
（曼哈顿下界确实不需要墙），**不能因为一个论证便宜就不给分**；不可接受的是另一半：
在这份卷子上，一张完美的三类混淆表分不出「对世界建了模」和「从卷面上读了两个整数」。
要关掉它得出「答案取决于墙」的题，那是改卷子的设计，不是一次彩排该做的事。

**它试了很久没能推翻的**（记下来，因为一个经得起真攻击的结论比没人攻过的值钱）：
神谕是穷举的、计数折叠是精确的——一个与 `solve()` 不共享任何代码的独立判定器，
每条序列都从 t=0 重放、拿完整 runtime 状态当访问键，在 **33 个用例 × 4 个计数上限上
0 处不一致**，其中包括同时多个 `step_limit`、`limit: 0`、起点格与终点格上的 loss、
以及 `value: 0` 的 `win_tighten`；`OracleTruncated` 严格早于任何错误答案触发；
RESET 确实不是漏洞；run 写出的 16 个文件里没有任何封存 id 或短名；
每个报出的数字都能从 `DRILL.json` 与 `truth.json` 精确重算；
`apply_command` 与 `env_proxy.py:373-406` 逐行相符。
