# ----------------------------------------------------------
# 素材 D: sokoban-2 — the A0 world, migrated to v0.3
#
# The manual is `a0-spike/theory/theory.dsl` (the `engine-rig` track's A0 cold
# start) with the two v0.3 repairs applied. It is carried here rather than
# edited there because `a0-spike` is the other track's directory; this copy is
# what the C7 run measures, and the migration is offered to that track through
# PARTNER_SYNC. `tools/probe_mentions.py` checks this file against
# `a0-spike/world/sokoban2.py` as ground truth and refuses if the levels have
# moved under it.
#
# Two changes from the v0.2 original, one per ledger entry:
#
# **X-1** — `slid(o, dir)` becomes `slid(o, p, dir) writes {o, p}`. A push moves
# the box two cells *and* carries the player one; under v0.2 that second motion
# was named nowhere in the manual, so the frame axiom's "mentions" and the
# compiled effect disagreed about the Player on every push. 376 mispredictions,
# measured. The pusher is now an argument, so the signature names every object
# the event writes, and `writes` says which arguments those are.
#
# **X-5** — `push2` gains `free(Box.pos)`, and `blocked_box_on_wall` catches the
# states it now refuses. The v0.2 manual had no way to say "the Box is not
# standing on a wall": the world checks `is_wall(target)` before it checks
# `target != box` (`world/sokoban2.py:142-145`), and `free(Box.pos)` compiled to
# a test the Box's own rendering made unconditionally false. 52 mispredictions,
# all of them firing `push2`. `blocked_box_crossing` and `blocked_box_landing`
# take the same clause, or they overlap the new rule and `conflict exclusive`
# stops being dischargeable.
#
# **A third change, and the only one that decides whether this compiles at
# all.** The v0.2 manual leaves `dir` a free name; `a0-spike`'s own generator
# passes it in as a function parameter, which is a schema written where no
# grammar can check it. Under `theory-compiler` that manual does not reach the
# event layer: `moved(Player, dir)` fails in `_direction` with *"expected a
# direction from ['down', 'left', 'right', 'up'], got NameRef(name='dir')"* —
# identically before and after v0.3. So every rule here binds `forall ?d in
# direction` over a declared `domain` (E-02), and five schemas ground to
# twenty-four rules. Neither X-1 nor X-5 is what was stopping this manual; they
# are what was wrong with it once it ran.
#
# A fourth, minor: `landmark target` is declared (E-04), which silences a
# warning both versions raise about the level locating a name the manual never
# names. It changes no world.
#
# **On the inherited evidence tags.** `ev:` is kept; `cov:` is dropped from the
# three rules whose guards changed. A coverage figure is a measurement of a
# specific rule against a specific trace, and `267/267` was measured on a
# `push2` that had one conjunct fewer. Carrying it forward would be quoting a
# number nobody re-derived — the thing `source:` exists to prevent one section
# over. The exhaustive check that *was* run on these guards is
# `tools/probe_mentions.py`: 0 mismatches over all 47,040 representable pairs.
# ----------------------------------------------------------

word_table:
  board
  object Player { pos: Cell }
  object Box { pos: Cell }
  domain direction { up, down, left, right }
  landmark target
  Player [segment: color-split-connected ev: t0-t340 compress: -39]
  Box [segment: color-split-connected ev: t0-t340 compress: -39]

semantics:
  # Adjudicated in a0-spike/runs/20260728T040057Z-c2 over 47,040 representable
  # (state, action) pairs by refuting the alternative, not by fitting the
  # chosen value. Unchanged by this migration: v0.3 defines what `persist`
  # ranges over, it does not change which value is true of this world.
  frame     persist
  conflict  exclusive
  cascade   single_frame

events:
  # `writes` is the v0.3 addition (ledger X-1). `slid` is the event it exists
  # for: it is compound, the grammar gives a rule one event, and a reader of
  # this file alone could not previously see that a push moves the player.
  # `stayed` declares `{}` rather than inheriting it from the default table,
  # because a manual that means "nothing happens" should be readable as saying
  # so — and a rule with an empty write set is the no-op rule ledger X-3 wants
  # adjudicated.
  event moved(o, dir) | slid(o, p, dir) writes {o, p} | stayed(o) writes {}

