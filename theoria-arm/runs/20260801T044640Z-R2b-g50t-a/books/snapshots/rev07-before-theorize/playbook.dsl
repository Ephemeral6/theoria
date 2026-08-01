# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Ten states, nine transitions: RESET, A1 A2 A3 A4 A5 A2 A5 A2 A5.
#   t1 A1 at spawn        -> nothing
#   t2 A2 at spawn        -> body one lattice cell SOUTH (48) + burn (63,63)
#   t3 A3 one cell south  -> nothing
#   t4 A4 one cell south  -> burn (63,62) and nothing else
#   t5 A5 one cell south  -> body to spawn (48) + panel A->B (23)
#   t6 A2 at spawn        -> body SOUTH (48) + burn (63,61), 9 frames not 7
#   t7 A5 one cell south  -> body to spawn (48) + panel B->A (23)
#   t8 A2 at spawn        -> body SOUTH (48) + burn (63,60), 7 frames
#   t9 A5 one cell south  -> body to spawn (48) + panel A->B (23)
# Body is at spawn, lattice (1,2). Panel is in configuration B. FOUR meter
# cells burned, cols 60-63; 60 remain. Next command index is 10, EVEN.
#
# ========= READ THIS FIRST: THE LAST FOUR COMMANDS WERE A LOOP =========
# t6-t9 were A2 A5 A2 A5. The body went south, home, south, home. The panel
# went B, A, B. Two meter cells burned. The store says 10 states and 8
# distinct, and the two duplicates are the old sterile pair.
#
# The loop is not bad luck, it is a ranker artefact and it will repeat. The
# probe ranker maximises expected bits over the manual and its ablations. My
# manual predicts ~50 or ~71 changed cells for keys 2 and 5 and predicts
# IDENTITY for keys 1, 3 and 4. Predicted identity scores near zero expected
# bits however ignorant I actually am, because the DSL cannot say `unknown` --
# it can only say `nothing happens`, in the same voice it uses for things it
# has watched three times. So the ranker keeps buying transitions I already
# model and never buys the ones I do not.
#
# The four commands did cash in: they witnessed meter_burn_key2_next (t6, t8)
# and the reverse panel toggle (t7), which were the entire content of the four
# probe_refutations, and both were already written out in the previous
# manual's own prose. Four commands and two meter cells for text I had
# already drafted.
#
# THE PRUNES BELOW ARE WRITTEN TO KILL THE LOOP, not to express a taste.
#
# ========= THE ONE THING WORTH BUYING, AND IT PAYS TWICE =========
# PRESS ACTION3 AT SPAWN.
#
#   Question 1, THE EAST KEY -- unanswered after nine commands and it is the
#   only thing standing between this arm and the knob. A2 is south (three
#   witnesses). A5 returns to spawn (three witnesses). A1 was pressed AT SPAWN
#   with east OPEN and moved nothing, so A1 is not east. EAST IS A3 OR A4 and
#   there is no third candidate. A3 and A4 have each been pressed exactly
#   once, both from lattice (2,2), where east AND west are both void -- so
#   neither press could ever have answered anything about east. East of spawn
#   is three unbroken lattice cells of floor along R=1, ending beside the
#   knob. If the body steps, A3 is east and the map closes. If it does not,
#   A4 is east by elimination. Both outcomes name the key.
#
#   Question 2, THE METER. Four burns, at indices 2, 4, 6, 8, under keys
#   2, 4, 2, 2. Five non-burns at indices 1, 3, 5, 7, 9 under keys 1, 3, 5,
#   5, 5. Reading A (burns iff key is 2 or 4) and reading B (burns iff index
#   is even) agree on ALL NINE transitions -- not because the evidence is
#   thin but because every key-2 and key-4 press happened to land on an even
#   index, four rounds running. Index 10 is EVEN and key 3 is neither 2 nor 4.
#   A burns nothing; B burns (63,59). One press decides it at last.
#
#   No other command on the board closes either question, and this one closes
#   both, and it is free under reading A.
#
# ========= SECOND CHOICE: PRESS ACTION5 AT SPAWN =========
#   Thirteen rules share the guard colored(spawn_probe, 5) -- the body is not
#   at home. In ten states that guard has three positive witnesses and ZERO
#   negatives, because A5 has never been pressed with the body at home. My
#   manual predicts identity. If the panel toggles anyway, thirteen rules are
#   wrong at once and I want to know in the cheapest possible way. Ranked
#   second only because it does not touch the east key.
#
# ========= WHAT NOT TO PRESS =========
#   A2 at spawn: every rule it would witness is at full coverage, it spends a
#   meter cell, and it re-enters the loop. A1 at spawn: witnessed inert at t1,
#   buys nothing. A4 at spawn: same experiment as A3 with the labels swapped
#   but it spends a meter cell whichever way it answers -- press it ONLY if
#   A3 comes back inert, at which point it is the confirmation of an
#   elimination already made.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * First step onto fresh ground costs 48 undrawable pixels. Rows 8-12 cols
#     20-24 have never changed, so they are board, so no instance exists to
#     draw the arrival; and no east-leaves rule is witnessed, so the departure
#     is undrawn too. 24 for the second step in the same direction, 0 after.
#   * Nothing else is owed. meter_burn_key2_next and all five reverse panel
#     rules are installed this round, so the two debts the previous playbook
#     advertised are paid.
#   Read a refutation by its divergence set. Where the set is exactly the
#   first-step price above, the manual is not implicated -- it said so first.
#
# ========= THERE IS NO GOAL LINE AND THE WINNING CONDITION IS THIS =========
# heuristic_miss is right: is_goal compiles to False, plan cannot return sat,
# and every command is a probe. I decline to invent a goal and the reason is
# structural, not lazy: a goal ranges over declared objects, an object gets
# instances only on cells that have VARIED, and every candidate win-marker on
# this board is constant -- the socket interior (rows 50-54 cols 44-48,
# colour 5), its pip (52,46), the comb teeth (rows 38-42 cols 14-18) and the
# knob (rows 9-11 cols 39-41) are all colour 8 or 5 and none has moved in ten
# frames. A goal true in the wrong state is worse than no goal because it
# halts a planner at its first step. So the winning condition is carried HERE,
# in prose, and the orders and heuristics below rank by distance to it:
#
#   WIN = the body stands in lattice (8,7), rows 50-54 cols 44-48, so that its
#   24 ring pixels render 9 and its aperture shows the pip at (52,46). That
#   cell is drawn as three colour-9 walls with its west side left open: a
#   socket cut to the body's shape.
#
#   ROUTE = lattice column 2 is the only north-south corridor and the comb at
#   (6,2) blocks it, 23 of its 25 pixels colour 8. The comb is wired by one
#   connected colour-8 line to a 3x3 knob at (1,6), reachable eastward along
#   R=1 from spawn: (1,2) -> (1,3) -> (1,4) -> (1,5), three steps on open
#   floor, and (1,5) is separated from the knob's cell only by separator col
#   37, which is floor.
#
#   THE GOAL LINE BECOMES WRITABLE the moment any comb pixel or any socket-
#   ring pixel changes colour: that cell becomes dynamic, the arm seats an
#   instance, and a count() goal can finally name it. That is one observation
#   away and it is the same observation that wins the level.
#
#   A SECOND HYPOTHESIS ABOUT THE COMB, worth its own probe once the body is
#   south: the panel is a two-slot MODE selector, and ACTION2 took 7 internal
#   frames in mode A (t2, t8) and 9 in mode B (t6) for the identical six-row
#   move. If the modes differ in what terrain the body may cross, the comb is
#   a mode problem rather than a switch problem. Test at lattice (5,2): press
#   A2 in mode A, then in mode B, and see whether either enters (6,2).

