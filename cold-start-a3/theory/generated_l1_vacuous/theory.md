# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Cart**: characterized by pos (a coordinate), color (a whole number).
- **Switch**: characterized by pos (a coordinate), color (a whole number).
- **Door**: characterized by pos (a coordinate), color (a whole number), present (true or false).

## How a Turn Works

If no rule applies to something in a turn, it is exactly as it was.

At most one rule may apply to any one thing in any one turn; the rules are written so that this cannot fail.

One move produces one new situation. Every rule reads the situation as it was before the move, and all of their effects happen together.

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or jumped (involving o, dest) or recolored (involving o, c) or vanished (involving o) or appeared (involving o).

## How Things Change

- **push up** (observed in all 69 cases): When the action is push(Cart, up) and the cell above Cart is free (unoccupied), then Cart moves up.
- **push down** (observed in all 70 cases): When the action is push(Cart, down) and the cell below Cart is free (unoccupied), then Cart moves down.
- **push left** (observed in all 40 cases): When the action is push(Cart, left) and leftof(Cart) is free (unoccupied), then Cart moves left.
- **push right** (observed in all 46 cases): When the action is push(Cart, right) and rightof(Cart) is free (unoccupied), then Cart moves right.
- **teleport a up** (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 3), then a peg jumps.
- **teleport a down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 3), then a peg jumps.
- **teleport a left** (observed in all 4 cases): When the action is push(Cart, left) and colored(leftof(Cart), 3), then a peg jumps.
- **teleport a right** (observed in all 2 cases): When the action is push(Cart, right) and colored(rightof(Cart), 3), then a peg jumps.
- **teleport b up** (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 4), then a peg jumps.
- **teleport b down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 4), then a peg jumps.
- **teleport b left** (observed in all 4 cases): When the action is push(Cart, left) and colored(leftof(Cart), 4), then a peg jumps.
- **teleport b right** (observed in all 2 cases): When the action is push(Cart, right) and colored(rightof(Cart), 4), then a peg jumps.
- **press up** (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then recolored(Switch, 8).
- **door opens up** (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Door vanishes.
- **press down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 7), then recolored(Switch, 8).
- **door opens down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 7), then Door vanishes.
- **unpress up** (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 8), then recolored(Switch, 7).
- **door closes up** (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 8), then appeared(Door).
- **unpress down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 8), then recolored(Switch, 7).
- **door closes down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 8), then appeared(Door).

## Winning Condition

The puzzle is solved when: the pos of Cart is (7, 7).

## Known Truths

### Preserved Quantities

- **cart unique**: The quantity count(Cart) always equals 1 (mathematically verified).
- **switch door latch**: The quantity count(Switch, 8) + count(Door) always equals 1 (mathematically verified).

### Derived Facts

- **portal destination is absolute**: 推向颜色 3 的格子, 小车落到同一个绝对格 exit_a, 而不是相对自身位移——第一关的四个方向各给一个见证, 四个位移互不相同而落点相同; 这一条只有换关才能真正判决, 那正是 A3 (verified by testing). This follows from: teleport a up, teleport a down, teleport a left, teleport a right.


## How a Turn Works

If no rule applies to an object in a turn, that object is exactly as it was.
At most one rule may apply to any one object in any one turn; the rules are written so that this cannot fail.
One action produces one new situation. Every rule reads the situation as it was before the action, and all of their effects happen together.

