# AGENT-H — adversarial review of OPS-M's merge-queue conclusion

Read-only on the main checkout. No worktree created, no process touched, no lock touched.
Verdicts are labelled by which version of OPS-M's claim they address:

* **v1** = `monitor/runs/opsm32/pass-cadence.txt` — "cycle 31's SPIRAL is refuted; the queue is fine, only reflex's end-of-cycle log line is broken"
* **v2** = `monitor/runs/opsm32/pass-growth.txt` — "the queue is MARGINAL; ~3.3–4.0 min per flagged branch; pass duration ≈ timeout"
* **v3** = `monitor/runs/opsm32/pass-model-CORRECTED.md` + coordinator message — "two kinds of pass: full (first after a master push, nothing holdable, ~4 min/candidate, ~73 min for 17) vs cheap; full passes straddle `timeout=3600`"

Headline: **one component of v3 is REFUTED** (the "full iff master moved" rule), **one is REFUTED in framing though its mechanism is confirmed** (permanent tail starvation), and **a new finding severs the last link between the two alarms**: reflex dies every cycle in `scan.py`, on cheap passes too, so the liveness outage is not the queue's margin at all.

---

## v3-1. Segmentation rule (">12 min gap or branch repeat") — SURVIVED, but the table's columns are not what they say

**Sound part.** "Branch repeat ⇒ new pass" is provably sound from the code: `todo` is built by `unmerged_branches()` appending each ref once (`ci_merge.py:448`), and `main()`'s loop (`:666`) iterates it once, so no branch can be gated twice in one pass. `--max` (`:635/:667`) caps *successful merges*, not attempts, so it cannot end a pass early unless two merges succeed.

**Measured separation, today's log.** Max FLAG→FLAG gap *inside* a pass = **10m44s** (a3 in the 08:41 pass: 08:41:47 → 08:52:31). Min gap *between* passes = **14m24s** (03:48:50 → 04:03:14). Every inter-pass gap today is ≥14m24s and every intra-pass FLAG→FLAG gap ≤10m44s, so the 12-minute threshold lands cleanly in the empty band. I tried to break it and could not, for today's data.

