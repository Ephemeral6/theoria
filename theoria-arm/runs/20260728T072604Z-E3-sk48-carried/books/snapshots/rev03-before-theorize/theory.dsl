# theory.dsl -- fifth draft. Seven states (t0-t6), six commands. This round
# brought NO new world observation: it brought certify's verdict on draft four.
# So this draft is judged entirely on whether draft four's predictions held,
# and on what re-reading the board and the six transitions can still buy.
#
# (1) THE SECOND POINT PREDICTION ALSO PAID, EXACTLY. Draft four wrote: "this
#     manual therefore predicts the NEXT responsibility report on frame 0 says
#     exactly 69. If it says 68, the checker's board is not 'constant over all
#     observed frames' and I have the wrong model of the checker." certify
#     returned 69, and the arithmetic closes cell by cell: the dynamic set over
#     seven states is 74 = 8 (slot-A ring) + 9 (slot-B block) + 6 (underline,
#     both positions) + 24 (ring pixels in cell (0,0)) + 24 (ring pixels in
#     cell (1,0)) + 3 (tally). Three of those -- (5,5),(5,6),(5,7) -- are
#     background in frame 0. 71 non-background, minus Marker at (1,1) and
#     Unused at (1,5), is 69. The render model is no longer a model; it is
#     arithmetic I can run in advance, and it is written as a formula below.
#
# (2) BOTH SURPRISES ARE THE LEDGER, AND I REFUSE TO CHANGE THE OBJECT SET.
#     Draft four pre-registered the test: "a replay failure whose divergence
#     set is exactly the conceded ledger is not evidence against any rule; one
#     that touches a cell OUTSIDE it is evidence and must be answered." Every
#     cell in both surprise reports -- (1,2),(1,3),(1,6),(1,7),(2,1),(2,3),
#     (2,5),(2,6),(2,7),(3,1..3),(3,5..7),(5,1..3),(8,14..18),(9,14) -- is a
#     HUD pixel or a ring pixel already conceded by name, and the two cells the
#     manual does draw, (1,1) and (1,5), are absent from the divergence list.
#     The test passed. Nothing in the object set changes.
#
# (3) DRAFT FOUR OVER-CLAIMED THE DIRECTION TABLE AND I AM RETRACTING HALF OF
#     IT. "Reading A survives every motion observation without exception" is
#     true and nearly vacuous: key(3) and key(4) were each fired exactly once,
#     both times from cell (1,0), where LEFT is off-board and RIGHT is an
#     all-void cell. Both directions are blocked there, so two 'no move'
#     results separate nothing. The honest statement is: key(2)=down is
#     witnessed positively; key(3) and key(4) are {left,right} in an order this
#     world has never revealed; key(1) is 'up' only via a bijection assumption
#     I have not tested. The route needs five steps RIGHT along the bottom
#     corridor, so this gap is on the critical path, and the playbook now says
#     where to close it for at most one wasted command.
#
# (4) I RE-READ THE STATIC BOARD PIXEL BY PIXEL THIS ROUND AND IT ALL HELD.
#     Lattice, floor map, ribbon width, gate cell, goal cup: every claim in
#     draft four survived the recount, with two refinements now written in --
#     the maze's right edge in lattice rows 0-2 is separator column 43, and the
#     colour-8 blob at cell (0,4) is exactly rows 9-11 x cols 39-41 with the
#     vertical stroke leaving it at (12,40).

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Marker { pos: Coord, color: Int }  # arc-colour: 9
  object Unused { pos: Coord, color: Int, present: Bool }  # arc-colour: 1
  object Spent { pos: Coord, color: Int, present: Bool }  # arc-colour: 2
  landmark hud_slot_a  # arc-cell: (1, 1)
  landmark hud_slot_b  # arc-cell: (1, 5)
  landmark start_cell  # arc-cell: (10, 16)
  landmark button_cell  # arc-cell: (10, 40)
  landmark gate_cell  # arc-cell: (40, 16)
  landmark corridor_cell  # arc-cell: (52, 16)
  landmark goal_cell  # arc-cell: (52, 46)
  Marker [segment: mdl_obj0_ring3x3_colour9 ev: t0-t6 compress: 7]
  Unused [segment: mdl_obj1_solid3x3_colour1 ev: t0-t4 compress: 5]
  Spent [segment: mdl_obj5_ring3x3_colour2 ev: t5-t6 compress: 2]

