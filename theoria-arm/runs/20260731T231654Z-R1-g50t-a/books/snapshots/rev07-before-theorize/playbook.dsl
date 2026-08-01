# playbook.dsl -- what to buy with the next command, not a route.
#
# ========= WHAT THE LAST ROUND BOUGHT =========
# Four commands were adjudicated: t6 ACTION2, t7 ACTION5, t8 ACTION1,
# t9 ACTION3. Two probe_refutations fired and BOTH were misses this
# playbook had already posted a price for -- one meter pixel at t6, the
# 23 panel pixels at t7. The toggle-back rules now have their witness and
# are back in the manual. The refutation report hashes the whole frame,
# so read the DIVERGENCE SET, never the verdict.
#
# TWO REAL RESULTS, and both change what to press next:
#
#  (1) THE METER IS A CLOCK, NOT A KEY. t1 is ACTION1 and burned nothing;
#      t8 is ACTION1 and burned (63,60). Burns land at t2, t4, t6, t8 --
#      every even command index, 9/9. No guard can read a command counter,
#      so both burn rules are DELETED and the manual is off by exactly one
#      pixel on every even-indexed command, at a cell it names in advance.
#      NEXT INDEX IS 10, EVEN: expect (63,59) to burn and expect the
#      manual to miss it. Subtract that pixel before reading any diff.
#      BUDGET CONSEQUENCE: every command costs half a meter cell whatever
#      key is pressed. 60 cells remain, so about 120 commands remain.
#      Keys 1, 3 and 5 are NOT free and the old plan treated them as free.
#
#  (2) ACTION3 IS NOT EAST. t9 pressed it from spawn, where east is three
#      lattice cells of unbroken floor, and nothing moved. ACTION1 is not
#      east either (pressed at spawn at t1 and t8). ACTION2 is down, 2/2.
#      ACTION5 returns north and toggles the panel, 2/2. THAT LEAVES
#      ACTION4 AS THE ONLY UNPRESSED CANDIDATE FOR EAST AMONG KEYS 1-5.
#      The playbook's previous top pick, ACTION3, is spent and answered.
#
# ========= THE BOARD AS THE MANUAL NOW SEES IT =========
#   Body at lattice (1,2), spawn. Panel in configuration A. Meter burned
#   at cols 60-63 of row 63. Next command index 10, EVEN.
#
#   At spawn:  key(2) -> 48 body cells south, WITNESSED t2 and t6
#              key(1) -> nothing, WITNESSED t1 and t8
#              key(3) -> nothing, WITNESSED t9
#              key(4) -> NEVER PRESSED HERE
#              key(5) -> NEVER PRESSED HERE (manual predicts nothing)
#
#   Open neighbours of spawn are DOWN and EAST only; up and left are void.
#
# ========= THE ONE THING WORTH BUYING =========
# PRESS ACTION4 FROM SPAWN.
#   It is the last untested candidate for the one direction the whole map
#   needs. East of spawn is three lattice cells of floor leading to the
#   knob that wires the comb, and the comb is the only door south to the
#   socket. Both outcomes are worth the command:
#     body steps east  -> ACTION4 is east, the corridor opens, and the
#                         next question is whether the knob can be bumped.
#     body stays still -> NO KEY IN 1..5 IS EAST. The body can travel only
#                         up and down lattice column 2, that column is
#                         sealed by the comb, and ACTION6/ACTION7 become
#                         the only remaining channel rather than a
#                         curiosity. That is a hard result, not a waste.
#
# THE ADVERTISED PRICE OF A STEP ONTO FRESH GROUND: 48 pixels the manual
# cannot draw -- rows 8-12 cols 20-24 have never changed, so they are
# board and no rule may draw their first change, and the 24 departure
# pixels need an east-leaves rule that cannot be written before an east
# press witnesses one. Plus the one clock pixel at (63,59). 49 in total,
# named cell by cell in the manual. Second step east costs 24, third 0.
#
# ========= WHAT TO BUY AFTER THAT =========
#   ACTION6, then ACTION7. Never pressed, wholly unconstrained, and one of
#   them is likely the click this action family usually carries. The knob
#   is a 3x3 target the body appears unable to stand on, which is the
#   shape of thing a click presses. The manual cannot express a click's
#   precondition, only its effect, and says so.
#
#   ACTION5 AT SPAWN. Thirteen panel rules carry `body is not at spawn'
#   and both toggles happened with the body at (2,2), so that conjunct
#   still has no discriminating witness after two presses. 23 pixels
#   either way. It also gates a bigger question, below.
#
#   RE-TEST 1, 3 AND 4 IN CONFIGURATION B. Every inertness witness for
#   those three keys was collected in configuration A -- t1, t3, t4, t8,
#   t9 all sit in A, because t7 put the panel back before t8. If the panel
#   is a mode selector the key map may differ by mode, and I have never
#   looked. Getting to B needs ACTION5, which needs the body away from
#   spawn under the current rules, so this is a two-command experiment.
#
# ========= PRICES POSTED IN ADVANCE, so none reads as a surprise =========
#   - one pixel at (63,59) on the next command, and one at the next
#     leading edge on every even-indexed command after it.
#   - 48 body pixels the first time the body enters any lattice cell it
#     has not entered before.
#   - 23 panel pixels if ACTION5 at spawn toggles the panel.
#
# ========= WHY NO PLAN, AND WHAT WOULD CHANGE IT =========
# The heuristic_miss surprise is right: with no goal: section is_goal is
# False everywhere, plan never returns sat, commit never runs. The manual
# enumerates all three goal forms the grammar admits and none can name the
# winning position, because the socket interior has never changed and is
# therefore board with no instances to count. THIS ARM IS IN PURE PROBE
# MODE ON PURPOSE. A goal becomes writable only after the body first
# enters lattice (8,7) -- one step after it stops being needed. Ranking is
# therefore entirely the business of the lines below.

