# playbook.dsl -- what to buy with the next command, not a route.
# The manual still has no goal it can state, so nothing here may name a
# sequence. Every line is a criterion on the current frame plus the manual's
# own open questions. Two lines changed this round: descending now buys a rule
# as well as ground (the missing key2 pair), and the up-probe is priced,
# because only_visited_cells_have_instances says a step into fresh corridor
# costs 48 wrong cells in replay while the up-probe costs 48 and buys the
# whole action map.

order     confirm_a_key_direction_before_relying_on_it             [proof: lean]
order     descend_the_only_corridor_before_testing_the_gate        [proof: lean]
order     resolve_gate_passability_before_planning_the_bottom_room [proof: lean]
order     free_probes_before_life_costing_probes                   [proof: lean]
order     witness_a_rule_before_writing_it                         [proof: lean]

prune     action_that_was_a_no_op_from_this_lattice_cell => dead    [proof: lean]
prune     respawn_while_the_body_still_has_a_legal_move => dead     [proof: lean]
prune     destination_lattice_cell_is_not_floor => dead             [proof: lean]
prune     meter_exhausted and not goal => dead                      [proof: lean]
prune     panel_slots_exhausted and not goal => dead                [proof: lean]

heuristic lattice_manhattan_to_socket_interior                      [admissible: lean]
heuristic unexplained_cells_after_redraw                            [admissible: lean]
heuristic meter_cells_still_lit                                     [admissible: lean]

prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule  [ev: 2/2 moves]
prefer    step_toward_the_socket_when_the_destination_reads_floor    [ev: 2/2 moves]
prefer    press_a_direction_key_from_a_cell_where_it_is_unblocked    [ev: 6/6 no_ops]
prefer    stay_in_the_corridor_that_reaches_the_socket               [ev: 1/1 levels]
prefer    probe_the_knob_only_if_the_gate_refuses_the_body           [ev: 1/1 levels]
prefer    a_probe_whose_outcome_lands_on_cells_that_have_instances   [ev: 1/1 levels]
prefer    untried_action_in_an_unvisited_lattice_cell                [ev: 2/5 levels]
