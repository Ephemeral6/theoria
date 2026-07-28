# ============================================================================
# A3 说明书 — the DOMAIN, revision 1
#
# Adjudicated from artifacts/candidates_l1.jsonl (level 1's sweep) by the
# theorize step.  Every clause was written by hand after reading a proposal;
# the accept / reject / probe reasoning for each is in ../THEORIZE_LOG.md.
#
# ---------------------------------------------------------------------------
# THIS FILE IS THE THING C3 CLAIMS TRAVELS.
#
# Theoria §1.10a: 说明书是 domain(跨关不变), 关卡布局是 problem(逐关实例) ——
# C3"迁移"的严格含义就是 domain 带得走。  So the test is arranged so that
# "travels" can be checked and not merely asserted:
#
#   * this file is compiled for BOTH levels, and
#     tests/test_transfer.py::test_the_domain_file_is_byte_identical_across_levels
#     asserts the two runs read the same sha256.  Not "equivalent" — the same
#     bytes.
#   * there is NOT ONE COORDINATE in this file.  No cell, no grid size, no
#     start, no goal.  Level data enters only through the two `landmark`
#     declarations below, whose values live in the problem instance, exactly
#     as CONTRACTS/dsl_grammar_v0.2.md specifies.
#   * there is no `goal:` section.  A goal cell is level data; PDDL puts it in
#     the problem file and so does A3.  See DECISIONS D-A3-004 — one of the
#     four backends agrees, and the other three do not, which is a finding
#     rather than a convenience.
#
# The clause count is 20 and it is *supposed* to look repetitive.  The guard
# language takes a literal direction (dsl_grammar v0.2, "Expressivity
# boundary"), so a mechanism that works in four directions costs four clauses.
# The miner's own better answer — one `?dir`-lifted rule at 225/225 — is on the
# record in THEORIZE_LOG R-09 and cannot be compiled by the Python backend.
# ============================================================================

word_table:
  board
  object Cart { pos: Coord, color: Int }
  object Switch { pos: Coord, color: Int }
  object Door { pos: Coord, color: Int, present: Bool }

  # The two free names that cross the domain/problem line (v0.2, E-04).  Their
  # values are supplied per level.  Declaring them is documentation only — no
  # backend reads a `landmark` declaration (D-A3-005) — but a reader of this
  # file alone can now tell level data from world data, which is the whole
  # reason v0.2 added the form.
  landmark exit_a
  landmark exit_b

  # compress: bits saved against a RESPONSIBILITY-COMPLETE alternative -- the
  # same pixels encoded raw, frame-0 declaration included.  See
  # ../artifacts/concept_accounts.json and THEORIZE_LOG O-04.
  Cart [segment: uniform_color ev: t0-t332 compress: 2371]
  Switch [segment: uniform_color ev: t0 compress: 7]
  Door [segment: uniform_color ev: t0 compress: 8]

semantics:
  frame persist                 # an object no firing rule mentions is unchanged
  conflict exclusive            # at most one rule per object per transition
  cascade single_frame          # one action -> one frame; guards read the pre-state

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o) | appeared(o)

