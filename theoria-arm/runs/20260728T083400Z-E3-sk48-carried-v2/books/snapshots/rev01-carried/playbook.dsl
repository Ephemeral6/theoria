# playbook.dsl -- the manual has no movement rule and cannot have one (the
# mover has no colour of its own), so the searcher gets nothing routable from
# the compiled theory and everything actionable is here. Five facts drive it,
# four of them read off the static board rather than guessed:
#
#   colour 0 is WALL and colour 5 is FLOOR, so free() must never be read as
#     walkable;
#   the colour-8 line is three pixels wide and the mover is five, so no route
#     may pass through the ribbon cells whatever colour 8 means;
#   exactly one cell joins the reachable twelve to the goal region -- the
#     colour-8 filled cell (5,0), gate_cell -- and it lies on the critical
#     path, so testing it costs nothing when the gate is open;
#   NEW THIS ROUND: the left/right binding of the two remaining direction keys
#     is completely undetermined -- both were only ever fired from a cell where
#     left and right were both blocked -- and the bottom corridor needs five
#     steps right, so this must be settled where a wrong guess cannot displace
#     the ring;
#   one HUD attempt remains. Spending it buys a position reset and nothing
#     else, so it is not an experiment, it is the end -- and the same logic
#     bars the two action keys never yet pressed.

order   read_the_tally_and_the_frame_count_after_every_command          [proof: lean]
order   settle_the_lateral_binding_where_one_side_is_off_board          [proof: lean]
order   descend_column_zero_before_exploring_the_blank_side_pockets     [proof: lean]
order   resolve_gate_cell_passability_before_any_other_experiment       [proof: lean]
order   visit_button_cell_only_if_the_gate_refuses                      [proof: lean]
order   press_a_never_pressed_key_only_if_gate_and_button_both_refuse   [proof: lean]
order   never_spend_the_last_hud_slot                                   [proof: lean]

prefer  the_direction_key_with_a_positive_motion_witness                [ev: 1/1 observed motions]
prefer  a_lateral_test_from_a_cell_whose_other_side_is_off_board        [ev: 2/2 uninformative lateral tests so far]
prefer  a_non_void_neighbour_cell_over_an_all_void_neighbour_cell       [ev: 1/1 blocked attempts]
prefer  a_full_five_by_five_non_void_target_over_a_three_wide_ribbon    [ev: 8/8 ribbon cells read]
prefer  the_only_non_void_neighbour_when_the_corridor_is_one_cell_wide  [ev: 1/1 corridors read]
prefer  the_neighbour_that_reduces_lattice_distance_to_goal_cell        [ev: 1/1 goal candidates in frame]
prefer  a_command_whose_cascade_returned_many_frames_over_one_frame     [ev: 2/2 real motions were multi_frame]
prefer  an_untried_action_from_a_cell_that_has_a_known_open_neighbour   [ev: 2/6 commands changed the board]

heuristic lattice_steps_from_ring_to_gate_cell_while_gate_is_untested   [admissible: lean]
heuristic lattice_steps_from_ring_to_corridor_cell_then_to_goal_cell    [admissible: lean]
heuristic lattice_steps_from_ring_to_button_cell_once_the_gate_refuses  [admissible: lean]

prune   target_cell_is_entirely_colour0 => dead                         [proof: lean]
prune   target_cell_is_a_three_wide_ribbon => dead                      [proof: lean]
prune   all_neighbour_cells_entirely_colour0 and not goal => dead       [proof: lean]
prune   route_that_leaves_column_zero_below_lattice_row_two => dead     [proof: lean]
prune   repeat_of_a_key_already_seen_to_do_nothing_from_this_cell => dead [proof: lean]
prune   both_hud_slots_spent and not goal => dead                       [proof: lean]
prune   tally_bar_full and not goal => dead                             [proof: lean]
