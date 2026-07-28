# Board `crossing-up`

One of the boards this world is played on. Everything on this page is supplied by *this board*; nothing on it is a law of the world. Compare it with the other board in `levels/` to see which is which.

## The board

```
    0123456
  0 .......
  1 .....8.
  2 ...8...
  3 ...B...
  4 ....8..
  5 ...P.8.
  6 .......
```

`.` is a cell holding the background colour. A digit is the board's own colour at that cell — the board never changes it. A capital letter is the first letter of an object's name, drawn where that object starts; where two objects would share a cell the alphabetically earlier name is drawn. `*` marks a cell a landmark names, drawn only where nothing else is. Row 0 is the top row and column 0 the left column.

Size: 7 rows by 7 columns. Background colour: 0.

## Where things start

| object | type | cell | colour | present |
|---|---|---|---|---|
| `Box` | `Box` | (3, 3) | — | yes |
| `Player` | `Player` | (5, 3) | — | yes |

## What this board's landmarks name

| landmark | cell |
|---|---|
| `target` | (3, 3) |

## Something already true on this board

An object starts on a cell a landmark names. Depending on the manual's goal clause this board may already be won before any action is taken — check the clause; this page only reports the coincidence.

- `Box` starts on the cell `target` names.

## Goal cell

This board supplies no `goal_cell`. That does not mean the board has no goal — if the manual's goal clause names a landmark or writes a coordinate outright, the goal comes from there.

## Cells in play

This board's `LEVEL.json` carries an `arena` list of 49 cells. It is the board's own note of which cells are worth considering and **no rule of the manual consults it** — whether a cell can be stood on is decided by `free`, whose definition is in `manual/PRIMITIVES.md`. Treat `arena` as a convenience, not as law.
