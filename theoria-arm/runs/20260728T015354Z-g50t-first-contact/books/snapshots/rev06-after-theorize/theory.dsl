# theory.dsl -- fourth draft. Seven states (t0-t6), six commands.
#
# WHAT THIS ROUND BOUGHT, in order of value. Read this before the sections.
#
# (1) THE RENDER MODEL MADE A POINT PREDICTION AND THE WORLD PAID IT EXACTLY.
#     The third draft wrote: "this manual PREDICTS the next responsibility
#     report will say 68 unexplained pixels in frame 0. If it instead says
#     about 53, then objects are drawn as the whole segmenter track. No third
#     value is expected." certify returned 68. The arithmetic closes to the
#     pixel: certify ran over 6 states (its replay says "transitions: 5"), so
#     the dynamic set was 73 cells; 3 of those are background in frame 0
#     (row 5, cols 5-7); 70 non-background; Marker was anchored at (1,1) and
#     painted 9 there, Unused at (1,5) and painted 1 there; 70 - 2 = 68.
#     Both anchors are absent from the divergence list, which is how I know
#     which two were right. AN OBJECT IS ONE PIXEL, AT THE RASTER-FIRST CELL
#     OF ITS DECLARED COLOUR, IN THAT COLOUR. That is no longer a conjecture.
#
# (2) t6 BROKE THE DIRECTION TABLE, AND IN THE DIRECTION I DID NOT EXPECT.
#     ACTION1 from the start cell did NOTHING AT ALL at t1 and advanced the
#     tally at t6 -- same cell, same key, different result. Reading B ("key 1
#     and key 3 are unbound") is dead: an unbound key cannot tick a counter.
#     Reading A (1=up 2=down 3=left 4=right) survives every motion observation
#     without exception, and the tally asymmetry that was reading A's only
#     problem dissolves once the tally is read as a CLOCK rather than a move
#     counter: it ticked at t2, t4, t6 and not at t1, t3, t5 -- a perfect
#     alternation, 6/6, one pixel per two commands. Reading A plus the clock is
#     the first hypothesis that covers all six transitions with no residue.
#
# (3) THE BOARD IS NOW READ TO THE PIXEL, AND IT SETTLES THE ROUTE QUESTION
#     MOSTLY WITHOUT AN EXPERIMENT. The colour-8 figure is a ONE-PIXEL-WIDE
#     line flanked by one pixel of floor on each side. A 5x5 ring cannot stand
#     on a 3-wide strip. So cells (1,4)..(4,4) and (5,1)..(5,3) are
#     un-occupiable whether or not colour 8 is passable, and the "walk the
#     ribbon" route is dead on geometry alone. Exactly one colour-8 cell has a
#     full 5x5 of non-void pixels: cell (5,0), rows 38-42 x cols 14-18. It sits
#     across the only floor path from the start to the bottom corridor.
#     Everything now turns on one cell, and one command tests it.

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
  landmark gate_cell  # arc-cell: (40, 16)
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

  theorem render_is_one_pixel_per_object "DISCHARGED, not pending -- kept as the record of the only quantitative prediction this manual has made and won. An object occupies exactly one cell, the raster-first cell of its declared arc-colour, painted in its color field; an object with no color field paints the wrong colour there; a colour absent from the frame stack anchors nothing and costs nothing. Predicted 68 unexplained pixels against an alternative of about 53, and 68 came back. The follow-up prediction, which is the new falsifier: certify has now seen seven states, so (63,61) has joined the dynamic set as a colour-9 cell of frame 0 that no object owns, and the dynamic set is 74 with 3 background in frame 0. This manual therefore predicts the NEXT responsibility report on frame 0 says exactly 69. If it says 68, the checker's board is not 'constant over all observed frames' and I have the wrong model of the checker rather than of the world."
    [probe: pending]

  theorem responsibility_ceiling_is_two_pixels "68, and next round 69, is not slack in the manual; it is the arithmetic maximum this language can reach here, and I want that on the record so no future round spends itself chasing it. An object is located by colour, so two objects of one colour land on one pixel and a colour explains at most one cell. The colours appearing on non-background dynamic cells of frame 0 are exactly 9 and 1. Colour 5 and colour 8 have raster-first cells at (7,13) and (9,39), both constant board cells, so objects in those colours explain nothing they were not already given. Two colours, two pixels, and both are already claimed by Marker and Unused. Full-frame responsibility is unreachable in this world and I do not pretend otherwise."
    [depends: render_is_one_pixel_per_object  probe: pending]

  theorem replay_can_never_pass_here "replay compares whole frames and frame 0 is already 68 pixels wrong before any rule fires, so 0/5 is structural and will stay 0/n for every n. The consequence I care about is diagnostic, not cosmetic: a replay failure whose divergence set is exactly the conceded ledger below is not evidence against any rule, and a replay failure that touches a cell OUTSIDE that ledger is evidence and must be answered. The ledger is written out precisely so that test can be run by eye."
    [depends: responsibility_ceiling_is_two_pixels  probe: pending]

  theorem the_mover_is_unnameable "the thing that plays this game is a 5x5 colour-9 ring with a one-pixel hole at its centre. It cannot be declared. Colour 9 is raster-first-claimed by the HUD at (1,1) in frames 0-4 and at (1,5) in frames 5-6, so any colour-9 object I declare lands on the HUD -- which is exactly what the arm did with Marker, correctly, and exactly what it did with the object called Player in the second draft, disastrously. mdl_segmenter offers no track for it either: under connected_components(4) with split_by_color off, the ring fuses with the colour-5 floor and the colour-8 line into obj3, 1006 cells, colour null. That fusion is also why cegis_miner concluded 'the world does not narrate as one mover'. It narrates as one mover. The mover is inside a 1006-cell blob and has no colour of its own. Therefore this manual contains NO movement rule, and cannot, and all movement knowledge lives in theorems and in the playbook."
    [probe: pending]

  theorem lattice_geometry "the maze is an 8x6 lattice of 5x5 cells at pitch 6. Cell (r,c) occupies rows 8+6r..12+6r and cols 14+6c..18+6c, for r=0..7 and c=0..5. Separator rows are 7+6r and separator columns are 13+6c; separators are themselves colour 5 where the neighbouring cells are floor, so they do not divide anything. Cell centres are (10+6r, 16+6c). Witnesses: the ring occupied exactly rows 8-12 x cols 14-18, then exactly rows 14-18 x cols 14-18, a displacement of exactly 6 with no intermediate frame reaching me; the ring's hole is at (10,16) and (16,16), each the exact centre of its cell; the goal dot is at (52,46), the exact centre of cell (7,5); the colour-8 blob is centred on (10,40), the exact centre of cell (0,4)."
    [probe: pending]

  theorem floor_map "the complete read of the static board, by lattice cell. Floor means all 25 pixels non-void. r=0: c=0,1,2,3,4 floor, c=5 void. r=1: c=0 floor, c=1 void, c=2 floor, c=3 void, c=4 three-wide ribbon, c=5 void. r=2: c=0,1,2 floor, c=3 void, c=4 ribbon, c=5 void. r=3 and r=4: c=0 floor, c=1,2,3 void, c=4 ribbon, c=5 void. r=5: c=0 is a full 5x5 of colour 8, c=1,2,3 are a three-ROW stripe at rows 39-41 only, c=4 is the ribbon junction with col 42 void, c=5 void. r=6: c=0 floor, rest void. r=7: c=0..5 all floor, the bottom corridor at rows 50-54 x cols 13-48. Consequence: the floor-only reachable set from the start is exactly the nine cells (0,0),(0,1),(0,2),(0,3),(0,4),(1,0),(1,2),(2,0),(2,1),(2,2),(3,0),(4,0) -- twelve cells -- and it does not contain the goal."
    [depends: lattice_geometry  probe: pending]

  theorem void_blocks_and_the_guard_language_is_inverted "colour 0 is wall and colour 5 is floor. Witness: cell (1,1), rows 14-18 x cols 20-24, is entirely colour 0, and key(4) fired from cell (1,0) at t4 moved nothing. Note the trap: free(x) in this DSL tests the BACKGROUND colour, which here is 0, i.e. exactly the cells that are NOT enterable. Any movement rule ever written here must be guarded with colored(x, 5) and never with free(x). What t4 does NOT establish is the rule for a PARTIALLY void destination: an all-void cell blocks, and whether a cell that is void at its edges but non-void at its centre blocks is untested."
    [depends: floor_map  probe: pending]

  theorem the_ribbon_is_too_narrow_for_the_ring "this is the sharpest deduction available from the static board and it kills half the search space without an experiment. The colour-8 figure is one pixel wide: a vertical stroke down col 40 from row 12 to row 41 with colour 5 at cols 39 and 41 and void at cols 38 and 42; a horizontal stroke along row 40 from col 40 back to col 14 with colour 5 at rows 39 and 41 and void at rows 38 and 42. Total width three. The mover is five wide. So cells (1,4),(2,4),(3,4),(4,4),(5,1),(5,2),(5,3),(5,4) cannot hold the ring no matter what colour 8 turns out to mean, and no route may pass through them. Exactly one colour-8 cell has a full 5x5 of non-void pixels: (5,0), rows 38-42 x cols 14-18, which is colour 8 everywhere except (39,14) and (41,14), which are colour 5."
    [depends: floor_map, lattice_geometry  probe: pending]

  theorem cell_five_zero_is_the_gate "combine floor_map with the_ribbon_is_too_narrow_for_the_ring and one cell decides the level. Column 0 is floor at r=0,1,2,3,4 and again at r=6,7; the bottom corridor r=7 runs all the way to the goal; between them sits (5,0), the colour-8 filled cell, gate_cell in the word table. There is no other join between the reachable twelve cells and the goal region. Therefore either the ring can enter (5,0), or the bracketed cell is unreachable and the win condition is something else entirely. No transition tests it and one command from (4,0) does. Because the reachable floor contains no other marked cell -- the pockets (1,2),(2,1),(2,2) are blank 5s with nothing drawn in them -- I now lean to 'colour 8 is simply walkable' rather than 'colour 8 is a door with a switch elsewhere', because there is nowhere for the switch to be. The competing reading survives only in the form below."
    [depends: the_ribbon_is_too_narrow_for_the_ring  probe: pending]

  theorem the_eight_line_may_be_a_wire "the alternative reading of the colour-8 figure, kept because it is cheap to keep and expensive to have missed. The figure is a connected line whose two ends are both distinguished: a 3x3 blob on the centre of cell (0,4), which IS reachable floor, and the filled 5x5 at (5,0), which is the gate. A line joining a reachable marked cell to the one blocking cell reads as button-and-door as naturally as it reads as a drawn path. If entry to (5,0) is refused, the next thing to try is standing on (0,4) and looking at whether (5,0) changes colour. Note that the ring standing on (0,4) would show the colour-8 blob through its central hole, the same visual signature the goal cell has with its colour-9 dot, which is a further reason to visit it."
    [depends: cell_five_zero_is_the_gate  probe: pending]

  theorem goal_is_the_cupped_cell "rows 48-56 x cols 42-50 is a 9x9 colour-5 box drawn around cell (7,5). Inside it colour 9 paints row 49 cols 43-49, row 55 cols 43-49 and col 49 rows 50-54: a cup open to the LEFT, which is the side the bottom corridor arrives from. A lone colour-9 pixel sits at (52,46), the exact centre of cell (7,5), and the ring's hole is at its own exact centre, so bringing the ring here makes the dot show through the hole. It is the only cell in the frame drawn this way and it is drawn in the ring's own colour. Read off the static board; no transition witnesses it. The shortest route consistent with floor_map is seven steps down column 0 and five steps right along the bottom corridor: twelve commands."
    [depends: lattice_geometry, floor_map  probe: pending]

  theorem direction_map_reading_a "1=up, 2=down, 3=left, 4=right. Every motion observation fits without exception: key(2) from (0,0) moved the ring down one cell (t2); key(1) from (0,0) is off-board and moved nothing (t1, and again t6); key(3) from (1,0) is off-board and moved nothing (t3); key(4) from (1,0) faces the all-void cell (1,1) and moved nothing (t4). Reading B from the third draft -- that key(1) and key(3) are simply unbound -- is now REFUTED, because at t6 key(1) advanced the tally, and an unbound key cannot advance a counter. Reading A's only remaining weakness is that it is untested off the boundary: every key(1) and key(3) so far was fired where the answer would be 'no' under any binding. One command settles it, and it must be fired from a cell with a real neighbour in that direction."
    [depends: floor_map  probe: pending]

  theorem tally_is_a_two_command_clock "row 63 is a 64-pixel colour-9 bar filling with colour 1 from the right. It advanced at t2, t4 and t6 and did not advance at t1, t3 or t5: a perfect alternation, coverage 6/6, one pixel per two commands, independent of which key was pressed, independent of whether anything moved, and unaffected by key(5). This replaces the third draft's reading of the bar as a count of processed move commands, which t6 refutes: the identical command from the identical cell tallied once and not the other time. Three of sixty-four are consumed, so on the clock reading about 122 commands remain against a twelve-command route -- not binding, but wandering is still what would kill this level rather than walls. THE HONEST CAVEAT: a perfect alternation over six samples is roughly a one-in-thirty accident, and zero_space already warned that six transitions constrain rank 4 of 370 features. Every single command tests this law for free and the playbook says to read it every time."
    [probe: pending]

  theorem hud_is_two_attempts_and_one_is_gone "two 3x3 slots at cols 1-3 and cols 5-7 with a 3-pixel underline at row 5 marking the active one. Frames 0-4: slot A is a colour-9 ring and underlined, slot B a colour-1 solid block. Frames 5-6: slot A is a colour-2 ring and unmarked, slot B a colour-9 RING and underlined. So the active slot shows the player's own icon in the player's own colour, an unused slot is a solid colour-1 block, and a spent slot is a colour-2 ring. key(5) did all of that in one nine-frame command and moved the ring back to its start, and the tally did NOT reset. Reading: two attempts, key(5) spends one and restarts the position. The competing reading -- 'objective cleared, next objective' -- is not dead but the position reset argues against it. Either way slot B is the LAST slot, and the guards on the three rules above encode that: with slot A at colour 2 and slot B at colour 9, none of them can fire again."
    [depends: key5_advances_marker, key5_marks_slot_a_spent, key5_consumes_slot_b  probe: pending]

  theorem spent_anchor_resolved "the third draft kept Spent on faith and named the price: 'if the next report shows a stray colour-2 pixel at (0,0), delete Spent'. It did not. The count came in at exactly the value predicted for a Spent that draws nothing in frame 0, so a declared object whose colour is absent from the frame is placed nowhere and costs nothing. Spent stays. Its untested half is what happens from t5 on, where colour 2 does exist and its raster-first cell is (1,1): if the arm anchors from the whole frame stack, Spent draws colour 2 at (1,1) and is right from t5 and wrong before it, and the per-frame counts will show that as a one-pixel improvement at t5 and no change at t0."
    [depends: render_is_one_pixel_per_object  probe: pending]

  theorem vacated_cell_repaints_to_five "when the ring left cell (0,0) at t2 those 24 pixels became colour 5, not background 0, and cell (1,0) did the same at t5. This is a fact about the world and a defect I cannot repair: nothing in the language repaints a cell an object has left, and a colour-5 Floor object would anchor at (7,13) and paint one pixel of a 1006-cell blob. The 24 pixels of whichever start cell is currently empty are conceded in every frame."
    [probe: pending]

  theorem cascade_length_is_a_signal "t2 returned 7 frames and t5 returned 9 for a single command; t1, t3, t4 and t6 returned 1 each, and t4 and t6 still changed a pixel. A multi-frame command is an animation of real motion; a single-frame command is an instant verdict. Only the last frame reaches me and cascade single_frame is the only value that compiles, so the intermediate slide is invisible -- but the frame COUNT is not, and it is a free channel: any future command that returns more than one frame moved something even if I cannot see what. Seven frames for a six-pixel displacement is quiet support for lattice_geometry."
    [probe: pending]

  theorem no_goal_section_on_purpose "the win condition I believe is 'the ring reaches goal_cell'. Its subject is unnameable, so writing it would either fail to compile or name the HUD marker and be false. An absent goal compiles to is_goal -> False, which under-claims; a goal about the wrong object over-claims and is refuted by the very first win. I under-claim, and the playbook carries the direction instead. goal_cell, gate_cell and start_cell are declared as landmarks with no rule referencing them for exactly one reason: the DSL has nowhere else to write a coordinate, and the playbook's distance heuristic needs a referent to name."
    [depends: goal_is_the_cupped_cell, the_mover_is_unnameable  probe: pending]

  theorem conceded_pixels "the honest ledger for frame 0, on the seven-state dynamic set of 74 cells, 3 of which are background there. Drawn correctly: 2 -- Marker at (1,1) and Unused at (1,5). Conceded: 7 of the HUD slot-A ring, 8 of the slot-B block, 3 of the slot-A underline, 24 of the player ring in cell (0,0), 24 of the repainted floor in cell (1,0), 3 of the tally bar. That is 7+8+3+24+24+3 = 69, which is the number predicted above. Every one of them fails for the same reason -- the object that owns them can be given exactly one Coord -- and not one of them is a missing rule. This violates full-frame responsibility knowingly and completely, and I would rather say so in one paragraph than declare seventy single-pixel objects that would satisfy the checker and teach nothing about the world."
    [depends: responsibility_ceiling_is_two_pixels, vacated_cell_repaints_to_five  probe: pending]
