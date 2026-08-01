# theory.dsl -- world observed for 6 states / 5 transitions
# (RESET, then ACTION1 ACTION2 ACTION3 ACTION4 ACTION5, indices t1..t5).
# 73 cells have ever changed; this manual names and owns all 73.
#
# WHY THIS ROUND EXISTS AND WHAT IT REPAIRS
#
#   The only surprise that fired is replay_mismatch with the reason
#   "theory.dsl is non-empty but generated/theory.py could not be loaded".
#   certify returned an EMPTY replay dict, an EMPTY responsibility dict and
#   unambiguous: null. Nothing ran. That is not a wrong manual, it is a
#   manual that does not compile, and there is exactly one line in the
#   previous text that the grammar calls a HARD compile error:
#
#       landmark spawn_probe  # arc-cell: carried, coordinates stripped
#
#   The spec is explicit: every landmark line MUST carry a trailing
#   # arc-cell: (row, col) comment, and a landmark the level cannot place
#   is a hard compile error. The previous manual even contained a theorem
#   named a_landmark_is_only_as_true_as_the_comment_beside_it which SAYS
#   the landmark reads (8, 14) -- while the landmark line itself said
#   prose. The prose was carried forward and the coordinate was not.
#   FIXED: the line now reads # arc-cell: (8, 14). Second parse risk
#   removed: the empty `goal:` section is gone entirely, since a manual
#   with no goal section at all is legal and an empty one is a guess.
#
#   THE OBSERVATION RECORD HAS BEEN ROLLED BACK AND I HAVE REWRITTEN THE
#   WHOLE MANUAL TO IT. The store now reports 6 states, 5 transitions, 73
#   dynamic cells, 4023 constant cells, 2 burned meter cells. The previous
#   manual was written against 34 states, 87 dynamic cells, 16 burned meter
#   cells. 87 - 73 = 14 and 16 - 2 = 14: this record is a strict PREFIX of
#   that history, cut at state 5. So every `ev:` and every `cov:` in the
#   old text cited transitions this desk cannot see. All of them are
#   rewritten to what the record actually contains, and every rule whose
#   only witnesses lay past t5 has been REMOVED from rules: and parked in
#   laws: with its text intact. See the_record_is_a_prefix and
#   the_rules_i_have_no_witness_for_in_this_record.
#
#   WHAT THAT BUYS: this manual should replay 5/5 exactly. t1 and t3 are
#   no-ops it draws as no-ops, t2 is 49 cells it draws as 49, t4 is 1 cell
#   it draws as 1, t5 is 71 cells it draws as 71. There is no priced-in
#   miss anywhere in this record. The old manual advertised 31/33; this one
#   advertises 5/5 and will be caught out at once if that is wrong.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Dark    { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  landmark spawn_probe  # arc-cell: (8, 14)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t5 compress: 37]
  Vacated [segment: dynamic_colour_5 ev: t2,t5 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key1_inert_at_spawn forall ?p in Glyph9 [ev: t1 cov: 1/1]
    when act=key(1) and colored(spawn_probe, 9) and colored(?p, 9) and colored(above(?p), 5) and colored(leftof(?p), 5) and colored(rightof(?p), 9) then recolored(?p, 9)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

laws:
  invariant glyph9_instances count(Glyph9) = 37 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4023 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 2 [status: counted]

  theorem why_theory_py_did_not_exist "The whole of this round's surprise. certify returned replay {}, responsibility {} and unambiguous null -- not a divergence, an absence. theory.dsl was non-empty and generated/theory.py could not be loaded, so the manual had no executable form and NOTHING downstream had a predictor. Exactly one line in the previous text is a documented HARD compile error: landmark spawn_probe carrying the comment arc-cell: carried, coordinates stripped, where the grammar demands arc-cell: (row, col) and calls a landmark the level cannot place a hard error. The manual even contained a theorem asserting the landmark reads (8, 14) -- the belief survived the rewrite and the coordinate did not. The line now reads arc-cell: (8, 14), which is the top-left pixel of the spawn ring, rendering 9 while the body is home and 5 the moment it is anywhere else. Second parse hazard removed at the same time: the previous manual carried a `goal:` header with an empty body, and the spec sanctions NO goal section rather than an empty one. THE LESSON THAT GENERALISES: a compile failure is invisible to every other check in this rig. Responsibility, ambiguity and step-crash counts all reported cleanly in earlier rounds while thirteen rules pointed at (0,0); this time not even those ran. Before believing any certify number, check that certify had something to run."
    [depends: key1_inert_at_spawn, key3_inert_below_spawn  probe: pending]

  theorem the_record_is_a_prefix_and_every_count_is_restated "The store I am given reports 6 states, 5 transitions, dynamic_cells 73, cells_needing_an_owner 70, constant_cells 4023, two burned meter cells. The manual I inherited was written against 34 states, 87 dynamic cells and 16 burned meter cells. The difference is 14 in both places, which is exactly the number of extra meter cells that had burned, so THIS RECORD IS A STRICT PREFIX OF THAT HISTORY, cut at state 5, and the current frame is that history's state 5. I have rewritten every ev: and every cov: to the transitions I can actually see, and I have deleted from rules: every rule whose only witnesses lay past t5. WHAT I AM GIVING UP AND SAYING SO: the inherited text reports things I now cannot re-derive -- thirteen descents, thirteen panel toggles, four presses of ACTION5 at spawn that witnessed its silence, and a discriminating experiment at indices 30 to 33 that killed the action-keyed reading of the meter. I do not treat my own prior prose as evidence in a book whose first rule is that every entry carries the transitions that witness it. I carry those claims as named beliefs below, flagged as unwitnessed HERE, and I let this record decide them again. Where the prefix and the prior text disagree about what to write, the prefix wins."
    [depends: dynamic_census  probe: passed]

  theorem the_rules_i_have_no_witness_for_in_this_record "Six rules were removed from rules: this round because their witnesses lie past t5. Their text is kept verbatim so the transition that witnesses one costs a paste and not a rediscovery, and their absence is PRICED so it cannot be read as a surprise. (1) THE PANEL TOGGLING BACK, five rules: key5_slot1_lights over Glyph9 when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9); key5_underline1_lights over Glyph9 with colored(?p, 0) and above-six equals wall then recolored(?p, 9); key5_slot2_ring_resets over Spent with colored(?s, 9) then recolored(?s, 1); key5_slot2_centre_resets over Spent with colored(?s, 0) then recolored(?s, 1); key5_underline2_dims over Dark with colored(?d, 9) then recolored(?d, 0). The panel is now in configuration B and no rule of mine fires on it, so MY MANUAL PREDICTS THE PANEL IS FROZEN. If the next effective ACTION5 toggles it back I am wrong by exactly 23 pixels, and that is the cost of obeying rule 2 rather than my own memory. (2) THE SECOND METER BURN UNDER KEY 2: meter_burn_key2_next over Glyph9 when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1). Only the rightmost cell has ever burned under key 2 in this record. If ACTION2 is pressed again my manual burns nothing and is wrong by one pixel. Both prices are stated before the press, not after."
    [depends: key5_slot1_dims, meter_burn_key2_rightmost  probe: pending]

  theorem the_two_meter_readings_are_not_separated_here_and_the_next_command_separates_them "Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right; it reads 9 through col 61 and 1 at cols 62 and 63, TWO burns in five commands. The burns were at t2 (ACTION2) and t4 (ACTION4) and at no other index. READING A: the bar burns iff the key is 2 or 4. READING B: the bar burns iff the command index is even. Over t1 to t5 the two are numerically IDENTICAL -- every even index carried an even key -- so this record cannot tell them apart, and I say that rather than pretend my rules settle it. My two burn rules encode reading A, for the only reason available inside this grammar: reading B cannot be written here at all, because the guard language reads pixels and the action name and there is no command counter. THE SEPARATOR IS FREE AND IT IS THE NEXT COMMAND. The next index is 6, EVEN. An ODD key at an even index splits them: reading A predicts no burn, reading B predicts (63,61) goes to 1. ACTION3 and ACTION4 are the two keys I want to press anyway for the direction question, and ACTION3 is odd, so ONE PRESS OF ACTION3 BUYS BOTH ANSWERS. The inherited text says this experiment was run at indices 30 to 33 and reading B won; I do not hold that as evidence, but I do note that if reading B is right my burn rules are a mis-attribution that happens to draw every burn in this record, and I would keep them anyway as the shortest expressible shadow of the true law."
    [depends: meter_burn_key2_rightmost, meter_burn_key4_next  probe: pending]

  theorem the_action_map_after_five_transitions "WITNESSED: ACTION2 IS DOWN. t2 moved the body six rows south, from lattice (1,2) to (2,2), one lattice cell, 1/1. ACTION5 carried it back north from (2,2) to (1,2), 1/1. Everything else is NEGATIVE information and I state it as negative. AT SPAWN (1,2) the open neighbours are DOWN and RIGHT only -- lattice (0,2) at rows 2-6 cols 14-18 is void and lattice (1,1) at cols 8-12 is void, while (1,3) at cols 20-24 and (2,2) at rows 14-18 are floor. ACTION1 was pressed there and moved nothing, so ACTION1 IS NEITHER DOWN NOR RIGHT. AT (2,2) the open neighbours are UP and DOWN only -- (2,1) and (2,3) are void, while (1,2) had just been vacated and (3,2) at rows 20-24 is floor. ACTION3 was pressed there and moved nothing; ACTION4 was pressed there and moved nothing but a meter cell. SO NEITHER ACTION3 NOR ACTION4 IS UP OR DOWN, and if either is a direction key at all it is HORIZONTAL. That is the sharpest thing this record says: the east key, if it exists, is ACTION3 or ACTION4, and one press from spawn -- where east is three lattice cells of unbroken floor -- names it whichever way it answers. ACTION5 is up, or return-to-start, or undo; all three agree on the only press ever made. The conventional mapping for this action family agrees with left/right for 3 and 4, which is a prior and not evidence."
    [depends: key2_body_arrives, key5_body_respawns, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem silence_is_a_prediction_and_three_of_my_five_spawn_silences_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the five keys AT SPAWN, which is where the body stands. key(2): moves 48 body cells and burns one meter cell, WITNESSED at t2. key(1): inert, WITNESSED at t1, zero cells. key(3), key(4), key(5): my manual predicts ZERO CELLS AND HAS NO WITNESS FOR ANY OF THEM AT THIS CELL -- 3 and 4 were pressed only from one cell south, and 5 was pressed only from one cell south. THREE FORGED DEATH CERTIFICATES out of five, and two of them are attached to the keys that the elimination argument says must be horizontal. This is the cheapest unclaimed information on the board and it is claimed by pressing a key, not by writing a rule."
    [depends: the_action_map_after_five_transitions, key1_inert_at_spawn  probe: pending]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "Twenty-three cells in the top-left corner, in two 3x3 seats with a 1x3 underline beneath each, and ONE toggle witnessed, at t5, all 23 cells at once. CONFIGURATION A, states 0 to 4: slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B, state 5 and the current frame: slot 1 a hollow colour-2 ring with dark underline, slot 2 a hollow colour-9 ring with dark centre and lit underline. Slot 1's centre (2,2) is colour 0 in BOTH configurations, which is why it is board and not an instance; slot 2's centre (2,6) is 1 in A and 0 in B, which is why it is. mdl_segmenter corroborates by frame index without having seen my rules: obj0 is a colour-9 eight-cell 3x3 present in all six frames, obj1 a colour-1 nine-cell 3x3 present in frames 0-4 only, obj5 a colour-2 eight-cell 3x3 first seen at frame 5, obj2 a colour-9 1x3 present in all six. The hollow ring and the lit underline do not appear and vanish, they TRAVEL between the two seats: one marker, two seats, colour 9 marks the occupied seat. WHAT THE SEATS HOLD IS UNKNOWN AND I WILL NOT GUESS. I cannot model the marker as a mover either -- the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring crossing four columns is not a move, and eight recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot2_row1_lights  probe: passed]

  theorem the_panel_guard_is_a_correlation_in_this_record "All eight panel rules carry colored(spawn_probe, 5), which reads cell (8,14) renders floor, which reads the body is not at spawn. In this record there is exactly ONE panel toggle and it happened on the one ACTION5 ever pressed, from lattice (2,2). So `key(5) was pressed` and `the body is away from spawn` are the SAME single event here and the conjunct has no discriminating witness -- by rule 3 it explains no pixel this record can show me. I keep it, and I name the reason rather than dress it up: without it my manual predicts that ACTION5 at spawn, which is where the body stands right now, repaints 23 panel cells, and I have no evidence for that either. The inherited text records that exact deletion being made, being answered by four presses of ACTION5 at spawn with the panel unmoved, and being reversed. I cannot cite those four presses. I can note that the cheap version of the same experiment is available: press ACTION5 at spawn once. Panel still means the guard is earned; panel moves means eight rules are guarded on the wrong thing. A second confound is worth naming before it costs me: the single positive had the body at ONE cell, (2,2), so a guard reading `the body is at (2,2)` fits identically and differs only at a third lattice cell the body has never occupied."
    [depends: key5_slot1_dims, the_panel_is_a_marker_that_alternates_between_two_slots  probe: pending]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9. ACTION2 from configuration A returned SEVEN frames at t2. ACTION5 returned NINE at t5. All three no-ops returned one. My semantics say cascade single_frame, so only the net change is compared and up to eight intermediate frames per command are discarded unread -- I record that as a limitation of my own manual, not of the world. The channel is free and it is the only hint that the panel does anything besides display: the inherited text claims ACTION2 takes seven frames from configuration A and NINE from configuration B, 13/13. That is a LIVE PREDICTION here and it costs nothing to collect, because the panel is now in configuration B and the frame count is printed in every diff. If the next ACTION2 returns nine frames the claim survives; if it returns seven, the panel is cosmetic after all."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: pending]

  theorem dynamic_census "Exactly 73 cells have ever changed and every one has an owner. 23 ARE THE PANEL: slot 1's eight ring pixels at rows 1-3 cols 1-3 excluding centre (2,2) which is colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in A and 0 in B; underline 2's three at row 5 cols 5-7. 24 ARE THE SPAWN RING, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 ARE THE SAME RING SIX ROWS SOUTH, rows 14-18 cols 14-18 minus its aperture (16,16). 2 ARE THE BURNED RIGHT END OF ROW 63, cols 62 and 63. 23+24+24+2 = 73 = dynamic_cells, and it agrees cell for cell with zero_space's enumerated support. BY FRAME-0 COLOUR: 37 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 2 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 37+9+24 = 70 = cells_needing_an_owner exactly, and 4096-73 = 4023 = constant_cells exactly."
    [probe: passed]

  theorem the_dark_type_may_receive_no_instances_and_i_would_rather_be_told "A risk in my own declarations, named in advance. cells_needing_an_owner is 70 while dynamic_cells is 73, and the three missing cells are exactly the three whose frame-0 colour is 0, the background: underline 2 at row 5 cols 5-7. That gap is consistent with the arm treating background-coloured cells as board-explained and refusing to instance them. If so, `object Dark ... arc-colour: 0 arc-instances: all` yields ZERO instances, key5_underline2_lights grounds on nothing, and three pixels of t5 come back unexplained in the responsibility report. I declare Dark anyway, because the alternative is to leave three pixels of an observed change with no owner at all, and because a responsibility report naming those three cells tells me the arm's rule in one round. If they come back unexplained the repair is not another type on colour 0 -- two types on one colour are indistinguishable to an arm that looks objects up by colour and nothing else -- it is to accept the three cells as board and delete the rule."
    [depends: dynamic_census, key5_underline2_lights  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_first_step_east_is_where_it_will_show "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4023 + dynamic 73 = 4096. A cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This prices the first eastward step exactly. Lattice (1,3) is rows 8-12 cols 20-24; not one of those 25 cells has ever changed, so 24 arrival pixels are undrawable NO MATTER WHAT RULE I WRITE. The 24 departure pixels at the spawn ring are instances, but no east-leaves rule exists and none can be written before an east press witnesses one. So the first step east costs 48 wrong pixels, plus one more at (63,61) if the meter turns out to be command parity. THE SECOND step east costs 24, the third costs 0. I state this now so that a refutation whose divergence set is exactly rows 8-12 cols 20-24 is read as the advertised price of new ground and not as a defect in the rules. One further consequence worth knowing before it confuses someone: THE BODY CHANGES TYPE AS IT WALKS. Typing is by frame-0 colour, the body was colour 9 at rows 8-12 and floor was colour 5 everywhere else, so the same physical mover is Glyph9 at spawn and Vacated one cell south."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem i_cannot_manufacture_an_instance_on_a_cell_that_has_never_changed "Recorded because the same repair will tempt the next desk. To draw the meter's leading edge before it burns I would need an instance on a board cell. arc-instances: all instances every cell of that colour THE BOARD CANNOT EXPLAIN, and a never-varying cell is precisely what the board explains, so it gets none. The tempting workaround is a second declared type on colour 9 without arc-instances, hoping the arm seats one instance somewhere useful; I reject it, because the arm looks objects up by colour and nothing else, so a second colour-9 type is indistinguishable from Glyph9, its seat is unspecified, and any cell it landed on would be claimed twice -- the rule-5 error the grammar warns about in as many words. A landmark cannot help either: landmarks are cells and every event in this language takes an object as its first argument. The hole is a property of the arm and it is permanent for this level."
    [depends: dynamic_census  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "key2_body_leaves grounds on meter instances at row 63 whose sixth-below is row 69, and the inherited certify runs reported zero step crashes, so colored(off-board, k) is FALSE rather than an exception, and `<cell> = wall` is the sanctioned positive test. Eight panel rules rest on this and every row and column discrimination in the panel is built from it. The k-th above is off-board exactly when k exceeds the row: row 1 is above-twice equals wall; row 3 is a colour test on above-twice, false for row 1 precisely because a colour test on an off-board cell is false; row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row BY COLUMN: col 5 is leftof-six equals wall; col 6 is leftof-seven equals wall with a colour test on leftof-once; col 7 is a colour test on leftof-twice. The three are pairwise exclusive, which is why no ambiguity clash has ever been reported on them. Not one rule in this manual uses `not`, deliberately. THIS CLAIM IS NOW UNVERIFIED, because certify could not load a predictor this round, so it must be re-confirmed by the first run that actually executes."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated over several internal frames and the world reports the whole animation for a single action. The refutation that matters: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor. ONE PRESS IS ONE LATTICE CELL, 1/1 in this record, and every distance in the playbook rests on it. With one witness this is the weakest load-bearing claim in the manual and the second ACTION2 press confirms or destroys it for free."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read pixel by pixel out of the CURRENT frame. R=1, rows 8-12, is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; C=7 does not exist in that band, cols 44 onward being void. R=2, rows 14-18, is floor at cols 13-19 and 25-31 only, so C=2 and C=4. R=3, rows 20-24, is floor cols 13-31, so C=2,3,4. R=4 and R=5, rows 26-30 and 32-36, are floor only at cols 13-19, so C=2. R=6, rows 38-42, is the comb: 23 of the 25 pixels at cols 14-18 render colour 8 and only (39,14) and (41,14) are floor, so nothing there is enterable. R=7, rows 44-48, is C=2, plus a fragment of floor at row 48 cols 42-50 that is one row deep and cannot hold a 5x5 body. R=8, rows 50-54, is floor from col 13 to col 48, so C=2 through C=7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across lattice column 2 and separator col 37 is floor across R=1, so LATTICE COLUMN 2 IS CONTINUOUS FROM R=1 TO R=8 APART FROM THE COMB, and LATTICE ROW 1 IS CONTINUOUS FROM C=2 TO C=6. Spawn is (1,2); in six frames the body has occupied exactly TWO cells, (1,2) and (2,2)."
    [depends: key2_body_arrives  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything. key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor -- so the centre is never repainted. Witnessed at t2: (16,16) stayed 5 while all 24 of its neighbours turned 9, and it is absent from the dynamic-cell census for exactly that reason. This matters because it is the only reading under which the winning cell is enterable at all: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor in the current frame, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell against the current frame. A colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 49-55. Rows 49 and 55 are separator rows and cols 43 and 49 are separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west wall at col 43 left as FLOOR. Inside it, rows 50-54 cols 44-48 are floor except one colour-9 pixel at the exact centre (52,46). Outside it, col 50 rows 49-56 is a one-cell strip of floor leading nowhere. Overlay the body standing in (8,7) -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my inventing a goal predicate: the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in six frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, and C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and every pixel is re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem pixel at (12,40), colour 8 filling col 40 from row 12 down to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18. It is ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell -- the eight knob pixels other than its centre, plus the stem at (12,40) -- so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: drive the body into a colour-8 cell and my manual predicts it stays put, and the world says otherwise in one command. C=2 to C=5 is THREE lattice cells of eastward travel and C=2 to C=6 is four, every step on floor that R=1 shows open. Five commands spent and none has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1 through ACTION5 plus RESET; the alphabet is ACTION1 through ACTION7. Two commands are entirely unconstrained, and in this family one is normally a click carrying coordinates. That matters here, because the knob is a 3x3 target the body appears unable to stand on and a click is the shape of interaction that presses it. I CANNOT WRITE SUCH A RULE: the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT -- comb pixels going 8 to 5 -- and never its precondition. With no witness for key(6) or key(7), no rule may name them, so they sit outside this manual's alphabet."
    [probe: pending]

  theorem the_goal_section_is_absent_on_purpose "There is no goal: section, which compiles is_goal to False, and I would rather have no goal than a goal true in the wrong states, because the latter stops a planner at its first step. Every candidate fails on this arm. `Cart.pos = exit_cell` needs one named instance and arc-instances: all gives me Glyph9_r8c14 and thirty-six siblings, none of them the body as such. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but their frame-0 colour is 5 so they would type as Vacated, indistinguishable from the 24 Vacated cells at rows 14-18 -- and count(Vacated, color = 9) = 24 is exactly the state of the body standing one cell south of spawn, which is not a win. count(Glyph9, color = 5) = 24 is true of every state in which the body is anywhere but home. A Wire type on colour 8 would have zero instances because every colour-8 cell is constant, so count(Wire) = 0 would be true at RESET. I name the price plainly: no plan terminates, and nothing ranks one command above another except what the playbook says."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter chose connected_components(4) with split_by_color false and reports NEGATIVE gain on both variants, -5042 bits at 6 tracks and -17520 at 17, so on this record its own script is longer than writing the pixels out and I owe it nothing structural. Its tracks still corroborate the panel by frame index, and that is what I took: obj0 colour-9 eight cells 3x3 across all six frames, obj1 colour-1 nine cells present frames 0-4, obj5 colour-2 eight cells first seen at frame 5, obj2 colour-9 1x3 across all six -- the ring and the underline travelling between two seats rather than appearing and vanishing. obj4 is the whole 64-cell bar of which 2 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. cegis_miner refuses on every track -- four refusals naming recolor and vanish narrations and one absent object -- and its verdict, the world does not narrate as one mover, is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours. zero_space self-reports THIN in its own words -- 5 transitions constrain rank 3 of 365 features, null space dimension 362, nearly every vector in it a law true over these states and unfalsified rather than confirmed -- and its single global law enumerates exactly my 73 dynamic cells, which is the census and nothing more."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body is at spawn, the panel is in configuration B, two meter cells are burned, the next command index is 6. ACTION3 AT SPAWN, which is what the playbook asks for: my manual predicts ZERO cells changed and has no witness for that at this cell. If the body steps east I am wrong by 48 pixels, ACTION3 IS EAST and the map closes; if only (63,61) burns I am wrong by one pixel, the meter is command parity rather than key-driven, and ACTION4 is east by elimination; if nothing at all changes then ACTION3 is not a direction key here, ACTION4 is east by elimination, and the key-driven meter reading survives. THREE OUTCOMES AND ALL THREE ARE INFORMATIVE, which is the property I am buying. ACTION4 at spawn: the same experiment with the labels swapped, except that a burn there is uninformative about the meter because 4 is an even key. ACTION2 at spawn: 48 body cells I draw correctly, plus one burn I do NOT draw since meter_burn_key2_next is out of the manual -- one wrong pixel, one free datum in the cascade length, and no new witness. ACTION5 at spawn: my manual predicts nothing and has no witness; if the panel moves, eight rules are guarded on the wrong atom and I want to know. ACTION1 at spawn: witnessed silence, nothing bought, the only strictly worthless press on the board."
    [depends: the_two_meter_readings_are_not_separated_here_and_the_next_command_separates_them, silence_is_a_prediction_and_three_of_my_five_spawn_silences_are_forged  probe: pending]
