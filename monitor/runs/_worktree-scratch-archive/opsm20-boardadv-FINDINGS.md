# Adversarial review of OPS-M's "board says done, master never got it" claim

Reviewer: adversarial subagent. Read-only. Zero API spend, zero sealed-pile contact,
zero network except local git plumbing against already-fetched refs.
Clock at time of review: `2026-07-29T21:45:03Z` (`date -u`).

**Verdict in one line: the arithmetic core reproduces exactly, but the claim is not a
finding — it is a re-report of a ruling the monitor already published and already
instrumented — and the two numbers OPS-M attached to it ("5", "4 of 5 stuck 17 hours")
are both wrong.**

---

## Findings, ranked by how much they change what OPS-M reports

### R1 — The finding already exists, is already ruled on, and is already a shipped probe. HIGHEST IMPACT.

`monitor/spec.py:669-672`, inside finding **F-20** (`monitor/spec.py:642`), marked
`【已裁决·监控代行 2026-07-29】`:

> "(2) 计分口径改正：**一件交付只有进了 master 才计分**，板上 done 只代表工人交了活；
> 差额由合并队列负责，不该由计分掩盖。(3) 上板：S25-probe-the-merge-queue（21 个探针没有
> 一个读 merge.log，所以五条分支被重刷 FLAG 十小时在仪表盘上完全不可见）…"

That is OPS-M's "intended conclusion", verbatim, adjudicated, and it names the same
five-branch backlog. It is not a discovered defect; it is the documented semantics.

Worse for the claim: the ruling was *acted on*. Board item `S25-probe-the-merge-queue`
was delivered and merged (`monitor/ci/merge.log`, `MERGED origin/agent/s25-probe-the-merge-queue`
at `2026-07-29T05:53:24Z`, again 05:58 and 06:18). Its deliverable is
`monitor/mergequeue.py:175` `done_not_on_master()`:

> "Board items marked done whose branch is not on master. **The board's `done` means
> "pushed", and merging is a different machine.** When the two diverge the score keeps
> climbing while master gains nothing."

and it is wired into the dashboard: `monitor/scan.py:1141` `_landed_gap()` →
`state["landed"]` (`monitor/scan.py:2371`), whose own comment
(`monitor/scan.py:1144-1145`) reads "这一格是今天最贵的一课的量化：把「板上 done」当成
「已落地」计分，headline 就虚高了 11.5 个百分点."

I ran the shipped probe (read-only, no fetch — `mergequeue.unmerged_branches()` does not
fetch, unlike `ci_merge.unmerged_branches()`):

```
$ python -c "import sys;sys.path.insert(0,'monitor');import mergequeue as mq;..."
done_not_on_master(): 6
   {'item': 'A13-sealed-audit-reads-the-wrong-fields', 'branch': 'agent/a13-...', 'state': 'unpushed'}
   {'item': 'E8-ic3-scale',                   'branch': 'origin/agent/e8-ic3-scale',   'state': 'queued'}
   {'item': 'R3-release-classifier-defaults', 'branch': 'origin/agent/r3-...',         'state': 'queued'}
   {'item': 'S11-sealed-halfguard',           'branch': 'origin/agent/s11-...',        'state': 'queued'}
   {'item': 'V21-leakage-gate-token-level',   'branch': 'origin/agent/v21-...',        'state': 'queued'}
   {'item': 'V5-battery-freeze',              'branch': 'origin/agent/v5-battery-freeze','state': 'queued'}
```

**OPS-M rebuilt an existing instrument by hand, got a different answer from it, and did
not reconcile the two.** Reporting "I measured that…" for a quantity the dashboard has
been printing since 06:18Z is the same class of error as the vacuous grep it already
caught itself making this cycle.

**What would refute R1:** evidence that F-20's action (2) was never merged into
`spec.py` on master, or that `_landed_gap()` is dead code. I checked: `spec.py:671` is
present in the working tree and the string is rendered into `monitor/index.html:433`
and `monitor/state.json:1070`. It is live.

### R2 — The count is wrong. It is 6, not 5, and the 6th is missed by OPS-M *and* by the shipped probe.

I reproduced OPS-M's method independently (strip `.W-####/.RES-#/.OPS-X/.APP-X` and
`.md`, lowercase, prefix `origin/agent/`, `git merge-base --is-ancestor <b> origin/master`):

