# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Twenty-two states, twenty-one transitions:
#   RESET, A1 A2 A3 A4 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5.
#   t1  A1 at spawn        -> nothing
#   t2  A2 at spawn        -> body one lattice cell SOUTH (48) + burn (63,63)
#   t3  A3 one cell south  -> nothing (east and west both void there)
#   t4  A4 one cell south  -> burn (63,62) and nothing else
#   t5  A5 one cell south  -> body to spawn (48) + panel A->B (23)
#   t6..t21  the same two commands, EIGHT more times, alternating.
#   Burns since: (63,61) (63,60) (63,59) (63,58) (63,57) (63,56) (63,55) (63,54)
# BODY AT SPAWN, lattice (1,2). PANEL IN CONFIGURATION B. TEN meter cells
# burned, columns 54-63; 54 remain. Next command index is 22, EVEN.
# certify this round: replay 17/17 exact, 0 cells unexplained, 0 clashes.
# THE MANUAL IS SOUND. THE PROBLEM IS NOT THE MANUAL'S ACCURACY.
#
# ========= THE FINDING THAT CHANGES WHAT THIS BOOK IS FOR =========
# The probe ranker scores expected bits over {manual, ablations, inert}.
# An ablation DELETES rules, so it predicts a SUBSET of the manual's changes.
# Therefore on any pair where the manual predicts IDENTITY, all 34 hypotheses
# agree and the expected gain is ZERO.
#
#   A MANUAL CANNOT PROBE ITS OWN SILENCES.
#
# At spawn, exactly one key has a live rule: key 2.
# At lattice (2,2), exactly one key has a live rule: key 5.
# So the nine-lap loop is not a taste, not the meter, and not bad luck --
# IT IS THE RANKER FOLLOWING THE ONLY NON-SILENT ACTION AT EACH OF THE TWO
# STATES MY RULES CAN REACH. Seventeen consecutive commands from {A2, A5}.
#
# AND THE COROLLARY THAT INDICTS THIS BOOK:
#   THE PLAYBOOK AND THE RANKER ARE EXACTLY ANTI-ALIGNED.
#   I rank by "keys whose inertness rests on no witness" -- i.e. by actions
#   the manual predicts SILENT. The ranker prices exactly those at zero.
#   Every command ranked below is a command the ranker ranks last, by
#   construction. Five rounds of prunes have bound nothing and this is why.
#
# I am NOT going to fix this by writing an unwitnessed rule so that some other
# key predicts pixels. That is the fabrication constraint 2 exists to stop and
# a manual that games its own ranker can be checked by nothing. The lever is
# not mine. It belongs to whoever can (a) score an UNWITNESSED silence above a
# witnessed noise, or (b) hand the plan tier a goal, or (c) override the arm.
# The list below is written FOR THAT READER.
#
# ========= A SECOND CORROLARY: THE METER QUESTION IS SEALED =========
# The loop presses key 2 at every EVEN index and key 5 at every ODD index.
# Reading A (burn iff key 2 or 4) and reading B (burn iff even index) are the
# same predicate on the loop. Ten burns, eleven non-burns, zero divergence,
# and NO COMMAND THE RANKER CAN CHOOSE WILL EVER SPLIT THEM. I stop treating
# this as evidence that will thicken with time.
#
# ========= heuristic_miss, ANSWERED FOR THE SIXTH TIME =========
# Declaring a goal is NOT the highest-value edit, for an arithmetic reason:
#   THE PLAN TIER REACHES A GOAL BY SEARCHING MY COMPILED RULES, AND MY RULES
#   CAN ONLY REACH TWO LATTICE CELLS AND TWO PANEL CONFIGURATIONS.
# So the only goal that could return sat is one satisfied inside the loop, and
# sat-inside-the-loop is WORSE than unsat: unsat leaves the arm probing, sat
# makes it commit and declare success one lattice cell from spawn. All four
# candidates the grammar admits over the four instanced types fail:
# count(Glyph9,color=5)=24 and count(Vacated,color=9)=24 both mean only "body
# is off spawn"; count(Glyph9,color=1)=64 exceeds the 45 instances that exist;
# count(Spent)=0 is constant-false.
#   THE GOAL IS NOT THE BOTTLENECK. THE MISSING TRANSITION IS.
#   ONE OBSERVATION FIXES BOTH: THE BODY IN A THIRD LATTICE CELL.
#
# THE WIN, carried in prose because the DSL cannot hold it:
#   WIN = the body stands in lattice (8,7), rows 50-54 columns 44-48, so its
#   24 ring pixels render 9 and its aperture shows the pip at (52,46). Drawn
#   as three colour-9 walls with the west side open: a socket cut to the body.
#   ROUTE = lattice column 2 is the only north-south corridor and the comb at
#   (6,2) blocks it, 23 of its 25 pixels colour 8. The comb is wired by one
#   connected colour-8 line to a 3x3 knob at lattice (1,6), reachable
#   eastward along R=1 from spawn through (1,3), (1,4), (1,5), all open floor.
#
# ========= THE COST OF THE LOOP, IN THE ONLY CURRENCY THAT MOVES =========
# Row 63 is the ONLY monotone quantity in this world. Body position cycles;
# the panel cycles; 22 states but only 20 distinct, and the two collisions are
# the ancient sterile pair -- every later state is nominally new ONLY because
# one more meter cell burned. 10 gone, 54 left, one per lap, two commands per
# lap. About 108 commands of loop remain before row 63 is fully colour 1.
# What happens then is not in evidence and I will not guess.
#
# ========= THE RANKED LIST, FOR A READER WHO CAN ACT ON IT =========
# Every item here is priced at ZERO expected bits by the current ranker. That
# is the point: they are the four places the manual is most likely wrong.
#
# 1. THE EAST KEY, TESTED AT SPAWN. ACTION3 first, ACTION4 only if 3 is inert.
#    - Names a direction whichever way it answers. A2 is south (9 witnesses).
#      A1 was pressed AT SPAWN with east OPEN and moved nothing, so A1 is not
#      east. EAST IS A3 OR A4 and there is no third candidate. Both were
#      pressed once, from one cell south where east AND west are void, so
#      neither press could answer anything.
#    - Splits the meter at an even index -- the only kind of command that can.
#      READ IT OFF THE RAW DIFF, NOT OFF A REFUTATION FLAG.
#    - Kills a forged silence: three of five spawn silences have no witness.
#    - Is step one of the only route to the knob, four lattice cells east
#      along a row that is open floor the whole way.
#
# 2. ACTION5 AT SPAWN. Thirteen rules share colored(spawn_probe,5): NINE
#    positive witnesses, ZERO negative, because A5 has never been pressed with
#    the body at home. The body is at home NOW and the panel is in
#    configuration B -- exactly the configuration in which the five reverse
#    rules would fire if the guard were not blocking them. Manual predicts
#    identity. If the panel toggles anyway, THIRTEEN RULES ARE WRONG AT ONCE,
#    and it costs no meter cell. Unclaimed for five rounds.
#
# 3. ACTION2 PRESSED ONE CELL SOUTH OF SPAWN. The manual predicts NOTHING
#    happens -- no Glyph9 renders 9 there, no Vacated renders 5 -- and that is
#    almost certainly false: rows 20-24 are floor from column 13 to column 31
#    and one A2 press has moved the body one lattice cell south nine times
#    running. The body has stood on that cell nine times and nobody has tried.
#    THIS IS THE SILENCE THAT CLOSES THE CYCLE: because the manual asserts it,
#    the ranker prices it at zero, so key 5 is forced at every odd index.
#    It is the ONE command likely to put the body in a lattice cell never
#    occupied, and it is half the separator between "A5 is north" and "A5 is
#    return to spawn".
#
# 4. ACTION6 OR ACTION7. Never pressed, entirely unconstrained. In this family
#    one is usually a click, and the knob is a 3x3 target the body appears
#    unable to stand on. My manual could record such a command's EFFECT and
#    never its precondition -- but the effect is what makes the comb dynamic
#    and the goal writable. Honest risk: actions_used lists only what has been
#    tried, so it is no evidence these exist.
#
# ========= WHAT NOT TO PRESS, AND WHY IT WILL BE PRESSED ANYWAY =========
#   A2 at spawn: it will score the guaranteed constant and buy NOTHING. The 48
#   body pixels are drawn correctly nine times over; the only divergent cell
#   is (63,53), which no manual in this language can draw. Guaranteed
#   refutation, guaranteed wasted round, one more burned meter cell.
#   I PREDICT IT WILL BE THE NEXT COMMAND ANYWAY, and I have written that
#   prediction into the manual so it can cost me.
#   A5 from one cell south is pure loop; A5 from spawn is item 2 above.
#   A1 at spawn: witnessed inert at t1.
#   A4 at spawn: the same experiment as A3 with the labels swapped, but it
#   spends a meter cell under BOTH readings -- press it only if A3 is inert.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The next burn cell (63,53) is undrawable: one pixel per press of key 2
#     or 4, forever. A refutation whose divergence set is exactly that cell
#     implicates nothing.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on cells that have never changed, and 24 departure pixels for
#     which no rule in that direction is witnessed. 24 for the second step in
#     the same direction, 0 after that.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.
#
# ========= A NOTE ON THIS DESK =========
#   The emit-all-three-blocks discipline held and certify came back clean on
#   every check. The remaining loss is no longer at my desk, and I have
#   stopped writing prunes as though they were filters. This book is now
#   addressed to whoever holds the ranker.

