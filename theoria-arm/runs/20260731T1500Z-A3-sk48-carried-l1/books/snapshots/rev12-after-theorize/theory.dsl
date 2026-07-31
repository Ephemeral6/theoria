# theory.dsl -- ELEVENTH DRAFT.
#
# 0. FOUR COMMANDS WERE PRESSED AND THEY KILLED EVERY CADENCE READING I HAD.
#    The store moved: steps 10 -> 14, states 10 -> 14, distinct_states 7 -> 9,
#    dynamic_cells 98 -> 99, cells_needing_an_owner 74 -> 75. The new commands
#    are t10 ACTION4 (no surprise, the manual was right), t11 ACTION3 (P-06),
#    t12 ACTION4 (P-07), t13 ACTION3 (P-08). One new bar cell converted,
#    (53,61), and it converted under ACTION3.
#
# 1. THE THIRD TICK LANDED UNDER THE WRONG KEY AND AT THE WRONG COUNT, AND ALL
#    FOUR SURVIVING READINGS DIED AT ONCE. Reading A (command counter, period
#    four) predicted the tick at command 12; it fell at command 11. Reading B
#    (parity of restore presses) predicted a tick at restore press five, t12;
#    nothing. Reading C (the world remembers that ACTION3 blanked) and C-prime
#    (the tick rides on whatever follows an ACTION3) both predicted a tick at
#    t10, which followed the ACTION3 at t9; nothing. I ranked C first and said
#    it would be settled by one press. It was, and it lost. Two new readings
#    replace them and are written out below; both are counters, both are
#    inexpressible, and they agree about the very next press.
#
# 2. THE MARCH RULE MOVES FROM key(4) TO key(3), AND THE REASON IS ARITHMETIC
#    I CAN SHOW. The new instance at (53,61) changes what the old rule does on
#    replay: on the 13-transition record the key(4) march now scores 7 of 13,
#    the key(3) march scores 9 of 13, and no march at all scores 6 of 13. All
#    three leave the manual's present frame exact except the third, which is
#    two cells wrong forever. I take the 9 and I do not dress it up: the march
#    is a phase-shifted shadow of a counter I cannot read, not a model of one.
#
# 3. THE PRE-REGISTRATION THAT MATTERS THIS ROUND IS NEWLY INFORMATIVE.
#    For the first time open-loop replay and resync replay give DIFFERENT
#    counts on the same manual -- 9 against 8 -- so certify's single number
#    re-tests a verdict that has rested on a five-transition record since the
#    fourth draft. It is confounded with one other assumption and I say which.
#
# 4. THE TOP-RANKED PROBE WAS NOT PRESSED. My playbook has ranked "repeat a
#    blanking key from the blanked state" first for two rounds. Four more
#    presses went by and every one of them was the same blank-then-restore
#    alternation. That press is now worth strictly more than it was, because
#    it separates the two surviving counter readings through the returned
#    frame count alone.

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
  Casing [segment: colour_class_6 ev: t0-t13 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t13 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t13 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t13 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t13 compress: 12]
  Erased [segment: colour_class_4 ev: t0-t13 compress: 12]

events:
  event recolored(o, c)

