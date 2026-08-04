# theory.dsl -- COMPLETE REWRITE. The manual I was handed described a
# DIFFERENT world (26 states, spawn ring rows 8-12, panel rows 1-5). certify:
# 0/5 replay, first divergence at t=0, 52 unexplained pixels of frame 0. Not
# one of its rules can ground here. I deleted it entire rather than patch it.
# Everything below comes from this log alone: RESET, A1, A2, A3, A4, A7.
#
# THE CENSUS I RECONSTRUCTED (the brief gives boxes and counts, not cell sets):
#   rows 30-35 x cols 11-16   36  top slot
#   rows 32-33 x cols 17-22   12  top readout
#   rows 36-41 x cols 11-16   36  bottom slot
#   rows 38-39 x cols 17-22   12  bottom readout
#   (53,63)                    1  meter tip
# FOUR NUMBERS I DID NOT CHOOSE LAND ON IT EXACTLY: 97 = dynamic_cells;
# 96 = the t1 and t2 diffs, box rows 30-41 cols 11-22; 97-24 background-
# coloured cells = 73 = cells_needing_an_owner; 4096-97 = 3999 = constant_cells.
#
# THE DEDUCTION EVERYTHING RESTS ON: states=6, distinct_states=5 => exactly one
# collision. S4/S5 carry (53,63)=3 and S0-S3 carry 2; S1 differs from S0 and S2
# by 96 each; S3 differs from S2 by 12 and from S1 by >=84. ONLY S0 = S2
# SURVIVES. So ACTION2 undid ACTION1, and THE CURRENT WIDGET IS THE FRAME-0
# WIDGET -- which is how I read frame 0's colours without being shown frame 0.
#
# THE READING: two 6x6 slots at cols 11-16 (rows 30-35, rows 36-41), each with
# a 6x2 readout at cols 17-22. W0 = bar on top (colour 3, core 2), hollow
# colour-6 box below, top readout blank, bottom readout patterned. ACTION1
# EXCHANGES the slots and the readouts; all 96 cells differ between the two
# configurations, which is why the diff says 96. ACTION2 exchanges back.
# ACTION3/ACTION7 blank the bottom readout; ACTION4 restores it AND advances
# the meter tip.
#
# EXPECTED REPLAY 5/5, with one named failure mode (Field seating, below).

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Field    { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object BarBody  { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object BarCore  { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Blank    { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Frame    { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  object Hollow   { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Dot      { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  Field   [segment: dynamic_colour_5 ev: t0-t5 compress: 24]
  BarBody [segment: dynamic_colour_3 ev: t0-t5 compress: 8]
  BarCore [segment: dynamic_colour_2 ev: t0-t5 compress: 10]
  Blank   [segment: dynamic_colour_4 ev: t0-t5 compress: 12]
  Frame   [segment: dynamic_colour_6 ev: t0-t5 compress: 22]
  Hollow  [segment: dynamic_colour_0 ev: t0-t5 compress: 12]
  Dot     [segment: dynamic_colour_1 ev: t0-t5 compress: 9]

events:
  event recolored(o, c)

rules:
  rule k1_field_to_frame forall ?p in Field [ev: t1 cov: 14/14]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_field_to_hollow forall ?p in Field [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_field_to_dot forall ?p in Field [ev: t1 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_field_to_core forall ?p in Field [ev: t1 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_bar_to_frame forall ?p in BarBody [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_bar_to_hollow forall ?p in BarBody [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_core_to_frame forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(above(above(?p)), 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_blank_to_dot forall ?p in Blank [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_blank_to_core forall ?p in Blank [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_frame_to_field forall ?p in Frame [ev: t1 cov: 14/14]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_frame_to_bar forall ?p in Frame [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_to_core forall ?p in Frame [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_dot_to_field forall ?p in Dot [ev: t1 cov: 1/1]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_dot_to_blank forall ?p in Dot [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k1_core_to_field forall ?p in BarCore [ev: t1 cov: 1/1]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_core_to_blank forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k2_field_from_frame forall ?p in Field [ev: t2 cov: 14/14]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_hollow forall ?p in Field [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_dot forall ?p in Field [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_core forall ?p in Field [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_bar_from_frame forall ?p in BarBody [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_from_hollow forall ?p in BarBody [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_core_from_frame forall ?p in BarCore [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k2_blank_from_dot forall ?p in Blank [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_blank_from_core forall ?p in Blank [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_frame_from_field forall ?p in Frame [ev: t2 cov: 14/14]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_dot_from_field forall ?p in Dot [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_dot_from_blank forall ?p in Dot [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_core_from_field forall ?p in BarCore [ev: t2 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k2_core_from_blank forall ?p in BarCore [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k3_dot_blanks forall ?s in Dot [ev: t3 cov: 8/8]
    when act=key(3) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k3_core_blanks forall ?s in BarCore [ev: t3 cov: 4/4]
    when act=key(3) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k4_dot_lights forall ?s in Dot [ev: t4 cov: 8/8]
    when act=key(4) and colored(?s, 4) then recolored(?s, 1)

  rule k4_core_lights forall ?s in BarCore [ev: t4 cov: 4/4]
    when act=key(4) and colored(?s, 4) then recolored(?s, 2)

  rule k4_meter_advances forall ?s in BarCore [ev: t4 cov: 1/1]
    when act=key(4) and colored(?s, 2) and rightof(?s) = wall then recolored(?s, 3)

  rule k7_dot_blanks forall ?s in Dot [ev: t5 cov: 8/8]
    when act=key(7) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k7_core_blanks forall ?s in BarCore [ev: t5 cov: 4/4]
    when act=key(7) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

laws:
  invariant field_instances count(Field) = 24 [status: counted-from-reconstructed-census]
  invariant barbody_instances count(BarBody) = 8 [status: counted-from-reconstructed-census]
  invariant barcore_instances count(BarCore) = 10 [status: counted-from-reconstructed-census]
  invariant blank_instances count(Blank) = 12 [status: counted-from-reconstructed-census]
  invariant frame_instances count(Frame) = 22 [status: counted-from-reconstructed-census]
  invariant hollow_instances count(Hollow) = 12 [status: counted-from-reconstructed-census]
  invariant dot_instances count(Dot) = 9 [status: counted-from-reconstructed-census]
  invariant board_cells count(board) = 3999 [status: matches constant_cells exactly]
  invariant meter_tip_now count(BarCore, color = 3) = 1 [status: state-dependent-not-an-invariant]

  theorem the_old_manual_is_discarded_entire "The manual I was handed is about another world: spawn ring rows 8-12, panel rows 1-5, 26 states, a 64-cell meter at row 63. This log has 6 states, dynamics confined to rows 30-41 cols 11-22 plus (53,63), and certify returns 0/5 replay with first divergence at t=0. No rule of it can ground here, so repair is meaningless and I deleted all of it. I kept two habits and no content: a manual that does not compile is worth less than a mediocre one that does, and a refutation is read by its divergence set."
    [probe: passed]

  theorem the_census_is_reconstructed_and_four_counts_confirm_it "The brief never hands me cell sets, so the five rectangles in the header are an inference. Four independent numbers land on them exactly: 36+12+36+12+1 = 97 = dynamic_cells; 36+12+36+12 = 96 = the cells changed at t1 and at t2 with bounding box rows 30-41 cols 11-22 as the diff reports; 97 minus the 24 cells of the top slot that render background 5 at frame 0 = 73 = cells_needing_an_owner; 4096-97 = 3999 = constant_cells. The render_mismatch listing corroborates where it is not truncated: it names (30,13),(30,14),(31,13),(31,14) as world 3, (32,13),(32,14),(33,13),(33,14) as world 2, and (32,17)-(33,22) as world 4 -- exactly the top slot's bar and the top readout, in exactly the colours the current frame shows. If any rectangle is wrong, replay breaks at t1 and I learn it in one round."
    [depends: the_old_manual_is_discarded_entire  probe: pending]

  theorem s0_equals_s2_and_that_is_what_lets_me_read_frame_zero "states = 6 and distinct_states = 5, so exactly one pair coincides. S4 and S5 carry (53,63)=3 while S0-S3 carry 2; S4 and S5 differ in 12 readout cells; S3 differs from S2 in 12 and from S1 in at least 84 since S1 and S2 differ in 96; S0 differs from S1 in 96. THE ONLY SURVIVOR IS S0 = S2. Two things follow. ACTION2 at t2 exactly undid ACTION1 at t1. And -- the part I cash -- the widget in the current frame IS the frame-0 widget, since t3, t4 and t5 touched only the bottom readout and the meter tip. Every source colour in every rule above is read off the picture in front of me, with the bottom readout back-corrected to the pattern ACTION3 erased. One deduction, no guess."
    [depends: the_census_is_reconstructed_and_four_counts_confirm_it  probe: passed]

  theorem the_widget_is_two_slots_and_action1_exchanges_them "Two 6x6 slots at cols 11-16, rows 30-35 and rows 36-41, each with a 6x2 readout at cols 17-22 (rows 32-33, rows 38-39). W0, which is frame 0 and is where I stand: the top slot is background with a two-column bar at cols 13-14 reading 3,3,2,2,3,3 down rows 30-35 and a blank readout; the bottom slot is a colour-6 box, colour-0 hollow, 2x2 colour-6 core at rows 38-39 cols 13-14, port pixels (38,16)=1 and (39,16)=2, and a patterned readout of eight 1s and four 2s with period 3 along each row and the rows offset by one column. ACTION1 exchanges them: (r,c) takes the colour of (r+6,c) for r in 30-35 and of (r-6,c) for r in 36-41. I checked all 96 cells and EVERY ONE differs between the configurations, which is exactly why the diff says 96 rather than fewer, and the exchange being an involution is exactly why S0 = S2. I hold this as a READING: a two-item list scrolled down then up is observationally identical over two transitions. The separator is a THIRD press of ACTION1 -- exchange returns to W1, scroll shows a third content."
    [depends: s0_equals_s2_and_that_is_what_lets_me_read_frame_zero  probe: pending]

  theorem the_swap_rules_are_thirty_six_and_constraint_three_is_failed "One law -- take the colour of the cell six away -- became 36 rules, and I will not dress that up. recolored(o, c) takes an INTEGER LITERAL, so a target colour cannot be read from a cell and must be named; the law splits into one rule per (source colour, target colour) pair, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I say so under constraint 3. I keep it because the alternative is 96 unexplained pixels twice over, and because these are one law under a grammar that cannot hold it. What buys some of it back is the TYPES: a type is a frame-0 colour, the frame-0 configuration is W0, so a rule's source colour selects its type for free, and the type separates top-half from bottom-half instances without a single row test. That is why not one rule in this file needs a deep nest of above() to say where it is."
    [depends: the_widget_is_two_slots_and_action1_exchanges_them  probe: passed]

  theorem barcore_is_four_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on four unrelated features: the 4-cell core of the bar (rows 32-33, cols 13-14), the lower port pixel (39,16), four dots of the bottom readout, and the meter tip (53,63). The arm looks types up by colour alone, so all ten are BarCore and no rule can tell the roles apart by type. I separate them by local geometry, every separator a cell I have actually read: the bar core has colour 3 two rows above, so k1_core_to_frame carries colored(above(above(?p)), 3); the readout dots have a colour-1 dot immediately left, so k1_core_to_blank, k3_core_blanks and k7_core_blanks carry colored(leftof(?s), 1); the port pixel has colour 0 left of it, so k1_core_to_field carries colored(leftof(?p), 0); the meter tip is the only instance with rightof off-board, so k4_meter_advances carries rightof(?s) = wall and every other BarCore rule fails a positive guard on it. I checked the four rules that can ground on colour 2 in one transition against all ten instances one at a time. NO RULE IN THIS FILE USES not: every exclusion is a positive colour test."
    [depends: the_swap_rules_are_thirty_six_and_constraint_three_is_failed  probe: pending]

  theorem the_twenty_four_field_cells_are_the_seating_i_am_betting_on "The named way this manual can fail replay. Twenty-four dynamic cells -- rows 30-35, cols 11, 12, 15, 16 -- render colour 5 at frame 0, and colour 5 is the BACKGROUND. The arm instances every cell of a declared colour the board cannot explain, and these cells vary, so they should seat. But cells_needing_an_owner is 73 rather than 97 and the 24 missing are exactly these, which shows something in the pipeline treats a background-coloured dynamic cell as needing nobody. IF FIELD SEATS NOTHING the fourteen Field rules never fire and replay is wrong by exactly those 24 cells at t1 and again at t2, and by nothing else. I take the bet because the alternative leaves 24 cells ownerless by construction, and because the failure is diagnosable at a glance."
    [depends: the_census_is_reconstructed_and_four_counts_confirm_it  probe: pending]

  theorem action1_here_should_move_seventy_two_cells_not_ninety_six "I stand in W0 but ACTION7 blanked the bottom readout at t5, so BOTH readouts render 4. Under the exchange reading, swapping two identical blank strips changes nothing, so ACTION1 now should move the 66 slot cells plus (32,13),(32,14),(33,13),(33,14) to colour 6, (39,16) to 5 and (38,16) to 5 -- 72 cells -- and no readout cell and no meter cell. My rules predict exactly that and not by arrangement: the readout rules are guarded on the pattern colours and simply do not ground when it is absent. 96 changed cells refutes the claim that a readout travels with its slot. 72 plus a cell of row 53 says the meter is not tied to ACTION4. Three outcomes, all legible in the raw diff."
    [depends: the_widget_is_two_slots_and_action1_exchanges_them  probe: pending]

  theorem the_readout_toggles_and_action3_and_action7_are_not_the_same_action "Twelve cells at rows 38-39 cols 17-22 have shown exactly two configurations in six states: BLANK (all 4) and PATTERN (eight 1s, four 2s). ACTION3 set BLANK at t3, ACTION4 set PATTERN at t4, ACTION7 set BLANK at t5. The pattern returns to the same twelve colours it had, which is why k4_dot_lights and k4_core_lights can be bare colour rules: an instance's TYPE is its frame-0 colour and therefore already records which cell gets a 1 and which a 2. WHAT I CANNOT CLOSE: ACTION3 and ACTION7 have identical net effects and I have written them as two rules with identical bodies, which is the shape of a claim that they are one key. THEY ARE NOT -- ACTION3 returned two internal frames and ACTION7 returned one. My own semantics say cascade single_frame, so my compiler discards the only evidence that separates them, and I record that here rather than pretend it is not in the log."
    [depends: the_census_is_reconstructed_and_four_counts_confirm_it  probe: passed]

  theorem the_meter_has_one_witness_and_its_next_cell_is_undrawable "Row 53 is a colour-2 bar across the frame; (53,63) turned 3 at t4 under ACTION4 and is the only cell of row 53 that has ever changed. I encode ACTION4-advances-it because that is the only reading this guard language can express and it has one witness. THREE READINGS FIT ONE WITNESS: that key 4 advances it, that lighting the readout advances it, that command index or parity advances it. There is no command counter in the guard language, so the third cannot be written at any length. THE STRUCTURAL PART: the next cell is (53,62), which has never changed, so it is board, so no instance sits on it, so no event here can touch it -- recolored takes an object and there is no object there. MY MANUAL MUST PREDICT THE SECOND ADVANCE NEVER HAPPENS and must be wrong by exactly one pixel every time the meter moves, until a later census heals one step behind. A divergence set of one cell in row 53 implicates nothing in this file."
    [depends: barcore_is_four_unrelated_things_and_the_arm_sees_only_colour  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where no rule fires I say NOTHING HAPPENS in the same voice I use for what I watched. Audit at the current state, W0 with both readouts blank. ACTION1: 72 cells, generalised from t1 and falsifiable at once -- not a silence. ACTION3 and ACTION7: predicted silent HERE because the pattern they erase is already gone; that silence is entailed by witnessed rules, not forged. ACTION4: predicted to light 12 readout cells and move no meter cell, the second half being the blind spot above rather than knowledge. ACTION2: PREDICTED SILENT ON ZERO WITNESSES -- every ACTION2 in the log was pressed in W1, never in W0 -- and that forgery covers 18 rules. ACTION5 and ACTION6: PREDICTED SILENT AND NEVER PRESSED IN ANY STATE. A probe ranker scoring expected bits over my manual and its ablations prices a predicted identity at zero, because every ablation agrees with a rule that does not fire, SO THE ACTIONS I MOST NEED ARE THE ONES IT CAN NEVER BUY. Saying so in prose is the only lever this desk has, and I would rather name the lever than pretend the silence is a finding."
    [depends: action1_here_should_move_seventy_two_cells_not_ninety_six, the_meter_has_one_witness_and_its_next_cell_is_undrawable  probe: pending]

  theorem no_goal_section_and_the_reason_is_arithmetic "The pos form is dead outright: nothing in this world moves, every rule here is a recolour, and no instance's pos changes in six states. That leaves counts over seven types whose members are one 12x12 widget plus one meter cell, and every count I can write names a CONFIGURATION rather than a victory. count(Frame, color = 5) = 14 says only the box is in the top slot. count(Dot, color = 4) = 8 says only the readout is blank. count(BarCore, color = 3) = 1 says the meter advanced once and IS TRUE RIGHT NOW, four commands after RESET, so declaring it would make the plan tier commit and report success at a state I have no reason to call a win. I cannot count the meter past one, because (53,62) and its 62 neighbours have never changed and hold no instance: THE GOAL LANGUAGE CAN ONLY SPEAK ABOUT CELLS THAT HAVE ALREADY MOVED. So there is no goal section. What ends that is an observation, not an edit -- a second cell of row 53, or any cell outside rows 30-41 and row 53 changing at all."
    [depends: the_meter_has_one_witness_and_its_next_cell_is_undrawable  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3999 constant cells, not just naming them board. A colour-4 panel fills about rows 29-41 from col 17 to col 46, carrying a 4x4 block of colour 14 at rows 31-34 cols 42-45 -- the only colour-14 anywhere and the only structure on the panel's right. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them from it. Row 29 shows the same 5,5,3,3,5,5 signature as the top slot but has NEVER changed, so the bar looks seven rows tall while only six of it is alive; I do not know whether row 29 is a static cap or a row the exchange refuses to move, and the exchange reading predicts it will look wrong on screen in W1. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the meter, row 54 a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports BOTH variants at negative gain -- minus 4037 bits on four tracks, minus 10409 on 33 -- so by its own measure it compressed nothing, and I take none of its structure. Its tracks are unusable individually: obj0, obj2 and obj3 are 436-to-440-cell blobs of shape 13x36 that swallow the colour-4 panel together with the widget; obj1 is a 108-cell 2x54 strip that is rows 53 and 54 read as one thing. What I DO take is a frame-index witness independent of my rules: obj0 present only at frame 0, obj2 first at frame 1, obj3 first at frame 2 and then present for four frames -- the widget redrawn at t1 and again at t2 and standing still after, exactly two 96-cell transitions and no third, which is the same shape as my S0 = S2 deduction arrived at from a different direction. cegis_miner refuses all four tracks and its verdict, that the world does not narrate as one mover, is TRUE and is the strongest negative result here: nothing in this world moves, everything recolours. zero_space self-reports THIN in its own words -- 5 transitions constraining rank 3 of 679 features, null space dimension 676 -- and its one global law is my census with the meter tip appended; I take the corroboration and reject the law as unfalsified rather than confirmed, which is what its own report says."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me. STATE: W0, both readouts blank colour 4, (53,63) rendering 3. ACTION1: exactly 72 cells change, no readout cell, no row-53 cell; 96 refutes the claim that readouts travel with slots. ACTION2: I predict NOTHING CHANGES on zero witnesses and I EXPECT TO BE WRONG -- if it exchanges, 18 rules generalise for free and my largest forgery closes in one press. ACTION3, ACTION7: nothing changes, and this one I believe. ACTION4: the 12 bottom readout cells take their frame-0 arrangement of 1s and 2s and NO cell of row 53 moves; if (53,62) turns 3 then ACTION4 advances the meter unconditionally, my rule is right in spirit and undrawable in fact, and the divergence set is one cell that implicates nothing. ACTION5, ACTION6: unconstrained, never pressed in six states, and I predict only that whichever of them is pressed produces the largest single addition to this manual available. If the next command is ACTION1, ACTION3 or ACTION7 I will have learned least, because those three are what the manual already speaks about."
    [depends: action1_here_should_move_seventy_two_cells_not_ninety_six, the_silences_i_assert_and_which_of_them_are_forged  probe: pending]
