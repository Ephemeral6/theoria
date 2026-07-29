# CONFLICT-origin_agent_e15-solver-status-bit.md
branch: origin/agent/e15-solver-status-bit
reason: verify gate red in engine-rig (verify.py)
tip: d2b75c2695ec1bf229e3a88d66a433863da95bc1
first_seen: 2026-07-29T05:26:29Z
last_seen: 2026-07-29T05:26:29Z
attempts: 1

```
[1/3] suite
   FAIL  suite red (exit 1)
elty_is_measured_and_the_random_split_withholds_nothing_new():
        """Pins E17's F1 so it cannot be quietly lost.
    
        A `parityworld` difference vector is a function of the operation alone, so a
        transition-level split holds out rows the fit already saw and its hit rate
        is forced. That is a property of the corpus, and the harness has to keep
        saying so beside the number.
        """
        world = _world()
>       s1 = zsh.run_s1(world)
             ^^^^^^^^^^^^^^^^^

tests\test_heldout.py:140: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
heldout\zero_space_heldout.py:156: in run_s1
    return score(world, train, heldout, "Z-S1")
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
heldout\zero_space_heldout.py:100: in score
    laws, basis = fit(encoded, features, train)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

encoded = [1626, 1621, 1641, 1689, 1369, 2649, ...]
features = [Feature(cell=0, color='B'), Feature(cell=0, color='R'), Feature(cell=1, color='B'), Feature(cell=1, color='R'), Feature(cell=2, color='B'), Feature(cell=2, color='R'), ...]
train = [0, 1, 4, 5, 6, 8, ...]

    def fit(encoded: Sequence[int], features: Sequence[Feature],
            train: Sequence[int]) -> Tuple[List[Law], List[int]]:
        """The engine's presentation, over an explicitly chosen set of transitions.
    
        `train` holds transition indices `t`, meaning the difference between state
        `t` and state `t+1`.
        """
        differences = [encoded[t] ^ encoded[t + 1] for t in train]
        basis = gf2.null_space(differences, len(features))
        locals_, truncated = zerospace.local_laws(basis, features)
        globals_ = [
            gf2.reduce_modulo(vector, locals_)
            for vector in gf2.quotient_basis(sorted(basis), locals_)
        ]
        laws: List[Law] = []
        for scope, vectors in (("cell_local", locals_), ("global", globals_)):
            for vector in vectors:
                laws.append(
>                   Law(vector=vector, features=list(features),
                        value=gf2.dot(vector, encoded[0]), scope=scope,
                        scope_exhaustive=not truncated)
                )
E               TypeError: Law.__init__() got an unexpected keyword argument 'scope_exhaustive'

heldout\zero_space_heldout.py:80: TypeError
=========================== short test summary info ===========================
FAILED tests/test_heldout.py::test_the_fit_reproduces_the_engine_without_going_through_the_gate
FAILED tests/test_heldout.py::test_withholding_an_operation_strictly_enlarges_the_recovered_space
FAILED tests/test_heldout.py::test_the_score_reads_the_heldout_side_and_not_the_train_side
FAILED tests/test_heldout.py::test_the_scored_witness_really_refutes_the_law
FAILED tests/test_heldout.py::test_row_novelty_is_measured_and_the_random_split_withholds_nothing_new

[2/3] one real run -- eight engines end to end, offline
   ok    wrote candidates.jsonl
[3/3] artefact self-check

engine-rig: RED (1 problem(s))

```
