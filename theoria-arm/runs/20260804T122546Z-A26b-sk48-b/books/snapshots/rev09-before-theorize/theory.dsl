# theory.dsl -- third edition.
#
# WHAT THE ROUND BOUGHT. Four more commands (t6 A1, t7 A2, t8 A1, t9 A3) and
# they settle three things and open one.
#
# 1. THE REFUTATION IS THE MIRROR OF THE ONE I FIXED LAST ROUND. certify
#    diverges on the ACTION2 transition at exactly four cells: (34,13) (34,14)
#    manual 0 world 3, and (35,13) (35,14) manual 6 world 3. Last round I
#    taught the manual that the bar TRUNCATES going down -- rows 40-41 of the
#    landing site go background instead of 3. I never taught it that the bar
#    REGROWS coming back up. My k2 rules copy the colour from six rows below,
#    and six rows below (34,13) and (35,13) in W1 is background, so nothing
#    fired and the two cells sat still. Two new rules, on BarBody, with the
#    positive guard colored(below^6(?p), 5) -> 3. Coverage 2/2 and 2/2, and
#    they are exclusive against k2_bar_from_frame/k2_bar_from_hollow because
#    those demand colour 3 six rows below. I also CORRECT the coverage I
#    claimed for those two rules: I wrote 4/4 for each and the truth is 2/2
#    each -- the missing two per rule are precisely these four cells. That
#    overclaim is what hid the defect for a round.
#
# 2. THE THREE VACUOUS PROBES HAVE ONE CAUSE AND IT IS THAT DEFECT. P-01,
#    P-02, P-03 each report that every hypothesis including `inert` was
#    refuted and the realised gain was 0.0 bits. That is not a missing
#    mechanism. The probe tier reconstructs the current state by replaying my
#    rules from t0; replay breaks at the SECOND transition, so from t2 onward
#    the manual's internal frame carried those four cells wrong and every
#    predicted hash after it was wrong by at least four cells, ablations
#    included. I predict, before it is run, that the fix restores t1 t2 t3 t4
#    t5 t6 t7 exactly and leaves t8 wrong by ONE cell, (53,62). If a probe
#    stays vacuous after that, the cause is a mechanism and I will have been
#    wrong here in a way that is cheap to read.
#
# 3. THE WORLD IS NOT A FUNCTION OF THE FRAME, AND I CAN PROVE IT FROM THE
#    STORE. distinct_states = 7 over 10 states. S0 = S2 (ACTION2 undid
#    ACTION1) and S5 = S7 (same, later, with both readouts blank); those two
#    coincidences are the only pairs available and they exhaust the count.
#    Now: t6 pressed ACTION1 in S5 and moved 72 cells and NOT the meter; t8
#    pressed ACTION1 in S7 and moved 72 cells AND (53,62) 2->3. Same visible
#    state, same key, different successor. There is hidden state. It ticks at
#    command 4 (ACTION4) and command 8 (ACTION1) -- every fourth command,
#    key-independent -- which kills the reading I encoded last round that
#    ACTION4 advances the meter. See the_meter_is_a_clock_not_a_key.
#
# 4. STILL OPEN, AND ASKABLE ONLY FROM WHERE I STAND: exchange versus scroll.
#    ACTION1 has now been pressed three times and ACTION2 twice, and every one
#    of the five was pressed in the OTHER configuration than its predecessor.
#    ACTION1 has never followed ACTION1. I am in W1 right now, so one command
#    splits the two readings, and I have not spent it.
#
# WHERE I AM. S9 = W1: hollow box in the TOP slot (rows 30-35), bar in the
# BOTTOM slot rendered four rows (rows 36-39, rows 40-41 background), both
# readouts blank, (53,63) and (53,62) both 3. mdl_segmenter corroborates the
# whole reconstruction from outside: its W0 blobs are 440 cells and its W1
# blobs are 436, a difference of exactly the four truncated cells, and its
# frame indices read W1 at 1, W0 at 2-5, W1 at 6, W0 at 7, W1 at 8-9.
#
# THE CENSUS, now 98 cells: 36 top slot + 12 top readout + 36 bottom slot +
# 12 bottom readout + (53,63) + (53,62). BarCore gains the new meter cell and
# becomes 11; board falls to 3998. Both match the store exactly.

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
  landmark bottom_port                          # arc-cell: (38, 16)
  Field   [segment: dynamic_colour_5 ev: t0-t9 compress: 24]
  BarBody [segment: dynamic_colour_3 ev: t0-t9 compress: 8]
  BarCore [segment: dynamic_colour_2 ev: t0-t9 compress: 11]
  Blank   [segment: dynamic_colour_4 ev: t0-t9 compress: 12]
  Frame   [segment: dynamic_colour_6 ev: t0-t9 compress: 22]
  Hollow  [segment: dynamic_colour_0 ev: t0-t9 compress: 12]
  Dot     [segment: dynamic_colour_1 ev: t0-t9 compress: 9]

