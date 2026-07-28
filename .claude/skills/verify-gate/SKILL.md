---
name: verify-gate
description: 验收 gate for a Theoria ticket — generate the territory's verify.sh and run it, printing a PASS/FAIL checklist that covers the territory test suite, MANIFEST hash reproduction, and the three repo red lines (nothing changed outside the declared territory, no sealed-pile game id in any changed file, no credential value in any tracked file). Use before claiming a ticket is done, before 收工/push, whenever the user says 验收 / 写 verify.sh / 跑验收 / "verify this" / "is it green" / "check before I hand off", and whenever a completion claim needs independent confirmation rather than a self-report. Also use to re-run an existing verify.sh after a fix.
---

# verify-gate

METHOD.md #2 and #3: a completion claim must pass an independent check, and the
acceptance list is a contract you may not quietly lower. This skill is that
check in executable form — and it is the difference between "自报完成" and
"核实" on the monitor's board.

Run from **your worktree root**.

## 1 — generate

```bash
python .claude/skills/verify-gate/scripts/verify_gate.py gen \
  --require engine-rig/runs/2026-07-28-fd/MANIFEST.json \
  --check "fixtures byte-stable::cd engine-rig && python -m fixtures.generate_all && git diff --quiet -- fixtures"
```

Territory, base commit, branch, prompt id and run dir come from the ticket
context `fleet-branch-ritual` left. Writes `<territory>/verify.sh` (override
with `--out`).

Generated checks:

| check | what it means |
|---|---|
| `tests -- <territory>` | `python -m pytest -q` from the territory root; prints `[ -- ] 不适用` for prose territories rather than a fake green |
| `MANIFEST hashes reproduce` | every artefact hash in the run's MANIFEST recomputed (`runs-archive check`) |
| `boundary` | no file outside the declared territory changed (PARTNER_SYNC.md excepted) |
| `sealed pile untouched` | no sealed game id appears in any file this branch touched |
| `credential never entered a tracked file` | `.env` still ignored and untracked; no `.env` value present in any tracked file — reports **names only, never the value** |
| `--require <path>` | the工单's promised deliverable exists |
| `--check "name::cmd"` | anything else the工单 made a condition |

## 2 — run

```bash
python .claude/skills/verify-gate/scripts/verify_gate.py run
```

Prints the full checklist and exits non-zero if any line is red. **Every check
runs even after one fails** — 不绿报清单: when it is not green you get the
whole list, because "the first failure" is not a status report.

`verify.sh` is plain POSIX sh with no arguments, so a hook, a reviewer, or
M-0's integration gate can run it directly: `sh <territory>/verify.sh`.

> **Windows note.** `run` deliberately looks for the MSYS / Git-for-Windows
> shell. The `bash` on PATH in PowerShell is usually WSL's, whose filesystem
> view is not this repo's, and `sh verify.sh` there fails in a confusing way.
> Set `FLEET_SH` to override.

## When it is not green

Do not lower the line. Two honest moves, in this order:

1. Fix it.
2. If it cannot be fixed inside this ticket's territory, carry the red **verbatim**
   into `RUN_STATE.md`'s gap list and PARTNER_SYNC's `阻塞` line, with the
   check name and its output. `handoff-close` will ask for it.

Silently dropping a check, or regenerating `verify.sh` without the failing
`--check`, is exactly the "提前宣捷" the double-column board exists to catch.

## Guards, on their own

They are separate processes on purpose — any harness can gate on them:

```bash
python .claude/skills/verify-gate/scripts/guards.py sealed   --base <sha>
python .claude/skills/verify-gate/scripts/guards.py secret   --base <sha>
python .claude/skills/verify-gate/scripts/guards.py boundary --base <sha> --territory proxy
```

`--allow <path>` exempts a file whose job is to hold what the guard looks for
(the contamination register legitimately names sealed games). An `--allow` is a
disclosure: say why in `RUN_STATE.md`.
