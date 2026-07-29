# E17 · adversarial review of the held-out validation

Reviewer: adversarial subagent, 2026-07-29. Worktree
`.worktrees/e17-held-out-validation`, `HEAD = e0fd43a`. No delivered file was
edited; every mutant is a monkeypatch or a pytest plugin under
`runs/20260729T034043Z-E17-held-out-validation/adversarial/`. No network, no API,
no sealed-pile contact.

**Marking convention.** `SUSTAINED` = my attack stands and the claim it attacks is
damaged. `OVERTURNED` = my attack failed and the delivered claim survives it.
`UNRESOLVED` = I could not settle it.

---

## Verdict

The arithmetic is clean and the honesty machinery mostly works. I re-derived all
four `zero_space` rates and all thirteen `lp_potential` counts from code I wrote
myself, including an independently written peg state space and BFS, and every
single one reproduces to the digit. Two consecutive re-runs of `heldout.run` are
byte-identical to the committed `results.json`. The pre-registration commit
`ef382c9` really is an ancestor of `e0fd43a`, the pre-registration text was never
touched afterwards, and the only post-hoc harness edits are an extra
disaggregation bucket and two derived constants — both self-disclosed in the
code. `504 passed, 27 skipped, exit 0` is the real pytest result on this machine.

What does not survive is the interpretation.

**The headline `zero_space` number is measuring nothing.** In a `parityworld`
world the difference vector of a transition is a function of the *operation
alone* — `apply` flips a fixed window, so both features of each flipped cell
toggle and the encoded difference is a constant per operation. Sixty transitions
therefore carry at most nine distinct difference vectors. I checked all 120
worlds: **every held-out difference vector under Z-S1 is bit-identical to one
already in the training set, in 120 / 120 worlds.** Z-S1's "held-out" 30 % is a
duplicate of the training rows. `100.0 %` is not an extrapolation result; it is
arithmetically forced. The proof by mutation is blunter than the proof by
argument: I made `split.random_transition_split` return **overlapping** train and
test sets — a 12-transition leak — and **not one published digit moved**.
`ENGINE_TABLE.md` row 3 says "the recovered laws extrapolate perfectly". That
sentence is wrong and should be struck.

**The `lp_potential` "pass" is an artefact of which graph the gate was handed.**
`lp_potential_heldout.py:158` calls `lp_potential.candidates(certificate,
heuristic, graph)` with the **complete** graph, while the certificate was fitted
on `reduced` (`:144`). The gate then fires on `missing_moves` — it is comparing
the certificate against ground truth the hold-out premise says the caller does
not have. `engines/lp_potential/__init__.py:44` says so in as many words:
"Production cannot reach either branch — `solve_certificate` builds the move list
*from* the graph." Re-run with the graph a caller with partial evidence would
actually hold and **all 1408 certificates are emitted, including all 58 false
ones**, each carrying `holds: true`, `sound_over_graph: true`, `missing: []`,
`raising: []`. "0 of 1408 reached `candidates.jsonl`" is true only of a call the
engine never makes.

**A pre-registered validity criterion is recorded as met and is not.**
PREREGISTRATION §5.3 requires *every* miss to carry a witness. `run.py:97` writes
`misses[:200]` — 200 of 1940 — and `run.py:166-170` caps every `witnesses{}` list
at 20. RESULTS.md's validity table marks that row "yes".

**Twelve of thirteen harness mutants survive the run's own gates**, including
three outright leakage mutants that push the number *up* to 100 %. `heldout/` has
zero test coverage: no file under `tests/` imports it.

Surviving intact: the reproducibility claim, the manifest (14 / 14 sha256 verify),
the ancestry claim, the pytest numbers, the smallest `peg4` witness (I checked it
by hand and it is exactly right), `26.4 %` as a per-`n`-stable figure, the
`counting` / `arithmetic` separation as a piece of bookkeeping, and — importantly
— the run's refusal to set a pass threshold.

---

## (a) Is the held-out set actually held out?

### F1 · Z-S1 withholds no information at all — SUSTAINED

`heldout/parityworld.py:40-44`: `apply` flips a fixed set of cells; the encoding
(`zerospace.encode`) has one bit per (cell, colour), so flipping cell *c* toggles
exactly bits `B@c` and `R@c`. The encoded difference `encoded[t] ^ encoded[t+1]`
is therefore a **function of `world.actions[t]` alone** and of nothing else.

