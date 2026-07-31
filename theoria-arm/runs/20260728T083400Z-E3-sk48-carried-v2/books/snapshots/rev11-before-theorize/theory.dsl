# theory.dsl -- FOURTH DRAFT.
#
# NO NEW TRANSITIONS ARRIVED THIS ROUND. The store is identical to last
# round's: 10 states, 9 transitions, 98 dynamic cells, 74 needing an owner.
# The only thing that fired is the replay divergence at t=0 -- and that
# divergence is the one I pre-registered in writing, to the transition and to
# the cell count. So this draft changes no rule. It records the score, states
# plainly why silence is still the right answer, closes one hole in the
# inexpressibility argument that I had left half-open, and corrects one
# over-claim of my own about the length of the meter bar.
#
# 1. THE PRE-REGISTRATION WAS MET EXACTLY. Last round I wrote: "replay will
#    report 6/9, with the first divergence at transition 0 (ACTION1, 96 cells)
#    and one-cell divergences at transitions 7 and 8, both at (53,62)." Certify
#    returns 6/9, first divergence transition 0, ACTION1, cells_wrong 96. The
#    matched set is forced to be {1,2,3,4,5,6} and the missed set {0,7,8}:
#    transition 1 matches BECAUSE the world returns to frame 0 under key(2)
#    while my silent manual never left it. Responsibility 0 unexplained,
#    unambiguous 0 clashes. Every number I promised, the checker produced.
#
# 2. THE SWAP WITNESS IS NOW MEASURED, NOT RECONSTRUCTED. The divergence
#    report hands me 24 cells of the t1 frame. (30,12) and (31,12) are both
#    colour 5 in frame 0 with above 5, below 5, left 5, right 3 -- identical to
#    every guard this language owns -- and the world turns them into 6 and 0.
#    That is no longer my reconstruction arguing with itself; it is the world
#    saying it. See the_swap_is_provably_inexpressible_here.
#
# 3. THE SWAP HAS A SECOND, HARDER BLOCKER I HAD NOT STATED. 24 of the 96
#    cells are background colour 5 in frame 0. No declared object has colour 5,
#    so no instance exists at those cells, so no `recolored` event can reach
#    them at all. Even a manual willing to pay 96 landmarks and 96 rules could
#    not draw the swap. Inexpressible was an argument about guards; it is also
#    an argument about instances, and the second one admits no workaround short
#    of declaring the background itself an object.
#
# 4. I CORRECT MY OWN ARITHMETIC ON THE BAR. I wrote "62 cells remain". I have
#    only ever been shown row 53 from col 10 rightward: cols 10-61 are colour 2
#    and cols 62-63 are consumed. Cols 0-9 of row 53 are constant and I have
#    never seen them. So 52 cells are measured as unconsumed and up to 62 exist
#    if the bar reaches the left edge. Under the clock reading that is 208 to
#    248 actions, not 248. A range I can defend beats a number I cannot.
#
# 5. A RIVAL METER RULE SCORES THE SAME 6/9 AND I REFUSE IT. Writing the tick
#    as "key(4) on a colour-2 bar cell whose right neighbour is already 3"
#    fires early at t6 instead of late at t8 and also lands 6/9. It is the same
#    score for a strictly stronger claim. I keep the rule whose error is a
#    missing event rather than an invented one.
#
# WHAT IS UNCHANGED AND WHY: the seven rules, the six colour classes, the
# widget anatomy that closes at 74 + 24 = 98, and the refusal to model the
# selector. Silence on key(1)/key(2) is worth six replayed transitions; any
# partial swap rule produces a frame equal to neither manual nor world and
# desynchronises open-loop replay permanently, taking all nine.

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

