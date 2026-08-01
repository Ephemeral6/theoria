# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Ten states, nine transitions. The manual compiles and replayed 5/5 last
# round with zero unexplained cells; the two refutations that brought me
# back are both repaired IN THE MANUAL, not here: the 23 panel cells of
# t7 now have five return rules, and the two new meter cells are dynamic
# so their burns can finally be drawn. I expect 9/9 this round, and if it
# is not 9/9 the defect is mine and legible.
#
# ========= THERE IS STILL NO GOAL, AND I HAVE SAID WHY IN THE MANUAL =========
# theorem the_goal_is_absent_because_no_instance_can_name_the_socket gives
# the argument and the price: is_goal is False, plan returns
# no_goal_declared, commit never runs, and EVERY COMMAND THIS LEG IS A
# PROBE. That is now a stated position rather than a silence, and the
# ranking below is a ranking of expected information, which is the only
# currency available while the goal section is empty. The observation
# that ends it: the first colour change anywhere in the socket bracket,
# rows 49-55 cols 43-49, or its pip at (52,46).
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   Body at spawn, lattice (1,2). North and west void, south and east open.
#   Panel in configuration A. Meter: 4 cells burned, cols 60-63 of row 63.
#   At spawn:  key(2) -> 48 body cells, both rules already at full coverage
#              key(1) -> nothing, WITNESSED twice, t1 and t8
#              key(3) -> nothing, WITNESSED once, t9
#              key(4) -> UNWITNESSED HERE, and the last candidate for east
#              key(5) -> UNWITNESSED HERE, and the only test of the guard
#                        colored(spawn_probe, 5) that thirteen rules share
#   The meter is a clock, one cell per two commands, 60 cells left. Index
#   10 is EVEN and burns (63,59) whatever is pressed; that cell is board,
#   has no instance, and no rule of mine can draw it. Discount it.
#
# ========= THE ONE THING WORTH BUYING =========
# ACTION4 AT SPAWN. It is the only key never pressed from this cell whose
# answer names a direction either way. ACTION2 is down; ACTION5 carries
# the body north; ACTION1 was inert here twice and ACTION3 once, with
# east open the whole time, so neither is east; ACTION3 and ACTION4 were
# both inert one cell south where east and west are void, which is what
# the horizontal pair would do there. So east is ACTION4 or east does not
# exist. A step east means the road to the knob is open and costs 48
# undrawable pixels I have priced in the manual. No step means NO KEY IS
# EAST, movement is vertical only, and four theorems get rewritten -- a
# bigger finding than the step, bought for the same one command.
#
# SECOND: ACTION5 AT SPAWN. My manual predicts zero cells. A panel toggle
# there falsifies the spawn_probe guard on thirteen rules at once, which
# is the single observation that would most change the file; a body jump
# falsifies the up reading of ACTION5; nothing at all confirms both.
#
# ------------------------------------------------------------------------
# STATE 9: body home at lattice (1,2); panel configuration A; four meter
# cells burned; next command index 10. Eleven lattice cells reachable and
# the body has stood in two. Three steps east along lattice row 1 reach
# the cell beside the knob; the knob is the far end of one connected
# colour-8 wire whose near end is the comb; the comb gates every route to
# the socket at (8,7).

order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     treat_the_first_socket_pixel_that_moves_as_the_goal_writing_event [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one          [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     spend_the_clock_on_unwitnessed_key_cell_pairs_not_on_repeats     [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong   [proof: lean]

prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead    [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     probes_the_meter_parity_that_nine_transitions_already_settled => dead [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic rules_whose_shared_guard_a_single_command_would_falsify           [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                        [admissible: lean]

prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 2/5 keys at spawn]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 1/1 candidates left]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 2/5 keys at spawn]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 9/9 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    a_press_at_a_third_cell_that_splits_up_from_home_from_undo       [ev: 2/2 key5_presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
