# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: fifteen entries, fourteen commands (RESET, A1, A2, A3, A4, A7, A1,
# A2, A1, A3, A2, A1, A2, A1). I am in W1: hollow box in the TOP slot, bar
# four rows in the BOTTOM slot (36-39, rows 40-41 background), BOTH readouts
# blank, (53,61) (53,62) (53,63) all colour 3. 99 cells have ever changed; 96
# are the widget and 3 are the meter.
#
# WHAT CHANGED THIS ROUND: NO COMMAND WAS PRESSED.
#   Every store number is identical to last round -- states 14, steps 14,
#   dynamic_cells 99, constant_cells 3997, distinct_states 10. The round was
#   spent re-certifying a manual that already forecast its own certify report.
#   That is the second failure mode this playbook now has to defend against.
#   Jaw one made the ranker re-press the keys I model; jaw two made it press
#   nothing at all. Both cost the same thing: the ONE question that only this
#   configuration can ask is still unasked, three rounds running.
#
# WHAT THE ROUND DID PRODUCE, WITHOUT SPENDING A COMMAND
#   * The certify report was predicted five for five, including the prediction
#     of my own permanent failure. The divergence set is closed: no unpriced
#     cell diverged anywhere in 13 transitions.
#   * All forty coverage figures re-derived by hand. Every type's k1 rules and
#     k2 rules each partition its instances exactly; the ONLY deficit is
#     BarCore 9 of 12, and those 3 are the meter. 96 of 99 covered both ways,
#     and 96 is the largest diff the world has ever produced.
#   * The one repair the mismatch invites -- meter propagates left when its
#     right neighbour is 3 -- was computed and REFUSED: it fires three
#     commands early, it does not reduce the wrong-cell total, and it walks
#     left into cells that are still board, unbounded. Arithmetic in the
#     manual.
#
# THE QUESTION THAT ONLY THIS CONFIGURATION CAN ASK -- UNCHANGED
#   ACTION1 has been pressed FIVE times and every one was in W0. ACTION2 four
#   times, every one in W1. ACTION1 HAS NEVER FOLLOWED ACTION1. Exchange and
#   scroll are both alive; row 29 never changing is evidence against scroll
#   and does not close it. In W1 one ACTION1 splits them: exchange returns W0
#   exactly, scroll shows a configuration never seen, silence would be the
#   most surprising outcome available. Any command that leaves W1 makes the
#   question cost two. I am in W1 now, and I have been in W1 for two rounds.
#
# THE TRAP THIS PLAYBOOK EXISTS TO DEFEAT, NOW WITH A THIRD JAW
#   Jaw one: every k1 rule demands its instance still wear its frame-0 colour,
#   true only in W0, so my silence on ACTION1-in-W1 is an artefact of rule
#   syntax, and a ranker prices a predicted identity at ZERO.
#   Jaw two: the clock makes every command I DO model score 4.88 bits.
#   Jaw three: a manual that correctly forecasts its own mismatch produces a
#   surprise report every round WITHOUT a command being pressed, and that
#   surprise can consume the round. A priced divergence is not news.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in fifteen entries. Zero constraint.
#   * ACTION1 in W1, ACTION2 in W0, ACTION4 in W1: silences with no witness.
#   * The meter's driver. Not a function of the frame -- two identical frames
#     disagree under the same key -- and not periodic in any count I can do.
#     It rides free on every command; it costs nothing to watch and must never
#     be paid for.
#   * The win condition. No GameState but NOT_FINISHED in fourteen states.
#     The goal language cannot name the un-ticked meter cells because they are
#     still board. The plan tier's silence is a true report of my ignorance.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * (53,62) is wrong in replay from transition 7 and (53,61) from
#     transition 10, permanently. Row-53 divergences buy nothing.
#   * ACTION1 here is predicted SILENT and I expect that to be wrong.
#   * ACTION4 here is predicted SILENT by a guard I added on purpose.
#   * ACTION2 here is predicted to the cell and repeats t7, t10 and t12.
#   * ACTION3 and ACTION7 here are predicted silent, ACTION3 witnessed silent.
#
# THE RANKED LIST -- UNCHANGED, BECAUSE NOTHING WAS OBSERVED THAT COULD
# CHANGE IT, AND CHANGING IT ANYWAY WOULD BE INVENTION
# 1. ACTION1, HERE, IN W1. Splits exchange from scroll, tests the largest
#    forged silence in the manual (20 rules, now known to cover 96 of 99
#    cells), askable only from where I am standing, three legible outcomes.
#    Unbought for three rounds.
# 2. ACTION5 or ACTION6. Never pressed in fifteen entries. Any outcome is the
#    largest single addition available -- including nothing, which after t9 I
#    know how to read -- and the cheapest place a win condition could come
#    from.
# 3. ACTION4, HERE. Tests the guard and the readout-follows-box reading in one
#    press, and relights the readout so the readout rules can be re-witnessed
#    in the other configuration.
# 4. The meter is checked for free in the raw diff of whatever is pressed.
#    Never spend a command on it.
#
# WHAT NOT TO PRESS, AND WHAT NOT TO DO INSTEAD OF PRESSING
#   ACTION2 here: drawn to the cell, witnessed four times, bits manufactured
#   by row 53. ACTION1 in W0: same, five witnesses. ACTION3 here: witnessed
#   inert in this exact state. ACTION7 here: entailed inert by a watched twin.
#   Anything chosen because the report says 4.88 bits: that is the clock.
#   AND: do not spend a round on certification alone. A surprise whose cells
#   the previous edition named by index is not a reason to re-open the manual.

