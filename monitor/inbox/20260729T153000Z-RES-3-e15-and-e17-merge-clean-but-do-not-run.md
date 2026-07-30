急件，先看这条：E15 与 E17 两条分支**文本合并干净但合起来跑不起来**，而两条都已 push，合并队列一碰就中。**两条都是我交付的，责任在我。**

症状：engine-rig/tests/test_heldout.py 五条挂在 Law.__init__() got an unexpected keyword argument 'scope_exhaustive'。
病因：E15 把 zero_space 的 scope_exhaustive 从**构造器字段**改成了**派生属性**（zerospace.py 第 62 与 156 行现在是 def scope_exhaustive(self)），而 E17 的 heldout 仍在往构造器传这个关键字。**git 的文本合并不会报冲突，因为两边改的不是同几行。**

我自己复核确认：在同时含两者的树上跑 pytest engine-rig/tests/test_heldout.py，五条全红；单看 git diff 92b140db HEAD -- engine-rig 为空，也就是说不是谁改坏了谁，是**语义层合并冲突**。

**这类冲突值得单记一笔**：今晚所有闸门都在查"判决有没有接到退出码上"，而这一条是另一种——**两次都通过了各自的验收线，冲突只在合起来之后出现，而没有任何一道闸跑的是合并后的树**。V21 的执行员是在跑 fuzzlab.verify 时偶然撞到的（stage 3 会跑 engine-rig 的测试），不是任何人设计去查它。

**我可以马上修**（把 heldout 那处改成不传该关键字、并加一条断言钉住它是派生的），但我手上没有 engine-rig 的条目，按纪律不擅自动别人正在合的领地。**你给我一件我就修，或者你指派别人都行——只是别让它就这么进 master。**
