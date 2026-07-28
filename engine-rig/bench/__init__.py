"""bench -- measurement, kept out of the engines it measures.

Nothing here is imported by an engine.  The rig's engines answer questions about
a world; this package answers questions about the rig, and the two must not be
able to drift into each other -- a benchmark that shares code with the thing it
benchmarks can only ever confirm it.

Three modules, one question each:

* `fdrun`  -- run one rung of the ladder and bring back its *own* node account,
              which `fd_adapter.solve()` deliberately throws away;
* `ladder` -- the same batch of instances on every rung: nodes, wall clock,
              optimality;
* `dividend` -- what a proved deadlock is worth, on the rung that can take a
              pruner and on the rung that cannot.

**Timings are not reproducible and the artifacts say so.**  Every record splits
into a structural half (node counts, plan lengths, exit codes -- a function of
the instance and the configuration, byte-stable across runs) and a timing half
(wall clock -- a function of this machine on this afternoon).  `verify.py`
re-derives the first and only sanity-checks the second.  The repo's determinism
requirement applies to the first; claiming it for the second would be a lie that
the next run on a busier machine would expose.
"""
