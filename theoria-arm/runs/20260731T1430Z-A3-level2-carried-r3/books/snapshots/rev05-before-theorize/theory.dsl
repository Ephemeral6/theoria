# theory.dsl -- world observed for 6 states / 5 transitions
# (RESET + A1 A2 A3 A4 A5). 73 cells have ever changed; this manual names
# and owns all 73, and replays all 5 transitions cell-for-cell.
#
# WHAT THIS ROUND COST ME, AND IT COST ME EXACTLY ONE COMMENT:
#
#   THE SURPRISE. certify replays 4/5 and diverges at the ACTION5
#   transition on 23 cells -- the entire panel. World toggled it; my manual
#   did not. The cause is not physics. It is this line, inherited verbatim:
#
#       landmark spawn_probe  # arc-cell: carried, coordinates stripped
#
#   The grammar is explicit that a landmark without a real `# arc-cell:
#   (row, col)` lands at (0, 0). (0,0) is background, so the guard
#   `colored(spawn_probe, 5)` was FALSE in every state that has ever
#   existed, and all thirteen panel rules were dead text. The fix is
#   `# arc-cell: (8, 14)`. Nothing else in the manual was wrong about the
#   panel: with the landmark placed, every panel rule fires at t5 with the
#   coverage it claims, and the 23 cells come out right.
#
#   I record the shape of that mistake because it is the expensive kind: a
#   rule that cannot fire produces no clash, no crash and no ambiguity
#   report. It fails silently and only replay catches it. Any guard naming
#   a landmark is only as true as the comment beside the landmark.
#
#   THE OBSERVATION WINDOW SHRANK. The brief I was handed last round ran to
#   14 states; this one runs to 6, and the current frame is state 5 of a
#   fresh episode on the same level. Every `ev:` tag below has been
#   recomputed against the five transitions I can actually see. Four rules
#   whose only witnesses were t6..t13 have been REMOVED from `rules:` and
#   written out verbatim in `laws:`, because a coverage claim citing a
#   transition this brief does not contain is a lie the certifier cannot
#   catch. See the_five_rules_i_no_longer_have_a_witness_for.

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
  Vacated [segment: dynamic_colour_5 ev: t2,t5  compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t5 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5    compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

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

  theorem the_landmark_that_was_never_placed "This is the whole of the surprise and the whole of the repair. certify reported frame_mismatch at the ACTION5 transition, 23 cells wrong, and the 23 are exactly the panel: slot 1's eight ring pixels (manual 9, world 2), underline 1's three (manual 9, world 0), slot 2's nine (manual 1, world 9 and 0 at the centre), underline 2's three (manual 0, world 9). The manual predicted state A and the world produced state B. My thirteen panel rules each carry the guard `colored(spawn_probe, 5)`, and the landmark was declared `# arc-cell: carried, coordinates stripped`. That is not a coordinate. The grammar says a landmark without a parseable `# arc-cell: (row, col)` lands at (0,0), and (0,0) is background colour 0 in every frame this world has ever drawn, so the guard was false everywhere and all thirteen rules were unreachable text. Note what did NOT catch it: responsibility passed 0 unexplained, ambiguity passed 0 clashes, step crashed 0 times. A rule that can never fire is invisible to every check except replay. The landmark now reads `# arc-cell: (8, 14)`, the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. With it placed, t5 replays: 24 body-clear + 24 body-respawn + 23 panel = 71 cells, and the brief says 71 cells changed at t5."
    [depends: key5_slot1_dims, key5_slot2_centre_darkens, key5_underline2_lights  probe: passed]

  theorem the_observation_window_shrank_and_i_will_not_cite_what_i_cannot_see "The brief I answered last round ran to 14 states and 13 transitions; this one runs to 6 states and 5 transitions, and the current frame is state 5 of a fresh run on the same level -- same maze, same comb, same socket, body home at spawn, panel in state B, two meter cells burned. Everything below is re-tagged against t0..t5 and nothing cites t6..t13. Three concrete consequences. (1) Coverage numbers fell by exactly the factor of repeated presses: key2_body_leaves was 72/72 over three descents and is now 24/24 over one. (2) Four rules and one guard-justification lost their only witnesses; the rules are out of `rules:` and written verbatim in laws, the guard is kept and its reason stated in the next theorem. (3) The meter question REOPENED -- the transitions that refuted action-keying are gone. I am not pretending to knowledge whose evidence I no longer hold, and I am not throwing away beliefs that were once witnessed; the distinction between the two is exactly what `rules:` versus `theorem ... [probe: pending]` is for."
    [probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_cannot_test_it "Honest accounting: within t0..t5 the guard `colored(spawn_probe, 5)` has one positive witness (t5, body away, panel toggled) and NO negative one, because this window contains no ACTION5 press with the body at home. By the letter of no-entry-without-gain the atom is unearned here. I keep it for two reasons and label both. First, dropping it changes nothing on replay -- t5 is the only key(5) in the window and the guard is true there either way -- so it costs no coverage. Second, the body is at spawn RIGHT NOW, and without the guard the manual predicts a 23-cell panel toggle on the very next ACTION5, which a longer window I once held said four times over does not happen. Keeping it makes the manual predict silence, and silence is the prediction I want on the record. If a future ACTION5 at spawn DOES toggle the panel, this guard is refuted and the thirteen rules lose it in one edit."
    [depends: the_landmark_that_was_never_placed  probe: pending]

  theorem the_five_rules_i_no_longer_have_a_witness_for "The panel has two configurations and ACTION5 swaps them; this window witnesses only the A-to-B half, so the manual can only toggle one way. The B-to-A half is written out here so that the first effective ACTION5 from state B restores it in one edit, and so that nobody rediscovers it from pixels. Verbatim, guards included: 'rule key5_slot1_lights forall ?p in Glyph9 when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)'; 'rule key5_underline1_lights forall ?p in Glyph9 when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)'; 'rule key5_slot2_ring_resets forall ?s in Spent when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)'; 'rule key5_slot2_centre_resets forall ?s in Spent when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)'; 'rule key5_underline2_dims forall ?d in Dark when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) and colored(above(above(?d)), 9) then recolored(?d, 0)'. Also removed for the same reason: 'rule meter_burn_key2_next forall ?p in Glyph9 when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)', whose only witnesses were second and third key-2 presses this window does not contain. I STATE THE PRICE IN ADVANCE: the next ACTION2 that burns will cost me one wrong pixel in row 63, and the next effective ACTION5 from state B will cost me 23. Those two numbers, and no others, are what these removals buy in honesty."
    [depends: key5_slot1_dims, meter_burn_key2_rightmost  probe: pending]

  theorem the_meter_question_is_open_again_and_both_readings_are_five_for_five "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right end. In this window: (63,63) burned at t2 (ACTION2), (63,62) burned at t4 (ACTION4), nothing burned at t1 (ACTION1), t3 (ACTION3) or t5 (ACTION5). TWO readings fit all five transitions perfectly and this window cannot separate them. READING A, ACTION-KEYING: the bar burns iff the key is 2 or 4. It is expressible in the guard language, it is what the two rules above encode, and it scores 5/5. READING B, COMMAND PARITY: the bar burns on every even-indexed command and never on an odd one -- t2 and t4 burned, t1, t3 and t5 did not. It also scores 5/5 and it is INEXPRESSIBLE: the guard vocabulary has no command counter and the frame carries no phase, which is the same wall cegis_miner hit from its side when it reported 'no literal separates transition 1 from the positives'. A longer window I no longer hold contained ACTION5 presses that burned, which would kill reading A; I do not cite it as evidence, I cite it as the reason I expect reading B to win. The separating experiment is one command and the playbook ranks it first: the next command has index 6, which is EVEN, so pressing ACTION3 or ACTION1 there makes parity predict a burn at (63,61) and action-keying predict silence. My manual, as written, predicts silence -- so a single changed pixel in row 63 refutes my own two burn rules and I will replace them with nothing."
    [depends: meter_burn_key2_rightmost, meter_burn_key4_next  probe: pending]

  theorem the_world_may_not_be_a_function_of_the_drawn_frame "Carried forward as a belief, not as a proof, because the proof lived in transitions this brief no longer contains: two consecutive ACTION5 presses from pixel-identical grids produced different successors, one nothing and one a meter burn. If that observation was sound then there is at least one bit of hidden state, it flips on every command, and no guard in this language can read it because no guard can read anything that is not a pixel. Within t0..t5 I have no such pair and therefore no proof, which is why this is a theorem and not the headline it was last round. It matters operationally in one way only: if the parity reading wins, every burn rule I can write is an approximation with a known error rate, and I should say so once rather than rediscover it."
    [depends: the_meter_question_is_open_again_and_both_readings_are_five_for_five  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "New this round, and the brief hands it to me directly: cascade_lengths are 1, 7 and 9. The 7-frame command is t2, which moved the body six rows south; the 9-frame command is t5, which moved it six rows north and toggled the panel; every other command returned 1 frame. So a move is animated one row per internal frame and the world reports the whole animation for a single action, while `cascade single_frame` compares only the net effect -- and the net effect replays 5/5, so the animation costs me nothing and I do not model it. What it BUYS is a refutation. Under a slide-until-blocked reading, ACTION2 at spawn would have run the body south past rows 14-18 through rows 20-24 and 26-30 all the way to the comb; it stopped after exactly six rows with open floor beneath it. ONE PRESS IS ONE LATTICE CELL, 1/1, and that is the number every distance estimate in the playbook rests on."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_action_map_after_five_transitions "What is WITNESSED: ACTION2 IS DOWN, 1/1, six rows south, one lattice cell, at t2. What is NEGATIVE INFORMATION, and I state it as negative because that is all it is: at spawn, lattice (1,2), up is void and left is void while down and right are open floor, and ACTION1 did nothing there -- so ACTION1 IS NOT DOWN AND NOT RIGHT, leaving up, left or inert. At lattice (2,2), rows 14-18, up and down are open floor while left (cols 8-12) and right (cols 20-24) are both void, and ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN, leaving left, right or inert. ACTION5 at (2,2) moved the body one cell north to spawn. Fit those together: down is ACTION2; left and right must be ACTION3 and ACTION4 in an order I DO NOT KNOW; up is therefore ACTION1 or ACTION5. I cannot separate those two here, because both were only ever pressed where up was void (ACTION1 at spawn) or where up led home (ACTION5 from one cell below home) -- 'up' and 'return to start' are the same pixel from lattice (2,2). The clean separator is two cells of distance: descend twice to lattice (3,2) and press ACTION5. Up puts the body at (2,2); return-to-start puts it at (1,2). Nothing cheaper distinguishes them and nothing downstream needs them distinguished until then."
    [depends: key2_body_leaves, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_east_key_is_the_blocking_question_and_spawn_is_the_cell_that_answers_it "Everything I want is east: the knob sits in lattice (1,6) and the only route to it runs along lattice row 1, open floor from column 13 to column 43. ACTION3 and ACTION4 are left and right in unknown order, and the sole reason I do not know which is that both were pressed at lattice (2,2), where left and right are BOTH void -- a cell that could not distinguish them. The body now stands at spawn, lattice (1,2), where left is void and right is open floor. Press either there and the answer is unambiguous in the raw diff: the body steps six columns east, or it does not. I ALSO PREDICT THE PRICE so it cannot be mistaken for failure. Rows 8-12 columns 20-24 have never changed, so they carry no instances and my manual cannot draw them under any rule; a successful eastward step costs 24 wrong pixels there plus 24 at columns 14-18 that no rule of mine clears -- 48 in total, plus one if the bar burns. 48 or 49 wrong cells is the correct price of the first step onto fresh ground, and the round after, the same rule text draws it for free. Any other number refutes my reading of the lattice."
    [depends: the_action_map_after_five_transitions, only_visited_cells_have_instances  probe: pending]

  theorem the_one_command_that_settles_two_questions "Command index 6 is EVEN. Pressing ACTION3 there separates BOTH open questions at once and nothing else on the board does. On the meter: parity predicts a burn at (63,61), action-keying predicts silence because 3 is neither 2 nor 4, and my manual predicts silence -- so a one-pixel diff in row 63 refutes my own two burn rules and a zero-pixel diff saves them. On the map: if ACTION3 is right the body steps east and I have found the key that walks lattice row 1; if it does not move, ACTION3 is left and ACTION4 is right by elimination. The four possible diffs are 0, 1, 48 and 49 cells and every one of them is a different pair of answers, which is exactly the shape of experiment worth buying. Note what I deliberately did NOT choose: ACTION4 burns under BOTH meter readings and so separates nothing there, and ACTION1 at spawn is a pure parity test that says nothing about the map."
    [depends: the_east_key_is_the_blocking_question_and_spawn_is_the_cell_that_answers_it, the_meter_question_is_open_again_and_both_readings_are_five_for_five  probe: pending]

  theorem the_panel_is_a_two_phase_indicator_and_i_still_do_not_know_what_it_indicates "PROVEN in this window: it has exactly two configurations and one effective ACTION5 swaps them, 23 cells at t5; ACTION2 never touches them, 1/1 at t2. STATE A (frames 0-4): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. STATE B (frame 5, and the current frame): slot 1 is a hollow colour-2 ring, underline 1 dark 0; slot 2 is a hollow colour-9 ring with a dark centre, underline 2 lit 9. The lit underline follows the slot drawn in 9, so the underline reads as a selector and 9 reads as selected. What I DO NOT know is what is selected -- two bodies, two modes, two carried items, a counter shown mod two -- and I will not guess, because nothing downstream needs the meaning: the rules encode the SWAP and the swap is fully witnessed. An earlier manual read this panel as two lives and ranked every branch by a life that could not be spent; that is the failure mode I am refusing to repeat. One asymmetry for whoever gets more data: slot 1's idle form is a hollow ring while slot 2's idle form is a SOLID block, so the two slots hold different things, not two copies of one thing."
    [depends: key5_slot1_dims, key5_slot2_centre_darkens  probe: passed]

  theorem dynamic_census "Exactly 73 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three; slot 2's nine, centre included because (2,6) is 1 in A and 0 in B; underline 2's three. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 2 are the burned right end of row 63, (63,63) and (63,62). 23+24+24+2 = 73 = dynamic_cells. By frame-0 colour: 37 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 2 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, which is floor at frame 0), 3 colour-0 (underline 2). 37+9+24 = 70 = cells_needing_an_owner exactly, and the 3 colour-0 cells are the difference between 73 and 70. zero_space's cell list is the same 73 cells and its one global law restates this census."
    [probe: passed]

  theorem only_visited_cells_have_instances "Re-verified on this build: constant 4023 + dynamic 73 = 4096, and 37+24+9 = 70. The arm instances exactly the cells that have already changed, typed by their frame-0 colour, background colour included -- that last clause is what let `object Dark # arc-colour: 0 arc-instances: all` take three instances rather than three thousand, and the gap between dynamic_cells and cells_needing_an_owner is a reliable advance count of the colour-0 instances a declaration will get. Three consequences I keep paying for and keep accepting. The corridor ahead carries no instances, so the first step onto never-yet-changed ground costs 48 wrong cells and the round after that the same rule text draws them for free -- the manual heals one step behind the body. The next meter cell to burn, (63,61), is board and cannot be drawn even if I knew it would burn, which is why the parity reading would cost me a pixel at command 6 whatever I wrote. And the body CHANGES TYPE as it walks: its pixels are Glyph9 at rows 8-12, Vacated at rows 14-18, and will be Vacated again wherever it goes next, because all that floor renders 5 at frame 0."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth `below` is row 69. So `colored(<off-board>, k)` is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Nine of the fourteen rules above rest on this, and every row and column discrimination in the panel is built from it: the k-th `above` is off-board exactly when k exceeds the row, so row 1 is `above(above(?s)) = wall`, row 3 is `colored(above(above(?s)), 1)` which is false for row 1 because a colour test on an off-board cell is false, and row 2 is `above^3 = wall` conjoined with `colored(above(?s), 1)`. The same trick separates the three cells of slot 2's middle row by column: col 5 is `leftof^6 = wall`, col 6 is `leftof^7 = wall and colored(leftof(?s), 1)`, col 7 is `colored(leftof(leftof(?s)), 1)`, and the three are pairwise exclusive, which is why the ambiguity check reports 0 clashes. Not one rule uses `not`, deliberately: a manual once failed to reach the compiler at all and I will not spend a round discovering whether `not` before an equality atom parses. If a future desk wants the shorter forms, try one rule, not fourteen."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "A descent from rows 14-18 to rows 20-24 needs Vacated pixels going 9 to 5, which no rule of mine does -- key2_body_leaves is typed Glyph9 and only ever clears the spawn ring. The missing text, verbatim: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. It is inert in the present frame and I am fairly sure it is true. It stays out because nothing witnesses it: the body has descended once and that descent started at spawn. One ACTION2 from lattice (2,2) buys it. The same hole exists east-west and is worse, because there I do not even know the key: whatever the east key turns out to be, it needs a leaves-rule typed on whichever object owns the departing pixels and an arrives-rule typed on the destination, and neither can be written before the first eastward step is witnessed. This is the standing reason the first step in any new direction costs 48 cells and the second costs nothing."
    [depends: key2_body_arrives  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read from the current frame: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are open, C=6 holds the knob, C=7 is void; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2; R=8 is floor from col 13 to col 48, so C=2..7. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); the body has occupied only (1,2) and (2,2) in six frames."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed at t2: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in six frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open: colour 8 leaves the comb along row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41 with a stem pixel at (12,40), all inside lattice (1,6). Not one colour-8 pixel has moved in six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the five-key reading I hold -- 2 down, 3 and 4 left and right, and up being 1 or 5 -- accounts for every key I have pressed, which makes 6 and 7 more likely to be a click and a spare than more directions."
    [depends: the_action_map_after_five_transitions  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and thirty-six siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells do become dynamic on first entry, but `count(Vacated, color = 9) = 24` would then be true of the body standing anywhere it has already been, which is not a win -- a goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in lattice (8,7) once, the playbook steers by lattice distance, and `is_goal -> False` is the honest compilation."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -5042 and -17520 bits, so its segmentation loses to writing the pixels out and I owe it nothing structural. Its six tracks are a useful audit and every one of them is already inside a type I declared: obj0 (colour 9, 8 cells, 3x3, all 6 frames) is slot 1's ring; obj2 (colour 9, 3 cells, 1x3) is underline 1; obj1 (colour 1, 9 cells, present 5 frames) is slot 2 solid, absent from frame 5 exactly because state B recolours it; obj5 (colour 2, 8 cells, first seen at frame 5) is slot 1 dimmed -- independent corroboration, from an engine that knows nothing of my rules, that the panel toggled at t5 and that my landmark bug was a bug and not a physics error; obj4 is the whole 64-cell row-63 bar of which 2 cells are dynamic; obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring, a fair description of my board plus the one thing I care about most. THAT ABSENCE IS THE FINDING: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor. None of these gets a type of its own -- a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words: 5 transitions constrain rank 3 of 365 features, null space dimension 362, 'nearly every vector in it is a law that is true over these states and unfalsified rather than confirmed'. Its single global law is my census. cegis_miner's refusal remains the most useful sentence any engine has produced: 'the world does not narrate as one mover'. True of the arm, false of the world -- there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs me a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. ACTION3 FROM SPAWN AT COMMAND INDEX 6: my manual predicts ZERO changed cells. If exactly one cell changes and it is (63,61), parity wins, my two burn rules are coincidence-fits and I delete them next round in favour of silence. If 48 cells change, ACTION3 is right, the body is at lattice (1,3), and I owe two new rules that the transition itself witnesses. If 49 change, both at once. If zero change, ACTION3 is left AND action-keying survives, and ACTION4 is right by elimination. ACTION5 FROM SPAWN, if anyone presses it: I predict zero changed cells outside row 63, on the strength of the spawn_probe guard and nothing else in this window -- any panel change there refutes the guard and means the toggle is bound to something I have not found. ACTION2 FROM SPAWN: 24+24 cells at rows 8-24 and a burn at (63,61) that my manual will NOT draw, because meter_burn_key2_next is out for want of a witness; one wrong pixel is the advertised price of that removal."
    [depends: the_one_command_that_settles_two_questions, why_i_keep_the_spawn_probe_guard_on_a_window_that_cannot_test_it  probe: pending]
