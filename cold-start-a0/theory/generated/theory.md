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

- moved (involving o, dir) or jumped (involving o, dest) or recolored (involving o, c) or vanished (involving o).

## How Things Change

- **push up** (observed in all 52 cases): When the action is push(Cart, up) and the cell above Cart is free (unoccupied), then Cart moves up.
- **push down** (observed in all 62 cases): When the action is push(Cart, down) and the cell below Cart is free (unoccupied), then Cart moves down.
- **push left** (observed in all 46 cases): When the action is push(Cart, left) and leftof(Cart) is free (unoccupied), then Cart moves left.
- **push right** (observed in all 52 cases): When the action is push(Cart, right) and rightof(Cart) is free (unoccupied), then Cart moves right.
- **teleport down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 3), then a peg jumps.
- **press left** (observed in all 1 cases): When the action is push(Cart, left) and colored(leftof(Cart), 7), then recolored(Button, 8).
- **door opens left** (observed in all 1 cases): When the action is push(Cart, left) and colored(leftof(Cart), 7), then Door vanishes.

## Winning Condition

The puzzle is solved when: the pos of Cart is (2, 7).

## Known Truths

### Preserved Quantities

- **cart unique**: The quantity count(Cart) always equals 1 (mathematically verified).
- **door latch**: The quantity count(Button, 8) + count(Door) always equals 1 (mathematically verified).

### Derived Facts

- **press is direction free**: 推向未按下的按钮就会按下它，无论从哪个方向推——但这一条只有一个见证，本世界的闩锁不可逆，证据永远补不齐 (awaiting verification). This follows from: press left.

