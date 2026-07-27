# ============================================================================
# A2 说明书 — the HOLED manual.  This is the exhibit's input.
#
# `theory.dsl` with ONE clause deleted:
#
#     rule teleport_down [ev: t183 cov: 1/1]
#       when act=push(Cart, down) and colored(below(Cart), 3)
#       then jumped(Cart, portal_exit)
#
# and, following from that, the `jumped` event and the `portal_exit` landmark
# lose their only user.  Nothing else changes -- diff this file against
# theory.dsl and the deletion is the entire diff.
#
# ---------------------------------------------------------------------------
# WHY THIS DELETION, AND WHY IT IS ISOMORPHIC TO DC22'S DEFECT
# ---------------------------------------------------------------------------
#
# Theoria §1.3 describes DC22 structurally: the model replayed 175/175 frames
# correctly, was missing one **teleport rule**, and a complete search over it
# "correctly" proved a humanly-solvable goal unreachable -- because the missing
# rule never fired in the history and therefore owed no frame.  A2 reproduces
# that structure and nothing else about DC22; no upstream DC22 artifact was
# read (INC-004; DECISIONS D-A2-001).
#
# The four structural properties, each checked by machine rather than asserted:
#
#   1. the deleted rule is a teleport -- a non-adjacent move of the mover
#      (engines_diff.json: the only proposal with |dy|+|dx| > 1)
#   2. it fired exactly once in the sweep and never in the play record
#      (trace_summary.json: portal_transition = 183; history = raw[0..183])
#   3. the play record owes it nothing: this manual replays history_trace.jsonl
#      at 100% (exhibit_report.json: certify_cheap.green)
#   4. deleting it makes the goal unreachable, provably
#      (theory/generated_holed/theory.lean: `unsolvable`, axiom-free)
#
# It is deliberately a STRONGER setup than DC22's.  DC22's 175 frames were a
# play record with unknown coverage; this play record is exhaustive over its own
# strata -- it covers 163 of the 164 reachable (state, action) pairs with the
# Cart in the left room, and the single pair it omits is the one that fires the
# deleted rule.  Near-total evidence still leaves the hole.  That is §1.3's
# construction argument at its sharpest: the defect is not a coverage failure,
# it is what past-facing checking cannot see.
# ============================================================================

word_table:
  board
  object Cart { pos: Coord, color: Int }
  object Button { pos: Coord, color: Int }
  object Door { pos: Coord, color: Int, present: Bool }
  Cart [segment: uniform_color ev: t0-t183 compress: 1433]
  Button [segment: uniform_color ev: t90 compress: -5]
  Door [segment: uniform_color ev: t90 compress: -1]

semantics:
  frame persist
  conflict exclusive
  cascade single_frame

events:
  event moved(o, dir) | recolored(o, c) | vanished(o)

rules:
  rule push_up [ev: t9,t11,t13 cov: 38/38]
    when act=push(Cart, up) and free(above(Cart)) then moved(Cart, up)

  rule push_down [ev: t3,t12,t16 cov: 39/39]
    when act=push(Cart, down) and free(below(Cart)) then moved(Cart, down)

  rule push_left [ev: t8,t10,t21 cov: 32/32]
    when act=push(Cart, left) and free(leftof(Cart)) then moved(Cart, left)

  rule push_right [ev: t2,t6,t15 cov: 35/35]
    when act=push(Cart, right) and free(rightof(Cart)) then moved(Cart, right)

  rule press_up [ev: t90 cov: 1/1]
    when act=push(Cart, up) and colored(above(Cart), 7) then recolored(Button, 8)

  rule door_opens_up [ev: t90 cov: 1/1]
    when act=push(Cart, up) and colored(above(Cart), 7) then vanished(Door)

goal:
  goal Cart.pos = (2, 7)

laws:
  invariant cart_unique count(Cart) = 1 [status: proven]
  invariant door_latch count(Button, 8) + count(Door) = 1 [status: proven]
  theorem right_room_locked "小车永远到不了右边那个房间：第 5 列从第 1 行到第 7 行是完整的墙，而说明书里的每一条规则都只让小车走到相邻格，所以目标格 (2,7) 不可达"
    [depends: push_up, push_down, push_left, push_right probe: pending]