- 122 done entries — **confirmed** (`ls monitor/board/done | wc -l` → 122).
- matched an existing remote branch: **15**, not 14.
- of those, not ancestors of `origin/master`: **5**, and they are OPS-M's exact five.

The 15/14 gap is OPS-M's regex: it does not strip `APP-*` claimants, so
`A7-envelope-finish.APP-A7.md` fell into the unmatched pile. That entry *is* landed
(`origin/agent/a7-envelope-finish` is an ancestor), so the bug was benign here — but it
is an undeclared blind spot in the instrument, and three more `APP-*` entries exist
(`C7-dsl-v03-mentions.APP-C7`, `P7-paper-section7.APP-P7`, `V3-battery-discrimination.APP-V3`).

**The real sixth: `P5-R4-ruling-path-for-undetermined.RES-4.md`.**

```
$ git rev-list --count origin/master..origin/agent/r4-ruling-path   → 8
$ git merge-base --is-ancestor origin/agent/r4-ruling-path origin/master → non-zero
$ git cat-file -e origin/master:release/tests/test_rulings.py       → ABSENT
$ grep r4-ruling-path monitor/ci/merge.log
  2026-07-29T21:30:06Z FLAG origin/agent/r4-ruling-path: verify gate red in release
     (verify.sh)  [NEEDS-HUMAN: 4 attempts since 2026-07-29T19:02:54Z]
```

`monitor/board/board.log` confirms the pairing: `2026-07-29T18:30:32Z CLAIM
P5-R4-ruling-path-for-undetermined by RES-4` … `2026-07-29T19:01:45Z DONE
P5-R4-ruling-path-for-undetermined by RES-4`, and the done file's body
(`monitor/board/done/P5-R4-ruling-path-for-undetermined.RES-4.md`) specifies exactly
`release/RULINGS.jsonl` — which is what the branch's 746-line `release/tests/test_rulings.py`
tests. Same work. Unlanded.

It is invisible to both instruments because the item id (`P5-R4-ruling-path-for-undetermined`)
is not the branch slug (`r4-ruling-path`). Note also that this branch is stacked on
`r3-release-classifier-defaults` (its log contains all five R3 commits), so R3 and R4 are
one unlanded stack, not two independent ones.

**The shipped probe's sixth entry, `A13-sealed-audit-reads-the-wrong-fields`, is a false
positive — I disproved it:**

```
$ grep a13 monitor/ci/merge.log | grep MERGED
  2026-07-29T15:39:17Z MERGED origin/agent/a13-sealed-audit-reads-the-wrong-fields (dirs: arc-recon; …)
$ git cat-file -e origin/master:arc-recon/test_sealed_audit_negatives.py  → PRESENT
$ git cat-file -e origin/master:arc-recon/sealed.py                       → PRESENT
$ git cherry -v origin/master agent/a13-sealed-audit-reads-the-wrong-fields → (empty)
$ git log --oneline origin/master..agent/a13-…
  eac0897e Merge remote-tracking branch 'origin/master' into agent/a13-…
```

The work is on master. What survives is a **stale local branch** carrying one local merge
commit, which makes it non-ancestor and lands it in `unpushed_branches()`
(`monitor/mergequeue.py:142-172`). So `done_not_on_master()` overcounts by one for a
reason unrelated to the board.

**Honest statement: 6 done entries are provably unlanded** — E8-ic3-scale,
R3-release-classifier-defaults, S11-sealed-halfguard, V21-leakage-gate-token-level,
V5-battery-freeze, **P5-R4-ruling-path-for-undetermined**.

### R3 — "4 of these 5 stuck 17 hours with NEEDS-HUMAN" is false. It is 3 of 5.

`NEEDS-HUMAN since` timestamps from `monitor/ci/merge.log`, against now = 21:45:03Z:

| branch | NEEDS-HUMAN since | age | in `done/`? |
|---|---|---|---|
| e8-ic3-scale | 04:15:47Z | 17h29m | yes |
| s11-sealed-halfguard | 04:19:41Z | 17h25m | yes |
| v5-battery-freeze | 04:33:05Z | 17h12m | yes |
| r3-release-classifier-defaults | 18:32:53Z | **3h12m** | yes |
| v21-leakage-gate-token-level | 18:32:59Z | **3h12m** | yes |
| a3-campaign-devpile | 04:14:01Z | 17h31m | **no — `claimed/`** |
| r4-ruling-path | 19:02:54Z | 2h42m | yes (the missed sixth) |

