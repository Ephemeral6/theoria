# S34 — finished work came back onto the board, and got done again

RES-4, 2026-07-29, branch `agent/s34-done-items-resurrect`, base `1c181b90`.
Offline: zero API calls, $0.00, zero sealed-pile contact.

## What was wrong

Board state is a set of **tracked files**, and all three of `board.py`'s verbs
are `os.rename`. Nothing in the module is wrong on its own. What is wrong is the
interaction with git, and no line of `board.py` can see it:

1. `done` renames `claimed/<id>.<worker>.md` into `done/`.
2. A merge from a branch whose base predates that rename restores
   `items/<id>.md`. Git compares trees. It sees *"a file the other side has and
   I do not"*; it has no rule that relates that file to a different file in a
   different directory, so it cannot see *"this work is finished"*.
3. `candidates()` hands the item out again.

Step 3 is the part that was fixable and was not fixed. `done_ids()` had existed
in this module the whole time — used for exactly one thing, resolving *other*
items' `deps`. The same set, three lines above the loop, was never asked about
the item in front of it.

## Measured, on the live board

| item | delivered | what happened next |
|---|---|---|
| `E8-ic3-scale` | W-1660, 12:16:28Z | re-claimed **four** times (W-1671 15:08:20Z, an accidental `--help` 15:54:30Z, W-130 15:59:18Z), swept back to the shelf after each. Found sitting in **`items/` + `claimed/` + `done/` at once.** |
| `A13-sealed-audit-reads-the-wrong-fields` | RES-4, 15:40:32Z | found in `claimed/` + `done/` at once. Its branch content was already on master, so the item genuinely was finished. |

Nothing errored. Nothing warned. `board.py list` showed E8 as ordinary
available work, and every one of those workers spent a session launch and a
fresh context to redo something already sitting on a branch. This is the lane's
standing shape: **it fails in the reassuring direction — the log looks busy.**

E8's own delivery branch `agent/e8-ic3-scale` is unmerged, for an unrelated
`ci_merge` conflict parked in `monitor/ci/`. That is a merge problem, not an
unfinished item, and conflating the two is how the resurrection kept looking
plausible to each new claimant.

## The fix, in four places

* **`delivered_map()` / `resurrected()`** — `resurrected()` returns every id
  that is in `done/` *and* on the shelf or under claim, with who delivered it
  and where the residue is.
* **`candidates()`** — a hard skip for any id already in `done_ids()`.
* **`cmd_sweep`** — refuses to move a delivered id from `claimed/` back to
  `items/`. This is the second and more damaging route, because it looks like
  housekeeping: E8 was swept back to the shelf three separate times *after*
  delivery, and each sweep was indistinguishable from the honest ones beside it.
* **`cmd_reconcile(fix=False)`** — reports by default, and with `--fix` deletes
  the `items/` and `claimed/` residue, logging a `RECONCILE` line per removal.
  **`done/` is authoritative**, and that is not a preference: treating the shelf
  as authoritative would re-open finished work, while treating `done/` as
  authoritative can at worst discard a claim on work that is already delivered.
  Report-only by default, because a board-repair tool that mutates by default is
  one nobody runs on a board they care about, and this one has to be runnable
  after every merge.

**A silent skip would only be half a fix.** The board would then quietly hide
finished items instead of quietly offering them, and nobody would learn that a
merge did it. So `cmd_list` prints a `RESURRECTED` section — placed *before* the
117-line done list, which is the part a reader has to not scroll past — and
`cmd_claim` prints it on the `BOARD-EMPTY` path too. A worker told "no work"
while three finished items sit on the shelf is being lied to in the reassuring
direction, and it is the one party with a reason to say so.

## Why the gate check has to be post-merge

`monitor/verify.py` gains a stage, **`board states disjoint`**: no id may be in
`done/` and also on the shelf or under claim.

It cannot live only in `board.py`. **No verb in `board.py` runs during a merge**
— the merge is precisely the moment the invariant breaks, and it breaks without
any of this code executing. So something has to look at the *result*. That is
the whole argument for putting it in the gate rather than in the tool, and it
generalises: any invariant over a directory of tracked files needs a check that
runs after git touches them, not only inside the program that normally writes
them.

The stage went **red on the live board on its first run**, which is how the
second case (A13) was found.

## The live board was reconciled by hand

`items/E8-ic3-scale.md` and `claimed/E8-ic3-scale.W-1671.md` were removed and
both removals logged as `RECONCILE` in `board.log`; the same was done earlier
for `A13`'s stale claim. By hand, because `reconcile --fix` only exists on this
branch and the live board runs master's `board.py`.

