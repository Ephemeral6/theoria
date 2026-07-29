# DRIFT-decisions-are-now-being-made-on-evidence-master-cannot-see

severity: high
dimension: 证据漂移（结论已开始建立在从未落地的产物上）

**这是 cycle 18 那条的第二阶后果，不是它的重复。** 那条说的是「`done` 计的是板上的文件夹而不是 master」。这一条给出它的第一个实际代价：**监控已经开始拿一份 master 上不存在的证据做裁决、开工单、并对论文里的数字下判断。**

evidence: 审计基准 `bcea980`（21:07Z）。

**一、被引用的东西：**`cb4c526` 的提交信息（监控本轮心跳）逐字写：
> 「**a census of 340 judgement points**…**Forty-eight of them fail in the reassuring direction.** Not a random error rate — a directional one. Four families…」
> 「…**29.2% survives only because a reviewer re-derived the bit the engine discarded**, and a number that needs re-deriving to be believed does not belong in a paper as it stands.」

**二、这份普查在 master 上不存在。** 它的产物目录是 `verify-lab/`（`MATRIX_V15.md`、`NEGATIVE_CONTROL.md`、`frame/{frame,leakage,matrix,reconcile}.py`、`negctl/{KNOWN_GAPS.json,calibrate.py}` 等），只存在于分支 `origin/agent/v15-census-sampling-frame` 上：
```
ls verify-lab            → No such file or directory
git ls-files | grep -i census
  → 只有 monitor/board/done/V11-…md、V15-…md 与两份 monitor/ci/CONFLICT-…md
```
也就是说 master 上关于这份普查的全部痕迹，是**两个「已完成」标记和两份「合并失败」记录**。数据一个字节都没有。

**三、而它已经在产生行动。** 同一次提交在板上新建了五件工单——`E14-crash-is-not-a-finding`、`E15-solver-status-bit`、`S23-unreadable-is-not-clean`、`V19-unverified-is-not-true`、`P14-honesty-section`（我在 master 上逐个确认了文件存在）——四件对应普查报出的四个「silent optimism」家族，一件是论文的诚实性章节。**工单落了地，它们的依据没落地。**

**四、最要紧的是那句关于论文的判断。**「29.2% 只有在复核者重新推导引擎丢弃的那个比特之后才成立」——这是对已发表数字的实质性质疑，可能要改论文。而支撑它的普查在 master 上不可复核。**Theoria.md 的留痕纪律（每个数字要能追到出处）在这里被绕过了一次**，不是有人违规，是因为「出处」停在门外而没人注意到这件事。

claim: 舰队已经越过了一条线——**从「工作堆在门外」变成「结论建立在门外的工作上」**。前者只是延迟，后者会让 master 上的判断无法被 master 上的证据支持。今天是五件工单和一句关于论文的话；如果队列继续这样，冻结清单与主表也会以同样的方式引用看不见的东西。

suggest:
1. **优先合并这两个分支**（`v15-census-sampling-frame`、`v11-negative-control-census`），优先级高于我上一轮提的「修门的先过」——因为已经有裁决建立在它们上面了。若一时合不进，**至少把普查的结果文件（`MATRIX_V15.md` / `NEGATIVE_CONTROL.md` / `KNOWN_GAPS.json`）单独取到 master**，让那 340 与 48 可复核。
2. **给引用加一条纪律**：裁决、工单、论文判断若引用某份产物，该产物必须在 master 上，或引用处必须写明「依据在分支 X，尚未落地」。这条极便宜，且正好补上 cycle 18 那条的另一半——`done/landed` 管的是计数，这条管的是**引用**。
3. `P14-honesty-section` 这件工单本身值得留意：它要写的是论文的诚实性章节，而它的依据现在正是一份 master 看不见的普查。**它会是第一件把这个问题写进论文的活**，建议在它开跑前先解决第 1 条。

（本轮另记：一份新到的 inbox 提案 `20260728T204718Z-W-1620-the-jam-is-not-the-lane-guard-eight-branches-die-on-a-backslash` 独立复现了 OPS-M 与我讲的那个反斜杠根因，且它的标题把范围说得比我准——「**eight** branches die on a backslash」，与我上一轮订正后的分解一致（`verify.sh` 8 个）。三个来源互相独立地收敛到同一个数，这条现在可以当作已确证。红线复核干净：密钥零命中、封存 ID 仅盘面渲染、append-only 主线零删除。）
