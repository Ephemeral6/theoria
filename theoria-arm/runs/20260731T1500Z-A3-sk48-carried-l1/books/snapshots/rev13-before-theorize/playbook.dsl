# playbook.dsl -- eleventh draft.
#
# WHAT MOVED, AND WHY.
#
# 1. FOUR ORDERS ARE DISCHARGED AND COME OUT. "Press the restore key to
#    separate the key-memory reading from the counters" was executed twice and
#    killed reading C, reading C-prime, reading A and reading B outright. It
#    has nothing left to buy and is removed. What replaces it is the ONE
#    separation still open: reading D counts every command the world answered
#    with two frames, reading E counts only strip keys, and they differ solely
#    on commands that are not strip keys.
#
# 2. THE FIRST ORDER IS UNCHANGED AND HAS NOW BEEN SKIPPED FOR TWO ROUNDS.
#    Repeating a blanking key from the blanked state is still first, and its
#    value went UP rather than down: it now answers four questions at once
#    (inertness, hide-and-show against toggle, whether a tick can occur with no
#    other change, and D against E through the returned frame count), and it is
#    still the only press my manual predicts to be null, so it cannot spend
#    what exactness the manual has. Four commands went by without it.
#
# 3. A NEW ENTRY THAT IS NOT A PROBE ORDER BUT A COST: pressing a selector key
#    is now the cleanest separation of D from E, and it is also the one press
#    that walks my manual into the state where its blank and restore rules are
#    known to be wrong. It is ranked, but below the free press, and it is
#    ranked as a PAIR -- selector out and back -- because ACTION2 returns the
#    world to the frame my silent manual never left.
#
# 4. STILL REMOVED AND STAYING REMOVED: anything that ranks on what the bar
#    MEANS. Direction is witnessed three times, right to left; filling and
#    spending are still indistinguishable and they invert every sign.
#
# 5. STILL NO GOAL. Nothing here is a plan. These are orders of interrogation.

order   repeat_a_blanking_key_in_the_blanked_state_for_four_answers_at_once  [proof: lean]
order   press_a_key_that_is_not_a_strip_key_to_separate_the_two_counter_readings  [proof: lean]
order   press_the_two_never_pressed_keys_while_the_bar_is_still_long  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_now_that_the_frame_count_is_load_bearing  [proof: lean]
order   vary_the_order_of_the_two_blanking_keys_across_a_restore  [proof: lean]
order   take_a_selector_excursion_only_as_an_out_and_back_pair  [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule  [proof: lean]
order   settle_which_way_the_bar_runs_before_ranking_anything_on_it  [proof: lean]
order   make_some_cell_outside_the_observed_window_vary  [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known  [proof: lean]
order   read_every_bar_cell_and_the_returned_frame_count_after_every_command  [proof: lean]

prefer  an_action_that_separates_the_two_surviving_counter_readings  [ev: 2 readings, both 3/3 on 3 ticks]
prefer  an_action_the_manual_has_pre_registered_a_null_frame_for  [ev: 0/13 transitions tested it]
prefer  an_action_that_answers_more_than_one_open_question_at_once  [ev: 1 press separates 4]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/13 commands returned one frame]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  an_action_that_varies_the_order_of_two_keys_already_witnessed_singly  [ev: 11/13 presses were blank_then_restore]
prefer  a_slot_never_selected_over_one_already_drawn_twice  [ev: 2 slots seen of a column]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats  [ev: 99/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced  [ev: 0/13 transitions test it]
prefer  a_probe_launched_from_a_state_the_manual_reconstructs_exactly  [ev: 4096/4096 cells right now]

heuristic bar_cells_still_unconverted  [admissible: lean]
heuristic counter_readings_no_single_command_can_yet_separate  [admissible: lean]
heuristic slots_in_the_column_never_yet_selected  [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed  [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness  [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed  [admissible: lean]

prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead  [proof: lean]
prune   plan_that_ties_the_bar_tick_to_one_particular_key => dead  [proof: lean]
prune   plan_that_prices_a_bar_cell_at_one_per_restore_press => dead  [proof: lean]
prune   plan_that_counts_the_bar_on_raw_command_number_alone => dead  [proof: lean]
prune   plan_that_asks_the_manual_to_tick_a_bar_cell_never_yet_witnessed => dead  [proof: lean]
prune   plan_that_needs_a_cell_that_has_never_varied_to_change => dead  [proof: lean]
prune   plan_that_rests_on_the_bar_meaning_being_known => dead  [proof: lean]
prune   plan_that_spends_the_manuals_present_exactness_and_returns_no_new_frame => dead  [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead  [proof: lean]
prune   plan_that_trusts_a_blank_or_restore_rule_across_a_selector_move => dead  [proof: lean]
prune   plan_that_treats_the_two_blanking_keys_as_interchangeable => dead  [proof: lean]
prune   plan_whose_rules_are_longer_than_the_pixels_they_draw => dead  [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead  [proof: lean]
prune   bar_consumed and not goal => dead  [proof: lean]
