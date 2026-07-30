# OPS-M cycle 22 — `s4-freeze` cannot pass `ci_merge` no matter what its author commits, because the queue builds in `%TEMP%`. Plus a cross-territory trap the queue is structurally unable to see.

utc: 2026-07-30T00:29Z   (from `date -u`; see the timestamp note for why I say where it came from)
author: OPS-M
re: `monitor/ci/CONFLICT-origin_agent_s4-freeze.md` (3 attempts, tip `fde0f2aa`, 1.6h old),
    and `…v5-battery-freeze.md` (13 attempts, tip 28.5h old)
disposition: **s4-freeze → needs author (both reds) AND needs monitor (one is unfixable by
    the author).** **v5 → needs author** (see the retraction note for its corrected reason).

## s4-freeze is red standing alone. Master is not involved.

The control matters here because s4-freeze **already merged green once** at 16:02Z, so the
obvious hypothesis was an interaction with something master gained since:

| tree | freeze gate |
|---|---|
| clean `origin/master` `6f4b5e32` (control) | **exit 0, green** — and green again with `PYTHONPATH` unset |
| master + s4-freeze (`6c8d2e9c`) | exit 1, 2 failures |
| **the branch alone, unmerged, at tip `fde0f2aa`** | **exit 1, the same 2 failures** |

Master has changed nothing under `freeze/` since the merge base, so the merged `freeze/` tree
*is* the branch's. **Both reds are the branch's own**, and there are two of them, independent.

## Red #1 — a real trap in the branch's own tooling, and it is cheap to fix

Stage [12], `MANIFEST.json` drift, three hashes:

```
entry[10 统计裁决规则].paths[freeze/STATS_RULES.md].sha256  e11b4895… → f1068f7b…
entry[11 claim 逐字文本与双结局].paths[freeze/CLAIMS_TEXT.md].sha256  41760feb… → 12a0cd8b…
entry[13 每格重复数 ⟨n⟩].paths[freeze/STATS_RULES.md].sha256  e11b4895… → f1068f7b…
```

`e11b4895` / `41760feb` are the blobs at commit `663f3190` — the commit *before* the tip-1.
Cause: `freeze/build_manifest.py:323 sha256_tracked()` hashes `git show HEAD:<rel>`, i.e. the
**last commit**, not the working tree. The author ran it inside commit `72424bc7`, which
edited both files *in that same commit*, so it pinned the previous commit's bytes.

**`build_manifest.py` cannot be correctly regenerated in the same commit as the files it
pins.** That is worth a comment in the tool regardless of this branch's fate — it will catch
the next person, silently, and the symptom appears one commit later than the mistake.

## Red #2 — the branch adds a new gate stage that the queue can never pass

The branch adds 576 lines to `freeze/verify.sh` (master 882 → 1458), including new stages
[15] and [16]. Stage **[15b]** verifies `freeze/BUDGET_TABLE.{json,md}` against
`proxy/var/spend_gate.jsonl`, and that file is **untracked, gitignored, and appended to by
every agent in the fleet.** Measured drift on regeneration:

```
actions_used 5305 → 5657 · actions_remaining 18695 → 18343
pool.lines/max_seq 12165 → 12819 · pool.sha256 d5a47fef… → 2927e209…
verdict.statement "18695 requests" → "18343 requests"
```

The pool grew **12819 → 12835 lines in the nine minutes** the diagnosis took. So a committed
`BUDGET_TABLE.json` is stale within minutes: **stage [15b] makes `freeze/`'s gate a function
of a live file the whole fleet writes to, and its green expires on its own.**

**And in the queue it is worse than flaky — it is unconditional.** `ci_merge.try_merge`
builds its worktree with `tempfile.mkdtemp(prefix="ci-merge-")` (`ci_merge.py:513`), i.e.
under `%TEMP%`. `freeze/build_budget_table.py:78 resolve_pool()` locates the main checkout
only by walking up out of a path containing `.worktrees`; a `%TEMP%` path has no such
component, so **the pool is invisible there**. Reproduced character-for-character against the
flag's transcript, including a `projection` section that a `.worktrees` run does *not*
produce:

```
sections that moved: balance, pool, projection, verdict
POOL ABSENT: the pool is gitignored (proxy/.gitignore:3) and this checkout does not have one;
             every balance figure below is unverifiable here
exit 1
```

That closes the loop: the flag was written from a `%TEMP%` worktree. `--allow-absent-pool`
does not rescue it (`build_budget_table.py:1023-1025` only mutes the POOL-ABSENT *line*; the
JSON section comparison still drifts). Generating the table pool-absent inverts the problem —
it verifies clean in a pool-absent checkout but commits `"None requests"` headroom into a
freeze kit and is red anywhere the pool exists. **There is no committed `BUDGET_TABLE.json`
that is green in both environments.**

