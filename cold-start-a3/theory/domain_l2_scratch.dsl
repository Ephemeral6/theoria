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
#
# THE RULES ARE GROUND, AND THAT IS NOT THE READING.  Seven clauses became
# twenty-eight because the Python backend's guard and effect subset takes a
# literal direction and cannot compile `forall ?d in dir`.  The seven-clause
# lifted form is what the evidence actually supports; this is its expansion,
# written out by hand.  The theory did not change — see THEORIZE_LOG round 3
# and the per-direction witness table there.  Each clause below carries its
# own witnesses, and `ev: none cov: 0/0` marks a grounding the trace never
# saw; those fourteen are the price of the expansion and are meant to be
# visible rather than tidy.
#
# THE OBJECT NAMES ARE THE TOOLCHAIN'S, NOT MINE.  This pass named the mover
# `Agent` and the barrier `Gate`, for reasons argued in THEORIZE_LOG O-1 and
# O-2.  Four components hard-code `Cart` and `Door` -- `certify.replay`'s
# action names, `gen_python_a0`'s `mover=` default, the Lean invariant helpers'
# `Door_present` axis, and the goal binder's `state.Cart_pos` -- so the manual
# was renamed in round 4 to compile and replay at all.  Nothing about the world
# changed; a reader comparing this manual with another should treat these two
# names as carrying no information, because they carry none.  See THEORIZE_LOG
# round 4 and E-L2-5.
# ============================================================================

word_table:
  board
  object Cart   { pos: Coord, color: Int }
  object Door   { pos: Coord, color: Int, present: Bool }
  object Switch { pos: Coord, color: Int }
  # E-04.  Each warp lands the Cart on one fixed cell that no rule in this
  # grammar can compute from the pad, from the Cart's cell, or from the entry
  # direction: three different entry cells reach warp A and all three land on
  # the same cell, and likewise for warp B.  So the destination is a name here
  # and a coordinate in the problem instance.  Evidence in THEORIZE_LOG R-3.
  # The two names are `exit_a` / `exit_b` and not names of my choosing: the
  # problem builder registers its landmark dictionary under those keys, and a
  # `landmark` declaration that does not match is a KeyError at the first step.
  # Logged as E-L2-4 -- the contract does not say who owns a landmark's name.
  landmark exit_a
  landmark exit_b
  # compress: bits saved against a RESPONSIBILITY-COMPLETE alternative -- the
  # same pixels encoded raw, frame-0 declaration included.  Computed with
  # cold-start-a0/pipeline/concept_account.py; see THEORIZE_LOG O-5.  The Cart
  # pays for itself many times over.  The Door barely pays (+3 bits) and the
  # Switch does not (-1); both are admitted anyway, because `door_latch` names
  # them and the invariant language has no pixel-level paraphrase of it.
  Cart   [segment: uniform_color ev: t0-t336 compress: 2517]
  Door   [segment: uniform_color ev: t61,t140,t230 compress: 3]
  Switch [segment: uniform_color ev: t61,t140,t230 compress: -1]

semantics:
  # Checked against the trace, not assumed.  Under `frame reset` the Door would
  # reappear on the transition after t61; it stays absent for 79 consecutive
  # frames (t62-t140) and again for 106 (t231-t336), and the Switch keeps its
  # new colour just as long.
  frame persist
  # The five guard classes -- free, colour 3, colour 4, colour 7, colour 8 --
  # partition the target cell's colour, so no two rules over one object can
  # fire together.  Grounding does not weaken this: within one direction the
  # five classes are still disjoint, and two clauses for different directions
  # cannot both fire because only one action is taken.  Confirmed independently
  # by the miner (engines_report §mining.mutually_exclusive, all three tracks).
  conflict exclusive
  # 336 actions, 337 frames: one action, one successor.  The parenthetical in
  # the contract is load-bearing here and not decoration: `switch_press_down`
  # and `door_opens_down` share a guard that reads the Switch's *pre-state*
  # colour, and `switch_press_down` overwrites exactly that colour.  Applied in
  # file order instead, `door_opens_down` would read colour 8, find no match and
  # silently not fire -- the A0 sprint's bug, reachable here at t61, t140, t230.
  cascade single_frame

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o) | appeared(o)

