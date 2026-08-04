# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# THE EPISODE RESTARTED. Seven states, six transitions:
#   RESET, A1, A2, A3, A4, A5, A5.
# BODY AT SPAWN, lattice (1,2). PANEL IN CONFIGURATION B. THREE meter cells
# burned, columns 61-63; 61 remain. NEXT COMMAND INDEX IS 7, WHICH IS ODD.
# Same level as the 26-state episode -- same knob, comb, socket, pixel for
# pixel -- but the log and the meter both restarted.
#
# ========= I WAS REFUTED, AND IT PAID =========
# Last round I deleted colored(spawn_probe,5) -- "body not at home" -- from
# thirteen panel rules, and I wrote the falsifier in advance in this book:
#   "(b) nothing changes -> the guard was real; I am refuted by 23 cells and
#    put it back."
# t6 IS THAT PRESS. ACTION5 at spawn changed ONE cell and it was not a panel
# cell. THE GUARD IS RESTORED. I am not sorry I spent the command: an
# unwitnessed conjunct is a HYPOTHESIS, deleting it was the cheapest possible
# test, and one press settled it. The procedure was right; the belief was
# wrong. That is the good case, and the general rule survives with a rider:
#   DELETING AN UNWITNESSED CONJUNCT IS AN EXPERIMENT, NOT A CORRECTION.
#   PRICE IT AS ONE AND REVERT IT THE MOMENT IT LOSES.
#
# ========= AND THE SAME PRESS BOUGHT THE BIG ONE =========
# t6 IS ACTION5 AND IT BURNED A METER CELL.
#   READING A -- "burn iff the key is 2 or 4" -- IS DEAD.
#   READING B -- "burn iff the command index is even" -- is 6/6 here and was
#   25/25 before the reset. THE METER IS A TWO-COMMAND TIMER.
# Six rounds of loop could never split these, because the loop pinned
# key-2-ness and even-ness to the same predicate. One press of key 5 at an
# even index split them. This is the first new fact about the world in six
# rounds and it came from the probe this book ranked first.
#
# ========= WHAT THE TIMER DOES TO EVERY RANKING =========
# THERE IS NO FREE PROBE ANY MORE. Every command costs half a meter cell,
# including the ones that change nothing -- t1 and t3 changed nothing and
# were charged. The line "prefer a free probe over one that costs a meter
# cell" is DELETED from this book; it was true only under a reading the world
# has now killed. The only criterion left is INFORMATION PER COMMAND, and a
# command whose answer is already known is now a strict loss, not a wash.
# 61 cells remain = about 122 commands. RESET refills them (12 burned cells
# came back at the restart), so a reset is cheap on this board -- it costs
# only position, and position has never been more than two lattice cells.
#
# ========= THE LOOP IS FORCED AGAIN AND I SAY SO =========
# With the guard back: at spawn only key 2 has a live rule; at lattice (2,2)
# only key 5 does. The ranker scores expected bits over {manual, ablations,
# inert}; an ablation only ever predicts FEWER changes; so wherever the manual
# predicts IDENTITY every hypothesis agrees and the gain is ZERO. The
# two-command cycle is therefore forced exactly as before.
# I looked for a second lever. THERE IS NONE I CAN TAKE HONESTLY: keys 3, 4,
# 6 and 7 have no rule to un-guard, and the one remaining guarded silence
# (key3's spawn_probe conjunct) guards a rule that recolours a pixel to the
# colour it already has, so removing it changes no successor and buys no bits.
# I am not going to invent a rule to break the loop. I said last round that
# adding an unwitnessed RULE is fabrication; the fact that my legitimate
# deletion lost does not make the fabrication legitimate.
#
# ========= BUT THE FORCED COMMAND IS INFORMATIVE THIS TIME =========
# INDEX 7 IS ODD. Under the timer NOTHING burns next, whatever is pressed.
# Under any surviving key-based reading, ACTION2 burns (63,60).
# So the command the ranker will take anyway -- ACTION2 at spawn -- is for
# once a real experiment, readable in the raw diff:
#   48 cells changed -> timer confirmed at an odd index.
#   49 cells changed with (63,60) burned -> timer dead, burn is keyed.
# That is the first time in six rounds that the forced move is worth its cost.
#
# ========= heuristic_miss, ANSWERED FOR THE EIGHTH TIME =========
# Declaring a goal is NOT the highest-value edit, for an arithmetic reason:
#   THE PLAN TIER REACHES A GOAL BY SEARCHING MY COMPILED RULES, AND MY RULES
#   REACH EXACTLY FOUR STATES: TWO LATTICE CELLS BY TWO PANEL CONFIGURATIONS.
# So the only goal that could return sat is one satisfied inside the loop, and
# sat-inside-the-loop is WORSE than unsat: unsat leaves the arm probing, sat
# makes it commit and declare success one lattice cell from spawn. Re-checked
# with this episode's counts: count(Glyph9,color=5)=24 and
# count(Vacated,color=9)=24 both mean only "body is off spawn";
# count(Dark,color=9)=3 means only "panel is in configuration B";
# count(Glyph9,color=1)=64 exceeds the 38 instances that exist and =38 is
# unreachable by any rule; count(Spent)=0 is constant-false.
#   THE GOAL IS NOT THE BOTTLENECK. THE MISSING TRANSITION IS.
#   ONE OBSERVATION FIXES BOTH: THE BODY IN A THIRD LATTICE CELL.
#
# THE WIN, carried in prose because the DSL cannot hold it:
#   WIN = the body stands in lattice (8,7), rows 50-54 columns 44-48, so its
#   24 ring pixels render 9 and its aperture shows the pip at (52,46). Drawn
#   as three colour-9 walls with the west side open: a socket cut to the body.
#   ROUTE = lattice column 2 is the only north-south corridor and the comb at
#   (6,2) blocks it, 23 of its 25 pixels colour 8. The comb is wired by one
#   connected colour-8 line to a 3x3 knob at lattice (1,6), reachable
#   eastward along R=1 from spawn through (1,3), (1,4), (1,5), all open floor.
#   THE EAST KEY IS STILL UNNAMED AFTER THIRTY-ONE COMMANDS.
#
# ========= THE RANKED LIST =========
# 1. ACTION3 AT SPAWN. The east key, tested where east is OPEN. A2 is south
#    (12 witnesses). A1 was pressed AT SPAWN with east open and moved nothing,
#    so A1 is not east. EAST IS A3 OR A4, no third candidate. Both were
#    pressed exactly once, from one cell south where east AND west are void,
#    so neither press could answer anything. This is step one of the only
#    route to the only switch on the board. STILL PRICED AT ZERO by the
#    ranker, and there is no conjunct to delete that would change that; I say
#    so rather than pretending otherwise.
# 2. ACTION2 AT SPAWN. Forced by the ranker, and this time worth it: at an ODD
#    index it splits the timer reading from every key-based reading, in the
#    raw diff, at the same half-cell every command costs.
# 3. ACTION2 PRESSED ONE CELL SOUTH OF SPAWN. Manual predicts NOTHING -- no
#    Glyph9 renders 9 there, no Vacated renders 5 -- and that is almost
#    certainly false: rows 20-24 are floor from column 13 to 31 and one A2
#    press has moved the body one lattice cell south twelve times running.
#    The one command likeliest to seat the body in a cell never occupied,
#    which is the observation that makes a goal writable. Not buyable with a
#    fabricated rule.
# 4. ACTION5 AT SPAWN AT AN ODD INDEX. Splits my written proxy guard
#    (position) from the timer (parity): the proxy says (63,60) burns, the
#    timer says nothing does. Cheap, but it settles bookkeeping rather than
#    the level.
# 5. ACTION6 OR ACTION7. Never pressed, entirely unconstrained. In this family
#    one is usually a click, and the knob is a 3x3 target the body appears
#    unable to stand on. My manual could record such a command's EFFECT and
#    never its precondition -- but the effect is what turns comb pixels
#    dynamic and makes a goal line writable. Honest risk: actions_used lists
#    only what has been tried, so it is no evidence these exist.
#
# ========= WHAT NOT TO PRESS =========
#   A5 from one cell south: pure loop. It re-witnesses the five reverse panel
#   rules, which is worth something, and nothing else.
#   A1 at spawn: witnessed inert at t1.
#   A4 at spawn: the same experiment as A3 with the labels swapped; press it
#   only if A3 is inert. It no longer costs more than A3 -- under the timer
#   nothing costs more than anything.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The next burn cell (63,60) is undrawable: no instance sits on a cell
#     that has never changed. A refutation whose divergence set is exactly
#     that cell implicates nothing.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on cells that have never changed, and 24 departure pixels for
#     which no rule in that direction is witnessed. 24 for the second step in
#     the same direction, 0 after that.
#   * The five reverse panel rules have NO witness in this episode and carry
#     pre-reset evidence. If the panel fails to flip back on the next ACTION5
#     from lattice (2,2), that is 23 cells against me and they come out.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.

