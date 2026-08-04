# theory.dsl -- seventh edition.
#
# WHAT THIS ROUND BOUGHT: FOUR COMMANDS, AND ONE LAW I CAN PROVE BUT CANNOT
# COMPILE. The store moved for the first time in three rounds: states 14->18,
# steps 14->18, distinct_states 10->13, dynamic_cells 99->101,
# cells_needing_an_owner 75->77, constant_cells 3997->3995. The four commands
# are t14 ACTION2, t15 ACTION1, t16 ACTION2, t17 ACTION4. Two new cells joined
# the dynamic set, (53,60) at t14 and (53,59) at t17, and both are meter cells.
#
# 1. THE METER IS A SIX-FRAME CLOCK. THE ARITHMETIC IS EXACT AND IT IS 5/5.
#    Cumulative frames returned, counting the RESET frame: t1..t17 =
#    3,5,7,9,10,12,14,16,17,19,21,23,25,27,29,31,33. The five ticks are at
#    t4 (9), t8 (16), t11 (21), t14 (27), t17 (33). The thresholds 9, 15, 21,
#    27, 33 are 9 + 6k, and each tick lands on the FIRST command whose
#    cumulative reaches or passes its threshold -- t3 stands at 7 < 9, t7 at
#    14 < 15, t10 at 19 < 21, t13 at 25 < 27, t16 at 31 < 33. Five ticks, two
#    parameters, no residual. The command-count reading (intervals 4,3,3,3)
#    and the wall-clock reading are both DEAD as exact laws: the frame reading
#    explains why the interval was 4 across t4-t8 (t5 returned ONE frame) and
#    why it was still 3 across t8-t11 despite t9 also returning one (the
#    counter is absolute, so t8 overshot its threshold by 1 and carried it).
#    See the_meter_is_an_absolute_six_frame_counter.
#
# 2. AND I STILL CANNOT WRITE IT AS A RULE, WHICH IS THE POINT. The counter is
#    HIDDEN STATE: it is not any function of the frame, and I re-proved that
#    this round with a fresh witness pair -- S11 = S13 exactly, ACTION2 from
#    S11 (t12) did not tick and ACTION2 from S13 (t14) did. The guard language
#    has no counter, no history and no frame-count term, so the law lives in
#    `laws:` and my replay stays wrong on the meter FOREVER, by construction
#    and now by a mechanism I can name. Logged as E-04.
#
# 3. MY STATE RECONSTRUCTION IS CONFIRMED BY A NUMBER I DID NOT FIT. I listed
#    the five duplicate pairs the widget parity and the meter force -- S2=S0,
#    S7=S5, S9=S8, S13=S11, S16=S14 -- and 18 - 5 = 13 = distinct_states
#    exactly. The census is confirmed twice over the same way: 24+8+14+12+22+
#    12+9 = 101 = dynamic_cells, and 101-24 = 77 = cells_needing_an_owner.
#
# 4. THE WORLD HAS COME BACK TO ITS OPENING POSITION. S17 is S0 in every
#    widget cell -- box in the BOTTOM slot rows 36-41, bar in the TOP slot
#    rows 30-35, bottom readout LIT, top readout dark -- and differs from it
#    only in five meter cells. Seventeen commands have moved nothing that
#    persists. There is still no progress variable anywhere in the widget, and
#    that is the strongest thing I can say about the goal.
#
# 5. THE MANUAL DREW t17 CORRECTLY AND I SAID SO IN ADVANCE. k4_dot_lights and
#    k4_core_lights fired on exactly the twelve readout cells, 8 to colour 1
#    and 4 to colour 2, because bottom_port (38,16) reads 1 in W0. Second
#    witness for those two rules; the guard I added on purpose held.
#
# WHERE I AM. S17 = W0, readout LIT, five meter cells lit, seventeen commands
# since RESET. The next swap will therefore move 96 cells, not 72 -- the first
# 96-cell diff since t2.
#
# WHAT I STILL HAVE NOT SEEN AFTER EIGHTEEN STATES: ACTION1 pressed in W1.
# ACTION2 pressed in W0. ACTION4 pressed in W1. ACTION5 or ACTION6 pressed at
# all. Any GameState but NOT_FINISHED. Any cell outside rows 30-41 and row 53
# changing.

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
  Field   [segment: dynamic_colour_5 ev: t0-t17 compress: 24]
  BarBody [segment: dynamic_colour_3 ev: t0-t17 compress: 8]
  BarCore [segment: dynamic_colour_2 ev: t0-t17 compress: 14]
  Blank   [segment: dynamic_colour_4 ev: t0-t17 compress: 12]
  Frame   [segment: dynamic_colour_6 ev: t0-t17 compress: 22]
  Hollow  [segment: dynamic_colour_0 ev: t0-t17 compress: 12]
  Dot     [segment: dynamic_colour_1 ev: t0-t17 compress: 9]

