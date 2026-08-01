# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Twenty-six states, twenty-five transitions:
#   RESET, A1 A2 A3 A4 A5, then A2 A5 eleven times.
# BODY AT SPAWN, lattice (1,2). PANEL IN CONFIGURATION B. TWELVE meter cells
# burned, columns 52-63; 52 remain. Next command index is 26, EVEN.
# certify last round: replay 21/21 exact, 0 cells unexplained, 0 clashes.
#
# ========= WHAT CHANGED AT THE THEORY DESK THIS ROUND =========
# For five rounds this book said the same thing: the ranker scores expected
# bits over {manual, ablations, inert}; an ablation only ever predicts FEWER
# changes; so on any pair where the manual predicts IDENTITY every hypothesis
# agrees and the gain is ZERO. A MANUAL CANNOT PROBE ITS OWN SILENCES. At
# spawn only key 2 was live; at (2,2) only key 5 was live; the eleven-lap loop
# was forced. And this book ranked precisely the silences, so it was the exact
# NEGATION of what the ranker would ever choose.
#
# I said the lever was not mine. THAT WAS TOO STRONG AND I FOUND ONE.
#
#   THIRTEEN PANEL RULES CARRIED colored(spawn_probe, 5) -- "body not at home".
#   ELEVEN positive witnesses. ZERO negative witnesses, and the zero is
#   STRUCTURAL: every ACTION5 in the log was pressed from lattice (2,2), so the
#   conjunct was true BY CONSTRUCTION at every press. It described where the
#   presses happened, not what the world does. It explains no pixel.
#   IT IS DELETED. Replay unaffected; ambiguity re-audited by hand at all
#   thirteen body-home states in both panel configurations; 0 new clashes.
#
# CONSEQUENCE: AT SPAWN, TWO KEYS ARE NOW LIVE.
#   key 2 -> 48 body pixels.   key 5 -> 23 panel pixels.
# The ensemble can disagree at this state for the first time in 26 frames.
#
# THE RULE THIS TAUGHT, AND IT IS THE ONLY GENERAL THING THIS BOOK HAS EVER
# LEARNED ABOUT ITSELF:
#   TO MOVE A PROBE FROM THIS BOOK INTO THE RANKER'S REACH, DO NOT ARGUE FOR
#   IT IN PROSE. FIND THE UNWITNESSED CONJUNCT HOLDING THE MANUAL SILENT
#   THERE AND DELETE IT. Where no such conjunct exists -- keys 3, 4, 6, 7 have
#   no rule to un-guard -- the silence is real ignorance and prose is all I
#   have.
#
# I DID NOT take the other lever, and the distinction is the whole of my
# honesty here: deleting an unwitnessed RESTRICTION on rules with eleven
# witnesses each is legitimate; adding an unwitnessed RULE (e.g. "A2 moves the
# body from lattice (2,2)", zero witnesses of any kind) is fabrication, and it
# stays refused for the sixth round.
#
# ========= THE PROBE THAT IS NOW BUYABLE, AND WHAT IT PAYS =========
# ACTION5 AT SPAWN. Four distinct outcomes, all legible in the RAW DIFF:
#   (a) 23 panel pixels change, no body pixel, no burn
#       -> the guard was fake, I was right, and thirteen rules generalise.
#   (b) nothing changes
#       -> the guard was real; I am refuted by 23 cells and put it back.
#   (c) panel toggles AND (63,51) burns
#       -> the meter runs on command PARITY, not on the key. Reading A dies.
#          This is the separator that six rounds of loop could never buy,
#          because the loop pinned key-2-ness and even-ness to the same
#          predicate. Index 26 is even. THIS IS THE WINDOW.
#   (d) panel toggles AND the body moves
#       -> ACTION5 is not "return to spawn"; the north/return/swap question
#          that eleven identical presses could not split is split.
# Under reading A it costs NO meter cell. There is no cheaper experiment on
# this board and there has not been one for six rounds.
#
# ========= heuristic_miss, ANSWERED FOR THE SEVENTH TIME =========
# Declaring a goal is NOT the highest-value edit, for an arithmetic reason:
#   THE PLAN TIER REACHES A GOAL BY SEARCHING MY COMPILED RULES, AND MY RULES
#   CAN ONLY REACH TWO LATTICE CELLS AND TWO PANEL CONFIGURATIONS.
# So the only goal that could return sat is one satisfied inside the loop, and
# sat-inside-the-loop is WORSE than unsat: unsat leaves the arm probing, sat
# makes it commit and declare success one lattice cell from spawn. Every
# candidate the grammar admits over the four instanced types, re-checked with
# this round's counts: count(Glyph9,color=5)=24 and count(Vacated,color=9)=24
# both mean only "body is off spawn"; count(Dark,color=9)=3 means only "panel
# is in configuration B"; count(Glyph9,color=1)=64 exceeds the 47 instances
# that exist and =47 is unreachable by any rule; count(Spent)=0 is
# constant-false.
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
# ========= THE PROBE NUMBERS ARE PERIOD-FOUR. I WAS WRONG LAST ROUND. =========
# I claimed expected_bits MOVES with the state while realised gain is pinned.
# It does not move. The four probes this round report 1.394848870026,
# 2.2195282823, 1.955012006402, 2.273661689922 -- BIT FOR BIT the same four
# numbers, in the same order, as last round's four. Aligned against the panel:
#   action 2 from config B -> 1.394848870026 (t18, t22)
#   action 5 from config B -> 2.2195282823   (t19, t23)
#   action 2 from config A -> 1.955012006402 (t20, t24)
#   action 5 from config A -> 2.273661689922 (t21, t25)
# EXPECTED BITS IS A FUNCTION OF (KEY, PANEL CONFIGURATION) AND NOTHING ELSE.
# It does not see the meter, which burned two more cells between the rounds.
# Both the prior and the posterior measure my manual's fixed geometry.
#   A GAIN THAT CAN BE PREDICTED FROM THE PANEL ALONE IS NOT A MEASUREMENT.
#
# ========= THE COST OF THE LOOP, IN THE ONLY CURRENCY THAT MOVES =========
# Row 63 is the ONLY monotone quantity. Body position cycles; the panel
# cycles; 26 states but only 24 distinct, and the two collisions are the
# ancient sterile pairs -- every later state is nominally new ONLY because one
# more meter cell burned. 12 gone, 52 left, one per lap, two commands per lap.
# About 104 commands of loop remain before row 63 is fully colour 1. What
# happens then is not in evidence and I will not guess.
#
# ========= THE RANKED LIST =========
# 1. ACTION5 AT SPAWN. Now priced above zero by the ranker's own arithmetic
#    (see above). Four outcomes, free under reading A, splits the meter at an
#    even index, splits north-vs-return, tests thirteen rules at once.
# 2. THE EAST KEY, TESTED AT SPAWN. ACTION3 first, ACTION4 only if 3 is inert.
#    A2 is south (11 witnesses). A1 was pressed AT SPAWN with east OPEN and
#    moved nothing, so A1 is not east. EAST IS A3 OR A4, no third candidate.
#    Both were pressed once, from one cell south where east AND west are void,
#    so neither press could answer anything. Step one of the only route to the
#    knob. STILL PRICED AT ZERO by the ranker; no conjunct exists to delete.
# 3. ACTION2 PRESSED ONE CELL SOUTH OF SPAWN. Manual predicts NOTHING -- no
#    Glyph9 renders 9 there, no Vacated renders 5 -- and that is almost
#    certainly false: rows 20-24 are floor from column 13 to 31 and one A2
#    press has moved the body one lattice cell south eleven times running.
#    The ONE command likely to put the body in a lattice cell never occupied.
#    I will not buy it with a fabricated rule.
# 4. ACTION6 OR ACTION7. Never pressed, entirely unconstrained. In this family
#    one is usually a click, and the knob is a 3x3 target the body appears
#    unable to stand on. My manual could record such a command's EFFECT and
#    never its precondition -- but the effect is what makes the comb dynamic
#    and the goal writable. Honest risk: actions_used lists only what has been
#    tried, so it is no evidence these exist.
#
# ========= WHAT NOT TO PRESS =========
#   A2 at spawn: buys the guaranteed constant. 48 body pixels drawn correctly
#   eleven times over; the only divergent cell is (63,51), which no manual in
#   this language can draw; gain returns 5.087463 for the ninth time and
#   expected_bits returns 1.394848870026 for the third. Guaranteed refutation,
#   guaranteed wasted round, one more burned meter cell.
#   A5 from one cell south is pure loop; A5 from spawn is item 1 above and is
#   a different experiment entirely.
#   A1 at spawn: witnessed inert at t1.
#   A4 at spawn: the same experiment as A3 with the labels swapped, but it
#   spends a meter cell under BOTH readings -- press it only if A3 is inert.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The next burn cell (63,51) is undrawable: one pixel per press of key 2
#     or 4, forever. A refutation whose divergence set is exactly that cell
#     implicates nothing.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on cells that have never changed, and 24 departure pixels for
#     which no rule in that direction is witnessed. 24 for the second step in
#     the same direction, 0 after that.
#   * NEW THIS ROUND, and it is mine: if ACTION5 at spawn changes nothing, I
#     am refuted by 23 panel cells and the spawn_probe guard goes back into
#     all thirteen rules. I priced that before pressing.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.

