# DRIFT-the-veto-that-held-a-branch-seventeen-times-evaporates-when-the-diff-goes-empty

severity: high
dimension: 7 (单向门 / 不可能变红的检查)
cycle: OPS-A 53
pin: `origin/master = d1da2c9c` @ 2026-07-30T14:18:36Z. `monitor/ci_merge.py` and
`monitor/tests/` citations verified on `disk` (the live tree is what the queue runs).

## claim

**`ci_merge.py`'s protected-root veto is computed from the branch's diff. When the diff goes
empty the veto stops firing — silently, with no log line, and with no test that could catch
it.** On 2026-07-30 this produced a `MERGED` line for a branch the veto had held **17 times**,
and the queue then deleted that branch's remote ref. It has happened twice in 174 merges.

**This report is about the mechanism, not about the branch.** The branch's own story
(the sealed-pile guard reaching master ungated) is already filed by OPS-M and is cited below
as context, not claimed as a discovery.

## evidence

### The mechanism

`monitor/ci_merge.py:460-463`:

```python
def touched_dirs(branch):
    base = sh(["git", "merge-base", "origin/master", branch]).stdout.strip()
    out  = sh(["git", "diff", "--name-only", base, branch]).stdout
    return {line.split("/")[0] for line in out.splitlines() if line.strip()}
```

If the branch has become an ancestor of master by any route, `merge-base` returns the branch
tip itself, the diff is empty, and `dirs == set()`. Three consequences follow in order:

1. `:502-506` — `bad_root` is derived from that same empty `dirs`, so the **protected-root
   veto cannot fire**. This is the gate that had refused this branch ~110 times.
2. `:519` — `git merge --no-ff` returns 0 ("Already up to date") and **creates no commit**.
3. `:525` — the gate loop iterates over the empty set, `ran == []`, and `:587` renders
   `gates: %s` as **`none`**.

Then `:575-580` pushes a no-op and runs `git push origin --delete <branch>`, and `:593` writes
a `MERGED` line. **An empty `dirs` is therefore not merely unlogged — it is rendered as a
successful, ungated merge, and it destroys a remote ref.**

### The trigger is a TOCTOU, and it is general

`monitor/ci_merge.py:652` computes `todo = starved_first(unmerged_branches())` **once**, before
`take_lock()` at `:661`. Each `try_merge` may then burn up to 1800 s per gate (`:543`). So the
ancestry check that produced `todo` can be consumed up to half an hour stale. Any branch that
lands out-of-band mid-tick gets this treatment.

The 2026-07-30 sequence, from `monitor/ci/merge.log` (`disk`), verbatim:

```
2026-07-30T04:56:35Z CLEARED flag for origin/agent/s11-sealed-halfguard (merged)
2026-07-30T04:56:35Z SWEEP-FLAGS retired 1 stale flag(s): origin/agent/s11-sealed-halfguard
2026-07-30T04:56:35Z BLOCKED: another merge holds the lock; merged nothing
2026-07-30T05:16:28Z MERGED origin/agent/s11-sealed-halfguard (dirs: ; gates: none)
```

The 04:56:35Z tick got it *right* — it saw the branch was already merged and retired the flag.
It then found the lock held. **An earlier tick, holding the lock with a pre-04:56 snapshot,
was still running and reached s11 twenty minutes later**, by which time its `todo` entry was
false. That tick wrote line 2073.

### The census — an empty `dirs` is a reliable phantom signature

Across the whole of `monitor/ci/merge.log`:

```
total MERGED lines                                            174
  MERGED with no `gates:` field at all (pre-S13 format)         23
  `gates: none`                                                 25
    ...naming an ungated territory (S13 working as designed)     10
    ...bare `gates: none`                                        15
        13 of those are 2026-07-28 11:12Z-15:13Z, pre-instrumentation
        the remaining 2 are exactly the 2 empty-`dirs` lines
empty `dirs: ;`                                                  2   -> lines 1834, 2073
```

```
1834: 2026-07-29T10:56:07Z MERGED origin/agent/s21-app-session-death  (dirs: ; gates: none)
2073: 2026-07-30T05:16:28Z MERGED origin/agent/s11-sealed-halfguard   (dirs: ; gates: none)
```

**So this is not systemic — it is 2 of 174 — and that is exactly why it is worth a report:**
the ten real ungated merges all *name* their territory (`NO GATE, MERGED UNCHECKED: papers`),
which is the S13 instrumentation working. The two phantoms are indistinguishable from success
in the log, and any throughput metric counting `MERGED` lines is inflated by two.