order     score_an_unwitnessed_silence_above_a_witnessed_repetition        [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     buy_a_third_lattice_cell_before_attempting_to_write_a_goal       [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language   [proof: lean]
order     treat_a_repeated_identical_information_gain_as_zero_gain         [proof: lean]
order     trust_a_realised_gain_less_when_the_expected_gain_moved_and_it_did_not [proof: lean]
order     discount_any_gain_that_comes_from_a_cell_with_no_instance        [proof: lean]
order     prefer_a_command_that_closes_three_open_questions_over_one       [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     break_a_repeating_command_cycle_before_optimising_within_it      [proof: lean]
order     test_a_shared_guard_where_it_has_never_been_false                [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one   [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation      [proof: lean]
order     prefer_a_key_that_adds_no_new_prediction_debt                    [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal     [proof: lean]
order     spend_a_meter_cell_only_on_a_question_it_actually_closes         [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it   [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them           [proof: lean]

prune     action_whose_expected_bits_are_zero_only_because_the_manual_is_silent => keep [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead                    [proof: lean]
prune     goal_that_becomes_true_at_a_state_that_is_not_a_win => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_cells_already_visited => dead [proof: lean]
prune     divergence_lies_only_on_the_unburned_meter_frontier => dead            [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key => dead   [proof: lean]
prune     repeats_the_two_command_cycle_that_returns_the_body_to_spawn => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead        [proof: lean]
prune     no_rule_it_could_witness_can_still_ground_in_this_census => dead       [proof: lean]
prune     spends_a_meter_cell_and_closes_no_open_question => dead                [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead        [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                   [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead          [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead        [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead            [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                      [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead         [proof: lean]
prune     tests_a_direction_at_a_cell_where_that_direction_is_void => dead       [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead         [proof: lean]
prune     meter_exhausted and not goal => dead                                   [proof: lean]

heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic actions_priced_at_zero_expected_bits_by_the_manuals_own_silence   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic rules_sharing_a_guard_that_one_command_could_refute_together      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic prediction_debt_a_command_would_add_to_the_rolled_forward_state   [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                   [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]

prefer    a_state_where_more_than_one_key_has_a_rule_that_can_fire           [ev: 0/22 states]
prefer    a_command_that_would_put_the_body_in_a_lattice_cell_never_occupied [ev: 2/11 reachable cells seen]
prefer    a_command_that_would_turn_a_machinery_pixel_dynamic                [ev: 0/22 states]
prefer    a_key_that_names_a_direction_whichever_way_it_answers              [ev: 2/2 candidates]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index          [ev: 21/21 transitions tie]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed      [ev: 3/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on               [ev: 3/5 keys at spawn]
prefer    a_command_that_leaves_the_cycle_the_last_seventeen_commands_formed [ev: 17/20 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 21/21 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    a_free_probe_over_one_that_costs_a_meter_cell                      [ev: 10/21 commands burned]