events:
  event recolored(o, c)

rules:
  rule k1_field_to_frame forall ?p in Field [ev: t1,t6,t8,t11,t13,t15 cov: 14/14]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_field_to_hollow forall ?p in Field [ev: t1,t6,t8,t11,t13,t15 cov: 8/8]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_field_to_dot forall ?p in Field [ev: t1,t6,t8,t11,t13,t15 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_field_to_core forall ?p in Field [ev: t1,t6,t8,t11,t13,t15 cov: 1/1]
    when act=key(1) and colored(?p, 5) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_bar_to_frame forall ?p in BarBody [ev: t1,t6,t8,t11,t13,t15 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_bar_to_hollow forall ?p in BarBody [ev: t1,t6,t8,t11,t13,t15 cov: 4/4]
    when act=key(1) and colored(?p, 3) and colored(below(below(below(below(below(below(?p)))))), 0) then recolored(?p, 0)

  rule k1_core_to_frame forall ?p in BarCore [ev: t1,t6,t8,t11,t13,t15 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(above(above(?p)), 3) and colored(below(below(below(below(below(below(?p)))))), 6) then recolored(?p, 6)

  rule k1_blank_to_dot forall ?p in Blank [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 1) then recolored(?p, 1)

  rule k1_blank_to_core forall ?p in Blank [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 4) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k1_frame_to_field forall ?p in Frame [ev: t1,t6,t8,t11,t13,t15 cov: 14/14]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_frame_to_bar forall ?p in Frame [ev: t1,t6,t8,t11,t13,t15 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_frame_clears forall ?p in Frame [ev: t1,t6,t8,t11,t13,t15 cov: 2/2]
    when act=key(1) and colored(?p, 6) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_frame_to_core forall ?p in Frame [ev: t1,t6,t8,t11,t13,t15 cov: 4/4]
    when act=key(1) and colored(?p, 6) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k1_hollow_to_field forall ?p in Hollow [ev: t1,t6,t8,t11,t13,t15 cov: 8/8]
    when act=key(1) and colored(?p, 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_hollow_to_bar forall ?p in Hollow [ev: t1,t6,t8,t11,t13,t15 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 3) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 3)

  rule k1_hollow_clears forall ?p in Hollow [ev: t1,t6,t8,t11,t13,t15 cov: 2/2]
    when act=key(1) and colored(?p, 0) and colored(above(above(?p)), 6) and colored(above(above(above(above(above(above(?p)))))), 3) then recolored(?p, 5)

  rule k1_dot_to_field forall ?p in Dot [ev: t1,t6,t8,t11,t13,t15 cov: 1/1]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_dot_to_blank forall ?p in Dot [ev: t1 cov: 8/8]
    when act=key(1) and colored(?p, 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k1_core_to_field forall ?p in BarCore [ev: t1,t6,t8,t11,t13,t15 cov: 1/1]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 0) and colored(above(above(above(above(above(above(?p)))))), 5) then recolored(?p, 5)

  rule k1_core_to_blank forall ?p in BarCore [ev: t1 cov: 4/4]
    when act=key(1) and colored(?p, 2) and colored(leftof(?p), 1) and colored(above(above(above(above(above(above(?p)))))), 4) then recolored(?p, 4)

  rule k2_field_from_frame forall ?p in Field [ev: t2,t7,t10,t12,t14,t16 cov: 14/14]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_hollow forall ?p in Field [ev: t2,t7,t10,t12,t14,t16 cov: 8/8]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_dot forall ?p in Field [ev: t2,t7,t10,t12,t14,t16 cov: 1/1]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_field_from_core forall ?p in Field [ev: t2,t7,t10,t12,t14,t16 cov: 1/1]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule k2_bar_from_frame forall ?p in BarBody [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_from_hollow forall ?p in BarBody [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 3) then recolored(?p, 3)

  rule k2_bar_regrows_from_hollow forall ?p in BarBody [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 0) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_bar_regrows_from_frame forall ?p in BarBody [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 3)

  rule k2_core_from_frame forall ?p in BarCore [ev: t2,t7,t10,t12,t14,t16 cov: 4/4]
    when act=key(2) and colored(?p, 6) and colored(below(below(below(below(below(below(?p)))))), 2) then recolored(?p, 2)

  rule k2_blank_from_dot forall ?p in Blank [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 1) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_blank_from_core forall ?p in Blank [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(below(below(below(below(below(below(?p)))))), 4) then recolored(?p, 4)

  rule k2_frame_from_field forall ?p in Frame [ev: t2,t7,t10,t12,t14,t16 cov: 16/16]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_bar forall ?p in Frame [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_frame_from_core forall ?p in Frame [ev: t2,t7,t10,t12,t14,t16 cov: 4/4]
    when act=key(2) and colored(?p, 2) and colored(above(above(above(above(above(above(?p)))))), 6) then recolored(?p, 6)

  rule k2_hollow_from_field forall ?p in Hollow [ev: t2,t7,t10,t12,t14,t16 cov: 10/10]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_hollow_from_bar forall ?p in Hollow [ev: t2,t7,t10,t12,t14,t16 cov: 2/2]
    when act=key(2) and colored(?p, 3) and colored(above(above(above(above(above(above(?p)))))), 0) then recolored(?p, 0)

  rule k2_dot_from_field forall ?p in Dot [ev: t2,t7,t10,t12,t14,t16 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_dot_from_blank forall ?p in Dot [ev: t2 cov: 8/8]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 1) then recolored(?p, 1)

  rule k2_core_from_field forall ?p in BarCore [ev: t2,t7,t10,t12,t14,t16 cov: 1/1]
    when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k2_core_from_blank forall ?p in BarCore [ev: t2 cov: 4/4]
    when act=key(2) and colored(?p, 4) and colored(above(above(above(above(above(above(?p)))))), 2) then recolored(?p, 2)

  rule k3_dot_blanks forall ?s in Dot [ev: t3 cov: 8/8]
    when act=key(3) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k3_core_blanks forall ?s in BarCore [ev: t3 cov: 4/4]
    when act=key(3) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k4_dot_lights forall ?s in Dot [ev: t4,t17 cov: 8/8]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 1)

  rule k4_core_lights forall ?s in BarCore [ev: t4,t17 cov: 4/4]
    when act=key(4) and colored(?s, 4) and colored(bottom_port, 1) then recolored(?s, 2)

  rule meter_first_tick_replay_patch forall ?s in BarCore [ev: t4 cov: 1/1]
    when act=key(4) and colored(?s, 2) and rightof(?s) = wall then recolored(?s, 3)

  rule k7_dot_blanks forall ?s in Dot [ev: t5 cov: 8/8]
    when act=key(7) and colored(?s, 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

  rule k7_core_blanks forall ?s in BarCore [ev: t5 cov: 4/4]
    when act=key(7) and colored(?s, 2) and colored(leftof(?s), 1) and colored(above(above(above(above(above(above(?s)))))), 4) then recolored(?s, 4)

laws:
  invariant field_instances count(Field) = 24 [status: census, re-read off the current frame, rows 30-35 cols 11,12,15,16]
  invariant barbody_instances count(BarBody) = 8 [status: census, rows 30,31,34,35 cols 13-14]
  invariant barcore_instances count(BarCore) = 14 [status: census, GREW BY 2 this round: 4 bar core + 1 port + 4 readout cores + 5 meter]
  invariant blank_instances count(Blank) = 12 [status: census, the dark top readout at frame 0, rows 32-33 cols 17-22]
  invariant frame_instances count(Frame) = 22 [status: census, 6+2+3+3+2+6 read down the box now standing in the BOTTOM slot rows 36-41]
  invariant hollow_instances count(Hollow) = 12 [status: census, 4+2+2+4 read down the same box]
  invariant dot_instances count(Dot) = 9 [status: census, 8 lit readout dots plus the upper port pixel (38,16)]
  invariant board_cells count(board) = 3995 [status: matches constant_cells exactly, down 2 because (53,59) and (53,60) turned dynamic]
  invariant total_owned_cells count(Field) + count(BarBody) + count(BarCore) + count(Blank) + count(Frame) + count(Hollow) + count(Dot) = 101 [status: matches dynamic_cells exactly, and 101 - 24 = 77 = cells_needing_an_owner]
  invariant meter_cells_lit count(BarCore, color = 3) = 5 [status: read off row 53 of the current frame, cols 59-63]

  theorem the_meter_is_an_absolute_six_frame_counter "THE LARGEST RESULT IN THIS FILE AND IT IS ARITHMETIC, NOT A GUESS. Let F(t) be the total number of grids the world has returned up to and including command t, counting the RESET frame: F = 3,5,7,9,10,12,14,16,17,19,21,23,25,27,29,31,33 for t1..t17. The five meter ticks are t4, t8, t11, t14, t17 and their F values are 9, 16, 21, 27, 33. The thresholds 9, 15, 21, 27, 33 are exactly 9 + 6k, and every tick is the FIRST command whose F reaches or passes its threshold: t3 stands at 7 < 9, t7 at 14 < 15, t10 at 19 < 21, t13 at 25 < 27, t16 at 31 < 33. Five ticks, two parameters, zero residual. THE COUNTER IS ABSOLUTE, NOT RESET ON TICK -- that is what explains the one interval every other reading fails on: t8 overshot threshold 15 by one frame, so only five further frames were needed for threshold 21 and the interval came out three commands long even though t9 returned a single frame. It also explains the drift my earlier editions mistook for a wall clock: a command returning two frames costs two clock units and one returning one frame costs one, so the interval in COMMANDS is 3 when every command is a swap and 4 when a one-frame command intervenes. Period-4-in-commands died two editions ago; period-3-in-commands and the wall clock die here. DATED PREDICTION, MADE BEFORE THE NEXT COMMAND: the next tick lights (53,58) and lands on the first command whose F reaches 39. If the next three commands each return two frames that is t20 and the command-count reading agrees; if exactly one of them returns a single frame -- ACTION7 returned one at t5, an inert ACTION3 returned one at t9 -- the frame clock says t21 and the command reading still says t20, and one cheap command decides between them."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: pending]

  theorem the_clock_cannot_be_compiled_and_this_is_a_language_limit_not_an_ignorance "I now know the mechanism and STILL cannot write a rule for it, and I want that stated plainly rather than smuggled into a guard. The counter is hidden state: it lives outside the grid, it is incremented by the world's own frame production, and the guard language admits only act=, free, colored, adjacent, comparisons of values, and cell = wall -- there is no counter term, no history term, no frames-returned term, and `recolored` takes an integer literal. So the honest manual predicts the widget exactly and the meter never, and my replay error is not a defect I can repair but a projection of a two-variable world onto a one-variable language. Logged as E-04. The consequence is quantified in the next theorem and it is a growing but strictly bounded and strictly located cost."
    [depends: the_meter_is_an_absolute_six_frame_counter  probe: passed]

  theorem the_replay_mismatch_is_answered_by_refusal_and_the_arithmetic_is_now_larger "The surprise fires again at certify t=7, ACTION1, one cell (53,62), manual 2 world 3 -- the cell and the transition index my fifth edition named in advance. It is the same divergence, inherited nine more times, and I refuse to repair it again. Current cost, exactly: 17 transitions, the first seven replay perfectly, and certify t=7,8,9 are wrong by one cell, t=10,11,12 by two, t=13,14,15 by three, t=16 by four -- 22 wrong-cell-transitions in total, growing by one cell every six frames and by nothing else, because NO RULE IN THIS FILE GROUNDS ON A METER CELL in any state. TWO REPAIRS WERE COMPUTED AND BOTH ARE REFUSED. (a) Propagation, a colour-2 BarCore whose right neighbour is 3 becomes 3: under cascade single_frame it walks one cell left per command, so by t17 it would have lit about thirteen cells against the world's five, and every extra cell it lights is still BOARD -- a confident wrong drawing on a cell that has never changed. (b) A second ACTION4-keyed patch, colour 2 with a colour-3 right neighbour under key(4), which would have drawn t17's tick exactly right and buys one transition. I refuse it because it fits a 2-of-2 coincidence: both ACTION4 presses ticked, but so did two ACTION1 presses and one ACTION2 press, and the frame clock explains all five while the key explains two. That patch would fire on the VERY NEXT ACTION4 press regardless of the clock, and ACTION4 is a key I intend to press again. A patch that would be wrong the moment I use it is worse than a declared gap."
    [depends: the_clock_cannot_be_compiled_and_this_is_a_language_limit_not_an_ignorance  probe: passed]

  theorem a_probe_goes_vacuous_exactly_when_the_world_ticks "PROMOTED FROM PENDING, 7 FOR 7, AND NOW WITH A MECHANISM. Of the seven probes I have been shown, P-06 (t11) and P-09 (t14) reported frontier_vacuous with zero survivors, and t11 and t14 are precisely the two commands among t10-t16 on which the meter ticked. P-05, P-07, P-08, P-10, P-11 each reported two survivors and their commands t10, t12, t13, t15, t16 each left row 53 alone. The mechanism is the previous theorem: every hypothesis on the frontier is my manual or an ablation of it, no hypothesis of mine can tick the meter, so on a ticking command the observed frame is outside the whole frontier and the probe eliminates nothing. This is a fact about my frontier, NOT about the world, and I refuse to read it as a widget mechanism. What it buys is real and free: a vacuous probe report is a TICK DETECTOR, so I can adjudicate the six-frame clock from the probe stream even when the raw diff is not in front of me."
    [depends: the_meter_is_an_absolute_six_frame_counter  probe: passed]

  theorem the_probes_that_said_the_manual_was_wrong_were_wrong_about_nothing_i_can_fix "P-10 (ACTION1, t15) and P-11 (ACTION2, t16) each reported THE MANUAL WAS WRONG at 4.882643 bits, which is log2(59/2) exactly, the same figure four earlier probes reported. P-09 and P-11 carry IDENTICAL predicted hashes and IDENTICAL observed hashes, which is itself a check on my reconstruction -- S14 and S16 are the same state, as the duplicate count requires. The divergence in every case is the meter cells my replayed state has wrong by construction, so my predicted hash cannot match no matter how perfectly I draw 96 of 101 cells, and every command I fully model will score as maximally informative forever. I therefore price these three refutations at ZERO structural content and I say so rather than editing a rule to chase them. The check that this is not an excuse: certify's cell-level report names ONE cell at the first divergence and it is a meter cell."
    [depends: a_probe_goes_vacuous_exactly_when_the_world_ticks  probe: passed]

  theorem the_five_duplicate_states_were_predicted_by_parity_and_the_store_agreed "A number I did not fit. From the widget parity, the readout state and the meter alone I list the duplicates among eighteen states: S2 = S0 (W0, readout lit, no meter cell lit), S7 = S5 (W0, dark, one lit), S9 = S8 (t9 ACTION3 changed nothing), S13 = S11 (W1, dark, three lit), S16 = S14 (W0, dark, four lit). Five coincidences, 18 - 5 = 13, and distinct_states = 13. Every element of my reconstruction -- which slot the box is in at each t, which readout is lit, and which meter cells are lit -- is loaded into that one number, and it came out right. S17 is NOT among the duplicates: it matches S0 in every widget cell but differs in five meter cells, so after seventeen commands THE WORLD IS BACK WHERE IT STARTED except for the clock."
    [probe: passed]

  theorem every_coverage_column_sums_to_its_type "Re-derived against the new instance counts. For each type the k1 rules partition its instances and so do the k2 rules: Field 14+8+1+1 = 24 both ways. Frame 14+2+2+4 = 22 going down and 16+2+4 = 22 coming up. Hollow 8+2+2 = 12 and 10+2 = 12. BarBody 4+4 = 8 and 2+2+2+2 = 8. Dot 1+8 = 9. Blank 8+4 = 12. BarCore 4+1+4 = 9 OF 14, and the deficit is now FIVE rather than three, because the two cells that turned dynamic this round are meter cells and joined BarCore by their frame-0 colour. So 96 of 101 owned cells are covered in both directions and the uncovered five are exactly the five cells no rule of mine may touch. The deficit will grow by one every six frames and it will never be anything but meter."
    [depends: the_clock_cannot_be_compiled_and_this_is_a_language_limit_not_an_ignorance  probe: passed]

  theorem the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help "Carried, and re-witnessed this round with a fresh pair. The old witness: S5 and S7 are the same frame, ACTION1 from S5 changed 72 cells and no meter cell, ACTION1 from S7 changed 73 and the extra was (53,62). The new witness: S11 and S13 are the same frame -- both W1, both readouts dark, meter {61,62,63} -- and ACTION2 from S11 at t12 left row 53 alone while ACTION2 from S13 at t14 lit (53,60). Same frame, same key, different successor, twice, under two different keys. My compiled step is a function of the frame, so it is WRONG on the meter and must stay wrong. What changed this round is that I now know WHAT the extra variable is."
    [probe: passed]

  theorem exchange_versus_scroll_is_still_open_and_the_discriminating_press_has_moved_to_action2 "READING A, exchange: two 6-row slots trade images and ACTION1 and ACTION2 are the same involution. READING B, scroll: a list steps by six rows, ACTION1 one way and ACTION2 the other, and the four-row glyph is a third item. Eleven swaps are observed now -- ACTION1 at t1, t6, t8, t11, t13, t15 and ACTION2 at t2, t7, t10, t12, t14, t16 -- and EVERY ACTION1 was pressed in W0 and EVERY ACTION2 in W1, so ACTION1 has still never followed ACTION1 and the question is untouched after eighteen entries. I now stand in W0, so the cheap discriminating press has swapped identity: ACTION2 HERE. Exchange predicts it reproduces exactly what ACTION1 does from here; scroll predicts a configuration never seen. The evidence still tilting to A: row 29 reads 5,5,3,3,5,5 at cols 11-16 and has never changed in eighteen states. And there is a bonus this round -- the bottom readout is LIT again, so whichever swap I press moves 96 cells rather than 72 and re-witnesses the four readout-transfer rules that have stood on a single witness since t1 and t2."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem the_bar_is_six_rows_above_and_four_below_in_both_directions "The bar reads 3,3 / 3,3 / 2,2 / 2,2 / 3,3 / 3,3 down rows 30-35 at cols 13-14 in the top slot -- re-read off the current frame, where it is standing -- and 3,3 / 3,3 / 2,2 / 2,2 down rows 36-39 in the bottom with rows 40-41 background. Going down the last two rows CLEAR; coming up they REGROW as 3, which is what the two k2 regrowth rules draw and what six ACTION2 presses have now witnessed without a replay complaint. The box renders 22 frame cells and 12 hollow cells in either slot without loss. So the swap is not an information-preserving exchange of two 6x6 windows: the bottom slot is lossy for the bar and the loss is restored from nowhere visible."
    [probe: passed]

  theorem the_readout_belongs_to_the_box_and_action4_was_drawn_right_a_second_time "At t1 the LIT readout travelled with the box from rows 38-39 to rows 32-33, twelve cells of pattern moving six rows in the step the box did. t17 confirms the binding from the other side: ACTION4 pressed in W0, with the box in the bottom slot and bottom_port (38,16) reading 1, lit exactly the twelve cells at rows 38-39 cols 17-22 -- eight to colour 1 and four to colour 2 -- which is precisely what k4_dot_lights and k4_core_lights draw, second witness, no unpriced cell. The lit pattern is two copies of a 2x3 glyph: reading columns 17..22, (2,1)(1,1)(1,2)(2,1)(1,1)(1,2). ACTION4 IN W1 REMAINS UNPRESSED after eighteen entries. Unguarded my k4 rules would light a strip the box has left, twelve cells drawn confidently wrong; the guard colored(bottom_port, 1) makes them fire on nothing there, so my manual is SILENT about ACTION4 in W1 and that silence is a declared gap, not a claim."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: pending]

  theorem barcore_is_five_unrelated_things_and_the_arm_sees_only_colour "Colour 2 at frame 0 sits on the 4-cell core of the bar, the lower port pixel (39,16), four dots of the readout, and now FIVE meter cells (53,59) through (53,63). Fourteen instances, one type, because the arm looks objects up by colour alone. The separators are all cells I have read: the bar core has colour 3 two rows above, the readout cores have a colour-1 dot immediately left, the port has colour 0 to its left, and the meter cells have neither. I re-checked every rule against every meter cell again this round: no k1, k2, k3, k4 or k7 guard grounds on one in any state, which is why they can be wrong in replay without contaminating a single other cell, and why certify's divergence set is exactly the cells the clock has lit and my patch did not."
    [depends: the_tick_is_not_a_function_of_the_frame_and_no_guard_language_can_help  probe: passed]

  theorem the_swap_rules_are_forty_and_constraint_three_is_still_failed "One law -- take the colour of the cell six away -- is forty rules. recolored takes an INTEGER LITERAL, so a target colour cannot be read out of a cell and must be named, and the law splits once per source colour, per target colour, per direction, per key. THE CONCEPT DOES NOT PAY FOR ITSELF and I will not dress that up: forty rules to explain 96 cells twice over is worse than a lookup table, and I keep it only because the alternative is 96 unexplained pixels. What buys part of it back is that a TYPE IS A FRAME-0 COLOUR, so a rule's source colour already says which half of the widget its instance lives in, and only the four truncation and regrowth rules need geometry on top. The consequence that drives the playbook is unchanged and is now symmetric: every k1 rule demands its instance still wear its frame-0 colour, true only in W0, and every k2 rule demands the swapped colour, true only in W1. So twenty rules are silent in W1 and twenty in W0 BY CONSTRUCTION rather than by evidence -- and I am standing in W0, where the twenty silent ones are the k2 family."
    [depends: the_bar_is_six_rows_above_and_four_below_in_both_directions  probe: passed]

  theorem action6_may_be_a_click_and_the_colour_14_block_is_the_only_target_on_the_board "A guess I am labelling as one. Five of the seven keys have been pressed and all five act on the widget in rows 30-41; ACTION5 and ACTION6 have never been pressed in eighteen entries. In this action family a coordinate-carrying action is common, and the guard language cannot express one -- there is no way to write act=click(row, col) and no way to name an arbitrary cell without declaring a landmark for it. If one of the unpressed keys is a click, the only structure on the board that looks like a target is the 4x4 block of colour 14 at rows 31-34, cols 42-45: it is the sole appearance of colour 14 anywhere, it sits alone on the colour-4 panel, and nothing in eighteen commands has touched it. Logged as E-05. I assert nothing about what pressing it does; I assert only that this is where I would look and that my manual currently cannot draw any consequence of it."
    [probe: pending]

  theorem no_goal_section_and_the_refusal_is_now_stronger_than_it_was "The heuristic_miss is right that is_goal is False everywhere, that plan never returns sat, that commit never runs and that every command is a probe. I accept every one of those consequences and still decline, and this round gives me a new argument rather than the old one repeated. NEW: after seventeen commands the widget has returned EXACTLY to its opening configuration -- S17 equals S0 in all 96 widget cells -- so nothing I have done is cumulative and there is no monotone quantity anywhere in the widget that a goal could name. The only monotone quantity in this world is the meter, and the meter is a CLOCK driven by frames returned, not by what I press, so it is not progress; it is either decoration or a budget, and a goal over a clock is a goal over the passage of time. The old arithmetic still holds too: the un-ticked meter cells have never changed, so they are board rather than instances, and count(BarCore, color = 3) can never exceed 14 while nine of those fourteen are widget cells with nothing to do with the meter (E-02). And the thing I actually want to write -- goal gamestate != NOT_FINISHED -- has no term in the goal language at all (E-03). A false goal converts a probe budget into a confident wrong plan, which is strictly worse than silence. WHAT ENDS THIS, unchanged and now urgent: a GameState other than NOT_FINISHED, or any cell outside rows 30-41 and row 53 changing at all. Both are most likely to come from ACTION5 or ACTION6."
    [depends: the_five_duplicate_states_were_predicted_by_parity_and_the_store_agreed, action6_may_be_a_click_and_the_colour_14_block_is_the_only_target_on_the_board  probe: pending]

  theorem the_silences_i_assert_and_which_of_them_are_forged "The compiled step is total, so where nothing fires I assert identity in the same voice I use for what I watched. Audit at S17 = W0, bottom readout LIT, five meter cells lit. ACTION1: fully predicted, and this time 96 cells rather than 72 because the lit readout travels with the box -- six witnesses for the swap, one witness for the readout transfer. ACTION3: predicted to blank the twelve lit readout cells, witnessed doing exactly that at t3 in this exact configuration. ACTION7: same twelve cells, witnessed at t5. ACTION4: predicted silent here because the readout is already lit and the k4 guards demand colour 4; entailed, not forged. ACTION2 HERE: PREDICTED SILENT ON ZERO WITNESSES, and this is now my largest forgery -- twenty rules ride on it and the silence is an artefact of every k2 guard demanding a swapped colour, so it is a property of my rule-writing rather than a claim about the world. I expect to be wrong and I want to be. ACTION5, ACTION6: predicted silent, never pressed, no witness of any kind, and a silent one-frame answer would itself adjudicate the six-frame clock. And every one of these omits the meter: whichever key is pressed, (53,58) turns 3 on the command that carries the clock past 39."
    [depends: exchange_versus_scroll_is_still_open_and_the_discriminating_press_has_moved_to_action2, the_meter_is_an_absolute_six_frame_counter  probe: pending]

  theorem what_lies_outside_the_widget "Full-frame responsibility means describing the 3995 constant cells, not just naming them board, and certify agrees at 0 of 4096 unexplained. A colour-4 panel fills rows 29-41 from col 17 to col 46 and carries a 4x4 block of colour 14 at rows 31-34, cols 42-45 -- the only colour 14 anywhere and the only structure on the panel. Both readouts are cut into that panel's left edge, which is why connected_components(4) cannot separate them and why every mdl_segmenter blob is a 13x36 slab. Row 29 shows 5,5,3,3,5,5 at cols 11-16 and has never changed in eighteen states: the bar reads seven rows tall on screen while only six of it is alive. Rows 42-52 are background across the window, which is what lets every bottom-half rule test six rows down without a wall test. Row 53 is the meter: colour 2 from col 10 to col 58 and colour 3 at cols 59-63, re-read off the current frame, which is five lit cells and matches five ticks. Row 54 is a solid colour-4 rule. Colours 8 and 9 appear in colours_seen and on no dynamic cell, so they sit on the board outside this window and have never moved. The meter has 49 unlit cells left inside the dynamic window; at six frames a cell and two frames a command that is about 147 more commands, which is the only number resembling a budget that this world has ever shown me."
    [depends: the_meter_is_an_absolute_six_frame_counter  probe: pending]

  theorem what_the_engines_gave_me "The candidate excerpt supplied this round is cegis_miner and nothing else, and it is the same refusal profile for the third round running: every track either refused because the transition narrates vanish rather than move, or refused because the object is absent at frame 0, or mined to NoSeparatingGuard on transition 1 or 2. I take NO structure from it and I accept its verdict as the strongest negative result available here -- THIS WORLD DOES NOT NARRATE AS ONE MOVER, and a miner built for movers is right to refuse rather than invent one. The 2866-row stream contains no named object and no rule I can check. What the engines could not have found is the thing that made this edition: the meter law is arithmetic over the FRAME COUNTS of commands, which is not in the grid at all and is invisible to any engine that mines transitions cell by cell."
    [probe: passed]

  theorem what_i_predict_before_i_see_it "Written so it can cost me, as three of these already have. CERTIFY, next run, if no command is pressed: 7 of 17 transitions replay exactly, first divergence certify t=7 ACTION1, the single cell (53,62) manual 2 world 3, then one wrong cell at t=8 and t=9, two at t=10, t=11, t=12, three at t=13, t=14, t=15 and four at t=16, twenty-two wrong-cell-transitions in all and every one of them on row 53; responsibility 0 of 4096; 0 clashes; 90 of 90 pairs adjudicated. STATE: S17 = W0, box bottom rows 36-41, bar top rows 30-35, bottom readout LIT, top readout dark, meter cols 59-63. ACTION1 HERE: 96 cells at rows 30-41 cols 11-22, the first 96-cell diff since t2, re-witnessing the four readout-transfer rules that have stood on one witness each since t1. ACTION2 HERE: my manual says nothing changes; I say that is false and I name the outcomes in advance -- 96 cells reproducing exactly what ACTION1 does from here means exchange and twenty rules generalise by symmetry, any configuration never seen before means scroll and my word_table is a two-item special case, and genuine silence would be the most surprising result of the run. ACTION3 and ACTION7 HERE: exactly the twelve readout cells at rows 38-39 cols 17-22 go to colour 4, and ACTION7 does it in ONE frame while ACTION3 does it in two. ACTION5, ACTION6: I predict only that whichever is pressed produces the largest single addition to this manual available, and that if it is inert it returns one frame. THE METER: (53,58) turns 3 on the first command whose cumulative frame count including RESET reaches 39, which is t20 if every intervening command returns two frames and t21 if exactly one returns one; the probe report on that command will be frontier_vacuous with zero survivors; and no other cell of row 53 changes before then."
    [depends: the_meter_is_an_absolute_six_frame_counter, the_silences_i_assert_and_which_of_them_are_forged  probe: pending]