order     settle_whether_action4_is_east_before_any_other_probe          [proof: lean]
order     press_an_untried_action_before_repeating_a_witnessed_no_op      [proof: lean]
order     test_actions_six_and_seven_once_the_five_are_eliminated         [proof: lean]
order     cost_every_command_at_half_a_meter_cell_whatever_key_it_is      [proof: lean]
order     subtract_the_clock_pixel_before_reading_any_divergence_set      [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance              [proof: lean]
order     confirm_the_manual_compiled_before_trusting_any_certify_number  [proof: lean]
order     treat_predicted_inertness_as_ignorance_unless_a_witness_backs_it [proof: lean]
order     re_test_an_inert_key_in_the_other_panel_configuration           [proof: lean]
order     rank_by_witnesses_a_command_would_create_not_by_pixels_it_moves [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it              [proof: lean]
order     collect_the_free_cascade_length_whenever_a_command_is_spent     [proof: lean]

prune     divergence_lies_only_on_the_meter_leading_edge => dead          [proof: lean]
prune     probe_designed_only_to_separate_the_two_meter_readings => dead  [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead            [proof: lean]
prune     ranked_only_because_the_manual_predicts_the_most_pixels => dead [proof: lean]
prune     every_rule_it_would_witness_is_already_at_full_coverage => dead [proof: lean]
prune     repeats_a_key_whose_inertness_here_is_already_witnessed => dead [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead  [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead     [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead               [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead  [proof: lean]
prune     treats_an_odd_key_as_free_because_the_bar_did_not_burn => dead  [proof: lean]
prune     meter_exhausted and not goal => dead                            [proof: lean]

heuristic actions_never_pressed_from_the_cell_the_body_stands_on          [admissible: lean]
heuristic direction_labels_a_command_would_fix_by_elimination             [admissible: lean]
heuristic actions_never_pressed_in_the_current_panel_configuration        [admissible: lean]
heuristic actions_outside_the_five_that_carry_no_witness_at_all           [admissible: lean]
heuristic open_questions_a_single_command_can_close                       [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                 [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                       [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut             [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open            [admissible: lean]
heuristic commands_remaining_before_the_bar_is_spent                      [admissible: lean]

prefer    the_last_unpressed_candidate_for_a_direction_the_map_needs     [ev: 1/1 candidates]
prefer    a_key_never_pressed_from_the_cell_the_body_stands_on           [ev: 2/5 keys at spawn]
prefer    an_action_outside_the_five_once_the_five_are_exhausted         [ev: 2/7 actions untried]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff               [ev: 9/9 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                 [ev: 1/1 levels]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered        [ev: 1/1 levels]
prefer    a_press_at_a_third_lattice_cell_that_splits_up_from_return     [ev: 2/2 key5_presses]
prefer    a_configuration_b_press_of_a_key_only_ever_tried_in_a          [ev: 5/5 inert presses in a]
