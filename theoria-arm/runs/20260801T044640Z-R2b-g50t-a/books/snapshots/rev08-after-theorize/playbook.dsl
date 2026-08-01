# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= THE STATE OF PLAY =========
# Fourteen states, thirteen transitions: RESET, A1 A2 A3 A4 A5 A2 A5 A2 A5
# A2 A5 A2 A5.
#   t1  A1 at spawn        -> nothing
#   t2  A2 at spawn        -> body one lattice cell SOUTH (48) + burn (63,63)
#   t3  A3 one cell south  -> nothing
#   t4  A4 one cell south  -> burn (63,62) and nothing else
#   t5  A5 one cell south  -> body to spawn (48) + panel A->B (23)
#   t6  A2 at spawn        -> body SOUTH (48) + burn (63,61), 9 frames
#   t7  A5 one cell south  -> body to spawn (48) + panel B->A (23)
#   t8  A2 at spawn        -> body SOUTH (48) + burn (63,60), 7 frames
#   t9  A5 one cell south  -> body to spawn (48) + panel A->B (23)
#   t10 A2 at spawn        -> body SOUTH (48) + burn (63,59), 9 frames
#   t11 A5 one cell south  -> body to spawn (48) + panel B->A (23)
#   t12 A2 at spawn        -> body SOUTH (48) + burn (63,58), 7 frames
#   t13 A5 one cell south  -> body to spawn (48) + panel A->B (23)
# Body is at spawn, lattice (1,2). Panel is configuration B. SIX meter cells
# burned, cols 58-63; 58 remain. Next command index is 14, EVEN.
#
# ========= WHAT ACTUALLY BROKE THIS ROUND: THE MANUAL DID NOT COMPILE =====
# No transition was spent. The four refutations are the four already priced.
# The one new fact is the compiler's:
#
#   UnsupportedClause: count(Gate) -- this level declares no instance of that
#   type, so the count is 0 on every state and the clause decides nothing.
#
# I had written a goal over a type with ZERO instances deliberately, arguing
# an unreachable goal is honest rather than vacuous. It is neither: it does
# not compile, and an uncompiled manual has no executable form, so plan,
# certify and probe all got nothing. Gate and the goal line are deleted.
#
# THE LAW THAT REPLACES THE MISTAKE, and it binds this playbook too:
#   A GOAL CAN ONLY NAME CELLS THAT HAVE ALREADY CHANGED, because only those
#   carry instances. It is the burn frontier from the other side.
#
# ========= heuristic_miss, ANSWERED WITH A REFUSAL AND A PRICE =========
# There is still no goal section, and this is the enumerated reason, not a
# shrug. A goal may say count(<type>) or <instance>.pos = <landmark>. The
# only types with instances are Glyph9 (panel slot 1, underline 1, the spawn
# ring, six burned meter cells), Vacated (the ring one cell south), Spent
# (slot 2) and Dark (underline 2). ALL OF THEM ARE PANEL, SPAWN RING OR
# METER. The nearest candidate, count(Glyph9, color = 9) = 0, is false in all
# fourteen states and would become TRUE one press of A2 from here, at a cell
# that is not a win -- a goal that halts a planner one move from spawn is
# worse than no goal, because unsat is honest and sat-on-garbage is not.
# The pos form is dead too: this world recolours, it never moves, so no
# instance's pos has ever changed.
#
#   SO THE GOAL IS BOUGHT WITH A COMMAND, NOT WRITTEN WITH AN EDIT.
#   The first pixel of the comb or of the socket bracket that changes colour
#   makes those cells dynamic, seats instances on them, and makes the goal
#   line both writable and sound in the same instant. Everything ranked below
#   is ranked by how close it gets to that pixel.
#
# THE WIN, carried in prose because the DSL cannot hold it:
#   WIN = the body stands in lattice (8,7), rows 50-54 cols 44-48, so its 24
#   ring pixels render 9 and its aperture shows the pip at (52,46). Drawn as
#   three colour-9 walls with the west side open: a socket cut to the body.
#   ROUTE = lattice column 2 is the only north-south corridor and the comb at
#   (6,2) blocks it, 23 of its 25 pixels colour 8. The comb is wired by one
#   connected colour-8 line to a 3x3 knob at (1,6), reachable eastward along
#   R=1 from spawn: (1,2) -> (1,3) -> (1,4) -> (1,5), three steps on open
#   floor, and (1,5) is separated from the knob's cell only by separator col
#   37, which is floor.
#
# ========= WHY THE ARM KEEPS BUYING THE SAME LAP =========
# The next meter burn always lands on a cell that has never changed, so no
# instance owns it, so no event can draw it. Every press of A2 refutes the
# manual by exactly one pixel; the refutation makes A2 look maximally
# informative; the ranker buys A2. It is a fixed point, not a taste.
# THE PROOF THAT THE BITS ARE FAKE IS IN THE PAYLOADS:
#   information_gain_bits = 5.087463 for action 2 at P-05 AND at P-07.
#   information_gain_bits = 3.5025   for action 5 at P-06 AND at P-08.
# Identical to six decimals across different states, different meter counts,
# opposite panel configurations. TREAT A REPEATED-IDENTICAL GAIN AS ZERO.
# I have NOT gamed the ranker back: the lever that would work is an
# unwitnessed rule making A3 predict 48 pixels, and constraint 2 forbids it.
#
# ========= THE ONE THING WORTH BUYING, AND IT PAYS THREE TIMES =========
# PRESS ACTION3 AT SPAWN.
#   1. THE EAST KEY, unanswered after thirteen commands and the only thing
#      between this arm and the knob. A2 is south (5 witnesses). A5 returns
#      to spawn (5 witnesses). A1 was pressed AT SPAWN with east OPEN and
#      moved nothing, so A1 is not east. EAST IS A3 OR A4, no third
#      candidate. A3 and A4 were each pressed once, both from lattice (2,2)
#      where east AND west are void, so neither press could answer anything.
#      If the body steps, A3 is east. If not, A4 is east by elimination.
#   2. THE METER. Six burns at even indices under keys 2,4,2,2,2,2; seven
#      non-burns at odd indices under keys 1,3,5,5,5,5,5. Reading A (key is 2
#      or 4) and reading B (index is even) agree on all thirteen. Index 14 is
#      EVEN and key 3 is neither 2 nor 4: A burns nothing, B burns (63,57).
#      READ IT OFF THE RAW DIFF, NOT OFF A REFUTATION FLAG -- under B the
#      burn is undrawable anyway, so a refutation fires either way.
#   3. A FORGED SILENCE. The manual predicts zero cells changed for A3 at
#      spawn and has no witness for it; three of the five spawn silences are
#      forged this way and A3 is one.
#   And the knob is four eastward lattice cells away, so the east key is the
#   first step of the only route to a goal line.
#
# ========= SECOND CHOICE: PRESS ACTION5 AT SPAWN =========
#   Thirteen rules share colored(spawn_probe, 5) -- the body is not at home.
#   Five positive witnesses, ZERO negatives, because A5 has never been
#   pressed with the body at home. The body is at home now. The manual
#   predicts identity. If the panel toggles anyway, thirteen rules are wrong
#   at once. Ranked second only because it does not touch the east key.
#
# ========= THIRD CHOICE: ACTION6 OR ACTION7 =========
#   Never pressed, entirely unconstrained. In this family one is usually a
#   click, and the knob is a 3x3 target the body appears unable to stand on.
#   My manual can record such a command's EFFECT and never its precondition
#   -- but the effect is exactly what makes the comb dynamic and the goal
#   writable, so the ceiling here is the level itself.
#
# ========= WHAT NOT TO PRESS, AND WHY IT WILL LOOK TEMPTING =========
#   A2 at spawn: it will score ~5.09 expected bits and buy NOTHING. The 48
#   body pixels are drawn correctly five times over; the only divergent cell
#   is (63,57), which no manual in this language can draw. Guaranteed
#   refutation, guaranteed wasted round, one more burned meter cell.
#   A5 from one cell south is pure loop; A5 from spawn is the exception and
#   is ranked second above.
#   A1 at spawn: witnessed inert at t1.
#   A4 at spawn: the same experiment as A3 with the labels swapped, but it
#   spends a meter cell under BOTH readings -- press it only if A3 is inert.
#
# ========= PRICES ADVERTISED IN ADVANCE, NOT DEFECTS =========
#   * The next burn cell is undrawable: one pixel per press of A2 or A4,
#     forever. A refutation whose divergence set is exactly that cell
#     implicates nothing.
#   * First step onto fresh ground costs 48 undrawable pixels: 24 arrival
#     pixels on rows 8-12 cols 20-24 which have never changed, and 24
#     departure pixels for which no east-leaves rule is witnessed. 24 for the
#     second step in the same direction, 0 after.
#   Read a refutation by its divergence set. Where the set is one of these,
#   the manual said so first.
#
# ========= ONE CAUTION ABOUT CERTIFY =========
#   Its block says 9/9 over 9 transitions while the world has 13, and this
#   manual did not compile, so those numbers describe an earlier snapshot.
#   Do not read them as coverage of t10-t13.

