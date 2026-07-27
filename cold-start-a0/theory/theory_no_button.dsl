# ============================================================================
# A0 说明书 — variant `a0-no-button`
#
# Derived from theory/theory.dsl by deleting every clause whose objects this
# instance does not contain.  Theoria 1.9 says dependency tracking should do
# this automatically ("说明书改一条规则,依赖它的玩法条目自动作废重审"); here it
# was done by hand and the deletions are listed, which is the honest version of
# the same discipline.
#
#   deleted   object Button        — no colour 7 anywhere in the trace
#   deleted   object Door          — cell (4,5) never changes, so it is board
#   deleted   rule press_left      — depends on Button
#   deleted   rule door_opens_left — depends on Door
#   deleted   invariant cart_unique, door_latch — door_latch depends on both
#   deleted   theorem press_is_direction_free   — depends on press_left
#
# Everything kept is unchanged, character for character.  That is the domain
# travelling and the problem not: the same four push rules and the same portal
# rule describe both instances.
#
# Frame axiom, as in the base manual: if no rule fires for an object, that
# object is unchanged.
# ============================================================================

word_table:
  board
  object Cart { pos: Coord, color: Int }
  Cart [segment: uniform_color ev: t0-t110 compress: 991]

events:
  event moved(o, dir) | jumped(o, dest)

rules:
  rule push_up [ev: t2,t8,t15 cov: 23/23]
    when act=push(Cart, up) and free(above(Cart)) then moved(Cart, up)

  rule push_down [ev: t0,t5,t9 cov: 28/28]
    when act=push(Cart, down) and free(below(Cart)) then moved(Cart, down)

  rule push_left [ev: t3,t12,t19 cov: 18/18]
    when act=push(Cart, left) and free(leftof(Cart)) then moved(Cart, left)

  rule push_right [ev: t1,t6,t10 cov: 22/22]
    when act=push(Cart, right) and free(rightof(Cart)) then moved(Cart, right)

  rule teleport_down [ev: t11 cov: 1/1]
    when act=push(Cart, down) and colored(below(Cart), 3) then jumped(Cart, portal_exit)

goal:
  goal Cart.pos = (2, 7)

laws:
  invariant right_room_locked w_room(Cart) = 0 [status: proven]
  theorem unsolvable_no_button "赢不了：小车永远待在左屋——它开局在左屋，而每一条推动规则都只把它送到相邻的空格，传送门也只把它送回左屋 (1,1)；隔墙上唯一的缺口 (4,5) 在这一关始终是障碍，没有任何规则能让它变空；目标格 (2,7) 在右屋，所以到不了。"
    [depends: push_up, push_down, push_left, push_right, teleport_down probe: passed]
