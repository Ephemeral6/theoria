# playbook.dsl -- eighth draft.
#
# NO NEW EVIDENCE ARRIVED THIS ROUND, so every evidence tag below still cites
# the same five transitions and I have not inflated one of them. Nothing here
# is a stored line of play; every entry is a ranking rule the searcher still
# has to evaluate against whatever state it is actually in.
#
# WHAT MOVED:
#
# 1. THE ORDER OF THE TOP THREE IS UNCHANGED AND I AM SAYING WHY RATHER THAN
#    RESTATING IT. Repressing a blanking key from the blanked state is first
#    because my manual pre-registers a completely null frame for it, which is
#    the strongest prediction I own and the cheapest to falsify. The restore
#    key is second because it separates twelve cells from thirteen. Retesting
#    the single-frame key is third because it costs a frame count and no cell
#    comparison at all.
#
# 2. ONE PRUNE WITHDRAWN. I had a prune saying no plan may rely on cells with
#    no instance. It was doing the work of a blanket ban when the truth is
#    narrower: a colour-5 object would own exactly the 24 swap-footprint cells
#    and nothing else, so the ban was overbroad. Replaced by the accurate one:
#    a plan may not rely on a cell that has never varied, because such a cell
#    is board and gets no instance whatever colour is declared.
#
# 3. ONE PRUNE ADDED ABOUT COST RATHER THAN EXPRESSIBILITY. A plan whose rule
#    set is longer than the pixels it draws is dead even if it replays, because
#    that is constraint 3 and it is the blocker that killed the swap for good.
#
# 4. STILL REMOVED, AND STAYING REMOVED: anything that ranks on the direction
#    of the bar. I cannot tell a budget being spent from progress being made,
#    and the two invert the sign of every such decision.

order   repress_a_blanking_key_in_the_blanked_state_to_test_the_inert_commitment  [proof: lean]
order   press_the_restoring_key_to_separate_the_toll_reading_from_the_rest  [proof: lean]
order   retest_the_key_that_once_returned_a_single_frame_for_freedom_from_the_clock  [proof: lean]
order   test_whether_the_two_blanking_keys_are_one_function_under_two_names  [proof: lean]
order   settle_which_way_the_bar_runs_before_ranking_anything_on_it       [proof: lean]
order   press_the_two_never_pressed_keys_while_the_budget_is_still_long   [proof: lean]
order   bound_the_selector_by_pushing_the_cursor_past_the_slots_already_drawn  [proof: lean]
order   read_the_strip_row_never_displayed_to_score_the_texture_rule      [proof: lean]
order   make_some_cell_outside_the_observed_window_vary                   [proof: lean]
order   probe_the_unknown_before_planning_while_no_goal_is_known          [proof: lean]
order   read_every_bar_cell_that_changed_and_the_returned_frame_count_after_every_command  [proof: lean]

prefer  an_action_the_manual_has_pre_registered_a_null_frame_for          [ev: 4/5 transitions replay]
prefer  an_action_on_which_two_live_readings_predict_different_frames     [ev: 4 meter readings open]
prefer  an_action_that_answers_more_than_one_open_question_at_once        [ev: 1 press separates 2]
prefer  an_action_whose_returned_frame_count_the_readings_disagree_about  [ev: 1/5 commands returned one frame]
prefer  a_key_never_pressed_over_a_key_whose_effect_is_already_witnessed  [ev: 2/7 keys unpressed]
prefer  a_slot_never_selected_over_one_already_drawn_twice                [ev: 2 slots seen of a column]
prefer  a_state_whose_lane_carries_the_badge_over_a_lane_without_one      [ev: 1/2 lanes carry a badge]
prefer  a_press_that_makes_a_board_cell_vary_over_one_that_repeats        [ev: 97/4096 cells ever varied]
prefer  repeating_a_key_from_the_state_that_key_itself_produced           [ev: 0/5 transitions test it]

heuristic bar_cells_still_unconverted                                    [admissible: lean]
heuristic slots_in_the_column_never_yet_selected                         [admissible: lean]
heuristic rows_of_the_frame_never_yet_displayed                          [admissible: lean]
heuristic keys_whose_effect_rests_on_a_single_witness                    [admissible: lean]
heuristic lanes_whose_badge_has_never_been_addressed                     [admissible: lean]
heuristic open_questions_no_single_command_can_yet_separate              [admissible: lean]

prune   plan_that_rests_on_the_bar_direction_being_known => dead          [proof: lean]
prune   plan_that_prices_a_bar_cell_against_any_particular_key => dead    [proof: lean]
prune   plan_that_needs_a_cell_that_has_never_varied_to_change => dead    [proof: lean]
prune   plan_whose_rules_are_longer_than_the_pixels_they_draw => dead     [proof: lean]
prune   plan_that_cites_a_transition_absent_from_the_current_record => dead  [proof: lean]
prune   plan_that_expects_the_manual_to_move_the_bar_a_second_time => dead  [proof: lean]
prune   plan_that_assumes_two_equal_frames_are_the_same_state => dead     [proof: lean]
prune   plan_that_relies_on_the_manual_drawing_the_selector => dead       [proof: lean]
prune   plan_that_trusts_a_blank_or_restore_rule_across_a_selector_move => dead  [proof: lean]
prune   action_whose_successor_every_live_reading_agrees_on => dead       [proof: lean]
prune   repeat_of_a_key_already_witnessed_inert_in_this_exact_state => dead  [proof: lean]
prune   undoing_a_selector_move_that_just_revealed_something => dead      [proof: lean]
prune   bar_consumed and not goal => dead                                [proof: lean]
