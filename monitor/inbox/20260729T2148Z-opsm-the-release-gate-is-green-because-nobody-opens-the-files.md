# release 闸门今天是绿的，因为它从不打开文件

from: OPS-M（合并裁判）· cycle 20
utc: 2026-07-29T21:48Z
re: `origin/agent/r3-release-classifier-defaults`（tip `e8d95c53`）、
    `origin/agent/r4-ruling-path`（tip `b5507b1f`）
状态: **要你裁两件**（都在合并裁判权限之上）；我一件都没做
对抗: 已派对抗组独立重算，**最重的一条是「向更可发布移动的 0 个」**；结论回来我追加在本文末尾

---

## 先撤回我自己的假设

我 21:35Z 在总线上说「这两条的红是 master 自己的、两个 NEEDS-HUMAN 都挂错了人」。
**错，撤回。** 控制实验：干净 master `4252f4ff`（恰好就是两个 flag 各自记的 `base`）上
release 闸门 **green、exit 0、6253 个文件、连 `?` 这个桶都不存在**；两条分支合上去才 RED。
**两个 flag 都挂对了人。**

我关于机理的判断是对的，且已逐条实证：`figure6_bill_shape.pdf` 头部就是
`%PDF-1.4\n%\xac\xdc`（0xac 正在第 10 字节）、点到的四局 `ar25 / g50t / sk48 / tn36`
全是**开发堆**、八个 `PAYLOAD_MARKERS` 在两个 PDF 的原始字节里一个都没有——
**这不是泄漏，是一个读不了自己输入的分类器**。但我把这个机理**归错了人**。

## 而它红的原因，正是 master 的绿是假的

master 的分类器靠**文件名最后一个点之后的字符**决定许可类，**从没打开过文件**。
r3 做的就是把这一步换成真读内容：调 `check_redlines.json_shaped()`——
**master 的 `check_redlines.py` 早就有这个函数，master 的 `enumerate.py` 从来没调过它**
（r3 自己的注释点出了这件事：「true of the module, false of the package」）。

同一棵 6253 文件的树、两个分类器、逐文件对比：

```
C -> B      8 个文件
C -> ?      3 个文件
向「更可发布」移动:  0 个
```

抽验两个 C→B，都带着字面的 ARC scorecard 响应体（`scorecard.card_id`、`runs[0].guid`、`state`）：

* `theoria-arm/runs/20260728T235841Z-leg01/run.json`
* `proxy/tests/fixtures/scorecard_corpus.json`

**它们今天正以 class C「releasable-flagged」上架。** 所以这里的选择不是「绿 vs 红」，
是**诚实的红 vs 假的绿**。三个渲染同一张图的文件被判成三个类（`.pdf`→`?`、`.svg`→C、`.png`→A），
判据是可解码性而不是内容——这就是那个假绿的破绽。

## 一个把两个 flag 合成一个的事实

**`r3` 的 tip 是 `r4` 的祖先**（`merge-base --is-ancestor` 为真，`e8d95c53` 是 r4 八个提交之一）。
一个原因被报了两次。r4 一进 master，`unmerged_branches()` 就会排除 r3、
S29 的 SWEEP-FLAGS 自动退掉它的 flag，不需要任何人手动清。

## 要你裁的两件

### 1. 千万不要单独合 r3

它装上收紧、**却没给 `?` 留任何出口**：除了改代码没有别的办法清一个 `?`。
后果是 release 通道**永久红着**，之后每一条碰 `release/` 的分支都堵在它后面。
这正是 OPS-A cycle 42 刚记下的那个形状——**「fail-closed 的闸门里有一个永远开不了」**，
只不过那次记的是 build 通道。别在 release 通道再造一个。

### 2. r4 加的就是那个出口，而它刻意 ship 了零条裁决

`RULINGS.jsonl` + 内容哈希键的人工裁决：只能 settle `?` 行，只能落进 A/B/C（**D 按设计不可达**），
保留原始证据，盖 `ruled_by` / `ruled_utc`。而 r4 **故意**提交了一个空的裁决表，
引的是 `CHARTER.md` 的 needs_human 路由：**「闸门一直红到有人签字为止，这是设计在工作，不是缺口。」**

后果很硬，必须说清楚：**ci_merge 闸的是合出来的那棵树，而那棵树按 r4 自己的设计就是红的
——所以 ci_merge 永远合不了 r4，只会每 15 分钟重新 flag 它一次。** 出路只有两条：

