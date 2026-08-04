# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE: ten states, nine commands (RESET, A1, A2, A3, A4, A7, A1, A2, A1, A3).
# I am in W1: hollow box in the TOP slot, bar four rows in the BOTTOM slot
# (rows 36-39, rows 40-41 background), BOTH readouts blank, (53,63) and
# (53,62) both 3. 98 cells have ever changed; 96 are the widget and 2 are the
# clock.
#
# WHAT CHANGED THIS ROUND.
#  * The four-cell replay defect was the MIRROR of last round's: the bar
#    truncates going down and REGROWS coming up, and my ACTION2 rules had no
#    way to say so. Two rules added; two coverage figures I had inflated to
#    4/4 corrected to 2/2. That inflation is what hid the defect for a round.
#  * The three vacuous probes are downstream of that one defect, not evidence
#    of a missing mechanism. Every hypothesis in the frontier is my manual or
#    an ablation, so all 57 inherited the same four wrong cells.
#  * THE WORLD HAS HIDDEN STATE. S5 and S7 are the same frame; ACTION1 in S5
#    moved 72 cells, ACTION1 in S7 moved 73. The extra cell is the clock,
#    which ticks at command 4 and command 8 -- every fourth command, whatever
#    the key. My rule that ACTION4 advances it is refuted as an attribution
#    and survives only because it can never fire again.
#  * ACTION4 is now guarded into silence outside W0, because the readout
#    travels with the box and firing it in W1 would draw 24 cells wrong.
#
# THE QUESTION THAT ONLY THIS STATE CAN ASK
#   ACTION1 has been pressed three times and ACTION2 twice, and every press
#   was in the opposite configuration from its predecessor -- ACTION1 HAS
#   NEVER FOLLOWED ACTION1. Exchange and scroll are therefore still both
#   alive. I am standing in W1, where one ACTION1 splits them: exchange
#   returns W0 exactly, scroll shows a configuration never seen. If I spend
#   this command on anything that leaves W1, the question costs two commands
#   instead of one.
#
# WHAT IS GENUINELY UNKNOWN
#   * ACTION5 and ACTION6: never pressed in ten states. Zero constraint.
#   * ACTION1 in W1, ACTION2 in W0, ACTION4 in W1, ACTION3/7 in W1-lit: all
#     silences with no witness behind them.
#   * The clock's period is fitted to two ticks. 4 and 8 fit every-fourth;
#     they also fit other arithmetics I cannot write either.
#   * The win condition. Nothing countable separates a win from here, no
#     GameState but NOT_FINISHED has ever been returned, and I refuse to
#     invent one -- see no_goal_section_and_this_is_a_refusal_not_an_oversight.
#     The plan tier's silence is a true report of my ignorance.
#
# PRICES ADVERTISED IN ADVANCE, SO A REFUTATION ON THEM IMPLICATES NOTHING
#   * The clock is undrawable one cell ahead of itself. (53,61) is board and
#     holds no instance, so command 12 costs exactly one pixel of accuracy
#     and every fourth command after it costs one more, permanently.
#   * ACTION1 here is predicted SILENT and I expect that to be wrong.
#   * ACTION4 here is predicted SILENT by a guard I added on purpose; if the
#     top readout lights, the guard was right about the box and wrong about
#     the silence, and that is a purchase.
#   * ACTION2 here is predicted at exactly 72 cells with the four regrowth
#     cells turning 3. That is the whole fix on trial in one command.
#
# THE RANKED LIST
# 1. ACTION1, HERE, IN W1. The only command that splits exchange from scroll,
#    the largest forged silence in the manual (20 rules), and it is askable
#    only from the configuration I am standing in. Three legible outcomes:
#    W0 exactly, a new configuration, or nothing.
# 2. ACTION5 or ACTION6. Never pressed in ten states. Any outcome is the
#    largest single addition available -- including nothing, which would be
#    the first WITNESSED inertness here -- and it is the cheapest place a win
#    condition could come from. Askable from any state, which is why it sits
#    below a probe that is not.
# 3. ACTION4, HERE. Tests the guard I just added and the readout-follows-box
#    reading in one press, and lights the readout so the A1/A2 readout rules
#    can be re-witnessed in the other configuration.
# 4. Any three commands in a row, to watch command 12. Confirms or kills the
#    clock, and the answer is legible in the raw diff as one cell of row 53.
#
# WHAT NOT TO PRESS
#   ACTION3 or ACTION7 here: the pattern they erase is already erased, my
#   manual predicts identity AND I believe it. Confirmed silence, no witness.
#   ACTION2 here: it repeats t7 from a state identical to t7's, so it buys
#   only what replay already tells me for free.
#   Anything chosen because my manual predicts the most pixels for it: that
#   number measures my coverage, not the world's information.

