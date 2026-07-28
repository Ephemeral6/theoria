# Board `match`

One of the boards this world is played on. Everything on this page is supplied by *this board*; nothing on it is a law of the world. Compare it with the other board in `levels/` to see which is which.

## The board

```
    0123456
  0 .......
  1 .....8.
  2 .......
  3 .*.B.P.
  4 ....8..
  5 .....8.
  6 .......
```

`.` is a cell holding the background colour. A digit is the board's own colour at that cell — the board never changes it. A capital letter is the first letter of an object's name, drawn where that object starts; where two objects would share a cell the alphabetically earlier name is drawn. `*` marks a cell a landmark names, drawn only where nothing else is. Row 0 is the top row and column 0 the left column.

Size: 7 rows by 7 columns. Background colour: 0.

## Where things start

| object | type | cell | colour | present |
|---|---|---|---|---|
| `Box` | `Box` | (3, 3) | — | yes |
| `Player` | `Player` | (3, 5) | — | yes |

## What this board's landmarks name

| landmark | cell |
|---|---|
| `target` | (3, 1) |

## Cells in play

49 cells are listed in this board's arena.
