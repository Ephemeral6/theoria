priority: 2
cell: C15
territory: theory-compiler
deps: none
spend: none

# C15-the-unnameable-cell-has-no-home-in-the-dsl · 臂能拿住、但编译不了的那条真话

GAP R2-2。R2 之前这是假想的，R2 让它够得着了，所以它现在上板。

R2 的反事实 replay 里，`edge_advance` 与 `world_inert_plus_edge` 是这条臂里
**第一批可能对一个棋盘格说对话**的假设，而且它们说中了很多：38 条被追回的
脱靶答案里，`edge_advance_1` 中 16、`edge_advance_2` 中 16、`edge_advance`
中 14、`world_inert_plus_edge_1` 中 5
（`runs/20260801T0900Z-R2-frontier-by-generation/REPLAY.json`）。

问题是：**其中一条通过探针存活下来，臂就学到了一件在 DSL 里没有住处的真话。**
manual 无法对一个自己没有实例的格子陈述规则；`arc-instances: all` 也无法在一个
「棋盘能解释」的格子上安一个实例。r3 自己的 manual 把这一点写成了一条命名判决——
`i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed`
（`runs/20260731T1430Z-A3-level2-carried-r3/`）——它逐条否掉了绕路的办法。
臂在这里付的是一条「每命令一像素」的账单。

这是一次**语法变更**，属于 `theory-compiler`。R2 只是把它从「以后再说」变成
「下一轮就会撞上」，并且明说不越界：任何关于分割器对环形 mover 失明的 ask
走 `monitor/inbox/`，不进 `engine-rig` 的补丁。

要的是一个**裁决**，两条出路任选，但必须选一条并写下理由：

* **(a) 扩语法**——给出一种能对「从未变过的格子」说话的形式（不是给它硬安一个
  实例），附一个把 `edge_advance` 编译过去的例子，四种共导出形式都要过；
* **(b) 明确拒绝**——写下为什么这条真话不该进 manual，以及臂确认了这类假设之后
  该把它放在哪（探针台账？表达力台账？`Theoria.md:345`？）。写下来的拒绝
  是一条契约，沉默不是。

验收：裁决落进 `CONTRACTS/` 的语法文件（新版本或现版本的附注，按该轨道自己的
版本纪律来），并在 `theoria-arm` 的 GAPS R2-2 处留一条反向指针。

负样本：**必须先证明今天真的说不出来。** 一条测试，把 `edge_advance` 形状的
规则喂给现语法，断言它编译失败**并给出那个失败理由**——「无法命名」要是演示
出来的，不是断言出来的。走 (a) 的话，同一条测试在新语法下翻绿；走 (b) 的话，
这条测试就是那份拒绝的执行形式，永久留着。
