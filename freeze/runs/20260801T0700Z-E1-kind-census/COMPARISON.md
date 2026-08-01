# E1 census: before and after the F1/D1/D2 repair

Population: the **24 Lean books on disk**, one row per directory.
This is an engineering denominator.  It is NOT STATS_RULES §1.2's E1
rate, whose denominator is the frozen 19 sealed claim-set games (12 at
the clean layer).  Nothing on disk today is a sealed game.

| label | before | after |
|---|---|---|
| `discharged` | 14 | 17 |
| `failing_obligation` | 1 | 1 |
| `unclassified` | 0 | 4 |
| `vacuous` | 9 | 2 |
| **attained** | **14 / 24** | **17 / 24** |

## the 7 books whose verdict moved

| book | before | after | why |
|---|---|---|---|
| `theory-compiler/handover_packages/a0-cart/levels/base` | `vacuous` | `unclassified` | two theorems: a closure lemma about the `Reachable` relation and an existential goal witness.  Neither is one of §1.2.1's three kinds, so nothing was ever checked -- `unclassified`, not an accusation |
| `theory-compiler/handover_packages/a0-cart/levels/no-button` | `vacuous` | `unclassified` | as above |
| `theory-compiler/handover_packages/a0-sokoban2/levels/crossing-up` | `vacuous` | `unclassified` | as above |
| `theory-compiler/handover_packages/a0-sokoban2/levels/match` | `vacuous` | `unclassified` | as above |
| `theory-compiler/lean` | `vacuous` | `discharged` | the invariant is called `Inv`, not `I`.  The old (c) hard-coded `defs['I']` and returned "no `def I` found to check" -> vacuous.  The predicate is now read off the theorem's own conclusion. |
| `theory-compiler/runs/20260728T080019Z-C4-deadlock-lean` | `vacuous` | `discharged` | the C4 deadlock proof: `dead` is now read as `prune` and §1.2.1-prune (a)(b)(c) are discharged by `pat_witness`, `no_goal_pinned`, `level_is_winnable` |
| `theory-compiler/runs/20260728T080019Z-C4-deadlock-lean/verify` | `vacuous` | `discharged` | same development, `verify/` copy |

## the books whose verdict did NOT move

Both true vacuity findings survive: `cold-start-a3/theory/
generated_l1_vacuous` (the frozen §9.2 negative control -- 抓不住它就不许
冻结) and `cold-start-a0/prime/theory/generated` are still `vacuous`, now
because a shape-classified invariant was found constant rather than
because a name matched.  `cold-start-a2/theory/generated_repaired_stale`
is still `failing_obligation`: it does not compile, and (a) is untouched.
The 17 other previously-discharged books are unchanged.

## direction of the change

Every move is `vacuous` -> something else, i.e. this repair only ever
**removes** an accusation.  Three become `discharged` and four become
`unclassified`; nothing that attained stopped attaining, and nothing
that was refuted became attained without a §1.2.1 check saying so.
The two developments §1.2.1 names as vacuous are still called vacuous.
