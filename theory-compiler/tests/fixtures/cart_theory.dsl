# ----------------------------------------------------------
# 素材 A: Cart 世界 theory.dsl
# 2x3 网格, 色号 6 的 Cart 对象, push 四方向, teleport 低证据规则
# ----------------------------------------------------------

word_table:
  board
  object Cart { pos: Coord, color: Int }

events:
  event moved(o, dir) | teleported(o, dest)

rules:
  rule push_up [ev: t1,t2,t3 cov: 3/3]
    when act=push(Cart, up) and free(above(Cart)) then moved(Cart, up)

  rule push_down [ev: t1,t2,t3 cov: 3/3]
    when act=push(Cart, down) and free(below(Cart)) then moved(Cart, down)

  rule push_left [ev: t4,t5 cov: 2/2]
    when act=push(Cart, left) and free(left(Cart)) then moved(Cart, left)

  rule push_right [ev: t4,t5 cov: 2/2]
    when act=push(Cart, right) and free(right(Cart)) then moved(Cart, right)

  rule teleport [ev: t6 cov: 1/1]
    when act=push(Cart, up) and above(Cart) = wall then teleported(Cart, origin)

goal:
  goal Cart.pos = (0, 0)

laws:
  invariant conservation Cart.color = 6 [status: proven]