Measured (`adversarial/a1_zs_recompute.py`):

```
distinct difference vectors per world (count -> #worlds): {4: 20, 5: 20, 6: 20, 7: 20, 8: 20, 9: 20}
ops per world: [4, 5, 6, 7, 8, 9]
Z-S1 worlds where EVERY held-out difference vector also occurs in train
(bit-identical): 120 / 120
```

60 transitions, ≤ 9 distinct rows. Every one of the 18 held-out rows is a literal
copy of a training row. Since the fitted `a` satisfies `a·d = 0` for every
training `d`, it satisfies it for every held-out `d` by substitution. `100.0 %`
is a theorem about the corpus, not a measurement of the engine.

This is the finding that decides the ticket: E17 exists because "已测" meant
"self-consistent on the data it was fitted to", and Z-S1 re-checks the laws on a
*copy* of the data they were fitted to. It is the same tautology one indirection
further out.

### F2 · `value_hit` cannot differ from `delta_hit` — it is not a second metric — SUSTAINED

PREREGISTRATION §3 calls `value_hit` "strictly stronger than `delta_hit`"; RESULTS.md
reports "They came out identical everywhere" as an observation. It is forced.

The states form a single path `x_0 … x_T` and every edge is in exactly one side of
the split. The fitted law satisfies `a·d = 0` on every *train* edge by
construction. If `delta_hit` holds, `a·d = 0` on every *held-out* edge too, so
`a·x` is constant along the whole path and equals `a·x_0 =: value` — `value_hit`
holds. If `delta_hit` fails, some held-out edge has `a·x_t ≠ a·x_{t+1}`, so at
least one endpoint differs from `value` — `value_hit` fails. The two are
logically equivalent for *any* split of a path.

Confirmed on all 8480 + 1140 law-instances: `delta_hit == value_hit` on
**8480/8480 and 1140/1140**. And confirmed by mutation P6: rewiring all three
published rate probes from `delta_hit` to `value_hit`, with the provenance strings
left byte-identical, gives `4 passed` — no digit moves, nothing notices.

Secondary point, inert but real: `law.value` is `gf2.dot(vector, encoded[0])`
(`zero_space_heldout.py:71`), and the `value_hit` loop
(`zero_space_heldout.py:104-112`) checks both endpoints of each held-out
transition. Under Z-S2 variant `op0` the held-out set *always* contains transition
0 — `parityworld.build:57` walks every operation in index order first — so state 0
is always among the states checked, and that one comparison is `value == value` by
definition. Under Z-S1 transition 0 is held out in 42 / 120 worlds. Harmless given
F2, but it is a re-check consuming its own input.

### F3 · The split salt is not a leak — OVERTURNED

`world_seed ^ 0x5115` feeds a different SplitMix64 stream. Re-cutting with salt
`0xBEEF` gives the identical `100.0 % / 100.0 %`. No correlation between the cut
and the data is detectable, and given F1 none could matter.

### F4 · `graph_minus_geometry` really does remove the geometry from the LP — OVERTURNED

`potential.moves_from_graph` (`potential.py:127-135`) builds the LP rows from
`graph["edges"]`, and `peg.graph_minus_geometry` (`peg.py:104-107`) rewrites
`edges`. The stale `move_instances` it leaves behind is dead for this engine.
I verified the withheld geometry is absent from `certificate.moves` in every case
(it is what makes `gate_missing_moves` non-empty for all 1408).

Keeping `distance_to_goal` at the full-move-set value is **correct**, not
double-dipping: it is the ground truth the claim is scored against, and the LP
never reads it.

No vacuous hold-outs: `peg.geometries` is derived from the edges, so a withheld
geometry always had at least one edge. Measured
(`adversarial/a3_lp_recompute.py`): `vacuous_geometry_holdouts: 0`.

### F5 · The harness scores the emit gate against evidence the hold-out says it does not have — SUSTAINED

`lp_potential_heldout.py:144` fits on `reduced`; `:158` gates on `graph` — the
complete one. So `premises_against_graph` compares a 3-move certificate to a
4-move graph and reports `missing_moves = ['jump(3,2,1)']`. Of course it does.

Re-run with the reduced graph (`adversarial/a4_gate_and_L2.py`):

```
emitted_full                 0
emitted_reduced              1408
false certificates: 58, of which emitted when the gate is handed the SAME
partial graph the LP was fitted on: 58
```

