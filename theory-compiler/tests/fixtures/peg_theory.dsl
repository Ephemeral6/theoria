# ----------------------------------------------------------
# 素材 B: 1D Peg Solitaire (孔明棋) theory.dsl
# 5 位置线性棋盘, 初始 [1,1,0,1,1] (位置 0-4, 中间空)
# 已知不可解构型 — pagoda 权重证明
# ----------------------------------------------------------

word_table:
  board
  object Peg { pos: Int, alive: Bool }
  # E-05: the domain declares that a pagoda potential exists over the cells.
  # The numbers are not here — they come from the LP certificate, per level.
  weights w over Peg.pos

semantics:
  frame persist                 # a peg no firing rule mentions is unchanged
  conflict exclusive            # jump_right and jump_left cannot both fire
  cascade single_frame          # one jump -> one frame; guards read the pre-state

events:
  event jumped(p, over, dir) | removed(p)

rules:
  # E-02. `Peg_a` and `Peg_b` used to be free names that looked like instances
  # and behaved like variables; nothing said which, and the backend guessed
  # wrong. `forall ?a in Peg` says it, and grounding over the level's instances
  # is what lets one clause cover a board with any number of pegs on it.
  rule jump_right forall ?a in Peg forall ?b in Peg [ev: t1,t2,t3,t4 cov: 4/4]
    when act=jump(?a, right) and ?a.alive = true and ?b.alive = true and ?b.pos = ?a.pos + 1 and free(pos(?a.pos + 2)) then jumped(?a, ?b, right)

  rule jump_left forall ?a in Peg forall ?b in Peg [ev: t1,t2,t3,t4 cov: 4/4]
    when act=jump(?a, left) and ?a.alive = true and ?b.alive = true and ?b.pos = ?a.pos - 1 and free(pos(?a.pos - 2)) then jumped(?a, ?b, left)

goal:
  goal count(Peg, alive = true) = 1

laws:
  # E-05. v0.1 had no way to name a weight function, so the potential was
  # spelled out as a free-text comprehension no backend could read. `pagoda(w)`
  # names the same object the LP certificate and an admissible heuristic share;
  # `source:` records that the numbers are the engine's, not the author's.
  invariant pagoda_potential pagoda(w) <= 0 [status: proven source: lp_potential]
  theorem unsolvable "The initial configuration with 4 pegs on a 5-cell board with center empty cannot be reduced to 1 peg"
    [depends: jump_right, jump_left  probe: passed]
