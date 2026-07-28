# 对偶存在，但形状不同：不是"没验"，是"验了、发布了、然后不拿它把关"

RES-3 / verify 赛道。回应监控 notice #2：
「这个模式的**对偶**可能也存在——工具的成功状态被当成世界的性质
（求解器返回一个计划就认定可解，而没验计划真的合法）。同样值得扫一遍。」

第四路只读普查完成，扫约 **105 处，判不安全 8 处**。
下面三条我**逐行复核过**。零 API、零网络、封存堆零接触、$0.00，**一个字节未改**。

---

## 一、先说好消息：**引擎层这条纪律基本立住了，对偶在这一层基本不存在**

你举的那个例子——「求解器返回计划就认定可解」——**在这个仓库里没有发生**：

* `engine-rig/engines/fd_adapter/__init__.py:140` **无条件**调用 `validate_plan()`，
  **三个梯级都过，含真 FD**；而且 `validate.py` **刻意不 import `search`**——
  验证器不认识搜索器，这是结构保证不是承诺。
* `ic3_pdr` 用**不共享搜索代码的枚举器**复验，不过就 `raise`。

这两处是 `fuzzlab` 那条 `plan_replays_to_the_goal` 在本仓库里的对应物。
**问的那个问题，答案是"已经做对了"**，值得记下来——
今晚的报告里正面结果太少，这一条是真的。

## 二、漏的不是"没验"，是**"验了、写进产物、然后不拿它把关"**

**这是对偶的真实形状，而且它是今晚主模式的一个新变种。**
主模式是「判决算对了，没接到**退出码**上」。这里是：
**判决算对了，接到了一个**兄弟字段**上，而**头条字段不看它**。**

两处同形，都已复核：

**(1) `engine-rig/engines/lp_potential/potential.py:255`**

```python
"admissible": True,
```

**是一个字面量。** 不是计算出来的，是写死在 payload 字典里的。
普查员实测：拿一张 `holds=False` 的证书造 `Heuristic`，**这个字段照样是 `true`**。
而**真正的可采纳性检查就躺在同一份 payload 的 `admissibility_check` 里**——
**头条不看它。**

**(2) `engine-rig/engines/deadlock_carver/__init__.py:168-180`**

```python
task = Task.build(domain, problem)
theorems = carve(task, max_pattern=max_pattern)
report = pruning_report(domain, problem, theorems) if with_report else None
if out_path:
    emit(out_path, candidates(theorems, task, report=report, timestamp=timestamp))
```

`run()` 是 **carve → report → emit，中间没有一个 `if`**。
那份 report 里含一个**经验证伪器** `same_answer`（「这条定理有没有改变实例的答案」），
它被算出来、被序列化成 `plan_length_unchanged`，
**然后和它所证伪的那条定理并排发布**。

**读者拿到的是一条定理和一份说它没用（或更糟）的报告，摆在一起，没有谁压过谁。**

## 三、**整个 `engine-rig` 没有任何留出验证**

`grep -ril "held_out\|held-out" engine-rig/engines engine-rig/tools` → **零命中**（我自己跑的）。

而 `zero_space.verify` 是**在拟合它的同一条轨迹上**复验的——
按 GF(2) 的构造，那近乎恒真，**那句 `AssertionError` 几乎不可能触发**。

**这一条把今晚三处发现串成了一条线**：
* E11：`DECISIONS.md` **D-003** 明写 `zero_space` 只承诺**在观测证据上**守恒（那是边界不是缺陷）；
* E9：`g50t` 原本被放在 `zero_space` 边界的**已测**一侧，而那里**从来没有东西检查过正确性**；
* 本轮：**整个 rig 没有留出验证，所以"已测"在很多格里的意思是"在拟合它的数据上自洽"。**

**三条独立发现指向同一件事**，而且它直接影响论文里每一处「已验证」的措辞。

## 四、六处"验了但不独立"，单列，因为这一格最容易被读成安全

你点名的接地层盲区**不是孤例**：

* `lp_potential` 与 `moves_from_graph` 共享后继关系；
* `ic3_pdr` 与 `system.moves` 共享；
* `interop/certificate_export.verify` **只复算生产者列出的 witness**——
  而它的 docstring **自称 importer 无需信任生产者**。

**"验了一道"和"用独立的东西验了一道"是两件事**，报告里分开列了。

## 建议

**另开一件，不要并进 C11。** C11 的验收线是失败那一族的逐处订正，
把对偶塞进去会让它的验收线没人复核得动（今晚 A9 与 V16 我都是这么切的）。

新条目该做三件：
1. **`"admissible": True` 改成读 `admissibility_check` 的结论**，并补一个负样本：
   拿 `holds=False` 的证书造 Heuristic，断言该字段**必须为假**；
2. **`deadlock_carver.run()` 在 `same_answer` 证伪时不得照常 `emit`**——
   要么不发，要么发出去的候选自带一个**机器可读的失效标记**（不是散文）；
3. **给 rig 补留出验证**——这一条最大，可能要单独一件；
   至少先**把"没有留出验证"这个事实写进 `ENGINE_TABLE.md` 的边界列**
   （E9 那张表的规矩就是边界列不许空，而这一格现在是空的）。

完整报告（含约 97 处**正当**写法作为免疫对照、以及三条我不确定的——
其中两条指向 `cold-start-a0/`，**本轨道禁入，只登记**）在分支
`agent/e11-engine-crosscheck-deep`：
`engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep/SURVEY-success-as-truth.md`。
