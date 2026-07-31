# theory.dsl -- world observed for 9 commands (RESET + ACTION1..ACTION5,
# ACTION1..ACTION4). 75 cells have ever changed; this manual names all 75 and
# owns the 72 that any colour-keyed object can own.
#
# WHAT HAPPENED THIS ROUND:
#
#   1. THE PREDICTION WAS MET EXACTLY. Last round I wrote, in the manual and in
#      advance: "t2 and t7 must each replay with ZERO cells wrong except
#      (63,63) at t2." certify's first divergence is t=1, ACTION2, cells_wrong
#      = 1, cell (63,63), manual 9 world 1. That is the prediction, to the
#      cell. The four movement rules are physics and they are now paid for.
#
#   2. THE INSTRUMENT IS SATURATED, AND I CAN PROVE IT. replay reports 1/9. If
#      replay re-seeded from the world frame each command, my manual would
#      match at least three transitions (the two no-ops it predicts correctly
#      and the second descent). It reports one. So replay carries its own state
#      forward, one wrong cell at t=1 poisons every later comparison, and the
#      meter is a cell no guard in this language can predict. My replay score
#      is pinned at 1/9 for the rest of this game. From here I score myself on
#      the responsibility check and on hand-read frame diffs, not on `matched`.
#      See replay_accumulates_so_the_meter_pins_the_score.
#
#   3. I READ THE WHOLE MAZE OFF THE FRAME AND IT HAS EXACTLY ONE DOOR. The
#      lattice is 6 rows by 8 columns of 5x5 cells. From spawn the body can
#      reach eleven cells and no more; the socket is not among them; the single
#      cell separating the two halves is the colour-8 comb, and the only thing
#      touching the reachable region that is neither floor nor void is the
#      colour-8 knob wired to that comb. That is a whole theory of the game,
#      and it is falsifiable in one command.
#
#   4. I WITHDRAW AN OVER-CLAIM OF MY OWN. Last round's action map said the
#      direction assignment was unique. It is not: at spawn, left is void too,
#      so ACTION1 could be left. What IS forced is that ACTION3 and ACTION4 are
#      not up. The corrected argument, and the one command that settles it, are
#      in the_action_map_is_weaker_than_i_claimed.

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Glyph9  { pos: Coord, color: Int }   # arc-colour: 9  arc-instances: all
  object Vacated { pos: Coord, color: Int }   # arc-colour: 5  arc-instances: all
  object Spent   { pos: Coord, color: Int }   # arc-colour: 1  arc-instances: all
  landmark spawn_center  # arc-cell: carried, coordinates stripped
  landmark socket_center  # arc-cell: carried, coordinates stripped
  landmark gate_center  # arc-cell: carried, coordinates stripped
  landmark knob_center  # arc-cell: carried, coordinates stripped
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
  invariant nine_count_this_build count(Glyph9) = 39 [status: counted]
  invariant five_count_this_build count(Vacated) = 24 [status: counted]
  invariant one_count_this_build count(Spent) = 9 [status: counted]
  invariant board_static_this_build count(board) = 4021 [status: counted]

  theorem the_prediction_i_made_last_round_was_met_exactly "I wrote the test into the manual before the manual was scored: after the two key2 rules compile, t2 and t7 must replay with zero cells wrong except (63,63), and any other residue refutes my reading of `colored` or of instance typing. certify's first divergence is t=1, ACTION2, cells_wrong 1, cell (63,63), manual 9 world 1. Nothing else. So: distance-six recolour pairs are the correct encoding of a rigid 24-cell mover on this arm; `colored(?p, 9)` reads the CURRENT rendered colour and not the frame-0 colour, since key2_body_leaves had to see the ring as 9 while its instances are typed 9 and key2_body_arrives had to see floor as 5 while typed 5; and the guards are inert on the panel and the meter exactly as I hand-checked them. This is the one thing in the manual that is finished."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem replay_accumulates_so_the_meter_pins_the_score "certify says 1/9 transitions replay exactly. Count what my manual predicts under the other reading, where replay re-seeds from the world frame each command: transition 0 (ACTION1, world no-op, no rule fires) matches; transition 2 (ACTION3, no-op) matches; transition 8 (ACTION4, no-op) matches; transition 6 (ACTION2, the second descent) matches, since transition 1 shows the descent is drawn correctly and t7 burns no meter cell. That is at least four, and four is not one. Therefore replay carries ITS OWN state forward and never re-seeds. Consequence, and it is the operational fact of this round: one unpredictable cell at t=1 makes every later transition wrong at that cell, so `matched` can never rise above 1 while the meter burns, and `first_divergence` can never move past t=1. The replay number is now blind to every improvement I make. I score the manual by the responsibility check, which is at 0 unexplained, and by reading the command diffs myself."
    [probe: passed]

  theorem the_meter_is_a_hidden_parity_and_no_guard_can_separate_it "Row 63 is a 64-cell colour-9 bar losing its rightmost live cell to colour 1, right to left. Burns: t2 (63,63), t4 (63,62), t6 (63,61), t8 (63,60). No burns: t1, t3, t5, t7, t9. I have now checked every guard this language offers against that split, and each one puts a burn and a non-burn in the same class. By action: ACTION1 burns at t6 and not at t1; ACTION2 burns at t2 and not at t7; ACTION3 burns at t8 and not at t3; ACTION4 burns at t4 and not at t9. By body position: spawn burns at t2, t6 and does not at t1, t7; the lower cell burns at t4, t8 and does not at t3, t5, t9. By the meter's own state, which is the only counter visible as cells: with 0 cells already burned the world both refuses (t1) and burns (t2); with 1 burned it both refuses (t3) and burns (t4); with 2, refuses (t5) and burns (t6); with 3, refuses (t7) and burns (t8). By panel state: within each of the two panel states the burns still alternate. The world is flipping a bit that is not drawn anywhere in the 4096 cells, and `free`, `colored`, `adjacent`, `= wall` and `act=` can only ask about drawn cells and the current action. So I write NO meter rule. This is a refusal, not an omission: it costs one cell on four transitions and, because replay accumulates, it costs the whole replay score, and every alternative I can write costs more. cegis_miner reached the same wall from the other side -- 'no literal separates transition 1 from the positives'."
    [probe: passed]

  theorem the_meter_may_be_counting_frames_rather_than_commands "A refinement worth having because it prices the game. Commands have returned 1, 7 or 9 frames; cumulative frames including the reset frame are 2, 9, 10, 11, 20, 21, 30, 31, 32 at the ends of t1..t9. The bar burns exactly when that cumulative count is ODD -- 9, 11, 21, 31 burn; 2, 10, 20, 30, 32 do not -- nine for nine. Command parity fits equally well, and the two readings cannot be told apart yet for a plain reason: 1, 7 and 9 are all odd, so every command so far flipped the parity. A command returning an EVEN number of frames is the separator, and I do not know how to force one. Either way the budget is the same to first order: one cell per two commands, 64 cells, 4 spent, so roughly 120 commands remain. The lattice route I can see is about twenty. The meter is not the binding constraint; the tokens are."
    [depends: the_meter_is_a_hidden_parity_and_no_guard_can_separate_it  probe: pending]

  theorem the_maze_is_a_six_pixel_lattice_and_i_have_read_all_of_it "Cell (R,C) is rows 6R+2..6R+6 by cols 6C+2..6C+6; separator strips are the rows and cols congruent to 1 mod 6. Colour 5 is floor, colour 0 is wall, and the body is a rigid 5x5 block of 9 with a one-cell hole at its centre, so a cell is enterable only if all 25 of its pixels are floor. Reading the current frame span by span: R=1 (rows 8-12) is floor at C=2,3,4,5, carries the knob at C=6 and is void at C=7; R=2 (rows 14-18) is floor at C=2 and C=4 only; R=3 (rows 20-24) at C=2,3,4; R=4 and R=5 (rows 26-36) at C=2 only; R=6 (rows 38-42) has no enterable cell at all -- C=2 is the comb and C=3..6 are floor only on rows 39 and 41, a three-tall channel flanking the row-40 cable, which a five-tall body cannot use; R=7 (rows 44-48) at C=2; R=8 (rows 50-54) is open floor from col 13 to col 48, so C=2 through C=7 all enterable, and C=7 is the socket interior. Openings: column 2 is continuous from R=1 to R=8 across every separator row; R=1 is continuous from C=2 to C=6; R=3 connects C=2,3,4; R=8 connects C=2 through C=7. That is the whole map and it took no concept beyond the lattice I already had."
    [depends: key2_body_arrives  probe: pending]

  theorem the_socket_is_unreachable_until_the_comb_opens "Flood the map from spawn (1,2) and the body reaches exactly eleven cells: (1,2), (1,3), (1,4), (1,5), (2,2), (2,4), (3,2), (3,3), (3,4), (4,2), (5,2). The socket interior (8,7) is not among them, and neither is anything in R=7 or R=8, because every path south crosses (6,2) and (6,2) is filled with colour 8 except the two pixels (39,14) and (41,14). So the comb is not an obstacle to route around; it is the door, and this game cannot be won without opening it. The cable makes the mechanism explicit: colour 8 leaves the comb along row 40, runs right to col 40, climbs col 40 and ends in a 3x3 colour-8 knob at rows 9-11 cols 39-41, which is the interior of lattice (1,6). No colour-8 pixel has moved in nine commands, which is why 8 is board and not an object; the first colour-8 pixel that changes converts this theorem into physics and gives me a rule to write."
    [depends: the_maze_is_a_six_pixel_lattice_and_i_have_read_all_of_it  probe: pending]

  theorem the_knob_is_the_only_thing_the_body_can_touch_and_i_do_not_know_how_it_is_pressed "Of the eleven reachable cells, ten are surrounded by floor and void only. The eleventh, (1,5), is adjacent through the open separator col 37 to (1,6), whose interior is the knob. So the knob is the single interactive object within reach, and pressing it is the only lever I can see. How it is pressed I do not know, and the geometry is against the obvious reading: the body's hole is ONE pixel, at (10,40) if it stood at (1,6), while the knob is nine pixels, so entering (1,6) means the body overlapping eight colour-8 pixels. Either colour 8 is walkable and my key2_body_arrives -- which demands the destination render 5 -- is wrong at the knob and at the comb, or the knob is triggered by proximity from (1,5), or by an action I have not pressed. All three are cheap to distinguish and my rules make the first one self-announcing: if the body enters a colour-8 cell, the manual predicts it stops and the world says otherwise, in one command."
    [depends: the_socket_is_unreachable_until_the_comb_opens  probe: pending]

  theorem the_action_map_is_weaker_than_i_claimed "I withdraw last round's 'unique assignment'. ACTION2 = down is proven twice, six pixels at t2 and t7. What the six no-ops actually force is less. ACTION1 was a no-op at t1 and t6, both from spawn (1,2), where up is off the floor AND left is void -- but right, (1,3), is open floor, so ACTION1 is not right, and ACTION1 is up or left or nothing. ACTION3 and ACTION4 were no-ops at t3, t8 and t4, t9, all four from (2,2), where left and right are both void -- but up, (1,2), is open floor, so NEITHER ACTION3 NOR ACTION4 IS UP. That is the strong new fact. If up lies in ACTION1..ACTION4 at all it is ACTION1; it could still be ACTION5, or one of the two keys I have never pressed. The separator is free, it is available from where the body stands right now, and it is progress rather than a detour: press ACTION1 from (2,2), where up is open and left is void. Body moves six pixels north, ACTION1 is up and the route to the knob is open; nothing moves, ACTION1 is left or inert and I have lost one meter tick and learned the same amount."
    [depends: key2_body_leaves  probe: pending]

  theorem two_actions_have_never_been_pressed "The store's actions_used is ACTION1..ACTION5 and RESET. This world's alphabet is ACTION1..ACTION7. So a sixth and a seventh command exist that I have never sent and that no observation constrains at all -- and in this family ACTION6 is normally a click carrying coordinates. That matters here specifically: the knob is a 3x3 target the body may be geometrically unable to stand on, and a click is exactly the shape of interaction that would press it. I cannot write such a rule. The guard language admits `act=key(6)` but has no way to attach the two coordinates a click carries, so a click rule would be silently wrong about which cell was clicked. If a click turns out to drive this world, my manual can record its EFFECT -- comb pixels going 8 to 5 -- and never its precondition. I am recording that limit now rather than discovering it under pressure."
    [probe: pending]

  theorem the_panel_is_two_tokens_and_one_is_already_spent "Rows 1-3 cols 1-3 and cols 5-7 are two 3x3 icons, each with a 1x3 underline at row 5. Frames 0-4: slot 1 a hollow colour-9 ring with its underline lit, slot 2 a solid colour-1 block with its underline dark. From frame 5: slot 1 a hollow colour-2 ring with its underline dark, slot 2 a hollow colour-9 ring with its underline lit. The icons are miniatures of the body -- a hollow square with a one-pixel hole -- so I read them as bodies: two tokens, the lit hollow 9 is the one in play, colour 2 is a token consumed. The only command that has ever touched the panel is ACTION5, and ACTION5 is respawn, so respawn spends a token and ONE TOKEN REMAINS. This is the binding budget of the game, not the meter: I have roughly 120 commands and one life. Every probe that could end in a respawn is therefore ranked below every probe that cannot."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem only_visited_cells_have_instances "Settled by arithmetic. The arm builds one instance per cell of the declared colour THAT THE BOARD CANNOT EXPLAIN, and board is the set of never-varying cells: constant_cells 4021 plus dynamic_cells 75 is 4096, and cells_needing_an_owner is 72, which is my 75 minus the three background-at-frame-0 cells no colour-keyed object can claim. 39 + 24 + 9 = 72 exactly. So the instance set IS the set of cells that have already changed, and the corridor ahead has no instances however much floor it shows. The deductive consequence, which is still untested: the first step into a never-yet-changed cell costs 48 wrong cells -- 24 for a body I keep drawing where it no longer is, 24 for a body I cannot draw where it now is -- and the round AFTER that, those cells are dynamic, instances exist, and key2_body_arrives draws them with no change to its text. The manual heals itself one step behind the body. I price every forward step at 48 and take it anyway."
    [depends: key2_body_arrives  probe: passed]

  theorem the_instance_counts_are_build_relative_not_world_facts "The four invariants above are counted at THIS build and will be false at the next one, because stepping into fresh corridor moves 24 more cells from board into Vacated and raises count(board) is 4021 to something smaller. I state them anyway because they are the arithmetic that proves only_visited_cells_have_instances, and I say plainly here that they are properties of what has been observed rather than laws of the world. Nothing in the rules depends on them."
    [probe: passed]

  theorem the_one_key2_rule_i_am_still_not_allowed_to_write "The arm types a cell by its frame-0 colour, so the body changes type as it walks: at rows 8-12 its pixels are Glyph9, at rows 14-18 they are Vacated. Last round I said this costs me two unwritten rules. It costs one. The next descent, from (2,2) to (3,2), needs Vacated pixels going 9 to 5 at rows 14-18 and Vacated pixels going 5 to 9 at rows 20-24 -- and the second of those IS key2_body_arrives, already written and already witnessed, which will ground at rows 20-24 as soon as they are dynamic. Only the clearing half is missing, verbatim for the next desk: 'rule key2_floor_leaves forall ?v in Vacated when act=key(2) and colored(?v, 9) and colored(below(below(below(below(below(below(?v)))))), 5) then recolored(?v, 5)'. I have checked it for spurious grounding and it is inert everywhere today, because no Vacated instance renders 9 unless the body is standing on it. I still refuse to write it: rule 2 is not negotiable and one descent buys it. The companion I named last round, Glyph9 going 5 to 9 on arrival, I now expect never to need for a downward move -- the only frame-0 colour-9 floor pixels in the maze are the spawn ring, and nothing lies above spawn."
    [depends: key2_body_arrives  probe: pending]

  theorem dynamic_census "Exactly 75 cells have ever changed. 23 are the status panel at rows 1-5 cols 1-7. 24 are the spawn ring, rows 8-12 cols 14-18 minus its hole (10,16), which never changes and is therefore board. 24 are the same shape six pixels down, rows 14-18 cols 14-18 minus its hole (16,16). 4 are the right end of the row-63 bar, cols 60-63. 23+24+24+4 = 75 and nothing is left over. At frame 0 they split as 39 colour-9, 9 colour-1 and 24 colour-5, plus 3 background; 39+9+24 = 72, exactly cells_needing_an_owner, and the responsibility check reports 0 unexplained."
    [probe: passed]

  theorem three_cells_no_object_can_ever_own "(5,5), (5,6), (5,7) are background at frame 0 and colour 9 from frame 5, so no colour-keyed object owns them and none can: an arc-colour 0 object would claim three thousand background cells. Any future panel rule has a floor of 3 wrong cells. This is exactly the gap between 75 dynamic cells and 72 cells_needing_an_owner, and it is structural."
    [probe: passed]

  theorem the_panel_debt_i_am_choosing_to_carry "I write no panel rule and every ACTION5 costs me 23 wrong cells. The reason is rules 3 and 5, not laziness: (1,2) and (5,2) have byte-identical four-neighbourhoods so no guard separates the slot-1 ring from its underline, and separating the slot-2 ring from its centre needs a disjunction this grammar does not have, so the honest encoding is four rules that all fire on a corner cell -- exactly the ambiguity rule 5 forbids. 23 wrong cells on a command I intend to press at most once more is the cheaper error, and since replay accumulates it is now free in the score."
    [probe: pending]

  theorem key5_is_respawn_and_i_have_written_it_as_respawn "key5_body_clears and key5_body_respawns say: on ACTION5 any floor pixel that is body-coloured returns to floor and the spawn ring lights up. That fits t5 exactly, 24/24 on both halves, and I checked key5_body_respawns for spurious grounding -- the only Glyph9 instances that ever render 5 are the spawn ring's. The rival reading, 'ACTION5 is up', fits t5 equally well because the body happened to be one lattice cell below spawn, and it is not idle: the_action_map_is_weaker_than_i_claimed leaves up unassigned. I keep respawn because ACTION5 alone has ever touched the panel and the panel reads as tokens. Separator: press ACTION5 from a cell that is NOT one lattice cell below spawn. It costs the last token, so it waits behind every other probe in the game, including the two keys I have never pressed."
    [depends: key5_body_clears, key5_body_respawns  probe: pending]

  theorem the_goal_section_is_absent_on_purpose "There is no goal: section, so is_goal is False, and that is deliberate. The socket interior, rows 50-54 cols 44-48, is floor that has never changed, so it is board and has no instances -- there is nothing there for a goal to name. `Cart.pos = exit_cell` needs a single named instance and arc-instances: all gives me Glyph9_r8c14 and 38 siblings instead. `count(Vacated, color = 9) = 24` is true of the body standing anywhere off spawn, which is most of the maze and not a win. A goal true in the wrong states is worse than none, because the planner stops at the first one. The manual will be able to state its goal only after the body has once stood in the socket and those pixels have become dynamic; until then the playbook steers by lattice distance."
    [probe: pending]

  theorem nested_cell_terms_parse "Settled by the compiler two rounds running: below(below(...)) six deep parses and grounds, one line of guard draws 24 pixels, and the fallback I dreaded -- one landmark per lattice cell, which is coordinates in disguise -- is off the table permanently."
    [depends: key2_body_leaves, key2_body_arrives  probe: passed]

  theorem the_meter_rules_i_withdrew "The manual before last carried meter_burn_key2 and meter_burn_key4 on one observation each. t7 refuted the first, t9 the second, and meter_burn_key4's guard would now invent a fifth burn at (63,59). One observation per action is not evidence for a rule keyed on the action when a hidden clock explains the same pixels. The lesson is why key2_floor_leaves stays out of the rules section this round despite being, I am fairly sure, true."
    [probe: passed]

  theorem what_the_engines_gave_me "mdl_segmenter scores NEGATIVE on both variants, -4457 and -22984 bits, so its own segmentation loses to writing the pixels out and I owe it nothing; its obj3 is a 1006-cell colour-null blob that swallowed the maze floor, which is a fair description of my board and not an object. obj0, obj2 and obj4 are colour-9 fragments already inside Glyph9; obj5 is the colour-2 panel ring, which is Glyph9 pixels after a recolour and gets no type of its own, since a second type on the same pixels invites the double claim rule 5 forbids. zero_space self-reports THIN -- 9 transitions constrain rank 6 of 375 features, null space dimension 369 -- and its one global law restates my 75-cell census. cegis_miner's refusal remains the most useful sentence any engine has produced: 'no track satisfies the precondition of exactly one move event per transition; the world does not narrate as one mover.' True of the ARM, false of the world. The world has exactly one mover, a rigid 24-pixel ring; the arm can only see 24 simultaneous recolours, which is why my movement law needs a pair of rules per direction instead of one moved() event."
    [probe: passed]
