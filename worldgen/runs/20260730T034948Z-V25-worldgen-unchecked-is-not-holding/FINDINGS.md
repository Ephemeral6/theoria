# V25 — findings (written incrementally as the audit ran)

Worker W-1693. Territory `worldgen`. Base commit `3b2a5873`.

## Req 1 — 先判现状：the fix IS on master. The work order's premise is stale.

The work order says «修复提交 `23ec179` **不在 master 上**». That was true when the
audit ran and is **false now**. All three commits of the repair are ancestors of
master:

| commit | subject | on master |
|---|---|---|
| `23ec1793` | worldgen: "I could not check this" was being written as "this holds" | yes |
| `abd9d47b` | worldgen: the adversarial pass found the defect rebuilt inside its own repair | yes |
| `57e6c716` | worldgen: unverified is not true -- and the first repair rebuilt the defect inside itself | yes |

Evidence: `evidence/01-merge-status.txt`.

### Why it did not merge, and how it eventually did

The branch was `agent/v19-unverified-is-not-true`. `monitor/ci/merge.log` records
the whole stall:

```
2026-07-29T02:50:00Z  FLAG origin/agent/v19-unverified-is-not-true: merge conflict
2026-07-29T02:57:00Z  FLAG  … (same)
2026-07-29T03:06:22Z  FLAG  … 03:16:03Z, 03:30:02Z, 03:45:45Z, 04:02:37Z, 04:33:01Z
2026-07-29T10:29:45Z  HELD 10 unchanged since last verdict: … v19-unverified-is-not-true (merge conflict, 1x)
2026-07-29T14:19:43Z  CLEARED-BY-OPS-M flags for a10-shared-ledger-real-arms,
                      v19-unverified-is-not-true, p13-figure-numbering
                      (merged to master by hand: the conflict resolutions were made
                       in a previous session's worktrees and ci_merge cannot reproduce them)
```

**The merge blocker, stated plainly:** eight consecutive `ci_merge` cycles failed
with a merge conflict, because the conflict resolution existed only in a previous
session's worktree — `ci_merge` replays merges from scratch and cannot reproduce a
resolution nobody committed. It was resolved by OPS-M merging **by hand** as
`b7783af7` at `2026-07-29T21:10:03+08:00` (= 13:10Z).

Per the work order («已经修好只是没合，就把合并卡点写清楚并推动»): the blocker is
written up above, and there is nothing left to push — it landed before this item
was claimed. **No repair work was needed for req 1.** What remains is to check
that what landed actually satisfies reqs 2–4, which is the rest of this document.

### A consequence outside this territory (registered, not touched)

`papers/phase1-workshop/sections/10_adjudication.md:110-135` still asserts this
defect «is the one of the four that is **not** repaired … the line stands
byte-for-byte unchanged on the mainline». That is now false, and the section was
edited at `2026-07-29T22:42Z+08:00` and `PAPER.md` at `2026-07-30T04:52Z+08:00`,
both **after** the fix landed — so it is not merely a stale draft, it is a claim
that survived two passes after it became false, inside the section about honesty.
Filed to `monitor/inbox/20260730T035500Z-W-1693-paper-says-unrepaired-about-a-line-repaired-on-master.md`.
Not edited here: `papers/` is not this territory.

### No foreign consumer

Nothing outside `worldgen/` reads `invariants_all_hold`, `invariant_failures` or
`invariant_unverified` as *code*; every hit outside the territory is prose or a
fleet-study record. So the blast radius of the old boolean was confined to
worldgen's own build gate, and the repair did not leave a stale reader elsewhere.

## Req 2 / 3 / 4 and the same-family sweep

Farmed out to four independent auditors; results below, added as they land.

## Baseline

`python -m pytest` in `worldgen/` at base commit: **593 passed, 13 skipped**
(`evidence/00-baseline-pytest.txt`).
