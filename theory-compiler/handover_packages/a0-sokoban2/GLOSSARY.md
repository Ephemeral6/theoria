# Glossary — every name in this package, and where it comes from

Names in this world come from exactly three places. A name the **manual** fixes is the same on every board. A name a **board** supplies changes from board to board. A **primitive** belongs to the language the manual is written in and means the same in every manual of every world.

The tables below are computed from the files in this package.

## Fixed by the world (from `manual/MANUAL.dsl`)

| name | kind | what it is |
|---|---|---|
| `Player` | object type | a kind of thing the world contains; its observed properties are `pos` |
| `Player.pos` | property | an observation of type `Cell` carried by every `Player` |
| `Box` | object type | a kind of thing the world contains; its observed properties are `pos` |
| `Box.pos` | property | an observation of type `Cell` carried by every `Box` |
| `direction` | domain | a fixed finite set of values: `up`, `down`, `left`, `right` |
| `target` | landmark name | the world names it; **each board says which cell it is** — see the level-data table |
| `frame persist` | semantics | what happens to an object no firing rule mentions |
| `conflict exclusive` | semantics | how many rules may claim one object in one transition |
| `cascade single_frame` | semantics | whether one action produces one frame or several |
| `moved(o, dir)` | event | a kind of change the world can undergo |
| `slid(o, p, dir)` | event | a kind of change the world can undergo; it writes `o`, `p` |
| `stayed(o)` | event | a kind of change the world can undergo; it writes nothing |
| `walk` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `push2` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `blocked_wall` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `blocked_box_on_wall` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `blocked_box_crossing` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `blocked_box_landing` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `box_row_parity` | invariant | something the manual says is true before the first action and after every action |
| `box_col_parity` | invariant | something the manual says is true before the first action and after every action |
| `box_parity` | invariant | something the manual says is true before the first action and after every action |
| `unsolvable_mismatch` | theorem | a consequence the manual states and cites its evidence for |
| the goal clause | goal | what winning is; the *shape* is fixed by the world, and any coordinate written into it is not — see the last section |

## Supplied by each board (from `levels/*/LEVEL.json`)

Every row here is a name whose value this package can *show* you changing — or not — because the package carries more than one board. A row marked **differs** is level data on the evidence in this package. A row marked *same here* is level data by where it lives (a board supplies it) even though these particular boards happen to agree; two boards agreeing is not a law.

| name | `match` | `crossing-up` | verdict |
|---|---|---|---|
| `Box start cell` | (3, 3) | (3, 3) | *same here* |
| `Player start cell` | (3, 5) | (5, 3) | **differs** |
| `arena` | 49 cells | 49 cells | *same here* |
| `background_colour` | 0 | 0 | *same here* |
| `board_shape` | 7 x 7 | 7 x 7 | *same here* |
| `goal_cell` | — | — | *same here* |
| `landmark target` | (3, 1) | (3, 3) | **differs** |
| `non_background_cells` | 3 | 4 | **differs** |

## Names the manual uses that only a board can resolve

These names appear in the manual's own clauses, and the manual does not say what they are: each board does. They are the seam between the world and the board, and the value column shows the seam.

| name | declared in the manual as a landmark? | `match` | `crossing-up` |
|---|---|---|---|
| `target` | yes | (3, 1) | (3, 3) |

## Fixed by the language (see `manual/PRIMITIVES.md`)

| name | meaning |
|---|---|
| `ahead(X, d)` | the cell one step from `X`'s cell in direction `d`. |
| `beyond(X, d)` | the cell two steps from `X`'s cell in direction `d`. |
| `free(c)` | the cell `c` is on the board, the board's own colour there is the background colour, and no object is standing on it. Written `free(X.pos)` — asking whether an object's *own* cell is a legal empty one — it excludes that object from the test and asks about the board and every *other* object. |

## Numbers written into the manual

These clauses of the manual contain a number. A law is a fact about the world; a number it is compared against is very often a fact about one board that has been written into the manual by accident. This package does not repair them — it points at them, because on a board where the number is different the manual's sentence is false as written.

| section | clause |
|---|---|
| `invariant` | `invariant box_row_parity (Box.pos.row) mod 2 = 1 [status: proven]` |
| `invariant` | `invariant box_col_parity (Box.pos.col) mod 2 = 1 [status: proven]` |
| `invariant` | `invariant box_parity (Box.pos.row + Box.pos.col) mod 2 = 0 [status: proven]` |
