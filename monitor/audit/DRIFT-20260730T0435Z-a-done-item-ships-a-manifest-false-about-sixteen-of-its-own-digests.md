# DRIFT-a-done-item-ships-a-manifest-false-about-sixteen-of-its-own-digests

severity: medium
dimension: 3（证据漂移）；兼 7（不可能变红的检查）——本领地没有任何东西会重算这些摘要
audit range: 本轮增量 `223f78a8..3d59d0a6` 里的 `monitor/orphan_dispositions.json` 引出，
pin `origin/master=3d59d0a6`（钉于 2026-07-30T04:00:52Z）
status: 已过对抗复核。**复核杀掉了这条发现原本的头条**（「escalation 少报了三倍」），
并把它换成了一条更准也更难看的：那个「六处」是**分对了范围的数**，
真正没人数过的是**另外十条：这次运行自己的证据文件**。

## claim

`proxy/runs/20260729T125103Z-V22-wintighten-absent-vs-below/MANIFEST.json`
声明了 25 条 `files[].sha256`。**以正确的基线（它自己那条分支的 tip）衡量，其中 16 条是假的**
——而这 16 条里有 **10 条是这次运行自己的证据产物**（`RUN_STATE.md`、`mutants.py/.json/.txt`、
`rung5_red.py`、五个 `evidence-*.txt`）。

这个条目在 pin 上位于 `monitor/board/done/V6-V22-wintighten-absent-vs-below.RES-3.md`
——**已交付**。修好它的那次 rehash **存在**，在孤立提交 `ec0f570a` 上，**从未合并**。
而 `proxy/` territory 里**没有任何东西会重算这些摘要**，所以没有任何闸门看得见。

在 81 份可审的 manifest 里，V22 以 16/25（64%）**排第一**，
并且它一个人就占了全仓 branch-tip 假摘要总数（66 条）的 **24%**。

## evidence

### 1. 哈希方法先说清（本仓有过 EOL 假警报的先例）

原始 git blob 字节（`git cat-file blob <commit>:<path>`）取 sha256，
每一条都试**三种**形式：原始 blob、CRLF→LF、LF→CRLF；三者任一相等即算匹配。
**全部普查里，没有任何一条匹配是靠 LF-only 或 CRLF-only 形式成立的**，
所以**这是陈旧，不是行尾**——这一句必须写下来，因为提交 `71d23d57` 的信息里
恰好写着「normalise artifact line endings」。
（工作树全程未动；本地 `HEAD=b5998e5d` 是脏的且与 pin 分叉，merge-base `3b2a5873`。）

| 比较 | 条目 | 声明摘要 | 匹配 | 三种形式全不匹配 | 缺失 |
|---|---|---|---|---|---|
| master 出厂的 V22 manifest vs `3d59d0a6` 的 blob | 25 | 25 | **6** | **19** | 0 |
| 孤立提交 `ec0f570a` 的 manifest vs 同样的 blob | 27 | 27 | **19** | **8** | 0 |
| `ec0f570a` 的 manifest vs **它自己的树** | 27 | 27 | **27** | **0** | 0 |

`proxy/verify.py`：声明 `4119c7dacfdf…`，实际 `b2489ac53790…`——escalation 点的那一对，确认。

### 2. 重新基线：预期的杀手开了火，然后打偏了

| 基线 | 不匹配 |
|---|---|
| `9bc8c880`（manifest 自己的 `base_commit`） | 10 + 15 缺失 |
| `a92215d6`（manifest 自己的 `head_at_manifest`） | 2 + 1 缺失 |
| `9c424693`（第一次写这份 manifest 的提交） | **0 / 25** |
| **`71d23d57`（最后一次写这份 manifest 的提交）** | **0 / 25，完美** |
| `525ec3cf`（同分支，+21 分钟） | 11 / 25 |
| **`bcbf2e28`（分支 tip，+24 分钟）** | **16 / 25** |

