# theory.dsl -- world observed for 14 states / 13 transitions
# (RESET, then A1 A2 A3 A4 A5 A2 A5 A1 A3 A2 A5 A2 A4, one command each).
# 77 cells have ever changed; this manual names and owns all 77.
#
# ================= WHAT HAPPENED SINCE THE LAST MANUAL =================
#
# 1. FOUR NEW TRANSITIONS, AND NOT ONE OF THEM SHOWED ME A NEW MECHANISM.
#    t10 A2 = t2 repeated. t11 A5 = t5 repeated. t12 A2 = t6 repeated.
#    t13 A4 at lattice (2,2) = t4 repeated, minus the burn. I read the
#    CURRENT FRAME cell by cell against what my manual draws for state 13
#    and it agrees on every one of the 77 dynamic cells: panel in
#    configuration B exactly as described, body ring at rows 14-18 cols
#    14-18 with its aperture at (16,16), meter burned at row 63 cols
#    58-63 and nowhere else. A manual missing a 23-cell or 48-cell
#    mechanism could not land on the observed frame after thirteen
#    transitions. So the manual is not missing a mechanism.
#
# 2. THEN WHY DID THREE PROBES COME BACK VACUOUS? Because the frontier
#    CANNOT contain the world on an even-indexed command, and P-05, P-06
#    and P-07 were commands 10, 11 and 12. See
#    the_frontier_is_vacuous_by_construction_at_even_indices. In short:
#    the cell the meter is about to burn has never changed, so the arm
#    gives it no instance, so NEITHER the manual NOR any ablation of it
#    NOR `inert` can draw it -- every hypothesis is refuted by the same
#    one pixel and the realised gain is 0 bits by arithmetic, not by
#    ignorance. I am not given divergence sets, only hashes, so I mark
#    this reading probe: pending and name the observation that would
#    overturn it.
#
# 3. THE CLOCK IS NOW 6/6 AND 7/7 AND THE STORE CONFIRMED MY STATE MODEL
#    FROM A NUMBER I DID NOT FIT. My model says a state is (body in one
#    of two cells) x (panel A or B) x (burn count 0..6). It predicts that
#    s0=s1, s2=s3, s8=s9, s12=s13 and no other coincidence, hence
#    14 - 4 = 10 distinct states. The store reports distinct_states = 10.
#    See the_state_model_predicted_the_duplicate_count.
#
# 4. ACTION4 IS STILL UNTESTED WHERE EAST IS OPEN. t13 spent ACTION4 at
#    lattice (2,2), where east AND west are void -- the one cell where
#    its answer means nothing. Thirteen commands, two lattice cells
#    occupied out of eleven reachable. The playbook's whole first page is
#    about that and about the cheaper question underneath it: does
#    ACTION2 work from anywhere but spawn, or is this a two-cell shuttle?

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
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t6,t7,t10,t11,t12 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t5,t7,t11 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t11 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t10,t12 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t10,t12 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_edge_key2 forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_next_key2 forall ?p in Glyph9 [ev: t6,t10,t12 cov: 1/1]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key4 forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_next_key1 forall ?p in Glyph9 [ev: t8 cov: 1/1]
    when act=key(1) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key3_inert_below_spawn forall ?v in Vacated [ev: t3,t9 cov: 1/1]
    when act=key(3) and colored(spawn_probe, 5) and colored(?v, 9) and colored(above(?v), 5) and colored(leftof(?v), 5) and colored(rightof(?v), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t11 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t11 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t11 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t11 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t11 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t11 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t11 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t11 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t11 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t11 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?p, 0) then recolored(?p, 9)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7 cov: 8/8]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7 cov: 1/1]
    when act=key(5) and colored(spawn_probe, 5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_dims forall ?d in Dark [ev: t7 cov: 3/3]
    when act=key(5) and colored(spawn_probe, 5) and colored(?d, 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 41 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: counted]
  invariant board_cells count(board) = 4019 [status: counted]
  invariant meter_burned_cells count(Glyph9, color = 1) = 6 [status: counted at state 13, monotone]

  theorem dynamic_census "Exactly 77 cells have ever changed and every one has an owner, two more than last round and both of them meter cells. 23 are the panel: slot 1's eight ring pixels at rows 1-3 cols 1-3, its centre (2,2) being colour 0 in both configurations and therefore board; underline 1's three at row 5 cols 1-3; slot 2's nine at rows 1-3 cols 5-7, centre included because (2,6) is 1 in configuration A and 0 in B; underline 2's three at row 5 cols 5-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows south, rows 14-18 cols 14-18 minus its aperture (16,16). 6 are the burned right end of row 63, cols 58 to 63, burned in order 63,62,61,60,59,58 at commands 2,4,6,8,10,12. 23+24+24+6 = 77 = dynamic_cells. By frame-0 colour: 41 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 6 meter), 9 colour-1 (slot 2, solid at frame 0), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 41+9+24 = 74 = cells_needing_an_owner EXACTLY, the store again declining to count background-coloured cells; Dark carries the remaining 3 anyway and replay proves the arm instances them. 4096-77 = 4019 = constant_cells exactly."
    [probe: passed]

  theorem the_state_model_predicted_the_duplicate_count "The strongest corroboration this round and it came from a number I did not fit. My manual says a state is exactly three things: which of two lattice cells the body occupies, which of two configurations the panel shows, and how many meter cells are burned. Writing them out for s0 to s13 -- burns floor(k/2), body spawn spawn (2,2) (2,2) (2,2) spawn (2,2) spawn spawn spawn (2,2) spawn (2,2) (2,2), panel A A A A A B B A A A A B B B -- exactly four pairs coincide: s0=s1, s2=s3, s8=s9 and s12=s13. That predicts 14 - 4 = 10 distinct states. The store reports distinct_states = 10. Any missing mechanism that varied a pixel anywhere in those fourteen frames would have broken a coincidence and pushed the count above 10; any spurious mechanism of mine would have pushed it the other way. This is why I do not believe the three vacuous probes indicate a missing mechanism."
    [depends: dynamic_census, the_meter_is_a_two_command_clock  probe: passed]

  theorem the_frontier_is_vacuous_by_construction_at_even_indices "My answer to P-05, P-06 and P-07, and it is a change of reading rather than a change of rules. All three report every hypothesis refuted, including `inert` and every ablation of the manual, and 0.0 bits realised. An ablation can only DELETE a rule, so the whole frontier is a lattice between the manual and `inert`; if the world does something NO rule of the manual can express, every member of that lattice dies together and the gain is 0 bits by arithmetic. There is exactly one such thing in this world and I named it two rounds ago: the meter's leading edge. The cell about to burn has never changed, so the arm gives it no instance, so no rule can recolour it. P-05 was command 10 (burn at 63,59), P-07 was command 12 (burn at 63,58) -- both even, both burning. P-06 was command 11, which does not burn, and my reading of it is that the frontier was built from a store that did not yet contain command 10's burn, so the predecessor the manual rolled forward from was already one pixel stale. WHAT WOULD OVERTURN THIS: a refutation report that carries a divergence SET rather than a hash, showing any cell outside row 63 cols 55-63. I am not given one, so I mark this pending and rest the claim on the census and on the state-model count instead: after thirteen transitions my manual lands on the observed frame at every one of the 77 dynamic cells, which no manual missing a 23-cell or 48-cell mechanism could do. CONSEQUENCE FOR THE ARM: half of all commands are even, and a probe designed at an even index has expected realised gain 0 whatever it expects on paper."
    [depends: i_cannot_draw_the_leading_edge_burn, the_meter_is_a_two_command_clock  probe: pending]

  theorem the_meter_is_a_two_command_clock "Now 6 out of 6 and 7 out of 7 and I consider it settled. Row 63 is a 64-cell colour-9 bar burning 9 to 1 one cell at a time from the right. Burns occurred at commands 2, 4, 6, 8, 10 and 12 and at no other command; commands 1, 3, 5, 7, 9, 11 and 13 burned nothing. The key pressed is irrelevant: ACTION1 burned at 8 and did not at 1, ACTION4 burned at 4 and did not at 13, ACTION2 burned at every one of 2, 6, 10 and 12 which happen all to be even, ACTION3 and ACTION5 were only ever pressed at odd indices and never burned. Cols 58-63 are spent, 58 cells remain, so roughly 116 commands remain before the bar is out. The next command is index 14, which is EVEN, and it will burn (63,57) whatever is pressed."
    [depends: meter_burn_next_key1, meter_burn_next_key4  probe: passed]

  theorem the_burn_rules_are_deliberate_mis_attributions_and_one_of_them_is_about_to_break "Constraints 3 and 6, and this time with a dated failure attached. My four burn rules key on act=key(1), key(2) and key(4) because THE GUARD LANGUAGE HAS NO COMMAND COUNTER and no pixel records the parity. I checked whether the parity is recoverable from the frame and it is not: at the start of command k the burn count is floor((k-1)/2), so a frame showing b burns is the start of command 2b+1 (no burn) or 2b+2 (burn) with equal warrant, and b's own parity separates neither -- b takes every value 0..5 in both classes. THE DATED FAILURE. Right now no dynamic meter cell renders 9, so no burn rule can misfire and replay is clean at 13/13. The moment command 14 burns (63,57), that cell becomes dynamic and gets an instance, and REPLAYING t13 -- ACTION4 at an odd index -- will find (63,57) rendering 9 with a colour-1 right neighbour and fire meter_burn_next_key4, predicting a burn the world did not deliver. Exactly one wrong pixel at (63,57) on exactly transition t13, from the next even command onward. I considered guarding that rule on the panel configuration, which happens to separate t4 from t13, and rejected it: it is a fifth mis-attribution fitted to two points and it would break the first time key 4 is pressed in configuration A at an odd index. I considered deleting the rules and rejected that too: it costs six real pixels of replay now to save one later. I keep them and I date the failure instead of being surprised by it."
    [depends: the_meter_is_a_two_command_clock  probe: pending]

  theorem i_cannot_draw_the_leading_edge_burn "A law of this manual rather than of this world, now paid five times. The arm instances exactly the cells that have ALREADY changed, so the next cell to burn is board, has no instance, and NO RULE OF MINE CAN RECOLOUR IT. I checked whether any declaration escapes this: arc-instances: all covers only cells the board cannot explain, so it will not reach a static cell; a landmark can be named at (63,57) but landmarks are cells, not objects, and every event in the language takes an object as its first argument, so a landmark cannot be recoloured. There is no construction in this DSL that draws a cell before its first change. CONSEQUENCE FOR READING REFUTATIONS: a divergence set consisting only of the bar's leading edge does not implicate this manual and must not be allowed to consume a round -- it has now consumed three."
    [depends: the_meter_is_a_two_command_clock  probe: passed]

  theorem the_world_is_not_a_function_of_the_drawn_frame_and_one_command_would_prove_it "Nearly forced, and the proof is now one command away instead of two. s12 and s13 are PIXEL-IDENTICAL -- same body cell, same panel configuration B, same six burns -- which is not a guess but part of the arithmetic that makes distinct_states come out at 10. From s12 the world was given ACTION4 (command 13) and changed nothing. The body stands on s13 now. Give it ACTION4 again (command 14, even) and the clock says (63,57) burns: identical state, identical action, different successor, and hidden state is proven rather than argued. I RANK THIS LOW ANYWAY and say why: constraint 5 obliges my manual to be a function of the frame, so I already know I must be wrong about one member of that pair, that pixel is the leading edge I cannot draw in any case, and the finding changes no rule. It is a cheap proof of something I would not act on differently. I record it so that nobody can sell it to me later as a discovery."
    [depends: the_state_model_predicted_the_duplicate_count  probe: pending]

  theorem the_down_key_may_be_a_shuttle_and_one_press_settles_it "THE LARGEST UNEXAMINED ASSUMPTION IN THIS FILE, and thirteen commands have failed to touch it. ACTION2 has been pressed four times and every one was from spawn; ACTION5 has been pressed three times and every one was from lattice (2,2). Not once has ACTION2 been pressed from anywhere but spawn. So every observation is equally consistent with two readings. READING DOWN: ACTION2 moves the body one lattice cell south wherever it stands, ACTION5 moves it one north, and the maze theorem below is about a maze. READING SHUTTLE: ACTION2 means go to cell two and ACTION5 means go back to cell one, the world is a two-cell rocker, and the lattice, the comb and the socket are scenery. One press decides it: ACTION2 from where the body stands now. Lattice (3,2) is rows 20-24 cols 14-18, read floor in the current frame, and separator row 19 is floor across cols 13-31, so the destination ring is clear. WHAT MY MANUAL PREDICTS FOR THAT PRESS, so it can cost me: NOTHING except an undrawable burn. key2_body_leaves ranges over Glyph9 and the body currently stands on Vacated cells, so no rule of mine erases rows 14-18; key2_body_arrives ranges over Vacated and rows 20-24 are board with no instances. If the body moves I am wrong by 48 cells, 24 of which -- the departure at rows 14-18 -- I could have drawn with a rule and deliberately did not, because constraint 2 forbids a rule with no witness and this one has none. That is the price of the constraint and I pay it once, knowingly, rather than smuggling an unwitnessed rule into the manual."
    [depends: key2_body_leaves, the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_action_map_after_thirteen_transitions "WITNESSED, with the negatives stated as negatives, and one negative wasted. ACTION2 CARRIES THE BODY SOUTH FROM SPAWN: t2, t6, t10, t12, the 5x5 ring from rows 8-12 to rows 14-18, four times, in both panel configurations. ACTION5 CARRIES IT BACK NORTH: t5, t7, t11, three times, each with a panel toggle. NEGATIVES. At spawn, north and west are void while south and east are open floor; ACTION1 did nothing there at t1 and t8, ACTION3 did nothing there at t9 -- so NEITHER ACTION1 NOR ACTION3 IS EAST. At (2,2) north and south are open while east and west are void; ACTION3 did nothing at t3 and ACTION4 did nothing at t4 and again at t13 -- so neither is up and neither is down, and both are consistent with being horizontal. Combine: ACTION3 is neither vertical nor east, which leaves west, and west is void at both cells it has been pressed from, explaining all three of its silences without inventing anything. ACTION4 IS STILL THE ONLY REMAINING CANDIDATE FOR EAST AND HAS STILL NEVER BEEN PRESSED WHERE EAST IS OPEN. t13 spent it at (2,2), the one cell where east and west are both void and its answer means nothing -- a command bought and thrown away. Cells where east is open: spawn (rows 8-12, cols 20-24 read floor) and lattice (3,2) (rows 20-24, cols 20-24 read floor). The residue: ACTION1 is consistent with up and so is ACTION5, and two up keys is a smell; one press of ACTION1 from (2,2) separates them."
    [depends: key2_body_arrives, key5_body_respawns  probe: pending]

  theorem action5_is_up_or_home_or_undo_and_a_third_cell_separates_them "Three witnesses now and all three moved the body from (2,2) to spawn, a move that up, return-home and undo-last-move predict identically, so this store still cannot separate them. The separator is unchanged and is a shape, not a route: stand two lattice steps from spawn and press ACTION5 once. Up predicts one step back; home predicts a jump of two cells; undo predicts one step back along the arrival direction, which differs from up as soon as the last step was horizontal. My rules encode none of the three -- key5_body_respawns is guarded on PIXELS, a Glyph9 cell rendering 5 whose neighbour above renders 5, so it is a spawn-ring refill rule and nothing more. As written it fires from ANY state where the spawn ring reads floor, so from a third cell my manual predicts the body is DRAWN AT SPAWN WITHOUT BEING ERASED where it stood: two bodies, 24 wrong pixels, priced here in advance."
    [depends: key5_body_respawns, the_action_map_after_thirteen_transitions  probe: pending]

  theorem the_spawn_probe_guard_is_still_the_untested_half_of_thirteen_rules "Every panel rule carries colored(spawn_probe, 5), which reads the body is not at home. All three witnesses had the body one cell south, so the guard has never been tested with the body home: ACTION5 has never been pressed at spawn in fourteen states. If the panel toggles anyway, thirteen rules are guarded on the wrong thing and my manual under-predicts 23 pixels on that command; if nothing happens, the guard survives and the manual is right that ACTION5 at spawn is inert. The asymmetry that makes this cheap is unchanged: my manual predicts ZERO cells for ACTION5 at spawn, so any change at all is legible in the raw diff."
    [depends: key5_slot1_dims, key5_slot1_lights  probe: pending]

  theorem the_panel_is_a_two_slot_selector_toggled_by_action5 "Both directions witnessed, A to B at t5 and t11 and B to A at t7, and the current frame re-read pixel by pixel is configuration B. A: slot 1's ring reads 9 with underline 1 reading 9, slot 2 reads solid 1 with underline 2 reading 0. B: slot 1's ring reads 2 with underline 1 reading 0, slot 2 reads a ring of 9 with its centre hollowed to 0 and underline 2 reading 9. THE READING: two slots, an underline under each, and the underlined slot is also the one rendered in colour 9 -- a two-item selector whose cursor ACTION5 advances, wrapping after two. The two glyphs are a hollow 3x3 square and a solid 3x3 square; the body is a hollow ring and the knob at rows 9-11 cols 39-41 is a solid 3x3 block, which is a suggestive pairing and nothing more. WHAT I DO NOT CLAIM: what the selection selects. ACTION2 moved the body identically from configuration A at t2 and t10 and from configuration B at t6 and t12, and ACTION4 was inert in configuration A at t4 and in configuration B at t13, so the selector remaps neither -- four cross-configuration comparisons and not one difference. If the selection matters at all it matters to a key never pressed, which is ACTION6 or ACTION7."
    [depends: key5_slot1_lights, key5_slot2_ring_resets, key5_underline2_dims  probe: passed]

  theorem the_goal_is_absent_because_no_instance_can_name_the_socket "I decline again to declare a goal, the argument is unchanged by four more transitions, and I restate the price. The winning position I believe in is lattice cell (8,7), rows 50-54 cols 44-48, whose 24 ring pixels read floor and whose centre (52,46) is a lone colour-9 pip inside a three-sided colour-9 bracket. Four forms of goal are available and every one is refuted. (1) Cart.pos = exit_cell needs ONE named instance; arc-instances: all gives me Glyph9_r8c14 and forty siblings and there is no instance called Glyph9, and a second colour-9 type would be indistinguishable to an arm that looks objects up by colour alone. (2) A count over the socket interior has nothing to range over: those cells have never changed, so they are board and carry no instances. (3) Counts over the four types I do have are all either true in some observed state -- count(Vacated, color = 9) = 0 holds in seven of fourteen, count(Glyph9, color = 5) = 24 holds in six -- or, like count(Spent, color = 0) = 9, false everywhere and meaningless, which is exactly the fake goal the rider warns is worse than none. (4) The goal cannot be conjunctive; the section takes one equation. THE PRICE: is_goal compiles to False, plan returns no_goal_declared, commit never runs, and all fourteen commands have been probes. THE OBSERVATION THAT ENDS THIS, restated sharply: a goal becomes writable the moment any pixel of the bracket rows 49-55 cols 43-49, or the pip (52,46), changes colour, because those cells become dynamic that instant and a count over them becomes both writable and false in every earlier state. Nothing the body has done in fourteen commands can cause that, because the body has not left a two-cell corridor. THAT is the reason there is no goal, and it is a reason about reach, not about vocabulary."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position, the_down_key_may_be_a_shuttle_and_one_press_settles_it  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 ring with a one-pixel aperture at its centre. Re-read pixel by pixel from the CURRENT frame. R=1 (rows 8-12) is floor from col 13 to col 43, so C=2,3,4,5 are open and C=6 holds the knob; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2 plus a one-row fragment at row 48 cols 42-50 that cannot hold a body; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2..7 are open. Separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so lattice column 2 is continuous from R=1 to R=8 apart from the comb, and lattice row 1 is continuous from C=2 to C=6. Spawn is (1,2); in fourteen frames the body has occupied exactly TWO cells, (1,2) and (2,2), and it stands at (2,2) now. THIS THEOREM IS HOSTAGE TO ONE PRESS: if ACTION2 does not carry the body from (2,2) to (3,2), there is no maze, only a rocker, and this theorem and the four below it are scenery."
    [depends: key2_body_arrives, the_down_key_may_be_a_shuttle_and_one_press_settles_it  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed seven times now: (16,16) stayed 5 at t2, t6, t10 and t12 while its 24 neighbours turned 9, and (10,16) did the same in reverse at t5, t7 and t11. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48, its 24 ring pixels all render floor, and its centre (52,46) renders colour 9, a lone pip. The map places something at a hole-centre exactly twice -- that pip and the knob's centre at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Verified cell by cell again against the current frame. The colour-9 bracket sits entirely on SEPARATOR strips: row 49 cols 43-49, row 55 cols 43-49, col 49 rows 50-54. Rows 49 and 55 are separator rows and cols 43 and 49 separator columns, so what is drawn is the north, south and east walls of lattice cell (8,7) painted colour 9, with the west side left as floor. Inside it, rows 50-54 cols 44-48 are floor except the lone colour-9 pixel at the exact centre (52,46). Overlay the body standing there -- 5x5, aperture at its centre -- and it is flush against three walls with the pip showing through the aperture. That is a plug and a socket drawn to the pixel. The bracket has not changed in fourteen frames, so it is board and no object owns it; the first time any of it changes, those cells become dynamic and the goal section can finally be written."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn under the DOWN reading and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. Nor is there a second route: C=3 exists only at R=3, C=4 dead-ends at R=3, C=5 and C=6 exist only at R=1, so lattice column 2 is the sole north-south corridor. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open and re-read in the current frame: a 3x3 colour-8 knob at rows 9-11 cols 39-41, a stem at col 40 running from row 12 to row 40, colour 8 filling row 40 from col 14 to col 40, and the comb teeth at rows 38-42 cols 14-18 with floor gaps only at (39,14) and (41,14). ONE CONNECTED WIRE from knob to gate, which is why I read the knob as the switch. Not one colour-8 pixel has moved in fourteen frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Fourteen commands and TWO OF SEVEN ACTIONS HAVE NEVER BEEN TRIED ONCE. In this action family one of them is normally a click carrying coordinates, and that matters here for a specific reason: the knob is a 3x3 target the body appears unable to stand on, the panel is a two-item selector whose selection provably changes nothing about ACTION2 or ACTION4, and a selector that selects nothing for the five keys I have tried is a selector for a key I have not. I cannot write a click rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5 or panel pixels moving, and never its precondition. My manual predicts ZERO cells for both keys, so any change at all is legible, and certify adjudicates five actions rather than seven, which means those two columns of the transition table are unexamined rather than clean."
    [probe: pending]

  theorem the_first_step_onto_fresh_ground_costs_pixels_and_that_is_not_a_defect "Priced in advance so it cannot be sold to me as a surprise. The arm instances exactly the cells that have already changed, so any lattice cell the body has never entered is board and has NO instance. The first step into a new cell costs 24 undrawable arrival pixels no matter what rule I write, plus up to 24 departure pixels if no witnessed rule of mine erases the cell being left. Concretely for the press I am about to recommend, ACTION2 from (2,2): 24 arrival pixels at rows 20-24 cols 14-18 are undrawable, and 24 departure pixels at rows 14-18 are drawable only by a rule I am forbidden to write until it has a witness -- so 48 on the first step, 24 on the second, 0 thereafter. The body also CHANGES TYPE as it walks -- Glyph9 at rows 8-12, Vacated everywhere else -- because typing is by frame-0 colour and all that floor was 5. A manual that heals one step behind is the price of this arm, and those pixels are tuition, not damage. THE COROLLARY THE ARM MUST HEAR: a probe frontier evaluated on that command will be vacuous for the same reason the meter makes even commands vacuous, and its 0 bits must not be read as a refutation."
    [depends: the_maze_is_a_six_pixel_lattice, the_frontier_is_vacuous_by_construction_at_even_indices  probe: pending]

  theorem silence_is_a_prediction_and_three_of_my_seven_silences_here_are_forged "The compiled transition function is total: where no rule fires the successor equals the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit the seven actions at lattice (2,2), where the body stands. key(1): NO WITNESS HERE -- pressed only at spawn. key(2): NO WITNESS HERE, and this is the shuttle question. key(3): inert, WITNESSED at t3. key(4): inert, WITNESSED twice, t4 and t13. key(5): carries the body north, witnessed three times. key(6) and key(7): NO WITNESS ANYWHERE. So four of seven silences at this cell are forged death certificates and one of them, key(2), is the load-bearing assumption of five theorems. That is the largest block of unearned confidence in this file and the cheapest to fix: one press each."
    [depends: the_action_map_after_thirteen_transitions, the_down_key_may_be_a_shuttle_and_one_press_settles_it  probe: pending]

  theorem the_cascade_length_is_a_free_channel_and_it_keeps_paying "ACTION2 returned 7 frames from configuration A at t2 and t10, and 9 frames from configuration B at t6 and t12 -- four for four, the split I predicted two rounds ago now doubled. ACTION5 returned 9 frames all three times and every no-op returned 1. So the animation length is not a function of the key alone and the panel configuration is the one correlate with a witness. This is hidden state I discard by construction, since cascade single_frame compares only net effect, and it is the ONLY evidence I have that the panel configuration changes anything at all -- the net pixel effect of ACTION2 is identical in both configurations. It costs nothing in replay and buys nothing in prediction; I keep reading it because it is free, and because if the selector ever does something visible I expect the frame count to have warned me first."
    [depends: the_panel_is_a_two_slot_selector_toggled_by_action5  probe: passed]

  theorem the_no_op_rule_fails_the_gain_test_and_i_keep_it_for_a_narrow_reason "key3_inert_below_spawn recolours one pixel to the colour it already has, has two witnesses on transitions where zero cells changed, and replay is identical without it. It explains no pixel and lengthens the manual, so it fails constraint 3 and I say so rather than dressing it up. The reason I keep it: it is the ONLY occurrence of act=key(3) in the file, and deleting it narrows the action set certify adjudicates from five keys to four. Note what that reason implies about keys 6 and 7, which appear nowhere: certify's fifty adjudicated pairs cover five of seven columns, and the two missing columns are unexamined rather than clean."
    [depends: key3_inert_below_spawn, two_actions_have_never_been_pressed_and_that_is_now_the_second_largest_gap  probe: passed]

  theorem the_rules_are_pairwise_exclusive_and_off_board_cell_terms_are_false "Constraint 5, re-checked by hand over all four instance types in both panel configurations after the meter grew by two cells. Under key(2): body_leaves needs below-six to render 5, which is off-board and therefore false for any row past 57, so it cannot fire on a meter cell; the two burn rules split on rightof = wall against a colour test on rightof, which cannot both hold. Under key(5) the type Glyph9 is split five ways by COLOUR FIRST -- 5 for respawns, 9 for the two dim rules, 2 for slot1_lights, 0 for underline1_lights -- and colours 2 and 0 occur on no other Glyph9 cell in any observed state, so the return half needs no geometry. The two colour-9 rules are then split by above-four: slot1_dims needs it to BE WALL, true only for rows 0-3; underline1_dims needs a COLOUR TEST on it, which is false off-board rather than raising, so it selects row 5 and excludes rows 0-3, and its above-six wall test excludes the meter at row 63. Spent splits by colour into 1 against 9 and 0; within colour 1 the geometry is row 1 by above-two wall, row 3 by a colour test on above-two, row 2 by above-three wall plus a colour test on above-one, and within row 2 col 5 by leftof-six wall, col 6 by leftof-seven wall plus a colour test on leftof-one, col 7 by a colour test on leftof-two. Dark splits by colour 0 against 9. Not one rule uses not, deliberately. Certify reports 0 clashes over 50 adjudicated pairs and 10 states."
    [depends: key2_body_leaves, key5_slot2_centre_darkens, key5_slot1_lights  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body is at lattice (2,2) rows 14-18, the panel is in configuration B, six meter cells are burned at row 63 cols 58-63, and the next command index is 14, which is EVEN, so under the clock it burns (63,57) whatever is pressed and I cannot draw that cell -- which also means whatever is pressed, the probe frontier will be vacuous and its 0 bits must be discounted. ACTION2, my first choice: my manual predicts ZERO cells and has NO WITNESS for that silence. If the body steps to (3,2) I pay 48 undrawable pixels already priced and the maze is real; if nothing moves, this world is a two-cell rocker and five theorems are scenery. Either answer is worth more than any other command on the board. ACTION4 here: predicted zero, witnessed zero twice already, and its only remaining value is the identical-state proof I have ranked low. ACTION5 here: 48 body cells and 23 panel cells I draw correctly, every rule already at full coverage, buying only a fourth cascade datum and a return to spawn. ACTION1 here: predicted zero, UNWITNESSED at this cell, and it separates ACTION1 from ACTION5 if it moves the body north. ACTION6 or ACTION7: predicted zero, never pressed anywhere, and the only keys that could plausibly give the selector something to select. THE SINGLE OBSERVATION THAT WOULD MOST CHANGE THIS FILE is unchanged and it is not a movement at all: any colour-8 pixel of the comb or the wire changing, because that turns the gate theorem into physics and puts the socket in reach."
    [depends: the_down_key_may_be_a_shuttle_and_one_press_settles_it, the_meter_is_a_two_command_clock  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on both variants, -1629 bits unsplit and -42062 split by colour, which is the segmenter saying its own script costs more than writing the pixels. I take its TRACK LIST and not its verdict, and this round the list dates my panel rules independently for a second time. obj0 (colour 9, eight cells, 3x3, all fourteen frames) and obj2 (colour 9, 1x3, all fourteen frames) are slot 1's ring and underline 1 persisting through all three toggles, so it does not see the panel as appearing and vanishing, which corroborates a marker with two seats rather than two objects. obj1 (colour 1, 3x3, frames 0-4) is slot 2 solid in configuration A; obj5 (colour 2, eight cells, first frame 5, present 2 frames) is slot 1 after the t5 dim, ending at t7; obj6 (colour 1, first frame 7, present 3 frames) is slot 2 solid again from t7 to t10; obj7 (colour 2, eight cells, FIRST FRAME 11, present 3 frames) is slot 1 dimmed again by t11 and still dim in the current frame. Four tracks whose birth and death frames are 5, 7, 7 and 11 -- exactly my three toggle transitions, from an engine that has never seen my rules. obj4 is the whole 64-cell row-63 bar, of which 6 cells are now dynamic. obj3 is a 1006-cell colour-null blob that swallowed the maze floor AND the body: connected_components(4) cannot see the mover, because the mover is a ring adjacent to floor on every side, and THAT ABSENCE IS THE FINDING. None of these gets a type of its own; a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 13 transitions constrain rank 7 of 385 features, null space dimension 378 -- and its one global law is my census cell for cell, 77 cells, a consistency check and not a discovery. cegis_miner refuses every track and its verdict, the world does not narrate as one mover, is true of the arm and false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours."
    [probe: passed]
