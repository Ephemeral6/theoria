# S39 · findings (requirements 1 and 4)

RES-4, infra. Requirement 1's numbers are in `RUN_STATE.md`; this file is the
adjudication of the paths behind them, plus the requirement-4 census.

## 1. Adjudication of the non-fleet-state dirty paths (requirement 1, part 2)

The capture in `master-tree-status-raw.txt` (04:40Z) went stale while the item
was being worked: 6 of the 22 resolved by 05:00Z, all as **direct-to-master
commits**. Capture-time verdict and current state both recorded.

| path | tracked | owner | verdict |
|---|---|---|---|
| `monitor/reflex.py` | yes | none — landed direct on master as `873d62ee` | **MISWRITE** (resolved by commit, not by branch) |
| `monitor/spec.py` | yes | none; blob matches no ref | SHOULD-BE-COMMITTED (master is its home; 5 prior master-only commits) |
| `release/runs/…S23/{before,after}/contamination.planted.txt` | yes | fixture drifted when A13 `1050b001` changed `contamination.py` output | SHOULD-BE-COMMITTED |
| `monitor/{state,quota_state,accounts_state}.json` | yes | — | FLEET-STATE (the 189/22 split misfiled these) |
| `monitor/standing_state.json` | **yes** | — | SHOULD-BE-GITIGNORED — it is *already* named in `.gitignore:22`, but `.gitignore` never applies to a tracked file. Needs `git rm --cached`; until then it is a permanent dirty-tree generator. |
| `monitor/res/RES-3-notes/` (3) | no | no history; V6 work has its own branch | **MISWRITE** |
| `theoria-arm/runs/20260729T2040Z-A3-unpriced/` (8) | no | **`agent/a3-campaign-devpile` @ `41ad497c`**, byte-identical, not an ancestor of HEAD | **MISWRITE** |
| `.claude/skills/deterministic-figures/SKILL.md` | no | none | SHOULD-BE-COMMITTED (a real 127-line skill, in no commit on any branch) |
| `worldgen/out/qc/t2-lock-fragile/engines_report.json` | no | none | SHOULD-BE-COMMITTED (its paired `candidates.jsonl` is tracked, same mtime) |
| `monitor/audit/` 3×DRIFT + 2×WIP-cycle47 | no → now tracked | OPS-A cycle 47 | SHOULD-BE-COMMITTED (77 siblings already tracked) |
| `scratchpad/` (3) | no | none | SHOULD-BE-GITIGNORED |
| `.mongate_clean.log` | no | pytest output from `.worktrees/opsm26-mongate` | SHOULD-BE-DELETED |
| `C:UsersuserDesktoptheoriamonitorpermtest.txt` | no | see §2 | SHOULD-BE-DELETED |
| `theoria-arm/runs/pytest-*/` (2) | no | none | SHOULD-BE-DELETED — and specifically **not** gitignored; `theoria-arm/.gitignore` removed that line on purpose and `armtools/verify_provenance.py:68` fails when they reappear |

**Totals: 4 MISWRITE, 11 SHOULD-BE-COMMITTED, 2 SHOULD-BE-GITIGNORED, 4
SHOULD-BE-DELETED, 3 misfiled FLEET-STATE.**

### Why this matters more than the count

* `monitor/reflex.py` is the purest instance of the defect: a substantive
  69+/115− rewrite of the low-memory top-up path, made in the live master
  checkout with the branch step skipped entirely. No branch ever carried it.
  It ended up committed rather than lost, and that is **luck, not process**.
* `worldgen/out/qc/t2-lock-fragile/candidates.jsonl` was last touched by commit
  `1bd7eea2`, titled **"On master: autostash"** — a git autostash of the live
  master tree. That is an *earlier instance of this same defect*, already in
  the history, with the sweep mechanism named in the commit subject.
* The A3 run directory is 8 files byte-identical to a branch commit that is not
  an ancestor of HEAD, and its own `MANIFEST.json` records `"branch": "master"`.
  The miswrite is self-documenting: the manifest recorded the tree it was
  written in, not the branch that owns it.

## 2. The flattened-path filename — explained, and already on the books

Repo root, `CUsersuserDesktoptheoriamonitorpermtest.txt` — the character
rendered as a colon is **U+F03A**, Windows' private-use substitute. 8 bytes:
`dc9fad1\n`.

