# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Cart**: characterized by pos (a coordinate), color (a whole number).
- **Button**: characterized by pos (a coordinate), color (a whole number).
- **Door**: characterized by pos (a coordinate), color (a whole number), present (true or false).

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or jumped (involving o, dest) or recolored (involving o, c) or vanished (involving o).

## How Things Change

- **push up** (observed in all 40 cases): When the action is push(Cart, up) and the cell above Cart is free (unoccupied), then Cart moves up.
- **push down** (observed in all 40 cases): When the action is push(Cart, down) and the cell below Cart is free (unoccupied), then Cart moves down.
- **push left** (observed in all 33 cases): When the action is push(Cart, left) and leftof(Cart) is free (unoccupied), then Cart moves left.
- **push right** (observed in all 36 cases): When the action is push(Cart, right) and rightof(Cart) is free (unoccupied), then Cart moves right.
- **teleport down** (observed in all 1 cases): When the action is push(Cart, down) and colored(the cell below Cart, 3), then a peg jumps.
- **press up** (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then recolored(Button, 8).
- **door opens up** (observed in all 1 cases): When the action is push(Cart, up) and colored(the cell above Cart, 7), then Door vanishes.

## Winning Condition

The puzzle is solved when: the pos of Cart is (2, 7).

## Known Truths

### Preserved Quantities

- **cart unique**: The quantity count(Cart) always equals 1 (mathematically verified).
- **door latch**: The quantity count(Button, 8) + count(Door) always equals 1 (mathematically verified).

### Derived Facts

- **pocket unreachable**: 格子 (7,1) 是地板，但它四邻全是墙，而说明书里能移动小车的规则只有相邻推动和一条传送——传送的落点是 (7,6)——所以没有任何可达状态让小车站上 (7,1) (verified by testing). This follows from: push up, push down, push left, push right, teleport down.
- **teleport is colour triggered**: 推向颜色 3 的格子就会被传送，而不是因为站在 (6,4) 这一格——本关只有一个传送口，两条守卫在这个世界里外延相同，实验分不开（probes.jsonl P-03），按描述长度裁决，证据永远补不齐 (awaiting verification). This follows from: teleport down.


## How a Turn Works

If no rule applies to an object in a turn, that object is exactly as it was.
At most one rule may apply to any one object in any one turn; the rules are written so that this cannot fail.
One action produces one new situation. Every rule reads the situation as it was before the action, and all of their effects happen together.

