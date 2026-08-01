# theory.dsl -- world observed for 18 states / 17 transitions
# (RESET, then A1 A2 A3 A4 A5 A2 A5 A1 A3 A2 A5 A2 A4 A5 A2 A5 A1).
# 79 cells have ever changed; this manual names and owns all 79.
# No new command was executed this round. The only new evidence is
# certify's own numbers, and they turned out to be worth more than a
# command.
#
# ================= WHAT HAPPENED SINCE THE LAST MANUAL =================
#
# 1. THE PIXEL AND THE DATE WERE EXACTLY RIGHT. Last round I wrote, in
#    advance: 'I predict certify will report first_divergence at t13,
#    cell (63,57)'. Certify reports first_divergence at transition index
#    12 -- which is t13 in my numbering, RESET being t0 -- arc_action
#    ACTION4, one cell wrong, (63,57), manual_says 1, world_says 9. That
#    is the misfire of meter_burn_next_key4, named, dated and priced two
#    rounds before it fired.
#
# 2. AND THE COUNT WAS WRONG, 15/17 WHERE I PREDICTED 13/17, AND THAT
#    GAP IS THE WHOLE FINDING OF THE ROUND. I had assumed replay
#    re-synchronises to the observed frame before every transition, so I
#    counted four independent one-pixel errors: two misfires (t13, t15)
#    and two missed burns (t14, t16). Certify says two. The only model
#    that gives exactly two is CUMULATIVE replay -- the predecessor of
#    each replayed transition is the manual's OWN previous predicted
#    frame. Under that model a premature burn HEALS the moment the world
#    catches up, and I re-simulated all seventeen transitions by hand and
#    got 15/17 with mismatches at exactly t13 and t15 and first
#    divergence at t13 cell (63,57). See
#    replay_is_cumulative_and_a_premature_burn_heals_itself.
#
# 3. THAT REVERSES THE ARITHMETIC BEHIND THREE REFUSALS, AND ALL THREE
#    REFUSALS SURVIVE WITH BETTER NUMBERS. Deleting the burn rules is not
#    9/17, it is about 1/17, because an omission never heals. The
#    witnessed key5 burn rule, even guarded so it fires only at t14 and
#    t16, is 14/17. The panel guard on key4, which I called a 14/17 buy
#    last round, is actually 13/17 -- it repairs t13 and then leaks four
#    transitions that used to heal. The manual I already had is the best
#    of the four, and I only know that now because certify disagreed with
#    my count.
#
# 4. THE OTHER TWO CHECKS PASSED CLEAN: responsibility 0/4096 cells
#    unexplained, and unambiguous 90/90 pairs adjudicated with 0 clashes
#    over 18 states x 5 actions.
#
# 5. THE BODY IS STILL AT SPAWN AND EAST IS STILL OPEN THERE. Re-read
#    from the current frame: rows 8-12 cols 19-43 are floor, so cols
#    20-24 are a clear destination ring. ACTION4 remains the only
#    candidate for east among keys 1-5 and has still never been pressed
#    where east is open. Its price went UP this round -- see
#    the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_defect,
#    which I have corrected, because a missed body step does not heal --
#    and it is still the buy.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Dark    { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  landmark spawn_probe  # arc-cell: (8, 14)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t17 compress: 43]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t10,t11,t12,t14,t15,t16 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t11,t14,t16 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t11,t14,t16 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t10,t12,t15 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t10,t12,t15 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_edge_key2 forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_next_key2 forall ?p in Glyph9 [ev: t6,t10,t12 cov: 3/4]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key4 forall ?p in Glyph9 [ev: t4 cov: 1/2]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key1 forall ?p in Glyph9 [ev: t8 cov: 1/1]
    when act=key(1) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3,t9 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t11,t14,t16 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t11,t14,t16 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t11,t16 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t11,t16 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t11,t16 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t11,t16 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t11,t16 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t14 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t14 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t14 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t14 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t14 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 43 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4017 [status: counted]
  invariant meter_burned_cells count(Glyph9, color = 1) = 8 [status: counted at state 17, monotone]

  theorem replay_is_cumulative_and_a_premature_burn_heals_itself "THE FINDING OF THIS ROUND, and it came from certify disagreeing with my count rather than from the world. I predicted 13/17 with four one-pixel divergences at t13, t14, t15, t16; certify reports 15/17 with first divergence at t13, cell (63,57), manual 1 world 9. My count assumed the arm re-synchronises to the observed frame before each replayed transition. It does not. The predecessor of a replayed transition is THE MANUAL'S OWN PREVIOUS PREDICTED FRAME, and under that model I re-simulated all seventeen transitions by hand and got certify's answer exactly. The trace: t1-t12 all match, the burn key and the world agreeing cell for cell; at t13 key(4) fires meter_burn_next_key4 on (63,57) and the world does not burn -- MISMATCH, one pixel; at t14 the world burns (63,57), the manual's state already has it burned and no key5 burn rule fires, so the two frames are equal again -- MATCH; at t15 key(2) fires on (63,56) against the manual's own leading edge and the world does not burn -- MISMATCH; at t16 the world burns (63,56) and the manual re-synchronises -- MATCH; at t17 every instanced meter cell reads 1 and (63,55) has no instance, so nothing can fire and nothing is expected -- MATCH. Two mismatches, both one pixel, first at t13 cell (63,57). CONSEQUENCE, and it is a general law of this arm and not of this world: A PREMATURE CHANGE HEALS WHEN THE WORLD CATCHES UP; AN OMITTED CHANGE NEVER HEALS, because nothing in the manual ever puts back what it failed to draw. Every cost estimate in this file had to be recomputed under that asymmetry, and three of them changed sign."
    [depends: meter_burn_next_key4, meter_burn_next_key2  probe: passed]

  theorem the_row_63_error_alternates_and_a_burn_key_on_an_even_command_keeps_it_in_step "Replaces my claim that every command from here refutes the manual at row 63; that claim was computed under the resync model and is FALSE. The corrected shape. The world burns the leading edge on EVEN commands only. The manual burns whenever key 1, 2 or 4 is pressed and its own leading edge has an instance and reads 9 with a burned cell to its right. So the two clocks leapfrog and the manual is never more than one cell ahead. If an even command uses key 1, 2 or 4, the manual burns the same cell the world burns and the transition MATCHES. If an even command uses key 3 or 5, the manual misses the burn and diverges by one pixel, and that divergence heals at the next command that uses a burn key. If an odd command uses key 1, 2 or 4, the manual burns one cell early and diverges by one pixel, and that divergence heals at the next even command. If an odd command uses key 3 or 5, nothing fires and the transition MATCHES. That is the entire row-63 error budget: at most one pixel at any time, alternating, self-healing, and the sign of the error is decided by which key is pressed at which parity. WHAT THIS DOES NOT CHANGE: the leading edge that has never burned still has no instance and still cannot be drawn by any construction in this DSL, so an even command that opens a fresh cell is a one-pixel miss whatever key is pressed -- but the miss now costs one transition rather than all of them, because the next burn key repairs it. A DIVERGENCE SET CONSISTING ONLY OF ROW 63 STILL DOES NOT IMPLICATE THIS MANUAL, and it has now consumed seven rounds."
    [depends: replay_is_cumulative_and_a_premature_burn_heals_itself, i_cannot_draw_the_leading_edge_burn  probe: passed]

  theorem three_refusals_recomputed_and_all_three_survive "Under the resync model I refused three patches with numbers that were wrong. Recomputed under cumulative replay, all three refusals stand and two of them stand much harder. (1) DELETE ALL FOUR BURN RULES: I said 9/17. It is about 1/17. With no burn rule the manual's row 63 stays at frame-0 colour 9 forever, the world's burns accumulate, and every transition from t2 onward is compared against a frame the manual can never catch up to -- the divergence grows monotonically to eight pixels. Omission is catastrophic precisely because it never heals. (2) THE WITNESSED KEY5 BURN RULE: I said 12/17. Unguarded it burns on every ACTION5 and drifts ahead of the world without bound, since ACTION5 has been pressed five times and only two of those were even commands. Guarded so that it fires only where it is witnessed -- a landmark at (63,58) and the extra literal colored(deep_meter, 1), which does separate s13 and s15 from s4, s6 and s10 -- it gives 14/17, because repairing t14 lets the key4 misfire at t13 leak forward into t14 and t15 instead of healing. I do not declare the landmark and I do not write the rule. (3) THE PANEL GUARD ON THE KEY4 BURN RULE: I said it would buy 14/17 and refused it on principle. It buys 13/17. It repairs t13 by suppressing the premature burn, which then means the manual MISSES the burn the world delivers at t14, and that omission never heals -- t14, t15, t16 and t17 all fail. The principled refusal and the arithmetic now agree, which is the first time this round that being right for the right reason and being right by the numbers coincided."
    [depends: replay_is_cumulative_and_a_premature_burn_heals_itself, i_refused_a_witnessed_key5_burn_rule_and_here_is_the_arithmetic  probe: passed]

  theorem i_refused_a_witnessed_key5_burn_rule_and_here_is_the_arithmetic "Constraint 2 says no entry without evidence; it does not say every witnessed pattern earns an entry. A rule 'when act=key(5) and colored(?p,9) and colored(rightof(?p),1) then recolored(?p,1)' has two clean witnesses, t14 and t16, and three clean counterexamples, t5, t7 and t11. Unguarded it drifts. Guarded on the meter depth it reaches 14/17 against the 15/17 I already have. I record the refusal rather than the rule so that the next desk does not rediscover it as a gain, and I now record the correct number beside it."
    [depends: the_meter_is_a_two_command_clock  probe: passed]

  theorem dynamic_census "Exactly 79 cells have ever changed and every one has an owner; certify confirms it independently this round with cells_unexplained = 0 over all 4096. 23 are the panel: slot 1's eight ring pixels at rows 1-3 cols 1-3, its centre (2,2) being colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in configuration A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 8 are the burned right end of row 63, cols 56 to 63, burned in order 63,62,61,60,59,58,57,56 at commands 2,4,6,8,10,12,14,16. 23+24+24+8 = 79 = dynamic_cells. By frame-0 colour: 43 colour-9, 9 colour-1, 24 colour-5, 3 colour-0. 43+9+24 = 76 = cells_needing_an_owner exactly, the store declining to count background-coloured cells; Dark carries the remaining 3 anyway. 4096-79 = 4017 = constant_cells exactly."
    [probe: passed]

  theorem the_state_model_predicted_the_duplicate_count "Corroborated a second time from a number I did not fit. A state is exactly three things: which of two lattice cells the body occupies, which of two configurations the panel shows, and how many meter cells are burned. Burns at s_k are floor(k/2). Body: spawn spawn (2,2) (2,2) (2,2) spawn (2,2) spawn spawn spawn (2,2) spawn (2,2) (2,2) spawn (2,2) spawn spawn. Panel: A A A A A B B A A A A B B B A A B B. Exactly five pairs coincide -- s0=s1, s2=s3, s8=s9, s12=s13, s16=s17 -- which predicts 18-5 = 13 distinct states. The store reports distinct_states = 13. Any mechanism I am missing that varied a pixel in those eighteen frames would have broken a coincidence and pushed the count above 13; any spurious mechanism would have pushed it below."
    [depends: dynamic_census, the_meter_is_a_two_command_clock  probe: passed]

  theorem the_meter_is_a_two_command_clock "8 out of 8 and 9 out of 9 and I consider it closed. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right end. Burns occurred at commands 2,4,6,8,10,12,14,16 and at no other command. The key pressed is irrelevant and every key pressed at both parities says so: ACTION1 burned at 8 and not at 1 or 17, ACTION2 burned at 2,6,10,12 and not at 15, ACTION4 burned at 4 and not at 13, ACTION5 burned at 14 and 16 and not at 5, 7 or 11. ACTION3 has only ever been pressed at odd indices. Cols 56-63 are spent, 56 cells remain, so roughly 112 commands remain before the bar is out. The next command is index 18, which is EVEN, and it will burn (63,55) whatever is pressed."
    [depends: meter_burn_next_key1, meter_burn_next_key4  probe: passed]

  theorem no_frame_function_can_predict_the_burn_and_five_identical_pairs_prove_it "A proof about my own form, not a guess. Group the eighteen commands by the burn count b visible at their start: exactly two commands share each b, the odd one k=2b+1 which does not burn and the even one k=2b+2 which does. For b = 0, 1, 4, 6 and 8 the two starting frames are PIXEL-IDENTICAL. So for five of the nine burn counts there is no function of the frame whatsoever that can output burn for one and no-burn for the other. The world is driven by a command counter that is drawn nowhere. What is NOT proven is that the world fails to be a function of (frame, action): each of those five pairs was given two different keys, so a table memorising the burn count per key survives the record. That table would need one clause per burn, compress nothing, and predict nothing about command 18. CONSEQUENCE I ACCEPT: my manual is required by constraint 5 to be a function of (frame, action), so it is required to be wrong about this world's meter, and the only open question is where I choose to be wrong -- and this round's arithmetic finally tells me where, which is early rather than never."
    [depends: the_meter_is_a_two_command_clock, replay_is_cumulative_and_a_premature_burn_heals_itself  probe: passed]

  theorem i_cannot_draw_the_leading_edge_burn "A law of this manual rather than of this world, now paid eight times. The arm instances exactly the cells that have ALREADY changed, so the next cell to burn is board, has no instance, and NO RULE OF MINE CAN RECOLOUR IT. I checked whether any declaration escapes this: arc-instances: all covers only cells the board cannot explain, so it never reaches a static cell; a landmark can be named at (63,55) but landmarks are cells, not objects, and every event in the language takes an object as its first argument. There is no construction in this DSL that draws a cell before its first change. What the cumulative-replay finding adds: the cell acquires an instance in the NEXT round's level, so the miss is repaired by the following burn key rather than being permanent."
    [depends: the_meter_is_a_two_command_clock, replay_is_cumulative_and_a_premature_burn_heals_itself  probe: passed]

  theorem the_probe_designer_is_blind_to_the_commands_worth_buying "Every hypothesis in the frontier is my manual or an ablation of it. Two ablations differ in their prediction ONLY on a command where some rule fires. So expected information gain is maximised exactly where my manual already fires most rules, and is exactly zero on every command my manual says nothing about. Commands 14, 15 and 16 were the three highest-rule-count commands on the board, each already at full coverage, two of them explicitly pruned by my playbook; command 17 was a silence already witnessed twice. Meanwhile ACTION4 where east is open, ACTION6 and ACTION7 have expected gain 0.000 by construction, and they are the only three commands that could tell me something I do not know. THE TRAP IS STRUCTURAL: a frontier built by deleting rules cannot represent 'a rule I am forbidden to write because it has no witness'. THE ONLY INSTRUMENT THAT WORKS ON THOSE COMMANDS IS THE RAW DIFF. My manual predicts ZERO changed cells outside row 63 for all three, so any non-empty diff elsewhere is legible without any frontier. WHAT WOULD OVERTURN THIS: a probe report showing non-zero expected bits for a command where no rule of mine fires."
    [depends: the_row_63_error_alternates_and_a_burn_key_on_an_even_command_keeps_it_in_step  probe: pending]

  theorem the_world_is_not_a_function_of_the_drawn_frame_and_one_repeat_would_prove_it "s16 and s17 are PIXEL-IDENTICAL -- body at spawn, panel B, eight burns. From s16 the world was given ACTION1 and changed nothing. The body stands on s17 now. Give it ACTION1 again at command 18, which is even, and the clock says (63,55) burns: identical state, identical action, different successor, hidden state proven rather than argued. I RANK IT LOW AND SAY WHY: constraint 5 obliges my manual to be a function of the frame, so I already know I must be wrong about one member of that pair; the divergent pixel is the leading edge I cannot draw in any case; and the finding changes no rule and opens no cell."
    [depends: no_frame_function_can_predict_the_burn_and_five_identical_pairs_prove_it  probe: pending]

  theorem the_down_key_may_be_a_shuttle_and_five_presses_have_all_been_from_spawn "STILL THE LARGEST UNEXAMINED ASSUMPTION IN THIS FILE. ACTION2 has been pressed five times and every one was from spawn; ACTION5 five times and every one from (2,2). Not once has either been pressed anywhere else. Two readings survive. READING DOWN: ACTION2 moves the body one lattice cell south wherever it stands, ACTION5 one north, and the maze theorem is about a maze. READING SHUTTLE: ACTION2 means go to cell two and ACTION5 means go back to cell one, the world is a two-cell rocker, and the lattice, the comb and the socket are scenery. The press that decides it is ACTION2 from (2,2), which costs TWO commands from here. Lattice (3,2) is rows 20-24 cols 14-18, floor in the current frame, and separator row 19 is floor across cols 13-31, so the destination ring is clear. WHAT MY MANUAL PREDICTS FOR THE SECOND PRESS: nothing except a meter burn -- key2_body_leaves ranges over Glyph9 and the body would stand on Vacated cells, key2_body_arrives ranges over Vacated and rows 20-24 are board with no instances. If the body moves I am wrong by 48 cells and, under cumulative replay, wrong by them on every subsequent transition until I write the rule."
    [depends: key2_body_leaves, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_action_map_after_seventeen_transitions "WITNESSED, with the negatives stated as negatives. ACTION2 CARRIES THE BODY SOUTH FROM SPAWN: t2, t6, t10, t12, t15, the 5x5 ring from rows 8-12 to rows 14-18, five times, in both panel configurations. ACTION5 CARRIES IT BACK NORTH: t5, t7, t11, t14, t16, five times, each with a panel toggle. NEGATIVES AT SPAWN, where north and west are void and south and east are open floor: ACTION1 did nothing at t1, t8 and t17, ACTION3 did nothing at t9 -- so NEITHER ACTION1 NOR ACTION3 IS EAST, and both are consistent with being north or west. NEGATIVES AT (2,2), where north and south are open and east and west are void: ACTION3 did nothing at t3, ACTION4 did nothing at t4 and t13 -- so neither is up and neither is down, and both are consistent with being horizontal. Combine: ACTION3 is neither vertical nor east, which leaves west, and west is void at both cells it has been pressed from. ACTION4 IS STILL THE ONLY REMAINING CANDIDATE FOR EAST AND HAS STILL NEVER BEEN PRESSED WHERE EAST IS OPEN -- and the body stands where east IS open, rows 8-12 cols 19-43 reading floor in the current frame. The residue: ACTION1 is consistent with up and so is ACTION5, and two up keys is a smell; one press of ACTION1 from (2,2) separates them."
    [depends: key2_body_arrives, key5_body_respawns  probe: pending]

  theorem action5_is_up_or_home_or_undo_and_a_third_cell_separates_them "Five witnesses and all five moved the body from (2,2) to spawn, a move that up, return-home and undo-last-move predict identically. The separator is a shape, not a route: stand two lattice steps from spawn and press ACTION5 once. Up predicts one step back; home predicts a jump of two cells; undo predicts one step back along the arrival direction, which differs from up as soon as the last step was horizontal. My rules encode none of the three: key5_body_respawns is guarded on PIXELS, a Glyph9 cell rendering 5 whose neighbour above renders 5, so it is a spawn-ring refill rule and nothing more. As written it fires from ANY state where the spawn ring reads floor, so from a third cell my manual predicts the body is DRAWN AT SPAWN WITHOUT BEING ERASED where it stood: two bodies, 24 wrong pixels, priced here in advance."
    [depends: key5_body_respawns, the_action_map_after_seventeen_transitions  probe: pending]

  theorem the_spawn_probe_guard_is_now_one_press_from_being_tested "Thirteen rules carry colored(spawn_probe, 5), which reads 'the body is not at home'. All five ACTION5 witnesses had the body one cell south, so the guard has never been tested with the body home: ACTION5 has never been pressed at spawn in eighteen states. THE BODY IS AT SPAWN RIGHT NOW, so the test is one press. My manual predicts ZERO changed cells for ACTION5 here -- the panel rules are gated off by the guard, key5_body_clears finds no Vacated cell rendering 9, key5_body_respawns finds no Glyph9 cell rendering 5 -- so any change at all is legible in the raw diff. If the panel toggles anyway, thirteen rules are guarded on the wrong thing and I under-predict 23 pixels which, under cumulative replay, stay wrong until repaired; if the body jumps somewhere, ACTION5 is not up at all."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: pending]

  theorem the_panel_is_a_two_slot_selector_toggled_by_action5 "Both directions witnessed five times between them, A to B at t5, t11 and t16 and B to A at t7 and t14, and the current frame re-read pixel by pixel is configuration B. A: slot 1's ring reads 9 with underline 1 reading 9, slot 2 reads solid 1 with underline 2 reading 0. B: slot 1's ring reads 2 with underline 1 reading 0, slot 2 reads a ring of 9 with its centre hollowed to 0 and underline 2 reading 9. THE READING: two slots, an underline under each, and the underlined slot is also the one rendered in colour 9 -- a two-item selector whose cursor ACTION5 advances, wrapping after two. WHAT I DO NOT CLAIM: what the selection selects. ACTION2 moved the body identically from configuration A at t2, t10 and t15 and from configuration B at t6 and t12, and ACTION4 was inert in configuration A at t4 and in configuration B at t13 -- five cross-configuration comparisons and not one difference in net effect. If the selection matters at all it matters to a key never pressed, which is ACTION6 or ACTION7."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, key5_underline2_dims  probe: passed]

  theorem the_goal_is_absent_because_no_instance_can_name_the_socket "I decline a goal clause for a fifth time and accept the price rather than pretending it away. The winning position I believe in is lattice cell (8,7), rows 50-54 cols 44-48, whose 24 ring pixels read floor and whose centre (52,46) is a lone colour-9 pip inside a three-sided colour-9 bracket. Four forms of goal are available and every one is refuted. (1) Cart.pos = exit_cell needs ONE named instance; arc-instances: all gives me Glyph9_r8c14 and forty-two siblings and there is no instance called Glyph9, and a second colour-9 type would be indistinguishable to an arm that looks objects up by colour alone. (2) A count over the socket interior has nothing to range over: those cells have never changed, so they are board. (3) Counts over the four types I have are either true in some observed state -- count(Vacated, color = 9) = 0 holds in eleven of eighteen -- or false everywhere and unreachable, like count(Spent, color = 0) = 9, which is exactly the fake goal that is worse than none. I also rejected count(Glyph9, color = 1) = 64: it says 'the clock has run out', so a planner given it would race to lose. (4) The goal cannot be conjunctive; the section takes one equation. THE PRICE: is_goal compiles to False, plan returns no_goal_declared, commit never runs, and all eighteen commands have been probes. THE OBSERVATION THAT ENDS THIS: a goal becomes writable the moment any pixel of the bracket rows 49-55 cols 43-49, or the pip (52,46), or any colour-8 pixel of the comb changes colour. THE GOAL IS DOWNSTREAM OF REACH, REACH IS DOWNSTREAM OF THE EAST KEY, AND THE EAST KEY IS ONE PRESS AWAY."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_action_map_after_seventeen_transitions  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 ring with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2 plus a one-row fragment at row 48 cols 42-50 that cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in eighteen frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it stands at (1,2) now. THIS THEOREM IS HOSTAGE TO ONE PRESS: if the body cannot leave those two cells, there is no maze, only a rocker."
    [depends: key2_body_arrives, the_down_key_may_be_a_shuttle_and_five_presses_have_all_been_from_spawn  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed ten times: (16,16) stayed 5 at t2, t6, t10, t12 and t15 while its 24 neighbours turned 9, and (10,16) did the same in reverse at t5, t7, t11, t14 and t16. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_cannot_be_stood_on_and_that_is_why_the_east_walk_ends_in_a_bump "Read off the current frame. Lattice (1,6) is rows 8-12 cols 38-42; the knob is a solid 3x3 colour-8 block at rows 9-11 cols 39-41, precisely the centre 3x3 of that cell. A body is 5x5 minus its centre pixel, so eight of its 24 ring pixels would have to overlap colour 8: by the aperture reading, (1,6) is NOT enterable, and only its exact centre is free. The four cells (1,2) to (1,5) are clear floor. So if ACTION4 is east, the body can walk C=2,3,4,5 and then meet the knob head-on. That is either a dead end or the intended interaction, and the two are distinguished by one pixel: any colour-8 pixel changing. Not one colour-8 pixel has moved in eighteen frames, so colour 8 is board and no object owns it."
    [depends: the_maze_is_a_six_pixel_lattice, the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 50-54. Rows 49 and 55 are separator rows and cols 43 and 49 separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side left as floor. Inside it, rows 50-54 cols 44-48 are floor except the lone colour-9 pixel at the exact centre (52,46). Overlay the body standing there -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel. The bracket has not changed in eighteen frames, so it is board; the first time any of it changes, those cells become dynamic and the goal section can finally be written."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn under the DOWN reading and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem at col 40 running from row 12 to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18 with floor gaps only at (39,14) and (41,14). ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. The first colour-8 pixel that changes turns this theorem into physics and hands me both a rule and a goal."
    [depends: the_maze_is_a_six_pixel_lattice, the_knob_cannot_be_stood_on_and_that_is_why_the_east_walk_ends_in_a_bump  probe: pending]

  theorem two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Eighteen commands and TWO OF SEVEN ACTIONS HAVE NEVER BEEN TRIED ONCE. In this action family one of them is normally a click carrying coordinates, and that matters here: the knob is a 3x3 target the body provably cannot stand on, and the panel is a two-item selector whose selection provably changes nothing for the five keys already tried. I cannot write a click rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT and never its precondition. My manual predicts ZERO cells for both keys, so any change is legible in the raw diff, and certify adjudicates five actions rather than seven, which means those two columns of the transition table are unexamined rather than clean."
    [probe: pending]

  theorem the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_defect "CORRECTED THIS ROUND AND THE PRICE WENT UP. The arm instances exactly the cells that have already changed, so any lattice cell the body has never entered is board and has NO instance. An east step from spawn to (1,3) costs 24 undrawable arrival pixels at rows 8-12 cols 20-24, plus 24 departure pixels at the spawn ring which NO rule of mine erases -- key2_body_leaves is guarded on the pixel six rows BELOW rendering 5, which is a southward move and nothing else. WHAT I GOT WRONG BEFORE: I said 48 wrong pixels on the first east step, 24 on the second, 0 thereafter, which assumed replay resynchronises. It does not. A missed MOVE never heals, so the manual's body would stay at spawn while the world's walks away, and EVERY subsequent transition would be replayed from a frame that is 48 cells wrong. The realistic cost of buying the east press is therefore one transition wrong immediately and every later transition wrong until the repair, and THE REPAIR IS AVAILABLE NEXT ROUND: the moment those cells change they become dynamic, acquire instances typed Vacated by their frame-0 colour 5, and both halves of an east rule become writable with a witness. One round of tuition, not permanent damage -- but it is tuition paid in the replay score, and I say so before spending it."
    [depends: the_maze_is_a_six_pixel_lattice, replay_is_cumulative_and_a_premature_burn_heals_itself  probe: pending]

  theorem silence_is_a_prediction_and_four_of_seven_silences_at_spawn_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says 'I do not know', it says 'nothing happens', in the same voice it uses for things it has seen. Audit the seven actions at spawn, where the body stands. key(1): inert, WITNESSED three times, t1 t8 t17 -- settled. key(2): carries the body south, witnessed five times -- settled. key(3): inert, WITNESSED once at t9. key(4): NO WITNESS HERE, and this is the east question. key(5): NO WITNESS HERE, and this is the guard shared by thirteen rules. key(6) and key(7): NO WITNESS ANYWHERE. So four of seven silences at this cell are forged death certificates, and the two most valuable presses on the board are among them."
    [depends: the_action_map_after_seventeen_transitions, the_spawn_probe_guard_is_now_one_press_from_being_tested  probe: pending]

  theorem the_cascade_length_is_a_free_channel_and_it_keeps_paying "ACTION2 returned 7 frames from configuration A at t2, t10 and t15, and 9 frames from configuration B at t6 and t12 -- five for five on a split I predicted three rounds ago. ACTION5 returned 9 frames all five times, in both directions of the toggle, and every no-op returned 1. So the animation length is not a function of the key alone and the panel configuration is the one correlate with a witness. It is also NOT a function of the burn: t4 burned with 1 frame and t2 burned with 7. This is hidden state I discard by construction, since cascade single_frame compares only net effect, and it is the ONLY evidence I have that the panel configuration changes anything at all. It costs nothing in replay and buys nothing in prediction; I keep reading it because it is free."
    [depends: the_panel_is_a_two_slot_selector_toggled_by_action5  probe: passed]

  theorem the_no_op_rule_fails_the_gain_test_and_i_keep_it_for_a_narrow_reason "key3_inert_below_spawn recolours one pixel to the colour it already has, has two witnesses on transitions where zero cells changed, and replay is identical without it. It explains no pixel and lengthens the manual, so it fails constraint 3 and I say so rather than dressing it up. The reason I keep it: it is the ONLY occurrence of act=key(3) in the file, and deleting it narrows the action set certify adjudicates from five keys to four -- certify confirms it adjudicated 18 x 5 = 90 pairs. Note what that implies about keys 6 and 7, which appear nowhere: five of seven columns are covered and the two missing ones are unexamined rather than clean."
    [depends: key3_inert_below_spawn, two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap  probe: passed]

  theorem the_rules_are_pairwise_exclusive_and_off_board_cell_terms_are_false "Constraint 5, re-checked by hand over all four instance types in both panel configurations, and certify reports 0 clashes over 90 adjudicated pairs with no call to step raising. Under key(2): body_leaves needs below-six to render 5, which is off-board and therefore false for any row past 57, so it cannot fire on a meter cell; the two burn rules split on rightof = wall against a colour test on rightof, which cannot both hold. Under key(5) the type Glyph9 is split five ways by COLOUR FIRST -- 5 for respawns, 9 for the two dim rules, 2 for slot1_lights, 0 for underline1_lights -- and colours 2 and 0 occur on no other Glyph9 cell in any observed state; no meter cell ever renders 5, so respawns cannot reach row 63. The two colour-9 rules are split by above-four: slot1_dims needs it to BE WALL, true only for rows 0-3; underline1_dims needs a COLOUR TEST on it, which is false off-board rather than raising, so it selects row 5, and its above-six wall test excludes the meter at row 63. Spent splits by colour into 1 against 9 and 0; within colour 1 the geometry is row 1 by above-two wall, row 3 by a colour test on above-two, row 2 by above-three wall plus a colour test on above-one, and within row 2 col 5 by leftof-six wall, col 6 by leftof-seven wall plus a colour test on leftof-one, col 7 by a colour test on leftof-two. Dark splits by colour 0 against 9. Not one rule uses not, deliberately."
    [depends: key2_body_leaves, key5_slot2_centre_darkens, key5_slot1_lights  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me, and last round's version half-cost me: the pixel and the date were right and the count was wrong, which is how the cumulative-replay finding was bought. STATE: body at spawn, rows 8-12 cols 14-18 rendering 9 with the aperture (10,16) rendering 5; panel configuration B; eight meter cells burned at row 63 cols 56-63; next command index 18, which is EVEN, so the clock burns (63,55) whatever is pressed. CERTIFY AFTER COMMAND 18, and this is now a sharp two-way prediction rather than a hedge. If command 18 uses key 1, 2 or 4: the level rebuilds with (63,55) instanced, the burn rule fires on it, the world burns it too, and t18 MATCHES -- replay 16/18, divergences still exactly t13 and t15, first_divergence still t13 cell (63,57). If command 18 uses key 3 or 5: the manual misses the burn -- replay 15/18 with a new divergence at t18, cell (63,55), manual_says 9 world_says 1, which will heal at the next command that uses key 1, 2 or 4. If instead certify reports anything that is not one of those two shapes, the cumulative-replay model is wrong and this whole round must be re-read. ACTION4 HERE, my first choice: my manual predicts ZERO cells outside row 63 and has NO WITNESS for that silence at this cell. If the body steps east to (1,3) I pay 48 undrawable pixels immediately and on every later transition until I write the east rules next round, ACTION4 is east, the maze is real, and lattice row 1 opens toward the knob. If nothing moves, the last candidate for east among keys 1-5 is eliminated and east belongs to key 6, key 7 or to nothing. ACTION5 HERE: predicted zero, never pressed at spawn, tests the guard carried by thirteen rules. ACTION6 or ACTION7: predicted zero, never pressed anywhere, and the only keys that could give the selector something to select. ACTION1 HERE: predicted zero, witnessed zero three times. ACTION2 HERE: 48 cells I draw correctly and nothing learned. THE SINGLE OBSERVATION THAT WOULD MOST CHANGE THIS FILE is unchanged: any colour-8 pixel of the comb or the wire changing."
    [depends: the_row_63_error_alternates_and_a_burn_key_on_an_even_command_keeps_it_in_step, the_action_map_after_seventeen_transitions  probe: pending]

  theorem what_the_engines_gave_me "No new frames this round, so the engine stream is the same stream and I re-read it rather than re-mine it. mdl_segmenter's ten-track unsplit variant reports gain +628 bits, split-by-colour stays catastrophic at -56428, and I take its TRACK LIST and not its verdict. obj0 (colour 9, eight cells, 3x3, all eighteen frames) and obj2 (colour 9, 1x3, all eighteen frames) are slot 1's ring and underline 1 persisting through all five toggles, which corroborates a marker with two seats rather than two objects. The birth frames of the transient tracks are 5, 7, 11, 14 and 16 -- EXACTLY my five toggle transitions, in order, from an engine that has never seen my rules -- and obj9, colour 2, present 2 frames, is slot 1 dimmed and still dim in the current frame, which is configuration B. obj4 is the whole 64-cell row-63 bar, of which 8 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body: connected_components(4) cannot see the mover, because the mover is a ring adjacent to floor on every side, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 17 transitions constrain rank 10 of 395 features -- and its one global law is my census cell for cell, a consistency check and not a discovery. cegis_miner refuses every track again and its verdict, 'the world does not narrate as one mover', is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
