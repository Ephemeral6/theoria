# The queue's real scheduler, and my prediction that it falsified within 3 minutes

**Supersedes** the prediction at the end of `pass-growth.txt`. That prediction
(*"the pass running now is killed at 13:28:49Z with ~13-14 of 17 branches
logged"*) was **WRONG, and wrong before I finished writing it**: the pass had
already ended at `12:42:13Z`, 13.5 minutes in, having gated **3** branches and
written one `HELD 14 unchanged since last verdict` line. It released its lock
cleanly.

## Why I got it wrong

I modelled the queue's cost from `merge.log` alone and never read its scheduler.
`monitor/ci_merge.py` has a hold rule I did not know existed:

* `should_hold(memo, tip, base)` (`ci_merge.py:190`) skips a branch whose
  recorded `tip:` **and** recorded `base:` both still match reality. The flag
  file itself is the memo (`last_attempt`, `:161`).
* So a branch is re-gated only when **its own tip moves** or **`origin/master`
  moves**. Otherwise one summary line stands in for the whole held set
  (`:693`), and the pass costs minutes.
* `starved_first` (`:603`) orders the work longest-waiting-first, never-tried
  before that. `--max 2` caps successful *merges* per pass, not attempts.

Checked against the pass I mispredicted: the three branches it did gate are
exactly the three whose tips had moved since their last verdict — `c14` (new
branch), `a3` (tip `1e29578a` pushed 11:36:04Z, i.e. *during* the previous pass,
after that pass's opening `git fetch`, so the previous pass recorded the older
tip), and `p18-audits-cover-half-the-paper` (tip pushed 11:51:31Z after its
11:09:04Z merge). `origin/master` has not moved since 11:18:15Z. 3 gated + 14
held = 17 candidates. The model accounts for every branch.

## The corrected cost model

| pass kind | trigger | cost | observed |
|---|---|---|---|
| **full** | `origin/master` moved since the last pass — no verdict can be held | ~4 min × every candidate + ~5 min startup | 10:14:12Z (13 logged, **killed at start+3600s**), 11:19:10Z (15 logged, exited on its own with 4.5 min to spare) |
| **cheap** | master still; only branches whose own tips moved | minutes | 12:28:49Z (3 gated, 14 held, 13.5 min) |

`reflex.py:346` kills `ci_merge` at `timeout=3600`. A full pass over the current
**17** candidates costs ~68 min of gate work plus ~5 min of startup. **The full
pass has therefore crossed the timeout that kills it**, and the two observed
full passes sit either side of the line (55 min survived, 60 min killed).

## What that actually means — and it is not "the queue is slow"

**Every push to `origin/master` invalidates all 17 held verdicts and buys a full
pass that can no longer finish.** Six-plus agents push. So does this report. The
casualties are the branches at the *end* of `starved_first`'s order, i.e. the
ones most recently first-seen — the fleet's freshest work is what gets dropped,
and it is dropped silently, because a branch that is never reached gets no line
at all (`HELD` covers only branches that were *considered*).

Two fixes, and they are independent:

1. **Raise or guard `reflex.py:346`'s `timeout=3600`** (monitor's one-line
   change; `monitor/` is the monitor's territory, not mine). A full pass needs
   ~75 min of headroom today and more with every new flag.
2. **Cut the candidate count.** Nine of the 17 are flagged for master's *own*
   red monitor gate. Each costs ~4 min of every full pass. Ruling the innocent
   ones in is the same fix as breaking the deadlock — this is the second time
   this cycle that those two problems turn out to be one problem.

## New prediction, and this one I am about to cause myself

Pushing this commit moves `origin/master`, which invalidates all 17 held
verdicts, which makes the next pass a **full** pass. So:

> The first pass after my push gates ~13-15 of 17 candidates, is **killed** at
> its start + 3600 s (no clean lock release; `finally` never runs), writes **no**
> `HELD` line — nothing can be held when the base has moved — and leaves the
> last few branches in `starved_first` order with no log line at all. No new
> line appears in `monitor/reflex.log` either, because reflex dies at
> `scan.py`'s unguarded 600 s timeout two lines before its heartbeat.

Falsifiers, stated in advance: a `HELD` line in that pass; all 17 gated; a clean
exit before start+3600 s; or a new `reflex.log` line. Watcher:
`monitor/runs/opsm32/pass-watch.log`.

**The honest lesson**: I published a cost model for a scheduler I had not read,
twice in one cycle — first "flags never clear", then "the queue is fine". Both
came from reading its log instead of its code. The log is what the queue says
about itself; the code is what it does.