**Where it is thin — a real intra-pass interval already exceeds the threshold.** The 10:14 pass logged `SWEEP-FLAGS` at 10:14:15Z and its first `FLAG` at 10:26:34Z: **12m19s of one pass, one branch (v6's monitor gate)**. That is above the 12-minute rule. It did not split the pass only because the segmenter ignores non-FLAG/MERGED lines. A single monitor gate has `timeout=1800` (`ci_merge.py:543`), so an interval of 12–30 min between two FLAG lines is available at any time; when it happens the growth table will show two short passes where there was one long one, i.e. the trend can be manufactured by the rule.

**Two column defects.**

* *"branches" excludes held branches.* Held branches produce no per-branch line — one `HELD n` line stands for all of them (`:693`), truncated at 8 names. So the column counts *gate runs*, not candidates. Consequence: four **complete** passes are missing from or misrendered in the table — 06:07:14, 06:22:11, 06:40:28 and 09:59:23 each gated 0 branches and held 12–14, and 09:42:45 (1 gated + `HELD 13`) appears as the degenerate row "09:42:45 09:42:45 0m 1 0.0". Those five passes each had 12–14 flagged branches and cost ~0–3 min of gate work, which by itself refutes v2's "each flagged branch adds 3.3–4.0 min to the pass".
* *"start" is the first FLAG line, and there is no real start marker.* `SWEEP-FLAGS` is the only pre-loop line and it is conditional. But the 10:14 pass dates it: process start 10:14:12Z (cycle 30's observation) → `SWEEP-FLAGS` 10:14:15Z. `sweep_stale_flags` runs *after* `unmerged_branches()` (`:652–656`), so **fetch + snapshot + sweep took 3 seconds, not "~5–6 min"**. The 5–6 min v2/v3 book as startup overhead is the first branch's own gate. Totals unchanged; per-branch coefficient goes up, "startup" goes to ~0.

Verdict: **SURVIVED** as a segmentation of today's log; **WEAKENED** as a measuring instrument (the boundary rule is 1m35s away from a demonstrated intra-pass interval, and the "branches" column silently drops the held set).

Reproduce: `.worktrees/opsm32-out/` has no script; the segmentation + master-move join was run inline (see §v3-2 table).

---

## v3-2. "full iff origin/master moved since the previous pass" — **REFUTED**

Re-segmenting today's `monitor/ci/merge.log` with OPS-M's own rule and joining against master's push times from `.git/logs/refs/remotes/origin/master` gives **3 genuine counterexamples out of 24 real passes** (excluding 3 rows that are only CLEARED/SWEEP/BLOCKED lines):

| pass (first→last line) | gated | held | master moved before it | verdict |
|---|---|---|---|---|
| 01:17:16 → 01:37:08 | 7 | **7** | 01:04:47, 01:05:06 | **MIXED** — predicted full, observed both |
| 05:00:10 → 05:44:04 | 15 | none | **none since 04:56:25** | **full without a master move** |
| 06:52:35 → 07:26:09 | 14 | none | **none since 05:16:09** | **full without a master move** |

All other passes fit (00:05, 00:32, 01:02, 02:45, 03:26, 03:47, 04:29, 07:46, 08:41, 10:14/10:26, 11:25 full; 01:55, 02:07, 02:30, 06:07, 06:22, 06:40, 09:42, 09:59, 12:34 cheap).

**Counterexample 1 is structural, not noise.** ci_merge pushes master itself on every successful merge (`:575`), so master routinely moves *mid-pass* — 01:04:47, 01:05:06, 06:57:21, 11:09:02 today. Flags written before the move record the old base, flags written after record the new one. The next pass is therefore **partly** holdable. "Two kinds of pass" is really a continuum indexed by *how many flags were written before the last master move*. Since a full pass is the expensive one, this matters: a merge that succeeds early in a pass guarantees the next pass is partly full.

**Counterexamples 2 and 3 expose a third invalidation channel, and it is a bug.**
`monitor/ci/CONFLICT-*.md` are **tracked** — `git ls-files monitor/ci` lists them. The queue's memory therefore lives in git, and git can rewrite it:

```
$ git show HEAD:monitor/ci/CONFLICT-origin_agent_a3-campaign-devpile.md | head -8
reason: verify gate red in theoria-arm (verify.py)
tip:  a5812063…      base: 3d59d0a6…      last_seen: 2026-07-30T04:03:14Z   attempts: 21
$ head -8 monitor/ci/CONFLICT-origin_agent_a3-campaign-devpile.md
reason: verify gate red in monitor (verify.sh)
tip:  1e29578a…      base: cc7e414e…      last_seen: 2026-07-30T12:41:15Z   attempts: 29
```

Any `git checkout` / `pull` / `stash` / `restore` / branch-merge in the main checkout that touches `monitor/ci` reverts every memo to a **04:03Z** state. That (a) forces a full pass, and (b) **rewinds `attempts:` from 29 to 21**. The only commit touching `monitor/ci` today is `ab85017d` at **04:45:32Z**, and the next pass — **05:00:10Z** — is counterexample 2. Counterexample 3 (06:52:35) I cannot explain from any channel visible in the logs; it stands as an unexplained full pass.

Two consequences OPS-M should carry:

* "Full" passes are not controllable by "stop pushing master" — a routine git operation on the checkout can trigger one.
* **v1's arithmetic is built on a rewindable counter.** `attempts:` / `first_seen:` are not monotone, so "54–85 min per attempt over 32 hours" is a lower bound on elapsed-per-attempt at best. `attempts` for a3 is 29 in the tree and 21 in HEAD.

---

## v3-3. "~4 min per candidate, ~73 min for 17" — WEAKENED; and no, the trend is not OPS-M's own load

**The coefficient is a mixture average, and it is only accidentally right for today's mix.** Per-branch cost (Δ from the previous log line, branches are processed serially) is set by *which gate runs*, and spans two orders of magnitude:

| gate | branches today | observed cost |
|---|---|---|
| `monitor` verify.sh | a3, s38, s39, c13, s40, s41, s42, v6, c14 (9) | 4m52s – 10m44s, mean ≈ 6.6m |
| `freeze` verify.sh | s4-freeze, s4-e23 (2) | 48s – 5m16s, mostly ~1m |
| `release` verify.sh | r3, r4 (2) | 56s – 2m04s |
| `papers` verify.py | p18-the-paper (1) | 22s – 52s |
| merge conflict, no gate | v5, e8, p18-onmaster (3) | **6s – 33s** |

Bottom-up for today's 17: 9×6.6 + 2×1 + 2×1.5 + 1 + 3×0.3 ≈ **67 min**, plus ~0 startup. So v3's ~73 min is close — but the per-*candidate* mean would be badly wrong for a different mix (17 conflict-only branches ⇒ ~6 min). The load-bearing quantity is **the number of monitor-gated candidates**, not the candidate count. That makes v3's own closing paragraph (clear the 9 branches held on master's red monitor gate) *more* justified than v3's arithmetic shows, not less.

**Load contamination: checked, and it does not produce the trend.** Same-branch cost across passes shows no monotone growth:

| branch | 07:46 pass | 08:41 | 10:26 | 11:19 | 12:34 (8 subagents) |
|---|---|---|---|---|---|
| a3 | 5m06 | 10m44 | 7m46 | **5m02** | 7m13 |
| s38 | 7m00 | 5m11 | 9m14 | **4m53** | — |
| s39 | 7m30 | 6m01 | 9m21 | 6m03 | — |
| c13 | 7m50 | 5m54 | 8m05 | 8m30 | — |

The 11:19 pass — the 49-minute one v2/v3 lean on — has the day's **lowest** per-branch costs for a3 and s38. Its 49 min came from carrying 8 monitor-gated branches, not from load. So: **the growth is a count effect and is real; OPS-M did not manufacture it.**

But the *margin* is load-dependent by roughly ±40%: a3 cost 7m13 under the 8 subagents vs 5m02 at 11:36. Scaling monitor gates to their idle-machine end (~5.0 min) gives **≈52 min for today's 17 — under the 3600 s timeout**; at the loaded end, ≈67–75 min — over it. Therefore:

> "The full pass has crossed its timeout" is true **only under load**, and OPS-M's own 8 concurrent pytest subagents are sufficient load to make it cross.

That is a self-contamination warning for the live prediction: a kill at (start + 3600 s) tonight would be partly OPS-M's doing and is **not** evidence about the unattended steady state. State the load in the prediction, or run the confirming pass with the subagents stopped.

---

## v3-4. Starvation — mechanism CONFIRMED exactly; "13 of ~15–16" and "permanent" REFUTED

**Candidate reconstruction at 10:14:12Z** (reflog tips at that instant, ancestry-tested against master-at-that-instant `74e090e`): **14 candidates**, not "~15–16" — the 13 reflog-derivable ones plus `p18-audits-cover-half-the-paper`, whose pre-11:51 reflog file was pruned when ci_merge deleted the remote branch at 11:09:04. Logged: **13** (12 FLAG + 1 MERGED).

**Exactly one branch got no line: `s40-fleetkit-fork-has-drifted`.** The "missing 2–3" in v3's "15–16" is `s41` (pushed **10:16:30Z**) and `s42` (**10:21:48Z**) — both pushed *after* the 10:14:12Z snapshot, so never candidates in that pass. Source: `.git/logs/refs/remotes/origin/agent/*`, message `update by push`.

**Order prediction, exact.** `starved_first` (`:603`) sorts by first-FLAG time from `mergequeue.read_log` (`:85` records `first` only from FLAG lines), never-flagged at 0.0. Predicted order for the 10:14 pass: v6 (never *FLAGged* before — its earlier lines are MERGED), then v5, a3, e8, s4-freeze, r3, r4, s4-e23, p18-onmaster, s38, s39, c13, p18-the-paper (first flag 06:52:35), **s40 (first flag 08:41:33) last**. Observed order is that, exactly, and the dropped branch is the predicted tail. **Mechanism confirmed.** Death at 10:14:12 + 3600 s with s40's gate in flight is the parsimonious reading, and there is no s40 line, so it was not a clean exit.

**"Pushes the tail toward permanent starvation" is refuted by the same data.** The tail position *rotates*: `first` is the first-FLAG time, so a branch that receives its first flag becomes the new tail and previously-starved branches move up. Newly pushed, never-flagged branches sort to the **front** (0.0), so a new branch is never starved. Observed: s40 starved at 10:14, **served at 12:04:35 in the very next full pass**; by then v6 (first flag 10:26:34) was the tail, and v6 was served too (12:14:21). Today's total starvation: **one branch, one pass, ≈110 min of extra wait.** Not permanent, and self-correcting at the current 1-of-14 loss rate.

**"Leaves merge.lock behind" is true but harmless by construction — predicting it as damage over-reports.** `take_lock` (`:429`) deletes a lock older than 3600 s; reflex kills ci_merge at exactly 3600 s; the lock's mtime is set within seconds of pass start (proven by `SWEEP-FLAGS` 3 s after process start). So a timeout-killed lock is always ≥3600 s old by the time any later pass reads it. There is no `BLOCKED` line after the 11:14:32 kill. The two `BLOCKED` lines today (04:56:35, 04:56:47) are concurrent reflex instances, not kill residue. `monitor/ci/merge.lock` does not exist as of 12:54:44Z.

---

## v3-5 / v1-5. NEW: reflex's death is not the queue's — it dies in `scan.py` every cycle, cheap passes included

This severs the link both v2 and v3 assume between "the pass gets killed" and "reflex writes no line".

| cycle | ci_merge gone | reflex gone | Δ | cause |
|---|---|---|---|---|
| 11:19 (full, 15 gated) | 12:14:05–12:14:36Z (pid 2220) | 12:23:56–12:24:28Z (pid 42104) | ≈ +9m30s–10m20s | `scan.py`, `reflex.py:361` `timeout=600` |
| 12:28 (**cheap**, 3 gated + HELD 14, 13.5 min) | by 12:44:32Z (pid 2592) | 12:51:48–12:52:50Z (pid 6328) | ≈ +600 s | same |

Evidence: `monitor/runs/opsm32/salvaged-cycle31/prediction-check.log` lines 33–53; `monitor/runs/opsm32/pass-watch.log` at 12:51:48Z / 12:52:50Z. `monitor/reflex.log` has been stuck at **280 lines since 08:32:21Z**.

The 12:28 cycle is decisive: the pass ended cleanly in 13.5 minutes with all 17 candidates accounted for (3 gated + `HELD 14`), `git pull` ran, lock released — **and reflex still died, at ci_merge-end + 600 s.** So reflex dies every cycle from `scan.py` exceeding its own timeout, regardless of the queue. Whatever the queue's margin is, the liveness outage has a separate, always-firing cause, and fixing the queue will not restore `reflex.log`.

**What is actually lost when reflex dies there** (everything after `reflex.py:361`): the `rlog` line at `:363`, and `scan.py`'s completion. Everything else is upstream and still runs every cycle — launch queue (`:131`), board sweep incl. standing-claim release (`:160`), dashboard-server keepalive (`:176`), reap (`:209`), quota check/probe/resume (`:215`), worker headcount (`:260`), revive (`:306`), ci_merge (`:344`). So v1-5's reassurance mostly holds — with one correction it under-reported: **`scan.py` never finishes**, so `monitor/index.html` and every probe scan.py drives are stale, not merely a missing log line. That is more than "a log line", and it is the thing to fix first because it fires on every cycle.

As of **12:54:44Z** there is no reflex and no ci_merge process running; `merge.lock` absent; `merge.log` unchanged since 12:42:13Z. The next pass depends on the scheduled task's next tick. OPS-M's push at 12:48:24Z (`232348e`) did invalidate all 17 memos (every flag now records `base: cc7e414` ≠ `232348e`), so the next pass will indeed be a full 17 — the live prediction is well set up, subject to the load caveat in §v3-3.

---

## Bottom line: **publish AMENDED**

The revised (v3) reading is close to right and much better founded than v1 or v2. Four amendments are load-bearing; the last two are the ones I would not publish without.

1. **Drop "full iff origin/master moved".** Replace with: *a branch is re-gated when its recorded `tip` or `base` no longer matches reality; three things break the match — its own tip moving, `origin/master` moving (including ci_merge's own mid-pass push, which makes **mixed** passes routine), and any git operation that rewrites the tracked `monitor/ci/CONFLICT-*.md` files.* Name the counterexamples: 01:17:16 (7 gated + HELD 7), 05:00:10 and 06:52:35 (full with no master move).
2. **Report the bug the third channel is.** `monitor/ci/CONFLICT-*.md` are tracked; `git show HEAD:` on the a3 flag returns `base 3d59d0a / attempts 21 / last_seen 04:03:14Z` against a working tree at `cc7e414 / 29 / 12:41:15Z`. The queue's memory — and the `attempts` counter v1's arithmetic rests on — is rewindable by a checkout or pull. Say that v1's "54–85 min per attempt" is therefore a bound, not a measurement.
3. **Re-state the cost model per gate, not per candidate.** ~6.6 min per *monitor-gated* branch, ~1–2 min for freeze/release/papers, 6–33 s for conflict-only branches, ~0 for held, ~3 s startup (not 5–6 min — measured from `SWEEP-FLAGS` at 10:14:15Z, 3 s after process start). Today's 17 ⇒ ≈52 min idle, ≈67–75 min loaded, against 3600 s. State plainly: **the crossing is load-dependent, and OPS-M's own 8 pytest subagents are enough load to cause it** — so the confirming pass should be run with them stopped, or the prediction reported as conditional on load.
4. **Correct the starvation numbers and drop "permanent".** The 10:14 pass had **14** candidates, logged 13, and starved **exactly one** — `s40`, which is precisely the tail of `starved_first`'s ordering, and which was served in the next full pass at 12:04:35. `s41`/`s42` were pushed at 10:16:30Z/10:21:48Z, after the snapshot, and were never candidates. The tail rotates because `first` is the first-FLAG time, and never-flagged branches sort to the front — so at today's loss rate (1 of 14) starvation is self-correcting, ~110 min of extra wait. Keep the mechanism, drop the word "permanent".
5. **Separate the two alarms in the write-up.** reflex died at ci_merge-end + 600 s on the 12:28 **cheap** pass — a 13.5-minute pass with all 17 candidates accounted for. `scan.py` overrunning `reflex.py:361`'s `timeout=600` kills reflex every cycle regardless of the queue. Presenting the 3600 s kill and the reflex silence as one phenomenon is the third version of the same error: pointing one alarm at two components.
6. **Note that "leaves merge.lock behind" is not damage.** `take_lock`'s 3600 s staleness threshold equals reflex's ci_merge timeout, so a timeout-killed lock is stale on arrival and self-clears; no `BLOCKED` line followed the 11:14:32 kill.

What I could not break: the segmentation (clean 10m44s / 14m24s separation today, though a 12m19s single-gate interval already exceeds the 12-minute rule and `timeout=1800` allows much longer), the `starved_first` order prediction (exact, to the branch), and the finding that the historical growth is a real count effect rather than an artefact of OPS-M's own load.
