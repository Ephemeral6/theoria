# ============================================================================
# L2-SCRATCH 说明书 — the from-scratch control arm's manual, induced from
# level 2's own evidence and nothing else.
#
# Adjudicated by hand from artifacts/candidates_l2_scratch.jsonl (35 rows: 3
# object hypotheses, 30 rule hypotheses, 2 invariants) and, where a proposal
# needed checking rather than believing, from artifacts/l2_sweep.jsonl itself
# (337 frames, 336 transitions).  The accept / reject / open ruling for every
# candidate family is in ../THEORIZE_LOG_L2_SCRATCH.md.
#
# There is deliberately no `goal:` section and no coordinate anywhere in this
# file.  The board layout, the two warp exits and the winning cell are level
# data and live in the problem instance — dsl_grammar_v0.2 §Expressivity
# boundary.  The miner offered eleven frontier entries whose guards name a
# literal cell, over seven rule families; every one of them was rejected on
# that ground, and the cells themselves are named only in
# ../THEORIZE_LOG_L2_SCRATCH.md R-2, never here.
# ============================================================================

word_table:
  board
  object Agent  { pos: Coord, color: Int }
  object Gate   { pos: Coord, color: Int, present: Bool }
  object Switch { pos: Coord, color: Int }
  # E-04.  Each warp lands the Agent on one fixed cell that no rule in this
  # grammar can compute from the pad, from the Agent's cell, or from the entry
  # direction: three different entry cells reach warp A and all three land on
  # the same cell, and likewise for warp B.  So the destination is a name here
  # and a coordinate in the problem instance.  Evidence in THEORIZE_LOG R-3.
  landmark warp_a_exit
  landmark warp_b_exit
  # E-02.  The world's response to an action is a function of the colour of the
  # cell the action points at; the direction only says which cell that is.  One
  # clause per response, four groundings each.
  domain dir { up, down, left, right }
  # compress: bits saved against a RESPONSIBILITY-COMPLETE alternative -- the
  # same pixels encoded raw, frame-0 declaration included.  Computed with
  # cold-start-a0/pipeline/concept_account.py; see THEORIZE_LOG O-1.  The Agent
  # pays for itself many times over.  The Gate barely pays (+3 bits) and the
  # Switch does not (-1); both are admitted anyway, because `gate_latch` names
  # them and the invariant language has no pixel-level paraphrase of it.
  Agent  [segment: uniform_color ev: t0-t336 compress: 2517]
  Gate   [segment: uniform_color ev: t61,t140,t230 compress: 3]
  Switch [segment: uniform_color ev: t61,t140,t230 compress: -1]

semantics:
  # Checked against the trace, not assumed.  Under `frame reset` the Gate would
  # reappear on the transition after t61; it stays absent for 79 consecutive
  # frames (t62-t140) and again for 106 (t231-t336), and the Switch keeps its
  # new colour just as long.
  frame persist
  # The five guard classes -- free, colour 3, colour 4, colour 7, colour 8 --
  # partition the target cell's colour, so no two rules over one object can
  # fire together.  Confirmed independently by the miner
  # (engines_report §mining.mutually_exclusive, true for all three tracks).
  conflict exclusive
  # 336 actions, 337 frames: one action, one successor.  The parenthetical in
  # the contract is load-bearing here and not decoration: `switch_press` and
  # `gate_opens` share a guard that reads the Switch's *pre-state* colour, and
  # `switch_press` overwrites exactly that colour.  Applied in file order
  # instead, `gate_opens` would read colour 8, find no match and silently not
  # fire -- the A0 sprint's bug, reachable in this world at t61, t140, t230.
  cascade single_frame

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o) | appeared(o)

rules:
  # 246 of the 336 transitions.  `free`, `clear` and `tcolor==0` are
  # extensionally identical on this trace (probe_frontier says so, and so does
  # the arithmetic); `free` is the shortest and the one the sibling manuals use.
  rule step forall ?d in dir [ev: t0,t6,t12,t26 cov: 246/246]
    when act=push(Agent, ?d) and free(toward(Agent, ?d)) then moved(Agent, ?d)

  # Seven transitions, three entry directions, three distinct entry cells, one
  # destination.  The miner proposed this as three ground displacements, one per
  # entry direction, all different -- the same fact written three times and
  # bound to this level's geometry.  A displacement cannot be the world's rule
  # if three of them produce one landing cell.
  rule warp_a forall ?d in dir [ev: t19,t51,t74,t130,t193,t223,t293 cov: 7/7]
    when act=push(Agent, ?d) and colored(toward(Agent, ?d), 3) then jumped(Agent, warp_a_exit)

  # Eight transitions, three entry directions, three distinct entry cells, one
  # destination -- a different one from warp_a's.  Mined, again, as three
  # mutually different ground displacements.
  rule warp_b forall ?d in dir [ev: t17,t24,t66,t79,t181,t199,t281,t313 cov: 8/8]
    when act=push(Agent, ?d) and colored(toward(Agent, ?d), 4) then jumped(Agent, warp_b_exit)

  # The Switch is a toggle, not a latch: colour 7 and colour 8 both respond.
  # The Agent does not enter the Switch's cell on any of the three witnesses --
  # no rule moves it, and `frame persist` leaves it where it was.
  rule switch_press forall ?d in dir [ev: t61,t230 cov: 2/2]
    when act=push(Agent, ?d) and colored(toward(Agent, ?d), 7) then recolored(Switch, 8)

  rule gate_opens forall ?d in dir [ev: t61,t230 cov: 2/2]
    when act=push(Agent, ?d) and colored(toward(Agent, ?d), 7) then vanished(Gate)

  rule switch_release forall ?d in dir [ev: t140 cov: 1/1]
    when act=push(Agent, ?d) and colored(toward(Agent, ?d), 8) then recolored(Switch, 7)

  rule gate_closes forall ?d in dir [ev: t140 cov: 1/1]
    when act=push(Agent, ?d) and colored(toward(Agent, ?d), 8) then appeared(Gate)

laws:
  # Both invariants come from zero_space, which stated them as mod-2 laws over
  # 34 literal cells.  Rewritten here as object counts: same content, no
  # coordinates.  `open` and not `proven` because nothing has proved them --
  # an engine observed them holding across 336 transitions, which is not the
  # same claim, and certify has not been run against this manual.
  invariant agent_unique count(Agent) = 1 [status: open source: zero_space]
  invariant gate_latch count(Gate) + count(Switch, 8) = 1 [status: open source: zero_space]

  theorem toggle_is_direction_free "朝颜色 7 或 8 的格子按下就会翻转 Switch，与方向无关——但本关的 Switch 三面是墙，只能自上而下触碰，三个见证全是 DOWN；判定按世界的统一性外推（每种目标颜色的响应都只取决于颜色），不是量出来的"
    [depends: switch_press, gate_opens, switch_release, gate_closes probe: pending]

  theorem warp_exit_is_a_landmark "两个传送口各自把 Agent 送到一个固定格子，与入口格和入口方向都无关：三个不同入口格给出同一个落点，位移读法要写三条规则且只对本关成立，落点读法只要一条"
    [depends: warp_a, warp_b probe: pending]

  theorem gate_is_solid "Gate 在场时挡路——它不是 free，因此 step 不触发；全轨迹只有 t18 一个见证，因为本关只有一格与 Gate 相邻且可达"
    [depends: step, gate_opens probe: pending]
