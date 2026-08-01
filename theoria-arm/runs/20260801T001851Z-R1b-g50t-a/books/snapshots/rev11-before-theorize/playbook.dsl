# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= READ THIS FIRST: THE LAST FOUR COMMANDS BOUGHT NOTHING =========
# Commands 14-17 were ACTION5 at (2,2), ACTION2 at spawn, ACTION5 at
# (2,2), ACTION1 at spawn. Every one repeated a key-cell pair already at
# full coverage. Two of them were explicitly named in this file's DO NOT
# BUY list last round. Zero new mechanisms, zero new lattice cells, and
# the shuttle question that has been first on this page for three rounds
# is now MORE expensive than it was, because the body was walked back to
# spawn and reaching (2,2) costs a command before the question can even
# be asked.
#
# WHY THAT KEEPS HAPPENING, and it is not carelessness: the probe
# frontier is my manual plus ablations of it. Two ablations differ only
# where a rule FIRES. So expected-bits is maximised exactly on the
# commands my manual already explains, and is exactly 0.000 on every
# command it says nothing about -- which is every command worth buying.
# See theorem the_probe_designer_is_blind_to_the_commands_worth_buying.
# THE INSTRUMENT FOR THOSE COMMANDS IS THE RAW DIFF, which is given for
# free. My manual predicts ZERO changed cells for ACTION4 here, for
# ACTION5 here, for ACTION6 and for ACTION7, so ANY non-empty diff
# outside row 63 is a discovery and needs no frontier to read.
#
# ========= AND EVERY COMMAND FROM NOW ON WILL LOOK REFUTED =========
# Even command: the world burns the meter's leading edge, which has no
# instance yet, so nothing in the frontier can draw it -- one wrong pixel
# on row 63. Odd command with key 1, 2 or 4: my burn rule fires on the
# edge that has an instance by then, so I predict a burn that does not
# come -- one wrong pixel on row 63. That is arithmetic, not ignorance;
# the manual explains it and prices it. DISCOUNT ANY DIVERGENCE WHOSE
# CELLS ALL LIE IN ROW 63 AND READ THE REST OF THE DIFF.
#
# ========= THE ONE THING WORTH BUYING NOW =========
# THE UNTESTED HORIZONTAL KEY, ACTION4, FROM WHERE THE BODY STANDS.
# For the first time since command 2 the body is at spawn, and at spawn
# east is OPEN: rows 8-12 cols 20-24 read floor in the current frame.
# ACTION4 has been pressed twice and both times at (2,2), where east and
# west are both void and its silence means nothing. It is the last
# candidate for east among keys 1-5. One press, and it answers whichever
# way it falls:
#   If the body moves east: ACTION4 is east, the body stands in a THIRD
#   lattice cell for the first time, the maze is real and the rocker
#   reading dies, ACTION5 from that cell then separates up from home from
#   undo, and lattice row 1 runs C=2,3,4,5 to the knob at C=6.
#   If nothing moves: east belongs to key 6, key 7 or to nothing, and
#   four theorems about routes lose their footing. That is a bigger
#   finding for the same command.
# The 48 pixels a first east step would cost me are priced in advance in
# the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_defect.
# They are tuition. They must not consume a round.
#
# SECOND: ACTION5 AT SPAWN. Never pressed here in eighteen states. It is
# the untested half of the guard carried by thirteen rules, and my manual
# predicts ZERO cells for it, so the raw diff answers it outright.
# THIRD: ACTION6, then ACTION7. Never pressed anywhere in eighteen
# commands; the panel is a selector that provably selects nothing for the
# five keys already tried, so it selects for a key not yet tried.
# FOURTH: the shuttle question -- stand on (2,2), then ask the down key
# to move again. Two commands, and it decides whether five theorems are
# about a maze or about scenery.
# DO NOT BUY: the up-key at spawn (silence witnessed three times); a
# sixth down-press from spawn or a sixth up-press from (2,2) (every rule
# already at full coverage); the horizontal key at (2,2) again; any probe
# ranked because a refutation fired on it or because many rules fire.
#
# ========= THERE IS STILL NO GOAL, AND THE REASON IS REACH =========
# theorem the_goal_is_absent_because_no_instance_can_name_the_socket
# gives the argument and accepts the price: is_goal is False, plan
# returns no_goal_declared, commit never runs, EVERY COMMAND THIS LEG IS
# A PROBE. A goal becomes writable the instant any pixel of the socket
# bracket (rows 49-55, cols 43-49), its pip (52,46), or any colour-8 comb
# or wire pixel changes -- those cells become dynamic that instant and a
# count over them becomes writable and false in every earlier state.
# Nothing reachable from a two-cell corridor causes that. So: goal after
# reach, reach after the east key, east key after one press.
#
# ------------------------------------------------------------------------
# STATE 17: body at spawn, lattice (1,2), rows 8-12 cols 14-18; panel
# configuration B; eight meter cells burned (row 63, cols 56-63); 56
# unburned, so roughly 112 commands remain. Next command index 18, EVEN,
# and it burns (63,55) whatever is pressed. s17 is pixel-identical to
# s16, from which the up-key changed nothing -- so repeating that key now
# would prove hidden state, and the manual explains why that proof is not
# worth a command.