order     press_something_rather_than_recertify_a_manual_that_forecast_itself [proof: lean]
order     spend_a_probe_only_the_current_state_can_ask_before_one_askable_anywhere [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     test_a_silence_that_is_an_artefact_of_rule_syntax_before_any_other [proof: lean]
order     override_a_ranker_that_prices_every_predicted_identity_at_zero    [proof: lean]
order     discount_gain_earned_only_on_a_cell_the_manual_declared_undrawable [proof: lean]
order     recompute_reported_bits_from_survivor_counts_before_trusting_them [proof: lean]
order     suspect_the_scoring_channel_when_one_key_wins_four_rounds_running [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     answer_a_priced_surprise_with_a_stated_refusal_and_arithmetic     [proof: lean]
order     sum_the_wrong_cells_a_repair_would_cost_before_adopting_it        [proof: lean]
order     add_no_rule_in_a_round_that_bought_no_new_observation             [proof: lean]
order     verify_what_a_recount_can_settle_before_asking_the_world          [proof: lean]
order     date_a_prediction_by_index_so_a_wrong_period_can_be_killed        [proof: lean]
order     kill_a_fitted_period_the_moment_one_interval_breaks_it            [proof: lean]
order     test_every_counter_computable_from_the_log_before_spending_a_command [proof: lean]
order     prove_a_quantity_is_not_a_function_of_the_frame_before_guessing_its_guard [proof: lean]
order     find_two_identical_frames_with_different_successors_before_adding_a_rule [proof: lean]
order     honour_the_refutation_clause_you_wrote_into_your_own_theorem      [proof: lean]
order     strike_a_refuted_theorem_rather_than_reinterpret_it               [proof: lean]
order     count_a_coverage_figure_before_writing_it_down                    [proof: lean]
order     check_each_types_coverages_sum_to_its_instance_count              [proof: lean]
order     recount_a_state_census_against_the_store_before_drawing_from_it   [proof: lean]
order     let_a_new_dynamic_cell_join_the_type_its_frame_zero_colour_names  [proof: lean]
order     read_a_never_changing_row_as_evidence_about_structure             [proof: lean]
order     guard_a_rule_into_silence_before_letting_it_draw_an_unwitnessed_state [proof: lean]
order     rename_a_rule_that_survives_only_as_a_replay_patch                [proof: lean]
order     refuse_a_patch_that_buys_one_right_cell_with_three_wrong_ones     [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     cite_only_engine_reports_that_were_actually_supplied_this_round   [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     refuse_a_goal_no_observation_distinguishes_and_say_so_out_loud    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_added_in_a_round_whose_store_counts_did_not_move => dead     [proof: lean]
prune     rule_over_a_quantity_shown_not_to_be_a_function_of_the_frame => dead [proof: lean]
prune     repair_that_does_not_reduce_total_wrong_cell_transitions => dead  [proof: lean]
prune     repair_whose_error_walks_into_cells_that_are_still_board => dead  [proof: lean]
prune     rule_that_would_fire_on_every_command_to_draw_a_cell_that_moves_on_one [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     period_fitted_to_two_ticks_and_broken_by_a_third => dead          [proof: lean]
prune     counter_that_fails_on_any_tick_already_in_the_log => dead         [proof: lean]
prune     divergence_lies_only_on_the_meter_frontier => dead                [proof: lean]
prune     divergence_a_later_transition_only_inherited_from_an_earlier_one => dead [proof: lean]
prune     divergence_the_previous_edition_named_by_cell_and_by_command => dead [proof: lean]
prune     probe_whose_reported_bits_are_all_earned_on_undrawable_cells => dead [proof: lean]
prune     probe_that_repeats_a_key_in_a_configuration_already_probed_twice => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     repeats_a_key_already_watched_doing_nothing_in_this_exact_state => dead [proof: lean]
prune     repeats_a_transition_already_witnessed_from_an_identical_frame => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     leaves_the_only_configuration_that_can_ask_the_open_question => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     goal_clause_over_a_cell_that_is_still_board => dead               [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     goal_no_observed_gamestate_could_have_distinguished => dead       [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic silences_that_follow_from_rule_syntax_rather_than_from_evidence   [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic questions_that_only_the_present_configuration_can_ask             [admissible: lean]
heuristic pairs_of_identical_frames_with_different_successors               [admissible: lean]
heuristic duplicate_state_pairs_the_store_count_requires_and_i_have_named   [admissible: lean]
heuristic coverage_deficits_between_a_types_rules_and_its_instance_count    [admissible: lean]
heuristic repairs_whose_wrong_cell_total_i_have_actually_summed             [admissible: lean]
heuristic counters_still_fitting_every_tick_in_the_log                      [admissible: lean]
heuristic reported_bits_that_survive_deleting_the_undrawable_cells          [admissible: lean]
heuristic consecutive_rounds_in_which_no_command_was_pressed                [admissible: lean]
heuristic consecutive_commands_spent_on_a_single_already_modelled_key       [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic rows_that_have_never_changed_and_constrain_a_structural_reading   [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic gamestates_other_than_not_finished_ever_returned                  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]

prefer    any_command_at_all_over_a_second_round_of_pure_certification      [ev: 1/1 rounds]
prefer    a_command_that_splits_two_named_readings_in_one_press             [ev: 1/1 available]
prefer    a_probe_askable_only_from_the_configuration_now_showing           [ev: 1/2 configurations]
prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 3/5 pressed keys]
prefer    a_command_that_tests_twenty_rules_at_once                         [ev: 2/2 available]
prefer    a_command_whose_outcome_the_manual_cannot_already_hash            [ev: 4/4 last probes failed this]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 3/15 entries]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 14/14 diffs]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 0/15 entries so far]
prefer    a_command_that_could_return_a_gamestate_never_yet_seen            [ev: 0/15 entries so far]
