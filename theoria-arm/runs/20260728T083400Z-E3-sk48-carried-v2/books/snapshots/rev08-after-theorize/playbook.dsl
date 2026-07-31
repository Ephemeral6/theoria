# playbook.dsl -- rewritten around the finding that inverted last round's
# economics. What changed:
#
#   THE TOLL READING IS DEAD. t6 was a key(4) press that restored twelve cells
#     and moved the bar not one unit. So key(4) is not "the metered action" and
#     there is nothing to ration. Every prune that rationed it is gone, and I
#     say so rather than quietly dropping it.
#   THE BAR IS PROBABLY A CLOCK, one cell per four actions, consumed right to
#     left, 62 cells and roughly 248 actions left. If that is right, delay is
#     the only thing that costs, and an action that learns nothing is the
#     expensive move.
#   TWO IDENTICAL FRAMES ANSWERED THE SAME KEY DIFFERENTLY (S5 and S7 under
#     key(4)). Any search that treats the frame as the state is unsound here,
#     and that is now a prune rather than a caveat.
#   THE STRIP IS ONE GLOBAL DIAGONAL TEXTURE, colour 2 where (r+c) mod 3 = 1.
#     It predicts the unseen row 33 exactly, so selecting the upper slot is now
#     a scored experiment and not just sightseeing.
#   THE CURRENT STATE IS BLANKED, which makes the blank-versus-toggle
#     separator available for one action, with the manual predicting inert.
#
# Nothing below is a stored line of play. Every entry is a ranking rule that
# still has to be evaluated against whatever state the searcher is in.

order   separate_hiding_from_toggling_by_repressing_the_hiding_key_in_the_hidden_state  [proof: lean]
order   settle_whether_the_bar_is_a_clock_by_spending_actions_that_are_not_the_restore_key  [proof: lean]
order   press_the_two_never_pressed_keys_while_the_bar_is_still_long      [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule      [proof: lean]
order   make_some_cell_outside_the_observed_window_vary                   [proof: lean]
order   compare_a_lane_against_the_badge_at_its_own_far_end               [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known          [proof: lean]
order   read_both_bar_cells_and_the_frame_count_after_every_command       [proof: lean]

prefer  an_action_on_which_two_live_readings_predict_different_frames     [ev: 4 rival pairs open]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  a_slot_never_selected_over_one_already_drawn_twice                [ev: 2 slots seen of a column]
prefer  a_state_whose_lane_carries_the_badge_over_a_lane_without_one      [ev: 1/2 lanes carry a badge]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats        [ev: 98/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced           [ev: 0/9 transitions test it]
prefer  an_action_whose_outcome_the_manual_commits_to_by_a_rule           [ev: 6/9 transitions replay]

heuristic slots_in_the_column_never_yet_selected                          [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed                           [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                     [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                      [admissible: lean]
heuristic cells_of_the_bar_still_unconsumed                               [admissible: lean]

prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead      [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead        [proof: lean]
prune   repeat_of_a_key_already_witnessed_inert_in_this_exact_state => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead       [proof: lean]
prune   bar_consumed and not goal => dead                                  [proof: lean]
