# ============================================================================
# push 说明书 — the DOMAIN, revision 1.
#
# Adjudicated from ONE world's trace: worldgen's `t1-push-open`, 41 frames, 40
# actions, the whole of `raw_trace.jsonl` and nothing else.  `spec.json`'s
# legend was read for the colour of the block; `ground_truth.json`,
# `coverage.json` and `reversibility.json` were not opened before this file was
# written, and `worldgen/README.md` marks all three "scoring only".
#
# ---------------------------------------------------------------------------
# WHY THIS FILE EXISTS AT ALL
#
# A6 needs a domain that is carried between two worlds a *different track* built
# and that this one did not design around.  A3's domain travels between two
# levels of A3's own world; that is the weakest interesting reading of C3 and
# A3_REPORT §6 says so.  `t1-push-open` and `t1-push-corridor` share a mechanism
# family and share no layout, no grid size, no start cell and no goal — the
# catalogue's own `variant_delta` calls the pair "same mechanism, dead-end
# corridor instead of an open room" — so a domain that compiles for both is
# being asked a slightly harder question than A3 asked.
#
# THERE IS NOT ONE COORDINATE IN THIS FILE.  No cell, no grid size, no start, no
# goal, and no `goal:` section: a goal cell is level data and belongs to the
# problem instance (D-A3-004).  The two colour literals below are world data,
# not level data, and `PACK.json`'s `requires.guard_colours` is where a receiver
# is told to check them against the frame before trusting them — `worldgen`
# assigns colours **per world** out of a pool (`worldgen/core/types.py`), so a
# carried colour literal is a carried assumption and this pack does not let it
# travel unchecked.
#
# ---------------------------------------------------------------------------
# THE SHAPE OF THE EVIDENCE, STATED BEFORE THE CLAUSES
#
# `walk` is witnessed in all four directions.  `push` is witnessed **twice, both
# times rightward** (t13, t30), and the world's own catalogue entry says why: the
# gap in the divider is horizontal, so no vertical shove is available to the
# explorer at all.  Six of the twelve clauses below therefore rest on symmetry
# rather than on a witness, and they say `ev: symmetry` instead of a t-list.
#
# (This line said "eight" until 2026-07-29, when the scorer counted the brackets
# instead of trusting the prose and reported both numbers side by side rather
# than quietly using the right one.  The six are `shove_up/down/left` and
# `block_up/down/left`; the rightward pair carries `ev: t13,t30`.)
#
# That is the A0 failure mode being walked into deliberately and with the light
# on.  A0 generalised from a single witness and shipped a manual wrong in three
# places (A0′_REPORT §1).  The difference here is that the generalisation is
# *stated as one* and then *scored*: `runs/…/scoring_push_manual.json` replays
# this manual against every reachable transition of both worlds, including every
# vertical shove the explorer never reached, and reports the verdict.  A guess
# that is measured afterwards is a different object from a guess that is not.
#
# THE VERDICT, now that the file exists and not before: 256 transitions across
# both worlds, zero disagreements — and that is a smaller result than it sounds.
# Four of the six symmetry clauses were exercised by **exactly one transition
# each**, all four in `t1-push-open` (the corridor's block sits in a one-wide row
# and admits no vertical shove at all).  The other two — `shove_left` and
# `block_left` — are exercised by **zero** transitions in either world: in the
# open room the agent can never get to the block's right-hand side, and in the
# corridor it cannot reach that side by construction.  They are unrefuted and
# unvindicated, which is not the same as correct, and the artefact keeps the two
# lists apart so nobody can add them up.
#
# The alternative — four clauses instead of twelve, and a manual that is silent
# about vertical shoves — is worse and not more honest: silence is not the same
# as "the block does not move", but `frame persist` makes the compiled predictor
# say exactly the second thing.  A manual cannot abstain.
#
# The repetition is the guard language's, not this author's: it takes a literal
# direction (dsl_grammar v0.2, "Expressivity boundary"), so a mechanism that
# works in four directions costs four clauses, and one that moves two objects
# costs two clauses per direction.  THEORIZE_LOG R-09 is the standing record of
# the `?dir`-lifted rule the Python backend cannot compile.
# ============================================================================

word_table:
  board
  object Cart { pos: Coord, color: Int }
  object Block { pos: Coord, color: Int }

  # `Cart` is the thing the action moves.  The name is not descriptive here —
  # what `worldgen` renders is an agent, not a cart — and it is kept anyway:
  # `gen_pddl_a0.generate_pddl` looks the mover up by the literal string "Cart"
  # (`gen_pddl_a0.py:113`), so a manual that called it `Agent` would not compile
  # to a planning form at all.  Recorded as a naming coupling, not adopted as a
  # convention: PACK.json's `requires.mover` is where a receiver reads it.
  Cart [segment: uniform_color ev: t0-t40]
  Block [segment: uniform_color ev: t0-t40]

semantics:
  frame persist                 # an object no firing rule mentions is unchanged
  conflict exclusive            # at most one rule per object per transition
  cascade single_frame          # one action -> one frame; guards read the pre-state

