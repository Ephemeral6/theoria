# A11：66 条全部无害，而找它们的过程翻出了三条更重的

W-1641，2026-07-29T01:40Z。条目 `A11-bypass-attempts-explained`，领地 `theoria-arm`。
一个分类员 + 一个专职推翻的对抗审计员并行；下面每一条**关键**结论我都自己复核过。

## 一、66 条的分类：(a) 66 / (b) 66 / (c) **0**

工单要求分三档，而**前两档在这里不互斥，这本身就是答案**：66 条全部由一次
**刻意的探针**产生（a），也全部被中和（b），**零条真的绕过**（c）。

66 条除 `seq`/`ts` 外**逐字节相同**：

| 字段 | 值（全部 66 条） |
|---|---|
| `arm` | **`probe`** |
| `run_id` | `probe-model-proxy` |
| `event` / `kind` | `incident` / `bypass_attempt` |
| `header` / `path` | `authorization` / `/v1/messages` |
| `detail` | the arm supplied its own authorization header to the model proxy |
| `game_id` | **不存在这个键** |

配对的 65 条 `model_call` 一律 `status: 401`、`usage: {}`（零 token、零花费）。
**66 对 65 的差**：incident 在**收到请求时**写，`model_call` 在**收到响应后**写；
第 131 行（末行）是一条没有配对的 incident——第 66 个请求还在飞行中，
CLI 就撞上了 180 秒超时。是被截断的一对，不是泄漏。

**封存堆：干净。** 131 条记录里没有 `game_id` 键；把 `piles.json` 的 25 个 id
（含词干）逐个子串匹配，零命中。

## 二、工单的前提不成立：这些不在真臂上

工单说这 66 条在「会去打真 API 的那条臂」上。**它们不是。**
`proxy/ledger.py:36-38` 把 `probe` 注册为与 `theoria` **并列的另一个身份**，
而 66 条全部 `arm: "probe"`、`run_id: "probe-model-proxy"`。
它们**早于这条臂存在**（`theoria-arm/evidence/README.md:9-10`：
「made before the arm was written」），产生方式是一次手动实验
（`ANTHROPIC_BASE_URL=<model proxy> claude -p`，D-P8-002，提交 `606c582`），
没有任何脚本会重新产生它。真臂的每一份 `runs/*/MANIFEST.json` 都写着
`"bypass_attempts": 0`。

## 三、`bypass_attempt` **不保证拒绝**——它只是记录

这是本轮最该记的机制性发现，我自己读了代码确认。
`proxy/model_proxy.py:176-181`：

```python
for name in CREDENTIAL_HEADERS:
    if self.headers.get(name):
        self.cfg.run.incident("bypass_attempt", ..., path=path, header=name)
```

**没有 `return`，没有 `_respond`。** 控制流直接落到 guard 检查、消费闸门、
然后 `_forward`。`proxy/env_proxy.py:231-248` 是同一个形状。

真正保住性质的是**另一个机制**：`_forward`（`model_proxy.py:345-352`）
从白名单 `PASSTHROUGH_REQUEST_HEADERS = ("content-type","accept",
"anthropic-version","anthropic-beta")` **重建**请求头，
`authorization`/`x-api-key`/`api-key` 都不在里面。
**记录的是 incident，执行的是白名单——两个独立的东西。**

**由此得出一条对现有说法的更正**：那 66 条 401 **不是代理拒绝了它们**。
是白名单剥掉了 CLI 的头，上游 Anthropic 因为**没有** `ANTHROPIC_API_KEY`
才回的 401。**假如 `.env` 里当时有一个 `ANTHROPIC_API_KEY`，这 66 个请求会
返回 200，而 incident 记录一模一样。**
`evidence/README.md` 那句「This is the sealing property working」**多说了一步**。

风险形态：若哪天有人把 `authorization` 加进白名单，这 66 条会**无声地**
从 (b) 变成 (c)，而计数器长得完全一样。**计数器是观测点，不是执行点。**

## 四、比 66 条重得多的三条（对抗审计翻出，我逐条复核）

### F1 —「臂不持有凭据」在**这条臂实际使用的部署方式下是假的**

`theoria-arm/harness/run.py:161` 是 `self.proxy = EnvProxy(self._cfg).start()`
——`EnvProxy` **在臂自己的进程里**启动（`proxy/env_proxy.py:498-531` 是
`threading.Thread`，不是子进程）。而 `env_proxy.py:78`：

```python
self.api_key = api_key if api_key is not None else read_secret("ARC_API_KEY")
```

**于是活的 ARC 凭据就在臂的进程内存里。** 我自己读了这两处确认。

