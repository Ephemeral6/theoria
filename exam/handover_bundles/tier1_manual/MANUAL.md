# The manual for this world

A deterministic rendering of the manual's source file (`MANUAL.dsl` in this bundle). It adds nothing; where it says more than the source, it is reading the source's compiled form and says so.

## What there is

- A **board**: a rectangular grid of cells that does not change while the game is played.
- A **Player**, which has one property: pos: Cell.
- A **Box**, which has one property: pos: Cell.

## What can happen

Three kinds of change, and no others: something **moved** one cell, something **slid** (further than one cell), or something **stayed** where it was.

## How things change

**walk**

When the Player is told to move in direction d, and
  - the cell one step from the Player in direction d is free,

then the Player moves one cell in direction d. Nothing else changes.

**push2**

When the Player is told to move in direction d, and
  - the Box is standing on the cell one step from the Player in direction d,
  - the cell one step from the Box in direction d -- the cell the Box would cross -- is free,
  - the cell two steps from the Box in direction d -- the cell the Box would land on -- is free,

then the Box slides two cells in direction d, and the Player advances one cell -- onto the cell the Box has just left.

**blocked_wall**

When the Player is told to move in direction d, and
  - the cell one step from the Player in direction d is NOT free,
  - the Box is NOT standing on the cell one step from the Player in direction d,

then nothing moves. The situation after the action is identical to the situation before it.

**blocked_box_crossing**

When the Player is told to move in direction d, and
  - the Box is standing on the cell one step from the Player in direction d,
  - the cell one step from the Box in direction d -- the cell the Box would cross -- is NOT free,

then nothing moves. The situation after the action is identical to the situation before it.

**blocked_box_landing**

When the Player is told to move in direction d, and
  - the Box is standing on the cell one step from the Player in direction d,
  - the cell one step from the Box in direction d -- the cell the Box would cross -- is free,
  - the cell two steps from the Box in direction d -- the cell the Box would land on -- is NOT free,

then nothing moves. The situation after the action is identical to the situation before it.

Exactly one of these rules applies to any situation and any action, so there is never a question of which one to use.

## When the game is won

- The game is won when the Box is standing on the target cell.

## What is always true

- **box_row_parity** (proven): `(Box.pos.row) mod 2 = 1` holds before the first action and after every action, whatever actions are taken.
- **box_col_parity** (proven): `(Box.pos.col) mod 2 = 1` holds before the first action and after every action, whatever actions are taken.
- **box_parity** (proven): `(Box.pos.row + Box.pos.col) mod 2 = 0` holds before the first action and after every action, whatever actions are taken.
- **unsolvable_mismatch**: 箱子每次滑动两格，(row+col) 的奇偶不变；开局箱子在偶格，目标格是奇格，所以永远到不了

## The words the rules are built from

These are the primitives the rules above use. They are not restated in the
manual's source; they are read off the manual's compiled executable form, which
is one of the forms the manual compiles to.

- A **cell** is written `(row, col)`. Row 0 is the top row and column 0 the
  left column.
- A **direction** `d` is one of UP, DOWN, LEFT, RIGHT. UP subtracts one from
  the row, DOWN adds one to the row, LEFT subtracts one from the column,
  RIGHT adds one to the column.
- **one step from X in direction d** is X's cell moved once by d;
  **two steps from X in direction d** is X's cell moved twice by d.
- A cell is **free** when all three of these hold: it is on the board, it is
  not a wall, and the Box is not standing on it. The Player never makes a cell
  un-free: the Player does not block anything, including itself.
- An action is always a move by the Player in one direction. There is no other
  kind of action.
