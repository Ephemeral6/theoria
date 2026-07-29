# 致 team@arcprize.org 的信 —— 草稿，**未发送**

状态：**草稿。本会话没有发送、也不会发送任何邮件**——对外发信属须由人执行的动作。
起草：OPS-B · 2026-07-28T10:25Z · 依据 `TERMS.md` §5 与 §7、`arc-recon/ACCESS_CHECK.md` 第 8 项

`arc-recon/ACCESS_CHECK.md` 第 8 项结案时明确把这封信记为未了结项
（原文："see §5 of `browser-ops/TERMS.md` for the letter that has not been sent"）。
本轮把它写成可直接发送的形态，**内容与收件人都需人过目后再发**。

---

## 为什么只剩三个问题（发信前先读这段）

原本有更多。第一轮列了三条，第二轮读到 `arcprize.org/policy`（Testing Policy）后
砍掉了大半——那份文件明文允许"在公开数据上独立测试并公开自己的分数"，
并且通篇预设自动化 agent 是正常玩法。剩下的三条是**它答不了的**：

| # | 问题 | 为什么非问不可 | 后果的可逆性 |
|---|---|---|---|
| 1 | 自动化访问的许可 | Testing Policy 的口径是**推定**，ToS §3(3) 的字面是**禁止**；只有 ARC 能说哪个管用 | **不可逆**（封号） |
| 2 | 释出原始帧/轨迹样本 | Testing Policy 只覆盖"我们的分数"，不覆盖"ARC 的内容" | 可逆（不发就是了） |
| 3 | 429 的退避曲线 | 文档只写 "exponential backoff"，无基数、无上限、无 `Retry-After` | 可逆（保守退避即可） |

**只有第 1 条是真正的阻塞项。** 若人手紧，只发第 1 条也是合理的取舍。

---

## 收件人与主题

* 收件人：`team@arcprize.org`
* 主题建议：`Research use of the ARC-AGI-3 API — three compliance questions`
  （提额不是本信目的；`rate_limits` 页要求提额用主题 "Increase Rate Limits"，**别用那个**，
  会把这封信路由到错误的流程里）
* 署名：需人决定用哪个身份与邮箱。**本仓不记录发信人邮箱**——
  账户邮箱属个人数据，而 Phase 4 释出清单会公开全部 tracked 文件。

---

## 正文（可直接复制）

> Hello ARC Prize team,
>
> We are a small independent research project using ARC-AGI-3 as an evaluation
> environment. We are not preparing a leaderboard submission. To date we have
> played only four games from the public set, via the REST API with a registered
> key, and we have read the Terms, the API docs, and the Verified Testing Policy.
>
> Three questions we could not settle from the published documents:
>
> **1. Automated access.** The Testing Policy describes agents playing the games
> as the normal mode of use, and the API exists to be driven by them. The site
> Terms (last updated 3 June 2024) state that a user "will not access the
> Services through automated or non-human means, whether through a bot, script or
> otherwise", and separately prohibit "any automated system … scraper". We read
> the Testing Policy as the controlling document for benchmark use and the Terms
> clause as generic website boilerplate that predates the ARC-AGI-3 API — but
> that is our reading, not your statement. **Can you confirm that running an
> automated agent against the public game set with a registered API key, for
> non-commercial research, is within permitted use?** We are asking because the
> downside is account termination, which we cannot undo.
>
> **2. Publishing reproducibility artifacts.** The Testing Policy says we are free
> to test on public data and share our scores independently, with the three
> disclosures you ask for, and we intend to comply with those in full. Our
> release will be limited to our own measurements: scores, metrics, frame
> *hashes*, methods, and conclusions. **We would like to know whether a small
> number of raw frames or short trajectory excerpts may be included as evidence
> for reproducibility**, or whether that falls under the Terms' restriction on
> republishing Service content and would need written permission. If permission
> is possible, please tell us the attribution wording you want.
>
> **3. Rate limiting behaviour.** The docs state 600 RPM with an exponential
> backoff mechanism and a 429 `RATE_LIMIT_EXCEEDED` response, but do not document
> the backoff base or ceiling, and we see no `Retry-After` or `RateLimit-*`
> headers to key off. **Is there a recommended client backoff policy?** And
> **does a 429 have any effect on an open scorecard** — for instance, does it
> count against the 15-minute inactivity window, or can it invalidate a card?
> We ask so we can be conservative rather than guess.
>
> We are happy to share what we have measured if it is useful to you. Two things
> we found while reading may be worth a line in the docs regardless of your
> answers: the REST overview's session-affinity requirement is easy to miss, and
> a client without a cookie jar pays roughly a 10× retry amplification without
> ever seeing an error that explains why; and the rate-limit page's 429 is absent
> from the OpenAPI spec, so a generated client will not handle it.
>
> Thank you for the benchmark, and for publishing the Testing Policy — it
> answered several questions we would otherwise have had to ask.
>
> — <署名>

---

## 起草时的三条自我约束（写下来免得后人以为是随口写的）

1. **不索取豁免，只求澄清。** 第 1 条问的是"我们这样用算不算允许"，
   而不是"能不能给我们开个口子"。前者若答"不允许"，我们就停；后者会把一次澄清
   变成一次谈判，而我们没有谈判的筹码，也不该有。
2. **主动交代我们做了什么。** 信里明说"只玩了公开集里的四局"、"持注册 key"、
   "不准备提交排行榜"。隐去这些会让第 1 条的答复失去意义——他们答的是一个不存在的用例。
3. **附赠的两条发现是真心的，不是筹码。** session affinity 那条我们付了约 10× 的
   重试放大才发现（`arc-recon/ACCESS_CHECK.md` §6b/§6c，探针 20/20 vs 0/20），
   429 不在 OpenAPI spec 里那条是他们的文档缺陷。**即使三个问题全被拒答，这两条也照给。**

## 未决

* **谁发、用哪个邮箱、用什么身份署名** —— 归人工。本仓不记录发信人邮箱。
* 发出后应把发送时间与回信（若有）记进 `browser-ops/RUN_STATE.md`，
  并在 `arc-recon/ACCESS_CHECK.md` 第 8 项里把那条"未发送"的注记闭环
  ——**后者归 arc-recon，本轨道只读**。
