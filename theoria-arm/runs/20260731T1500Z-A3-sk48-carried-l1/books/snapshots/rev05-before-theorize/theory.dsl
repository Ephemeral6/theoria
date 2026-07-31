# theory.dsl -- SEVENTH DRAFT.
#
# THE RECORD SHRANK, AND THAT IS THE WHOLE STORY OF THIS ROUND.
# The store now reads 6 states, 5 transitions, steps 6, dynamic_cells 97,
# cells_needing_an_owner 73. The draft I am replacing was written against 14
# states, 13 transitions, dynamic_cells 99, cells_needing_an_owner 75. The six
# states I am now given are cell-for-cell the first six of that longer record
# (RESET, swap up, swap back, blank, restore + one bar cell, blank), and the
# bar in the current frame has exactly one consumed cell instead of three.
# I cannot tell whether the episode was re-run from RESET or the record was
# truncated, and it does not matter for what I am allowed to write: the record
# is five transitions and I may cite nothing else.
#
# WHAT THAT COSTS ME, STATED BEFORE THE PLEASANT PARTS.
#  * key3_marches_the_meter_leftward is DELETED. Its only witness was t11 and
#    there is no t11. It never fires anywhere in this record, so deleting it
#    changes no replay score; keeping it would be a rule with coverage 0/0,
#    which constraint 2 forbids outright.
#  * The period-three extra-frame clock had three ticks and now has ONE. A
#    period and an offset fitted to one point is not a reading, it is a shrug.
#    Deflated accordingly.
#  * The refutation of the toll-on-the-restore-key reading rested on the third
#    tick arriving under ACTION3. That transition is gone, so the refutation is
#    gone with it and the toll reading is ALIVE AGAIN. I re-open it rather than
#    quietly keeping the conclusion I liked.
#  * The confirmation that the checker replays open-loop rested on the 9-vs-10
#    split over thirteen transitions. In THIS record open-loop and resyncing
#    both score 4 of 5, because my only error is at transition 0 and the world
#    returns to frame 0 at transition 1 where my silent manual already sits.
#    The two are indistinguishable here and I move that theorem back to pending.
#  * The 9-of-13 rule-search ledger is deleted, not demoted. It ranked rules
#    against transitions this record does not contain and I cannot re-check a
#    single line of it.
#
# 2. THE SURPRISE THAT FIRED IS THE ONE I PRE-REGISTERED, AND I REFUSE IT
#    AGAIN. replay_mismatch at t=0, ACTION1, 96 cells, first cell (30,11)
#    manual 5 world 6. Two measured blockers, both witnessed inside this very
#    brief: (a) (30,16), (31,16), (32,16), (33,16), (34,16) are all colour 5 in
#    frame 0 with above 5, below 5, left 5, right 4 -- one indistinguishable
#    guard reading -- and the world gives 6, 6, 1, 2, 6; constraint 5 forbids
#    the rule set that would be needed. (b) 24 of the 96 repainted cells are
#    background colour 5 in frame 0, carry no instance, and no recolored event
#    can name them. Silence costs exactly one transition of five. A partial
#    swap rule costs all five by desynchronising the replay.
#
# 3. WHAT THE SHORTER RECORD DID NOT COST. The frame-zero anatomy re-closes on
#    the new numbers without a single free parameter: the same six colour
#    classes give 22+12+8+9+10+12 = 73 = cells_needing_an_owner, and 73 + the
#    same 24 background cells of the swap footprint = 97 = dynamic_cells. The
#    only change is that the meter now contributes one Stud instead of three.
#    Responsibility stayed 0 unexplained of 4096. That is a real check passed,
#    not a coincidence rescued.
#
# 4. THIRTEEN LANDMARKS DELETED. Every one carried the comment
#    "arc-cell: carried, coordinates stripped", which is not the required
#    "arc-cell: (row, col)". Each of them therefore lands at (0,0). No rule in
#    this manual references any of them, so they were thirteen declarations
#    buying nothing and thirteen chances to drag a rule to the origin.
#
# 5. WHAT IS SHARP NOW. The manual says the bar NEVER MOVES AGAIN: the seed
#    rule needs a colour-2 Stud whose right neighbour is off-board, and after
#    t4 there is none. That is a deliberate under-claim and it will be wrong at
#    the next tick, whenever it comes. It is also the cleanest separator I
#    have: from the current blanked state, key(4) under my manual repaints
#    twelve strip cells and leaves the bar alone, while under the toll reading
#    it repaints thirteen. One press decides it.

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
  Casing [segment: colour_class_6 ev: t0-t5 compress: 22]
  Cavity [segment: colour_class_0 ev: t0-t5 compress: 12]
  Rail [segment: colour_class_3 ev: t0-t5 compress: 8]
  Pip [segment: colour_class_1 ev: t0-t5 compress: 9]
  Stud [segment: colour_class_2 ev: t0-t5 compress: 10]
  Erased [segment: colour_class_4 ev: t0-t5 compress: 12]

