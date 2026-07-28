# Board `no-button`

One of the boards this world is played on. Everything on this page is supplied by *this board*; nothing on it is a law of the world. Compare it with the other board in `levels/` to see which is which.

## The board

```
    012345678
  0 111111111
  1 1*...1..1
  2 1....1..1
  3 1....1..1
  4 1....5..1
  5 1C...1..1
  6 1...11..1
  7 111311..1
  8 111111111
```

`.` is a cell holding the background colour. A digit is the board's own colour at that cell — the board never changes it. A capital letter is the first letter of an object's name, drawn where that object starts; where two objects would share a cell the alphabetically earlier name is drawn. `*` marks a cell a landmark names, drawn only where nothing else is. Row 0 is the top row and column 0 the left column.

Size: 9 rows by 9 columns. Background colour: 0.

## Where things start

| object | type | cell | colour | present |
|---|---|---|---|---|
| `Cart` | `Cart` | (5, 1) | 6 | yes |

## What this board's landmarks name

| landmark | cell |
|---|---|
| `portal_exit` | (1, 1) |

## Cells in play

37 cells are listed in this board's arena.
