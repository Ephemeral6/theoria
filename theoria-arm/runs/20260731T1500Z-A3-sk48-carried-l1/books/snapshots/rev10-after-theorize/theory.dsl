# theory.dsl -- TENTH DRAFT.
#
# 0. WHAT IS NEW THIS ROUND IS NOT A FRAME. IT IS A VERDICT. The store is
#    byte-for-byte the record the ninth draft already digested: steps 10,
#    states 10, distinct_states 7, dynamic_cells 98, cells_needing_an_owner 74,
#    the same nine transitions t1-t9. No command was pressed between the ninth
#    draft and this one. So nothing in this draft may be justified by new
#    evidence about the world; the only new evidence is about the MANUAL, and
#    it is certify's report.
#
# 1. THE PRE-REGISTRATION WAS MET IN FULL, ON ALL FOUR NUMBERS CERTIFY GIVES.
#    I wrote: replay 6 of 9; first divergence at transition 0 under ACTION1,
#    96 cells, first cell (30,11) manual 5 world 6; responsibility 0
#    unexplained of 4096; 0 clashes. Certify returned 6/9, ACTION1 at t=0 with
#    96 cells and (30,11) 5-against-6 at the head of the list, 0 of 4096
#    unexplained, and 0 clashes over 30 adjudicated pairs. That is the second
#    consecutive round in which a pre-registration written before the check was
#    met cell for cell, and this time it covered a rule -- the march -- that
#    had been added on explanatory grounds with no replay support.
#
# 2. THE ONE SURPRISE THAT FIRED IS THE ONE I PRICED. replay_mismatch at t=0
#    is the selector swap, which this manual is deliberately silent about. I
#    refuse to change for it, for the second time, and the refusal now rests on
#    two independent arguments (inexpressibility, compression) that are both
#    written out below. What I did change is a claim I made in DEFENCE of that
#    silence which was too strong -- see the correction in the eighth theorem.
#
# 3. THE MARCH RULE IS PROMOTED FROM "PAYS IN PROSE" TO "PAYS IN PIXELS", AND
#    THE OLD JUSTIFICATION WAS UNDERSOLD. I had said the march buys zero replay
#    transitions and is carried for explanatory content. That undersold it. The
#    march makes the manual RECONVERGE at transition 7, so the manual's state
#    after transition 8 equals the world's frame at t9 exactly -- every one of
#    4096 cells. Without the march the manual would be sitting one cell wrong
#    at (53,62) right now and would stay wrong forever, because nothing else in
#    the manual can ever repaint that cell. Every probe I press from here is
#    scored against the manual's present frame, so being exactly right NOW is
#    worth more than being exactly right at two transitions in the middle of a
#    record I will never replay again.
#
# 4. ONE PROBE DISCHARGED BY CERTIFY RATHER THAN BY A PRESS. The seed rule and
#    the march rule could in principle both fire on (53,63) in states 0-3, and
#    whether they do turns on how `colored` reads an off-board cell. Certify
#    adjudicated all 30 pairs and reported no pair that "admitted two rules".
#    Those states and that action are inside the 30. See the theorem for the
#    single assumption that reading still carries.
#
# 5. ONE CLAIM RETRACTED WITHOUT CHANGING ITS VERDICT. I had written that a
#    partial or wrong swap rule "would lose both" transitions 0 and 1. False: a
#    wrong rule paired with its exact inverse loses only transition 0. The swap
#    stays out anyway, on compression, and now for a reason I can state without
#    an argument that does not hold.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Casing { pos: Coord, color: Int }  # arc-colour: 6  arc-instances: all
  object Cavity { pos: Coord, color: Int }  # arc-colour: 0  arc-instances: all
  object Rail { pos: Coord, color: Int }  # arc-colour: 3  arc-instances: all
  object Pip { pos: Coord, color: Int }  # arc-colour: 1  arc-instances: all
  object Stud { pos: Coord, color: Int }  # arc-colour: 2  arc-instances: all
  object Erased { pos: Coord, color: Int }  # arc-colour: 4  arc-instances: all
  Casing [segment: colour_class_6 ev: t0-t9 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t9 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t9 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t9 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t9 compress: 11]
  Erased [segment: colour_class_4 ev: t0-t9 compress: 12]

