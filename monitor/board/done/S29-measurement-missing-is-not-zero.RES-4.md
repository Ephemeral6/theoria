priority: 1
cell: S3
territory: proxy
deps: none
lane: infra

# S29-measurement-missing-is-not-zero · 量不到被写成了 $0.00

对抗性普查（2026-07-29）在花费这一侧抓到三条，全部指向同一件事：
**「没测到」和「测了，是零」编码成了同一个字面量。**

1. **`proxy/cost.py:58`** —— 「未计价」机制（`usd: None` + `unpriced_models`）
   只在**模型**未知时触发，**从不在测量缺失时触发**：`usage == {}` 走完全计价分支，
   返回一个格式良好的零，`price_run` 加 0.0 却照样把 `calls` +1，
   而 `unpriced_models: null` 正面断言「什么都没漏」。
   残缺情形更坏：只有 `input_tokens` 时返回一个正的、可信的价格，
   **静默漏掉贵五倍的输出侧**。
2. **`proxy/spend_gate.py:305`** —— `SpendPolicy` 接受非有限的 `usd_ceiling`。
   模块自己的 `finite()`（:164-181）注释逐字解释了这个失效模式
   （「NaN 不小于 0，之后每个 > 比较都是 False，天花板被静默作废」），
   却只用在调用方传入的金额上，**没用在策略字段**。
   于是 `check` / `reserve` / `_first_breach` 三处执法点恒假，
   `verify_spend.sh:83-94` 那条「池策略可读且有天花板」的专项检查印出 `inf` 后退出 0。
3. **`proxy/runner.py:248`** —— 崩溃清理的所有权过滤是
   `... and kwargs.get("run_id") is not None`，而 `run_id` 在 `_run_game` 内部生成，
   普通调用方从不传入，于是那个 `continue` **永不触发**：一次崩溃会释放运行期间
   出现在共享池里的**每一个**预留，包括别的会话的。`release` 不校验所有权、
   对不认识的 id 静默 no-op，落下的记录写着「run ended without releasing its claim」
   ——读起来正是它被写出来要做的那件事。

做四件：

1. `cost()` 对**已知模型**加一条：必备计量键缺失 → `usd=None` 并进
   `unpriced_usage_keys`。**注意 `test_arm.py:570` 断言 `unpriced_models is None`
   ——正是那一条让套件在漏账时保持绿色，要一起改。**
2. `spend_gate.py:305` 套上 `finite()`（一行，函数已存在）。
   （原报告里 `action_ceiling` 那一半是错的：`int()` 会先抛，那是响的失败，别改。）
3. 删掉 `runner.py:248` 那个死掉的第二合取项，并让 `release` 校验所有权。
   顺带修测试——`test_spend_gate_egress.py:129-149` 既 monkeypatch 掉 `_run_game`
   又传了 `run_id=`，两重真空。
4. **三条各一个阴性样本**：空 usage 的调用（断言 `usd is None`）、
   `usd_ceiling: NaN` 的策略（断言拒绝装载）、两个会话并发时的崩溃清理
   （断言只释放自己的预留）。

服务论文 WP2、WP3（账单形状那张图的可信度全在这里）。零 API 计费。