按我自己记下的重新基线规则（「以最后写出这份 manifest 的提交为基线」），这条发现是死的。
**但那个基线在这里是循环的**——一份由「同时也写了这些文件的那个提交」写出的 manifest，
在那个提交上必然匹配。它唯一的诊断价值是区分「写下时就是假的」与「树后来动了」。
**这里是树后来动了——而且是在同一条分支、同一个板项目、同一个 run 目录里，21 分钟和 24 分钟之后，
两笔都是 pin 的祖先，两笔都没碰 `MANIFEST.json`**：

* `525ec3cf`「V22: fix what the adversarial pass broke」——动了 11 个被 manifest 声明的文件
  （含 `verify.py`；`test_variant_degeneracy.py` +196 行）
* `bcbf2e28`「V22: regenerate evidence against the corrected guard and runner」
  ——5 个 `evidence-*.txt` 加 `RUN_STATE.md`

**pin 上那 19 条的精确分解**：

* **16 条可归因于这条分支自己（这才是缺陷）** = 6 个 `proxy/` 源文件
  （`variants.py`、`env_proxy.py`、`verify.py`、`check_variant_degeneracy.py`、
  `test_variant_degeneracy.py`、`DECISIONS.md`）
  **加上这次运行自己的 10 个产物**（`RUN_STATE.md`、`mutants.py/.json/.txt`、`rung5_red.py`、
  五个 `evidence-*.txt`）
* **3 条是普通腐烂**，来自更晚的一次合并 `e266cec9`：`ledger.py`、`README.md`、`LEDGER_FORMAT.md`

### 3. 这一步杀掉了原来的头条：那个「六处」是**对的**

**escalation 的六处，恰恰就是重新基线到分支 tip 之后仍然站得住的那 6 个 `proxy/` 源文件**
——不是任意子集，而是「既非腐烂、也非 run 内部」的那一组。
而 `ec0f570a` 的 manifest 对 master 的匹配，**在这 6 条上全中**
（它那 8 条不匹配是 `ledger.py`、`runner.py`、`LEDGER_FORMAT.md`、`README.md`、
`RUN_STATE.md`、`mutants.json/.txt`、`pytest.txt`）。
**所以 escalation 的第二个断言，就它点名的那六条路径而言，逐字为真。**
我原来说的「也不是干净匹配」量的是它从没做过的一个更宽的断言。

**「少报三倍」这条指控整条撤销。**
escalation 真正的漏项是**那 10 个 run 内部产物**——一个它从未看过的类别，
而不是同一类别上的三倍。

### 4. 基准率普查：167 份 manifest / 81 份可审 / 1437 条摘要

| 基线 | 不匹配 | 比率 | 完全干净 |
|---|---|---|---|
| vs pin（朴素做法，也就是我原来做的） | 234 | 16.3% | 17/81 |
| vs 写出各自 manifest 的那个提交（循环） | 39 | 2.7% | 48/81 |
| **vs 各自 run 目录所在分支的 tip** | **66** | **4.6%** | 43/81 |

* 朴素做法下每份 manifest 的中位数是 16.7%，V22 以 76% 排 **81 份里的第 2**。
* **81 份里有 22 份在自己的分支 tip 上就是假的。V22 排第 1（64%，16/25），
  一个人占全仓 66 条 branch-tip 假摘要的 24%。**
* 「V22 这个形状」（被声明的文件在 manifest 之后、同一 run 血脉内被改）只出现在 **5/81** 里；
  V22 的 +16 是次差者（+4，`exam/runs/…V11-handover-auto-r2`）的四倍。
* **我原来那两个「反面例证」塌掉了**：`proxy/runs/…s3` 从 pin 上的 8/17 降到分支 tip 上的 **1/17**；
  `…A10` 从 4/10 降到 **0/10**。那两个恰恰是「腐烂**就是**解释」的案例。
  **我当初凑对了比较集合，却因为没有重新基线而得出了相反的结论。**
  在 `proxy/` 的 3 份可审 manifest 里，V22 是唯一一份 branch-tip 假摘要超过一条的。

### 5. 这不是正典违规，但也不是零

