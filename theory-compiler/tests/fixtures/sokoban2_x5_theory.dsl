# ----------------------------------------------------------
# 素材 D′: sokoban-2 with ledger X-5 **left open** — the control
#
# Identical to `sokoban2_theory.dsl` except that the X-5 repair is absent:
# `push2` does not require `free(Box.pos)`, the two other blocked rules do not
# either, and `blocked_box_on_wall` does not exist. This is the v0.2 manual's
# guard set, carried forward only through the X-1 migration so that it can be
# compiled at all.
#
# It exists to be **wrong**, on exactly 52 of the 47,040 representable pairs,
# and `tools/probe_mentions.py` asserts that number. A repair whose control is
# not run is a repair whose number nobody re-derived: the 52 came from another
# track's probe against another track's generator, and a claim this run's
# artefacts cannot reproduce is a claim this run has not checked.
#
# Do not "fix" this file. Its defect is its content.
# ----------------------------------------------------------

word_table:
  board
  object Player { pos: Cell }
  object Box { pos: Cell }
  domain direction { up, down, left, right }
  landmark target

semantics:
  frame     persist
  conflict  exclusive
  cascade   single_frame

events:
  event moved(o, dir) | slid(o, p, dir) writes {o, p} | stayed(o) writes {}

rules:
  rule walk forall ?d in direction [ev: t0,t1,t2 cov: 262/262]
    when act=move(Player, ?d) and free(ahead(Player, ?d)) then moved(Player, ?d)

  rule push2 forall ?d in direction [ev: t3,t9,t27 cov: 267/267]
    when act=move(Player, ?d) and Box.pos = ahead(Player, ?d) and free(ahead(Box, ?d)) and free(beyond(Box, ?d)) then slid(Box, Player, ?d)

  rule blocked_wall forall ?d in direction [ev: t5,t11 cov: 16/16]
    when act=move(Player, ?d) and not free(ahead(Player, ?d)) and not Box.pos = ahead(Player, ?d) then stayed(Player)

  rule blocked_box_crossing forall ?d in direction [ev: t7,t19 cov: 24/24]
    when act=move(Player, ?d) and Box.pos = ahead(Player, ?d) and not free(ahead(Box, ?d)) then stayed(Player)

  rule blocked_box_landing forall ?d in direction [ev: t31,t44 cov: 28/28]
    when act=move(Player, ?d) and Box.pos = ahead(Player, ?d) and free(ahead(Box, ?d)) and not free(beyond(Box, ?d)) then stayed(Player)

goal:
  goal Box.pos = target

laws:
  invariant box_row_parity (Box.pos.row) mod 2 = 1 [status: proven]
  invariant box_col_parity (Box.pos.col) mod 2 = 1 [status: proven]
  invariant box_parity (Box.pos.row + Box.pos.col) mod 2 = 0 [status: proven]

  theorem unsolvable_mismatch "箱子每次滑动两格，(row+col) 的奇偶不变；开局箱子在偶格，目标格是奇格，所以永远到不了"
    [depends: push2  probe: passed]
