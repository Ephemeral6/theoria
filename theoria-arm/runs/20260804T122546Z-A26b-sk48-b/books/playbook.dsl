# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: unchanged. Eighteen states, seventeen commands, and THIS ROUND BOUGHT
# NOTHING. I am in W0 and it is the opening position: box in the BOTTOM slot
# rows 36-41, bar in the TOP slot rows 30-35, bottom readout LIT at rows 38-39
# cols 17-22, top readout dark. S17 equals S0 in all 96 widget cells. The only
# persistent change in seventeen commands is the meter: five cells, (53,59)
# through (53,63). Cumulative frames including RESET: 33.
#
# WHAT ACTUALLY HAPPENED THIS ROUND
#   Certify ran, the replay_mismatch fired at certify t=7 on cell (53,62)
#   manual 2 world 3, and that is the exact transition, the exact cell and the
#   exact pair of colours the previous edition published in advance. Five
#   certify predictions were made and five landed. No rule changed. No rule
#   should have changed: nothing was observed.
#   THE ONE PREDICTION THAT COST SOMETHING IS matched = 7. It is not tunable --
#   it falls out of the six-frame clock putting the second tick on t8, which is
#   certify t=7. A ledger that gets an integer right in advance is worth more
#   than a repair that gets a cell right in hindsight.
#
# THE ONE NEW THING, AND IT WAS FREE
#   FRAME COST IS A PROPERTY OF THE KEY, NOT OF THE CHANGE. Frames per command
#   t1..t17: 2,2,2,2,1,2,2,2,1,2,2,2,2,2,2,2,2. A command returns ONE frame if
#   it changed nothing (t9) or if it is ACTION7 (t5, which changed twelve
#   cells), and TWO otherwise. The decisive pair is t3 and t5: ACTION3 and
#   ACTION7 perform the IDENTICAL twelve-cell blanking and cost two units and
#   one unit. So:
#     * ACTION7 IS A HALF-PRICE ACTION3 for the same effect.
#     * An inert command is half-price whatever the key.
#     * The next tick is now forecastable, not just explicable: 33 + 6 = 39, so
#       the sixth tick lands on the third acting non-seven command from here,
#       and on the fourth if any one of them is inert or is ACTION7.
#   Each exception clause stands on ONE witness. ACTION5 and ACTION6 obey
#   neither clause knowably, because they have never been pressed.
#
# A FREE TICK DETECTOR: a probe reports frontier_vacuous with zero survivors
#   EXACTLY on the commands that tick -- 7 of 7. It is a fact about my
#   frontier, not about the world: no hypothesis of mine can tick the meter, so
#   a ticking command falls outside the whole frontier. Never pay for it;
#   always read it.
#
# THE QUESTION THAT ONLY THIS CONFIGURATION CAN ASK
#   ACTION1 has been pressed six times, every one in W0. ACTION2 six times,
#   every one in W1. ACTION1 HAS NEVER FOLLOWED ACTION1 AND ACTION2 HAS NEVER
#   FOLLOWED ACTION2. Exchange and scroll are both alive. Standing in W0, the
#   cheap discriminating press is ACTION2 HERE: exchange says it does exactly
#   what ACTION1 does from here, scroll says a configuration never seen, and my
#   manual says silence -- a silence resting on twenty rules and zero
#   witnesses. BONUS: the readout is lit, so any swap moves 96 cells and
#   re-witnesses the four readout-transfer rules that stand on one witness.
#
# A SECOND FREE EXPERIMENT NOBODY HAS TO PAY FOR
#   ACTION4 here is predicted SILENT by two guards I wrote deliberately. If the
#   frame-cost law is right it must therefore return ONE frame -- and every
#   previous ACTION4 acted and returned two. So a press that my manual scores
#   at zero information about the widget is a clean one-bit test of the law
#   that prices every other command. It is the cheapest experiment on the
#   board, but it is still below the two above, because it cannot produce a
#   GameState or a third configuration.
#
# THE TRAP THIS PLAYBOOK EXISTS TO DEFEAT
#   Jaw one: every k1 guard demands a frame-0 colour and every k2 guard the
#   swapped one, so twenty rules are silent in W1 and twenty in W0 BY SYNTAX,
#   and a ranker prices a predicted identity at zero.
#   Jaw two: my replayed meter is wrong by construction, so every command I
#   fully model scores 4.88 bits = log2(59/2) forever.
#   Jaw three: a manual that correctly forecasts its own mismatch produces a
#   surprise report every round even when nothing was pressed -- which is
#   EXACTLY what happened this round, for the second time. A round spent
#   answering that report buys nothing and costs no clock, so it looks free; it
#   is not free, it is a round in which the six open gaps stayed open.
#   Jaw four: the clock guarantees a fresh empirical surprise on one command in
#   three whatever is pressed. A tick is not news.
#
# WHAT IS GENUINELY UNKNOWN -- NOT ONE OF THESE MOVED THIS ROUND
#   * ACTION5 and ACTION6: never pressed. Zero constraint. If one is a
#     coordinate action the guard language cannot express it (E-05), and the
#     4x4 colour-14 block at rows 31-34 cols 42-45 is the only untouched
#     structure on the board.
#   * ACTION2 in W0, ACTION1 in W1, ACTION4 in W1: silences with no witness.
#   * The win condition. Eighteen states, all NOT_FINISHED. The widget has
#     returned to its opening position, so nothing in it is cumulative, and the
#     one monotone quantity is a clock. The goal language cannot name a
#     GameState (E-03) or a cell that is still board (E-02).
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * Replay is 7 of 17 and every wrong cell is on row 53. It loses one more
#     cell every six frames, permanently. Two repairs refused with arithmetic.
#   * ACTION2 here is predicted SILENT and I expect that to be wrong.
#   * ACTION1 here: 96 cells, rows 30-41, cols 11-22, two frames.
#   * ACTION3 and ACTION7 here: the same twelve readout cells go dark, in two
#     frames and one frame respectively.
#   * ACTION4 here: silent, entailed by its guards, and ONE frame.
#
# THE RANKED LIST -- UNCHANGED, BECAUSE NOTHING WAS OBSERVED THAT COULD CHANGE
# IT, AND REPEATED VERBATIM IS THE HONEST OUTPUT OF A ROUND THAT BOUGHT NOTHING
# 1. ACTION5 OR ACTION6. Never pressed in twenty entries; the only place a
#    GameState other than NOT_FINISHED could come from; the only place a cell
#    outside rows 30-41 and row 53 could turn dynamic; and if it is inert it
#    returns one frame and adjudicates the clock for free. Any outcome is the
#    largest single addition to the manual available, including nothing.
# 2. ACTION2, HERE, IN W0. Splits exchange from scroll, tests the twenty
#    forged-silent k2 rules at once, moves 96 cells because the readout is lit,
#    three legible outcomes, and askable only from W0.
# 3. ACTION4 HERE. Predicted silent and entailed so; its value is that the
#    frame-cost law says it must return ONE frame, which no ACTION4 ever has.
# 4. ACTION1 HERE, only if a 96-cell readout-transfer re-witness is wanted: it
#    re-earns four rules that stand on one witness each.
# 5. ACTION4 IN W1, whenever W1 is next occupied with a dark bottom readout.
# 6. The meter is read for free in the raw diff and in the vacuity flag of
#    whatever is pressed. NEVER spend a command on it.
#
# WHAT NOT TO PRESS
#   ACTION1 or ACTION2 in the configuration each has already been pressed six
#   times in, unless the lit readout is the point. ACTION3 or ACTION7 here:
#   witnessed in this exact configuration at t3 and t5. Anything chosen because
#   the report says 4.88 bits: that is my own meter error being sold back to
#   me. And DO NOT SPEND A THIRD ROUND ON CERTIFICATION ALONE -- two in a row
#   have now produced the same forecast divergence and nothing else.

