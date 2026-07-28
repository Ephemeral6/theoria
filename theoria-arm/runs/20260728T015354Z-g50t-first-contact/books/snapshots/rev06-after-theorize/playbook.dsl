# playbook.dsl -- the manual has no movement rule and cannot have one (the
# mover has no colour of its own), so the searcher gets nothing routable from
# the compiled theory and everything actionable is here. Four facts drive all
# of it, and three of them are read off the static board rather than guessed:
#
#   colour 0 is WALL and colour 5 is FLOOR, so free() must never be read as
#     walkable;
#   the colour-8 line is three pixels wide and the mover is five, so no route
#     may pass through cells (1,4)..(5,4) or (5,1)..(5,3) whatever colour 8
#     means;
#   exactly one cell joins the reachable twelve to the goal region -- the
#     colour-8 filled cell (5,0), gate_cell -- and one command from (4,0)
#     decides the whole level;
#   one HUD attempt remains. Spending it buys a position reset and nothing
#     else, so it is not an experiment, it is the end.

order   read_the_tally_after_every_command                             [proof: lean]
order   confirm_the_direction_map_from_a_cell_with_a_real_neighbour    [proof: lean]
order   descend_column_zero_before_exploring_the_blank_side_pockets    [proof: lean]
order   resolve_gate_cell_passability_before_any_other_experiment      [proof: lean]
order   visit_the_reachable_terminal_only_if_the_gate_refuses          [proof: lean]
order   never_spend_the_last_hud_slot                                  [proof: lean]

prefer  the_action_class_that_has_already_moved_the_ring               [ev: 1/1 observed motions]
prefer  a_non_void_neighbour_cell_over_an_all_void_neighbour_cell      [ev: 1/1 blocked attempts]
prefer  a_full_five_by_five_non_void_target_over_a_three_wide_ribbon   [ev: 8/8 ribbon cells read]
prefer  the_only_non_void_neighbour_when_the_corridor_is_one_cell_wide [ev: 1/1 corridors read]
prefer  the_neighbour_that_reduces_lattice_distance_to_goal_cell       [ev: 1/1 goal candidates in frame]
prefer  an_untried_action_from_a_cell_that_has_a_known_open_neighbour  [ev: 2/6 commands changed the board]
prefer  a_command_whose_cascade_returned_many_frames_over_one_frame    [ev: 2/2 real motions were multi_frame]

heuristic lattice_steps_from_ring_to_goal_cell                         [admissible: lean]
heuristic lattice_steps_from_ring_to_gate_cell_while_gate_is_untested  [admissible: lean]

prune   target_cell_is_entirely_colour0 => dead                        [proof: lean]
prune   target_cell_is_a_three_wide_ribbon => dead                     [proof: lean]
prune   all_neighbour_cells_entirely_colour0 and not goal => dead      [proof: lean]
prune   route_that_leaves_column_zero_below_lattice_row_two => dead    [proof: lean]
prune   both_hud_slots_spent and not goal => dead                      [proof: lean]
prune   tally_bar_full and not goal => dead                            [proof: lean]
