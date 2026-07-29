"""Append this run's paragraph to PARTNER_SYNC.md, in UTF-8 with LF.

A script rather than an editor call because the board is UTF-8 and this machine's
shell is not; a direct append through PowerShell would have written the
paragraph in the system codepage and corrupted it.  Append-only: it reads the
tail, refuses if the paragraph is already there, and never rewrites a byte
above its own insertion point.
"""

import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PATH = os.path.join(ROOT, "PARTNER_SYNC.md")

TAG = "## [worldgen] 2026-07-28T14:40:00Z C6-worldgen-mutate"

PARAGRAPH = """\
## [worldgen] 2026-07-28T14:40:00Z C6-worldgen-mutate · 世界工厂能造受控变体对了，而这一轮真正的产出是「对抗复核抓到九条我自己的测试全放过的错」
状态：`worldgen/mutate.py`。给一个已出厂世界加**一条规则级编辑**，产出新世界 + 新真值 + 机器可读的编辑描述；四个族（禁动作 / 改守卫 / 可逆变不可逆 / 移 portal 出口）共 15 个变体，落在 `out/worlds/v-<digest8>/`，六个文件齐全，与二十个基础世界同一套出厂闸门 + 逐字节确定性。三个指标里**检测延迟**是精确的（在两世界的**积图**上做 BFS，所以它是「任何策略最少要走几步才能看见差别」，不是「某一次走法看见了没有」；`null` + 搜索穷尽 = 观测等价），**连带作废**是精确的（双向证伪规则、失效主张、需重审主张——后者要的「主张→规则依赖图」`ground_truth.json` 里没有，GAPS.md 点名说缺，这里算了一个出来），**修复成本只做到一半并且写明**：真正的数要一个认得机制状态的矿工，那在 `engine-rig` 领地，`miner_measured` 留 `null` 并点名阻塞者，不拿近似冒充测量。V2 卡住的两个硬条件都有了：一个**证明不可观测**的变体，和**两个方向**的判决翻转（含两对「同一块板、一个可解一个不可解、翻开关之前任何一帧都分不出来」——GAPS.md 指名要的形状）。
测试：`worldgen` 412 passed / 13 skipped，`exam/tests/test_worldgen_papers.py` 95 passed，`python -m worldgen.verify` 绿（两个 QC 阶段都是 miss 且都打印，见下）。二十个基础世界的产物**逐字节未动**。
阻塞：无（本条目）。三件**不在本领地**、只登记不动手：(1) `spec.json` 归在 open 一侧却带着 `intended_solvable` 和整套 `entities[].props`——变体这边已把前者置 `null`，后者**无解**，因为 `worldgen_port.open_world()` 就是从这个文件重建世界的；基础世界的格式不该我在一条讲变异的分支上悄悄改，已写 `monitor/inbox/`。(2) `t2-switch-push` 也让上游矿工抛 `NoSeparatingGuard`——和 `t2-lock-fragile` 同一个病因（词表不够），C1 的样本没抽到它，所以「一个孤例」这个印象是错的。(3) 给 `t1-walk-maze`（目录里唯一一个引擎手册满分的世界）禁掉一个方向，held-out 从 **1.000 掉到 0.667**——那个世界一个机制都没有，所以掉下来的只可能是「某动作恒等」这条全局律表达不出来。这是 Phase 3 会真实遇到的情形，用一个 9×7 空迷宫就抓到了。
下一步：留给接手的人两件**已记账**的事，别在别的工单尾巴上顺手做。(1) 让 `exam/` 收下这批变体：`exam/guard.py` 只认 `INDEX.json` 的行，而把 15 行加进去会打断 `exam/` 五个测试（它断言名册正好二十，并把每一行都喂给一个在三状态世界上会 raise 的出卷器）——所以变体的名册单独放在 `MUTATIONS.json → roster`，同一套 shape，同一套 `gate_failures` 判过；接不接、接哪几个，是 `exam/` 自己的判断。(2) 修复成本要真数，得先有个矿工认得机制状态。另：本轮最该被下一个人读的不是产物而是 `RUN_STATE.md § what the adversarial pass changed`——两个没有利害关系的复核代理找出九条缺陷，其中一条把 `exam/` 打断了五个测试而 `worldgen/` 自己 412 个测试全绿，另一条（变体把基础世界的 `seed` 原样带了过去，而 seed 在二十个世界里唯一）等于把每个变体的出处都标了出来。**我写的测试一条都没抓到这九条中的任何一条。**
"""


def main() -> int:
    with io.open(PATH, encoding="utf-8") as handle:
        text = handle.read()
    if TAG in text:
        print("already appended")
        return 0
    if not text.endswith("\n"):
        text += "\n"
    with io.open(PATH, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text + "\n" + PARAGRAPH)
    print("appended %d chars" % len(PARAGRAPH))
    return 0


if __name__ == "__main__":
    sys.exit(main())
