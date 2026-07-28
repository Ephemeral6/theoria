# DRIFT-probes-have-hardcoded-scope-that-stopped-growing

severity: medium
dimension: 监控自身漂移（三个探针的扫描范围是写死的清单，仓库长出新目录后它们看不见）

evidence: 审计区间 `3822815..1a8ed00`（26 个提交、161 文件）。三处同因，合并成一条。

**(1) `TERRITORIES` 清单停在九个目录，仓库已有十九个。** `monitor/scan.py:218-220`：
```python
TERRITORIES = ["engine-rig", "theory-compiler", "cold-start-a0", "cold-start-a2",
               "a0-spike", "baseline-arms", "arc-recon", "proxy", "battery",
               "monitor"]
```
根目录下**不在清单里**的产出目录：`theoria-arm`、`exam`、`fuzzlab`、`figures`、`worldgen`、`ablation-arm`、`cold-start-a3`、`browser-ops`、`papers`。这个清单被两个探针共用（`:269` 的 `probe_conflicts`、`:302` 的 `probe_provenance`），所以**留痕核查与跨领地冲突检测，对这九个目录同时是瞎的**。

**(2) 后果之一：花钱的那条臂没人查留痕。** 实测各目录 `runs/` 与 `MANIFEST.json` 覆盖：
```
theoria-arm  runs=11  MANIFEST.json=4      <- 在线臂，真花 API 钱
figures      runs=3   MANIFEST.json=2
ablation-arm runs=2   MANIFEST.json=1
fuzzlab      runs=1   MANIFEST.json=1      (齐)
worldgen     runs=1   MANIFEST.json=1      (齐)
exam         runs=2   MANIFEST.json=2      (齐)
```
`theoria-arm` 缺 MANIFEST 的七个 run 里，四个是首次在线接触的 `-salvage` / `-aborted` 变体，一个是 `preflight-20260728T012031Z`——**正是最需要留痕的那一类**（失败 run 同等归档是 P-12 立的口径）。而 `monitor/state.json` 的 `provenance_scan` detail 里，`theoria-arm` 一个字都没有出现过。
（另两个 `runs/pytest-*` 目录我查了，`theoria-arm/.gitignore:6` 已排除，是测试临时件，不算问题。）

**(3) 新造的 `verify_gates` 探针看不见它自己的立案案由。** `monitor/scan.py:522-527` 的 docstring 逐字写：
> DRIFT stop-hook-verify-gates-are-decoration: **C2 已合并，它自己命名的 `a0-spike/verify.sh` 从未被造出来**，合并时无人发现。

而扫描范围是：
```python
for d in ("monitor/board/items", "monitor/board/claimed", "monitor/board/done"):
```
C2 的工单在 `monitor/prompts/archive/superseded-by-board/C2-semantics-migrate.md`——**不在这三个目录里**。实测探针本轮报 risk，抓到的是 `ablation-arm/verify.sh`（A4a 声称），`a0-spike/verify.sh` 一次都没出现。也就是说：**为某个案子造的探针，结构上看不见那个案子**，而 `a0-spike/verify.sh` 至今仍缺（欠 3 周期），现在既不在板上、也不在探针视野里，等于从台账上消失了。

claim: 三个探针都用写死的范围清单，而仓库这两天长了九个新目录。写死本身不是错——错在**没有任何东西在提醒清单已经落后**。这与我上一轮报的盘面陈旧是同一个病换了层皮：那次是手写的**值**落后于树，这次是手写的**范围**落后于树，而且更隐蔽——盘面陈旧至少看得见一个数字不对，扫描范围漏了目录，页面上什么都不会发生，它只是安静地少查了九个地方。

suggest:
1. `TERRITORIES` 改成推导：根目录下含 `runs/` 或 `STATUS.md`/`DECISIONS.md` 的目录即为领地，写死的只保留排除表（`.git`、`node_modules`、`monitor` 自身按需）。这样新目录一落盘就自动进入留痕与冲突两道检查。做不到就退一步：加一个极小的探针，比对根目录实际子目录与 `TERRITORIES`，有差集就报 note——**让清单陈旧本身可见**，这是最低成本的一条。
2. `verify_gates` 的扫描范围加上 `monitor/prompts/**`（含 `archive/`）。工单会从 prompts 迁到板上，但迁走不等于它的收工承诺被兑现——历史工单里未兑现的闸门正是这个探针该记住的东西。
3. `theoria-arm` 的七个 run 补 MANIFEST（`preflight-20260728T012031Z` 与四个 salvage/aborted 优先，用 `retro:` 前缀标注回溯）。它是三臂里唯一真花钱的一条，Phase 4 回算时每一次在线动作都要能追到出处。
4. `a0-spike/verify.sh` 重新挂到板上——它已经欠了三个周期，且现在连被谁记着都没有了。

（本轮同时复核、结果是好的，一并记在这里免得另开文件：**append_only 的判据已改 `--first-parent`、`BASELINE` 降为 1**，实测 green；且它在落地当天就正确分类了一个新案例——`e24f140` 又是一次分支内自我订正，全历史三笔删除、主线仍只有 `63ef0bf` 一笔，探针没有误报。**ALL.md 已用新段落撤销 `6dec6f7` 的案底并重画了边界**，形态上也守住了「新段落 supersede」这条纪律本身。**释出许可已接进 `p1-access`** 并开了板项 `R2-release-licence`；那张单子里「**不要自行去申请许可——那是人的决定，写进 needs_human**」这一句，比我上一轮建议的「开一件工单去发那封申请」**更对**，我的建议应以它为准。唯一还没跟上的是 `WP10` 的 `scale` 仍逐字承诺「对标 Schema：全公开集 artifacts」，而 R2 已经判定这一项在帧数据上做不到——量小，不单开报告，请顺手改。）
