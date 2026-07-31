# theory.dsl -- THIRD DRAFT. Four more commands arrived (t6..t9) and they paid
# for themselves several times over. Three things fired at me and each is
# answered below by a change, not by a paragraph.
#
# 1. THE WORLD IS NOT A FUNCTION OF THE FRAME. This is the finding of the
#    round and it is a proof from the record, not a guess.
#      S5 (after t5, key(7)) and S7 (after t7, key(3)) are the SAME FRAME:
#      strip B blanked, (53,63)=3, everything else frame 0. The store agrees --
#      10 states, 7 distinct, and the three collisions are exactly S2=S0,
#      S6=S4, S7=S5.
#      key(4) from S5 gave S6 with NO meter change.
#      key(4) from S7 gave S8 with (53,62): 2 -> 3.
#    Same visible state, same key, different successor. No manual whose rules
#    read only colours can produce both, mine included, and constraint 5
#    forbids writing two rules that both fire. There is a counter behind the
#    glass. I say so in the_world_has_hidden_state..., I decline to fake it,
#    and I pre-register exactly which two transitions I therefore lose.
#
# 2. MY PRE-REGISTRATION WAS HALF RIGHT AND I SCORE BOTH HALVES. I wrote that
#    the second tick would diverge at ONE cell, (53,62), 2 -> 3, and nowhere
#    else. The cell is right -- the bar is consumed RIGHT TO LEFT, which was a
#    guess and is now measured -- and the timing is wrong: it came on the THIRD
#    key(4) press, not the second. That miss is the whole of finding 1.
#
# 3. THE METER IS PROBABLY A CLOCK, NOT A TOLL. Ticks landed after global
#    action 4 and after global action 8. t6 was a key(4) press that restored
#    twelve cells and cost nothing. So "key(4) is the metered action and the
#    other keys are free", which I wrote last round, is refuted: either every
#    action ticks the bar one cell per four, or the tick follows odd-numbered
#    key(4) presses. Both need hidden state; they differ on a probe that costs
#    three actions and none of them key(4). This inverts the playbook -- there
#    is nothing to ration and no reason to hoard.
#
# WHAT I ALSO LEARNED BY FINALLY BEING SHOWN THE PIXELS
#
# 4. THE STRIP IS A WINDOW ONTO ONE GLOBAL DIAGONAL TEXTURE. Frame 0 rows 38
#    and 39, cols 16-22, and the row the world drew at t1 in lane A, row 32,
#    cols 16-22, are all covered by ONE rule: colour 2 where (r + c) mod 3 = 1,
#    colour 1 otherwise. 21 cells, three rows, two lanes, no exception. It
#    predicts the row I have never been shown, row 33, exactly. Last round I
#    asked whether the strip was one display or two patterns; the answer is
#    better than either -- it is one texture, and each lane shows two rows of
#    it. See the_strip_is_one_global_diagonal_texture.
#
# 5. COL 16 IS A SEED AND IS NEVER ERASED. Blanking takes cols 17-22 and stops.
#    (38,16)=1 and (39,16)=2 survive every blank, and both continue their row's
#    period-3 run leftward. That is why key(4) can restore the pattern cell for
#    cell: what it needs is still on the glass.
#
# 6. THE WIDGET ANATOMY CLOSES ARITHMETICALLY. The selected slot is a 6x6 box,
#    rows 36-41 x cols 11-16: colour-6 ring (20) minus two right-edge ports
#    (38,16),(39,16) plus a colour-6 2x2 core at rows 38-39 x cols 13-14 = 22
#    Casing; colour-0 cavity rows 37-40 x cols 12-15 minus that core = 12
#    Cavity. An unselected slot is a 2-wide bar at cols 13-14: colour 3 at its
#    four outer rows (8 Rail) and colour 2 at its two middle rows (4 Stud), the
#    other 24 cells of its 6x6 footprint being background. 22+12+8+4 = 46,
#    plus 9 Pip and 5 Stud in strip and ports and 12 Erased in lane A and 2
#    Stud in the bar = 74, which is cells_needing_an_owner to the unit, and
#    74 + 24 background = 98 = dynamic_cells. The t1 diff of 96 cells is
#    36 + 36 + 12 + 12 with nothing left over. The drawing is settled.
#
# WHAT I STILL REFUSE. The selector swap stays out of rules: the witness pairs
# in the_swap_is_provably_inexpressible_here are unchanged and silence still
# buys me six replayed transitions instead of none.

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
  landmark slot_above_head  # arc-cell: (24, 11)
  landmark strip_a_seed  # arc-cell: (32, 16)
  landmark strip_b_seed  # arc-cell: (38, 16)
  landmark strip_a_row_two  # arc-cell: (33, 17)
  landmark strip_b_row_two  # arc-cell: (39, 17)
  landmark rail_witness  # arc-cell: (29, 13)
  landmark badge_head  # arc-cell: (31, 42)
  landmark meter_tip  # arc-cell: (53, 63)
  landmark meter_next  # arc-cell: (53, 62)
  landmark meter_third  # arc-cell: (53, 61)
  Casing [segment: colour_class_6 ev: t0-t9 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t9 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t9 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t9 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t9 compress: 11]
  Erased [segment: colour_class_4 ev: t0-t9 compress: 12]

