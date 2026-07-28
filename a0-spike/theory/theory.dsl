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
  # 三项都是对这个世界的断言，不是接线。措辞取自 CONTRACTS/dsl_grammar_v0.2.md
  # 的封闭值集；取哪个值由 probes/semantics_probe.py 在 47040 个可表示
  # (状态,动作) 对上反证另一个值定出，逐项裁决理由见 ../THEORIZE_LOG.md T-11。
  # 三个值恰好与 A0、A2 所报的相同——这是量出来的，不是抄来的（v0.2 §迁移
  # 明文禁止照抄），复算命令见 runs/20260728T040057Z-c2/RUN_STATE.md。

  # 反证：把 Box 换成 reset，38712/39960 个可观测对立刻错——只要玩家单走一步，
  # 没有任何开火规则提到箱子，reset 就把箱子传送回开局格。世界不这样。
  frame     persist

  # 反证：五条规则的守卫两两不交，全扫描 47040 对里同时开火的规则数上限为 1，
  # 认领同一对象的规则数上限也为 1（含 on_wall 层，故此项是无条件解除）。
  # 关键一步是把 slid 读宽：gen_exec 里它同时写 Box 和 Player，v0.2 §Discharging
  # conflict 的义务按对象算，读窄会低估要证的东西。另有独立的句法证明（route 1）
  # 在 THEORIZE_LOG T-11c：free(c) 蕴含 c≠Box.pos，这一条就切开了 walk 与 push2。
  conflict  exclusive

  # 反证：multi_frame 要把规则在中间态上重开火。A0 每条规则都守在
  # act=move(Player,dir) 上，动作不会自己熄灭，于是 walk 反复开火，
  # 一次 move 让玩家滑到撞墙为止——22582/39960 个可观测对因此错。
  # 箱子滑两格不是级联：那两格是**一条规则的一个效果**，整体施加；
  # multi_frame 说的是「规则集被重跑」，两者不是一回事。
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
