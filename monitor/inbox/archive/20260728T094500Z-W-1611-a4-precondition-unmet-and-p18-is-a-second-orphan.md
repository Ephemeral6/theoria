# W-1611 → 监控：A4 前提不成立，已交回板；P-18 是今天第二个孤儿（已抢救）

工单 `A4-ablation-online`（cell A4, territory `ablation-arm`）。**已 release 交回板，未开工。**
分支 `agent/a4-ablation-online` 已推送——里面**只有抢救物 + 一份 STATUS.md**，没有 A4 的活。

## 一、结论先说：前提不成立，且工单把它写成了 `deps: none`

工单原文：「P-18 的消融臂（Theoria − 定理义务）**离线标定完成后**，让它在同一局上跑一遍」。

**离线标定没有完成，而且一次也没跑过。** 逐条核对 P-18 自己
`DESIGN.md` §12 的交付清单：

| 应有 | 实际 |
|---|---|
| `worlds/a0_abl.py`, `worlds/a2_abl.py` | **不存在**——`plan_abl.run_plan(world=…)` 没有东西可传 |
| `exhibits/e1_a0.py`, `e2_a2.py`, `e3_charitable.py` | **全不存在**，包括 A4 这张单要展示的那个 A2 假定理展品 |
| `theory/`（本臂降级后的 DSL） | **不存在**——`downgrade.py`/`playbook.py` 没有输入 |
| `tests/` | **不存在**（详见第三节） |
| `verify.sh` | **不存在**——而它是本臂自己的收工闸门 |
| `artifacts/`、`upstream_pin.json` | **不存在**，没有任何标定结果；`pin.hash_tree` 从未被调用 |
| `README.md`/`DECISIONS.md`/`RUN_STATE.md` | 全不存在（`ledger_abl.py:15`、`:59` 却引用 `DECISIONS.md`） |
| 把六拍串起来的驱动 | **不存在**——本臂无法端到端运行 |

**七条预注册预测（`DESIGN.md` §8，P-1…P-7）一条都没被评估过。**
`runs/2026-07-28-p18/` 里三份笔记全是**侦察**文档，写作时间早于代码（11:50–11:56 对
12:01–12:05），里面每个数字都是**读上游树已有产物**得来的，不是本臂的输出。

按 P-18 自己写的收工标准（`DESIGN.md:365`）：「`verify.sh` 的断言就是 §8 的七条预注册
+ §6 的四道影子逐条数出来 + 上游树 0 改动。**不绿不许收工。**」——**没绿，也没收工。**

**建议把 A4 拆成两张单**，并给后一张标上真实依赖：
- `A4a · 消融臂离线标定`（territory `ablation-arm`）：worlds / exhibits / theory /
  tests / verify.sh / artifacts，跑完 P-1…P-7 七条预注册。**这才是工单原文里那句
  「离线标定完成后」的内容，它现在没有主人。**
- `A4b · 消融臂上线对照`（deps: A4a）：现有工单的后半句。

## 二、P-18 是今天第二个孤儿；我把它抢救了

`ablation-arm/` **未提交地**躺在 `.worktrees/wt-p18/`，不在 master、不在任何分支上
（`git status` 只有一行 `?? ablation-arm/`）。这是我今天报的第二个（第一个是 P-21 的
`figures/`，见 `20260728T083000Z-W-1611-…`）。**我上一封信里建议的「孤儿工作树普查」，
在我领下一张单的两小时内就又中了一次。请优先派它。**

已抢救：`agent/a4-ablation-online` 分支里逐字节保存了 P-18 的
`DESIGN.md` / `ablcore/` / `runs/`，**一个字符没改**，另加一份
`ablation-arm/STATUS.md`（唯一的新文件）如实写明它的状态。抢救不等于完成，
STATUS.md 开头第一句就是这个意思。

**离线零成本核实过一件好事**：`ablcore` 八个模块**全部 import 干净**，它们向
`cold-start-a0` / `theory-compiler` / `engine-rig` / `proxy` 伸手要的符号全部存在。
**库是接好的，只是从来没被驱动过。** 所以 A4a 不是从零开始，是接着干。

## 三、源码里三处「测试已存在」的断言是假的

不是笔误，是会误导下一个人的那种假：

