# R-09, confirmed blind — the miner's better rule is the one the compiler cannot take

`domain_l2_scratch_lifted.dsl` is the **first** manual the from-scratch control
arm produced: seven `forall ?d in dir` schemas covering the same 28 ground
rules that level 1's manual spells out as twenty clauses.

It does not compile.

    compile.gen_python_a0.UnsupportedClause: moved(o, dir)

`gen_python_a0`'s guard and effect subset takes a **literal** direction, so a
direction-lifted rule compiles to nothing.  A2 logged this as a limitation of
the backend (`A2_REPORT.md` §8); level 1's manual avoided it only because its
author already knew, and wrote twenty ground clauses while recording in
`THEORIZE_LOG.md` R-09 that the miner's lifted rule — one clause at 225/225 —
was the better answer.

**What makes this run evidence rather than a repeat.** The control arm's author
was blind: no access to level 1's manual, its theorize log, the world source or
the referee's copy.  Given the same kind of evidence and no knowledge of the
backend, they reached for the lifted form independently — which is what
description length recommends and what the miner itself proposes.  Two
independent passes preferred the rule the toolchain rejects.

That is a sharper statement of the gap than either pass could make alone: it is
not a stylistic preference that happens to collide with a backend limitation,
it is the *reading the evidence favours*, and the compiler cannot express it.

`domain_agreement_lifted.json` is the clause-by-clause comparison against level
1's manual **before** the grounding pass, and it is worth keeping for a second
reason: `strict_agreement` is **0.0** and `canonical_agreement` puts all twenty
of level 1's clauses inside the blind manual.  The whole of that 0 % is naming
and the ground/lifted choice — a measurement of how much of a manual is
convention rather than content.

The grounding pass that followed cost the control arm an extra theorize round,
and that round is charged to its bill.  It was forced by an expressiveness gap,
not by new evidence.
