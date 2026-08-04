# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# ELEVEN states, TEN transitions:
#   RESET, A1, A2, A3, A4, A5, A5, A2, A5, A2, A5.
# BODY AT SPAWN, lattice (1,2). PANEL IN CONFIGURATION B. FIVE meter cells
# burned, columns 59-63; 59 remain, about 118 commands.
# NEXT COMMAND INDEX IS 11, WHICH IS ODD.
#
# THE CURRENT STATE IS PIXEL-IDENTICAL TO THE t7 STATE EXCEPT FOR TWO MORE
# BURNED METER CELLS. That sentence is the whole problem with this round.
#
# ========= WHAT THE LAST FOUR COMMANDS BOUGHT =========
# ONE THING, AND I ASKED FOR IT IN WRITING.
# Last round I staked the timer on an odd-index key-2 press and named both
# diffs in advance: 48 cells means the timer holds, 49 with (63,60) burned
# means the timer is dead. t7 RETURNED 48. t9 RETURNED 48.
#   THE METER IS A TWO-COMMAND TIMER: 10/10 this episode, burns at indices
#   2,4,6,8,10 under FOUR different keys, none at 1,3,5,7,9 under three.
# t8 and t10 also killed my labelled proxy (key 5 burns only at home) and
# t8 re-witnessed the five reverse panel rules, which had been carrying
# pre-RESET evidence. Both were priced in advance; neither is news.
#
# ========= WHAT THEY DID NOT BUY =========
# t7, t8, t9, t10 = A2, A5, A2, A5 = the loop, twice.
#   t9 is t2 EXACTLY: same cell, same panel, same 48-pixel diff.
#   t7, t8, t10 differ from t2 and t5 only in which way the panel toggles.
# ELEVEN STATES AND THE BODY HAS OCCUPIED TWO OF ELEVEN REACHABLE LATTICE
# CELLS. ZERO machinery pixels have moved. The manual now predicts both loop
# commands TO THE PIXEL, so every further press of either is worth exactly
# nothing and costs half a meter cell.
#
# ========= WHY THE LOOP IS FORCED, SAID PLAINLY ONE MORE TIME =========
# The ranker scores expected bits over {manual, ablations, inert}; an ablation
# only ever predicts FEWER changes; so wherever the manual predicts IDENTITY
# every hypothesis agrees and the gain is ZERO. At spawn only key 2 has a live
# rule; at (2,2) only key 5 does. THE RANKER CANNOT BUY AN EXPERIMENT THE
# MANUAL IS SILENT ABOUT, AND THE DSL FORBIDS ME FROM WRITING AN UNWITNESSED
# HYPOTHESIS AS A RULE. That is a closed loop between the two halves of the
# system and I cannot open it from this desk without fabricating. I will not
# fabricate. I have now recorded this for five consecutive rounds and the
# selector has taken the forced move every time; I record that as a fact about
# the arm, not about the world.
#
# ========= THE ONE HONEST THING I DID TO THE BOOKS =========
# meter_burn_key5_away_late carries a conjunct with NO MEANING -- "at least
# three cells already burned to my right" -- fitted to separate t8 and t10
# from t5, which are otherwise identical in body position, panel, and action.
# I labelled it a LOOKUP in the manual rather than letting it read as physics.
# All five burn rules are RETRODICTIVE ONLY: the frontier (63,58) is a board
# cell with no instance, so none of them can ever fire forward again.
#
# THE WIN, carried in prose because the DSL cannot hold it:
#   WIN = the body stands in lattice (8,7), rows 50-54 columns 44-48, so its
#   24 ring pixels render 9 and its aperture shows the pip at (52,46). Drawn
#   as three colour-9 walls with the west side open: a socket cut to the body.
#   ROUTE = lattice column 2 is the only north-south corridor and the comb at
#   (6,2) blocks it, 23 of its 25 pixels colour 8. The comb is wired by one
#   connected colour-8 line to a 3x3 knob at lattice (1,6), reachable
#   eastward along R=1 from spawn through (1,3), (1,4), (1,5), all open floor.
#   THE EAST KEY IS STILL UNNAMED AFTER THIRTY-FIVE COMMANDS.
#   IT IS ACTION3, ACTION4, ACTION6 OR ACTION7. ACTION1 IS ELIMINATED: it was
#   pressed AT SPAWN with east open and moved nothing.
#   ACTION3 and ACTION4 were each pressed once, from (2,2), where east AND
#   west are both void -- so NEITHER PRESS COULD HAVE ANSWERED ANYTHING, and
#   my two inert rules for them are transcriptions of a cell where every key
#   is inert.
#
# ========= THE RANKED LIST =========
# 1. ACTION3 AT SPAWN. The east key, tested for the first time at a cell where
#    east EXISTS: lattice (1,3) is rows 8-12 columns 20-24, all floor. Whichever
#    way it answers it eliminates a candidate. If it moves the body, the
#    reachable set goes from 2 cells to 11, the knob comes into range, and the
#    goal becomes writable. STILL PRICED AT ZERO by the ranker and there is no
#    conjunct I can delete that would change that; I say so rather than
#    pretending otherwise.
# 2. ACTION4 AT SPAWN. Same experiment, other label. Under the timer it costs
#    exactly what ACTION3 costs.
# 3. ACTION2 PRESSED ONE CELL SOUTH OF SPAWN, at lattice (2,2). My manual
#    asserts NOTHING HAPPENS -- no Glyph9 renders 9 there, no Vacated renders
#    5 -- and that is almost certainly false: rows 20-24 are floor from column
#    13 to 31 and one A2 press has moved the body one lattice cell south
#    fifteen times running. The single command likeliest to seat the body in a
#    cell never occupied, which is the observation that makes a goal writable.
#    Not buyable with a fabricated rule.
# 4. ACTION6 OR ACTION7. Never pressed in thirty-five commands, entirely
#    unconstrained. In this family one is usually a click, and the knob is a
#    3x3 target the body appears unable to stand on. My manual could record
#    such a command's EFFECT and never its precondition -- but the effect is
#    what turns comb pixels dynamic. Honest risk: actions_used lists only what
#    has been tried, so it is no evidence these exist.
# 5. ANYTHING ELSE.
# 6. ACTION2 AT SPAWN. Third identical press, predicted to the pixel, worth
#    nothing. This is what will be taken.
#
# ========= WHAT NOT TO PRESS =========
#   A5 from (2,2): pure loop, and the panel rules it would re-witness are now
#   witnessed in both directions in this episode.
#   A1 at spawn: witnessed inert at t1 and it is eliminated as east.
#   A2 at spawn a fourth time: the timer question it once split is closed.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The index-12 command WILL burn (63,58) and I cannot draw it: no instance
#     sits on a cell that has never changed. One cell of divergence,
#     implicating nothing. This exact failure will recur every second command
#     for the rest of the episode.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on cells that have never changed, and 24 departure pixels for
#     which no rule in that direction is witnessed. 24 for the second step in
#     the same direction, 0 after that.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.

