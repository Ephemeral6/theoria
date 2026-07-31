# theory.dsl -- world re-observed for 6 states / 5 transitions (RESET +
# ACTION1..ACTION5). 73 cells have ever changed; this manual names all 73 and
# owns the 70 that any colour-keyed object can own.
#
# WHAT CHANGED THIS ROUND, AND IT IS MOSTLY THE INSTRUMENT, NOT THE WORLD:
#
#   1. THE OBSERVATION WINDOW SHRANK. The manual I inherited was written from
#      10 states (t0..t9). The store now reports states=6, steps=6,
#      dynamic_cells=73, cells_needing_an_owner=70. Those are exactly the
#      first six states of the same run: same spawn, same descent at t2, same
#      respawn at t5, and the meter bar has lost two cells instead of four. So
#      four transitions I once observed are no longer in the window and cannot
#      be re-checked by certify. Every count in this manual is re-derived from
#      the six frames I can see; every claim that rests on a transition I can
#      no longer see is labelled as such, in the theorem that uses it.
#      See the_window_shrank_and_two_of_my_theorems_now_rest_on_memory.
#
#   2. THE SURPRISE IS THE ONE CELL I DECLARED UNPREDICTABLE. replay diverges
#      at t=1, ACTION2, cells_wrong = 1, cell (63,63), manual 9 world 1. That
#      is the meter, and it is the only divergence: the 48 body pixels of the
#      descent are drawn right. The manual's physics is intact.
#
#   3. AND THE SHRUNK WINDOW HANDS ME A CHEAP LIE. In these five transitions
#      each action appears exactly once, so "the bar burns iff the action is
#      ACTION2 or ACTION4" fits 5/5, is writable in this grammar, and would
#      lift replay from 1/5 to 4/5. I refuse it, I show the arithmetic of what
#      I am refusing, and I convert the refusal into a scheduled test that the
#      very next command settles. See
#      the_meter_is_a_hidden_parity_and_the_short_window_tempts_me_to_lie.
#
#   4. I READ THE SOCKET AND IT IS A KEYHOLE. Rows 49-55, cols 43-49 are a 7x7
#      colour-9 bracket, open on the left, with ONE colour-9 pip at (52,46).
#      The body is a 5x5 ring with a one-pixel hole at its centre. Stand the
#      body in lattice (8,7) -- rows 50-54, cols 44-48 -- and its hole lands
#      exactly on (52,46). The pip is what shows through the hole. That is the
#      winning position, named to the pixel, and it is still not writable as a
#      `goal:` for reasons I give in the_goal_section_is_absent_on_purpose.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark spawn_center   # arc-cell: (10, 16)
  landmark knob_center    # arc-cell: (10, 40)
  landmark gate_center    # arc-cell: (40, 16)
  landmark socket_center  # arc-cell: (52, 46)
  domain dir { up, down, left, right }
  Glyph9  [segment: dynamic_colour_9 ev: t0-t5 compress: 37]
  Vacated [segment: dynamic_colour_5 ev: t2,t5 compress: 24]
  Spent   [segment: dynamic_colour_1 ev: t0-t5 compress: 9]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule key2_body_leaves forall ?p in Glyph9 [ev: t2 cov: 24/24]
    when act=key(2) and colored(?p, 9) and colored(below(below(below(below(below(below(?p)))))), 5) then recolored(?p, 5)

  rule key2_body_arrives forall ?v in Vacated [ev: t2 cov: 24/24]
    when act=key(2) and colored(?v, 5) and colored(above(above(above(above(above(above(?v)))))), 9) then recolored(?v, 9)

  rule key5_body_clears forall ?v in Vacated [ev: t5 cov: 24/24]
    when act=key(5) and colored(?v, 9) then recolored(?v, 5)

  rule key5_body_respawns forall ?p in Glyph9 [ev: t5 cov: 24/24]
    when act=key(5) and colored(?p, 5) and colored(above(?p), 5) then recolored(?p, 9)

