# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Cart**: characterized by pos (a coordinate), color (a whole number).
- **Button**: characterized by pos (a coordinate), color (a whole number).
- **Door**: characterized by pos (a coordinate), color (a whole number), present (true or false).

## How a Turn Works

If no rule applies to something in a turn, it is exactly as it was.

At most one rule may apply to any one thing in any one turn; the rules are written so that this cannot fail.

One move produces one new situation. Every rule reads the situation as it was before the move, and all of their effects happen together.

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or recolored (involving o, c) or vanished (involving o).

## How Things Change

- **push up** (`push_up`) (observed in all 38 cases): When the action is push(Cart, up) and the cell above Cart is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell up.
- **push down** (`push_down`) (observed in all 39 cases): When the action is push(Cart, down) and the cell below Cart is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell down.
- **push left** (`push_left`) (observed in all 32 cases): When the action is push(Cart, left) and leftof(Cart) is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell left.
- **push right** (`push_right`) (observed in all 35 cases): When the action is push(Cart, right) and rightof(Cart) is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell right.
- **press up** (`press_up`) (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Button's colour becomes 8.
- **door opens up** (`door_opens_up`) (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Door stops being present.

## Winning Condition

The puzzle is solved when: the pos of Cart is (2, 7).

## Known Truths

### Preserved Quantities

- **cart unique**: The quantity count(Cart) always equals 1.
- **door latch**: The quantity count(Button, 8) + count(Door) always equals 1.

