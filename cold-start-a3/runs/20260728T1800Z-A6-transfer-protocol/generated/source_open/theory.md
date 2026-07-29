# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Cart**: characterized by pos (a coordinate), color (a whole number).
- **Block**: characterized by pos (a coordinate), color (a whole number).

## How a Turn Works

If no rule applies to something in a turn, it is exactly as it was.

At most one rule may apply to any one thing in any one turn; the rules are written so that this cannot fail.

One move produces one new situation. Every rule reads the situation as it was before the move, and all of their effects happen together.

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or jumped (involving o, dest) or recolored (involving o, c) or vanished (involving o) or appeared (involving o).

## How Things Change

- **step up** (`step_up`) (observed in all 5 cases): When the action is push(Cart, up) and the cell above Cart is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell up.
- **step down** (`step_down`) (observed in all 5 cases): When the action is push(Cart, down) and the cell below Cart is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell down.
- **step left** (`step_left`) (observed in all 7 cases): When the action is push(Cart, left) and leftof(Cart) is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell left.
- **step right** (`step_right`) (observed in all 6 cases): When the action is push(Cart, right) and rightof(Cart) is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell right.
- **shove up** (`shove_up`) (observed in all 0 cases): When the action is push(Cart, up) and colored(the cell above Cart, 2) and the cell above Block is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell up.
- **shove down** (`shove_down`) (observed in all 0 cases): When the action is push(Cart, down) and colored(the cell below Cart, 2) and the cell below Block is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell down.
- **shove left** (`shove_left`) (observed in all 0 cases): When the action is push(Cart, left) and colored(leftof(Cart), 2) and leftof(Block) is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell left.
- **shove right** (`shove_right`) (observed in all 2 cases): When the action is push(Cart, right) and colored(rightof(Cart), 2) and rightof(Block) is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell right.
- **block up** (`block_up`) (observed in all 0 cases): When the action is push(Cart, up) and colored(the cell above Cart, 2) and the cell above Block is free — on the board, not a wall, and nothing standing on it, then Block moves one cell up.
- **block down** (`block_down`) (observed in all 0 cases): When the action is push(Cart, down) and colored(the cell below Cart, 2) and the cell below Block is free — on the board, not a wall, and nothing standing on it, then Block moves one cell down.
- **block left** (`block_left`) (observed in all 0 cases): When the action is push(Cart, left) and colored(leftof(Cart), 2) and leftof(Block) is free — on the board, not a wall, and nothing standing on it, then Block moves one cell left.
- **block right** (`block_right`) (observed in all 2 cases): When the action is push(Cart, right) and colored(rightof(Cart), 2) and rightof(Block) is free — on the board, not a wall, and nothing standing on it, then Block moves one cell right.

## Winning Condition

The puzzle is solved when: the pos of Cart is (2, 5).

## Known Truths

### Preserved Quantities

- **cart unique**: The quantity count(Cart) always equals 1 (mathematically verified).
- **block unique**: The quantity count(Block) always equals 1 (mathematically verified).

### Derived Facts

- **shove is relative not absolute**: 推动是一对物体之间的相对事实——小车进入方块让出的那一格, 方块沿同一方向前进一格——而不是关于某个绝对格子的事实; 第一关只有两个见证, 都是同一行的向右推, 两种读法在那里无法区分, 只有换一个方块位置完全不同的世界才能裁决 (verified by testing). This follows from: shove right, block right.

