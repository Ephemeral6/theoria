# theory.dsl -- second edition. The first edition of THIS world's manual
# replayed 4/5 with a divergence of exactly four cells at t=0:
#   (40,13) (40,14) (41,13) (41,14)   manual says 3, world says 5.
# That is 92 of 96 cells of the ACTION1 transition correct and four wrong, and
# the four are not scattered: they are the BOTTOM TWO ROWS of the bar's landing
# site in the bottom slot, at the bar's own two columns. Everything else in the
# file is untouched by this refutation and stays.
#
# WHAT THE FOUR CELLS MEAN. My reading was "the two 6x6 slots exchange images,
# (r,c) takes the colour of (r+-6,c)". Under it the bar copies down as
# 3,3,2,2,3,3 into rows 36-41. THE WORLD COPIED ONLY 3,3,2,2 INTO ROWS 36-39
# AND LEFT ROWS 40-41 BACKGROUND. The bar is six rows tall in the top slot
# (seven on screen, counting the never-changing cap at row 29) and FOUR rows
# tall in the bottom slot. The exchange is exact everywhere else, including the
# box travelling up entire and the two port pixels (38,16)=1 and (39,16)=2
# landing at (32,16) and (33,16).
#
# THE FIX IS FOUR RULES WHERE THERE WERE TWO. I need to separate the two
# destination cells that copy the bar from the two that clear, and the two are
# MIRROR IMAGES in the box: (37,13) and (40,13) have identical 4-neighbourhoods
# (6 above, 6 below, 0 left, 0 right). The nearest cell that tells them apart is
# TWO up: above(above((37,13))) = (35,13) = 3, above(above((40,13))) = (38,13)
# = 6. Same for the border pair: above^2 of (36,13) is 3, of (41,13) is 6. So
# every one of the four new rules carries colored(above(above(?p)), <3|6>) and
# the split is exact, 2/2 and 2/2. I SAY PLAINLY WHAT THAT GUARD IS: a proxy
# for a row test I cannot write, fitted to one transition. It is not a law
# about neighbours; it is the cheapest expressible separator of two cells I
# have watched behave differently. See the_truncation theorem.
#
# THE CENSUS (unchanged, and now confirmed rather than reconstructed):
#   rows 30-35 x cols 11-16   36  top slot
#   rows 32-33 x cols 17-22   12  top readout
#   rows 36-41 x cols 11-16   36  bottom slot
#   rows 38-39 x cols 17-22   12  bottom readout
#   (53,63)                    1  meter tip
# 97 = dynamic_cells, 96 = the t1/t2 diffs, 4096-97 = 3999 = constant_cells,
# and certify now reports cells_unexplained = 0 over the whole 64x64 frame.
#
# EXPECTED REPLAY 5/5.

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

  rule k1_frame_to_bar forall ?p in Frame [ev: t1 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_clears forall ?p in Frame [ev: t1 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_frame_to_core forall ?p in Frame [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_hollow_clears forall ?p in Hollow [ev: t1 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

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

  rule k2_frame_from_field forall ?p in Frame [ev: t2 cov: 16/16]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2 cov: 10/10]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2 cov: 2/2]
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
  invariant field_instances count(Field) = 24 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant barbody_instances count(BarBody) = 8 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant barcore_instances count(BarCore) = 10 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant blank_instances count(Blank) = 12 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant frame_instances count(Frame) = 22 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant hollow_instances count(Hollow) = 12 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant dot_instances count(Dot) = 9 [status: census confirmed by responsibility 0/4096 unexplained]
  invariant board_cells count(board) = 3999 [status: matches constant_cells exactly]
  invariant meter_tip_now count(BarCore, color = 3) = 1 [status: state-dependent-not-an-invariant]

  theorem the_old_manual_is_discarded_entire "The manual I was first handed is about another world: spawn ring rows 8-12, panel rows 1-5, 26 states, a 64-cell meter at row 63. This log has 6 states, dynamics confined to rows 30-41 cols 11-22 plus (53,63), and certify returned 0/5 replay with first divergence at t=0. No rule of it could ground here, so repair was meaningless and I deleted all of it. That decision is now paid for: the replacement replays 4/5 and its single divergence is four cells wide."
    [probe: passed]

  theorem the_census_is_confirmed "The five rectangles in the header were an inference from counts, since the brief hands me boxes and totals rather than cell sets. They are now confirmed from two directions. certify: responsibility reports cells_unexplained = 0 over all 4096 cells, so every pixel of frame 0 is board or belongs to a declared instance, which no wrong census survives. And replay: 92 of the 96 cells of the ACTION1 transition are reproduced exactly by rules whose guards read cells six rows away, which is impossible if the slot rectangles were misplaced by even one row. The four failures are a fact about the BAR, not about the rectangles."
    [depends: the_old_manual_is_discarded_entire  probe: passed]

  theorem s0_equals_s2_and_that_is_what_lets_me_read_frame_zero "states = 6 and distinct_states = 5, so exactly one pair coincides. S4 and S5 carry (53,63)=3 while S0-S3 carry 2; S4 and S5 differ in 12 readout cells; S3 differs from S2 in 12 and from S1 in at least 84 since S1 and S2 differ in 96; S0 differs from S1 in 96. THE ONLY SURVIVOR IS S0 = S2. Two things follow. ACTION2 at t2 exactly undid ACTION1 at t1, so whatever ACTION1 does to the bar is REVERSIBLE and the bar comes back six rows tall. And the widget in the current frame IS the frame-0 widget, since t3, t4 and t5 touched only the bottom readout and the meter tip -- which is how every source colour in this file was read off the picture in front of me without ever being shown frame 0."
    [depends: the_census_is_confirmed  probe: passed]

  theorem the_truncation_is_the_only_thing_i_got_wrong_and_i_have_fitted_it_not_explained_it "THE REFUTATION, stated exactly. Under ACTION1 the bar's image lands in the bottom slot as 3,3 / 3,3 / 2,2 / 2,2 at rows 36-39 and rows 40-41 cols 13-14 go BACKGROUND, where I predicted 3,3 / 3,3. The bar is six rows in the top slot (30-35, seven on screen counting the never-changing cap at row 29) and four rows in the bottom. THE FIX IS A FIT. (37,13) and (40,13) have identical four-neighbourhoods -- 6 above, 6 below, 0 left, 0 right -- because the box is mirror-symmetric, so no local test separates them; the nearest asymmetry is two rows up, where (35,13)=3 and (38,13)=6, and that is the guard I wrote. It separates all four pairs exactly, 2/2 and 2/2, and it is a proxy for a row test the guard language does not have. I am claiming a fitted separator, not a neighbour law, and I would rather say so than let colored(above(above(?p)), 3) read as physics."
    [depends: s0_equals_s2_and_that_is_what_lets_me_read_frame_zero  probe: passed]

  theorem two_readings_of_the_widget_and_the_truncation_now_favours_the_second "READING A, exchange: two 6x6 slots trade images, and the bar simply RENDERS shorter in the lower slot. READING B, scroll: this is a list of at least three items scrolled by 6 rows, ACTION1 brings the box up to the top slot and a THIRD item -- which happens to look like 3,3,2,2 -- into the bottom, and ACTION2 scrolls back. Both explain every cell of t1 and t2 identically, because from S0 the two are the same map. The truncation is what tilts me: under A I must carry a slot-dependent rendering law with one witness and no mechanism; under B the four-row thing is just a different item and nothing needs explaining. I DO NOT DECIDE, because deciding costs nothing today and the probe is one command: A says a second consecutive ACTION1 returns W0 exactly, B says it produces a configuration never seen. My compiled rules implement neither reading in W1 -- they are colour lookups keyed on W0 colours and they fire on nothing there -- so the manual currently predicts SILENCE for ACTION1 in W1 and I expect that to be refuted."
    [depends: the_truncation_is_the_only_thing_i_got_wrong_and_i_have_fitted_it_not_explained_it  probe: pending]

  theorem the_swap_rules_are_thirty_eight_and_constraint_three_is_failed "One law -- take the colour of the cell six away -- became 36 rules, and the truncation made it 38, and I will not dress that up. recolored(o, c) takes an INTEGER LITERAL, so a target colour cannot be read from a cell and must be named; the law splits into one rule per (source colour, target colour) pair, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I say so under constraint 3. I keep it because the alternative is 96 unexplained pixels twice over. What buys some of it back is the TYPES: a type is a frame-0 colour, the frame-0 configuration is W0, so a rule's source colour selects its type for free and separates top-half from bottom-half instances without a single row test -- which is why only the two truncation rules in this file need a nest of above() to say where they are."
    [depends: two_readings_of_the_widget_and_the_truncation_now_favours_the_second  probe: passed]

  theorem barcore_is_four_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on four unrelated features: the 4-cell core of the bar (rows 32-33, cols 13-14), the lower port pixel (39,16), four dots of the bottom readout, and the meter tip (53,63). The arm looks types up by colour alone, so all ten are BarCore and no rule can tell the roles apart by type. I separate them by local geometry, every separator a cell I have read: the bar core has colour 3 two rows above; the readout dots have a colour-1 dot immediately left; the port pixel has colour 0 left of it; the meter tip is the only instance whose rightof is off-board. This is no longer a bet -- five transitions replayed with these separators in place, including t4 where the meter rule fired on exactly one of the ten instances and the readout rules on four others in the same step, and certify found no ambiguous pair in 30. NO RULE IN THIS FILE USES not: every exclusion is a positive colour test."
    [depends: the_swap_rules_are_thirty_eight_and_constraint_three_is_failed  probe: passed]

  theorem the_twenty_four_background_coloured_cells_do_seat "The named way this manual could have failed, now settled. Twenty-four dynamic cells -- rows 30-35, cols 11, 12, 15, 16 -- render colour 5 at frame 0, and 5 is the BACKGROUND; cells_needing_an_owner is 73 rather than 97, which is exactly those 24 short, and I read that as the pipeline not requiring an owner for a background-coloured cell. It does not follow that the arm refuses to SEAT one, and it does not: the fourteen Field rules fired at t1 and the divergence set contains none of those 24 cells. Declaring the background colour as an object type is legal and it works."
    [depends: the_census_is_confirmed  probe: passed]

  theorem action1_here_moves_seventy_two_cells_and_four_of_them_have_new_colours "I stand in W0 with BOTH readouts blank, since ACTION7 erased the bottom one at t5. Swapping two identical blank strips changes nothing, so ACTION1 now should move the 72 slot cells and NOT ONE readout cell and NOT the meter. The count is unchanged by this edition's fix -- the four truncation cells change either way -- but their TARGET colours are new: (40,13),(40,14) go 0 to 5 and (41,13),(41,14) go 6 to 5, where the last edition said 3. That is a sharp, cheap check on the fix, legible in the raw diff without any replay machinery. 96 changed cells would refute the claim that a blank readout travels invisibly; 3 at any of those four cells would say the truncation is not a property of the destination at all."
    [depends: the_truncation_is_the_only_thing_i_got_wrong_and_i_have_fitted_it_not_explained_it  probe: pending]

  theorem the_readout_toggles_and_action3_and_action7_are_not_the_same_action "Twelve cells at rows 38-39 cols 17-22 have shown exactly two configurations in six states: BLANK (all 4) and PATTERN (eight 1s, four 2s, period 3 along each row, the rows offset by one column). ACTION3 set BLANK at t3, ACTION4 set PATTERN at t4, ACTION7 set BLANK at t5, and all three transitions replay exactly. The pattern returns to the same twelve colours it had, which is why k4_dot_lights and k4_core_lights can be bare colour rules: an instance's TYPE is its frame-0 colour and therefore already records which cell gets a 1 and which a 2. WHAT I CANNOT CLOSE: ACTION3 and ACTION7 have identical net effects and I have written them as two rules with identical bodies, which is the shape of a claim that they are one key. THEY ARE NOT -- ACTION3 returned two internal frames and ACTION7 returned one. My own semantics say cascade single_frame, so my compiler discards the only evidence that separates them, and I record that here rather than pretend it is not in the log."
    [depends: the_census_is_confirmed  probe: passed]

  theorem the_meter_has_one_witness_and_its_next_cell_is_undrawable "Row 53 is a colour-2 bar across the frame; (53,63) turned 3 at t4 under ACTION4 and is the only cell of row 53 that has ever changed. I encode ACTION4-advances-it because that is the only reading this guard language can express and it has one witness. THREE READINGS FIT ONE WITNESS: that key 4 advances it, that lighting the readout advances it, that command index or parity advances it. There is no command counter in the guard language, so the third cannot be written at any length. THE STRUCTURAL PART: the next cell is (53,62), which has never changed, so it is board, so no instance sits on it, so no event here can touch it -- recolored takes an object and there is no object there. MY MANUAL MUST PREDICT THE SECOND ADVANCE NEVER HAPPENS and must be wrong by exactly one pixel every time the meter moves, until a later census heals one step behind. A divergence set of one cell in row 53 implicates nothing else in this file."
    [depends: barcore_is_four_unrelated_things_and_the_arm_sees_only_colour  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where no rule fires I say NOTHING HAPPENS in the same voice I use for what I watched. Audit at the current state, W0 with both readouts blank. ACTION1: 72 cells, witnessed and falsifiable at once -- not a silence. ACTION3 and ACTION7: predicted silent HERE because the pattern they erase is already gone; that silence is entailed by witnessed rules, not forged. ACTION4: predicted to light 12 readout cells and move no meter cell, the second half being the blind spot above. ACTION2 IN W0: PREDICTED SILENT ON ZERO WITNESSES -- every ACTION2 in the log was pressed in W1 -- and that forgery covers 18 rules. ACTION1 IN W1: PREDICTED SILENT ON ZERO WITNESSES, and this is now my LARGEST forgery, because it is exactly the probe that would decide exchange against scroll and my rules are colour lookups that ground on nothing there. ACTION5 and ACTION6: predicted silent and never pressed in any state. A probe ranker scoring expected bits over my manual and its ablations prices a predicted identity at zero, because every ablation agrees with a rule that does not fire, SO THE ACTIONS I MOST NEED ARE THE ONES IT CAN NEVER BUY. Saying so in prose is the only lever this desk has."
    [depends: action1_here_moves_seventy_two_cells_and_four_of_them_have_new_colours, the_meter_has_one_witness_and_its_next_cell_is_undrawable  probe: pending]

  theorem no_goal_section_and_the_reason_is_arithmetic "The pos form is dead outright: nothing in this world moves, every rule here is a recolour, and no instance's pos changes in six states -- cegis_miner's refusal of all four tracks says the same thing from outside. That leaves counts over seven types whose members are one 12x12 widget plus one meter cell, and every count I can write names a CONFIGURATION rather than a victory. count(Frame, color = 5) = 14 says only that the box is in the top slot. count(Dot, color = 4) = 8 says only that the readout is blank. count(BarCore, color = 3) = 1 says the meter advanced once and IS TRUE RIGHT NOW, four commands after RESET, so declaring it would make the plan tier report success at a state I have no reason to call a win. I cannot count the meter past one, because (53,62) and its 62 neighbours have never changed and hold no instance: THE GOAL LANGUAGE CAN ONLY SPEAK ABOUT CELLS THAT HAVE ALREADY MOVED. So there is no goal section. What ends that is an observation, not an edit -- a second cell of row 53, or any cell outside rows 30-41 and row 53 changing at all."
    [depends: the_meter_has_one_witness_and_its_next_cell_is_undrawable  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3999 constant cells, not just naming them board, and certify now agrees that they are all accounted for. A colour-4 panel fills rows 29-41 from col 17 to col 46, carrying a 4x4 block of colour 14 at rows 31-34 cols 42-45 -- the only colour-14 anywhere and the only structure on the panel's right. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them from it. Row 29 shows 5,5,3,3,5,5 at cols 11-16, the same signature as the top slot, and has NEVER changed: the bar reads seven rows tall on screen while only six of it is alive, and that static cap is now load-bearing evidence, because the thing that lands in the bottom slot is four rows and the thing that leaves the top is six or seven depending on whether you count it. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the meter, row 54 a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports BOTH variants at negative gain -- minus 4037 bits on four tracks, minus 10409 on 33 -- so by its own measure it compressed nothing, and I take none of its structure: obj0, obj2 and obj3 are 436-to-440-cell blobs of shape 13x36 that swallow the colour-4 panel together with the widget, and obj1 is rows 53 and 54 read as one 2x54 strip. What I DO take is a frame-index witness independent of my rules: obj0 present only at frame 0, obj2 first at frame 1, obj3 first at frame 2 and present for four frames -- the widget redrawn at t1 and again at t2 and standing still after, exactly two 96-cell transitions and no third, which is my S0 = S2 deduction arrived at from another direction. Note also that obj2 has 436 cells where obj0 and obj3 have 440: the frame-1 blob is FOUR CELLS SMALLER, and those four cells are the truncation this edition fixes. The engine had the answer in a field I did not read last round. cegis_miner refuses all four tracks and its verdict, that the world does not narrate as one mover, is TRUE and is the strongest negative result here. zero_space self-reports THIN in its own words -- 5 transitions constraining rank 3 of 679 features, null space dimension 676 -- and its one global law is my census with the meter tip appended; I take the corroboration and reject the law as unfalsified rather than confirmed, which is what its own report says."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me. STATE: W0, both readouts blank colour 4, (53,63) rendering 3. ACTION1: exactly 72 cells change, no readout cell, no row-53 cell, and (40,13),(40,14),(41,13),(41,14) all become 5. ACTION1 TWICE: my manual predicts the second press changes NOTHING, and I expect to be wrong; if it restores W0 the exchange reading wins and 18 rules generalise by symmetry, if it shows a configuration I have never seen the scroll reading wins and the bar and the four-row glyph are different items. ACTION2 HERE: predicted silent on zero witnesses, and I expect to be wrong for the same reason. ACTION3, ACTION7: nothing changes, and this one I believe. ACTION4: the 12 bottom readout cells take their frame-0 arrangement of 1s and 2s and NO cell of row 53 moves; if (53,62) turns 3 then ACTION4 advances the meter unconditionally, my rule is right in spirit and undrawable in fact, and the divergence set is one cell that implicates nothing. ACTION5, ACTION6: never pressed in six states, and I predict only that whichever is pressed produces the largest single addition to this manual available. If the next command is ACTION3 or ACTION7 I will have learned least."
    [depends: action1_here_moves_seventy_two_cells_and_four_of_them_have_new_colours, the_silences_i_assert_and_which_of_them_are_forged  probe: pending]
