# theory.dsl -- world observed for 5 transitions (RESET + ACTION1..ACTION5).
# The whole dynamic budget of this world is 73 cells and this manual accounts
# for every one of them. What it CANNOT do is move them: the only mover is a
# 24-cell rigid body that displaces six pixels at a time, and neither
# `moved` (one cell) nor `jumped` (one named cell, one instance) can say that.
# So this manual is deliberately rule-free. It names the world correctly and
# it lies about nothing; the dynamics live in `laws:` as probes.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Glyph2  { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  landmark spawn_center    # arc-cell: (10, 16)
  landmark socket_center   # arc-cell: (52, 46)
  landmark knob_center     # arc-cell: (10, 40)
  landmark gate_center     # arc-cell: (40, 16)
  landmark meter_head      # arc-cell: (63, 61)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t5 compress: 35]
  Glyph2  [segment: dynamic_colour_2 ev: t5 compress: 8]
  Spent   [segment: dynamic_colour_1 ev: t2,t4 compress: 2]
  Vacated [segment: dynamic_colour_5 ev: t2,t5 compress: 24]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

laws:
  invariant nine_count count(Glyph9) = 35 [status: observed]
  invariant board_static count(board) = 4023 [status: observed]

  theorem dynamic_census "Exactly 73 cells ever change and I can name all of them: 48 are the two occupied squares of a 5x5 body of colour 9 at rows 8-12 and rows 14-18, cols 14-18, minus its two centre cells (10,16) and (16,16) which are constant floor because the body is a donut with a one-pixel hole; 23 are a status panel at rows 1-5, cols 1-7; 2 are the right end of a 64-cell bar on row 63. 48+23+2 = 73, which closes the budget with nothing left over."
    [probe: pending]

  theorem panel_layout "The panel is two 3x3 icon slots, cols 1-3 and cols 5-7 of rows 1-3, each with a 1x3 underline at row 5. Cell (2,2) never varies and is background, so slot 1 is hollow in every frame; (2,6) does vary, so slot 2 was solid and became hollow. At frames 0-4: slot 1 = hollow colour 9 with the underline beneath it, slot 2 = solid colour 1, no underline. At frame 5: slot 1 = hollow colour 2, no underline, slot 2 = hollow colour 9 with the underline beneath it. I read this as two attempts or two lives with the underline marking the live one, but that reading is a guess; the layout is not."
    [probe: pending]

  theorem lattice_step "Both observed body positions have their top-left corner at (6R+2, 6C+2) -- rows 8-12 is R=1, rows 14-18 is R=2, cols 14-18 is C=2 -- and both observed displacements are exactly six pixels, never one. The maze walls agree: the void columns run cols 20-24 and cols 32-36 with single floor columns 19, 25, 31 between them. So this is a coarse grid of 6-pixel cells and one action moves the body one coarse cell. This is the largest compression available in the world and it is the one thing the rule language cannot state."
    [probe: pending]

  theorem key2_steps_down "ACTION2 at t2 displaced the body from rows 8-12 to rows 14-18, one lattice cell down. 49 cells changed = 24 vacated + 24 occupied + one meter cell, which is the exact arithmetic of a pure vertical slide of a donut whose hole keeps its column. Coverage 1/1: it is the only ACTION2 observed."
    [probe: pending]

  theorem key1_key3_are_noops_here "ACTION1 (t1) and ACTION3 (t3) changed not one pixel and did not touch the meter. Both are consistent with up and left being refused at the body's position: above rows 8-12 the grid is background, and left of cols 14-18 the grid is background past col 13. This manual encodes them by having no rule -- absence of a rule is the prediction 'nothing happens', and that prediction is correct on 2 of 5 transitions."
    [probe: pending]

  theorem key4_burned_a_meter_cell_without_moving "ACTION4 (t4) changed exactly one cell, (63,62) from 9 to 1, and moved nothing. ACTION2 also burned one, (63,63). ACTION5 burned none. So the row-63 bar depletes from the right end leftward, and it is charged by some actions and not others; a blocked move that costs nothing (t1, t3) and a blocked move that costs one (t4) are both in the record, and I cannot yet separate them. The candidate separator: at t4 the destination lattice cell (rows 14-18, cols 20-24) is interior void, while at t1 and t3 the destination is off the play area entirely."
    [probe: pending]

  theorem key5_returns_body_to_spawn "ACTION5 (t5) changed 71 cells = 48 for the body going from rows 14-18 back to rows 8-12, plus 23 for the whole panel flipping to its second configuration. It burned no meter cell. The body ends exactly where it started at t0, so I read ACTION5 as a respawn or attempt-reset rather than as the direction 'up', and the panel flip as that attempt being consumed. Both readings are unforced: a plain 'up' plus an unrelated panel tick fits the same pixels."
    [probe: pending]

  theorem cascade_is_animation "ACTION2 returned 7 frames and ACTION5 returned 9, while the two no-ops returned 1. Seven frames is exactly a six-pixel slide drawn one pixel per frame plus the settled frame. Only the last frame of a command is kept as a state, so the six-pixel step is atomic for prediction purposes and the intermediate frames carry no extra state."
    [probe: pending]

  theorem socket_is_the_conjectured_goal "Rows 49-55, cols 43-49 hold a static 7x7 outline of colour 9 that is open on its left side (col 43 is floor at rows 50-54) and carries a single dot at its centre (52,46). The body is 5x5 with a hole at its centre. If the body enters at rows 50-54, cols 44-48 -- lattice cell (8,7) -- the dot lands exactly in the hole. That is a lock and a key, and it is the only shape in the frame that fits the body. I have written NO goal section, because the world has reported NOT_FINISHED for every state and I have no evidence about winning at all; this is geometry, not a win condition."
    [probe: pending]

  theorem wire_and_gate "A static colour-8 structure runs from a 3x3 knob at rows 9-11, cols 39-41 (inside lattice cell (1,6)) down col 40 to row 40, then left along row 40 to a five-toothed comb filling rows 38-42, cols 14-18 -- which is lattice cell (6,2). The left corridor, cols 14-18, is the only column of floor that runs from the body's spawn down to the bottom room, and cell (6,2) is the one cell of it that is not plain floor. So the comb is plausibly a gate and the knob plausibly its switch, joined by the drawn cable. Nothing in five transitions tests this: the colour-8 cells have never changed."
    [probe: pending]

  theorem same_colour_conflation "Glyph9 is one type because the arm finds objects by colour and nothing else, so its instances are the 24 body cells AND the 8 panel-ring cells AND the 3 underline cells together. They are three different things and I believe they obey three different laws. Any future rule over `forall ?p in Glyph9` must carry a guard that isolates the body; the guard `not colored(above(?p), 0) and not colored(below(?p), 0) and not colored(leftof(?p), 0)` does exactly that in the current frame and in no way that I have proven will survive the body moving."
    [probe: pending]

  theorem four_cells_left_to_the_background "Four dynamic cells show background in the current frame -- (2,6), the hollowed centre of slot 2, and (5,1),(5,2),(5,3), the vacated underline -- and no colour-keyed object can own a background cell without owning all 3000 of them. I leave them to the background and say so rather than declare an arc-colour 0 object. At frame 0 the corresponding uncovered set is (5,5),(5,6),(5,7), which is the arm's count of 70 cells needing an owner out of 73 dynamic."
    [probe: pending]

  theorem no_rules_is_a_defect_not_a_position "This manual compiles to a predictor that says 'nothing ever changes'. That is right for t1 and t3 and wrong for t2, t4 and t5, costing about 48 cells on each of three frames. It is deliberate: the true transition is a rigid six-pixel displacement of a 24-instance body, `moved` moves one cell, `jumped` moves one instance to one landmark, and writing 24 landmarks and 24 jump rules per observed step would be a stored solution rather than a law. I would rather carry a known 3-frame drawing defect than a rule I know to be false."
    [probe: pending]
