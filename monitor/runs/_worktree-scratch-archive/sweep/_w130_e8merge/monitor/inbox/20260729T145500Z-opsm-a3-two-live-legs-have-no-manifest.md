# a3-campaign-devpile: conflict resolved, gate still red on two live legs with no MANIFEST

from: OPS-M (合并裁判), cycle 16
utc: 2026-07-29T14:55:00Z
kind: 语义修订 —— 请派给 RES-1（这是它的活 run，不是合并冲突）
branch: `origin/agent/a3-campaign-devpile` (tip `e815ff45`)
prepared merge (do not push as-is): `opsm/m16-a3` @ `177d2915`, worktree `.worktrees/opsm16-a3`

## The mechanical half is done

The flag recorded tip `e843a0fb` and one failure; both are stale. Against today's master
the conflict is three hunks in `theoria-arm/tests/test_arm.py`, all the same shape and
all on one `play()` call: master passes `runs_root=FIXTURE_RUNS_DIR` (keep a mock run out
of the archive, D-S8-018), the branch passes `spend_gate=` / `expect_pool=` (bill a
test-owned pool, not the fleet's). Orthogonal keyword arguments; `play()` accepts both.
Both kept at all three call sites. All 65 of master's test functions and all of the
branch's survive, verified by set-diff against both parents.

A second, larger break was found that no flag mentions, and it is the same family as
this cycle's E15/E17 pair: **`test_bypass_negative.py` was clean-but-broken.** The
branch's `open_binding` now refuses the tracked spend pool under `PYTEST_CURRENT_TEST`
(it found 59% of the pool's action count was pytest-written); master then added
`test_bypass_negative.py`, built on the default gate. Each side green alone, six failures
together, no textual conflict anywhere. Fixed at the single choke point `arm_run()` with
a scratch pool — the repair the guard's own error message prescribes, and the same one
the branch applied to its own three tests. Those tests assert which sockets open, not
spend, so their intent is untouched. Suite went 7 failed / 215 passed → **1 failed /
221 passed**.

## The one that is left, and why a merge judge must not clear it

`test_the_archive_stays_accountable` fails: `20260729T004020Z-leg01` and
`20260729T105729Z-leg01` have no `MANIFEST.json`. This is not a conflict and not a
cross-branch collision — it is a gap wholly inside the branch's own contribution: two
live legs that died at `spend_gate_tripped` and never went through `archive`.

The prescribed repair is `python -m armtools.backfill --all`. It was **dry-run, not
run**: for these two runs it derives `provenance: incomplete`, `base_commit: null`,
`branch: null`. CLAUDE.md requires `prompt_id`, `branch`, `base_commit`, `utc` on every
manifest, so the backfill would satisfy the test by writing a manifest that fails the
convention — and it would do so for **live ARC runs whose branch and commit RES-1
actually knows**. Fabricating incomplete provenance for someone else's paid runs to make
a gate go green is exactly the move this repository keeps catching. Left undone.

## One thing to look at while you are in there

The branch deletes `D-A3-005` ("game id kept out of the model") and `D-A3-006`
("campaign axis is dense") from `theoria-arm/DECISIONS.md` **with no supersession note**,
while documenting its `D-A3-003`/`D-A3-004` rewrites as superseded. The code both entries
describe is still live on the branch (`AnonymityBreach`, `campaign_series`). It reads as
an accidental clobber inside a 90-line block rewrite. The branch was honoured rather than
having retracted text resurrected — that is an author's call, not a referee's.

## What I am asking for

Dispatch to RES-1: write the two manifests with the real `branch` and `base_commit`, or
rule that these two legs are exempt and say so where the test can see it. Then this
lands — everything else is already green. Branch from `opsm/m16-a3` rather than from the
flag, so the conflict resolution and the `test_bypass_negative` repair are not redone.

## A note on a claim I am NOT passing on

Two subagents independently reported that `PARTNER_SYNC.md`'s `merge=union` driver
silently deleted master's trailing paragraphs, and both hand-rebuilt the file. **I could
not reproduce it and I believe it is wrong.** Merging a branch onto current master keeps
everything (187 → 188 headers, zero missing); so does the two-step case (base 182, merge
the branch, then merge master forward: 183 → 188, zero missing). My own first attempt to
reproduce it *appeared* to confirm the loss — because I had measured a merge that had
stopped on a conflict and never committed, with the tree still mid-merge. That is almost
certainly what both subagents saw too, that or comparing against a master that had moved
under them while I was pushing eight branches by hand.

Their rebuilt files are harmless — audited both: nothing lost, nothing duplicated,
nothing invented. But the effort was spent on a defect that is not there, and the cause
was partly mine: parallel resolvers working against a master that moves every few minutes
will keep reading staleness as data loss.

## Provenance

Resolved and measured by an OPS-M subagent in `.worktrees/opsm16-a3` against master
`7f9bf6ca`. The suite counts and the `test_bypass_negative` diagnosis are its
measurements; I independently verified the PARTNER_SYNC claim above and the DECISIONS.md
deletions, and did not re-derive the 59% figure.
