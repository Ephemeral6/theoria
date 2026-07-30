# DRIFT-a-red-verdict-whose-every-cited-file-is-a-dead-copy

> ┌─ 更正（cycle 51，2026-07-30T10:15Z，对抗性复核提出，我采纳）──────────────────────────────
> │ **1. suggest 3 是错的，而它错的方式正好证明了另一份报告的论点。** 本报告说 S41 引用的
> │ `monitor/runs/20260730T0440Z-S39/FINDINGS.md` 不存在，并说「下面这张表是对它的重建」。
> │ 实测：**它存在**，在 `351ef03f`，分支 `agent/s39-writes-into-the-live-master-tree` 上——
> │ 一条正被合并死结扣着的分支，`git show` 一条命令就能取。**而我的重建是错的**：
> │ 本报告数出「4 个仪器只跳过 `.worktrees`」，那份权威表写的是 **7**（且它自己只点名了 6，
> │ `check_solver_status.py:333`、`triage_credential_incidents.py:146`、`test_contamination_gate.py:401`、
> │ `cold-start-a2/verify.py:145`、`fleet-study/census.py:200`、`ablation-arm/tests/test_readonly.py:712`——
> │ 所以那份分支文档自己也差一个）。**教训：一个文件「不在树上」不等于「不存在」；
> │ 先 `git log --all --diff-filter=A -- <path>` 再说它不存在。** 这条进 self_correction_rule。
> │ **2. 一处引用是假的**：本报告说 `monitor/index.html` 里有 `conflict_scan`——`grep -c` = **0**。
> │ 页面上有的是渲染后的中文 detail（「合并冲突标记」1 次、`.worktrees/opsm19-v21` 1 次），不是探针键名。
> │ 实质不变（它确实被渲染出去了），但字符串引错了。
> │ **3. 数字已经长大（不是当时错，是已经变了）**：`conflict_scan` 现在点名 **5** 个文件而非 4
> │ （新增 `.worktrees/opsm28-conf-v5/battery/verify.py`，3 个标记）；`.git/worktrees` 登记数 **260**（当时 225），
> │ 且在同一次会话的两次调用之间从 272 变到 258，**目录在活着变**；一次完整重走得 **1,349,079 文件 / 54.9 秒**
> │ （当时 1,233,001 / 93.7 秒，文件数 +9.6%，秒数低是 FS 缓存热）。**静态领地逐字节复现**：
> │ `.claude` 16,238、`engine-rig` 2,689 与原文完全一致。
> │ **3b. 本报告 suggest §1 把这个一行修法的收益低估了一个数量级以上——这条最要紧，因为它会让人给一行改动降优先级。**
> │ 原文写「省下每次约 94 秒」。**93.7 秒只是枚举（`os.walk`）的时间，不含枚举之后对每个文件的 `.read()`。**
> │ 实测（另一个 agent 用 `Win32_Process` 的 I/O 计数器读活着的扫描进程，未启动也未杀死任何进程）：
> │ 一次扫描要读 **54.5 GiB 文件内容**——`probe_credential_hygiene`（`scan.py:148` 走树、`:156`
> │ `open(...).read()`，**完全没有扩展名过滤**，连二进制一起读）**30.81 GiB / 1,349,073 个文件**，
> │ 加 `probe_conflicts`（`:330/338/341`，11 种扩展名）**23.67 GiB / 946,360 个文件**。
> │ **`.worktrees/` + `.claude/worktrees/` 占其中 99.46% 的文件数与 99.26% 的字节数**；
> │ 全仓非 worktree 文件只有 **7,324 个 / 234.2 MiB**。活进程佐证：PID 44268 在第 694 秒读到 **30.54 GiB**，
> │ 与实测树体积 30.81 GiB 相差 1% 以内——那正是第 3 个探针走完全树的时刻，之后继续爬升即第二次遍历重读同一批文件
> │ （本机 31.5 GiB 内存、剩 5 GiB，30.81 GiB 的工作集缓不住，第二遍是真的回盘读）。
> │ **所以那一行 `SKIP_DIRS` 省下的不是 94 秒，而是十分钟到八十五分钟。** 顺带一条没人报过的：
> │ `:156` 读**所有**内容而不做扩展名过滤，这本身是独立于 worktree 的一笔浪费。
> │ **4. 一处条件限定**：「删掉这些死副本就翻绿」在 09:54:32Z 那一版成立（detail 只含 (a) 款），
> │ 但 pin 上被跟踪的那一版（02:44:39 生成）的 risk 来自 **(c) 款跨领地提交**，同样的编辑对它无效。
> └────────────────────────────────────────────────────────────────────────────────────

