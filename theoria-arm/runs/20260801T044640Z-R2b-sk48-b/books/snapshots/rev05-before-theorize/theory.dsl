# theory.dsl -- REWRITTEN FROM SCRATCH. This is not the world the previous
# manual described.
#
# WHY THE OLD MANUAL IS GONE, IN ONE PARAGRAPH
#
#   The store now reads: 6 states, 6 steps, 5 transitions, background 5,
#   97 dynamic cells, dynamic box rows 29-54 cols 10-63, colours seen
#   {0,1,2,3,4,5,6,8,9,14}, actions used A1 A2 A3 A4 A7. The manual I was
#   handed described 34 states, an 87-cell dynamic set at rows 8-18 and
#   row 63, a 5x5 body ring, a two-slot panel and a 64-cell meter bar. Not
#   one of those pixels exists in these frames. This is a different level
#   (the surprise says level 1) with a fresh store. Every rule, every
#   landmark and every count in that manual is about geometry that is not
#   on this board, so keeping any of it would be inventing pixels. I have
#   kept exactly three things from it and they are all method, not content:
#   price your defects in advance, never write a rule the diff did not
#   show you cell by cell, and check that a rule can fire before ranking a
#   probe that tests it.
#
# THE SURPRISE THAT BROUGHT ME HERE, AND MY ANSWER
#
#   certify: "theory.dsl is non-empty but generated/theory.py could not be
#   loaded". The old manual did not COMPILE, so replay, responsibility and
#   ambiguity all reported nothing. Two constructs in it are the plausible
#   causes and this manual removes both:
#     (1) `landmark spawn_probe  # arc-cell: carried, coordinates stripped`
#         -- the grammar says a landmark the level cannot place is a HARD
#         compile error, and "carried, coordinates stripped" is not a
#         coordinate. THIS MANUAL DECLARES NO LANDMARKS AT ALL. Every
#         discrimination below is done with colour and neighbour tests, so
#         there is nothing for the level to fail to place.
#     (2) a bare `goal:` header with an empty body. "No goal section at all
#         is legal"; an EMPTY one is not documented to be. THIS MANUAL HAS
#         NO GOAL SECTION.
#   I cannot bisect a compiler I cannot run, so I say plainly: I have
#   removed the two constructs I can argue for and I do not know which one
#   it was. If theory.py still fails to load, the cause is neither, and the
#   next desk should delete rule blocks in halves rather than re-reason.
#
# WHAT I ACTUALLY KNOW ABOUT THIS WORLD
#
#   Every one of the 97 dynamic cells is accounted for, and the account is
#   not my guess -- zero_space's single global law enumerates its cells and
#   they are exactly these four rectangles plus one corner pixel:
#     icon1  rows 30-35 x cols 11-16   36 cells
#     icon2  rows 36-41 x cols 11-16   36 cells
#     tape1  rows 32-33 x cols 17-22   12 cells
#     tape2  rows 38-39 x cols 17-22   12 cells
#     meter  (53,63)                    1 cell
#   36+36+12+12+1 = 97 = dynamic_cells, exactly.
#
#   Three of the five transitions are known cell by cell and are fully
#   ruled below. Two of them -- A1 and A2 -- were reported only as a count,
#   a bounding box and two colour sets, so I have NO cell-level evidence and
#   I write NO rule. That is the one large hole and I price it in advance:
#   replay will miss t1 and t2 by up to 96 cells each and be exact on
#   t3, t4, t5. Expect 3/5.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Ink0 { pos: Coord, color: Int }   # arc-colour: 0  arc-instances: all
  object Ink1 { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  object Ink2 { pos: Coord, color: Int }   # arc-colour: 2  arc-instances: all
  object Ink3 { pos: Coord, color: Int }   # arc-colour: 3  arc-instances: all
  object Ink4 { pos: Coord, color: Int }   # arc-colour: 4  arc-instances: all
  object Ink5 { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Ink6 { pos: Coord, color: Int }   # arc-colour: 6  arc-instances: all
  Ink0 [segment: frame0_colour_0 ev: t1,t2 compress: 12]
  Ink1 [segment: frame0_colour_1 ev: t1,t2,t3,t4,t5 compress: 9]
  Ink2 [segment: frame0_colour_2 ev: t1,t2,t3,t4,t5 compress: 10]
  Ink3 [segment: frame0_colour_3 ev: t1,t2 compress: 8]
  Ink4 [segment: frame0_colour_4 ev: t1,t2 compress: 12]
  Ink5 [segment: frame0_colour_5 ev: t1,t2 compress: 24]
  Ink6 [segment: frame0_colour_6 ev: t1,t2 compress: 22]

events:
  event recolored(o, c)

rules:
  rule a3_hides_tape2_ones forall ?p in Ink1 [ev: t3 cov: 8/8]
    when act=key(3) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule a3_hides_tape2_twos forall ?p in Ink2 [ev: t3 cov: 4/4]
    when act=key(3) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule a7_hides_tape2_ones forall ?p in Ink1 [ev: t5 cov: 8/8]
    when act=key(7) and colored(?p, 1) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule a7_hides_tape2_twos forall ?p in Ink2 [ev: t5 cov: 4/4]
    when act=key(7) and colored(?p, 2) and colored(above(above(?p)), 4) then recolored(?p, 4)

  rule a4_shows_tape2_ones forall ?p in Ink1 [ev: t4 cov: 8/8]
    when act=key(4) and colored(?p, 4) and colored(above(above(?p)), 4) then recolored(?p, 1)

  rule a4_shows_tape2_twos forall ?p in Ink2 [ev: t4 cov: 4/4]
    when act=key(4) and colored(?p, 4) and colored(above(above(?p)), 4) then recolored(?p, 2)

  rule a4_advances_the_corner_pixel forall ?p in Ink2 [ev: t4 cov: 1/1]
    when act=key(4) and colored(?p, 2) and rightof(?p) = wall then recolored(?p, 3)

laws:
  invariant board_cells count(board) = 3999 [status: counted]
  invariant ink0_instances count(Ink0) = 12 [status: derived]
  invariant ink1_instances count(Ink1) = 9 [status: derived]
  invariant ink2_instances count(Ink2) = 10 [status: derived]
  invariant ink3_instances count(Ink3) = 8 [status: derived]
  invariant ink4_instances count(Ink4) = 12 [status: derived]
  invariant ink5_instances count(Ink5) = 24 [status: derived]
  invariant ink6_instances count(Ink6) = 22 [status: derived]
  invariant owned_dynamic_cells count(Ink0) + count(Ink1) + count(Ink2) + count(Ink3) + count(Ink4) + count(Ink5) + count(Ink6) = 97 [status: derived]
  invariant cells_needing_an_owner count(Ink0) + count(Ink1) + count(Ink2) + count(Ink3) + count(Ink4) + count(Ink6) = 73 [status: derived]

  theorem the_dynamic_set_is_four_rectangles_and_one_corner_pixel "THE LOAD-BEARING FACT OF THIS MANUAL, AND IT IS NOT MY GUESS. zero_space's single global law enumerates the cells it constrains and I read them off one by one: (30,11)-(30,16) through (41,11)-(41,16), which is a 12x6 column band; (32,17)-(32,22) and (33,17)-(33,22); (38,17)-(38,22) and (39,17)-(39,22); and (53,63). That is 72 + 12 + 12 + 1 = 97, and the store says dynamic_cells is 97. The bounding box of that set is rows 30-41 x cols 11-63, which is the reported box [29,10,54,63] padded by one on each side, so the two agree exactly and nothing is left over. I name the four parts by what the pixels look like rather than by what they do, because what they do is only partly known: ICON1 rows 30-35 cols 11-16, ICON2 rows 36-41 cols 11-16, TAPE1 rows 32-33 cols 17-22, TAPE2 rows 38-39 cols 17-22, METER (53,63). Note the alignment that makes the reading almost forced: each tape is exactly the middle two rows of its icon, extended six columns to the right. Two rows of a list, each an icon with a value strip beside it."
    [probe: passed]

  theorem the_census_closes_to_the_pixel_and_that_is_why_seven_types "Read the frame-0 colour of all 97 cells from the current frame (which IS frame 0 outside tape2, since s2 = s0 and s5 differs from s0 only in tape2 and the meter, and tape2's frame-0 colours are recoverable from the t4 diff). ICON1: cols 11,12,15,16 x rows 30-35 render background 5, that is 24 cells; cols 13,14 x rows 30,31,34,35 render 3, that is 8; cols 13,14 x rows 32,33 render 2, that is 4. ICON2: 22 cells of colour 6, 12 of colour 0, plus (38,16) colour 1 and (39,16) colour 2. TAPE1: 12 cells of colour 4. TAPE2, from the t4 diff's target colours: 8 of colour 1 and 4 of colour 2. METER: 1 of colour 2. By colour the totals are 0:12, 1:9, 2:10, 3:8, 4:12, 5:24, 6:22, summing to 97. TWO INDEPENDENT CHECKS PASS. First, 97 - 24 = 73 = cells_needing_an_owner exactly, and the 24 excluded are precisely the background-coloured ones -- so the store's `needing an owner` means `dynamic and not the background colour`, and Ink5 is the type that owns the 24 the store does not count. Second, 4096 - 97 = 3999 = constant_cells exactly. That is why there are seven types and not four: the arm looks objects up by colour and nothing else, so a type per frame-0 colour is the ONLY declaration that owns every dynamic cell. It buys no structure and I do not pretend it does -- ICON1 is spread across Ink5, Ink3 and Ink2 and no rule can say `icon1`."
    [depends: the_dynamic_set_is_four_rectangles_and_one_corner_pixel  probe: passed]

  theorem the_ninety_six_cell_transition_is_the_hole_and_here_is_its_price "A1 and A2 each changed 96 cells in rows 30-41 x cols 11-22 and the diff reported a COUNT, A BOX AND TWO COLOUR SETS AND NOTHING ELSE. 96 is exactly icon1 + icon2 + tape1 + tape2, so I know that EVERY dynamic cell of the widget area changes under A1 and again under A2 and that the meter does not. I also know A2 undoes A1: distinct_states is 5 against 6 states, so exactly one pair coincides, and it can only be s0 = s2 because s3, s4, s5 are separated from each other and from s0 by the tape and the meter. So A2 o A1 is the identity on this state. WHAT I DO NOT KNOW is which colour each of the 96 cells takes, and no amount of reasoning recovers it from a colour SET. THEREFORE I WRITE NO RULE. The compiled step is total, so my manual predicts identity for key(1) and key(2), which is KNOWN FALSE by 96 cells each. I state the bill before certify does: t1 misses 96, t2 misses 96, t3 t4 t5 are exact, expect replay 3/5. This is a defect of my evidence and not of my vocabulary, and it is repaired by one command and no thought at all -- see the_cheapest_command_on_this_board."
    [depends: the_dynamic_set_is_four_rectangles_and_one_corner_pixel  probe: passed]

  theorem the_cheapest_command_on_this_board "The frame I am shown each round is the CURRENT one, in full, over every cell that has ever changed. The frame I am NOT shown is s1, the configuration A1 produces, because it was two states ago and the diff that made it was summarised. So the entire content of the 96-cell hole is one press away: press key(1) now, and next round the current frame IS the other configuration, cell by cell, and the A1 and A2 rules can be written from pixels instead of guessed. Nothing else on this board buys 96 cells. The cost is exactly the refutation I priced above -- 96 divergent cells on a transition whose ignorance I declared in advance -- and it must not be read as the manual failing. A second press of key(1) afterwards is worth almost as much and answers a different question: if it returns to s0 the widget is a 2-cycle, and if it produces a third configuration it is a longer cycle or a scroll, which changes what a rule over it has to say."
    [depends: the_ninety_six_cell_transition_is_the_hole_and_here_is_its_price  probe: pending]

  theorem tape2_is_hidden_and_shown_and_the_guard_that_isolates_it "Three transitions, 12 cells each way, and they are the whole of what this manual predicts. In s0 the seven cells (38,16)-(38,22) render 1,2,1,1,2,1,1 and (39,16)-(39,22) render 2,1,1,2,1,1,2 -- one diagonal stripe pattern, colour 2 exactly where (row + col) mod 3 = 1 and colour 1 elsewhere, verified on all fourteen. Six of each row, cols 17-22, are dynamic; the col-16 pair never changes and is board. key(3) at t3 and key(7) at t5 turned all twelve to 4, the colour of the canvas they sit in; key(4) at t4 turned all twelve back to their stripe colours, each to its own. So the tape is SEVEN long when shown and ONE long when hidden, or equivalently the canvas is painted over it -- the two readings are the same pixels and I take the painting one because it is what a recolour rule can say. THE GUARD. `colored(above(above(?p)), 4)` is what separates the twelve tape cells from the other seven Ink1 and Ink2 instances, and I checked every one: (38,16) has (36,16) = 6, (39,16) has (37,16) = 6, the four icon1 cells at rows 32,33 cols 13,14 have (30,13)=(30,14)=(31,13)=(31,14) = 3, and the meter (53,63) has (51,63) = 5 -- all excluded, while every tape cell has (36,c) or (37,c) = 4. Twelve fire, seven do not, 12/12 on three transitions."
    [depends: the_dynamic_set_is_four_rectangles_and_one_corner_pixel  probe: passed]

  theorem the_guard_i_did_not_write_and_why "I considered conjoining `colored(below(below(?p)), 4)` to all six tape rules. It is TRUE of every one of the twelve tape cells -- (40,c) and (41,c) are canvas -- and it excludes not one instance that `colored(above(above(?p)), 4)` had not already excluded. It therefore has ZERO discriminating witnesses and constraint 3 keeps it out: a conjunct that explains no pixel does not earn a line. I am recording the confound rather than burying it, because the two guards differ on cells no frame has shown: after key(1) redraws the widget area, an Ink1 or Ink2 instance could land somewhere with canvas two above and something else two below, and there the one-atom guard fires and the two-atom guard does not. THE PROBE IS THE SAME PRESS I ALREADY WANT: expose the other configuration, then press key(3) in it. If twelve cells hide, the guard survives; if more than twelve hide, the second atom was load-bearing and goes back in. I have been burned before by deleting an unearned atom, and the lesson I took was not `never delete` -- it was `delete, and name the press that will answer you`."
    [depends: tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem tape1_has_never_been_shown "TAPE1, rows 32-33 cols 17-22, renders colour 4 in every one of the six observed frames, and yet all twelve of its cells are in zero_space's dynamic list. Both statements can only be true if TAPE1 was non-4 in some frame I was not shown at cell level -- which is s1, the A1 configuration. That is independent corroboration of the reading: the t1 diff's before-colour set contains 4, and the only dynamic cells rendering 4 in s0 are exactly these twelve. So A1 shows tape1 and hides or changes tape2, and A2 puts it back. It also says something about key(3), key(4) and key(7): all three touched only tape2, never tape1, in three transitions. Either those keys address the second list row specifically, or they address `the shown tape` and tape1 was already hidden. I cannot separate those two readings from here and I will not pretend to; one press of key(4) after the A1 press separates them, because it would act on tape1 under the first reading and on tape2 under the second."
    [depends: the_ninety_six_cell_transition_is_the_hole_and_here_is_its_price, tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem the_meter_pixel_has_one_witness_and_three_live_readings "(53,63) went 2 to 3 at t4 and at no other command. It sits at the right end of row 53, a row that renders 2 across the whole window and is otherwise constant, above row 54 which renders 4 across the whole window -- a status bar at the bottom of the screen with one cell consumed at its right edge. THREE READINGS FIT ONE WITNESS EQUALLY WELL. (A) key(4) advances it: 1/1, and it is what I wrote, because it is the only reading the guard language can express at all. (B) SHOWING the tape advances it, whatever key does the showing: also 1/1, and t4 is the only reveal in history. (C) it counts something else entirely -- a score, a move budget, a level timer -- that happened to tick once. WHAT KILLS THE READING THE PREVIOUS LEVEL TAUGHT ME: command-index parity predicted burns at indices 2 and 4 and only index 4 burned, so parity is REFUTED here and I do not carry it over. THE SEPARATOR IS ONE COMMAND AND I NAME ITS PREDICTION. The tape is hidden now and the meter renders 3, so my rule cannot fire; press key(4) and my manual predicts exactly 12 cells and no meter change. If the meter advances anyway, reading A is a counter rather than a one-shot and the guard `colored(?p, 2)` is wrong; if it does not, I have a negative witness where I currently have none."
    [depends: tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem three_and_seven_are_the_same_key_so_far_and_i_wrote_them_twice "key(3) at t3 and key(7) at t5 produced identical 12-cell effects, each from a state in which the tape was shown. I have one witness apiece and no state in which they differ. THE GRAMMAR HAS NO `or`, so `act=key(3) or act=key(7)` cannot be written and I paid four rules where two would do -- a doubling I am declaring rather than hiding, and the honest reason is expressiveness, not evidence. TWO THINGS ARE NOT THE SAME ABOUT THEM. key(7) returned ONE frame; key(1), key(2), key(3) and key(4) each returned TWO. cascade_lengths is [1,2] and max_frames_in_one_command is 2, so key(7) is the only single-frame command in this world's history. That is a free channel my semantics discards by construction -- cascade single_frame compares only the net -- and it is the only evidence that 3 and 7 are different mechanisms with a coinciding net effect. THE SEPARATOR: press one of them when the tape is already HIDDEN. If it is `hide`, nothing happens; if it is `toggle`, twelve cells show. Two presses separate hide from toggle for both keys, and my manual currently predicts nothing for either in that state -- an unwitnessed silence, which is the shape of claim this world has punished before."
    [depends: tape2_is_hidden_and_shown_and_the_guard_that_isolates_it  probe: pending]

  theorem silence_is_a_prediction_and_almost_all_of_mine_are_forged "The compiled step is total: where no rule fires the successor equals the current state, so my manual never says `I do not know`, it says `nothing happens`. Audit what it now claims from the current state s5, in which tape2 is hidden and the meter reads 3. key(1): predicted silent, KNOWN FALSE, 96 cells, declared. key(2): predicted silent, KNOWN FALSE, 96 cells, declared. key(3): predicted silent -- the hide rules need colour 1 or 2 and the tape renders 4 -- NO WITNESS, this is exactly the hide-versus-toggle question. key(7): same, NO WITNESS. key(4): predicted 12 cells shown and no meter change, and the meter half of that has NO WITNESS. key(5) and key(6): NEVER PRESSED IN THIS WORLD, predicted silent, no witness of any kind. So of seven keys, my manual has an honest witnessed prediction for none of them in this state, two known-false silences it has priced, and five untested claims. That is what six commands buys and I would rather post the number than dress it up."
    [depends: the_ninety_six_cell_transition_is_the_hole_and_here_is_its_price, three_and_seven_are_the_same_key_so_far_and_i_wrote_them_twice  probe: pending]

  theorem two_keys_have_never_been_pressed_and_one_of_them_is_probably_a_pointer "actions_used is A1 A2 A3 A4 A7 plus RESET; the alphabet is ACTION1..ACTION7. key(5) and key(6) are entirely unconstrained after six states. In this action family one command conventionally carries coordinates -- a click -- and that is a prior about the family, not evidence about this world; note that ACTION7 was used here and ACTION6 was not, which is mild evidence that the usual numbering does not hold. IT MATTERS BECAUSE OF WHAT THIS BOARD LOOKS LIKE: two icons, two value tapes, a scrollbar-shaped 2-wide colour-3 track at cols 13-14 with a colour-2 segment at rows 32-33, a large colour-4 canvas, a 4x4 colour-14 block at rows 31-34 cols 42-45 that has never changed, and a status bar. That is the anatomy of a MENU, and menus are usually pointed at. I CANNOT WRITE A CLICK RULE: the guard language admits act=key(6) but has nowhere to put two coordinates, so such a rule would fire on every click anywhere and be silently wrong about which cell was clicked. If a pointer drives this world my manual can record its EFFECT and never its precondition."
    [probe: pending]

  theorem what_the_current_frame_shows_outside_the_dynamic_set "Everything here is board and none of it earns an object, but a future desk will want it written down because the window hides it the moment it stops mattering. Cols 10-12 and 15-16 of rows 29 and above render background 5. Cols 13-14 render 3 at rows 29,30,31,34,35 and 2 at rows 32,33 -- a two-wide vertical track with a two-row segment in it, and row 29's pair is CONSTANT while rows 30-35 are dynamic, so the track extends above the window and only the part inside icon1 varies. The canvas is colour 4 filling rows 29-41 cols 17-46, with a 4x4 colour-14 block at rows 31-34 cols 42-45 that has not changed in six frames. Col 47 and beyond in rows 29-41 is background 5. Rows 42-52 are background 5 across the window. Row 53 is colour 2 across the window except (53,63); row 54 is colour 4 across the window. I HAVE NEVER SEEN rows 0-28 or rows 55-63, at any column, because the display only shows cells that have ever changed -- colours 8 and 9 appear in colours_seen and I cannot point at a single cell that holds them. That is a gap in my knowledge and not in the manual: those cells are constant, so board owns them, and no rule of mine references them."
    [probe: passed]

  theorem what_the_engines_gave_me "zero_space is the round's one useful engine and it gave me the census, not a law: its single global law enumerates exactly the 97 dynamic cells and that enumeration is what turned my four-rectangle reading from a guess into an arithmetic identity. Its own verdict on its laws is THIN in its own words -- 5 transitions constrain rank 3 of 679 features, null space dimension 676, nearly every vector in it true over these states and unfalsified rather than confirmed -- so I took the cell list and left the law. mdl_segmenter I REJECT WHOLESALE and its own numbers are why: both variants have NEGATIVE gain, -4037 bits at split_by_color=false and -10409 at true, so by its own measure its segmentation loses to writing the pixels out. Its tracks say what is wrong with connected_components(4) here: obj0 (frame 0), obj2 (frame 1), obj3 (frames 2-5) are all ~440-cell 13x36 blobs, which is one blob -- the canvas with the widgets embedded in it -- being re-identified as a new object every time any pixel inside it changes; obj1 is the 2x54 bottom bar. Four-connectivity cannot separate a widget from a canvas it is drawn on, and THAT ABSENCE IS THE FINDING. cegis_miner refused every track and its verdict, `the world does not narrate as one mover`, is TRUE here and not merely an artefact: nothing in six frames moved, everything recoloured in place."
    [probe: passed]

  theorem the_dsl_cannot_say_unknown_and_cannot_say_or "Two expressive holes, both paid for in this manual. FIRST: there is no third outcome for a (state, action) pair -- not `no change`, not a named successor, but `unobserved, the manual declines to predict`. So my complete ignorance of key(1) is emitted in the same voice as my three-times-witnessed knowledge of key(3), and only this prose distinguishes them. SECOND: guards join with `and` only. key(3) and key(7) have identical observed effects and I cannot write one rule for both, so six rules do the work of three and the manual is longer than the world. I record both rather than working around them, because a workaround here means inventing a distinction the evidence does not support. If a future desk gains one extension, ask for `or` before asking for anything else -- it is the one that would shorten this manual today."
    [depends: three_and_seven_are_the_same_key_so_far_and_i_wrote_them_twice  probe: passed]

  theorem there_is_no_goal_section_and_that_is_deliberate "No frame has ever reported anything but NOT_FINISHED and nothing in six states resembles a win. The candidates all fail and I would rather have no goal than a goal true in the wrong states, which stops a planner at its first step. `count(Ink2, color = 3) = 1` is true right now, in a state that is plainly not a win. `count(Ink4) = 0` is false at RESET and stays false forever, since instances are fixed by the arm. A goal over the meter would need me to know what the meter counts, and I have one witness and three readings for it. There is also a structural reason nothing can be named: `arc-instances: all` gives me Ink2_r53c63 and nine siblings, so there is no single instance to write `X.pos = exit_cell` about, and I have declared no landmarks at all after the compile failure. I name the price plainly: is_goal compiles to False, no plan terminates, and nothing ranks one command above another except what the playbook says -- which is why the playbook is about buying pixels rather than about reaching anything."
    [depends: the_census_closes_to_the_pixel_and_that_is_why_seven_types, two_keys_have_never_been_pressed_and_one_of_them_is_probably_a_pointer  probe: passed]

  theorem what_i_predict_before_i_see_it "Written in advance so it can cost me. State s5: tape2 hidden (rows 38-39 cols 17-22 all render 4), meter (53,63) renders 3, tape1 hidden, both icons in configuration s0. key(1): my manual predicts ZERO cells and the truth is 96 -- the largest wrong prediction in it, made on purpose, and the press I want, because it converts a summarised diff into a readable frame. key(2): the same 96-cell hole with nothing new bought, since A2 from here is not the A2 I have a witness for. key(3): my manual predicts ZERO and has NO witness -- if twelve cells appear, key(3) is a toggle and my four hide rules need their converses; if nothing happens, key(3) is `hide` and I gain a negative witness I currently lack. key(7): the identical experiment, and it additionally tests the one-frame-versus-two-frame difference. key(4): my manual predicts EXACTLY TWELVE cells shown and NO meter change; twelve-plus-one refutes `colored(?p, 2)` in the meter rule and tells me the meter counts rather than fires once. key(5), key(6): predicted silent, never pressed, and if either moves a pixel this manual learns a whole action. If key(1) is pressed and the 96 cells land where I cannot see them, that is not a refutation of anything I claimed -- read it by its divergence set."
    [depends: the_cheapest_command_on_this_board, the_meter_pixel_has_one_witness_and_three_live_readings  probe: pending]

  theorem a_manual_that_does_not_compile_predicts_nothing_at_all "The lesson of the surprise, kept because it is worth more than any rule above. The previous manual was thirty theorems long, replayed twenty-five transitions in earlier rounds and had a carefully argued account of its own defects -- and this round it scored NOTHING, because theory.py could not be loaded. Responsibility: empty. Replay: empty. Unambiguous: null. A manual that does not compile is not a slightly worse manual, it is no manual, and every hour of reasoning inside it is unbanked. TWO CONCRETE RULES FALL OUT. First, prefer constructs that cannot fail to be placed: this manual has no landmarks, no goal section and no domain, and every discrimination is a colour test on a cell reachable by above/below/leftof/rightof from an instance. Second, when a section is optional, OMIT IT rather than emit it empty -- an empty `goal:` header was legal-looking and may well have been the fault. Small and running beats large and dark, and this manual is deliberately the former."
    [probe: passed]
