# ----------------------------------------------------------
# 素材 C: 4-cell peg solitaire, the configuration `lp_potential` cannot do
#
# From `0111` the goal `0100` is unreachable, and D-014 in engine-rig's
# DECISIONS pins this board as **LP-infeasible**: there is no linear pagoda
# function separating that goal. It is the acceptance case for `ic3_pdr`, and
# therefore the acceptance case for consuming its certificate here.
#
# The manual is the 5-cell one with two changes: `weights`/`pagoda(...)` become
# `clauses`/`cnf(...)`, because the separating object is a propositional
# invariant rather than a potential. Everything else — the rules, the semantics,
# the `unique` declaration E-07 needed — is identical, which is the point: the
# world is the same kind of world and only the *proof method* differs.
# ----------------------------------------------------------

word_table:
  board
  object Peg { pos: Int unique, alive: Bool }
  # E-06. The clauses are not here. They come from an `ic3_pdr` certificate,
  # exactly as the pagoda weights come from an `lp_potential` one — declaring
  # the name is what lets a reader of this file alone see that the manual rests
  # on an engine-derived object, and on which engine.
  clauses sep over Peg.pos

semantics:
  frame persist                 # a peg no firing rule mentions is unchanged
  conflict exclusive            # discharged by guard analysis; see `unique` above
  cascade single_frame          # one jump -> one frame; guards read the pre-state

events:
  event jumped(p, over, dir) | removed(p)

rules:
  rule jump_right forall ?a in Peg forall ?b in Peg [ev: t1,t2 cov: 2/2]
    when act=jump(?a, right) and ?a.alive = true and ?b.alive = true and ?b.pos = ?a.pos + 1 and free(pos(?a.pos + 2)) then jumped(?a, ?b, right)

  rule jump_left forall ?a in Peg forall ?b in Peg [ev: t1,t2 cov: 2/2]
    when act=jump(?a, left) and ?a.alive = true and ?b.alive = true and ?b.pos = ?a.pos - 1 and free(pos(?a.pos - 2)) then jumped(?a, ?b, left)

goal:
  goal count(Peg, alive = true) = 1

laws:
  # E-06. `cnf(sep)` is to `ic3_pdr` what `pagoda(w)` is to `lp_potential`: the
  # manual names the separating object and records whose it is; the certificate
  # carries the content and every obligation is re-derived before use.
  invariant separating cnf(sep) [status: proven source: ic3_pdr]
  theorem unsolvable "Three pegs on a 4-cell board starting from 0111 cannot be reduced to the single peg at position 1"
    [depends: jump_right, jump_left  probe: passed]
