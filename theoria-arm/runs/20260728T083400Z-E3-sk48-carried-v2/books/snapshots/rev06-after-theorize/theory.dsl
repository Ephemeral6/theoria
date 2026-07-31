# theory.dsl -- SECOND DRAFT. The first draft was written blind against frame 0
# and came back with two hard numbers: responsibility 0/4096 unexplained, and
# replay 4/5 with first divergence at t=0. Both of those are results, not
# scores, and this round is mostly about reading them.
#
# WHAT THE CERTIFY OUTPUT ACTUALLY PROVED
#
#   (1) responsibility ok, 0 unexplained. The pre-registered question
#       instance_anchoring_has_one_alternative resolves in favour of the first
#       branch: arc-instances: all enumerates cells of the declared colour in
#       FRAME 0 that the board cannot explain. The 12 strip cells are NOT
#       double-claimed and (53,63) is NOT double-claimed. Six colour classes
#       own all 73 cells. That question is now closed and I write it as passed.
#
#   (2) replay says 4/5 and first_divergence says t=0. Those two look
#       contradictory and they are not: they can only both be true if replay is
#       OPEN LOOP -- the manual is run forward from frame 0 without being
#       resynced to the world. My manual is silent on key(1) and key(2), so its
#       state after both is still frame 0; the world went S0 -> S1 -> S2 and
#       matched again at t=1. That is a MEASUREMENT, from the harness rather
#       than from my arithmetic, that S2 = S0 exactly, cell for cell. The
#       deduction in frame_zero_is_reconstructed_exactly is no longer a
#       deduction. It is confirmed, and with it the whole reconstruction, since
#       t2..t5 then replayed exactly on top of it.
#
#   (3) 4/5 is one better than the 3/5 I pre-registered. I predicted t1 and t2
#       would both fail. t2 passed for the reason above. I record the miss.
#
# WHAT I LEARNED FROM THE FRAME THAT I HAD NOT SEEN
#
#   (4) Row 29, cols 13-14, holds colour 3 -- and row 29 is BOARD. The true
#       dynamic box is rows 30-53 x cols 11-63 (the reported [29,10,54,63] is
#       that box padded by one and clipped), so (29,13) and (29,14) have never
#       varied. Colour 3 at cols 13-14 is the signature of a COLLAPSED SLOT.
#       There is therefore at least one more slot above row 29, at rows 24-29,
#       which has never been selected and is consequently indistinguishable
#       from furniture. Rows 42 and below are uniform background, so slot B at
#       rows 36-41 is the LAST slot. The panel is a column of slots running
#       upward from row 41, key(1) moves the selection up one slot and key(2)
#       moves it down one slot. That reading, not the two-slot toggle I wrote
#       last round, is what the board itself says.
#
#   (5) The badge -- the 4x4 colour-14 block at rows 31-34 x cols 42-45 -- is
#       vertically centred on row 32.5, which is exactly the centre of SLOT A
#       (rows 30-35) and exactly the rows of STRIP A. Slot B's lane (rows
#       36-41) has no badge: cols 17-46 are uniform colour 4 there. So the
#       arena is lanes, one per slot, strip at the left end and badge at the
#       right end, and slot A has a task where slot B has none.
#
#   (6) In S1 the world drew strip A as 2 1 1 2 1 1 on row 32 -- the same six
#       colours strip B shows on row 38 in S0. Six of twelve cells agree. The
#       strip may be one display that follows the selection rather than two
#       stored patterns.
#
# WHAT I REFUSE TO DO, AND THIS TIME WITH A PROOF
#
#   The swap stays out of `rules:`. Last round I said it was inexpressible and
#   waved at "96 simultaneous recolourings". That was an assertion. This round
#   I checked it and it is a theorem with named witnesses: three pairs of cells
#   that are IDENTICAL in colour and in all four neighbour colours in frame 0
#   and that must take DIFFERENT colours under key(1). No guard in the
#   documented language separates them, and constraint 5 forbids writing two
#   rules that both fire. See the_swap_is_provably_inexpressible_here. The
#   refusal is now earned rather than pleaded.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Casing { pos: Coord, color: Int }  # arc-colour: 6  arc-instances: all
  object Cavity { pos: Coord, color: Int }  # arc-colour: 0  arc-instances: all
  object Rail { pos: Coord, color: Int }  # arc-colour: 3  arc-instances: all
  object Pip { pos: Coord, color: Int }  # arc-colour: 1  arc-instances: all
  object Stud { pos: Coord, color: Int }  # arc-colour: 2  arc-instances: all
  object Erased { pos: Coord, color: Int }  # arc-colour: 4  arc-instances: all
  landmark slot_a_head  # arc-cell: (30, 11)
  landmark slot_b_head  # arc-cell: (36, 11)
  landmark slot_c_head  # arc-cell: (24, 11)
  landmark strip_a_head  # arc-cell: (32, 17)
  landmark strip_b_head  # arc-cell: (38, 17)
  landmark strip_c_head  # arc-cell: (26, 17)
  landmark rail_witness  # arc-cell: (29, 13)
  landmark meter_tip  # arc-cell: (53, 63)
  landmark meter_next  # arc-cell: (53, 62)
  landmark badge_cell  # arc-cell: (31, 42)
  Casing [segment: colour_class_6 ev: t0-t5 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t5 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t5 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t5 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t5 compress: 10]
  Erased [segment: colour_class_4 ev: t0-t5 compress: 12]

