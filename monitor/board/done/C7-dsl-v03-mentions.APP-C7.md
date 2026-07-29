priority: 1
cell: C1
territory: theory-compiler
deps: none

# C7 · DSL v0.3：`mentions` 从未被定义，而三种读法互不等价

a0-spike 用 376 个用例把契约的一个洞钉死了（X-1，见 `a0-spike/THEORIZE_LOG.md` 表达力台账）：
v0.2 的 `frame persist` 说「未被提及的对象保持不变」，却**从未定义「提及」指什么**。三种读法：
按规则文本读会让后继态未定；按事件签名读**实测错 376 个用例**；只有按编译效果读与世界一致。
另一条 X-5：「箱子不站在墙上」在 v1 守卫语言里不可表达，`free(Box.pos)` 编译成恒假的
`_free(state, state.box)`，手册在 52 个态上错。

做四件：(1) 给 `mentions` 一个**定义**并升 v0.3（编译效果读法为正典，理由写进契约）；
(2) 给事件签名一个能写全所写对象的形式（`slid(Box,dir)` 同时写 Box 与 Player）；
(3) 修 `free(...)` 对非位置参数的编译；(4) 四份 DSL（peg / cold-start-a0 / a0-spike /
cold-start-a2）全部过新编译链，376 与 52 两个数字复现为 0。契约升版只做加法，v0.2 校验器保留。