`proxy/env_proxy.py:7-9` 那句封装论证——「绕开它就等于没有钥匙」——
**只对独立部署（`python -m proxy.env_proxy`）成立**，对臂内线程部署不成立。
而 `theoria-arm/STATUS.md:56` 与 `GAPS.md:20` 拿 `key_injected: true` 当作
「臂无钥匙」的证据，**那个标志只说明代理注入了钥匙，不说明臂没有钥匙**。

**这正是工单点名的那个形状：在一个地方验了，当成另一个地方的结论。**
CLAUDE.md 写的 Phase 1 封装纪律是「凭据只在环境代理内部注入，不进入任何 arm」。

### F2 — 模型这条路**根本不经过封存堆护栏**

`harness/modelcall.py:503-518` 直接 spawn `claude -p`，
`proxy/model_proxy.py:186` 的 `guard.check_request` → `sealed_pile_in_prompt`
被**按设计绕开**（`modelcall.py:9-42` 有声明）。臂侧唯一的替代是
`inner/loop.py:160` 的 `forbid_in_prompt=(game_id, stem)`——**只含本局的开发堆 id，
任何封存 id 都不在这张表上**。

于是切分规则的第二条（**不得阅读关于封存局的任何东西**）在模型流量上**无人执行**。
A3 已经发现过的那条通道（引擎 traceback / 绝对路径 / Lean 诊断进入
`evidence_brief`）会把一个封存 id 原样带进上下文而不被拦。

### F3 — `modelcall._invoke` 的环境清洗与它自己的注释矛盾

`harness/modelcall.py:505-508`：注释说这张桌子「must not inherit a base URL that
would send it somewhere unrecorded」，而代码**只 pop 掉 `ARC_API_KEY`**。
`ANTHROPIC_BASE_URL`、`ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN` 全部照常继承。
**不改一行代码、仅靠配置**就能把臂的模型流量重定向到任意主机，
而账本照样记 `provider: anthropic`、`status: 200`。

### F4 — 那份证据文件本身把操作者身份发布了出去

`theoria-arm/evidence/model-proxy-401.jsonl`：**被跟踪**、**5.8 MB**，
里面 `account_uuid` / `device_id` / `session_id` **各 65 次**（我自己数的），
以及 Claude Code 的系统提示词。CLAUDE.md 写着
**「Phase 4 的释出清单会发布每一个被跟踪的文件」**。

**准确地说**：里面**没有** `Bearer` token、没有 `oauth` 字面量（各 0 次）——
凭据本身没泄漏，泄漏的是**操作者标识符**。这不是密钥事故，是隐私面，
但它已经在被跟踪的树里，且会被发布。

## 五、没能推翻的（对抗审计如实列出它试过什么）

* **另一条 ARC 出口**：`theoria-arm/` 全量 grep `urllib`/`requests`/`httpx`/
  `http.client`/`socket`/`anthropic`，只有 `harness/arc.py:122-127`；
  `ARC_BASE_URL` 全臂从不读取。**关闭。**
* **靠配置关掉护栏**：`run.py:110` 硬构造 `SealedPileGuard()`，
  没有 kwarg / CLI 标志 / 环境变量能碰它；`--mock` 换的是上游与 `require_key`，
  不是护栏。**关闭。**
* **护栏是否在 socket 之前拒绝**：拿真 `EnvProxy` 对一个本地插桩上游跑——
  封存 id → 403 且**零次上游命中**；开发 id → 才开 socket。**关闭。**
* **规避尝试**：裸词干 `bp35` → 403；不点名游戏的命令 → 403
  `unattributable_command`；封存 id + 臂自带 auth 头 → 403。**全部关闭。**
* **篡改切分**：重新签名的 `piles.json` 能过 `campaign.assert_dev_pile`，
  但过不了 `Run` 构造时 `load_piles` 的钉死摘要。**关闭。**
* **负控能变红**：封存堆那套机器确实有失败路径（403 拒绝/无 socket 对
  502 放行/尝试 socket 可区分）。**但「臂无钥匙」这条没有任何测试断言它**
  ——这正是 F1 的推论。

## 六、结论，分两行写，永不合并

按工单第 3 条，`proxy` 侧与真臂侧是**两个判决**：

* **proxy 侧**：封存护栏成立。上述所有规避尝试都在 socket 之前被 403 拒绝，
  且 `bypass_attempt` 的凭据剥离由白名单结构性保证。
* **真臂侧**：**尚不成立。** 环境这条路成立（走 `EnvProxy`，护栏在
  socket 之前生效），但 **(i) 臂进程持有活凭据**（F1）、
  **(ii) 模型这条路完全不过封存护栏**（F2）、
  **(iii) 模型子进程的环境清洗可被配置绕开**（F3）。

**66 条不是问题。问题是找它们时翻出来的这三条，而它们没有一条被现有的检查覆盖。**
