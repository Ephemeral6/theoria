# DRIFT-a1-probe-can-only-ever-say-partial

severity: high
dimension: 单向门（第 7 维第二句判据的推广：这个检查有没有**任何**能改变它结论的样本）

evidence: 审计区间 `4d6f1ee..423cd5b`（9 个提交）。本条是总线 `#3` 指派的「继续拿那把尺子扫其它检查」的产物。我把尺子做成了机器判据——用 `ast` 遍历 `monitor/scan.py` 里全部 15 个 `probe_*`，看每个函数体内出现过哪些状态字面量。结果只有一个是病态的：

```
probe_a1_state             statuses: partial                     **只有 partial**
```
（其余 14 个都至少有 green + 一种非绿；`probe_a0_state` / `provenance` / `dispatch_board` / `inbox` 是 green+partial 的盘点型探针，属正常。）

**`monitor/scan.py:199-216` 全文**——它算了两个布尔量，把它们渲染进 detail，然后 `return` 一个**写死的** `"status": "partial"`：
```python
def probe_a1_state():
    bridge = exists("engine-rig/interop/certificate_export.py")
    consumed = False
    ...  # 遍历 theory-compiler 找 "certificate"
    return {"status": "partial",
            "detail": "engine-rig 侧证书导出：%s；theory-compiler 侧消费：%s。"
                      "两半接通前，A1 仍是彩排而非验收。" % (...)}
```
`bridge` 与 `consumed` **只进字符串，不进判决**。两半都接通了它照样报 partial；两半都断了它也照样报 partial。

**两半现在都是通的**（可复核）：
- `engine-rig/interop/certificate_export.py` **在树上**；
- theory-compiler 侧消费也在：`theory-compiler/lean/TheoriaLean.lean` 等文件命中 `certificate`，且 `3f3f396`「theory-compiler: consume the ic3_pdr certificate」已合并。

**后果不是一格颜色，是一道门永远关不上。** `monitor/scan.py:1833` 已经实现了「探针优先于手写判断」这条规则：
```python
st = pr["status"] if it["status"] not in ("risk",) else it["status"]
```
`spec.py` 的 `p1-a1` 手写 `green`，探针说 `partial`，**探针赢**。于是盘面实况是 `p1: green 9 / partial 7`，而这 7 个 partial 里的 `p1-a1` **在任何情况下都不会变绿**。

`Theoria.md:305` 逐字写着「全绿才准烧游戏钱（Phase 3 的门）」。只要 `probe_a1_state` 保持这个写法，**Phase 1 全绿是一个构造上不可达的状态**，这道门在字面意义上永远关不上。我第二轮报过这道门已被跨过并已被登记为例外——那条报告说的是「跨门这件事必须是被记录的决定」；这一条说的是更根本的：**即使所有人把活全干完，门也不会亮绿灯**。

claim: `probe_a1_state` 不是一个检查，是一个带动态说明文字的固定标签。它没有负样本，也没有正样本——**没有任何输入能改变它的输出**。它把 Phase 1 验收单上的一项永久钉在 partial，从而让整个 Phase 1 的门无法达成。

suggest:
1. **改一行就够**：
   ```python
   status = "green" if (bridge and consumed) else ("partial" if (bridge or consumed) else "missing")
   ```
   detail 保持不变（它写得很好，两半的状态一目了然）。改完之后按现在的树，`p1-a1` 应当转绿。
2. **补一个能让它变红/变绿的样本**（这正是 S20 刚定的通用验收要求，本条是它的第一个客户）：注入 `bridge=False` 断言非绿、两半都真断言绿。没有这一步，第 1 条改完仍然没人能证明它会动。
3. **拿同一把尺子扫一遍所有「固定返回值」的地方**，不限于探针。这次的机器判据很便宜，可以常驻：`ast` 遍历，凡是函数计算了变量却把它们只用在字符串插值里、返回值是字面常量的，列出来。我这轮跑它花了不到一分钟，覆盖了 15 个探针。判据脚本我留在 `scratchpad/probe_red.py`，逻辑十几行，建议直接搬进 `monitor/` 作为一个 meta 探针——**让「探针本身是不是活的」也变成盘面上的一个数**。
4. 顺带把 `spec.py` 的 `p1-a1` 手写 `green` 与探针的冲突显式化：按 03:57Z 立的规则，矛盾本身该报出来而不是静默取探针值。现在 `scan.py:1833` 只是静默覆盖，没有任何地方记「手写 green / 探针 partial」这个分歧——**规则的后半句（把矛盾报出来）仍未实现**，这已经是我第三次提它了。

**本轮同时扫过、结论是干净的（沉默即健康，但既然是指派任务，把覆盖面留证）：**
- **四个闸门模块全部有负样本**：`battery/guard.py`（5 个测试命名它，4 个含失败断言）、`exam/guard.py`（6/6）、`proxy/guard.py`（10/9）、`proxy/spend_gate.py`（4/3）。
- **六个 `verify*.sh` 全部有失败路径**。其中 `proxy/verify_spend.sh` 我一开始的正则判它「无失败路径」，**读了全文发现是我错**——它用 `fail=1` 累积、末行 `exit "$fail"`，五处 step 都能置红，还额外查「闸门有没有长出开关」和「有没有模块绕过 forward() 出网」。这是我这轮见到写得最好的一个闸门，**假阳性归我，记在这里免得下一个转世重报**。
- 红线：本区间 9 个提交，封存 ID 命中仅污染登记与盘面渲染；密钥零命中；主线 append-only 零新增删除。
