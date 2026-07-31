# theory.dsl -- world observed for 10 states / 9 transitions
# (RESET + A1 A2 A3 A4 A5 A2 A5 A2 A5). 75 cells have ever changed; this
# manual names all 75 and now attempts to OWN all 75.
#
# WHAT HAPPENED THIS ROUND, IN ORDER OF WHAT IT COST ME:
#
#   1. THE WORLD ADVANCED BY FOUR COMMANDS AND THEY WERE THE FOUR I NEEDED.
#      t6 A2, t7 A5, t8 A2, t9 A5. Three of the five surprises are the same
#      surprise twice over: my ACTION5 rules only ran one way, and the world
#      runs ACTION5 BOTH ways.
#
#   2. MY PREDECESSOR'S BUDGET THEOREM IS DEAD. "Two tokens, one spent, one
#      remains, roughly 120 commands and one life" is REFUTED by t7: the
#      colour-1 solid block came BACK. The panel is a two-state toggle driven
#      by ACTION5, not a consumable. ACTION5 is therefore CHEAP, and every
#      ordering in the playbook that ranked branches by token cost was ranking
#      on a fiction. See the_panel_is_a_toggle_and_the_budget_theorem_is_dead.
#
#   3. I REVERSED THE STANDING REFUSAL ON THE METER AND I SAY WHY. Four
#      readings entered this round; the world killed one (phase-reset), and
#      arithmetic showed two others (frames-parity, command-parity) are the
#      SAME reading because every command returns an odd frame count. Two
#      survive, they are perfectly confounded -- and ONE OF THEM CANNOT BE
#      WRITTEN IN THIS LANGUAGE AT ALL. I wrote the writable one, on 4
#      witnesses, and I name the exact command that refutes it. See
#      the_meter_collapsed_to_two_readings_and_only_one_is_expressible.
#
#   4. I AM GAMBLING ON THREE PIXELS. (5,5),(5,6),(5,7) were declared
#      permanently unownable by two builds running. The arithmetic that
#      declared them unownable -- cells_needing_an_owner is 72, not 75 --
#      is exactly the arithmetic that says an arc-colour 0 object gets THREE
#      instances rather than three thousand. I declare `Dark` and guard its
#      two rules so that all three possible outcomes are safe. See
#      three_cells_i_am_gambling_can_be_owned_and_the_gamble_is_hedged.
#
#   5. THE PREVIOUS DESK EMITTED NO THEORY BLOCK AND THE MANUAL DID NOT
#      COMPILE. Nothing downstream ran. That is a process failure, not a
#      modelling one, and the only fix is the one I am applying: emit all
#      three blocks, every time.

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
  landmark spawn_center   # arc-cell: (10, 16)
  landmark knob_center    # arc-cell: (10, 40)
  landmark gate_center    # arc-cell: (40, 16)
  landmark socket_center  # arc-cell: (52, 46)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t9 compress: 39]
  Vacated [segment: dynamic_colour_5 ev: t2-t9 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t9 compress: 9]
  Dark    [segment: dynamic_colour_0 ev: t5,t7,t9 compress: 3]

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t6,t8 cov: 72/72]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t6,t8 cov: 72/72]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule meter_burn_key2_rightmost forall ?p in Glyph9 [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)

  rule meter_burn_key2_next forall ?p in Glyph9 [ev: t6,t8 cov: 2/2]
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule meter_burn_key4_next forall ?p in Glyph9 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

  rule key5_body_clears forall ?v in Vacated [ev: t5,t7,t9 cov: 72/72]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5,t7,t9 cov: 72/72]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

  rule key5_slot1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 16/16]
    when act=key(5) and colored(?p, 9) and above(above(above(above(?p)))) = wall then recolored(?p, 2)

  rule key5_slot1_lights forall ?p in Glyph9 [ev: t7 cov: 8/8]
    when act=key(5) and colored(?p, 2) then recolored(?p, 9)

  rule key5_underline1_dims forall ?p in Glyph9 [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(?p, 9) and colored(above(above(above(above(?p)))), 9) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 0)

  rule key5_underline1_lights forall ?p in Glyph9 [ev: t7 cov: 3/3]
    when act=key(5) and colored(?p, 0) and above(above(above(above(above(above(?p)))))) = wall then recolored(?p, 9)

  rule key5_slot2_row1_lights forall ?s in Spent [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(?s, 1) and above(above(?s)) = wall then recolored(?s, 9)

  rule key5_slot2_row3_lights forall ?s in Spent [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(?s, 1) and colored(above(above(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_row2_left_lights forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(?s)))))) = wall then recolored(?s, 9)

  rule key5_slot2_row2_right_lights forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and colored(leftof(leftof(?s)), 1) then recolored(?s, 9)

  rule key5_slot2_centre_darkens forall ?s in Spent [ev: t5,t9 cov: 2/2]
    when act=key(5) and colored(?s, 1) and above(above(above(?s))) = wall and colored(above(?s), 1) and leftof(leftof(leftof(leftof(leftof(leftof(leftof(?s))))))) = wall and colored(leftof(?s), 1) then recolored(?s, 0)

  rule key5_slot2_ring_resets forall ?s in Spent [ev: t7 cov: 8/8]
    when act=key(5) and colored(?s, 9) then recolored(?s, 1)

  rule key5_slot2_centre_resets forall ?s in Spent [ev: t7 cov: 1/1]
    when act=key(5) and colored(?s, 0) then recolored(?s, 1)

  rule key5_underline2_lights forall ?d in Dark [ev: t5,t9 cov: 6/6]
    when act=key(5) and colored(?d, 0) and colored(above(above(?d)), 1) and colored(above(above(above(above(?d)))), 1) then recolored(?d, 9)

  rule key5_underline2_dims forall ?d in Dark [ev: t7 cov: 3/3]
    when act=key(5) and colored(?d, 9) and colored(above(above(?d)), 9) then recolored(?d, 0)

