# theory.dsl -- Theoria manual, third draft. Six observed transitions.
#
# THIS DRAFT IS A REWRITE FORCED BY ONE MEASUREMENT, and that measurement is the
# most valuable thing learned this round, so it is stated first and in full.
#
# certify reported 69 unexplained pixels in frame 0. That number is not vague:
# it is derivable to the pixel, and deriving it pins down how this arm draws.
#   The 73 dynamic cells of frame 0 are
#     HUD slot A  rows 1-3 x cols 1-3 minus (2,2)   =  8   (colour 9)
#     HUD slot B  rows 1-3 x cols 5-7               =  9   (colour 1)
#     underline   row 5 cols 1-3 and cols 5-7       =  6   (9,9,9 / 0,0,0)
#     maze cell (0,0) rows 8-12  x cols 14-18 - ctr = 24   (colour 9)
#     maze cell (1,0) rows 14-18 x cols 14-18 - ctr = 24   (colour 5)
#     tally  (63,62),(63,63)                        =  2   (colour 9)
#   Of those, exactly 3 are background in frame 0 (row 5 cols 5-7), so 70 are
#   non-background. 70 - 69 = 1 cell was drawn correctly. That one cell is
#   (1,5): it is the ONLY dynamic cell missing from the divergence list, and it
#   is exactly where `Token { color: Int }  # arc-colour: 1` was placed.
#   So an object is drawn as ONE PIXEL at its pos, in its `color` field.
#   Two corollaries, both witnessed in the same report:
#     - Coord is the RASTER-FIRST cell of the object's colour, not a centroid:
#       Token landed on (1,5), the top-left of the colour-1 block, not (2,6).
#     - `Player { pos: Coord }` had NO color field, was placed at (1,1) (the
#       raster-first colour-9 cell) and painted colour 1 there -- manual_says 1,
#       world_says 9. A missing color field is a wrong pixel, not a blank one.
#
# Consequence, stated bluntly: a 24-pixel ring, a 9-cell block and a 62-cell bar
# CANNOT BE DRAWN by this manual, at any effort, because the language gives an
# object one Coord and the arm gives it one pixel. Full-frame responsibility is
# unreachable in this world; the best attainable is 70 - (number of objects
# whose colour anchors on a dynamic cell) and there are only three such colours.
# I therefore do not pretend, and the last section says exactly which pixels I
# concede and why.

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
  Marker [segment: mdl_obj0_ring3x3_colour9 ev: t0-t5 compress: 6]
  Unused [segment: mdl_obj1_solid3x3_colour1 ev: t0-t4 compress: 5]
  Spent [segment: mdl_obj5_ring3x3_colour2 ev: t5 compress: 1]

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

  theorem arm_draws_one_pixel_per_object "the derivation at the head of this file. 70 non-background dynamic cells in frame 0, 69 reported wrong, the single right one is (1,5) where the only object carrying a color field was anchored. This draft declares three objects whose colours anchor on dynamic cells: Marker anchors (1,1)=9 correct, Unused anchors (1,5)=1 correct, Spent is absent at frame 0. So this manual PREDICTS the next responsibility report will say 68 unexplained pixels in frame 0. If it instead says about 53, then objects are drawn as the whole segmenter track they bind to (8 cells for Marker plus 9 for Unused) and I have been too pessimistic; 68 and 53 are far enough apart that one number decides it. No third value is expected."
    [probe: pending]

  theorem replay_cannot_pass_here "0/5 transitions replay and the first divergence is at t=0, before any rule has fired. That is the render defect above, not a rule defect: 68 pixels of the opening frame are undrawable. Until the render model changes, a replay failure whose divergence set is the SAME undrawable pixels is not evidence against any rule, and a replay failure that touches a cell outside that set is. I am recording the distinction now so the next round does not spend itself repairing rules that were never wrong."
    [depends: key5_advances_marker  probe: pending]

  theorem the_player_ring_is_unnameable "the thing that actually plays this game is a 5x5 colour-9 ring with a one-pixel hole, at rows 8-12 x cols 14-18 in frames 0,1 and 5, and at rows 14-18 in frames 2,3,4. I cannot declare it. Two independent reasons. (a) One colour binds one object and colour 9 is raster-first-claimed by the HUD marker at (1,1); any colour-9 object I declare lands on the HUD, which is precisely what happened to the object named Player in the last draft. (b) mdl_segmenter chose connected_components(4) without split_by_color, and under that operator the ring is 4-connected to the colour-5 maze and the colour-8 route, fusing into obj3: 1006 cells, colour null, present in all six frames. There is no track for the ring, which is also why cegis_miner found that no track satisfies 'exactly one move event per transition' and concluded the world does not narrate as one mover. It narrates as one mover; the mover is inside a 1006-cell blob. I believe there are at least five distinct colour-9 entities -- ring, HUD marker, 3-pixel underline, the bracket at rows 49-55, and the row-63 bar -- and I say so here rather than declaring objects the arm cannot tell apart."
    [probe: pending]

  theorem no_goal_section_on_purpose "the win condition I believe is 'the ring reaches the bracketed cell'. Its subject cannot be declared (the_player_ring_is_unnameable), so writing it would either fail to compile or name the HUD marker and be false. An absent goal compiles to is_goal -> False, which under-claims; a goal about the wrong object over-claims and would be refuted by the next win. I chose to under-claim, and the playbook carries the direction instead."
    [probe: pending]

  theorem maze_geometry "the maze is a lattice of 5x5 cells at pitch 6: cell (r,c) occupies rows 8+6r..12+6r and cols 14+6c..18+6c, for r=0..7 and c=0..5; separators are rows 7+6r and cols 13+6c and are themselves colour 5, so adjacent floor cells are not divided. Cell centres are (10+6r, 16+6c). Witness: the ring occupied exactly rows 8-12 x cols 14-18 and then exactly rows 14-18 x cols 14-18, a displacement of 6, and the colour-8 blob sits on rows 9-11 x cols 39-41, the centre 3x3 of cell (0,4). Floor is colour 5 and void is colour 0."
    [probe: pending]

  theorem walkable_is_colour_five "inside the maze a cell is enterable when its pixels are colour 5 and blocked when they are colour 0. Witness: cell (1,1), rows 14-18 x cols 20-24, is all colour 0, and key(4) fired from cell (1,0) at t4 moved nothing. This INVERTS the guard language: free(x) tests the background colour, which here is 0, i.e. exactly the cells that are not enterable. Any future movement rule must be guarded with colored(x, 5) and never with free(x)."
    [probe: pending]

  theorem every_route_passes_through_the_colour_eight_cell "this is the sharpest thing the static board says and it decides the game. Reading floor off the frame: cell column 0 is floor at r=0,1,2,3,4,6,7; cells (r,1) are void for r=1 and r=4..6; cells (r,c) for c>=1 are void everywhere below row band 2 except the bottom corridor. The bottom corridor, rows 50-54, runs from col 13 to col 48, i.e. cells (7,0)..(7,5), and cell (7,5) is the bracketed target. So the only way from the start at (0,0) down to row 7 is straight down column 0 -- and cell (5,0), rows 38-42 x cols 14-18, is filled solid with colour 8. Therefore colour 8 is enterable, or the bracketed cell is unreachable and the win condition is something else entirely. No transition tests this. It is the one experiment that is worth more than all the others."
    [depends: maze_geometry, walkable_is_colour_five  probe: pending]

  theorem colour_eight_is_a_drawn_ribbon "colour 8 is one connected figure, not decoration: a 3x3 blob on the centre of cell (0,4); a vertical stroke down col 40 from row 12 to row 40, flanked by colour 5 at cols 39 and 41 and by void beyond, so it is a 3-wide ribbon laid ACROSS the void rather than a 5-wide floor corridor; a horizontal stroke along row 40 from col 40 back to col 14, the centre row of cell row 5; and cell (5,0) filled. Not one of its pixels moved in six frames, including across a real player move. So it is not an enemy that reacts. It reads as a route already traced, or a second agent's track, or a barrier. Note what it connects: (0,4), which the ring can reach along the open top band rows 8-12 cols 14-42, to (5,0), which the ring must reach anyway."
    [depends: every_route_passes_through_the_colour_eight_cell  probe: pending]

  theorem goal_is_the_bracketed_cell "rows 48-56 x cols 42-50 is a 9x9 box drawn in colour 5 around cell (7,5). Inside it, colour 9 paints row 49 cols 43-49, row 55 cols 43-49 and col 49 rows 50-54 -- a cup open to the LEFT, which is the side the bottom corridor arrives from -- plus a lone colour-9 pixel at (52,46). (52,46) is exactly the centre of cell (7,5), and the player ring's one-pixel hole sits exactly at its own centre. Bring the ring here and the dot shows through the hole. It is the only cell in the frame drawn this way and it is drawn in the ring's own colour. Read off the static board only; no transition witnesses it."
    [depends: maze_geometry  probe: pending]

  theorem directional_keys "reading A: key(1)=up, key(2)=down, key(3)=left, key(4)=right. Reading B: key(2) and key(4) are the only bound movement keys and key(1), key(3) are unbound. Every frame fits both. Evidence: key(2) moved the ring one cell down (t2); key(1) at t1 and key(3) at t3 were fired from the top-left cell, where up and left are off-board, and changed nothing at all, not even the tally; key(4) at t4 was fired from cell (1,0) whose right neighbour is void, moved nothing, but DID advance the tally. Reading A must then explain why an off-board attempt is not tallied while a blocked-by-void attempt is; reading B explains it for free. One experiment separates them, and it is now harder than it was: key(5) put the ring back at (0,0), so the ring must first be stepped down before key(1) or key(3) means anything."
    [probe: pending]

  theorem tally_bar "row 63 is a 64-cell colour-9 bar filling with colour 1 from the right: (63,63) at t2, (63,62) at t4, nothing at t1, t3 or t5. Two of 64 consumed. It reads as a budget of processed move commands. The shortest route I can see, straight down column 0 and right along the bottom corridor, is 12 cell-steps, so the budget is not the binding constraint yet -- but if it is a budget, wandering is what kills this level and not walls. No event in the language grows a region by one pixel, and colour 1 is claimed by Unused at (1,5), so I cannot draw the bar: (63,62) and (63,63) are conceded in every frame from t2 on."
    [probe: pending]

  theorem hud_is_two_attempt_slots "two 3x3 slots, cols 1-3 and cols 5-7, plus a 3-pixel underline at row 5 under exactly one of them. Frames 0-4: slot A is a colour-9 ring and underlined, slot B is a colour-1 SOLID block. Frame 5: slot A is a colour-2 ring and unmarked, slot B is a colour-9 RING and underlined, and the maze ring is back at its start. So the active slot displays the player's own icon in the player's own colour, an unused slot is a solid colour-1 block, and a used slot is a colour-2 ring. key(5) did all of that in one 9-frame command and the tally did NOT reset. Two readings: 'attempt spent, position reset' versus 'objective cleared, next objective'. They disagree about whether key(5) is to be hoarded or sought. The tally not resetting is weak evidence against a full restart, and the fact that slot B is now the LAST slot is the reason the playbook forbids spending it."
    [depends: key5_advances_marker, key5_marks_slot_a_spent, key5_consumes_slot_b  probe: pending]

  theorem spent_is_anchored_on_faith "Spent is absent from frame 0 -- cegis refused obj5 for exactly that reason -- so the arm has no colour-2 pixel to anchor it on when it builds the level instance, and it may place it at (0,0). If the next responsibility report shows a stray colour-2 pixel at (0,0) in every frame, that is this, and the fix is to delete Spent and lose the key(5) witness rather than pay a wrong pixel for it. I kept it because the rule it witnesses -- that key(5) marks slot A used -- is real knowledge about the world, and one speculative pixel is a cheap price to learn the arm's placement rule for a late-appearing object."
    [depends: key5_marks_slot_a_spent  probe: pending]

  theorem colour_one_collision "colour 1 paints slot B in frames 0-4 and also the tally fill from t2 on. Raster order puts (1,5) first while slot B exists, so Unused anchors correctly; from t5 the raster-first colour-1 cell is (63,62), but Unused has vanished by then, so the collision never bites. Recorded because it would bite immediately if slot B were ever restored."
    [probe: pending]

  theorem vacated_cell_repaints_to_five "when the ring left cell (0,0) at t2 those 24 pixels became colour 5, not background 0, and cell (1,0) did the same at t5. Nothing in the language repaints a cell an object has left, and declaring a colour-5 Floor object would anchor at (7,13) and paint one pixel of an 1006-cell blob. So the 24 pixels of whichever start cell is currently empty are conceded in every frame."
    [probe: pending]

  theorem cascade_length_is_a_signal "t2 returned 7 frames and t5 returned 9 for a single command; t1, t3, t4 returned 1 each, and t4 still changed a pixel. A multi-frame command is an animation of real motion; a single-frame command is an instant verdict. Only the last frame reaches me and cascade single_frame is the only value that compiles, so an intermediate cell-by-cell slide is invisible -- but the frame COUNT is not, and 7 frames for a 6-pixel displacement is quiet support for maze_geometry."
    [probe: pending]

  theorem conceded_pixels "the honest ledger, per frame, under the one-pixel render model. Drawn: 2 pixels (Marker, Unused; 2 again at t5 as Marker and Spent). Conceded: 7 of the HUD marker ring, 8 of slot B, 3 of the underline, 24 of the player ring, 24 of the vacated start cell, 2 of the tally = 68. Every one of them fails for the same reason -- the object that owns them can only be given one Coord -- and not one of them is a missing rule. This violates full-frame responsibility knowingly and completely, and I would rather say so in one paragraph than declare seventy single-pixel objects that would satisfy the checker and teach nothing."
    [depends: arm_draws_one_pixel_per_object  probe: pending]
