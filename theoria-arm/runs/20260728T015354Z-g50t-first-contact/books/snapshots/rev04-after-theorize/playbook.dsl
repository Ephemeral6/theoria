# playbook.dsl -- six transitions in, three of them no-ops, and the manual's
# only rules are about the HUD. So the searcher gets no route from the compiled
# theory this round; everything actionable is here. Two facts drive all of it:
# colour 0 is WALL and colour 5 is FLOOR (so free() must never be read as
# walkable), and every path from the start to the bracketed cell passes through
# the colour-8 cell at rows 38-42 x cols 14-18. That single cell is worth more
# information than any other action available.

order   settle_the_action_table_before_routing              [proof: lean]
order   probe_the_silent_actions_from_a_non_boundary_cell   [proof: lean]
order   resolve_colour8_passability_before_routing_past_it  [proof: lean]
order   test_movement_before_spending_the_last_hud_slot     [proof: lean]
prefer  colour5_neighbour_over_colour0_neighbour            [ev: 1/1 blocked attempts]
prefer  the_only_floor_neighbour_when_the_corridor_is_one_wide [ev: 1/1 corridors read]
prefer  the_neighbour_that_reduces_distance_to_the_bracket  [ev: 1/1 goal candidates in frame]
prefer  the_action_class_that_has_already_moved_the_ring    [ev: 1/2 tallied actions]
prefer  untried_action_from_the_current_cell                [ev: 2/5 actions changed anything]
heuristic maze_cells_between_ring_and_bracketed_cell        [admissible: lean]
prune   target_cell_is_colour0 => dead                      [proof: lean]
prune   all_neighbours_colour0 and not goal => dead         [proof: lean]
prune   both_hud_slots_spent and not goal => dead           [proof: lean]
prune   tally_bar_full and not goal => dead                 [proof: lean]
