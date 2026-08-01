# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHERE THE ROUND ACTUALLY WENT =========
# No command was adjudicated this round. certify returned an EMPTY replay,
# an EMPTY responsibility map and unambiguous null, because theory.py was
# never generated: the manual did not compile. One landmark line carried
# prose where the grammar demands a coordinate. Nothing else could run.
# The manual is repaired and rewritten against the observation record as it
# now stands -- 6 states, 5 transitions -- and it should replay 5/5 with no
# priced-in miss. THE FIRST THING TO CHECK NEXT ROUND IS THAT CERTIFY HAD
# SOMETHING TO RUN. A compile failure is invisible to every other check.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   Body at lattice (1,2), spawn. Panel in configuration B. Two meter cells
#   burned, cols 62-63 of row 63. Next command index is 6.
#
#   At spawn:  key(2) -> 48 body cells south, WITNESSED at t2
#              key(1) -> nothing, WITNESSED at t1
#              key(3), key(4), key(5) -> nothing, NO WITNESS AT THIS CELL
#
#   Open neighbours of spawn are DOWN and RIGHT only; up and left are void.
#   ACTION1 was pressed here and moved nothing, so it is neither.
#   At (2,2) the open neighbours were UP and DOWN only; ACTION3 and ACTION4
#   were each pressed there and moved nothing, so NEITHER IS VERTICAL.
#   If either is a direction key at all, IT IS HORIZONTAL.
#
# ========= THE ONE THING WORTH BUYING, AND IT PAYS TWICE =========
# PRESS ACTION3 FROM SPAWN.
#   (1) It settles the east key. Body steps -> ACTION3 is east and the map
#       closes. Body still -> ACTION4 is east by elimination. Either answer
#       names it, and east of spawn is three lattice cells of unbroken
#       floor while west is void, so the test is free at this cell.
#   (2) It separates the two meter readings AT NO EXTRA COST. Both readings
#       fit t1-t5 identically because every even index carried an even key.
#       Index 6 is EVEN and key 3 is ODD: key-driven predicts no burn,
#       command-parity predicts (63,61) burns. No other single command
#       splits them.
#   (3) It converts one of three forged silences at spawn into a witness.
#   ACTION4 is the same probe minus benefit (2), so it is the fallback and
#   not the choice.
#
# THE ADVERTISED PRICE OF A STEP ONTO FRESH GROUND: 48 pixels the manual
# cannot draw. Rows 8-12 cols 20-24 have never changed, so they are board
# and no rule may draw their first change; the 24 departure pixels need an
# east-leaves rule that cannot be written before an east press witnesses
# one. 24 pixels for the second step, 0 for the third. A refutation whose
# divergence set is exactly that block is the price, not a defect.
#
# TWO PRICES ALREADY POSTED, so neither can be read as a surprise:
#   - the panel toggle-back rules are OUT of the manual for want of a
#     witness in this record, so the next effective ACTION5 costs 23 pixels
#     if the panel does toggle back.
#   - meter_burn_key2_next is OUT for the same reason, so a second ACTION2
#     costs one pixel.
#
# ------------------------------------------------------------------------
# THE MAP, FOR WHEN THE DIRECTION KEYS ARE NAMED. Eleven lattice cells are
# reachable and the body has stood in two. Every route south crosses (6,2),
# 23 of whose 25 pixels are colour 8; lattice column 2 is the only
# north-south corridor, so the comb is the door and not an obstacle. The
# comb is the near end of ONE connected colour-8 wire whose far end is a
# 3x3 knob beside lattice (1,5), three steps east along lattice row 1. The
# socket at (8,7) is drawn as three colour-9 walls with a pip at its exact
# centre -- a keyhole shaped for a body with an aperture -- and it is south
# of the comb. So: open the gate before planning anything south of it, and
# the gate is reached by going EAST, which is the key nobody has pressed.

order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_probe_that_answers_two_open_questions_in_one_press      [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     confirm_the_manual_compiled_before_trusting_any_certify_number   [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     collect_the_free_cascade_length_whenever_a_command_is_spent      [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     even_key_pressed_only_to_separate_the_two_meter_readings => dead   [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_single_command_can_close                         [admissible: lean]
heuristic readings_still_live_that_this_command_would_eliminate             [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                        [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 3/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    an_odd_key_while_the_command_index_is_even                       [ev: 0/5 commands so far]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 3/5 keys at spawn]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 5/5 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
prefer    a_press_at_a_third_lattice_cell_that_splits_up_from_return       [ev: 1/1 key5_presses]
