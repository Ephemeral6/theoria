# playbook.dsl -- what to buy with the next command, not a route.
#
# ============ READ THIS FIRST: THE MENU MAY HAVE BEEN THE PROBLEM ============
# For four rounds this file has said "press an unpressed key" and for four
# rounds the commands bought were ACTION2, ACTION5, ACTION2, ACTION5. This
# round I stopped assuming the ranking was ignored and looked at what could
# have been ON THE MENU. certify reports `actions: 3` and 18 x 3 = 54 pairs.
# Three. They are key(2), key(4), key(5) -- exactly the three keys my rules
# mentioned. ACTION1 and ACTION3 were pressed by the world at t1 and t3 and
# appeared in NO rule of mine, so they were absent from the manual's action
# alphabet, and if the chooser reads its candidates the way certify reads its
# adjudication list, A2/A5 was not a bad pick from many but the entire set.
#
# THE MANUAL NOW CARRIES key(1) AND key(3). Two witnessed no-op rules,
# key1_inert_at_spawn (t1) and key3_inert_below_spawn (t3), each explaining
# zero pixels and each declared as failing the gain test in the manual's own
# words. They exist to widen the alphabet. If the next command is an ACTION1
# or ACTION3, that was the bottleneck. If it is A2 or A5 again, the
# hypothesis is dead and the fault is genuinely in ranking -- either answer
# is worth more than a fifth identical round.
#
# ---------------------------------------------------------------------------
# THE BOARD AT STATE 21: body home at lattice (1,2); panel in configuration
# B; TEN meter cells burned, cols 54-63 of row 63; next command index is 22,
# EVEN. Eleven lattice cells reachable, the body has stood in TWO. Three
# steps east along lattice row 1 reach the cell beside the knob; the knob
# gates the comb; the comb gates every route to the socket at (8,7). Under
# the harsher meter reading 54 commands remain against a route of about
# nineteen, so the budget is not binding -- waste is.
#
# THE ONE COMMAND THIS FILE IS ARGUING FOR, AS CRITERIA:
#
#  (1) ACTION3 AT SPAWN CLOSES TWO QUESTIONS AT ONCE AND HAS NEVER BEEN
#      TRIED FROM THIS CELL. East is ACTION3 or ACTION4 (ACTION1 was
#      excluded from east at t1). At spawn, west is void and east is three
#      lattice cells of open floor, so pressing either settles which is
#      which -- if it steps it is east, if it does not the OTHER is east by
#      elimination. And ACTION3 is ODD at an EVEN index, which is the only
#      thing that has ever separated the two meter readings, tied 21/21.
#
#  (2) PARITY SEPARATION COMPOUNDS, SO TAKE THE ODD KEY FIRST. Twenty-one
#      commands, twenty-one times a key whose parity matched its index's,
#      zero separation. An odd key now separates; the even key it displaces
#      separates too at index 23. Odd-then-even collects twice, even-then-
#      odd collects never. That is an ordering fact, not a stored route.
#
#  (3) EVERY REFUTATION SO FAR IS THE SAME UNDRAWABLE PIXEL. Sixteen across
#      four rounds, every divergence set a subset of the meter's leading
#      edge -- cells that were board at the instant they burned. Ranking by
#      refutation-fired therefore ranks ACTION2 first forever. Read
#      divergence SETS, discount what the manual priced in advance.
#
#  (4) A2 FROM SPAWN AND A5 FROM (2,2) ARE EXHAUSTED. Nine presses each,
#      216/216 coverage each, cascade split settled 9/9. A tenth witness
#      buys nothing and costs one command and one bar cell.
#
#  (5) ONE PRESS IS ONE LATTICE CELL, 9/9. Distances below are lattice cells.

order     widen_the_key_alphabet_before_blaming_the_ranking                  [proof: lean]
order     check_which_keys_the_manual_can_even_name_before_ranking_them      [proof: lean]
order     take_the_separation_that_compounds_before_the_one_that_does_not    [proof: lean]
order     buy_the_probe_that_closes_two_questions_before_one_that_closes_one [proof: lean]
order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full      [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired    [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                 [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                 [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                 [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it         [proof: lean]

prune     every_rule_it_would_witness_is_already_at_full_coverage => dead     [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead              [proof: lean]
prune     repeats_a_key_already_pressed_from_this_very_cell => dead           [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead         [proof: lean]
prune     key_parity_equals_index_parity_while_the_two_readings_are_tied => dead [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                   [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead      [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead      [proof: lean]
prune     meter_exhausted and not goal => dead                                [proof: lean]

heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic keys_the_manual_named_for_the_first_time_this_round                 [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                     [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                           [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                 [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open                [admissible: lean]
heuristic live_readings_a_command_can_eliminate                               [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings        [admissible: lean]

prefer    a_key_that_entered_the_manuals_alphabet_only_this_round            [ev: 0/21 commands]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on               [ev: 0/16 commands]
prefer    a_key_whose_parity_differs_from_the_command_index                  [ev: 0/21 commands]
prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree        [ev: 9/11 no_ops]
prefer    a_press_at_home_that_splits_up_from_undo_from_return               [ev: 9/9 key5]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 21/21 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                      [ev: 2/7 keys]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