# The seven rules are BYTE-FOR-BYTE last round's. They produced exactly the
# score I predicted for them, and no observation has arrived since. Changing a
# rule that is meeting its own pre-registration, on no new evidence, is how a
# manual loses transitions it already owns.

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

  theorem the_pre_registration_was_met_to_the_transition_and_to_the_cell "last round I wrote down, before the checker ran, exactly how my manual would fail: 6 of 9 transitions, first divergence at transition 0 under ACTION1 with 96 cells wrong, one-cell divergences at transitions 7 and 8 both at (53,62). Certify returns replay 6/9, first_divergence t=0, arc_action ACTION1, cells_wrong 96, responsibility 0 unexplained, unambiguous 0 clashes. The matched set is forced by open-loop arithmetic to be transitions 1 through 6 and the missed set 0, 7 and 8: transition 1 scores BECAUSE the world's key(2) returns it to frame 0, where my silent manual has been sitting all along. This is the strongest evidence the manual has produced, because it is the only claim it made that could have come back wrong in a way I named in advance. Nothing here licenses a new rule; it licenses keeping the rules I have."
    [depends: replay_is_open_loop_and_silence_on_the_selector_is_worth_six_transitions  probe: passed]

  theorem the_world_has_hidden_state_two_identical_frames_answered_the_same_key_differently "S5, reached by key(7) at t5, and S7, reached by key(3) at t7, are the same frame cell for cell: strip B blanked to colour 4 over rows 38-39 x cols 17-22, (53,63) already colour 3, (53,62) still colour 2, everything else as frame 0. Every cell outside the dynamic box is constant by definition, so there is nowhere else for them to differ. key(4) from S5 produced S6 with no change outside the strip; key(4) from S7 produced S8 with (53,62) 2 -> 3 as well. Same state, same action, two successors. The store corroborates independently: 10 states, 7 distinct, and the only way to get three collisions out of this trace is S2=S0, S6=S4, S7=S5. So the world carries a counter the frame does not show, my guard language has no counters and no memory of the previous action, and constraint 5 forbids two rules that both fire on one instance. I therefore write the tick I can witness once and none of the ticks I cannot, and the cost is the two transitions certify reports."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem a_rival_meter_rule_scores_the_same_six_and_i_keep_the_understated_one "there is a second single-rule meter I could write: key(4) on a colour-2 bar cell whose right neighbour is already colour 3. Traced by hand it misses the tick at transition 3, so I would also have to keep the current rule; together they tick (53,62) early at t6 instead of late at t8, and the matched set becomes 1,2,3,4,7,8 -- also six. Identical score for a strictly stronger claim, since it asserts that every key(4) after the first tick ticks again, which t6 refutes. Between two manuals that replay equally, the one whose error is a missing event is worth more than the one whose error is an invented event, because a missing event stops being wrong the moment the hidden counter is understood and an invented one has to be retracted. I record the rival rather than hide that the choice was mine."
    [depends: the_world_has_hidden_state_two_identical_frames_answered_the_same_key_differently  probe: passed]

  theorem the_meter_is_probably_a_clock_and_not_a_toll "the two ticks landed after global action 4 and after global action 8, consumed right to left, one cell each. Two readings survive nine transitions. CLOCK: the bar loses one cell every four actions whatever they are, so the next tick is at global action 12 and lands on (53,61). TOLL WITH PARITY: the tick follows the first, third, fifth key(4) press, so the next key(4) press is the fourth and does nothing. Both require the hidden counter and neither is expressible here. The separator is three consecutive actions none of which is key(4): the clock says (53,61) turns 3 on the third of them, the parity toll says the bar does not move at all, and my manual predicts no movement, so the probe scores the manual as well as the world. Frame counts cannot substitute -- cumulative frames at the ticks were 8 and 15, no period. This question outranks every refinement of the drawing because it decides whether there is any reason to be frugal."
    [depends: the_world_has_hidden_state_two_identical_frames_answered_the_same_key_differently  probe: pending]

  theorem i_over_claimed_the_length_of_the_bar_and_here_is_the_range "I wrote that 62 cells of the bar remain. I have only ever been shown row 53 from column 10 rightward: cols 10-61 read colour 2, cols 62-63 are consumed. Columns 0-9 of row 53 are outside every frame I have been given and are constant, so they may be bar or may be something else entirely. The defensible statement is that between 52 and 62 cells remain, and under the clock reading that is between 208 and 248 actions. Making a cell of row 53 left of column 10 vary is the only way to settle it, and it is not worth an action of its own; it will settle itself the moment the tick crosses column 10."
    [depends: the_meter_is_probably_a_clock_and_not_a_toll  probe: pending]

  theorem the_meter_cadence_is_inexpressible_in_this_language "a guard reads a cell's colour, its four neighbours' colours, off-board, and the action name. A cadence needs a count of past actions, and there is no count anywhere in the grammar -- not in guards, not in values, not in events. I could fake a parity bit only by recolouring some cell the world does not recolour, which is a guaranteed responsibility or replay failure, so faking it is strictly worse than silence. This is the second thing this world does that the language cannot say; the first is the selector swap. Both are recorded as prose and neither is smuggled into rules."
    [depends: the_world_has_hidden_state_two_identical_frames_answered_the_same_key_differently  probe: passed]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have ever seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Witnesses: frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, the same period-3 run offset by one column; and the divergence report gives all seven of row 32 cols 16-22 as the world drew them at t1 -- 1 2 1 1 2 1 1 -- and every one satisfies the rule, with rows 32 and 38 agreeing because they are six apart and six is divisible by three. So the two strips are not two stored patterns and not one display that follows the selection; they are two windows onto a single diagonal texture, which is why key(4) can restore twelve cells cell for cell. The untested prediction is unchanged: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2, with (33,16) colour 2. Nothing in rules needs it, because each instance already remembers its frame 0 colour, so by constraint 3 this concept currently buys understanding rather than symbols and I say so."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, three times for key(3) and once for key(7), twelve cells every time. (38,16)=1 and (39,16)=2 sit on the widget's right edge, are Pip and Stud instances, and have never changed under any blank; the blanking rules confirm why in their guards, since leftof both is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. I read col 16 as a seed the world keeps visible; the alternative is that it is simply where the 6x6 box ends and the survival is coincidence. Nine transitions do not separate them."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I was shown with two edits: rows 38-39 x cols 17-22 hold the texture rather than colour 4, and (53,63) and (53,62) hold 2 rather than 3. The widget anatomy closes: 22 Casing as a 20-cell ring minus two ports plus a 2x2 core, 12 Cavity as a 4x4 minus that core, 8 Rail and 4 Stud as the unselected bar at cols 13-14, 9 Pip and 5 Stud in the strips and ports, 12 Erased in lane A, 2 Stud in the meter bar, total 74 = cells_needing_an_owner. The 24 remaining dynamic cells are exactly the background cells of the unselected slot's 6x6 footprint, and 74 + 24 = 98 = dynamic_cells. The t1 diff of 96 cells is 36 for panel A plus 36 for panel B plus 12 for lane A's strip rows plus 12 for lane B's, with nothing left over. Responsibility reports 0 unexplained over all 4096 cells."
    [probe: passed]

  theorem replay_is_open_loop_and_silence_on_the_selector_is_worth_six_transitions "the manual is run forward from frame 0 without resync. My manual is a no-op on key(1) and key(2), so it sat at frame 0 through both, the world left at t1 and came back at t2, and every strip transition since has replayed on top of it -- which is why transition 1 counts as a match even though transition 0 is a 96-cell miss. A wrong or partial rule for key(1) would not cost one transition: it would produce a frame equal to neither manual nor world, desynchronise permanently, and cost all nine. That is the numerical argument for silence and certify has now measured both of its terms."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied, so they are board. Colour 3 at cols 13-14 is exactly what an unselected slot shows at its four outer rows, and the unselected slot at rows 30-35 shows 3 3 2 2 3 3 down cols 13-14, so row 29 sits where the last row of a slot at rows 24-29 would sit. The period is now measured rather than inferred: the divergence report gives the world's t1 rows 30, 31 and 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37 and 38 at the same columns read 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1. Eighteen cells, identical, six rows apart. Below, rows 42 onward are uniform background, so rows 36-41 is the bottom slot. I read key(1) as move-selection-up-one-slot and key(2) as move-selection-down-one-slot. The probe is still the cheapest structural test in the game, in two halves: from the bottom slot key(2) should do nothing under the move reading and repaint 96 cells under a two-slot toggle; and from the upper slot key(1) should repaint rows 24-35 if a third slot exists and do nothing if slot A is the top. My manual, being silent, predicts nothing for both, so either press scores it for free."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_arena_is_lanes_and_the_badge_is_row_aligned_with_the_cavity "the arena is colour 4 over cols 17-46, rows 30-41 at least. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 x cols 42-45. Those are precisely the rows a selected slot's 4x4 cavity occupies within its own 6-row band -- the cavity of the selected bottom slot is rows 37-40 within band 36-41, and the badge is rows 31-34 within band 30-35. So the badge is a cavity-shaped, cavity-aligned object at the far right of slot A's lane, and slot B's lane has nothing at cols 42-45. Two readings: the badge is a target the lane's cavity or strip must be made to match, or it is a marker that slot A carries a task and slot B does not. Zero transitions bear on either. Slots above row 29 may carry badges I have never seen, since an unvarying badge is board by definition."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_strip_hides_and_shows_and_no_key_has_been_shown_to_cost_anything "key(3) blanked a shown strip at t3, t7 and t9; key(7) blanked one at t5; key(4) restored a blanked one at t4, t6 and t8, identically every time, so the pattern lives somewhere the frame does not show and blanking does not destroy it. What I wrote two drafts ago -- that key(4) is the metered action and the rest are free -- is refuted by t6, a key(4) press that moved no bar. What is still untested is the same thing as after five transitions: key(3) has never been pressed from a blanked strip and key(4) has never been pressed from a shown one. Until one of those happens, hide-and-show and toggle-and-toggle are indistinguishable. The current state is blanked, so the separator costs exactly one action; I have checked every Pip and Stud instance against the blanking guards in this state and none of them fires, including the two ports, the four bar studs of the unselected slot and the two meter studs, so my manual commits to inert and a restore refutes it."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language can produce them. A guard sees a cell's own colour and its four neighbours' colours and nothing else -- no coordinate, no row band, no distance. The witness is no longer reconstructed: the divergence report contains the world's own t1 values. (30,12) and (31,12) are both colour 5 in frame 0 with above 5, below 5, left 5, right 3, and the world makes them 6 and 0. (32,13) and (32,14) are colour 2 with left and right in the same bar and the world makes them 6, while (30,13) and (30,14) are colour 3 in an identical local neighbourhood and the world also makes them 6, so the classes do not even separate consistently. And (30,16), (31,16), (32,16), (33,16), (34,16) are all colour 5 with above 5, below 5, left 5, right 4 and must become 6, 6, 1, 2, 6 -- four distinct answers to one indistinguishable question, two of them now read off the report directly. Constraint 5 forbids writing rules that both fire. The swap does not go in the manual."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem the_swap_has_a_second_blocker_twenty_four_of_its_cells_have_no_instance_at_all "I had left the inexpressibility argument resting entirely on guards, and that was incomplete. 24 of the 96 cells the swap repaints are colour 5 in frame 0 -- the background cells of the unselected slot's 6x6 footprint. No declared object carries colour 5, so the arm creates no instance there, so no `recolored` event can name them, so those cells cannot be drawn by any rule however many landmarks I buy. The only escape would be to declare the background itself an object, which puts an instance on every colour-5 cell the board cannot explain and makes the manual responsible for arguing about the arena's own filler. This blocker is stronger than the guard blocker because it does not depend on what a guard can see: it is arithmetic about which cells exist as objects. Both blockers point the same way and I record both."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem nesting_would_break_the_ties_and_would_still_fail_the_gain_test "if above(above(?p)) compiles -- the grammar does not list it -- a chain of nested neighbours could count a cell's distance from the panel edge and recover its offset in the period. I decline that route three times over now. A guard form the grammar does not document is a parse risk, and a manual that fails to parse loses all six transitions it currently replays. Distinguishing 96 cells by 96 neighbour chains costs more symbols than the 96 pixels it explains, which is exactly the failure constraint 3 names. And 24 of those cells have no instance to attach a guard to in the first place."
    [depends: the_swap_has_a_second_blocker_twenty_four_of_its_cells_have_no_instance_at_all  probe: pending]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, which is rows 29-54 x cols 10-63. They are therefore somewhere in the 3998 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility is safe; but it is also where any title, target display, score or instruction would live, and it is the most likely home of whatever finishing means. It is the largest thing I do not know, and the only way to see it is to make a cell of it change, which is another argument for pressing the selector past the slots I have already mapped."
    [depends: no_goal_section_on_purpose  probe: pending]

  theorem cascade_length_carries_no_signal_here "t1 through t4 and t6 through t9 each returned 2 frames and t5 returned 1, yet t5 (key(7)) and t7 (key(3)) produced identical 12-cell effects, and t6 (key(4), 2 frames) and t8 (key(4), 2 frames) produced different effects. Frame count tracks neither the magnitude nor the presence nor the identity of change and must not be used as a motion detector. The one thing it may still carry is that ACTION7 is a different key from ACTION3 that happened to agree in this state."
    [probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot's middle rows, a port, four strip cells and two cells of the meter bar -- four unrelated roles. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm is what draws the frame. The gain is measured: six declarations own all 74 cells that need an owner against 74 pixels written out, responsibility reports 0 unexplained, and seven rules over those classes reproduce six of nine transitions. The cost is measured too: no rule can name the strip, so every strip rule carves it out of its class with four negative neighbour guards, and the meter rule needs an off-board test to separate two cells of the same class two columns apart. Those guards are pixel-fitting in a costume; they are correct on every instance of both classes in frame 0, they have survived three blanks and three restores, and they are the price of a colour-first arm."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem instance_anchoring_is_frame_zero_and_the_arm_extends_it_as_cells_vary "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0. Two consequences, both confirmed. A cell constant in frame 0 gets no instance, which is why the slots above row 29 are invisible to this manual, why it cannot draw the selector, and why 24 background cells of the swap are unreachable. And a cell that later varies stops being board and gains one: (53,62) was constant through t7 and owned by nothing, then varied at t8, and cells_needing_an_owner went 73 to 74 with dynamic_cells 97 to 98. stud_population is 11 accordingly, and that new instance is why the meter rule needs the off-board guard: the earlier guard was true of both bar cells and would have ticked them together at t4."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem two_keys_have_never_been_pressed "this world has seen ACTION1, 2, 3, 4 and 7. key(5) and key(6) are unpressed and unknown, and the case for pressing them is strong: t6 showed that a key press can accomplish twelve cells of change and move the bar not at all, so the worst case cost of an experiment is a quarter of one bar cell out of fifty-two or more remaining. If either is a click carrying coordinates, this guard language cannot express it and the finding will be recorded as prose. Pressing them also doubles as two thirds of the clock probe, since neither is key(4)."
    [depends: the_meter_is_probably_a_clock_and_not_a_toll  probe: pending]

  theorem no_goal_section_on_purpose "all ten states returned NOT_FINISHED and nothing in nine transitions indicates what finishing means. The live candidates are that a lane's texture must be brought to agree with the badge at its far end, that every slot in the column must be visited or solved, or that the objective is in the rows I have never been shown. An absent goal compiles to is_goal -> False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level."
    [depends: the_arena_is_lanes_and_the_badge_is_row_aligned_with_the_cavity  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "the proposal stream is unchanged from last round and so is my reading of it. mdl_segmenter returns negative gain on both variants, -3513 bits at 4 tracks and -18186 at 51, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator and not about the world. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition and this world has no mover; correct and unhelpful, and its refusal messages naming vanish and recolor agree with my event vocabulary. zero_space calls its own evidence THIN in its own words -- 9 transitions constraining rank 4 of 686 features, null space of dimension 682 -- and its single global law spans nearly every dynamic cell at once, which is what a 682-dimensional null space produces rather than what a conservation law looks like. What I took from the engines is the store arithmetic, dynamic_cells 98 and cells_needing_an_owner 74, and both closed against a reconstruction built without them."
    [probe: pending]
