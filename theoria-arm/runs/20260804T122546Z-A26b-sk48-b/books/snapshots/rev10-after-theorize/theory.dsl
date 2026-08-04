# theory.dsl -- fourth edition.
#
# WHAT THIS ROUND BOUGHT. One command (t9, ACTION3, zero cells changed) and a
# certify report, and between them they settle four things.
#
# 1. THE REGROWTH FIX HELD, AND THE PREDICTION I ATTACHED TO IT WAS EXACT.
#    Last round I wrote, before the rerun: "with the regrowth rules in, I
#    predict t1 through t7 replay exactly and t8 is wrong by exactly one cell,
#    (53,62), which no rule of mine may claim." certify now reports 7/9
#    transitions replaying exactly, first divergence at transition index 7
#    (the ACTION1 command), one cell wrong, (53,62), manual 2 world 3. That is
#    the sentence I wrote, returned to me by the machine. The four-cell
#    ACTION2 defect is gone; responsibility is 0/4096 unexplained; ambiguity
#    is 0 clashes over all 50 adjudicated pairs.
#
# 2. THE SURPRISE IS THE PRICE I ADVERTISED, AND I REFUSE TO PATCH IT. The
#    replay_mismatch names (53,62) and nothing else. The guard language has no
#    counter, so a clock that ticks on the command index cannot be written as
#    a rule at any length; the only rules that would draw that cell would fire
#    on every command and be wrong on three commands out of four. I take the
#    one-cell error permanently and keep saying where it comes from. See
#    the_only_divergence_left_is_the_one_i_priced_in_advance.
#
# 3. THE REPLAY IS CUMULATIVE, AND I CAN READ THAT OFF THE COUNTS. Two
#    transitions failed (7 matched of 9) but only one divergence is named.
#    t9's ACTION3 is an identity in the world and an identity in my manual, so
#    a one-step replay would have matched it and reported 8/9. It reported
#    7/9, so the replay carries my state forward and transition 8 inherits the
#    same single wrong cell. Every future transition inherits it too. The cost
#    is one cell, not one cell per command.
#
# 4. I CORRECT AN ARITHMETIC ERROR OF MY OWN, AND t9 IS WHAT FIXED IT. Last
#    edition I wrote that distinct_states = 7 over 10 states is exhausted by
#    S0 = S2 and S5 = S7. Ten states with seven distinct needs THREE
#    coincidences, not two. The third is S8 = S9: ACTION3 at t9 changed
#    nothing, which is the FIRST WITNESSED INERTNESS in this world's history
#    and closes the count exactly. mdl_segmenter corroborates it from outside
#    -- its obj6 now spans frames 8-9 where last round it spanned only 8. The
#    hidden-state argument is untouched: S5 = S7 still have different
#    successors under the same key.
#
# 5. THE CLOCK SURVIVES A DISCRIMINATION I HAD NOT RUN. Ticks at command 4 and
#    command 8; commands 1,2,3,5,6,7,9 left row 53 alone. A rival counter --
#    "every fourth command that returned two frames" -- is now REFUTED: t4 is
#    the 4th two-frame command but t8 is the 7th, and t5 and t9 returned one
#    frame each. The plain command index survives; the next tick is command 12
#    and lands on (53,61).
#
# WHERE I AM. S9 = S8 = W1: hollow box in the TOP slot (rows 30-35, border 6,
# hollow 0, a 2x2 core of 6 at rows 32-33 cols 13-14, ports 1 and 2 at
# (32,16) and (33,16)); bar in the BOTTOM slot rendered four rows (36-39,
# rows 40-41 background); both readouts blank; (53,63) and (53,62) both 3.
# Nine commands since RESET. Read straight off the current frame, and it
# agrees with the manual cell for cell.
#
# THE CENSUS, 98 cells, and it now decomposes twice over. 24 Field + 8 BarBody
# + 11 BarCore + 12 Blank + 22 Frame + 12 Hollow + 9 Dot = 98 = dynamic_cells.
# Separately, cells_needing_an_owner = 74 = 98 - 24, and 24 is exactly the
# Field count: the store is counting dynamic cells that are NOT background at
# frame 0, and my one background-coloured type covers the difference. Two
# independent numbers in the store land on my type table without adjustment.

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
  invariant field_instances count(Field) = 24 [status: census, and 98 minus 24 is exactly cells_needing_an_owner = 74]
  invariant barbody_instances count(BarBody) = 8 [status: census, responsibility reported 0/4096 unexplained this round]
  invariant barcore_instances count(BarCore) = 11 [status: census, includes both meter cells (53,63) and (53,62)]
  invariant blank_instances count(Blank) = 12 [status: census, responsibility reported 0/4096 unexplained this round]
  invariant frame_instances count(Frame) = 22 [status: census, matches the 22 colour-6 cells I count in the current frame's box]
  invariant hollow_instances count(Hollow) = 12 [status: census, matches the 12 colour-0 cells I count in the current frame's box]
  invariant dot_instances count(Dot) = 9 [status: census, responsibility reported 0/4096 unexplained this round]
  invariant board_cells count(board) = 3998 [status: matches constant_cells exactly]

  theorem the_only_divergence_left_is_the_one_i_priced_in_advance "The surprise names one cell, (53,62), manual 2 world 3, on the ACTION1 command at index 7 -- and last edition, in writing, before the rerun, I named that exact cell on that exact command as the one thing my manual may not draw. certify agrees on everything else: 7/9 transitions replay exactly, 0/4096 pixels unexplained, 0 ambiguity clashes over all 50 adjudicated pairs. I therefore make NO CHANGE in response to this surprise, and I say why rather than letting the silence look like an oversight. The tick is keyed to the command index; the guard language has cells, colours, adjacency and off-board tests and NO COUNTER of any length; and any rule that could paint (53,62) from what the frame shows -- say, a colour-2 cell whose right neighbour is 3 -- would fire on commands 9, 10 and 11 as well, buying one right cell at the price of three wrong ones. A permanent one-cell error I can locate and explain is worth more than a rule that is wrong three times in four."
    [depends: the_meter_is_a_clock_not_a_key  probe: passed]

  theorem the_replay_is_cumulative_and_one_cell_contaminates_every_later_frame "certify reports matched 7 of 9 with exactly ONE first divergence. Transition 8 is t9's ACTION3, which changed nothing in the world and fires nothing in my manual, so a one-step replay from the true previous frame would have matched it and reported 8/9. It reported 7/9. The replay must therefore carry MY reconstructed state forward, and transition 8 fails only by inheriting the (53,62) cell that transition 7 got wrong. This matters twice. First, it bounds the damage: the error is one cell held forever, not one cell added per command, until the next tick makes it two. Second, it is the mechanism I blamed last round for three vacuous probes, now demonstrated on a case where I know the answer independently -- a single wrong cell propagates to every downstream hypothesis whether or not that hypothesis has anything to do with it."
    [depends: the_only_divergence_left_is_the_one_i_priced_in_advance  probe: passed]

  theorem the_regrowth_fix_is_confirmed_and_the_prediction_that_confirmed_it_was_dated "I wrote: with the regrowth rules in, t1 through t7 replay exactly and t8 is wrong by exactly one cell, (53,62). certify: first divergence at index 7, one cell, (53,62). No ACTION2 cell appears anywhere in the report, so (34,13) (34,14) (35,13) (35,14) now replay correctly and the two rules k2_bar_regrows_from_hollow and k2_bar_regrows_from_frame are witnessed by the replay as well as by the diff. The corrected coverage figures -- 2/2 rather than the 4/4 I had inflated -- stand. The general lesson I drew last round is now paid for: the coverage number I did not count was the lie that hid the defect, and counting it was what let me date the fix in advance."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem the_regrowth_is_the_answer_to_the_replay_mismatch "The previous round's surprise named four cells on the ACTION2 transition: (34,13) (34,14) manual 0 world 3, (35,13) (35,14) manual 6 world 3. All four are BarBody instances -- their frame-0 colour is 3 -- and in W1 they carry the box, 0 in the interior rows and 6 in the border row. Both original k2 BarBody rules demand colour 3 six rows below, and six rows below them lies rows 40-41 of the bottom slot, which the truncation leaves BACKGROUND. So no rule fired and the four cells stood still. Two rules with the guard colored(below^6, 5) close it, 2/2 and 2/2, exclusive against the existing pair by that colour alone."
    [probe: passed]

  theorem the_bar_is_six_rows_above_and_four_below_in_both_directions "The bar reads 3,3 / 3,3 / 2,2 / 2,2 / 3,3 / 3,3 down rows 30-35 at cols 13-14 in the top slot, and 3,3 / 3,3 / 2,2 / 2,2 down rows 36-39 in the bottom, with rows 40-41 background -- I have just re-read all of it off the current frame. Going down the last two rows CLEAR; coming up they REGROW as 3. The box, by contrast, renders 22 frame cells and 12 hollow cells in either slot without loss, and I have re-counted both in the current frame: 22 colour-6 (border ring minus the two port cells, plus a 2x2 core at rows 32-33 cols 13-14) and 12 colour-0. So the swap is not an information-preserving exchange of two 6x6 windows: the bottom slot is lossy for the bar and the loss is restored from nowhere visible when it comes back. mdl_segmenter says the same from outside -- its W0 blobs have 440 cells and its W1 blobs 436, and 440 minus 436 is these four cells."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem the_world_is_not_a_function_of_the_frame_and_i_correct_my_own_arithmetic "The conclusion stands and the count that supports it was off by one, so I restate both. distinct_states = 7 over 10 states requires THREE coincidences, not the two I claimed. They are S0 = S2 (ACTION2 undid ACTION1, both readouts lit), S5 = S7 (the same, later, both readouts blank), and -- new this round -- S8 = S9, because ACTION3 at t9 changed nothing at all. That third one is the FIRST WITNESSED INERTNESS this world has produced and mdl_segmenter corroborates it without being asked: obj6 spanned frame 8 alone last round and spans frames 8-9 now. The negative result is untouched by the correction. S5 and S7 are the same visible frame; ACTION1 in S5 changed 72 cells and no meter cell, ACTION1 in S7 changed 73, the extra being (53,62) 2 to 3. Same frame, same key, different successor. My compiled step is a function of the frame, so it MUST be wrong somewhere, and I would rather name where than let it look sound."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: passed]

  theorem the_meter_is_a_clock_not_a_key "The meter has advanced twice: at command 4 under ACTION4, painting (53,63), and at command 8 under ACTION1, painting (53,62). Two different keys, the second a key already pressed twice without advancing it. What they share is the COMMAND INDEX. This round I ran a discrimination I had not run before, and it kills the best rival: 'every fourth command that returned two frames' predicts a tick at the 4th and 8th two-frame commands, but t8 is only the 7th two-frame command (t5 and t9 returned one frame each), so that counter is REFUTED and the plain command index survives. Seven commands have now failed to tick -- 1,2,3,5,6,7,9 -- and every one of them is a non-multiple of four. I read the meter as a clock ticking every fourth command from RESET, eating row 53 from the right, and I predict the third tick lands on (53,61) at command 12, three commands from now. THE GUARD LANGUAGE HAS NO COUNTER, at any length, so this cannot be written as a rule; it is written here instead. I keep k4_meter_tip_first_advance because it reproduces t4 in replay and, since (53,63) is no longer colour 2, it can never fire again and so can never assert the refuted key-attribution a second time."
    [depends: the_world_is_not_a_function_of_the_frame_and_i_correct_my_own_arithmetic  probe: pending]

  theorem the_vacuous_probes_were_replay_damage_and_half_of_that_is_now_shown "Last round P-01, P-02 and P-03 each refuted all 57 hypotheses including inert and returned 0.0 bits against about 1.9 expected, and I blamed the four-cell replay defect rather than a missing mechanism. The falsifiable half of that claim is now confirmed: the replay does carry my reconstructed state forward (see the_replay_is_cumulative...), so a divergence at transition 1 did contaminate every later predicted hash for every hypothesis, ablations included. The other half is untested, because no probe report reached me this round. IT REMAINS FALSIFIABLE IN THE SAME WORDS: with replay now exact through transition 6 and wrong by one advertised cell after it, a probe that still refutes every hypothesis including inert is evidence of a mechanism I have not stated, and this theorem is refuted."
    [depends: the_replay_is_cumulative_and_one_cell_contaminates_every_later_frame  probe: pending]

  theorem exchange_versus_scroll_is_still_open_and_i_am_still_standing_where_it_can_be_asked "READING A, exchange: two slots trade images and the bar simply renders four rows below. READING B, scroll: a list of at least three items steps by six rows, and the four-row glyph in the bottom of W1 is a THIRD ITEM that happens to look like the bar's first four rows. Five swap commands are observed -- A1 at t1, A2 at t2, A1 at t6, A2 at t7, A1 at t8 -- and every one was pressed in the opposite configuration from its predecessor, so ACTION1 HAS NEVER FOLLOWED ACTION1. t9 spent a command without leaving W1, so the question is still askable from where I stand and still costs one command rather than two. What tilts me slightly to A is the regrowth: under B the bar's rows 34-35 must be redrawn from an item that has scrolled out of view, which is ordinary for a scroll, whereas under A they are redrawn from a slot that never lost them, which needs no memory -- but that is taste, not evidence. One ACTION1 answers it: A returns W0 exactly and 20 rules generalise, B shows a configuration never seen and my whole word_table is a two-item special case."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence "At t1 the LIT readout travelled with the box from rows 38-39 to rows 32-33 -- twelve cells of pattern moved six rows up in the same step the box did -- and the current frame confirms the binding from the other side: in W1 the two port pixels read 1 at (32,16) and 2 at (33,16), six rows above where they sit in W0. So the readout is bound to the box, not to the slot. ACTION4 has been pressed exactly once, in W0, where bottom_port = (38,16) is 1. Unguarded, my k4 rules would fire on the Dot and BarCore instances at rows 38-39 in ANY state, and pressed in W1 they would light a strip the box has left: 24 cells drawn confidently wrong and quite likely 24 more left dark. The guard colored(bottom_port, 1) makes them fire on nothing in W1, so my manual is SILENT about what ACTION4 does there. That silence is a declared gap, not a claim, and it is cheaper than a fabricated arrangement of 1s and 2s over twelve Blank instances my type system cannot tell apart."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem barcore_is_five_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on the 4-cell core of the bar, the lower port pixel, four dots of the readout, and two meter cells, (53,63) and (53,62). Eleven instances, one type, because the arm looks objects up by colour alone. The separators are all cells I have read: the bar core has colour 3 two rows above; the readout cores have a colour-1 dot immediately left; the port has colour 0 to its left; the old meter tip is the only instance whose rightof is off-board. I have re-checked every rule in this file against (53,62): its left neighbour is 2, its right neighbour is not a wall, two rows above it is background, so no rule of mine grounds on it in any state -- which is precisely why certify can report it wrong and report nothing else. It is a cell I own and cannot move, the right shape for a clock I cannot read."
    [depends: the_meter_is_a_clock_not_a_key  probe: passed]

  theorem the_swap_rules_are_forty_and_constraint_three_is_still_failed "One law -- take the colour of the cell six away -- is forty rules. recolored takes an INTEGER LITERAL, so a target colour cannot be read out of a cell and must be named, and the law splits once per source colour, per target colour, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I will not dress that up: forty rules to explain 72 cells twice over is worse than a lookup table, and I keep it only because the alternative is 96 unexplained pixels. What buys part of it back is that a TYPE IS A FRAME-0 COLOUR: the frame-0 configuration is W0, so a rule's source colour already says which half of the widget the instance lives in, and only the four truncation and regrowth rules need geometry on top of that. A consequence worth stating because it drives the playbook: every k1 rule demands that the instance still wears its frame-0 colour, which is true only in W0, so the whole family is silent in W1 BY CONSTRUCTION rather than by evidence."
    [depends: the_regrowth_is_the_answer_to_the_replay_mismatch  probe: passed]

  theorem no_goal_section_and_this_is_a_refusal_not_an_oversight "With no goal, is_goal is False everywhere, plan never returns sat, commit never runs, and every command this arm spends is a probe. I accept that consequence and still decline to write one, for arithmetic rather than modesty. Ten states have returned NOT_FINISHED and no other GameState has ever been seen, so no observation distinguishes a win from a non-win. The pos form is dead -- nothing in this world moves, every rule here is a recolour, and cegis_miner refused all seven tracks for exactly that reason. That leaves counts over seven types, and every count I can write names a CONFIGURATION: count(Frame, color = 5) = 14 says the box is up, count(Dot, color = 4) = 8 says the readout is dark, count(BarCore, color = 3) = 2 IS TRUE RIGHT NOW and would make the plan tier declare victory at a state I have no reason to call one. A false goal is worse than none, because it converts a probe budget into a confident wrong plan. WHAT ENDS THIS IS AN OBSERVATION, NOT AN EDIT: a GameState other than NOT_FINISHED, or any cell outside rows 30-41 and row 53 changing at all. ACTION5 and ACTION6 have never been pressed and are the cheapest place to look for it."
    [depends: the_meter_is_a_clock_not_a_key  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where nothing fires I assert identity in the same voice I use for what I watched. Audit at S9 = W1, both readouts blank. ACTION3: NOW WITNESSED -- t9 pressed it here and changed zero cells, exactly as entailed, and the silence I believed is a silence I have seen; this is the only entry in this audit that has been upgraded. ACTION7: predicted silent by the same entailment (its rules are k3's twins and the pattern they erase is already erased), unwitnessed in W1 but riding on a witnessed twin, and I believe it. ACTION2: fully predicted, 72 cells, the only action here my manual draws. ACTION1: PREDICTED SILENT ON ZERO WITNESSES and this is my largest forgery, 20 rules and one structural reading riding on it; worse, the silence is an artefact of every k1 guard demanding a frame-0 colour, so it is a property of my rule-writing rather than a claim about the world. I expect to be wrong and I want to be. ACTION4: predicted silent because bottom_port is 5 here -- a declared gap I chose over a wrong drawing. ACTION5, ACTION6: predicted silent, never pressed in ten states, no witness of any kind. And every one of these omits the clock: on command 12 one extra cell (53,61) turns 3 and I cannot draw it. A probe ranker prices a predicted identity at zero because every ablation agrees with a rule that does not fire, SO THE ACTIONS I MOST NEED ARE THE ONES IT CAN NEVER BUY, and saying so in prose is the only lever this desk has."
    [depends: exchange_versus_scroll_is_still_open_and_i_am_still_standing_where_it_can_be_asked, the_readout_belongs_to_the_box_so_i_have_guarded_action4_into_silence  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3998 constant cells, not just naming them board. A colour-4 panel fills rows 29-41 from col 17 to col 46 and carries a 4x4 block of colour 14 at rows 31-34, cols 42-45 -- the only colour-14 anywhere and the only structure on the panel. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them from it and why every mdl_segmenter blob is a 13x36 slab. Row 29 shows 5,5,3,3,5,5 at cols 11-16 and has NEVER changed: the bar reads seven rows tall on screen while only six of it is alive. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the clock, all colour 2 except its two rightmost cells, both now 3. Row 54 is a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved."
    [probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter reports BOTH variants at negative gain -- minus 7528 bits on 7 tracks, minus 7968 on 38 -- so by its own measure it compressed nothing and I take none of its structure. What I take is a frame-index witness independent of my rules: obj0 440 cells at frame 0, obj2 436 at frame 1, obj3 440 across frames 2-5, obj4 436 at frame 6, obj5 440 at frame 7, obj6 436 across frames 8-9. That is W0 W1 W0 W0 W0 W0 W1 W0 W1 W1 over ten frames, arrived at without any rule of mine, matching my reconstruction cell for cell, including the four-cell size difference that is the truncation, and including obj6's growth from one frame to two, which is t9's inertness seen from outside. cegis_miner refuses all seven tracks and its verdict that the world does not narrate as one mover remains the strongest negative result available. zero_space self-reports THIN in its own words -- 9 transitions constraining rank 5 of 686 features, null space 681 -- and its one global law is my census with both meter cells appended; I take the corroboration of the cell set and reject the law as unfalsified rather than confirmed, which is what its own report says."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me. STATE: S9 = S8 = W1, box in the top slot, bar four rows in the bottom, both readouts blank, (53,63) and (53,62) both 3, nine commands since RESET. ACTION1 HERE: my manual says nothing changes; I say that is false, and I name the outcomes in advance -- 72 cells back to W0 means exchange and 20 rules generalise by symmetry, anything else means scroll and the bottom glyph is a third item. ACTION2 HERE: exactly 72 cells, no readout cell, no row-53 cell. ACTION4 HERE: my manual says nothing changes; I expect the twelve cells at rows 32-33, cols 17-22 to light instead, which refutes the silence and confirms the readout follows the box. ACTION3, ACTION7: nothing changes, and ACTION3 has now been watched doing exactly that here. ACTION5, ACTION6: never pressed in ten states; I predict only that whichever is pressed produces the largest single addition to this manual available, and that it is the cheapest place a win condition could come from. THE CLOCK RIDES ON ALL OF THEM: commands 10 and 11 leave row 53 alone, command 12 turns (53,61) from 2 to 3 and I cannot draw it. A one-cell divergence in row 53 on the twelfth command confirms the clock and implicates nothing else in this file; a tick on command 10 or 11 refutes the period and I would rather learn that in three commands than in thirty."
    [depends: the_silences_i_assert_and_which_of_them_are_forged, no_goal_section_and_this_is_a_refusal_not_an_oversight  probe: pending]
