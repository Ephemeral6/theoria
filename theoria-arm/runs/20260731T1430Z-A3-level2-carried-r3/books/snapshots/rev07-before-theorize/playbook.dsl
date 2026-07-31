# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE OF PLAY (state 9): body home at lattice (1,2); panel in configuration
# B; four meter cells burned, (63,60)..(63,63); nine commands spent; the next
# command has index 10, which is EVEN.
#
# WHAT CHANGED THIS ROUND:
#  (a) THE FOUR REFUTATIONS COST WHAT THE MANUAL SAID THEY WOULD -- 23 cells
#      for the panel's unwitnessed half, one pixel per unwitnessed burn. No
#      line below caused them and none is retracted for them.
#  (b) THE REAL FAILURE IS NOT IN THE MANUAL, IT IS HERE. Nine commands have
#      been spent and the body has occupied exactly TWO lattice cells; six of
#      those commands were spent oscillating between them. An oscillation is
#      not a probe: the second ACTION2-then-ACTION5 pair bought two witnesses
#      the first pair had already bought, and the third bought none at all.
#      New prune, and it is the load-bearing line of this file: a command
#      that returns the body to a cell it has already occupied, from a cell
#      it has already occupied, with a key already witnessed there, is dead.
#  (c) ACTION4 NOW DOMINATES ACTION3 as the way to ask the east question.
#      At spawn, left is void and right is open floor. Either outcome of one
#      ACTION4 press names the east key -- it moves, or ACTION3 is east by
#      elimination, ACTION1 having been excluded from east at t1 -- and one
#      of the two outcomes also advances four cells' worth of route toward
#      the knob at lattice (1,6).
#  (d) THE METER SEPARATOR IS FREE AND NEEDS NO COMMAND OF ITS OWN. Every
#      command so far used a key whose parity matches its own index's parity,
#      which is exactly why nine transitions cannot separate action-keying
#      from command parity. Walking east breaks that alignment on the SECOND
#      step. Buying a dedicated parity probe now would pay a command for a
#      bit that arrives free.
#  (e) ONE PRESS IS ONE LATTICE CELL, 3/3. Every distance below is counted in
#      lattice cells, not pixels.
# No stored sequence anywhere: every line is a criterion on the current frame
# plus the manual's own open questions.

order     settle_the_east_key_before_routing_toward_the_knob                 [proof: lean]
order     prefer_the_probe_that_advances_over_the_probe_that_only_answers    [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open        [proof: lean]
order     take_a_separation_that_arrives_free_over_one_that_costs_a_command  [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it         [proof: lean]
order     identify_a_direction_key_before_routing_with_it                    [proof: lean]
order     separate_two_readings_before_planning_against_either               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                 [proof: lean]
order     reach_the_switch_before_testing_the_switch                         [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end                   [proof: lean]
order     witness_a_rule_before_writing_it                                   [proof: lean]
order     spend_commands_on_information_while_the_bar_is_still_long          [proof: lean]

prune     revisits_an_occupied_cell_by_an_already_witnessed_key => dead      [proof: lean]
prune     repeats_a_transition_whose_rule_already_has_full_coverage => dead  [proof: lean]
prune     dedicated_meter_probe_while_a_map_question_is_open => dead         [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead      [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead [proof: lean]
prune     guard_whose_landmark_carries_no_arc_cell_comment => dead           [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time                [admissible: lean]
heuristic unwitnessed_rules_this_command_would_witness                       [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]
heuristic unexplained_cells_after_redraw                                     [admissible: lean]

prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree        [ev: 3/5 no_ops]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule          [ev: 3/3 moves]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has                 [ev: 2/11 cells]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    a_key_whose_parity_differs_from_the_command_index                  [ev: 0/9 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 9/9 diffs]
prefer    distance_from_spawn_that_makes_up_undo_and_return_differ           [ev: 3/3 key5]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket               [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                      [ev: 2/7 keys]
