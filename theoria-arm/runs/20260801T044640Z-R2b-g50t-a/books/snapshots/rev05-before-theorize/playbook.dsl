# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Six states, five transitions: RESET, A1, A2, A3, A4, A5.
#   t1 A1 at spawn        -> nothing
#   t2 A2 at spawn        -> body one lattice cell SOUTH (48 cells) + burn (63,63)
#   t3 A3 one cell south  -> nothing
#   t4 A4 one cell south  -> burn (63,62) and nothing else
#   t5 A5 one cell south  -> body back NORTH (48 cells) + panel toggles A to B (23)
# Body is at spawn, lattice (1,2). Panel is in configuration B. Two meter
# cells burned. Next command index is 6.
#
# THE ROUND ITSELF WAS NOT ABOUT THE WORLD. The manual did not compile --
# theory.py could not be loaded -- so nothing replayed and no check ran. The
# landmark line carried prose where a coordinate must be, and eight rules
# depended on it. Fixed to (8, 14); the empty goal: header removed. Until
# certify loads the manual, every number below is a plan and not a measurement.
#
# ========= THE ONE THING WORTH BUYING, AND IT PAYS TWICE =========
# PRESS ACTION3 AT SPAWN.
#
#   Question 1, the east key. A2 is south (witnessed). A5 went north
#   (witnessed). A1 was pressed at spawn with east OPEN and moved nothing, so
#   A1 is not east. EAST IS A3 OR A4 and there is no third candidate. East of
#   spawn is three lattice cells of unbroken floor; west and north are void.
#   If the body steps, A3 is east and the map closes. If it does not, A4 is
#   east by elimination. Both outcomes name the key.
#
#   Question 2, the meter. Two burns, at index 2 under key 2 and index 4
#   under key 4. Reading A -- burns iff the key is 2 or 4 -- and reading B --
#   burns iff the index is even -- agree on all five transitions and cannot
#   be told apart by anything observed. Index 6 is EVEN and key 3 is neither
#   2 nor 4. A burns nothing; B burns (63,61). One press decides it.
#
#   No other command on the board closes either question, and this one closes
#   both. A2 closes neither: its two rules are at full coverage and its only
#   new datum is the free cascade length.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * First step onto fresh ground costs 48 undrawable pixels. Rows 8-12 cols
#     20-24 have never changed, so they are board, so no instance exists to
#     draw the arrival; and no east-leaves rule is witnessed, so the departure
#     is undrawn too. 24 for the second step, 0 thereafter.
#   * The next effective A5 costs 23 panel cells: this window witnessed the
#     A-to-B toggle only, so the five return rules are not in the manual.
#   * The next A2 costs one pixel: meter_burn_key2_next has no witness.
#   Read a refutation by its divergence set. Where the set is exactly one of
#   these three, the manual is not implicated -- it said so first.
#
# ------------------------------------------------------------------------
# THE MAP, re-verified pixel by pixel against the current frame this round.
# Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6. Eleven cells are
# reachable from spawn; the body has stood in two. Three steps east along
# lattice row 1 reach (1,5), beside the knob at (1,6); the knob is the far end
# of one connected colour-8 wire whose near end is the comb at R=6; the comb
# gates the sole north-south corridor and therefore every route to the socket
# at (8,7), which is drawn as three colour-9 walls, an open west side and a
# pip at its centre -- a keyhole shaped to the body's aperture.

order     compile_before_anything_else_a_manual_that_does_not_load_predicts_nothing [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_command_that_closes_two_open_questions_over_one         [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     buy_the_direction_of_a_toggle_before_buying_its_repetition       [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead      [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic unwitnessed_directions_of_a_toggle_the_manual_half_knows          [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 3/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index        [ev: 5/5 transitions tie]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 3/5 keys at spawn]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 5/5 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
