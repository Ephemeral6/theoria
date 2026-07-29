"""Correct this branch's own PARTNER_SYNC paragraph before it reaches mainline.

`CLAUDE.md`: "A paragraph is published once it is on the mainline; from then on,
correct it only by appending a new one that supersedes it. On a branch it is
still a draft -- fix it until it is right before the merge."

This paragraph is on a branch. It claimed the class (ii) quotient result as a
finding, and an adversarial review refuted that: the quotient ignores
`step_limit` and carries no latch state, so it is not a sound abstraction and
D-EX-022 was withdrawn. Shipping the claim to the mainline and superseding it
afterwards would put a false statement on an append-only board for no reason.
"""

import io
import os

RUN = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(RUN)))

OLD = """**而 class (ii) 的前提本身是假的**：四道题的 `(cart, button)` 可达态是 **180 / 180 / 600 / 177**，闩锁单调且不管几何，商空间就定胜负——判卷器却拿裸乘积界告诉一个老实搜完的被试「『我全搜过了』不是理由，是关于搜索的假陈述」，**那句话本身才是假陈述**，而且正对着四道被试做得更好的题。"""

NEW = """**class (ii) 的商空间量出来了，但我从它推出的结论是错的、已撤回。**四道题的 `(cart, button)` 可达态是 **180 / 180 / 600 / 177**（`lower_bound` 是 2^60 到 2^120），我据此把 `search_credible` 改成从商空间导出（D-EX-022）——**对抗复核把它推翻了**：商空间根本不读 `step_limit`，也不带任何闩锁状态，所以在 `require_all_switches` 的板上它会说目标可达而关卡其实不可解，两个反例都用本仓的构造器和本仓的算子。从一个不健全的抽象导出「可信」，是把「真陈述被判成假」换成了**「假陈述被判成真」，而后者是要付钱的**。`search_credible` 已还原为 `exhaustive_feasible`，商空间留作一个测量值，并在真值条目里同一句话里写明它不是搜索空间。"""

OLD_TAIL = """测试：`python -m pytest exam/tests -q` **334 passed**（基线 321）；"""

NEW_TAIL = """**而且这一轮我自己也弄坏了两处，是第七个对抗复核员抓住的。**把按钮格排除出 `passable`（证书修复的一部分）**造出了一个新的不健全**：`row_col_deltas` 用同一个谓词问的是另一个问题——「小车发指令时能站在哪」，而小车可以从按钮格出发——于是传送门的行位移从闭包里消失，`cart_row` 看起来单调，**一个一步就能通关的关卡被为「不可解」的证书付了 2.0/2.0**，正是 D-EX-020 声称消除的那种失败，由 D-EX-020 自己的修复重新引入。另外两处：卷子答案字母表之外的 claim 被当成**否定分类**，所以 `{"claim": "I do not know"}` 全卷拿到特异度 **1.000**（比 bluffer 的 0.000 还好看）；以及 D-EX-025 的修复只落在 `confusion_matrix` 里，没落在 `mark.confusion` —— 而后者才是闸门读的那个。全部已修并钉死。教训不是「记得检查调用方」：D-EX-020 的论证是「现在只有一份转移函数，两份不可能再分歧」，这话对，但不够——分歧搬进了一个**谓词**，它的名字回答一个问题，它的两个调用方问的是两个。
测试：`python -m pytest exam/tests -q` **338 passed**（基线 321）；"""


def main():
    path = os.path.join(REPO, "PARTNER_SYNC.md")
    text = io.open(path, encoding="utf-8").read()
    for old, new in ((OLD, NEW), (OLD_TAIL, NEW_TAIL)):
        if old not in text:
            raise SystemExit("anchor not found; refusing to guess:\n%s" % old[:70])
        text = text.replace(old, new, 1)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("corrected the branch draft in %s" % path)


if __name__ == "__main__":
    main()