order     delete_an_unwitnessed_guard_before_complaining_that_a_probe_is_unbuyable [proof: lean]
order     distinguish_deleting_a_restriction_from_inventing_a_rule       [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition      [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     prefer_a_probe_with_four_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     split_the_meter_readings_at_an_even_index_while_a_window_exists [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell          [proof: lean]
order     buy_a_third_lattice_cell_before_attempting_to_write_a_goal     [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language [proof: lean]
order     treat_a_repeated_identical_information_gain_as_zero_gain       [proof: lean]
order     treat_a_gain_predictable_from_the_panel_alone_as_no_measurement [proof: lean]
order     discount_any_gain_that_comes_from_a_cell_with_no_instance      [proof: lean]
order     prefer_a_command_that_closes_three_open_questions_over_one     [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     break_a_repeating_command_cycle_before_optimising_within_it    [proof: lean]
order     test_a_shared_guard_where_it_has_never_been_false              [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance             [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation    [proof: lean]
order     prefer_a_key_that_adds_no_new_prediction_debt                  [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it             [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal   [proof: lean]
order     spend_a_meter_cell_only_on_a_question_it_actually_closes       [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it     [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it [proof: lean]
order     reaudit_ambiguity_by_hand_after_any_guard_deletion             [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them         [proof: lean]

prune     action_whose_expected_bits_are_zero_only_because_the_manual_is_silent => keep [proof: lean]
prune     rule_proposed_with_zero_witnesses_of_any_kind => dead                  [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead                    [proof: lean]
prune     goal_that_becomes_true_at_a_state_that_is_not_a_win => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_cells_already_visited => dead [proof: lean]
prune     divergence_lies_only_on_the_unburned_meter_frontier => dead            [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key => dead   [proof: lean]
prune     expected_bits_predictable_from_the_panel_configuration_alone => dead   [proof: lean]
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

heuristic guards_carried_with_no_negative_witness_anywhere_in_the_log       [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic actions_priced_at_zero_expected_bits_by_the_manuals_own_silence   [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
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

prefer    a_state_where_more_than_one_key_has_a_rule_that_can_fire           [ev: 13/26 states]
prefer    a_command_that_tests_a_guard_shared_by_thirteen_rules_at_once      [ev: 1/1 available]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index          [ev: 25/25 transitions tie]
prefer    a_command_that_would_put_the_body_in_a_lattice_cell_never_occupied [ev: 2/11 reachable cells seen]
prefer    a_command_that_would_turn_a_machinery_pixel_dynamic                [ev: 0/26 states]
prefer    a_key_that_names_a_direction_whichever_way_it_answers              [ev: 2/2 candidates]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed      [ev: 2/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on               [ev: 3/5 keys at spawn]
prefer    a_command_that_leaves_the_cycle_the_last_twenty_one_commands_formed [ev: 21/24 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 25/25 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    a_free_probe_over_one_that_costs_a_meter_cell                      [ev: 12/25 commands burned]