rules:
  rule walk forall ?d in direction [ev: t0,t1,t2 cov: 262/262]
    when act=move(Player, ?d) and free(ahead(Player, ?d)) then moved(Player, ?d)

  # box_ahead_free was forced by the held-out test, not by replay: the crossed
  # cell always has odd parity and every wall in `match` has even parity, so no
  # evidence from that level alone could pin it down (THEORIZE_LOG T-9).
  # cov: dropped — the guard gained `free(Box.pos)` and 267/267 was measured
  # without it. See the header.
  rule push2 forall ?d in direction [ev: t3,t9,t27]
    when act=move(Player, ?d) and Box.pos = ahead(Player, ?d) and free(Box.pos) and free(ahead(Box, ?d)) and free(beyond(Box, ?d)) then slid(Box, Player, ?d)

  rule blocked_wall forall ?d in direction [ev: t5,t11 cov: 16/16]
    when act=move(Player, ?d) and not free(ahead(Player, ?d)) and not Box.pos = ahead(Player, ?d) then stayed(Player)

  # X-5. The world refuses a push into a box that is itself standing on a wall,
  # because it tests the target cell for wall-ness *before* it notices the box.
  # Without this rule the repair to `push2` would turn 52 wrong answers into 52
  # missing ones, which is not a repair.
  #
  # **No `ev:` and no `cov:`, deliberately.** This rule is not adjudicated from
  # the trace — the states it covers are unreachable in play, which is exactly
  # why T-9 says that is not a defence. Its warrant is the exhaustive sweep and
  # the world's own source (`sokoban2.py:142-145`), and inventing an evidence
  # tag it does not have would be worse than carrying none.
  rule blocked_box_on_wall forall ?d in direction
    when act=move(Player, ?d) and Box.pos = ahead(Player, ?d) and not free(Box.pos) then stayed(Player)

  # two rules, because guards are conjunctions and "the box cannot move" is a
  # disjunction over which of the two cells is obstructed. Both take
  # `free(Box.pos)` as well — not because `conflict exclusive` needs it (under
  # v0.3 `stayed` writes nothing, so these rules claim nothing and no pair of
  # them is ever examined) but to keep **exactly one rule fires** true. That is
  # a strictly stronger property than the contract requires, it is what
  # `a0-spike`'s `gen_exec` enforces at runtime and what its semantics probe
  # measures, and without these two clauses it fails on 24 pairs.
  rule blocked_box_crossing forall ?d in direction [ev: t7,t19]
    when act=move(Player, ?d) and Box.pos = ahead(Player, ?d) and free(Box.pos) and not free(ahead(Box, ?d)) then stayed(Player)

  rule blocked_box_landing forall ?d in direction [ev: t31,t44]
    when act=move(Player, ?d) and Box.pos = ahead(Player, ?d) and free(Box.pos) and free(ahead(Box, ?d)) and not free(beyond(Box, ?d)) then stayed(Player)

goal:
  goal Box.pos = target

laws:
  # zero_space returned a null space of dimension 2: each coordinate's parity is
  # conserved separately, which is stronger than the (row+col) form first
  # proposed. The strong pair is what is registered; the sum survives as a
  # corollary (THEORIZE_LOG T-6).
  invariant box_row_parity (Box.pos.row) mod 2 = 1 [status: proven]
  invariant box_col_parity (Box.pos.col) mod 2 = 1 [status: proven]
  invariant box_parity (Box.pos.row + Box.pos.col) mod 2 = 0 [status: proven]

  # `probe: passed` survives the migration on purpose, and the reason is worth
  # writing down rather than assuming: the theorem depends on `push2`, and
  # `push2` changed. What changed is its **guard**, not its effect — `slid`
  # still moves the box two cells — and a narrower guard cannot break a
  # conservation law that holds of the effect. Had the effect moved, this tag
  # would have to go back to `pending`.
  theorem unsolvable_mismatch "箱子每次滑动两格，(row+col) 的奇偶不变；开局箱子在偶格，目标格是奇格，所以永远到不了"
    [depends: push2  probe: passed]
