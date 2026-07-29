priority: 1
cell: S26
territory: monitor
deps: none
lane: infra

# S26-phase1-gate-must-decide · 一个关不上的门就是一个会被跨过去的门

`monitor/scan.py:199-216`：

```python
def probe_a1_state():
    bridge = exists("engine-rig/interop/certificate_export.py")
    consumed = False
    ...
    return {"status": "partial", "detail": "... %s ... %s" % (...)}
```

两个布尔量被算出来、格式化进 detail 字符串，**然后无条件返回 `partial`**。
它们从不参与判定。所以这道门**在结构上永远关不上，也永远开不了**。

而 `Theoria.md:305` 规定 Phase 1 全绿才准烧游戏钱，门后挂着 WP6(0.20) + WP7(0.06)
+ WP8(0.05)，**共 0.31 权重**。它确实被跨过去了：钱门 9/16 时发生过跨门花费。

做四件：

1. **让判据参与判定**：`bridge and consumed` → green，一半 → partial，都没有 → risk。
   一行，但**先写测试再改**，三种输入各一条。
2. **全仓复查同族**：任何 `probe_*` 里算了量却不用于 `status` 的，逐处列出并订正。
   这是今晚那一族（判决算对了、不接到出口上）在**监控自己身上**的实例，
   不要只修这一处就收工。
3. **把 Phase 1 的十六项逐项接上探针**，现在是 9/16 而那九项怎么数出来的没有单一出处；
   缺探针的项如实标 `unprobed`，**不许默认算绿**。
4. **负样本**：喂一个两半皆通的假树，断言它必须报 green；再喂一个只通一半的，
   断言不得报 green。没有这两条，这次修复本身也只是一份自称。

服务论文 WP6/WP7/WP8 的解锁前提。零 API、零封存堆接触。
