# playbook.dsl -- what to buy with the next command, not a route.
#
# ================= THE ONLY THING THAT MATTERS THIS ROUND =================
# ACTION2 FROM SPAWN IS EXHAUSTED. It has been pressed seven times, its two
# rules stand at 168/168, its cascade behaviour is settled 7/7, and its only
# remaining effect is one meter cell I cannot draw. An eighth press buys
# NOTHING and costs one command and one bar cell. The same is true of
# ACTION5 pressed from lattice (2,2): seven presses, 168/168, seven panel
# toggles, nothing left in it.
#
# Twelve of the last twelve commands were those two keys alternating between
# those two cells. Three consecutive rounds. The manual is not the problem:
# certify replays every transition exactly, explains every pixel, admits no
# clash, and all twelve probe_refutations in three rounds had divergence sets
# lying entirely on the meter's undrawable leading edge. The RANKING is the
# problem, so this file is deliberately short -- a criterion at line thirty
# is a criterion nobody read.
#
# ---------------------------------------------------------------------------
# WHY THE RANKING FAILED: every ACTION2 press burns a meter cell; every burn
# lands on a cell that is board at the instant it burns; no rule the manual
# can express draws it. So EVERY ACTION2 PRESS FIRES A REFUTATION however
# little it teaches, and a desk that ranks by refutation-fired keeps buying
# the move that fires one. Read divergence SETS, not hashes. The first two
# prunes encode this.
#
# WHAT THIS ROUND ACTUALLY BOUGHT, honestly: two more witnesses for rules
# already at full coverage (nothing), two more panel toggles (nothing), two
# more burns on the diagonal where both meter readings agree (nothing), and
# one sharpening -- the 7-frame/9-frame cascade split is now 7/7.
#
# ---------------------------------------------------------------------------
# THE BOARD AS IT STANDS (state 17): body home at lattice (1,2); panel in
# configuration B; EIGHT meter cells burned, cols 56-63 of row 63; the next
# command has index 18, which is EVEN. Eleven lattice cells are reachable and
# the body has stood in TWO. Three steps east along lattice row 1 reach the
# cell adjacent to the knob; the knob gates the comb; the comb gates every
# route to the socket. Under the harsher meter reading 56 commands remain and
# the route costs about nineteen, so the budget is not yet binding -- waste
# is.
#
# WHAT TO BUY, AND WHY, AS CRITERIA:
#
#  (1) PARITY FIRST, BECAUSE IT IS FREE AND IT COMPOUNDS. Seventeen commands,
#      seventeen times a key whose parity matched its index's parity, zero
#      separation of the two meter readings. Index 18 is even. An ODD key
#      bought now separates them; the EVEN-key probe it displaces separates
#      them too when bought at index 19. Taking the odd probe first collects
#      the separation on both commands; taking the even one first collects it
#      on neither. That is an ordering consequence, not a stored route.
#
#  (2) THE ODD PROBE AVAILABLE HERE IS THE FIFTH KEY PRESSED AT HOME, AND IT
#      IS THE CHEAPEST TRIPLE ON THE BOARD. The body has never been at spawn
#      when that key was pressed -- seven presses, all from one cell south.
#      The manual stakes a prediction of EXACTLY ZERO CHANGED CELLS, the only
#      zero-pixel stake it can make. Zero cells confirms the spawn_probe
#      guard and kills the parity reading. One cell on the bar confirms the
#      guard and kills the action-keying reading. Twenty-three cells refutes
#      the guard and puts thirteen rules into repair. Forty-eight cells names
#      that key as UNDO rather than UP or RETURN. Four outcomes, all legible
#      in the raw pixel count, every one decisive.
#
#  (3) THE EAST KEY IS THE ONLY QUESTION WHOSE ANSWER MOVES THE BODY, and it
#      is next. At spawn west is void and east is open floor for three
#      lattice cells, so the right-hand direction candidate pressed here
#      either steps east or names the other candidate by elimination -- the
#      first key was already excluded from east at t1. Advertised cost if it
#      moves: 49 divergent cells, all of them cells the manual said in
#      advance it cannot own. DO NOT READ THAT AS A REFUTATION. A zero-cell
#      answer at an even index kills both meter readings at once.
#
#  (4) TWO KEYS HAVE NEVER BEEN PRESSED AT ALL. Every outcome of either is
#      new information on a board where twenty rules sit at full coverage,
#      and one of them is plausibly the click that presses a knob the body
#      cannot stand on. Rank behind (2) and (3), ahead of any repeat.
#
#  (5) ONE PRESS IS ONE LATTICE CELL, 7/7. Every distance below is counted in
#      lattice cells, not pixels.
#
# No stored sequence anywhere: every line below is a criterion on the current
# frame plus the manual's own open questions.

