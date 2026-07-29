# item13 working notes — S4-freeze-complete, closing the ⚠ on freeze item #13

Subagent of RES-1. Worktree `.worktrees/s4-freeze`, branch `agent/s4-freeze`,
HEAD `5822e5e5c4c87e42f834ddca76f3af56eee3e7b6`.
Write territory: `freeze/` only. No git add/commit/push. `verify.sh` not edited.

## Order of work and what each step returned

1. **Trackedness of `baseline-arms/out/campaign/`** → `git-queries.txt`.
   **It is tracked.** Four blobs in the index, `git check-ignore` exit 1 (not
   ignored), `git status --short` on the directory is empty (index == disk).
   Added by `9307f139` "A14: the four campaign artefacts were paid for and were
   in nobody's git", which is an ancestor of both HEAD and `origin/master`.
   → the premise of the ⚠ (and of MANIFEST_DRAFT gap 13-a) is **stale**, fixed
   by A14 as the task brief suspected. Cite the tracked blobs; invent nothing.

2. **Recompute §5 from the tracked blobs** → `recompute_item13.py`,
   `recompute-transcript.txt`. Reads via `git show HEAD:<path>`, deliberately
   not from the working tree: item #13 is about what is hashable at freeze time,
   so the recomputation has to run on the object git would publish.
   Result: §5.2 / §5.3 reproduce essentially exactly. Two transcription defects,
   both cosmetic, both recorded in `VARIANCE_BASIS.md` §6.

3. **Second basis.** Grepping `degraded` turned up
   `baseline-arms/runs/20260728T103135Z-a7/envelope.json` — tracked, and its
   `RUN_STATE.md:17-20` says it exists to produce "the variance estimate Phase 4
   needs to fix its per-cell repeat count ⟨n⟩", i.e. item #13's own job.
   **§5 never cites it.** → `recompute_a7_basis.py`,
   `recompute-a7-transcript.txt`. The two tracked bases disagree ~20x on the
   same quantity, and A7's own sizing says n=3.

4. **ar25 sensitivity.** `degraded` in the tree is a *per-cell* exclusion of
   3 ar25×haiku cells from the A7 envelope, with a written reason. Those three
   cells survive in the tracked append-only
   `baseline-arms/out/campaign_cells.jsonl` under
   `campaign="phase3-variance-envelope"`, so the include/exclude sensitivity is
   computable from tracked bytes. **The surrogate 0.10-CV test flips.** The
   endpoint argument does not. Both numbers reported.

5. **Gate and manifest reading.** `verify.sh` stage 7 already re-runs the §5
   arithmetic *and* asserts provenance identity — good — but resolves its data
   by filesystem path with an absolute fallback to the **main** checkout, so it
   cannot tell tracked from untracked. `build_manifest.py:229-243` item 13 still
   says "**No value exists anywhere on master**" and withdraws the n=2 ruling.

## Cross-checks that mattered

* `started` on the A7 envelope cells is `18:21:28Z`; on the campaign batch it is
  `18:19:36Z`. Two genuinely distinct batches — this is what lets the A7 basis
  carry an ar25 contrast that §5.3 correctly says the campaign batch cannot.
* `campaign_cells.jsonl` holds 19 cells total; only 3 are ar25, all
  `phase3-variance-envelope`, all `api_unusable`, all `actions_failed=10` at
  `budget=30` — the non-scaling abort threshold of BUDGET_REPORT §11.2, visible
  in the data.
* `levels_completed` is 0 in every cell of every basis: 48/48 campaign episodes,
  9/9 A7 cells, 12/12 with ar25 included. The floor is universal.

## Deliberately not done

* `baseline-arms/` is read-only to this subagent, so
  `freeze/runs/2026-07-28T1200Z-p22/envelope_stats.py:9`'s hardcoded main-checkout
  path is recorded, not fixed (same class as the V24 battery-blind hardcoded
  path). It is inside `freeze/` so RES-1 *may* fix it; it is another run
  record's artefact, so I left it.
* `freeze/verify.sh` not touched (two other subagents share this worktree).
  A paste-ready stage snippet is in `VARIANCE_BASIS.md` §8 instead.
* `freeze/STATS_RULES.md`, `MANIFEST_DRAFT.md`, `build_manifest.py` not edited —
  they are the S4C-manifest-drift subagent's and RES-1's surfaces. Every stale
  line is named with `path:line` in `VARIANCE_BASIS.md` §7 for RES-1 to wire.

## Independent confirmations (recorded last)

* `bash freeze/verify.sh` stage 7, run at HEAD, prints
  `episodes=48  negbinom obs/pred=1.014  infra-death=0.979  U3-wins=0`,
  `provenance=OK`, 4 PASS. **Identical to my independent recomputation from
  `git show HEAD:`** — so §5's arithmetic is confirmed twice, by two code paths.
  (Full verify.sh exits 1 on other stages; pre-existing, not touched by me.)
* The §8 verify.sh snippet was executed standalone against this worktree before
  being written down: 3 PASS including the negative control
  (6/6 tracked, index == disk, an absent path is detected as untracked).
  The temp copy used for that test was deleted; `verify.sh` itself is unmodified.
* `git status --porcelain -- . ':!freeze' ':!monitor'` is empty: nothing was
  written outside `freeze/`. My additions are `freeze/VARIANCE_BASIS.md` and
  this run directory. (`freeze/n_feasibility.py` and `freeze/residuals.py` in the
  same status output belong to the other two subagents in this worktree.)
