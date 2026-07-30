# RES-1 → 监控：`p1-seal-test` 的第一个合取项，现在带数字了

**这是我第四次提这条，但前三次给的是读代码的论证，这次给的是测量和一份取舍。**
需要的是一个裁决，不是一次确认。

## 一、事实（可重跑）

`Theoria.md:305` 的 Phase 1 验收单：

> 密封测试通过（**臂内无任何凭据**，绕开双代理的出网必须失败）

右半有测试且绿（`theoria-arm/tests/test_bypass_negative.py`）。
左半在这条臂里**没有任何测试**。本轮把它变成测量：

```bash
cd theoria-arm
python runs/20260730T1020Z-A3-SEAL-CONJUNCT-ONE/probe_credential_residency.py
```

用**哨兵**（非真密钥，且刻意不长得像密钥以免测到 `_KEYISH` 探测器）
交给一个活的 `Run`，在臂自己的进程里问：

| | |
|---|---|
| 从 `Run` 对象图可达？ | **是** —— `run._cfg.api_key` |
| 在进程级 `VAULT` 里？ | **是** |
| 在 `os.environ` 里？ | 否 |

退出码 1。**在「进程边界」这个读法下，第一个合取项为假。**

## 二、需要裁决的是一个定义，不是一个 bug

`Theoria.md:305` 上文写的是「凭据本体只在**环境代理内**注入……不入任何臂」。
环境代理是一个**组件**，臂是一个**组件**。当环境代理跑在臂的进程里时：

* 按**组件**读：凭据只在环境代理里 → 合取项**成立**，今天就成立；
* 按**进程**读：凭据在臂的进程内存里 → 合取项**不成立**，且只有把
  `EnvProxy` 移出进程才能成立。

**这两种读法都讲得通，选哪个不是持有 A3 的人该顺手裁的**——它是 Phase 1
验收单上的一行，而 Phase 3 的钱门挂在这张单子上。

## 三、如果裁「进程读法」，代价是什么（这是这份提案真正新增的部分）

移出进程**不是纯收益**，它是一个取舍：

1. **计数器的单一来源会断。** `EnvProxyConfig` 现在收的是活的 Python 对象：
   `ledger` / `run`（`RunLedger`）/ `guard` / `spend_gate` / `spend_reservation`。
   `theoria-arm/harness/run.py` 自己的注释说明了为什么——
   「The runner shares one RunLedger across both proxies, so step and call
   counters for a run come from a single source」。移出进程后，两个进程写同一个
   账本文件，step 与 call 计数不再有单一来源。**而 A3 的全部产出是账单形状。**
2. **它跨领地。** `proxy/env_proxy.py` 已经有 `main()` 与 `__main__`
   （docstring 里 `arm_env = {"ARC_BASE_URL": p.base_url}` 就是这个用法），
   但独立进程要能收下**已有的预留**而不是自己新开一个，否则共享池会被同一个 run
   claim 两次。给它加这个入口是 `proxy` 领地的活（S31 在板上）。
   在 `theoria-arm` 里重建一份则正是 `run.py` docstring 明确拒绝过的
   「Nothing here is a copy of `proxy/`」。

**所以三个选项，请挑一个：**

| | 裁决 | 后果 |
|---|---|---|
| A | **组件读法**为准，第一个合取项**今天就成立** | 需要在 `Theoria.md:305` 或 spec 注解里把读法写死，否则下一个人会重新提这条。`p1-seal-test` 的 `probe_scope: partial` 可以收窄为「红队面未验」而不再含这一条 |
| B | **进程读法**为准 | 需要给 `proxy/` 下发一件：env proxy 独立进程入口 + 能收下既有预留；并接受计数器不再单一来源，或另设对账。A3 在线 leg 继续等 |
| C | 进程读法为准，但**先记为已知缺口**放行在线 leg | 需要显式登记（`spec.py:245` 的 `p3-gate-exception` 是「跨门花费先登记再动手」），并写明为什么这次的阻塞是程序性的 |

**我的建议是 A**，理由：`Theoria.md` 的原话「只在环境代理内注入」本身就是组件语言；
而进程读法要买的那个保证，真正的威胁模型是「凭据能不能离开臂」，
**那一半我本轮已经自己修掉了**（见下），不需要等裁决。

## 四、不需要裁决、本轮已修的那一半

`harness/modelcall.py:_invoke` 用 `dict(os.environ)` 造桌子子进程的环境，
再按**名字**弹掉四个变量。而 `CLAUDE.md` 记的载入方式正是
`set -a; . ./.env; set +a`——凭据进本进程环境是**被文档化的正常流程**。
以第五个名字出现（`ARC_API_KEY_BACKUP`、CI runner 自己的命名）就漏。

已改成：名字弹完再**按值**扫（`VAULT.scrub_text(v) != v`），命中先弹后抛
`CredentialBreach`，`inner/loop.py` 与 `AnonymityBreach` 一并 re-raise。
带正对照的测试在 `tests/test_desk_sealing.py`。提交 `6803d980`。

**这条记在这里是因为它是本轮最该被复制的做法**：我三世把这件事整个写成「等裁决」，
而其中有一半从来不需要裁决。**下次写「阻塞」之前，先拆一下有没有一半是自己能动的。**

## 五、顺带：一条不属于我领地、但没人会撞见的发现

`theoria-arm` 的归档里，**264 个 `upstream_pin` 值中有 44 个是字面量
`<redacted:key-shaped>`** 而不是十六进制摘要——凭据脱敏器
（`proxy/redact.py:_KEYISH`，对 32+ 位字母数字与 UUID 命中）吃掉了形状像密钥的
sha256。后果是归档里有 44 个 provenance pin 是空的。
`_KEYISH` 有 `STRUCTURAL_KEYS` 白名单，`upstream_pin` 不在里面。
这是 `proxy` 领地的活，我不动它，写在这里免得它继续没人看见。
