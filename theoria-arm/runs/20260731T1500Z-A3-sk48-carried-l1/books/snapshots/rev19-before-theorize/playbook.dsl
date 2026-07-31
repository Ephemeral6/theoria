# playbook.dsl -- fifteenth draft.
#
# WHAT MOVED, AND WHY.
#
# 1. THE ONLY REAL CHANGE IS A PRUNE AGAINST MY OWN LAST ROUND. Zero commands
#    were pressed between the fourteenth draft and this one. The store is
#    byte-identical, certify returned exactly the four numbers I pre-registered,
#    and the manual learned nothing about the world because there was nothing
#    new to learn from. A round that produces a draft and no press is a round
#    spent measuring the manual against a record it has already fitted. That
#    is now a dead plan, written first and pruned explicitly.
#
# 2. THE TOP OF THE ORDER IS UNCHANGED AND IS RESTATED RATHER THAN RE-ARGUED.
#    The five pressed keys move the world only inside a product of three
#    coordinates -- strip shown or blanked, selector slot, meter length. All
#    eighteen states lie in it, the world's own hashes confirm the lattice
#    closes at twelve distinct states, and every one returns NOT_FINISHED. The
#    two never-pressed keys are the only cheap thing that can leave it. They
#    have been rank one for two rounds and have not been pressed.
#
# 3. ONE READING SPLIT INTO TWO AND THE FIRST PROBE GOT MORE VALUABLE, NOT
#    LESS. Reading D ("count two-frame commands") has a twin D-prime ("count
#    every command that is not ACTION7") which this record cannot separate
#    from it. A key(5)/key(6) press separates D from E if it returns two
#    frames and D from D-prime if it returns one. Either way the frame count
#    of that press is information, so read it before anything else.
#
# 4. THE CADENCE IS NOT MERELY UNWRITTEN, IT IS UNWRITEABLE, AND THAT IS NOW
#    A PRUNE. A landmark makes any cell readable, so reading was never the
#    obstacle; the obstacle is that no cell of the frame carries a
#    period-three quantity. All 4096 checked: 3995 constant, 96 period two, 5
#    monotone. Any plan that hopes to find the tick counter in the frame is
#    dead.
#
# 5. STILL NO PLAN HERE, AND STILL NO GOAL. These are orders of interrogation.

order   press_the_two_never_pressed_keys_before_anything_else  [proof: lean]
order   press_at_least_one_command_before_writing_another_draft  [proof: lean]
order   read_the_returned_frame_count_of_every_command_since_two_readings_count_it  [proof: lean]
order   take_the_selector_excursion_as_a_pair_then_one_strip_key_to_split_D_from_E  [proof: lean]
order   repeat_a_blanking_key_in_the_blanked_state_to_kill_hide_or_toggle  [proof: lean]
order   prefer_a_press_that_leaves_the_reachable_product_over_one_that_moves_inside_it  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_since_two_readings_rest_on_it  [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   look_at_the_badge_lane_while_its_own_slot_is_the_selected_one  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule  [proof: lean]
order   make_some_cell_outside_the_observed_window_vary  [proof: lean]
order   vary_the_order_of_the_two_blanking_keys_across_a_restore  [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known  [proof: lean]
order   read_every_bar_cell_after_every_command  [proof: lean]

prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  an_action_that_can_leave_the_closed_product_of_states_already_enumerated  [ev: 12/12 states in the product]
prefer  a_command_pressed_now_over_an_argument_written_now  [ev: 0/1 rounds with a press]
prefer  an_action_the_surviving_counter_readings_give_different_answers_for  [ev: 3 readings, each 5/5 on 5 ticks]
prefer  a_non_strip_press_since_only_that_advances_the_readings_differently  [ev: 14/14 work presses moved both alike]
prefer  a_press_whose_returned_frame_count_would_split_D_from_its_twin  [ev: 1/17 commands returned one frame]
prefer  an_action_that_answers_more_than_one_open_question_at_once  [ev: 1 press separates 3]
prefer  an_action_the_manual_has_pre_registered_a_null_frame_for  [ev: 0/17 transitions tested it]
prefer  a_slot_never_selected_over_one_already_drawn_twice  [ev: 2 slots seen of a column]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats  [ev: 101/4096 cells ever varied]
prefer  a_probe_launched_from_a_state_the_manual_reconstructs_exactly  [ev: 4096/4096 cells right now]
prefer  an_excursion_that_returns_the_frame_to_where_it_started  [ev: 1/17 commands undid another]

heuristic state_classes_outside_the_enumerated_product  [admissible: lean]
heuristic keys_never_pressed  [admissible: lean]
heuristic counter_readings_still_alive  [admissible: lean]
heuristic presses_needed_to_separate_the_surviving_counter_readings  [admissible: lean]
heuristic rounds_since_the_store_last_grew  [admissible: lean]
heuristic bar_cells_still_unconverted  [admissible: lean]
heuristic slots_in_the_column_never_yet_selected  [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed  [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed  [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness  [admissible: lean]

prune   plan_that_produces_a_draft_and_presses_no_command => dead  [proof: lean]
prune   plan_that_expects_certify_to_teach_something_about_the_world => dead  [proof: lean]
prune   plan_that_looks_for_the_tick_counter_inside_the_frame => dead  [proof: lean]
prune   plan_that_treats_the_two_frame_reading_as_a_single_hypothesis => dead  [proof: lean]
prune   plan_that_spends_a_work_press_and_returns_a_state_already_enumerated => dead  [proof: lean]
prune   plan_that_expects_a_run_of_strip_keys_to_separate_the_readings => dead  [proof: lean]
prune   plan_that_treats_the_internal_frame_total_reading_as_still_alive => dead  [proof: lean]
prune   plan_that_counts_the_lone_one_frame_command_toward_the_cadence => dead  [proof: lean]
prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead  [proof: lean]
prune   plan_that_assumes_the_checker_resyncs_the_manual_between_transitions => dead  [proof: lean]
prune   plan_that_assumes_a_rule_replays_the_same_after_the_store_grows => dead  [proof: lean]
prune   plan_that_ties_the_bar_tick_to_one_particular_key => dead  [proof: lean]
prune   plan_that_prices_a_bar_cell_at_one_per_restore_press => dead  [proof: lean]
prune   plan_that_counts_the_bar_on_raw_command_number_alone => dead  [proof: lean]
prune   plan_that_asks_the_manual_to_tick_a_bar_cell_never_yet_witnessed => dead  [proof: lean]
prune   plan_that_needs_a_cell_that_has_never_varied_to_change => dead  [proof: lean]
prune   plan_that_teleports_an_object_out_of_a_cell_the_bar_has_converted => dead  [proof: lean]
prune   plan_that_rests_on_the_bar_meaning_being_known => dead  [proof: lean]
prune   plan_that_spends_the_manuals_present_exactness_and_returns_no_new_frame => dead  [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead  [proof: lean]
prune   plan_that_presses_a_strip_key_while_the_upper_slot_is_selected => dead  [proof: lean]
prune   plan_that_treats_the_two_blanking_keys_as_interchangeable => dead  [proof: lean]
prune   plan_whose_rules_are_longer_than_the_pixels_they_draw => dead  [proof: lean]
prune   plan_that_pins_a_cell_identity_with_one_landmark_per_pixel => dead  [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_spends_a_round_on_a_manual_that_does_not_compile => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead  [proof: lean]
prune   bar_consumed and not goal => dead  [proof: lean]
