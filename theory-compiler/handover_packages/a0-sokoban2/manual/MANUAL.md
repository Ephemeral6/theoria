# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Player**: characterized by pos (cell).
- **Box**: characterized by pos (cell).

These names each stand for a fixed set of values:

- **direction**: one of `up`, `down`, `left`, `right`.

These names appear in the rules and are **not** fixed by this description — each individual level says which cell each one is:

- **target**

## How a Turn Works

If no rule applies to something in a turn, it is exactly as it was.

At most one rule may apply to any one thing in any one turn; the rules are written so that this cannot fail.

One move produces one new situation. Every rule reads the situation as it was before the move, and all of their effects happen together.

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or slid (involving o, p, dir) or stayed (involving o).

## How Things Change

- **walk** (observed in all 262 cases) — for every ?d in direction: When the action is move(Player, ?d) and ahead(Player, ?d) is free (unoccupied), then Player moves ?d.
- **push2** — for every ?d in direction: When the action is move(Player, ?d) and the pos of Box is ahead(Player, ?d) and the cell box stands on is a legal empty one (on the board, not a wall, nothing but box there) and ahead(Box, ?d) is free (unoccupied) and beyond(Box, ?d) is free (unoccupied), then slid(Box, Player, ?d).
- **blocked wall** (observed in all 16 cases) — for every ?d in direction: When the action is move(Player, ?d) and it is **not** the case that ahead(Player, ?d) is free (unoccupied) and it is **not** the case that the pos of Box is ahead(Player, ?d), then stayed(Player).
- **blocked box on wall** — for every ?d in direction: When the action is move(Player, ?d) and the pos of Box is ahead(Player, ?d) and it is **not** the case that the cell box stands on is a legal empty one (on the board, not a wall, nothing but box there), then stayed(Player).
- **blocked box crossing** — for every ?d in direction: When the action is move(Player, ?d) and the pos of Box is ahead(Player, ?d) and the cell box stands on is a legal empty one (on the board, not a wall, nothing but box there) and it is **not** the case that ahead(Box, ?d) is free (unoccupied), then stayed(Player).
- **blocked box landing** — for every ?d in direction: When the action is move(Player, ?d) and the pos of Box is ahead(Player, ?d) and the cell box stands on is a legal empty one (on the board, not a wall, nothing but box there) and ahead(Box, ?d) is free (unoccupied) and it is **not** the case that beyond(Box, ?d) is free (unoccupied), then stayed(Player).

## Winning Condition

The puzzle is solved when: the pos of Box is target.

## Known Truths

### Preserved Quantities

- **box row parity**: The quantity (Box.pos.row) mod 2 always equals 1 (mathematically verified).
- **box col parity**: The quantity (Box.pos.col) mod 2 always equals 1 (mathematically verified).
- **box parity**: The quantity (Box.pos.row + Box.pos.col) mod 2 always equals 0 (mathematically verified).

### Derived Facts

- **unsolvable mismatch**: 箱子每次滑动两格，(row+col) 的奇偶不变；开局箱子在偶格，目标格是奇格，所以永远到不了 (verified by testing). This follows from: push2.

