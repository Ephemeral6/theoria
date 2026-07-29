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
  rule move_down [ev: t2 cov: 1/1]
    when act=key(2) and colored(below(Cart), 0) then moved(Cart, down)

laws:
  invariant cart_unique count(Cart) = 1 [status: proven]
  theorem board_structure "Board (colour 1) forms the border and interior walls. Static and unchanged across all observed transitions."
    [probe: pending]
  theorem floor_terrain "Floor (colour 0) instances fill every free interior cell. When Cart moves away, floor is revealed; when Cart occupies a cell, floor is overlaid beneath (rendered or inferred as hidden). Arc-instances: all covers every 0-cell in every frame."
    [probe: pending]
  theorem single_action_moves "ACTION2 causes Cart to move down. ACTION1, ACTION3, ACTION4, ACTION5 produce no observable change in any of the observed 6 transitions."
    [probe: passed]
  theorem landmarks_role_unknown "Landmark_3 at (6,5) and Landmark_4 at (5,3) are static throughout. No goal state reached; their function is unknown."
    [probe: pending]
