# playbook.dsl -- what to buy with the next command, not a route.
#
# ===== THIS ROUND SPENT ZERO COMMANDS =====
# The store still reads 22 states and 21 transitions, the same keys, the
# same ten burns. Nothing was bought and nothing was learned from the
# world. The surprise that called the theorize desk was a REPLAY
# divergence -- one pixel, (63,57), ACTION4, transition index 12 -- which
# the manual named, dated and priced three rounds before it fired, and
# which last round's written prediction reproduced number for number
# together with 16/21, 0 unexplained cells and 0 clashes over 110 pairs.
# A round in which certify confirms the manual's own advance prediction
# in every field is a round in which the manual should not be edited and
# a command should be pressed instead.
#
# ===== WHAT THE ROUND DID PRODUCE: THE BURN-SUBSET TABLE =====
# The one honest gain was arithmetic. All eight subsets of the burn keys
# were hand-simulated under cumulative replay:
#   {1,2,4} = 16/21  <- what the manual has
#   {2,4}   =  9/21
#   {1,2}   =  3/21     {2} = 3/21
#   any set without key2 = 1/21   (the edge rule is key2-only)
#   adding key3 =  2/21
# The rule the surprise complains about buys eleven of the sixteen
# matches. Deleting it to remove one premature burn costs seven
# transitions, because a premature burn heals and an omission never does.
# CONSEQUENCE FOR THIS PAGE: a replay divergence in row 63 is not a
# ticket to edit the burn rules; the optimum is already occupied, and it
# is now occupied with a table rather than a hunch.
#
# ===== THE ONE THING WORTH BUYING, SECOND ROUND RUNNING =====
# THE DOWN KEY, FROM THE CELL IT HAS NEVER BEEN PRESSED IN.
# ACTION2 has been pressed seven times and all seven were from spawn.
# THE BODY IS AT LATTICE (2,2) RIGHT NOW and south of it is clear floor
# (rows 20-24, cols 13-31 read 5; separator row 19 reads 5 across).
#   If the body moves south: it stands in a THIRD lattice cell for the
#   first time, the rocker reading dies, the maze is real, five theorems
#   are promoted at once, and the up-key can then be split into
#   up/home/undo from that cell.
#   If nothing moves: the down key is a shuttle, the lattice and the comb
#   and the socket are scenery, and five theorems fall. Bigger finding,
#   same command.
# THE PRICE, STATED BEFORE SPENDING IT: 48 pixels I cannot draw -- 24
# departure, 24 arrival on board cells -- and a missed move never heals,
# so it poisons replay until the rules are written next round. One round
# of tuition. Buy it anyway; the replay score is bookkeeping and a
# direction label is physics. The departure half was NOT pre-written: no
# witness either way, it saves 24 pixels if the world is a maze and
# invents 24 wrong ones if it is a rocker, and only the second kind never
# heals.
#
# SECOND: the up key from this same cell, never pressed here, north
# open. It splits the two candidate up-keys; predicted zero, so the raw
# diff answers it outright.
# THIRD: the two actions never pressed anywhere in twenty-two commands.
# FOURTH: the horizontal key at spawn, where east is finally open -- but
# it costs a trip home first, so it drops behind the two presses
# available from where the body stands.
# DO NOT BUY: the up key from here or the down key from spawn, both
# settled to the pixel; either horizontal key from here, where both
# horizontal directions are void; anything ranked because many rules fire
# on it or because a refutation fired on it.
#
# ===== THE PROBE DESIGNER IS BLIND BY CONSTRUCTION =====
# It ranks by expected bits over a frontier of ablations, and two
# ablations differ only where a rule FIRES, so it is guaranteed to rank
# the commands this manual already explains and to score at exactly zero
# every command that could teach it something. Last time commands were
# spent, four were bought, every one of them named by a prune line here,
# expected 0.544 + 0.918 + 0.544 bits, realised 0.0 three times over.
# AND A VACUOUS FRONTIER IS A METER READING: the meter burns a cell of
# row 63 that has never changed, that cell is board, board renders its
# frame-0 colour in EVERY hypothesis, so the whole frontier dies together
# on one pixel that no rule edit could save. This recurs on EVERY EVEN
# COMMAND. THE TEST THAT SEPARATES IT FROM A REAL GAP: do the divergent
# cells lie only in row 63? The probe report gives hashes and not cells,
# so printing the divergent cells remains the cheapest instrument upgrade
# available to this arm; until it exists, the raw diff is the instrument.
#
# ===== THERE IS STILL NO GOAL, AND THE PRICE IS MEASURED =====
# is_goal is False, plan returns no_goal_declared, commit has never run,
# all twenty-two commands have been probes, roughly 108 remain on the
# meter. The manual cannot name the socket because every cell of it has
# never changed and is therefore board. A goal writable today is one a
# planner could satisfy with a single press, which would hand the level
# to a fake win. Goal after reach, reach after the gate, gate after the
# maze is proven to be a maze, and that proof is one press away.
#
# ---------------------------------------------------------------------
# STATE 21, unchanged: body at lattice (2,2), rows 14-18 cols 14-18;
# spawn ring empty; panel configuration A; ten meter cells burned at row
# 63 cols 54-63; 54 unburned. Next command index 22, EVEN, and it burns
# (63,53) whatever is pressed -- a board cell, so it refutes every
# hypothesis in every frontier.