laws:
  invariant nine_count_this_build count(Glyph9) = 37 [status: counted]
  invariant five_count_this_build count(Vacated) = 24 [status: counted]
  invariant one_count_this_build count(Spent) = 9 [status: counted]
  invariant board_static_this_build count(board) = 4023 [status: counted]

  theorem the_descent_replays_to_the_pixel_and_that_is_the_whole_physics_bill "certify's first divergence is t=1, ACTION2, cells_wrong 1, cell (63,63), manual 9 world 1. Nothing else. The descent moves 49 cells and 48 of them are the body; all 48 are drawn correctly by two rules whose whole content is a distance-six recolour pair. So: a rigid 24-pixel mover on this arm is correctly encoded as source-cells-recolour-to-floor plus destination-cells-recolour-to-body, `colored(?p, 9)` reads the CURRENTLY RENDERED colour and not the frame-0 colour that typed the instance, and both guards are inert on the panel, on the meter and on every floor cell the body is not standing on -- I re-checked each class by hand against this frame. This part of the manual is finished and I changed not one character of it."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem the_window_shrank_and_two_of_my_theorems_now_rest_on_memory "The store reports 6 states where the manual I inherited worked from 10, and the six are the same six: RESET, a no-op, the descent, two no-ops, the respawn. Consequences I must state plainly. (a) Every count is re-derived here from the six visible frames: 23 panel cells + 24 spawn-ring cells + 24 lower-ring cells + 2 meter cells = 73 = dynamic_cells, and 73 - 3 background-at-frame-0 cells = 70 = cells_needing_an_owner. (b) The key2 pair is now witnessed by ONE descent, not two, so its coverage tags read 24/24 at t2 and not 48/48; the rule text did not need to change, which is itself the evidence that the second descent was not carrying it. (c) Two things I believe are now UNCHECKABLE by certify because the transitions that witness them are outside the window: that ACTION1 burned the meter at the old t6 and ACTION3 burned it at the old t8, and that ACTION2 at the old t7 and ACTION4 at the old t9 did NOT burn. I carry those as recorded observation, not as anything this round can re-derive, and I name exactly where they are load-bearing rather than letting them hide."
    [probe: passed]

  theorem replay_accumulates_and_the_count_now_proves_it_one_against_two "certify says 1/5. Count what my manual predicts under the rival reading, where replay re-seeds from the world frame before each command: t1 is a world no-op and no rule of mine fires, so it matches; t3 is a world no-op and no rule fires, so it matches; t2, t4 and t5 all miss (meter, meter, panel). That is 2, and 2 is not 1. Under accumulation: t1 matches, t2 diverges at (63,63), and from then on my carried state differs from the world's at that cell forever, so t3, t4, t5 all miss whatever else I get right. That is exactly 1. So replay carries its own state forward and never re-seeds -- last round the same argument gave 4-against-1 on nine transitions and this round it gives 2-against-1 on five, from an independent count. Operationally: while the meter burns unpredicted, `matched` cannot exceed 1 and `first_divergence` cannot move past t=1, no matter how much of the manual is right. I score myself on the responsibility check (0 unexplained) and on reading the command diffs by hand."
    [probe: passed]

  theorem the_meter_is_a_hidden_parity_and_the_short_window_tempts_me_to_lie "Row 63 is a 64-cell colour-9 bar losing its rightmost live cell to colour 1, right to left. In this window: burn at t2 (63,63), burn at t4 (63,62), no burn at t1, t3, t5. HERE IS THE TEMPTATION, priced honestly. In five transitions each of ACTION1..ACTION5 occurs exactly once, so 'burns iff act is key(2) or key(4)' fits 5/5, and it is writable: `when act=key(2) and colored(?p, 9) and rightof(?p) = wall then recolored(?p, 1)` picks (63,63) and only it, and `when act=key(4) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)` picks (63,62) and only it, neither clashing with key2_body_leaves because that rule's below-six guard is off-board at row 63. Writing them takes replay from 1/5 to 4/5, since t5 would still lose 23 panel cells. I REFUSE, for two reasons and I want both on the record. First, one observation per action is not evidence for a law keyed on the action when a one-parameter clock explains the same pixels: cumulative frames returned, counting the reset frame, are 2, 9, 10, 11, 20 at the ends of t1..t5, and the bar burns exactly on the odd ones -- 9 and 11 burn, 2, 10 and 20 do not, 5 for 5, with no free parameter. Second, my own manual records a longer window in which ACTION2 did not burn and ACTION1 did, which kills action-keying outright; that record is now unverifiable here, which is precisely why I refuse to let a 4/5 score buy me a rule I have written down as refuted. And no drawn cell can carry the clock: the count of already-burned cells is 0 at t1 (no burn) and 0 at t2 (burn), 1 at t3 (no burn) and 1 at t4 (burn), so the meter's own visible state does not separate its own behaviour. cegis_miner hit the same wall from the other side -- 'no literal separates transition 1 from the positives'."
    [probe: passed]

  theorem the_next_command_settles_the_meter_and_i_am_writing_the_prediction_down_first "Cumulative frames now stand at 20, which is even, and every command this world has ever returned has had an odd frame count -- 1, 7 or 9. So the next command, whatever it is, lands on an odd cumulative count and BOTH parity readings (frames-odd, or command-index-even, which agree on t6) predict the bar burns its next cell, (63,61), 9 to 1. Action-keying predicts a burn only if that command is ACTION2 or ACTION4. Therefore ANY command other than those two is a free, decisive separator, and the cost is one meter tick out of the roughly 62 the bar still holds. If the next non-key-2, non-key-4 command burns (63,61), action-keying is dead and my refusal above was right. If it does NOT burn, the parity reading is dead, my recorded memory of the longer window is wrong, and the very next desk must write the two burn rules quoted above verbatim. That is what makes the refusal a test rather than an omission."
    [depends: the_meter_is_a_hidden_parity_and_the_short_window_tempts_me_to_lie  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice_and_i_re_read_every_span_this_round "Lattice cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; the separator strips are the rows and cols congruent to 1 mod 6. Colour 5 is floor, colour 0 is void, colour 8 is the machine, and the body is a rigid 5x5 block of colour 9 with a one-cell floor hole at its centre, so a cell is enterable only if all 25 of its pixels render floor. Re-read from the current frame, span by span: R=1 (rows 8-12) is floor from col 13 to col 43 except the knob, so C=2,3,4,5 are enterable, C=6 holds the knob and C=7 is void; R=2 (rows 14-18) is floor only at cols 13-19 and 25-31, so C=2 and C=4 only; R=3 (rows 20-24) is floor cols 13-31, so C=2,3,4; R=4 and R=5 (rows 26-36) are floor only at cols 13-19, so C=2; R=6 (rows 38-42) is the comb, and its only floor pixels are (39,14) and (41,14), so nothing is enterable there; R=7 (rows 44-48) is floor cols 13-19, so C=2; R=8 (rows 50-54) is floor from col 13 to col 48, so C=2 through C=7 including the socket interior. Separator rows 7, 13, 19, 25, 31, 37, 43, 49 are floor across column 2, and separator col 37 is floor across R=1, so column 2 is continuous from R=1 to R=8 apart from the comb and row R=1 is continuous from C=2 to C=6. That is the whole map, and it costs no concept beyond the lattice."
    [depends: key2_body_arrives  probe: pending]

  theorem the_socket_is_a_keyhole_and_the_pip_names_the_winning_position "New this round, and it is the best-paying pixel-reading I have done. Rows 49-55, cols 43-49 form a 7x7 colour-9 bracket: top bar row 49 cols 43-49, bottom bar row 55 cols 43-49, right wall col 49 rows 49-55, and the left side col 43 rows 50-54 is FLOOR, i.e. the bracket is open on the left. Inside it, one lone colour-9 pixel at (52,46) and nothing else. Now overlay the body: it is 5x5 with its hole at its own centre, and lattice (8,7) is rows 50-54 cols 44-48, whose centre is exactly (52,46). So a body standing in (8,7) has the bracket flush against it on three sides and the pip showing through its hole. This is a socket and a plug, drawn to the pixel, and it tells me the winning position without my having to guess a goal predicate: the game is won when the 24 ring pixels of rows 50-54 cols 44-48 render 9. The bracket has never changed in six frames, so it is board today and no object of mine owns it; the first time the body enters, those pixels become dynamic and the manual can finally speak about them."
    [depends: the_maze_is_a_six_pixel_lattice_and_i_re_read_every_span_this_round  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood the map from spawn (1,2) and the body reaches exactly eleven cells: (1,2), (1,3), (1,4), (1,5), (2,2), (2,4), (3,2), (3,3), (3,4), (4,2), (5,2). The socket interior (8,7) is not among them, and neither is anything in R=7 or R=8, because every route south crosses (6,2) and (6,2) renders colour 8 on 23 of its 25 pixels. So the comb is not an obstacle to route around; it is the door, and this game cannot be won without opening it. The wiring is drawn in the open: colour 8 leaves the comb along row 40, runs right from col 14 to col 40, climbs col 40 through rows 13 to 39, and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41, which sits inside lattice (1,6). Not one colour-8 pixel has moved in six frames, which is why 8 is board and not an object; the first colour-8 pixel that changes turns this theorem into physics and hands me a rule to write."
    [depends: the_maze_is_a_six_pixel_lattice_and_i_re_read_every_span_this_round  probe: pending]

  theorem the_knob_is_the_only_thing_the_body_can_touch_and_i_do_not_know_how_it_is_pressed "Of the eleven reachable cells, ten are bounded by floor and void alone. The eleventh, (1,5) at rows 8-12 cols 32-36, is separated from (1,6) only by separator col 37, which is floor. So the knob is the single interactive object within reach and pressing it is the only lever I can see. The geometry argues against the obvious reading: (1,6) contains ten colour-8 pixels -- nine knob and one cable at (12,40) -- while the body's hole is one pixel, so entering it would mean the body overlapping colour 8. Either 8 is walkable and key2_body_arrives, which demands the destination render 5, is wrong at the knob and at the comb; or the knob answers to proximity from (1,5); or it answers to an action I have never pressed. All three are cheap to tell apart and my rules make the first self-announcing: if the body enters a colour-8 cell, my manual predicts it stays put and the world will say otherwise, in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem the_action_map_after_five_transitions "Proven: ACTION2 is down, 24 pixels leaving rows 8-12 and 24 arriving at rows 14-18 at t2. Everything else is negative information and I will not overstate it. ACTION1 was a no-op at t1 from spawn (1,2), where up is void and left is void but RIGHT, (1,3), is open floor and DOWN, (2,2), is open floor -- so ACTION1 is neither right nor down, leaving up, left, or inert. ACTION3 and ACTION4 were no-ops at t3 and t4 from (2,2), where left and right are both void but UP, (1,2), was open floor at the time and DOWN, (3,2), is open floor -- so NEITHER ACTION3 NOR ACTION4 IS UP OR DOWN, leaving left, right, or inert. That last fact is what makes the cheapest probe in the game available from where the body stands right now: at spawn, up and left are void, down is excluded for ACTION3 and ACTION4 by the paragraph above, so RIGHT IS THE ONLY CANDIDATE DIRECTION EITHER OF THEM COULD EXPRESS. Press one at spawn and the outcome is unambiguous -- a six-pixel step east identifies the key that walks the body along R=1 toward the knob, and no movement retires that key to left-or-inert. The same command doubles as the meter separator of the previous theorem. ACTION5 is respawn and up remains unassigned among ACTION1, ACTION6, ACTION7."
    [depends: key2_body_leaves  probe: pending]

  theorem what_i_predict_for_that_probe_before_i_see_it "Written in advance so it can cost me. If the next command is ACTION3 or ACTION4 from spawn and it does NOT move the body, my manual predicts the frame is unchanged and the world will change one cell, (63,61), and replay will disagree with me on that one cell and no other. If it DOES move the body east, my manual has no right-hand rule and cols 20-24 have never been dynamic so they carry no instances: I predict 48 wrong cells, 24 at rows 8-12 cols 14-18 where I keep drawing a body that has left and 24 at rows 8-12 cols 20-24 where I cannot draw the body that arrived, plus the meter cell. Anything OTHER than 1 or 49 wrong cells refutes something I currently believe -- most likely my reading of the lattice or of which cells the arm has instanced -- and I would rather learn that from a counted diff than from a vague sense that the manual is drifting."
    [depends: the_action_map_after_five_transitions, only_visited_cells_have_instances  probe: pending]

  theorem two_actions_have_never_been_pressed "The store's actions_used is ACTION1..ACTION5 and RESET; this world's alphabet is ACTION1..ACTION7. So two commands exist that no observation constrains at all, and in this family one of them is normally a click carrying coordinates. That matters here specifically: the knob is a 3x3 target the body may be geometrically unable to stand on, and a click is exactly the shape of interaction that would press it. I cannot write such a rule. The guard language admits `act=key(6)` but has nowhere to put the two coordinates a click carries, so a click rule would be silently wrong about WHICH cell was clicked and would fire on every click anywhere. If a click drives this world, my manual can record its EFFECT -- comb pixels going 8 to 5 -- and never its precondition. I record the limit now rather than discovering it under pressure."
    [probe: pending]

  theorem the_panel_is_two_tokens_and_one_is_already_spent "Rows 1-3 cols 1-3 and rows 1-3 cols 5-7 are two 3x3 icons, each with a 1x3 underline at row 5. Frames 0 through 4: slot 1 is a hollow colour-9 ring with its underline lit colour 9, slot 2 is a solid colour-1 block with its underline dark. From frame 5: slot 1 is a hollow colour-2 ring with its underline dark, slot 2 is a hollow colour-9 ring with its underline lit. The icons are miniatures of the body -- a hollow square with a one-pixel hole -- so I read them as bodies: two tokens, the lit hollow 9 is the one in play, and colour 2 marks a token consumed. The only command that has ever touched the panel is ACTION5, and ACTION5 is respawn, so respawn spends a token and ONE TOKEN REMAINS. This, not the meter, is the binding budget: roughly 120 commands and one life. Every branch that can end in a respawn ranks below every branch that cannot."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem only_visited_cells_have_instances "Settled by arithmetic, and the shrunk window re-confirms it with different numbers, which is the strongest form of the check. The arm builds one instance per cell of the declared colour THAT THE BOARD CANNOT EXPLAIN, and board is the set of never-varying cells: constant_cells 4023 plus dynamic_cells 73 is 4096, and cells_needing_an_owner is 70, which is my 73 minus the three cells that render background at frame 0 and which no colour-keyed object can claim. 37 + 24 + 9 = 70 exactly. Last round the same identity held at 4021, 75, 72 and 39 + 24 + 9. So the instance set IS the set of cells that have already changed, and the corridor ahead carries no instances however much floor it shows. The consequence I have now priced twice: the first step into never-yet-changed ground costs 48 wrong cells, and the round after, those cells are dynamic, instances exist, and key2_body_arrives draws them with no change to its text. The manual heals itself one step behind the body, and I take the step anyway."
    [depends: key2_body_arrives  probe: passed]

  theorem the_instance_counts_are_build_relative_not_world_facts "The four invariants above are counted at THIS build and were different at the last one -- 39, 24, 9, 4021 then, 37, 24, 9, 4023 now, and the only thing that moved was two meter cells falling out of the observation window. They will change again the moment the body steps onto fresh floor. I state them because they are the arithmetic that proves only_visited_cells_have_instances, and I say here plainly that they are properties of what has been observed rather than laws of the world. No rule depends on them."
    [probe: passed]

  theorem dynamic_census "Exactly 73 cells have ever changed. 23 are the status panel: slot 1's eight ring pixels going 9 to 2, its three underline pixels going 9 to 0, slot 2's nine block pixels of which eight go 1 to 9 and the centre (2,6) goes 1 to 0, and its three underline pixels going 0 to 9. 24 are the spawn ring, rows 8-12 cols 14-18 minus the hole (10,16), which never changes and is therefore board. 24 are the same shape six rows down, rows 14-18 cols 14-18 minus its hole (16,16). 2 are the right end of the row-63 bar, (63,62) and (63,63). 23+24+24+2 = 73 and nothing is left over. zero_space independently lists 73 cells_used and its cell list ends with exactly those two meter cells. At frame 0 they split as 37 colour-9, 9 colour-1, 24 colour-5 and 3 background; 37+9+24 = 70 = cells_needing_an_owner, and the responsibility check reports 0 unexplained."
    [probe: passed]

  theorem three_cells_no_object_can_ever_own "(5,5), (5,6), (5,7) render background at frame 0 and colour 9 from frame 5, so no colour-keyed object owns them and none can: an arc-colour 0 object would claim three thousand background cells. Any future panel rule therefore has a floor of 3 wrong cells. This is exactly the gap between 73 dynamic cells and 70 cells_needing_an_owner, and it is structural, not an oversight."
    [probe: passed]

  theorem the_panel_debt_i_am_choosing_to_carry "I write no panel rule and every ACTION5 costs me 23 wrong cells. The reason is rules 3 and 5, not laziness: (1,2) and (5,2) have byte-identical four-neighbourhoods, so no guard in this language separates slot 1's ring from its underline, and separating slot 2's ring from its dark centre needs a disjunction the grammar does not have. The honest encoding would be four rules that all fire on the same corner cell -- exactly the ambiguity rule 5 forbids. 23 wrong cells on a command I intend to press at most once more is the cheaper error, and since replay accumulates it is currently free in the score."
    [probe: pending]

  theorem key5_is_respawn_and_i_have_written_it_as_respawn "key5_body_clears and key5_body_respawns say: on ACTION5 every floor pixel rendering body-colour returns to floor and the spawn ring lights up. That fits t5 exactly, 24/24 on each half, and I re-checked key5_body_respawns for spurious grounding against this frame -- the meter Glyph9 cells render 9 or 1 and never 5, and the panel Glyph9 cells rendered 9 before t5 and render 2 or 0 after, so neither can satisfy colored(?p, 5). The rival reading, 'ACTION5 is up', fits t5 equally well because the body happened to be exactly one lattice cell below spawn, and it is not idle since up is still unassigned. I keep respawn because ACTION5 alone has ever touched the panel and the panel reads as tokens. Separator: press ACTION5 from a cell that is NOT one lattice cell below spawn. It costs the last token, so it waits behind every other probe in the game, including the two keys never pressed."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "There is no goal: section, so is_goal is False, and that is deliberate even though I can now name the winning position to the pixel. `Cart.pos = exit_cell` needs one named instance, and arc-instances: all gives me Glyph9_r8c14 and 36 siblings instead of a Cart. The socket interior, rows 50-54 cols 44-48, has never changed, so it is board, has no instances, and there is literally nothing there for a count() to range over. `count(Vacated, color = 9) = 24` is true of the body standing on any already-visited floor, which is not a win and would stop a planner at the first step it takes. A goal true in the wrong states is worse than no goal at all. The manual can state its goal only after the body has once stood in (8,7) and those 24 pixels have become dynamic; until then the playbook steers by lattice distance to the knob, which is where the game actually is."
    [depends: the_socket_is_a_keyhole_and_the_pip_names_the_winning_position  probe: pending]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "The arm types a cell by its frame-0 colour, so the body changes type as it walks: at rows 8-12 its pixels are Glyph9, at rows 14-18 they are Vacated. The next descent, from (2,2) to (3,2), needs Vacated pixels going 9 to 5 at rows 14-18 and pixels going 5 to 9 at rows 20-24 -- the second is key2_body_arrives, already written and already witnessed, which will ground at rows 20-24 the moment they are dynamic. Only the clearing half is missing, verbatim for the next desk: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. I have checked it for spurious grounding and it is inert everywhere in this frame, because no Vacated instance renders 9 unless the body stands on it. I still refuse to write it: rule 2 is not negotiable and one descent buys it. Last round the second descent was in the window and I still did not write it; the window has since shrunk and taken that descent with it, which is exactly the kind of thing that makes writing unwitnessed rules expensive."
    [depends: key2_body_arrives  probe: pending]

  theorem nested_cell_terms_parse "Settled by the compiler three rounds running: below(below(...)) six deep parses and grounds, one line of guard draws 24 pixels, and the fallback I once dreaded -- one landmark per lattice cell, which is coordinates in disguise -- is off the table permanently. The four landmarks this manual does declare now carry real arc-cell comments (10,16), (10,40), (40,16), (52,46) instead of the stripped placeholders the previous build shipped, which were silently landing every one of them at (0,0). No rule referenced them, so nothing was drawn wrong; it was a latent trap and it is closed."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem the_meter_rules_i_withdrew "An older build of this manual carried meter_burn_key2 and meter_burn_key4 on one observation each. Both were refuted, and meter_burn_key4's guard would additionally have invented a fifth burn. The lesson is the load-bearing one this round, because the shrunk window offers me those exact two rules again at a 4/5 replay score: one observation per action is not evidence for a rule keyed on the action when a hidden clock explains the same pixels with no free parameter. It is also why key2_floor_leaves stays out of the rules section despite my being fairly sure it is true."
    [probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -5042 and -17520 bits, so its own segmentation loses to writing the pixels out and I owe it nothing structural. Its tracks are nonetheless a useful audit: obj0 (colour 9, 8 cells, 3x3) is panel slot 1, obj1 (colour 1, 9 cells, present 5 frames) is panel slot 2 before the recolour, obj2 (colour 9, 1x3) is an underline, obj4 (colour 9, 1x64) is the whole row-63 bar of which only two cells are dynamic, obj5 (colour 2, first_frame 5) is slot 1 after the recolour, and obj3 is a 1006-cell colour-null blob that swallowed the maze floor -- a fair description of my board, not an object. Every one of them is already inside Glyph9, Spent or board, and obj5 gets no type of its own because a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN in its own words -- 5 transitions constrain rank 3 of 365 features, null space dimension 362 -- and its single global law restates my 73-cell census, which I take as corroboration of the census and nothing more. cegis_miner's refusal remains the most useful sentence any engine has produced here: 'no track satisfies the precondition of exactly one move event per transition; the world does not narrate as one mover.' True of the ARM, false of the world. The world has exactly one mover, a rigid 24-pixel ring; the arm can only see 24 simultaneous recolours, which is why my movement law needs a pair of rules per direction instead of one moved() event."
    [probe: passed]
