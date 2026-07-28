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

semantics:
  # v0.2 强制三项。这里不是框架常数，是 sokoban-2 这个世界的事实：
  #   frame persist    —— 没有规则提到的对象保持原样（箱子不会自己衰减）
  #   conflict exclusive —— 一次转移里每个对象至多一条规则；walk / push2 /
  #                        blocked_* 的 guard 两两互斥，certify 的
  #                        exactly_one_successor 就是这条义务的兑现
  #   cascade single_frame —— 一动作一后继；所有 guard 读前态，效果一起生效
  frame     persist
  conflict  exclusive
  cascade   single_frame

events:
  # stayed(o) 是被 certify 逼出来的：blocked_* 原本写成 then moved(Player, dir)，
  # 生成的执行态照此把玩家推出棋盘。事件语汇缺一个「什么都没发生」。
  event moved(o, dir) | slid(o, dir) | stayed(o)

rules:
  rule walk [ev: t0,t1,t2 cov: 262/262]
    when act=move(Player, dir) and free(ahead(Player, dir)) then moved(Player, dir)

  # box_ahead_free was forced by the held-out test, not by replay: the crossed
  # cell always has odd parity and every wall in `match` has even parity, so no
  # evidence from that level alone could pin it down (THEORIZE_LOG T-9).
  rule push2 [ev: t3,t9,t27 cov: 267/267]
    when act=move(Player, dir) and Box.pos = ahead(Player, dir) and free(ahead(Box, dir)) and free(beyond(Box, dir)) then slid(Box, dir)

  rule blocked_wall [ev: t5,t11 cov: 16/16]
    when act=move(Player, dir) and not free(ahead(Player, dir)) and not Box.pos = ahead(Player, dir) then stayed(Player)

  # two rules, because guards are conjunctions and "the box cannot move" is a
  # disjunction over which of the two cells is obstructed
  rule blocked_box_crossing [ev: t7,t19 cov: 24/24]
    when act=move(Player, dir) and Box.pos = ahead(Player, dir) and not free(ahead(Box, dir)) then stayed(Player)

  rule blocked_box_landing [ev: t31,t44 cov: 28/28]
    when act=move(Player, dir) and Box.pos = ahead(Player, dir) and free(ahead(Box, dir)) and not free(beyond(Box, dir)) then stayed(Player)

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