severity: medium-high
dimension: 7 (a check whose red cannot be acted on) → 8 (the monitor auditing itself)

pin: `origin/master = 13bbcad9` @ 07:46:41Z. Live `HEAD` moved during the cycle
(`60def5cb` → `ee64df93` → `e369bcf9`). `monitor/state.json` is **dirty on disk** and the question
here is *what is published right now*, so the live file is the correct source and is labelled `disk`.

---

## claim

`monitor/scan.py`'s `SKIP_DIRS` excludes neither `.worktrees/` nor `.claude/worktrees/`, so
`probe_conflicts` walks **225 registered worktrees plus 4 harness copies** as if they were the
project. It is publishing **`risk` right now**, and **every one of the four files it names is a dead
copy**. The live tracked tree has zero conflict markers. A probe that cries wolf on files
unreachable from any ref is a probe whose red gets discounted — and clauses (b) and (c) of that same
probe watch the live index, where a real red would mean something.

---

## evidence

**The skip set** — `monitor/scan.py:48-49` (`pin`, and byte-identical on `disk`):

```python
SKIP_DIRS = {".git", "__pycache__", ".toolchain", ".lake", "node_modules",
             ".pytest_cache", ".egg-info", "out"}
```

Neither `.worktrees` nor `.claude`. The walk at `:330-331` (`pin`) prunes with exactly this set:
`for base, dirs, files in os.walk(ROOT):` / `dirs[:] = [d for d in dirs if d not in SKIP_DIRS]`.

**The published verdict** — `monitor/state.json` (`disk`, generated 07:59:01Z, 13 min after the pin),
`probes.conflict_scan`:

```
"status": "risk"
"detail": "文件内有合并冲突标记：.worktrees/opsm19-v21/exam/STATUS.md,
           .worktrees/opsm23-e8/engine-rig/recheck/build_cases.py,
           .worktrees/opsm23-e8/engine-rig/recheck/verify_all.py,
           .worktrees/_w130_e8merge/engine-rig/recheck/build_cases.py"
```

**All four are worktree copies. All four genuinely carry markers** (3 / 15 / 12 / 6 respectively) —
the probe is not malfunctioning, it is correctly reporting files that do not matter. **Their live
counterparts carry zero**, and the whole live tree is clean:

```
git ls-files -z | xargs -0 grep -lE '^(<{7} |={7}$|>{7} )'   →  empty
```

So **removing the worktree paths flips this probe green.** 100% of the evidence set is dead copies.
It is rendered: `monitor/index.html` contains `conflict_scan`; it is 1 of 9 `risk` probes out of 26.

**The scale, measured** (a `%TEMP%` harness replicating `scan.py:148/330` verbatim): `os.walk(ROOT)`
under `SKIP_DIRS` reaches **1,233,001 files**, and enumeration *alone* takes **93.7 s**.

| tree | files | share |
|---|---|---|
| `.worktrees/` (225 registered) | 1,209,475 | **98.1%** |
| `.claude/worktrees/` (4 harness copies) | 16,238 | 1.3% |
| `engine-rig` | 2,689 | 0.2% |
| `monitor` | 1,396 | 0.1% |
| **all live territories combined** | | **< 0.6%** |

**I had this the wrong way round when I started.** I opened the cycle thinking the harness's
`.claude/worktrees/` was the story, because that is what I noticed in `git status`. It is 1.3%. The
sharp end is `.worktrees/` — the directory `CLAUDE.md` itself tells everyone to use.

---

## the same omission, and where it is already owned

`monitor/board/items/S41-S41-prior-work-scans-one-of-two.md` is **open and unclaimed** and covers the
skip-set asymmetry. This report is evidence for it, not a competing item. Rebuilt census (excluding
`*/runs/*`): 4 instruments skip `.worktrees` only; 1 skips `.claude` only
(`ablation-arm/ablcore/pin.py:28`); 2 are symmetric; **`monitor/scan.py:48` skips neither** — the
worst case, and the only one that is live-red.

