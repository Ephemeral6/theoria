# Glossary — every name in this package, and where it comes from

Names in this world come from exactly three places. A name the **manual** fixes is the same on every board. A name a **board** supplies changes from board to board. A **primitive** belongs to the language the manual is written in and means the same in every manual of every world.

The tables below are computed from the files in this package.

## Fixed by the world (from `manual/MANUAL.dsl`)

| name | kind | what it is |
|---|---|---|
| `Cart` | object type | a kind of thing the world contains; its observed properties are `pos`, `color` |
| `Cart.pos` | property | an observation of type `Coord` carried by every `Cart` |
| `Cart.color` | property | an observation of type `Int` carried by every `Cart` |
| `Button` | object type | a kind of thing the world contains; its observed properties are `pos`, `color` |
| `Button.pos` | property | an observation of type `Coord` carried by every `Button` |
| `Button.color` | property | an observation of type `Int` carried by every `Button` |
| `Door` | object type | a kind of thing the world contains; its observed properties are `pos`, `color`, `present` |
| `Door.pos` | property | an observation of type `Coord` carried by every `Door` |
| `Door.color` | property | an observation of type `Int` carried by every `Door` |
| `Door.present` | property | an observation of type `Bool` carried by every `Door` |
| `frame persist` | semantics | what happens to an object no firing rule mentions |
| `conflict exclusive` | semantics | how many rules may claim one object in one transition |
| `cascade single_frame` | semantics | whether one action produces one frame or several |
| `moved(o, dir)` | event | a kind of change the world can undergo |
| `jumped(o, dest)` | event | a kind of change the world can undergo |
| `recolored(o, c)` | event | a kind of change the world can undergo |
| `vanished(o)` | event | a kind of change the world can undergo |
| `push_up` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `push_down` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `push_left` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `push_right` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `teleport_down` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `press_left` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `door_opens_left` | rule | one sentence of the form *when … then …*; see `manual/MANUAL.md` |
| `cart_unique` | invariant | something the manual says is true before the first action and after every action |
| `door_latch` | invariant | something the manual says is true before the first action and after every action |
| `press_is_direction_free` | theorem | a consequence the manual states and cites its evidence for |
| the goal clause | goal | what winning is; the *shape* is fixed by the world, and any coordinate written into it is not — see the last section |

## Supplied by each board (from `levels/*/LEVEL.json`)

Every row here is a name whose value this package can *show* you changing — or not — because the package carries more than one board. A row marked **differs** is level data on the evidence in this package. A row marked *same here* is level data by where it lives (a board supplies it) even though these particular boards happen to agree; two boards agreeing is not a law.

| name | `base` | `no-button` | verdict |
|---|---|---|---|
| `Button colour` | 7 | — | **differs** |
| `Button start cell` | (3, 2) | — | **differs** |
| `Cart colour` | 6 | 6 | *same here* |
| `Cart start cell` | (5, 1) | (5, 1) | *same here* |
| `Door colour` | 5 | — | **differs** |
| `Door start cell` | (4, 5) | — | **differs** |
| `arena` | 38 cells | 37 cells | **differs** |
| `background_colour` | 0 | 0 | *same here* |
| `board_shape` | 9 x 9 | 9 x 9 | *same here* |
| `goal_cell (the board's field, which the manual's goal clause may not consult)` | (2, 7) | — | **differs** |
| `landmark portal_exit` | (1, 1) | (1, 1) | *same here* |
| `non_background_cells` | 43 | 44 | **differs** |

## Names the manual uses that only a board can resolve

These names appear in the manual's own clauses, and the manual does not say what they are: each board does. They are the seam between the world and the board, and the value column shows the seam.

| name | declared in the manual as a landmark? | `base` | `no-button` |
|---|---|---|---|
| `portal_exit` | **no** — a reader of the manual alone cannot tell this is level data | (1, 1) | (1, 1) |

## Fixed by the language (see `manual/PRIMITIVES.md`)

| name | meaning |
|---|---|
| `above(X)` | the cell one step up from `X`'s cell. |
| `below(X)` | the cell one step down from `X`'s cell. |
| `colored(c, k)` | the colour showing at cell `c` — the board's colour there, or the colour of whatever object is standing on it — is exactly `k`. |
| `count(T)  /  count(T, k)` | how many objects of type `T` are present; with a second argument, how many of them have colour `k`. |
| `free(c)` | the cell `c` is on the board, the board's own colour there is the background colour, and no object is standing on it. Written `free(X.pos)` — asking whether an object's *own* cell is a legal empty one — it excludes that object from the test and asks about the board and every *other* object. |
| `leftof(X)` | the cell one step left from `X`'s cell. |
| `rightof(X)` | the cell one step right from `X`'s cell. |

## Numbers written into the manual

These clauses of the manual contain a number. A law is a fact about the world; a number it is compared against is very often a fact about one board that has been written into the manual by accident. This package does not repair them — it points at them, because on a board where the number is different the manual's sentence is false as written.

| section | clause |
|---|---|
| `goal` | `goal Cart.pos = (2, 7)` |
| `invariant` | `invariant cart_unique count(Cart) = 1 [status: proven]` |
| `invariant` | `invariant door_latch count(Button, 8) + count(Door) = 1 [status: proven]` |

## What the manual says it has checked

Each of these carries a tag saying how its author says it was established. **A tag is a claim about evidence that is not in this package.** Nothing here re-derives one, and a reader should not treat `proven` or `passed` as checked.

Where a claim can be tested against the two boards in `levels/`, test it. A claim that speaks about how a board starts — a parity, a distance, whether the goal is reachable — is a claim about *some* board, and this package carries two you can hold it against.

| clause | kind | what its author says |
|---|---|---|
| `cart_unique` | invariant | status: proven |
| `door_latch` | invariant | status: proven |
| `press_is_direction_free` | theorem | probe: pending, depends: ['press_left'] |

## Names the playbook uses that the manual does not define

A playbook answers to the manual. These names appear in its sentences and in no declaration of the manual, so nothing in this package says what they mean. Treat an entry that rests on one as unverifiable from this package rather than as a fact about the world.

| name |
|---|
| `no_button` |
| `press_before_door` |
| `w_room` |
