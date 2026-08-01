# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE SITUATION IN THREE LINES =========
# This is a NEW world, six states old. The previous manual described
# somewhere else entirely and also failed to compile, so nothing replayed
# and nothing was checked. Everything below is five transitions deep.
#
# ========= WHAT IS KNOWN =========
#   ACTION1 -> 96 cells in rows 30-41 cols 11-22. PIXELS NOT SHOWN.
#   ACTION2 -> exactly undoes ACTION1 (s0 = s2, forced by distinct_states=5).
#              PIXELS NOT SHOWN.
#   ACTION3 -> blanks the 12-cell strip at rows 38-39 cols 17-22 to colour 4.
#   ACTION7 -> the same 12 cells, same result, but in ONE frame not two.
#   ACTION4 -> restores the strip AND burned (53,63) from 2 to 3, once.
#   ACTION5, ACTION6 -> never pressed. Nothing is known about either.
#
# ========= WHAT THE MANUAL PREDICTS FROM HERE =========
#   Strip currently BLANK, (53,63) already burned to 3.
#     ACTION4 -> 12 cells (strip restored), no burn.
#     ACTION3, ACTION7 -> nothing, unwitnessed but believed.
#     ACTION1, ACTION2 -> nothing, AND THAT IS KNOWN TO BE FALSE.
#     ACTION5, ACTION6 -> nothing, with no witness of any kind.
#
# ========= THE ONE THING WORTH BUYING =========
# PRESS ACTION1.
#   The manual's largest defect is a forged silence over 96 cells, and it is
#   forged in the strongest sense: I know the world moves them and I have
#   never been shown which. The diff channel will not tell me -- it itemised
#   12 and 13 cells and summarised 96 to a bounding box -- but the FRAME
#   will, because every round hands me the current frame in full and I hold
#   this one. One press converts a 96-cell hole into a cell-by-cell diff.
#   It is also free of risk: ACTION2 provably restores the state exactly.
#   No other command on the board closes anything comparable.
#
# Ranked below it: ACTION5 or ACTION6, because two of seven keys have never
# been pressed and either answer -- motion or a witnessed silence -- is new.
# Ranked last: ACTION3 and ACTION7 from here, which my manual and the world
# probably agree do nothing, and re-pressing ACTION4 to chase the burn,
# which needs two commands to separate its readings and cannot be settled by
# one.
#
# The advertised price of ACTION1: my manual draws NONE of the 96 cells, so
# the refutation is guaranteed and it is 96 cells wide. That is priced here,
# in advance, and it must not be read as a defect discovered by certify.
#
# ------------------------------------------------------------------------
# STATE 5: strip blank; (53,63) burned; 97 dynamic cells all owned; 3999
# board. Seven rules, all of them witnessed, covering 25 of the 217 cell
# changes in history. The other 192 are t1 and t2 and I have not seen one
# of them.

order     buy_the_pixels_of_the_transition_i_have_never_been_shown        [proof: lean]
order     close_a_known_false_silence_before_testing_an_unwitnessed_one   [proof: lean]
order     press_a_key_that_has_never_been_pressed_before_repressing_one   [proof: lean]
order     prefer_a_reversible_probe_when_its_inverse_key_is_known         [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance              [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered   [proof: lean]
order     separate_two_live_readings_before_encoding_either_as_a_rule     [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it      [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead  [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead   [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead              [proof: lean]
prune     divergence_lies_only_on_the_burned_end_of_row_fiftythree => dead  [proof: lean]
prune     repeats_a_key_whose_effect_in_this_state_is_already_itemised => dead [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead   [proof: lean]
prune     needs_two_commands_when_a_one_command_probe_is_unspent => dead    [proof: lean]
prune     asserts_a_goal_no_frame_has_ever_shown => dead                    [proof: lean]
prune     carries_a_landmark_with_no_arc_cell_coordinate => dead            [proof: lean]

heuristic cells_the_manual_currently_draws_wrong_in_a_known_transition    [admissible: lean]
heuristic keys_whose_silence_here_rests_on_no_witness                     [admissible: lean]
heuristic keys_never_pressed_in_the_whole_history                         [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                    [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_row_fiftythree_edge        [admissible: lean]
heuristic frames_returned_per_command_as_a_free_side_channel              [admissible: lean]

prefer    the_key_whose_pixels_the_diff_channel_refused_to_itemise        [ev: 2/5 transitions]
prefer    a_probe_whose_result_arrives_as_a_full_frame_not_a_summary      [ev: 1/1 rounds]
prefer    an_unpressed_key_over_repeating_a_witnessed_effect              [ev: 2/7 keys]
prefer    a_probe_that_is_undone_by_a_key_already_known_to_undo_it        [ev: 1/1 pairs]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 3/5 diffs]
