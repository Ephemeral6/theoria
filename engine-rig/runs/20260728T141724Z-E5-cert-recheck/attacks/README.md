# attacks — three adversarial reviews of `recheck/`, and their inputs

Three reviewers were run against the rechecker with no brief except to break it.
They wrote these files; nothing here was edited afterwards except the pruning
noted at the bottom. Each report records the exact input, the exact command, the
real output, and BROKEN / held.

| report | lens | result |
|---|---|---|
| `expr-lens.md` | the expression language and its evaluation | 31 attacks, **1 wrong ACCEPT** + 5 tracebacks |
| `ruleset-lens.md` | the obligations the rule set owes about itself | 21 hand-built + 30 000 fuzzed pairs, **2 classes broken** |
| `transcription-lens.md` | are the rule sets the worlds they claim to be | 0 discrepancies, differentials run rather than reasoned about |

Re-runnable scripts, all of which read `cold-start-a2/` and write nothing to it:

| script | what it compares |
|---|---|
| `a2_differential.py` | the derived step vs `cold-start-a2`'s compiled predictors, whole product |
| `replay_world_episode.py` | the derived `rendered` vs the world's own 19 recorded frames, pixel by pixel |
| `pagoda_and_anchors.py` | `def w` in the Lean file vs the certificate's weight table |
| `sokoban_differential.py` | the derived step vs an independently parsed and grounded PDDL simulator |
| `deadlock_spotcheck.py` | the shipped dead-region theorems vs the carver's actual output |
| `fuzz_ruleset.py` | 30 000 random (rule set, certificate) pairs against a re-implemented ground truth |

**Every finding is now a standing entry in `recheck/forgeries.py`**, so none of
them can come back silently: `act-through-a-def`,
`shrunken-domain-and-patched-guard`, `region-hiding-a-win`,
`region-reaching-outside-the-constraint`, `deep-predicate`, `arity-zero-lit`,
`tampered-under-the-same-name`. The fixes and their reasoning are in
`engine-rig/DECISIONS.md` D-029 (the constraint's qualifier) and D-031 (the
scope-flag leak, and why a crash must not exit as a REJECT).

**One caveat the reviewers recorded and it is fair.** `recheck/` was being
edited while two of them were running; for about seventy seconds every
invocation raised `NameError` from a half-applied edit. Both re-ran everything
afterwards and pinned their verdicts to file digests. That incident is also how
the exit-code aliasing was noticed, so it earned its place.

**Pruned before committing:** four machine-padded payloads
(`expr-A03-deep-5k`, `expr-A03-deep-900`, `expr-A23-defstack-1500`,
`expr-A23-defstack-3000` — 131 KB of nested `and`s and stacked defs). The shapes
are described in `expr-lens.md` and reproduced by `forgeries.py::_nest_past_the_stack`;
the smaller members of each family are still here.
