# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# The manual did not compile last round, so nothing has ever been checked:
# certify's replay, responsibility and ambiguity blocks are all empty. The
# landmark comment is repaired and the first thing this round must produce
# is an EXECUTABLE manual and a real divergence report. Until that exists,
# every ranking below is a ranking of expected information, not of proof.
#
# The store holds SIX states. The inherited manual claimed thirty-four and
# the current frame refutes it (two burned meter cells, not sixteen). All
# rules now cite t1-t5 only; the beliefs that cannot be witnessed here are
# demoted to pending theorems with their prices named.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   Body at spawn, lattice (1,2). North and west void, south and east open.
#   At spawn:  key(2) -> 48 body cells, both its rules already full
#              key(1) -> nothing, WITNESSED at t1
#              key(3), key(4), key(5) -> nothing, NO WITNESS, and at least
#              one of those three silences is FALSE because east is 3 or 4.
#   Next command index is 6, EVEN: under the parity reading of the meter it
#   burns (63,61) whatever is pressed, and I cannot draw that cell.
#
# ========= THE ONE THING WORTH BUYING =========
# ONE ODD, UNTESTED KEY AT THIS CELL ANSWERS TWO QUESTIONS AT ONCE.
#   (a) DIRECTION. ACTION2 is down. ACTION1 was inert at spawn with east
#       open, so ACTION1 is not east. ACTION3 and ACTION4 were each inert
#       one cell south, where east and west are both void -- which is
#       exactly what the horizontal pair would do there. So east is ACTION3
#       or ACTION4, and pressing either names the key whichever way it
#       answers: a step means that key is east, no step means the other one
#       is east by elimination.
#   (b) THE METER. Reading A says burns follow keys 2 and 4; reading B says
#       burns follow even command indices. Both fit all five transitions
#       because every even index so far carried an even key. An ODD key at
#       the EVEN index 6 splits them in one press, and ACTION3 is odd.
#
# The advertised price of the step onto fresh ground: 48 pixels the manual
# cannot draw, because rows 8-12 cols 20-24 have never changed and are
# board, plus the departure ring which has no east-leaves rule yet. That is
# a refutation priced in advance and it must not be read as a defect.
# 24 pixels for the second step east, 0 for the third.
#
# ------------------------------------------------------------------------
# STATE 5: body home at lattice (1,2); panel in configuration B; TWO meter
# cells burned, cols 62-63 of row 63; next command index 6. Eleven lattice
# cells reachable; the body has stood in two of them. Three steps east
# along lattice row 1 reach the cell beside the knob; the knob is the far
# end of one connected colour-8 wire whose near end is the comb; the comb
# gates every route to the socket at (8,7).

order     make_the_manual_executable_before_trusting_any_other_verdict     [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong   [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one          [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                      [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                        [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 3/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    an_odd_key_at_an_even_index_while_the_meter_readings_are_tied    [ev: 0/5 commands so far]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 3/5 keys at spawn]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 5/5 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    a_press_at_a_third_cell_that_splits_up_from_return               [ev: 1/1 key5_presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