events:
  event recolored(o, c)

rules:
  rule k1_field_to_frame forall ?p in Field [ev: t1,t6,t8 cov: 14/14]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_field_to_hollow forall ?p in Field [ev: t1,t6,t8 cov: 8/8]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_field_to_dot forall ?p in Field [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_field_to_core forall ?p in Field [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_bar_to_frame forall ?p in BarBody [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_bar_to_hollow forall ?p in BarBody [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_core_to_frame forall ?p in BarCore [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(above(above(?p)), 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_blank_to_dot forall ?p in Blank [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_blank_to_core forall ?p in Blank [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_frame_to_field forall ?p in Frame [ev: t1,t6,t8 cov: 14/14]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_frame_to_bar forall ?p in Frame [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_clears forall ?p in Frame [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_frame_to_core forall ?p in Frame [ev: t1,t6,t8 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1,t6,t8 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_hollow_clears forall ?p in Hollow [ev: t1,t6,t8 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_dot_to_field forall ?p in Dot [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_dot_to_blank forall ?p in Dot [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k1_core_to_field forall ?p in BarCore [ev: t1,t6,t8 cov: 1/1]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_core_to_blank forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k2_field_from_frame forall ?p in Field [ev: t2,t7 cov: 14/14]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_hollow forall ?p in Field [ev: t2,t7 cov: 8/8]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_dot forall ?p in Field [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_core forall ?p in Field [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_bar_from_frame forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_from_hollow forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_regrows_from_hollow forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_bar_regrows_from_frame forall ?p in BarBody [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_core_from_frame forall ?p in BarCore [ev: t2,t7 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k2_blank_from_dot forall ?p in Blank [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_blank_from_core forall ?p in Blank [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_frame_from_field forall ?p in Frame [ev: t2,t7 cov: 16/16]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2,t7 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2,t7 cov: 10/10]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2,t7 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_dot_from_field forall ?p in Dot [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_dot_from_blank forall ?p in Dot [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_core_from_field forall ?p in BarCore [ev: t2,t7 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k2_core_from_blank forall ?p in BarCore [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k3_dot_blanks forall ?s in Dot [ev: t3 cov: 8/8]
    when act=key(3) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k3_core_blanks forall ?s in BarCore [ev: t3 cov: 4/4]
    when act=key(3) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k4_dot_lights forall ?s in Dot [ev: t4 cov: 8/8]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 1)

  rule k4_core_lights forall ?s in BarCore [ev: t4 cov: 4/4]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 2)

  rule k4_meter_tip_first_advance forall ?s in BarCore [ev: t4 cov: 1/1]
    when act=key(4) and colored(?s, 2) and rightof(?s) = wall then recolored(?s, 3)

  rule k7_dot_blanks forall ?s in Dot [ev: t5 cov: 8/8]
    when act=key(7) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k7_core_blanks forall ?s in BarCore [ev: t5 cov: 4/4]
    when act=key(7) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

laws:
  invariant field_instances count(Field) = 24 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant barbody_instances count(BarBody) = 8 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant barcore_instances count(BarCore) = 11 [status: census updated this round, was 10, gains (53,62) which became dynamic at t8]
  invariant blank_instances count(Blank) = 12 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant frame_instances count(Frame) = 22 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant hollow_instances count(Hollow) = 12 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant dot_instances count(Dot) = 9 [status: census, responsibility reported 0/4096 unexplained last round]
  invariant board_cells count(board) = 3998 [status: matches constant_cells exactly, was 3999 before (53,62) moved]

  theorem the_regrowth_is_the_answer_to_the_replay_mismatch "The surprise names four cells on the ACTION2 transition: (34,13) (34,14) manual 0 world 3, (35,13) (35,14) manual 6 world 3. All four are BarBody instances -- their frame-0 colour is 3 -- and in W1 they carry the box, 0 in the interior rows and 6 in the border row. My k2 BarBody rules both demand colour 3 six rows below, and six rows below them lies rows 40-41 of the bottom slot, which the truncation I fixed last round leaves BACKGROUND. So no rule fired and the four cells stood still. Two rules with the guard colored(below^6, 5) close it, 2/2 and 2/2, and they are exclusive against the existing pair by that colour alone. I ALSO CORRECT AN OVERCLAIM: I had written cov 4/4 on k2_bar_from_frame and k2_bar_from_hollow when each in fact covers 2/2, and that inflated pair of numbers is exactly what hid this defect for a round. The lesson is not about the bar; it is that a coverage figure I did not count is a lie that costs a round."
    [probe: passed]

  theorem the_bar_is_six_rows_above_and_four_below_in_both_directions "Stated as one fact now that both directions are witnessed. The bar reads 3,3 / 3,3 / 2,2 / 2,2 / 3,3 / 3,3 down rows 30-35 at cols 13-14 in the top slot, and 3,3 / 3,3 / 2,2 / 2,2 down rows 36-39 in the bottom, with rows 40-41 background. Going down the last two rows CLEAR; coming up they REGROW as 3. The box, by contrast, renders 22 frame cells and 12 hollow cells in either slot without loss. So the swap is not an information-preserving exchange of two 6x6 windows: the bottom slot is lossy for the bar and the loss is restored from nowhere visible when it comes back. mdl_segmenter says the same from outside without being asked -- its W0 blobs have 440 cells and its W1 blobs 436, and 440 minus 436 is these four cells."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem the_world_is_not_a_function_of_the_frame "The strongest result of this round, and it is a negative one. distinct_states = 7 over 10 states, and the only two coincidences available are S0 = S2 and S5 = S7, which exhausts the count exactly. So S5 and S7 are the SAME visible frame: W0, both readouts blank, (53,63) = 3, (53,62) = 2. ACTION1 in S5 changed 72 cells and no meter cell. ACTION1 in S7 changed 73: the same 72 plus (53,62) 2 to 3. Same frame, same key, different successor. There is state this arm cannot see. My compiled step is a function of the frame, so it MUST be wrong somewhere, and I would rather name where than let it look sound."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: passed]

  theorem the_meter_is_a_clock_not_a_key "Last round I encoded that ACTION4 advances the meter, on one witness, and listed three readings I could not split. t8 splits them and my reading loses. The meter has advanced twice: at command 4 under ACTION4, painting (53,63), and at command 8 under ACTION1, painting (53,62). Two different keys, and the second is a key that had already been pressed twice without advancing it. What both have in common is the COMMAND INDEX: 4 and 8. I read the meter as a clock that ticks every fourth command from RESET and eats row 53 from the right, and I predict the third tick lands on (53,61) at command 12 -- three commands from now. THE GUARD LANGUAGE HAS NO COUNTER, at any length, so this cannot be written as a rule; it is written here instead. I keep k4_meter_tip_first_advance because it reproduces t4 and, since (53,63) is no longer colour 2, it can never fire again and so can never assert the refuted key-attribution a second time."
    [depends: the_world_is_not_a_function_of_the_frame  probe: pending]

  theorem the_three_vacuous_probes_have_one_cause_and_i_name_it_before_the_rerun "P-01, P-02 and P-03 each refuted all 57 hypotheses including inert and returned 0.0 bits against about 1.9 expected. The report reads that as a missing mechanism. I say it is the four-cell defect above, and here is the argument a reader can check: the probe tier reconstructs the present state by replaying my rules from t0, replay first diverges at the SECOND transition, and after that the manual's own frame carries (34,13) (34,14) as 0 and (35,13) (35,14) as 6 forever. Every hypothesis in the frontier is my manual or an ablation of it, so every one of them inherits those four wrong cells and every predicted hash misses. THE FALSIFIABLE PART: with the regrowth rules in, I predict t1 through t7 replay exactly and t8 is wrong by exactly one cell, (53,62), which no rule of mine may claim. If a probe is still vacuous after that, the cause is a mechanism I have not stated and this theorem is refuted."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch, the_meter_is_a_clock_not_a_key  probe: pending]

  theorem exchange_versus_scroll_is_still_open_and_i_am_standing_where_it_can_be_asked "READING A, exchange: two slots trade images and the bar simply renders four rows below. READING B, scroll: a list of at least three items steps by six rows, and the four-row glyph in the bottom of W1 is a THIRD ITEM that happens to look like the bar's first four rows. Five swap commands have now been observed -- A1 at t1, A2 at t2, A1 at t6, A2 at t7, A1 at t8 -- and every one of them was pressed in the opposite configuration from its predecessor, so ACTION1 HAS NEVER FOLLOWED ACTION1 and nothing observed splits the two readings. What tilts me slightly to A is the regrowth: under B, the bar's rows 34-35 would have to be redrawn from an item that has scrolled out of view, which is ordinary for a scroll, whereas under A they are redrawn from a slot that never lost them, which needs no memory at all -- but that is taste, not evidence. I am in W1 now. One ACTION1 answers it: A returns W0 exactly and 20 rules generalise, B shows a configuration never seen and my whole word_table is a two-item special case."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence "At t1 the LIT readout travelled with the box from rows 38-39 to rows 32-33 -- twelve cells of pattern moved six rows up in the same step the box did. So the readout is bound to the box, not to the slot. ACTION4 has been pressed exactly once, in W0, where the box is at the bottom and its ports (38,16) = 1 and (39,16) = 2 sit at the left edge of the bottom readout. Unguarded, my k4 rules would fire on the Dot and BarCore instances at rows 38-39 in ANY state, and pressed in W1 they would light a strip the box has left, which is a confident wrong drawing of 24 cells and quite likely 24 more left dark. I have therefore added colored(bottom_port, 1) to both, using a landmark at (38,16): it is 1 exactly when the box is in the bottom slot. In W1 the rules now fire on nothing and my manual is SILENT about what ACTION4 does there. That silence is a declared gap, not a claim, and it is cheaper than a fabricated arrangement of 1s and 2s over twelve Blank instances that my type system cannot even tell apart."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem barcore_is_five_unrelated_things_now_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on the 4-cell core of the bar, the lower port pixel, four dots of the readout, and now TWO meter cells, (53,63) and (53,62), the latter having joined the census when it moved at t8. Eleven instances, one type, because the arm looks objects up by colour alone. The separators are all cells I have read: the bar core has colour 3 two rows above; the readout cores have a colour-1 dot immediately left; the port has colour 0 to its left; the old meter tip is the only instance whose rightof is off-board. I have checked every rule in this file against the new instance (53,62): its left neighbour is 2, its right neighbour is not a wall, two rows above it is background, so no rule of mine grounds on it in any state. It is a cell I own and cannot move, which is exactly the right shape for a clock I cannot read."
    [depends: the_meter_is_a_clock_not_a_key  probe: passed]

  theorem the_swap_rules_are_forty_and_constraint_three_is_still_failed "One law -- take the colour of the cell six away -- is now forty rules, up two. recolored takes an INTEGER LITERAL, so a target colour cannot be read out of a cell and must be named, and the law splits once per source colour, per target colour, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I will not dress that up: forty rules to explain 72 cells twice over is worse than a lookup table would be, and I keep it only because the alternative is 96 unexplained pixels. What buys part of it back is that a TYPE IS A FRAME-0 COLOUR: the frame-0 configuration is W0, so a rule's source colour already says which half of the widget the instance lives in, and only the four truncation and regrowth rules need geometry on top of that."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem no_goal_section_and_this_is_a_refusal_not_an_oversight "The heuristic_miss is right about the consequence and I accept it: with no goal, is_goal is False everywhere, plan never returns sat, commit never runs, and every command this arm spends is a probe. I still decline to write one, and the reason is arithmetic rather than modesty. Ten states have returned NOT_FINISHED and no other GameState has ever been seen, so no observation distinguishes a win from a non-win. The pos form is dead -- nothing in this world moves, every rule here is a recolour, and cegis_miner refused all seven tracks for exactly that reason. That leaves counts over seven types, and every count I can write names a CONFIGURATION: count(Frame, color = 5) = 14 says the box is up, count(Dot, color = 4) = 8 says the readout is dark, count(BarCore, color = 3) = 2 IS TRUE RIGHT NOW and would make the plan tier declare victory at a state I have no reason to call one. A false goal is worse than none, because it converts a probe budget into a confident wrong plan. WHAT ENDS THIS IS AN OBSERVATION, NOT AN EDIT: a GameState other than NOT_FINISHED, or any cell outside rows 30-41 and row 53 changing at all. ACTION5 and ACTION6 have never been pressed and are the cheapest place to look for it."
    [depends: the_meter_is_a_clock_not_a_key  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where nothing fires I am asserting identity in the same voice I use for what I watched. Audit at S9, which is W1 with both readouts blank. ACTION2: fully predicted, 72 cells, and it is the only action here my manual draws -- the four regrowth cells are the fix on trial. ACTION1: PREDICTED SILENT ON ZERO WITNESSES and this is my largest forgery, 20 rules and one structural reading riding on it; I expect to be wrong and I want to be. ACTION3, ACTION7: predicted silent because the pattern they erase is already erased, and this silence is ENTAILED by witnessed rules rather than forged -- I believe it. ACTION4: predicted silent because bottom_port is 5 here, and that is a declared gap I chose over a wrong drawing. ACTION5, ACTION6: predicted silent, never pressed in ten states, no witness of any kind. And every one of these predictions omits the clock: on the twelfth command since RESET, whatever it is, one extra cell (53,61) turns 3 and I cannot draw it. A probe ranker prices a predicted identity at zero because every ablation agrees with a rule that does not fire, SO THE ACTIONS I MOST NEED ARE THE ONES IT CAN NEVER BUY, and saying so in prose is the only lever this desk has."
    [depends: exchange_versus_scroll_is_still_open_and_i_am_standing_where_it_can_be_asked, the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3998 constant cells, not just naming them board. A colour-4 panel fills rows 29-41 from col 17 to col 46 and carries a 4x4 block of colour 14 at rows 31-34, cols 42-45 -- the only colour-14 anywhere and the only structure on the panel. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them from it and why every mdl_segmenter blob is a 13x36 slab. Row 29 shows 5,5,3,3,5,5 at cols 11-16 and has NEVER changed: the bar reads seven rows tall on screen while only six of it is alive. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the clock, all colour 2 except its two rightmost cells, both now 3. Row 54 is a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports BOTH variants at negative gain -- minus 7528 bits on 7 tracks, minus 7968 on 38 -- so by its own measure it compressed nothing and I take none of its structure. What I take is a frame-index witness independent of my rules, and this round it is decisive: obj0 has 440 cells at frame 0, obj2 has 436 at frame 1, obj3 has 440 across frames 2-5, obj4 has 436 at frame 6, obj5 has 440 at frame 7, obj6 has 436 across frames 8-9. That is W0 W1 W0 W0 W0 W0 W1 W0 W1 W1, arrived at without any rule of mine, and it matches my state reconstruction cell for cell -- including that the W1 blobs are exactly four cells smaller, which is the truncation. cegis_miner refuses all seven tracks and its verdict that the world does not narrate as one mover is TRUE and remains the strongest negative result available. zero_space self-reports THIN in its own words -- 9 transitions constraining rank 5 of 686 features, null space 681 -- and its one global law is my census with both meter cells appended; I take the corroboration of the cell set and reject the law as unfalsified rather than confirmed, which is what its own report says."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me. STATE: S9 = W1, box in the top slot, bar four rows in the bottom, both readouts blank, (53,63) and (53,62) both 3, nine commands since RESET. ACTION1 HERE: my manual says nothing changes; I say that is false, and I name the two outcomes in advance -- 72 cells back to W0 means exchange and 20 rules generalise by symmetry, anything else means scroll and the bottom glyph is a third item. ACTION2 HERE: exactly 72 cells, no readout cell, no row-53 cell, and (34,13) (34,14) (35,13) (35,14) all become 3; anything but 3 at those four refutes the regrowth. ACTION4 HERE: my manual says nothing changes; I expect the twelve cells at rows 32-33, cols 17-22 to light instead, which refutes the silence and confirms that the readout follows the box. ACTION3, ACTION7: nothing changes, and this one I believe. ACTION5, ACTION6: never pressed in ten states; I predict only that whichever is pressed produces the largest single addition to this manual available, and that it is the cheapest place a win condition could come from. THE CLOCK RIDES ON ALL OF THEM: commands 10 and 11 leave row 53 alone, command 12 turns (53,61) from 2 to 3 and I cannot draw it, so a one-cell divergence in row 53 on that command confirms the clock and implicates nothing else in this file."
    [depends: the_silences_i_assert_and_which_of_them_are_forged, no_goal_section_and_this_is_a_refusal_not_an_oversight  probe: pending]