Producer: `monitor/prompts/Z0-permprobe.md:3` tells a dispatched session to
Write `monitor/permtest.txt` containing `write-ok`, then append
`git rev-parse --short HEAD`. The session passed the **absolute** path to Write;
Windows folded out the backslashes and mapped `:` to U+F03A, and the entire path
became one filename at the repo root. `monitor/permtest.txt` was never created
and `write-ok` was never written — only step 2's short HEAD landed.

**Not a string-concatenation bug in any script.** No code writes this path; it
is an agent path-handling failure, already catalogued three times:
`fleet-study/data/failures.jsonl` **F-16**, `counterevidence.jsonl` **C-12**,
and `monitor/inbox/archive/20260728T034833Z-OPS-R-optional-checks-fail-open.md`.

F-16's angle is the sharp one for S39: the probe printed `DONE` and exited 0,
and `monitor/_runner.py:85-93` records only `{code, seconds, log, ended}` — it
never reads the artifact. **The instrument built to prove that exit codes lie
was itself judged by its exit code.** That fix is still unimplemented, so the
same artefact can reappear; deleting the file does not close it.

## 3. Requirement 4 — the two worktree directories

`git worktree list --porcelain` covers both roots and puts the **main tree
first**; verified from inside a linked worktree, output identical from either.
That is what `master_tree_guard.main_worktree()` uses, so this gate does not
repeat the S36 mistake.

**Counts (2026-07-30):** 221 registered (main 1, `.worktrees/` 216,
`.claude/worktrees/` 4) + **5 orphaned checkouts on disk that git has forgotten**
(`_advscratch`, `_c1w_salvage`, `_e1_salvage`, `_res3_v26merge`,
`opsm21-adv4-probe`). `reap_worktrees.py` is purely porcelain-driven, so it
cannot see those five either. `.worktrees/` also holds 12 loose *files*, so
anything counting entries rather than directories is off by 12.

### Blind-spot inventory — scripts that see only one of the two

Enumerators:

| file:line | coverage | note |
|---|---|---|
| `monitor/board.py:634-637` (`prior_work`) | **`.worktrees` only** | **The S36 shape exactly, and the highest-value one.** This is the check that exists *specifically* to warn "someone may already be doing this item" — and `.claude/worktrees/p11-arc-hygiene` is precisely where the three paid shards sat. Message text hardcodes `工作树 .worktrees/%s`. |
| `ablation-arm/abltools/worktree_audit.py:97-135` | git part both; **unregistered sweep `.worktrees` only** | Knows the distinction exists (`:351` tags `harness_owned`) but only for git-registered entries. |
| `monitor/reap_worktrees.py:57-72`, `monitor/scan.py:729-733` | both (via git) | clean |
| `monitor/ci_merge.py:513` | `%TEMP%\ci-merge-*` — a **third** location | neither root |

Tree-walk skip sets — **8 asymmetric**, 7 `.worktrees`-only
(`engine-rig/tools/check_solver_status.py:333`,
`proxy/tools/triage_credential_incidents.py:146`,
`arc-recon/test_contamination_gate.py:401`, `cold-start-a2/verify.py:145`,
`fleet-study/census.py:200`, `ablation-arm/tests/test_readonly.py:712`) and one
the opposite way (`ablation-arm/ablcore/pin.py:28`, `.claude` only). Clean
examples to copy: `papers/phase1-workshop/verify_paper.py:199,1106`,
`monitor/gates.py:60`, `monitor/scan.py:305`,
`verify-lab/negctl/criterion.py:317`.

### A latent hazard found on the way — not S39's to fix, filed here

```
$ git check-ignore -v .claude/worktrees
.git/info/exclude:11:**/.claude/worktrees/
```

**`.claude/worktrees/` is excluded only by `.git/info/exclude`** — which is
per-clone, untracked and never pushed. `.claude/` itself is *not* ignored
(`.gitignore:15` covers only `settings.local.json`), which is why
`git status` shows `?? .claude/`.

So **on any fresh clone, `.claude/worktrees/` is not ignored at all** — four
whole checkouts become untracked content. That matters for the Phase 4 release
manifest, which publishes every tracked file, and for any gate that trusts
`git check-ignore` to classify a path. Raised to the monitor as an inbox
proposal rather than fixed here: the root `.gitignore` is not S39's territory.