order     never_repeat_a_key_at_a_cell_where_its_rules_are_already_full      [proof: lean]
order     read_a_refutation_by_its_divergence_set_not_by_whether_it_fired    [proof: lean]
order     discount_a_divergence_the_manual_priced_in_advance                 [proof: lean]
order     take_the_separation_that_compounds_before_the_one_that_does_not    [proof: lean]
order     buy_the_probe_that_closes_three_questions_before_one_that_closes_one [proof: lean]
order     settle_the_east_key_before_routing_toward_the_knob                 [proof: lean]
order     open_the_gate_before_planning_anything_south_of_it                 [proof: lean]
order     try_an_unpressed_key_before_repeating_an_exhausted_one             [proof: lean]
order     check_a_rule_can_fire_before_ranking_a_probe_that_tests_it         [proof: lean]

prune     every_rule_it_would_witness_is_already_at_full_coverage => dead     [proof: lean]
prune     ranked_only_because_a_refutation_fired_on_it => dead                [proof: lean]
prune     divergence_lies_only_on_the_meter_leading_edge => dead              [proof: lean]
prune     repeats_a_key_already_pressed_from_this_very_cell => dead           [proof: lean]
prune     revisits_a_lattice_cell_by_an_already_witnessed_key => dead         [proof: lean]
prune     key_parity_equals_command_index_parity_while_the_meter_is_open => dead [proof: lean]
prune     destination_ring_pixels_are_not_all_floor => dead                   [proof: lean]
prune     action_excluded_for_this_direction_by_an_earlier_no_op => dead      [proof: lean]
prune     route_that_crosses_the_comb_while_it_still_reads_eight => dead      [proof: lean]
prune     meter_exhausted and not goal => dead                                [proof: lean]

heuristic open_questions_a_command_can_close                                 [admissible: lean]
heuristic divergent_cells_that_lie_outside_the_meter_edge                    [admissible: lean]
heuristic lattice_cells_the_body_has_never_occupied                          [admissible: lean]
heuristic lattice_distance_to_the_knob_while_the_gate_is_shut                [admissible: lean]
heuristic lattice_distance_to_the_socket_once_the_gate_is_open               [admissible: lean]
heuristic live_readings_a_command_can_eliminate                              [admissible: lean]
heuristic commands_remaining_under_the_worse_of_the_two_meter_readings       [admissible: lean]

prefer    a_key_never_pressed_from_the_cell_the_body_stands_on               [ev: 0/12 commands]
prefer    a_key_whose_parity_differs_from_the_command_index                  [ev: 0/17 commands]
prefer    a_press_at_home_that_splits_up_from_undo_from_return               [ev: 7/7 key5]
prefer    a_direction_key_at_a_cell_where_its_two_candidates_disagree        [ev: 7/9 no_ops]
prefer    a_probe_whose_outcome_is_legible_in_the_raw_diff                   [ev: 17/17 diffs]
prefer    east_along_lattice_row_one_over_any_other_axis                     [ev: 1/1 levels]
prefer    an_unpressed_key_over_repeating_a_known_no_op                      [ev: 2/7 keys]
prefer    bumping_the_switch_before_assuming_it_cannot_be_entered            [ev: 1/1 levels]