The smallest witness, through the gate:

```
weights            : ['0', '1/2', '-1/2', '0']
conditions         : {'inv_init': True, 'inv_closed': True, 'goal_break': True}
claim              : goal unreachable from 0011
true distance 0011->0100: 1
candidates(full graph)   -> 0 rows
candidates(reduced graph)-> 2 rows
  emitted claim : goal unreachable from 0011
  emitted holds : True
  premise_check : True missing: [] raising: []
```

A false unreachability certificate, `holds: true`, `sound_over_graph: true`, in
the shared candidate stream. RESULTS.md's "the hole is in `check_exactly`, not at
the emit boundary" is only true when somebody hands the emit boundary the answer.

### F6 · The `counting` / `arithmetic` split is bookkeeping, not two detectors — SUSTAINED (partially)

RESULTS.md: "Counting caught all 1408; arithmetic independently caught 1036, which
is exactly the 1408 − 372 that fail `inv_closed`. The two detectors agreeing to
the unit is a consistency check on this run."

It is an identity, not an agreement. `check_exactly` has already proved
`delta ≤ 0` **exactly** for every move in `certificate.moves`, so
`moves_raising_potential` computed over the full graph can only ever contain the
withheld geometry. Therefore `gate_raising_moves ≠ []` **iff**
`heldout_inv_closed` is false, always, by construction. Reporting `1036` beside
`1408 − 372` as a cross-check credits a tautology. The paragraph is half-honest —
it does say "not a second piece of evidence" — but "agreeing to the unit" invites
exactly the reading it disclaims.

### F7 · L-L2's "0 violations in 506 held-out states" is entailed, not observed — SUSTAINED

On a complete graph `check_exactly` verifies `inv_closed` over **every** geometry
in exact rationals. Given that, admissibility on every finite-distance state is a
one-line consequence: the potential never rises, so a state with a finite path to
the goal has `pot(s) ≥ pot(g)`, and each move drops the potential by at most `M`,
so any `d`-move path gives `d ≥ (pot(s) − pot(g))/M ≥ h(s)`. There is no
configuration in which the check could return a violation.

Empirical confirmation, over all 1408 held-out certificates:

```
inv=True  viol>0=False   372      inv=True  violations 0
inv=False viol>0=False   294      inv=False violations 1778
inv=False viol>0=True    742
```

Not one violation exists where `inv_closed` holds over the full move set; all 1778
live where it fails. The states are held out of the LP's *constraint set* but not
out of the *argument*, which quantifies over move instances and therefore covers
every state at once.

So `ENGINE_TABLE.md` row 4's "**Alone among the eight rows, this engine's 「已验证」
was not circular to begin with**" is exactly backwards. It is circular in the same
shape as `zero_space`'s `verify()`, one deduction step longer: a re-check of a
consequence of a condition already verified on the fitting evidence. Strike the
sentence or re-label it "entailed by `inv_closed`, therefore not an independent
check".

### F8 · A pre-registered validity criterion is marked met and is not — SUSTAINED

PREREGISTRATION §5.3: "Every miss is emitted with a concrete witness … so a reader
can reproduce it by hand."

* `run.py:97` — `"misses": misses[:200]` against `"misses_total": 1940`. **10.3 %**
  of `zero_space` misses carry a witness.
* `run.py:166-170` — `false_certificates[:20]` (of 58), `inv_closed_misses[:20]`
  (of 1036), `admissibility_violations[:20]` (of 742).

RESULTS.md's validity table: "every miss carries a concrete witness | yes —
`misses[]`, `witnesses{}`". And RESULTS.md line 45: "1940 laws miss in total.
**Every one** is emitted with the world id, the law's support, the offending
transition index and the operation that caused it." That is false as written.

By §5's own reading ("The run is **valid** iff all of:"), the run does not meet
its own validity bar. The fix is one line (`misses` uncapped, or a documented cap
recorded as a deviation) — but "recorded as met" is the failure mode this
pre-registration was written to prevent.

---

## (b) Is the hit rate manufactured by the split?

`adversarial/a2_recut.py`, all on the delivered 120-world corpus:

