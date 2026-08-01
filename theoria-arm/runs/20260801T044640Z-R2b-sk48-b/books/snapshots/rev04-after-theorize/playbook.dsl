# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHERE THIS ROUND STANDS =========
# The world changed under me: this is a new level with a fresh store, six
# states, 97 dynamic cells, none of the old geometry. The old manual did not
# compile, so it scored nothing at all. The new one is small, has no
# landmarks and no goal section, and predicts three of five transitions
# exactly.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   97 dynamic cells, and every one has an owner:
#     icon1 rows 30-35 cols 11-16 (36)   icon2 rows 36-41 cols 11-16 (36)
#     tape1 rows 32-33 cols 17-22 (12)   tape2 rows 38-39 cols 17-22 (12)
#     meter (53,63) (1)
#   KNOWN CELL BY CELL: key(3) and key(7) hide tape2, twelve cells; key(4)
#   shows it, twelve cells, and advanced the meter once.
#   NOT KNOWN AT ALL: key(1) and key(2) each change all 96 widget cells and
#   the diff reported only a count, a box and two colour sets. key(5) and
#   key(6) have never been pressed.
#   Current state: tape2 hidden, tape1 hidden, meter reads 3.
#
# ========= THE ONE THING WORTH BUYING =========
# THE FRAME I AM SHOWN IS THE CURRENT ONE, IN FULL. The 96-cell hole is not
# a hole in my reasoning, it is a hole in what the summariser printed, and
# it closes the instant the other configuration BECOMES the current frame.
# Press the key whose diff was never itemised. Next round the pixels are on
# the page and two rules can be written from evidence instead of guessed.
#
# The advertised price: my manual predicts zero cells there and the world
# will change 96. That refutation is declared in advance, in the manual, in
# writing, and it must not be read as a defect. Every other command on this
# board buys at most twelve cells and most buy one.
#
# ========= THE THREE CHEAP QUESTIONS BEHIND IT =========
#   1. HIDE OR TOGGLE. tape2 is hidden now, so a hide-key pressed here does
#      nothing under one reading and shows twelve cells under the other. My
#      manual predicts silence and has NO witness for it.
#   2. ONE-SHOT OR COUNTER. The meter rule fires only on colour 2 and the
#      meter now reads 3, so my manual predicts the show-key moves twelve
#      cells and not thirteen. Thirteen refutes the guard.
#   3. TWO KEYS OR ONE. The two hide-keys have identical twelve-cell effects
#      and differ only in frame count, one versus two. Nothing separates
#      them yet and I wrote each rule twice because the grammar has no `or`.
#
# ------------------------------------------------------------------------
# Do not read a divergence on the widget area as a failed rule: there is no
# rule there, only a declared ignorance, and closing it is the whole plan.

order     buy_the_frame_the_summariser_refused_to_itemise                 [proof: lean]
order     close_a_declared_ignorance_before_refining_a_witnessed_rule     [proof: lean]
order     treat_predicted_silence_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance              [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered   [proof: lean]
order     separate_two_keys_with_one_effect_before_trusting_either        [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it      [proof: lean]
order     prefer_constructs_that_cannot_fail_to_compile_over_expressive_ones [proof: lean]

prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     repeats_a_key_whose_effect_here_is_already_known_cell_by_cell => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead              [proof: lean]
prune     divergence_lies_only_where_the_manual_declared_ignorance => dead  [proof: lean]
prune     restates_a_transition_the_previous_command_just_answered => dead  [proof: lean]
prune     asks_a_question_the_current_state_cannot_pose => dead             [proof: lean]

heuristic dynamic_cells_whose_colour_map_is_still_unknown                 [admissible: lean]
heuristic configurations_no_frame_has_ever_shown_in_full                  [admissible: lean]
heuristic keys_never_pressed_in_this_world                                [admissible: lean]
heuristic silences_the_manual_asserts_without_a_witness                   [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                    [admissible: lean]
heuristic divergent_cells_lying_outside_a_declared_ignorance              [admissible: lean]

prefer    the_key_whose_ninety_six_cell_diff_was_never_itemised           [ev: 2/5 commands]
prefer    a_state_that_makes_the_hidden_configuration_the_current_frame   [ev: 1/1 displays]
prefer    a_key_whose_predicted_silence_here_has_never_been_witnessed     [ev: 4/7 keys]
prefer    an_unpressed_key_over_a_key_already_at_full_coverage            [ev: 2/7 keys]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 3/5 diffs]
prefer    the_press_that_splits_a_one_shot_from_a_counter                 [ev: 1/1 witnesses]
