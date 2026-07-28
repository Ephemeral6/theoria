# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Cart**: characterized by pos (a coordinate), color (a whole number).

## How a Turn Works

If no rule applies to something in a turn, it is exactly as it was.

At most one rule may apply to any one thing in any one turn; the rules are written so that this cannot fail.

One move produces one new situation. Every rule reads the situation as it was before the move, and all of their effects happen together.

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or jumped (involving o, dest).

## How Things Change

- **push up** (observed in all 23 cases): When the action is push(Cart, up) and the cell above Cart is free (unoccupied), then Cart moves up.
- **push down** (observed in all 28 cases): When the action is push(Cart, down) and the cell below Cart is free (unoccupied), then Cart moves down.
- **push left** (observed in all 18 cases): When the action is push(Cart, left) and leftof(Cart) is free (unoccupied), then Cart moves left.
- **push right** (observed in all 22 cases): When the action is push(Cart, right) and rightof(Cart) is free (unoccupied), then Cart moves right.
- **teleport down** (observed in all 1 cases): When the action is push(Cart, down) and colored(the cell below Cart, 3), then a peg jumps.

## Winning Condition

The puzzle is solved when: the pos of Cart is (2, 7).

## Known Truths

### Preserved Quantities

- **right room locked**: The quantity w_room(Cart) always equals 0 (mathematically verified).

### Derived Facts

- **unsolvable no button**: 赢不了：小车永远待在左屋——它开局在左屋，而每一条推动规则都只把它送到相邻的空格，传送门也只把它送回左屋 (1,1)；隔墙上唯一的缺口 (4,5) 在这一关始终是障碍，没有任何规则能让它变空；目标格 (2,7) 在右屋，所以到不了。 (verified by testing). This follows from: push up, push down, push left, push right, teleport down.