events:
  event recolored(o, c)

# Seven rules. Six of them are the blank/restore pair for the two keys that
# blank and the one key that restores, and their coverage is now one witness
# each instead of five, because there is one witness each in this record. The
# seventh is the meter seed, which fires once and then can never fire again.
# The march rule that used to sit here is deleted: zero witnesses in this
# record, and a rule with no witness is not a rule.
#
# The four negative neighbour guards on the blank rules are what carves the
# twelve strip cells out of their colour classes: leftof-is-cavity excludes the
# two port cells (38,16) and (39,16); leftof-is-background and
# rightof-is-background exclude the four bar Studs at rows 32-33 cols 13-14;
# above-is-background excludes the meter Stud at (53,63), which is exactly why
# the t3 diff is twelve cells and not thirteen. Those guards are pixel-fitting
# in a costume and I say so in colour_classes_are_not_the_worlds_objects.

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

  rule key4_advances_the_meter_once forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall and colored(below(?p), 4) then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 10 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 73 [status: proven]

  theorem the_record_now_holds_five_transitions_and_i_may_cite_nothing_else "the store reads 6 states and 5 transitions where my previous draft cited 14 and 13. The six states I am given are cell for cell the first six of that longer record, and the bar has one consumed cell where it had three. I cannot tell a re-run from a truncation and it changes nothing about what I may write. Four consequences, each paid: the march rule is deleted for want of a witness; the three-tick clock is down to one tick; the refutation of the toll-on-the-restore-key reading is withdrawn because it rested on a transition that is gone; and the 9-of-13 rule ledger is deleted rather than demoted, since not one of its lines can be re-checked here. What survives untouched is everything whose witness sits inside this brief: the frame-zero anatomy, the two swap blockers, the diagonal texture, and the six-row panel period, all of which the divergence report re-witnesses. A manual that loses evidence should get smaller, and this one did."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and (53,63) holds 2 rather than 3. The anatomy closes cell by cell on the new totals: 22 Casing as the 20-cell perimeter of rows 36-41 by cols 11-16 minus the two ports plus the 2x2 core at rows 38-39 cols 13-14; 12 Cavity as the 4x4 at rows 37-40 cols 12-15 minus that core; 8 Rail as the unselected slot bar at rows 30-31 and 34-35 by cols 13-14; 4 Stud as the same bar middle at rows 32-33; 8 Pip and 4 Stud in the strip; 1 Pip and 1 Stud in the two ports at (38,16) and (39,16); 12 Erased as lane A strip at rows 32-33 by cols 17-22; 1 Stud in the meter at (53,63). Totals 22+12+8+9+10+12 = 73 = cells_needing_an_owner. The 24 remaining dynamic cells are exactly the background cells of the unselected slot footprint, cols 11, 12, 15, 16 over rows 30-35, and 73+24 = 97 = dynamic_cells. The one difference from last draft is the meter contributing one Stud instead of three, and it is the only difference the shorter record demanded."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_the_arm_extends_it_as_cells_vary "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0. A cell constant across the whole record gets no instance, which is why the slots above row 29 are invisible to this manual and why 24 background cells of the swap are unreachable. A cell that varies gains one, and the meter is the clean demonstration read in both directions: with three bar cells consumed the store said 75 owners and 99 dynamic, with one consumed it says 73 and 97, and my declarations move by exactly the same two. This also fixes what the meter rules can reach -- (53,62) carries no instance in this record, so no rule of mine can ever repaint it, and that is a fact about the arm rather than about the world."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language can produce them. A guard sees a cell own colour and its four neighbour colours and nothing else -- no coordinate, no row band, no distance. The witness is measured inside this brief, not remembered: (30,16), (31,16), (32,16), (33,16) and (34,16) are all colour 5 in frame 0 with above 5, below 5, left 5, right 4, and the divergence report has the world make them 6, 6, 1, 2, 6 -- four distinct answers to one indistinguishable question. A second pair from the same report: (30,13) is colour 3 and becomes 6 while (32,13) is colour 2 in an equally uniform bar neighbourhood and also becomes 6, so colour does not decide it either. Constraint 5 forbids rules that both fire, so the swap does not go in the manual and the replay_mismatch at transition 0 is a cost I accept rather than a defect I can repair."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem the_swap_has_a_second_blocker_twenty_four_of_its_cells_have_no_instance "24 of the 96 cells the swap repaints are colour 5 in frame 0 -- the background cells of the unselected slot footprint at cols 11, 12, 15, 16 over rows 30 to 35, and the divergence report shows the world painting (30,11), (30,12), (30,15), (30,16), (31,11), (31,16), (32,11), (32,12), (32,15) among them. No declared object carries colour 5, so no instance exists there, so no recolored event can name them, and this blocker does not depend on what a guard can see. The only escape is declaring the background itself an object, which puts an instance on every unexplained colour-5 cell in a 4096-cell frame. Both blockers point the same way and they are independent, which is why I refuse this surprise twice with a clear conscience."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem silence_on_the_selector_costs_one_transition_of_five "my manual is silent on key(1) and key(2), so it draws frame 0 at transition 0 where the world draws the swapped panel: one transition lost, the one certify reports. Transition 1 then counts as a match because ACTION2 returns the world to frame 0 while my silent manual never left it, and transitions 2, 3 and 4 match because manual and world are back in step. That is 4 of 5, and it is the score certify returned. A partial or wrong swap rule would produce a frame equal to neither manual nor world at transition 0, would not be undone at transition 1, and would lose all five. The arithmetic is harsher than it was over thirteen transitions -- 20 percent of the record instead of 8 -- and it still comes out the same way."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem i_withdraw_the_claim_that_replay_is_confirmed_open_loop "I confirmed open-loop replay last round by pre-registering that a resyncing checker would return 10 of 13 and getting 9. That separation lived entirely in transitions 5 to 12, which this record does not contain. Here my only error is at transition 0 and the world hands the frame back at transition 1, so an open-loop checker and a resyncing checker both score 4 of 5 and nothing in this brief distinguishes them. I keep reading my coverage numbers as open-loop because that is the conservative reading and because it was measured once, but the status is pending, not passed. The separator is any transition on which my manual is wrong and the world does not immediately return to where my manual sits -- which is precisely what the next tick of the bar will provide, since my manual now says the bar never moves again."
    [depends: silence_on_the_selector_costs_one_transition_of_five  probe: pending]

  theorem the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified "row 53 reads colour 2 from column 10 to column 62 and colour 3 at column 63, and the whole of my evidence about how it moves is one transition: at t4 an ACTION4 press turned (53,63) from 2 to 3. One tick cannot identify a cadence. All four readings I have ever entertained are alive on this record -- a toll on the restore key, a toll on every key, a period in commands, a period in returned extra frames -- and I have no way to rank them. So the manual carries the seed rule, which fits the one thing about that tick I can express, that the cell with no right neighbour went first, and carries nothing about what happens next. The consequence is a deliberate under-claim: after t4 there is no colour-2 Stud whose right neighbour is off-board, so my manual says the bar never moves again and will be wrong at the next tick. I prefer to be wrong once, visibly, at a moment I have named, over inventing a cadence with a one-point fit."
    [depends: instance_anchoring_is_frame_zero_and_the_arm_extends_it_as_cells_vary  probe: passed]

  theorem the_seed_rule_is_a_one_shot_and_here_is_what_it_is_worth "key4_advances_the_meter_once has coverage 1/1 and by constraint 3 that looks like a rule spent on a single pixel. Its defence is smaller than it used to be and I state it at its true size: without it the current frame cannot be drawn at all, because (53,63) is colour 3 in every state from t4 onward and only this rule paints it. So it buys the last two transitions of the record rather than the three I once claimed for it. What it does not buy is understanding -- it is silent on why that tick fell on that press, and its guard rightof-is-wall makes it structurally unrepeatable, which is an honest way of saying that it explains a boundary and not a mechanism."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: passed]

  theorem i_deleted_the_march_rule_and_i_expect_to_regret_it_if_the_long_record_returns "the previous draft carried a rule marching the bar leftward on key(3), justified by a hand ledger scoring it 9 of 13 against 6 for silence. Every transition in that ledger except the first six is absent here, the rule fires nowhere in this record, and a rule with coverage 0/0 is exactly what constraint 2 forbids. So it is deleted, and my commitment flips: where the previous draft said the next key(3) press consumes a bar cell, this one says it does not. That is not a change of mind about the world, it is a change in what I am allowed to assert, and I flag it as the single most likely place this draft is wrong. If a longer record returns and the bar has moved on key(3) presses again, the rule comes straight back with its witnesses."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_extra_frame_clock_is_down_to_one_point "the reading was that a command advances a hidden clock by its frame count minus one and the bar loses a cell every third advance, and it was fitted to three ticks. This record has one tick. The count at the tick is four: t1, t2, t3, t4 each returned two frames, t5 returned one and did not advance it. Four advances and one tick determine neither a period nor an offset, so this is a shape without parameters now. It still makes the same qualitative prediction that ACTION7 is cheaper than the other keys, since it is the one command in six that returned a single frame, and that prediction is cheap to test by pressing ACTION7 again and reading the frame count alone. I record the clock here so that when ticks two and three arrive the fit can be re-made against the same numbers rather than re-invented."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_toll_on_the_restore_key_reading_is_alive_again "for two drafts I treated the reading -- one bar cell per key(4) press -- as refuted, on the strength of a tick that arrived under ACTION3 at t11. There is no t11 here. In this record ACTION4 was pressed exactly once and the bar moved exactly once, which is the toll reading fitting perfectly with one point. My manual does not implement it, because implementing it means guarding the next bar cell (53,62), which carries no instance and cannot be repainted by any rule of mine. So the reading is untestable by replay and testable in one press: from the current blanked state, key(4) restores twelve strip cells under my manual and thirteen cells including (53,62) under the toll reading. That is the cheapest open question in the game right now."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem i_do_not_know_which_way_the_bar_runs "one cell has gone from 2 to 3 at the right end of row 53. That is equally a resource being spent and a progress meter being filled, and colour 3 is also the colour an unselected slot shows on its rails, which argues weakly that 3 is a resting or completed state rather than a consumed one. Nothing in five transitions separates them, and they invert the sign of every ranking decision: under one reading a probe costs part of a budget, under the other it earns progress. Until something separates them the playbook may not rank on bar movement in either direction. The separator is cheap and will arrive on its own -- either the bar reaching column 10 ends the level, or NOT_FINISHED survives it."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_bar_is_between_fifty_three_and_sixty_three_cells_long "row 53 reads colour 2 over columns 10 to 62 and colour 3 at 63. I have never been shown columns 0 to 9 of that row, so 53 cells are measured unconverted and up to 63 exist if the bar reaches the left edge. Whatever the cadence turns out to be, the magnitude is what matters for ranking and it is safe in both directions: the budget is large compared with six actions, so probing is cheap now and will not stay cheap. I have deliberately stopped calling it a countdown."
    [depends: i_do_not_know_which_way_the_bar_runs  probe: pending]

  theorem the_strip_hides_and_shows_and_the_separator_is_still_one_action_away "key(3) blanked a shown strip at t3, key(7) blanked one at t5, key(4) restored a blanked one at t4, twelve cells and cell for cell identical each time, so the pattern lives somewhere the frame does not show. Both blank presses were made from a shown strip and the single restore press from a blanked one, so hide-and-show and toggle-and-toggle remain indistinguishable after five transitions exactly as they were after thirteen. The state now is blanked, and my manual commits to inert for a repeat of either blanking key: every strip cell is colour 4, so no blanking guard can fire, and no meter rule of mine can fire either. A restore of the strip under a blanking key refutes hide-and-show outright; nothing happening confirms it and also tells me what a null command does to the frame count."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_restore_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "key4_restores_the_strip_pips and _studs guard on colour 4 alone. That is correct on the one restore observed, because the press was made from a state where slot B was selected and the only colour-4 Pip and Stud instances in existence were the twelve blanked cells of lane B. It would be wrong the moment slot A is selected: lane A strip cells become texture while lane B strip cells become arena fill of colour 4, and a key(4) would then repaint an unselected lane. My manual never reaches that state, because it is silent on the selector, so this costs zero transitions today and certify cannot see it. It is written here because a searcher planning through a selector move would be misled by a rule that scores 12 of 12. The fix needs a guard that reads which slot is selected, and selection is exactly what the guard language cannot see."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have ever seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Witnesses inside this brief: frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, the same period-3 run offset by one column, and the divergence report gives all seven of lane A row 32 cols 16-22 as the world drew them at t1 -- 1 2 1 1 2 1 1 -- with rows 32 and 38 agreeing because they are six apart and 6 is divisible by 3. The two port cells fit the same formula, which is a small unforced success. So the two strips are two windows onto one diagonal texture, which is why a restore can rebuild twelve cells exactly. Untested prediction: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2. No rule needs this, since each instance already remembers its frame 0 colour, so by constraint 3 the concept buys understanding rather than symbols and I say so rather than smuggling it into the word table."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, twice now, twelve cells both times. (38,16)=1 and (39,16)=2 sit on the widget right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since leftof both is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The rival explanation is that col 16 is simply where the 6x6 widget ends and the survival is coincidence; two blanks do not separate them and neither did six."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied, so they are board. Colour 3 at cols 13-14 is what an unselected slot shows at its four outer rows, and the unselected slot at rows 30-35 shows 3 3 2 2 3 3 down those columns, so row 29 sits where the last row of a slot at rows 24-29 would sit. The period is measured inside this brief: the divergence report gives the world t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at the same columns read identically -- eighteen cells, six rows apart. Rows 42 onward are uniform background, so rows 36-41 is the bottom slot. I read key(1) as move selection up one slot and key(2) as down one. The probe has two halves and my manual is silent on both, so either press scores it for free: from the bottom slot the down key does nothing under the move reading and repaints 96 cells under a two-slot toggle, and from the upper slot the up key repaints rows 24-35 if a third slot exists."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_arena_is_lanes_and_the_badge_is_row_aligned_with_the_cavity "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47, and I have re-counted that against the current frame rather than assuming it. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45. Those are exactly the rows a selected slot 4x4 cavity occupies within its own six-row band -- the selected bottom slot cavity is rows 37-40 within band 36-41, and the badge is rows 31-34 within band 30-35. So the badge is a cavity-shaped, cavity-aligned object at the far right of the lane belonging to the slot at rows 30-35, and the bottom slot lane has nothing at cols 42-45. Either it is a target a lane must be made to match, or it marks which slot carries a task. Zero transitions bear on either, and slots above row 29 may carry badges I have never seen, since an unvarying badge is board by definition."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_meter_cadence_is_inexpressible_and_i_checked_for_a_latch "a guard reads a cell colour, its four neighbour colours, off-board, and the action name. A cadence needs a count and there is no count in the grammar. Before settling for silence I re-checked the one loophole: an object whose declared colour equals the background renders the same whether present or vanished, so present could in principle be an invisible bit. It cannot be used. The value grammar exposes only color as a field, so no guard can read present; and an object declared with arc-colour 5 would be instantiated on every background cell the board cannot explain, which is the 24 cells of the swap footprint, none of them where a latch would be wanted. So the cadence stays prose, and with the march rule gone the manual now carries no proxy for it at all, which is the smaller and more honest of the two failures available."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: passed]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot bar, a port, four strip cells and the meter cell -- four unrelated roles. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 73 cells that need an owner against 73 pixels written out, with 0 unexplained confirmed again this round. The cost is measured too: no rule can name the strip, so every blanking rule carves it out of its class with four negative neighbour guards, and the meter rule needs an off-board test to separate one Stud from the other nine. Those guards are pixel-fitting in a costume, they are correct on every instance in frame 0, and they are the price of a colour-first arm."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem thirteen_landmarks_deleted_because_none_of_them_had_coordinates "the previous draft declared thirteen landmarks each carrying the comment arc-cell colon carried, coordinates stripped, which is not the arc-cell (row, col) form the arm requires. Every one of them therefore resolves to (0,0). No rule in that draft or this one references a single landmark, so they bought nothing and risked dragging a future rule to the origin. They are gone. If I ever need a named cell -- the likeliest candidate is the next bar cell (53,62) once it varies and gains an instance -- I will declare exactly that one, with its coordinates in the comment where the grammar demands them."
    [probe: passed]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, which is rows 29-54 by cols 10-63. They are somewhere in the 3999 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is also where a title, target, score or instruction would live, and the most likely home of whatever finishing means. It is the largest thing I do not know, and it is also where the answer to i_do_not_know_which_way_the_bar_runs most plausibly sits."
    [depends: no_goal_section_on_purpose  probe: pending]

  theorem two_keys_have_never_been_pressed "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not. The case for pressing them is unchanged and the budget argument is unchanged in magnitude even though its sign is unknown: the bar is 53 cells or more from its end and six actions have been spent. If either key is a click carrying coordinates, this guard language cannot express it and the finding will be recorded as prose rather than as a rule. Each press also reads its own returned frame count, which is the only handle I have left on the clock."
    [depends: the_extra_frame_clock_is_down_to_one_point  probe: pending]

  theorem no_goal_section_on_purpose "all six states returned NOT_FINISHED and nothing in five transitions indicates what finishing means. The live candidates are that a lane texture must be brought to agree with the badge at its far end, that every slot in the column must be visited or solved, or that the objective lives in the rows I have never been shown. An absent goal compiles to is_goal implies False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. I will not write a goal on the strength of a badge I have never interacted with."
    [depends: i_do_not_know_which_way_the_bar_runs  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "I re-read the stream against the new, shorter numbers rather than assuming it repeated. mdl_segmenter returns negative gain on both variants, -4037 bits at 4 tracks and -10409 at 33, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator and not the world; its event tally of 4 recolors, 2 appears and 2 vanishes is however consistent with my reading that this world only ever recolours and that the appear/vanish pair is the swap seen as one blob. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition, and its own verdict says the world does not narrate as one mover, which agrees with my event vocabulary of recolored alone. zero_space calls its own evidence THIN in its own words -- 5 transitions constraining rank 3 of 679 features, null space of dimension 676 -- and its single global law spans 97 dynamic cells at once, which is what a 676-dimensional null space produces rather than what a conservation law looks like. What I took from the engines is the store arithmetic, dynamic_cells 97 and cells_needing_an_owner 73, and both closed against a reconstruction I built without them."
    [probe: pending]

  theorem what_this_draft_pre_registers "certify should return replay 4 of 5, first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) with manual 5 and world 6; responsibility 0 unexplained of 4096; unambiguous 0 clashes. That is the same score the previous draft got, because deleting the march rule removes a rule that never fired in this record, so this prediction tests the checker not at all and I say so instead of dressing it up. The informative pre-registrations are about the world and there are three, each decided by one press from the current blanked state. key(3) or key(7): my manual says the frame does not change at all, which refutes toggle-and-toggle if it holds and refutes my manual if the strip comes back. key(4): my manual says exactly twelve cells change and the bar does not move, while the toll reading says thirteen. ACTION7 again: my manual says nothing about frame count, and a second single-frame return would make ACTION7 the only key that does not advance the world clock."
    [depends: the_record_now_holds_five_transitions_and_i_may_cite_nothing_else  probe: pending]