# Eight rules. Six are the strip toggle and are untouched -- they have now
# survived five ACTION3 blanks, one ACTION7 blank and five ACTION4 restores,
# 132 cell-recolourings, every one of them correct. The seed is untouched. The
# march is the one rule that changed and it changed key, not shape.
#
# The twelve Stud instances are (32,13) (32,14) (33,13) (33,14) in the
# unselected slot bar, (38,17) (38,20) (39,19) (39,22) in the strip, (39,16) in
# the lower port, and (53,61) (53,62) (53,63) in the meter -- one more than
# last draft, because (53,61) has now varied and the arm gives instances only
# to cells that vary.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3,t7,t9,t11,t13 cov: 40/40]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3,t7,t9,t11,t13 cov: 20/20]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4,t6,t8,t10,t12 cov: 40/40]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4,t6,t8,t10,t12 cov: 20/20]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_seeds_the_meter_at_the_right_edge forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

  rule key3_marches_the_meter_leftward forall ?p in Stud [ev: t8,t11 cov: 2/2]
    when act=key(3) and colored(?p, 2) and colored(rightof(?p), 3) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 12 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 75 [status: proven]

  theorem all_four_cadence_readings_are_dead_and_i_name_the_press_that_killed_each "for three drafts I carried four readings of when the bar ticks, all of them 3/3 on the ticks at t4 and t8. Four commands later all four are refuted, and the refutations are clean because each reading named a specific press. Reading A, a command counter of period four: it required the next tick at command 12; the tick fell at command 11 and command 12 did nothing. Reading B, a parity on the restore key: restore presses one and three ticked, so press five at t12 had to tick; it did not, and worse, the tick at t11 fell under ACTION3, a key B does not count at all. Reading C, the world remembers which key blanked, and Reading C-prime, the tick rides on whatever command follows an ACTION3: both required a tick at t10, which directly followed the ACTION3 at t9; t10 changed exactly twelve cells. I ranked C first on the grounds that it explained why the world spends two key names on one strip function. That argument was good and the reading was still wrong, which is the lesson: an explanation of an old puzzle is not evidence about a new fact. The ACTION3-versus-ACTION7 redundancy is once again unexplained and I hand it back to the open list."
    [depends: the_world_is_not_a_function_of_the_visible_frame  probe: passed]

  theorem two_counter_readings_survive_and_they_disagree_about_which_keys_pay "ticks fell at commands 4, 8 and 11 out of thirteen. Two readings fit all three and I have found no third that does. Reading D counts commands that returned TWO frames and ticks on every third one: the two-frame commands in order are t1 t2 t3 t4 t6 t7 t8 t9 t10 t11 t12 t13, ordinals 1 to 12, and the ticks fell on ordinals 4, 7 and 10 exactly. The single ACTION7 at t5 returned one frame and is skipped, which is why the raw command count shows gaps of four then three. Reading E counts presses of ACTION3 or ACTION4 only and ticks on every third, starting at the second: work presses t3 t4 t6 t7 t8 t9 t10 t11 t12 t13 are ordinals 1 to 10 and the ticks fell on 2, 5 and 8. Both are 3/3, both need a modulo-three counter, and the grammar has no counter, so neither can be written as a rule. They agree that the next ACTION4 ticks (53,60) -- D because it would be two-frame ordinal 13, E because it would be work press 11 -- so ACTION4 cannot separate them. They are separated by any command that is not a strip key: a selector press is two-frame ordinal 13 and D says it ticks while E says a selector press is free. They are also separated by a repeated ACTION3 from the blanked state IF that press returns one frame, because then D does not advance and E still counts it."
    [depends: all_four_cadence_readings_are_dead_and_i_name_the_press_that_killed_each  probe: pending]

  theorem the_world_is_not_a_function_of_the_visible_frame_and_it_is_now_witnessed_under_both_keys "this was proven once and is now proven twice, once for each strip key, which removes the last chance that it was an artefact of ACTION4. Witness one, unchanged: s5 and s7 are the same 4096 cells, ACTION4 from s5 restored twelve cells and ACTION4 from s7 restored twelve cells and ticked (53,62). Witness two, new: s8 and s10 are the same 4096 cells -- strip shown, (53,63) and (53,62) colour 3, (53,61) colour 2 -- and ACTION3 from s8 blanked twelve cells while ACTION3 from s10 blanked twelve cells and ticked (53,61). The store corroborates the enumeration exactly: fourteen states, and my reading collapses five pairs, s2=s0, s6=s4, s7=s5, s10=s8, s13=s11, giving 14 minus 5 = 9 = distinct_states. So the world carries at least one bit no guard of mine can read, constraint 5 forbids me from writing both successors of an identical frame, and any planner that treats a frame as a state is planning in the wrong space."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_march_moved_to_the_blanking_key_and_the_move_is_worth_three_transitions "the arm gave (53,61) an instance the moment it varied, and that changed what my old rule does on replay -- a rule I did not touch behaved differently because the level instance grew. With the march on key(4) it now fires at t6 and t8, the manual diverges at transitions 5 through 9, and the score is 7 of 13. With the march on key(3) it fires at t7 and t9, the manual diverges at transitions 0, 6, 8 and 9, and the score is 9 of 13. With no march at all the score is 6 of 13 and the manual ends two cells wrong at (53,62) and (53,61) with no rule able ever to repair them. I checked all three by hand, transition by transition, before writing this. The march is therefore worth three replay transitions and two cells of present-state exactness, which is the first time it has paid in replay rather than only at the present frame. What I will not claim is that key(3) is the world's key for the meter: the world ticked under ACTION4 twice and under ACTION3 once, so no key owns the meter, and the march is a shadow whose phase happens to align better on key(3) over this record. It is pixel-fitting with a measured price and I would trade it tomorrow for one expressible counter."
    [depends: two_counter_readings_survive_and_they_disagree_about_which_keys_pay  probe: passed]

  theorem the_march_is_exactly_one_command_early_and_that_is_the_whole_of_its_error "the world ticked (53,62) at t8 and (53,61) at t11. My march paints (53,62) at t7 and (53,61) at t9. Each firing is one ACTION3 ahead of the world's tick, and the manual then sits one cell wrong until the world catches up, at which point the frames coincide again -- transition 7 for the first, transition 10 for the second. That is why the divergences are one cell long and why they close. The alternative phase, key(4), lags instead of leads and closes more slowly. Neither is a theory of the cadence; the two counter readings are, and neither can be written down."
    [depends: the_march_moved_to_the_blanking_key_and_the_move_is_worth_three_transitions  probe: passed]

  theorem the_manual_structurally_lags_the_bar_by_one_cell_forever "the arm instantiates only cells that have varied. (53,60) has been colour 2 in all fourteen states, so it is board, no rule of mine can name it, and no guard I can write changes that. My march can replay a tick that has already been observed and can never predict a new one. From the current state I therefore predict that the next ACTION4 changes exactly twelve cells and that (53,60) does not move, while reading D and reading E both say it does. For the second round running I am pre-registering a prediction I expect to lose, because the arm leaves me no way to write the one I believe. Each cell the world converts hands me one more instance and one more cell of reach, so the lag is permanent but bounded at one cell."
    [depends: instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances  probe: passed]

  theorem the_three_probe_refutations_are_one_cell_of_drift_and_the_hashes_prove_it "P-06 pressed ACTION3 from a state my manual reconstructed exactly; the manual predicted 3bf51d2fd9036a78, the strip blanked with (53,61) still colour 2, and the world answered b278887e087d3593, the strip blanked with (53,61) converted. One cell. P-07 pressed ACTION4: the manual's inert hash was 3bf51d2fd9036a78, which is its own P-06 prediction, so the checker does not resync the manual between probes; the manual predicted bb5c436a2318c544 and the world answered 1317da5b367d300a, the same twelve-cell restore differing in the same one cell. P-08 pressed ACTION3 and returned byte-identical hashes to P-06 in every field -- same inert, same manual prediction, same observation -- which is exactly what my enumeration requires, since the manual was back at 'shown, (53,61) colour 2' and the world was at s12 whose ACTION3 successor s13 equals s11. Three refutations, one error, and that error is the structural lag above rather than anything wrong with the twelve-cell toggle, which has now survived eleven presses untouched."
    [depends: the_manual_structurally_lags_the_bar_by_one_cell_forever  probe: passed]

  theorem replay_is_open_loop_and_this_round_the_number_finally_re_tests_it "under resync the checker hands the manual the world's state before each transition; under open loop it does not. The verdict has stood since the five-transition record, where open loop scored 4 and resync scored 3. On the nine-transition record both scored 6 and the discrimination was lost, which I recorded. On this thirteen-transition record they separate again and by a wider margin: I walked both. Open loop matches transitions 1,2,3,4,5,7,10,11,12 and scores 9; resync matches 2,3,4,5,9,10,11,12 and scores 8. So certify's single count discriminates. One confound, and I name it rather than bury it: if colored(<off-board>, 3) returned true, my march would fire on (53,63) at transition 2 and open loop would also score 8. The three-way reading is that 9 means open loop with off-board silent, 7 means resync with off-board reading as a colour, and 8 leaves the two possibilities tied and needs another round."
    [depends: off_board_does_not_read_as_a_colour  probe: pending]

  theorem off_board_does_not_read_as_a_colour "the evidence is historical and I must be careful not to re-cite it as if it were fresh. Last round the seed rule and the then-key(4) march could both have been admitted on (53,63) in states 0 through 3, where it is colour 2 with no right neighbour, precisely if colored(off_board, 3) were true. Certify adjudicated all thirty state-action pairs, including those four, and reported no pair admitting two rules. Moving the march to key(3) dissolves that configuration, so a fresh zero-clash report this round will say nothing new about off-board. What does test it now is the replay count, as the previous theorem sets out. The assumption the old evidence carries is unchanged: that the ambiguity check tests admissibility and not outcome disagreement, since both rules would have recoloured to 3 and an outcome-based checker would have stayed silent."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_march_and_the_blanking_rule_cannot_both_fire_and_i_checked_all_twelve_studs "both are guarded on act=key(3) and colored(?p,2), so constraint 5 needs the rest of the guards disjoint on every instance in every reachable state, and I enumerated rather than hoped. Meter studs: (53,61) has (53,60) colour 2 to its left in every state, so the blanking guard's not-colored-leftof-2 is false and blanking never fires there; (53,62) and (53,63) are likewise blocked by a colour-2 left neighbour in every state where they are themselves colour 2, because the bar converts strictly right to left and so no state has a colour-3 cell to the left of a colour-2 one. Strip studs: their right neighbours are only ever 1, 2 or 4, so the march guard's colored-rightof-3 is false. Unselected-bar studs at rows 32-33: right neighbours are colour 2 or colour 5. Port stud (39,16): right neighbour is 1 or 4. The latent risk, and it is real, is that a state with (53,61) colour 3 and (53,62) colour 2 would admit both rules on (53,62); the monotone right-to-left order of the bar is what forbids it, and that order is witnessed three times, not proven."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: pending]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and (53,61), (53,62) and (53,63) all hold 2 rather than 3. The anatomy closes cell by cell: 22 Casing as the perimeter of rows 36-41 by cols 11-16 minus the two ports plus the 2x2 core at rows 38-39 cols 13-14; 12 Cavity as the 4x4 at rows 37-40 cols 12-15 minus that core; 8 Rail at rows 30-31 and 34-35 by cols 13-14; 4 Stud at rows 32-33 by cols 13-14; 8 Pip and 4 Stud in the lane B strip; 1 Pip at (38,16) and 1 Stud at (39,16) in the ports; 12 Erased as the lane A strip at rows 32-33 cols 17-22; 3 Stud in the meter. 22+12+8+9+12+12 = 75 = cells_needing_an_owner. The 24 remaining dynamic cells are the background of the unselected slot footprint, cols 11, 12, 15, 16 over rows 30-35, and 75+24 = 99 = dynamic_cells, and 4096-99 = 3997 = constant_cells. The dynamic set closes independently: the selector swap repaints 96 cells and the meter has ticked three times, 96+3 = 99. Certify has returned 0 unexplained of 4096 on this reconstruction three rounds running and the growth from 74 to 75 owners is exactly the one bar cell that converted."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0; a cell constant across the whole record gets none. The arithmetic has now been demonstrated four times: 73 owners at 97 dynamic, 74 at 98, and now 75 at 99, the difference each time being exactly one bar cell, and my Stud declaration moving by exactly one each time. This round it did something sharper than bookkeeping: the new instance at (53,61) changed the behaviour of a rule I did not edit, because the march suddenly had a twelfth Stud to land on. Level data is not inert with respect to the manual, and I will not again assume a rule's replay is stable across a store update."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_bar_runs_leftward_and_the_budget_is_measurable "three cells have converted, (53,63) then (53,62) then (53,61), so right-to-left is witnessed three times with no exception. Row 53 reads colour 2 from column 10 to column 60 in the window I am given and I have never been shown columns 0 to 9 of that row, so at least 51 and at most 61 cells remain. Thirteen commands have bought three ticks; both surviving readings put the rate near one tick per three counted commands, so of order 150 to 190 commands of bar remain. Probing is still cheap and the cheapness is now a measured quantity rather than a hope. What I still do not know is whether colour 3 means consumed or filled -- colour 3 is also what an unselected slot shows on its rails, which argues weakly for a resting or completed state -- and the two readings invert the sign of every ranking decision, so the playbook still may not rank on it."
    [depends: the_manual_structurally_lags_the_bar_by_one_cell_forever  probe: pending]

  theorem a_repeat_of_a_blanking_key_has_still_never_been_tried_and_is_now_worth_more "key(3) blanked a shown strip at t3, t7, t9, t11 and t13, key(7) blanked one at t5, key(4) restored a blanked one at t4, t6, t8, t10 and t12, twelve cells and cell for cell identical every time. Eleven presses, and every blank came from a shown strip and every restore from a blanked one, so hide-and-show and toggle-and-toggle remain indistinguishable. This has been my first-ranked probe for two rounds and four more commands went by without it. Its value has risen: my manual commits to complete inertness for a repeat of either blanking key from the current blanked state, since every strip cell is colour 4 and no blanking guard and no march guard can fire; a restore under a blanking key refutes hide-and-show outright; a tick with no other change proves the meter is a pure command counter independent of the strip; and if the press returns one frame rather than two it separates reading D from reading E, which nothing else cheap does. Four answers from one press, and it is the only press in the space my manual predicts to be null."
    [depends: two_counter_readings_survive_and_they_disagree_about_which_keys_pay  probe: pending]

  theorem the_extra_frame_count_is_the_only_visible_correlate_of_the_hidden_bit_and_it_is_now_load_bearing "every command in the record returned two frames except t5, the single ACTION7, which returned one. Last draft this was a curiosity. Reading D makes it structural: the counter that drives the bar advances on two-frame commands and not on the one-frame one, which is what makes 4, 8, 11 come out as a clean period of three when the raw command count shows four then three. That is either a real mechanism -- the frame count is the world telling me how many internal steps it took, and the meter counts internal steps -- or a coincidence on a single data point, since ACTION7 is the only command that ever returned one frame. A second ACTION7 that returns one frame again and does not tick makes reading D much stronger; one that returns two frames breaks the whole construction and leaves reading E alone."
    [depends: two_counter_readings_survive_and_they_disagree_about_which_keys_pay  probe: pending]

  theorem the_cadence_is_inexpressible_and_both_loopholes_are_still_shut "a guard reads a cell colour, its four neighbour colours, off-board, and the action name. Both surviving readings need a counter modulo three and the grammar has no counter and no latch. Loophole one, an object at the background colour used as an invisible bit: unusable, because the value grammar exposes only color as a field so no guard can read present, and the 24 colour-5 cells the arm would instantiate all sit in the slot footprint. Loophole two, a second type declared at colour 2 to reach the next bar cell: unusable, because the arm finds objects by colour alone and would duplicate all twelve Studs. I also considered using the strip itself as a phase register, since it is a two-cycle and the tick is a three-cycle, but the two never combine into a readable six-cycle because the blank and restore presses have not alternated regularly with respect to the counter. So the hidden bit stays prose and the march stays a shadow."
    [depends: the_world_is_not_a_function_of_the_visible_frame_and_it_is_now_witnessed_under_both_keys  probe: passed]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language can produce them. A guard sees a cell's own colour, its four immediate neighbour colours, off-board, and the action name -- no coordinate, no row band, no distance. The witness is inside the divergence report certify returned again this round: (30,16), (31,16), (32,16), (33,16) and (34,16) are all colour 5 in frame 0 with above 5, below 5, left 5, right 4, one indistinguishable guard reading, and the world makes them 6, 6, 1, 2, 6. Three answers to one question. A second pair kills colour as a discriminator: (30,13) is colour 3 and becomes 6 while (32,13) is colour 2 in an equally uniform bar neighbourhood and also becomes 6. Constraint 5 forbids two rules that both fire, so the swap does not go in the manual and the transition-0 mismatch is a cost I accept for the third round running."
    [depends: the_panel_is_a_column_of_slots  probe: passed]

  theorem the_swap_also_fails_the_compression_test "grant every expressibility obstacle removed and free reading of position. The swap still does not belong. It repaints 96 cells whose new colours follow no local law, because the widget is teleported six rows and no event in the vocabulary does that -- moved is one cell, jumped-over is two, jumped-to-a-landmark needs a landmark and a rule per instance. The shortest form I can construct is of order one landmark and one rule per repainted cell, in both directions, which is longer than the 96 pixels it explains. Constraint 3 refuses it independently of constraint 5. Two independent refusals, which is why I expect never to write the swap rather than merely not to have written it yet. The proportional cost of my silence has fallen again, from a ninth of the record to a thirteenth, purely because the record grew."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem a_background_object_would_own_exactly_the_swap_footprint_and_i_still_do_not_declare_it "an object declared at arc-colour 5 with arc-instances all would be placed on the colour-5 cells the board cannot explain, and those number exactly 99 minus 75 = 24: cols 11, 12, 15, 16 over rows 30-35, the unselected slot footprint, and not one cell more. The declaration is cheap and surgical. I still do not declare it, because it would explain no pixel the board does not already draw correctly and would enable no rule I can write, which is constraint 3 refusing it on its own terms. If a device ever appears that lets a guard read position, this is the first declaration to add."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_restore_and_blank_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "the restore rules guard on colour 4 alone and the blanking rules on one to three neighbour tests. Both are correct on all eleven blank-or-restore presses observed, because every press was made with the bottom slot selected, where the only colour-4 Pip and Stud instances in existence are the twelve blanked lane B cells. They would be wrong the moment slot A is selected: lane A strip cells become texture while lane B strip cells become arena fill of colour 4, and the instances do not move with the widget because I only ever recolour. My manual never reaches that state, being silent on the selector, so this costs zero transitions and certify cannot see it. It is written here because a searcher planning through a selector move would be misled by rules that score 132 of 132, and because reading D wants me to press a selector key next, which would walk straight into it."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have ever seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, a period-3 run offset by one column; the divergence report gives lane A row 32 cols 16-22 as the world drew it at t1, 1 2 1 1 2 1 1, and rows 32 and 38 agree because 6 divides by 3. The two port cells fit the same formula, which is an unforced success. So the two strips are two windows onto one texture, which is why a restore can rebuild twelve cells exactly, and why five restores have rebuilt them identically. Untested prediction: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2. No rule needs this, since each instance remembers its frame 0 colour, so the concept buys understanding rather than symbols and stays out of the word table."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, six times now, twelve cells every time. (38,16)=1 and (39,16)=2 sit on the widget right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since the left neighbour of each is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The rival explanation is that col 16 is where the 6x6 widget ends and the survival is coincidence; six blanks do not separate them."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots "the divergence report gives the world's t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at those columns read identically -- eighteen cells, six rows apart. Rows 42 to 52 are uniform background, so rows 36-41 is the bottom slot and rows 30-35 the one above it. ACTION1 moved selection from the bottom slot to the upper one and ACTION2 moved it back, one witness each for up and down, no wrap needed. Whether a third slot exists above is untested: (29,13) and (29,14) hold colour 3 and never vary, which is what a slot at rows 24-29 would show on its bottom rail, but board cells prove nothing about slots I have never selected. Two presses would settle it, and reading D now gives a second reason to spend one of them."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_badge_is_lane_aligned_and_the_matching_reading_stays_downgraded "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45. Those are exactly the rows an upper-slot cavity occupies within its six-row band, so the badge belongs to the lane of the slot at rows 30-35, and the bottom slot's lane has nothing at cols 42-45. The tempting reading is that it is a target the lane texture must be made to match, but the strip is 2 rows by 6 cols and the badge is 4 rows by 4 cols of one uniform colour, so shape refutes it. The surviving readings are that it marks which slot carries the task, that it is a destination, or that it is a picture of a completed cavity, the widget cavity being also 4x4 with a 2x2 core removed. Thirteen transitions and zero of them bear on any of the three; colour 14 appears nowhere else in the frame."
    [depends: the_panel_is_a_column_of_slots  probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot bar, a port, four strip cells and three meter cells -- four unrelated roles in one type, and the count grows whenever the bar converts. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 75 cells that need an owner against 75 pixels written out, with 0 unexplained confirmed three times. The cost is measured too, and it grew this round: no rule can name the strip, so every blanking rule carves it out of its colour class by neighbour tests, and the march now has to be kept off eleven Studs by a right-neighbour test that is a fact about the bar's geometry rather than about the meter. Those guards are pixel-fitting in a costume, and the march is the worst offender because its guard is an accident of what has already ticked."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, which is rows 29-54 by cols 10-63. They live in the 3997 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is where a title, target, score or instruction would live, and the likeliest home of whatever finishing means and of whether the bar is a budget or a score. Thirteen commands have not made one cell of it vary, which is mild evidence that it is decoration, but only mild, since ten of those thirteen commands were the same two keys."
    [depends: no_goal_section_on_purpose  probe: pending]

  theorem two_keys_have_never_been_pressed "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not, after fourteen commands. The budget argument now has a measured number behind it: of order 150 to 190 commands of bar remain, so two presses are affordable and are the cheapest untried source of a genuinely new frame. If either is a click carrying coordinates, this guard language cannot express it and the finding will be recorded as prose rather than as a rule. Each press also reads its own returned frame count, which reading D makes into a direct measurement of the counter."
    [depends: the_extra_frame_count_is_the_only_visible_correlate_of_the_hidden_bit_and_it_is_now_load_bearing  probe: pending]

  theorem no_goal_section_on_purpose "all fourteen states returned NOT_FINISHED and nothing in thirteen transitions indicates what finishing means. The live candidates are that a lane must be brought into some relation with the badge at its far end, that every slot in the column must be visited or solved, that the bar reaching one end ends the level, or that the objective lives in the rows I have never been shown. An absent goal compiles to is_goal implies False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. The bar is the only monotone quantity in the whole record and is therefore the most tempting goal, and it is exactly the one I cannot sign because I cannot tell filling from spending. Thirteen transitions of pressing the same two keys have produced no evidence either way, which is itself an argument for spending the next presses on keys and slots rather than on more toggling."
    [depends: the_bar_runs_leftward_and_the_budget_is_measurable  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "mdl_segmenter returns negative gain on both variants, -2989 bits at 4 tracks and -25963 at 69, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator rather than the world. Its obj1 is 108 cells of shape 2 by 54 present in all fourteen frames, which is rows 53 and 54 clipped to the window, the meter bar and the fill row beneath it, fused because colour 2 and colour 4 touch vertically and background 5 does not separate them; it corroborates that the bar is one object continuing left of column 10 where I have never seen it, and that my colour-class declarations cut across the world's own segmentation. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition, and its own verdict says the world does not narrate as one mover, which agrees with my event vocabulary of recolored alone. zero_space calls its evidence THIN in its own words -- 13 transitions constraining rank 5 of 693 features, null space of dimension 688 -- and its single global law spans 99 dynamic cells at once, which is what a 688-dimensional null space produces rather than what a conservation law looks like. Its cell list, ninety-six slot cells plus (53,61) (53,62) (53,63), is exactly my dynamic set and is the one thing in the stream I use. What I took from the engines this round is the store arithmetic, dynamic_cells 99, cells_needing_an_owner 75, and above all distinct_states 9."
    [probe: pending]

  theorem what_this_draft_pre_registers "the informative numbers first. Certify should return replay 9 of 13 if replay is open loop and off-board reads as nothing; first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6; further divergences at transition 6 under ACTION3 on the single cell (53,62) with manual 3 and world 2, at transition 8 under ACTION3 on (53,61) manual 3 world 2, and at transition 9 under ACTION4 on (53,61) manual 3 world 2; reconvergence at transition 10 with transitions 10, 11 and 12 all matching. A count of 8 means either resync replay or that off-board reads as colour 3, and those two stay tied; a count of 7 means both. Responsibility 0 unexplained of 4096. Unambiguous 0 clashes over 14 states by 3 actions, 42 pairs. Now the world. Repeat a blanking key from the current blanked state: my manual says not one cell changes; if the strip returns, hide-and-show is dead; if the bar ticks with nothing else, the meter is a pure command counter; and the returned frame count separates reading D from reading E. Press ACTION4: my manual says exactly twelve cells and readings D and E both say thirteen including (53,60), so I am betting against myself again on the record. Press a selector key: reading D says the bar ticks and reading E says selector presses are free, and this is the only clean separation of the two. Press key(5) or key(6) and anything at all is new."
    [depends: replay_is_open_loop_and_this_round_the_number_finally_re_tests_it  probe: pending]
