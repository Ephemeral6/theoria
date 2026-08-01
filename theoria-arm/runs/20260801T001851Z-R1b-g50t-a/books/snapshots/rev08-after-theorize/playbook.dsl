# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Fourteen states, thirteen transitions, and the manual lands on the
# current frame at every one of the 77 dynamic cells. Three probes came
# back vacuous and NONE of them found a missing mechanism; they found the
# meter's leading edge, which no hypothesis in the frontier can draw. The
# manual says why in the_frontier_is_vacuous_by_construction_at_even_
# indices, and the practical consequence belongs here: HALF OF ALL
# COMMANDS ARE EVEN AND EVERY ONE OF THEM WILL REPORT 0 BITS. Read the
# raw diff, which is given for every command regardless, and stop reading
# the frontier's bits as a verdict on the manual.
#
# ========= WHAT THIRTEEN COMMANDS BOUGHT, AND WHAT THEY DID NOT =========
# Bought: ACTION2 south from spawn (x4), ACTION5 north from (2,2) (x3),
# the two-command clock (6/6 and 7/7), the panel's two configurations in
# both directions, and a state model that predicted distinct_states = 10
# before the store said 10.
# Not bought: the body has occupied TWO lattice cells out of eleven, and
# it has occupied them since command 2. ACTION4 was finally pressed at
# t13 -- at (2,2), the one cell where east and west are both void, so its
# silence there means nothing. Two of seven actions have never been
# pressed at all.
#
# ========= THERE IS STILL NO GOAL, AND THE REASON IS REACH =========
# theorem the_goal_is_absent_because_no_instance_can_name_the_socket
# gives the argument and the price: is_goal is False, plan returns
# no_goal_declared, commit never runs, EVERY COMMAND THIS LEG IS A PROBE.
# The reason is not vocabulary and not shyness. A goal becomes writable
# the instant any pixel of the socket bracket (rows 49-55, cols 43-49) or
# its pip (52,46) changes colour, because those cells become dynamic that
# instant. Nothing the body can do inside a two-cell corridor causes
# that. So the goal is downstream of movement, and movement is downstream
# of one unasked question.
#
# ========= THE ONE THING WORTH BUYING =========
# ACTION2 FROM WHERE THE BODY STANDS NOW, lattice (2,2), rows 14-18.
# ACTION2 has been pressed four times and every one was from spawn.
# ACTION5 has been pressed three times and every one was from (2,2). So
# the entire movement record is consistent with a TWO-CELL ROCKER -- go
# to cell two, go back to cell one -- in which the lattice, the comb and
# the socket are scenery. One press decides it. Destination (3,2), rows
# 20-24 cols 14-18, reads floor in the current frame and separator row 19
# is floor across cols 13-31, so the ring is clear.
#   If the body moves: the maze is real, the body stands in a THIRD cell
#   for the first time, east is OPEN there (cols 20-24 read floor) so the
#   east key can finally be tested next command, and ACTION5 from a third
#   cell separates up from home from undo. One press, three questions.
#   If it does not move: this is a rocker, five theorems are scenery, and
#   that is a bigger finding bought for the same command.
# My manual predicts ZERO cells for this press and has no witness for
# that silence. The 48 pixels it will cost if the body moves are priced
# in the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_
# defect; they are tuition and they must not consume a round.
#
# SECOND: ACTION4 from any cell where east is open -- spawn or (3,2),
# never (2,2). It is the last candidate for east and its answer names a
# direction whichever way it falls.
# THIRD: ACTION6, then ACTION7. Never pressed, predicted zero, so any
# change is legible; and the panel is a selector that provably selects
# nothing for the five keys already tried.
# DO NOT BUY: ACTION4 at (2,2) again (witnessed inert twice); a fifth
# ACTION2 from spawn or a fourth ACTION5 from (2,2) (every rule already
# at full coverage); any probe ranked because a refutation fired on it.
#
# ------------------------------------------------------------------------
# STATE 13: body at lattice (2,2); panel configuration B; six meter cells
# burned (row 63, cols 58-63); next command index 14, which is EVEN and
# burns (63,57) whatever is pressed. s13 is pixel-identical to s12, from
# which ACTION4 changed nothing -- so ACTION4 now would prove hidden
# state, and the manual explains why that proof is not worth a command.

order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     treat_the_first_socket_pixel_that_moves_as_the_goal_writing_event [proof: lean]
order     settle_whether_down_works_off_the_spawn_ring_before_anything_else [proof: lean]
order     read_the_raw_diff_rather_than_the_frontier_bits_when_a_burn_is_due [proof: lean]
order     press_a_direction_key_only_where_that_direction_is_open           [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one           [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered     [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     spend_the_clock_on_unwitnessed_key_cell_pairs_not_on_repeats      [proof: lean]
order     try_an_action_never_pressed_before_repeating_a_settled_one        [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong    [proof: lean]

prune     divergence_lies_only_on_a_cell_that_has_never_changed => dead      [proof: lean]
prune     frontier_cannot_contain_the_world_so_its_bits_are_bookkeeping => dead [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead    [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead    [proof: lean]
prune     repeats_a_key_cell_pair_whose_inertness_is_already_witnessed => dead [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead    [proof: lean]
prune     tests_a_direction_from_a_cell_where_that_direction_is_void => dead [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead             [proof: lean]
prune     probes_the_meter_parity_that_thirteen_transitions_settled => dead  [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead               [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead        [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                  [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead     [proof: lean]
prune     meter_exhausted and not goal => dead                               [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic actions_never_pressed_anywhere_in_the_store                       [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic theorems_a_single_press_would_promote_or_demolish                 [admissible: lean]
heuristic rules_whose_shared_guard_a_single_command_would_falsify           [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                   [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                        [admissible: lean]

prefer    the_press_that_decides_whether_this_world_is_a_maze_or_a_rocker  [ev: 5/22 theorems hostage]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 4/7 keys at this cell]
prefer    stepping_into_a_lattice_cell_the_body_has_never_occupied         [ev: 2/11 cells visited]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 1/1 candidates left]
prefer    an_action_pressed_zero_times_over_one_pressed_four_times         [ev: 2/7 actions unpressed]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 13/13 diffs]
prefer    east_along_a_lattice_row_over_any_other_axis_once_south_is_known [ev: 1/1 levels]
prefer    a_press_at_a_third_cell_that_splits_up_from_home_from_undo       [ev: 3/3 key5_presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