order     settle_the_east_key_before_anything_else_at_this_cell            [proof: lean]
order     buy_the_observation_that_makes_a_goal_writable_before_writing_one [proof: lean]
order     treat_a_repeated_identical_information_gain_as_zero_gain         [proof: lean]
order     discount_any_gain_that_comes_from_a_cell_with_no_instance        [proof: lean]
order     prefer_a_command_that_closes_three_open_questions_over_one       [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves  [proof: lean]
order     break_a_repeating_command_cycle_before_optimising_within_it      [proof: lean]
order     test_a_shared_guard_where_it_has_never_been_false                [proof: lean]
order     press_an_action_never_pressed_before_repressing_a_modelled_one   [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired  [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance               [proof: lean]
order     read_the_meter_answer_off_the_raw_diff_not_off_a_refutation      [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it               [proof: lean]
order     treat_the_socket_as_the_win_and_the_comb_only_as_the_subgoal     [proof: lean]
order     spend_a_meter_cell_only_on_a_question_it_actually_closes         [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it       [proof: lean]
order     check_the_arm_can_seat_a_declaration_before_any_clause_uses_it   [proof: lean]

prune     goal_clause_over_a_type_with_zero_instances => dead                    [proof: lean]
prune     goal_that_becomes_true_at_a_state_that_is_not_a_win => dead            [proof: lean]
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

heuristic cells_whose_first_change_would_make_a_goal_line_writable          [admissible: lean]
heuristic keys_whose_inertness_here_rests_on_no_witness                     [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination               [admissible: lean]
heuristic open_questions_a_command_can_close                                [admissible: lean]
heuristic actions_of_the_alphabet_never_yet_pressed                         [admissible: lean]
heuristic live_readings_of_the_meter_a_command_can_eliminate                [admissible: lean]
heuristic rules_sharing_a_guard_that_one_command_could_refute_together      [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_advertised_prices            [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                         [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut               [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open              [admissible: lean]
heuristic meter_cells_remaining_as_a_budget_on_every_plan                   [admissible: lean]

prefer    a_command_that_would_turn_a_machinery_pixel_dynamic               [ev: 0/14 states]
prefer    a_key_that_names_a_direction_whichever_way_it_answers             [ev: 2/2 candidates]
prefer    a_key_that_splits_the_two_meter_readings_at_an_even_index         [ev: 13/13 transitions tie]
prefer    a_key_whose_predicted_inertness_here_has_never_been_witnessed     [ev: 3/5 keys at spawn]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on              [ev: 3/5 keys at spawn]
prefer    a_command_that_leaves_the_cycle_the_last_eight_commands_formed    [ev: 8/10 commands]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                  [ev: 13/13 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                    [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered           [ev: 1/1 levels]
prefer    a_free_probe_over_one_that_costs_a_meter_cell                     [ev: 6/13 commands burned]
