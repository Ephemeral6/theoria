# theory.dsl -- world observed for 5 transitions (RESET + ACTION1..ACTION5).
# 73 cells in this world ever change and this manual accounts for every one.
#
# What changed this round, and why:
#   The surprise was replay_mismatch at t2 (ACTION2, 49 cells). It is the
#   defect the previous manual already declared: the body is a 24-cell rigid
#   donut and it slides SIX pixels, while `moved` moves one cell and `jumped`
#   moves at most two. That part I still cannot say, and I say so again below.
#   But two things I CAN say, and did not, are now rules:
#     - the row-63 meter burns its rightmost live cell on ACTION2 and ACTION4
#       (this is a genuine law, general, and it makes t4 exact);
#     - on ACTION2 the body vacates the cells it occupied and floor shows
#       through (24/24, general, grammar-safe). It draws half of the move.
#   Everything I refused to write is named in `laws:` with the exact text I
#   would have written, so it is a probe and not a silence.

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
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t5 compress: 37]
  Glyph2  [segment: dynamic_colour_2 ev: t5 compress: 8]
  Spent   [segment: dynamic_colour_1 ev: t0-t5 compress: 9]
  Vacated [segment: dynamic_colour_5 ev: t2,t5 compress: 24]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule meter_burn_key2 forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and below(?p) = wall and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key4 forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and below(?p) = wall and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key2_vacates_body forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and not colored(above(?p), 0) and not colored(below(?p), 0) and not colored(leftof(?p), 0) and not colored(rightof(?p), 0) then recolored(?p, 5)

