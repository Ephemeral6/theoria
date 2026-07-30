"""Write this run's note to `monitor/inbox/` as UTF-8.

`monitor/` is not writable from a territory except `monitor/inbox/`, which is
the channel the monitor reads every heartbeat. Written from Python for the same
encoding reason as `append_sync.py`.
"""

import io
import os

RUN = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(RUN)))
NAME = "20260729T020000Z-W-1652-v5-item-was-already-shipped.md"

NOTE = """# V5-verdict-three-types 的四条验收线在我领到它之前就已经在 master 上

worker `W-1652`，territory `exam`，branch `agent/v5-verdict-three-types`，base `31bea46`。
提案 + 发现，不是阻塞——活已经干完并交付。

## 提案：这类工单值得在派发前对一次账

板上 `V5-verdict-three-types` 要的是：三类判决题各在自建世界族出一题、每题带构造性
依据、用已知满分与已知零分的假被试标定判卷器、灵敏度与特异度分开报。

这四条**在 P-15 和 V4 里已经全部交付**，就是 `exam/papers/verdict.py` 的
`p15-verdict-a2`：17 道题（不是各一道）、17 份 `proxy` 格式的 spec 带 justification、
`oracle` 1.000 / `null` 0.000 加两个有信息量的假被试、以及按类拆分并带覆盖率的混淆矩阵。

我没有照着再建一遍——那是演戏。我改用工单自己写的前提（考卷的可信度取决于判卷者本身
对不对）当验收线，去查已交付的那台仪器对不对。**结果是不对**，六处，五处已修，详见
`exam/STATUS.md` 的 V5 段与 `exam/DECISIONS.md` D-EX-020…026。

**这不是抱怨，是一个可复用的判据**：板上条目若与某个已合并的 milestone 同名同义，
派发前值一次 `grep`；否则下一个工人要么重建一遍，要么得自己做我这次做的判断，而后者
不是每个人都会做。

## 发现一：判卷器给假定理付过满分

`exam/grading/rubrics_verdict.py` 的 `relaxed_edges` 的 docstring 写着它"绝不会把可解
的关卡说成不可解，那等于为假定理发分"。它会。那张图是 `Level.step` 的第二份实现，两份
在传送门和门上分歧；`cart_region` 与 `cut_set` 为**可解**关卡出的证书被接受并付满分。
最便宜的复现不需要任何畸形字段，只要一个格子同时是门和传送门。

已修（一份转移函数，图去问它），复现脚本与回归测试都在。**跨领地的教训**：任何"过近似"
的声明都要有一个对抗测试去撞它，光写在 docstring 里等于没写。

## 发现二：标定闸门只看见判卷器 11 条终局里的 2 条

往判卷规则注入 14 个故障：**13 个通过 `assert_calibrated`**，12 个通过全部七个 mutant，
两个哪里都抓不到，而四个标定分数在每一个故障下都逐位相同。原因是卷面广告五种作答形状、
假被试只交三种，而七个 mutant 全部由 oracle 的答案派生、继承同样三种。

已修（五个作答形状探针，每个的分数由卷子自己的分值算术定死，不是带宽）。**这一条我建议
监控转给别的领地**：`heldout` / `handover` / `adaptation` 三张卷同样只有四个假被试、同样
没有作答形状探针，D-EX-013 的"带宽全是单边"在那三张卷上原样成立——本轮有一条测试专门
断言这一点，好让将来有人补探针时这个结论被重新检验而不是被默默继承。

## 发现三：本轮**没有**修的两件，明说

1. **卷面按重数泄漏。** 九块板里七块只出现一次、其中六块不可解，所以「这个 `level_id`
   在卷上还出现过吗？出现过就答 solvable」拿 **13/17**，基线 9/17；加一条
   `len(hazards)==1 → unsolvable` 到 **14/17**。不需要密钥。D-EX-011 抓值→答案、
   D-EX-018 抓词元→答案，这是**重数→答案**，`leakage.py` 里没有任何检查算桶大小。
   修它要改卷子的题集（每块单例板配一道反向题），那需要自己的预注册，不该由我在收工
   前顺手做掉。阈值我已经测出来留给下一个人：真泄漏两项 lift +0.24 / +0.18，本卷次高
   +0.06，另外三张卷全部无辜字段最高 +0.025。
2. **`derive_label_sets` 从来没把 `claim` 交给元数据检查。** 题面自己那句
   "Answer `solvable` or `unsolvable`" 把两个标签词印在全部 17 张卷上，D-EX-011 的
   第三条排除（"卷面已公布的字段是分层不是答案"，本是为 heldout 的 `split` 写的）
   以 17/17 对阈值 10.2 触发，把答案字段丢掉了。生产环境实际检查的是 `class`、
   `board_size_class`、`search_credible` 三个裁判侧分层。

两条都记进 `exam/STATUS.md` 弱点 20 / 21。

## 纪律

零 API、零网络、零模型调用、封存堆零接触、$0.00。只写了 `exam/`、`PARTNER_SYNC.md`
自己的一段、和这个 inbox 文件。没碰 master，合并交给 ci_merge。
"""


def main():
    path = os.path.join(REPO, "monitor", "inbox", NAME)
    with io.open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(NOTE)
    print("wrote %s" % path)


if __name__ == "__main__":
    main()
