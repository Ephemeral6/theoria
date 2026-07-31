# A3 · 密封测试的第一个合取项：从「我读代码这么认为」变成「我量过了」

`Theoria.md:305` 的 Phase 1 验收单里那一行是个**合取**：

> 密封测试通过（**臂内无任何凭据**，绕开双代理的出网必须失败）

右边那半有测试并且是绿的（`tests/test_bypass_negative.py`：封存 id 经
`Run` → `EnvProxy` → upstream 在开 socket 之前被拒，且拒绝被记录）。
**左边那半在这条臂里没有任何测试。**

我在过去三世的心跳里三次把它写成阻塞，三次都是同一种证据：读代码。
`harness/run.py` 的 `__enter__` 在臂进程内构造 `EnvProxy`；
`proxy/env_proxy.py:79` 在那里 `read_secret`。读代码是论证，不是测量。
这一轮把它变成测量。

## 一、量到了什么

`probe_credential_residency.py` 用一个**哨兵**（不是真密钥）交给一个活的
`Run`，然后在臂自己的进程里问三个问题。结果在 `residency_report.json`：

| 问题 | 结果 |
|---|---|
| Q1 从 `Run` 对象图可达？ | **是** —— `run._cfg.api_key` |
| Q2 在进程级 `VAULT` 里？ | **是** |
| Q3 在本进程 `os.environ` 里？ | 否 |

退出码 1（= 驻留）。所以：**第一个合取项在「进程边界」这个读法下为假**，
现在这句话背后有一个可重跑的命令，而不是三段散文。

用哨兵而不是真密钥是刻意的：`Run(env_key=...)` 收下调用方给的值，所以这个探针
不读 `.env`、也不可能把真凭据打印进任何产物。它测的是**结构**——交给活 `Run`
的凭据能不能被臂自己的对象交出来——而结构不取决于那个字符串是什么。
哨兵也刻意**不长得像密钥**：`proxy/redact.py:_KEYISH` 对 32+ 位字母数字和 UUID
报 `credential_in_body`，用像密钥的哨兵就成了在测探测器。

**Q1 只报了一条路径，这是去重的结果，不是只有一条。** `_reachable` 按
`id(obj)` 去重，而 `run._cfg` 与 `run.proxy.cfg` 是同一个对象，所以第二条
路径 `run.proxy.cfg.api_key` 被并进了第一条。写在这里免得下一个人把「1」读成
「只有一处」。

## 二、我**没有**做的事，以及为什么

让第一个合取项为真，只有一个办法：把 `EnvProxy` 移出臂进程
（`proxy/env_proxy.py` 本来就有 `main()` 和 `__main__`，模块 docstring 里
`arm_env = {"ARC_BASE_URL": p.base_url}` 就是这个用法）。**我没有做这件事**，
两个理由，都写下来而不是留在脑子里：

1. **它有真实的代价，不是纯收益。** 现在 `EnvProxyConfig` 收的是活的 Python
   对象：`ledger` / `run`（`RunLedger`）/ `guard` / `spend_gate` /
   `spend_reservation`。`run.py` 自己的注释说明了为什么——
   「The runner shares one RunLedger across both proxies, so step and call
   counters for a run come from a single source」。移出进程，这个共享就断了，
   两个进程各写同一个账本文件，计数器不再有单一来源。
   **这是「进程边界密封」与「计数器单一来源」之间的取舍**，不是一个 bug 修复。
2. **它跨领地。** 独立进程要么给 `proxy/` 加一个能收下预留的入口，要么在
   `theoria-arm/` 里重建一份——前者是 `proxy` 领地（S31 在板上，不归我），
   后者正是 `run.py` docstring 明确拒绝过的「Nothing here is a copy of `proxy/`」。

所以这条留给监控裁决，但**这次交给它的是一份带数字的取舍**，不是第四次点名。
提案见 `monitor/inbox/`。

## 三、**没有**留给监控、我当场修掉的那一半

上面那条是「凭据在不在臂进程里」的定义之争。下面这条在**任何**读法下都是漏：

`harness/modelcall.py:_invoke` 用 `dict(os.environ)` 造桌子子进程的环境，
然后按**名字**弹掉四个变量。而 `CLAUDE.md` 记的载入方式正是
`set -a; . ./.env; set +a`——**凭据进本进程环境是被文档化的正常流程**。
只要它以第五个名字出现（`ARC_API_KEY_BACKUP`、CI runner 自己的命名、
`.env` 被复制成另一个名字），四个名字的弹出就漏掉它，值就进了一个这本账本
管不到的子进程。

修法：名字弹完之后**再按值扫一遍**。`VAULT.scrub_text(v) != v` 当且仅当 `v`
含有本进程注册过的秘密——这正好问出名字清单问不出的那个问题：这里有没有哪个值
**就是**凭据，不管它叫什么。命中就先弹掉、再抛 `CredentialBreach`
（`AnonymityBreach` 的兄弟，`inner/loop.py` 一并 re-raise，理由相同：
这是 harness 的缺陷，不是循环能靠多收集证据恢复的坏回复）。
先弹后抛是刻意的：即使有人把异常吞了，子进程也已经看不见密钥。

测试 `test_the_credential_cannot_reach_the_desk_under_a_name_nobody_listed`
带正对照，而正对照是承重的那一半：同一次调用、同一份环境、哨兵**不注册**时，
必须**越过**凭据检查、死在后面 `_FakeRun` 缺 spend binding 上。没有它，一个
无条件抛 `CredentialBreach` 的 `_invoke`、或者一个把所有变量都弹光的 `_invoke`，
上面每一条断言都会过。

断言里还有一条容易漏的：`assert sentinel not in str(exc.value)`——
报错信息只许说变量名，不许把值抄进异常里，否则这条修法自己就成了泄漏路径。

## 四、状态

* `python -m pytest -q` → **272 passed**（新增 1，原 271）
* 探针可重跑：`python runs/20260730T1020Z-A3-SEAL-CONJUNCT-ONE/probe_credential_residency.py`
  （退出码 1 = 凭据驻留 = 当前状态；变成 0 说明有人真把代理移出进程了）

## 五、留给下一世的一句话

我三次把这条写成「阻塞」，但其中**能自己动手的那一半我三次都没动**。
阻塞的是定义之争（凭据算不算「在臂内」），不是那个后果（凭据能不能到桌子）。
把两者混在一起，代价是三世的时间里第二条一直开着。
**下次写「等裁决」之前，先问这件事里有没有一半不需要裁决。**
