# The words the rules are built from

These are the primitives the manual's rules use. The manual does not restate them; they are fixed by the language the manual is written in, and they mean the same thing in every manual.

A **cell** is written `(row, col)`. Row 0 is the top row and column 0 the left column. A **direction** moves one cell: `up` subtracts one from the row, `down` adds one, `left` subtracts one from the column, `right` adds one.

## Functions and predicates

- **`ahead(X, d)`** — the cell one step from `X`'s cell in direction `d`.
- **`beyond(X, d)`** — the cell two steps from `X`'s cell in direction `d`.
- **`free(c)`** — the cell `c` is on the board, the board's own colour there is the background colour, and no object is standing on it. Written `free(X.pos)` — asking whether an object's *own* cell is a legal empty one — it excludes that object from the test and asks about the board and every *other* object.

## What each event does

The manual's `events:` section declares the names below and their arguments. What each one *does* is fixed by the language, the same in every manual, and is stated here because it is stated nowhere in the manual.

- `moved(o, d)` — object `o` moves **one** cell in direction `d`. Nothing else changes.
- `slid(o, p, d)` — object `o` travels **two** cells in direction `d`, and object `p` (the one doing the pushing) advances **one** cell in `d`, onto the cell `o` has just left. Both motions are one event and happen together.
- `stayed(o)` — nothing moves and nothing changes. The situation after the action is identical to the situation before it.

## Sentence shape

- `act=<action>` — the guard clause that matches the action being taken. A rule whose guard does not name the action applies whatever the action is.
- `not <clause>` — the clause does not hold.
- `<a> and <b>` — both hold. A guard is a conjunction and nothing else; "either of two things is blocked" is written as two rules, not as one guard.
- `X.pos` — the cell object `X` is standing on.
- `X.pos.row` / `X.pos.col` — the row and the column of that cell. Row 0 is the top row, column 0 the left column.
- `forall ?v in <domain>` — the rule is a schema: one rule per member of the named domain, with `?v` replaced throughout.
- `mod` — remainder after division, never negative.
