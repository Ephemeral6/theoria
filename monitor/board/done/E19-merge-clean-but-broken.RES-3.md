priority: 1
cell: E19
territory: engine-rig
deps: none
lane: verify
author: RES-3

# E19-merge-clean-but-broken · E15 与 E17 合并干净但跑不起来——没有一道闸跑的是合并后的树

E15 与 E17 文本合并干净但合起来跑不起来，两条都已 push，合并队列一碰就中。RES-3 自供并自修（两条都是我交付的）。

症状：engine-rig/tests/test_heldout.py 五条挂在 Law.__init__() got an unexpected keyword argument 'scope_exhaustive'。
病因：E15 把 zero_space 的 scope_exhaustive 从构造器字段改成派生属性（zerospace.py:61-63，return not self.truncated_cells），而 E17 的 heldout/zero_space_heldout.py:82 仍在往构造器传 scope_exhaustive=not truncated。git 文本合并不报冲突，因为两边改的不是同几行。

修法（语义精确，不是打补丁）：local_laws 的第二个返回值就是**被截断的 cell 下标表**（zerospace.py:232-233 签名 Tuple[List[int], List[int]]），所以把那一行改成 truncated_cells=tuple(truncated) 即可——派生属性算出的 scope_exhaustive 与原来逐位相同，而且额外保留了"是哪几个 cell 被截断"这个信息（严格更多，不是更少）。全仓只有这一处调用点。

另加一条钉子：断言 scope_exhaustive 是派生的（不能再被构造器覆盖），否则下一次同样的改动还会静默复发。

这件值得单记的是它的形状：今晚所有闸门查的都是"判决有没有接到退出码上"，而这一条是另一种——两个条目**各自都通过了自己的验收线**，冲突只在合并后出现，而**没有任何一道闸跑的是合并后的树**。它是 V21 的执行员跑 fuzzlab.verify（stage 3 会跑 engine-rig 的测试）时偶然撞到的，不是任何人设计去查它。**建议后续单开一件：给合并队列加一道"合并后跑一次全测"的闸**，本件不顺手做（那是 CI 领地）。

验收线：在同时含 E15 与 E17 的树上 pytest engine-rig 全绿；改动只碰 engine-rig/heldout/；留痕 engine-rig/runs/<UTC>-E19-merge-clean-but-broken/。

