# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Cart**: characterized by pos (a coordinate), color (a whole number).
- **Switch**: characterized by pos (a coordinate), color (a whole number).
- **Door**: characterized by pos (a coordinate), color (a whole number), present (true or false).

These names appear in the rules and are **not** fixed by this description — each individual level says which cell each one is:

- **exit_a**
- **exit_b**

## How a Turn Works

If no rule applies to something in a turn, it is exactly as it was.

At most one rule may apply to any one thing in any one turn; the rules are written so that this cannot fail.

One move produces one new situation. Every rule reads the situation as it was before the move, and all of their effects happen together.

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or jumped (involving o, dest) or recolored (involving o, c) or vanished (involving o) or appeared (involving o).

## How Things Change

- **push up** (`push_up`) (observed in all 69 cases): When the action is push(Cart, up) and the cell above Cart is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell up.
- **push down** (`push_down`) (observed in all 70 cases): When the action is push(Cart, down) and the cell below Cart is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell down.
- **push left** (`push_left`) (observed in all 40 cases): When the action is push(Cart, left) and leftof(Cart) is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell left.
- **push right** (`push_right`) (observed in all 46 cases): When the action is push(Cart, right) and rightof(Cart) is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell right.
- **teleport a up** (`teleport_a_up`) (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 3), then Cart is placed on the cell exit_a names.
- **teleport a down** (`teleport_a_down`) (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 3), then Cart is placed on the cell exit_a names.
- **teleport a left** (`teleport_a_left`) (observed in all 4 cases): When the action is push(Cart, left) and colored(leftof(Cart), 3), then Cart is placed on the cell exit_a names.
- **teleport a right** (`teleport_a_right`) (observed in all 2 cases): When the action is push(Cart, right) and colored(rightof(Cart), 3), then Cart is placed on the cell exit_a names.
- **teleport b up** (`teleport_b_up`) (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 4), then Cart is placed on the cell exit_b names.
- **teleport b down** (`teleport_b_down`) (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 4), then Cart is placed on the cell exit_b names.
- **teleport b left** (`teleport_b_left`) (observed in all 4 cases): When the action is push(Cart, left) and colored(leftof(Cart), 4), then Cart is placed on the cell exit_b names.
- **teleport b right** (`teleport_b_right`) (observed in all 2 cases): When the action is push(Cart, right) and colored(rightof(Cart), 4), then Cart is placed on the cell exit_b names.
- **press up** (`press_up`) (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Switch's colour becomes 8.
- **door opens up** (`door_opens_up`) (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Door stops being present.
- **press down** (`press_down`) (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 7), then Switch's colour becomes 8.
- **door opens down** (`door_opens_down`) (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 7), then Door stops being present.
- **unpress up** (`unpress_up`) (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 8), then Switch's colour becomes 7.
- **door closes up** (`door_closes_up`) (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 8), then Door starts being present.
- **unpress down** (`unpress_down`) (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 8), then Switch's colour becomes 7.
- **door closes down** (`door_closes_down`) (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 8), then Door starts being present.

## Winning Condition

The puzzle is solved when: the pos of Cart is (1, 1).

## Known Truths

### Preserved Quantities

- **cart unique**: The quantity count(Cart) always equals 1 (mathematically verified).
- **switch door latch**: The quantity count(Switch, 8) + count(Door) always equals 1 (mathematically verified).

### Derived Facts

- **portal destination is absolute**: 推向颜色 3 的格子, 小车落到同一个绝对格 exit_a, 而不是相对自身位移——第一关的四个方向各给一个见证, 四个位移互不相同而落点相同; 这一条只有换关才能真正判决, 那正是 A3 (verified by testing). This follows from: teleport a up, teleport a down, teleport a left, teleport a right.

