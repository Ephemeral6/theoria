# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Cart**: characterized by pos (a coordinate), color (a whole number).
- **Door**: characterized by pos (a coordinate), color (a whole number), present (true or false).
- **Switch**: characterized by pos (a coordinate), color (a whole number).

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

- **step up** (`step_up`) (observed in all 72 cases): When the action is push(Cart, up) and the cell above Cart is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell up.
- **step down** (`step_down`) (observed in all 78 cases): When the action is push(Cart, down) and the cell below Cart is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell down.
- **step left** (`step_left`) (observed in all 42 cases): When the action is push(Cart, left) and leftof(Cart) is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell left.
- **step right** (`step_right`) (observed in all 54 cases): When the action is push(Cart, right) and rightof(Cart) is free — on the board, not a wall, and nothing standing on it, then Cart moves one cell right.
- **warp a up** (`warp_a_up`) (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 3), then Cart is placed on the cell exit_a names.
- **warp a down** (`warp_a_down`) (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 3), then Cart is placed on the cell exit_a names.
- **warp a left** (`warp_a_left`) (observed in all 3 cases): When the action is push(Cart, left) and colored(leftof(Cart), 3), then Cart is placed on the cell exit_a names.
- **warp a right** (`warp_a_right`) (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 3), then Cart is placed on the cell exit_a names.
- **warp b up** (`warp_b_up`) (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 4), then Cart is placed on the cell exit_b names.
- **warp b down** (`warp_b_down`) (observed in all 0 cases): When the action is push(Cart, down) and colored(the cell below Cart, 4), then Cart is placed on the cell exit_b names.
- **warp b left** (`warp_b_left`) (observed in all 4 cases): When the action is push(Cart, left) and colored(leftof(Cart), 4), then Cart is placed on the cell exit_b names.
- **warp b right** (`warp_b_right`) (observed in all 2 cases): When the action is push(Cart, right) and colored(rightof(Cart), 4), then Cart is placed on the cell exit_b names.
- **switch press up** (`switch_press_up`) (observed in all 0 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Switch's colour becomes 8.
- **switch press down** (`switch_press_down`) (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 7), then Switch's colour becomes 8.
- **switch press left** (`switch_press_left`) (observed in all 0 cases): When the action is push(Cart, left) and colored(leftof(Cart), 7), then Switch's colour becomes 8.
- **switch press right** (`switch_press_right`) (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 7), then Switch's colour becomes 8.
- **door opens up** (`door_opens_up`) (observed in all 0 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Door stops being present.
- **door opens down** (`door_opens_down`) (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 7), then Door stops being present.
- **door opens left** (`door_opens_left`) (observed in all 0 cases): When the action is push(Cart, left) and colored(leftof(Cart), 7), then Door stops being present.
- **door opens right** (`door_opens_right`) (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 7), then Door stops being present.
- **switch release up** (`switch_release_up`) (observed in all 0 cases): When the action is push(Cart, up) and colored(the cell above Cart, 8), then Switch's colour becomes 7.
- **switch release down** (`switch_release_down`) (observed in all 1 cases): When the action is push(Cart, down) and colored(the cell below Cart, 8), then Switch's colour becomes 7.
- **switch release left** (`switch_release_left`) (observed in all 0 cases): When the action is push(Cart, left) and colored(leftof(Cart), 8), then Switch's colour becomes 7.
- **switch release right** (`switch_release_right`) (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 8), then Switch's colour becomes 7.
- **door closes up** (`door_closes_up`) (observed in all 0 cases): When the action is push(Cart, up) and colored(the cell above Cart, 8), then Door starts being present.
- **door closes down** (`door_closes_down`) (observed in all 1 cases): When the action is push(Cart, down) and colored(the cell below Cart, 8), then Door starts being present.
- **door closes left** (`door_closes_left`) (observed in all 0 cases): When the action is push(Cart, left) and colored(leftof(Cart), 8), then Door starts being present.
- **door closes right** (`door_closes_right`) (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 8), then Door starts being present.

## Winning Condition

The puzzle is solved when: the pos of Cart is (1, 1).

## Known Truths

### Preserved Quantities

- **cart unique**: The quantity count(Cart) always equals 1 (conjectured, not yet proven).
- **door latch**: The quantity count(Door) + count(Switch, 8) always equals 1 (conjectured, not yet proven).

### Derived Facts

- **toggle is direction free**: 朝颜色 7 或 8 的格子按下就会翻转 Switch，与方向无关——但本关的 Switch 三面是墙，只能自上而下触碰，三个见证全是 DOWN；判定按世界的统一性外推（每种目标颜色的响应都只取决于颜色），不是量出来的。展开成四条 ground 规则后，其中三条 ev: none 的就是这条定理本身 (awaiting verification). This follows from: switch press down, door opens down, switch release down, door closes down.
- **warp exit is a landmark**: 两个传送口各自把 Cart 送到一个固定格子，与入口格和入口方向都无关：三个不同入口格给出同一个落点，位移读法要写三条规则且只对本关成立，落点读法只要一条 (awaiting verification). This follows from: warp a up, warp a down, warp a left, warp b up, warp b left, warp b right.
- **door is solid**: Door 在场时挡路——它不是 free，因此 step 不触发；全轨迹只有 t18 一个见证，因为本关只有一格与 Door 相邻且可达 (awaiting verification). This follows from: step up, door opens down.

