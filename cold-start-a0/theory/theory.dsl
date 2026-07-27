# ============================================================================
# A0 说明书 — revision 3
#
# Adjudicated from artifacts/candidates.jsonl by the theorize step.
# Every clause here was written by hand after reading a proposal; the
# accept / reject / probe reasoning for each one is in ../THEORIZE_LOG.md.
#
# Frame axiom (declared here because the grammar has no place for it):
#   if no rule fires for an object, that object is unchanged.
#   The mined `*_still_*` rules are entailed by this and are therefore not
#   entered — see THEORIZE_LOG R-07.
# ============================================================================

word_table:
  board
  object Cart { pos: Coord, color: Int }
  object Button { pos: Coord, color: Int }
  object Door { pos: Coord, color: Int, present: Bool }
  Cart [segment: uniform_color ev: t0-t274 compress: 2967]
  Button [segment: uniform_color ev: t99 compress: -17]
  Door [segment: uniform_color ev: t99 compress: -13]

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule push_up [ev: t6,t16,t21 cov: 52/52]
    when act=push(Cart, up) and free(above(Cart)) then moved(Cart, up)

  rule push_down [ev: t0,t9,t12 cov: 62/62]
    when act=push(Cart, down) and free(below(Cart)) then moved(Cart, down)

  rule push_left [ev: t5,t20,t27 cov: 46/46]
    when act=push(Cart, left) and free(leftof(Cart)) then moved(Cart, left)

  rule push_right [ev: t3,t8,t10 cov: 52/52]
    when act=push(Cart, right) and free(rightof(Cart)) then moved(Cart, right)

  rule teleport_down [ev: t11,t103 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 3) then jumped(Cart, portal_exit)

  rule press_left [ev: t99 cov: 1/1]
    when act=push(Cart, left) and colored(leftof(Cart), 7) then recolored(Button, 8)

  rule door_opens_left [ev: t99 cov: 1/1]
    when act=push(Cart, left) and colored(leftof(Cart), 7) then vanished(Door)

goal:
  goal Cart.pos = (2, 7)

laws:
  invariant cart_unique count(Cart) = 1 [status: proven]
  invariant door_latch count(Button, 8) + count(Door) = 1 [status: proven]
  theorem press_is_direction_free "推向未按下的按钮就会按下它，无论从哪个方向推——但这一条只有一个见证，本世界的闩锁不可逆，证据永远补不齐"
    [depends: press_left probe: pending]
