# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Cart**: characterized by pos (a coordinate), color (a whole number).
- **Button**: characterized by pos (a coordinate), color (a whole number).
- **Door**: characterized by pos (a coordinate), color (a whole number), present (true or false).

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or recolored (involving o, c) or vanished (involving o).

## How Things Change

- **push up** (observed in all 38 cases): When the action is push(Cart, up) and the cell above Cart is free (unoccupied), then Cart moves up.
- **push down** (observed in all 39 cases): When the action is push(Cart, down) and the cell below Cart is free (unoccupied), then Cart moves down.
- **push left** (observed in all 32 cases): When the action is push(Cart, left) and leftof(Cart) is free (unoccupied), then Cart moves left.
- **push right** (observed in all 35 cases): When the action is push(Cart, right) and rightof(Cart) is free (unoccupied), then Cart moves right.
- **press up** (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then recolored(Button, 8).
- **door opens up** (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Door vanishes.

## Winning Condition

The puzzle is solved when: the pos of Cart is (2, 7).

## Known Truths

### Preserved Quantities

- **cart unique**: The quantity count(Cart) always equals 1 (mathematically verified).
- **door latch**: The quantity count(Button, 8) + count(Door) always equals 1 (mathematically verified).

### Derived Facts

- **right room locked**: 小车永远到不了右边那个房间：第 5 列从第 1 行到第 7 行是完整的墙，而说明书里的每一条规则都只让小车走到相邻格，所以目标格 (2,7) 不可达 (awaiting verification). This follows from: push up, push down, push left, push right.


## How a Turn Works

If no rule applies to an object in a turn, that object is exactly as it was.
At most one rule may apply to any one object in any one turn; the rules are written so that this cannot fail.
One action produces one new situation. Every rule reads the situation as it was before the action, and all of their effects happen together.

