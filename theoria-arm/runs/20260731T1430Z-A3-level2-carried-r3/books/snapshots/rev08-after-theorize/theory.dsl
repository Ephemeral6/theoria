# theory.dsl -- world observed for 14 states / 13 transitions
# (RESET + A1 A2 A3 A4 A5 A2 A5 A2 A5 A2 A5 A2 A5).
# 77 cells have ever changed; this manual names and owns all 77.
#
# WHAT THIS ROUND COST AND WHAT IT BOUGHT
#
#   Four commands were spent -- A2 A5 A2 A5 -- and they moved the body
#   between the same two lattice cells it was already oscillating between.
#   Four probe_refutations fired. THEY ARE ONE DEFECT, COUNTED FOUR TIMES,
#   AND THE DEFECT IS ONE PIXEL.
#
#   Read the `inert` fields of P-05..P-08 in order: 15c2e5..., 287dc6...,
#   818eaa..., b90a62... Each one is the PREVIOUS probe's `manual` value.
#   The harness rolls MY predicted frame forward; it does not resync to the
#   world. So at t10 the manual failed to burn (63,59) -- a cell that had
#   never changed, was therefore board, was owned by no object, and could
#   not be drawn by any rule I am able to write -- and that single wrong
#   pixel then travelled through t11, t12 (where a second undrawable burn
#   at (63,58) joined it) and t13. Four refutations, two pixels, zero
#   rules implicated. Every other rule in this manual took two more
#   full-coverage witnesses and not one contradiction.
#
#   The previous manual advertised this outcome by name and by price:
#   `the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows`
#   said the next burn was at (63,59), said it was board, said it would
#   cost exactly one wrong pixel, and said no rewriting fixes it. The
#   price came in exactly. The repair is arithmetic -- (63,59) and (63,58)
#   are dynamic now, Glyph9 goes 39 -> 41, and both transitions replay --
#   and the same bill will be presented again at (63,57).
#
#   THE STRUCTURAL CONSEQUENCE IS THE FINDING OF THIS ROUND, and it is
#   about the instrument rather than the world: every meter cell burns
#   exactly once, and at the moment it burns it is still board. So no
#   burn is ever predictable in advance by this manual, every ACTION2 or
#   ACTION4 press registers as a refutation whatever else it does, and the
#   refutation channel is SATURATED. A probe desk that ranks by
#   refutation-fired will keep choosing moves that teach nothing.
#   See the_meter_edge_saturates_the_refutation_channel.

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
  Glyph9  [segment: dynamic_colour_9 ev: t0-t13 compress: 41]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t8,t9,t10,t11,t12,t13 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t9,t11,t13 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9,t11,t13 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8,t10,t12 cov: 120/120]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8,t10,t12 cov: 120/120]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8,t10,t12 cov: 4/4]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9,t11,t13 cov: 120/120]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9,t11,t13 cov: 120/120]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9,t13 cov: 24/24]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9,t13 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9,t13 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9,t13 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9,t13 cov: 9/9]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7,t11 cov: 16/16]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7,t11 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7,t11 cov: 16/16]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7,t11 cov: 2/2]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7,t11 cov: 6/6]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 41 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4019 [status: counted]
  invariant meter_cells_burned count(Glyph9, color = 1) = 6 [status: counted]

  theorem the_four_refutations_are_one_undrawable_pixel_rolled_forward "P-05 and P-07 are ACTION2, P-06 and P-08 ACTION5, and the diagnosis is arithmetic, not physics. Chain the inert fields: P-06 inert is P-05 manual, P-07 inert is P-06 manual, P-08 inert is P-07 manual. The harness rolls MY predicted frame forward and never resyncs to the world, so a divergence introduced once is carried until the run ends. The divergence was introduced at t10, where the world burned meter cell (63,59). At that moment (63,59) had never changed, was therefore board, was owned by no object, and no rule expressible in this DSL could draw it -- exactly as the previous manual stated in advance, at exactly the price it quoted. t12 added a second such pixel at (63,58). t11 and t13 introduced nothing of their own: their panel toggle is 23 cells and their body return is 48, and every one of those 71 cells was drawn correctly by rules that now carry five witnesses each. So the honest ledger for this round is TWO wrong pixels and FOUR refutation reports, and the ratio is a property of the instrument. Repair: (63,59) and (63,58) are dynamic now, Glyph9 rises 39 to 41, both transitions replay exactly, and the bill will be represented at (63,57)."
    [depends: meter_burn_key2_next, the_meter_edge_saturates_the_refutation_channel  probe: passed]

  theorem the_meter_edge_saturates_the_refutation_channel "Stated as a law of this manual rather than of this world, and it is the finding I most want on the record. Each of the 64 cells of the row-63 bar burns EXACTLY ONCE, from colour 9 to colour 1, advancing leftward. At the instant a cell burns it has never changed, so it is board, so no instance exists for it, so no rule of mine draws it. Therefore: (1) my three meter_burn rules have ZERO predictive value on the leading edge and full value on replay, which is not a contradiction but a division of labour I should not confuse with a rule that works; (2) EVERY press of a key that burns will be scored a refutation regardless of what else it teaches, so refutation-fired is no longer a signal that discriminates between commands; (3) the correct reading of a refutation is now its DIVERGENCE SET, not its hash, and where the divergence set is a subset of the bar's leading edge the manual is not implicated. Deleting the burn rules does not help -- the wrong-pixel count at the moment of the burn is identical -- and keeping them is strictly better because they make every past transition replay. I cannot repair this: `arc-instances: all` instances only cells the board cannot explain, and a cell that has never changed is exactly what the board explains."
    [depends: meter_burn_key2_next, the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows  probe: passed]

  theorem the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right. SIX burns now: (63,63) t2, (63,62) t4, (63,61) t6, (63,60) t8, (63,59) t10, (63,58) t12. Seven silences: t1, t3, t5, t7, t9, t11, t13. The current frame confirms it -- row 63 reads 9 through col 57 and 1 from col 58 to col 63. READING A, ACTION-KEYING: burns iff the key is 2 or 4. READING B, COMMAND PARITY: burns iff the command index is even. BOTH SCORE 13/13 AND NEITHER HAS GAINED A SINGLE BIT SINCE THE LAST ROUND, because the four new commands were key 2 at index 10, key 5 at 11, key 2 at 12, key 5 at 13 -- every one of them a key whose parity equals its index's parity, which is the diagonal on which the two readings are numerically identical. Thirteen commands, thirteen alignments, zero separation. THE SEPARATOR REMAINS FREE: any press whose key parity differs from its index parity settles it. The next index is 14, EVEN, so an odd key there (1, 3 or 5) separates in one command, and an even key there does not. I encode reading A because it is the only one the guard language can say -- there is no command counter and no phase pixel -- and I still expect B, because at t3 and t4 the body stood at lattice (2,2) with left and right both void, ACTION3 and ACTION4 were blocked identically, and only ACTION4 burned. Under A that is a cost attached to a key and not to an attempt; under B it is one bit of clock."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_cascade_length_is_a_free_channel_that_i_discard_by_construction "cascade_lengths are 1, 7 and 9. Sharpened to 5/5 this round and it is no longer a three-sample curiosity. ACTION2 returned SEVEN frames at t2, t8 and t12 and NINE frames at t6 and t10. The panel configuration in the state each press acted FROM: t2 from state 1 (A), t8 from state 7 (A), t12 from state 11 (A) -- seven frames; t6 from state 5 (B), t10 from state 9 (B) -- nine frames. Five for five, no exceptions: ACTION2 animates in 7 internal frames when the panel is in configuration A and 9 when it is in B. ACTION5 returned nine frames all five times regardless of configuration, and every no-op returned one. THE NET EFFECT IS IDENTICAL IN ALL FIVE ACTION2 PRESSES -- 48 body cells, rows 8-18, cols 14-18, plus one burn -- so this costs me nothing in replay and buys me nothing in prediction, and yet it is the only evidence I have that the panel does anything at all besides display. Six rows of travel at one row per frame is 7 frames with a terminal frame; the two extra frames under configuration B are two internal steps whose content I never see, because `cascade single_frame` compares only the net. I therefore record, as a limitation of my own semantics and not of the world: up to eight intermediate frames per command are discarded unread, and something distinguishable happens inside them. If the panel selects a mode, that mode's effect is either invisible in the net frame or has not yet had an occasion to show."
    [depends: key2_body_arrives, the_panel_is_a_marker_that_alternates_between_two_slots  probe: passed]

  theorem the_panel_is_a_marker_that_alternates_between_two_slots "PROVEN over FIVE toggles now -- t5, t7, t9, t11, t13 -- 23 cells every time, and ACTION2 has never touched a panel pixel in five presses. CONFIGURATION A (states 0-4, 7-8, 11-12): slot 1 at rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline at row 5 cols 1-3 lit 9; slot 2 at rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline at row 5 cols 5-7 dark 0. CONFIGURATION B (states 5-6, 9-10, 13, and the current frame, which reads 222/2.2/222 at cols 1-3 and 999/9.9/999 at cols 5-7 with row 5 dark at 1-3 and lit at 5-7): slot 1 is a hollow colour-2 ring with underline dark; slot 2 is a hollow colour-9 ring with dark centre and underline lit. mdl_segmenter corroborates this independently and by frame index: its colour-1 nine-cell tracks are obj1 (frames 0-4), obj6 (7-8), obj8 (11-12) and its colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13) -- A,B,A,B,A,B read off an engine that has never seen my rules. Its obj0 (colour 9, eight cells, 3x3, present in all 14 frames) and obj2 (colour 9, 1x3, all 14) persist while it narrates ten MOVE events: the hollow ring and the lit underline do not appear and vanish, they TRAVEL between slot 1 and slot 2. So the panel is one marker with two seats and colour 9 marks the occupied seat. What the seats HOLD is still unknown and I will not guess. I cannot model it as a moving marker either: the arm gives one instance per cell and moved(o, dir) moves one cell, so an eight-pixel ring travelling four columns is not expressible as a move, and ten recolour rules are the shortest thing this DSL can say."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: passed]

  theorem why_i_keep_the_spawn_probe_guard_on_a_window_that_still_cannot_test_it "Unchanged in kind, stronger in count, and now the cheapest open question on the board. The guard `colored(spawn_probe, 5)` has FIVE positive witnesses (t5, t7, t9, t11, t13 -- body away, panel toggled) and STILL NO NEGATIVE ONE, because ACTION5 has never once been pressed with the body at home. Every ACTION5 in this window immediately followed an ACTION2, so ACTION5 was pressed and the body was away from spawn are the same event five times over and no guard can be credited over the other. By the letter of no-entry-without-gain the atom is still unearned. I keep it because dropping it changes no replay and because the body is at spawn RIGHT NOW: with the guard my manual predicts SILENCE for an ACTION5 pressed here, without it a 23-cell toggle. Silence is the prediction I want on the record. Note what one such press would settle at once: the guard, the meter parity (key 5 is odd, index 14 is even, so reading A predicts no burn and reading B predicts a burn at (63,57)), and the identity of ACTION5 (UNDO would return the body to (2,2) for 48 cells, while UP and RETURN both predict no motion from spawn). Three open questions, one command, and my manual's stake is a bare prediction of zero changed cells."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, what_action5_is_and_the_two_cell_experiment_that_names_it  probe: pending]

  theorem the_action_map_after_thirteen_transitions_and_the_standard_mapping_hypothesis "WITNESSED: ACTION2 IS DOWN, 5/5, six rows south, one lattice cell, at t2, t6, t8, t10, t12. ACTION5 returns the body from lattice (2,2) to (1,2), 5/5. NEGATIVE INFORMATION, and I state it as negative because that is all it is. At spawn (1,2) up and left are void while down and right are open floor, and ACTION1 did nothing at t1 -- so ACTION1 IS NEITHER DOWN NOR RIGHT. At (2,2) the body had just vacated rows 8-12 so UP WAS OPEN, and rows 20-24 cols 14-18 are floor so DOWN WAS OPEN, while left (cols 8-12) and right (cols 20-24) are void; ACTION3 and ACTION4 each did nothing there -- so NEITHER IS UP AND NEITHER IS DOWN. One assignment survives that invents nothing: ACTION1 up, ACTION2 down, ACTION3 left, ACTION4 right, ACTION5 something else. It explains every no-op as a blocked move and it is the conventional mapping for this action family, which is a prior and not evidence. FOUR COMMANDS WERE SPENT THIS ROUND AND NOT ONE OF THEM TOUCHED THIS QUESTION -- the map is exactly as constrained as it was at state 9. THE CHEAP TEST IS STILL ONE PRESS: the body stands at spawn, where left is void and right is open floor, so ACTION4 pressed here either steps six columns east or does not, and either answer names the east key -- if ACTION4 does not move, ACTION3 is east by elimination, since ACTION1 is already excluded from east by t1."
    [depends: key2_body_arrives, key5_body_respawns, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem what_action5_is_and_the_two_cell_experiment_that_names_it "Three readings survive all FIVE ACTION5 presses because all five were made from exactly one cell south of spawn, where they are indistinguishable: UP (move one cell north), UNDO (revert the last move), RETURN (jump to spawn from anywhere). They separate the moment the body is somewhere else, and they separate differently by axis. FROM SPAWN ITSELF, which is where the body is now: UP predicts no motion (north of spawn is void), RETURN predicts no motion (already home), UNDO predicts 48 cells back to (2,2) -- so one press here splits UNDO from the other two for free. Two cells EAST at lattice (1,4): UP no move, UNDO one cell west to (1,3), RETURN spawn at (1,2) -- three different diffs, all legible in the raw pixel count, which is the full separation. Two cells SOUTH at (3,2): UP and UNDO both predict (2,2) and only RETURN separates. So the eastward route answers this question completely and the southward route does not, which is one more reason to go east first. Note the coupling I cannot yet break: the panel toggles on every effective ACTION5, five for five, so whatever ACTION5 is, the panel is its counter or its selector -- and the 7-versus-9 cascade result says the panel's state is not merely cosmetic."
    [depends: the_panel_is_a_marker_that_alternates_between_two_slots, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_cascade_is_animation_and_one_press_is_one_lattice_cell "A move is animated one row per internal frame and the world reports the whole animation for a single action; `cascade single_frame` compares only the net effect, which is identical for all five ACTION2 presses (48 body cells, rows 8-18, cols 14-18) regardless of whether the command took 7 frames or 9. The refutation I keep: under a slide-until-blocked reading, ACTION2 at spawn would have run the body south through rows 20-24 and 26-30 to the comb; it stopped after exactly six rows over open floor, FIVE times. ONE PRESS IS ONE LATTICE CELL, 5/5, and every distance in the playbook rests on that."
    [depends: key2_body_arrives, the_maze_is_a_six_pixel_lattice  probe: passed]

  theorem the_world_may_still_not_be_a_function_of_the_drawn_frame "Carried as a belief and NOT proven in this window. To prove it I need two pixel-identical states from which the SAME action produced different successors; I have no such pair, and distinct_states is 12 against 14 states, so two coincidences exist but neither is followed by the same key. What keeps the belief alive is the parity reading of the meter, which if true IS one bit of hidden state that flips every command and that no guard in this language can read, because no guard can read anything that is not a pixel. What now strengthens it is the cascade length: ACTION2 took 7 frames or 9 depending on a panel configuration that the net frame records but that my rules never consult, which is the same shape of dependence one step less hidden. Operationally it matters in exactly one way: if parity wins, every burn rule I can write is an approximation with a known error rate, and I would rather say that once than rediscover it."
    [depends: the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break, the_cascade_length_is_a_free_channel_that_i_discard_by_construction  probe: pending]

  theorem the_manual_heals_one_step_behind_and_the_meter_is_where_it_shows "The arm instances exactly the cells that have ALREADY changed, typed by their frame-0 colour: constant 4019 + dynamic 77 = 4096, and 41+24+9 = 74 = cells_needing_an_owner with the 3 colour-0 cells making up the difference to 77. Consequence: a cell that has never changed is board, no object owns it, and NO RULE CAN DRAW ITS FIRST CHANGE. This round is the second consecutive round in which that sentence, written in advance, was the entire content of every refutation. meter_burn_key2_next now replays t6, t8, t10 and t12 perfectly, because by replay time all four burned cells are dynamic; it will still miss the SEVENTH burn at (63,57), because that cell is board today. The same arithmetic prices the first eastward step: rows 8-12 cols 20-24 have never changed, so 24 arrival pixels are undrawable no matter what rule I write, and the 24 departure pixels are undrawable too until an east-leaves rule is witnessed. 48 wrong cells for the first step onto fresh ground, 24 if I already had the leaves rule, 0 for the second step. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated at rows 14-18 -- because typing is by frame-0 colour and all that floor was 5."
    [depends: key2_body_arrives, dynamic_census  probe: passed]

  theorem dynamic_census "Exactly 77 cells have ever changed and every one has an owner. 23 are the panel: slot 1's eight ring pixels, its centre (2,2) being colour 0 in BOTH configurations and therefore board; underline 1's three; slot 2's nine, centre included because (2,6) is 1 in A and 0 in B; underline 2's three. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 6 are the burned right end of row 63: cols 58 through 63. 23+24+24+6 = 77 = dynamic_cells. By frame-0 colour: 41 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 6 meter), 9 colour-1 (slot 2 solid), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 41+9+24 = 74 = cells_needing_an_owner exactly. zero_space's global-law cell list is the same 77 cells -- it lists (2,1) and (2,3) but not (2,2), (10,14),(10,15),(10,17),(10,18) but not (10,16), and all six burned bar cells -- and its single global law restates this census and nothing more."
    [probe: passed]

  theorem the_rules_i_still_have_no_witness_for_and_will_not_write "Three holes, each with its text ready so that the transition that witnesses it costs one paste and not one round of rediscovery. (1) A SECOND DESCENT. The body has descended five times and all five started at spawn, so no rule of mine turns Vacated pixels from 9 back to 5 on an ACTION2: rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below-six(?v), 5) then recolored(?v, 5). One ACTION2 from lattice (2,2) buys it, and four commands this round each had the chance and none took it. (2) EAST-WEST MOTION. Whatever the east key turns out to be, it needs a pair: a leaves rule over Glyph9 guarded on colour 9 with rightof-six rendering 5, and its arrives twin typed on whichever object owns the destination pixels -- which today is NO object, because rows 8-12 cols 20-24 are board. (3) A SEVENTH BURN AT A CELL THAT IS STILL BOARD, which is not a missing rule but a missing instance and cannot be written at all. I state the price of all three in advance so it cannot be mistaken for a surprise: the first eastward step costs 48 wrong cells plus one if the bar burns, the first second-descent costs 24, and every fresh burn costs 1."
    [depends: key2_body_arrives, the_meter_edge_saturates_the_refutation_channel  probe: pending]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth below is row 69. So colored(off-board, k) is false rather than an exception, and `<cell> = wall` is the sanctioned positive test. Thirteen of the twenty rules rest on this and every row and column discrimination in the panel is built from it: the k-th above is off-board exactly when k exceeds the row, so row 1 is above-twice equals wall, row 3 is a colour test on above-twice -- false for row 1 precisely because a colour test on an off-board cell is false -- and row 2 is above-three equals wall conjoined with a colour test on above-once. The same trick separates slot 2's middle row by column: col 5 is leftof-six equals wall, col 6 is leftof-seven equals wall with a colour test on leftof-once, col 7 is a colour test on leftof-twice, pairwise exclusive, which is why the ambiguity check reports 0 clashes over 30 adjudicated pairs. Not one rule uses `not`, deliberately. The eight A-to-B slot-2 and underline rules could collapse to two if I could write that not all four neighbours are colour 1, and I decline to gamble a whole round's compile on discovering whether `not` before an equality atom parses. If a future desk wants the shorter form, try it on ONE rule, not on eight."
    [depends: key2_body_leaves, key5_slot2_centre_darkens  probe: passed]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Re-read from the CURRENT frame and unchanged: R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open, C=6 holds the knob, C=7 does not exist (col 44 is void in this band); R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2, plus a fragment of floor at cols 42-50 in row 48 alone which cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are all open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6. Spawn is (1,2); in fourteen frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it has been at spawn in eight of them."
    [depends: key2_body_arrives, the_cascade_is_animation_and_one_press_is_one_lattice_cell  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed FIVE times: (16,16) stayed 5 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket, verified again against the current frame: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 50-54, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7) -- rows 50-54 cols 44-48, aperture at (52,46): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in fourteen frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and I have re-read every pixel of it in the current frame: colour 8 fills row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41 with a stem pixel at (12,40), all inside lattice (1,6). Not one colour-8 pixel has moved in fourteen frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) at cols 38-42 only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of that cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body is driven into a colour-8 cell my manual predicts it stays put, and the world says otherwise in one command. Four lattice cells of eastward travel put the body at (1,5) and every one of those four steps is on floor that R=1 shows open. Thirteen commands have been spent and none of them has taken step one."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained after fourteen states, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition. Note that the standard mapping I favour -- 1 up, 2 down, 3 left, 4 right, 5 undo-or-return -- accounts for every key pressed, which makes 6 and 7 more likely to be a click and a spare than more directions."
    [depends: the_action_map_after_thirteen_transitions_and_the_standard_mapping_hypothesis  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and the reason has not weakened. Cart.pos = exit_cell needs one named instance and `arc-instances: all` gives me Glyph9_r8c14 and forty siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells of lattice (8,7) do become dynamic on first entry, but they are frame-0 colour 5 and would type as Vacated -- indistinguishable by this arm from the 24 Vacated cells at rows 14-18 -- so count(Vacated, color = 9) = 24 would be true of the body standing one cell south of spawn, which is not a win. A goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in lattice (8,7) once, the playbook steers by lattice distance, and is_goal -> False is the honest compilation."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter has crossed into POSITIVE gain for the first time, +614 bits at compression_ratio 0.937 on split_by_color=false, against -55676 bits when split by colour -- so its segmentation now just barely beats writing the pixels out, and I still owe it nothing structural. Its ten tracks remain the round's best independent corroboration and this round they corroborate the toggle by frame index: colour-1 nine-cell tracks obj1 (frames 0-4), obj6 (7-8), obj8 (11-12); colour-2 tracks obj5 (5-6), obj7 (9-10), obj9 (13). That is A,B,A,B,A,B derived by an engine that has never seen my rules. obj0 and obj2 persisting through all fourteen frames while the segmenter narrates ten moves is the marker-with-two-seats reading. obj4 is the whole 64-cell bar of which 6 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body ring: connected_components(4) cannot see the mover at all, because the mover is a ring of floor-adjacent pixels that merges with the floor, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 13 transitions constrain rank 7 of 385 features, null space dimension 378, nearly every vector in it is a law true over these states and unfalsified rather than confirmed -- and its single global law is my census. cegis_miner refuses on every track and its verdict, the world does not narrate as one mover, remains true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The next command has index 14, which is EVEN, and the body is at spawn with the panel in configuration B. ACTION4: if the standard mapping holds, the world changes 48 cells in rows 8-12 cols 14-24 and burns (63,57) for 49 total, and MY MANUAL DRAWS NONE OF THEM -- no east rules exist and (63,57) is board -- so I expect a 49-cell divergence, which is the advertised price of the first step onto fresh ground and not a failure of physics. If instead ZERO cells change, ACTION4 is not east, ACTION3 is east by elimination, AND BOTH METER READINGS DIE AT ONCE, because key 4 is even and index 14 is even and both demanded a burn. If exactly ONE cell changes and it is (63,57), ACTION4 is not east and both readings survive. ACTION5: I predict ZERO changed cells anywhere, on the strength of the spawn_probe guard and nothing else; a 23-cell panel toggle refutes the guard outright, a 48-cell move south says ACTION5 is UNDO, and a lone burn at (63,57) kills action-keying while leaving parity standing. ACTION2: 48 cells I draw correctly plus a burn at (63,57) I cannot draw -- exactly one wrong pixel, and nothing else learned, because key2_body_leaves and key2_body_arrives are at 120/120 and a sixth witness buys nothing. ACTION1 OR ACTION3 from spawn: zero cells under my manual, one cell at (63,57) under parity."
    [depends: the_action_map_after_thirteen_transitions_and_the_standard_mapping_hypothesis, the_parity_diagonal_survived_four_more_commands_and_is_still_free_to_break  probe: pending]

  theorem a_landmark_is_only_as_true_as_the_comment_beside_it "Kept in compressed form because the lesson is structural and cost a full round. Thirteen panel rules once carried colored(spawn_probe, 5) while the landmark line read a prose placeholder instead of a coordinate; the grammar puts such a landmark at (0,0), (0,0) is background in every frame this world has drawn, and so all thirteen rules were unreachable text that fired never and clashed never. Responsibility passed, ambiguity passed, step crashed zero times, and ONLY replay caught it. The landmark now reads (8, 14), the top-left pixel of the spawn ring, which renders 9 while the body is home and 5 the moment it is anywhere else. Before ranking any probe, check that the rules it is meant to test can actually fire."
    [depends: key5_slot1_dims  probe: passed]
