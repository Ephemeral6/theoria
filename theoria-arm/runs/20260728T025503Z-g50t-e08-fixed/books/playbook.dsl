# playbook.dsl -- what to buy with the next command, not a route.
# Three things changed this round and all three change the ordering.
#   (a) The map is read: the socket is unreachable until the comb opens, so
#       distance-to-socket is the wrong heuristic while the gate is shut and
#       distance-to-switch is the right one.
#   (b) The binding budget is tokens, not the meter. One token remains. Any
#       branch that can end in a respawn ranks below every branch that cannot.
#   (c) replay accumulates and the meter pins it at 1/9, so "wrong cells in
#       replay" is no longer a currency I can spend down. Probes are now chosen
#       by what the raw frame diff will tell me, not by what certify will say.
# Still no stored sequence anywhere: every line is a criterion on the current
# frame plus the manual's own open questions.

order     identify_a_direction_key_before_routing_with_it            [proof: lean]
order     probe_from_a_cell_where_the_rival_readings_disagree        [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it         [proof: lean]
order     reach_the_switch_before_testing_the_switch                 [proof: lean]
order     free_probes_before_token_costing_probes                    [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end           [proof: lean]
order     witness_a_rule_before_writing_it                           [proof: lean]

prune     destination_lattice_cell_is_not_wholly_floor => dead        [proof: lean]
prune     action_that_was_a_no_op_from_this_lattice_cell => dead      [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead [proof: lean]
prune     respawn_while_a_legal_move_exists => dead                   [proof: lean]
prune     respawn_when_no_token_remains and not goal => dead          [proof: lean]
prune     meter_exhausted and not goal => dead                        [proof: lean]

heuristic lattice_distance_to_the_switch_while_the_gate_is_shut       [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open        [admissible: lean]
heuristic commands_remaining_at_one_burn_per_two_commands             [admissible: lean]
heuristic unexplained_cells_after_redraw                              [admissible: lean]

prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule   [ev: 2/2 moves]
prefer    a_key_whose_only_unblocked_candidate_direction_is_forward   [ev: 6/6 no_ops]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff            [ev: 1/1 levels]
prefer    a_step_toward_the_switch_over_a_step_toward_the_socket      [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op               [ev: 2/5 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered     [ev: 1/1 levels]
prefer    stay_on_the_lattice_column_that_reaches_the_gate            [ev: 1/1 levels]