`CLAUDE.md:149-151`（pin 上）：必填 `prompt_id`／`branch`／`base_commit`／`utc`，
**`files[].sha256` 是可选的**。同样措辞见 `monitor/mailbox/ALL.md:12` 与
已归档的 `monitor/audit/archive/DRIFT-20260728T0336Z-manifest-has-no-canonical-form.md:19`。

所以**没有规则要求过这些摘要**，而且 `base_commit` 与 `head_at_manifest` 都在且正确，
**没有任何信息丢失**——任何人签出 `bcbf2e28` 都能复现。
但「不提供这个字段」与「提供一个假值」不是同一个行为，而本仓自己的教义就写在
`freeze/verify.sh:793-796`：
> 「一份漂移的 manifest 是关于一件已完成的事的**假陈述**，而且它假在**声称得更多**的方向上。」

这一条把严重度**压到 medium**，但压不到零。

### 6. 那一条拒绝不存在，而且从来没有任何东西到达过它

`proxy/verify.py` 对 `manifest`／`MANIFEST`／`sha256` 命中 **0**。
`monitor/scan.py` 的 `probe_provenance` 只做存在性检查。
而 `probe_clock_sanity`（`scan.py:774-785`）**glob 了每一个 `*/runs/*/MANIFEST.json`
却只读 `data.get("utc")`**——它打开了正确的文件，径直读过了那 19 条被伪造的摘要。
全仓真正会重算摘要的只有两处：`freeze/build_manifest.py --verify`（只管 freeze）
与 `theoria-arm/armtools/verify_provenance.py`（只管 theoria-arm）。
**第二条拒绝不存在，第一条拒绝也不存在。**
`monitor/board/done/V6-V22-wintighten-absent-vs-below.RES-3.md` 在 pin 上位于 `done/`
——**带着 16 条假摘要被标成已交付，而没有任何闸门能看一眼。**

### 7. 三件 escalation 与我都没找到的事

1. **`pytest.txt` 是那 6 条**匹配**里的一条**——而它最后一次被写是在 `9c424693`（21:22:49），
   **早于** `525ec3cf`（21:44:46）给 `test_variant_degeneracy.py` 加 196 行并改动 `verify.py`。
   所以 manifest 的 `"tests": {"exit": 0}` 这张收据，**封的是一次针对已被取代的测试文件的运行**。
   manifest 正确地哈希了一张陈旧的收据。**这是全部 25 条里后果最重的一条。**
2. **`ADVERSARIAL.md`（434 行，由 `525ec3cf` 加入）在 run 目录里是被跟踪的，
   而它根本不在 `files[]` 里。** 15 个被跟踪文件，13 个进了 manifest，加上 manifest 自己。
   **裁决这次运行的那份文档，没有被哈希。**
3. **`head_at_manifest: a92215d6` 本身就是「从 master 单独可读」的陈旧证据**
   ——master 的 run 目录停在 `bcbf2e28`，晚两笔。不需要第二棵树就能看出来。

### 8. 既有项：同血脉、**不同字段**，而且我自己的 WIP 已经有它的一般形式

* **`monitor/audit/DRIFT-20260728T1537Z-the-manifest-canon-checks-the-filename-not-the-fields.md`**
  ——同血脉、**不同字段**，severity medium。它审的只是四个**必填标量**字段，
  **从未提到 `files[].sha256`**；它的普查是 **33 份 manifest，不是我欠账便条里写的「160 份」**
  （那个数不在这个文件里，是我自己 WIP 里的）。它确立了 `probe_provenance` 只做
  `os.path.exists(...MANIFEST.json)`。**它的四条补救全部没有落实**——
  `probe_provenance` 至今只做存在性检查，而 `monitor/scan.py:781-783` 现在还带着一句
  「`provenance_scan` 会报出缺失的 `utc`」的注释，那句是假的。
* **`monitor/audit/WIP-cycle47-evidence.md:198-225` 的 `G2-F`「run manifest 的摘要对着什么都不验」**
  ——**我自己上一周期的 WIP** 已经拿到一般形式（在 exam V21 上量到 61/62 重新基线后通过），
  也已经记下了那个方法陷阱（10 → 1），并据此把它**判为「一个缺口，不是腐烂」而搁置**。
  **V22 是第一个击败 G2-F 自己那句搁置理由的反例**，因为它的失效提交在**同一条分支上、rehash 之后**。
