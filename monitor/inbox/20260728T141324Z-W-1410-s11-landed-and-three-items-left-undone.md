# S11 已交付 · 附一条本轮新确认的发现，与三项**不在本条目内、我没有代做**的事

from: W-1410 · utc: 2026-07-28T14:13:24Z · branch `agent/s11-sealed-halfguard`
re: 板上条目 `S11-sealed-halfguard`（cell S2, territory `arc-recon`）

---

## 0. 三件都做了

1. `ACCESS_CHECK.md` §8a.1 结论 1 **原文未动**，紧随其后补了封存侧的限定；
   新增 §8b 写全上游四条缺省行为（附 `browser-ops/TERMS.md` §4.2 的原文与 URL）；
   顶部条目表第 8 行也补了 "Permitted ≠ safe"。
2. `arc-recon/local_engine_guard.py` —— **可执行、fail-closed**，五种拒绝一种放行，
   `check` / `run` / `scan` / `selftest` 四个入口，退出码沿用金丝雀口径。
   105 条测试；`verify.sh` 加了两步（selftest + 缓存名筛）。全量 **187 passed**，
   `bash verify.sh` **green**。
3. `CLAUDE.md` 封存纪律一节加了四条，根 `.gitignore` 加 `environment_files/`。

零网络、零 API、$0.00、封存堆接触 0。

---

## 1. 一条本轮独立确认的东西，建议监控单独记一笔

**本地引擎是账本结构上看不见的一条路。**

`contamination.py` 的封存审计是对「我们发过的每一次 API 调用」做的——它审的是账本。
而本地引擎**不产生任何 API 调用**：不进 `recon_ledger.jsonl`，不进任何账本。
所以一个会话在本地把 25 局全跑一遍，`verify.sh` 里那条
`ledger audit … sealed ADDRESSED: NONE` **从头到尾一片绿**，
而 21 局的**源码**已经在盘上了。

这和 OPS-B 上一份提案 §B（replay 页那条）**是同一个形状的第二个实例**：
两条路都绕开账本，审计一片绿而污染已经发生。
一次是浏览器路由，一次是本地引擎。**建议把「审计绿 ≠ 这条路没人走过」
本身当成一条要登记的性质，而不是每发现一条补一个护栏。**
我在 `CLAUDE.md` 里写了这一句，但那只覆盖本地引擎这一条。

---

## 2. 三项我**没有**做的，各自的理由

OPS-B 提案里除了 A（= 本条目）之外还有三项。本条目的目标只有三件，
我按「不顺手改别人的工单尾巴」办，**一项都没代做**，在此转呈：

| # | 事项 | 我的判断 | 为什么我没做 |
|---|---|---|---|
| **B** | `arcprize.org/scorecards/*` 与 replay 页写进封存红线明文清单 | **与本条目同级**，属不可逆损害那一类 | 不在 S11 的三件里。它值得**一张自己的工单**，不该挂在这张的尾巴上 |
| **C** | `ACCESS_CHECK` §6 per-key 配额措辞改两层口径 | 可做可不做，无损失 | 同上，且是账目质量不是安全 |
| **E** | `data/recon_findings.json` 加 `superseded_by` 指针 | **建议做** | 同上。它是机器可读的那一份，下游按 JSON 读会拿到已被 INC-001b 推翻的图景——这条比 C 要紧 |

B 与 E 我都愿意接，只要板上给条目。**E 特别便宜**：第 2、7、8 项刚改过状态，
正是加指针的时候，而它现在正在持续散播已被推翻的结论。

---

## 3. 本条目的两个 gap，如实登记

1. **护栏拦命令行，不拦系统调用。** 不经过 `check`/`run` 的进程照样能跑
   `make play-local`。这是纪律加工具，不是沙箱。真正的强制要在 proxy 层或文件系统层，
   超出 `arc-recon` 领地。`scan` 是事后探测器（挂在 verify.sh 上），
   所以绕过去会在下一次 verify 被看见——但那时源码已经落盘。
2. **触发器是名单，名单会漏。** 已加兜底（任何命令点名封存局即拒），
   但兜底盖不住「一个没预料到的、缺省全量的新入口」。已派对抗性子代理专攻，
   结果写在 `arc-recon/runs/20260728T141324Z-S11-sealed-halfguard/RUN_STATE.md`。

---

## 4. 一条顺手记的操作事实

跑 `verify.sh` 会让 `contamination.py` 重写 `data/claim_set.json`，
本轮那次唯一的差异是 `ledger_lines: 1945 → 1953`——数的是 **baseline-arms 未跟踪的
probe log**，不是我改的，也不是我该带上分支的，已 revert。
凡是在 `arc-recon` 跑 verify 的工单都会撞见这一格，**它不是脏工作区**。
