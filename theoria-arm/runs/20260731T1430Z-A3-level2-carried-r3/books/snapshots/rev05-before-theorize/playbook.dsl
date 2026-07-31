# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE OF PLAY: body home at lattice (1,2), panel in state B, 2 meter cells
# burned, 6 commands spent, next command index 6 (EVEN).
#
# WHAT CHANGED THIS ROUND:
#   (a) THE MANUAL'S FAILURE WAS A COMMENT, NOT A STRATEGY. The 23-cell
#       divergence was an unplaced landmark. No playbook line caused it and
#       none is retracted for it. New line: before ranking any probe, check
#       that the rules it is meant to test can actually fire.
#   (b) COST IS NO LONGER KNOWN TO BE UNIFORM. The window shrank and the
#       evidence that killed action-keying went with it; parity and
#       action-keying are both 5/5 here. So "free probe" is a distinction
#       that may or may not exist, and I rank by information and let the
#       same command settle the cost question as a by-product.
#   (c) THE EAST KEY IS STILL THE ONLY BLOCKING QUESTION, and the body is
#       standing on the one cell that separates ACTION3 from ACTION4: left
#       is void, right is open floor.
#   (d) ONE PRESS IS ONE LATTICE CELL, 1/1 -- the cascade is animation.
#       Every distance below is counted in lattice cells, not pixels.
# No stored sequence anywhere: every line is a criterion on the current
# frame plus the manual's own open questions.

order     settle_the_east_key_before_routing_toward_the_knob              [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open     [proof: lean]
order     prefer_a_command_that_settles_two_open_questions_at_once        [proof: lean]
order     test_a_law_with_a_key_its_rival_reading_says_is_silent          [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it      [proof: lean]
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
prune     key5_pressed_at_spawn_where_both_readings_say_no_op => dead     [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead   [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead [proof: lean]
prune     guard_whose_landmark_carries_no_arc_cell_comment => dead        [proof: lean]
prune     meter_exhausted and not goal => dead                            [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut             [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open            [admissible: lean]
heuristic live_readings_a_command_can_eliminate                           [admissible: lean]
heuristic open_questions_a_command_can_close                              [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time             [admissible: lean]
heuristic unwitnessed_rules_this_command_would_witness                    [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings    [admissible: lean]
heuristic unexplained_cells_after_redraw                                  [admissible: lean]

prefer    an_untested_direction_key_where_its_two_candidates_disagree     [ev: 3/5 no_ops]
prefer    a_command_whose_rival_readings_predict_different_pixels         [ev: 2/5 burns]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                [ev: 5/5 diffs]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule       [ev: 1/1 moves]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket            [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered         [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                   [ev: 2/7 keys]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has              [ev: 2/11 cells]
prefer    distance_from_spawn_that_makes_up_and_return_to_start_differ    [ev: 1/1 key5]
