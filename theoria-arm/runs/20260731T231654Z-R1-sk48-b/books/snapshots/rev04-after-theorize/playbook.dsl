# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
# Slot at rows 38-39 x cols 17-22 is BLANK. Rail marker at rows 32-33.
# One bar cell burned, (53,63). Five transitions observed in total.
#
#   key(3), key(7): predicted inert here, NO WITNESS for that silence.
#   key(4): predicted twelve cells, the slot redrawn. Witnessed once.
#   key(1), key(2): predicted inert and KNOWN FALSE -- 96 cells each.
#   key(5), key(6): never pressed in this world. Nothing is known.
#
# ========= THE ONE THING WORTH BUYING =========
# THE FRAME THAT SHOWS s1. ACTION1 rewrote all 96 dynamic cells and the
# brief prints cell-level diffs only for small changes, so the pixels of
# that state have never been shown and never will be shown by a diff. They
# WILL be shown by the current-frame print if the round ends in that state.
# One press of the rewrite key, not immediately undone, converts the
# manual's largest hole into transcribable pixels. Nothing else on the board
# is worth ninety-six pixels.
#
# THE TRAP TO AVOID: with the goal empty, the only thing ranking commands is
# predicted change, and the only key this manual predicts change for is the
# slot-redraw key. Ranking by predicted pixels therefore loops on the one
# thing already at full coverage. Rank by witnesses a command would CREATE.
#
# The advertised price of the probe: 96 pixels of divergence, priced in
# advance in the manual, and it must not be read as a defect.

order     buy_the_frame_that_shows_a_state_never_yet_drawn                 [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     settle_which_key_the_bar_answers_to_before_spending_more_of_it    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     press_the_never_pressed_keys_before_re_pressing_a_solved_one      [proof: lean]
order     separate_two_rules_that_differ_only_in_their_key_literal          [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]
order     prefer_a_probe_whose_answer_is_legible_in_the_raw_diff            [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead              [proof: lean]
prune     divergence_lies_only_on_a_cell_the_board_still_owns => dead       [proof: lean]
prune     immediately_undoes_the_command_that_just_bought_a_new_state => dead [proof: lean]
prune     repeats_a_key_whose_inertness_in_this_state_is_witnessed => dead  [proof: lean]
prune     asserts_a_goal_that_is_true_of_the_current_state => dead          [proof: lean]
prune     needs_a_click_coordinate_the_guard_language_cannot_hold => dead   [proof: lean]

heuristic states_never_yet_printed_as_a_current_frame                      [admissible: lean]
heuristic keys_whose_inertness_here_rests_on_no_witness                    [admissible: lean]
heuristic keys_never_pressed_in_this_world                                 [admissible: lean]
heuristic live_readings_of_the_bar_a_command_can_eliminate                 [admissible: lean]
heuristic unowned_cells_a_command_would_make_dynamic                       [admissible: lean]
heuristic open_questions_a_command_can_close                               [admissible: lean]
heuristic remaining_bar_cells_as_a_budget_of_unknown_denomination          [admissible: lean]

prefer    a_command_that_leaves_the_world_in_an_undrawn_state              [ev: 1/6 states hidden]
prefer    a_key_never_pressed_over_one_pressed_and_understood              [ev: 2/7 keys]
prefer    a_key_whose_predicted_silence_has_never_been_witnessed           [ev: 4/7 keys]
prefer    a_press_that_splits_the_key_reading_from_the_effect_reading      [ev: 1/1 burns]
prefer    a_press_that_repeats_a_key_from_a_state_it_has_not_acted_on      [ev: 3/3 slot keys]
prefer    an_outcome_small_enough_that_the_brief_prints_it_cell_by_cell    [ev: 3/5 diffs]
prefer    learning_the_alphabet_before_theorising_about_the_goal           [ev: 0/6 frames scored]
