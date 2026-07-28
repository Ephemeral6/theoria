# theory.dsl -- Theoria manual, round 1
#
# Observed: 6 states t0..t5, one command each. 4023 of 4096 cells never vary.
# The whole of this manual is written against the 73 cells that DO vary; the
# maze (colour-5 corridors on colour-0 void, the colour-8 trail, the 9x9
# colour-9 marker at rows 48-56 / cols 42-50) is constant in every observed
# frame and is therefore board, not object.
#
# The 73 varying cells, located exactly (from zero_space's cell list):
#   G1  rows 1-3, cols 1-3   minus (2,2)          8 cells   left glyph slot
#   B1  row  5,   cols 1-3                        3 cells   left bar slot
#   G2  rows 1-3, cols 5-7                        9 cells   right glyph slot
#   B2  row  5,   cols 5-7                        3 cells   right bar slot
#   C1  rows 8-12,  cols 14-18 minus (10,16)     24 cells   upper 5x5 maze slot
#   C2  rows 14-18, cols 14-18 minus (16,16)     24 cells   lower 5x5 maze slot
#   T   (63,62), (63,63)                          2 cells   right end of row 63
# 8+3+9+3+24+24+2 = 73.  t2 changed exactly C1+C2+(63,63) = 49 cells; t5
# changed exactly G1+B1+G2+B2+C1+C2 = 71 cells.  Those two counts are why I
# trust the region decomposition above: they are not approximations, they are
# equalities.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Ring { pos: Coord, present: Bool }     # arc-colour: 9
  object Cursor { pos: Coord, present: Bool }   # arc-colour: 9
  object Pip { pos: Coord, present: Bool }      # arc-colour: 9
  object Locked { pos: Coord, present: Bool }   # arc-colour: 1
  object Spent { pos: Coord, present: Bool }    # arc-colour: 1
  object Done { pos: Coord, present: Bool }     # arc-colour: 2
  landmark slot2_glyph
  landmark slot2_bar
  landmark exit_cell
  Ring [segment: uniform_color ev: t0-t5 compress: 8]
  Cursor [segment: uniform_color ev: t0-t5 compress: 3]
  Pip [segment: uniform_color ev: t0-t5 compress: 24]
  Locked [segment: uniform_color ev: t0-t4 compress: 9]
  Done [segment: uniform_color ev: t5 compress: 8]
  Spent [segment: uniform_color ev: t2-t5 compress: 2]

events:
  event moved(o, dir) | jumped(o, dest) | vanished(o) | appeared(o)

rules:
  rule cursor_to_slot2 [ev: t5 cov: 1/1]
    when act=key(5) then jumped(Cursor, slot2_bar)

  rule ring_to_slot2 [ev: t5 cov: 1/1]
    when act=key(5) then jumped(Ring, slot2_glyph)

  rule locked_clears [ev: t5 cov: 1/1]
    when act=key(5) then vanished(Locked)

  rule done_stamped [ev: t5 cov: 1/1]
    when act=key(5) then appeared(Done)

  rule budget_opens [ev: t2 cov: 1/1]
    when act=key(2) then appeared(Spent)

  rule budget_advances [ev: t4 cov: 1/1]
    when act=key(4) then moved(Spent, left)

goal:
  goal Pip.pos = exit_cell

