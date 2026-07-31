# theory.dsl -- world observed for 9 commands (RESET + ACTION1..ACTION5,
# ACTION1..ACTION4). 75 cells have ever changed; this manual names all 75 and
# owns the 72 that any colour-keyed object can own.
#
# WHAT CHANGED THIS ROUND, AND WHY:
#
#   1. THE PARSE ERROR IS FIXED, AND IT WAS NOT WHAT I FEARED. The compiler
#      said "Line 65: Expected 'goal' statement, got: laws:". Line 65 is the
#      `laws:` header; the `goal:` section above it contained comment lines and
#      no statement, and a section header demands at least one statement. The
#      spec says "No goal section at all is legal", so the section is DELETED
#      rather than filled with a goal I do not believe. See
#      the_goal_section_is_absent_on_purpose.
#
#   2. THE BET OF LAST ROUND IS WON. Six-deep nested cell terms PARSE. The
#      proof is the error message itself: the parser reached line 65, and the
#      four movement rules are lines 44-53. So `below(below(...))` is legal
#      cell syntax in this grammar and the manual may speak about distance six
#      without inventing one landmark per lattice cell. That is the single
#      most valuable fact I learned this round and it is now a settled part of
#      the language, not a gamble.
#
#   3. THE REPLAY DIVERGENCE IS ANSWERED, NOT PATCHED. certify replayed the
#      LAST COMPILED manual -- the move-less one -- and it lost 24 cells at
#      the first ACTION2, saying 5 where the world said 9 over rows 14-18,
#      cols 14-18 minus (16,16). That is exactly the footprint of a body that
#      arrived and was never drawn. The two key2 rules in this manual draw
#      those 24 cells and erase the 24 they came from, so the divergence
#      should close to zero on t2 and on t7 without a single new concept. If
#      it does not close, the fault is in `colored` or in instance typing and
#      not in the physics, and I will know which from the cells that remain.
#
#   4. A NEW STRUCTURAL LIMIT IS NAMED: instances live only where pixels have
#      already moved. See only_visited_cells_have_instances. It changes the
#      price of the next descent from 24 wrong cells to 48, and I would rather
#      pay a known 48 than hide it.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark spawn_center    # arc-cell: (10, 16)
  landmark socket_center   # arc-cell: (52, 46)
  landmark gate_center     # arc-cell: (40, 16)
  landmark knob_center     # arc-cell: (10, 40)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t9 compress: 39]
  Vacated [segment: dynamic_colour_5 ev: t2,t5,t7 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t9 compress: 9]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2,t7 cov: 48/48]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2,t7 cov: 48/48]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

