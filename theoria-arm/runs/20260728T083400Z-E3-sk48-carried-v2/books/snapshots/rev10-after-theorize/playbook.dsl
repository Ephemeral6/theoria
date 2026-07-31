# playbook.dsl -- no new transitions arrived, so nothing here is re-derived
# from scratch. Two things change:
#
#   THE PROBE IS NOW A COMPOSITE AND ITS ORDER IS FORCED. Three consecutive
#     actions, none of them the restore key, separate the clock reading from
#     the parity-toll reading. The current state is blanked, and the hiding key
#     is not the restore key, so the first of those three can be the hiding key
#     and simultaneously settle hide-versus-toggle. The other two can be the
#     two keys never pressed. Three actions, four open questions, and my manual
#     predicts a specific frame for all three. Nothing else in this game buys
#     that much.
#   THE PREDICTION LEDGER IS THE RANKING SIGNAL. Last round's manual named its
#     own failure set in advance and the checker reproduced it exactly. So an
#     action whose outcome the manual has committed to in writing outranks one
#     it is merely silent about, because the silent one cannot be scored.
#
# The frugality entries stay dead: t6 was a restore press that moved no bar,
# so no single key has been shown to cost anything, and under the clock reading
# the expensive move is the one that learns nothing.
#
# Nothing below is a stored line of play. Every entry is a ranking rule that
# still has to be evaluated against whatever state the searcher is in.

order   separate_hiding_from_toggling_by_repressing_the_hiding_key_in_the_hidden_state  [proof: lean]
order   settle_the_clock_by_spending_three_consecutive_actions_that_are_not_the_restore_key  [proof: lean]
order   press_the_two_never_pressed_keys_while_the_bar_is_still_long      [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule      [proof: lean]
order   make_some_cell_outside_the_observed_window_vary                   [proof: lean]
order   compare_a_lane_against_the_badge_at_its_own_far_end               [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known          [proof: lean]
order   read_both_consumed_bar_cells_and_the_next_one_after_every_command [proof: lean]

prefer  an_action_the_manual_has_pre_registered_a_frame_for               [ev: 6/9 transitions replay]
prefer  an_action_on_which_two_live_readings_predict_different_frames     [ev: 4 rival pairs open]
prefer  an_action_that_answers_more_than_one_open_question_at_once        [ev: 1 press separates 2 pairs]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  a_slot_never_selected_over_one_already_drawn_twice                [ev: 2 slots seen of a column]
prefer  a_state_whose_lane_carries_the_badge_over_a_lane_without_one      [ev: 1/2 lanes carry a badge]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats        [ev: 98/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced           [ev: 0/9 transitions test it]

heuristic slots_in_the_column_never_yet_selected                          [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed                           [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                     [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                      [admissible: lean]
heuristic cells_of_the_bar_still_unconsumed                               [admissible: lean]

prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead      [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead        [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead        [proof: lean]
prune   repeat_of_a_key_already_witnessed_inert_in_this_exact_state => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead       [proof: lean]
prune   bar_consumed and not goal => dead                                  [proof: lean]
