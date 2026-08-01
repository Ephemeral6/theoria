# theory.dsl -- rebuilt from scratch this round.
#
# WHY IT IS A REBUILD AND NOT AN EDIT.
#
#   The manual I was handed narrates 34 states, a 64-cell colour-9 meter on
#   row 63, a two-slot panel at rows 1-5, and a 5x5 colour-9 body walking a
#   six-pixel lattice at rows 8-18. The evidence brief in front of me reports
#   SIX states, FIVE transitions, background 5, dynamic cells confined to
#   rows 30-41 x cols 11-22 plus the single cell (53,63), and colours 0-6
#   with 8, 9 and 14 appearing only on cells that have never changed. Not one
#   dynamic cell here has frame-0 colour 9, so every Glyph9 rule in the
#   inherited manual is unreachable text -- and worse, its Spent (colour 1)
#   and Dark (colour 0) types WOULD instantiate on my 9 colour-1 and 12
#   colour-0 cells and fire panel recolours that no frame here witnesses.
#   Carrying it forward would poison replay with rules that have zero
#   evidence in this evidence stream. I discard it wholesale. If those frames
#   return, its text is in the history; nothing is lost but a paste.
#
#   The compiler complaint that brought me here is separate and simpler: the
#   last reply carried no === THEORY === block at all, so nothing compiled and
#   nothing replayed. That is fixed by emitting the block.
#
# WHAT THIS MANUAL CLAIMS AND WHAT IT PAYS.
#
#   Cell-level diffs exist for exactly three transitions (t3 key3, t4 key4,
#   t5 key7) and they are fully explained by seven rules. t1 (key1) and t2
#   (key2) each rewrote all 96 dynamic cells of the arena and I was given
#   only their count and bounding box, never their pixels. I write NO rule
#   for key1 or key2. My manual therefore predicts identity for them and is
#   wrong by 96 pixels on t1 and 96 on t2. Expect replay 3/5. That number is
#   posted in advance so it cannot be mistaken for a surprise, and the probe
#   that fixes it is named in what_i_predict_before_i_see_it.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Ink0   { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Tok1   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Tok2   { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Rail3  { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object Panel4 { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Floor5 { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Case6  { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  Tok1   [segment: dynamic_colour_1 ev: t3,t4,t5 compress: 9]
  Tok2   [segment: dynamic_colour_2 ev: t3,t4,t5 compress: 10]
  Ink0   [segment: dynamic_colour_0 ev: t1,t2 compress: 12]
  Rail3  [segment: dynamic_colour_3 ev: t1,t2 compress: 8]
  Panel4 [segment: dynamic_colour_4 ev: t1,t2 compress: 12]
  Floor5 [segment: dynamic_colour_5 ev: t1,t2 compress: 24]
  Case6  [segment: dynamic_colour_6 ev: t1,t2 compress: 22]