order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]
order     count_witnesses_by_distinct_states_not_by_presses_of_a_cycle      [proof: lean]
order     delete_a_rule_the_world_has_refuted_in_the_round_it_refutes_it    [proof: lean]
order     label_a_fitted_threshold_as_a_lookup_wherever_the_law_is_unsayable [proof: lean]
order     treat_deleting_an_unwitnessed_conjunct_as_an_experiment_to_price  [proof: lean]
order     distinguish_deleting_a_restriction_from_inventing_a_rule          [proof: lean]
order     rank_by_information_per_command_now_that_no_command_is_free       [proof: lean]
order     treat_a_pixel_identical_repeat_of_an_earlier_state_as_zero_gain   [proof: lean]
order     read_a_settled_question_off_the_raw_diff_and_then_stop_asking_it  [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition         [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     test_a_direction_only_at_a_cell_where_that_direction_exists       [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell             [proof: lean]
order     buy_a_third_lattice_cell_before_attempting_to_write_a_goal        [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language    [proof: lean]
order     discount_any_gain_that_comes_from_a_cell_with_no_instance         [proof: lean]
order     prefer_a_command_that_closes_three_open_questions_over_one        [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     break_a_repeating_command_cycle_before_optimising_within_it       [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     recite_every_rule_against_the_log_that_actually_exists            [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal      [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it    [proof: lean]
order     reaudit_ambiguity_by_hand_after_adding_any_rule_to_a_live_key     [proof: lean]

prune     action_whose_expected_bits_are_zero_only_because_the_manual_is_silent => keep [proof: lean]
prune     rule_proposed_with_zero_witnesses_of_any_kind => dead                  [proof: lean]
prune     rule_whose_witnesses_all_come_from_one_repeating_cycle => suspect       [proof: lean]
prune     guard_conjunct_the_world_has_since_witnessed_negatively => keep         [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead                     [proof: lean]
prune     goal_that_becomes_true_at_a_state_that_is_not_a_win => dead             [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_cells_already_visited => dead  [proof: lean]
prune     divergence_lies_only_on_the_unburned_meter_frontier => dead             [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead           [proof: lean]
prune     state_pixel_identical_to_one_already_probed_by_that_key => dead         [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key => dead    [proof: lean]
prune     ranking_that_still_assumes_a_key_free_of_meter_cost => dead             [proof: lean]
prune     repeats_the_two_command_cycle_that_returns_the_body_to_spawn => dead    [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead         [proof: lean]
prune     no_rule_it_could_witness_can_still_ground_in_this_census => dead        [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead         [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                    [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead         [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead             [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                       [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead          [proof: lean]
prune     tests_a_direction_at_a_cell_where_that_direction_is_void => dead        [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead          [proof: lean]
prune     meter_exhausted and not goal => dead                                    [proof: lean]

heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic actions_priced_at_zero_expected_bits_by_the_manuals_own_silence   [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic states_visited_that_are_pixel_identical_to_an_earlier_one         [admissible: lean]
heuristic rules_still_carrying_only_pre_reset_or_fitted_evidence            [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic meter_cells_remaining_as_a_uniform_budget_on_every_command        [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]

prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 3/3 unassigned keys]
prefer    a_key_tested_at_a_cell_where_the_direction_it_might_name_exists  [ev: 0/2 presses so far]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 2/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 2/5 keys at spawn]
prefer    a_command_that_would_put_the_body_in_a_lattice_cell_never_occupied [ev: 2/11 reachable cells seen]
prefer    a_command_that_would_turn_a_machinery_pixel_dynamic              [ev: 0/11 states]
prefer    a_command_that_leaves_the_cycle_the_manual_forces                [ev: 2/10 transitions]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 10/10 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
prefer    a_reset_over_a_stall_once_the_timer_is_nearly_spent              [ev: 1/1 resets refilled it]