laws:
  invariant glyph9_instances count(Glyph9) = 39 [status: counted]
  invariant vacated_instances count(Vacated) = 24 [status: counted]
  invariant spent_instances count(Spent) = 9 [status: counted]
  invariant dark_instances count(Dark) = 3 [status: predicted_not_verified]
  invariant board_cells count(board) = 4021 [status: counted]

  theorem the_world_advanced_and_here_is_what_the_four_new_commands_bought "Unlike the last two rounds the store moved: 6 states became 10, 6 steps became 10, dynamic_cells 73 became 75, cells_needing_an_owner 70 became 72. The four new commands were ACTION2, ACTION5, ACTION2, ACTION5 at t6..t9, and their diffs are 49 / 71 / 49 / 71 cells. 49 = 24 body pixels leaving rows 8-12 plus 24 arriving at rows 14-18 plus one meter cell. 71 = 24 clearing rows 14-18 plus 24 respawning at rows 8-12 plus 23 panel cells, and NO meter cell. Every one of those numbers is what my movement rules already predicted; the entire cost of the round was the 23 panel cells and the 1 meter cell, and both are answered below with rules rather than with prose."
    [probe: passed]

  theorem the_panel_is_a_toggle_and_the_budget_theorem_is_dead "REFUTATION, stated first because it changes the playbook more than anything else here. The last manual read the panel as two lives: slot 1 hollow-9 in play, slot 2 solid-1 not yet issued, ACTION5 spends one, ONE TOKEN REMAINS. t7 killed it. The diff at t7 is [0,2,5,9] -> [0,1,5,9]: colour 2 vanished from the frame and colour 1 came BACK, and mdl_segmenter independently reports obj6, a 9-cell 3x3 colour-1 solid block, first seen at frame 7 and present for two frames -- the same shape as obj1, the colour-1 block of frames 0-4. t9 flipped it again. So the panel has exactly two configurations and ACTION5 swaps them. STATE A (frames 0-4, 7-8): slot 1 rows 1-3 cols 1-3 is a hollow colour-9 ring, its underline row 5 cols 1-3 lit 9, slot 2 rows 1-3 cols 5-7 is a SOLID colour-1 block, its underline row 5 cols 5-7 dark 0. STATE B (frames 5-6, 9, and now): slot 1 is a hollow colour-2 ring, underline 1 dark, slot 2 is a hollow colour-9 ring with its centre (2,6) dark, underline 2 lit 9. A consumable does not come back, so this is not lives; it is a two-phase indicator -- whose turn, which body, which mode -- and I do not yet know which. What it costs me to be wrong about the MEANING is nothing, because the ten rules below encode the SWAP and not the meaning. What it cost my predecessor to be wrong was the whole ordering of the search: every branch was ranked by a life it could not spend."
    [depends: key5_slot1_lights, key5_slot2_ring_resets  probe: passed]

  theorem the_meter_collapsed_to_two_readings_and_only_one_is_expressible "Row 63 is a 64-cell colour-9 bar burning to colour 1 from the right: (63,63) at t2, (63,62) at t4, (63,61) at t6, (63,60) at t8; no burn at t1, t3, t5, t7, t9. Four readings entered this round and here is the accounting. (c) PHASE-RESET-BY-RESPAWN, which predicted no burn at t6 because ACTION5 re-zeroed the phase, is REFUTED -- t6 burned. (a) FRAMES-PARITY and (b) COMMAND-PARITY are THE SAME READING and I should have seen it a round ago: every command this world has ever returned has an odd frame count (1, 7 or 9), so cumulative frames flip parity on every single command and 'cumulative frames odd' is identically 'command index even'. Cumulative frames stand at 1,2,9,10,11,20,29,38,45,54; the burns are at 9,11,29,45, all odd, all even-t. That leaves TWO live readings, 9/9 each: PARITY (burn on every second command) and ACTION-KEYED (burn iff the action is key 2 or key 4, equivalently iff the action number is even -- I cannot separate those two sub-readings either). They are perfectly confounded here because every ACTION2 landed on an even t and every ACTION5 on an odd t. Now the asymmetry that decides what I write: PARITY IS NOT EXPRESSIBLE IN THIS LANGUAGE. There is no command counter among the guards, and the meter's own drawn state does not carry the phase -- burned-count 2 occurs at t5 (no burn) and at t6 (burn), just as burned-count 0 occurred at t1 and t2 and burned-count 1 at t3 and t4. cegis_miner hit the same wall from its side: 'no literal separates transition 1 from the positives'. So my choice is not between two rules, it is between one rule and silence. Action-keying now has four positive witnesses (t2, t4, t6, t8) and five negatives, including ACTION5 pressed three times with no burn -- that is far more than the one-observation-per-action that made my predecessor refuse. I write it, I mark it as the most refutable thing in this manual, and I schedule its execution: any command that is not key 2 and not key 4, pressed at an EVEN command index, burns under parity and does not burn under action-keying. That is a free, one-bit, one-command experiment and the playbook puts it near the top."
    [depends: meter_burn_key2_next, meter_burn_key4_next  probe: pending]

  theorem the_meter_rule_repairs_the_past_and_cannot_predict_the_future "An honest bound on what I just bought. The burn rules can only fire on cells that HAVE instances, and instances exist only for cells that have already changed, so the four burned cells (63,60)..(63,63) are drawable and (63,59) -- the next to burn -- is board and is not. On the observed transitions the rules should take replay from 1/9 towards 9/9, because at t2 (63,63) is an instance whose right neighbour is off-board, and at t4, t6, t8 the burning cell is an instance whose right neighbour already renders 1. On the NEXT command they draw nothing at all: whatever the meter does at t10 my manual leaves row 63 alone and the raw diff, not certify, is what tells me the answer. I state this so that nobody reads a rising replay score as predictive power it does not have."
    [depends: meter_burn_key2_rightmost, only_visited_cells_have_instances  probe: pending]

  theorem three_cells_i_am_gambling_can_be_owned_and_the_gamble_is_hedged "(5,5),(5,6),(5,7) -- underline 2 -- render 0 at frame 0 and 9 in state B. Two builds declared them permanently unownable on the grounds that an arc-colour 0 object would claim three thousand background cells. I think that is exactly backwards, and the evidence is the arm's own arithmetic: constant_cells 4021 + dynamic_cells 75 = 4096, while cells_needing_an_owner is 72 = 75 - 3. The arm already excludes background-coloured cells from the owner census, and it already instances only cells the BOARD CANNOT EXPLAIN -- and the board explains every constant background cell in this frame. So `object Dark # arc-colour: 0 arc-instances: all` should yield exactly three instances. I do not know that it does, so I hedged: both Dark rules carry positional guards that pin them to row 5 columns 5-7 by colour arithmetic alone -- lights requires the cell two above and the cell four above to render 1, which in state A is true only of (5,5),(5,6),(5,7), and dims requires the cell itself and the cell two above to render 9, which is true only of cells this manual has already lit. The three outcomes: THREE instances, and I gain 3 cells on every ACTION5 and the panel is complete; ZERO instances, and the two rules are dead text that draws nothing and costs nothing but their own lines, which I will then delete; THREE THOUSAND instances, and the guards keep every one of them inert except the three I want. No outcome draws a wrong pixel. This is the one place in the manual where I am testing the ARM rather than the world, and I say so."
    [depends: key5_underline2_lights, only_visited_cells_have_instances  probe: pending]

  theorem the_five_rule_decision_tree_i_previously_refused_and_now_buy "My predecessor wrote out, verbatim and correctly, the decision tree that draws slot 2's centre pixel (2,6) apart from its eight ring pixels, then refused it under rule 3: five rules to draw nine pixels is not shorter than nine pixels. That accounting was right for a ONE-OFF event and is wrong now that the panel is a recurrent toggle -- ACTION5 has been pressed three times in nine transitions and is now known to be free, so the tree is amortised over every future press, not over one. I bought it, and I re-derived it in a form that needs no `not` and no neighbour disjunction: row 1 is `above(above(?s)) = wall`; row 3 is `colored(above(above(?s)), 1)`, which is false for row 1 because off-board colour tests are false; row 2 is `above(above(above(?s))) = wall and colored(above(?s), 1)`, the second atom excluding row 1; and within row 2, column 5 is `leftof^6 = wall`, column 6 is `leftof^7 = wall and colored(leftof(?s), 1)`, column 7 is `colored(leftof(leftof(?s)), 1)`. The five guards are pairwise contradictory on at least one atom, checked cell by cell against the frame-0 panel, so rule 5 is satisfied by construction. The reverse direction costs only two rules, because in state B the nine cells render just 9 and 0 and all nine go to 1. Net: seven rules for slot 2, zero known-wrong pixels, where the last build had one rule and one deliberately wrong pixel."
    [depends: key5_slot2_centre_darkens, key5_slot2_ring_resets  probe: passed]

  theorem no_rule_in_this_manual_uses_negation_and_that_was_a_choice "Every row and column discrimination here could have been written with `not <cell> = wall`, which the grammar appears to allow and which would have been shorter. I refused it in every case and paid extra atoms instead, because the previous desk's manual never reached the compiler at all and I will not spend a round discovering that `not` before an equality atom is a parse error. Everything separating is therefore done with two facts I have already proven on this arm: k-th `above` is off-board exactly when k exceeds the row, and a colour test on an off-board cell returns false rather than raising. If a future desk wants the shorter forms, the place to try one is a single rule, not eighteen."
    [depends: off_board_cell_terms_evaluate_false_and_that_is_load_bearing  probe: passed]

  theorem off_board_cell_terms_evaluate_false_and_that_is_load_bearing "certify reports 0 step crashes across all adjudicated pairs while key2_body_leaves grounds on meter instances at row 63 whose sixth `below` is row 69. So `colored(<off-board>, k)` is false, not an exception, and `<cell> = wall` is the sanctioned positive test. Eleven of the twenty rules below rest on this."
    [depends: key2_body_leaves  probe: passed]

  theorem the_action_map_after_nine_transitions "PROVEN: ACTION2 is down, now three times over -- 24 pixels leave rows 8-12 and 24 arrive at rows 14-18 at t2, t6 and t8, identical to the pixel. ACTION5 returns the body to rows 8-12 from rows 14-18, three times. NEGATIVE INFORMATION, stated as negative: ACTION1 at spawn did not move a body that had open floor to its right and below it, so ACTION1 is not right and not down. ACTION3 at lattice (2,2) did not move a body that had open floor above and below it, so ACTION3 is neither up nor down; left and right are both void there, so ACTION3 is left, right, or inert. ACTION4 at the same cell did the same nothing -- but it BURNED THE METER, and under the action-keyed reading that makes ACTION4 a movement key whose move was blocked by void on both sides, hence left or right, while ACTION1 and ACTION3, which burned nothing, are not movement keys at all. THE PROBE THIS HANDS ME: from spawn, lattice (1,2), left is void and right (1,3) is open floor. Press ACTION4 there. If the body steps six pixels east, ACTION4 is right and it is the key that walks lattice row 1 toward the knob; if nothing moves, ACTION4 is left and no key I have found goes east. Either answer is worth more than anything else on the board, and it costs one meter tick under every surviving reading, which is why it is not also the meter probe."
    [depends: key2_body_leaves, the_meter_collapsed_to_two_readings_and_only_one_is_expressible  probe: pending]

  theorem action5_is_respawn_or_up_and_the_separator_is_now_cheap "Three ACTION5 presses, three returns from rows 14-18 to rows 8-12, and every one of them happened to be exactly one lattice cell below spawn, so 'respawn' and 'up' still fit identically. Two things changed. First, the panel toggles on ACTION5 and an up-key has no business toggling a panel, which tilts me towards respawn without deciding it. Second, and this is the operational change: the token budget was a fiction, so ACTION5 is FREE -- it does not even burn the meter, 3/3 -- and the separator has gone from last-resort to cheap. Press ACTION2 twice to reach lattice (3,2), rows 20-24, then press ACTION5: my rules predict the body reappears at rows 8-12, because key5_body_respawns can only ever light the original 24 spawn-ring instances, while the up-reading predicts rows 14-18. The manual announces its own refutation here with no extra machinery. There is a cheaper half-test available first: press ACTION5 while the body is ALREADY at spawn. My rules then predict the panel toggles and nothing else moves; if the panel does not toggle, the toggle is bound to body motion rather than to the key."
    [depends: key5_body_respawns, key5_body_clears  probe: pending]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me, for the two commands the playbook ranks highest. ACTION5 FROM SPAWN: I predict exactly 23 changed cells -- slot 1's eight ring pixels 2 to 9, underline 1's three 0 to 9, slot 2's eight ring pixels 9 to 1 and its centre 0 to 1, underline 2's three 9 to 0 -- and no change anywhere in rows 6-63. If the meter also burns at (63,59), parity beats action-keying and I will delete the three burn rules next round. If the body moves, ACTION5 is not respawn-in-place and I learn that instead. ACTION4 FROM SPAWN, if it is right: 24 pixels of rows 8-12 cols 14-18 go to 5, 24 pixels of rows 8-12 cols 20-24 go to 9, and one meter cell burns; my manual has no rule for ACTION4 except the burn, so I predict 48 wrong cells, and cols 20-24 carry no instances yet so I could not draw them even with the rule. 48 wrong cells is the correct price of the first step onto fresh ground and I will pay it. ANYTHING OTHER than 23-or-24 for the first and 0-or-49 for the second refutes my reading of the lattice or of the arm's instancing, and I would rather learn it from a counted diff."
    [depends: action5_is_respawn_or_up_and_the_separator_is_now_cheap, the_action_map_after_nine_transitions  probe: pending]

  theorem dynamic_census "Exactly 75 cells have ever changed and every one has an owner in this build. 23 are the panel: slot 1's eight ring pixels (9 in state A, 2 in B), underline 1's three (9 / 0), slot 2's nine (solid 1 in A; eight 9 plus centre 0 in B), underline 2's three (0 / 9). 24 are the spawn ring, rows 8-12 cols 14-18 minus the aperture (10,16), which never changes and is board. 24 are the same ring six rows down, rows 14-18 cols 14-18 minus its aperture (16,16). 4 are the right end of the row-63 bar, (63,60)..(63,63). 23+24+24+4 = 75. Frame-0 colours split them 39 colour-9 (8 slot-1 ring + 3 underline-1 + 24 spawn ring + 4 meter), 9 colour-1 (slot 2), 24 colour-5 (the lower ring, floor at frame 0), 3 colour-0 (underline 2). 39+9+24 = 72 = cells_needing_an_owner exactly, and the 3 colour-0 cells are the difference between 75 and 72 -- which is the whole basis of the Dark gamble."
    [probe: passed]

  theorem only_visited_cells_have_instances "Re-verified on this build's numbers: constant 4021 + dynamic 75 = 4096, and 39+24+9 = 72 = cells_needing_an_owner. The arm instances exactly the cells that have already changed, typed by their frame-0 colour. Three consequences I keep paying for and keep accepting. The corridor ahead carries no instances, so the first step onto never-yet-changed ground costs 48 wrong cells and the round after that the same rule text draws them for free -- the manual heals one step behind the body. The next meter cell to burn cannot be drawn. And the body CHANGES TYPE as it walks: its pixels are Glyph9 at rows 8-12, Vacated at rows 14-18, and will be Vacated again at rows 20-24 because that floor renders 5 at frame 0."
    [depends: key2_body_arrives  probe: passed]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "A descent from rows 14-18 to rows 20-24 needs Vacated pixels going 9 to 5, which no rule of mine does -- key2_body_leaves is typed Glyph9 and only clears the spawn ring. The missing text, verbatim for whoever witnesses it: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. It is inert everywhere in the present frame and I am fairly sure it is true. It stays out because nothing witnesses it: the body has descended three times and every descent started at spawn. One press of ACTION2 from lattice (2,2) buys it. Note the contrast with the eighteen rules I DID write, each of which has a transition under it."
    [depends: key2_body_arrives  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; the rows and columns congruent to 1 mod 6 are separator strips. Colour 5 is floor, 0 is void, 8 is machinery, and the body is a rigid 5x5 colour-9 block with a one-pixel aperture at its centre. Read from this frame: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are open, C=6 holds the knob, C=7 is void; R=2 is floor at cols 13-19 and 25-31, so C=2 and C=4; R=3 is floor cols 13-31, so C=2,3,4; R=4 and R=5 are floor only at cols 13-19, so C=2; R=6 is the comb, whose only floor pixels are (39,14) and (41,14), so nothing there is enterable; R=7 is C=2; R=8 is floor from col 13 to col 48. The separator rows 7,13,19,25,31,37,43,49 are floor across column 2 and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb, and row R=1 is continuous from C=2 to C=6."
    [depends: key2_body_arrives  probe: pending]

  theorem the_hole_is_an_aperture_and_only_the_ring_needs_floor "A destination lattice cell needs its 24 RING pixels to render floor; the centre may render anything, because key2_body_arrives fires on a destination pixel only when the pixel six rows above renders 9, and at the destination centre that pixel is the source centre, which renders floor. Witnessed three times now: (16,16) stayed 5 at t2, t6 and t8 while its 24 neighbours turned 9. This matters because it is the only reading under which the winning cell is enterable: lattice (8,7) is rows 50-54 cols 44-48 and its centre (52,46) renders colour 9, the socket pip. The map places something at a hole-centre exactly twice -- the pip at (52,46) and the knob's centre pixel at (10,40) -- which I read as the designer saying the body acts through its aperture, and record as a reading, not a law."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_socket_is_a_keyhole_and_names_the_winning_position "Rows 49-55 by cols 43-49 form a 7x7 colour-9 bracket: top bar row 49, bottom bar row 55, right wall col 49, and col 43 rows 50-54 is FLOOR, so it is open on the left. Inside it one lone colour-9 pixel at (52,46). Overlay the body standing in lattice (8,7): flush on three sides, pip showing through the aperture. That is a plug and a socket drawn to the pixel, and it names the winning position without my guessing a goal predicate -- the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in ten frames, so it is board and no object owns it; the first time the body enters, those 24 pixels become dynamic and the manual can finally speak about them."
    [depends: the_hole_is_an_aperture_and_only_the_ring_needs_floor  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood from spawn and the body reaches eleven lattice cells: (1,2),(1,3),(1,4),(1,5),(2,2),(2,4),(3,2),(3,3),(3,4),(4,2),(5,2). The socket (8,7) is not among them and nothing in R=7 or R=8 is, because every route south crosses (6,2) and 23 of that cell's 25 pixels render colour 8. The comb is not an obstacle to route around, it is the door. Its wiring is drawn in the open: colour 8 leaves the comb along row 40 from col 14 to col 40, climbs col 40 through rows 12 to 39 in a three-wide channel flanked by cols 39 and 41, and ends in the 3x3 colour-8 knob at rows 9-11 cols 39-41, inside lattice (1,6). Not one colour-8 pixel has moved in ten frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule."
    [depends: the_maze_is_a_six_pixel_lattice  probe: pending]

  theorem the_knob_is_the_only_thing_within_reach_and_i_do_not_know_how_it_is_pressed "Ten of the eleven reachable cells are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from the knob's cell (1,6) only by separator col 37, which is floor. Lattice (1,6) contains ten colour-8 pixels, nine of them ring pixels of the cell, so even under the aperture rule the body cannot stand there while 8 is solid. Either 8 is walkable and key2_body_arrives is wrong at the knob; or the knob answers to proximity from (1,5); or it answers to a key never pressed. My rules make the first self-announcing: if the body enters a colour-8 cell my manual predicts it stays put and the world says otherwise, in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem two_actions_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1..ACTION5 plus RESET; the alphabet is ACTION1..ACTION7. Two commands are entirely unconstrained, and in this family one is normally a click carrying coordinates. That matters here: the knob is a 3x3 target the body appears unable to stand on, and a click is the shape of interaction that presses it. I cannot write such a rule -- the guard language admits act=key(6) but has nowhere to put two coordinates, so a click rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT, comb pixels going 8 to 5, and never its precondition."
    [probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Still absent, and for a reason that got sharper this round. `Cart.pos = exit_cell` needs one named instance and arc-instances: all gives me Glyph9_r8c14 and thirty-eight siblings. The socket interior has never changed, so it is board and count() has nothing to range over there, and the pip (52,46) will never become dynamic because the body's aperture leaves it rendering 9. The 24 ring cells do become dynamic on first entry, but `count(Vacated, color = 9) = 24` would then be true of the body standing anywhere it has already been, which is not a win -- a goal true in the wrong states is worse than no goal, because it stops a planner at its first step. Until the body has stood in (8,7) once, the playbook steers by lattice distance to the knob."
    [depends: the_socket_is_a_keyhole_and_names_the_winning_position  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter still scores NEGATIVE on both variants, -2214 and -36598 bits, so its segmentation loses to writing the pixels out and I owe it nothing structural. Its tracks are a useful audit: obj0 (colour 9, 8 cells, 3x3, present in all ten frames) is whichever slot currently holds the hollow-9 ring -- slot 1 in state A, slot 2 in state B, which is itself corroboration of the toggle; obj1 (colour 1, 9 cells, frames 0-4) and obj6 (colour 1, 9 cells, from frame 7) are slot 2 solid in state A before and after the round trip, and obj6 is the single most valuable number any engine produced this round because it is the refutation of the budget theorem; obj5 and obj7 (colour 2, from frames 5 and 9) are slot 1 dimmed; obj2 is an underline; obj4 is the whole row-63 bar of which four cells are dynamic; obj3 is a 1006-cell colour-null blob that swallowed the maze floor, a fair description of my board rather than an object. Every one is already inside Glyph9, Spent, Dark or board, and none gets a type of its own because a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 9 transitions constrain rank 5 of 375 features, null space dimension 370 -- and its one global law restates my census. cegis_miner's refusal remains the most useful sentence here: no track has exactly one move event per transition, 'the world does not narrate as one mover'. True of the arm, false of the world: there is one mover, a rigid 24-pixel ring, and the arm can only see 24 simultaneous recolours, which is why movement costs me a pair of rules per direction instead of one moved() event."
    [probe: passed]

  theorem the_instance_counts_are_build_relative_not_world_facts "The five invariants above are counted at THIS build. Glyph9 was 39, then 37, and is 39 again; board was 4021, then 4023, and is 4021 again -- the only thing that moved was meter cells entering and leaving the observation window. They will change again the moment the body steps onto fresh floor. I state them because they are the arithmetic that proves only_visited_cells_have_instances and the arithmetic behind the Dark gamble, and I say plainly that they describe what has been observed rather than laws of the world. No rule depends on them, and dark_instances is flagged predicted because nothing has verified it yet."
    [probe: passed]
