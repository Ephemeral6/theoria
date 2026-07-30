# DRIFT-a-red-verdict-whose-every-cited-file-is-a-dead-copy

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
