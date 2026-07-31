# playbook.dsl -- what to buy with the next command, not a route.
#
# WHAT CHANGED, AND IT IS THE BIGGEST CHANGE SINCE THIS FILE EXISTED:
#   (a) THE TOKEN BUDGET WAS A FICTION. The panel toggles back on the next
#       ACTION5, so respawn costs no life -- and it does not burn the meter
#       either, 3/3. Every line that ranked branches by token cost is gone.
#       ACTION5 is now the cheapest informative command on the board.
#   (b) THE METER HAS TWO LIVE READINGS, not four: parity of the command
#       index, and action-keyed on keys 2 and 4. They are separated by ONE
#       free command -- any non-2, non-4 key at an even command index.
#   (c) THE DIRECTION QUESTION IS NOW THE BLOCKING ONE. ACTION4 burned the
#       meter while doing nothing visible, which under the action-keyed
#       reading marks it a movement key; at lattice (2,2) both its candidate
#       directions were void, and at spawn exactly one of them is open. So
#       there is a cell where ACTION4's answer is unambiguous, and the body
#       is standing on it.
#   (d) The respawn-versus-up separator dropped from last-resort to cheap:
#       two descents put the body somewhere ACTION5's two readings disagree.
# No stored sequence anywhere: every line is a criterion on the current frame
# plus the manual's own open questions.

order     settle_the_blocking_question_before_the_merely_open_one       [proof: lean]
order     identify_a_direction_key_before_routing_with_it               [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open   [proof: lean]
order     free_probes_before_probes_that_spend_a_meter_tick             [proof: lean]
order     prefer_a_command_that_settles_two_open_questions_at_once      [proof: lean]
order     separate_two_readings_before_budgeting_against_either         [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it            [proof: lean]
order     reach_the_switch_before_testing_the_switch                    [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end              [proof: lean]
order     witness_a_rule_before_writing_it                              [proof: lean]

prune     destination_ring_pixels_are_not_all_floor => dead             [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead [proof: lean]
prune     meter_probe_using_a_key_that_burns_under_every_reading => dead [proof: lean]
prune     meter_probe_at_an_index_where_both_readings_agree => dead     [proof: lean]
prune     reset_that_returns_to_a_cell_this_branch_already_left => dead  [proof: lean]
prune     meter_exhausted and not goal => dead                          [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut           [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open          [admissible: lean]
heuristic live_readings_a_command_can_eliminate                         [admissible: lean]
heuristic open_questions_a_command_can_close                            [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time           [admissible: lean]
heuristic commands_remaining_at_one_burn_per_movement_key               [admissible: lean]
heuristic unexplained_cells_after_redraw                                [admissible: lean]

prefer    the_movement_key_whose_last_open_candidate_is_open_here       [ev: 3/3 no_ops]
prefer    a_command_whose_rival_readings_predict_different_pixels       [ev: 4/9 burns]
prefer    a_free_command_over_an_equally_informative_costly_one         [ev: 3/3 resets]
prefer    a_reset_pressed_where_its_two_readings_land_in_different_cells [ev: 3/3 resets]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule     [ev: 3/3 moves]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff              [ev: 9/9 diffs]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket          [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                 [ev: 2/7 keys]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered       [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                 [ev: 1/1 levels]
