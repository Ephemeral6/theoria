# ----------------------------------------------------------
# A0 说明书 — sokoban-2（玩家走一格，箱子被推时滑两格）
# 由 theorize 裁决入册：引擎提案，LLM 裁决。
# 证据：341 条转移，60 个前缀重放 episode。裁决理由见 ../THEORIZE_LOG.md。
# ----------------------------------------------------------

word_table:
  board
  object Player { pos: Cell }
  object Box { pos: Cell }
  Player [segment: color-split-connected ev: t0-t340 compress: -39]
  Box [segment: color-split-connected ev: t0-t340 compress: -39]

events:
  event moved(o, dir) | slid(o, dir)

rules:
  rule walk [ev: t0,t1,t2 cov: 262/262]
    when act=move(Player, dir) and free(ahead(Player, dir)) then moved(Player, dir)

  rule push2 [ev: t3,t9,t27 cov: 51/51]
    when act=move(Player, dir) and Box.pos = ahead(Player, dir) and free(beyond(Box, dir)) then slid(Box, dir)

  rule blocked_wall [ev: t5,t11 cov: 16/16]
    when act=move(Player, dir) and not free(ahead(Player, dir)) and not Box.pos = ahead(Player, dir) then moved(Player, dir)

  rule blocked_box [ev: t7,t19 cov: 12/12]
    when act=move(Player, dir) and Box.pos = ahead(Player, dir) and not free(beyond(Box, dir)) then moved(Player, dir)

goal:
  goal Box.pos = target

laws:
  # zero_space 返回的零空间维数为 2：两个坐标的奇偶各自守恒，比我最初提的
  # (row+col) 更强。入册取强的一对，和式作为推论保留（见 THEORIZE_LOG T-6）。
  invariant box_row_parity (Box.pos.row) mod 2 = 1 [status: proven]
  invariant box_col_parity (Box.pos.col) mod 2 = 1 [status: proven]
  invariant box_parity (Box.pos.row + Box.pos.col) mod 2 = 0 [status: proven]

  theorem unsolvable_mismatch "箱子每次滑动两格，(row+col) 的奇偶不变；开局箱子在偶格，目标格是奇格，所以永远到不了"
    [depends: push2  probe: passed]