events:
  event recolored(o, c)

# The six strip rules are UNCHANGED in form and now carry three witnesses each
# for key(3) and three for key(4) instead of one. The seventh rule, the meter
# tick, is the only edit: (53,62) has now varied, so the arm will hand it a
# Stud instance (cells_needing_an_owner went 73 -> 74), and the old guard
# `above=5 and below=4` is true of BOTH bar cells, which would have ticked them
# together at t4. `rightof(?p) = wall` is the one documented guard that names
# the rightmost cell and nothing else. If that form does not fire, the symptom
# is a one-cell divergence at (53,63) on t4 and the repair is
# `not colored(rightof(?p), 2)`; I say this here so the failure is diagnosable
# rather than mysterious.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3,t7,t9 cov: 24/24]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3,t7,t9 cov: 12/12]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 5) and not colored(rightof(?p), 5) and not colored(above(?p), 5) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4,t6,t8 cov: 24/24]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4,t6,t8 cov: 12/12]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_advances_the_meter_once forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall and colored(below(?p), 4) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 11 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 74 [status: proven]

  theorem the_world_has_hidden_state_two_identical_frames_answered_the_same_key_differently "S5, reached by key(7) at t5, and S7, reached by key(3) at t7, are the same frame cell for cell: strip B blanked to colour 4 over rows 38-39 x cols 17-22, (53,63) already colour 3, everything else as frame 0. key(4) from S5 produced S6 with no change outside the strip; key(4) from S7 produced S8 with (53,62) 2 -> 3 as well. Same state, same action, two successors. The store corroborates independently: 10 states, 7 distinct, and the only way to get three collisions out of this trace is S2=S0, S6=S4, S7=S5. So the world carries a counter the frame does not show, my guard language has no counters and no memory of the previous action, and constraint 5 forbids two rules that both fire on one instance. I therefore write the tick I can witness once and none of the ticks I cannot, and I state the cost rather than hide it: replay will report 6/9, with the first divergence at transition 0 (ACTION1, 96 cells, the selector I refuse to guess) and one-cell divergences at transitions 7 and 8, both at (53,62), both because my bar is one unit longer than the world's from that point on. Any divergence anywhere else refutes this reading."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_second_tick_landed_where_i_said_and_when_i_did_not "last round I pre-registered the shape of my own failure: the next tick would be a single cell, (53,62), 2 -> 3, and nowhere else. That is exactly what arrived, so the bar is consumed RIGHT TO LEFT and the arm does hand a cell an instance the moment it stops being constant -- cells_needing_an_owner went 73 to 74 and dynamic_cells 97 to 98, which is that one cell and no other. What I got wrong was the timing: I said the second key(4) press and it was the third, because t6 was a key(4) press that restored twelve cells and moved no bar at all. I record the miss plainly: it refutes 'key(4) is the metered action', which I had asserted on one witness, and it is the observation that forced the hidden-state theorem."
    [depends: the_world_has_hidden_state_two_identical_frames_answered_the_same_key_differently  probe: passed]

  theorem the_meter_is_probably_a_clock_and_not_a_toll "the two ticks landed after global action 4 and after global action 8. Two readings survive. CLOCK: the bar loses one cell every four actions whatever they are, so the game is timed, 62 cells remain and about 248 actions with them, and no key is cheaper than any other. TOLL WITH PARITY: the tick follows the first, third, fifth key(4) press. Both require the hidden counter and neither is expressible here, so the manual cannot choose between them and does not try. The separator is cheap and I want it early: spend three consecutive actions none of which is key(4). The clock reading says (53,61) turns 3 on the third of them; the toll reading says the bar does not move at all. Frame counts cannot substitute -- cumulative frames at the ticks were 8 and 15, no period. This question outranks every refinement of the drawing because it decides whether there is any reason to be frugal, and after t6 there is no evidence left that any single key costs anything."
    [depends: the_second_tick_landed_where_i_said_and_when_i_did_not  probe: pending]

  theorem the_meter_cadence_is_inexpressible_in_this_language "a guard reads a cell's colour, its four neighbours' colours, off-board, and the action name. A cadence needs a count of past actions, and there is no count anywhere in the grammar -- not in guards, not in values, not in events. I could fake a parity bit only by recolouring some cell the world does not recolour, which is a guaranteed responsibility or replay failure, so faking it is strictly worse than silence. This is the second thing this world does that the language cannot say; the first is the selector swap. Both are recorded as prose and neither is smuggled into rules."
    [depends: the_world_has_hidden_state_two_identical_frames_answered_the_same_key_differently  probe: passed]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have ever seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Witnesses: frame 0 row 38, cols 16-22, reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, which are the same period-3 run offset by one column; and at t1 the world drew lane A's row 32, cols 16-22, as 1 2 1 1 2 1 1 -- the divergence report gave me (32,16)=1 and (32,17)=2 and (32,20)=2 and the rest, and every one of those 21 cells satisfies the rule. So the two strips are not two stored patterns and not one display that follows the selection; they are two windows onto a single diagonal texture that runs across the whole arena, which is why key(4) can restore twelve cells cell for cell and why the ports at col 16 continue their row's run leftward. The prediction, made before looking: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2, with (33,16) colour 2. Nothing needs it in rules -- the colour classes already restore the right colours because each instance remembers its frame 0 colour -- so it earns its place as structure, not as prediction, and I flag that: by constraint 3 this concept currently buys understanding rather than symbols."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, three times for key(3) and once for key(7), twelve cells every time. (38,16)=1 and (39,16)=2 sit on the widget's right edge, are Pip and Stud instances, and have never changed under any blank. They are the only cells of the texture that survive hiding, and they are exactly the two cells needed to phase a period-3 run. I read col 16 as a seed the world keeps visible; the alternative is that it is simply part of the widget's border and the survival is a coincidence of the 6x6 box ending there. Both are consistent with nine transitions."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I was shown with two edits: rows 38-39 x cols 17-22 hold the texture rather than colour 4, and (53,63) and (53,62) hold 2 rather than 3. The reconstruction is now over-determined. Open-loop replay matched the world from t2 onward, which can only happen if the world returned to my frame 0 after key(2). The widget anatomy closes: 22 Casing as a 20-cell ring minus two ports plus a 2x2 core, 12 Cavity as a 4x4 minus that core, 8 Rail and 4 Stud as the unselected bar at cols 13-14, 9 Pip and 5 Stud in the strips and ports, 12 Erased in lane A, 2 Stud in the meter bar, total 74 = cells_needing_an_owner. The 24 remaining dynamic cells are exactly the background cells of the unselected slot's 6x6 footprint, and 74 + 24 = 98 = dynamic_cells. The t1 diff of 96 cells is 36 for panel A plus 36 for panel B plus 12 for lane A's strip rows plus 12 for lane B's, with nothing left over. Load-bearing and measured from three independent directions."
    [probe: passed]

  theorem replay_is_open_loop_and_silence_on_the_selector_is_worth_six_transitions "the manual is run forward from frame 0 without resync, which is why last round reported 4/5 with its first divergence at t=0. My manual is a no-op on key(1) and key(2), so it sat at frame 0 through both, the world left and came back, and every strip transition since has replayed on top of it. A wrong rule for key(1) would not cost one transition, it would desynchronise the manual from the world permanently and cost all nine. That is the numerical argument for silence and it got stronger this round, not weaker: silence now buys six of nine instead of four of five."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied in nine transitions, so they are board. Colour 3 at cols 13-14 is exactly what an unselected slot shows at its four outer rows, and the unselected slot at rows 30-35 shows 3 3 2 2 3 3 down cols 13-14, so row 29 sits where the last row of a slot at rows 24-29 would sit. Below, rows 42 onward are uniform background, so the slot at rows 36-41 is the bottom one. I read key(1) as move-selection-up-one-slot and key(2) as move-selection-down-one-slot. The probe I named last round was not run and it is still the cheapest structural test in the game, now in two halves: from the bottom slot key(2) should do nothing under the move reading and repaint 96 cells under a two-slot toggle; and from the upper slot key(1) should repaint rows 24-35 if a third slot exists and do nothing if slot A is the top. My manual, being silent, already predicts 'nothing' for both, so either press scores it for free."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_arena_is_lanes_and_the_badge_is_row_aligned_with_the_cavity "the arena is colour 4 over cols 17-46, rows 30-41 at least. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 x cols 42-45. Those are precisely the rows a selected slot's 4x4 cavity occupies within its own 6-row band -- the cavity of the selected bottom slot is rows 37-40 within band 36-41, and the badge is rows 31-34 within band 30-35. So the badge is a cavity-shaped, cavity-aligned object at the far right of slot A's lane, and slot B's lane has nothing at cols 42-45. Two readings: the badge is a target the lane's cavity or strip must be made to match, or it is simply a marker that slot A carries a task and slot B does not. Zero transitions bear on either. Slots above row 29 may carry badges I have never seen, since an unvarying badge is board by definition."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_strip_hides_and_shows_and_no_key_has_been_shown_to_cost_anything "key(3) blanked a shown strip at t3, t7 and t9; key(7) blanked one at t5; key(4) restored a blanked one at t4, t6 and t8, identically every time, so the pattern lives somewhere the frame does not show and blanking does not destroy it. What I wrote last round -- that key(4) is the metered action and the rest are free -- is refuted by t6, a key(4) press that moved no bar. What is still untested after nine transitions is the same thing as after five: key(3) has never been pressed from a blanked strip and key(4) has never been pressed from a shown one. Until one of those happens, hide-and-show and toggle-and-toggle are indistinguishable, and the current state is blanked, so the separator costs exactly one action and my manual predicts inert for it -- which makes it a test of the manual as well as of the world."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language can produce them. A guard sees a cell's own colour and its four neighbours' colours and nothing else -- no coordinate, no row band, no distance. Under key(1) the new colour of a panel cell is a function of its offset within a six-row period, and that offset is not determined by the four neighbour colours. Witnesses, all in frame 0: (30,12) and (31,12) are colour 5 with above 5, below 5, left 5, right 3, and must become 6 and 0; (41,12) and (41,13) are colour 6 with above 0, below 5, left 6, right 6, and must become 5 and 3; (32,18) and (32,20) are colour 4 with all four neighbours colour 4, and must become 1 and 2. Worse, (30,16), (31,16), (32,16), (33,16), (34,16) are all colour 5 with above 5, below 5, left 5, right 4 and must become 6, 6, 1, 2, 6 -- four distinct answers to one indistinguishable question. Constraint 5 forbids writing both rules. The swap does not go in the manual."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem nesting_would_break_the_ties_and_would_still_fail_the_gain_test "if above(above(?p)) compiles -- the grammar does not list it -- a chain of nested neighbours could count a cell's distance from the panel edge and recover its offset in the period. I decline that route twice over. A guard form the grammar does not document is a parse risk, and a manual that fails to parse loses all six transitions it currently replays. And distinguishing 96 cells by 96 neighbour chains costs more symbols than the 96 pixels it explains, which is exactly the failure constraint 3 names. Inexpressible without nesting, uncompressible with it."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, which is rows 29-54 x cols 10-63. They are therefore somewhere in the 3998 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility is safe; but it is also where any title, target display, score or instruction would live, and it is the most likely home of whatever finishing means. I mention it because it is the largest thing I do not know, and because the only way to see it is to make a cell of it change, which is another argument for pressing the selector past the slots I have already mapped."
    [depends: no_goal_section_on_purpose  probe: pending]

  theorem cascade_length_carries_no_signal_here "t1 through t4 and t6 through t9 each returned 2 frames and t5 returned 1, yet t5 (key(7)) and t7 (key(3)) produced identical 12-cell effects, and t6 (key(4), 2 frames) and t8 (key(4), 2 frames) produced different effects. Frame count tracks neither the magnitude nor the presence nor the identity of change and must not be used as a motion detector. The one thing it may still carry is that ACTION7 is a different key from ACTION3 that happened to agree in this state."
    [probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot's middle rows, a port, four strip cells and two cells of the meter bar -- four unrelated roles. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm is what draws the frame. The gain is measured: six declarations own all 74 cells that need an owner against 74 pixels written out, responsibility reports 0 unexplained, and seven rules over those classes reproduce six of nine transitions. The cost is measured too: no rule can name the strip, so every strip rule carves it out of its class with four negative neighbour guards, and the meter rule now needs an off-board test to separate two cells of the same class two columns apart. Those guards are pixel-fitting in a costume; they are correct on every instance of both classes in frame 0, they have survived three blanks and three restores, and they are the price of a colour-first arm."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem instance_anchoring_is_frame_zero_and_the_arm_extends_it_as_cells_vary "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0. Two consequences, both now confirmed rather than assumed. A cell constant in frame 0 gets no instance, which is why the slots above row 29 are invisible to this manual and why it cannot draw the selector. And a cell that later varies stops being board and gains one: (53,62) was constant through t7 and owned by nothing, then varied at t8, and cells_needing_an_owner went from 73 to 74 with dynamic_cells 97 to 98. I have raised stud_population to 11 accordingly, and that new instance forced the meter rule's guard to be rewritten, since the old one was true of both bar cells and would have ticked them together at t4."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem two_keys_have_never_been_pressed "this world has seen ACTION1, 2, 3, 4 and 7. key(5) and key(6) are unpressed and unknown, and the case for pressing them just got much stronger: t6 showed that a key press can accomplish twelve cells of change and move the bar not at all, so the cost of an experiment is at worst one quarter of a bar cell out of sixty-two remaining. If either is a click carrying coordinates, this guard language cannot express it at all and the finding will be recorded as prose. Pressing them also doubles as the meter probe, since neither is key(4)."
    [depends: the_meter_is_probably_a_clock_and_not_a_toll  probe: pending]

  theorem no_goal_section_on_purpose "all ten states returned NOT_FINISHED and nothing in nine transitions indicates what finishing means. The live candidates are that a lane's texture must be brought to agree with the badge at its far end, that every slot in the column must be visited or solved, or that the objective is in the rows I have never been shown. An absent goal compiles to is_goal -> False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level."
    [depends: the_arena_is_lanes_and_the_badge_is_row_aligned_with_the_cavity  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "mdl_segmenter returned negative gain on both variants, -3513 bits at 4 tracks and -18186 at 51, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), which is a fact about the operator and not about the world. cegis_miner refused all four tracks because its precondition is exactly one move event per transition and this world has no mover; correct and unhelpful, and its refusal messages naming 'vanish' and 'recolor' agree with my event vocabulary. zero_space calls its own evidence THIN in its own words -- 9 transitions constraining rank 4 of 686 features, null space of dimension 682 -- and its single global law spans nearly every dynamic cell at once, which is what a 682-dimensional null space produces rather than what a conservation law looks like; notably its cell list includes both (53,62) and (53,63), so even its one law is really the observation that those two cells changed. What I took from the engines is the store arithmetic, dynamic_cells 98 and cells_needing_an_owner 74, and both closed against a reconstruction built without them."
    [probe: pending]
