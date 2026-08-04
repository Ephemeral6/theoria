# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: six states, five transitions (RESET, A1, A2, A3, A4, A7). Widget in
# configuration W0 -- colour-3 bar in the TOP slot, hollow colour-6 box in the
# BOTTOM slot. BOTH readouts blank (colour 4). (53,63) advanced to 3 at t4.
# 97 cells have ever changed and all 97 are owned by the seven declared types.
#
# THE MANUAL WAS REPLACED, NOT PATCHED. The book I was handed described a
# different world; certify gave it 0/5 replay and a divergence at t=0. Gone.
#
# THE DEDUCTION EVERYTHING RESTS ON: states=6, distinct_states=5 forces
# S0 = S2. So ACTION2 undid ACTION1 and the CURRENT widget is the FRAME-0
# widget -- which is how frame 0 was read without being shown.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in any state. Zero constraint.
#   * ACTION2 in W0: never pressed. My manual says "nothing happens" on zero
#     witnesses. Largest forged silence in the file; it covers 18 rules.
#   * Whether ACTION4 advances the meter always, or only when it lights the
#     readout, or whether the meter runs on the command index. One witness
#     cannot split three readings, and the index reading is inexpressible.
#   * ACTION3 vs ACTION7: identical net effect, 2 frames vs 1. Not the same
#     action inside; cascade single_frame throws away the only evidence.
#   * The win condition. Nothing countable separates a win from here.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * (53,62) is board, holds no instance, is UNDRAWABLE. Every meter advance
#     after the first costs exactly one pixel of accuracy, permanently.
#   * The 24 background-coloured Field cells may not be seated. If not, t1 and
#     t2 each diverge by exactly those 24 and no rule of mine is wrong.
#   * ACTION1 now is predicted at 72 cells, NOT 96, because swapping two
#     identical blank readouts changes nothing. That is a prediction.
#
# THE RANKED LIST
# 1. ACTION5 or ACTION6. Never pressed in six states. Any outcome is the
#    largest single addition available -- including "nothing", which would be
#    the first WITNESSED inertness in this world. The ranker prices these at
#    zero because my manual is silent on them; that is a fact about my manual.
# 2. ACTION2, HERE, IN W0. Tests a zero-witness silence covering 18 rules. If
#    it exchanges, the toggle is key-symmetric and 18 rules generalise free.
# 3. ACTION4 A SECOND TIME, once the readout is lit. The only way to split
#    "key 4 advances the meter" from "lighting the readout advances it".
#    Costs a meter cell; read the answer off the RAW DIFF, since the
#    divergence lands on (53,62) which I cannot draw either way.
# 4. ACTION1, HERE. Fully predicted at 72 cells. Cheap confirmation of the
#    exchange reading. Buy only if the ranker refuses everything above.
#
# WHAT NOT TO PRESS
#   ACTION3 or ACTION7 here: the pattern they erase is already erased, my
#   manual predicts identity AND I believe it. Confirmed silence, no witness.
#   Anything chosen because my manual predicts the most pixels for it: that
#   number measures my coverage, not the world's information.

order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition         [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation       [proof: lean]
order     confirm_a_reconstructed_census_before_trusting_a_rule_built_on_it [proof: lean]
order     replace_a_manual_about_another_world_rather_than_patching_it      [proof: lean]
order     derive_a_state_collision_from_counts_before_guessing_a_frame      [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     prefer_a_positive_colour_test_over_a_negated_wall_test            [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it    [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language    [proof: lean]
order     spend_a_monotone_counter_only_on_a_question_it_actually_closes    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead               [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead     [proof: lean]
prune     divergence_lies_only_on_the_unadvanced_meter_frontier => dead     [proof: lean]
prune     divergence_is_exactly_the_twenty_four_background_coloured_cells => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     advances_the_meter_and_closes_no_open_question => dead            [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                   [admissible: lean]

prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 1/5 pressed keys]
prefer    a_command_that_tests_eighteen_rules_at_once                       [ev: 1/1 available]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 1/6 states]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 5/5 diffs]
prefer    a_free_probe_over_one_that_advances_the_meter                     [ev: 1/5 commands advanced it]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 2/6 states are W1 or W0-with-pattern]