rules:
  # ---- 1. push -------------------------------------------------------------
  # Four clauses for one mechanism; see the header on the `?dir` gap.
  rule push_up [ev: t0,t5,t8 cov: 69/69]
    when act=push(Cart, up) and free(above(Cart)) then moved(Cart, up)

  rule push_down [ev: t3,t4,t10 cov: 70/70]
    when act=push(Cart, down) and free(below(Cart)) then moved(Cart, down)

  rule push_left [ev: t13,t17,t26 cov: 40/40]
    when act=push(Cart, left) and free(leftof(Cart)) then moved(Cart, left)

  rule push_right [ev: t7,t16,t22 cov: 46/46]
    when act=push(Cart, right) and free(rightof(Cart)) then moved(Cart, right)

  # ---- 2. the portal, A -> exit_a -----------------------------------------
  # THE ADJUDICATION THIS WHOLE SPIKE TURNS ON.  The miner proposed these four
  # as four *ground displacements* — (dy,dx) = (0,+4), (-1,+3), (-1,+5),
  # (-2,+4) — because a displacement is what a frame diff shows.  Four
  # different vectors, and every one of them lands the Cart on the same
  # absolute cell.  `jumped(Cart, exit_a)` explains all four with one clause.
  #
  # The decisive fact is not description length, though: the displacement
  # reading is NOT WRITABLE.  `moved` carries exactly one cell and `jumped`
  # carries a landmark, whose value the contract puts in the problem instance —
  # the event language has no form for "displace by (-1,+3)".  The
  # domain/problem split is enforced here by the effect language, not merely
  # observed as a discipline.  The guard language offers no such protection:
  # see THEORIZE_LOG R-08, where the miner proposed `!at(3,1)` and only
  # judgement kept a level-1 coordinate out of this file.
  #
  # Level 1's evidence cannot separate the two readings; level 2 can, because
  # the manual must predict cells it has never seen.  THEORIZE_LOG R-05.
  rule teleport_a_up [ev: t48,t117 cov: 2/2]
    when act=push(Cart, up) and colored(above(Cart), 3) then jumped(Cart, exit_a)

  rule teleport_a_down [ev: t104,t167 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 3) then jumped(Cart, exit_a)

  rule teleport_a_left [ev: t70,t154,t217 cov: 4/4]
    when act=push(Cart, left) and colored(leftof(Cart), 3) then jumped(Cart, exit_a)

  rule teleport_a_right [ev: t91,t124 cov: 2/2]
    when act=push(Cart, right) and colored(rightof(Cart), 3) then jumped(Cart, exit_a)

  # ---- 3. the portal, B -> exit_b -----------------------------------------
  # The return leg.  Level 1's winning path never uses it — the sweep does,
  # because the world is reversible (F-12), and that is the entire reason this
  # clause exists to be carried.  Level 2 wins through this leg and through no
  # other, so if reversibility had not put it in the manual, transfer would
  # have failed and the failure would have looked like a fact about C3 rather
  # than a fact about level 1's exploration.
  rule teleport_b_up [ev: t112,t175 cov: 2/2]
    when act=push(Cart, up) and colored(above(Cart), 4) then jumped(Cart, exit_b)

  rule teleport_b_down [ev: t50,t119 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 4) then jumped(Cart, exit_b)

  rule teleport_b_left [ev: t87,t141,t249 cov: 4/4]
    when act=push(Cart, left) and colored(leftof(Cart), 4) then jumped(Cart, exit_b)

  rule teleport_b_right [ev: t97,t160 cov: 2/2]
    when act=push(Cart, right) and colored(rightof(Cart), 4) then jumped(Cart, exit_b)

  # ---- 4. the Switch, and the Door it drives ------------------------------
  # Two rules per guard, deliberately: the recolour and the Door event fire on
  # the same transitions, which is what `cascade single_frame` means and what
  # the PDDL backend reads off to fold them into one action.  The Switch is a
  # TOGGLE, not a latch — both polarities have witnesses because the world is
  # reversible, so `unpress` and `door_closes` are enumerated evidence and not
  # an analogy from `press`.  A0's latch could not do this and A0's manual
  # shipped a known hole because of it (A0′_REPORT §1).
  rule press_up [ev: t1,t18 cov: 2/2]
    when act=push(Cart, up) and colored(above(Cart), 7) then recolored(Switch, 8)

  rule door_opens_up [ev: t1,t18 cov: 2/2]
    when act=push(Cart, up) and colored(above(Cart), 7) then vanished(Door)

  rule press_down [ev: t64,t251 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 7) then recolored(Switch, 8)

  rule door_opens_down [ev: t64,t251 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 7) then vanished(Door)

  rule unpress_up [ev: t2 cov: 1/1]
    when act=push(Cart, up) and colored(above(Cart), 8) then recolored(Switch, 7)

  rule door_closes_up [ev: t2 cov: 1/1]
    when act=push(Cart, up) and colored(above(Cart), 8) then appeared(Door)

  rule unpress_down [ev: t58,t114 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 8) then recolored(Switch, 7)

  rule door_closes_down [ev: t58,t114 cov: 2/2]
    when act=push(Cart, down) and colored(below(Cart), 8) then appeared(Door)

laws:
  invariant cart_unique count(Cart) = 1 [status: proven]
  invariant switch_door_latch count(Switch, 8) + count(Door) = 1 [status: proven  source: zero_space]
  theorem portal_destination_is_absolute "推向颜色 3 的格子, 小车落到同一个绝对格 exit_a, 而不是相对自身位移——第一关的四个方向各给一个见证, 四个位移互不相同而落点相同; 这一条只有换关才能真正判决, 那正是 A3"
    [depends: teleport_a_up, teleport_a_down, teleport_a_left, teleport_a_right  probe: passed]
