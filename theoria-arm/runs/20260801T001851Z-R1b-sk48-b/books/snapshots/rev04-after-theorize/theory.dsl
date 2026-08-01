# theory.dsl -- REWRITTEN FROM ZERO. World observed for 6 states / 5 transitions
# (RESET, then ACTION1 ACTION2 ACTION3 ACTION4 ACTION7, one press each).
#
# WHY THERE IS NOTHING LEFT OF THE PREVIOUS MANUAL
#
#   Two separate failures, and only one of them is a bug.
#
#   (1) THE SURPRISE THAT CALLED ME: `theory.dsl is non-empty but
#       generated/theory.py could not be loaded`. Nothing replayed, nothing
#       was checked, responsibility and ambiguity both reported empty. The
#       previous manual carried the line
#           landmark spawn_probe  # arc-cell: carried, coordinates stripped
#       and the grammar says in as many words that a landmark the level
#       cannot place is a HARD COMPILE ERROR. `carried, coordinates
#       stripped` is not `(row, col)`. Thirteen rules depended on that
#       landmark and the whole file died with it. THIS MANUAL DECLARES NO
#       LANDMARK AT ALL. Not as caution -- I have no rule that needs one,
#       and the cheapest way never to repeat that error is to have nothing
#       to get wrong.
#
#   (2) THE WORLD IS NOT THE SAME WORLD. The store says 6 states, 6 steps,
#       5 transitions, dynamic box rows 29-54 cols 10-63, 97 dynamic cells,
#       3999 constant, colours {0,1,2,3,4,5,6,8,9,14}, actions used
#       1,2,3,4,7. The previous manual described 34 states, a dynamic box
#       at rows 8-18 and row 63, 87 dynamic cells, 4009 constant, a five-key
#       alphabet with ACTION5 in it and ACTION7 never pressed, a 6-pixel
#       lattice, a comb, a socket at rows 50-54 cols 44-48. In the CURRENT
#       frame rows 50-54 cols 44-48 read plain 5,5,5,5 and 4 -- there is no
#       socket, no bracket, no colour-8 wire anywhere in the window, and
#       colour 14 exists here and existed nowhere there. Not one census
#       number matches. That manual is not stale, it is about somewhere
#       else, and AMENDING IT WOULD BE A LIE ABOUT WHAT I HAVE SEEN. Every
#       one of its thirty theorems is discarded together with its evidence
#       tags, because an ev: tag naming t29 in a world that has had five
#       transitions witnesses nothing.
#
#   WHAT I CARRY ACROSS IS METHOD AND NOT CONTENT: type by frame-0 colour,
#   check the census closes to the cell before believing a segmentation,
#   price the undrawable leading edge in advance, and never write a rule
#   for a transition whose pixels I have not been shown.
#
# WHAT THIS MANUAL CAN AND CANNOT DRAW, STATED BEFORE ANYONE REPLAYS IT
#
#   t3, t4, t5 are itemised cell by cell in the command log and this manual
#   reproduces all 25 of those recolours exactly. t1 and t2 are reported
#   ONLY as `96 cells changed, rows 30-41, cols 11-22` with a before/after
#   colour multiset -- no cell list, no per-cell colours. I therefore have
#   NO rule for ACTION1 and NO rule for ACTION2, my compiled step returns
#   identity for both, and replay WILL diverge by up to 96 cells at t1 and
#   again at t2. Expect replay 3/5. That is not a defect I can repair from
#   the evidence I was handed; it is repaired by pressing ACTION1 once and
#   reading the next full frame against this one. See
#   the_ninety_six_cell_hole_and_how_it_closes.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Ink1   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Ink2   { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Ink3   { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object Dark   { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Frame6 { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  object Field  { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Ground { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  Ink1   [segment: frame0_colour_1 ev: t3,t4,t5 compress: 9]
  Ink2   [segment: frame0_colour_2 ev: t3,t4,t5 compress: 10]
  Ink3   [segment: frame0_colour_3 ev: t1,t2 compress: 8]
  Dark   [segment: frame0_colour_0 ev: t1,t2 compress: 12]
  Frame6 [segment: frame0_colour_6 ev: t1,t2 compress: 22]
  Field  [segment: frame0_colour_4 ev: t1,t2 compress: 12]
  Ground [segment: frame0_colour_5 ev: t1,t2 compress: 24]

