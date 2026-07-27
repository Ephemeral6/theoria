# ============================================================================
# A2 说明书 — the complete manual, revision 1
#
# Adjudicated from artifacts/candidates.jsonl (the full sweep) by the theorize
# step.  Every clause was written by hand after reading a proposal; the
# accept / reject / probe reasoning for each one is in ../THEORIZE_LOG.md.
#
# This file is the CONTROL.  The exhibit is ../theory_holed.dsl, which is this
# manual with exactly one rule deleted.  Diff them: that diff is A2.
#
# ============================================================================

word_table:
  board
  object Cart { pos: Coord, color: Int }
  object Button { pos: Coord, color: Int }
  object Door { pos: Coord, color: Int, present: Bool }
  # compress: bits saved against a RESPONSIBILITY-COMPLETE alternative --
  # the same pixels encoded raw, frame-0 declaration included.  See
  # ../artifacts/concept_accounts.json and THEORIZE_LOG O-04.
  Cart [segment: uniform_color ev: t0-t247 compress: 1891]
  Button [segment: uniform_color ev: t90 compress: -5]
  Door [segment: uniform_color ev: t90 compress: -1]

semantics:
  frame persist                 # an object no firing rule mentions is unchanged
  conflict exclusive            # at most one rule per object per transition
  cascade single_frame          # one action -> one frame; guards read the pre-state

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule push_up [ev: t9,t11,t13 cov: 56/56]
    when act=push(Cart, up) and free(above(Cart)) then moved(Cart, up)

  rule push_down [ev: t3,t12,t16 cov: 51/51]
    when act=push(Cart, down) and free(below(Cart)) then moved(Cart, down)

  rule push_left [ev: t8,t10,t21 cov: 39/39]
    when act=push(Cart, left) and free(leftof(Cart)) then moved(Cart, left)

  rule push_right [ev: t2,t6,t15 cov: 43/43]
    when act=push(Cart, right) and free(rightof(Cart)) then moved(Cart, right)

  # The thin-evidence rule, and the one this whole spike is about.  One witness,
  # t183, and a live frontier: `tcolor(DOWN)==3` and `at(6,4)` both fit it
  # (engines_report.json, probes[0]).  Adjudicated to the colour guard on
  # description length -- see THEORIZE_LOG R-05 -- and the ambiguity is carried
  # openly as `teleport_is_colour_triggered` below rather than silently closed.
  rule teleport_down [ev: t183 cov: 1/1]
    when act=push(Cart, down) and colored(below(Cart), 3) then jumped(Cart, portal_exit)

  rule press_up [ev: t90 cov: 1/1]
    when act=push(Cart, up) and colored(above(Cart), 7) then recolored(Button, 8)

  rule door_opens_up [ev: t90 cov: 1/1]
    when act=push(Cart, up) and colored(above(Cart), 7) then vanished(Door)

goal:
  goal Cart.pos = (2, 7)

laws:
  invariant cart_unique count(Cart) = 1 [status: proven]
  invariant door_latch count(Button, 8) + count(Door) = 1 [status: proven]
  theorem teleport_is_colour_triggered "推向颜色 3 的格子就会被传送，而不是因为站在 (6,4) 这一格——两条守卫在扫描轨迹上不可分辨，本关的传送口只有一个，证据永远补不齐"
    [depends: teleport_down probe: pending]
