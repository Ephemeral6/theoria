# playbook.dsl -- ordering for probes, not a route.
# The manual still cannot draw where the body lands, and it has no goal it can
# state, so anything resembling a route here would be a stored solution.
# Every line below is about which question to buy next with a metered action.

order     free_probes_before_metered_probes                   [proof: lean]
order     identify_each_key_direction_before_routing          [proof: lean]
order     resolve_gate_before_committing_to_left_corridor     [proof: lean]

prune     action_that_changed_nothing_in_this_lattice_cell => dead   [proof: lean]
prune     meter_exhausted and not goal => dead                [proof: lean]
prune     panel_slots_exhausted and not goal => dead          [proof: lean]

heuristic lattice_manhattan_to_socket                         [admissible: lean]
heuristic unexplained_cells_after_redraw                      [admissible: lean]

prefer    press_a_key_whose_direction_is_still_unknown        [ev: 2/5 levels]
prefer    probe_from_a_cell_where_two_readings_disagree       [ev: 1/1 levels]
prefer    descend_the_left_corridor                           [ev: 1/1 levels]
prefer    probe_the_knob_cell_along_the_open_top_band         [ev: 1/1 levels]
prefer    avoid_the_respawn_action_while_progress_exists      [ev: 1/1 levels]
prefer    untried_action_in_an_unvisited_lattice_cell         [ev: 2/5 levels]
