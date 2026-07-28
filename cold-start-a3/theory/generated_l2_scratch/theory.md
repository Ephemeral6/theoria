# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Cart**: characterized by pos (a coordinate), color (a whole number).
- **Door**: characterized by pos (a coordinate), color (a whole number), present (true or false).
- **Switch**: characterized by pos (a coordinate), color (a whole number).

## How a Turn Works

If no rule applies to something in a turn, it is exactly as it was.

At most one rule may apply to any one thing in any one turn; the rules are written so that this cannot fail.

One move produces one new situation. Every rule reads the situation as it was before the move, and all of their effects happen together.

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or jumped (involving o, dest) or recolored (involving o, c) or vanished (involving o) or appeared (involving o).

## How Things Change

- **step up** (observed in all 72 cases): When the action is push(Cart, up) and the cell above Cart is free (unoccupied), then Cart moves up.
- **step down** (observed in all 78 cases): When the action is push(Cart, down) and the cell below Cart is free (unoccupied), then Cart moves down.
- **step left** (observed in all 42 cases): When the action is push(Cart, left) and leftof(Cart) is free (unoccupied), then Cart moves left.
- **step right** (observed in all 54 cases): When the action is push(Cart, right) and rightof(Cart) is free (unoccupied), then Cart moves right.
- **warp a up** (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 3), then a peg jumps.
- **warp a down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 3), then a peg jumps.
- **warp a left** (observed in all 3 cases): When the action is push(Cart, left) and colored(leftof(Cart), 3), then a peg jumps.
- **warp a right** (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 3), then a peg jumps.
- **warp b up** (observed in all 2 cases): When the action is push(Cart, up) and colored(the cell above Cart, 4), then a peg jumps.
- **warp b down** (observed in all 0 cases): When the action is push(Cart, down) and colored(the cell below Cart, 4), then a peg jumps.
- **warp b left** (observed in all 4 cases): When the action is push(Cart, left) and colored(leftof(Cart), 4), then a peg jumps.
- **warp b right** (observed in all 2 cases): When the action is push(Cart, right) and colored(rightof(Cart), 4), then a peg jumps.
- **switch press up** (observed in all 0 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then recolored(Switch, 8).
- **switch press down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 7), then recolored(Switch, 8).
- **switch press left** (observed in all 0 cases): When the action is push(Cart, left) and colored(leftof(Cart), 7), then recolored(Switch, 8).
- **switch press right** (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 7), then recolored(Switch, 8).
- **door opens up** (observed in all 0 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Door vanishes.
- **door opens down** (observed in all 2 cases): When the action is push(Cart, down) and colored(the cell below Cart, 7), then Door vanishes.
- **door opens left** (observed in all 0 cases): When the action is push(Cart, left) and colored(leftof(Cart), 7), then Door vanishes.
- **door opens right** (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 7), then Door vanishes.
- **switch release up** (observed in all 0 cases): When the action is push(Cart, up) and colored(the cell above Cart, 8), then recolored(Switch, 7).
- **switch release down** (observed in all 1 cases): When the action is push(Cart, down) and colored(the cell below Cart, 8), then recolored(Switch, 7).
- **switch release left** (observed in all 0 cases): When the action is push(Cart, left) and colored(leftof(Cart), 8), then recolored(Switch, 7).
- **switch release right** (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 8), then recolored(Switch, 7).
- **door closes up** (observed in all 0 cases): When the action is push(Cart, up) and colored(the cell above Cart, 8), then appeared(Door).
- **door closes down** (observed in all 1 cases): When the action is push(Cart, down) and colored(the cell below Cart, 8), then appeared(Door).
- **door closes left** (observed in all 0 cases): When the action is push(Cart, left) and colored(leftof(Cart), 8), then appeared(Door).
- **door closes right** (observed in all 0 cases): When the action is push(Cart, right) and colored(rightof(Cart), 8), then appeared(Door).

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


## How a Turn Works

If no rule applies to an object in a turn, that object is exactly as it was.
At most one rule may apply to any one object in any one turn; the rules are written so that this cannot fail.
One action produces one new situation. Every rule reads the situation as it was before the action, and all of their effects happen together.

