# theory.dsl -- EIGHTH DRAFT.
#
# 0. NOTHING NEW CAME IN. The store reads the same 6 states and 5 transitions
#    as the draft I am replacing: same actions, same dynamic_cells 97, same
#    cells_needing_an_owner 73, same current frame. No press was made between
#    drafts. So this round cannot be about new evidence, and any change I make
#    has to be paid for out of re-reading what I already had.
#
# 1. THE PRE-REGISTRATION WAS MET, CELL FOR CELL. Last draft predicted certify
#    would return replay 4/5, first divergence at transition 0 under ACTION1,
#    96 cells wrong, first cell (30,11) with manual 5 and world 6,
#    responsibility 0 unexplained of 4096, 0 clashes. Certify returned exactly
#    that, down to the cell. That is the one thing this round confirmed, and it
#    confirms my model of the CHECKER, not my model of the world. I say so.
#
# 2. THE SURPRISE IS THE SAME SURPRISE AND I REFUSE IT A THIRD TIME -- BUT ON
#    DIFFERENT GROUNDS, BECAUSE ONE OF MY TWO BLOCKERS TURNED OUT TO BE FALSE.
#    I had been saying the swap is blocked because (a) guards cannot tell the
#    96 cells apart and (b) 24 of them are background-coloured and carry no
#    instance. Blocker (b) is WRONG and I withdraw it: an object declared with
#    arc-colour 5 and arc-instances: all would be placed on exactly the colour-5
#    cells the board cannot explain, and those are exactly those 24 cells,
#    because 97 dynamic minus 73 owned is 24. The escape I said was ruinous is
#    in fact cheap and precise. It just does not help, for reasons (a) and (c).
#    In its place I put a blocker I had not written down before:
#    (c) MDL. Even granting every position-reading device I can imagine, the
#    swap comes out as roughly one rule per repainted cell, which is longer
#    than the 96 pixels it explains. Constraint 3 kills it independently of
#    constraint 5. Two blockers, both stated as measurements, both new-ish.
#
# 3. THE GUARDS GOT SHORTER AND THE MANUAL GOT MORE HONEST. The blanking rules
#    carried four negative neighbour guards each. Re-checking every one of the
#    9 Pip and 10 Stud instances against the frame I can reconstruct, three of
#    the four do nothing on the Pip rules and one of the four does nothing on
#    the Stud rules. Blanking now costs 1 guard for pips and 3 for studs
#    instead of 4 and 4, and the meter seed loses its redundant below-is-4 test.
#    Eight guard atoms deleted, same firing set on every instance in every state
#    my manual can reach, predicted replay unchanged at 4/5. This is the whole
#    of what a round with no new evidence is allowed to buy: a shorter manual
#    that says the same thing.
#
# 4. WHAT I CHECKED AND DID NOT TAKE. Declaring the background as an object
#    (rejected: zero gain, it explains no pixel that the board does not already
#    draw correctly). Declaring a second colour-2 type to reach the next bar
#    cell (rejected: the arm finds objects by colour and nothing else, so it
#    would duplicate the ten Studs). Nesting cell expressions -- above(above(?p))
#    -- which would give guards a two-cell reach and is the only thing that
#    could ever separate (32,16) from (33,16): the grammar calls its cell list
#    exhaustive and does not say whether the argument may itself be a cell
#    expression, so I will not gamble a parse error on it; it is written as a
#    probe instead.
#
# 5. WHAT IS STILL SHARP. The manual says the bar NEVER MOVES AGAIN, and it
#    says a repeat of either blanking key from the current blanked state
#    changes NOTHING. Both are deliberate under-claims and both are decided by
#    one press.

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

# Seven rules, and every guard atom in them is now load-bearing. I re-derived
# each one against all 19 Pip and Stud instances rather than inheriting it:
#
#  Pip blanking needs ONE guard. Only the port pip (38,16) must be spared, and
#  its left neighbour (38,15) is a colour-0 cavity cell. The three other guards
#  the previous draft carried -- left-is-5, right-is-5, above-is-5 -- exclude no
#  Pip whatsoever, because no Pip has a background neighbour on any of those
#  sides. They were decoration and they are gone.
#
#  Stud blanking needs THREE. The port stud (39,16) is spared by the same
#  left-is-cavity test. The four bar studs at rows 32-33 cols 13-14 form a 2x2
#  of colour 2, so each has a colour-2 cell to its left or its right; the meter
#  stud (53,63) has the colour-2 bar to its left. One pair of guards --
#  not-left-is-2 and not-right-is-2 -- therefore spares all five at once, where
#  the previous draft spent three guards doing it. The four strip studs are
#  flanked by colour-1 pips or by arena fill on both sides, so all four fire.
#
#  The meter seed needs ONE positional guard. Exactly one Stud in existence has
#  no right neighbour, so rightof-is-wall alone picks it out; the below-is-4
#  test the previous draft added was true of that cell and of nothing that
#  needed excluding.