| cut | global laws | `delta_hit` | train covers every op |
|---|---|---|---|
| **Z-S1 as registered (70/30, salt 5115)** | 180 | **100.0 %** | 120/120 |
| random 70/30, salt `0xBEEF` | 180 | 100.0 % | 120/120 |
| random 90/10 | 180 | 100.0 % | 120/120 |
| contiguous prefix 70 / suffix 30 | 180 | 100.0 % | 120/120 |
| random 50/50 | 181 | 98.3 % | 118/120 |
| contiguous suffix 70 (train = last 42) | 182 | 97.8 % | 118/120 |
| parity of transition index | 187 | 89.8 % | 111/120 |
| **random 20/80** | 252 | **35.3 %** | 48/120 |
| **Z-S2 (leave one op out)** | 1680 | **13.1 %** | 0/780 |
| **leave TWO ops out** | 6140 | **2.0 %** | 0/2320 |

The rate is a step function of one binary: does the training half witness every
operation? It has no other content. A 20/80 split is exactly as defensible as
70/30 and moves the headline 65 points. "100.0 %" and "13.1 %" are the two ends of
a dial the harness set, not two properties of the engine.

### F9 · Z-S1's 100 % is driven by `T`/`|ops|`, not by the coverage guarantee — SUSTAINED, with a correction to my own hypothesis

I expected `parityworld.build:57-62`'s "every operation walked once first" rule to
be the culprit. It is not the main one. Removing the guarantee entirely:

| corpus | `T` | global `delta_hit` | train covers every op |
|---|---|---|---|
| no guarantee | 60 | 99.4 % | 118/120 |
| no guarantee | 20 | 61.0 % | 53/120 |
| no guarantee | 12 | 52.5 % | 18/120 |
| no guarantee | 8 | 49.7 % | 5/120 |

At `T = 60` with `|ops| ≤ 9`, coverage survives by sheer repetition. The real
driver is the corpus constant `N_TRANSITIONS = 60`, chosen in the pre-registration
without being flagged as load-bearing. Either way the conclusion is the same and
neither knob is a property of `zero_space`.

### F10 · The `cell_local` 92.9 % "surprise" is a boundary artefact of 1-D windows — SUSTAINED

RESULTS.md calls this "the run's one real surprise … thinner evidence
**manufactures encoding-local laws that are not there**", and `ENGINE_TABLE.md`
carries it as a `scope` finding.

`operations_for` builds *contiguous* windows on a line, so cell `0` is touched by
exactly one operation and cell `n-1` by exactly one. Withhold either and that cell
is constant in the training data, which mints exactly two spurious `cell_local`
laws (`B@c` and `R@c`). Nothing else can happen.

Measured (`adversarial/a7_celllocal.py`): all misses sit on cells
`{0: 240, 5: 80, 7: 80, 9: 80}` — cell 0 and cell `n-1`, nowhere else — arising in
exactly 240 = 120 worlds × 2 boundary operations of the 780 variants. Rebuild the
identical family with **wrap-around** windows, so every cell is touched by `k`
operations:

```
contiguous (delivered)   cell_local laws=6800  hit= 92.9 %   global laws=1680  hit= 13.1 %
cyclic                   cell_local laws=8000  hit=100.0 %   global laws=1080  hit= 66.7 %
```

`92.9 → 100.0` and `13.1 → 66.7`. Both published `zero_space` numbers are
properties of "the corpus is a line segment, and a line segment has two ends".
The *mechanism* RESULTS.md describes is real; the *magnitude* it publishes is a
fact about `parityworld`'s geometry. The table should not carry `92.9 %` as
evidence about `scope`.

### F11 · `26.4 %` is stable across `n`, and the lp side re-cuts sanely — OVERTURNED

`adversarial/a6_lp_recut.py`:

```
n=4  geometries=4   cases=80    silent=16   certs=64   inv_closed=31.2 %  false=6
n=5  geometries=6   cases=270   silent=68   certs=202  inv_closed=31.7 %  false=8
n=6  geometries=8   cases=672   silent=286  certs=386  inv_closed=23.8 %  false=26
n=7  geometries=10  cases=1400  silent=644  certs=756  inv_closed=25.9 %  false=18
```

No single `n` drives the pooled 26.4 %. Withholding two geometries instead of one
moves it to **8.5 %** (n ∈ {4,5}, 715 certificates, 52 false), which is the
expected monotone response rather than a discontinuity. This is a real
measurement and I could not break it.

### F12 · A state-level hold-out is vacuous for this engine — SUSTAINED (as a limit on what L-L2 can mean)

