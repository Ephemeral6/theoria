# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= READ THIS FIRST: LAST ROUND'S DIAGNOSIS WAS WRONG =========
# I said the chooser's menu was my rules' key alphabet, and that four rounds
# of A2 A5 A2 A5 were the whole menu rather than a bad pick. I paid two
# witnessed no-op rules to widen it. certify went from `actions: 3,
# pairs_checked: 54` to `actions: 5, pairs_checked: 110`. The alphabet
# widened. THE COMMANDS DID NOT. t22 A2, t23 A5, t24 A2, t25 A5. Alphabet
# width is not the bottleneck and that hypothesis is closed.
#
# ========= THE REPLACEMENT, AND IT IS THE MANUAL'S OWN FAULT =========
# Ground every rule in the only two cells this body has ever stood in.
#   At spawn:            key(2) changes 48 cells. keys 1,3,4,5 change NOTHING.
#   One cell south:      key(5) changes 71 cells. keys 1,2,3,4 change NOTHING.
# Exactly one live key per state, and the two live keys are exactly the two
# keys that have been pressed for five rounds. Anything that ranks by "does
# this action change pixels under the manual" -- the only signal left when
# is_goal compiles to False -- is FORCED into A2 A5 A2 A5. This is not
# stubbornness downstream; it is my manual's silence being read as knowledge.
#
# ========= AND THREE OF THOSE SILENCES ARE FORGED =========
# At spawn, key(1)'s inertness is WITNESSED (t1, zero cells). key(3)'s,
# key(4)'s and key(5)'s are NOT: key(3) and key(4) were each pressed once
# ever, both from one cell south; key(5) was pressed eleven times, all from
# one cell south. Under the standard mapping one of key(3)/key(4) is EAST,
# east of spawn is three lattice cells of unbroken floor, and that key moves
# 48 pixels. So at least one of my three unwitnessed silences is very likely
# FALSE. The DSL has no way to write "unknown"; these lines are the
# substitute.
#
# ------------------------------------------------------------------------
# THE BOARD AT STATE 25: body home at lattice (1,2); panel configuration B;
# TWELVE meter cells burned, cols 52-63 of row 63; next command index 26,
# EVEN. Eleven lattice cells reachable, the body has stood in TWO. Three
# steps east along lattice row 1 reach the cell beside the knob; the knob is
# the far end of one connected colour-8 wire whose near end is the comb; the
# comb gates every route to the socket at (8,7). 52 meter cells remain
# against a route of about nineteen steps: the budget is not binding, waste is.
#
# THE ARGUMENT FOR THE NEXT COMMAND, AS CRITERIA:
#
#  (1) A KEY WHOSE PREDICTED INERTNESS HAS NO WITNESS IS NOT A NO-OP, IT IS
#      AN UNTESTED CLAIM. Three of five keys at spawn are in that state.
#      Ranking them below key(2) because the manual draws nothing for them
#      is circular: the manual draws nothing for them because nobody has
#      ever pressed them here.
#
#  (2) THE EAST KEY IS ONE PRESS AWAY AND UNBLOCKED. East is key(3) or
#      key(4); key(1) was excluded from east at t1. At spawn west is void
#      and east is open floor, so either one settles it -- if it steps it is
#      east, if it does not the other is east by elimination.
#
#  (3) PARITY SEPARATION COMPOUNDS, SO TAKE THE ODD KEY FIRST. Twenty-five
#      commands, twenty-five times a key whose parity matched its index's,
#      zero separation between action-keying and command-parity. An odd key
#      at index 26 separates; the even key it displaces separates again at
#      index 27. Odd-then-even collects twice, even-then-odd never.
#
#  (4) EVERY REFUTATION SO FAR IS THE SAME UNDRAWABLE PIXEL. Twenty across
#      five rounds, every divergence set inside the meter's leading edge --
#      cells that were board at the instant they burned. Ranking by
#      refutation-fired therefore ranks key(2) first forever.
#
#  (5) A2 FROM SPAWN AND A5 FROM ONE CELL SOUTH ARE EXHAUSTED. Eleven
#      presses each, 264/264 coverage each, cascade split settled 11/11. A
#      twelfth witness buys nothing and costs one command and one bar cell.
#
#  (6) ONE PRESS IS ONE LATTICE CELL, 11/11. Distances are lattice cells.

order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     take_the_separation_that_compounds_before_the_one_that_does_not   [proof: lean]
order     buy_the_probe_that_closes_two_questions_before_one_that_closes_one [proof: lean]
order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full     [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]

prune     ranked_only_because_the_manual_predicts_it_changes_pixels => dead  [proof: lean]
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

heuristic keys_whose_inertness_here_rests_on_no_witness                      [admissible: lean]
heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                    [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed     [ev: 3/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on              [ev: 0/20 commands]
prefer    a_key_whose_parity_differs_from_the_command_index                 [ev: 0/25 commands]
prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree       [ev: 11/13 no_ops]
prefer    a_press_at_home_that_splits_up_from_undo_from_return              [ev: 11/11 key5]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 25/25 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                    [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                     [ev: 2/7 keys]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered           [ev: 1/1 levels]
