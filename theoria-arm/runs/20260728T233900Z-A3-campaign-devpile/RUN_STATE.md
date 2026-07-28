# A3-campaign-devpile — RUN_STATE (worker W-1640)

Written incrementally, as the work happens. Anything that exists only in a
session's context does not exist.

## Inheritance

The board item warns that RES-1 held this ticket and died to a session quota
limit around 2026-07-29T02:0xZ, and that it "may have half-finished work —
check before starting from zero."

It did. `.worktrees/a3-campaign-devpile` existed with an **uncommitted** working
tree: three new modules (`harness/campaign.py`, `harness/spend.py`,
`inner/levels.py`), four new test files, eight modified files, and four run
directories. None of it was committed, so none of it was attributable.

First action taken, before reading or editing any of it: committed it verbatim
as `4565c46`, with a message saying it is unverified. Everything I do after
that point is a reviewable diff against what RES-1 actually left, instead of an
indistinguishable merge of two sessions' work. Then merged `master`
(148 commits, `6dccf95`) — the only theoria-arm commit among them is E14's
crash-accounting fix.

## Clock

Local time on this machine is UTC+08. True UTC at run start is
**2026-07-28T23:39Z**, not 2026-07-29T07:39Z. Master commit `bac8282`
("six runs are dated in the future") records that a prior session stamped local
time into UTC-named run directories; three of RES-1's four inherited run dirs
carry that same defect (`20260728T210000Z`, and the pair at `152910Z`/`152930Z`
are plausible but unverified). This directory uses true UTC. Not correcting the
inherited names — they are already committed and renaming them would break the
manifests that reference them — but recording the discrepancy here so nobody
reads the campaign timeline off the directory names.

## Baseline test state — one defect found before any of my own work

`python -m pytest -q` in `theoria-arm/`: **148 passed** on the first
invocation after merge.

The second invocation of the identical command **failed**:

    tests/test_arm.py::test_the_shell_turns_end_to_end_against_the_mock
    assert [r["seq"] for r in everything] == list(range(1, len(everything)+1))
    E  At index 143 diff: 137 != 144

It then failed three more times in isolation, deterministically. So the suite is
green exactly once per clean checkout and red forever after. The test pins a
constant run slug, reuses one append-only `ledger.jsonl`, and asserts (citing
`LEDGER_FORMAT.md` §2) that `seq` is dense across the whole file no matter who
wrote it. Once a second run appends, it is not.

This is not incidental to A3. A campaign is by definition many runs appending to
one ledger, and the per-turn cost series that feeds the paper's figure 2 is read
out of that ledger. If `seq` is unreliable across runs, it is unreliable in
precisely the case this ticket creates. Root-cause delegated; verdict below when
it lands.

<!-- INCREMENTAL: sections below are appended as work proceeds -->
