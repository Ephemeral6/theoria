# ============================================================================
# A2 说明书 — the REPAIRED manual, revision 2.
#
# `theory_holed.dsl` plus one rule, adjudicated from probe P-01 rather than
# copied back from theory.dsl.  The two files agree on the teleport's guard and
# effect, and that agreement is a RESULT, not an input: the repair was written
# from `artifacts/probes.jsonl` alone, and A2_REPORT.md §5 diffs it against the
# control afterwards.  Compiled and certified against `probed_trace.jsonl` --
# the play record with the probe episodes appended, which is the evidence the
# theorizer holds after M8.
#
# The loop that produced this file, per Theoria §1.4 and §1.10d:
#
#   打脸  refutation.json    an 18-action episode ends on the goal, win=true,
#                            so `unsolvable` is false of the world
#   定位  locate_report.json exactly one of §1.4's three fires: a mispredicted
#                            step, at t=11, at (6,4), on DOWN
#   戳探  probes.jsonl       P-01, prediction written first: the holed manual
#                            said "stays", the world jumped three cells to (7,6)
#   修订  this file
#   重证  repair_report.json the old certificate dies, a true one replaces it
#   解出  plan_repaired.json SAT in 18, and the world agrees
# ============================================================================

word_table:
  board
  object Cart { pos: Coord, color: Int }
  object Button { pos: Coord, color: Int }
  object Door { pos: Coord, color: Int, present: Bool }
  Cart [segment: uniform_color ev: t0-t195 compress: 1521]
  Button [segment: uniform_color ev: t90 compress: -5]
  Door [segment: uniform_color ev: t90 compress: -1]

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o)

rules:
  rule push_up [ev: t9,t11,t13 cov: 40/40]
    when act=push(Cart, up) and free(above(Cart)) then moved(Cart, up)

  rule push_down [ev: t3,t12,t16 cov: 40/40]
    when act=push(Cart, down) and free(below(Cart)) then moved(Cart, down)

  rule push_left [ev: t8,t10,t21 cov: 33/33]
    when act=push(Cart, left) and free(leftof(Cart)) then moved(Cart, left)

  rule push_right [ev: t2,t6,t15 cov: 36/36]
    when act=push(Cart, right) and free(rightof(Cart)) then moved(Cart, right)

  # THE REPAIR.  One witness, t194, and it is a probe rather than a lucky
  # observation: P-01 predicted three outcomes before acting, the world produced
  # the third, and the other two are refuted on the record.  The guard is the
  # colour test rather than `at(6,4)` on description length -- P-03 established
  # that no experiment in this world can separate them, so the choice is honest
  # only if it is declared, which is what the pending theorem below does.
  rule teleport_down [ev: t194 cov: 1/1]
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
  theorem pocket_unreachable "格子 (7,1) 是地板，但它四邻全是墙，而说明书里能移动小车的规则只有相邻推动和一条传送——传送的落点是 (7,6)——所以没有任何可达状态让小车站上 (7,1)"
    [depends: push_up, push_down, push_left, push_right, teleport_down probe: passed]
  theorem teleport_is_colour_triggered "推向颜色 3 的格子就会被传送，而不是因为站在 (6,4) 这一格——本关只有一个传送口，两条守卫在这个世界里外延相同，实验分不开（probes.jsonl P-03），按描述长度裁决，证据永远补不齐"
    [depends: teleport_down probe: pending]