Dropping one state's outgoing edges leaves `moves_from_graph` unchanged in
**1024 / 1024** cases, so the LP, the certificate and every metric are
bit-identical. The geometry is the only unit that can be withheld from this
engine, which is the right choice — but it also means the "held-out states" of
L-L2 are held out of nothing (F7).

---

## (c) Does the table write "not tested" as "tested, and the boundary is thus"?

### F13 · "the recovered laws extrapolate perfectly" — SUSTAINED

`tools/engine_table.py:484`, rendered at `ENGINE_TABLE.md:22`:

> "Under a random {ho.zs_train_pct} / {ho.zs_heldout_pct} transition split the
> recovered laws **extrapolate perfectly** — **{ho.zs_s1_global} %** of global
> laws hold on the withheld transitions."

Nothing extrapolated (F1). The correct sentence is: *under a random transition
split the withheld transitions repeat difference vectors already in the training
set, so the check is vacuous and returns 100 % by construction.* As it stands the
cell converts "the cut withheld nothing" into a measurement of extrapolation, in
the one row the ticket exists to stop over-claiming.

### F14 · Corpus scope is stated plainly — OVERTURNED

Row 3 already carries "Behaviour on any family but `parityworld` … 边界未测" and
row 4 "only the `jumpgraph` family was tested", and the E17 paragraphs name their
corpora ("120 `parityworld` worlds", "289 `pegN` instances"). A reader is not
invited to think `g50t` or any real world was held out. The generality limit is
honestly drawn; I tried to break this and could not.

### F15 · The "0 reached candidates.jsonl" pass, as written — SUSTAINED

`engine_table.py:500` / `ENGINE_TABLE.md:23`: "**The pass is that the emit boundary
already holds: {ho.lp_gate_let_through} of those certificates reach
`candidates.jsonl`.**" See F5: 0 under the harness's call, 1408 (including 58
false) under the caller's. The number is not wrong; the sentence around it is,
because it names a boundary as holding under conditions the boundary will never
see. The `counting`/`arithmetic` sub-claim is bookkeeping (F6).

### F16 · "Alone among the eight rows … was not circular" — SUSTAINED

See F7. The claim is not merely unsupported; the evidence offered for it is
entailed by a condition already checked on the fitting evidence.

### F17 · The standing rule binds nothing and no test enforces it — SUSTAINED

`ENGINE_TABLE.md:69-73`: "Where no held-out validation exists, a cell may say
「在观测证据上自洽」 and may not say 「已验证」."

* `在观测证据上自洽` occurs **once** in the whole file — inside the rule itself.
  No row uses it.
* `已验证` occurs **four** times: the heading, the rule, and twice inside rows 3
  and 4 *in quotation marks, discussing the word*. No re-check cell asserts it.
* `grep -rn "已验证\|在观测证据上自洽" tests/` returns **nothing**.
  `tests/test_engine_table.py` enforces `边界未测` for `ic3_pdr` (`:46-73`) and
  non-empty boundary cells (`:36-43`); it has no analogue for the new rule.

So the rule is a paragraph, not a gate. Contrast `UNMEASURED`/`边界未测`, which has
a test. The rule as drafted is also unenforceable in the negative direction — it
forbids a word no cell currently uses.

### F18 · Every published numeral is probed, and the tripwires bite — OVERTURNED

`python -m tools.engine_table --check` returns 0;
`test_every_number_in_the_table_is_backed_by_a_probe` passes; all 21 `ho.*` probes
resolve against `results.json` and every `expect` literal matches. I mutated two
probes (P1: wrong denominator; P5: averaging rates instead of pooling counts) and
both were caught by `tests/test_engine_table.py`. The E9 mechanism works. The
exemption list did grow by three tokens (`"0100"`, `"0011"`, `"3,2,1"`,
`test_engine_table.py:99`) but they are genuinely labels, and the weight vector was
correctly kept out of the prose.

### F19 · The `k = 2` / `k = 3` disaggregation is post-hoc and only the code says so — SUSTAINED (minor)

`run.py:45-55` discloses it: "added after the headline was read, to test
prediction 2". Neither `RESULTS.md` nor `ENGINE_TABLE.md` repeats that disclosure,
and the table states `0.0 % at k = 2 against 22.9 % at k = 3` with the same
authority as the pre-registered figures. The disclosure belongs where the number
is read, not only where it is computed.

---

## Mutation table

