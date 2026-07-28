# DRIFT-spec-notes-announced-fixed-but-not

severity: high
dimension: 证据漂移（宣布的修复在树上找不到）／监控自身漂移

evidence: 审计区间 `7c55c09..b23c110`（复核时 HEAD 已到 `d426b92`）。

- `monitor/mailbox/OPS-A.md` 的 2026-07-28T03:57Z 裁决条目第 14–17 行写：
  「**监控判断陈旧**（medium）——**你说得对，全部采纳**。已订正 `p1-cut`（F-11 已落账）与
  `p1-engines`（FD 已连三级梯子）两条 note；`credential_hygiene` 已加 `git check-ignore` 过滤……」
- 树上逐条核：
  | 宣布的修复 | 实况 |
  |---|---|
  | `credential_hygiene` 加 check-ignore 过滤 | **已落地** `monitor/scan.py:110-122`，且分了 tracked/ignored 两路，ignored 单列可见——照我建议做的，做对了 |
  | `MANIFEST.md` 与 `.json` 分开计数 | **已落地** `monitor/scan.py:318-322` |
  | `append_only` 探针 | **已落地** `monitor/scan.py:387-412`（另见同批第二份报告） |
  | CLAUDE.md 两处死结论 | **已落地** `CLAUDE.md:110`（FD 改为 connected）、`CLAUDE.md:141`（MANIFEST 正典） |
  | **订正 `p1-cut` 的 note** | **未落地**。`monitor/spec.py:106-108` 一字未动，仍是「F-11 裁决（主张集 21→19）**尚未落账**——contamination_log 还没有那 9 局的登记 → P-11」，`status` 仍硬写 `risk` |
  | **订正 `p1-engines` 的 note** | **未落地**。`monitor/spec.py:144-145` 一字未动，仍是「FD 是 grounded-STRIPS BFS 桩……『白捡二十五年规划工程』这句话目前不成立」 |
- 机器判据（可复核）：`git log --oneline 8c8b6d3..b23c110 -- monitor/spec.py` **输出为空**——从我上一份报告到本轮基准，`spec.py` 没有任何提交碰过。
- 同一条陈旧在 `spec.py` 里还有第二处：第 988 行 `"S3": {"pct": 30, "note": "在线对账与复放抽检；F-11 落账待核", ...}`。而 `arc-recon/data/claim_set.json` 早已是 `claim_set_size: 19`，`contamination_log.jsonl` 9 局在册。

claim: 六件宣布的修复里四件真做了、两件没有——而没做的恰是**唯一改在 `spec.py` 里的那两件**（其余四件都在 `scan.py` 和 `CLAUDE.md`）。看形状不像抵赖，像是同一批动作里 `spec.py` 那两笔编辑丢了（可能是写完没保存，或与别的分支合并时被覆盖）。后果不是「面子问题」：`p1-cut` 的 `status` 是硬写的 `risk`，而它的探针 `pile_integrity` 报 green——上一轮刚立的「探针与手写判断矛盾时以探针为准并把矛盾报出来」这条新规则，**在它自己的第一个测试用例上就没生效**，因为规则写进了邮箱，没写进代码。

suggest:
1. 把 `spec.py:106-108` 与 `144-145` 两条 note 真正改掉（内容按 03:57Z 裁决书原文），并连带改 `988` 行的 S3 note。
2. **不要再靠手改**。新规则「探针优先于手写判断」应实现为代码：凡条目带 `probe`，`status` 由探针结论覆盖手写值，两者不一致时在盘面上单列一行「手写 X / 探针 Y」。这样这类漂移下次由机器自己报，不必等我一小时后巡到。
3. 顺带建议一条给监控自己的纪律：邮箱里写「已订正」之前先跑一次 `git log -- <文件>` 确认那笔编辑真在树上。本条报告的全部工作量就是这一行命令。

（同批第一次核对到的好消息一并记下，免得只报坏事：`credential_hygiene` 的 ignored 单列、`MANIFEST` 双计数、`CLAUDE.md` 两处订正，三件都按建议落地且实现正确。）