order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     rank_by_what_the_raw_diff_would_show_not_by_expected_frontier_bits [proof: lean]
order     buy_the_commands_the_frontier_scores_at_zero_because_it_is_blind_there [proof: lean]
order     treat_the_first_socket_or_comb_pixel_that_moves_as_the_goal_writing_event [proof: lean]
order     test_the_last_unlabelled_direction_key_where_that_direction_is_open [proof: lean]
order     settle_whether_down_works_off_the_spawn_ring_before_planning_routes [proof: lean]
order     discount_a_divergence_whose_cells_all_lie_in_the_meter_row      [proof: lean]
order     press_a_direction_key_only_where_that_direction_is_open         [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one         [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered   [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     spend_the_clock_on_unwitnessed_key_cell_pairs_not_on_repeats    [proof: lean]
order     try_an_action_never_pressed_before_repeating_a_settled_one      [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it              [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it      [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong  [proof: lean]

prune     ranked_only_because_many_rules_fire_on_it => dead                [proof: lean]
prune     expected_bits_computed_over_ablations_of_already_witnessed_rules => dead [proof: lean]
prune     divergence_lies_only_on_a_cell_that_has_never_changed => dead    [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead           [proof: lean]
prune     frontier_cannot_contain_the_world_so_its_bits_are_bookkeeping => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead  [proof: lean]
prune     repeats_a_key_cell_pair_whose_inertness_is_already_witnessed => dead [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead  [proof: lean]
prune     tests_a_direction_from_a_cell_where_that_direction_is_void => dead [proof: lean]
prune     probes_the_meter_parity_that_seventeen_transitions_settled => dead [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead             [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead      [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead   [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                [proof: lean]
prune     destination_centre_holds_machinery_so_the_body_cannot_stand => dead [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead   [proof: lean]
prune     meter_exhausted and not goal => dead                             [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                   [admissible: lean]
heuristic actions_never_pressed_anywhere_in_the_store                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination             [admissible: lean]
heuristic theorems_a_single_press_would_promote_or_demolish               [admissible: lean]
heuristic rules_whose_shared_guard_a_single_command_would_falsify         [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                    [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_row                  [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                       [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut             [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open            [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                      [admissible: lean]

prefer    the_untested_horizontal_key_where_that_direction_is_finally_open [ev: 1/1 candidates left]
prefer    a_command_the_frontier_scores_at_zero_but_the_diff_can_read      [ev: 3/3 vacuous probes]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 4/7 keys at this cell]
prefer    stepping_into_a_lattice_cell_the_body_has_never_occupied         [ev: 2/11 cells visited]
prefer    the_press_that_decides_whether_this_world_is_a_maze_or_a_rocker  [ev: 5/23 theorems hostage]
prefer    an_action_pressed_zero_times_over_one_pressed_five_times         [ev: 2/7 actions unpressed]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 17/17 diffs]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 1/1 candidates left]
prefer    a_press_at_a_third_cell_that_splits_up_from_home_from_undo       [ev: 5/5 up_presses]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