19 mutants. **None of them was chosen to match an existing test** — `heldout/` has
no tests at all (`grep -rln heldout tests/` → nothing), so the interesting column
is not pytest but "did the run's own gates notice". Sources:
`adversarial/a5_mutants.py` (M1–M13, monkeypatch) and
`adversarial/mutplug_p*.py` (P1–P6, pytest plugins).

| # | mutant | injected in | effect on the published numbers | caught by | survived? |
|---|---|---|---|---|---|
| M1 | `random_transition_split` returns **overlapping** train/test (12-transition leak), asserts removed | `heldout/split.py:36` | **nothing moves at all** | nothing | **SURVIVES** |
| M2 | `fit` ignores `train` and fits on all 60 transitions | `heldout/zero_space_heldout.py:52` | Z-S2 global 13.1 → **100.0**, cell_local 92.9 → **100.0** | nothing (`fit_matches_engine` passes — it tests train = everything) | **SURVIVES** |
| M3 | `fit` sneaks **one** held-out difference into the fit | same | Z-S2 global → 100.0 | nothing | **SURVIVES** |
| M4 | `score` re-checks the **train** transitions | `zero_space_heldout.py:86` | Z-S2 global → 100.0, cell_local → 100.0 | nothing | **SURVIVES** |
| M5 | `fit_matches_engine` always returns `True` | `zero_space_heldout.py:77` | nothing | nothing | **SURVIVES** |
| M6 | `leave_one_operation_out` trains on everything, asserts removed | `heldout/split.py:45` | Z-S2 global → 100.0 | nothing | **SURVIVES** |
| M7 | `parityworld.build` drops the coverage guarantee | `heldout/parityworld.py:57` | Z-S1 100.0 → 99.4 | nothing | **SURVIVES** |
| M8 | `parityworld.build` leaves an operation unwitnessed | `heldout/parityworld.py:61-62` | — | `build`'s own `AssertionError` → `run.py` **exit 3** | caught |
| M9 | `graph_minus_geometry` deletes nothing | `heldout/peg.py:96` | inv rate 31.6 → **100.0**, false 14 → **0**, gate let-through 0 → **198** | nothing (`matches_fixture_peg4` never touches it) | **SURVIVES** |
| M10 | `matches_fixture_peg4` always returns `(True, [])` | `heldout/peg.py:119` | nothing | nothing | **SURVIVES** |
| M11 | `_admissibility_on_heldout` `continue`s past the violating states | `lp_potential_heldout.py:93` | violations 154 → **0** | nothing | **SURVIVES** |
| M12 | held-out `inv_closed` scored `< 0` instead of `<= 0` | `lp_potential_heldout.py:155` | inv rate 31.6 → 27.1 | nothing | **SURVIVES** |
| M13 | emit gate handed the **reduced** graph (not a defect — the harness's own premise) | `lp_potential_heldout.py:158` | gate let-through 0 → **266 / 266** | nothing | **SURVIVES** |
| P1 | `ho.zs_s1_global` probe divides by `laws + 1` | `tools/engine_table.py` | 100.0 → 99.4 | `test_engine_table.py::test_the_table_is_current…` **fails** | caught |
| P2 | `check_exactly`'s `inv_closed` uses `< 0` | `engines/lp_potential/potential.py:254` | — | pytest: **14 failed, 33 errors** | caught |
| P3 | `random_transition_split` leaks (as M1) | `heldout/split.py` | — | pytest: **504 passed** | **SURVIVES** |
| P4 | `graph_minus_geometry` no-op **and** `fit_matches_engine` always True | `heldout/peg.py`, `zero_space_heldout.py` | — | pytest: **504 passed** | **SURVIVES** |
| P5 | `ho.zs_s2_k3` probe averages rates instead of pooling counts | `tools/engine_table.py` | 22.9 → 22.6 | `test_engine_table.py` **fails** | caught |
| P6 | all three E17 rate probes read `value_hit` instead of the pre-registered `delta_hit`, provenance strings unchanged | `tools/engine_table.py` | **no digit moves** | nothing (`4 passed`) | **SURVIVES** |

**14 of 19 survive.** The pattern is not random: everything inside `engines/` or
`tools/` is caught (P1, P2, P5); everything inside `heldout/` survives unless it
trips an assertion the delivered code already had (M8). The two pre-registered
"validity gates" are themselves undefended — disabling either (M5, M10) is
invisible — and `fit_matches_engine` is structurally incapable of detecting
leakage, because the only case it examines is the one where nothing is withheld
(M2, M3, M6 all pass it while fitting on the held-out data).

M1 deserves separate mention. It is the classic held-out-validation catastrophe —
test rows inside the training set — and it changes **no digit of any published
number**. That is F1 restated as an experiment.

---

## Independent recomputation

Everything below was computed by code I wrote, not read out of `results.json`;
`results.json` was opened only afterwards, to compare.

**`zero_space`** (`adversarial/a1_zs_recompute.py`, fit and score re-implemented
from `engines.zero_space` directly):

| bucket | mine | `results.json` |
|---|---|---|
| Z-S1/global | 180 laws, **100.0 %** | 180, 100.0 % |
| Z-S1/cell_local | 960 laws, **100.0 %** | 960, 100.0 % |
| Z-S2/global | 1680 laws, **13.1 %** | 1680, 13.1 % |
| Z-S2/cell_local | 6800 laws, **92.9 %** | 6800, 92.9 % |
| Z-S2/global n6-k3 / n8-k3 / n10-k3 | 20.0 / 25.0 / 22.7 % | same |
| Z-S2/global n6-k2 / n8-k2 / n10-k2 | 0.0 / 0.0 / 0.0 % | same |

**`lp_potential`** (`adversarial/a3_lp_recompute.py`, with the peg state space,
the move geometry and the BFS ground truth written from scratch — only
`solve_certificate` is shared, since it is the thing under test): all thirteen
counts agree exactly — instances 289, cases 2422, silent 1014, errors 0,
certificates 1408, `inv_closed` hits 372 = 26.4 %, false certificates 58,
gate-let-through 0, raised-potential 1036, held-out admissibility violations 1778,
baseline certificates 105, states tested 506, baseline violations 0.

**Reproducibility.** `python -m heldout.run --out …` twice:

```
RUN1 EXIT=0 ; RUN2 EXIT=0
RUN1==RUN2 byte-identical
REPRO==COMMITTED byte-identical
```

So `results.json` is exactly what the committed harness produces — it was not
hand-edited.

**Manifest.** All **14 / 14** `files[].sha256` in `MANIFEST.json` verify against
the working tree, including the two files (`heldout/run.py`,
`heldout/lp_potential_heldout.py`) edited after the harness commit.

**Git ordering.**

```
git merge-base --is-ancestor ef382c9 e0fd43a   -> ANCESTOR-OK
git diff ef382c9 HEAD -- .../PREREGISTRATION.md -> empty
git log --oneline -- engine-rig/heldout/split.py -> (no commits after c781a73)
```

`git diff c781a73 e0fd43a -- engine-rig/heldout/` is three hunks: `D-008 → D-014`
in a docstring, the `s1_train_share_pct` constants, and the third tally bucket
(the `k`-disaggregation, F19). **No split rule and no hit definition changed after
the numbers were seen.** That claim survives.

**Pytest, run by me on this machine:**

```
$ cd engine-rig && python -m pytest . -q          -> exit 0 (summary suppressed by `addopts = -q`)
$ cd engine-rig && python -m pytest .             -> 504 passed, 27 skipped in 30.36s ; exit 0
```

Matches `measured/pytest.txt`, including its note that `-q` swallows the summary
line. Honestly recorded.

**The smallest witness, by hand.** `peg4`, goal `0100`, start `0011`, geometry
`jump(3,2,1)` withheld, `w = [0, 1/2, −1/2, 0]`. `delta(m) = w[dst] − w[src] − w[over]`.

| geometry | in the LP? | `delta` | ≤ 0 ? |
|---|---|---|---|
| `jump(0,1,2)` | yes | `w2 − w0 − w1 = −1/2 − 0 − 1/2 = −1` | ✓ |
| `jump(1,2,3)` | yes | `w3 − w1 − w2 = 0 − 1/2 + 1/2 = 0` | ✓ |
| `jump(2,1,0)` | yes | `w0 − w2 − w1 = 0 + 1/2 − 1/2 = 0` | ✓ |
| **`jump(3,2,1)`** | **withheld** | `w1 − w3 − w2 = 1/2 − 0 + 1/2 = +1` | **✗** |

`potential(0011) = w2 + w3 = −1/2`. `potential(0100) = w1 = +1/2`.
`inv_init`: `−1/2 ≤ −1/2` ✓. `goal_break`: `1/2 − (−1/2) = 1 ≥ margin 1` ✓.
`inv_closed` over the truncated list: ✓ (three rows above). So all three
conditions are exactly true in the rationals, and the certificate reads *"goal
unreachable from 0011"*.

Reachability: from `0011` pegs sit at 2 and 3. `jump(3,2,1)` needs peg at 3 ✓, peg
at 2 ✓, hole at 1 ✓; applying it clears 3 and 2 and fills 1, giving `0100` — the
goal, **in one move**. The containing path `1101 → 0011 → 0100`: from `1101` (pegs
0, 1, 3) `jump(0,1,2)` needs peg 0 ✓, peg 1 ✓, hole 2 ✓ → `0011`. Two moves,
exactly as Fixture C's docstring records.

Every claim in RESULTS.md's witness paragraph checks out, and the weights are
present in `results.json :: lp_potential.witnesses.false_certificates` as the table
says.

---

## What I could not check, and why

1. **Any world family other than `parityworld` and `pegN`.** `zero_space` would
   accept `gridworld`/`hypset` trajectories but the E17 harness has no adapter for
   them, and `lp_potential` hard-codes peg geometry (row 4 already says so). So my
   F10 counter-corpus (cyclic windows) is still `parityworld`; I have shown the
   numbers are corpus-dependent, not what they would be on a different engine
   domain.
2. **`g50t` or any live-API data.** Out of scope by the pile cut and by the
   instructions; no network was touched. Nothing in E17 is held out on real data
   and I could not create such a check.
3. **Whether HiGHS's `None` verdicts are genuine infeasibilities.** The 1014
   silences rest on the solver's float infeasibility flag with no exact Farkas
   dual, which row 4 already marks 边界未测. If some of those are wrong, the
   denominator `1408` is wrong too. I did not attempt an exact certificate of
   infeasibility.
4. **Leave-two-geometries-out at `n = 6, 7`** — I ran it only at `n ∈ {4,5}`
   (795 LP solves) for time. The trend (26.4 → 8.5 %) is clear but the pooled
   figure is not directly comparable to the delivered one.
5. **The three `fuzzlab` expectation corrections** (`500 → 60`, `55 → 64`,
   `15 → 14`). I confirmed the table probes now agree with `fuzzlab/out/*.json`
   via `--check`, but I did not audit the fuzzlab track's own commits
   `eb61aa9` / `404e136` to confirm the downward corrections were themselves
   sound. That is another track's work.
6. **Whether the 58 false certificates are exactly the reachable instances** —
   I reproduced the count from my own BFS, which agrees, but both my BFS and the
   harness's assume the same move semantics (`apply` clears src and over, fills
   dst). A shared misreading of peg solitaire would be invisible to both. Fixture
   C's committed docstring is the third party, and it agrees on the one path I
   checked by hand.