laws:
  invariant nine_count_frame0 count(Glyph9) = 37 [status: counted]
  invariant board_static count(board) = 4023 [status: counted]

  theorem dynamic_census "Exactly 73 cells ever change and I can name all of them, from the engine's own cell list: 23 are a status panel at rows 1-5, cols 1-7; 24 are a 5x5 donut of colour 9 at rows 8-12, cols 14-18, minus its hole (10,16); 24 are the same shape at rows 14-18, cols 14-18, minus its hole (16,16); 2 are the right end of a 64-cell bar on row 63. 23+24+24+2 = 73, which closes the budget with nothing left over. At frame 0 those 73 split as 37 colour-9 cells, 9 colour-1 cells, 24 colour-5 cells and 3 background cells, and 37+9+24 = 70, which is exactly the arm's cells_needing_an_owner."
    [probe: pending]

  theorem meter_head_is_uniquely_addressable "The interior of the row-63 bar never changes, so it is board, and the ONLY Glyph9 instances with below(?p) = wall are (63,62) and (63,63). That is why meter_burn_key2 and meter_burn_key4 can name the head of the meter with two documented guards and no coordinates. meter_burn_key2 picks (63,63) by rightof(?p) = wall; meter_burn_key4 picks (63,62) by its right neighbour already being spent. If colored() on an off-board cell were to return true for 1, meter_burn_key4 would also ground on (63,63), where recolored(?p, 1) is a no-op -- so the rule is safe under either reading of off-board."
    [depends: meter_burn_key2, meter_burn_key4  probe: pending]

  theorem meter_depletes_rightward "ACTION2 burned (63,63) and ACTION4 burned (63,62), both 9 -> 1, so the bar empties from its right end leftward and is shared across actions. ACTION1, ACTION3 and ACTION5 burned nothing. I have one observation per action and therefore two rules rather than one law over a key domain; I do not know whether key(1)/key(3) are free because they are different actions or because they were refused moves. Candidate separator: at t4 the destination lattice cell is interior void, while at t1 and t3 the destination is off the play area entirely -- so 'a move attempt that stays on the play area costs one meter cell, whether or not it succeeds' is the hypothesis, and it predicts that key(1) and key(3) WILL burn a cell once the body is somewhere they can legally aim."
    [depends: meter_burn_key2, meter_burn_key4  probe: pending]

  theorem body_guard_isolates_the_donut "The arm finds objects by colour alone, so Glyph9's 37 frame-0 instances are three different things: the 24 donut cells, 8 panel-ring cells, 3 underline cells, 2 meter cells. The conjunction used by key2_vacates_body -- no neighbour in any of the four directions renders as background -- is true of all 24 donut cells and false of all 13 others, at BOTH observed body positions: the donut is embedded in colour-5 floor on every side (row 7 and row 13 and row 19 are floor across cols 14-18, col 13 and col 19 are floor), while every panel cell touches row 0, row 4, col 0 or col 4, and every meter cell has row 62 above it. This is the only separator I have and it is a property of the floor, not of the body, so it will fail the moment the body stands next to a background cell."
    [depends: key2_vacates_body  probe: pending]

  theorem the_move_is_six_pixels_and_the_dsl_cannot_say_it "Both observed body positions have their top-left at (6R+2, 6C+2) -- rows 8-12 is R=1, rows 14-18 is R=2 -- and the observed displacement is exactly six pixels. The maze agrees: void columns run cols 20-24 and cols 32-36 with single floor columns 19, 25, 31 between them. So the world is a coarse 6-pixel lattice and one action moves the donut one lattice cell. The event table tops out at two cells: moved(o, dir) is one, jumped(o, over, dir) is two. There is no event of any arity that displaces an instance by six, and no way to move 24 instances as a body. This is the largest compression in the world and it is inexpressible; cegis_miner reached the same wall from the other side and refused every track with 'the world does not narrate as one mover'."
    [probe: pending]

  theorem what_key2_vacates_body_deliberately_does_not_draw "key2_vacates_body draws the 24 cells the donut LEAVES and nothing the donut ARRIVES at, so after ACTION2 my manual shows an empty maze. That is a hole, not a lie: it takes t2 from 49 wrong cells to 24, and every cell it does draw is right. I know exactly which 24 it misses -- rows 14-18, cols 14-18 minus (16,16). I accept an avatar-less state model rather than the two alternatives, both of which I reject below."
    [depends: key2_vacates_body  probe: pending]

  theorem the_two_destination_rules_i_refused "First: 'rule key2_lands forall ?v in Vacated when act=key(2) then recolored(?v, 9)'. It is 24/24 on t2 and takes t2 to zero wrong cells, because the arm's Vacated instances happen to be exactly the 24 destination cells and nothing else. That is not a law, it is the t2 answer key wearing a forall -- it would be right again only for an ACTION2 pressed from spawn and wrong for every other ACTION2 in the game. Rejected as a stored solution. Second, and this one I want: 'rule key2_lands forall ?v in Vacated when act=key(2) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)' -- a floor cell whose cell six above is body-coloured becomes body-coloured. That IS general, it is 24/24 on t2, and it even leaves (16,16) alone for the right reason, because the cell six above it is the donut's hole. I did not write it because the grammar is published as 'cells -- EXHAUSTIVE: above(x) below(x) ...' without saying whether x may itself be a cell, and a parse error costs the entire manual, not one rule. PROBE: compile this one rule alone. If cell terms nest, it goes in next round and t2 replays exactly."
    [depends: key2_vacates_body  probe: pending]

  theorem key1_key3_are_silent_here "ACTION1 (t1) and ACTION3 (t3) changed not one pixel and burned no meter cell. Having no rule for them IS the prediction 'nothing happens', and that prediction is exactly right on both. Both are consistent with up and left being refused at rows 8-12, cols 14-18: above the donut is background past row 7 and left of it is background past col 13."
    [probe: pending]

  theorem key5_is_a_respawn_not_a_direction "ACTION5 changed 71 cells: 48 put the donut back at rows 8-12 from rows 14-18, and 23 flipped the whole panel. It burned no meter cell and it landed the body exactly where t0 started it. I read ACTION5 as respawn/next-attempt, and I have written no rule for it, because the honest rule needs the same six-pixel displacement plus a panel rewrite that includes three cells I cannot own. A plain 'up' plus an unrelated panel tick fits the same pixels and I cannot yet separate the two readings; the separator is cheap -- press ACTION5 from a position that is not one lattice cell below spawn."
    [probe: pending]

  theorem panel_layout "Two 3x3 icon slots at cols 1-3 and cols 5-7 of rows 1-3, each with a 1x3 underline at row 5. Frames 0-4: slot 1 is a hollow colour-9 ring with its underline lit, slot 2 is a solid colour-1 block with no underline. Frame 5: slot 1 is a hollow colour-2 ring with no underline, slot 2 is a hollow colour-9 ring with its underline lit. I read this as attempts or lives with the underline marking the live one and colour 2 marking a spent one, but that reading is a guess; the layout is not."
    [probe: pending]

  theorem three_cells_i_cannot_own "At frame 5 the cells (5,5),(5,6),(5,7) go 0 -> 9, and at frame 0 they are background, so no colour-keyed object owns them and none can: an arc-colour 0 object would claim all three thousand background cells. Symmetrically (5,1),(5,2),(5,3) and (2,6) end at background. Any future rule for ACTION5 therefore has a floor of 3 wrong cells. This is the arm's 70-of-73 figure and it is structural, not an oversight."
    [probe: pending]

  theorem socket_is_the_conjectured_goal "Rows 49-55, cols 43-49 hold a static 7x7 colour-9 outline, open on its left at col 43 rows 50-54, with a single dot at its centre (52,46). The donut is 5x5 with a hole at its centre. If the body enters at rows 50-54, cols 44-48 -- lattice cell (8,7) -- the dot lands exactly in the hole. That is a lock and a key and it is the only shape in the frame that fits the body. I have written NO goal section: every observed state is NOT_FINISHED, so I have zero evidence about winning, and this is geometry."
    [probe: pending]

  theorem i_cannot_write_the_goal_i_believe "Even granting the socket, `goal Glyph9.pos = socket_center` does not compile, because arc-instances: all means there is no instance named Glyph9 -- only Glyph9_r8c14 and its 36 siblings -- and there is no aggregate in the goal grammar that says 'some instance of this type is here'. count(Glyph9) = 37 is true of winning and losing states alike. So the manual has no goal and the planner cannot plan; that is a language limit I am recording, not a belief I am hiding."
    [probe: pending]

  theorem wire_and_gate "A static colour-8 structure runs from a 3x3 knob at rows 9-11, cols 39-41 (lattice cell (1,6)) down col 40 to row 40, then left along row 40 to a five-toothed comb filling rows 38-42, cols 14-18 -- lattice cell (6,2). Cols 14-18 is the only floor corridor running from spawn to the bottom room, and (6,2) is its one non-plain cell. So the comb is plausibly a gate, the knob plausibly its switch, and the cable is drawn between them. Nothing in five transitions tests this: no colour-8 cell has ever changed, which is why colour 8 is board and not an object."
    [probe: pending]

  theorem engines_gave_me_no_object_i_did_not_have "mdl_segmenter's own MDL is negative on both variants (-5042 and -17520 bits), so its segmentation loses to writing the pixels out; I take its tracks as hints only. Its obj3 is a 1006-cell colour-null blob that has swallowed the maze floor and the donut together and is not an object. zero_space returns THIN by its own verdict -- 5 transitions constrain rank 3 of 365 features -- and its single global law is a restatement of the 73-cell census, which I had already. No engine proposed anything I accepted as new."
    [probe: pending]
