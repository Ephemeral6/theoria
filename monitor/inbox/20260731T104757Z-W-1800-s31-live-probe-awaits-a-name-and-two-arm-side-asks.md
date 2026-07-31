# W-1800 · S31 的真臂探针已备好未发；另有两条跨领地请求

- 工人：`W-1800`（cleanup campaign 2026-07-31 复工批次）
- 时刻：2026-07-31T10:47:57Z
- base_commit：`6fabcc7e`
- 分支：`cleanup2/s31-a10`（worktree `.worktrees/s31-a10/`，未推送、未合并）
- 领地：`proxy`
- 板件：`monitor/board/claimed/S31-a10-said-done-prove-it.W-1800.md`
- 一句话：**A10 与 S31 自身都已在 master 上，不必再判；这一轮把「文档与代码
  必须同口径」做成了闸门，并把要花钱的那一步备成一条命令，等署名。**

本文件只提出请求，不代替任何领地动手。

---

## 1 · 要花钱的那一步：备好了，没发

S31 的第 2 项要求一次最小真臂调用。诊断的那一半 2026-07-30 已在离线完成
（写入端没坏：`run_game(arm='bare_cc')` 打回环 mock 写出了 61 条 `arm: bare_cc`
的记录）。剩下的只有**轴 2**——「这次运行确实出了本机」——而轴 2 要花钱，
花钱由会话主人把关。

所以这一轮**没有发起任何网络调用，$0.00**。共享池在本轮前后一致：

```
pool theoria-shared-2026-07  (policy 732778326d64)
  spent    $  36.1423 / $214.90     7425 / 24000 actions
  held     $   0.0000                 0 actions   (0 live reservation(s))
```

要放行，是一条命令：

```bash
cd <checkout>/proxy/runs/20260731T104757Z-S31
python live_probe.py --go --authorised-by "<谁批的，在哪说的>"
```

预算已算好，写在 `proxy/runs/20260731T104757Z-S31/LIVE_PROBE_PLAN.md`：

| | 档 1（默认） | 档 2 |
|---|---|---|
| ARC 上游 | 真 | 真 |
| 模型上游 | 回环 mock | 真 |
| 最坏花费 | **$0.000000** | **$0.009688** |
| ARC 请求 | 4 | 4 |
| 满足轴 2 | 是 | 是 |

`reserve("s31-live-arm-probe", usd_cap=0.05, action_cap=10, holder={..., "undeclared": False})`
——**不是** `default_run_caps` 的 $5.00 / 600 actions。`python -m proxy.runner`
的 CLI 没有 `--usd-cap`，所以走 CLI 会自动吃下那个默认值，是它可达上限的 500 倍；
这也是这一步是脚本而不是那条命令的原因。

不发是有理由的，不是省事：只满足轴 1 的记录 `--mock --arm bare_cc` 花 $0.00
就能造出来，而 2026-07-29 那次核查只问轴 1。**为了满足一条「关于真臂记录」的
要求而制造一条真臂记录，正是这一板件要裁的那件事。** 两轴必须同时为真。

## 2 · 请求 A（三条臂领地）：账本里零条真臂记录，缺口在臂侧不在 proxy

`proxy/DELIVERY_RULING.md` §4 已经记着这条，但它至今 **unassigned**。具体到可动手：

- `theoria-arm`：**只需配置**。`harness/run.py` 已经接受 `ledger_path` 参数，
  但 `main()` 从不往下传。
- `baseline-arms`、`ablation-arm`：需要改源码；`ablation-arm` 另有设计决定
  D-AB-004 指向相反方向，得先裁。

请求：把它拆成三件分派给三条臂领地，而不是继续挂在 `proxy` 名下。
`proxy` 提供账本与钱门，它不决定臂什么时候真跑。

**在那之前，`proxy/var/ledger.jsonl` 里零条真臂记录是预期状态**，任何核查不应
据此判 A10 未交付——这一点 `proxy/tools/audit_delivery.py` 已经可执行地写下了。

## 3 · 请求 B（仓库共同地）：`.env.example` 缺 `ANTHROPIC_API_KEY`

档 2 需要 `ANTHROPIC_API_KEY`，而 `.env.example` 里只有 `ARC_API_KEY`。
探针在**取预留之前**就检查它并拒绝（`refusals.txt` 第 3 段），所以付不起的运行
不会先占住池子的余量再失败——但变量名本身没有被文档化。

请求：在 `.env.example` 里加一行 `ANTHROPIC_API_KEY=`（只加变量名，不加值）。
`.env.example` 是仓库根的共同地，不在 `proxy` 领地内，所以这里只提请求。

## 4 · 顺带一条给核查方法的教训

判断一条分支是否「已做未合」时，**先读 `git log master..<branch>`**：
输出非空但只含 merge commit，是「分支落后」的签名，而它和「分支领先」在只数行数时
长得一模一样。S31 自己的分支就是这种情况——`master` 反而比它新 1115 行，
合并它是回退。已写进 `proxy/DELIVERY_RULING.md` §7。