laws:
  invariant nine_count_frame0 count(Glyph9) = 39 [status: counted]
  invariant five_count_frame0 count(Vacated) = 24 [status: counted]
  invariant one_count_frame0 count(Spent) = 9 [status: counted]
  invariant board_static count(board) = 4021 [status: counted]

  theorem the_goal_section_is_absent_on_purpose "The previous manual carried a `goal:` header whose body was two comment lines, and the compiler refused it at the next section header. A section must contain a statement. I did not fill it, because the only goals this grammar can state are false: `Cart.pos = exit_cell` needs a single named instance and `arc-instances: all` gives me Glyph9_r8c14 and 38 siblings instead; `count(Vacated, color = 9) = 24` is true of the body standing ANYWHERE off spawn, which is most of the maze and not a win. A goal that is true in the wrong states is worse than no goal, because the planner would stop at the first one. So the section is gone, is_goal is False, and the playbook steers by lattice distance instead. This is a language limit I am recording in the open, not a belief I am hiding."
    [probe: pending]

  theorem nested_cell_terms_parse "SETTLED, and settled by the compiler. Last round I spent the manual on the guess that `below(below(x))` is legal, and said that if it was not, nothing would compile. The compiler's only complaint was at line 65, the `laws:` header; the movement rules are lines 44-53 and it walked past them. A recursive-descent parser that rejected nested cell terms would have died there, not thirteen lines later. Therefore this grammar can express distance six, one line of guard draws 24 pixels, and the fallback I dreaded -- one landmark per lattice cell, which is coordinates in disguise and generalises to nothing -- is off the table permanently."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem the_replay_divergence_and_what_i_did_about_it "certify replayed the move-less manual and diverged at the first ACTION2, 24 cells, manual 5 versus world 9 across rows 14-18 cols 14-18 minus (16,16). Those 24 cells ARE the body's arrival footprint, and the old manual had no rule that could draw an arrival. I have answered it with physics rather than with a patch: key2_body_arrives recolours exactly those 24 cells to 9 and key2_body_leaves clears the 24 they left. I make the prediction sharp so it can be scored -- after this manual compiles, t2 and t7 must each replay with ZERO cells wrong except (63,63) at t2, which is the meter and which I have deliberately left undrawn. Any other residue at t2 or t7 refutes my reading of `colored`, of instance typing, or of both, and the identity of the residual cells says which."
    [depends: key2_body_leaves, key2_body_arrives  probe: pending]

  theorem only_visited_cells_have_instances "New this round, and it changes what my manual can promise. `arc-instances: all` creates one instance per cell of that colour THE BOARD CANNOT EXPLAIN, and board is the never-varying cells. The arm reports 72 cells_needing_an_owner and 0 unexplained, and 72 is exactly my dynamic census minus the three cells no colour can own -- so the instance set is the cells that have already changed, not every cell of that colour. Consequence: the corridor ahead, rows 20-24 cols 14-18, is constant floor so far and therefore has NO Vacated instances, so key2_body_arrives cannot ground there however true it is. The next ACTION2 will cost me 48 wrong cells -- 24 for a body I still draw at rows 14-18 and 24 for one I cannot draw at rows 20-24 -- and only 24 of those are the missing-rule debt below. The round after, those cells will be dynamic, instances will exist, and the same unchanged rule will draw them. I am not confident enough to call this proven: it is an inference from the arm's own 72, and the cheapest test is the next descent, whose residue will be 48 cells if I am right and 24 if instances exist everywhere."
    [depends: key2_body_arrives  probe: pending]

  theorem the_body_is_a_ring_on_a_six_pixel_lattice "The mover is a 5x5 hollow ring of colour 9 whose top-left sits at (6R+2, 6C+2), hole at (6R+4, 6C+4). Seen at (R,C) = (1,2), rows 8-12, and (2,2), rows 14-18; one command displaces it exactly six pixels. The maze agrees six is the module: void columns run 20-24 and 32-36 with single floor columns at 19, 25, 31, and the socket interior is rows 50-54 cols 44-48, which is lattice (8,7). Spawn is lattice (1,2). The corridor at column-lattice 2 is floor at R=1..5 and R=7..8 and carries the colour-8 comb at R=6."
    [depends: key2_body_leaves, key2_body_arrives  probe: pending]

  theorem dynamic_census "Exactly 75 cells have ever changed. 23 are the status panel at rows 1-5 cols 1-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus its hole (10,16), which never changes and is therefore board. 24 are the same shape six pixels down, rows 14-18 cols 14-18 minus its hole (16,16). 4 are the right end of the row-63 bar, cols 60-63. 23+24+24+4 = 75 and nothing is left over. At frame 0 they split as 39 colour-9 (8 panel ring + 3 panel underline + 24 spawn ring + 4 meter), 9 colour-1 (the solid slot-2 block), 24 colour-5 (the lower ring's footprint) and 3 background ((5,5),(5,6),(5,7)); 39+9+24 = 72, exactly the arm's cells_needing_an_owner."
    [probe: pending]

  theorem the_two_key2_rules_i_am_still_not_allowed_to_write "The arm types cells by their frame-0 colour, so the body changes type as it walks: the ring at rows 8-12 is Glyph9, at rows 14-18 it is Vacated. Every movement law therefore needs four rules, and for ACTION2 I hold witnesses for only two. The missing pair, verbatim so the next desk can paste them: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)' and 'rule key2_body_arrives_at_nine forall ?p in Glyph9 when act=key(2) and colored(?p, 5) and colored(above(above(above(above(above(above(?p)))))), 9) then recolored(?p, 9)'. I have checked both for spurious grounding and both are inert everywhere except the intended cells, so the temptation to write them now is real. I refuse anyway, on rule 2: they have never fired in an observed transition, and the identical-looking pair I wrote last round on one observation each -- the meter rules -- were both refuted within two commands. One consecutive ACTION2 buys both, and the playbook prefers it."
    [depends: key2_body_leaves, key2_body_arrives  probe: pending]

  theorem the_action_map "ACTION2 is down: proven twice, t2 and t7, six pixels each. The rest is the unique assignment consistent with every observation. ACTION1 did nothing at t1 and t6, both from rows 8-12, where six above is rows 2-6, off the floor. ACTION3 did nothing at t3 and t8, both from rows 14-18, where six left is cols 8-12, void. ACTION4 did nothing at t4 and t9, both from rows 14-18, where six right is cols 20-24, void. So 1=up, 3=left, 4=right all fit as blocked moves and no other assignment explains all six no-ops. ACTION5 is respawn: it alone has ever touched the panel. The separator is free and available RIGHT NOW: the body sits at lattice (2,2) and the cell above it, rows 8-12, is floor, so ACTION1 here must move the body up six pixels if 1=up and must do nothing if it is anything else. It is also the one probe whose entire outcome lands on cells that already have instances, so my manual could be scored on it exactly -- if I had a key1 rule, which I do not, so it costs 48 wrong cells to buy the fact."
    [depends: key2_body_leaves, key5_body_respawns  probe: pending]

  theorem the_meter_is_a_clock_and_the_dsl_has_no_counter "Row 63 is a 64-cell colour-9 bar losing its rightmost live cell to colour 1. Burns: t2 (63,63), t4 (63,62), t6 (63,61), t8 (63,60). No burns: t1, t3, t5, t7, t9. That is every even-numbered command and no odd one, and it cuts clean across the actions -- ACTION2 burned at t2 and not t7, ACTION4 burned at t4 and not t9, ACTION1 burned at t6 but not t1, ACTION3 burned at t8 but not t3. I also tested it against internal time, since commands return 1, 7 or 9 frames: cumulative frames at the burns are 8, 10, 20, 30, which is a clean period of ten for the last three and not for the first, so I do not claim it. Either reading needs a counter over commands and the guard language has no state that is not a cell. I write NO meter rule, which predicts 'the bar never burns' and is wrong by one cell on four of nine transitions. The alternative, 'burn every command', is wrong by one cell on five of nine AND empties a 64-cell budget twice too fast for any planning that reads the bar as a budget."
    [probe: pending]

  theorem the_meter_rules_i_withdrew "The manual before last carried meter_burn_key2 and meter_burn_key4 on one observation each. t7 refuted the first (an ACTION2 with no burn), t9 the second (an ACTION4 with no burn); worse, meter_burn_key4's guard 'right neighbour already spent' now grounds on (63,59) and would invent a fifth burn. The lesson is recorded because I nearly repeated it this round: one observation per action is not evidence for a rule keyed on the action when a clock explains the same pixels."
    [probe: pending]

  theorem the_panel_debt_i_am_choosing_to_carry "The panel is two 3x3 icon slots at rows 1-3 cols 1-3 and cols 5-7, each with a 1x3 underline at row 5. Frames 0-4: slot 1 a hollow colour-9 ring, underline lit; slot 2 a solid colour-1 block, underline dark. Frame 5 on: slot 1 a hollow colour-2 ring, underline dark; slot 2 a hollow colour-9 ring, underline lit. I read it as two lives, lit underline marking the live one, colour 2 marking a spent one. I write no rule and every ACTION5 costs me 23 wrong cells. The reason is rules 3 and 5, not laziness: (1,2) and (5,2) have byte-identical four-neighbourhoods so no guard separates the slot-1 ring from its underline, and separating the slot-2 ring from its centre needs a disjunction this grammar does not have, so the honest encoding is four rules that all fire on a corner cell -- exactly the ambiguity rule 5 forbids. 23 wrong cells on a command I intend never to press again is the cheaper error."
    [probe: pending]

  theorem three_cells_no_object_can_ever_own "(5,5), (5,6), (5,7) are background at frame 0 and colour 9 from frame 5, so no colour-keyed object owns them and none can: an arc-colour 0 object would claim three thousand background cells. Any future panel rule has a floor of 3 wrong cells. This is exactly the gap between the arm's 75 dynamic cells and its 72 cells_needing_an_owner, and it is structural."
    [probe: pending]

  theorem key5_is_respawn_and_i_have_written_it_as_respawn "key5_body_clears and key5_body_respawns say: on ACTION5 any floor cell that is body-coloured returns to floor and the spawn ring lights up. That is respawn-from-anywhere and it fits t5 exactly, 24/24 on both halves. I checked key5_body_respawns for spurious grounding: the only Glyph9 instances that ever render 5 are the spawn ring's, since panel cells render 9, 2 or 0 and meter cells render 9 or 1. The rival reading, 'ACTION5 is up', fits t5 equally well because the body happened to be one lattice cell below spawn. I chose respawn because ACTION5 alone has touched the panel and because 1-4 already exhaust the directions. Separator: press ACTION5 from a cell that is NOT one lattice cell below spawn. Land at spawn, respawn; move up one, my two rules are wrong and become an up-rule. It costs a life, so it waits behind every free probe."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem the_socket_is_the_conjectured_lock "Rows 49-55, cols 43-49 hold a static colour-9 outline, open on the left at col 43 for rows 50-54, with a single dot at its centre (52,46). Its interior, rows 50-54 cols 44-48, is lattice (8,7), and the body is a 5x5 ring whose hole is its centre -- so a body parked there puts the dot exactly in the hole and covers not one pixel of it. That is a lock and a key and it is the only shape in the frame that fits the body. It also means the win leaves NO colour signature I can test: the 24 arriving cells go 5 to 9 like any other move and the dot never changes. Route, in lattice steps: down column-lattice 2 from (2,2) to (8,2), then right five to (8,7); row band 50-54 is unbroken floor from col 13 to col 48."
    [probe: pending]

  theorem the_only_route_down_and_the_gate_across_it "Cols 14-18 is the sole corridor from spawn to the bottom room; floor at lattice rows R=1..5 and R=7..8, blocked at R=6 by a five-toothed colour-8 comb filling rows 38-42 cols 14-18. A colour-8 cable leaves the comb along row 40, runs right to col 40 and up col 40 to a 3x3 colour-8 knob at rows 9-11 cols 39-41, lattice (1,6), the same lattice row as spawn. So the comb is plausibly a gate and the knob plausibly its switch. No colour-8 cell has changed in nine commands, which is why 8 is board and not an object. My rules make this falsifiable: key2_body_arrives needs the destination to render 5 and the comb renders 8, so my manual says the body stops at R=5. If it walks through, the gate is open and I learn it in one command."
    [depends: key2_body_arrives  probe: pending]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants (-4457 and -22984 bits), so its own segmentation loses to writing the pixels out and I owe it nothing; its obj3 is a 1006-cell colour-null blob that swallowed the maze floor, which is not an object but is a fair description of my `board`. obj0, obj2 and obj4 are colour-9 fragments already inside Glyph9; obj5 is the colour-2 panel ring, which is Glyph9 cells after a recolour and gets no type of its own -- a second type on the same pixels would invite the double claim rule 5 forbids. zero_space self-reports THIN (9 transitions constrain rank 6 of 375 features, null space dimension 369) and its one global law restates my 75-cell census. cegis_miner's refusal is the most useful sentence any engine produced: 'no track satisfies the precondition of exactly one move event per transition; the world does not narrate as one mover.' That is true of the ARM and false of the world. The world has exactly one mover, a 24-cell rigid ring; the arm can only see 24 simultaneous recolours, which is why my movement law needs four rules instead of one moved() event."
    [probe: pending]
