# The words the rules are built from

These are the primitives the manual's rules use. The manual does not restate them; they are fixed by the language the manual is written in, and they mean the same thing in every manual.

A **cell** is written `(row, col)`. Row 0 is the top row and column 0 the left column. A **direction** moves one cell: `up` subtracts one from the row, `down` adds one, `left` subtracts one from the column, `right` adds one.

## Functions and predicates

- **`above(X)`** — the cell one step up from `X`'s cell.
- **`below(X)`** — the cell one step down from `X`'s cell.
- **`colored(c, k)`** — the colour showing at cell `c` — the board's colour there, or the colour of whatever object is standing on it — is exactly `k`.
- **`count(T)  /  count(T, k)`** — how many objects of type `T` are present; with a second argument, how many of them have colour `k`.
- **`free(c)`** — the cell `c` is on the board, the board's own colour there is the background colour, and no object is standing on it. Written `free(X.pos)` — asking whether an object's *own* cell is a legal empty one — it excludes that object from the test and asks about the board and every *other* object.
- **`leftof(X)`** — the cell one step left from `X`'s cell.
- **`rightof(X)`** — the cell one step right from `X`'s cell.

## What each event does

The manual's `events:` section declares the names below and their arguments. What each one *does* is fixed by the language, the same in every manual, and is stated here because it is stated nowhere in the manual.

- `moved(o, d)` — object `o` moves **one** cell in direction `d`. Nothing else changes.
- `jumped(o, dest)` — object `o` is placed on the cell the landmark `dest` names. It does not travel through the cells in between; where that cell is, is supplied by the level.
- `recolored(o, k)` — object `o`'s colour becomes `k`. It does not move.
- `vanished(o)` — object `o` stops being present. It is no longer drawn and no longer occupies its cell.

## Sentence shape

- `act=<action>` — the guard clause that matches the action being taken. A rule whose guard does not name the action applies whatever the action is.
- `not <clause>` — the clause does not hold.
- `<a> and <b>` — both hold. A guard is a conjunction and nothing else; "either of two things is blocked" is written as two rules, not as one guard.
- `X.pos` — the cell object `X` is standing on.
- `X.pos.row` / `X.pos.col` — the row and the column of that cell. Row 0 is the top row, column 0 the left column.
- `forall ?v in <domain>` — the rule is a schema: one rule per member of the named domain, with `?v` replaced throughout.
- `mod` — remainder after division, never negative.
