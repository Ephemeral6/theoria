# theory.dsl -- FIRST DRAFT AGAINST THIS WORLD. The manual I was handed
# describes a different board: an 8x6 lattice at rows 8-56, a HUD at rows 1-7,
# a 64-pixel tally at row 63, a 5x5 colour-9 ring, 74 dynamic cells, 69
# unexplained. NONE of that survives contact with the evidence in front of me:
# the dynamic set here is 97 cells in rows 30-41 x cols 11-22 plus the single
# cell (53,63); there is no colour 9 and no colour 8 anywhere in the dynamic
# set; the actions are 1,2,3,4,7 and key(5) has never been pressed. I discard
# the old manual wholesale rather than patch it. Nothing is carried over.
#
# WHAT I GOT THIS ROUND, AND IT IS THE WHOLE ROUND: frame 0 is now known
# EXACTLY, and the object inventory is forced rather than guessed.
#
#   (a) distinct_states = 5 over six states S0..S5. S3,S4,S5 are pairwise
#       distinct and all differ from S0 and S1 (the meter cell (53,63) or the
#       12 strip cells separate them); S1 cannot equal S3 without contradicting
#       the 96-cell diff at t2. The ONLY possible coincidence is S2 = S0.
#       Therefore ACTION2 exactly undid ACTION1. Deduced, not assumed.
#   (b) S2 = S0 plus the t3/t4/t5 diffs run backwards gives frame 0 cell for
#       cell: it is the frame I was shown, except rows 38-39 x cols 17-22 hold
#       2 1 1 2 1 1 / 1 1 2 1 1 2 instead of colour 4, and (53,63) is 2 not 3.
#   (c) That reconstruction was then CHECKED TWICE against numbers I did not
#       use to build it. The dynamic set it implies is exactly
#       {rows 30-35 x cols 11-16} u {rows 36-41 x cols 11-16} u
#       {rows 32-33 x cols 17-22} u {rows 38-39 x cols 17-22} u {(53,63)}
#       = 36 + 36 + 12 + 12 + 1 = 97, and the store says dynamic_cells = 97.
#       Its non-background frame-0 population is 22 (colour 6) + 12 (colour 0)
#       + 8 (colour 3) + 10 (colour 2) + 9 (colour 1) + 12 (colour 4) = 73,
#       and the store says cells_needing_an_owner = 73. Two independent
#       arithmetic closures on a reconstruction built from neither number.
#   (d) The old manual never used arc-instances: all, which is why it sat at
#       69-72 unexplained pixels and called that a ceiling. It is not a
#       ceiling. Six colour classes with arc-instances: all own all 73 cells.
#       I therefore make a hard, falsifiable prediction: the next
#       responsibility report on frame 0 reads 0 unexplained. If it does not,
#       the arm anchors instances from the union of frames rather than from
#       frame 0, and the residue will be exactly the 12 strip cells whose
#       colour differs between frame 0 and the later frames -- that is the one
#       alternative and it is pre-registered below.
#
# WHAT I STILL CANNOT WRITE: the 96-cell swap that ACTION1 and ACTION2 perform.
# It relocates a 6x6 widget by six rows and it is 96 simultaneous recolourings
# that this event vocabulary can only express one instance at a time with no
# guard that selects a row band. I refuse to fake it with 96 pixel rules that
# buy no compression. Replay will therefore fail at t1 and t2 and pass at
# t3, t4, t5 -- 3/5, up from 0/5 -- and that too is pre-registered.

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
  landmark strip_a_head  # arc-cell: (32, 17)
  landmark strip_b_head  # arc-cell: (38, 17)
  landmark meter_tip  # arc-cell: (53, 63)
  landmark badge_cell  # arc-cell: (31, 42)
  Casing [segment: colour_class_6 ev: t0-t5 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t5 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t5 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t5 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t5 compress: 10]
  Erased [segment: colour_class_4 ev: t0-t5 compress: 12]

