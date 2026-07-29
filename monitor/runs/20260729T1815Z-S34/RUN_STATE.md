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
