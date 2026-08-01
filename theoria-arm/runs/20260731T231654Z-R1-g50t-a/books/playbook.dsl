# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHAT THE LAST ROUND ACTUALLY COST =========
# One surprise: replay_mismatch, ONE CELL, (63,63). certify: replay 1/9.
# The previous playbook had advertised 5/9 and called the difference a
# priced-in pixel. IT WAS NOT A PIXEL. Replay rolls forward from frame 0
# and stops -- or stays poisoned -- at the first disagreement, so the four
# meter pixels the previous desk chose not to draw withdrew EIGHT OF NINE
# TRANSITIONS from scoring, including 48 correct body pixels at t6 and 71
# correct pixels at t7 that earned nothing.
#
# THE POLICY CHANGE THAT FOLLOWS IS THE MAIN PRODUCT OF THIS ROUND:
#   DRAW EVERY DRAWABLE PIXEL, even at an MDL loss, even with a rule that
#   can never fire again. "Dead code going forward" is not a reason to
#   delete anything, because replay is retrospective and retrospective is
#   what gets scored. Reserve the word "undrawable" for cells the arm
#   gives no instance for, and for nothing else.
#
# AND THE SUBSTANTIVE REVERSAL:
#   THE KEY READING OF THE METER IS NOT DEAD. t1 and t8 are both ACTION1
#   with opposite outcomes, but they are NOT the same state -- at t1 the
#   bar was pristine, at t8 three cells were already burned, and a guard
#   can read that with colored(rightof(?p), 1). Four burn rules are back
#   and they fit ALL NINE transitions, positives and negatives.
#   The manual should now replay 9/9. If it does not, read the cell.
#
# ========= THE BOARD =========
#   Body at lattice (1,2), spawn. Panel configuration A. Meter burned at
#   row 63 cols 60-63. Next command index 10.
#
#   At spawn:  key(2) -> 48 body cells south, WITNESSED t2 and t6
#              key(1) -> no body cells, WITNESSED t1 and t8
#              key(3) -> no body cells, WITNESSED t9
#              key(4) -> NEVER PRESSED HERE
#              key(5) -> NEVER PRESSED HERE (manual predicts a no-op)
#
#   Open neighbours of spawn are DOWN and EAST only; up and left are void.
#   The next burn lands at (63,59), which is board, has no instance, and
#   is UNDRAWABLE by any rule. That one pixel will halt replay whenever it
#   lands. It is unavoidable and it is not a defect.
#
# ========= THE ONE THING WORTH BUYING =========
# PRESS ACTION4 FROM SPAWN.
#   Last untested candidate for the one direction the whole map needs.
#   East of spawn is three lattice cells of floor leading to the knob that
#   wires the comb, and the comb is the only door south to the socket.
#     body steps east  -> ACTION4 is east, the corridor opens.
#     body stays still -> NO KEY IN 1..5 IS EAST; the body can only travel
#                         lattice column 2, which the comb seals, and
#                         ACTION6/ACTION7 become the only channel. A hard
#                         result, not a waste.
#   It does NOT separate the two meter readings: key 4 burns under both.
#
# ========= WHAT TO BUY AFTER THAT =========
#   ACTION5 AT SPAWN -- now a triple purchase. (a) Thirteen panel rules
#   carry "the body is not at spawn" and both toggles happened at (2,2),
#   so the conjunct has no discriminating witness. (b) ACTION5 has no burn
#   rule, so under the key reading nothing burns while under the clock
#   reading (63,59) burns: ONE PRESS SETTLES THE METER. (c) It is the only
#   route to configuration B, where keys 1, 3 and 4 have never been tried.
#
#   ACTION6, then ACTION7. Never pressed, wholly unconstrained, and one of
#   them is likely the click this action family carries. The knob is a 3x3
#   target the body appears unable to stand on, which is the shape of
#   thing a click presses. The manual can record a click's effect and
#   never its precondition, and it says so rather than guessing.
#
#   RE-TEST 1, 3 AND 4 IN CONFIGURATION B. Every inertness witness for
#   those keys was collected in configuration A -- t1, t3, t4, t8, t9 all
#   sit in A, because t7 put the panel back before t8.
#
# ========= PRICES POSTED IN ADVANCE =========
#   - Replay should be 9/9. Nothing in this record is priced in. A single
#     wrong cell anywhere is a defect in the manual.
#   - (63,59) is undrawable whenever it burns, and it halts replay there.
#     One burn behind, permanently, by construction of the arm.
#   - 48 body pixels the first time the body enters any lattice cell it
#     has not entered before, and replay halts at that transition too.
#     That is the price of new ground and it is worth paying.
#
# ========= WHY NO PLAN =========
# No goal: section, so is_goal is False, plan never returns sat, commit
# never runs. The manual enumerates all three goal forms the grammar
# admits and none can name the winning position, because the socket
# interior has never changed and is therefore board with no instances to
# count. THIS ARM IS IN PURE PROBE MODE ON PURPOSE, and ranking is
# entirely the business of the lines below.

