# playbook.dsl -- thirteenth draft.
#
# WHAT MOVED, AND WHY.
#
# 1. NOTHING IN THIS FILE MOVED, AND THE REASON IS NOT INERTIA. This round was
#    spent on a compile failure in theory.dsl -- an empty `goal:` header, which
#    this grammar does not accept -- and no world command was pressed. No new
#    frame means no new ordering evidence, so every order, prefer, heuristic
#    and prune below is supported by exactly the evidence it was supported by
#    last round. Re-ranking on no data would be inventing a preference, and an
#    invented playbook is worse than a stale one.
#
# 2. THE FIRST ORDER HAS NOW BEEN SKIPPED FOUR ROUNDS. Repeating a blanking key
#    from the blanked state is still first and still unpressed. It is the only
#    press the manual predicts to be null, so it cannot spend the manual's
#    present exactness, and it separates reading F from D and E on the tick
#    alone on top of the four answers it already bought. Four skips of a
#    first-ranked free probe is a fact about the loop, not about the ranking,
#    and it is recorded in the manual as such.
#
# 3. THE SELECTOR EXCURSION STAYS SECOND. Two consecutive non-strip presses
#    give three DISTINCT tick signatures across D, E and F, so one out-and-back
#    pair kills two of three readings of the only monotone quantity in the
#    world. Its known danger -- the state where my blank and restore rules are
#    provably wrong -- is discharged by a condition rather than by avoidance:
#    press no strip key while the upper slot is selected. An out-and-back pair
#    satisfies that by construction, which is why the order names the pair.
#
# 4. STILL NO GOAL, AND NOW SAID PROPERLY. The manual no longer carries an
#    empty goal section; the silence lives in a theorem. Nothing here is a
#    plan. These are orders of interrogation.

order   repeat_a_blanking_key_in_the_blanked_state_for_four_answers_at_once  [proof: lean]
order   press_two_consecutive_non_strip_keys_to_separate_all_three_counter_readings  [proof: lean]
order   take_the_selector_excursion_as_a_pair_and_press_no_strip_key_inside_it  [proof: lean]
order   press_the_two_never_pressed_keys_while_the_bar_is_still_long  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_since_two_readings_rest_on_it  [proof: lean]
order   vary_the_order_of_the_two_blanking_keys_across_a_restore  [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule  [proof: lean]
order   look_at_the_badge_lane_while_its_own_slot_is_the_selected_one  [proof: lean]
order   make_some_cell_outside_the_observed_window_vary  [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known  [proof: lean]
order   read_every_bar_cell_and_the_returned_frame_count_after_every_command  [proof: lean]

prefer  an_action_the_three_counter_readings_give_different_answers_for  [ev: 3 readings, each 3/3 on 3 ticks]
prefer  a_pair_of_actions_that_separates_more_readings_than_either_alone  [ev: 2 presses, 3 signatures]
prefer  an_action_the_manual_has_pre_registered_a_null_frame_for  [ev: 0/13 transitions tested it]
prefer  an_action_that_answers_more_than_one_open_question_at_once  [ev: 1 press separates 4]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/13 commands returned one frame]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  an_action_that_varies_the_order_of_two_keys_already_witnessed_singly  [ev: 11/13 presses were blank_then_restore]
prefer  a_slot_never_selected_over_one_already_drawn_twice  [ev: 2 slots seen of a column]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats  [ev: 99/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced  [ev: 0/13 transitions test it]
prefer  a_probe_launched_from_a_state_the_manual_reconstructs_exactly  [ev: 4096/4096 cells right now]
prefer  an_excursion_that_returns_the_frame_to_where_it_started  [ev: 1/13 commands undid another]

heuristic bar_cells_still_unconverted  [admissible: lean]
heuristic counter_readings_still_alive  [admissible: lean]
heuristic presses_needed_to_separate_the_surviving_counter_readings  [admissible: lean]
heuristic slots_in_the_column_never_yet_selected  [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed  [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness  [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed  [admissible: lean]

prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead  [proof: lean]
prune   plan_that_assumes_the_checker_resyncs_the_manual_between_transitions => dead  [proof: lean]
prune   plan_that_ties_the_bar_tick_to_one_particular_key => dead  [proof: lean]
prune   plan_that_prices_a_bar_cell_at_one_per_restore_press => dead  [proof: lean]
prune   plan_that_counts_the_bar_on_raw_command_number_alone => dead  [proof: lean]
prune   plan_that_treats_the_cadence_as_a_race_between_two_named_readings => dead  [proof: lean]
prune   plan_that_asks_the_manual_to_tick_a_bar_cell_never_yet_witnessed => dead  [proof: lean]
prune   plan_that_needs_a_cell_that_has_never_varied_to_change => dead  [proof: lean]
prune   plan_that_teleports_an_object_out_of_a_cell_the_bar_has_converted => dead  [proof: lean]
prune   plan_that_rests_on_the_bar_meaning_being_known => dead  [proof: lean]
prune   plan_that_spends_the_manuals_present_exactness_and_returns_no_new_frame => dead  [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead  [proof: lean]
prune   plan_that_presses_a_strip_key_while_the_upper_slot_is_selected => dead  [proof: lean]
prune   plan_that_treats_the_two_blanking_keys_as_interchangeable => dead  [proof: lean]
prune   plan_whose_rules_are_longer_than_the_pixels_they_draw => dead  [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_spends_a_round_on_a_manual_that_does_not_compile => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead  [proof: lean]
prune   bar_consumed and not goal => dead  [proof: lean]