rules:
  # -- step: 246 of the 336 transitions, all four directions witnessed. -------
  # `free`, `clear` and `tcolor==0` are extensionally identical on this trace
  # (probe_frontier says so, and so does the arithmetic); `free` is the shortest
  # and the one the sibling manuals and the backend already use.
  rule step_up [ev: t0,t1,t2,t3,t13 cov: 72/72]
    when act=push(Cart, up) and free(above(Cart)) then moved(Cart, up)

  rule step_down [ev: t6,t7,t8,t9,t10 cov: 78/78]
    when act=push(Cart, down) and free(below(Cart)) then moved(Cart, down)

  rule step_left [ev: t12,t30,t38,t48,t85 cov: 42/42]
    when act=push(Cart, left) and free(leftof(Cart)) then moved(Cart, left)

  rule step_right [ev: t26,t31,t32,t39,t56 cov: 54/54]
    when act=push(Cart, right) and free(rightof(Cart)) then moved(Cart, right)

  # -- warp A: colour 3.  Seven transitions, three entry directions, three -----
  # distinct entry cells, ONE destination.  The miner proposed this as three
  # ground displacements, all different -- the same fact written three times and
  # bound to this level's geometry.  A displacement cannot be the world's rule
  # if three of them produce one landing cell.  `warp_a_right` has no witness:
  # approaching this pad rightward would put the Cart inside the border wall,
  # so the grounding is unreachable in this level, not merely unobserved.
  rule warp_a_up [ev: t193,t293 cov: 2/2]
    when act=push(Cart, up) and colored(above(Cart), 3) then jumped(Cart, exit_a)

  rule warp_a_down [ev: t19,t74 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 3) then jumped(Cart, exit_a)

  rule warp_a_left [ev: t51,t130,t223 cov: 3/3]
    when act=push(Cart, left) and colored(leftof(Cart), 3) then jumped(Cart, exit_a)

  rule warp_a_right [ev: none cov: 0/0]
    when act=push(Cart, right) and colored(rightof(Cart), 3) then jumped(Cart, exit_a)

  # -- warp B: colour 4, a different destination.  Eight transitions, three ----
  # entry directions, three distinct entry cells, one destination.  Mined, again,
  # as three mutually different ground displacements.  `warp_b_down` is the
  # unreachable grounding here, for the same wall reason.
  rule warp_b_up [ev: t17,t66 cov: 2/2]
    when act=push(Cart, up) and colored(above(Cart), 4) then jumped(Cart, exit_b)

  rule warp_b_down [ev: none cov: 0/0]
    when act=push(Cart, down) and colored(below(Cart), 4) then jumped(Cart, exit_b)

  rule warp_b_left [ev: t181,t199,t281,t313 cov: 4/4]
    when act=push(Cart, left) and colored(leftof(Cart), 4) then jumped(Cart, exit_b)

  rule warp_b_right [ev: t24,t79 cov: 2/2]
    when act=push(Cart, right) and colored(rightof(Cart), 4) then jumped(Cart, exit_b)

  # -- the Switch is a toggle, not a latch: colours 7 and 8 both respond. ------
  # The Cart does not enter the Switch's cell on any of the three witnesses --
  # no rule moves it, and `frame persist` leaves it where it was.
  #
  # Only `down` is witnessed, and the manual still claims all four.  This is the
  # most extrapolated thing in the file and it is deliberate: the Switch has
  # walls on its three other sides, so the other groundings are unreachable in
  # this level rather than untested, and every other colour in this world
  # answers to the target cell alone (4/4 directions for colour 0, 4/4 for
  # colour 1, 3/3 reachable for colours 3 and 4).  Claiming `down` only would
  # assert that this one colour behaves differently, which the evidence does not
  # support either.  Carried openly as `toggle_is_direction_free`, probe pending.
  rule switch_press_up [ev: none cov: 0/0]
    when act=push(Cart, up) and colored(above(Cart), 7) then recolored(Switch, 8)

  rule switch_press_down [ev: t61,t230 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 7) then recolored(Switch, 8)

  rule switch_press_left [ev: none cov: 0/0]
    when act=push(Cart, left) and colored(leftof(Cart), 7) then recolored(Switch, 8)

  rule switch_press_right [ev: none cov: 0/0]
    when act=push(Cart, right) and colored(rightof(Cart), 7) then recolored(Switch, 8)

  rule door_opens_up [ev: none cov: 0/0]
    when act=push(Cart, up) and colored(above(Cart), 7) then vanished(Door)

  rule door_opens_down [ev: t61,t230 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 7) then vanished(Door)

  rule door_opens_left [ev: none cov: 0/0]
    when act=push(Cart, left) and colored(leftof(Cart), 7) then vanished(Door)

  rule door_opens_right [ev: none cov: 0/0]
    when act=push(Cart, right) and colored(rightof(Cart), 7) then vanished(Door)

  rule switch_release_up [ev: none cov: 0/0]
    when act=push(Cart, up) and colored(above(Cart), 8) then recolored(Switch, 7)

  rule switch_release_down [ev: t140 cov: 1/1]
    when act=push(Cart, down) and colored(below(Cart), 8) then recolored(Switch, 7)

  rule switch_release_left [ev: none cov: 0/0]
    when act=push(Cart, left) and colored(leftof(Cart), 8) then recolored(Switch, 7)

  rule switch_release_right [ev: none cov: 0/0]
    when act=push(Cart, right) and colored(rightof(Cart), 8) then recolored(Switch, 7)

  rule door_closes_up [ev: none cov: 0/0]
    when act=push(Cart, up) and colored(above(Cart), 8) then appeared(Door)

  rule door_closes_down [ev: t140 cov: 1/1]
    when act=push(Cart, down) and colored(below(Cart), 8) then appeared(Door)

  rule door_closes_left [ev: none cov: 0/0]
    when act=push(Cart, left) and colored(leftof(Cart), 8) then appeared(Door)

  rule door_closes_right [ev: none cov: 0/0]
    when act=push(Cart, right) and colored(rightof(Cart), 8) then appeared(Door)

