# Cycle 33 — the three conflict-class flags, looked at while the six arm agents run

The gate-red flags are being measured by subagents. These three are *merge
conflicts*, a different class, and I looked at them myself.

## `s31-a10-said-done-prove-it` — "push rejected (race?)", and the race was mine

The only flag in the queue that is not a defect in a branch. s31 **passed every
gate** and then lost the push:

```
! [rejected]  HEAD -> master (non-fast-forward)
```

Timeline, from commit timestamps (`%cI`, local +08:00 → UTC):

| UTC | event |
|---|---|
| ~12:56Z | ci_merge's pass takes a worktree at the then-current master |
| 13:02:00Z | **I push `d1da2c9c`** (cycle 32 disclosure commit) |
| 13:02:46Z | ci_merge pushes s31 → rejected non-fast-forward → FLAG |

So a branch that had already earned its merge was thrown back into the queue
because the merge referee pushed his own notes into master mid-pass. That is a
cost I imposed, not a property of s31.

**I checked whether it is stuck and it is not — my first read was wrong.**
`should_hold` (ci_merge.py:220-230) skips a branch only when the memo's tip
*and* base both still match; s31's memo records `base: d1da2c9c` and master is
now `ea4f6af6`, so the base check fires and it retries. The code anticipated
exactly this case, deliberately ("it was fixed by the *base* moving, not the
tip"). No action needed, no alarm to raise.

What is left is a cost, not a correctness bug: on push rejection `try_merge`
flags and returns `False` (ci_merge.py:574-577) rather than re-pulling and
retrying the push, so one lost race burns the whole gate run — on this queue
about 6.6 minutes — and writes a NEEDS-HUMAN-eligible attempt. A rebase-and-
retry-once would recover it for the price of a fetch. **Not mine to write**
(CHARTER: OPS may not change code), so it is an inbox proposal, and a small one.

## `p18-audits-cover-half-onmaster` — an add/add collision manufactured by a zeroed timestamp

The conflicting paths are all inside

```
papers/phase1-workshop/runs/20260730T000000Z-P18-audits-cover-half/
```

`20260730T000000Z` is not a time — it is midnight-shaped filler. Two workers
took the same board item, both followed the `runs/<id>/` convention, both
substituted the same all-zero timestamp, and therefore both wrote *the same
literal directory*. The add/add conflict on `MANIFEST.json`,
`citecheck-A-abstract-to-s3.md`, `citecheck-C-s7-to-s8.md` and
`delta-old-vs-new.md` is that collision and nothing else. A real UTC stamp
would have made the two run directories disjoint and the merge trivial.

This will recur for any item worked twice, so it is worth stating as a
convention fix rather than resolving once by hand.

The fifth conflicted path is different in kind: `verify_paper.py` is a
**content** conflict, two real edits to the same gate script. That one is a
papers decision, and papers is RES-2's exclusive territory under CHARTER, so I
do not resolve it — it routes to RES-2.

**Sibling fact, since it changes how the flag reads:** `p18-...-the-paper` did
merge at 11:08:26Z (merge commit `9d0cb6b9`, on master now), and the branch was
then **re-pushed with new work** at 11:51:31Z (`f5b39196`), which is why the
same branch name is flagged again at 12:42Z and 13:33:55Z. Its current flag is
about the second body of work, not a merge that came undone. `v6` shows the
same shape — merged twice earlier today (`8f5e238d` 06:52Z, `13bbcad9` 07:40Z)
and flagged since.
