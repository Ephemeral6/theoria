# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Floor**: characterized by pos (a coordinate), color (a whole number).
- **Cart**: characterized by pos (a coordinate), color (a whole number).
- **Landmark_3**: characterized by pos (a coordinate), color (a whole number).
- **Landmark_4**: characterized by pos (a coordinate), color (a whole number).

## How a Turn Works

If no rule applies to something in a turn, it is exactly as it was.

At most one rule may apply to any one thing in any one turn; the rules are written so that this cannot fail.

One move produces one new situation. Every rule reads the situation as it was before the move, and all of their effects happen together.

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir).

## How Things Change

- **move down** (`move_down`) (observed in all 4 cases): When the action is key(2) and colored(the cell below Cart, 0), then Cart moves one cell down.

## Known Truths

### Preserved Quantities

- **cart unique**: The quantity count(Cart) always equals 1 (mathematically verified).

### Derived Facts

- **board static**: Board (colour 1) forms the border and interior walls, unchanging across all observed transitions. (awaiting verification).
- **floor terrain**: Floor (colour 0, with arc-instances: all) fills every unoccupied interior cell. When Cart moves away, floor is revealed; when Cart occupies a cell, it covers the floor visually. (awaiting verification).
- **action2 moves cart**: ACTION2 causes Cart to move down one cell when the cell below is floor (colour 0). ACTION1, ACTION3, ACTION4, ACTION5 produce no observable change in the observed window. (awaiting verification).
- **landmarks static**: Landmark_3 (colour 3) at (6,6) and Landmark_4 (colour 4) at (5,3) remain unchanged throughout. Their role is unknown. (awaiting verification).
- **replay init mismatch**: The replay failure at t=1 (manual predicts (1,1)=1, world is (1,1)=0) contradicts the shown initial frame where (1,1)=0. Frame initialization or transition semantics may have a subtlety not yet expressed in rules or object semantics. (awaiting verification).

