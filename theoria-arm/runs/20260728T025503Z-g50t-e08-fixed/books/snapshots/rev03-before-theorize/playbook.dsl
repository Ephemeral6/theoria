# playbook.dsl -- what to do with a manual that cannot yet predict.
# Every line below is about ordering probes, not about a route: after five
# transitions the only route I could write down would be a stored solution.

order     resolve_gate_before_committing_to_left_corridor   [proof: lean]
order     free_probes_before_metered_probes                 [proof: lean]

prune     action_that_changed_nothing_in_this_lattice_cell => dead   [proof: lean]
prune     panel_slots_exhausted and not goal => dead        [proof: lean]

heuristic lattice_manhattan_to_socket                       [admissible: lean]
heuristic unexplained_cells_after_redraw                    [admissible: lean]

prefer    probe_the_knob_cell_along_the_open_top_band       [ev: 1/1 levels]
prefer    descend_the_left_corridor                         [ev: 1/1 levels]
prefer    avoid_the_respawn_action_while_progress_exists    [ev: 1/1 levels]
prefer    untried_action_in_an_unvisited_lattice_cell       [ev: 2/5 levels]
