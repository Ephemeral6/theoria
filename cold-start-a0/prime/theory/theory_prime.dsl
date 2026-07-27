# ============================================================================
# A0′ 说明书 — revision 1
#
# Adjudicated from prime/artifacts/candidates.jsonl.  Verdicts and reasoning:
# prime/THEORIZE_LOG.md.  Evidence is INCOMPLETE by design — the explorer stops
# at 40% of the exhaustive walk (107/228 state-action pairs), so several rules
# below carry `probe: pending` rather than a claim.
# ============================================================================

word_table:
  board
  object Cart { pos: Coord, color: Int }
  object Switch { pos: Coord, color: Int }
  object Door { pos: Coord, color: Int, present: Bool }
  Cart [segment: uniform_color ev: t0-t109 compress: 1698]
  Switch [segment: uniform_color ev: t12-t106 compress: -13]
  Door [segment: uniform_color ev: t12-t106 compress: -9]

semantics:
  frame persist                 # an object no firing rule mentions is unchanged
  conflict exclusive            # at most one rule per object per transition
  cascade single_frame          # one action -> one frame; guards read the pre-state

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o) | appeared(o)

rules:
  # -- the Cart moves onto floor ------------------------------------------
  rule push_up [ev: t12,t39 cov: 17/17]
    when act=push(Cart, up) and free(above(Cart)) then moved(Cart, up)

  rule push_down [ev: t0,t5,t9 cov: 26/26]
    when act=push(Cart, down) and free(below(Cart)) then moved(Cart, down)

  rule push_left [ev: t3,t46 cov: 16/16]
    when act=push(Cart, left) and free(leftof(Cart)) then moved(Cart, left)

  rule push_right [ev: t1,t38 cov: 23/23]
    when act=push(Cart, right) and free(rightof(Cart)) then moved(Cart, right)

  # -- the Portal --------------------------------------------------------
  rule teleport_down [ev: t11,t43 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 3) then jumped(Cart, portal_exit)

  # -- pushing into colour 7 turns it 8 and takes the Door away -----------
  rule switch_on_up [ev: t12 cov: 1/1]
    when act=push(Cart, up) and colored(above(Cart), 7) then recolored(Switch, 8)
  rule switch_on_down [ev: t43 cov: 1/1]
    when act=push(Cart, down) and colored(below(Cart), 7) then recolored(Switch, 8)
  rule switch_on_left [ev: t106 cov: 1/1]
    when act=push(Cart, left) and colored(leftof(Cart), 7) then recolored(Switch, 8)
  rule switch_on_right [ev: t11 cov: 1/1]
    when act=push(Cart, right) and colored(rightof(Cart), 7) then recolored(Switch, 8)

  rule door_opens_up [ev: t12 cov: 1/1]
    when act=push(Cart, up) and colored(above(Cart), 7) then vanished(Door)
  rule door_opens_down [ev: t43 cov: 1/1]
    when act=push(Cart, down) and colored(below(Cart), 7) then vanished(Door)
  rule door_opens_left [ev: t106 cov: 1/1]
    when act=push(Cart, left) and colored(leftof(Cart), 7) then vanished(Door)
  rule door_opens_right [ev: t11 cov: 1/1]
    when act=push(Cart, right) and colored(rightof(Cart), 7) then vanished(Door)

  # -- pushing into colour 8 turns it 7 and brings the Door back ----------
  rule switch_off_up [ev: t39 cov: 1/1]
    when act=push(Cart, up) and colored(above(Cart), 8) then recolored(Switch, 7)
  rule switch_off_down [ev: t46 cov: 1/1]
    when act=push(Cart, down) and colored(below(Cart), 8) then recolored(Switch, 7)
  rule switch_off_left [ev: t85 cov: 1/1]
    when act=push(Cart, left) and colored(leftof(Cart), 8) then recolored(Switch, 7)
  rule switch_off_right [ev: t38 cov: 1/1]
    when act=push(Cart, right) and colored(rightof(Cart), 8) then recolored(Switch, 7)

  rule door_shuts_up [ev: t39 cov: 1/1]
    when act=push(Cart, up) and colored(above(Cart), 8) then appeared(Door)
  rule door_shuts_down [ev: t46 cov: 1/1]
    when act=push(Cart, down) and colored(below(Cart), 8) then appeared(Door)
  rule door_shuts_left [ev: t85 cov: 1/1]
    when act=push(Cart, left) and colored(leftof(Cart), 8) then appeared(Door)
  rule door_shuts_right [ev: t38 cov: 1/1]
    when act=push(Cart, right) and colored(rightof(Cart), 8) then appeared(Door)

goal:
  goal Cart.pos = (2, 7)

laws:
  invariant cart_unique count(Cart) = 1 [status: proven]
  invariant door_mirrors_switch count(Switch, 8) + count(Door) = 1 [status: proven]
  theorem toggle_is_direction_free "推向开关就会把它翻面，无论从哪个方向推，也无论它当前是 7 还是 8——这一条八个方向-状态组合各有一个见证，是证据支持的推广，不是类比"
    [depends: switch_on_up, switch_off_up probe: pending]
