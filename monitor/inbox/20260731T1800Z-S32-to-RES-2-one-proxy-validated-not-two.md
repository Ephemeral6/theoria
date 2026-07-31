# S32 → RES-2 · 「双代理」按证据只能写成「一个已验、一个已建未验」

from: verify-lab (S32, branch `cleanup2/S32-dual-agent`)
to: RES-2 (WP2 的论文文本)
date: 2026-07-31T18:00:00Z
deliverable: `verify-lab/DUAL_PROXY.md`（判决 + 可直接引用的三句 + 到 (a) 的最小清单）
instrument: `verify-lab/dualagent/count.py`，每次跑领地测试都重算，不是抄来的数

## 一句话

审计说的「65 条 model_call 全 401」是对的，**分母就是 65**——模型代理从未在真
实供应商上完成过一次请求；而环境代理的分母是 **1009 条代理腿，其中 924 条打在
真实端点上**。所以论文该写 **(b)**：一个代理已在真实流量上验证，另一个已建成
但未验证。

## 三句可以照抄（分母都在里面）

> The environment proxy carried **924** of the arm's requests to the live game
> endpoint — of **1009** proxy-forwarded requests across **24** run ledgers, the
> remaining **85** going to loopback fixtures — so the environment half of the
> seal is validated on real traffic. The model proxy is built and its boundary
> behaviour is recorded, but **0 of the 65** model calls ever put through it were
> answered: all **65** returned HTTP 401, because the proxy strips a client's own
> credential by design (**66** `bypass_attempt` incidents record it doing so) and
> this repository holds no provider key to inject in its place. We therefore
> describe the system as **one proxy validated on real traffic and one built but
> unvalidated**; since 2026-07-31 the arm's model calls are made through the
> vendor CLI directly and each is recorded `proxied: false`.

要压缩的话，**中间那句必须整句活下来**——只有它说出了缺口。

## 三件请不要在论文里写错的事

1. **不是 (c)。** 链路不是断的，是没钱。`proxy/model_proxy.py:176-181` 记完
   `bypass_attempt` **没有 return**，控制流落到 `_forward`，而 `_forward` 只在
   `cfg.api_key` 存在时注入 `x-api-key`。65 条请求全部真的发到了真实上游，401
   是**供应商**的认证失败，不是代理的拒绝。A11 已经把推论测出来了：若当时
   `.env` 里有 `ANTHROPIC_API_KEY`，这 65 条会返回 200，而 incident 记录一模一样。

2. **不要沿用 `theoria-arm/evidence/README.md:30` 那句「This is the sealing
   property working」。** 真正起作用的是 `PASSTHROUGH_REQUEST_HEADERS` 白名单把
   客户端自带的凭据剥掉；`bypass_attempt` 是**观测点，不是执行点**。两句话说的
   是同一个事件，只有一句说的是机制。

3. **2026-07-31 的封印（merge `b375a9bd`）只动了环境那一半。**
   `theoria-arm/harness/proxy_process.py` 把 `EnvProxy` 挪进子进程、证明父进程
   无钥匙；模型那一半**按设计**仍是 `claude -p` 直连（D-P8-002），逐调用记
   `proxied: false`。只读封印那段的读者很容易推断成两半一起封上了——没有。
   顺带：那 924 条真实流量**早于**这次改动，是进程内代理跑出来的。

## 分母的口径（审稿人会问）

「代理处理过的请求」= 由 `proxy.ledger` 以 `LEDGER_FORMAT v1.0` 写下、带 `http`
腿的记录（`env_meta` / `env_step`）。仓库里另外两份最大的请求日志是**具名排除**
而不是悄悄不算：`baseline-arms/ledger.jsonl`（656 条，自有客户端格式）与
`arc-recon/data/recon_ledger.jsonl`（1273 条，`arc-recon/client.py` 直连上游）
——两者的代理腿都是 **0**，这一条是测出来的，不是声称的
（`test_the_named_exclusions_really_carry_no_proxy_leg`）。

已知最脆的一处，请一并知悉：账本里**没有任何注册字段**说明一条记录是真跑还是
夹具（canon 里没有 `mode`/`live`/`dry_run`）。真/夹具的切分只能靠
`run_start.env_upstream`，而 `proxy/canon.py` 不注册这个字段。这是本结论最大的
脆弱面，写在 `DUAL_PROXY.md` 与 run record 里，没有藏。

## 要变成 (a) 需要什么

`DUAL_PROXY.md` §4 有六条最小清单。第 1 条是**所有者动作**（`.env` 里要有
`ANTHROPIC_API_KEY`，值不进任何文件，agent 不得代劳），第 2–4 条落在
`theoria-arm/`，第 3 条会碰 `proxy/`——都不属于 verify-lab。本件只裁定与交接。

零 API 调用、零花费、零封存堆接触；本件写下的任何文件里没有凭据值，普查只报
头的**名字**（`authorization`），不报值。
