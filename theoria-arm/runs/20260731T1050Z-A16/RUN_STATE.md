# A16 · launch_gate 接进真正会花钱的路径

`freeze/launch_gate.py` 从 S4 起就存在、自测 12/12（含「绿是可达的」那一例），
而**没有任何会花钱的路径调用它**：`freeze/verify.sh` 只把裁决当 NOTE 报，
`verify.sh` 不是开跑路径。于是 `STATS_RULES.md` §9 的「未实现不得开跑」
仍然只有散文在拦。本条目就是那处接线。

## 一 接在哪，以及为什么闸排在 `assert_dev_pile` 前面

`theoria-arm/harness/campaign.py`，`Campaign.__init__` 里，两道硬拒绝并排：

```python
assert_launch_cleared(games)   # §9 的闸，只管封存堆
assert_dev_pile(games)         # 堆切分本身，不变
```

顺序是被论证过的，不是随手排的。`assert_dev_pile` 对任何封存局号一律拒绝，
所以它若排在前面，下面那道闸**永远到不了**——一根点不着的线正是本条目要消灭的东西。
闸排前面不丢任何信息，因为它抛出的拒绝**点名触发它的封存局号**：
两件事在同一条消息里都到达读者。而闸若哪天真的转绿，`assert_dev_pile`
照样拒绝——这个模块是开发堆战役，封存名单无论如何都不归它跑。
同一输入两道独立拒绝，是有意的形状。

## 二 阴性对照：两个方向都测了

只测拒绝，测不出「接反了」和「根本没生效」——今天真实答案是 blocked，
而且在 §9.2/§9.14 被实现之前会一直是 blocked，所以一根无条件抛异常的线
和一根正常工作的线在只测拒绝的套件里完全一样。

* **REFUSE**：真 `freeze/launch_gate.py` + 真 `STATS_RULES.md` + 真注册表，
  走真 `Campaign.__init__`，对封存名单拒绝并点出未清行号。
  今天实际未清：**§9.2、§9.14、§9.15、§9.16、§9.17**（§9.11 已清）。
  注意条目正文写的是 9.2/9.11/9.14 三条——那是 S4 当时的状态，
  今天的表已经长了，所以消息里的行号是**从裁决里读出来的**，不是抄的常量。
* **LAUNCH**：同一根线，喂给它一个报 clear 的闸，必须放行。
  按 `freeze/runs/20260729T155500Z-S4-launch-gate/probe_r4_clearing_path.py`
  的写法造：**真** `launch_gate.gate()`、**真** `STATS_RULES.md`，
  只有注册表是合成的，且每条都指向一个真有判别力的检查
  （接受 `good.txt`、拒绝 `vacuous.txt`，两半都跑，任一半不过即不算清）。
  行集合是从真 §9 解析出来的，所以 §9 明天加一行，这个对照仍然覆盖它。
* **UNAFFECTED**：开发堆四局**根本不调闸**——不是「调了再忽略答案」。
  证法是把 `LAUNCH_GATE` 指向一个不存在的路径再构造真的开发堆 `Campaign`：
  `assert_launch_cleared` 里每一条失败路径都是拒绝，所以若闸被调用了，
  这里必然抛异常。它没抛。

`launch_gate.py --json` 没有指向临时注册表的开关，而 `freeze/` 是别人的领地、
本臂不可改，所以 LAUNCH 那半需要一个 driver 脚本。driver 是
`launch_gate.main()` 契约的第二份拷贝，拷贝会漂——所以
`test_the_driver_agrees_with_the_real_binary_on_the_real_state`
拿**真注册表**同时跑真二进制与 driver，要求 verdict、`may_launch`、
退出码、逐行 `cleared` 全部一致。契约漂了，这条先红。

## 三 exit 2 与 exit 1 同样拒绝，以及其它四种「没说是」

`launch_gate.py` 自己的文档写着：*1 and 2 are both "no" ... never so a caller
can treat 2 as a pass*。只测 exit 1 的调用方满足这句的字面，却会在闸坏掉时开跑——
而闸坏掉恰恰是最容易造出来的状态。所以全部按拒绝处理，各有一条测试：

| 情形 | 处理 |
|---|---|
| exit 1（有未清行） | 拒绝，点名行号 |
| exit 2 / `verdict: error` | 拒绝，「闸评不了自己不是通过」 |
| exit 0 但 `may_launch` 不是 `True` | 拒绝，「退出码与文档自相矛盾」 |
| `may_launch: "yes"`（真值但不是 `True`） | 拒绝（用 `is True`，不是真值测试） |
| 输出不是可读 JSON | 拒绝 |
| 闸起不来 / 超时 | 拒绝 |

## 四 接线过程中量到的一个真缺陷

第一版用 `subprocess.run(..., text=True)`。`text=True` 用**本地 locale**
解码，本机是 CJK Windows，即 GBK；而 §9 是中文散文、带 ⟨…⟩ 占位符，
闸自己正是为此把 stdout 重设成 UTF-8（`launch_gate.py:83`）。
结果 `UnicodeDecodeError` 抛在 subprocess 的 reader 线程里，
本函数拿到空 stdout。它**仍然会拒绝**（不可读 JSON 即拒绝，闸是 fail-closed 的），
但会在每一次封存开跑上**用错误的理由**拒绝——「闸没输出可读 JSON」
而不是「§9 还有五行没清」。改成 `encoding="utf-8", errors="replace"`。

这是新测试抓到的，不是读代码读出来的：如果只写了 REFUSE 那一半，
它会照样绿，因为两种理由都是拒绝。

## 五 边界

零 API、零花费、封存堆零接触。本条目**没有**改 `freeze/` 的任何文件
（只读调用）。任何封存局号都不在源码或测试里写死——
测试用的那一个是运行时从 `arc-recon/data/piles.json` 读的，
并且有一条测试断言 `harness/campaign.py` 的源码里一个封存局号都不出现。

## 六 状态

* 新测试 `theoria-arm/tests/test_launch_gate_wired.py`：13 条全绿。
* 今天真闸的裁决：`blocked`，exit 1，五行未清。开发堆四局不受影响。
