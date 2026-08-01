# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Eighteen states, seventeen transitions:
#   RESET, A1 A2 A3 A4 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5 A2 A5.
#   t1  A1 at spawn        -> nothing
#   t2  A2 at spawn        -> body one lattice cell SOUTH (48) + burn (63,63)
#   t3  A3 one cell south  -> nothing (east and west both void there)
#   t4  A4 one cell south  -> burn (63,62) and nothing else
#   t5  A5 one cell south  -> body to spawn (48) + panel A->B (23)
#   t6..t17  the same two commands, six more times, alternating.
#   Burns since: (63,61) (63,60) (63,59) (63,58) (63,57) (63,56).
# BODY AT SPAWN, lattice (1,2). PANEL IN CONFIGURATION B. EIGHT meter cells
# burned, columns 56-63; 56 remain. Next command index is 18, EVEN.
#
# ========= WHAT HAPPENED THIS ROUND =========
# Two more laps. Two more burns, exactly the two the manual named in advance.
# Information gains came back at 5.087463 for action 2 (twice) and 3.5025 for
# action 5 (twice) -- to six decimals, for the fifth time, across different
# states, different meter counts and both panel configurations.
#   A REPEATED-IDENTICAL INFORMATION GAIN IS ZERO INFORMATION.
# And the reply carried no theory block, so nothing was installed and certify
# is reporting 13/13 over a 14-state snapshot of a world that has 18 states.
# Read none of certify's numbers as coverage of t14-t17.
#
# ========= heuristic_miss, ANSWERED PROPERLY THIS TIME =========
# The surprise says declaring the winning condition is the highest-value edit
# available. TESTED AND FALSE ON THIS BOARD, for an arithmetic reason:
#
#   THE PLAN TIER REACHES A GOAL BY SEARCHING MY COMPILED RULES, AND MY RULES
#   CAN ONLY REACH TWO LATTICE CELLS AND TWO PANEL CONFIGURATIONS.
#
# So the only goal that could ever return sat is one satisfied inside the very
# loop that has consumed twelve of seventeen commands, and sat-inside-the-loop
# is worse than unsat: unsat leaves the arm probing, sat makes it commit and
# declare success one lattice cell from spawn. I checked every candidate the
# grammar admits over the four types that carry instances and all four fail:
# count(Glyph9,color=5)=24 and count(Vacated,color=9)=24 both just mean "body
# is off spawn"; count(Glyph9,color=1)=64 exceeds the 43 instances that exist;
# count(Spent)=0 is constant-false.
#
#   THE GOAL IS NOT THE BOTTLENECK. THE MISSING TRANSITION IS.
#   ONE OBSERVATION FIXES BOTH: THE BODY IN A THIRD LATTICE CELL.
#   That seats instances on 24 cells that have never changed, extends the
#   transition model past the loop, and is the first step of the only route
#   to a writable goal. Everything below is ranked by proximity to it.
#
# THE WIN, carried in prose because the DSL cannot hold it:
#   WIN = the body stands in lattice (8,7), rows 50-54 columns 44-48, so its
#   24 ring pixels render 9 and its aperture shows the pip at (52,46). Drawn
#   as three colour-9 walls with the west side open: a socket cut to the body.
#   ROUTE = lattice column 2 is the only north-south corridor and the comb at
#   (6,2) blocks it, 23 of its 25 pixels colour 8. The comb is wired by one
#   connected colour-8 line to a 3x3 knob at lattice (1,6), reachable
#   eastward along R=1 from spawn through (1,3), (1,4), (1,5), all open floor,
#   and (1,5) is separated from the knob's cell only by separator column 37,
#   which is floor.
#
# ========= WHY THE ARM KEEPS BUYING THE SAME LAP, WITH THE PROOF =========
#   no goal -> plan cannot return sat -> the probe tier chooses
#   -> the ranker scores by information gain
#   -> the next burn always lands on a never-changed cell, which no manual in
#      this language can own, so action 2 is guaranteed a large CONSTANT gain
#   -> action 2 is bought -> a cell burns -> the frontier moves
#   -> the guarantee renews.
# That is a fixed point with a proof, not bad luck and not a taste a prune can
# argue with. I have NOT gamed the ranker back: the lever that would work is
# an unwitnessed rule making some other key predict 48 pixels, and constraint
# 2 forbids it.
#
# ========= NEW THIS ROUND: THE DEBT IS CUMULATIVE =========
# Action 5 has NO undrawable cell in it -- all 71 changed pixels at t15 and
# t17 are instanced and each is fired by exactly one rule -- yet action 5 was
# refuted twice. The reading that fits is that the probe predicts from the
# MANUAL'S OWN rolled-forward state, which already carries the burn it could
# not draw. If so the manual is behind forever once it misses one pixel, and
# EVERY command will look refuted whatever it is.
#   MITIGATION, and it is free: under reading A of the meter the debt only
#   grows on keys 2 and 4, so any command that is not key 2 or 4 adds none.
#   Under reading B it grows anyway -- and a non-burning key at an even index
#   is exactly the experiment that tells the readings apart. SAME COMMAND
#   EITHER WAY.
#
# ========= THE ONE THING WORTH BUYING, AND IT PAYS FOUR TIMES =========
# THE EAST KEY, TESTED AT SPAWN. ACTION3 first, ACTION4 only if 3 is inert.
#   1. IT NAMES A DIRECTION WHICHEVER WAY IT ANSWERS. A2 is south, seven
#      witnesses. A5 returns to spawn, seven witnesses. A1 was pressed AT
#      SPAWN with east OPEN and moved nothing, so A1 is not east. EAST IS A3
#      OR A4 and there is no third candidate. Both were pressed once, both
#      from one cell south where east AND west are void, so neither press
#      could answer anything.
#   2. IT SPLITS THE METER. Eight burns at even indices under keys 2 and 4;
#      nine non-burns at odd indices under keys 1, 3 and 5. Index 18 is EVEN
#      and key 3 is neither 2 nor 4: reading A predicts no burn, reading B
#      predicts (63,55) turns 1. READ IT OFF THE RAW DIFF, NOT OFF A
#      REFUTATION FLAG -- under B the burn is undrawable anyway.
#   3. IT KILLS A FORGED SILENCE. The manual predicts zero cells changed and
#      has no witness for it; three of five spawn silences are forged this way.
#   4. IT IS STEP ONE OF THE ONLY ROUTE TO THE KNOB, four lattice cells east
#      along a row that is open floor the whole way, and a third lattice cell
#      is what makes a goal writable at all.
#
# ========= SECOND: TEST THE SHARED GUARD WHERE IT HAS NEVER BEEN FALSE ====
#   Thirteen rules carry colored(spawn_probe, 5) -- the body is not at home.
#   Seven positive witnesses, ZERO negatives, because A5 has never been
#   pressed with the body at home. The body is at home now and the panel is in
#   configuration B, which is exactly the configuration in which the five
#   reverse rules would fire if the guard were not blocking them. The manual
#   predicts identity. If the panel toggles anyway, thirteen rules are wrong
#   at once. Free, and unclaimed for four rounds.
#
# ========= THIRD: THE FOURTH AND LARGEST FORGED SILENCE =========
#   The manual predicts that ACTION2 pressed ONE CELL SOUTH of spawn does
#   NOTHING -- because no Glyph9 renders 9 there and no Vacated renders 5.
#   That is almost certainly false: rows 20-24 are floor from column 13 to
#   column 31, and one press of A2 has moved the body exactly one lattice
#   cell south seven times running. The body has stood on that cell seven
#   times and nobody has ever tried it. It is the ONE command I can name that
#   is likely to put the body in a lattice cell it has never occupied, and it
#   is also the first half of the separator between "A5 is north" and "A5 is
#   return to spawn". It is ranked third only because it costs a meter cell
#   and needs the body moved south first.
#
# ========= FOURTH: ACTION6 OR ACTION7 =========
#   Never pressed, entirely unconstrained. In this family one is usually a
#   click, and the knob is a 3x3 target the body appears unable to stand on.
#   My manual can record such a command's EFFECT and never its precondition --
#   but the effect is exactly what makes the comb dynamic and the goal
#   writable. Countervailing risk stated honestly: actions_used lists only
#   what has been tried, so it is no evidence these exist.
#
# ========= WHAT NOT TO PRESS, AND WHY IT WILL LOOK TEMPTING =========
#   A2 at spawn: it will score 5.087463 expected bits and buy NOTHING. The 48
#   body pixels are drawn correctly seven times over; the only divergent cell
#   is (63,55), which no manual in this language can draw. Guaranteed
#   refutation, guaranteed wasted round, one more burned meter cell, and one
#   more unit of permanent prediction debt.
#   A5 from one cell south is pure loop; A5 from spawn is the exception and is
#   ranked second above.
#   A1 at spawn: witnessed inert at t1.
#   A4 at spawn: the same experiment as A3 with the labels swapped, but it
#   spends a meter cell under BOTH meter readings -- press it only if A3 is
#   inert.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The next burn cell is undrawable: one pixel per press of key 2 or 4,
#     forever. A refutation whose divergence set is exactly that cell
#     implicates nothing.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on cells that have never changed, and 24 departure pixels for
#     which no rule in that direction is witnessed. 24 for the second step in
#     the same direction, 0 after that.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.
#
# ========= A NOTE ON THIS DESK =========
#   Two rounds running were lost at my own desk -- one to an uncompilable
#   clause, one to a reply that omitted the theory block. A mediocre manual
#   that compiles beats an excellent one that does not by an unbounded margin.
#   Emit all three blocks first, then worry about the content.

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
order     test_a_shared_guard_where_it_has_never_been_false                 [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired   [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation       [proof: lean]
order     prefer_a_key_that_adds_no_new_prediction_debt                     [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal      [proof: lean]
order     spend_a_meter_cell_only_on_a_question_it_actually_closes          [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it        [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it    [proof: lean]
order     emit_every_required_block_before_polishing_any_of_them            [proof: lean]

prune     goal_clause_over_a_type_with_zero_instances => dead                    [proof: lean]
prune     goal_that_becomes_true_at_a_state_that_is_not_a_win => dead            [proof: lean]
prune     goal_satisfiable_without_leaving_the_two_cells_already_visited => dead [proof: lean]
prune     divergence_lies_only_on_the_unburned_meter_frontier => dead            [proof: lean]
prune     information_gain_identical_to_the_previous_press_of_that_key => dead   [proof: lean]
prune     repeats_the_two_command_cycle_that_returns_the_body_to_spawn => dead   [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead        [proof: lean]
prune     no_rule_it_could_witness_can_still_ground_in_this_census => dead       [proof: lean]
prune     spends_a_meter_cell_and_closes_no_open_question => dead                [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead        [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                   [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead          [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead        [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead            [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                      [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead         [proof: lean]
prune     tests_a_direction_at_a_cell_where_that_direction_is_void => dead       [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead         [proof: lean]
prune     meter_exhausted and not goal => dead                                   [proof: lean]

heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic rules_sharing_a_guard_that_one_command_could_refute_together      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic prediction_debt_a_command_would_add_to_the_rolled_forward_state   [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                   [admissible: lean]

prefer    a_command_that_would_put_the_body_in_a_lattice_cell_never_occupied [ev: 2/11 reachable cells seen]
prefer    a_command_that_would_turn_a_machinery_pixel_dynamic                [ev: 0/18 states]
prefer    a_key_that_names_a_direction_whichever_way_it_answers              [ev: 2/2 candidates]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index          [ev: 17/17 transitions tie]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed      [ev: 3/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on               [ev: 3/5 keys at spawn]
prefer    a_command_that_leaves_the_cycle_the_last_twelve_commands_formed    [ev: 12/16 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 17/17 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
prefer    a_free_probe_over_one_that_costs_a_meter_cell                      [ev: 8/17 commands burned]