order     press_a_command_when_certify_reproduces_the_manuals_own_prediction [proof: lean]
order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     read_a_vacuous_frontier_as_a_board_cell_before_calling_it_a_missing_mechanism [proof: lean]
order     ask_for_the_divergent_cells_of_a_refutation_and_not_only_its_hash [proof: lean]
order     rank_by_what_the_raw_diff_would_show_not_by_expected_frontier_bits [proof: lean]
order     buy_the_commands_the_frontier_scores_at_zero_because_it_is_blind_there [proof: lean]
order     test_the_down_key_from_the_cell_it_has_never_been_pressed_in   [proof: lean]
order     spend_the_press_that_is_available_from_where_the_body_stands   [proof: lean]
order     price_a_missed_change_higher_than_a_premature_one_because_only_one_heals [proof: lean]
order     enumerate_every_variant_of_a_rule_set_before_deleting_the_one_that_misfired [proof: lean]
order     separate_the_replay_scoreboard_from_the_live_prediction_scoreboard [proof: lean]
order     recompute_a_refusal_when_the_replay_model_changes_under_it     [proof: lean]
order     treat_the_first_socket_or_comb_pixel_that_moves_as_the_goal_writing_event [proof: lean]
order     settle_whether_down_works_off_the_spawn_ring_before_planning_routes [proof: lean]
order     discount_a_divergence_whose_cells_all_lie_in_the_meter_row     [proof: lean]
order     press_a_direction_key_only_where_that_direction_is_open        [proof: lean]
order     prefer_a_press_that_answers_two_open_questions_over_one        [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered  [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     spend_the_clock_on_unwitnessed_key_cell_pairs_not_on_repeats   [proof: lean]
order     try_an_action_never_pressed_before_repeating_a_settled_one     [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it             [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it     [proof: lean]
order     read_an_empty_certify_block_as_nothing_known_not_nothing_wrong [proof: lean]

prune     burn_rule_edit_that_scores_below_sixteen_of_twenty_one_in_replay => dead [proof: lean]
prune     deleting_a_rule_that_misfires_once_and_fires_correctly_more_often => dead [proof: lean]
prune     vacuous_streak_whose_refuting_cells_all_lie_in_the_meter_row => dead [proof: lean]
prune     hypothesis_that_differs_from_its_siblings_only_by_a_board_cell => dead [proof: lean]
prune     divergence_that_the_next_burn_command_repairs_by_itself => dead [proof: lean]
prune     ranked_only_because_many_rules_fire_on_it => dead              [proof: lean]
prune     expected_bits_computed_over_ablations_of_already_witnessed_rules => dead [proof: lean]
prune     divergence_lies_only_on_a_cell_that_has_never_changed => dead  [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead         [proof: lean]
prune     frontier_cannot_contain_the_world_so_its_bits_are_bookkeeping => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead [proof: lean]
prune     repeats_a_key_cell_pair_whose_inertness_is_already_witnessed => dead [proof: lean]
prune     repeats_a_key_cell_pair_whose_effect_is_already_witnessed => dead [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead [proof: lean]
prune     tests_a_direction_from_a_cell_where_that_direction_is_void => dead [proof: lean]
prune     probes_the_meter_parity_that_twenty_one_transitions_settled => dead [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead           [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead    [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead              [proof: lean]
prune     destination_centre_holds_machinery_so_the_body_cannot_stand => dead [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead [proof: lean]
prune     goal_a_planner_could_satisfy_with_a_single_press => dead       [proof: lean]
prune     meter_exhausted and not goal => dead                           [proof: lean]

heuristic key_cell_pairs_whose_inertness_here_rests_on_no_witness        [admissible: lean]
heuristic actions_never_pressed_anywhere_in_the_store                    [admissible: lean]
heuristic presses_available_without_first_moving_the_body                [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination            [admissible: lean]
heuristic theorems_a_single_press_would_promote_or_demolish              [admissible: lean]
heuristic rules_whose_shared_guard_a_single_command_would_falsify        [admissible: lean]
heuristic live_readings_a_single_command_can_eliminate                   [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_row                 [admissible: lean]
heuristic divergences_that_will_not_heal_without_a_new_rule              [admissible: lean]
heuristic replay_transitions_a_rule_set_variant_would_gain_or_lose       [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                      [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut            [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open           [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                     [admissible: lean]

prefer    the_down_key_from_the_only_other_cell_the_body_has_ever_occupied [ev: 7/7 presses from one cell]
prefer    the_press_that_decides_whether_this_world_is_a_maze_or_a_rocker  [ev: 5/27 theorems hostage]
prefer    a_command_the_frontier_scores_at_zero_but_the_diff_can_read      [ev: 3/3 vacuous probes]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 3/7 keys at this cell]
prefer    stepping_into_a_lattice_cell_the_body_has_never_occupied         [ev: 2/11 cells visited]
prefer    an_action_pressed_zero_times_over_one_pressed_seven_times        [ev: 2/7 actions unpressed]
prefer    a_press_available_from_here_over_one_that_needs_a_trip_first     [ev: 2/4 ranked probes]
prefer    a_press_that_would_split_two_keys_that_share_a_direction_label   [ev: 6/6 up_presses]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 21/21 diffs]
prefer    leaving_the_manual_untouched_when_its_advance_prediction_held    [ev: 8/8 certify fields]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
