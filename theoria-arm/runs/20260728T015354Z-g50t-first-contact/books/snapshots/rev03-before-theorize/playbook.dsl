# playbook.dsl -- six transitions in, three of them no-ops. Everything below is
# an ordering preference or a pruning rule, not a claim about the world. The one
# substantive addition since the last draft is that colour 0 inside the maze is
# void and colour 5 is floor, so the searcher must not read free() as walkable.

order   settle_the_action_table_before_routing          [proof: lean]
order   probe_the_two_silent_actions_from_an_inner_cell [proof: lean]
order   test_movement_before_spending_key5              [proof: lean]
prefer  untried_action_from_the_current_cell            [ev: 2/5 actions changed anything]
prefer  colour5_neighbour_over_colour0_neighbour        [ev: 1/1 blocked attempts]
prefer  step_toward_the_bracketed_cell                  [ev: 1/1 goal candidates in frame]
heuristic maze_cells_between_ring_and_exit_cell         [admissible: lean]
prune   target_cell_is_background_colour => dead        [proof: lean]
prune   both_hud_tokens_spent and not goal => dead      [proof: lean]