order     spend_a_probe_only_the_current_state_can_ask_before_one_askable_anywhere [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     press_a_modelled_action_in_a_configuration_it_was_never_pressed_in [proof: lean]
order     test_a_silence_that_rests_on_no_witness_before_one_that_is_entailed [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition         [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     prefer_a_probe_with_three_distinct_legible_outcomes_over_one_with_two [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     suspect_the_replay_before_the_mechanism_when_every_hypothesis_dies [proof: lean]
order     count_a_coverage_figure_before_writing_it_down                    [proof: lean]
order     look_for_the_mirror_of_a_fixed_defect_in_the_reverse_direction    [proof: lean]
order     guard_a_rule_into_silence_before_letting_it_draw_an_unwitnessed_state [proof: lean]
order     name_the_hidden_state_rather_than_key_a_rule_to_the_wrong_cause   [proof: lean]
order     keep_a_refuted_attribution_only_while_it_can_never_fire_again     [proof: lean]
order     separate_same_coloured_roles_by_a_cell_you_have_actually_read     [proof: lean]
order     prefer_a_landmark_guard_over_a_chain_of_cell_operators            [proof: lean]
order     search_the_engine_report_for_a_count_that_matches_the_divergence  [proof: lean]
order     prefer_a_positive_colour_test_over_a_negated_wall_test            [proof: lean]
order     patch_a_manual_whose_divergence_is_four_cells_rather_than_replacing_it [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language    [proof: lean]
order     refuse_a_goal_no_observation_distinguishes_and_say_so_out_loud    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     rule_proposed_with_zero_witnesses_of_any_kind => dead             [proof: lean]
prune     rule_whose_two_witnesses_demand_opposite_outcomes_from_one_frame => dead [proof: lean]
prune     rule_that_would_forge_the_reverse_direction_of_an_unobserved_press => dead [proof: lean]
prune     guard_conjunct_with_no_negative_witness_and_no_explained_pixel => dead [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead               [proof: lean]
prune     goal_that_is_already_true_at_the_current_state => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_widget_configurations => dead [proof: lean]
prune     goal_no_observed_gamestate_could_have_distinguished => dead       [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead     [proof: lean]
prune     divergence_lies_only_on_the_unadvanced_clock_frontier => dead     [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_entailed_by_witnessed_rules => dead [proof: lean]
prune     repeats_a_transition_already_witnessed_from_an_identical_frame => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     leaves_the_only_configuration_that_can_ask_the_open_question => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]

heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic configurations_in_which_a_known_key_has_never_been_pressed        [admissible: lean]
heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic structural_readings_a_single_command_could_eliminate              [admissible: lean]
heuristic rules_that_one_command_could_generalise_or_refute_together        [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic questions_that_only_the_present_configuration_can_ask             [admissible: lean]
heuristic pairs_of_identical_frames_with_different_successors               [admissible: lean]
heuristic commands_remaining_before_the_clock_ticks_again                   [admissible: lean]
heuristic widget_configurations_never_yet_observed                          [admissible: lean]
heuristic cells_outside_the_widget_a_command_could_turn_dynamic             [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic gamestates_other_than_not_finished_ever_returned                  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic fitted_guards_a_command_could_convert_into_witnessed_ones         [admissible: lean]

prefer    a_command_that_splits_two_named_readings_in_one_press             [ev: 1/1 available]
prefer    a_probe_askable_only_from_the_configuration_now_showing           [ev: 1/2 configurations]
prefer    a_key_never_pressed_in_any_state                                  [ev: 2/7 keys]
prefer    a_key_never_pressed_in_the_configuration_now_showing              [ev: 3/5 pressed keys]
prefer    a_command_that_tests_twenty_rules_at_once                         [ev: 2/2 available]
prefer    a_command_that_would_turn_a_cell_outside_the_widget_dynamic       [ev: 2/10 states]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 9/9 diffs]
prefer    a_command_that_would_produce_a_third_widget_configuration         [ev: 0/10 states so far]
prefer    a_command_that_could_return_a_gamestate_never_yet_seen            [ev: 0/10 states so far]
