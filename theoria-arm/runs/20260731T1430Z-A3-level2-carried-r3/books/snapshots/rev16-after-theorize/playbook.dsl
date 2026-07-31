# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHAT CHANGED IN THE MANUAL, AND WHY IT MATTERS HERE =========
# For six rounds the commands were A2 A5 A2 A5. Two explanations were tried
# and both are closed: the chooser's alphabet (refuted -- certify widened
# 3 -> 5 actions, commands unmoved), and stubborn ranking (wrong -- there was
# nothing to rank). The real cause was in my own manual: it left EXACTLY ONE
# key with a non-identity successor in each of the two cells this body has
# stood in, and those two keys are exactly A2 and A5.
#
# This round I removed the cause instead of describing it. Thirteen panel
# rules carried `colored(spawn_probe, 5)`. That atom had 13 positive
# witnesses and ZERO negative ones -- every ACTION5 ever pressed followed an
# ACTION2, so "key(5) was pressed" and "the body is away" are the same
# thirteen events. Constraint 3 settles it: the atom explains no pixel, costs
# thirteen conjuncts, and deleting it changes no replay. Deleted.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   At spawn (where the body IS):  key(2) -> 48 body cells
#                                  key(5) -> 23 panel cells, body unmoved
#                                  keys 1,3,4 -> nothing
#   One cell south:                key(5) -> 71 cells; all others nothing
#
# TWO live keys at spawn, for the first time in six rounds. That is the whole
# product of the round and the lines below exist to spend it correctly.
#
# ========= AND TWO SILENCES ARE STILL FORGED =========
# key(1) inert at spawn is WITNESSED (t1, zero cells). key(3) and key(4)
# inert at spawn are NOT: each was pressed once ever, both from one cell
# south. Under the standard mapping one of them is EAST, east of spawn is
# three lattice cells of unbroken floor, and that key moves 48 pixels. At
# least one of those two silences is very likely FALSE.
#
# ------------------------------------------------------------------------
# STATE 29: body home at lattice (1,2); panel configuration B; FOURTEEN meter
# cells burned, cols 50-63 of row 63; next command index 30, EVEN. Eleven
# lattice cells reachable, the body has stood in TWO. Three steps east along
# lattice row 1 reach the cell beside the knob; the knob is the far end of one
# connected colour-8 wire whose near end is the comb; the comb gates every
# route to the socket at (8,7). 50 meter cells against a route of about
# nineteen steps: the budget is not binding, waste is.
#
# THE ARGUMENT FOR THE NEXT COMMAND, AS CRITERIA:
#
#  (1) KEY(5) AT SPAWN IS NOW THE CHEAPEST MULTI-BIT PROBE ON THE BOARD, and
#      it is the one command whose value the cut created. One press yields
#      three independent bits in one legible diff: 23 cells vindicates the
#      cut, 0 cells refutes it and puts thirteen rules into repair, 71 cells
#      says ACTION5 is UNDO; and (63,49) burning or not settles meter parity,
#      because key 5 is odd and index 30 is even. A fourth bit comes free on
#      the following command: if the panel toggled, the next A2 from spawn
#      takes 7 internal frames instead of 9.
#
#  (2) A KEY WHOSE PREDICTED INERTNESS HAS NO WITNESS IS NOT A NO-OP, IT IS
#      AN UNTESTED CLAIM. key(3) and key(4) at spawn are both in that state.
#      Ranking them below key(2) because the manual draws nothing for them is
#      circular: the manual draws nothing because nobody has pressed them here.
#
#  (3) THE EAST KEY IS ONE PRESS AWAY AND UNBLOCKED. East is key(3) or
#      key(4); key(1) was excluded from east at t1. At spawn west is void and
#      east is open floor, so either one settles it -- if it steps it is east,
#      if it does not the other is east by elimination.
#
#  (4) PARITY SEPARATION COMPOUNDS, SO TAKE THE ODD KEY FIRST. Twenty-nine
#      commands, twenty-nine times a key whose parity matched its index's,
#      zero separation between action-keying and command-parity. An odd key at
#      index 30 separates; the even key it displaces separates again at 31.
#
#  (5) EVERY REFUTATION SO FAR IS THE SAME UNDRAWABLE PIXEL. Twenty-four
#      across six rounds, every divergence set inside the meter's leading edge
#      -- cells that were board at the instant they burned. Ranking by
#      refutation-fired therefore ranks key(2) first forever.
#
#  (6) A2 FROM SPAWN IS EXHAUSTED. Thirteen presses, 312/312 coverage, cascade
#      split settled 13/13. A fourteenth witness buys nothing and costs one
#      command and one bar cell.
#
#  (7) ONE PRESS IS ONE LATTICE CELL, 13/13. Distances are lattice cells.

order     prefer_a_command_whose_outcome_splits_a_rule_the_cut_just_created  [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     take_the_separation_that_compounds_before_the_one_that_does_not   [proof: lean]
order     buy_the_probe_that_closes_three_questions_before_one_that_closes_one [proof: lean]
order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full     [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead    [proof: lean]
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

heuristic newly_unguarded_rules_a_command_would_put_to_first_test           [admissible: lean]
heuristic keys_whose_inertness_here_rests_on_no_witness                      [admissible: lean]
heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                    [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]

prefer    a_press_that_tests_a_guard_removed_for_failing_the_gain_test      [ev: 13/13 unguarded]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed     [ev: 2/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on              [ev: 0/24 commands]
prefer    a_key_whose_parity_differs_from_the_command_index                 [ev: 0/29 commands]
prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree       [ev: 15/17 no_ops]
prefer    a_press_at_home_that_splits_up_from_undo_from_return              [ev: 13/13 key5]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 29/29 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                    [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                     [ev: 2/7 keys]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered           [ev: 1/1 levels]
