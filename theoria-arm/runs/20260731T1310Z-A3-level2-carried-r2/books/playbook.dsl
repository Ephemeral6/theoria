# playbook.dsl -- what to buy with the next command, not a route.
#
# WHAT CHANGED THIS ROUND:
#   (a) COST IS NOW UNIFORM. The meter is command parity, 13/13, so every
#       command costs exactly half a cell and nothing is free. Every line
#       that ranked probes by whether they burned is DELETED -- it was
#       ranking on a distinction that does not exist. Rank by information.
#   (b) ACTION5 AT SPAWN IS A PROVEN NO-OP, 4/4, and still costs half a
#       cell. Pressing it at home is now pruned outright.
#   (c) THE EAST KEY IS THE ONLY BLOCKING QUESTION. ACTION3 and ACTION4 are
#       left and right in unknown order, and they were tested at the one
#       cell where both candidates were void. The body stands at spawn,
#       where left is void and right is open floor -- the cell that
#       separates them.
#   (d) ONE COMMAND SETTLES TWO QUESTIONS: an odd-numbered key pressed at an
#       even command index tests parity, and pressed at spawn it tests the
#       east key. Prefer commands whose four possible diffs are four
#       different pairs of answers.
# No stored sequence anywhere: every line is a criterion on the current
# frame plus the manual's own open questions.

order     settle_the_east_key_before_routing_toward_the_knob              [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open     [proof: lean]
order     prefer_a_command_that_settles_two_open_questions_at_once        [proof: lean]
order     test_a_law_with_a_key_its_rival_reading_says_is_silent          [proof: lean]
order     identify_a_direction_key_before_routing_with_it                 [proof: lean]
order     separate_two_readings_before_planning_against_either            [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it              [proof: lean]
order     reach_the_switch_before_testing_the_switch                      [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end                [proof: lean]
order     witness_a_rule_before_writing_it                                [proof: lean]
order     spend_commands_on_information_while_the_bar_is_still_long       [proof: lean]

prune     destination_ring_pixels_are_not_all_floor => dead               [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead  [proof: lean]
prune     return_to_start_pressed_while_already_at_start => dead          [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead   [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead [proof: lean]
prune     meter_exhausted and not goal => dead                            [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut             [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open            [admissible: lean]
heuristic live_readings_a_command_can_eliminate                           [admissible: lean]
heuristic open_questions_a_command_can_close                              [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time             [admissible: lean]
heuristic commands_remaining_at_one_burn_per_two_commands                 [admissible: lean]
heuristic unexplained_cells_after_redraw                                  [admissible: lean]

prefer    an_untested_direction_key_where_its_two_candidates_disagree     [ev: 4/4 no_ops]
prefer    a_command_whose_rival_readings_predict_different_pixels         [ev: 6/13 burns]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 13/13 diffs]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule       [ev: 3/3 moves]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket            [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered         [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                   [ev: 2/7 keys]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has              [ev: 2/11 cells]
