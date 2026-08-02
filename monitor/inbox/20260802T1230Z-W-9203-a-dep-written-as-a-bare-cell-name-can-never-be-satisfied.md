# W-9203 → monitor: `deps: A23` can never be satisfied, and A22 is already stuck on it

**From:** W-9203 · **UTC:** 2026-08-02T12:30Z
**Found:** while wrapping up on `BOARD-EMPTY`, checking why anything was left blocked
**Nothing is requested.** The fix is one line in a board item, but board items are
`monitor/`'s and I do not write there.

## The finding

`board.py` resolves a dependency by asking whether the dep string is in
`done_ids()`, and `done_ids()` holds **full item ids** — the slug, not the cell
name. Two items on the board write their `deps` as a bare cell name:

```
monitor/board/items/A22-r3-generated-frontier-round.md        deps: A23
monitor/board/items/A26-frontier-width-and-probe-yield-...md  deps: A24
```

Measured just now:

```
'A23-anchor-drift-on-the-default-leg' in done_ids()  ->  True
'A23'                                 in done_ids()  ->  False
```

So **A22 is permanently unclaimable.** A23 was delivered by W-9202 and is in
`done/`; A22 still prints `waits on A23` and always will. `board.py list` shows
it under `blocked`, which reads like "not yet", not like "never".

**A26 is the same bug one step behind.** Its `deps: A24` is currently reported as
`pending` only because `A24-round-scoreboard-columns-are-null` is still in
flight with W-9202. The moment that lands, A26 stops being pending and becomes
permanently blocked, exactly like A22 — and it will look like it is merely
waiting.

## Why this is worth a note rather than a shrug

`board.py:154-156` already carries the comment for this exact failure class:

> 一个空的 `deps:` 借来下一行，变成一个**永远不可能被满足**的依赖，条目从此
> 不可领，而板上给出的解释（`waits on lane: infra`）指着一件不存在的事。

That comment was written about an empty `deps:` swallowing the next line. This is
the same outcome by a different route — a dep that is *well-formed and readable*
and simply does not name an id. The board's own explanation points at something
real (A23 exists, A23 is done), which makes it harder to spot than the case
already guarded against, not easier.

It also costs asymmetrically: a claimant never sees these items, so nobody is
ever confronted with the contradiction. The board looks busy and the work is
invisible. `BOARD-EMPTY` for a generic worker today is partly this.

## Two fixes, and I have a preference

1. **Rewrite the two `deps:` lines to full ids** (`deps: A23-anchor-drift-on-the-default-leg`).
   Correct, one line each, and leaves the trap set for the next author who
   writes a cell name — which is the natural thing to write, since every item's
   own `cell:` field *is* the bare name.
2. **Resolve a dep by cell name as well as by id**, i.e. treat `A23` as satisfied
   when some done id is `A23` or starts with `A23-`. Then both spellings work
   and the item files need no edit.

I would do **both**, and I would add the negative control the board deserves
more than the fix: **a check that every `deps:` entry names something that
exists** — an item id present in `items/`, `claimed/` or `done/`. A dep naming
nothing at all is today indistinguishable from a dep naming something unfinished,
and that is the property that let this sit. `unreachable_ids()` already computes
a related notion for lanes; this is its sibling for deps.

Whichever way it goes, A22 has a **second, independent** block that this does not
touch: its own text says the live half must not start while the programme is over
its ceiling (~$285 spent against $214.90, owner has not ruled). Unblocking the
dependency makes its offline half reachable; it does not authorise spending.

## What I checked, so it is not taken on trust

```
item                                       deps   satisfiable?
A22-r3-generated-frontier-round            A23    NEVER (done as A23-anchor-drift-on-the-default-leg)
A26-frontier-width-and-probe-yield-...     A24    pending -> will become NEVER when A24 lands
```

Every other item on the board carries `deps: none`. Blast radius is exactly these
two.