That is a deliberate departure from how R3 and S29 were handled on this shift,
where the correct fix turned a gate red and the red was left standing as the
deliverable. The difference is that those reds mark work a human still has to
rule on, and this one marks residue with a one-command fix and no judgement in
it. Leaving `monitor`'s gate red over it would have blocked every territory's
merges to make a point that a `board.log` line makes better.

---

## Correction: the merge that resurrects is not the one I described

Everything above says the resurrection comes from *"a merge from a branch whose
base predates the `done`."* That is **wrong**, and it was found by writing the
fixture rather than by reasoning about it. Six merge shapes were probed in
throwaway repositories:

* **The story above does not reproduce.** Item on the shelf at the merge base →
  branch off → master does `claim` → `done` → merge the branch back. Git keeps
  the item deleted: delete-on-one-side beats unmodified-on-the-other. And if the
  branch *edits* the item file, rename detection carries the edit onto
  `done/<id>.<worker>.md` instead. This is pinned as
  `test_the_naive_merge_story_does_not_reproduce_it`, so that nobody later
  "simplifies" the fixture into something that reproduces nothing.
* **What does reproduce: the merge base predates the item's *creation*.** Then
  master's net change against the base is an *add* in `done/`, and the branch's
  is an *add* in `items/`. Two adds, no delete — git merges both without a
  murmur and without a conflict. That is the literal *"a file the other side has
  and I do not"*, and it is the centrepiece fixture.
* **A second route, which conflicts loudly and then resolves quietly:** the
  branch ran `sweep` or `release` while master ran `done`. That is a
  rename/rename conflict, and git leaves **both** paths in the working tree — so
  any "resolve by keeping both" resolution commits the resurrection.

The distinction matters operationally: the dangerous branches are the **old**
ones, cut before the item existed at all, not the ones cut before it finished.
This fleet keeps 130+ worktrees, many of them weeks of commits behind, so that is
the common case rather than the exotic one.

## A defect in this fix, found by the tests written for it

`resurrected()` built its claim side from `claimed_map()`, which is a dict keyed
on the id — so when one id carries **two** claim files it kept only whichever
`os.listdir` returned last. `reconcile --fix` then removed one, printed
「清掉 1 个残留」and returned **0**, with the second claim still sitting there.

A repair tool whose exit code says *clean* over residue it left is this lane's
own disease, and a CI gate would have believed it. Two claims on one id is not
the rare case either: it is a *more* resurrected board, because every
resurrection is another chance for somebody to claim. `claimed_by` is now a list
and `--fix` removes all of them. The adversary had filed it as a strict `xfail`;
the marker is gone and the test passes.

## Tests

`python -m pytest monitor/tests` → **248 passed, 2 xfailed**, from 220 passed / 2
xfailed before. 29 new tests in `test_done_items_resurrect.py`.

Each guard was removed from a restored copy of `board.py` and the suite re-run:

| guard removed | failures |
|---|---|
| `candidates()` `if iid in ready: continue` | **5** |
| `cmd_sweep()` delivered-`kept` branch | **3** |
| `_warn_resurrected()` in `cmd_list` | **1** |
| `_warn_resurrected()` in `cmd_claim` | **1** |

Beyond the four the work order named, the suite pins: that `done_ids()`'s
original job still works (an item whose `deps` name a delivered id stays
unblocked, and an unmet dep still blocks); that both roles of `done_ids()`
coexist in one run; that ids sharing a prefix do not collide in **either**
direction (`S4-freeze` delivered must not suppress `S4-freeze-complete`, and
vice versa — they do not, because `done_ids()` splits on `.` and gets the whole
id); that `P13-P13-figure-numbering-and-plates` round-trips; and that the whole
`RESURRECTED` + `reconcile` output is encodable in cp936, which is the trap
`prior_work` fell into once on this platform.

## One thing this branch does that is board *data*, not code

`monitor/board/items/E8-ic3-scale.md` and
`monitor/board/claimed/E8-ic3-scale.W-1671.md` are deleted here, by running
`board.py reconcile --fix` in this worktree, with both removals logged as
`RECONCILE` in `board.log`. Without it this branch's own gate is red, because
the invariant it adds is violated by the board data sitting in the same tracked
tree. A branch that ships a check and not the repair the check demands is a
branch that hands the next person a red gate and no explanation.

The same reconciliation was done by hand in the live checkout earlier, since
`reconcile` only exists on this branch.
