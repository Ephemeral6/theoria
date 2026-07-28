# World Description

## Things in This World

This world takes place on a **grid** (a fixed playing surface that does not change between turns).

The following kinds of entities exist:

- **Ring**: characterized by pos (a coordinate), present (true or false).
- **Cursor**: characterized by pos (a coordinate), present (true or false).
- **Pip**: characterized by pos (a coordinate), present (true or false).
- **Locked**: characterized by pos (a coordinate), present (true or false).
- **Spent**: characterized by pos (a coordinate), present (true or false).
- **Done**: characterized by pos (a coordinate), present (true or false).

## How a Turn Works

If no rule applies to something in a turn, it is exactly as it was.

At most one rule may apply to any one thing in any one turn; the rules are written so that this cannot fail.

One move produces one new situation. Every rule reads the situation as it was before the move, and all of their effects happen together.

## What Can Happen

The following types of changes can occur:

- moved (involving o, dir) or jumped (involving o, dest) or vanished (involving o) or appeared (involving o).

## How Things Change

- **cursor to slot2** (observed in all 1 cases): When the action is key(5), then a peg jumps.
- **ring to slot2** (observed in all 1 cases): When the action is key(5), then a peg jumps.
- **locked clears** (observed in all 1 cases): When the action is key(5), then Locked vanishes.
- **done stamped** (observed in all 1 cases): When the action is key(5), then appeared(Done).
- **budget opens** (observed in all 1 cases): When the action is key(2), then appeared(Spent).
- **budget advances** (observed in all 1 cases): When the action is key(4), then Spent moves left.

## Winning Condition

The puzzle is solved when: the pos of Pip is exit_cell.

## Known Truths

### Preserved Quantities

- **ring unique**: The quantity count(Ring) always equals 1 (mathematically verified).
- **cursor unique**: The quantity count(Cursor) always equals 1 (mathematically verified).
- **pip at most one**: The quantity count(Pip) always equals 1.

### Derived Facts

- **slot geometry**: The indicator is TWO slots, not one: a glyph slot at rows 1-3 and a bar slot at row 5, duplicated at cols 1-3 and cols 5-7. Cell (2,2) is constant 0 in all six states while (2,6) varies, so the left glyph slot can never hold a solid 3x3 and the right one can. mdl reports a solid 9-cell colour-1 3x3 present in states 0-4 and an 8-cell colour-9 3x3 present in all six; the only assignment consistent with (2,2) being constant is: states 0-4 = 9-ring left, colour-1 solid right, bar under left; state 5 = colour-2 ring left, 9-ring right, bar under right. mdl's own event tally (2 moves, 1 vanish, 1 appear, 4 recolors) is exactly what that assignment predicts. (awaiting verification). This follows from: cursor to slot2, ring to slot2, locked clears, done stamped.
- **colour9 is overloaded**: Ring, Cursor and Pip are all declared arc-colour 9, and colour 9 also paints the constant row-63 bar and the constant 9x9 marker at rows 48-56. This arm cannot tell them apart by colour. I declare three objects anyway because they move independently -- Cursor moved 4 columns at t5 while Pip did not move at all -- and collapsing them into one object would make the manual predict a single body where the frames show three. I expect the responsibility check to mis-assign colour-9 pixels until the arm is given a component index; that is a defect in the manual and I am recording it rather than hiding it. (awaiting verification).
- **colour1 is overloaded**: Locked (the solid 3x3 in the right glyph slot, states 0-4) and Spent (the eaten right end of row 63, states 2-5) are both colour 1 and are disjoint in space, but overlap in time at states 2,3,4. Same arm limitation as colour9_is_overloaded. They cannot be one object: Locked vanished at t5 while Spent persisted. (awaiting verification). This follows from: locked clears, budget advances.
- **budget bar**: Row 63 is a 64-cell colour-9 bar being eaten from the right by colour 1. (63,63) turned at t2, (63,62) at t4; no cell turned at t1, t3 or t5. I read it as a budget that is charged when a command is ACCEPTED, not as a function of which command was sent -- ACTION1 and ACTION3 changed nothing at all and were charged nothing, and ACTION5 changed 71 cells and was also charged nothing, which is the one fact my act=key(n) guards cannot explain. budget_opens and budget_advances are therefore almost certainly the wrong guard on the right phenomenon. (awaiting verification). This follows from: budget opens, budget advances.
- **pip slots are a pair**: C1 (rows 8-12) and C2 (rows 14-18), cols 14-18, are two 5x5 maze slots on a 6-pixel pitch. Both were rewritten by ACTION2 (t2, 7 frames) and again by ACTION5 (t5, 9 frames). Across all six states they show only colours 5 and 9: at t2 the colour set of the changed box went [5,9] -> [1,5,9] and the new 1 is fully accounted for by (63,63). Right now C1 holds a colour-9 5x5 with a one-cell hole at its centre and C2 is empty. I do NOT know whether the glyph moved from C2 to C1 or whether one of two glyphs was consumed: mdl merges both slots into the board component obj3 and reports only 'recolor', which carries no position. This is why there is no ACTION2 rule for Pip -- the manual currently predicts ACTION2 leaves C1 and C2 alone, which I believe is wrong. (awaiting verification).
- **null commands**: ACTION1 at t1 and ACTION3 at t3 changed zero cells. I have written no rule for them, so 'frame persist' reproduces both exactly. I claim only that they were refused IN THAT STATE; I do not claim they are globally inert, and one observation each is not enough to tell the two apart. (awaiting verification).
- **goal is unwitnessed**: goal Pip.pos = exit_cell is a hypothesis, not an observation. Nothing in six states witnesses a win: every state reported NOT_FINISHED, including t5 after the indicator advanced. I chose it because the constant frame reads as a maze with a token in one corner (C1) and a distinguished 9x9 marker in the opposite corner (rows 48-56, cols 42-50), and because the two expressible alternatives are already dead: count(Locked)=0 holds right now and the game is still NOT_FINISHED, and count(Done)=2 is unreachable with one declared Done instance. Treat the goal line as the cheapest survivable guess. (awaiting verification).
- **trail is not the route**: The colour-8 trail runs from maze cell (0,4) down column 40 to row 40 and then left to a filled 8-glyph at maze cell (5,0). It never touches the corner marker at cell (7,5), and it did not change in any of the six states. So it is either a wall, a wire to be traced, or scenery -- it is NOT a drawn solution path to exit_cell. Recorded so the next round does not mistake it for one. (awaiting verification).

