# 2026-08-01T044513Z-A19 · running notes

Prompt A19 · branch agent/a19-bare-cc-seal-split · base 4c08ea6
Opened 2026-08-01T04:45:13Z

## 2026-08-01T04:58:23Z

baseline red at ritual time was a worktree artefact, not master: baseline-arms/schema_traces/** is gitignored so a linked worktree never checks it out. Main checkout runs 534 passed / 0 failed. With THEORIA_SCHEMA_TRACES pointed at the main checkout payload (the escape hatch schema_column.resolve_root documents for exactly this case) the worktree runs 533 passed / 1 skipped / 0 failed BEFORE any A19 test is added.

## 2026-08-01T05:07:52Z

PRE-EXISTING, NOT A19: baseline-arms/runs/ is not worktree-reproducible. The committed runs/MANIFEST.json records evidence hashes computed in the main checkout, where tracked files still sit on disk with CRLF (baseline-arms/out/pilot_g50t_sonnet_rerun.json: 28 CRLF, 811 bytes). A fresh worktree checks the same file out with LF (0 CRLF, 783 bytes; byte-identical after newline normalisation), so archive_runs.verify() computes different sha256 and three tests in test_archive_runs.py go red on the FIRST suite run in any new worktree. The suite then self-heals, because test_rebuilding_produces_the_same_digest calls archive_runs.build(), which REWRITES tracked files (runs/MANIFEST.json and ~20 runs/*/run.json) with the worktree's own provenance (branch agent/a19-..., worktree path .worktrees/a19). That rebuild is deliberately NOT committed by A19: it would put worktree-local provenance on master and break again for the next worktree. This is the full explanation of the red baseline start_ritual reported.