---

## What should change

In descending order of damage:

1. Strike "extrapolate perfectly" from `engine_table.py:484` and record Z-S1 for
   what it is: a cut that withholds no distinct difference vector, hence 100 % by
   construction. Either drop the figure or publish it beside the sentence
   "120/120 worlds: every held-out difference vector also occurs in training".
2. Re-word `engine_table.py:500` and RESULTS.md's "the emit gate holds": say that
   the gate was scored against the complete graph, and that when it is handed the
   graph the LP was fitted on, 1408 of 1408 — 58 of them false — are emitted.
3. Strike "Alone among the eight rows … was not circular" (`engine_table.py:501`).
   L-L2 on complete graphs is entailed by `inv_closed`.
4. Uncap `misses` and the `witnesses{}` lists in `run.py`, or record the cap as a
   deviation from §5.3 instead of ticking the criterion.
5. Drop `value_hit` or say in one line that it is provably equivalent to
   `delta_hit` on a path trajectory.
6. Add tests for `heldout/`. Start with the three that would have caught M1, M4
   and M9: a split whose halves must be disjoint *and* whose held-out difference
   vectors must not all appear in training; a scoring test on a hand-built world
   with a known miss; and a `graph_minus_geometry` test asserting the withheld
   geometry is absent from `moves_from_graph(reduced)`.
7. Either give the 「已验证」 standing rule a test, or mark it as guidance rather
   than a rule.
8. Label the `k = 2 / k = 3` figures post-hoc where they are published.

None of this touches the run's real achievement: the pre-registration held, the
numbers are reproducible to the byte, and the run refused to set a threshold that
would have turned a boundary into a defect. The problem is entirely in the
sentences wrapped around the numbers.