rules:
  rule key3_clears_strip_tok1 forall ?p in Tok1 [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key3_clears_strip_tok2 forall ?p in Tok2 [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key7_clears_strip_tok1 forall ?p in Tok1 [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key7_clears_strip_tok2 forall ?p in Tok2 [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule key4_redraws_strip_tok1 forall ?p in Tok1 [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) and colored(above(above(?p)), 4) then recolored(?p, 1)

  rule key4_redraws_strip_tok2 forall ?p in Tok2 [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) and colored(above(above(?p)), 4) then recolored(?p, 2)

  rule key4_burns_bar_end forall ?p in Tok2 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

laws:
  invariant board_cells count(board) = 3999 [status: counted from the store]
  invariant tok1_instances count(Tok1) = 9 [status: inferred from the frame-0 census]
  invariant tok2_instances count(Tok2) = 10 [status: inferred from the frame-0 census]
  invariant ink0_instances count(Ink0) = 12 [status: inferred from the frame-0 census]
  invariant rail3_instances count(Rail3) = 8 [status: inferred from the frame-0 census]
  invariant floor5_instances count(Floor5) = 24 [status: inferred, and it equals the 24 the store withholds from cells_needing_an_owner]
  invariant case6_instances count(Case6) = 22 [status: inferred from the frame-0 census]
  invariant panel4_instances count(Panel4) = 12 [status: derived by subtraction, the weakest number in this manual]
  invariant bar_burned_cells count(Tok2, color = 3) = 1 [status: counted in the current frame, a tally and not a conservation law]

  theorem the_inherited_manual_describes_a_world_these_frames_do_not_show "I was handed a manual for 34 states, a colour-9 body on a six-pixel lattice, a two-slot panel at rows 1-5 and a 64-cell colour-9 meter on row 63. The brief in front of me reports 6 states, 5 transitions, dynamic cells only in rows 30-41 x cols 11-22 plus (53,63), and colour 9 present only on cells that have never changed. Those two descriptions cannot both be of the frames I was given, and the brief is what the responsibility check will redraw my manual onto, so the brief wins. Discarding was not a preference: the inherited Spent (arc-colour 1) and Dark (arc-colour 0) types would seat instances on my nine colour-1 and twelve colour-0 cells and fire thirteen panel recolours that no transition here witnesses, which is a direct violation of no-entry-without-evidence and would have made replay worse than an empty manual. The one thing I carry across is a method, not a fact: price the pixels you cannot draw BEFORE the world charges you for them."
    [depends: the_census_of_ninety_seven_cells  probe: passed]

  theorem the_census_of_ninety_seven_cells "Every dynamic cell is owned and the arithmetic closes three separate ways. The store says shape 64x64, constant 3999, dynamic 97, cells_needing_an_owner 73. The five diffs place 96 of those 97 inside rows 30-41 x cols 11-22 and the last at (53,63). Frame-0 colour of every cell is recoverable because t3, t4 and t5 touched only the strip and the bar, and t2 undid t1 exactly (distinct_states is 5 for 6 states, so exactly one pair coincides and s2 = s0): so frame 0 is the current frame with the strip redrawn as 2-1-1-2-1-1 over 1-1-2-1-1-2 and (53,63) back to 2. Counting the current frame cell by cell gives 12 colour-0, 9 colour-1, 10 colour-2, 8 colour-3, 24 colour-5, 22 colour-6, which is 85, leaving 12 colour-4 by subtraction, and 85 + 12 = 97 exactly. INDEPENDENT CHECK: 97 minus cells_needing_an_owner 73 is 24, which is exactly the count of dynamic cells whose colour is the background 5 -- the cells the board can already explain and which therefore need no owner. That the two numbers agree without being fitted to each other is the strongest evidence in this manual. I declare all seven colours anyway, so that if the checker does demand owners for background-coloured cells it finds twenty-four."
    [probe: passed]

  theorem the_arena_as_i_read_it_off_the_current_frame "Read pixel by pixel, and stated so a later desk can check me. A colour-4 PANEL fills rows 29-41 x cols 17-46, holding a constant 4x4 colour-14 block at rows 31-34 x cols 42-45 and a 2x6 SLOT at rows 38-39 x cols 17-22. West of it a 2-wide RAIL runs down cols 13-14 from row 29 to row 35, colour 3 except rows 32-33 which are colour 2 -- a two-row marker sitting at the middle of a seven-row track. Below the rail a 6x6 colour-6 CASE occupies rows 36-41 x cols 11-16: solid colour-6 border, an interior ring of colour 0 at rows 37-40 x cols 12-15, a 2x2 colour-6 core at rows 38-39 x cols 13-14, and TWO SOCKET PIXELS punched through its east wall at (38,16) colour 1 and (39,16) colour 2. The socket rows are exactly the slot rows and the socket colours are exactly the slot colours, which is why I read the case as the source of what the slot displays -- a reading, not a law. Far below, row 53 cols 10-63 is a 54-cell colour-2 BAR with row 54 beneath it in colour 4; the bar segmenter track obj1 is 2x54 and confirms the bar starts at col 10, not col 0. Colours 8 and 9 exist somewhere outside this window on cells that have never changed; I have never been shown them and say nothing about them."
    [depends: the_census_of_ninety_seven_cells  probe: passed]

  theorem the_slot_is_a_two_state_display_and_three_keys_drive_it "The slot at rows 38-39 x cols 17-22 holds two side-by-side copies of one 2x3 glyph, 2-1-1 over 1-1-2, and it is either FULLY DRAWN or FULLY BLANK -- twelve cells move together, three times, with no intermediate ever observed. Blank is colour 4, the panel colour, not the background 5, which is why I model the transition as recolour and not as vanished(): present=False would render the wrong colour and cost twelve pixels every time. ACTION3 blanked it (t3), ACTION7 blanked it (t5), ACTION4 redrew it (t4), each time the whole twelve. Redraw restores the exact original pattern, so the pattern is held somewhere the frame does not show or is a fixed template; I cannot tell which and do not need to, because two rules per key reproduce it from the cells themselves. THE GUARD THAT DOES THE WORK is colored(above(above(?p)), 4): among all Tok1 and Tok2 instances it is true of the twelve slot cells and false of the case sockets (their two-above is colour 6), of the rail marker (colour 3 above), and of the bar end (colour 5 above). One atom separates four groups, which is what earns it under the gain test."
    [depends: key3_clears_strip_tok1, key4_redraws_strip_tok2  probe: passed]

  theorem what_key1_and_key2_do_is_this_manual_s_largest_hole_and_i_price_it_at_ninety_six_pixels "ACTION1 changed 96 cells and ACTION2 changed 96 cells, bounding box rows 30-41 x cols 11-22, colour sets [0..6] before and after both times. 96 is EVERY dynamic cell of the arena except the bar end -- the rail, the case, the slot and the twelve dynamic panel cells all moved at once. I was given the count and the box and never the pixels, so I have no witness for a single cell of state s1 and I write no rule. Consequence, stated as a bill and not as an excuse: my compiled step returns identity for key(1) and key(2), so replay diverges by 96 cells on t1 and 96 on t2, and 3/5 is the ceiling of this manual, not a defect I can repair from what I hold. WHAT I DO KNOW ABOUT s1, all of it: s2 = s0 (distinct_states 5 of 6, and t2 restored exactly the cells t1 touched), so ACTION2 undoes ACTION1; and mdl_segmenter, which has never seen my rules, reports the arena blob at 440 non-background cells in frame 0, 436 in frame 1, and 440 again from frame 2 -- so s1 has FOUR FEWER non-background cells than s0, which rules out any reading where the twenty-four background cells at cols 11-12 and 15-16 are simply filled in. THE PROBE IS FREE AND OBVIOUS: the brief always prints the current frame, and prints cell-level diffs only for small changes, so the way to see s1 is to make s1 the state the round ENDS in. One press of ACTION1 not followed by ACTION2 buys ninety-six pixels of manual."
    [depends: the_census_of_ninety_seven_cells, what_the_engines_gave_me  probe: pending]

  theorem the_bar_burn_has_one_witness_and_the_even_index_reading_is_already_dead "(53,63), the east end of the 54-cell colour-2 bar, went 2 to 3 at t4 and at no other transition. THREE READINGS FIT ONE WITNESS. (a) ACTION4 burns: 1 positive, and 4 negatives, since keys 1, 2, 3 and 7 each ran without a burn. (b) The burn is charged for the EFFECT -- t4 is the only transition that redrew the slot rather than blanking it, so the bar may count restorations, or mistakes. (c) The burn is keyed to the command counter. READING (c) IN ITS SIMPLEST FORM IS ALREADY REFUTED: command index 2 was even and did not burn. I encode (a) because it is the only one this guard language can say, and I flag the confound loudly rather than let it rot: (a) and (b) agree on every transition observed so far and are separated by ONE press -- ACTION4 while the slot is already drawn. Under (a) the bar burns again; under (b) nothing happens. Note that my rule cannot show the second burn either way, for the reason in i_cannot_draw_a_burn_on_a_cell_that_has_never_changed, so the separator must be read off the raw diff and not off the refutation flag."
    [depends: key4_burns_bar_end  probe: pending]

  theorem i_cannot_draw_a_burn_on_a_cell_that_has_never_changed "The arm seats instances only on cells the board cannot explain, so a cell that has never varied has no instance and no rule of mine can repaint it. (53,63) is dynamic and owned; (53,62), its western neighbour and the natural next cell of a bar that burns from the east, is still constant and therefore unowned. So if the bar advances, the first pixel of the advance is undrawable BY CONSTRUCTION, exactly one wrong cell, and my manual heals only on the transition after. My burn rule is already unable to fire twice: it demands colour 2 at a cell that now reads 3. The rule that will be needed the moment the second burn makes (53,62) dynamic is written out here so it costs a paste and not a round -- rule burn_next forall ?p in Tok2 when act=key(4) and colored(?p, 2) and colored(rightof(?p), 3) then recolored(?p, 3) -- and it stays OUT of the manual until a transition witnesses it, because a rule with cov 0/0 is exactly what constraint 2 forbids."
    [depends: the_bar_burn_has_one_witness_and_the_even_index_reading_is_already_dead  probe: pending]

  theorem silence_is_a_prediction_and_four_of_my_silences_are_unwitnessed "The compiled step is total: where no rule fires the successor is the current state, so my manual never says I do not know, it says nothing happens, in the same voice it uses for things it has seen. Audit every key against the current state, where the slot is BLANK and the bar end is burned. key(3) and key(7): my clear rules demand colour 1 or 2 in the slot, which is false now, so both are predicted inert -- NO WITNESS, the slot has never been blanked twice running. key(4): the redraw rules fire, twelve cells, WITNESSED at t4; the burn rule cannot fire again. key(1) and key(2): predicted inert and KNOWN FALSE, ninety-six cells each, the hole above. key(5) and key(6): never pressed in this world, predicted inert, NO WITNESS AT ALL, and therefore the cheapest unclaimed information on the board -- two keys of a seven-key alphabet about which this manual asserts total inertness on the strength of nothing."
    [depends: key3_clears_strip_tok1, what_key1_and_key2_do_is_this_manual_s_largest_hole_and_i_price_it_at_ninety_six_pixels  probe: pending]

  theorem key3_and_key7_are_indistinguishable_so_far_and_i_refuse_to_merge_them "Each was pressed once, each from a state with the slot drawn, each blanked exactly the same twelve cells. Four of my seven rules exist only because the guard language keys on the action name: key3_clears and key7_clears are the same body twice. The gain test says merge them, and I cannot -- there is no disjunction in the guard grammar and no domain of actions to quantify over, so two identical bodies is the shortest thing sayable. I record it as a cost I pay to the DSL rather than a claim about the world, and I record the discriminator: press either key from a state the other has never acted on, or press one twice. If they ever diverge, four rules become two plus a difference; if they never do, this manual carries two redundant lines forever and says so."
    [depends: key3_clears_strip_tok1, key7_clears_strip_tok1  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "Nothing in six frames has announced a win: state is NOT_FINISHED throughout, no cell has behaved like a scoreboard except the bar, and the bar moved once. The candidates all fail. count(Tok1) = 0 is never true -- the arm counts instances, not drawn cells. count(Tok1, color = 4) = 8 is true of every blanked-slot state including the current one, which is plainly not a win. The colour-14 block at rows 31-34 x cols 42-45 is the most goal-shaped thing on the board and it is CONSTANT, so it has no instance and count() has nothing to range over there. A goal true in the wrong state is worse than no goal because it halts a planner at its first step. So is_goal compiles to False, no plan terminates, and command choice falls back entirely on what the manual predicts will change -- which today is key(4) and nothing else, and that is a trap I name in the playbook."
    [depends: the_arena_as_i_read_it_off_the_current_frame  probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter reports NEGATIVE gain on both variants, -4037 bits unsplit and -10409 bits split by colour, so its own accounting says its segmentation does not beat writing the pixels out, and I owe it nothing structural. I take two facts from it anyway, both checkable. FIRST, obj1: 108 cells, shape 2x54, present in all six frames -- that is rows 53-54 x cols 10-63, and it is how I know the bar starts at col 10 rather than col 0. SECOND, obj0/obj2/obj3: one 13x36 blob at rows 29-41 x cols 11-46, 440 cells in frame 0, 436 in frame 1, 440 from frame 2 on. Since it chose connected_components(4) with split_by_color false, that blob is the whole non-background arena -- panel plus rail plus case, 468 box cells minus the 28 that are background or colour-14 -- and its four-cell dip at frame 1 is the only quantitative thing I possess about s1. I reject all four tracks AS OBJECTS: a 440-cell track cannot be one instance, and a second type over the same pixels invites the double claim constraint 5 forbids. cegis_miner refused every track and its verdict, the world does not narrate as one mover, is CORRECT here and not merely an arm limitation -- nothing in six frames translates; every event is a recolour in place. zero_space self-reports THIN in its own words, rank 3 of 679 features over 5 transitions, and its single global law is a list of my 97 dynamic cells, which is my census and not an independent law."
    [depends: the_census_of_ninety_seven_cells  probe: passed]

  theorem what_i_predict_before_i_see_it "Written so the world can charge me. The state is: slot BLANK, rail marker at rows 32-33, case unchanged, one bar cell burned. key(4): I predict exactly twelve cells, the slot redrawn to 2-1-1-2-1-1 over 1-1-2-1-1-2, and NO burn, because my burn rule needs colour 2 at (53,63) and finds 3. If a burn appears at (53,62) I am wrong by one pixel and reading (a) of the bar survives; if a burn appears anywhere else the bar is not a right-to-left counter. key(3) or key(7): I predict ZERO cells, an unwitnessed silence, and any change at all refutes the clear rules as stated. key(1): I predict ZERO cells and I EXPECT TO BE WRONG BY NINETY-SIX -- this is the press I want, because the resulting frame is printed in full and buys me the state s1 that five transitions have hidden, and because being wrong by 96 predicted pixels is the loudest signal available. key(2) from here: unknown, since ACTION2 has only ever been observed immediately after ACTION1; if it is an undo it should be inert here and if it is an independent rewrite it should move 96 cells. key(5) or key(6): I predict ZERO cells on no evidence whatsoever. The one prediction I would most like refuted is that the slot has only two states."
    [depends: silence_is_a_prediction_and_four_of_my_silences_are_unwitnessed, what_key1_and_key2_do_is_this_manual_s_largest_hole_and_i_price_it_at_ninety_six_pixels  probe: pending]

  theorem the_dsl_cannot_say_i_have_not_been_shown_this "Two holes I hit this round. FIRST and worst: there is no way to write unobserved, the manual declines to predict. Rules produce events and the absence of a rule produces identity, so my honest ignorance about ACTION1 is compiled into a confident claim that ACTION1 does nothing. The only lever the grammar offers is to write a guessed rule instead, which trades a known-wrong silence for an invented change and violates constraint 2; I take the silence and post the 96-pixel bill in the open. SECOND: the arm types instances by frame-0 colour and looks objects up by colour alone, so the twelve slot cells, which render 4 exactly when they are blank, are Tok1 and Tok2 forever and never Panel4. Every one of my seven rules depends on that, and if the arm instead retypes by current colour then all seven fire on the wrong instances and replay collapses -- so this is the single assumption whose failure would be total rather than incremental, and I name it here so the first divergence report can be read against it."
    [depends: the_slot_is_a_two_state_display_and_three_keys_drive_it  probe: pending]
