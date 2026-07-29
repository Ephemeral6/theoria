# S25 — twenty-one probes and none of them read the merge log

## Items 1, 2, 4 — delivered

**1. `probe_merge_queue`.** `monitor/mergequeue.py`, registered in `scan.PROBES`.
Reads `monitor/ci/merge.log` and `monitor/ci/CONFLICT-*.md`, reports how many
branches wait, how long each has waited, and a breakdown by reason.

The headline is **the longest single wait, not the count**, and that choice has
a test (`test_the_headline_does_not_fall_when_an_easy_branch_merges`). The count
falls when an unrelated easy branch merges while the stuck one has not moved —
a number that improves for reasons unrelated to the problem stops being read.
`git` is the authority on what is outstanding, not the log, so a branch someone
merged by hand leaves the queue.

**2. Board-versus-tree crosscheck.** `done_not_on_master()` lists every item the
board scores as `done` whose artefacts are not on `master`. This is the
mechanism behind the 11.5-point overstatement: `done` means *pushed*, merging is
a different machine, and when they diverge the score climbs while master gains
nothing. Currently 7.

**4. Negative sample.** `monitor/tests/test_merge_queue.py` builds a branch that
must jam and asserts the probe reports it **and that the wait grows** — a probe
that notices a jam but whose number drifts down while the jam persists is worse
than none, because it reads as progress.

**A real starvation bug, found while building the above.** `unmerged_branches()`
returned alphabetical order and each run stops after `--max` successes, so
branches late in the alphabet were only reached in rounds where earlier ones
failed enough times. `v5-battery-freeze` went four ticks and 40 minutes without
a single retry while its blocker had already been fixed. Now ordered
"never-tried first, then longest-waiting".

## Item 2, extended — the queue cannot see a branch that never joined it

Not in the ticket. Found by walking into it this cycle.

`done_not_on_master()` built its candidate set from `origin/agent/*`, so an item
marked `done` whose branch **was never pushed at all** was skipped in silence.
That is the strictly worse failure of the two: a queued branch is being worked
on, an unpushed one is not in the queue and no amount of waiting will fix it.

The case that exposed it: **S16-silent-failure-hunt** sat `done` on the board
for hours with its branch existing only in one checkout. The board said
delivered. The merge log said nothing was waiting. Both were telling the truth.

Now reported as a separate line, because absent and slow want different fixes.
The discrimination that matters — "no remote ref because never pushed" versus
"no remote ref because merged and the robot deleted it" — only git can make, so
three new tests build a real repository with a real remote. Deleting the
`is-ancestor` check fails two of them; that mutation was run.

## Item 3 — both premises were stale, and neither unblock was mine to make

The ticket said these were "two mechanical unblocks, both on the `ci_merge`
side, in this territory". Reproducing first, as it asked, showed that neither
description held.

### `v5-battery-freeze` — not a sys.path defect

The ticket described `ModuleNotFoundError: battery` in the temp checkout — a
gate sys.path defect rather than a red test. That was true when the ticket was
written and is not true now:

* the defect was fixed hours earlier by `gate_env()` (`gates.py:118-121`), which
  prepends the merged temp worktree root to `PYTHONPATH`;
* **this tip does not import `battery` at all** — its `verify.py` imports only
  `os, re, subprocess, sys` and shells out. The fix was never what it needed.

The actual blocker is `CONFLICT (add/add): Merge conflict in battery/verify.py`.
Both sides created that file after the fork: master's in `127edab` — **S14, my
own work**, gating eleven territories in one sweep — and the branch's in
`32fa34d`, four hours later. Master's is 341 lines (suite → offline pipeline
recompute → seven-artefact field/count floors); the branch's is 110 (freeze
manifest consistency → suite with deselect treated as loudly as failure →
artefact drift reported but tolerated). **Neither is a superset**; they check
disjoint properties and want unioning, not choosing between.

**Not resolved here, deliberately.** Resolving it means writing
`battery/verify.py`, and `battery` is held by RES-2
(`P7-P14-battery-section-blind-round`). The board's one-worker-per-territory
guard is the only thing standing between two sessions editing the same gate, and
walking around it to close my own ticket faster is exactly the trade this lane
exists to refuse. Reported to the monitor instead.

### `s11-sealed-halfguard` — a contract change, not a mechanical fix

Blocked by `touches protected root files`; the file is `CLAUDE.md`, and editing
`CLAUDE.md` is **what its own work item asked it to do**. The item requires A,
the guard forbids auto-merging anything that does A, and the guard has no
approved-exception channel. That is a closed loop, and the branch is 96%
`arc-recon` work held by a 37-line append.

Relaxing the guard would be dismantling a gate to let one branch through — and
the kind that looks fine the day you do it and costs you three days later. Under
`CHARTER.md` contract changes are the monitor's, so this was written up rather
than acted on: `monitor/inbox/20260729T0222Z`, three options, preferring the
second — split `protected_root` into `never` / `needs_declaration`, the latter
requiring a `contract-change:<item-id>` commit trailer naming an item that
declared it on the board, printed explicitly in the merge log. It turns "who
approved this" into an artefact instead of a memory.

## Verification

* `python -m pytest monitor/tests/test_merge_queue.py -q` → **15 passed**.
* `bash monitor/verify.sh` → **GREEN**.
* Mutation check: removing the `is-ancestor` discrimination fails two tests.

## Standing caveat

The board-versus-tree crosscheck maps an item id to a branch by the fleet's
naming rule (`<item-id-lowercased>` → `agent/<slug>`). An item delivered on a
differently-named branch is invisible to it. That is a naming-convention
dependency, not a check — worth knowing before this number is quoted.
