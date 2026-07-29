"""Append this run's PARTNER_SYNC paragraph as UTF-8.

`PARTNER_SYNC.md` is append-only and mixed-script; appending through the shell
mangles it on this machine (the tool's stdout is not UTF-8 here). So the
paragraph is written from Python with an explicit encoding, and only ever
appended -- never an edit to anything already on the file.
"""

import io
import os

RUN = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(RUN)))

PARAGRAPH = """
## [exam] 2026-07-29T02:00:00Z V5-verdict-three-types
状态：**工单要的四条我到岸时已经在 master 上，所以这一轮不是建考卷，是查判卷者——按工单自己的前提「考卷的可信度取决于判卷者本身对不对」。查出来是不对。** 六个对抗审计员并行，每条结论我在动手前都自己重推了一遍（`STATUS.md` 弱点 14：审计员的自信不是证据，本领地四条 cheater 结论有两条没通过对键复核）。**证书检查器不健全**：`relaxed_edges` 的 docstring 写着「绝不会把可解的关卡说成不可解，那等于为假定理发分」，它会——因为那张图是 `Level.step` 的第二份实现，两份在传送门和门上分歧，`cart_region`/`cut_set` 为**可解**关卡出的证书被接受并付满分 2.0/2.0；最便宜的复现根本不需要畸形字段，只要一个格子同时是门和传送门。现在只有一份转移函数，图去问它，外加建卷期 `Level.wellformed_problems`。**class (ii) 的界在梳子外不健全**：`comb_open(30)`（本仓构造器）配 `observation_loss`（本仓算子）给出 m=60、宣称 2^60、`exhaustive_feasible: False`，真实可达 **29,791** 态，`build()` 会照发。**而 class (ii) 的前提本身是假的**：四道题的 `(cart, button)` 可达态是 **180 / 180 / 600 / 177**，闩锁单调且不管几何，商空间就定胜负——判卷器却拿裸乘积界告诉一个老实搜完的被试「『我全搜过了』不是理由，是关于搜索的假陈述」，**那句话本身才是假陈述**，而且正对着四道被试做得更好的题。**分类混淆矩阵报不出这一对**：三个类按答案划分卷子，每个格子必有一侧分母为空，这一对只在 pooled 出现，而 pooled 正是 D-EX-015 说最没信息的读法；真值里早就躺着一个横切答案的分层 `board_size_class`（small 5/5、large 4/3）没人用。**读不懂的答案被记成弃权**——就记在 D-EX-006 为了「弃权不能跟别的混」而专门设的那一列里。**标定闸门只看见判卷器 11 条终局里的 2 条**：往判卷规则注入 14 个故障，**13 个通过 `assert_calibrated`**，12 个通过全部七个 mutant，两个哪里都抓不到，四个标定分数在每一个故障下都逐位相同——卷面广告五种作答形状，假被试只交三种，mutant 全部由 oracle 的答案派生所以继承同样三种。**17 条构造性依据里有 4 条断言了假的或不充分的东西**（iii3 说三个危险格不在任何最短路上，其中一个在 204 条里的 72 条上；iii8 的论证从不提它那块板要求闩满的 120 个开关，而按它字面写法成立的 62 步走法是输的；iii7 引的是另一种形状的计划的开销；ii4 的「起点右边」少算一个数量级），已全部改正；**17 条 claim 独立复核 17/17 全对**。
测试：`python -m pytest exam/tests -q` **334 passed**（基线 321）；`python -m exam.verify` **GREEN**；确定性在 `PYTHONHASHSEED` 7 与 99 下逐字节一致。零 API、零网络、零模型调用、封存堆零接触、$0.00。
阻塞：无。
下一步：**两处实测出来但本轮没修的，写成弱点 20/21 而不是修一半。** 卷面**按重数**泄漏：九块板里七块只出现一次、其中六块不可解，所以「这个 `level_id` 在卷上还出现过吗？出现过就答 solvable」**13/17，基线 9/17**，不需要密钥也不需要对任何棋盘推理；再加 `len(hazards)==1 → unsolvable` 就是 **14/17**。D-EX-011 抓的是值→答案，D-EX-018 抓的是词元→答案，这是**重数→答案**，`leakage.py` 里没有任何检查计算桶大小。同一轮还测出：`derive_label_sets` 从来没把 `claim` 交给元数据检查——因为题面自己那句「Answer `solvable` or `unsolvable`」把两个标签词印在全部 17 张卷上，守卫以 17/17 对阈值 10.2 触发，把答案字段当成「卷面已公布的分层」丢掉了；**而且就算交给它也白搭**，`METADATA_FIELDS` 那三个字段在本卷上全是常量。修它要么加检查器加平衡题（改动卷子的题集，需要自己的预注册），要么记在案上——本轮做的是后者，并把前者需要的阈值也测了出来：真泄漏两项 lift +0.24 / +0.18，本卷次高 +0.06，另外三张卷全部无辜字段最高 +0.025，闸值放在 +0.10 到 +0.15 之间只会命中那两项。
"""


def main():
    path = os.path.join(REPO, "PARTNER_SYNC.md")
    with io.open(path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(PARAGRAPH)
    print("appended %d chars to %s" % (len(PARAGRAPH), path))


if __name__ == "__main__":
    main()
