priority: 1
cell: C4
territory: engine-rig

# C13-certificate-bridge-two-halves · 证书桥造了一半，另一半没人接

**这是第 1、2 列（造仪器 / 离线验证）四个缺口里最贵的一个**：网格 C4 至今是 **0%**。

`engine-rig/interop/certificate_export.py` 已经存在，`theory-compiler` 侧有没有消费
则由 `monitor/scan.py` 的 `probe_a1_state` 判断——而它长年报 partial。
（那个探针本身「算了两个布尔却不用于判定」的缺陷已由 S26 修掉，
所以**现在它的判决是可信的**，partial 就是真的 partial。）

Lean 那一半是全仓最强的证据：A1 pagoda、IC3、deadlock 三条证书路径都能重新生成
并用 `lean 4.9.0` 编译通过，公理集与 `verify/EVIDENCE.json` 逐条吻合。
**造好的东西没接上，比没造更可惜。**

做四件（**只动 `engine-rig/`，`theory-compiler/` 是另一条轨道，一个字节都不许改**）：

1. **把导出侧做实并证明它可被消费**：给 `certificate_export` 写一个
   **端到端往返测试**——引擎产一张证书 → 导出 → **用一个不 import 引擎的独立读取器**
   把它读回来并重新验证。读取器不认识生产者，这是结构保证，
   而不是「我们保证格式对」。
2. **把格式钉进 `/CONTRACTS/`**：证书交换格式是跨轨道接口，
   按仓库规矩要走契约文件 + 两轨道在 PARTNER_SYNC 签认。
   **只做加法**（新增字段可选），不动既有冻结条款。
3. **在 PARTNER_SYNC 写清楚我方已就绪**：导出侧能产什么、格式在哪、
   怎么验、示例证书在哪个 `runs/<id>/`。对方接不接是对方的事，
   **但「我们这半没做完」不能再是理由**。
4. **负样本**：喂一张被篡改过的证书，断言独立读取器**必须拒绝**；
   再喂一张合法的，断言通过。

做完之后 `probe_a1_state` 的 `bridge` 应当为真、`consumed` 仍可能为假——
**那正是我们要的状态：我方就绪，等对方**。别为了让探针变绿而去改探针。

服务论文 WP1。零 API、零封存堆接触。