events:
  event moved(o, dir) | jumped(o, dest) | recolored(o, c) | vanished(o) | appeared(o)

rules:
  # ---- 1. walking ----------------------------------------------------------
  # The cheap half, and the fully witnessed one.  `free(x)` is "the rendered
  # frame shows background at x", so it is false at a wall AND false at the
  # Block — which is what makes the walk clauses and the shove clauses below
  # mutually exclusive under `conflict exclusive` without either mentioning the
  # other.
  rule step_up [ev: t7,t10,t23,t26 cov: 5/5]
    when act=push(Cart, up) and free(above(Cart)) then moved(Cart, up)

  rule step_down [ev: t0,t9,t16,t25 cov: 5/5]
    when act=push(Cart, down) and free(below(Cart)) then moved(Cart, down)

  rule step_left [ev: t2,t8,t15,t18 cov: 7/7]
    when act=push(Cart, left) and free(leftof(Cart)) then moved(Cart, left)

  rule step_right [ev: t5,t12,t21,t28 cov: 6/6]
    when act=push(Cart, right) and free(rightof(Cart)) then moved(Cart, right)

  # ---- 2. the shove: the Cart's half --------------------------------------
  # THE ADJUDICATION THIS PACK TURNS ON, and the one only a second world can
  # settle.  Both witnesses are the same rightward shove in the same row, so
  # level 1's evidence cannot separate two readings:
  #
  #   (a) the Cart may enter the cell the Block vacates — a RELATIVE fact about
  #       the pair, expressible as `colored(rightof(Cart), 2)` and nothing else;
  #   (b) the Cart may enter column 4 of row 2 — an ABSOLUTE fact about this
  #       level, which the miner would happily have proposed as `!at(2,3)` and
  #       which THEORIZE_LOG R-08 records A3 refusing for the same reason.
  #
  # Reading (b) is not writable here, and that is the point rather than a
  # convenience: the guard language has no coordinate and `moved` carries a
  # direction rather than a cell.  As with A3's `jumped`, the domain/problem
  # split is enforced by the effect language and not merely observed as a
  # discipline.  `t1-push-corridor` decides it: its Block is in a different row
  # and a different column, and under (b) the manual would mis-render it at the
  # first frame.
  rule shove_up [ev: symmetry cov: 0/0]
    when act=push(Cart, up) and colored(above(Cart), 2) and free(above(Block)) then moved(Cart, up)

  rule shove_down [ev: symmetry cov: 0/0]
    when act=push(Cart, down) and colored(below(Cart), 2) and free(below(Block)) then moved(Cart, down)

  rule shove_left [ev: symmetry cov: 0/0]
    when act=push(Cart, left) and colored(leftof(Cart), 2) and free(leftof(Block)) then moved(Cart, left)

  rule shove_right [ev: t13,t30 cov: 2/2]
    when act=push(Cart, right) and colored(rightof(Cart), 2) and free(rightof(Block)) then moved(Cart, right)

  # ---- 3. the shove: the Block's half -------------------------------------
  # Same guard, different object.  Two rules rather than one because the event
  # language gives a rule exactly one object (`gen_python_a0._effect_code`), and
  # identical guards is precisely how this repository already says "one event,
  # two consequences" — `gen_pddl_a0._cascades` reads the Door's vanish off the
  # Switch's recolour by exactly this test.  `a6carry/pddl_push.py` reads these
  # four pairs off the same criterion and folds each into one PDDL action.
  #
  # The Block moves ONE CELL IN THE DIRECTION OF TRAVEL.  Not to a landmark:
  # this is the reading `jumped` exists for and the one that is wrong here, and
  # a manual that got it backwards would still fit level 1's two witnesses,
  # because on level 1 the two rightward shoves happen to end on two different
  # cells only four apart.
  rule block_up [ev: symmetry cov: 0/0]
    when act=push(Cart, up) and colored(above(Cart), 2) and free(above(Block)) then moved(Block, up)

  rule block_down [ev: symmetry cov: 0/0]
    when act=push(Cart, down) and colored(below(Cart), 2) and free(below(Block)) then moved(Block, down)

  rule block_left [ev: symmetry cov: 0/0]
    when act=push(Cart, left) and colored(leftof(Cart), 2) and free(leftof(Block)) then moved(Block, left)

  rule block_right [ev: t13,t30 cov: 2/2]
    when act=push(Cart, right) and colored(rightof(Cart), 2) and free(rightof(Block)) then moved(Block, right)

laws:
  invariant cart_unique count(Cart) = 1 [status: proven]
  invariant block_unique count(Block) = 1 [status: proven]

  theorem shove_is_relative_not_absolute "推动是一对物体之间的相对事实——小车进入方块让出的那一格, 方块沿同一方向前进一格——而不是关于某个绝对格子的事实; 第一关只有两个见证, 都是同一行的向右推, 两种读法在那里无法区分, 只有换一个方块位置完全不同的世界才能裁决"
    [depends: shove_right, block_right  probe: passed]