laws:
  # Both invariants come from zero_space, which stated them as mod-2 laws over
  # 34 literal cells.  Rewritten here as object counts: same content, no
  # coordinates.  `open` and not `proven` because nothing has proved them --
  # an engine observed them holding across 336 transitions, which is not the
  # same claim, and certify has not been run against this manual.
  invariant cart_unique count(Cart) = 1 [status: open source: zero_space]
  invariant door_latch count(Door) + count(Switch, 8) = 1 [status: open source: zero_space]

  theorem toggle_is_direction_free "朝颜色 7 或 8 的格子按下就会翻转 Switch，与方向无关——但本关的 Switch 三面是墙，只能自上而下触碰，三个见证全是 DOWN；判定按世界的统一性外推（每种目标颜色的响应都只取决于颜色），不是量出来的。展开成四条 ground 规则后，其中三条 ev: none 的就是这条定理本身"
    [depends: switch_press_down, door_opens_down, switch_release_down, door_closes_down probe: pending]

  theorem warp_exit_is_a_landmark "两个传送口各自把 Cart 送到一个固定格子，与入口格和入口方向都无关：三个不同入口格给出同一个落点，位移读法要写三条规则且只对本关成立，落点读法只要一条"
    [depends: warp_a_up, warp_a_down, warp_a_left, warp_b_up, warp_b_left, warp_b_right probe: pending]

  theorem door_is_solid "Door 在场时挡路——它不是 free，因此 step 不触发；全轨迹只有 t18 一个见证，因为本关只有一格与 Door 相邻且可达"
    [depends: step_up, door_opens_down probe: pending]
