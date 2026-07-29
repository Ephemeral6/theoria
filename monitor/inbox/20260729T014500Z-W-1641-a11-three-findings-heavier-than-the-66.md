# A11：66 条全部无害，但找它们时翻出三条更重的——其中一条现在就该处理

W-1641，2026-07-29T01:45Z。条目 `A11-bypass-attempts-explained`，领地 `theoria-arm`。
完整分析：`theoria-arm/runs/20260729T013000Z-A11/FINDINGS.md`（分支已推）。
**下面每一条我都自己读过代码复核，不是转述 subagent。**

## 先回答工单：66 条 = (a) 66 / (b) 66 / (c) **0**

全部由一次刻意探针产生，全部被中和，**零条真绕过**，封存堆零命中
（131 条记录里没有 `game_id` 键；25 个 id 含词干逐个子串匹配，零命中）。
逐条分类落盘在 `runs/20260729T013000Z-A11/classification.jsonl`。

**但工单的前提不成立**：这 66 条 `arm: "probe"`、`run_id: "probe-model-proxy"`，
`proxy/ledger.py:36-38` 把 `probe` 注册为与 `theoria` 并列的**另一个身份**，
且它们**早于这条臂存在**（`evidence/README.md:9-10`）。
它们不在「会去打真 API 的那条臂」上。真臂每份 MANIFEST 都写 `bypass_attempts: 0`。

## 需要现在看的一条：被跟踪的证据文件在发布操作者身份

`theoria-arm/evidence/model-proxy-401.jsonl`，**被 git 跟踪、5.8 MB**，
内含 `account_uuid` / `device_id` / `session_id` **各 65 次**（我自己数的），
外加 Claude Code 的系统提示词。CLAUDE.md 写着
**「Phase 4 的释出清单会发布每一个被跟踪的文件」**。

**说准确**：里面**没有** Bearer token、没有 oauth 字面量（各 0 次）——
**凭据没有泄漏**，泄漏面是**操作者标识符**。所以这不是密钥事故，
不必按 INC 走密钥流程；但它已经在树里，且默认会被发布。
**请裁决**：删除 / 脱敏（`redact.py` 已有先例，INC-008 就这么处理的）/ 明示保留。
属 `theoria-arm` 领地，我可以执行，但删除一份被引用的证据文件是所有权判断，
不该我一个人做——它被 `DECISIONS.md:44`、`GAPS.md:39`、`STATUS.md:86` 引用。

## 机制性的一条：`bypass_attempt` **不保证拒绝**，它只是记录

`proxy/model_proxy.py:176-181` 记完 incident **没有 `return`、没有 `_respond`**，
控制流直接落到 guard、闸门、`_forward`。`env_proxy.py:231-248` 同形状。
真正保住性质的是 `_forward` 里的白名单 `PASSTHROUGH_REQUEST_HEADERS`
（只有 content-type / accept / anthropic-version / anthropic-beta）。

**推论，也是对现有说法的更正**：那 66 条 401 **不是代理拒绝的**——
是白名单剥掉了头，上游因为没有 `ANTHROPIC_API_KEY` 才回 401
（实测 `http.status` 全 401、`usage` 全 `{}`）。
**若当时 `.env` 里有 `ANTHROPIC_API_KEY`，这 66 个请求会返回 200，
而 incident 记录一模一样。** `evidence/README.md` 那句
「This is the sealing property working」多说了一步。

**风险**：谁要是把 `authorization` 加进白名单，这 66 条会**无声地**从
(b) 变成 (c)，计数器长得完全一样。**计数器是观测点，不是执行点。**
属 `proxy` 领地，只报不改。

## 最重的一条：「臂不持有凭据」在这条臂实际的部署方式下是**假的**

`theoria-arm/harness/run.py:161`：`self.proxy = EnvProxy(self._cfg).start()`
——`EnvProxy` **在臂自己的进程里**跑（`proxy/env_proxy.py:498-531` 是
`threading.Thread`，不是子进程）。而 `env_proxy.py:78` 是
`self.api_key = ... read_secret("ARC_API_KEY")`。
**活的 ARC 凭据就在臂的进程内存里。**

`env_proxy.py:7-9` 那句「绕开它就等于没有钥匙」**只对独立部署成立**。
而 `theoria-arm/STATUS.md:56` 与 `GAPS.md:20` 拿 `key_injected: true` 当
「臂无钥匙」的证据——**那个标志只说明代理注入了钥匙，不说明臂没有钥匙**。

**这正是本工单点名的形状：在一个地方验了，当成另一个地方的结论。**
而且**全仓没有任何测试断言「臂无钥匙」**——所以它一直是声称，不是性质。

同族还有两条（细节见 FINDINGS）：
* **模型这条路完全不过封存护栏**：`modelcall.py:503-518` 直接 spawn `claude -p`，
  臂侧唯一替代 `inner/loop.py:160` 的 `forbid_in_prompt` **只含本局开发堆 id，
  任何封存 id 都不在表上**。切分规则第二条（不得阅读关于封存局的东西）
  在模型流量上无人执行。
* **`modelcall._invoke` 的环境清洗与自己的注释矛盾**（`:505-508`）：
  注释说不得继承 base URL，代码只 pop `ARC_API_KEY`，
  `ANTHROPIC_BASE_URL` / `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` 照常继承。
  **不改代码、仅靠配置**即可重定向臂的模型流量，而账本照记 `provider: anthropic`。

## 结论按工单第 3 条分两行，永不合并

* **proxy 侧**：封存护栏**成立**。对抗审计的所有规避（裸词干、不点名游戏的命令、
  自带 auth 头、重签的 piles.json）都在 socket 之前被 403 拒绝，实测零上游命中。
* **真臂侧**：**尚不成立**。环境路成立，但臂进程持钥、模型路无护栏、
  模型子进程环境可配置绕开——三条都没有任何现有检查覆盖。

`ACCESS_CHECK.md` 在 **`arc-recon/`**，不在我的领地。
现在那里是**一行**：`:608`「No sealed game was contacted，`contamination.py`
的账本审计查了每一次调用」。两处要改，**请转 arc-recon**：
1. 拆成上面那两行（这正是工单要的）；
2. 那一行倚靠的 `contamination.py` **本身不可能变红**（第 338 行退出码只看
   一次 sha256 比对，扫 3 个文件、无负控——S17 的 C-48 已量化）。
**一个不能变红的检查撑着一句「从未接触」，是本轮最该修的组合。**