rules:
  rule key3_blanks_the_strip_pips forall ?p in Pip [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key3_blanks_the_strip_studs forall ?p in Stud [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key7_blanks_the_strip_pips forall ?p in Pip [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and not colored(leftof(?p), 0) then recolored(?p, 4)

  rule key7_blanks_the_strip_studs forall ?p in Stud [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and not colored(leftof(?p), 0) and not colored(leftof(?p), 2) and not colored(rightof(?p), 2) then recolored(?p, 4)

  rule key4_restores_the_strip_pips forall ?p in Pip [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) then recolored(?p, 1)

  rule key4_restores_the_strip_studs forall ?p in Stud [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) then recolored(?p, 2)

  rule key4_advances_the_meter_once forall ?p in Stud [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

laws:
  invariant casing_population count(Casing) = 22 [status: derived]
  invariant cavity_population count(Cavity) = 12 [status: derived]
  invariant rail_population count(Rail) = 8 [status: derived]
  invariant pip_population count(Pip) = 9 [status: derived]
  invariant stud_population count(Stud) = 10 [status: derived]
  invariant erased_population count(Erased) = 12 [status: derived]
  invariant every_dynamic_cell_has_an_owner count(Casing) + count(Cavity) + count(Rail) + count(Pip) + count(Stud) + count(Erased) = 73 [status: proven]

  theorem the_last_drafts_pre_registration_was_met_exactly_and_no_new_evidence_arrived "the previous draft predicted replay 4 of 5, first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6, responsibility 0 unexplained of 4096, and 0 clashes over 18 adjudicated pairs. Certify returned all six numbers. The store is byte for byte what it was: 6 states, 5 transitions, 97 dynamic cells, 73 needing an owner, same current frame with one consumed bar cell. So no press was taken between drafts and this round has no new observation in it. What the match confirms is my model of the checker -- that it replays from frame 0, that silence draws the previous frame forward, that responsibility is scored on frame 0 -- and not one thing about the world. A draft written against an unchanged record may only get shorter or better argued, and I have tried to do both rather than manufacture a discovery."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem frame_zero_is_reconstructed_exactly "frame 0 equals the frame I am shown with two edits: rows 38-39 by cols 17-22 hold the texture rather than colour 4, and (53,63) holds 2 rather than 3. The anatomy closes cell by cell: 22 Casing as the 20-cell perimeter of rows 36-41 by cols 11-16 minus the two ports plus the 2x2 core at rows 38-39 cols 13-14; 12 Cavity as the 4x4 at rows 37-40 cols 12-15 minus that core; 8 Rail as the unselected slot bar at rows 30-31 and 34-35 by cols 13-14; 4 Stud as the same bar middle at rows 32-33; 8 Pip and 4 Stud in the strip; 1 Pip at (38,16) and 1 Stud at (39,16) in the ports; 12 Erased as the lane A strip at rows 32-33 by cols 17-22; 1 Stud in the meter at (53,63). Totals 22+12+8+9+10+12 = 73 = cells_needing_an_owner. The 24 remaining dynamic cells are exactly the background cells of the unselected slot footprint, cols 11, 12, 15, 16 over rows 30-35, and 73+24 = 97 = dynamic_cells. Responsibility came back 0 unexplained again, so this reconstruction has now been checked twice against the arm."
    [probe: passed]

  theorem instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances "instances are the cells of a declared colour that the board cannot explain, coloured as they are in frame 0. A cell constant across the whole record gets no instance, which is why the slots above row 29 are invisible to this manual and why the next bar cell (53,62) is unreachable: it has been colour 2 in all six states, so it is board, so no rule of mine can ever repaint it however I guard. A cell that varies gains one, and the meter demonstrated the arithmetic in both directions across the record change -- three bar cells consumed gave 75 owners and 99 dynamic, one consumed gives 73 and 97, and my declarations move by exactly the same two. This is a fact about the arm, not about the world, and it is the single largest constraint on what this manual can say."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem the_swap_is_provably_inexpressible_here "the selector move relabels 96 cells and no set of rules in this language can produce them. A guard sees a cell's own colour, its four immediate neighbour colours, off-board, and the action name -- no coordinate, no row band, no distance. The witness is measured inside this brief: (30,16), (31,16), (32,16), (33,16) and (34,16) are all colour 5 in frame 0 with above 5, below 5, left 5, right 4 -- one indistinguishable guard reading -- and the divergence report has the world make them 6, 6, 1, 2, 6. Three distinct answers to one question. A second pair from the same report kills colour as a discriminator: (30,13) is colour 3 and becomes 6 while (32,13) is colour 2 in an equally uniform bar neighbourhood and also becomes 6. Constraint 5 forbids two rules that both fire, so the swap does not go in the manual, and the replay_mismatch at transition 0 is a cost I accept rather than a defect I can repair."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: passed]

  theorem i_withdraw_the_no_instance_blocker_because_a_colour_five_object_would_own_those_cells_exactly "for two drafts I gave a second reason the swap cannot be written: 24 of its 96 cells are background colour 5, carry no instance, and no recolored event can name them, and I called the only escape ruinous on the grounds that a colour-5 object would be instantiated on every background cell of a 4096-cell frame. That was wrong and the arithmetic in my own manual says so. The arm instantiates the cells of a declared colour THAT THE BOARD CANNOT EXPLAIN, and the colour-5 cells the board cannot explain number exactly 97 minus 73 = 24 -- precisely cols 11, 12, 15, 16 over rows 30-35, precisely the swap footprint, and not one cell more. So the escape is cheap and surgical, and I am withdrawing the blocker rather than keeping a conclusion whose reason has collapsed. I still do not declare the object, because it would explain no pixel the board does not already draw correctly and would enable no rule I can write, which is constraint 3 refusing it on its own terms. If a device ever appears that lets a guard read position, this declaration is the first thing to add."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_swap_also_fails_the_compression_test_and_that_blocker_needs_no_grammar_argument "suppose every expressibility obstacle vanished and I could read a cell's position freely. The swap would still not belong in the manual. It repaints 96 cells whose new colours follow no local law -- the widget is teleported six rows, which no event in the vocabulary does; moved is one cell, jumped-over is two, jumped-to-a-landmark needs a landmark and a rule per instance. The shortest form I can construct is on the order of one landmark and one rule per repainted cell, for both directions, which is longer than writing out the 96 pixels it explains. Constraint 3 refuses it independently of constraint 5, and unlike the guard argument this one does not depend on any reading of the grammar. Two independent refusals, and this is the reason I expect never to write the swap in this language rather than merely not to have written it yet."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem silence_on_the_selector_costs_one_transition_of_five "my manual is silent on key(1) and key(2), so it draws frame 0 at transition 0 where the world draws the swapped panel: one transition lost, the one certify reports. Transition 1 counts as a match because ACTION2 returns the world to frame 0 while my silent manual never left it, and transitions 2, 3 and 4 match because manual and world are back in step. That is 4 of 5, which is the score certify returned twice now. A partial or wrong swap rule would produce a frame equal to neither manual nor world at transition 0, would not be undone at transition 1, and would lose all five. Twenty percent of the record is a harsher price than the eight percent the longer record charged, and it still comes out the same way."
    [depends: the_swap_is_provably_inexpressible_here  probe: passed]

  theorem the_blanking_guards_shrank_from_sixteen_atoms_to_eight_with_no_change_of_firing_set "the four blanking rules carried four negative neighbour guards each. I re-checked all 9 Pip and 10 Stud instances. Among Pips, only the port pip (38,16) must be spared and its left neighbour is a colour-0 cavity cell; no Pip anywhere has a background cell to its left, right or above, so three of the four guards excluded nothing and are deleted. Among Studs, the four bar studs form a 2x2 of colour 2 so each has a colour-2 horizontal neighbour, and the meter stud has the colour-2 bar to its left, so not-left-is-2 with not-right-is-2 spares all five where three separate guards did it before; the port stud still needs the cavity test. The meter seed loses its below-is-4 atom because exactly one Stud in existence has no right neighbour. Eight atoms deleted. The firing set is unchanged on every instance in every state this manual can reach -- 8 pips and 4 studs blank, 12 restore, 1 meter cell advances -- so the predicted replay stays 4 of 5 and this is a pure shortening."
    [depends: frame_zero_is_reconstructed_exactly  probe: passed]

  theorem i_withdraw_the_claim_that_replay_is_confirmed_open_loop "I once confirmed open-loop replay by pre-registering that a resyncing checker would return 10 of 13 and getting 9. That separation lived in transitions this record does not contain. Here my only error is at transition 0 and the world hands the frame back at transition 1, so open-loop and resyncing both score 4 of 5 and nothing distinguishes them. I keep reading my coverage as open-loop because that is the conservative reading, but the status is pending. The separator is any transition on which my manual is wrong and the world does not immediately return to where my manual sits -- which the next tick of the bar will supply, since my manual now says the bar never moves again."
    [depends: silence_on_the_selector_costs_one_transition_of_five  probe: pending]

  theorem the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified "row 53 reads colour 2 from column 10 to column 62 and colour 3 at column 63, and the whole of my evidence about how it moves is one transition: at t4 an ACTION4 press turned (53,63) from 2 to 3. One tick cannot identify a cadence. All four readings remain alive -- a toll on the restore key, a toll on every key, a period in commands, a period in returned extra frames -- and I have no way to rank them. So the manual carries the seed rule, which fits the only expressible thing about that tick, that the cell with no right neighbour went first, and carries nothing about what happens next. The consequence is a deliberate under-claim: after t4 there is no colour-2 Stud whose right neighbour is off-board, so my manual says the bar never moves again and will be wrong at the next tick. I declare no landmark for (53,62) either, because a landmark is a cell and every event in the vocabulary takes an object."
    [depends: instance_anchoring_is_frame_zero_and_only_varying_cells_get_instances  probe: passed]

  theorem the_seed_rule_is_a_one_shot_and_here_is_what_it_is_worth "key4_advances_the_meter_once has coverage 1/1 and by constraint 3 that looks like a rule spent on a single pixel. Its defence, at its true size: without it the current frame cannot be drawn at all, because (53,63) is colour 3 in every state from t4 onward and only this rule paints it. So it buys the last two transitions of the record. What it does not buy is understanding -- it is silent on why that tick fell on that press, and its rightof-is-wall guard makes it structurally unrepeatable, which is an honest way of saying it explains a boundary and not a mechanism."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: passed]

  theorem i_deleted_the_march_rule_and_i_flag_it_as_the_likeliest_error_in_this_draft "an earlier draft carried a rule marching the bar leftward on key(3), justified by a ledger scoring it 9 of 13 against 6 for silence over a record that no longer exists. It fires nowhere here, and a rule with coverage 0/0 is what constraint 2 forbids. So my commitment is flipped: the next key(3) press does not consume a bar cell. That is a change in what I am allowed to assert rather than a change of mind, and even if I wanted it back the arm forbids it, since (53,62) is board and carries no instance. If a longer record returns and the bar moves on key(3) presses, the rule comes back with its witnesses and with a colour-5 or landmark device to reach the cell."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_extra_frame_clock_is_down_to_one_point "the reading was that a command advances a hidden clock by its frame count minus one and the bar loses a cell every third advance, and it was once fitted to three ticks. This record has one. The advance count at the tick is four: t1 through t4 each returned two frames, t5 returned one and did not advance it. Four advances and one tick determine neither period nor offset, so this is a shape with no parameters left. It still makes one cheap qualitative prediction -- that ACTION7 is the only command so far that did not advance the world clock -- and that is testable by pressing ACTION7 and reading the frame count alone, with no cell comparison needed."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_toll_on_the_restore_key_reading_is_alive "in this record ACTION4 was pressed exactly once and the bar moved exactly once, which is the toll reading fitting perfectly with one point. My manual does not implement it, because implementing it means repainting (53,62), which is board and carries no instance. So the reading is untestable by replay and settled by one press: from the current blanked state, key(4) restores exactly twelve strip cells under my manual and thirteen cells including (53,62) under the toll reading. Cheapest open question in the game."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem i_do_not_know_which_way_the_bar_runs "one cell has gone from 2 to 3 at the right end of row 53. That is equally a resource being spent and a progress meter being filled, and colour 3 is also what an unselected slot shows on its rails, which argues weakly that 3 is a resting or completed state rather than a consumed one. Nothing in five transitions separates them, and they invert the sign of every ranking decision: under one reading a probe costs part of a budget, under the other it earns progress. Until something separates them the playbook may not rank on bar movement in either direction. The separator arrives on its own -- either the bar reaching column 10 ends the level, or NOT_FINISHED survives it."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: pending]

  theorem the_bar_is_between_fifty_three_and_sixty_three_cells_long "row 53 reads colour 2 over columns 10 to 62 and colour 3 at 63. I have never been shown columns 0 to 9 of that row, so 53 cells are measured unconverted and up to 63 exist if the bar reaches the left edge. Directly beneath it, row 54 reads colour 4 across the whole window and has never varied. Whatever the cadence turns out to be, the magnitude is safe in both directions: the bar is long compared with six actions, so probing is cheap now and will not stay cheap. I have stopped calling it a countdown."
    [depends: i_do_not_know_which_way_the_bar_runs  probe: pending]

  theorem the_strip_hides_and_shows_and_the_separator_is_still_one_action_away "key(3) blanked a shown strip at t3, key(7) blanked one at t5, key(4) restored a blanked one at t4, twelve cells and cell for cell identical each time, so the pattern lives somewhere the frame does not show. Both blank presses were made from a shown strip and the single restore from a blanked one, so hide-and-show and toggle-and-toggle are still indistinguishable. That key(3) and key(7) produced identical twelve-cell diffs is itself worth naming: they may be one function under two names, and no evidence separates them either. The state now is blanked and my manual commits to inert for a repeat of either blanking key -- every strip cell is colour 4, so no blanking guard can fire and no meter rule can fire. A restore under a blanking key refutes hide-and-show outright; nothing happening confirms it and also reads what a null command does to the frame count."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_restore_and_blank_rules_are_conditioned_on_a_selection_the_manual_cannot_represent "the restore rules guard on colour 4 alone, and the blanking rules now guard on as few as one neighbour test. Both are correct on every press observed, because every press was made with the bottom slot selected, where the only colour-4 Pip and Stud instances in existence are the twelve blanked lane B cells. They would be wrong the moment slot A is selected: lane A strip cells become texture while lane B strip cells become arena fill of colour 4, and the instances do not move with the widget because I only ever recolour. My manual never reaches that state, being silent on the selector, so this costs zero transitions and certify cannot see it. It is written here because a searcher planning through a selector move would be misled by rules that score 12 of 12. The fix needs a guard that reads which slot is selected, and selection is exactly what the guard language cannot see."
    [depends: the_swap_is_provably_inexpressible_here  probe: pending]

  theorem the_strip_is_one_global_diagonal_texture "one rule covers every strip cell I have ever seen: a strip cell is colour 2 when (row + col) mod 3 = 1 and colour 1 otherwise. Twenty-one witnesses inside this brief. Frame 0 row 38 cols 16-22 reads 1 2 1 1 2 1 1 and row 39 reads 2 1 1 2 1 1 2, a period-3 run offset by one column; the divergence report gives lane A row 32 cols 16-22 as the world drew it at t1 -- 1 2 1 1 2 1 1 -- and rows 32 and 38 agree because 6 is divisible by 3. The two port cells fit the same formula, which is an unforced success. So the two strips are two windows onto one texture, which is why a restore can rebuild twelve cells exactly. Untested prediction: select slot A and row 33 cols 17-22 reads 1 1 2 1 1 2. No rule needs this, since each instance remembers its frame 0 colour, so by constraint 3 the concept buys understanding rather than symbols and stays out of the word table."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_seed_column_is_never_erased "blanking takes cols 17-22 of the selected lane and stops there, twice now, twelve cells both times. (38,16)=1 and (39,16)=2 sit on the widget right edge, are Pip and Stud instances, and have never changed under any blank; the guards say why, since the left neighbour of each is a colour-0 cavity cell. They are the only cells of the texture that survive hiding and they are exactly the two needed to phase a period-3 run. The rival explanation is that col 16 is simply where the 6x6 widget ends and the survival is coincidence; two blanks do not separate them."
    [depends: the_strip_is_one_global_diagonal_texture  probe: pending]

  theorem the_panel_is_a_column_of_slots_and_it_continues_above_row_29 "cells (29,13) and (29,14) hold colour 3 and have never varied, so they are board. Colour 3 at cols 13-14 is what an unselected slot shows at its four outer rows, and the unselected slot at rows 30-35 shows 3 3 2 2 3 3 down those columns, so row 29 sits where the last row of a slot at rows 24-29 would sit. The period is measured inside this brief: the divergence report gives the world's t1 rows 30, 31, 32 at cols 11-16 as 6 6 6 6 6 6 / 6 0 0 0 0 6 / 6 0 6 6 0 1, and frame 0 rows 36, 37, 38 at those columns read identically -- eighteen cells, six rows apart. Rows 42 to 52 are uniform background, so rows 36-41 is the bottom slot. I read key(1) as moving selection up one slot and key(2) as down one. My manual is silent on both, so either press scores for free: from the bottom slot the down key does nothing under the move reading and repaints 96 cells under a two-slot toggle, and from the upper slot the up key repaints rows 24-35 if a third slot exists."
    [depends: frame_zero_is_reconstructed_exactly  probe: pending]

  theorem the_badge_is_lane_aligned_but_it_is_not_the_same_shape_as_a_strip "the arena is colour 4 over cols 17-46, bounded on the right by background from col 47, re-counted against the current frame. The only thing in it that is neither strip nor fill is a 4x4 block of colour 14 at rows 31-34 by cols 42-45. Those are exactly the rows an upper-slot cavity occupies within its own six-row band, so the badge belongs to the lane of the slot at rows 30-35, and the bottom slot's lane has nothing at cols 42-45. But the strip is 2 rows by 6 cols and the badge is 4 rows by 4 cols of one uniform colour, so the tempting reading -- a target the lane texture must be made to match -- does not survive a shape comparison and I am downgrading it. The surviving readings are that it marks which slot carries a task, or that it is a destination something must reach. Zero transitions bear on either, and slots above row 29 may carry badges I have never seen, since an unvarying badge is board by definition."
    [depends: the_panel_is_a_column_of_slots_and_it_continues_above_row_29  probe: pending]

  theorem the_meter_cadence_is_inexpressible_and_i_rechecked_both_loopholes "a guard reads a cell colour, its four neighbour colours, off-board, and the action name. A cadence needs a count and there is no count in the grammar. Loophole one, an object whose declared colour equals the background used as an invisible latch bit: unusable, because the value grammar exposes only color as a field so no guard can read present, and the 24 colour-5 cells the arm would instantiate are all in the slot footprint, none of them where a latch would be wanted. Loophole two, a second object type declared at colour 2 to reach the next bar cell: unusable, because the arm finds objects by colour alone and would place a duplicate instance on all ten existing Studs. So the cadence stays prose, and with the march rule gone the manual carries no proxy for it at all, which is the smaller of the two available failures."
    [depends: the_meter_has_exactly_one_witnessed_tick_and_the_cadence_is_unidentified  probe: passed]

  theorem nesting_a_cell_expression_is_the_one_device_that_could_break_the_swap_deadlock_and_i_have_not_tested_it "the grammar lists above, below, leftof and rightof as taking a cell, and lists cells exhaustively including those four forms, but does not say whether the argument may itself be one of them. If above(above(?p)) parses, guards gain a two-cell reach and the situation changes measurably: at depth two, (30,16) and (31,16) both see colour 3 two cells to their left while (32,16) and (33,16) see colour 2, which separates the pair that goes to 6 from the pair that goes to 1 and 2; at depth three below, (32,16) sees background and (33,16) sees casing, which separates the last two. So a position-reading device exists in principle. It does not change my verdict, because the compression blocker stands regardless and every such guard is pixel-fitting of the purest kind. I do not test it inside the manual because a parse error costs the whole round; it is a probe, and the cheapest form of the probe is a single throwaway rule with coverage 0/0 in a scratch manual, not this one."
    [depends: the_swap_also_fails_the_compression_test_and_that_blocker_needs_no_grammar_argument  probe: pending]

  theorem colour_classes_are_not_the_worlds_objects_and_i_admit_the_cost "the six declared types are colour classes, not things. Stud alone spans the unselected slot bar, a port, four strip cells and the meter cell -- four unrelated roles. Casing and Cavity together are one widget. The world segments by widget and the arm segments by colour, and the arm wins because the arm draws the frame. The gain is measured: six declarations own all 73 cells that need an owner against 73 pixels written out, with 0 unexplained confirmed twice. The cost is measured too, and it got smaller this round: no rule can name the strip, so every blanking rule still carves it out of its colour class by neighbour tests, but the carving now costs eight guard atoms rather than sixteen, and the meter rule still needs an off-board test to separate one Stud from the other nine. Those guards remain pixel-fitting in a costume; there are simply fewer of them."
    [depends: the_blanking_guards_shrank_from_sixteen_atoms_to_eight_with_no_change_of_firing_set  probe: passed]

  theorem i_have_never_been_shown_rows_0_to_28 "colours_seen lists 8 and 9 and neither appears anywhere in the window I am given, which is rows 29-54 by cols 10-63. They live somewhere in the 3999 constant cells I have never looked at -- above row 29, left of col 10, or below row 54. That region is board by definition and my manual draws it correctly by doing nothing, so responsibility stays at 0 unexplained; but it is also where a title, target, score or instruction would live, and the most likely home of whatever finishing means. It is the largest thing I do not know, and the likeliest place the bar's direction is written down."
    [depends: no_goal_section_on_purpose  probe: pending]

  theorem two_keys_have_never_been_pressed "ACTION1, 2, 3, 4 and 7 have been pressed; key(5) and key(6) have not. The budget argument is unchanged in magnitude even though its sign is unknown: the bar is 53 cells or more from its end and six actions have been spent. If either key is a click carrying coordinates, this guard language cannot express it and the finding will be recorded as prose rather than as a rule. Each press also reads its own returned frame count, which is the only handle left on the clock."
    [depends: the_extra_frame_clock_is_down_to_one_point  probe: pending]

  theorem no_goal_section_on_purpose "all six states returned NOT_FINISHED and nothing in five transitions indicates what finishing means. The live candidates are that a lane must be brought into some relation with the badge at its far end, that every slot in the column must be visited or solved, or that the objective lives in the rows I have never been shown. An absent goal compiles to is_goal implies False, which under-claims and costs a round; a wrong goal sends the searcher after a fiction and costs the level. I will not write a goal on the strength of a badge I have never interacted with, and this round's downgrade of the badge-matching reading makes me less willing, not more."
    [depends: i_do_not_know_which_way_the_bar_runs  probe: pending]

  theorem what_the_engines_offered_and_why_none_of_it_was_taken "mdl_segmenter returns negative gain on both variants, -4037 bits at 4 tracks and -10409 at 33, with tracks that are 440-cell blobs of shape 13x36 and colour null -- the panel and the arena fused by connected_components(4), a fact about the operator rather than the world; its tally of 4 recolors, 2 appears and 2 vanishes is nonetheless consistent with my reading that this world only ever recolours and that the appear/vanish pair is the swap seen as one blob. cegis_miner refuses all four tracks because its precondition is exactly one move event per transition, and its own verdict says the world does not narrate as one mover, which agrees with my event vocabulary of recolored alone. zero_space calls its own evidence THIN in its own words -- 5 transitions constraining rank 3 of 679 features, null space of dimension 676 -- and its single global law spans 97 dynamic cells at once, which is what a 676-dimensional null space produces rather than what a conservation law looks like. What I took from the engines is the store arithmetic, dynamic_cells 97 and cells_needing_an_owner 73, and this round that arithmetic paid a second time by telling me exactly how many colour-5 instances a background object would get, which is what refuted my own second swap blocker."
    [probe: pending]

  theorem what_this_draft_pre_registers "certify should return replay 4 of 5, first divergence at transition 0 under ACTION1, 96 cells wrong, first cell (30,11) manual 5 world 6; responsibility 0 unexplained of 4096; unambiguous 0 clashes. That is deliberately the same score as the previous draft, and it is now a real test rather than a formality: I deleted eight guard atoms, and if my re-derivation of the firing sets is wrong anywhere then t3, t4 or t5 will break and the score will fall to 3 or worse. Any drop below 4 is my error and localises immediately to the blanking or seed guards. The informative pre-registrations about the world are three, each decided by one press from the current blanked state. key(3) or key(7): my manual says the frame does not change at all, which refutes toggle-and-toggle if it holds and refutes my manual if the strip comes back. key(4): my manual says exactly twelve cells change and the bar does not move, while the toll reading says thirteen including (53,62). ACTION7 again: a second single-frame return would make it the only key that does not advance the world clock."
    [depends: the_blanking_guards_shrank_from_sixteen_atoms_to_eight_with_no_change_of_firing_set  probe: pending]
