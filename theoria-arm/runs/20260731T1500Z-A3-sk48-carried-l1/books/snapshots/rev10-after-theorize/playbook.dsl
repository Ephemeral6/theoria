# playbook.dsl -- tenth draft.
#
# WHAT MOVED. No command was pressed this round, so nothing here may move on
# new evidence about the world. Two things move on evidence about the manual:
#
# 1. A NEW TOP-LEVEL FACT WORTH RANKING ON: THE MANUAL IS CURRENTLY EXACT.
#    Certify's 6 of 9 with reconvergence at transition 7 means the manual's
#    present state equals the world's present frame in all 4096 cells. That is
#    an asset, not a score: every probe pressed from here is scored against a
#    correct baseline, so a divergence measured now is information about the
#    world rather than accumulated drift. Two entries encode it -- a prefer
#    that ranks probes launched from an exact state, and a prune that kills
#    plans which spend the exactness for nothing.
#
# 2. ONE ORDER IS NOW STRICTLY BETTER THAN I THOUGHT AND STAYS FIRST.
#    Repeating a blanking key from the blanked state answers three questions
#    at once -- inertness, hide-and-show against toggle, and whether the tick
#    follows ACTION3 onto any next command -- and it is the ONLY press in the
#    space that my manual predicts to be null, so it cannot cost the exactness
#    described above whichever way it lands.
#
# 3. STILL REMOVED AND STAYING REMOVED: anything that ranks on what the bar
#    MEANS. Its direction is witnessed twice, right to left, but filling and
#    spending are still indistinguishable and they invert every sign.
#
# 4. UNCHANGED AND UNDER-CLAIMED ON PURPOSE: no goal is known, so nothing here
#    is a plan. These are orders of interrogation, not a route.

order   repeat_a_blanking_key_in_the_blanked_state_for_three_answers_at_once  [proof: lean]
order   press_the_restore_key_to_separate_the_key_memory_reading_from_the_counters  [proof: lean]
order   vary_the_order_of_the_two_blanking_keys_across_a_restore  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_for_freedom_from_the_clock  [proof: lean]
order   press_the_two_never_pressed_keys_while_the_bar_is_still_long  [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule  [proof: lean]
order   settle_which_way_the_bar_runs_before_ranking_anything_on_it  [proof: lean]
order   make_some_cell_outside_the_observed_window_vary  [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known  [proof: lean]
order   read_every_bar_cell_and_the_returned_frame_count_after_every_command  [proof: lean]

prefer  a_probe_launched_from_a_state_the_manual_reconstructs_exactly  [ev: 4096/4096 cells right now]
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
prune   plan_that_spends_the_manuals_present_exactness_and_returns_no_new_frame => dead  [proof: lean]
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