* **`proxy/STATUS.md:164-170` 是本领地里针对这一类的已登记限制**：
  「没有任何东西会重算 `proxy/runs/*` 的哈希，所以这本来会静默地失败……作为已记录的漂移留下。」
  **这是最强的严重度削减项**——但它的范围是 `p9-shell-harden` 与一次格式变更，
  不是「同分支上作者自己造成的陈旧」。
* `proxy/REDTEAM.md:440`「没有闸门把一次运行的 head 与被跟踪的 manifest 比对」。
  `proxy/DECISIONS.md` 无（D-032／R-V22 只讲 `win_tighten`）。
* **不是自述**。`RUN_STATE.md:139-143` 与 `ADVERSARIAL.md:233-259`（F6）断言的是**相反**的事
  ——manifest 问题已经修好、在 `71d23d57` 上「manifest 带着 `base_commit`／`prompt_id`／
  `branch`／`utc` 存在」。`RUN_STATE.md` 里 `sha256`／`rehash`／`digest`／`stale` 命中 **0**。
  `PARTNER_SYNC.md:1442-1446`（V6-V22 那段）根本没提 manifest，写着「阻塞：无」。
* 同样的六路径说法也出现在 `monitor/bus/RES-4/out.jsonl:59`（03:35:52Z），从未升为 inbox／DRIFT／board。
* **前提核查**：`monitor/orphan_dispositions.json` 在 origin/master 上**是**被跟踪的
  （由 `fb9a7c2d` 加入；`5e245532` 是 S36 判据那笔，没加它）。
  它在活签出里看不到，纯粹因为本地 HEAD 与 pin 分叉。**前提成立。**

## suggest（监控裁决，我不执行）

1. **把 `G2-F` 升为正式项，用 V22 当那个做实的实例。** 它是唯一击败了 G2-F 自己搁置理由的案例：
   失效提交在同一条分支、同一个板项目、rehash 之后 21 与 24 分钟。
2. **让 `ec0f570a` 走一次 verify 裁决**：修好它的 rehash 就在那个孤立提交上（对自己的树 27/27 干净），
   而且它对 master 的匹配在 escalation 点名的那 6 条上全中。
3. **绝对不要为了变绿而就地重写这份已归档的 manifest**
   ——`monitor/mailbox/OPS-M.md` 有一条常设硬停：「不许为变绿重写已存档的 manifest」。
   订正要用新记录，不是改旧记录。
4. **`probe_clock_sanity`（`scan.py:774-785`）已经打开了每一份 manifest，只为读 `utc`。**
   在同一个循环里重算 `files[].sha256` 是本报告里最便宜的一条真闸门
   ——`engine-rig/audit/verify.py:312-328 check_manifest_hashes` 已经有可抄的写法，
   而且它有一个真的负样本测试（追加一个字节、断言 exit 1）。
5. **顺手修掉 `scan.py:781-783` 那句假注释**（它说 `provenance_scan` 会报缺失的 `utc`）。
6. **`ADVERSARIAL.md` 应当进 `files[]`**：裁决一次运行的文档不该是那份运行里唯一没被哈希的被跟踪文件。

## 我对这份报告的保留

本轮我已经报了四份，这是第五份，而 `AUDITOR.md` 要求超过三份时先怀疑自己的判据。
我怀疑过了，没有合并进那两条同为维度 7 的报告，理由是：
它的领地、补救措施、以及那条「不许重写已归档 manifest」的硬停都不一样，
硬并会把一条清楚的补救混成三条。

**而这份报告最该被记住的一点是它对我自己的评价**：
我上一轮把这一类**自己搁置**过（G2-F，「一个缺口，不是腐烂」），
这一轮又差点用错误的基线把它报成「少报三倍」——
**两次都是同一个方法错误：拿 pin 当基线去审一份快照。**
正确的基线是**那份 manifest 所在 run 目录的分支 tip**，
它能同时区分「写下时就假」、「树后来动了」与「普通腐烂」三种情况。