Three of OPS-M's five are ~17h. The fourth 17-hour branch is `a3-campaign-devpile`, which
is in `monitor/board/claimed/A3-campaign-devpile.RES-1.md`, **not** in `done/` — so if
that is where the "4" came from, it is a set-boundary error: the flag set and the done set
were mixed. All five *do* currently carry a NEEDS-HUMAN flag, so the safe sentence is
"5 of 5 flagged NEEDS-HUMAN; the three oldest have been so for ~17 hours."

Also worth noting: R3 and V21 were marked done at 18:30:32Z and 18:18:29Z
(`monitor/board/board.log`) and were flagged at 18:32:53Z / 18:32:59Z — i.e. **the flags
are ~2 minutes younger than the done marks**. Calling those "stuck" at all overstates it;
they are the merge robot's normal first pass.

### R4 — Is the slug→branch mapping sound? Yes in kind, but it reads nothing authoritative, and OPS-M should say so.

**A done entry records no branch and no landing commit.** I read two in full
(`monitor/board/done/E8-ic3-scale.W-1660.md`, `monitor/board/done/V5-battery-freeze.W-252.md`):
they are the original item spec unchanged — front matter `priority/cell/territory/deps`
plus the Chinese task body. Nothing else. The code confirms it —
`monitor/board.py:372-379`:

```python
def cmd_done(iid, worker):
    src = os.path.join(CLAIMED, "%s.%s.md" % (iid, worker))
    if not os.path.exists(src):
        print("not claimed by you"); return 1
    os.rename(src, os.path.join(DONE, "%s.%s.md" % (iid, worker)))
    note("DONE %s by %s" % (iid, worker))
```

A rename and a log line. `cmd_done` does not even take a branch argument. So the mapping
is a **reconstruction of an unwritten naming convention**, not a read of a record.