rules:
  rule key3_strip_blanks_ink1 forall ?p in Ink1 [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key3_strip_blanks_ink2 forall ?p in Ink2 [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key7_strip_blanks_ink1 forall ?p in Ink1 [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key7_strip_blanks_ink2 forall ?p in Ink2 [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key4_strip_restores_ink1 forall ?p in Ink1 [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_strip_restores_ink2 forall ?p in Ink2 [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_meter_burns_right_end forall ?p in Ink2 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

laws:
  invariant ink1_instances   count(Ink1) = 9      [status: counted]
  invariant ink2_instances   count(Ink2) = 10     [status: counted]
  invariant ink3_instances   count(Ink3) = 8      [status: counted]
  invariant dark_instances   count(Dark) = 12     [status: counted]
  invariant frame6_instances count(Frame6) = 22   [status: counted]
  invariant field_instances  count(Field) = 12    [status: counted]
  invariant ground_instances count(Ground) = 24   [status: counted]
  invariant board_cells      count(board) = 3999  [status: counted]

  theorem the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout "This is the load-bearing arithmetic of the whole manual and it closes with no slack, which is the only reason I trust a reconstruction built from bounding boxes. The diffs give a dynamic set of exactly two pieces: the 96 cells inside rows 30-41 x cols 11-22 that ACTION1 moved, and the single cell (53,63) that ACTION4 burned. 96 + 1 = 97 = dynamic_cells, and the 12 cells ACTION3 and ACTION7 touch lie inside the 12x12 box, so they add nothing. Now read the CURRENT frame inside that box and sort by colour. Colour 5 appears at rows 30-35 cols 11,12,15,16 and nowhere else in the box: 6 rows x 4 columns = 24 cells. 97 - 24 = 73 = cells_needing_an_owner EXACTLY, which is the store's own count of dynamic cells that are not background. That is not a coincidence I arranged; it is the store agreeing, from a number I did not compute, that my 24 background cells are the right 24. The remaining 73 sort as: 8 colour-3 (cols 13-14 at rows 30,31,34,35), 4 colour-2 (cols 13-14 at rows 32,33), 22 colour-6 and 12 colour-0 (the 6x6 token at rows 36-41 cols 11-16, whose border is 6 except that (38,16) reads 1 and (39,16) reads 2, whose interior is 0 except a 2x2 colour-6 core at rows 38-39 cols 13-14), 8 colour-1 and 4 colour-2 (the strip at rows 38-39 cols 17-22), 1 colour-1 at (38,16), 1 colour-2 at (39,16), 1 colour-2 at (53,63), and 12 colour-4 cells somewhere in rows 30-41 cols 17-22 that no diff itemises. 8+4+22+12+8+4+1+1+1+12 = 73. 4096 - 97 = 3999 = constant_cells. Three independent numbers from the store, all hit on the nose."
    [probe: passed]

  theorem the_twelve_unlocated_field_cells_are_real_and_i_do_not_need_their_addresses "The census above forces exactly 12 dynamic cells of frame-0 colour 4 into rows 30-41 cols 17-22, and no diff tells me which. This does not block the manual, because the arm locates instances BY COLOUR from the frames rather than from anything I write: `arc-instances: all` on Field seats one instance per colour-4 cell the board cannot explain, and the board explains every constant colour-4 cell in the huge field at cols 17-46 and in row 54. So Field gets those 12 and only those 12, wherever they are. What I lose is the ability to write a rule ABOUT them, which costs nothing today because the only transitions that move them are t1 and t2, for which I have no rule at all. My guess -- and I mark it a guess -- is rows 36-37 cols 17-22, i.e. the strip drawn two rows higher, because that is the one 2x6 block adjacent to the strip and because it would make ACTION1 a two-row shift of the strip rather than a repaint. If the next ACTION1 frame shows the strip at rows 36-37 the guess was right and the rule writes itself; if it shows something else I lose nothing but the guess."
    [depends: the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout  probe: pending]

  theorem action2_undoes_action1_and_the_store_proves_it_without_showing_me_a_pixel "distinct_states is 5 against 6 states, so among s0..s5 there is EXACTLY ONE coinciding pair. Enumerate the candidates. s2 -> s3 changed 12 cells, s3 -> s4 changed 13, s4 -> s5 changed 12, so s2,s3,s4,s5 are pairwise distinct except possibly s2 vs s5 -- and those differ at (53,63), 2 against 3, and at the strip, so no. s0 -> s1 and s1 -> s2 each changed 96 cells in the SAME box with the SAME colour multiset going in as coming out. The only pair left that can coincide is s0 and s2, so s0 = s2, and therefore ACTION2 EXACTLY UNDOES ACTION1 on this state. That is a real fact derived from one integer, and it is worth stating because it tells me the pair is a toggle or a two-way selector rather than a one-way commitment, so pressing ACTION1 to learn its pixels is REVERSIBLE and cannot strand me. It does NOT tell me what either key does, and I refuse to invent one: a 96-cell change whose colour multiset is preserved is equally consistent with a shift, a rotation, a swap of two sub-pictures, or a repaint, and I have seen zero of the pixels."
    [depends: the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout  probe: passed]

  theorem the_ninety_six_cell_hole_and_how_it_closes "The largest defect in this manual, named before certify names it. My compiled step is total, so where no rule fires it says `nothing happens` in the same voice it uses for things it has seen -- and for ACTION1 and ACTION2 it will say `nothing happens` while the world moves 96 cells. That silence is FORGED and it is the worst kind, because I know it is false rather than merely unwitnessed. I will not repair it by guessing, because a wrong 96-cell rule is worse than no rule: it would fire on future states, cascade into the strip rules, and it would be unfalsifiable-looking rather than obviously absent. THE REPAIR IS ONE COMMAND. The evidence brief hands me the full current frame every round, and the diff channel only itemises small changes -- 12 and 13 cells were itemised, 96 was summarised to a bounding box. So the pixels of ACTION1 are unreachable through the diff and reachable through the FRAME: press ACTION1, receive the resulting frame next round, subtract it from the frame I hold now, and the 96 cells are mine cell by cell. This is the single highest-value command on the board and the playbook ranks it first."
    [depends: action2_undoes_action1_and_the_store_proves_it_without_showing_me_a_pixel  probe: pending]

  theorem action3_and_action7_have_the_same_net_effect_and_action4_inverts_it "The three transitions I can actually see. t3 (ACTION3) recoloured all twelve cells of rows 38-39 cols 17-22 to colour 4. t5 (ACTION7) recoloured the same twelve cells to colour 4 again, from the same starting pattern, cell for cell identical to t3's list. t4 (ACTION4) recoloured those twelve back and burned one more cell. So on this state ACTION3 and ACTION7 are indistinguishable in net effect, 12/12 each, and ACTION4 is their inverse plus a side effect. The restored pattern is row 38 = 2,1,1,2,1,1 and row 39 = 1,1,2,1,1,2 across cols 17-22, which is a period-3 stripe: row 39 equals row 38 shifted one column left, so the 2s lie on a diagonal of slope one. This is why my two restore rules can be written without a single positional guard -- the arm types each instance by its FRAME-0 colour, so `recolour every Ink1 that currently reads 4 back to 1, and every Ink2 that currently reads 4 back to 2` reproduces the diagonal exactly, at no cost in rule length, and the pattern is carried by the type assignment rather than by anything I had to describe. That is the one place in this manual where a concept genuinely pays: two rules and no coordinates for twelve cells of structured pattern."
    [depends: the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout  probe: passed]

  theorem the_strip_guard_is_forced_and_i_checked_every_rival_instance "The blank rules must fire on the twelve strip cells and on NO other Ink1 or Ink2 instance, and the guard I use is `colored(above(above(?p)), 4)`. Here is the check, instance by instance, in the pre-blank state. Row-38 strip cells: two above is row 36 cols 17-22, which reads 4. Row-39 strip cells: two above is row 37 cols 17-22, which reads 4. Both pass. Now the rivals. (38,16) is Ink1: two above is (36,16), which reads 6 -- fails. (39,16) is Ink2: two above is (37,16), 6 -- fails. The four bar cells at rows 32-33 cols 13-14 are Ink2: two above is rows 30-31 cols 13-14, which read 3 -- fails. (53,63) is Ink2: two above is (51,63), which reads 5 -- fails. Every rival is excluded and every target is included, so coverage is 8/8 and 4/4 with no leakage. I considered and REJECTED the shorter guards: `colored(above(?p), 4)` catches only row 38 and needs a second rule for row 39, and `colored(below(?p), 4)` catches row 39 but ALSO catches (53,63), because row 54 is solid colour 4 from edge to edge -- that near miss is exactly the kind that would have cost a round, and it is why I checked all ten Ink2 instances rather than the obvious four."
    [depends: action3_and_action7_have_the_same_net_effect_and_action4_inverts_it  probe: passed]

  theorem the_seven_rules_cannot_clash_and_here_is_the_case_analysis "Constraint 5 demands exactly one successor per state and action, so pairwise exclusivity is checked rather than assumed. The seven rules partition first by action: {key3_strip_blanks_ink1, key3_strip_blanks_ink2} on key 3, {key7_strip_blanks_ink1, key7_strip_blanks_ink2} on key 7, {key4_strip_restores_ink1, key4_strip_restores_ink2, key4_meter_burns_right_end} on key 4. Across groups no clash is possible. Inside the key-3 and key-7 groups the two rules quantify over DISJOINT instance sets, Ink1 and Ink2, so no instance is ever claimed twice. Inside the key-4 group, key4_strip_restores_ink1 is over Ink1 and the other two are over Ink2; those two are separated by their colour test, `colored(?p, 4)` against `colored(?p, 2)`, which cannot both hold of one cell in one state. Zero clashes by construction, and no rule anywhere in this manual uses `not`, so there is no negation whose scope I could have got wrong."
    [depends: the_strip_guard_is_forced_and_i_checked_every_rival_instance  probe: passed]

  theorem the_row_53_burn_has_exactly_one_witness_and_three_live_readings "At t4, and only at t4, (53,63) went 2 to 3. Row 53 reads solid colour 2 from col 10 to col 62 with col 63 now 3, and it is the only row in the frame with that colouring, so I read it as a bar consumed one cell at a time from the right end -- but I have ONE burn in five transitions and I will not pretend that is a law. THREE READINGS ARE ALIVE. (A) The burn is keyed to ACTION4: my rule encodes this because it is the only reading that fires exactly once in the observed history and never elsewhere. (B) The burn is keyed to the RESTORE event rather than the key, so any action that repaints the strip burns. (C) The burn counts something the frame does not show -- a command counter, an attempt counter -- in which case no guard in this language can express it, exactly as the previous world's meter could not be expressed. Note what SEPARATES them cheaply: t2 was also an even-index command and did NOT burn, which kills plain index parity outright; and pressing ACTION4 now, when the strip is already blank so nothing is there to restore, splits (A) from (B) in a single press -- (A) predicts nothing, since (53,63) already reads 3 and my rule needs colour 2, while (B) predicts nothing either. The honest separator is ACTION4 pressed twice with a restore in between, which is two commands and not one, so I rank it below the ninety-six-cell hole."
    [depends: action3_and_action7_have_the_same_net_effect_and_action4_inverts_it  probe: pending]

  theorem the_next_burn_is_undrawable_and_i_price_it_now_rather_than_be_surprised "If row 53 really is a bar consumed from the right, the next cell to go is (53,62), and (53,62) HAS NEVER CHANGED. The arm seats instances only on cells the board cannot explain, a never-varying cell is precisely what the board explains, so (53,62) gets no instance, no object owns it, and NO RULE I CAN WRITE WILL DRAW ITS FIRST CHANGE. This is a property of the arm, not of my rules, and it is permanent for this level: every burn costs me exactly one wrong pixel on the transition where it happens and zero thereafter, because the cell becomes dynamic the moment it changes and my Ink2 type picks it up on the next instancing. I reject the two tempting repairs in advance. Declaring a second colour-2 type without arc-instances seats one instance at an unspecified cell that Ink2 may also claim, which is the double claim constraint 5 forbids. Declaring a landmark does not help, because every event in this language takes an object as its first argument and a landmark is a cell. So: when a refutation's divergence set is the single cell immediately left of the burned end of row 53, the manual is not implicated, and it must not be read as one."
    [depends: the_row_53_burn_has_exactly_one_witness_and_three_live_readings  probe: passed]

  theorem two_keys_have_never_been_pressed_and_one_of_them_may_be_a_click "actions_used is ACTION1, ACTION2, ACTION3, ACTION4, ACTION7 plus RESET; the alphabet is ACTION1..ACTION7. ACTION5 and ACTION6 are entirely unconstrained after six states, and in this action family one of the higher indices is normally a click carrying coordinates. That the world already answers to ACTION7 is itself informative -- the previous world in this series never used it and this one does, on its fifth command -- so nothing about which indices are `the movement keys` transfers. I cannot write a click rule: the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a click drives this world my manual can record its EFFECT and never its precondition. Until one of these keys is pressed my manual predicts silence for both, and that silence is unwitnessed -- a forged death certificate, not a finding."
    [probe: pending]

  theorem what_the_frame_shows_that_no_rule_of_mine_touches "Stated so that the parts of the picture I have not explained are visible rather than absent. FIRST, the 6x6 token at rows 36-41 cols 11-16: a colour-6 border, a colour-0 interior, a 2x2 colour-6 core at rows 38-39 cols 13-14, and two border cells that are NOT 6 -- (38,16) reads 1 and (39,16) reads 2, in the same two rows as the strip and immediately to its left. That alignment says the token and the strip are one widget read left to right, and the 1 and the 2 at col 16 look like the first two entries of the same sequence the strip continues; but they did not blank at t3, t5 or restore at t4, so whatever they are, they are not part of what ACTION3 and ACTION4 toggle. SECOND, the vertical bar at cols 13-14 rows 29-35: colour 3 except rows 32-33, which are colour 2. It sits directly above the token, two cells wide, with a two-row colour-2 marker a third of the way down -- the shape of a slider or a gauge. It is entirely inside the ACTION1 box, so ACTION1 or ACTION2 almost certainly moves that marker, and that is the single most likely meaning of the 96 cells. THIRD, the colour-14 block at rows 31-34 cols 42-45 and everything of colours 8 and 9 elsewhere in the frame: constant in all six frames, therefore board, therefore unowned and undrawable if they ever move. I name all three rather than model them."
    [depends: the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout  probe: pending]

  theorem the_goal_section_is_absent_on_purpose_and_it_costs_me_a_planner "There is no goal section, so is_goal compiles to False and no plan can terminate. I could have invented one and I decline, because a goal true in the wrong states is worse than no goal: it stops a planner at its first step and it is a claim about winning that six frames cannot support. Nothing in the history has shown a win, a score, or a state change other than NOT_FINISHED. The candidate predicates all fail on inspection. `count(Ink2, color = 3) = 1` is true right now, in a state that is plainly not a win. `count(Ink1, color = 4) = 8` is true in every blanked-strip state including the current one. There is no instance I could name for a positional goal because arc-instances: all yields Ink1_r38c18 and eight siblings rather than anything called Ink1. The price is explicit: nothing ranks one command above another except whether it is predicted to change pixels and what it would witness, so the playbook does the ranking and it does it on epistemic value, not on distance to a target."
    [depends: the_census_closes_to_the_cell_and_that_is_why_i_believe_the_layout  probe: passed]

  theorem the_cascade_channel_carries_one_bit_that_i_discard_by_construction "cascade_lengths are 1 and 2, and max_frames_in_one_command is 2. Four commands returned two frames -- t1, t2, t3, t4 -- and t5, the ACTION7, returned one. That is interesting precisely because t5's NET effect is identical to t3's, cell for cell: the same twelve cells to colour 4. So ACTION3 and ACTION7 differ in their animation and agree in their result, which is the only evidence I have that they are different commands at all rather than aliases. My semantics say cascade single_frame, which compares only the net, so I discard the intermediate frame of every two-frame command unread and my manual cannot distinguish ACTION3 from ACTION7 anywhere. I record this as a limitation of my own semantics rather than a fact about the world. LIVE PREDICTION, free to check: if ACTION7 is pressed again from a state with the strip showing, it should return ONE frame while ACTION3 returns two. If ACTION7 ever returns two, this is not a stable property of the key."
    [depends: action3_and_action7_have_the_same_net_effect_and_action4_inverts_it  probe: pending]

  theorem what_the_engines_gave_me_and_what_i_took "cegis_miner refused on all four tracks -- two for narrating vanish or recolor when it mines only move and none, two because the object is absent at frame 0 -- and its verdict, `the world does not narrate as one mover`, I ACCEPT as literally true here: nothing in six frames translates, everything recolours in place, and no object of mine has a pos that ever changes. That is a real finding and it is why this manual contains not one moved() event. mdl_segmenter reports NEGATIVE gain on both variants, -4037 bits with connected_components(4) and -10409 bits when split by colour, meaning its script costs more than writing the pixels out; by constraint 3 that segmentation has not earned its place and I take NO structure from it. Its four tracks are also unusable as they stand: obj0 and obj2 and obj3 are 13x36 blobs of 436-440 cells that have swallowed the whole colour-4 field along with everything embedded in it, and obj1 is a 2x54 strip present in all six frames, which is row 53 and row 54 fused. zero_space self-reports THIN in its own words -- 5 transitions constrain rank 3 of 679 features, null space dimension 676 -- and its single global law is a list of cells that is my dynamic set, so it corroborates the census and nothing else. Three engines, one accepted verdict, zero accepted structure."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. The body of this world, if it has one, is invisible to me; what I hold is a state where the strip at rows 38-39 cols 17-22 reads colour 4 and (53,63) reads colour 3. ACTION4: my manual predicts TWELVE cells, the strip restored to the 2,1,1,2,1,1 / 1,1,2,1,1,2 diagonal, and NO burn, because key4_meter_burns_right_end needs colour 2 at the right end and finds colour 3. If a burn happens anyway at (53,62) I cannot draw it and reading (C) of the burn theorem gains. ACTION3 and ACTION7: my manual predicts ZERO cells, since the strip is already 4 and both blank rules require colour 1 or 2. That silence is unwitnessed for both keys and I would believe it, but it buys almost nothing. ACTION1: my manual predicts ZERO cells and I KNOW that is false -- 96 cells will move and the resulting frame closes my largest hole. This is the press I want and the playbook says so. ACTION2: same 96 cells, but it returns to s0, a state I already hold, so it teaches strictly less than ACTION1. ACTION5 and ACTION6: my manual predicts zero cells with no witness whatever; either answer is new information and both are cheap. If ACTION1 is pressed and the frame comes back unchanged, then s5 is not s0-like in the way I assumed and this manual is wrong about more than its silences."
    [depends: the_ninety_six_cell_hole_and_how_it_closes, the_row_53_burn_has_exactly_one_witness_and_three_live_readings  probe: pending]