events:
  event recolored(o, c)

# The seven rules below are UNCHANGED from the draft that replayed t3, t4 and
# t5 exactly. Nothing observed this round bears on them, so nothing is touched.
# Their negative neighbour guards are ugly and I defend them, at cost, in
# colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_advances_the_meter forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and colored(above(?p), 5) and colored(below(?p), 4) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 10 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 73 [status: proven]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I was shown with two edits: rows 38-39 x cols 17-22 hold 2 1 1 2 1 1 over 1 1 2 1 1 2 instead of colour 4, and (53,63) holds 2 instead of 3. Last round this was a deduction from distinct_states = 5 plus two arithmetic closures, 97 dynamic cells and 73 owned cells, neither of which I had used to build it. This round the harness confirmed it independently: replay reports 4/5 with its first divergence at t=0, which is only consistent with open-loop replay, which in turn means the world returned to my frame 0 after key(2) and then matched me for three more transitions. Load-bearing, and now measured rather than inferred."
    [probe: passed]

  theorem replay_is_open_loop_and_that_is_what_four_of_five_means "the manual is run forward from frame 0 without resync. My manual is a no-op on key(1) and key(2), so it sat at frame 0 through both; the world left and came back; from t=2 onward the strip rules carried it. The single failing transition is t=0, the key(1) selector move, 96 cells wrong. This has a consequence I must design around: a wrong rule for key(1) would not merely fail at t=0, it would DESELECT the manual from the world for the rest of the trace and lose the three transitions I currently get for free. Silence on the selector is worth more than a guess at it, and that is a numerical argument, not a temperamental one."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied, so they are board. Colour 3 at cols 13-14 is exactly the signature of a collapsed slot -- it is what slot A shows at its four outer rows. So there is a further slot at rows 24-29 that has never been selected, and probably more above it, all of them invisible to me because an unselected slot is a constant drawing and a constant drawing is board by definition. Below, rows 42 onward are uniform background, so slot B at rows 36-41 is the last slot. key(1) took the selection from B up to A and key(2) took it back down. I therefore read key(1) as move-selection-up-one-slot and key(2) as move-selection-down-one-slot, in preference to the two-slot toggle I wrote last round. The two readings differ on a probe that costs nothing: from the current state, with the bottom slot selected, a move reading predicts key(2) does nothing at all and a toggle reading predicts 96 cells change. My manual, being silent, already commits to the move reading, so the next key(2) press scores it."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_arena_is_lanes_and_only_slot_a_has_a_badge "the arena is colour 4 over cols 17-46, rows 29-41 at least and probably further up where I cannot see. The 4x4 colour-14 badge at rows 31-34 x cols 42-45 is centred on row 32.5, which is the centre of slot A and the exact rows of strip A. Slot B's band, rows 36-41, is uniform colour 4 from col 17 to col 46 -- no badge. So the arena reads as one lane per slot, a 2x6 strip at the lane's left end and a badge at its right end, and slot A carries a task that slot B does not. Slots above row 29 may carry badges too and I would not know, because their badges would never have varied. This is the only structure in the arena that is neither strip nor fill and it remains the natural candidate for what the strips are compared against. Zero transitions bear on it."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_strip_may_be_one_display_rather_than_two "in S1 the world drew strip A row 32 as 2 1 1 2 1 1, which is exactly what strip B row 38 shows in S0. Six of the twelve cells agree; the divergence report was truncated at 24 cells and row 33 was never shown to me. Either the strip is a single display that follows the selection, or each slot has its own pattern and the two agree on their first row. The separator is free and comes with the selector probe: select slot A and read row 33. If it is 1 1 2 1 1 2 the two are the same display or the same pattern; if it differs, patterns are per-slot and the strip is slot data."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and I cannot write it, and this is now a proof rather than a complaint. A guard sees a cell's own colour and the colours of its four neighbours, and nothing else -- there is no coordinate, no row band, no distance. Under key(1) the new colour of a panel cell is a function of its offset within a six-row period, and that offset is not determined by the four neighbour colours. Three witness pairs, each identical in colour and in all four neighbour colours in frame 0, each required to take different colours: (30,12) and (31,12) are colour 5 with above 5, below 5, left 5, right 3, and must become 6 and 0; (41,12) and (41,13) are colour 6 with above 0, below 5, left 6, right 6, and must become 5 and 3; (32,18) and (32,20) are colour 4 with all four neighbours colour 4, and must become 1 and 2. Stronger still, the five cells (30,16), (31,16), (32,16), (33,16), (34,16) are all colour 5 with above 5, below 5, left 5, right 4 and must become 6, 6, 1, 2, 6 -- four distinct answers to one indistinguishable question. Constraint 5 forbids two rules firing on one object in one transition, so there is no escape by writing both. The swap does not go in the manual."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem nesting_would_break_the_ties_and_would_still_fail_the_gain_test "the proof above assumes cell expressions take an instance or a landmark, as the grammar documents. If above(above(?p)) in fact compiles, the ties break: a chain of five nested neighbours can count a cell's distance from the panel edge and so recover its offset in the period. I decline that route for two reasons and I want both on the record. First, a guard form the grammar does not list is a parse risk, and a manual that fails to parse loses everything including the three transitions it currently gets right. Second, and decisively, distinguishing 96 cells by 96 distinct neighbour chains is writing the pixels out with extra syntax: it would cost more symbols than the 96 pixels it explains, which is exactly the failure constraint 3 names. The swap is inexpressible without nesting and uncompressible with it, so it stays out either way."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_meter_can_tick_only_once_in_this_manual_and_the_second_tick_is_pre_registered "row 53 is a colour-2 bar running at least cols 10 to 62 with its rightmost cell at col 63, and (53,63) is the only cell of it that has ever varied. My rule key4_advances_the_meter recolours that one Stud instance from 2 to 3 and then guards itself off, because it now holds colour 3. There is no instance at (53,62): that cell is constant in frame 0 and therefore board. So this manual predicts the meter never advances again, which is almost certainly wrong. I pre-register the shape of the failure exactly: the second key(4) press diverges at ONE cell, (53,62), 2 -> 3, and nowhere else. That divergence would confirm the bar reading rather than refute the manual, and the repair is one line -- the arm will hand (53,62) an instance once it has varied, and stud_population goes from 10 to 11. A divergence anywhere other than (53,62) refutes the bar reading and I would rebuild the meter from what is reported."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_strip_toggles_and_only_key_four_costs_anything "key(3) at t3 and key(7) at t5 each blanked all 12 cells of the selected slot's strip to arena colour 4; key(4) at t4 restored exactly the same 1 and 2 pattern cell for cell and additionally advanced the meter. The pattern is therefore stored somewhere the frame does not show and blanking does not destroy it. Over five commands the meter ticked once and only under key(4), so key(4) is the metered action and keys 1, 2, 3 and 7 are free. One witness each: key(3) and key(7) may be a blank and a toggle that agreed because the strip was shown both times, and key(4) may be a show or a toggle that agreed because the strip was blank. Nothing in the record separates blank from toggle for any of the three, and the cheapest separator is a second consecutive key(3) from a shown strip."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_sign_of_the_meter_is_unknown_and_that_matters_more_than_its_length "I have been calling (53,63) a meter and treating its tick as a cost, and I have no evidence for the sign. Colour 2 is the bar and colour 3 is what one unit became; colour 3 is also the colour of an unselected slot's rails, and colour 2 is also the colour of half the strip. A bar consumed right to left and a score accumulated right to left look identical after one tick. If it is a cost, key(4) should be rationed; if it is a score, key(4) is the only action that has ever accomplished anything and should be repeated. This is the single largest open question about what to do next, it is worth more than any refinement of the drawing, and one further key(4) press resolves the direction while leaving at least fifty-two units of whatever it is."
    [depends: the_meter_can_tick_only_once_in_this_manual_and_the_second_tick_is_pre_registered  probe: pending]

  theorem cascade_length_carries_no_signal_here "t1, t2, t3 and t4 returned 2 frames each and t5 returned 1, yet t3 and t5 produced identical 12-cell effects. Frame count does not track the magnitude or even the presence of change and must not be used as a motion detector. What it may still carry is that ACTION7 and ACTION3 are genuinely different actions that happened to agree in this state -- one animates and one does not. That is a hint about key identity, not about world state."
    [probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans slot A's core, a port cell of the expanded slot, four strip cells and the meter tip -- four unrelated roles. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm is what draws the frame. The gain is real and now measured: six declarations own all 73 cells that need an owner, against 73 pixels written out, responsibility reports 0 unexplained, and seven rules over those classes reproduce three of the five transitions exactly. The cost is real too: no rule can name the strip as such, so every strip rule carves it out of its class with four negative neighbour guards. Those guards are pixel-fitting in a costume. They are correct on every instance of both classes in frame 0, which I checked one by one, and they survived replay, and they are the price of a colour-first arm."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem instance_anchoring_is_frame_zero_and_that_question_is_closed "I pre-registered two branches: instances anchored from frame 0, predicting 0 unexplained, or anchored from the union of frames, predicting a residue drawn from exactly 13 named cells. The report reads 0 unexplained over 4096 cells. Frame 0 it is. The consequence I now rely on: a cell that is constant in frame 0 gets no instance and can never be drawn as anything else, which is precisely why the meter cannot tick twice and why the slots above row 29 are invisible to this manual. Both of those are stated as their own entries rather than left implicit."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem two_keys_have_never_been_pressed "this world has seen ACTION1, 2, 3, 4 and 7. key(5) and key(6) are unpressed and unknown. In this family a click carrying coordinates is common and this guard language cannot express one at all -- if key(5) or key(6) is that, the finding will be recorded as prose and never as a rule. Both are worth pressing early: whatever they cost, they cost less now, while the manual is small enough that a surprise is cheap to absorb, than later when a plan depends on them."
    [depends: the_sign_of_the_meter_is_unknown_and_that_matters_more_than_its_length  probe: pending]

  theorem no_goal_section_on_purpose "every command returned NOT_FINISHED and nothing in five transitions indicates what finishing means. The live candidates are that a strip must be brought to agree with the badge in its lane, that the meter must be filled, or that the objective lies above row 29 where I have never looked. Writing any of them as a goal would compile to a claim refuted by the first win, or worse, would send the searcher after a fiction. An absent goal compiles to is_goal -> False, which under-claims and costs a round; a wrong goal over-claims and costs the level."
    [depends: the_arena_is_lanes_and_only_slot_a_has_a_badge  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "mdl_segmenter returned negative gain on both variants, -4037 bits at 4 tracks and -10409 at 33, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4). That is a fact about the operator. cegis_miner refused every track because its precondition is one move event per transition and this world has no mover; correct and unhelpful. zero_space calls its own evidence THIN, 5 transitions constraining rank 3 of 679 features, and its single global law spans nearly every dynamic cell at once, which is what a 676-dimensional null space produces rather than what a conservation law looks like. I took one thing from the engines and it was the store arithmetic, dynamic_cells 97 and cells_needing_an_owner 73, both of which closed against a reconstruction built without them and both of which the responsibility check has since ratified."
    [probe: pending]
