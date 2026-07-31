# playbook.dsl -- fourteenth draft.
#
# WHAT MOVED, AND WHY.
#
# 1. THE TOP OF THE ORDER CHANGED FOR THE FIRST TIME IN FIVE DRAFTS, AND NOT
#    OUT OF BOREDOM. Four commands were finally pressed and what they taught
#    me was structural: the five keys I have pressed move the world only
#    inside a product of three coordinates -- strip shown or blanked, selector
#    in one of two slots, meter length k. All eighteen states are in that
#    product, the world's own hashes confirm it (s14 and s16 answered the
#    identical hash), and every one of them returned NOT_FINISHED. A closed
#    space that has never contained the ending cannot be explored into
#    containing it. So the two keys never pressed go first.
#
# 2. THE CADENCE QUESTION SHRANK BY ONE READING AND GOT ONE CLEAN PRESS.
#    Reading F is dead -- it required the tick at t15, the world ticked at
#    t14. D and E are both 5 for 5 and are provably inseparable by any run of
#    strip keys, because over such a run the two counters advance in lockstep.
#    That is why fourteen presses bought no discrimination and why one
#    selector excursion buys all of it. The excursion moves up to second.
#
# 3. THE REPEAT-BLANK PROBE LOST HALF ITS VALUE AND I DEMOTE IT RATHER THAN
#    RE-ARGUING FOR IT. It used to separate F from D and E on the tick; F is
#    gone, and both survivors now agree that one extra strip press does not
#    tick. It still separates hide-and-show from toggle-and-toggle, which
#    nothing else does, so it stays third rather than falling off.
#
# 4. NEW PRUNE, AND IT IS THE MOST EXPENSIVE THING I HAVE LEARNED. Fourteen
#    work presses accomplished nothing and the meter advanced five times
#    regardless. A quantity that rises at a fixed rate whatever you do is a
#    clock. That is not proof and there is still no goal section, but it flips
#    the price of a press that produces a state I have already seen from free
#    to costly, and the toggle loop I ran for four rounds was the worst
#    offender in the record.
#
# 5. STILL NO PLAN HERE. These are orders of interrogation.

order   press_the_two_never_pressed_keys_before_anything_else  [proof: lean]
order   take_the_selector_excursion_as_a_pair_then_one_strip_key_to_split_D_from_E  [proof: lean]
order   repeat_a_blanking_key_in_the_blanked_state_to_kill_hide_or_toggle  [proof: lean]
order   read_the_returned_frame_count_of_every_command_since_one_reading_counts_it  [proof: lean]
order   prefer_a_press_that_leaves_the_reachable_product_over_one_that_moves_inside_it  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_since_a_reading_rests_on_it  [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   look_at_the_badge_lane_while_its_own_slot_is_the_selected_one  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule  [proof: lean]
order   make_some_cell_outside_the_observed_window_vary  [proof: lean]
order   vary_the_order_of_the_two_blanking_keys_across_a_restore  [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known  [proof: lean]
order   read_every_bar_cell_after_every_command  [proof: lean]

prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  an_action_that_can_leave_the_closed_product_of_states_already_enumerated  [ev: 12/12 states in the product]
prefer  an_action_the_two_surviving_counter_readings_give_different_answers_for  [ev: 2 readings, each 5/5 on 5 ticks]
prefer  a_non_strip_two_frame_press_since_only_that_advances_the_readings_differently  [ev: 14/14 work presses moved both alike]
prefer  an_action_that_answers_more_than_one_open_question_at_once  [ev: 1 press separates 3]
prefer  an_action_the_manual_has_pre_registered_a_null_frame_for  [ev: 0/17 transitions tested it]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/17 commands returned one frame]
prefer  a_slot_never_selected_over_one_already_drawn_twice  [ev: 2 slots seen of a column]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats  [ev: 101/4096 cells ever varied]
prefer  a_probe_launched_from_a_state_the_manual_reconstructs_exactly  [ev: 4096/4096 cells right now]
prefer  an_excursion_that_returns_the_frame_to_where_it_started  [ev: 1/17 commands undid another]

heuristic state_classes_outside_the_enumerated_product  [admissible: lean]
heuristic keys_never_pressed  [admissible: lean]
heuristic counter_readings_still_alive  [admissible: lean]
heuristic presses_needed_to_separate_the_surviving_counter_readings  [admissible: lean]
heuristic bar_cells_still_unconverted  [admissible: lean]
heuristic slots_in_the_column_never_yet_selected  [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed  [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed  [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness  [admissible: lean]

prune   plan_that_spends_a_work_press_and_returns_a_state_already_enumerated => dead  [proof: lean]
prune   plan_that_expects_a_run_of_strip_keys_to_separate_the_two_readings => dead  [proof: lean]
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
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_spends_a_round_on_a_manual_that_does_not_compile => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead  [proof: lean]
prune   bar_consumed and not goal => dead  [proof: lean]
