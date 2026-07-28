# theory.dsl -- Theoria manual, second draft. Six observed transitions.
#
# COMPILER FIX: the last draft died on `invariant ring_fills_one_cell "<prose>"`.
# The invariant body is parsed for a comparison operator, so a prose invariant
# cannot exist. Every prose claim that was an `invariant` is now a `theorem`,
# which is where prose belongs. Nothing was deleted; two claims changed section.
#
# What the frame is made of: a 64x64 grid whose 4023 constant cells are `board`.
# The 73 cells that ever varied are, exactly, and they add up:
#   HUD token A  rows 1-3 x cols 1-3 minus (2,2)          =  8
#   HUD token B  rows 1-3 x cols 5-7                      =  9
#   underline    row 5 cols 1-3 and row 5 cols 5-7        =  6
#   maze cell (0,0)  rows 8-12  x cols 14-18 minus (10,16) = 24
#   maze cell (1,0)  rows 14-18 x cols 14-18 minus (16,16) = 24
#   tally bar    (63,62) and (63,63)                       =  2
#   8 + 9 + 6 + 24 + 24 + 2 = 73, the whole dynamic set.
# Cross-check against the diffs: t2 touched 24+24+1 = 49, t4 touched 1,
# t5 touched 23+24+24 = 71, and the union is exactly those 73 cells.
# Everything else -- the colour-5 maze, the colour-8 route, the colour-9
# bracket at rows 48-56, the other 62 cells of row 63 -- is board.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Player { pos: Coord }  # arc-colour: 9
  object Done { pos: Coord, present: Bool }  # arc-colour: 2
  object Token { pos: Coord, color: Int }  # arc-colour: 1
  landmark cell_r0c0  # arc-cell: (8, 14)
  landmark cell_r1c0  # arc-cell: (14, 14)
  landmark cell_r0c4  # arc-cell: (8, 38)
  landmark cell_r5c0  # arc-cell: (38, 14)
  landmark exit_cell  # arc-cell: (50, 44)
  domain dir { up, down, left, right }
  Player [segment: ring24_colour9_in_one_maze_cell ev: t0-t5 compress: 144]
  Token [segment: solid3x3_colour1_hud_slot_b ev: t0-t5 compress: 45]
  Done [segment: ring8_colour2_hud_slot_a ev: t5 compress: 8]

events:
  event jumped(o, dest) | recolored(o, c) | appeared(o)

rules:
  rule step_down_from_home [ev: t2 cov: 1/1]
    when act=key(2) and colored(cell_r0c0, 9) then jumped(Player, cell_r1c0)
  rule key5_sends_ring_home [ev: t5 cov: 1/1]
    when act=key(5) and colored(cell_r1c0, 9) then jumped(Player, cell_r0c0)
  rule key5_spends_token_a [ev: t5 cov: 1/1]
    when act=key(5) then appeared(Done)
  rule key5_lights_token_b [ev: t5 cov: 1/1]
    when act=key(5) then recolored(Token, 9)

goal:
  goal Player.pos = exit_cell