order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     spend_a_probe_only_the_current_state_can_ask_before_one_askable_anywhere [proof: lean]
order     test_a_silence_that_is_an_artefact_of_rule_syntax_before_any_other [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     press_something_rather_than_recertify_a_manual_that_forecast_itself [proof: lean]
order     treat_a_second_identical_certification_round_as_a_cost_not_a_saving [proof: lean]
order     repeat_a_ranked_list_verbatim_when_no_observation_could_have_moved_it [proof: lean]
order     count_the_frames_a_command_returns_as_the_price_it_charges_the_clock [proof: lean]
order     read_frame_cost_off_the_key_and_the_inertness_before_off_the_diff_size [proof: lean]
order     compare_two_commands_with_identical_effects_and_different_frame_costs [proof: lean]
order     prefer_a_short_command_when_two_probes_are_otherwise_equal        [proof: lean]
order     read_a_free_experiment_off_the_command_you_were_going_to_press_anyway [proof: lean]
order     value_an_entailed_silence_for_the_frame_count_it_still_reveals    [proof: lean]
order     fit_a_hidden_counter_to_cumulative_frames_before_to_command_index [proof: lean]
order     test_an_absolute_counter_against_one_that_resets_on_every_tick    [proof: lean]
order     prefer_a_two_parameter_law_that_leaves_no_residual_over_a_drifting_one [proof: lean]
order     date_a_prediction_by_index_so_a_wrong_period_can_be_killed        [proof: lean]
order     publish_the_certify_report_you_expect_before_the_report_arrives   [proof: lean]
order     credit_a_forecast_only_for_the_number_you_could_not_have_tuned    [proof: lean]
order     kill_a_fitted_period_the_moment_one_interval_breaks_it            [proof: lean]
order     test_every_counter_computable_from_the_log_before_spending_a_command [proof: lean]
order     mine_the_frame_count_column_of_the_log_as_data_in_its_own_right   [proof: lean]
order     prove_a_quantity_is_not_a_function_of_the_frame_before_guessing_its_guard [proof: lean]
order     find_two_identical_frames_with_different_successors_before_adding_a_rule [proof: lean]
order     name_a_hidden_variable_as_a_language_limit_rather_than_as_ignorance [proof: lean]
order     check_a_reconstruction_against_a_store_number_you_did_not_fit     [proof: lean]
order     list_the_duplicate_states_your_parity_forces_and_count_them       [proof: lean]
order     recount_a_state_census_against_the_store_before_drawing_from_it   [proof: lean]
order     re_read_a_census_off_the_frame_rather_than_copying_last_edition   [proof: lean]
order     let_a_new_dynamic_cell_join_the_type_its_frame_zero_colour_names  [proof: lean]
order     check_each_types_coverages_sum_to_its_instance_count              [proof: lean]
order     count_a_coverage_figure_before_writing_it_down                    [proof: lean]
order     relabel_a_state_dependent_count_that_was_written_as_an_invariant  [proof: lean]
order     sum_the_wrong_cells_a_repair_would_cost_before_adopting_it        [proof: lean]
order     answer_a_priced_surprise_with_a_stated_refusal_and_arithmetic     [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     refuse_a_patch_fitted_to_a_two_of_two_coincidence_of_keys         [proof: lean]
order     refuse_a_patch_that_would_be_wrong_on_the_next_press_of_its_own_key [proof: lean]
order     audit_the_patch_you_kept_against_the_prune_you_wrote_for_others   [proof: lean]
order     declare_the_condition_under_which_a_surviving_patch_becomes_wrong [proof: lean]
order     guard_a_rule_into_silence_before_letting_it_draw_an_unwitnessed_state [proof: lean]
order     rename_a_rule_that_survives_only_as_a_replay_patch                [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     read_a_never_changing_row_as_evidence_about_structure             [proof: lean]
order     override_a_ranker_that_prices_every_predicted_identity_at_zero    [proof: lean]
order     discount_gain_earned_only_on_a_cell_the_manual_declared_undrawable [proof: lean]
order     recompute_reported_bits_from_survivor_counts_before_trusting_them [proof: lean]
order     suspect_the_scoring_channel_when_one_number_repeats_six_probes_running [proof: lean]
order     use_a_vacuous_frontier_as_a_detector_rather_than_as_a_defeat      [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     add_no_rule_in_a_round_that_bought_no_new_observation             [proof: lean]
order     label_an_outside_prior_as_a_prior_rather_than_as_evidence         [proof: lean]
order     verify_what_a_recount_can_settle_before_asking_the_world          [proof: lean]
order     honour_the_refutation_clause_you_wrote_into_your_own_theorem      [proof: lean]
order     strike_a_refuted_theorem_rather_than_reinterpret_it               [proof: lean]
order     move_a_tested_prediction_out_of_the_pending_block_that_made_it    [proof: lean]
order     cite_only_engine_reports_that_were_actually_supplied_this_round   [proof: lean]
order     refuse_a_goal_no_observation_distinguishes_and_say_so_out_loud    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_over_a_quantity_shown_not_to_be_a_function_of_the_frame => dead [proof: lean]
prune     rule_keyed_to_an_action_that_explains_two_of_five_occurrences => dead [proof: lean]
prune     rule_that_would_fire_on_the_next_press_of_the_key_it_was_fitted_to => dead [proof: lean]
prune     repair_that_does_not_reduce_total_wrong_cell_transitions => dead  [proof: lean]
prune     repair_whose_error_walks_into_cells_that_are_still_board => dead  [proof: lean]
prune     repair_that_races_ahead_of_a_clock_it_cannot_read => dead         [proof: lean]
prune     rule_added_in_a_round_whose_store_counts_did_not_move => dead     [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     period_fitted_to_two_ticks_and_broken_by_a_third => dead          [proof: lean]
prune     counter_that_fails_on_any_tick_already_in_the_log => dead         [proof: lean]
prune     counter_that_must_be_reset_on_tick_to_fit => dead                 [proof: lean]
prune     frame_cost_law_contradicted_by_any_command_already_in_the_log => dead [proof: lean]
prune     divergence_lies_only_on_the_meter_frontier => dead                [proof: lean]
prune     divergence_a_later_transition_only_inherited_from_an_earlier_one => dead [proof: lean]
prune     divergence_the_previous_edition_named_by_cell_and_by_command => dead [proof: lean]
prune     surprise_reported_in_a_round_that_added_no_state_to_the_store => dead [proof: lean]
prune     probe_whose_reported_bits_are_all_earned_on_undrawable_cells => dead [proof: lean]
prune     probe_vacuous_because_the_clock_ticked_under_it => dead           [proof: lean]
prune     probe_that_repeats_a_key_in_a_configuration_already_probed_twice => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     repeats_a_key_already_watched_doing_nothing_in_this_exact_state => dead [proof: lean]
prune     repeats_a_transition_already_witnessed_from_an_identical_frame => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     leaves_the_only_configuration_that_can_ask_the_open_question => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     goal_clause_over_a_cell_that_is_still_board => dead               [proof: lean]
prune     goal_over_a_quantity_shown_to_be_a_clock => dead                  [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     goal_no_observed_gamestate_could_have_distinguished => dead       [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic silences_that_follow_from_rule_syntax_rather_than_from_evidence   [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic entailed_silences_whose_frame_count_still_tests_a_law             [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic rules_still_standing_on_a_single_witness                          [admissible: lean]
heuristic law_clauses_still_standing_on_a_single_witness                    [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic questions_that_only_the_present_configuration_can_ask             [admissible: lean]
heuristic frames_a_command_returns_and_the_clock_units_it_therefore_spends  [admissible: lean]
heuristic pairs_of_commands_with_equal_effect_and_unequal_frame_cost        [admissible: lean]
heuristic commands_that_would_slip_a_clock_prediction_against_a_rival_one   [admissible: lean]
heuristic counters_still_fitting_every_tick_in_the_log                      [admissible: lean]
heuristic store_numbers_a_reconstruction_predicts_without_having_fitted_them [admissible: lean]
heuristic integers_published_in_advance_that_a_later_report_confirmed       [admissible: lean]
heuristic pairs_of_identical_frames_with_different_successors               [admissible: lean]
heuristic coverage_deficits_between_a_types_rules_and_its_instance_count    [admissible: lean]
heuristic repairs_whose_wrong_cell_total_i_have_actually_summed             [admissible: lean]
heuristic surviving_patches_whose_own_guard_the_world_has_shut              [admissible: lean]
heuristic reported_bits_that_survive_deleting_the_undrawable_cells          [admissible: lean]
heuristic consecutive_commands_spent_on_a_single_already_modelled_key       [admissible: lean]
heuristic consecutive_rounds_that_added_no_state_to_the_store               [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic rows_that_have_never_changed_and_constrain_a_structural_reading   [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic board_structures_no_command_has_ever_touched                      [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic gamestates_other_than_not_finished_ever_returned                  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]

prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 3/5 pressed keys]
prefer    a_command_that_splits_two_named_readings_in_one_press             [ev: 1/1 available]
prefer    a_probe_askable_only_from_the_configuration_now_showing           [ev: 1/2 configurations]
prefer    a_command_that_tests_twenty_rules_at_once                         [ev: 2/2 available]
prefer    a_command_that_re_witnesses_a_rule_standing_on_one_witness        [ev: 8/47 rules]
prefer    a_command_whose_frame_count_alone_tests_a_law                     [ev: 3/7 keys here]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 5/20 entries]
prefer    a_command_that_could_return_a_gamestate_never_yet_seen            [ev: 0/20 entries so far]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 0/20 entries so far]
prefer    a_command_whose_outcome_the_manual_cannot_already_hash            [ev: 6/6 last probes failed this]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 18/18 diffs]
prefer    a_command_returning_one_frame_when_two_probes_tie                 [ev: 2/17 commands]
prefer    any_command_at_all_over_a_further_round_of_pure_certification     [ev: 2/2 rounds]