laws:
  invariant ring_unique count(Ring) = 1 [status: proven]
  invariant cursor_unique count(Cursor) = 1 [status: proven]
  invariant pip_at_most_one count(Pip) = 1 [status: assumed]

  theorem slot_geometry "The indicator is TWO slots, not one: a glyph slot at rows 1-3 and a bar slot at row 5, duplicated at cols 1-3 and cols 5-7. Cell (2,2) is constant 0 in all six states while (2,6) varies, so the left glyph slot can never hold a solid 3x3 and the right one can. mdl reports a solid 9-cell colour-1 3x3 present in states 0-4 and an 8-cell colour-9 3x3 present in all six; the only assignment consistent with (2,2) being constant is: states 0-4 = 9-ring left, colour-1 solid right, bar under left; state 5 = colour-2 ring left, 9-ring right, bar under right. mdl's own event tally (2 moves, 1 vanish, 1 appear, 4 recolors) is exactly what that assignment predicts."
    [depends: cursor_to_slot2, ring_to_slot2, locked_clears, done_stamped  probe: pending]

  theorem colour9_is_overloaded "Ring, Cursor and Pip are all declared arc-colour 9, and colour 9 also paints the constant row-63 bar and the constant 9x9 marker at rows 48-56. This arm cannot tell them apart by colour. I declare three objects anyway because they move independently -- Cursor moved 4 columns at t5 while Pip did not move at all -- and collapsing them into one object would make the manual predict a single body where the frames show three. I expect the responsibility check to mis-assign colour-9 pixels until the arm is given a component index; that is a defect in the manual and I am recording it rather than hiding it."
    [probe: pending]

  theorem colour1_is_overloaded "Locked (the solid 3x3 in the right glyph slot, states 0-4) and Spent (the eaten right end of row 63, states 2-5) are both colour 1 and are disjoint in space, but overlap in time at states 2,3,4. Same arm limitation as colour9_is_overloaded. They cannot be one object: Locked vanished at t5 while Spent persisted."
    [depends: locked_clears, budget_advances  probe: pending]

  theorem budget_bar "Row 63 is a 64-cell colour-9 bar being eaten from the right by colour 1. (63,63) turned at t2, (63,62) at t4; no cell turned at t1, t3 or t5. I read it as a budget that is charged when a command is ACCEPTED, not as a function of which command was sent -- ACTION1 and ACTION3 changed nothing at all and were charged nothing, and ACTION5 changed 71 cells and was also charged nothing, which is the one fact my act=key(n) guards cannot explain. budget_opens and budget_advances are therefore almost certainly the wrong guard on the right phenomenon."
    [depends: budget_opens, budget_advances  probe: pending]

  theorem pip_slots_are_a_pair "C1 (rows 8-12) and C2 (rows 14-18), cols 14-18, are two 5x5 maze slots on a 6-pixel pitch. Both were rewritten by ACTION2 (t2, 7 frames) and again by ACTION5 (t5, 9 frames). Across all six states they show only colours 5 and 9: at t2 the colour set of the changed box went [5,9] -> [1,5,9] and the new 1 is fully accounted for by (63,63). Right now C1 holds a colour-9 5x5 with a one-cell hole at its centre and C2 is empty. I do NOT know whether the glyph moved from C2 to C1 or whether one of two glyphs was consumed: mdl merges both slots into the board component obj3 and reports only 'recolor', which carries no position. This is why there is no ACTION2 rule for Pip -- the manual currently predicts ACTION2 leaves C1 and C2 alone, which I believe is wrong."
    [probe: pending]

  theorem null_commands "ACTION1 at t1 and ACTION3 at t3 changed zero cells. I have written no rule for them, so 'frame persist' reproduces both exactly. I claim only that they were refused IN THAT STATE; I do not claim they are globally inert, and one observation each is not enough to tell the two apart."
    [probe: pending]

  theorem goal_is_unwitnessed "goal Pip.pos = exit_cell is a hypothesis, not an observation. Nothing in six states witnesses a win: every state reported NOT_FINISHED, including t5 after the indicator advanced. I chose it because the constant frame reads as a maze with a token in one corner (C1) and a distinguished 9x9 marker in the opposite corner (rows 48-56, cols 42-50), and because the two expressible alternatives are already dead: count(Locked)=0 holds right now and the game is still NOT_FINISHED, and count(Done)=2 is unreachable with one declared Done instance. Treat the goal line as the cheapest survivable guess."
    [probe: pending]

  theorem trail_is_not_the_route "The colour-8 trail runs from maze cell (0,4) down column 40 to row 40 and then left to a filled 8-glyph at maze cell (5,0). It never touches the corner marker at cell (7,5), and it did not change in any of the six states. So it is either a wall, a wire to be traced, or scenery -- it is NOT a drawn solution path to exit_cell. Recorded so the next round does not mistake it for one."
    [probe: pending]
