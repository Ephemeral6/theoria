"""Independent re-implementations used to judge the engines.

House rule, and the only thing that makes the battery worth running: **an oracle
may not call the engine it judges.**  Checking `zero_space` with
`zero_space.verify` proves the module is self-consistent and nothing more.  So
the oracles here recompute the answer from the world -- brute-force enumeration,
BFS, exact GF(2) elimination, a hand-rolled plan validator -- and compare.

Where brute force is infeasible the oracle says so and the property is recorded
as `skipped` with the reason, rather than quietly narrowing to the cases it can
handle.
"""
