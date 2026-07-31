# playbook.dsl -- sixth draft. Small changes, each forced.
#
# NOTHING NEW HAPPENED IN THE WORLD THIS ROUND. No transition arrived, so no
# ranking entry may move on evidence about the world. Two things did move.
#
# 1. THE CHECKER IS SETTLED. I pre-registered that a 10-of-13 return would mean
#    the checker resyncs; it returned 9. Replay is open-loop, confirmed. The
#    prefer-entry that ranks pre-registered actions keeps its 9/13 evidence tag
#    and that tag is now a measurement rather than my own arithmetic.
#
# 2. I REMOVED AN ASSUMPTION I HAD NO RIGHT TO. Every previous draft ranked as
#    if the bar were a countdown. I cannot tell a countdown from a progress
#    meter: three cells went 2 -> 3 from the right edge leftward and that is
#    all. Under one reading a probe costs a third of a cell; under the other it
#    earns one. So the two entries that ranked on bar movement are gone and a
#    prune replaces them. Every remaining entry is sign-independent, and the
#    one surviving bar entry -- the deadline prune -- is safe in both readings,
#    because a progress bar that fills would presumably not leave us NOT_GOAL.
#
# THE NEXT COMMAND IS STILL THE SAME COMMAND, AND IT IS STILL WORTH THREE
# ANSWERS. The state is blanked. Pressing the hiding key from here separates
# hide-and-show from toggle-and-toggle, tests the extra-frame clock (the count
# stands at twelve, so a two-frame return should consume (53,60) while my
# manual says it cannot), and scores my manual's committed prediction of inert.
# Immediately after it, repressing the key that once returned a single frame
# tests whether that key is free of the world's clock.
#
# Nothing below is a stored line of play. Every entry is a ranking rule that
# still has to be evaluated against whatever state the searcher is in.

order   separate_hiding_from_toggling_by_repressing_the_hiding_key_in_the_hidden_state  [proof: lean]
order   settle_the_extra_frame_clock_on_the_next_command_before_the_count_drifts  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_for_freedom_from_the_clock  [proof: lean]
order   settle_which_way_the_bar_runs_before_ranking_anything_on_it       [proof: lean]
order   press_the_two_never_pressed_keys_while_the_budget_is_still_long   [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule      [proof: lean]
order   make_some_cell_outside_the_observed_window_vary                   [proof: lean]
order   compare_a_lane_against_the_badge_at_its_own_far_end               [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known          [proof: lean]
order   read_every_bar_cell_that_changed_and_the_returned_frame_count_after_every_command  [proof: lean]

prefer  an_action_the_manual_has_pre_registered_a_frame_for               [ev: 9/13 transitions replay]
prefer  an_action_on_which_two_live_readings_predict_different_frames     [ev: 3 rival pairs open]
prefer  an_action_that_answers_more_than_one_open_question_at_once        [ev: 1 press separates 3]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/13 commands returned one frame]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  a_slot_never_selected_over_one_already_drawn_twice                [ev: 2 slots seen of a column]
prefer  a_state_whose_lane_carries_the_badge_over_a_lane_without_one      [ev: 1/2 lanes carry a badge]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats        [ev: 99/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced           [ev: 0/13 transitions test it]

heuristic advances_of_the_extra_frame_clock_still_available               [admissible: lean]
heuristic slots_in_the_column_never_yet_selected                         [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed                          [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                    [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                     [admissible: lean]
heuristic open_questions_no_single_command_can_yet_separate              [admissible: lean]

prune   plan_that_rests_on_the_bar_direction_being_known => dead          [proof: lean]
prune   plan_that_treats_one_particular_key_as_the_metered_one => dead    [proof: lean]
prune   plan_that_reads_the_march_rule_as_a_price_per_press => dead       [proof: lean]
prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead     [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead       [proof: lean]
prune   plan_that_trusts_a_restore_rule_across_a_selector_move => dead    [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead       [proof: lean]
prune   repeat_of_a_key_already_witnessed_inert_in_this_exact_state => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead      [proof: lean]
prune   bar_consumed and not goal => dead                                [proof: lean]