order     draw_every_drawable_pixel_before_optimising_the_manual_length  [proof: lean]
order     never_delete_a_rule_replay_still_needs_however_dead_it_looks   [proof: lean]
order     treat_a_one_pixel_miss_as_a_loss_of_every_later_transition     [proof: lean]
order     prefer_a_witnessed_positive_test_over_an_untested_negation     [proof: lean]
order     settle_whether_action4_is_east_before_any_other_probe          [proof: lean]
order     press_an_untried_action_before_repeating_a_witnessed_no_op     [proof: lean]
order     test_actions_six_and_seven_once_the_five_are_eliminated        [proof: lean]
order     take_the_meter_separator_as_a_rider_not_as_its_own_command     [proof: lean]
order     budget_commands_at_the_pessimistic_meter_reading               [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     confirm_the_manual_compiled_before_trusting_any_certify_number [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     re_test_an_inert_key_in_the_other_panel_configuration          [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it             [proof: lean]
order     collect_the_free_cascade_length_whenever_a_command_is_spent    [proof: lean]

prune     rule_deletion_justified_only_by_being_dead_going_forward => dead [proof: lean]
prune     divergence_explained_by_a_pixel_the_arm_gives_no_instance => dead [proof: lean]
prune     guard_that_rests_on_a_semantics_no_transition_has_exercised => dead [proof: lean]
prune     click_rule_that_cannot_name_the_cell_it_fires_on => dead        [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead            [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead  [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead               [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead  [proof: lean]
prune     meter_exhausted and not goal => dead                            [proof: lean]

heuristic transitions_a_repair_would_return_to_scoring                   [admissible: lean]
heuristic actions_never_pressed_from_the_cell_the_body_stands_on         [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination            [admissible: lean]
heuristic actions_never_pressed_in_the_current_panel_configuration       [admissible: lean]
heuristic actions_outside_the_five_that_carry_no_witness_at_all          [admissible: lean]
heuristic open_questions_a_single_command_can_close_at_once              [admissible: lean]
heuristic divergent_cells_the_arm_could_have_given_an_instance_for       [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                      [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut            [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open           [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                     [admissible: lean]

prefer    the_last_unpressed_candidate_for_a_direction_the_map_needs    [ev: 1/1 candidates]
prefer    a_press_that_closes_two_open_questions_over_one_that_closes_one [ev: 3/3 action5_purchases]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on          [ev: 2/5 keys at spawn]
prefer    an_action_outside_the_five_once_the_five_are_exhausted        [ev: 2/7 actions untried]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff              [ev: 9/9 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered       [ev: 1/1 levels]
prefer    a_press_at_a_third_lattice_cell_that_splits_up_from_return    [ev: 2/2 key5_presses]
prefer    a_configuration_b_press_of_a_key_only_ever_tried_in_a         [ev: 5/5 inert presses in a]
