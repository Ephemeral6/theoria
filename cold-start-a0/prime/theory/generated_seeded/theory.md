# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Cart**: characterized by pos (a coordinate), color (a whole number).
- **Switch**: characterized by pos (a coordinate), color (a whole number).
- **Door**: characterized by pos (a coordinate), color (a whole number), present (true or false).

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or jumped (involving o, dest) or recolored (involving o, c) or vanished (involving o) or appeared (involving o).

## How Things Change

- **push up** (observed in all 17 cases): When the action is push(Cart, up) and the cell above Cart is free (unoccupied), then Cart moves up.
- **push down** (observed in all 26 cases): When the action is push(Cart, down) and the cell below Cart is free (unoccupied), then Cart moves down.
- **push left** (observed in all 16 cases): When the action is push(Cart, left) and leftof(Cart) is free (unoccupied), then Cart moves left.
- **push right** (observed in all 23 cases): When the action is push(Cart, right) and rightof(Cart) is free (unoccupied), then Cart moves right.
- **push onto crate** (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 4), then Cart moves right.
- **teleport down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 3), then a peg jumps.
- **switch on up** (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then recolored(Switch, 8).
- **switch on down** (observed in all 1 cases): When the action is push(Cart, down) and colored(the cell below Cart, 7), then recolored(Switch, 8).
- **switch on left** (observed in all 1 cases): When the action is push(Cart, left) and colored(leftof(Cart), 7), then recolored(Switch, 8).
- **switch on right** (observed in all 1 cases): When the action is push(Cart, right) and colored(rightof(Cart), 7), then recolored(Switch, 8).
- **door opens up** (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Door vanishes.
- **door opens down** (observed in all 1 cases): When the action is push(Cart, down) and colored(the cell below Cart, 7), then Door vanishes.
- **door opens left** (observed in all 1 cases): When the action is push(Cart, left) and colored(leftof(Cart), 7), then Door vanishes.
- **door opens right** (observed in all 1 cases): When the action is push(Cart, right) and colored(rightof(Cart), 7), then Door vanishes.
- **switch off up** (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 8), then recolored(Switch, 7).
- **switch off down** (observed in all 1 cases): When the action is push(Cart, down) and colored(the cell below Cart, 8), then recolored(Switch, 7).
- **switch off left** (observed in all 1 cases): When the action is push(Cart, left) and colored(leftof(Cart), 8), then recolored(Switch, 7).
- **switch off right** (observed in all 1 cases): When the action is push(Cart, right) and colored(rightof(Cart), 8), then recolored(Switch, 7).
- **door shuts up** (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 8), then appeared(Door).
- **door shuts down** (observed in all 1 cases): When the action is push(Cart, down) and colored(the cell below Cart, 8), then appeared(Door).
- **door shuts left** (observed in all 1 cases): When the action is push(Cart, left) and colored(leftof(Cart), 8), then appeared(Door).
- **door shuts right** (observed in all 1 cases): When the action is push(Cart, right) and colored(rightof(Cart), 8), then appeared(Door).

## Winning Condition

The puzzle is solved when: the pos of Cart is (2, 7).

## Known Truths

### Preserved Quantities

- **cart unique**: The quantity count(Cart) always equals 1 (mathematically verified).
- **door mirrors switch**: The quantity count(Switch, 8) + count(Door) always equals 1 (mathematically verified).

### Derived Facts

- **toggle is direction free**: 推向开关就会把它翻面，无论从哪个方向推，也无论它当前是 7 还是 8——这一条八个方向-状态组合各有一个见证，是证据支持的推广，不是类比 (awaiting verification). This follows from: switch on up, switch off up.


## How a Turn Works

If no rule applies to an object in a turn, that object is exactly as it was.
At most one rule may apply to any one object in any one turn; the rules are written so that this cannot fail.
One action produces one new situation. Every rule reads the situation as it was before the action, and all of their effects happen together.

