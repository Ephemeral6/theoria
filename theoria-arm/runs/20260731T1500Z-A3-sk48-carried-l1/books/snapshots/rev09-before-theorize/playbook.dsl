# playbook.dsl -- ninth draft.
#
# WHAT MOVED, AND ALL OF IT IS PAID FOR BY THE FOUR NEW COMMANDS:
#
# 1. ONE ENTRY OF THE EIGHTH DRAFT WAS VINDICATED OUTRIGHT AND I AM PROMOTING
#    IT TO THE TOP OF THE PRUNES. `plan_that_assumes_two_equal_frames_are_the
#    _same_state` was written as a hunch. It is now proven: states 5 and 7 are
#    the same 4096 cells and ACTION4 from each gave different successors. A
#    planner that keys on frames in this world is planning in the wrong space,
#    and that is a fact, not a preference.
#
# 2. ONE ORDER DELETED BECAUSE THE QUESTION IT ASKED IS ANSWERED. The toll-on-
#    the-restore-key reading is refuted -- t6 was an ACTION4 and the bar did
#    not move -- so there is nothing left to separate.
#
# 3. THE NEW TOP TWO ARE BOTH ABOUT THE HIDDEN BIT, WHICH IS NOW THE ONLY
#    THING THIS MANUAL GETS WRONG. Repeating a blanking key from the blanked
#    state goes first because it answers three questions with one press and
#    does not destroy the setup for the second probe: inertness (never once
#    tested in nine transitions), hide-and-show against toggle, and whether the
#    tick follows ACTION3 onto any next command or specifically onto ACTION4.
#    Pressing ACTION4 goes second because it separates the reading I rank first
#    from the two numerological ones, at a cost of one cell of prediction.
#
# 4. A NEW PRUNE ABOUT REACH. My march rule can only ever repaint a bar cell
#    that has already ticked once, because the arm gives instances only to
#    cells that have varied. Any plan that asks the manual to advance the bar
#    into fresh territory is asking for a pixel the arm will not give it.
#
# 5. STILL REMOVED AND STAYING REMOVED: anything that ranks on what the bar
#    MEANS. Its direction is now witnessed twice, right to left, but filling
#    and spending are still indistinguishable and they invert every sign.

order   repeat_a_blanking_key_in_the_blanked_state_for_three_answers_at_once  [proof: lean]
order   press_the_restore_key_to_separate_the_key_memory_reading_from_the_counters  [proof: lean]
order   blank_with_one_key_then_restore_then_blank_with_the_other_and_restore  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_for_freedom_from_the_clock  [proof: lean]
order   press_the_two_never_pressed_keys_while_the_bar_is_still_long  [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule  [proof: lean]
order   settle_which_way_the_bar_runs_before_ranking_anything_on_it  [proof: lean]
order   make_some_cell_outside_the_observed_window_vary  [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known  [proof: lean]
order   read_every_bar_cell_and_the_returned_frame_count_after_every_command  [proof: lean]

prefer  an_action_whose_successor_the_surviving_readings_disagree_about  [ev: 3 cadence readings open]
prefer  an_action_the_manual_has_pre_registered_a_null_frame_for  [ev: 0/9 transitions tested it]
prefer  an_action_that_answers_more_than_one_open_question_at_once  [ev: 1 press separates 3]
prefer  an_action_that_varies_the_order_of_two_keys_already_witnessed_singly  [ev: 6/9 presses were blank_then_restore]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/9 commands returned one frame]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  a_slot_never_selected_over_one_already_drawn_twice  [ev: 2 slots seen of a column]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats  [ev: 98/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced  [ev: 0/9 transitions test it]

heuristic bar_cells_still_unconverted  [admissible: lean]
heuristic cadence_readings_no_single_command_can_yet_separate  [admissible: lean]
heuristic slots_in_the_column_never_yet_selected  [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed  [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness  [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed  [admissible: lean]

prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead  [proof: lean]
prune   plan_that_rests_on_the_bar_meaning_being_known => dead  [proof: lean]
prune   plan_that_asks_the_manual_to_tick_a_bar_cell_never_yet_witnessed => dead  [proof: lean]
prune   plan_that_needs_a_cell_that_has_never_varied_to_change => dead  [proof: lean]
prune   plan_that_prices_a_bar_cell_at_one_per_restore_press => dead  [proof: lean]
prune   plan_whose_rules_are_longer_than_the_pixels_they_draw => dead  [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead  [proof: lean]
prune   plan_that_trusts_a_blank_or_restore_rule_across_a_selector_move => dead  [proof: lean]
prune   plan_that_treats_the_two_blanking_keys_as_interchangeable => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead  [proof: lean]
prune   bar_consumed and not goal => dead  [proof: lean]
