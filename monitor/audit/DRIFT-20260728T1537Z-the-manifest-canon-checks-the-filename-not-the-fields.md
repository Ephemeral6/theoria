# DRIFT-the-manifest-canon-checks-the-filename-not-the-fields

severity: medium
dimension: 流程漂移（留痕正典的必填字段从未被任何检查执行）／第 6 维的一个变体：纪律看起来生效、实际只查了文件名

evidence: 审计区间 `8d42373..4d6f1ee`（35 个提交、411 文件）。本条是欠了四轮的「新交付目录内容维度巡检」的产物，扫的是全仓，不只是那六个目录。

**正典的原文（两处一致）：**
- `CLAUDE.md:141`：`runs/<id>/MANIFEST.json` — required `prompt_id`, `branch`, `base_commit`, `utc`；
- `monitor/mailbox/ALL.md` 的全员通告：「必填 prompt_id / branch / base_commit / utc」。

**执行情况：全仓 33 份 `MANIFEST.json`，24 份齐全，9 份缺字段——而 9 份缺的全是同一个 `utc`，一个不多一个不少。**
```
arc-recon/runs/P-11/                                     missing utc
battery/runs/P-14/                                       missing utc
cold-start-a3/runs/p-17/                                 missing utc
exam/runs/p15-rehearsal-01/                              missing utc
proxy/runs/p9-shell-harden/                              missing utc
theoria-arm/runs/20260728T012311Z-...-aborted/           missing utc
theoria-arm/runs/20260728T014402Z-...-aborted/           missing utc
theoria-arm/runs/20260728T015354Z-g50t-first-contact/    missing utc
theoria-arm/runs/preflight-20260728T012057Z/             missing utc
```
**我查过是不是换了个键名，不是**：这 9 份里 7 份连一个含 `utc/time/date/stamp/when/_at` 的键都没有；`proxy` 那份有 `date`，`battery` 那份只有 `head_commit_at_archive`（归档时的 HEAD，不是跑的时间）。

**为什么没人发现：探针只数文件，不看字段。** `monitor/scan.py` 的 `probe_provenance` 判据是 `os.path.exists(.../MANIFEST.json)`；全文 grep `prompt_id` / `base_commit` 在 `scan.py` 里**零命中**。也就是说正典宣布了四个必填字段之后，唯一在跑的检查只检查了「文件叫不叫这个名字」。

**外加 11 个 `runs/` 目录连 `MANIFEST.json` 都没有**（`engine-rig/runs/p13-fd-real/` 有 `MANIFEST.md` 属已知的格式分歧；`theoria-arm` 占 7 个，其中两个 `pytest-*` 是 gitignored 的测试临时件不算；`theory-compiler/runs/P-10/`、`ablation-arm/runs/2026-07-28-p18/`、`figures/runs/20260728T034857Z-p21/` 是真缺）。这一半监控的探针看得见，只是没人清偿。

claim: 留痕正典有四个必填字段，实际被执行的只有「文件名对不对」。27% 的 manifest 缺 `utc`，而缺的方式高度一致——说明不是谁疏忽，是**大家照着彼此的 manifest 抄，而第一份就没写 `utc`**，没有任何一道检查把它拦下来。这与我前面报过的几条是同一个家族：规矩写在文档里，检查只覆盖了它的一部分，于是覆盖不到的那部分安静地不存在。

**这条的严重度我压在 medium 而不是更高，理由要说清楚**：`base_commit` 这四份里都有，而它比时间戳是**更强**的锚——Phase 4 回算要的是「这个数字出自哪次提交」，commit 比 UTC 更能回答。所以现状不至于让证据链断掉。但正典既然写了四个字段，就该么执行、要么改成三个；现在这种「写了不查」的状态最坏，因为它让人以为查过了。

suggest:
1. `probe_provenance` 加一句字段检查：读每份 `MANIFEST.json`，缺 `prompt_id`/`branch`/`base_commit`/`utc` 任一即列出来。这是十行以内的改动，且能立刻把上面 9 份变成盘面上的一个数。
2. 那 9 份补 `utc`（值可从 run 目录名的时间戳或该 run 的提交时间回填，标 `retro:` 说明是回溯补的）。
3. 若认为 `base_commit` 已足够、`utc` 是冗余的，**那就改正典**——把 `utc` 从必填降为可选，并同步 `CLAUDE.md:141` 与 ALL.md 的通告。两条路都行，**含糊着放着最糟**。
4. 顺带清偿三个真缺 manifest 的 run：`theory-compiler/runs/P-10/`、`ablation-arm/runs/2026-07-28-p18/`、`figures/runs/20260728T034857Z-p21/`。

**本轮同时查过、干净的两项，一并记此（沉默即健康，但这两项值得留证）：**
- **生成物手改（约束 4）**：全仓自称生成物的文件（`a0-spike/artifacts/A0.lean`、`theory_exec.py`、`ablation-arm/artifacts/*/{domain,problem}.pddl`、`theory.py` 等）逐个查提交历史，**没有一次是脱离其生成器单独被改的**——`theory_exec.py` 的三次改动都与 `pipeline/gen_exec.py` 同批（`35d3a2c` 是 v0.2 迁移，`a479e92`、`b4bee60` 同理）。约束 4 守住了。
- **红线**：本区间封存 ID 命中 6 文件，全为污染登记、release 分类清单与盘面渲染；密钥零命中；主线 append-only 零新增删除。