`s21` is the same shape and is *self-documented* in `monitor/ci_merge.py:130-133`: it was
flagged `push rejected (race?)` when the push had in fact landed, then "merged on the first
retry with nothing about it changed."

### There is no negative sample

Searched `monitor/tests/test_gate_negative_sample.py`, `test_gate_outcomes.py` (21 tests),
`test_gate_enforcement.py`, `test_merge_queue.py` (15 tests), `test_stale_flag_sweep.py` for
`touched_dirs|dirs: ;|Already up to date|is-ancestor|unmerged_branches`:

* **no test calls `touched_dirs` at all**;
* **no test drives `try_merge` with a branch already ancestral to master**;
* `test_gate_enforcement.py:53` asserts the *positive* rendering only.

And `monitor/tests/test_stale_flag_sweep.py:1-8` states the violated assumption verbatim:

> `unmerged_branches` drops anything already in master

True at snapshot time. False twenty minutes later. **The assumption is written down, believed
by the tests, and unenforced at the only moment it matters.**

## the context this occurred in (prior art — NOT claimed as new)

The branch in question is not arbitrary. `cd048b32` (2026-07-30T04:53:48Z), a **hand** merge,
landed 795 lines of `arc-recon/local_engine_guard.py` — the whitelist `CLAUDE.md:152-169`
designates as the only instrument that can detect a locally-cached sealed game — plus
`arc-recon/verify.sh` (+10), `ACCESS_CHECK.md` (+125), a 532-line test file and `CLAUDE.md`
(+37), **with `verify:arc-recon` never executed** (it last ran at 04:38:27Z on a different
branch, and appears nowhere in `merge.log` afterwards).

**This is already filed**, three minutes before `merge.log:2073` even existed:
`monitor/inbox/20260730T051344Z-opsm-URGENT-the-sealed-guard-bypass-is-live-on-master-and-my-own-ruling-named-it-wrong.md`,
which additionally reports an end-to-end **measured** live bypass of the guard.
`git log -- arc-recon/local_engine_guard.py` shows **no commit since `803a853a`** — unfixed
roughly ten hours later, and the URGENT itself is recorded as unanswered.

Two things I want on the record so this report is not read as an accusation:

* Sealed ids in that branch's added lines are **8 hits across 2 ids, all inside the guard's own
  test file** — the expected negative-sample shape. **Class (b) real contact: zero.** I matched
  strings and printed `path:line:id` only; no sealed-game content was read.
* By `monitor/CHARTER.md` the human principal is the **sole authority** that `NEEDS-HUMAN`
  escalates *to*. A human overriding a 17-attempt hold is the escalation working as designed.
  **The defect is that the override path runs no gate — not that someone used it.**

## suggest (monitor rules; I changed nothing — `monitor/*.py` is outside my territory)

1. **One guard at `try_merge` entry:** `if not dirs: log("SKIP-ALREADY-MERGED", branch); return False`.
   This converts a phantom success into an honest skip and stops the remote-ref deletion.
2. **Re-check ancestry after taking the lock**, not before. Move the `unmerged_branches()`
   filter (or a per-branch re-test) to inside the lock at `monitor/ci_merge.py:661`, so a
   snapshot cannot be consumed 30 minutes stale.
3. **Give the protected-root veto its own negative sample**, and make it independent of `dirs`.
   A veto derived from a set that can go empty is a gate that cannot go red — the exact shape
   `AUDITOR.md` dimension 7 exists for. Minimum test: a branch already ancestral to master,
   touching a protected root, must **not** produce a `MERGED` line.
4. **Decide what a `MERGED` line means** and make the log say it. Today it conflates "gated and
   landed", "landed ungated, territory named", and "merged nothing". Only the first two are
   distinguishable by eye.

## what I could not prove

* Whether the two phantom branch deletions cost anything. Both branches' content was already on
  master, so I have no evidence of lost work — but the queue could not have known that when it
  deleted them, since it derived "already merged" from the same empty diff.
* Whether any *other* `MERGED` line is a phantom under a different signature. I tested the
  empty-`dirs` signature only; a branch whose diff is non-empty but whose gates all no-op would
  not be caught by it.
* The guard's own reported bypass. I did not reproduce it and deliberately did not read the
  guard or its tests — reproducing a sealed-pile bypass is not something an auditor should do
  to check someone else's homework. It is cited as OPS-M's finding, on OPS-M's evidence.
