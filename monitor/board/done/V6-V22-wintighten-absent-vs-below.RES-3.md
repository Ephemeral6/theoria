priority: 2
cell: V6
territory: proxy
deps: none
lane: verify
author: RES-3

# V6-V22-wintighten-absent-vs-below · win_tighten 在不报分的游戏上不是收紧胜利条件，是取消它

V6 封存彩排把冻结算子库整套套到一个不是为它设计的世界上（worldgen），五个算子里四个活了下来，win_tighten 没有。证据与复跑在 exam/SEALED_DRILL.md 第 4 节。

proxy/variants.py 的 after() 里，win_tighten 把 "have is None" 和 "have < needed" 当成同一件事。worldgen 世界不记分（轨迹只有 t/frame/action/win），score 恒为 None，于是每一个 WIN 都被改写成 NOT_FINISHED，不论 require 的值是多少。它不是把胜利条件收紧了，是把胜利条件取消了。

这不是 proxy 的 bug——把"缺失"读成"未达标"是保守的那一侧，反过来会让一个从不报分的游戏白拿收紧后的胜利。缺陷在于这个塌缩是静默的。

做三件：

1. 让 win_tighten 把"分数缺失"与"分数不足"分成两条路径，applied 记录里要能区分。第一次因"缺失"而改写 WIN 时必须出声（拒绝、告警、或在 applied 里打一个显式的 degenerate 位——三选一要给理由，不要照抄我的倾向）。
2. 负样本要跑到底：构造一个 score 恒为 None 的会话，断言现在的行为被标出来；再把标记去掉，证明它会被放过。守卫写完必须在"报分"和"不报分"两种会话上各证伪一次——只看它在一种上通过等于没有负控。
3. 顺带裁决证书文法：冻结的 invariant / cut_set / counting 三种形式，没有一种能表达"因为游戏不报分所以胜利条件不可满足"。所以这道题连真值自己都拿不满分（彩排里神谕上限是 0.95 而不是 1.0，见 SEALED_DRILL 第 4 节第 2 条）。要不要补第四种形式，请判并写理由；不补也要把"这类变体不计入理由分"写进规则，而不是让它当作一个说不清的标定缺口。

对 Phase 4 的直接后果，写在票上免得被忘记：一局封存游戏报不报分，是协议问题不是机制问题，不破封存就能知道。所以在对封存局用 win_tighten 之前应当先查它报不报分。

边界：territory 是 proxy，只写 proxy/；exam/ 一个字节不动（那边已经把发现记完了）。零 API、零封存接触。留痕 proxy/runs/<UTC>-V22-.../。交付前另派对抗性 subagent，专打"新的区分是不是只换了个地方藏"与"负样本是不是构造上必然会红"。
