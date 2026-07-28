# theory.dsl -- Theoria manual, first draft. Six observed transitions.
#
# What the frame is made of: a 64x64 grid whose 4023 constant cells I hand to
# `board`. The 73 cells that ever varied are, exactly:
#   * rows 1-3 x cols 1-3 minus (2,2), plus row 5 cols 1-3   -- HUD token A + underline
#   * rows 1-3 x cols 5-7, plus row 5 cols 5-7               -- HUD token B + underline
#   * rows 8-12 x cols 14-18 minus (10,16)                   -- maze cell (0,0)
#   * rows 14-18 x cols 14-18 minus (16,16)                  -- maze cell (1,0)
#   * (63,62) and (63,63)                                    -- right end of the row-63 bar
# 23 + 24 + 24 + 2 = 73, which is the whole dynamic set. Everything else --
# the colour-5 maze, the colour-8 marks, the colour-9 bracket at rows 49-55,
# the other 62 cells of row 63 -- never moved in six frames and is board.

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
  invariant one_ring count(Player) = 1 [status: observed 6/6 frames, never proven]
  invariant ring_fills_one_cell "the 24 colour-9 pixels always cover exactly one 5x5 maze cell minus its centre pixel, which stays colour 5" [status: observed 6/6 frames]
  invariant board_is_static "4023 of 4096 cells never changed across six frames; the maze, the colour-8 marks and the colour-9 bracket are among them" [status: observed 6/6 frames]

  theorem grid_pitch_six "maze cell (r,c) spans rows 8+6r..12+6r and cols 14+6c..18+6c; walls sit on rows 7+6r and cols 13+6c. The ring moved 6 pixels at t2 and 6 pixels back at t5. moved(o,dir) steps one cell, so I could not write a general step rule and wrote two jumped() rules naming the only two positions ever witnessed. This manual therefore predicts NOTHING about any maze cell other than (0,0) and (1,0)."
    [depends: step_down_from_home, key5_sends_ring_home  probe: pending]

  theorem directional_keys "I believe key(1)=up, key(2)=down, key(3)=left, key(4)=right. Evidence: key(2) moved the ring from cell (0,0) to (1,0) (t2); key(1) fired from the top row and key(3) from the leftmost column and both changed nothing (t1,t3); key(4) fired from (1,0) whose right neighbour rows 14-18 cols 20-24 is colour 0, i.e. not floor, and the ring did not move (t4). Every one of these is also consistent with the key being unbound, which is why this is a theorem and not a rule."
    [depends: step_down_from_home  probe: pending]

  theorem tally_bar "row 63 is a bar of colour 9 that fills with colour 1 from the right edge: (63,63) turned 1 at t2 and (63,62) turned 1 at t4. It did not advance at t1, t3 or t5. The pattern that fits is 'a directional action the engine actually processed', with the two off-board attempts (t1,t3) rejected before counting and the wall bump (t4) counted; a budget of up to 62 is then plausible. I cannot express one further pixel turning 1 -- there is no event for growing an object -- so the manual leaves (63,62) and (63,63) unexplained in the frames where they are still 9."
    [probe: pending]

  theorem hud_is_two_tokens "the HUD holds two 3x3 tokens (rows 1-3, cols 1-3 and cols 5-7) and a 3-pixel underline at row 5 that sits under exactly one of them. Frames 0-4: token A is a colour-9 ring and is underlined, token B is a solid colour-1 block. Frame 5: token A is a colour-2 ring and unmarked, token B is a colour-9 ring and is underlined -- and the maze ring is back at cell (0,0). key(5) did all of that in one command. This reads either as 'attempt spent, position reset' or as 'objective cleared, next objective'; the two disagree about whether key(5) is to be hoarded or sought, and nothing observed separates them."
    [depends: key5_spends_token_a, key5_lights_token_b, key5_sends_ring_home  probe: pending]

  theorem colour_nine_collision "colour 9 paints four different things: the player ring, HUD token A (frames 0-4) and token B (frame 5), the selection underline, the bracket around maze cell (7,5), and the row-63 bar. One colour binds one object, so Player takes 9 and the 11 dynamic colour-9 HUD pixels of frames 0-4 plus the 6 underline pixels have no object and will be reported unexplained. I believe there are at least three distinct colour-9 entities; the arm cannot tell them apart, so I said so here instead of pretending."
    [probe: pending]

  theorem goal_is_the_bracketed_cell "maze cell (7,5), rows 50-54 x cols 44-48, is walled in colour 9 on its top, bottom and right edges and carries a lone colour-9 pixel at its centre (52,46); it is the only cell in the frame drawn that way, and it is drawn in the ring's own colour. I take it for the target. No transition witnesses this -- it is read off the static board -- so the goal section is a hypothesis the searcher will act on and the next win or non-win will settle."
    [probe: pending]

  theorem eight_marks_unknown "colour 8 fills maze cell (5,0), runs along the cell centres from (0,4) down to (5,4) and from (5,4) left to (5,0), and fills a 3x3 blob in the centre of cell (0,4). Not one of those pixels changed in six frames. Whether the marks are a route to trace, an obstacle, another agent's track, or decoration is untested, and my movement rules say nothing about them."
    [probe: pending]

  theorem coord_convention "every landmark above names the TOP-LEFT pixel of the intended 5x5 cell: cell_r0c0 = (8,14), cell_r1c0 = (14,14), exit_cell = (50,44). If the arm's Coord is instead an object's centroid, all three must shift by (+2,+2) to (10,16), (16,16), (52,46), and until a redraw is compared I do not know which."
    [probe: pending]

  theorem cascades_unseen "t2 returned 7 frames and t5 returned 9 for a single command, but only the last frame of each reached me, and `cascade single_frame` is the only value that compiles. Any intermediate motion -- a ring sliding cell by cell, for instance -- is invisible to this manual and would be evidence for grid_pitch_six."
    [probe: pending]
