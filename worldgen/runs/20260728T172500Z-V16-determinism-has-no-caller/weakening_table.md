# V16 — the negative control, weakened

Each cell is `n/m` over `m` distinct parent `PYTHONHASHSEED` values (1..m); the gate pins its own comparison build at `271828`.

**RED** = `build --check` exited non-zero, printed `NOT DETERMINISTIC:` **and named at least one artefact as differing**. The third condition is not redundant: `build.py:251-253` prints the same banner when the comparison subprocess merely failed to build, so without it a crash scores as a catch.  **MISSED** = the injected defect got past.

| injection | class | none | shared_hashseed | size_only | no_diff |
|---|---|---|---|---|---|
| `mechanism_order` | B | **RED (25/30 seeds)** | MISSED (0/10) | MISSED (0/10) | MISSED (0/10) |
| `hash_order_wide` | B | **RED** (30/30) | MISSED (0/10) | MISSED (0/10) | MISSED (0/10) |
| `unseeded_rng` | A | **RED** (30/30) | **RED** (10/10) | **RED (5/10 seeds)** | MISSED (0/10) |
| `wall_clock` | A | **RED** (30/30) | **RED** (10/10) | MISSED (0/10) | MISSED (0/10) |

## The two classes are not the same claim

`CLAUDE.md` states the requirement as *"byte-reproducible for a fixed seed"*.  **Only class A breaks that.**

* **class A** — varies at a fixed seed (violates CLAUDE.md as written): `unseeded_rng`, `wall_clock`
* **class B** — stable at a fixed seed, moves across seeds (violates the stronger requirement check_determinism enforces): `mechanism_order`, `hash_order_wide`

Class B is byte-identical on two runs at one seed — verified by `determinism_sandbox.classify`, which builds twice at the same seed.  It is a real defect and the `shared_hashseed` column is the evidence that catching it is worth something; but a reader who takes it for a `CLAUDE.md` violation has been told something this repository does not promise.  A note has gone to `monitor/inbox/` proposing the charter say which of the two it means.

## Weakenings

* `shared_hashseed` — the comparison build inherits the parent's PYTHONHASHSEED — the gate as it stood before C1's F7
* `size_only` — compare file sizes instead of bytes
* `no_diff` — run the comparison build and never look at it

## Injections

* `mechanism_order` (on `t3-latch-maze`, class B) — the structural defect the gate's own docstring names: a `set` reaching an output. `GridWorld` drops the `(priority, name)` sort and takes its mechanism order from set iteration, so the variable layout and every `State.key()` move with the hash seed. Measured effect on the shipped artefacts: `ground_truth.json`, `GROUND_TRUTH.md` and `reversibility.json` differ; `raw_trace.jsonl`, `spec.json` and `coverage.json` do NOT — the trace renders frames, not the variable vector, so it is blind to this. (An earlier draft of this sentence said 'the whole trace moves'. It does not, and the run directory's own console log had said so from the first experiment.)
* `hash_order_wide` (on `t1-walk-maze`, class B) — sixty-four strings iterated out of a `set` into a JSON list. Same class as `mechanism_order` but wide enough that two different seeds practically cannot agree, so it is the case that pins the gate even if a future Python changes small-set layout.
* `unseeded_rng` (on `t1-walk-maze`, class A) — an unseeded `random.random()` in an output. Moves between two runs at the same seed, so it is the written requirement this repository states and not merely the one the gate enforces.
* `wall_clock` (on `t1-walk-maze`, class A) — wall-clock nanoseconds in an output. The other fixed-seed violation, and the one that survives a `random.seed()` being added somewhere.
