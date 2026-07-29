# ----------------------------------------------------------
# 素材 E: count-lock — the smallest world whose rule cannot be written in v0.3
#
# Forced by `worldgen`'s `t2-lock-fragile` (expressivity ledger **E-08**): a gate
# that opens once k tokens have been collected. The condition is a *cardinality*
# — how many tokens are gone — and the v0.3 guard language has no way to say it.
# `count` existed, but only in a `goal:` clause and only under `=`; a guard
# reaching it got `unknown predicate 'count'`.
#
# This fixture is deliberately the smallest world that needs the clause and
# nothing else. It is **not** a model of `t2-lock-fragile`: that world's collect
# rule moves the agent and consumes a token in one transition, which is a
# two-object write and a separate question (ledger X-1's shape). Taking a token
# is its own action here so that the fixture tests the counting predicate and
# not the event vocabulary.
#
# The three rules are the three cases a counting guard has to get right: below
# the threshold, at it, and the boundary between them.
# ----------------------------------------------------------

word_table:
  board
  object Agent { pos: Coord }
  object Token { pos: Coord, present: Bool }
  object Gate { pos: Coord, present: Bool }
  domain direction { up, down, left, right }
  landmark exit
  Agent [segment: uniform_color ev: synthetic compress: 0]
  Token [segment: uniform_color ev: synthetic compress: 0]
  Gate [segment: uniform_color ev: synthetic compress: 0]

semantics:
  frame     persist
  conflict  exclusive
  cascade   single_frame

events:
  event moved(o, dir) | vanished(o) writes {o} | stayed(o) writes {}

rules:
  rule walk forall ?d in direction
    when act=move(Agent, ?d) and free(ahead(Agent, ?d)) then moved(Agent, ?d)

  # Taking a token is an action on that token, not a side effect of walking.
  # See the header: a compound write is a different ledger row.
  rule take_t1
    when act=take(T1) and T1.present = true then vanished(T1)

  rule take_t2
    when act=take(T2) and T2.present = true then vanished(T2)

  rule take_t3
    when act=take(T3) and T3.present = true then vanished(T3)

  # E-08, the clause this fixture exists for. Three tokens collected and the
  # gate is gone; two and it is not. Nothing in the frame says "three" — the
  # only witness is how many tokens are no longer present.
  rule gate_opens
    when act=open(Gate) and count(Token, present = false) >= 3 then vanished(Gate)

  # The other side of the threshold, written as its own rule because a guard is
  # a conjunction and `conflict exclusive` wants the two cases disjoint.
  rule gate_holds
    when act=open(Gate) and not count(Token, present = false) >= 3 then stayed(Gate)

goal:
  goal Agent.pos = exit

laws:
  invariant tokens_never_return count(Token) = 3 [status: unproven]