That said, it is the fleet's own convention and two shipped call sites depend on it —
`monitor/board.py:271-308` `prior_work()` (`git branch -a --list *<slug>*`) and
`monitor/mergequeue.py:188-201` ("An item id maps to its branch by the fleet's own naming
rule"). So OPS-M is not inventing the join; it is using the same one the codebase uses.
It just must not describe it as authoritative.

**Coincidental matches: none found.** I content-checked all five, not just the ref graph:

```
ABSENT on origin/master: engine-rig/tests/test_ic3bounds_harness.py      (E8)
ABSENT on origin/master: release/tests/test_defaults_are_not_publishable.py (R3)
ABSENT on origin/master: arc-recon/local_engine_guard.py                 (S11)
ABSENT on origin/master: exam/tests/test_leakage_tokens.py               (V21)
ABSENT on origin/master: battery/freeze.py, battery/BATTERY_V1.md        (V5)
```

and `git cherry -v origin/master <branch>` marks **every** commit on all five with `+`,
i.e. no patch-equivalent landed by squash or cherry-pick. All five are genuinely absent
from the product. None of the five is a name collision.

**Collision risk: real in the directory, but exact matching defuses it.** `done/`
contains seven near-identical sibling pairs sharing an item-code prefix
(`S29-S29-third-condition-and-lock-ignore` vs `S29-S29-triage-the-five-red-gates`,
`P17-P17-bare-filename-citations` vs `P17-P17-machine-checked-ruling`,
`V21-leakage-gate-token-level` vs `V21-lp-unavailable-is-not-a-pass`,
`V5-battery-freeze` vs `V5-verdict-three-types`, plus S27/S30/P13/P4/P5 pairs). I checked
each: **exact** equality on the full slug resolves all of them correctly. OPS-M's
substring-free matching is the collision-safe choice here; `prior_work()`'s `*<slug>*`
substring form is the one that would misfire.

### R5 — OPS-M is *not* entitled to say the other 107/108 are "unmeasurable". That framing is worse than the claim it replaces.

`monitor/ci_merge.py:578-580` deletes the remote branch on a successful merge:

```python
sh(["git", "push", "origin", "HEAD:master"], cwd=wt)
...
sh(["git", "push", "origin", "--delete", branch.replace("origin/", "")])
```

So **absence of a remote branch is weak evidence *of* landing, not absence of evidence.**
OPS-M's "measurable" population is precisely the branches the robot failed to merge-and-
delete, plus a dozen that merged by some other route and kept their refs
(`monitor/ci_merge.py:263-266` documents that route). Quoting "5 of 14" as a rate is
therefore meaningless: the denominator is selected on the outcome.

Using `merge.log`'s 120 distinct `MERGED origin/...` lines as a second, independent
instrument, all 122 done entries resolve as:

| category | n |
|---|---|
| provably landed — surviving branch is an ancestor of origin/master | 11 |
| provably landed — a `MERGED` line names its branch | 89 |
| provably **unlanded** | **6** (incl. P5-R4) |
| genuinely undetermined | ~3 |

The residue I could not settle either way is small and named:
`E10-engine-crosscheck`, `E12-adopt-the-unsolvable-canon`, `P4-P16-e06-contradiction`
(no surviving branch, no `MERGED` line, no matching master commit found). Two more that
first looked undetermined do resolve: `S24-merge-conflict-drain` landed as merge commits
(`e26a1403 Merge origin/master into agent/a4a-ablation-build (S24 conflict drain)`), and
`S6-merge-gate-509.superseded-by-derived-gate.md` is self-labelled superseded, its
replacement being `86958a91 ci_merge: derive the gate from the tree`.

So: "at least 5 and 108 unmeasurable" would be a **false** escalation. The correct
sentence is "6 unlanded, ~3 undetermined, 113 positively landed."

### R6 — OPS-M measured an uncommitted board. Nobody else can reproduce its 122 or its 5.

```
$ ls monitor/board/done | wc -l                                   → 122
$ git ls-tree -r --name-only origin/master -- monitor/board/done | wc -l → 109
$ git ls-tree -r --name-only HEAD          -- monitor/board/done | wc -l → 109
```

13 done entries are untracked (`git status --porcelain -- monitor/board` shows them as
`??`), and **two of OPS-M's five are among them**:
`?? monitor/board/done/R3-release-classifier-defaults.RES-4.md` and
`?? monitor/board/done/V21-leakage-gate-token-level.RES-3.md`.
Local `HEAD` (3b0dd342) is also 29 commits behind `origin/master` (4252f4ff), though
OPS-M correctly compared against `origin/master`, not `HEAD`. A reader on another
checkout who pulls master sees 109 done entries and 4 unlanded, not 122 and 5. The
measurement needs that caveat or a commit.

### R7 — The reverse divergence exists but is almost entirely benign, and the one real case was already fixed.

I cross-matched all 12 `items/` and 4 `claimed/` ids against the `MERGED` set. Exactly one
open item has a merged branch: `items/S22-access-check-close.md` ↔
`MERGED origin/agent/s22-access-check-close` (02:40:24Z, 06:08:43Z). `monitor/board/board.log`
shows this is deliberate, not a defect — RES-4 released it three times, e.g.
`2026-07-29T06:08:52Z RELEASE S22-access-check-close by RES-4 (第(2)项已交付…；第(1)项要真实
API 调用，CHARTER 只允许 RES-1 花钱…)`. Half delivered and merged, half needs spend only
RES-1 may authorise. Correct behaviour.

The genuinely bad reverse case existed and is closed. `monitor/board/board.log`:

- `2026-07-29T18:00:34Z RECONCILE A13-… (stale claimed/ entry removed: done/ record exists
  … and the branch content is already on master -- the claim file was resurrected by a merge
  from a branch based before the DONE.)`
- `2026-07-29T18:21:23Z RECONCILE E8-ic3-scale removed items/E8-ic3-scale.md (already
  delivered by W-1660 at 2026-07-29T12:16:28Z; a merge from a branch based before that DONE
  put it back, and it was **re-claimed four times after**. done/ is authoritative. **Its
  delivery branch agent/e8-ic3-scale is unmerged for an unrelated ci_merge conflict -- that
  is a merge problem, not an unfinished item.**)`

That last sentence is the board's own log stating OPS-M's conclusion, about OPS-M's own
E8, 3h24m before OPS-M measured it. And the fix shipped: board item
`S4-S34-done-items-resurrect` was done at 19:00:38Z and `MERGED origin/agent/s34-done-items-resurrect`
at 19:05:28Z.

### R8 — Does it matter? Harmless is the stronger reading of the claim as written.

**Case for harmless (strong).** `monitor/ci/` holds exactly 7 `CONFLICT-*.md` flags, and
they are a **perfect 1:1 with the 7 non-ancestor `origin/agent/*` branches**
(a3-campaign-devpile, e8-ic3-scale, r3-release-classifier-defaults, r4-ruling-path,
s11-sealed-halfguard, v21-leakage-gate-token-level, v5-battery-freeze). `merge.log`
re-states each with a cause and an attempt count roughly every 10 minutes. `spec.py:671`
already rules that scoring must count master, not the board. `scan.py`'s `landed` cell
already renders the gap. `board.py:271-308` warns the next claimant about a branch that
exists. No information is lost and no reader who looks at `monitor/ci/` is misled. The
board and the merge queue are two machines by design (`CHARTER.md:28` — merging to master
is `ci_merge`'s job, not even the monitor's), and a state machine that ends at "delivered"
is not lying by not also knowing about a different machine.

**Case for it mattering (narrower, but the real one).** The flags are keyed by **branch**;
the board is keyed by **item**; the only thing joining them is an unwritten naming
convention. That join has already failed three times in ways with measurable cost:
(a) `P5-R4-ruling-path-for-undetermined` is unlanded and **invisible to every existing
probe** because its id ≠ its slug — the dashboard's `landed` cell under-reports it right
now; (b) `A13` is a false positive of the same join; (c) E8 was re-claimed **four times
after** it was done (`board.log`), and `board.py:275-277` records that S21 was done twice
and S27 three times for the same reason. Sessions are the currency being burned.

**Which is stronger on the evidence:** the harmless reading, for the claim *as OPS-M
states it*. "Done overstates completion" is documented, ruled on, instrumented, and
dashboarded; re-reporting it as a measurement is at best redundant and at worst
(given the wrong 5 and the wrong 17-hour pairing) a regression on an existing correct
number. The only part of this that is new is the **join**, not the gap: `cmd_done` takes
`(iid, worker)` and could take the delivery branch or commit, and if it recorded one,
P5-R4 would not be invisible, A13 would not be a false positive, and E8 would not have
been claimed five times.

---

## Where I could not refute OPS-M

- **The five branches are real and really absent from the product.** Content-level checks
  (files absent on `origin/master`) and `git cherry` (no patch-equivalents) both confirm
  it. No coincidence, no collision, no squash-merge explanation.
- **122 is right**, on disk.
- **The "done ≠ landed" semantics claim is true.** It is simply not news.

What *would* refute the remaining core: a `MERGED` line or a master commit containing any
of those five branches' distinctive files. I looked for both and found neither.

## Recommended rewrite of what OPS-M reports

> The board–master gap is already ruled on (`spec.py` F-20 action 2) and already measured
> by `mergequeue.done_not_on_master()`, delivered by board item S25 and rendered in
> `state["landed"]`. Re-running that probe rather than a hand-rolled slug match gives 6
> rows, of which **`A13-sealed-audit-reads-the-wrong-fields` is a false positive** (merged
> 15:39:17Z; only a stale local branch survives). The probe also **misses**
> `P5-R4-ruling-path-for-undetermined` → `origin/agent/r4-ruling-path` (8 commits,
> `release/tests/test_rulings.py` absent from master), because item id ≠ branch slug. True
> count: **6 unlanded done entries.** Five of the six carry a NEEDS-HUMAN flag; the three
> oldest (e8-ic3-scale, s11-sealed-halfguard, v5-battery-freeze) have carried one for
> ~17 hours, the other three for 2–3 hours. The 17-hour branch that is *not* in `done/` is
> `a3-campaign-devpile`, which is still `claimed/`.
>
> The reportable defect is not "done overstates completion" — that is documented. It is
> that **`board.py cmd_done` records no branch**, so the item↔branch join is a convention
> rather than a record; that is why R4 is invisible, why A13 is a false positive, and why
> E8 was re-claimed four times after delivery.