laws:
  invariant one_ring count(Player) = 1 [status: observed]

  theorem ring_fills_one_cell "the 24 colour-9 pixels of the maze ring always cover exactly one 5x5 maze cell minus its centre pixel, and that centre pixel stays colour 5. This was an invariant in the last draft and would not parse, because an invariant body must contain a comparison operator and this claim is about a shape. It is 6/6 frames true and unproven."
    [probe: pending]

  theorem board_is_static "4023 of the 4096 cells never changed across six frames; the maze, the colour-8 route, the colour-9 bracket at rows 48-56 and 62 of the 64 cells of row 63 are all among them. Also demoted from invariant for the same parse reason."
    [probe: pending]

  theorem maze_grid_pitch_six "maze cell (r,c) spans rows 8+6r..12+6r and cols 14+6c..18+6c; the separator lines sit on rows 7+6r and cols 13+6c and are themselves colour 5, so adjacent floor cells are not divided by anything. Cell centres are (10+6r, 16+6c). The ring moved 6 pixels down at t2 and 6 pixels back up at t5. The only movement event I have is moved(o,dir), which steps ONE pixel, so I cannot write a general step rule at all; I wrote two jumped() rules naming the only two cells ever witnessed. This manual therefore predicts NOTHING about any maze cell other than (0,0) and (1,0)."
    [depends: step_down_from_home, key5_sends_ring_home  probe: pending]

  theorem walkable_is_colour_five "inside the maze rectangle a cell is floor when its pixels are colour 5 and void when they are colour 0. Witness: cell (1,1), rows 14-18 x cols 20-24, is all colour 0, and key(4) fired from cell (1,0) at t4 did not move the ring. This inverts the guard language: free(x) tests for the BACKGROUND colour, which here is 0, i.e. exactly the cells that are NOT enterable. Any future movement rule must be guarded with colored(x, 5), never with free(x). I am recording this before I need it, because writing free() would have silently meant the opposite of what I intend."
    [probe: pending]

  theorem directional_keys "I believe key(1)=up, key(2)=down, key(3)=left, key(4)=right. Evidence: key(2) moved the ring from cell (0,0) to (1,0) (t2); key(1) fired from the top cell row and key(3) from the leftmost cell column, both off-board, and both changed nothing (t1,t3); key(4) fired from (1,0) whose right neighbour cell (1,1) is colour 0 by walkable_is_colour_five, and the ring did not move (t4). A second reading fits every one of these frames equally well: key(2) and key(4) are bound and key(1) and key(3) are unbound, which is why this is a theorem. The two readings are separated by one experiment -- fire key(1) or key(3) from a cell that is not on the boundary."
    [depends: step_down_from_home  probe: pending]

  theorem tally_bar "row 63 is a 64-cell bar of colour 9 that fills with colour 1 from the right edge: (63,63) turned 1 at t2 and (63,62) turned 1 at t4. It did not advance at t1, t3 or t5. So it counts something that the two off-board attempts did not do, that the blocked-into-void attempt DID do, and that key(5) did not do. 'Move commands the engine actually processed' fits; so does 'key(2) and key(4) are the only bound movement keys'. There is no event in the language for growing an object one pixel, so I cannot draw this at all: the manual leaves (63,62) and (63,63) unexplained in every frame, and I expect the responsibility check to report exactly those two cells."
    [probe: pending]

  theorem cascade_length_is_a_signal "t2 returned 7 frames and t5 returned 9 frames for one command; t1, t3 and t4 returned 1 each. t4 returned one frame yet still changed a pixel. So a multi-frame command is an animation of real motion and a single-frame command is an instant verdict. Only the last frame of each cascade reaches me and `cascade single_frame` is the only value that compiles, so any intermediate cell-by-cell slide is invisible here -- and seeing one would be direct evidence for maze_grid_pitch_six."
    [probe: pending]

  theorem hud_is_two_tokens "the HUD holds two 3x3 tokens (rows 1-3 cols 1-3, and cols 5-7) and a 3-pixel underline at row 5 that sits under exactly one of them. Frames 0-4: token A is a colour-9 ring and is underlined, token B is a solid colour-1 block. Frame 5: token A is a colour-2 ring and unmarked, token B is a colour-9 ring and IS underlined, the underline having jumped from cols 1-3 to cols 5-7 -- and the maze ring is back at cell (0,0), while the tally bar did not reset. key(5) did all of that in one 9-frame command. This reads either as 'attempt spent, position reset' or as 'objective cleared, next objective'. They disagree about whether key(5) is to be hoarded or sought. Nothing observed separates them, though the tally bar NOT resetting is weak evidence against a full restart."
    [depends: key5_spends_token_a, key5_lights_token_b, key5_sends_ring_home  probe: pending]

  theorem colour_nine_collision "colour 9 paints at least five different things: the player ring, HUD token A (frames 0-4), HUD token B (frame 5), the 3-pixel selection underline, the bracket around maze cell (7,5), and the row-63 bar. One colour binds one object in this arm, so Player takes 9 and the HUD colour-9 pixels and the 6 underline pixels have no object and will be reported unexplained. Worse, the arm locates Player by searching colour 9, and it may find the bar or the bracket instead of the ring; if the redraw puts Player somewhere absurd, that is this collision and not a bad movement rule. I believe there are at least three distinct colour-9 entities and the arm cannot tell them apart, so I say so here rather than declaring a second object that would be indistinguishable from the first."
    [probe: pending]

  theorem colour_one_collision "colour 1 paints HUD token B (frames 0-4) and also the filled pixels of the row-63 tally bar (from t2 onward). Token is declared with colour 1, so from t2 the arm has two colour-1 regions to choose between and may locate Token at (63,62)-(63,63) instead of the HUD. Same defect as colour_nine_collision, same reason for not splitting the object."
    [probe: pending]

  theorem vacated_cell_repaints_to_five "when the ring left cell (0,0) at t2, those 24 pixels became colour 5, not the background colour 0; and cell (1,0) did the same at t5. My manual has no object that owns 'floor', and no event that repaints a cell an object has left, so on any frame where the ring is at one of the two witnessed cells I expect the OTHER cell's 24 pixels to be drawn wrong. That is 24 unexplained pixels per frame and it is the largest known defect in this manual. Declaring a colour-5 Floor object would seize the entire 1006-cell maze, which is worse."
    [probe: pending]

  theorem goal_is_the_bracketed_cell "maze cell (7,5), rows 50-54 x cols 44-48, is edged in colour 9 on row 49 cols 43-48, row 55 cols 43-48 and col 49 rows 50-54, and carries a lone colour-9 pixel at its centre (52,46). It is the only cell in the frame drawn that way and it is drawn in the ring's own colour. I take it for the target. No transition witnesses this -- it is read off the static board -- so the goal section is a hypothesis the searcher will act on and the next win or non-win settles it."
    [probe: pending]

  theorem colour_eight_is_a_drawn_route "colour 8 is not scattered decoration; it is one connected polyline along maze cell centres. A 3x3 blob at rows 9-11 cols 39-41 sits on the centre of cell (0,4); a vertical line at col 40 (the centre column of cell column 4) runs from row 12 down to row 40; a horizontal line at row 40 (the centre row of cell row 5) runs from col 40 left to col 14; and cell (5,0), rows 38-42 x cols 14-18, is filled solid. So the route is cell (0,4) -> (5,4) -> (5,0), with a small mark at one end and a filled cell at the other. Not one of those pixels changed in six frames. Whether it is a worked example to imitate, a path already consumed, a barrier, or another agent's track is untested, and no rule of mine mentions it. Note it does NOT touch the player's start cell (0,0) nor the bracketed cell (7,5), which is the main reason I did not make it the goal."
    [probe: pending]

  theorem coord_convention "every landmark above names the TOP-LEFT pixel of the intended 5x5 cell: cell_r0c0 = (8,14), cell_r1c0 = (14,14), cell_r0c4 = (8,38), cell_r5c0 = (38,14), exit_cell = (50,44). If the arm's Coord is instead a centroid, all five must shift by (+2,+2) to (10,16), (16,16), (10,40), (40,16), (52,46). The ring's centroid happens to be its own colour-5 hole, which is a coincidence worth remembering when reading a failed redraw. Until one redraw is compared I do not know which convention holds."
    [probe: pending]
