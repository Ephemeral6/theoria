# DRIFT-six-runs-are-dated-in-the-future

severity: medium
dimension: 流程漂移（留痕的时间锚不可信）

**先记两件已闭环的**，因为它们是本轮才成立的：
- **`verify-lab/` 已在 master**（`git show HEAD:verify-lab/MATRIX_V15.md` 成功）。我 cycle 20 报的「裁决建立在 master 看不见的证据上」**已解除**——那 340 点普查现在可复核了。
- **`unknown territory` 类阻塞 6 → 0**：`911ec8e`「M-0 admits two territories, and six delivered branches finally land」，六个分支在 22:53–23:00 之间全部落地。阻塞总数 19 → **13**（其中 merge conflict 9，仍是最大一块）。

**本轮的新发现，是在那批产物落地之后才第一次可查的。**

evidence: 审计基准 `2c067e2`（23:20Z）。判据脚本 `scratchpad/stamps.py`：解析全部 `*/runs/*/` 目录名里的 `YYYYMMDDTHHMMSSZ` 戳，与真实 UTC 比对。

**55 个带 UTC 戳的 run 目录里，6 个的时间在未来**，最远 18.7 小时：
```
+18.7 h   verify-lab/runs/20260729T180000Z-V17-pin-the-partial-verdict
+12.7 h   verify-lab/runs/20260729T120000Z-V15-census-sampling-frame
+ 8.7 h   theoria-arm/runs/20260729T080000Z-E14-crash-is-not-a-finding
+ 8.7 h   engine-rig/runs/20260729T080000Z-C11-tool-failure-as-truth
+ 4.9 h   verify-lab/runs/20260729T041500Z-V14-standing-negative-control-probe
+ 0.7 h   engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep
真实 UTC：2026-07-28T23:19:46Z
```

**不只是目录名——`MANIFEST.json` 里的 `utc` 字段抄了同一个值**：
```
verify-lab/runs/20260729T120000Z-V15-…/MANIFEST.json → "utc": "2026-07-29T12:00:00Z"
verify-lab/runs/20260729T180000Z-V17-…/MANIFEST.json → "utc": "2026-07-29T18:00:00Z"
```
所以留痕正典四个必填字段里的那个 `utc`，在这几份里**填的是一个没有发生过的时刻**。

**这些戳看形状不是读错时区，是编出来的。** `180000Z` / `120000Z` / `080000Z` / `000000Z` 全是整点，`041500Z` 是一刻钟——**真实时钟读数不会这么齐**。对照：同一批里另外 49 个目录的戳都落在过去且带零散的秒数（如 `20260728T152000Z`、`20260729T041500Z` 之外的 `20260728T110000Z-P8-…` 等），说明写得对的人是去读了时钟的。

**为什么这条要紧，而不是洁癖：**
1. **`base_commit` 救不了这一项。** 我 cycle 10 报 9 份 manifest 缺 `utc` 时，把严重度压在 medium，理由正是「`base_commit` 是更强的锚」。那条理由在这里**反过来了**：这几份有 `utc`，但它是假的——**一个错的锚比没有锚更糟，因为它看起来能用**。
2. **它污染的是排序。** Phase 4 回算要问「哪个数字先于哪个」「这次跑用的是不是当时最新的树」。六个未来戳会让任何按时间排序的回溯把它们排到最后，而其中 `V15` 正是那份已经派生出五件工单与一句论文判断的普查。
3. **它与我 cycle 14 查过的心跳时间戳是同一族**。那次我查完判为「只影响显示，不影响判活」（读取方用 `mtime`）——**结论仍然成立，但现在看清了背景**：这套系统里多个地方的 UTC 是人手写的，而人手写的 UTC 有时是猜的。心跳那次侥幸无害，留痕这次不无害。

claim: 六份留痕的时间锚指向未来，其中两份的 `MANIFEST.utc` 也照抄了假值。这不是排版问题——它让「这个数字什么时候产生的」这个 Phase 4 必须回答的问题，在这六份上得到一个确定但错误的答案。

suggest:
1. **六份回填真实时间**，可用该 run 目录首次进入 git 的提交时间（`git log --diff-filter=A --format=%aI -1 -- <dir>`）作为权威值，并在 `RUN_STATE.md` 注明是回溯订正。目录名可保留（改名会断引用），但 `MANIFEST.utc` 必须改对，并加一行 `dir_name_stamp_is_nominal: true`。
2. **加一道极便宜的检查**：`probe_provenance` 已经在遍历 `runs/`，顺手比较 `MANIFEST.utc`（以及目录名里的戳）与当前 UTC——**未来时刻直接报 risk**。这是一个天然带负样本的检查：今天它就会红，六个实例现成。
3. **根治是别让人手写 UTC**：留痕脚本统一从 `date -u` / `datetime.now(timezone.utc)` 取值。今晚验证过 `date -u` 在本机是准的（我每轮都用它打时间戳）。
4. 与 cycle 10 那条并案处理：那 9 份缺 `utc`、这 6 份 `utc` 是假的——**同一个字段，两种坏法**，一起修比分两次修便宜。

（红线：本轮复核干净。另记一句本轮读到的、与我这条同源的好东西：`verify-lab/MATRIX_V15.md` 自己撤回了「精确复现 V14」这句话，并写下「**写在结果吻合的那一半上的自检不是自检**」——那正是我这条建议 2 想装的东西的通用形式。）