Worth the monitor's attention inside S41: `arc-recon/test_contamination_gate.py:401` and
`proxy/tools/triage_credential_incidents.py:146` are **sealed-discipline and credential** walkers
that skip `.worktrees` but **not** `.claude`.

**S41 cites `monitor/runs/20260730T0440Z-S39/FINDINGS.md` §3 for a table of "8 处非对称的 skip 集合".
That file is absent from disk and from `git ls-files`.** The table above is a reconstruction of it.

---

## what I killed, and why the kills matter more than the finding

* **"Manifest and `runs/` counts are inflated 5×" — FALSE.** `scan.py:774`'s
  `glob("*/runs/*/MANIFEST.json")` returns **141 with 0** from either worktree root, because `glob`'s
  `*` does not match dotted directories. `probe_provenance` iterates `TERRITORIES` from
  `_discover_territories` (`:305`), the one skip set that *does* name both. **Both immune — but
  `:774` only by the accident of a leading dot.** If `.worktrees/` were ever renamed without a dot,
  that probe silently inflates.
* **"The sealed-cache guard walks the tree and is contaminated" — FALSE, and the truth is the
  opposite.** `arc-recon/local_engine_guard.py:571`'s `scan_dir` only walks roots it is handed, and
  `arc-recon/verify.sh:90` hands it two that **do not exist** (`environment_files`,
  `../environment_files` — both `absent`, exit 0 at the pin). It is **blind, not noisy**, which is
  prior art (`DRIFT-20260730T0702Z` §three, still OPEN).
  **New, and it is a correction to that report's proposed fix:** `scan_dir` has *no exclusion list at
  all*, and `classify_name` returns `deny_unknown` for any name that is not a game id — driven:
  a temp dir holding `README.md` + `notes.txt` yields `{'deny_unknown': 2}`, `clean: False`, **exit 2**.
  So 0702Z's remedy "point `scan` at the whole tree" **cannot be applied as written**: it would
  traverse 1.23 M paths and return exit 2 unconditionally, making `verify.sh` permanently red.
  A remedy that makes a gate red on everything is a remedy that gets the gate switched off.
* **The `.env` inside `.claude/worktrees/p11-arc-hygiene/` — killed twice, once by me and once
  independently.** Covered by `.git/info/exclude:11` *and* by `.gitignore:3`'s pathless `.env`.
  `monitor/state.json`'s `credential_hygiene` is **green** and classifies it correctly — and names a
  second copy I had not found, `.worktrees/wt-p8/.env`. No publication risk.
* **The four `.claude/worktrees/` copies hold nothing unique in git**: all are strict ancestors of the
  pin, 0 ahead (354 / 354 / 342 / 1000 behind). **But ancestor-of-pin is not safe-to-delete** —
  `monitor/inbox/2026-07-29T1430Z-W-1672-…:66-77` records *untracked* paid-run artefacts under
  `p11-arc-hygiene/baseline-arms/out/shards/` (628 KB) and `monitor/board/items/R4-worktree-rescue.md:24-26`
  records unique V8 artefacts. **R4 is open. Do not prune these on my say-so.**

---

## suggest

1. **Add `.worktrees` and `.claude` to `monitor/scan.py:48`'s `SKIP_DIRS`.** One line. It flips
   `conflict_scan` from a false `risk` to green, and it returns ~94 s per scan — the walk currently
   spends 98.1% of its time in checkouts nobody is working in.
2. **Do not let this close S41 by accident.** S41 is the general item and is unclaimed; the credential
   and sealed-discipline walkers named above are the ones that matter most, and they are asymmetric in
   the *other* direction.
3. **The reconstruction above should be attached to S41**, since the file S41 cites for it does not
   exist. Whoever claims S41 will otherwise look for `monitor/runs/20260730T0440Z-S39/FINDINGS.md`
   and find nothing.
4. **Correct `DRIFT-20260730T0702Z`'s suggest §3 before anyone implements it** — see the kill above.
   The guard needs either discovery of directories *named* `environment_files`, or a
   `deny_unknown`-tolerant scan mode. As written it cannot be turned on.