order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     prefer_a_command_that_closes_two_open_questions_over_one         [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     break_a_repeating_command_cycle_before_optimising_within_it      [proof: lean]
order     test_a_shared_guard_where_it_has_never_been_false                [proof: lean]
order     stop_pressing_a_key_the_moment_its_question_has_been_answered    [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     treat_the_socket_as_the_goal_even_though_no_goal_line_compiles   [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     spend_a_meter_cell_only_on_a_question_it_actually_closes         [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]

prune     repeats_the_two_command_cycle_that_returns_the_body_to_spawn => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead      [proof: lean]
prune     spends_a_meter_cell_and_closes_no_open_question => dead              [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead      [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                 [proof: lean]
prune     divergence_lies_only_on_a_cell_that_had_never_changed => dead        [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead      [proof: lean]
prune     repeats_the_key_that_the_previous_command_just_answered => dead      [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead          [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                    [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead       [proof: lean]
prune     tests_a_direction_at_a_cell_where_that_direction_is_void => dead     [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead       [proof: lean]
prune     meter_exhausted and not goal => dead                                 [proof: lean]

heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                               [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate               [admissible: lean]
heuristic rules_sharing_a_guard_that_one_command_could_refute_together     [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices           [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                        [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut              [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open             [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                  [admissible: lean]

prefer    a_key_that_names_a_direction_whichever_way_it_answers            [ev: 2/2 candidates]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index        [ev: 9/9 transitions tie]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed    [ev: 3/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on             [ev: 3/5 keys at spawn]
prefer    a_command_that_leaves_the_cycle_the_last_four_commands_formed    [ev: 4/4 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                 [ev: 9/9 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                   [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered          [ev: 1/1 levels]
prefer    a_free_probe_over_one_that_costs_a_meter_cell                    [ev: 4/9 commands burned]