events:
  event jumped(o, dest) | vanished(o) | appeared(o)

rules:
  rule key5_advances_marker [ev: t5 cov: 1/1]
    when act=key(5) and colored(hud_slot_b, 1) then jumped(Marker, hud_slot_b)
  rule key5_marks_slot_a_spent [ev: t5 cov: 1/1]
    when act=key(5) and colored(hud_slot_a, 9) then appeared(Spent)
  rule key5_consumes_slot_b [ev: t5 cov: 1/1]
    when act=key(5) and colored(hud_slot_b, 1) then vanished(Unused)

laws:
  invariant one_marker count(Marker) = 1 [status: observed]

  theorem render_accounting_closed "DISCHARGED TWICE, and now stated as a formula rather than a number, which is the only way it can keep earning. An object is drawn as ONE pixel; its initial cell is the raster-first cell of its declared arc-colour over the frames the arm was given; two objects sharing a colour collide on that one cell (witnessed in the second draft, where Player and Marker both landed at (1,1)); an object whose colour is absent from the frames anchors nowhere and costs nothing (witnessed by Spent, which drew no stray colour-2 pixel at (0,0)). Therefore: unexplained(frame 0) = D0 - K, where D0 is the number of dynamic cells that are non-background in frame 0 and K is the number of DISTINCT colours in frame 0 for which I have declared an object. Draft three predicted 68 against 53 and got 68; draft four predicted 69 against 68 and got 69. The formula's next falsifier is mechanical: each NEW lattice cell the ring enters turns 24 previously-constant colour-5 pixels into colour-9 pixels and so adds exactly 24 to D0 and 24 to the count; each tally pixel that flips adds exactly 1; re-entering a cell the ring has already occupied adds 0. So if the next two commands walk the ring from cell (0,0) to (1,0) to (2,0) and the tally ticks once, the next responsibility report reads 69 + 24 + 1 = 94. Any deviation from D0 - 2 that is not explained by that arithmetic refutes this theorem, not the world."
    [probe: pending]

  theorem responsibility_ceiling_is_two_pixels "69 is not slack, it is the arithmetic maximum this language reaches here, and it will grow with every cell the ring visits without any of it being a missing rule. An object is located by colour and same-colour objects collide, so a colour explains at most one cell. The colours on non-background dynamic cells of frame 0 are exactly 9 and 1; colour 5 and colour 8 have raster-first cells at (7,13) and (9,39), both constant board cells, so objects in those colours would explain nothing they were not already given. Two colours, two pixels, both claimed. I could satisfy the checker by declaring seventy single-pixel objects ONLY IF same-colour objects took distinct anchors, they do not, and even if they did I would refuse: seventy noise objects buy zero compression and teach nothing. Full-frame responsibility is unreachable in this world and I say so rather than fake it."
    [depends: render_accounting_closed  probe: pending]

  theorem replay_can_never_pass_here "replay compares whole frames and frame 0 is 69 pixels wrong before any rule fires, so 0/6 is structural and stays 0/n for every n. The diagnostic pre-registered in draft four RAN THIS ROUND AND PASSED: every divergence cell reported is in the conceded ledger and the two drawn cells are not in it. That is the only signal replay can carry here, it is a real one, and it must be re-run every round -- a divergence cell outside the ledger is evidence against a rule and must be answered."
    [depends: responsibility_ceiling_is_two_pixels  probe: pending]

  theorem the_mover_is_unnameable "the thing that plays this game is a 5x5 colour-9 ring with a one-pixel hole at its centre, and it cannot be declared. Colour 9 is raster-first-claimed by the HUD at (1,1) in frames 0-4 and at (1,5) in frames 5-6, so any colour-9 object lands on the HUD. mdl_segmenter offers no track for it: under connected_components(4) with split_by_color off the ring fuses with the colour-5 floor and the colour-8 wire into obj3, 1006 cells, colour null. I ACCEPT that fusion as fact and REJECT the conclusion cegis_miner drew from it -- 'the world does not narrate as one mover'. It narrates as exactly one mover; the mover is buried in a 1006-cell blob and owns no colour. Consequence: this manual contains no movement rule and cannot, and every movement claim lives in a theorem or in the playbook."
    [probe: pending]

  theorem lattice_geometry "the maze is an 8x6 lattice of 5x5 cells at pitch 6. Cell (r,c) occupies rows 8+6r..12+6r and cols 14+6c..18+6c for r=0..7, c=0..5; separator rows are 7+6r, separator columns 13+6c; separators are colour 5 wherever both neighbours are floor, so they divide nothing. Cell centres are (10+6r, 16+6c). Witnesses: the ring occupied exactly rows 8-12 x cols 14-18, then exactly rows 14-18 x cols 14-18, a displacement of exactly 6; its hole sat at (10,16) then (16,16), each the exact centre; the goal dot is at (52,46), the centre of (7,5); the colour-8 blob is centred on (10,40), the centre of (0,4). Refinement from this round's recount: in lattice rows 0-2 the floor stops at separator column 43, so column c=5 is void above the bottom corridor."
    [probe: pending]

  theorem floor_map "the complete read of the static board by lattice cell, re-verified pixel by pixel this round. r=0: c=0..4 floor (an open five-cell corridor, separators 25,31,37,43 all floor), c=5 void. r=1: c=0 floor, c=1 void (rows 14-18 x cols 20-24 all colour 0), c=2 floor, c=3 void, c=4 the three-wide ribbon, c=5 void. r=2: c=0,1,2 floor, c=3 void, c=4 ribbon, c=5 void. r=3, r=4: c=0 floor, c=1,2,3 void, c=4 ribbon, c=5 void. r=5: c=0 is a 5x5 of colour 8 (23 pixels colour 8, colour 5 only at (39,14) and (41,14)), c=1,2,3 are the three-row stripe at rows 39-41 only, c=4 the ribbon junction, c=5 void. r=6: c=0 floor, rest void. r=7: c=0..5 all floor, the bottom corridor rows 50-54 x cols 14-48, arriving at the goal cup from the left. Consequence: the floor-only reachable set from start is exactly twelve cells -- (0,0),(0,1),(0,2),(0,3),(0,4),(1,0),(1,2),(2,0),(2,1),(2,2),(3,0),(4,0) -- and it does not contain the goal."
    [depends: lattice_geometry  probe: pending]

  theorem void_blocks_and_the_guard_language_is_inverted "colour 0 is wall, colour 5 is floor. Witness: key(4) fired from cell (1,0) at t4 faced the all-void cell (1,1) and moved nothing. Note the trap: free(x) in this DSL tests the BACKGROUND colour, which here is 0 -- exactly the cells that are NOT enterable. Any movement rule ever written here must be guarded colored(x, 5) and never free(x). Untested: whether a cell that is void at its edges but non-void at its centre blocks. No such cell is on the intended route."
    [depends: floor_map  probe: pending]

  theorem the_ribbon_is_too_narrow_for_the_ring "the sharpest deduction available without an experiment, and it kills half the search space. The colour-8 figure is one pixel wide throughout: a vertical stroke down col 40 from row 12 to row 41 with colour 5 at cols 39 and 41 and void at 38 and 42; a horizontal stroke along row 40 from col 40 back to col 14 with colour 5 at rows 39 and 41 and void at 38 and 42. Total corridor width three; the mover is five. So cells (1,4),(2,4),(3,4),(4,4),(5,1),(5,2),(5,3),(5,4) cannot hold the ring whatever colour 8 means, and no route may pass through them. Exactly one colour-8 cell has a full 5x5 of non-void pixels: (5,0), rows 38-42 x cols 14-18."
    [depends: floor_map, lattice_geometry  probe: pending]

  theorem cell_five_zero_is_the_gate "one cell decides the level. Column 0 is floor at r=0,1,2,3,4 and again at r=6,7; the bottom corridor r=7 runs unbroken to the goal; between them sits (5,0), the colour-8 filled cell, gate_cell in the word table, joined above by floor separator row 37 and below by floor separator row 43. There is no other join between the reachable twelve and the goal region. So either the ring can enter (5,0), or the goal as I read it is unreachable and the win condition is something else. No transition tests it; one command from (4,0) does, and that command is on the critical path either way, so it costs nothing if the gate is open."
    [depends: the_ribbon_is_too_narrow_for_the_ring  probe: pending]

  theorem the_eight_line_is_probably_a_wire_and_the_blob_is_its_button "the competing reading of colour 8, kept because it is cheap to keep and expensive to have missed, and strengthened this round by the recount. The figure is one connected line with two distinguished ends: a 3x3 blob at rows 9-11 x cols 39-41, dead centre of cell (0,4), which is REACHABLE floor four steps right of start; and the filled 5x5 at (5,0), which is the gate. A line joining a reachable marked cell to the one blocking cell reads as button-and-door at least as naturally as it reads as a drawn path. Two further hints: the blob is 3x3 like the HUD icons rather than 5x5 like a cell, and the ring standing on (0,4) would show colour 8 through its central hole -- the same 'dot through the hole' signature the goal cell has. If the gate refuses entry, standing on button_cell and watching gate_cell for a colour change is the next experiment, and it is eight commands out and back from (0,0)."
    [depends: cell_five_zero_is_the_gate  probe: pending]

  theorem goal_is_the_cupped_cell "rows 48-56 x cols 42-50 is a 9x9 colour-5 box drawn around cell (7,5). Inside it colour 9 paints row 49 cols 43-49, row 55 cols 43-49 and col 49 rows 50-54: a cup open to the LEFT, which is the side the bottom corridor arrives from. A lone colour-9 pixel sits at (52,46), the exact centre of (7,5), and the ring's hole is at its own exact centre, so bringing the ring here makes the dot show through the hole. It is the only cell in the frame drawn this way and it is drawn in the ring's own colour. Read off the static board; no transition witnesses it. Shortest route consistent with floor_map: seven steps down column 0, five steps right along the bottom corridor, twelve commands."
    [depends: lattice_geometry, floor_map  probe: pending]

  theorem direction_map_is_one_third_known "RETRACTION of draft four's confident table, on re-examination of what the negative results can separate. key(2) = DOWN: positively witnessed at t2, cell (0,0) to (1,0), the only motion in the record. key(1): fired at t1 and again at t6, both times from (0,0), both times nothing moved; (0,0) has floor to its right and floor below, so key(1) is NOT right and NOT down, leaving key(1) in {up, left}. key(3) at t3 and key(4) at t4 were BOTH fired from (1,0), which has floor above and floor below but off-board to the left and an all-void cell to the right; so each of them is in {left, right} and NOTHING in this record distinguishes them from each other. If keys 1-4 are a bijection onto the four directions then key(3) and key(4) exhaust {left,right}, forcing key(1) = up -- but that bijection is an assumption, not an observation, and key(1) could equally be a no-op that only ticks the clock. What matters for the route: the bottom corridor needs five steps RIGHT, so the left/right order MUST be settled, and it must be settled at a cell where a wrong guess cannot displace the ring."
    [depends: floor_map  probe: pending]

  theorem tally_is_a_two_command_clock "row 63 is a 64-pixel colour-9 bar filling with colour 1 from the right: (63,63) at t2, (63,62) at t4, (63,61) at t6, and no advance at t1, t3 or t5. A perfect alternation, 6/6, one pixel per two commands, independent of which key was pressed, independent of whether anything moved, and NOT reset by key(5) -- which is the observation that rules out reading it as a per-attempt score. Three of sixty-four consumed leaves about 122 commands against a twelve-command route: not binding, so wandering rather than walls is what would kill this level. THE HONEST CAVEAT, unchanged and unresolved: a perfect alternation over six samples is roughly a one-in-thirty accident, and zero_space's own verdict is THIN -- six transitions constrain rank 4 of 370 features, so nearly every law it can state is unfalsified rather than confirmed. I accept that verdict for this law too. Every command tests it for free and the playbook says to read it every time; the first tick on an odd command or the first pair of consecutive ticks kills it."
    [probe: pending]

  theorem hud_is_two_attempts_and_one_is_gone "two 3x3 slots at cols 1-3 and cols 5-7 with a 3-pixel underline at row 5 marking the active one. Frames 0-4: slot A a colour-9 ring, underlined; slot B a solid colour-1 block. Frames 5-6: slot A a colour-2 ring, unmarked; slot B a colour-9 RING, underlined. So the active slot shows the player's own icon in the player's own colour, an unused slot is a solid colour-1 block, a spent slot is a colour-2 ring. key(5) did all of that in one nine-frame command, moved the ring back to start, and did not reset the tally. Reading: two attempts, key(5) spends one and restarts the position. The competing reading -- 'objective cleared, next objective' -- is not dead, but a position reset with no tally reset argues against it. Either way slot B is the LAST slot, and the guards on the three rules encode that: with slot A at colour 2 and slot B at colour 9, none of them can fire again."
    [depends: key5_advances_marker, key5_marks_slot_a_spent, key5_consumes_slot_b  probe: pending]

  theorem two_action_keys_have_never_been_pressed "ARC offers ACTION1..ACTION7 and this world has seen only 1..5. Draft four never said so and that is a gap, not a fact. ACTION6 in this family is customarily a click carrying coordinates, which this guard language cannot express at all; ACTION7 is unknown. I do not press them, and the playbook says why: exactly one attempt remains, key(5) demonstrated that a single key press can cost an attempt and reset the position, and an unknown key is therefore a bet with an unbounded downside on a level whose route I believe I can already walk. They are held in reserve for the case where both the gate and the button refuse."
    [probe: pending]

  theorem spent_anchor_unresolved_and_maybe_unresolvable "Spent survives on the evidence that it cost nothing in frame 0, which is what a colour absent from the frame should cost. Its other half -- whether the arm anchors from the whole frame stack, in which case Spent sits at (1,1) and draws colour 2 there from t5 on, correctly, and before t5 incorrectly -- may never be answered, because responsibility reports frame 0 only and replay diverges at t=0 and stops. I flag this as a limit of the instrument, not a hole in the world: nothing about the route depends on it."
    [depends: render_accounting_closed  probe: pending]

  theorem vacated_cell_repaints_to_five "when the ring left cell (0,0) at t2 those 24 pixels became colour 5, not background 0, and cell (1,0) did the same at t5. A fact about the world and a defect I cannot repair: nothing in the language repaints a cell an object has left, and a colour-5 Floor object would anchor at (7,13) and paint one pixel of a 1006-cell blob. The 24 pixels of whichever start cell is currently empty are conceded in every frame."
    [probe: pending]

  theorem cascade_length_is_a_signal "t2 returned 7 frames and t5 returned 9 for a single command; t1, t3, t4, t6 returned 1 each, and t4 and t6 still changed a pixel. A multi-frame command is an animation of real motion; a single-frame command is an instant verdict. Only the last frame reaches me and cascade single_frame is the only value that compiles, so the slide itself is invisible -- but the frame COUNT is not, and it is a free channel: any command returning more than one frame moved something even if I cannot see what. This is how the left/right probe will be read, and seven frames for a six-pixel displacement is quiet support for lattice_geometry."
    [probe: pending]

  theorem no_goal_section_on_purpose "the win condition I believe is 'the ring reaches goal_cell'. Its subject is unnameable, so writing it would either fail to compile or name the HUD marker and be false. An absent goal compiles to is_goal -> False, which under-claims; a goal about the wrong object over-claims and is refuted by the first win. I under-claim and the playbook carries the direction. start_cell, button_cell, gate_cell, corridor_cell and goal_cell are declared with no rule referencing them for one reason: the DSL has nowhere else to write a coordinate and the playbook's heuristics need referents to name."
    [depends: goal_is_the_cupped_cell, the_mover_is_unnameable  probe: pending]

  theorem conceded_pixels "the ledger for frame 0 on the seven-state dynamic set of 74 cells, 3 of them background there. Drawn correctly: 2 -- Marker at (1,1), Unused at (1,5). Conceded: 7 of the slot-A ring, 8 of the slot-B block, 3 of the slot-A underline, 24 of the player ring in cell (0,0), 24 of the repainted floor in cell (1,0), 3 of the tally bar. 7+8+3+24+24+3 = 69, the number predicted and the number returned, and every cell certify listed is in this list. Every one of them fails for the same reason -- the object that owns them can be given exactly one Coord -- and not one of them is a missing rule. This violates full-frame responsibility knowingly and completely, and I would rather say so in a paragraph than declare seventy single-pixel objects that would satisfy the checker and teach nothing."
    [depends: responsibility_ceiling_is_two_pixels, vacated_cell_repaints_to_five  probe: pending]
