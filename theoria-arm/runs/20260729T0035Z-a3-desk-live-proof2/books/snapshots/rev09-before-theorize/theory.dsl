semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Floor { pos: Coord, color: Int }  # arc-colour: 0  arc-instances: all
  object Cart { pos: Coord, color: Int }  # arc-colour: 2
  object Landmark_3 { pos: Coord, color: Int }  # arc-colour: 3
  object Landmark_4 { pos: Coord, color: Int }  # arc-colour: 4

events:
  event moved(o, dir)

rules:
  rule move_down [ev: t2,t6,t7,t8 cov: 4/4]
    when act=key(2) and colored(below(Cart), 0) then moved(Cart, down)

laws:
  invariant cart_unique count(Cart) = 1 [status: proven]
  theorem board_static "Board (colour 1) forms the border and interior walls, unchanging across all observed transitions."
    [probe: pending]
  theorem floor_terrain "Floor (colour 0, with arc-instances: all) fills every unoccupied interior cell. When Cart moves away, floor is revealed; when Cart occupies a cell, it covers the floor visually."
    [probe: pending]
  theorem action2_moves_cart "ACTION2 causes Cart to move down one cell when the cell below is floor (colour 0). ACTION1, ACTION3, ACTION4, ACTION5 produce no observable change in the observed window."
    [probe: pending]
  theorem landmarks_static "Landmark_3 (colour 3) at (6,6) and Landmark_4 (colour 4) at (5,3) remain unchanged throughout. Their role is unknown."
    [probe: pending]
  theorem replay_init_mismatch "The replay failure at t=1 (manual predicts (1,1)=1, world is (1,1)=0) contradicts the shown initial frame where (1,1)=0. Frame initialization or transition semantics may have a subtlety not yet expressed in rules or object semantics."
    [probe: pending]