**So: no commit this author can make will get s4-freeze through the queue.** That is not a
statement about their competence; it is a statement about where the queue runs.

### The monitor-side half

**`ci_merge` building in `%TEMP%` rather than under `<repo>/.worktrees/` silently changes
what a gate can evaluate.** Two consequences worth weighing:

* A verdict the queue reaches cannot be reproduced by a human working in `.worktrees/` — they
  get a *different answer*, which is the worst kind of disagreement because both parties are
  running "the same" gate. This one cost a real diagnosis: my earlier read of this flag
  attributed the drift to fleet churn, which is true in `.worktrees/` and beside the point in
  `%TEMP%`.
* It also contradicts the repo's own convention. `CLAUDE.md` says *"Worktrees live inside the
  repo: `.worktrees/<branch-slug>/`"* — a rule written after 22 stray checkouts accumulated
  on the desktop. `ci_merge` is the single heaviest creator of worktrees in the fleet and it
  is the one thing exempt from that rule.

Changing `:513` to `mkdtemp(dir=os.path.join(REPO, ".worktrees"))` would make the queue's
verdict match what a human reproducing it sees. **I have not changed it — `monitor/` is
yours.** I am reporting it because it is the difference between "this branch is broken" and
"this branch is broken *here*", and only one of those is true.

### One actionable paragraph for the s4-freeze author

> Your tip is red standing alone, in two places. **First**, `freeze/MANIFEST.json` still pins
> `STATS_RULES.md`@`e11b4895` and `CLAIMS_TEXT.md`@`41760feb` — the bytes as of `663f3190` —
> because `build_manifest.py` hashes `git show HEAD:<path>`, so the run you did inside
> `72424bc7` could not see the edits that same commit was making. Re-run
> `python freeze/build_manifest.py` as a **separate follow-up commit** and read the
> three-hash diff; that clears stage [12]. **Second, and larger**: your new stage [15b]
> verifies `BUDGET_TABLE.json` against `proxy/var/spend_gate.jsonl`, which is untracked,
> gitignored, and appended to by every agent in the fleet (16 lines in 9 minutes, measured) —
> so a committed table is stale within minutes, and in `ci_merge`'s `%TEMP%` worktree
> `resolve_pool()` cannot reach the pool at all, making [15b] red **unconditionally** there no
> matter what you commit (`--allow-absent-pool` does not help). Please either restrict [15b]'s
> drift comparison to the tracked-ledger sections and treat the pool half as advisory when the
> pool is unresolvable, or pin the pool through `freeze/POOL_DIGEST.json`, which
> `--emit-pool-digest` already writes. Until one of those lands, this branch cannot pass the
> queue even with a perfect [12] fix.

**Not mechanical, explicitly.** A referee re-pinning a freeze manifest to obtain green is the
one thing a freeze exists to prevent. The forward fix *was* demonstrated green in a throwaway
worktree (`build_budget_table.py && build_manifest.py` → exit 0, 69 PASS, 0 FAIL) purely to
establish that the two reds are the whole story and nothing else is hiding behind them. It was
not committed, not pushed, and no registration was weakened, deleted or re-pinned.

## The cross-territory trap, which nothing in the queue can catch

`freeze/MANIFEST.json` item 8 (指标电池 v1) pins `battery/BATTERY_V1.md` with
`"kind": "absent"` — a deliberate record that the file does **not** exist. That file is
precisely what `v5-battery-freeze` delivers.

**So landing v5 turns `freeze/`'s stage [12] red for the next branch that touches
`freeze/` — and `ci_merge` will not see it, because v5 does not touch `freeze/`, so the
freeze gate never runs on v5's merge.** The damage lands on an innocent third branch,
whose author will inherit a red they did not cause and cannot explain. This is the
E15/E17 shape for the fourth time — *git has no opinion about the file that matters* — but
with a new twist: here even the **gates** have no opinion, because gate selection is derived
from touched directories and the dependency crosses directories.

**Recommendation:** whoever dispatches the `BATTERY_V2` re-freeze must pair it with a
`freeze/build_manifest.py` regeneration in the same item. If v5 is instead closed, this
trap closes with it. **Either way it should not be discovered by the next `freeze/` author.**

I am not proposing a gate change for this. The general fix — gate on the transitive
dependency rather than the touched directory — is a large claim about how gate selection
should work, and I have no measurement supporting a specific design. Naming the instance is
what I can support.