events:
  event recolored(o, c)

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

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I was shown with two edits: rows 38-39 x cols 17-22 hold 2 1 1 2 1 1 over 1 1 2 1 1 2 instead of colour 4, and (53,63) holds 2 instead of 3. The chain is forced. distinct_states = 5 over six states, and every pair except (S0,S2) is separated by the meter cell or by the 96-cell t2 diff, so S2 = S0 and ACTION2 exactly undid ACTION1. Running t3, t4, t5 backwards from the current frame then reaches S2 = S0. The reconstruction was checked against two numbers it was not built from: it implies a dynamic set of 36 + 36 + 12 + 12 + 1 = 97 cells and the store reports 97, and a non-background frame-0 population of 22 + 12 + 8 + 10 + 9 + 12 = 73 and the store reports cells_needing_an_owner = 73. Both close to the unit. This is the load-bearing entry of the manual and everything below rests on it."
    [probe: passed]

  theorem the_panel_is_two_slots_one_of_them_expanded "the moving part of this world is a panel of two stacked slots at cols 11-16, slot A at rows 30-35 and slot B at rows 36-41, each with a 2x6 strip lying to its right inside the arena at cols 17-22 on its two centre rows -- rows 32-33 for A and rows 38-39 for B. Exactly one slot is expanded at a time. The expanded slot is drawn as a 6x6 colour-6 casing with a colour-0 cavity, a 2x2 colour-6 core at its centre rows and cols 13-14, and two port cells at its right edge showing colour 1 over colour 2. The collapsed slot is drawn as a bare 2-wide stack at cols 13-14, colour 3 at its four outer rows and colour 2 at its two centre rows. In frame 0 slot B is expanded and slot A is collapsed. The arithmetic that forces this: the expanded and collapsed drawings differ in every one of the 36 positions, so a swap changes 72 casing cells, and the two strips change 12 each, giving exactly 96 -- which is exactly what t1 and t2 each reported, over exactly rows 30-41 x cols 11-22."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_swap_is_inexpressible_and_i_refuse_to_fake_it "ACTION1 and ACTION2 swap which slot is expanded and are exact inverses of each other. I can state that and I cannot compile it. The event vocabulary moves one instance one cell or recolours one instance to one integer literal; the swap relocates a 6x6 widget by six rows, which is 96 simultaneous recolourings whose target colours differ per cell, and the guard language has no way to say -- the instances in rows 30-35 -- because there is no coordinate expression and no landmark comparison that grounds over a row band. I could write 96 single-instance rules. Each would explain one pixel and cost more than the pixel, which fails the gain test outright, and it would still not generalise to a third slot. So this manual predicts NO CHANGE for key(1) and key(2), which is wrong, and I say so here rather than let the reader discover it. Consequence, pre-registered: replay diverges first at t=1 with 96 cells wrong, and t3, t4, t5 replay exactly, giving 3/5."
    [depends: the_panel_is_two_slots_one_of_them_expanded  probe: pending]

  theorem the_strip_toggles_and_only_key_four_costs_anything "key(3) at t3 and key(7) at t5 each blanked all 12 cells of the expanded slot strip to the arena colour 4; key(4) at t4 restored exactly the same 1 and 2 pattern, cell for cell, and additionally advanced the meter cell (53,63) from 2 to 3. The pattern is therefore stored somewhere the frame does not show and is not destroyed by blanking. Over five commands the meter ticked once and only under key(4), so key(4) is the metered action and keys 1, 2, 3, 7 are free. One witness each: key(3) and key(7) may be a blank action and a toggle action that happened to agree because the strip was shown both times, and key(4) may be a show action or a toggle action that happened to agree because the strip was blank. Nothing in the record separates blank from toggle for any of the three. The cheapest separator is to press key(3) twice in a row from a shown strip."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem cascade_length_carries_no_signal_here "t1, t2, t3 and t4 returned 2 frames each and t5 returned 1, yet t3 and t5 produced identical 12-cell effects. So frame count does not track the magnitude or even the presence of change, and it must not be used as a motion detector the way the discarded manual used it. What it may still carry is that ACTION7 and ACTION3 are genuinely different actions with the same visible result in this state -- one animates and one does not. That is a hint about key identity, not about the world state."
    [probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the collapsed slot core, a port cell of the expanded slot, four strip cells and the meter tip, which are four unrelated roles; Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm is what draws the frame. What this buys is real and I claim it: six declarations own all 73 cells that need an owner, against 73 pixels written out, and seven rules over those classes reproduce three of the five transitions exactly. What it costs is also real: because a class is not a widget, no rule can name the strip as such, and every strip rule has to carve the strip out of its class with four negative neighbour guards -- not colour 0 to the left, not colour 5 to the left, not colour 5 to the right, not colour 5 above. Those four negations are pixel-fitting wearing a guard costume. They are correct on every instance of both classes in frame 0, which I checked one by one, and they are the price of the colour-first arm."
    [depends: the_panel_is_two_slots_one_of_them_expanded  probe: pending]

  theorem instance_anchoring_has_one_alternative_and_it_is_pre_registered "I predict the next responsibility report on frame 0 reads 0 unexplained. That holds if arc-instances: all enumerates cells of the declared colour in FRAME 0 that the board cannot explain. The alternative is that it enumerates over the union of all observed frames, in which case the 12 strip cells are claimed twice -- once by Pip or Stud from frame 0 and once by Erased from frames 3 and 5 -- and (53,63) is claimed by both Stud and Rail. Under that alternative the report will not read 0 and the residue will be drawn from exactly those 13 cells and no others. Any residue outside those 13 cells refutes frame_zero_is_reconstructed_exactly and I would rebuild the manual from the reported cells rather than defend it."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_meter_is_long_so_exploration_is_cheap_now "row 53 is a colour-2 bar running at least cols 10 to 62 with the tip at col 63, and one unit has been consumed. Whether it extends left of col 10 I cannot see, because everything left of the window has held one colour throughout and is board by definition -- so at least 54 units, possibly many more, against one spent. This is the opposite of the situation the discarded manual described, where two attempts remained and every press was a bet. Here the correct posture is to spend free presses freely and metered presses deliberately. I do not know whether the bar filling to the tip is a loss, a win, or neither, and nothing in five commands speaks to it."
    [probe: pending]

  theorem two_keys_have_never_been_pressed "ARC offers ACTION1..ACTION7 and this world has seen 1, 2, 3, 4 and 7. key(5) and key(6) are unpressed and unknown. In this family key(6) is customarily a click carrying coordinates, which this guard language cannot express at all -- if that is what it is, it will need a probe reported as prose and never as a rule. Given the meter is long, I hold no fear of pressing either, and the playbook says to do it early rather than late, while a wrong outcome is still cheap to absorb."
    [depends: the_meter_is_long_so_exploration_is_cheap_now  probe: pending]

  theorem the_arena_and_its_untouched_badge "the arena is a colour-4 rectangle spanning cols 17 to 46 across rows 29 to 41 at least, bounded below by background from row 42 and by a solid colour-4 band at row 54. Inside it, rows 31-34 x cols 42-45 is a 4x4 block of colour 14, the only colour 14 in the window, and it has never changed. Colours 8 and 9 appear in the store's colour list but on no dynamic cell and nowhere in rows 29-54, so they live in the constant region above row 29 and are board. The badge is the only structure in the arena that is neither the two strips nor uniform fill, which makes it the natural candidate for whatever the strips are being compared against -- a reading with zero transitions behind it, recorded because it is the first thing to test once the strips are readable."
    [probe: pending]

  theorem no_goal_section_on_purpose "every command returned NOT_FINISHED and nothing in five transitions indicates what finishing means. The candidates are that the strips must be brought to match the badge, that the meter must be filled, or that something outside the window entirely is the objective. Writing any of them as a goal would compile to a claim refuted by the first win or, worse, would make the searcher chase a fiction. An absent goal compiles to is_goal -> False, which under-claims and costs one round; a wrong goal over-claims and costs the level. I under-claim."
    [depends: the_arena_and_its_untouched_badge  probe: pending]

  theorem what_the_engines_offered_and_why_most_of_it_was_declined "mdl_segmenter returned negative gain on both variants, -4037 bits with 4 tracks and -10409 bits with 33, and its tracks are 440-cell and 436-cell blobs of shape 13x36 with colour null -- the whole panel plus arena fused under connected_components(4). That is a fact about the operator, not about the world, and I accept the fusion while rejecting it as a segmentation. cegis_miner refused every track because its precondition is exactly one move event per transition, and this world has no mover at all; its verdict that the world does not narrate as one mover is correct and unhelpful. zero_space reports its own evidence as THIN -- 5 transitions constraining rank 3 of 679 features -- and its single global law spans nearly every dynamic cell at once, which is what a null space of dimension 676 produces and not what a conservation law looks like. I take one thing from the engine round and it is the store arithmetic: dynamic_cells 97 and cells_needing_an_owner 73, both of which closed against a reconstruction built without them."
    [probe: pending]