events:
  event recolored(o, c)

# Eight rules, unchanged from the ninth draft, not one atom touched. They were
# checked this round against the whole 9-transition record and scored 36 of 36
# on the transitions they claim, 0 unexplained pixels, 0 clashes. A rule set
# that has just been vindicated is not a rule set to rewrite, and there is no
# new observation to rewrite it from.
#
# The eleven Stud instances are (32,13) (32,14) (33,13) (33,14) in the
# unselected slot bar, (38,17) (38,20) (39,19) (39,22) in the strip, (39,16) in
# the lower port, and (53,62) (53,63) in the meter.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3,t7,t9 cov: 24/24]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3,t7,t9 cov: 12/12]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4,t6,t8 cov: 24/24]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4,t6,t8 cov: 12/12]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_seeds_the_meter_at_the_right_edge forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

  rule key4_marches_the_meter_leftward forall ?p in Stud [ev: t8 cov: 1/2]
    when act=key(4) and colored(?p, 2) and colored(rightof(?p), 3) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 11 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 74 [status: proven]

  theorem the_ninth_drafts_pre_registration_was_met_in_full_and_no_command_was_pressed_this_round "the store this round is identical to the store last round -- steps 10, states 10, distinct_states 7, dynamic_cells 98, cells_needing_an_owner 74, the same nine transitions with the same diffs. Nothing about the world is newly known and no theorem below may cite a press that does not exist. What is newly known is the manual's score, and every number of it was written down in advance: replay 6 of 9 against a prediction of 6 of 9; first divergence at transition 0 under ACTION1 with 96 cells wrong and (30,11) manual 5 world 6 at the head, exactly as written; responsibility 0 unexplained of 4096; unambiguous 0 clashes over 30 pairs. I record this because it is the strongest kind of evidence this framework produces and because the run it vindicated was not a safe one: I had added the march rule on explanatory grounds alone, predicted that it would cost transitions 5 and 6 and win back 7 and 8, and that is precisely the shape of a 6 that the alternative manual would also have scored -- differently placed. The count came out where I put it."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_world_is_not_a_function_of_the_visible_frame "this is proven, not suspected, and it is the largest single fact I have learned about this game. State 5 and state 7 are the same 4096 cells: both have the lane B strip blanked to colour 4, both have (53,63) colour 3 and (53,62) colour 2, both have the bottom slot selected, and every other cell is constant across the whole record by definition since constant_cells is 3998. ACTION4 was pressed from each. From state 5 it restored twelve cells and the bar did not move; from state 7 it restored twelve cells and (53,62) went 2 to 3. Same frame, same action, different successor. I do not rest this on my own reading of the grids: the store reports distinct_states = 7 over 10 states, and my enumeration collapses exactly three pairs -- s2 = s0 because ACTION2 undid ACTION1, s6 = s4, and s7 = s5 -- giving 10 minus 3 = 7 on the nose. So the world carries at least one bit my guards cannot read, constraint 5 forbids me from writing both successors, and any planner that treats a frame as a state is planning in the wrong space."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem three_readings_of_the_hidden_bit_survive_and_one_of_them_pays_for_an_old_puzzle "ticks fell at t4 and t8 and not at t6. Three readings fit all three points. (A) a command counter: ticks at command 4 and command 8, period four. (B) a parity on the restore key: restore presses one and three ticked, press two did not. (C) the world remembers which key blanked the strip: t3 blanked with ACTION3 and t4 ticked, t5 blanked with ACTION7 and t6 did not, t7 blanked with ACTION3 and t8 ticked. All three are 3/3 and none is expressible. I rank C first on grounds constraint 3 recognises: for eight drafts I had two keys, ACTION3 and ACTION7, producing byte-identical twelve-cell diffs, and no reason for the world to spend two names on one function. C explains that redundancy; A and B leave it as coincidence. A reading that pays for a fact I already had beats two readings that only fit the new one. A fourth variant, C-prime, says the tick is a delayed effect of ACTION3 landing on whatever command comes next rather than specifically on ACTION4; it fits equally and is separated from C by pressing anything except ACTION4 from the current state. The current state was reached by an ACTION3 at t9, so all three readings are loaded and disagree about the very next press: C says the next ACTION4 ticks, A says the next tick is at command 12, B says restore press four is even and does not tick, C-prime says the tick lands on whatever is pressed next whatever it is."
    [depends: the_world_is_not_a_function_of_the_visible_frame  probe: pending]

  theorem the_march_earns_its_place_by_keeping_the_manual_in_sync_with_the_present_frame "the hidden bit forces me to be wrong at t6 or at t8, and I chose t6. Last draft I justified that by explanatory content and recorded that it bought zero replay transitions. That undersold it and certify has now shown me the better argument. Both manuals score 6 of 9 -- with the march I lose transitions 5 and 6, without it I lose 7 and 8 -- but the two sixes are not equivalent, because replay ends at the present. With the march the manual reconverges at transition 7 and its state after transition 8 is the world's frame at t9 in all 4096 cells: strip blanked, (53,62) and (53,63) both colour 3. Without the march the manual would be one cell wrong at (53,62) at this instant and could never repair it, since no other rule of mine can repaint that cell and no future ACTION4 restores it to 2. Every probe I press is scored from here, so a manual that is exactly right now is worth strictly more than one that was exactly right in the middle. The equal-sixes analysis was correct arithmetic and the wrong figure of merit."
    [depends: three_readings_of_the_hidden_bit_survive_and_one_of_them_pays_for_an_old_puzzle  probe: passed]

  theorem the_march_can_never_reach_a_cell_that_has_not_already_ticked "the arm gives an instance only to cells that vary somewhere in the record. (53,63) and (53,62) have varied and are Stud instances; (53,61) has been colour 2 in all ten states, so it is board and no rule of mine can repaint it however I guard. The consequence is exact and worth stating plainly: my march rule can replay a tick that has been observed and can never predict a new one. From the current state my manual therefore predicts that the next ACTION4 changes exactly twelve cells and moves nothing at (53,61), which is what readings A and B predict and is the opposite of reading C, the reading I rank first. I am pre-registering a prediction I expect to lose, because the arm leaves me no way to write the one I believe. This is not a defect I can repair by writing better guards; it means the manual will lag the world by exactly one bar cell forever, catching up each time a tick is observed, and every bar cell the world consumes hands me one more instance and one more cell of reach."
    [depends: instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances  probe: passed]

  theorem the_toll_on_the_restore_key_is_refuted "the eighth draft carried the reading that every ACTION4 costs one bar cell, fitted perfectly to the single point it then had. t6 was an ACTION4 pressed from a blanked strip and it restored twelve cells and moved nothing. One press killed it, which is what I said it would take, and it is the cheapest refutation in the record. What survives from that reading is only the association of the tick with ACTION4 rather than with ACTION3, which is itself a correction of the draft before."
    [depends: three_readings_of_the_hidden_bit_survive_and_one_of_them_pays_for_an_old_puzzle  probe: passed]

  theorem the_two_probe_refutations_are_one_error "P-03 pressed ACTION4 and the manual predicted 8ccbe276408c4dd7 where the world answered bb5c436a2318c544. That is my restore of twelve strip cells against the world's restore of twelve strip cells plus the (53,62) tick: one pixel. P-04 pressed ACTION3 and the manual predicted 05615f3d5f835100 where the world answered 3bf51d2fd9036a78, and this is not a second failure at all -- my frame had been one cell off since P-03, so blanking twelve cells from it lands one cell off too. The hashes corroborate the reading rather than merely permitting it: P-03's manual hash 8ccbe276408c4dd7 is exactly P-04's inert hash, and P-03's inert hash 05615f3d5f835100 is exactly P-04's manual prediction, which is what a perfect blank-restore toggle between two frames looks like from the outside. So the twelve-cell toggle model survived both probes untouched and the entire error surface of that manual was one meter cell -- a cell the current manual, thanks to the march, now holds correctly."
    [depends: the_march_earns_its_place_by_keeping_the_manual_in_sync_with_the_present_frame  probe: passed]

  theorem replay_is_open_loop_and_the_proof_is_the_old_five_transition_score_not_the_new_nine "under resync the checker hands the manual the world's state before each transition; under open loop it does not. On the five-transition record these separated cleanly: open loop predicted 4 of 5 -- transition 0 lost to the swap, transition 1 regained because ACTION2 returns the world to frame 0 while my silent manual never left it -- and resync predicted 3 of 5, because a resynced manual starts transition 1 from the swapped panel, is silent on ACTION2, and holds the swap while the world drops it. Certify returned 4 of 5, so open loop it is. I must now record that the new score does NOT reproduce this discrimination and my last draft would have been wrong to lean on it: on the nine-transition record resync also scores 6, losing transitions 0, 1 and 5 where open loop loses 0, 5 and 6. Same count, different places, and certify reports only the count and the first divergence, both of which the two readings share. The verdict stands on the old evidence alone and would be re-opened by any future record on which the two counts differ."
    [depends: silence_on_the_selector_costs_one_transition_of_nine  probe: passed]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and both (53,62) and (53,63) hold 2 rather than 3. The anatomy closes cell by cell: 22 Casing as the perimeter of rows 36-41 by cols 11-16 minus the two ports plus the 2x2 core at rows 38-39 cols 13-14; 12 Cavity as the 4x4 at rows 37-40 cols 12-15 minus that core; 8 Rail at rows 30-31 and 34-35 by cols 13-14; 4 Stud at rows 32-33 by cols 13-14; 8 Pip and 4 Stud in the lane B strip at rows 38-39 cols 17-22; 1 Pip at (38,16) and 1 Stud at (39,16) in the ports; 12 Erased as the lane A strip at rows 32-33 cols 17-22; 2 Stud in the meter. 22+12+8+9+11+12 = 74 = cells_needing_an_owner. The 24 remaining dynamic cells are the background of the unselected slot footprint, cols 11, 12, 15, 16 over rows 30-35, and 74+24 = 98 = dynamic_cells. The dynamic set closes independently: the selector swap repaints 96 cells and the meter has ticked twice, 96+2 = 98, and the reported dynamic_box of rows 29-54 by cols 10-63 is exactly my set padded by one row and column and clipped at the frame edge, which is why row 29 appears in the box while being board. Certify has now returned 0 unexplained of 4096 on this reconstruction three rounds running."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0. A cell constant across the whole record gets no instance. The record has demonstrated the arithmetic three times: at 6 states, 73 owners and 97 dynamic; at 10 states, 74 and 98, the difference being exactly the one bar cell that ticked; and my declarations moved by exactly one Stud each time. This is a fact about the arm, not about the world, and it is the single largest constraint on what this manual can say -- most sharply through the march rule, which can never reach an untouched bar cell."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language can produce them. A guard sees a cell's own colour, its four immediate neighbour colours, off-board, and the action name -- no coordinate, no row band, no distance. The witness is inside the divergence report certify returned again this round: (30,16), (31,16), (32,16), (33,16) and (34,16) are all colour 5 in frame 0 with above 5, below 5, left 5, right 4, one indistinguishable guard reading, and the world makes them 6, 6, 1, 2, 6. Three answers to one question. A second pair kills colour as a discriminator: (30,13) is colour 3 and becomes 6 while (32,13) is colour 2 in an equally uniform bar neighbourhood and also becomes 6. Constraint 5 forbids two rules that both fire, so the swap does not go in the manual and the transition-0 mismatch is a cost I accept for the second round running."
    [depends: the_panel_is_a_column_of_slots  probe: passed]

  theorem the_swap_also_fails_the_compression_test "grant every expressibility obstacle removed and free reading of position. The swap still does not belong. It repaints 96 cells whose new colours follow no local law, because the widget is teleported six rows and no event in the vocabulary does that -- moved is one cell, jumped-over is two, jumped-to-a-landmark needs a landmark and a rule per instance. The shortest form I can construct is of order one landmark and one rule per repainted cell, in both directions, which is longer than the 96 pixels it explains. Constraint 3 refuses it independently of constraint 5, and this argument does not depend on any reading of the grammar. Two independent refusals, which is why I expect never to write the swap rather than merely not to have written it yet."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem silence_on_the_selector_costs_one_transition_of_nine_and_my_defence_of_it_contained_a_false_step "my manual is silent on key(1) and key(2), so it draws frame 0 at transition 0 where the world draws the swapped panel: 96 cells, the divergence certify reports. Transition 1 is a match because ACTION2 returns the world to frame 0 while my silent manual never left it. The proportional cost has fallen from a fifth of the record to a ninth simply because the record grew. I now retract a supporting claim I made twice: that a partial or wrong swap rule 'would lose both' transitions. It is false. A wrong rule for key(1) paired with its exact inverse for key(2) -- for instance recolour every Rail to 6 and back -- returns my state to frame 0 at transition 1 whatever it did at transition 0, so it loses one transition, not two. I checked what such a pair would buy: a uniform Rail-to-6 rule gets (30,13) and (30,14) right and (31,13), (31,14), (34,13), (34,14) wrong, 4 of 8 Rail cells and 4 of 96 overall, and transition 0 still fails. Two rules for zero transitions is constraint 3 refusing it, which is the argument I should have given in the first place and the one that survives."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem a_background_object_would_own_exactly_the_swap_footprint_and_i_still_do_not_declare_it "an object declared at arc-colour 5 with arc-instances all would be placed on the colour-5 cells the board cannot explain, and those number exactly 98 minus 74 = 24: cols 11, 12, 15, 16 over rows 30-35, the unselected slot footprint, and not one cell more. The declaration is cheap and surgical rather than ruinous, which is why I withdrew the blocker that said otherwise. I still do not declare it, because it would explain no pixel the board does not already draw correctly and would enable no rule I can write, which is constraint 3 refusing it on its own terms. If a device ever appears that lets a guard read position, this is the first declaration to add."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem off_board_does_not_read_as_a_colour_and_certify_is_what_settled_it "the seed fires on a colour-2 Stud with no right neighbour and the march on a colour-2 Stud with a colour-3 right neighbour. The one state of affairs where both could fire on the same instance is (53,63) in states 0 through 3, where it is colour 2 and its right neighbour is off the board: if `colored(off_board, 3)` returned true, both rules would be admitted on that instance under key(4) and constraint 5 would be violated. Certify adjudicated all 30 state-action pairs, which includes those four states under key(4), and reported that no pair 'admitted two rules', 0 clashes, no step crashes. The assumption this reading carries, and I name it rather than hide it, is that the ambiguity check tests whether two rules are ADMITTED and not merely whether they disagree about the outcome -- here both would recolour to 3, so an outcome-based checker would stay silent and teach me nothing. Certify's own wording is the admissibility one. If a later round shows the check is outcome-based, this returns to pending and the repair is still one atom on the march."
    [depends: the_march_earns_its_place_by_keeping_the_manual_in_sync_with_the_present_frame  probe: passed]

  theorem the_bar_runs_leftward_and_the_budget_is_now_measurable "two cells have converted, (53,63) then (53,62), so the direction of travel is witnessed twice and is right to left. Row 53 reads colour 2 from column 10 to column 61 and colour 3 at 62 and 63, and I have never been shown columns 0 to 9 of that row, so between 52 and 62 cells remain. Nine commands have bought two ticks. If reading A or C holds the rate is near one tick per four commands and the bar is of order two hundred commands deep; if B holds it is one per two ACTION4 presses. Either way probing is still cheap and will not stay cheap. What I still do not know is whether 3 means consumed or filled -- colour 3 is also what an unselected slot shows on its rails, which argues weakly for a resting or completed state -- and the two readings invert the sign of every ranking decision, so the playbook still may not rank on it."
    [depends: the_march_can_never_reach_a_cell_that_has_not_already_ticked  probe: pending]

  theorem the_strip_hides_and_shows_and_a_repeat_of_a_blanking_key_has_still_never_been_tried "key(3) blanked a shown strip at t3, t7 and t9, key(7) blanked one at t5, key(4) restored a blanked one at t4, t6 and t8, twelve cells and cell for cell identical every time, so the pattern lives somewhere the frame does not show. Every blank was pressed from a shown strip and every restore from a blanked one, so hide-and-show and toggle-and-toggle remain indistinguishable after nine transitions, which is remarkable and is entirely my fault for never varying the order. My manual commits to complete inertness for a repeat of either blanking key from the current blanked state, since every strip cell is colour 4 and no blanking guard can fire. A restore under a blanking key refutes hide-and-show outright. A tick with nothing else refutes reading C in favour of C-prime. Nothing at all confirms inertness and reads the returned frame count for free. One press, three answers, and it is the only press in the space that risks nothing: my manual currently reconstructs the world exactly, and a null press cannot cost that."
    [depends: three_readings_of_the_hidden_bit_survive_and_one_of_them_pays_for_an_old_puzzle  probe: pending]

  theorem the_restore_and_blank_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "the restore rules guard on colour 4 alone and the blanking rules on one to three neighbour tests. Both are correct on all six blank-or-restore presses observed, because every press was made with the bottom slot selected, where the only colour-4 Pip and Stud instances in existence are the twelve blanked lane B cells. They would be wrong the moment slot A is selected: lane A strip cells become texture while lane B strip cells become arena fill of colour 4, and the instances do not move with the widget because I only ever recolour. My manual never reaches that state, being silent on the selector, so this costs zero transitions and certify cannot see it. It is written here because a searcher planning through a selector move would be misled by rules that score 36 of 36."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have ever seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Twenty-one witnesses, and I re-walked all of them this round against the divergence report rather than inheriting the count. Frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, a period-3 run offset by one column; the divergence report gives lane A row 32 cols 16-22 as the world drew it at t1, 1 2 1 1 2 1 1, and rows 32 and 38 agree because 6 divides by 3. The two port cells fit the same formula, which is an unforced success. So the two strips are two windows onto one texture, which is why a restore can rebuild twelve cells exactly. Untested prediction: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2. No rule needs this, since each instance remembers its frame 0 colour, so the concept buys understanding rather than symbols and stays out of the word table."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, four times now, twelve cells every time. (38,16)=1 and (39,16)=2 sit on the widget right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since the left neighbour of each is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The rival explanation is that col 16 is where the 6x6 widget ends and the survival is coincidence; four blanks do not separate them."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots "the divergence report gives the world's t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at those columns read identically -- eighteen cells, six rows apart. Rows 42 to 52 are uniform background, so rows 36-41 is the bottom slot and rows 30-35 the one above it. ACTION1 moved selection from the bottom slot to the upper one and ACTION2 moved it back, which is one witness each for up and down and needs no wrap to explain. Whether a third slot exists above is untested: (29,13) and (29,14) hold colour 3 and never vary, which is what a slot at rows 24-29 would show on its bottom rail, but board cells prove nothing about slots I have never selected. Two presses would settle it -- ACTION1 twice from the bottom, or ACTION2 once from the bottom."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_badge_is_lane_aligned_and_i_have_downgraded_the_matching_reading "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45. Those are exactly the rows an upper-slot cavity occupies within its six-row band, so the badge belongs to the lane of the slot at rows 30-35, and the bottom slot's lane has nothing at cols 42-45. The tempting reading is that it is a target the lane texture must be made to match, but the strip is 2 rows by 6 cols and the badge is 4 rows by 4 cols of one uniform colour, so shape refutes it. The surviving readings are that it marks which slot carries the task, that it is a destination, or that it is a picture of a completed cavity, the widget cavity being also 4x4 with a 2x2 core removed. Zero transitions bear on any of the three, and colour 14 appears nowhere else in the frame."
    [depends: the_panel_is_a_column_of_slots  probe: pending]

  theorem the_cadence_is_inexpressible_and_both_loopholes_are_still_shut "a guard reads a cell colour, its four neighbour colours, off-board, and the action name. Every surviving reading of the tick needs memory -- a command count, a press parity, or a bit set by whichever key last blanked -- and there is no count and no latch in the grammar. Loophole one, an object declared at the background colour used as an invisible latch bit: unusable, because the value grammar exposes only color as a field so no guard can read present, and the 24 colour-5 cells the arm would instantiate all sit in the slot footprint, none of them where a latch would be wanted. Loophole two, a second type declared at colour 2 to reach the next bar cell: unusable, because the arm finds objects by colour alone and would duplicate all eleven Studs. So the hidden bit stays prose, and my march rule is the shadow it casts on the frame rather than a model of it."
    [depends: the_world_is_not_a_function_of_the_visible_frame  probe: passed]

  theorem nesting_a_cell_expression_is_the_one_untested_device "the grammar lists above, below, leftof and rightof as taking a cell and lists cells exhaustively including those four forms, but does not say whether the argument may itself be one of them. If above(above(?p)) parses, guards gain a two-cell reach: at depth two, (30,16) and (31,16) both see colour 3 two cells to their left while (32,16) and (33,16) see colour 2, which separates the pair that goes to 6 from the pair that goes to 1 and 2. So a position-reading device exists in principle. It does not change my verdict on the swap, because the compression blocker stands regardless, and it does nothing at all for the meter, where the obstacle is memory rather than reach. I do not test it inside this manual because a parse error costs the whole round, and this round the manual is otherwise perfect on every check certify runs, which is the worst possible moment to gamble it."
    [depends: the_swap_also_fails_the_compression_test  probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot bar, a port, four strip cells and two meter cells -- four unrelated roles in one type. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 74 cells that need an owner against 74 pixels written out, with 0 unexplained confirmed three times. The cost is measured too: no rule can name the strip, so every blanking rule carves it out of its colour class by neighbour tests, and both meter rules separate one Stud from ten others by an off-board test or a neighbour colour. Those guards are pixel-fitting in a costume, and the march rule is the worst offender because its guard is not a property of the meter but an accident of what has already ticked."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, which is rows 29-54 by cols 10-63. They live in the 3998 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is where a title, target, score or instruction would live, and the likeliest home of whatever finishing means and of whether the bar is a budget or a score. Nine commands have not made one cell of it vary, which is itself mild evidence that it is decoration rather than a display -- but only mild, since six of those nine commands were the same two keys."
    [depends: no_goal_section_on_purpose  probe: pending]

  theorem two_keys_have_never_been_pressed "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not, after ten commands. The budget argument has a number behind it: of order two hundred commands of bar remain if the cadence is roughly one tick in four, so two presses are affordable and are the cheapest untried source of a genuinely new frame. If either is a click carrying coordinates, this guard language cannot express it and the finding will be recorded as prose rather than as a rule. Each press also reads its own returned frame count, which is one of only two handles left on the hidden bit."
    [depends: the_extra_frame_count_is_the_only_visible_correlate_of_the_hidden_bit  probe: pending]

  theorem the_extra_frame_count_is_the_only_visible_correlate_of_the_hidden_bit "every command in the record returned two frames except t5, the single ACTION7, which returned one. Ticks fell at t4 and t8 and not at t6. Cumulative frame-advances at the ticks are 4 and 7, which no single period fits given that no tick fell at advance 1, so the old every-third-advance clock is dead. What survives is weaker and cheaper: the frame count is the one channel through which the world has ever shown me something the grid did not, ACTION7 is so far the only command that did not advance it, and reading C's discriminator between ACTION3 and ACTION7 is confounded with exactly that difference. A second ACTION7 that returns one frame again makes the confound real and worth a rule; one that returns two frames breaks it and leaves C standing on the key name alone."
    [depends: three_readings_of_the_hidden_bit_survive_and_one_of_them_pays_for_an_old_puzzle  probe: pending]

  theorem no_goal_section_on_purpose "all ten states returned NOT_FINISHED and nothing in nine transitions indicates what finishing means. The live candidates are that a lane must be brought into some relation with the badge at its far end, that every slot in the column must be visited or solved, that the bar reaching one end ends the level, or that the objective lives in the rows I have never been shown. An absent goal compiles to is_goal implies False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. The bar is the only monotone quantity in the whole record and is therefore the most tempting goal, and it is exactly the one I cannot sign because I cannot tell filling from spending."
    [depends: the_bar_runs_leftward_and_the_budget_is_now_measurable  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "the candidate stream is unchanged in substance from last round and I re-read it for anything I had missed. mdl_segmenter returns negative gain on both variants, -3513 bits at 4 tracks and -18186 at 51, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator rather than the world. One track I had passed over does deserve a sentence: obj1 is 108 cells of shape 2 by 54, present in all ten frames and the only stable track it found. That is rows 53 and 54 clipped to the window, the meter bar and the fill row beneath it, fused because colour 2 and colour 4 touch vertically and background 5 does not separate them. It corroborates two things I hold: the bar is one object spanning the frame and continuing left of column 10 where I have never seen it, and my colour-class declarations cut across the world's own segmentation, which is the cost I admit elsewhere. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition, and its own verdict says the world does not narrate as one mover, which agrees with my event vocabulary of recolored alone. zero_space calls its own evidence THIN in its own words -- 9 transitions constraining rank 4 of 686 features, null space of dimension 682 -- and its single global law spans 98 dynamic cells at once, which is what a 682-dimensional null space produces rather than what a conservation law looks like. What I took from the engines is the store arithmetic, dynamic_cells 98, cells_needing_an_owner 74 and above all distinct_states 7."
    [probe: pending]

  theorem what_this_draft_pre_registers "the rules are unchanged, so certify should return exactly what it returned: replay 6 of 9; first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6; further divergences at transitions 5 and 6 on the single cell (53,62); reconvergence at transition 7 with transitions 7 and 8 matching; responsibility 0 unexplained of 4096; unambiguous 0 clashes over 30 pairs. Any movement in those numbers without a movement in the record would mean the checker changed, not the world. The informative pre-registrations are about the world and each is decided by one press from the current state, which my manual reconstructs in all 4096 cells. Repeat a blanking key: my manual says the frame does not change at all, C-prime says the bar ticks anyway, and hide-and-show dies if the strip comes back. Press ACTION4: my manual and readings A and B say exactly twelve cells change, reading C -- the reading I rank first -- says thirteen including (53,61), the cell my manual is structurally unable to paint, so I am betting against myself on the record. Press ACTION7 again and read the frame count alone: one frame confirms the confound, two frames breaks it. Press key(5) or key(6) and anything at all is new."
    [depends: the_march_earns_its_place_by_keeping_the_manual_in_sync_with_the_present_frame  probe: pending]
