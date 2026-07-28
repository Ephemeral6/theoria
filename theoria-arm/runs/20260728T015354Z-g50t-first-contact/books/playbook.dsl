# playbook.dsl -- six transitions in, three of them no-ops. Almost everything
# below is an ordering preference, not a claim about the world.

order   map_the_action_table_before_routing     [proof: lean]
order   test_movement_before_spending_key5      [proof: lean]
prefer  untried_action_from_the_current_cell    [ev: 2/5 actions changed anything]
prefer  step_toward_the_bracketed_cell          [ev: 1/1 goal candidates in frame]
heuristic maze_cells_between_ring_and_exit_cell [admissible: lean]
prune   both_hud_tokens_spent and not goal => dead [proof: lean]
