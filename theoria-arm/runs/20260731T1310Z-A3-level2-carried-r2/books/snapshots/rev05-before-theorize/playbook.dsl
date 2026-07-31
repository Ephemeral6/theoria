# playbook.dsl -- what to buy with the next command, not a route.
# What changed this round and why the ordering changed with it:
#   (a) One command now settles TWO open questions at once. At spawn, up and
#       left are void and down is excluded for ACTION3 and ACTION4 by the
#       t3/t4 no-ops, so right is the only direction either could express --
#       and simultaneously, cumulative frames stand at even, so both parity
#       readings of the meter predict a burn at (63,61) while action-keying
#       predicts none. Any non-key-2, non-key-4 command tests both. Take it.
#   (b) The winning position is now named to the pixel -- lattice (8,7), the
#       body's hole over the pip at (52,46) -- but the comb still shuts the
#       only route to it, so distance-to-the-knob is still the live heuristic
#       and distance-to-the-socket is still dead weight.
#   (c) The binding budget is tokens, not the meter: one token remains, the
#       bar still holds about 62 cells, so roughly 120 commands and one life.
#   (d) replay accumulates and one unpredicted meter cell pins it at 1/5, so
#       "wrong cells in replay" is not a currency I can spend down. Probes are
#       chosen by what the raw frame diff will say, not by what certify will.
# No stored sequence anywhere: every line is a criterion on the current frame
# plus the manual's own open questions.

order     prefer_a_command_that_settles_two_open_questions_at_once     [proof: lean]
order     probe_the_meter_by_piggybacking_it_on_a_direction_probe      [proof: lean]
order     identify_a_direction_key_before_routing_with_it              [proof: lean]
order     probe_from_a_cell_where_one_candidate_direction_is_open      [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it           [proof: lean]
order     reach_the_switch_before_testing_the_switch                   [proof: lean]
order     free_probes_before_token_costing_probes                      [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end             [proof: lean]
order     witness_a_rule_before_writing_it                             [proof: lean]

prune     destination_lattice_cell_is_not_wholly_floor => dead         [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead [proof: lean]
prune     meter_probe_using_a_key_that_burns_under_every_reading => dead [proof: lean]
prune     respawn_while_a_legal_move_exists => dead                    [proof: lean]
prune     respawn_when_no_token_remains and not goal => dead           [proof: lean]
prune     meter_exhausted and not goal => dead                         [proof: lean]

heuristic lattice_distance_to_the_knob_while_the_gate_is_shut          [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open         [admissible: lean]
heuristic commands_remaining_at_one_burn_per_two_commands              [admissible: lean]
heuristic open_questions_a_command_can_close                           [admissible: lean]
heuristic unexplained_cells_after_redraw                               [admissible: lean]

prefer    an_unassigned_key_where_right_is_its_only_open_candidate     [ev: 3/3 no_ops]
prefer    a_command_whose_two_rival_readings_predict_different_pixels  [ev: 2/2 meter]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule    [ev: 1/1 moves]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff             [ev: 1/1 levels]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket         [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                [ev: 2/5 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered      [ev: 1/1 levels]
prefer    stay_on_the_lattice_row_that_reaches_the_knob                [ev: 1/1 levels]