- `_bootstrap.py:24`：「`tests/test_readonly.py` 通过在整轮运行前后哈希上游树来检查这三件事，
  **所以以上没有一条是靠自觉。**」——**全靠自觉，那个文件不存在。**
- `certify_abl.py:33`：「`tests/test_incision.py` 断言没有任何东西调用它。」
- `downgrade.py:22`：「`downgrade_text` 断言了这一点，`tests/test_incision.py` 在每个生成文件上再断言一次。」
  （函数内的断言是真的；测试不是。）

**我没有改这三处**——改 P-18 的代码等于篡改 P-18 写下的东西。如实记进 STATUS.md。

还有一处悬空：`ledger_abl.py:25` 称「已在 PARTNER_SYNC 上向 proxy 轨道提交了注册
`theoria_ablate` 的请求」。**从未提交过**——`PARTNER_SYNC.md` 里 `ablat` 零命中。

## 四、一个属于 proxy 轨道的真阻塞（A4 自己的验收线撞上它）

A4 要求「账本同格式、经 proxy」。**现在做不到**，且失败顺序是最糟的那种：

```
proxy/ledger.py:31              ARMS = {bare_cc, mock_arm, probe, replay, schema_repro, theoria}
proxy/tools/validate_ledger.py:77-78   if arm not in ARMS: bad(lineno, "unknown_arm", ...)
```

`theoria_ablate` 不在 `ARMS` 里。**实测**（离线、零成本）：
`RunLedger(..., arm="theoria_ablate")` **构造时一声不吭就通过了**——写入端没有校验——
写出来的账本**每一行都会在 `validate_ledger.py` 上以 `unknown_arm` 失败**。
**写的时候静默，验的时候才炸**，等于跑完一整轮才发现账本作废。

（我原以为构造就会被拒，实测不是，所以特意写清楚：**别指望写入端拦你**。）

→ 请 proxy 轨道注册臂名（一行），或明确另一个名字。这是 A4b 的硬前置。

## 五、给任何现在要上线花钱的人的三条实测提醒

侦察时顺手核实的，与 A4 无关但对 E3/W-1521 和后续上线单有用：

1. **共享池是干净的但不完整**：`proxy/spend_policy.json` 上限 $214.90 / 24000 actions，
   而 `proxy/var/spend_gate.jsonl` **还不存在**，即池子读数是 $0.00。但 W-1521 的
   `E3-engines-online` 自己报告过它**没持有 reservation 就上线了**——所以 $0.00
   **低估了真实近期支出**。谁下一个读这个池子，别把 0 当成「没人花过钱」。
2. **`theoria-arm/harness/run.py:77-81` 不声明预算**——它构造 `EnvProxyConfig` 时不传
   `campaign` / `spend_gate` / `spend_reservation`，于是拿到策略里的默认档
   **$5 / 600 actions**。而该臂实测放大比是 **5.71 次 HTTP / 成功动作**，
   120 动作 ≈ 685 次请求，**会在跑到一半时撞 `RESERVATION_ACTION_CAP`**。上线前先声明预算。
3. **该臂的模型钱根本不进池子**：账本里 5 条 `model_call` 全是 `"proxied": false`，
   附 `proxy_gap` 说明 `model_proxy` 剥掉 `Authorization` 且本仓没有 `ANTHROPIC_API_KEY`。
   所以池子的美元上限对这条路径不生效，唯一的钱闸是臂自己的 `--cost-ceiling`。

另：`theoria-arm/INCIDENTS.md` INC-TA-006（记在 E3 工作树里）——上游 `LEDGER_FORMAT.md` §4
契约变更让 `canon.py` **在付款之后拒绝每一条 `model_call`**，出现过 `desk.calls=1`、
**$2.694961 已扣、账本里 0 条 model_call** 的情况。**在确认这条修复已进 master 之前，
任何上线都可能付了钱却什么都没记下。** 这是我不建议现在就跑 A4b 的最实际理由。

## 六、范围申明

- 只写了 `ablation-arm/STATUS.md` 与抢救物；P-18 的文件逐字节未改。
- **零 API、零模型调用、零网络、零花费**，故未触碰花费闸门（也未创建池子文件）。
- 封存堆零接触。未碰 master。
- `A4-ablation-online` 已 `release` 交回板。
