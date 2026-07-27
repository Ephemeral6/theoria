# ----------------------------------------------------------
# 素材 B: 1D Peg Solitaire (孔明棋) theory.dsl
# 5 位置线性棋盘, 初始 [1,1,0,1,1] (位置 0-4, 中间空)
# 已知不可解构型 — pagoda 权重证明
# ----------------------------------------------------------

word_table:
  board
  object Peg { pos: Int, alive: Bool }

events:
  event jumped(p, over, dir) | removed(p)

rules:
  rule jump_right [ev: t1,t2,t3,t4 cov: 4/4]
    when act=jump(Peg_a, right) and Peg_a.alive = true and adjacent(Peg_a, Peg_b) and Peg_b.alive = true and Peg_b.pos = Peg_a.pos + 1 and free(pos(Peg_a.pos + 2)) then jumped(Peg_a, Peg_b, right)

  rule jump_left [ev: t1,t2,t3,t4 cov: 4/4]
    when act=jump(Peg_a, left) and Peg_a.alive = true and adjacent(Peg_b, Peg_a) and Peg_b.alive = true and Peg_b.pos = Peg_a.pos - 1 and free(pos(Peg_a.pos - 2)) then jumped(Peg_a, Peg_b, left)

goal:
  goal count(Peg, alive = true) = 1

laws:
  invariant pagoda_weight sum(w(p) * Peg_p.alive for p in positions) >= 4 [status: proven]
  theorem unsolvable "The initial configuration with 4 pegs on a 5-cell board with center empty cannot be reduced to 1 peg"
    [depends: jump_right, jump_left  probe: passed]
