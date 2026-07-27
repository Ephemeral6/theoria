# ----------------------------------------------------------
# 素材 A: Cart 世界 theory.dsl
# 2x3 网格, 色号 6 的 Cart 对象, push 四方向, teleport 低证据规则
# ----------------------------------------------------------

word_table:
  board
  object Cart { pos: Coord, color: Int }
  # E-04. `origin` is where the teleport lands. It used to be a free name the
  # backend guessed at; the domain names it, the problem instance locates it.
  landmark origin
  domain dir { up, down, left, right }

semantics:
  frame persist                 # an object no firing rule mentions is unchanged
  conflict exclusive            # push_up and teleport are disjoint: a wall is not free
  cascade single_frame          # one action -> one frame; guards read the pre-state

events:
  event moved(o, dir) | teleported(o, dest)

rules:
  # E-02. One clause, four directions. Written out by hand this was four rules
  # that each looked like a 3/3 or 2/2 claim; lifted, it is the one 10/10 claim
  # the evidence actually supports. Expansion regenerates `push_up`,
  # `push_down`, `push_left`, `push_right` under exactly those names.
  rule push forall ?d in dir [ev: t1,t2,t3,t4,t5 cov: 10/10]
    when act=push(Cart, ?d) and free(toward(Cart, ?d)) then moved(Cart, ?d)

  rule teleport [ev: t6 cov: 1/1]
    when act=push(Cart, up) and above(Cart) = wall then teleported(Cart, origin)

goal:
  goal Cart.pos = (0, 0)

laws:
  invariant conservation Cart.color = 6 [status: proven]
