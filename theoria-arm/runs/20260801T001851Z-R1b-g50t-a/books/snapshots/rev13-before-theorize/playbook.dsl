# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHAT CHANGED: THE REPLAY MODEL, NOT THE WORLD =========
# No command was executed this round. Certify came back 15/17 where the
# manual predicted 13/17, and the two-transition gap proved that replay
# is CUMULATIVE: each transition is replayed from the manual's own
# previous predicted frame, never resynchronised to the observation.
# Two consequences run this page now.
#
#   A PREMATURE CHANGE HEALS. The manual burned (63,57) one command
#   early at t13; the world burned it at t14; the frames matched again
#   and t14 counted as a match. Same story at t15/t16.
#   AN OMITTED CHANGE NEVER HEALS. Nothing in the manual puts back what
#   it failed to draw, so a missed burn -- or a missed BODY STEP --
#   poisons every later transition until a rule is written for it.
#
# That asymmetry re-priced three refusals (delete the burn rules: ~1/17,
# not 9/17; a guarded key5 burn rule: 14/17; a panel guard on the key4
# burn rule: 13/17, not the 14/17 I claimed). All three refusals stand.
# The rule set is unchanged and is the best of the four.
#
# ========= AND THE ROW-63 ERROR IS NOT PERMANENT AFTER ALL =========
# I previously wrote that every command from here refutes the manual at
# row 63. That was computed under the wrong replay model and is FALSE.
# The corrected shape: the world burns on EVEN commands; the manual
# burns whenever key 1, 2 or 4 is pressed on an edge that has an
# instance. So an even command with a burn key MATCHES, an odd command
# with a burn key is one pixel early and heals next command, an even
# command with key 3 or 5 is one pixel short and heals at the next burn
# key. At most one pixel of error at any time.
# STILL DISCOUNT A DIVERGENCE WHOSE CELLS ALL LIE IN ROW 63 -- but read
# it now as a phase, not as a wound.
#
# ========= THE ONE THING WORTH BUYING NOW =========
# THE UNTESTED HORIZONTAL KEY, FROM WHERE THE BODY STANDS.
# The body is at spawn and east is OPEN: rows 8-12 are floor from col 19
# to col 43, so the destination ring at cols 20-24 is clear. That key has
# been pressed twice and both times at (2,2), where east and west are
# both void and its silence means nothing. It is the last candidate for
# east among the five keys tried. One press answers it whichever way it
# falls:
#   If the body moves east: it stands in a THIRD lattice cell for the
#   first time, the rocker reading dies, the up-key can then be split
#   into up/home/undo from that cell, and lattice row 1 runs toward the
#   knob.
#   If nothing moves: east belongs to an untried key or to nothing, and
#   four theorems about routes lose their footing. Bigger finding, same
#   command.
# THE PRICE WENT UP AND I STATE IT: a body step my manual cannot draw
# does NOT heal. 48 wrong pixels immediately and on every later
# transition until the east rules are written -- and they become
# writable next round, because the arrival cells acquire instances the
# instant they change. One round of tuition. Buy it anyway; the replay
# score is bookkeeping and the direction label is physics.
# BONUS, AND ONLY AS A TIEBREAKER: command 18 is even, so a burn key
# pressed now also keeps the meter phase in step and costs nothing.
#
# SECOND: the up-key at spawn. Never pressed here in eighteen states. It
# is the untested half of the guard carried by thirteen rules, and the
# manual predicts ZERO cells for it, so the raw diff answers it outright.
# THIRD: the two actions never pressed anywhere; the panel is a selector
# that provably selects nothing for the five keys already tried.
# FOURTH: the shuttle question -- stand one cell south, then ask the
# down key to move again. Two commands, and it decides whether five
# theorems are about a maze or about scenery.
# DO NOT BUY: the key whose silence at spawn is witnessed three times; a
# sixth down-press from spawn or a sixth up-press from the cell south of
# it; the horizontal key where that direction is void; any probe ranked
# because a refutation fired on it or because many rules fire.
#
# ========= THE PROBE FRONTIER IS STILL BLIND WHERE IT MATTERS =========
# Every hypothesis in the frontier is the manual or an ablation of it,
# and two ablations differ only where a rule FIRES. So expected-bits is
# maximised on the commands already explained and is exactly 0.000 on
# every command worth buying. THE INSTRUMENT FOR THOSE COMMANDS IS THE
# RAW DIFF, given for free. The manual predicts ZERO changed cells
# outside row 63 for the horizontal key here, the up key here, and both
# untried keys -- so ANY non-empty diff outside row 63 is a discovery.
#
# ========= THERE IS STILL NO GOAL, AND THE REASON IS REACH =========
# is_goal is False, plan returns no_goal_declared, commit never runs,
# EVERY COMMAND THIS LEG IS A PROBE. A goal becomes writable the instant
# any pixel of the socket bracket (rows 49-55, cols 43-49), its pip
# (52,46), or any colour-8 comb or wire pixel changes. Nothing reachable
# from a two-cell corridor causes that. Goal after reach, reach after the
# east key, east key after one press.
#
# ------------------------------------------------------------------------
# STATE 17: body at spawn, lattice (1,2), rows 8-12 cols 14-18; panel
# configuration B; eight meter cells burned (row 63, cols 56-63); 56
# unburned, so roughly 112 commands remain. Next command index 18, EVEN,
# and it burns (63,55) whatever is pressed.

order     say_out_loud_that_every_command_is_a_probe_while_is_goal_is_false [proof: lean]
order     rank_by_what_the_raw_diff_would_show_not_by_expected_frontier_bits [proof: lean]
order     buy_the_commands_the_frontier_scores_at_zero_because_it_is_blind_there [proof: lean]
order     price_a_missed_change_higher_than_a_premature_one_because_only_one_heals [proof: lean]
order     recompute_a_refusal_when_the_replay_model_changes_under_it   [proof: lean]
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

prune     divergence_that_the_next_burn_command_repairs_by_itself => dead  [proof: lean]
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
heuristic divergences_that_will_not_heal_without_a_new_rule               [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                       [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut             [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open            [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                      [admissible: lean]

prefer    the_untested_horizontal_key_where_that_direction_is_finally_open [ev: 1/1 candidates left]
prefer    a_command_the_frontier_scores_at_zero_but_the_diff_can_read      [ev: 3/3 vacuous probes]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 4/7 keys at this cell]
prefer    stepping_into_a_lattice_cell_the_body_has_never_occupied         [ev: 2/11 cells visited]
prefer    the_press_that_decides_whether_this_world_is_a_maze_or_a_rocker  [ev: 5/24 theorems hostage]
prefer    an_action_pressed_zero_times_over_one_pressed_five_times         [ev: 2/7 actions unpressed]
prefer    a_press_that_tests_the_guard_shared_by_thirteen_rules            [ev: 13/22 rules]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 17/17 diffs]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 1/1 candidates left]
prefer    a_press_at_a_third_cell_that_splits_up_from_home_from_undo       [ev: 5/5 up_presses]
prefer    a_burn_key_on_an_even_command_when_information_is_otherwise_tied [ev: 2/2 healed pairs]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
