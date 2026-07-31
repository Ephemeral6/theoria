semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Cart { pos: Coord, color: Int }  # arc-colour: 2
  landmark item_4  # arc-cell: (5, 3)
  landmark item_3  # arc-cell: (6, 6)

events:
  event moved(o, dir)

rules:
  rule move_down [ev: t2 cov: 1/1]
    when act=key(2) and colored(below(Cart), 0) then moved(Cart, down)

laws:
  invariant cart_unique count(Cart) = 1 [status: proven]
  theorem single_move_observed "Only ACTION2 produced observable change: Cart moved from (1,1) to (2,1). ACTION1, ACTION3-5 had no effect."
    [probe: pending]
  theorem goal_unidentified "No goal state reached. Landmarks at (5,3) and (6,6) are likely significant but their role is unknown."
    [probe: pending]
