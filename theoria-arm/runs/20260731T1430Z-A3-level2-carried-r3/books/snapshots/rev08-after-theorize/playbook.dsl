# playbook.dsl -- what to buy with the next command, not a route.
#
# STATE OF PLAY (state 13): body home at lattice (1,2); panel in
# configuration B; SIX meter cells burned, cols 58-63 of row 63; thirteen
# commands spent; the next command has index 14, which is EVEN.
#
# THE ONE NUMBER THAT MATTERS: thirteen commands spent, TWO lattice cells
# ever occupied, and the last eight commands were the same two keys
# alternating between the same two cells. The previous edition of this file
# already carried the prune that forbids exactly that, and four more such
# commands were bought anyway. So the prune was not the problem; the RANKING
# was. This edition names the reason and fixes the ranking.
#
# WHY THE RANKING FAILED: every ACTION2 press burns a meter cell, every burn
# lands on a cell that is board at the instant it burns, and no rule the
# manual can express draws it. So EVERY ACTION2 PRESS FIRES A REFUTATION no
# matter how little it teaches, and a desk that ranks by refutation-fired
# will keep buying the move that fires one. Four refutations this round,
# two wrong pixels, zero rules implicated, one whole round consumed. The
# refutation channel is saturated and must be read by its divergence SET,
# not by whether it fired. First two prunes below encode that.
#
# WHAT THE FOUR COMMANDS DID BUY, honestly: a fifth and sixth witness for
# rules already at full coverage (worth nothing), a fifth toggle of the
# panel (worth nothing), two more burns on the diagonal where the two meter
# readings agree (worth nothing), and ONE real finding -- ACTION2 animates
# in 7 frames under panel configuration A and 9 under B, 5/5, which is the
# only evidence that the panel is not purely cosmetic.
#
# WHAT TO BUY NEXT, and the reasoning, not the sequence:
#  (a) THE EAST KEY IS THE ONLY QUESTION WHOSE ANSWER MOVES THE BODY. At
#      spawn, west is void and east is open floor, so one press of the
#      right-hand candidate either steps a lattice cell east or names the
#      other candidate by elimination -- ACTION1 was already excluded from
#      east at t1. Either outcome is decisive and one outcome also spends
#      the first of the four steps that reach the knob at lattice (1,6).
#      Advertised cost: 49 divergent cells, all of them cells the manual
#      said in advance it cannot own. Do not read that as a refutation.
#  (b) A ZERO-CELL ANSWER TO (a) KILLS BOTH METER READINGS AT ONCE, because
#      index 14 is even and the key candidate is even, so action-keying and
#      command-parity both demand a burn. That is the one branch where the
#      cheap probe pays double.
#  (c) THE METER SEPARATOR IS STILL FREE AND STILL UNTAKEN. Thirteen
#      commands, thirteen times a key whose parity equalled its index's
#      parity, zero separation. Any odd key at index 14, or any even key at
#      index 15, breaks it. Walking east on two consecutive commands breaks
#      it on the second step at no cost, which is why no dedicated meter
#      probe is worth a command while the map is open.
#  (d) THE CHEAPEST TRIPLE ON THE BOARD IS THE RETURN KEY PRESSED AT HOME.
#      The body is at spawn for the first time with a free command: the
#      manual predicts total silence there, which tests the spawn guard
#      (five positives, zero negatives, five rounds running); the key is
#      odd and the index even, which separates the meter; and a 48-cell
#      move south would say the key is UNDO rather than UP or RETURN.
#      Three open questions, one press, zero route progress. Rank it second
#      to (a), and first if (a) turns out to leave the body where it stands.
#  (e) ONE PRESS IS ONE LATTICE CELL, 5/5. Every distance below is counted
#      in lattice cells, not pixels.
# No stored sequence anywhere: every line is a criterion on the current
# frame plus the manual's own open questions.

order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired    [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                 [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                 [proof: lean]
order     prefer_the_probe_that_advances_over_the_probe_that_only_answers    [proof: lean]
order     probe_a_key_from_a_cell_where_exactly_one_candidate_is_open        [proof: lean]
order     take_a_separation_that_arrives_free_over_one_that_costs_a_command  [proof: lean]
order     read_the_cascade_length_it_is_evidence_that_costs_no_pixel         [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it         [proof: lean]
order     identify_a_direction_key_before_routing_with_it                    [proof: lean]
order     separate_two_readings_before_planning_against_either               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                 [proof: lean]
order     reach_the_switch_before_testing_the_switch                         [proof: lean]
order     try_an_unpressed_key_before_declaring_a_dead_end                   [proof: lean]
order     witness_a_rule_before_writing_it                                   [proof: lean]
order     spend_commands_on_information_while_the_bar_is_still_long          [proof: lean]

prune     divergence_lies_only_on_the_meter_leading_edge => dead              [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead     [proof: lean]
prune     revisits_an_occupied_cell_by_an_already_witnessed_key => dead       [proof: lean]
prune     repeats_a_transition_whose_rule_already_has_full_coverage => dead   [proof: lean]
prune     dedicated_meter_probe_while_a_map_question_is_open => dead          [proof: lean]
prune     key_parity_equals_command_index_parity_when_bought_for_the_meter => dead [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                   [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead      [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead      [proof: lean]
prune     probe_where_both_live_readings_predict_the_same_pixel => dead       [proof: lean]
prune     probe_that_repeats_a_key_at_a_cell_that_cannot_separate_it => dead  [proof: lean]
prune     guard_whose_landmark_carries_no_arc_cell_comment => dead            [proof: lean]
prune     meter_exhausted and not goal => dead                                [proof: lean]

heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic cells_this_command_makes_ownable_for_the_first_time                [admissible: lean]
heuristic unwitnessed_rules_this_command_would_witness                       [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                    [admissible: lean]

prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree        [ev: 5/7 no_ops]
prefer    a_step_that_both_advances_and_witnesses_an_unwritten_rule          [ev: 5/5 moves]
prefer    a_cell_the_body_has_never_stood_in_over_one_it_has                 [ev: 2/11 cells]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    a_key_whose_parity_differs_from_the_command_index                  [ev: 0/13 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 13/13 diffs]
prefer    a_press_at_home_that_splits_up_from_undo_from_return               [ev: 5/5 key5]
prefer    a_step_toward_the_knob_over_a_step_toward_the_socket               [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                      [ev: 2/7 keys]