* **(a)** 由有权绕闸的人手工合 r4，并把这条红**记成 `release` 领地的常设条件**（不是分支的判决）；
* **(b)** 先签裁决让闸门变绿，再让 ci_merge 正常合。

**两条都在合并裁判权限之上，所以我停在这里。** 我作为合并裁判那一半的意见：
若要动，**动 r4、不要动 r3**；而等签字的每一分钟，master 那个假绿都还在替 8 个
带 API 响应体的文件说「无环境载荷」。**但绕一个 fail-closed 的释出闸门是不是可以被
「理由充分」绕过，这件事本身就是那道闸门存在的理由**，所以该由你而不是我来定，
对抗组也正在专打这一条。

## 给签字人的硬提醒：r4 提的两个 PDF 哈希已经过期

`RULINGS_PROPOSED.md` 引的是 merge-base `7852ef30` 时的
`ca805a75…` / `d4397dd8…`（257,076 / 257,901 字节）；
master 在 `a5f597dd` 重建过图，现在的 blob 是
`6d258de8…` / `e33eb18f…`（647,691 / 648,516 字节）。
**照抄那两行 JSON 签下去，会签到一个不存在的对象上。**
（r4 自己的 `stale_rulings()` 会把这件事说出来——机制是好的——但签之前请重算哈希。）
`pytest-baseline.txt` 的 `764359440f0d4444…` 未变、仍然有效。

## 我撞上的硬停，一条都没越

每一条能让这道闸门变绿的路，都会把那三个文件从 `?`/needs_human 推向 `C`/releasable-flagged：
(i) 签 `RULINGS.jsonl`；(ii) 给分类器加一条「非文本 + 只含开发堆 id + 原始字节无 payload marker → C」；
(iii) 把 `pytest-baseline.txt` 里三对 cp936 字节转成 UTF-8 让机器读得动。
**三条我都没执行，也不推荐其中任何一条。** (iii) judgement 最少（它让输入可读，而不是覆盖读者的判断），
但它落在 `theoria-arm` 别人的领地，而且**仍然改变一个许可结果**。

## 顺手两条不归我修的

1. **`release/verify.sh` 的 S23 复演步骤每跑一次都重写两个被跟踪文件**
   （`release/runs/20260728T234923Z-S23/{before,after}/contamination.planted.txt`），
   `gates.py` 管这叫 drift。它害过一次合并尝试被 `Please commit your changes` 挡下。
   不阻塞（ci_merge 是先合后跑闸门），但一个每跑一次就改自己输入的验证脚本值得一张单。
2. **谁要写「无 payload marker → C」这条规则，先看这个反例**：那份 pytest 日志的原始字节里
   **确实有** `scorecard`，但 45 行非空行里 0 行以 `{` 开头，命中全是 pytest 抓下来的源码文本
   （`game = "g50t-5849a774"`、`assert summary["scorecard"]["total_actions"] == 6`），
   真正的毛病只是注释里三对 cp936 字节。所以 r4 给它提的 class C 实质上站得住，
   **但那条朴素规则会把它判红**。

## 诊断组自报的未定项（我照抄，不替它抹平）

* **没验证「签了字闸门就会绿」**：r4 提交的 `runs/20260729T1835Z-R4/verify.with-demo-rulings.txt`
  声称绿，但复现它必须写裁决——撞硬停，没做。r4 的 `test_rulings.py`（746 行）在通过的 96 个测试里，
  那是间接证据，不是同一个断言。
* **8 个 C→B 只抽验了 2 个**。其余六个同族（三份 `theoria-arm/runs/*/run.json`、一份 `MANIFEST.json`、
  `proxy/runs/p9-shell-harden/scores_ar25_lifted.json`）未审。方向是安全的那一侧，
  但 class B 写着「needs written permission」，那是一句声称，不是一个摆手。
* **两个 figure6 PDF 是否与其 SVG 双胞胎同一条流水线出来的，没验**（r4 自己也标了这个弱点）。
* **为什么 r3 与 r4 被推成两条分支**（r4 严格包含 r3），不知道。若 r3 本来就打算先落地，
  上面的建议要改。
* 只跑了 `release` 闸门（两个 flag 指名的那个），没检查落地 r4 是否影响别的领地。

---

## 对抗组结论（待追加）

对抗组正在独立重算四条：①「向更可发布移动的 0 个」（唯一为落地背书的 claim，
含「文件整体从分类里消失」这种逐类 diff 看不见的放松）；②「master 的绿是假的」；
③「单独合 r3 会造出永开不了的闸门」；④「合 r4 并记录红」这条建议本身。
**推不翻我才会照上面动；推翻了我在本文追加更正。**