order     revert_an_edit_in_the_round_the_world_refutes_it                  [proof: lean]
order     treat_deleting_an_unwitnessed_conjunct_as_an_experiment_to_price  [proof: lean]
order     distinguish_deleting_a_restriction_from_inventing_a_rule          [proof: lean]
order     rank_by_information_per_command_now_that_no_command_is_free       [proof: lean]
order     read_the_burn_answer_off_the_raw_diff_not_off_a_refutation        [proof: lean]
order     confirm_a_timer_reading_at_an_odd_index_while_the_window_is_open  [proof: lean]
order     score_an_unwitnessed_silence_above_a_witnessed_repetition         [proof: lean]
order     treat_an_action_the_manual_calls_silent_as_unprobeable_not_untested [proof: lean]
order     settle_the_east_key_before_anything_else_at_this_cell             [proof: lean]
order     buy_a_third_lattice_cell_before_attempting_to_write_a_goal        [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     extend_the_transition_model_before_extending_the_goal_language    [proof: lean]
order     treat_a_repeated_identical_information_gain_as_zero_gain          [proof: lean]
order     discount_any_gain_that_comes_from_a_cell_with_no_instance         [proof: lean]
order     prefer_a_command_that_closes_three_open_questions_over_one        [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it  [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves   [proof: lean]
order     break_a_repeating_command_cycle_before_optimising_within_it       [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     recite_every_rule_against_the_log_that_actually_exists            [proof: lean]
order     label_a_proxy_guard_as_a_proxy_wherever_the_true_law_is_unsayable [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal      [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it    [proof: lean]
order     reaudit_ambiguity_by_hand_after_any_guard_restoration             [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     action_whose_expected_bits_are_zero_only_because_the_manual_is_silent => keep [proof: lean]
prune     rule_proposed_with_zero_witnesses_of_any_kind => dead                  [proof: lean]
prune     guard_conjunct_the_world_has_since_witnessed_negatively => keep        [proof: lean]
prune     goal_clause_over_a_type_with_zero_instances => dead                    [proof: lean]
prune     goal_that_becomes_true_at_a_state_that_is_not_a_win => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_cells_already_visited => dead [proof: lean]
prune     divergence_lies_only_on_the_unburned_meter_frontier => dead            [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead          [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key => dead   [proof: lean]
prune     ranking_that_still_assumes_a_key_free_of_meter_cost => dead            [proof: lean]
prune     repeats_the_two_command_cycle_that_returns_the_body_to_spawn => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead        [proof: lean]
prune     no_rule_it_could_witness_can_still_ground_in_this_census => dead       [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead        [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                   [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead        [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead            [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                      [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead         [proof: lean]
prune     tests_a_direction_at_a_cell_where_that_direction_is_void => dead       [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead         [proof: lean]
prune     meter_exhausted and not goal => dead                                   [proof: lean]

heuristic silences_of_the_manual_that_rest_on_no_witness                    [admissible: lean]
heuristic actions_priced_at_zero_expected_bits_by_the_manuals_own_silence   [admissible: lean]
heuristic distinct_legible_outcomes_a_single_command_can_produce            [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic rules_carrying_only_pre_reset_evidence_a_command_would_rewitness  [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic meter_cells_remaining_as_a_uniform_budget_on_every_command        [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]

prefer    a_command_that_splits_the_timer_reading_from_a_key_based_one     [ev: 1/6 transitions split them]
prefer    a_command_at_an_odd_index_while_the_timer_reading_is_testable    [ev: 3/3 odd indices agree]
prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 2/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 2/5 keys at spawn]
prefer    a_command_that_would_put_the_body_in_a_lattice_cell_never_occupied [ev: 2/11 reachable cells seen]
prefer    a_command_that_would_turn_a_machinery_pixel_dynamic              [ev: 0/7 states]
prefer    a_command_that_leaves_the_cycle_the_manual_forces                [ev: 2/6 transitions]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 6/6 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
prefer    a_reset_over_a_stall_once_the_timer_is_nearly_spent              [ev: 1/1 resets refilled it]
