# theory.dsl -- world observed for 10 states / 9 transitions
# (RESET + A1 A2 A3 A4 A5 A2 A5 A2 A5). 75 cells have ever changed; this
# manual names and owns all 75.
#
# WHAT THE FOUR REFUTATIONS COST AND WHAT THEY BOUGHT
#
#   The window grew from 6 states to 10 and the four new commands were
#   A2 A5 A2 A5 -- the body oscillating between lattice (1,2) and (2,2).
#   Four probe_refutations fired and ALL FOUR are the same two holes, both
#   of which the previous manual named in advance and priced in advance:
#
#   HOLE 1, 23 cells, transition t7. The panel has two configurations and
#   the previous window only ever witnessed the A->B half, so the five
#   B->A rules sat in `laws:` as preserved text. t7 is the first B->A
#   toggle. The manual, having no rule that fires on a B-coloured panel,
#   predicted no panel change at all and was wrong on exactly the 23 panel
#   cells -- the advertised price, to the cell. The five rules are now
#   witnessed and are back in `rules:`.
#
#   HOLE 2, 1 cell, transitions t6 and t8. `meter_burn_key2_next` had been
#   removed for want of a witness; t6 burned (63,61) and t8 burned (63,60).
#   Advertised price one wrong pixel per burn, paid twice, rule restored.
#
#   The four observed hashes are all distinct while the manual's two
#   predictions repeat (25cac.../9bb17...) because the manual was a 2-cycle
#   -- panel frozen in B, meter frozen at two burns -- while the world is
#   an open trajectory. That is the exact signature of a missing toggle
#   plus a missing counter, and nothing else needed diagnosing.
#
#   WHAT NOTHING FIXES: the NEXT burn is at (63,59), a cell that has never
#   changed and is therefore board, so no object owns it and no rule of
#   mine can draw it. Every burn costs one wrong pixel in the round it
#   happens and zero pixels forever after. See the_manual_heals_one_step_behind.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t9 compress: 39]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t8,t9 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8 cov: 72/72]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8 cov: 72/72]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8 cov: 2/2]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9 cov: 72/72]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9 cov: 72/72]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 16/16]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 39 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4021 [status: counted]

  theorem the_four_refutations_were_two_holes_and_both_were_advertised "P-01 and P-03 are ACTION2 presses, P-02 and P-04 ACTION5 presses, and the manual's predictions repeat (25cac.../9bb17...) while the world's four answers are all distinct. That pattern is the whole diagnosis: my compiled manual was a two-state cycle -- spawn and one-cell-south, panel frozen in configuration B because no rule of mine fires on B-coloured panel pixels, meter frozen at two burns because meter_burn_key2_next had been struck for want of a witness -- and the world is an open trajectory whose panel toggles B->A->B and whose bar burns twice more. Two holes, both named in the previous manual's own laws, both priced in advance: 23 cells for the missing B->A half and one pixel per unwitnessed burn. Both prices came in exactly. Repair: the five B->A rules move from prose back into `rules:` with t7 as their witness (8+3+8+1+3 = 23), and meter_burn_key2_next returns with t6,t8 as witnesses. Nothing else in the manual was implicated -- key2_body_leaves, key2_body_arrives, key5_body_clears and key5_body_respawns each gained two more full-coverage witnesses and not one contradiction. I record the shape of this because it is the CHEAP kind of failure: a manual that says in advance what it cannot draw and what that will cost is refuted at a price it already quoted, and the repair is a paste, not a rethink."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, meter_burn_key2_next  probe: passed]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over three toggles now, t5 t7 t9, 23 cells every time, and ACTION2 has never touched a panel pixel in three presses. CONFIGURATION A (states 0-4, 7, 8): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B (states 5, 6, 9, and the current frame): slot 1 is a hollow colour-2 ring with underline dark; slot 2 is a hollow colour-9 ring with a dark centre and its underline lit 9. mdl_segmenter, which knows nothing of my rules, corroborates this independently and adds a reading I had not seen: its obj0 is a colour-9 8-cell 3x3 present in ALL TEN frames and its obj2 a colour-9 1x3 present in all ten, and it narrates six MOVE events -- because the hollow 9 ring and the lit underline do not appear and vanish, they TRAVEL between slot 1 and slot 2, three toggles times two objects. So the panel is one marker with two seats, not two independent lamps, and colour 9 marks the occupied seat. What is still unknown is what the seats hold. I will not guess; nothing downstream needs it, because the rules encode the swap and the swap is fully witnessed in both directions. I cannot model it AS a moving marker: the arm gives one instance per cell and `moved(o, dir)` moves one cell, so an eight-pixel ring travelling four columns is not expressible as a move and the ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_still_cannot_test_it "Unchanged in kind, stronger in count: the guard `colored(spawn_probe, 5)` now has THREE positive witnesses (t5, t7, t9 -- body away, panel toggled) and STILL NO NEGATIVE ONE, because ACTION5 has never once been pressed with the body at home. Every ACTION5 in this window immediately followed an ACTION2, so 'ACTION5 was pressed' and 'the body was away from spawn' are the same event ten times over and no guard can be credited over the other. By the letter of no-entry-without-gain the atom is still unearned. I keep it because dropping it changes no replay and because the body is at spawn RIGHT NOW: with the guard, my manual predicts SILENCE for an ACTION5 pressed here; without it, it predicts a 23-cell toggle. Silence is the prediction I want on the record, and one press refutes it or confirms it outright."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots  probe: pending]

  theorem the_meter_question_after_nine_transitions_and_why_it_is_still_open "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right. Four burns: (63,63) at t2, (63,62) at t4, (63,61) at t6, (63,60) at t8. Five silences: t1, t3, t5, t7, t9. READING A, ACTION-KEYING -- burns iff the key is 2 or 4 -- scores 9/9 and is what the three burn rules encode. READING B, COMMAND PARITY -- burns iff the command index is even -- also scores 9/9. NINE TRANSITIONS CANNOT SEPARATE THEM, and now I know exactly why: every command so far has used a key whose parity equals its own index's parity (indices 2,4,6,8 used keys 2,4,2,2; indices 1,3,5,7,9 used keys 1,3,5,5,5). The two readings are numerically identical on that diagonal and differ nowhere else. THE SEPARATOR IS THEREFORE FREE AND NEEDS NO DEDICATED COMMAND: any press that breaks the alignment settles it -- key 2 or 4 at an odd index, or key 1, 3 or 5 at an even one. Next index is 10, EVEN. One new piece of evidence STRAINS reading A without refuting it: at t3 and t4 the body stood at lattice (2,2) with left and right BOTH void, so ACTION3 and ACTION4 were blocked identically -- and ACTION4 burned while ACTION3 did not. Under action-keying that means the cost is attached to the key and not to the attempt, with keys 2 and 4 charging and 1, 3 and 5 free; under parity it is one bit of clock and no special pleading. I encode A because it is the only one the guard language can say -- there is no command counter and no phase pixel, which is the same wall cegis_miner hit when it reported 'no literal separates transition 1 from the positives' -- and I expect B to win."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis "WITNESSED: ACTION2 IS DOWN, 3/3, six rows south, one lattice cell, at t2, t6, t8. ACTION5 returns the body from lattice (2,2) to (1,2), 3/3. NEGATIVE INFORMATION, and I state it as negative because that is all it is. At spawn (1,2) up and left are void while down and right are open floor, and ACTION1 did nothing -- so ACTION1 IS NEITHER DOWN NOR RIGHT. At (2,2) the body had just vacated rows 8-12 so UP WAS OPEN, and rows 20-24 cols 14-18 are floor so DOWN WAS OPEN, while left (cols 8-12) and right (cols 20-24) were both void; ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN. Fit those together and one assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else. It explains every no-op as a blocked move and it is the conventional mapping for this action family, which is a prior and not evidence. It has one cost, and I name it: under it, ACTION3 and ACTION4 were blocked in exactly the same way at the same cell and only one of them burned the meter, which is why I expect the parity reading of the bar. THE CHEAP TEST IS ONE PRESS: the body stands at spawn, where left is void and right is open floor, so ACTION4 pressed here either steps six columns east or does not, and either answer names the east key -- if ACTION4 does not move, ACTION3 is east by elimination, since ACTION1 is already excluded from east by t1."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_and_the_two_cell_experiment_that_names_it "Three readings survive all three ACTION5 presses because all three were made from exactly one cell south of spawn, where they are indistinguishable: UP (move one cell north), UNDO (revert the last move), RETURN (jump to spawn from anywhere). They separate the moment the body is TWO cells from spawn, and they separate differently depending on the axis. Two cells EAST at lattice (1,4): up is void there so UP predicts no move, UNDO predicts one cell west to (1,3), RETURN predicts spawn at (1,2) -- three different diffs, all legible in the raw pixel count. Two cells SOUTH at (3,2): UP and UNDO both predict (2,2) and only RETURN separates. So the eastward route answers this question for free and the southward route does not, which is one more reason to go east first. Note the coupling I cannot yet break: the panel toggles on every effective ACTION5, so whatever ACTION5 is, the panel is its counter or its selector, and if ACTION5 turns out to be UNDO then the panel is plausibly an undo-parity display -- a reading I record and do not act on."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "cascade_lengths are 1, 7 and 9. Every ACTION5 returned 9 frames; ACTION2 returned 7 frames at t2 and t8 and 9 frames at t6; every no-op returned 1. So a move is animated one row per internal frame, the world reports the whole animation for a single action, and `cascade single_frame` compares only the net effect -- which is identical for all three ACTION2 presses (48 body cells, rows 8-18, cols 14-18) regardless of whether the command took 7 frames or 9. TWO THINGS FOLLOW. First, a refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, three times. ONE PRESS IS ONE LATTICE CELL, 3/3, and every distance in the playbook rests on that. Second, an anomaly I will not over-read: the two 7-frame ACTION2 presses both had the panel in configuration A and the 9-frame one had it in B. Three samples, one clean correlation, zero effect on the net frame. It is not evidence of unobservable state -- it is evidence that the animation length is a function of something the panel also depends on -- and since the net effect is what I model, it costs me nothing either way."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_world_may_still_not_be_a_function_of_the_drawn_frame "Carried as a belief and NOT proven in this window. To prove it I need two pixel-identical states from which the SAME action produced different successors; I have no such pair. The near misses: states 2 and 3 are pixel-identical (ACTION3 changed nothing at t3) but were followed by different keys; t2 and t8 are the same key from the same lattice cell but from states differing in row 63. What keeps the belief alive is the parity reading of the meter, which if true IS one bit of hidden state that flips every command and that no guard in this language can read, because no guard can read anything that is not a pixel. Operationally it matters in exactly one way: if parity wins, every burn rule I can write is an approximation with a known error rate, and I would rather say that once than rediscover it."
    [depends: the_meter_question_after_nine_transitions_and_why_it_is_still_open  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4021 + dynamic 75 = 4096, and 39+24+9 = 72 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 75. Consequence, stated as a law of this manual rather than of this world: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. The bar makes this exact and unavoidable. meter_burn_key2_next now replays t6 and t8 perfectly, because by replay time (63,61) and (63,60) are dynamic and have instances; it will still miss the FIFTH burn at (63,59), because that cell is board today. Every burn therefore costs exactly one wrong pixel in the round it first happens and zero pixels forever after, and no rewriting of the rule fixes it -- only observation does. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable too until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, 24 if I already had the leaves rule, 0 for the second step. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 75 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three; slot 2's nine, centre included because (2,6) is 1 in A and 0 in B; underline 2's three. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 4 are the burned right end of row 63: (63,63), (63,62), (63,61), (63,60). 23+24+24+4 = 75 = dynamic_cells. By frame-0 colour: 39 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 4 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 39+9+24 = 72 = cells_needing_an_owner exactly. zero_space's cell list is the same 75 cells -- it lists (2,1) and (2,3) but not (2,2), (10,14),(10,15),(10,17),(10,18) but not (10,16), and all four burned bar cells -- and its single global law restates this census."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so that the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended three times and all three started at spawn, so no rule of mine turns Vacated pixels from 9 back to 5 on an ACTION2: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. One ACTION2 from lattice (2,2) buys it. (2) EAST-WEST MOTION. Whatever the east key turns out to be, it needs a pair: 'rule keyE_body_leaves forall ?p in Glyph9 when act=key(N) and colored(?p, 9) and colored(rightof(rightof(rightof(rightof(rightof(rightof(?p)))))), 5) then recolored(?p, 5)' and its arrives-twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) A FIFTH BURN AT A CELL THAT IS STILL BOARD, which is not a missing rule but a missing instance and cannot be written at all. I state the price of all three in advance so it cannot be mistaken for a surprise: the first eastward step costs 48 wrong cells plus one if the bar burns, the first second-descent costs 24, and every fresh burn costs 1."
    [depends: key2_body_arrives, the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth `below` is row 69. So `colored(<off-board>, k)` is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen of the twenty rules rest on this and every row and column discrimination in the panel is built from it: the k-th `above` is off-board exactly when k exceeds the row, so row 1 is `above(above(?s)) = wall`, row 3 is `colored(above(above(?s)), 1)` -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is `above^3 = wall` conjoined with `colored(above(?s), 1)`. The same trick separates slot 2's middle row by column: col 5 is `leftof^6 = wall`, col 6 is `leftof^7 = wall and colored(leftof(?s), 1)`, col 7 is `colored(leftof(leftof(?s)), 1)`, pairwise exclusive, which is why the ambiguity check reports 0 clashes. Not one rule uses `not`, deliberately. The eight A->B slot-2 and underline rules could collapse to two if I could write 'not all four neighbours are colour 1', and I decline to gamble a whole round's compile on discovering whether `not` before an equality atom parses. If a future desk wants the shorter form, try it on ONE rule, not on eight."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read from the current frame: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are open, C=6 holds the knob, C=7 is void; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2; R=8 is floor from col 13 to col 48, so C=2..7. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); in ten frames the body has occupied exactly two cells, (1,2) and (2,2), and it has been at spawn in six of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed three times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in ten frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open: colour 8 leaves the comb along row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41 with a stem pixel at (12,40), all inside lattice (1,6). Not one colour-8 pixel has moved in ten frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. Four lattice cells of eastward travel put the body at (1,5) and every one of those four steps is on floor that R=1 shows open."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after ten states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the standard mapping I now favour -- 1 up, 2 down, 3 left, 4 right, 5 undo-or-return -- accounts for every key I have pressed, which makes 6 and 7 more likely to be a click and a spare than more directions."
    [depends: the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and the reason has not weakened. `Cart.pos = exit_cell` needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and thirty-eight siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells do become dynamic on first entry, but `count(Vacated, color = 9) = 24` would then be true of the body standing anywhere it has already been, which is not a win -- a goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in lattice (8,7) once, the playbook steers by lattice distance, and `is_goal -> False` is the honest compilation."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -2214 and -36598 bits, so its segmentation still loses to writing the pixels out and I owe it nothing structural -- but its EIGHT tracks are the round's best independent corroboration. obj1 (colour 1, nine cells, first seen frame 0, present 5 frames) and obj6 (colour 1, nine cells, first seen frame 7, present 2 frames) are slot 2 solid in configurations A; obj5 (colour 2, first seen frame 5, present 2) and obj7 (colour 2, first seen frame 9, present 1) are slot 1 dimmed in configurations B. Read the frame indices off those four tracks and you get A at 0-4, B at 5-6, A at 7-8, B at 9 -- exactly the toggle sequence my three ACTION5 rules produce, derived by an engine that has never seen my rules. obj0 and obj2 persisting through all ten frames while the segmenter narrates six moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 4 cells are dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 9 transitions constrain rank 5 of 375 features, null space dimension 370, 'nearly every vector in it is a law that is true over these states and unfalsified rather than confirmed' -- and its single global law is my census. cegis_miner refuses on every track and its verdict, 'the world does not narrate as one mover', remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. ACTION4 FROM SPAWN, command index 10: if the standard mapping holds, the world changes 48 cells in rows 8-12 cols 14-24 and burns (63,59) for 49 total, and MY MANUAL DRAWS NONE OF THEM -- no east rules exist and (63,59) is board -- so I expect a 49-cell divergence and that is the advertised price of the first step onto fresh ground, not a failure of physics. If instead ZERO cells change, ACTION4 is not east, ACTION3 is east by elimination, and action-keying is refuted too, because index 10 is even and parity demanded a burn. If exactly ONE cell changes and it is (63,59), ACTION4 is not east and both meter readings survive. ACTION2 FROM SPAWN: 48 cells I draw correctly plus a burn at (63,59) I cannot draw -- exactly one wrong pixel, every time, forever, until that cell has burned once. ACTION5 FROM SPAWN: I predict ZERO changed cells anywhere, on the strength of the spawn_probe guard and nothing else; any panel toggle there refutes the guard outright and means the toggle is bound to the key and not to the return. ACTION1 OR ACTION3 FROM SPAWN at an even index: zero cells under my manual, one cell at (63,59) under parity -- the cheapest single-bit experiment on the board, and worth buying only when no map question is open."
    [depends: the_action_map_after_nine_transitions_and_the_standard_mapping_hypothesis, the_meter_question_after_nine_transitions_and_why_it_is_still_open  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept in compressed form because the lesson is structural and cost a full round. Thirteen panel rules once carried `colored(spawn_probe, 5)` while the landmark line read `# arc-cell: carried, coordinates stripped`, which is not a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The landmark now reads `# arc-cell: (8, 14)`, the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key5_slot1_dims  probe: passed]
