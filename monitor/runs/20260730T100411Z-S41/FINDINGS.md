# S41 — the empirical facts

All numbers measured on this machine, from the main checkout
`C:/Users/user/Desktop/theoria`, on 2026-07-30. The fleet was running
throughout, so two snapshots are recorded rather than one: the counts move
while you watch them, and a single number would read as more solid than it is.

## 1. The worktree census

`git worktree list --porcelain`, main checkout excluded:

| root | 09:5x snapshot | 10:0x snapshot |
|---|---|---|
| `.worktrees/` | 246 | 252 |
| `.claude/worktrees/` | 4 | 4 |
| `%TEMP%` (`ci_merge`'s throwaway trees) | 1 | 4 |
| **registered, linked, total** | **251** | **260** |

The `%TEMP%` row is the one worth stopping on. The item brief, `CLAUDE.md` and
S39's survey all describe this machine as having **two** worktree roots. It has
at least three: `ci_merge` builds its merge trees under
`C:/Users/user/AppData/Local/Temp/`, and between the two snapshots above that
number went 1 -> 4. Any fix built on a hard-coded list of two roots would have
been wrong on the day it landed. This is the argument for `git worktree list`
being the enumerator rather than a wider glob: it is root-agnostic by
construction and needs no constant to be kept current.

## 2. Orphans — checkouts git has forgotten

Directories present under a worktree root that appear in no
`git worktree list` record:

| root | orphans |
|---|---|
| `.worktrees/` | **6** |
| `.claude/worktrees/` | 0 |

The six: `_advscratch`, `_c1w_salvage`, `_e1_salvage`, `_res3_v26merge`,
`opsm21-adv4-probe`, `opsm28-master-control`.

The item predicted five. The first five are exactly the five it named;
`opsm28-master-control` is a sixth that has appeared since the item was
written. Neither `git worktree list` nor `reap_worktrees.py` can see any of
them, which is why pass 1 alone would have swapped one blind spot for another.

## 3. Loose files — the count trap

`.worktrees/` holds **12 entries that are files, not directories**:

```
opsm-gate.py                 opsm21-v25-probeB2.py    s29-fig-master-out.txt
opsm20-boardadv-FINDINGS.md  opsm21-v25-probeC.py     s29-fig-out.txt
opsm20-msg.txt               opsm21-v25-probeD.py     s29-rel-out.txt
opsm20-v21adv-FINDINGS.md    opsm21-v25-probe.py
opsm21-v25-probeB.py
```

`.claude/worktrees/` holds 0. So a census by `len(os.listdir('.worktrees'))`
overstates by 12 — 264 entries against 252 directories in the later snapshot.
The orphan sweep filters on `os.path.isdir`, and a test pins it in both roots.

## 4. The defect, demonstrated

`p11-arc-hygiene` — the S36 incident directory, three paid shards — replayed
against both implementations on the live tree:

```
OLD (origin/master board.py:634-637)   worktree hits: []
NEW registered hits: ['.claude/worktrees/p11-arc-hygiene']
NEW orphan hits:     []
```

The old check is silent on the only directory where duplicated paid work has
ever actually happened. Silent, and the claim succeeds.

## 5. Test counts

Full `monitor` suite, `python -m pytest` from `monitor/`:

| | failed | passed | xfailed |
|---|---|---|---|
| baseline (origin/master 7972a075, before any edit) | 5 | 390 | 2 |
| after S41 | 5 | 409 | 2 |

**No new failures.** +19 passing, all in the new file.

The 5 baseline failures are pre-existing and untouched by this item. The brief
said 3, in `test_standing_reflex_no_third_value.py`; the measured set is 5, in
two files:

* `test_scan_no_third_value.py::test_a_deleted_append_only_file_is_a_risk`
* `test_scan_no_third_value.py::test_all_files_present_still_reads_green`
* `test_standing_reflex_no_third_value.py::test_reflex_reads_the_return_code_of_every_child_it_scrapes`
* `test_standing_reflex_no_third_value.py::test_a_failed_git_query_skips_revival_instead_of_reviving_everyone`
* `test_standing_reflex_no_third_value.py::test_supply_unknown_is_distinct_from_supply_low_zero`

They are all source-grep assertions (`assert "SUPPLY-UNKNOWN:" in src`) against
`scan.py` / `reflex.py`, i.e. they fail because master's `scan.py` and
`reflex.py` do not contain strings the tests demand. Nothing in S41 touches
either file.

## 6. Requirement 4 — the cross-repo survey (recorded, not acted on)

RES-4 ran an independent survey in parallel and superseded the brief's figure.
Recorded here as instructed; **no other call site was changed.**

* The "8 asymmetric skip sets (7 only-`.worktrees`, 1 only-`.claude`)" figure
  from `runs/20260730T0440Z-S39/FINDINGS.md` §3 **does not reproduce.** Several
  sites S39 named are subtree-scoped and can never reach either root, so they
  are benign; S39 also missed at least two real ones.
* **Should there be one shared enumeration helper? No.** The sites are three
  unrelated shapes — enumerators, path walk-up, walk-skip sets — a shared
  constant would create a cross-territory import edge in a repo that forbids
  exactly that, and the "two roots" model the helper would encode is false
  anyway (see §1: `%TEMP%`, plus §2's orphans).
* The recommended never-again mechanism is instead a **lint test living in
  `monitor/`**. That is implemented here — see §7.

## 7. The lint, and what it does and does not catch

`tests/test_prior_work_both_roots.py::test_no_skip_set_in_monitor_names_one_worktree_root_but_not_the_other`
parses every top-level `monitor/*.py` with `ast` and flags any set/list/tuple
of string literals that names one worktree root and not the other.

It currently passes. Two adjudications were needed to get there, and both are
findings rather than tuning:

* **`ci_merge.py:59 KNOWN_DIRS` — false positive, rule narrowed.** It names
  `.claude` and not `.worktrees`, but it is a *positive allowlist* of
  territories, where the opposite polarity applies: adding `.worktrees` to it
  would be the bug. The rule now only judges a set that also names a machine
  directory (`.git`, `__pycache__`, `.pytest_cache`, `node_modules`, `.venv`,
  `.toolchain`) — the markers every genuine skip set in this repo carries.

* **`scan.py:48 SKIP_DIRS` — real, out of scope, deliberately not flagged.**
  It names *neither* root, so `os.walk(ROOT)` at `scan.py:148` (the ARC API-key
  leak scan) and `scan.py:331` (the conflict-marker scan) descend into all 252
  worktrees. That is a different decision from a half-done exclusion, and it is
  not obviously wrong: a leaked key inside a worktree is still a leaked key, so
  the leak scan arguably *should* go there. Adjudicating it would change what
  those two scans cover, which is well outside S41. Left for whoever takes it,
  recorded here so it is not rediscovered from scratch.

  The two skip sets that *do* name a root — `scan.py:305` and
  `gates.py:60 NOT_TERRITORIES` — are both already symmetric.

The lint has its own control (`test_the_lint_fires_on_the_shape_it_is_looking_for`)
that feeds it five synthetic sources: the S36 shape, its mirror image, a
symmetric set, an allowlist, and a set naming neither root. A lint nobody has
watched fail is a lint nobody knows works.
