# P3 — verification half

Verifier: a separate agent from the one that wrote the P3 code change. Scope is
`PREREGISTRATION.md` § "P3 — zero_space says its `scope` was not proved" only.
P2's census and P4's N2 control belong to other agents and were not touched.

Branch `agent/e15-solver-status-bit`, worktree
`.worktrees/e15-solver-status-bit`, base commit
`e942ee6d1ea6109175032a0af67adda357ea1f0c`. Zero API calls, zero network.
Nothing outside `engine-rig/` was written; `release/MANIFEST.jsonl` was read and
not edited.

Drivers (both written by this verification, both in this run directory):

* `p3_check.py` — runs the real public entry `engines.zero_space.run` over a
  10-colour palette and over the 2-colour baseline, and reads the pass
  conditions off the emitted candidate rows rather than off internal state.
* `p3_counterfactual.py` — the non-vacuity check for P3.3: monkeypatches
  `Law.as_json` to emit the same keys **ungated** and shows the artifact hash
  moves. Writes only into a temp directory.

## Verdict

| item | verdict |
|---|---|
| P3.1 no law reports `scope == "global"`, degraded label is a distinct word | **PASS** |
| P3.2 degradation written positively, in `bench/ladder.py:74-82`'s shape | **PASS, with two stated divergences** |
| P3.3 extra keys only on degraded rows; artifact sha256 unchanged | **PASS** (artifact byte-identical) |
| — but the manifest pin quoted in the pre-registration is **already stale**, by two commits that predate this branch | **finding, not an E15 failure** |

`python -m tools.validate_candidates artifacts/candidates.jsonl` → `OK
artifacts/candidates.jsonl (44 rows)`, exit 0, both before and after
regeneration.

`python -m pytest` → **519 passed, 27 skipped**.

---

## P3.1 — PASS

Trajectory: 4 cells, 10 colours (`c0`…`c9`), 12 transitions, a deterministic
adjacent-swap walk. 10 > `SUBSET_ENUMERATION_LIMIT = 8`, so every cell truncates.
Run through `engines.zero_space.run(..., out_path=...)` — the real entry point,
emitting real candidate rows — and the assertions read off the emitted JSONL.

```
truncated_cells        [0, 1, 2, 3]
n_features             40
laws                   31   (28 cell_local + 3 undetermined)
scopes present         ["cell_local", "undetermined"]
rows with scope == "global"        0
rows with "global" as a substring  0
result.global_laws()               []
```

Both halves of the condition hold:

* No law reports `scope == "global"`. The 3 quotient representatives that
  *would* have been promoted to `global` before E15 come out as `undetermined`.
* The degraded label is a distinct word, and deliberately **not a superstring**
  of `global` — so neither `scope == "global"` nor the sloppier
  `"global" in scope` resurrects the claim. A consumer filtering on `"global"`
  gets 0 laws where it previously got 3: strictly fewer, never a wrongly
  promoted one.

The 2-colour baseline still reports `global` (`baseline_scopes: ["cell_local",
"global"]`, `truncated_cells: []`), so the downgrade is not a blanket one.

## P3.2 — PASS, with two divergences worth stating

`bench/ladder.py:74-82`, the over-budget rung, does five things:

1. still emits the row rather than dropping it;
2. withholds the strong claim explicitly, as a **negative bit** —
   `"proved_unsolvable": False`;
3. carries an `error` string prefixed `"over budget: "` that names the budget;
4. nulls the fields that would have carried the answer (`plan_length`,
   `nodes.expanded`, `timing.wall_seconds`);
5. `failures()` (`ladder.py:248`) whitelists `"over budget"` so a budget is
   reported but not counted as a defect.

The degraded zero_space payload:

```json
"scope": "undetermined",
"scope_proved": false,
"subset_enumeration_limit": 8,
"truncated_cells": [0, 1, 2, 3],
"error": "over budget: cell-local enumeration capped at 8 colours per cell; cells [0, 1, 2, 3] were searched only for singletons and their full set",
"scope_note": "scope is 'undetermined', not 'global': a cell-local explanation for this law may exist in cells [0, 1, 2, 3] and was not searched for. The law itself is unaffected -- it holds on the trajectory either way -- but whether it is a fact about the world or about the encoding is undecided here."
```

Checked mechanically on all 3 degraded rows, all true: the negative bit is
present and is `False`; `error` contains `"over budget"` and the literal `8`;
`subset_enumeration_limit` equals the module constant; `truncated_cells` equals
the result's; the prose sentence is present. So the pre-registration's three
named requirements — *the limit*, *the truncated cells*, *a sentence saying what
the label now means* — are all met, and `scope_proved: False` is a faithful
analogue of `proved_unsolvable: False`. Point 3 is arguably done better than
ladder.py, which delegates naming the budget to an exception's `str()`, whereas
this formats the constant in directly.

Two honest divergences from the shape, neither of which I think sinks the item:

**(a) ladder nulls the answer field; zero_space relabels it.** `ladder.py` says
"no answer" by setting `plan_length: None`. zero_space does not null `scope`; it
writes a third word into it. That is a different mechanism for the same
discipline — and it is the mechanism P3.1 *requires*, since a `null` scope is
something a consumer might coerce, whereas an unknown word is not. The two
pre-registration conditions are internally consistent; but "matches the
established shape" is true of the discipline, not of the field typing.

**(b) ladder emits `error` unconditionally (`None` when fine); zero_space omits
it entirely on good rows.** This is a real departure, and it is *forced* by
P3.3 — an unconditional key re-hashes every row (see below). The consequence is
concrete: `payload["error"]` raises `KeyError` on a non-degraded zero_space
candidate where the same expression on a ladder row yields `None`. `.get()`
works for both. Notably `ZeroSpaceResult.as_json()`, which is **not** hashed
into any candidate id and so can afford it, *does* follow ladder.py exactly,
carrying `"error": None` unconditionally. So the engine follows the shape
wherever it can and departs only where content-addressing forbids it. I record
that as the deliberate, documented trade-off it is, not as a defect.

Two further observations, offered as doubts rather than findings:

* **Point 5 has no counterpart.** ladder.py pairs its positive record with a
  reader (`failures()`) that knows `"over budget"` is not a defect. Nothing in
  the rig currently reads `payload["error"]` on a zero_space row —
  `tools/check_status_bit.py` (another agent's, untracked) reads `scope`, not
  `error`. The positive record exists; it has no consumer yet.
* **The run-level degradation record never reaches an artifact.**
  `ZeroSpaceResult.as_json()` (`"form": "zero_space_run"`) composes a clean
  ladder-shaped summary with `scope_counts` and an unconditional `error`, but
  `zero_space.candidates()` emits only `to_payload(law, result)` per law — grep
  finds `"zero_space_run"` in exactly one place, its own definition. So in the
  emitted stream the budget appears **only** on `undetermined` rows. A truncated
  run whose null space happened to be entirely explained by found cell-local
  laws would emit zero `undetermined` rows and therefore leave no trace of the
  truncation in `candidates.jsonl` at all. That is outside P3's three stated
  conditions (no law would be wrongly promoted in that case, since there is no
  quotient representative to promote), so it is not a failure of this item — but
  it is a gap someone should know about.
* The gate is on the **label** (`scope == UNDETERMINED`), not on
  `scope_exhaustive`. So the 28 `cell_local` rows from the truncated run carry
  no truncation marker. The code's justification is sound — a found cell-local
  law was *proved*, and the budget cut short the searching, not the finding — so
  no false claim leaks. Recorded because it is a judgement call, not a
  tautology.

## P3.3 — PASS on the artifact; the quoted pin is separately stale

### The regeneration

`artifacts/candidates.jsonl` is produced by
`python -m tools.run_all --out artifacts/candidates.jsonl --deterministic
--force` (the command named in `tools/run_all.py`'s own header; the bare
`--force` writes to `out/candidates.jsonl`, which is a different, untracked
file). `python -m fixtures.generate_all` was also run — the fixtures feed the
engines, and it left the tree unchanged.

```
sha256 before (HEAD blob and on disk)  5113ad321f680af0133ae17e2a549a8c75edd90ebfbcd69d9cb076b86daded8a   47705 bytes
sha256 after  regeneration #1          5113ad321f680af0133ae17e2a549a8c75edd90ebfbcd69d9cb076b86daded8a
sha256 after  regeneration #2          5113ad321f680af0133ae17e2a549a8c75edd90ebfbcd69d9cb076b86daded8a
sha256 after  regeneration #3          5113ad321f680af0133ae17e2a549a8c75edd90ebfbcd69d9cb076b86daded8a
sha256 after  regeneration #4 (guarded) 5113ad321f680af0133ae17e2a549a8c75edd90ebfbcd69d9cb076b86daded8a
```

`git diff --stat engine-rig/artifacts/` is empty and `git status --porcelain
engine-rig/artifacts` prints nothing: **the artifact is byte-identical to
HEAD after regeneration, and byte-identical across four runs.** LF endings
preserved (0 CRLF), 44 rows, 9 of them zero_space. Nothing needed reverting.

### The keys really are gated — non-vacuity

A hash that does not move proves nothing unless a wrong version would move it.
`p3_counterfactual.py` re-runs the identical driver with `Law.as_json`
monkeypatched to add the same four keys to **every** row:

```
checked_in artifact  5113ad321f680af0133ae17e2a549a8c75edd90ebfbcd69d9cb076b86daded8a
control  (shipped)   5113ad321f680af0133ae17e2a549a8c75edd90ebfbcd69d9cb076b86daded8a   matches
mutant   (ungated)   3acf09e9f5505064b5bf48c320b9e29633b6932a9a90298a6372d7484a985755   differs
zero_space ids changed by the mutant: 9 of 9
```

`common/candidates.py:_make_id` derives the deterministic id as
`uuid5(NS, sha256(dumps([engine, kind, payload, evidence])))` — content-addressed
on the payload, exactly as the pre-registration says. So an unconditional key
re-hashes **every one** of the 9 zero_space rows, and the gate is what prevents
it. The check is not vacuous.

Direct confirmation of the gating, from the emitted rows:

```
extra keys on the 28 non-degraded rows of the truncated run   []
extra keys on the 5 rows of the 2-colour baseline run         []
extra keys on all 3 degraded rows                             all five present
```

No checked-in fixture has more than 2 colours, so no row in
`artifacts/candidates.jsonl` is degraded and none carries the new keys.

### Finding: the pin the pre-registration quotes is two commits out of date

`release/MANIFEST.jsonl:667` does carry the quoted string, verbatim:

```json
{"class": "A", "class_name": "self-built", "evidence": "no ARC game id appears in this file",
 "path": "engine-rig/artifacts/candidates.jsonl",
 "sha256": "679fe331cbc82191928a63b766c8f853c236756fce27ef71928d9af7078cfdad",
 "size": 47054, "verdict": "releasable"}
```

But `679fe331…` is **not** the current artifact and was not the current artifact
before this branch existed. Hashing the blob at each commit that touched the
file:

| commit | sha256 | size |
|---|---|---|
| `dbb0243` commit the M8 candidate stream | `d50e7e72…` | 24779 |
| `17fe471` engine-rig M9 | **`679fe331…`** ← the pin | 47054 |
| `3de10b7` the verdict was already computed | `b74576fa…` | 47270 |
| `c6a5b82` the fix left a sibling unread | **`5113ad32…`** | 47705 |

`c6a5b82` is an ancestor of this branch's base commit `e942ee6`, and `e942ee6`'s
blob is already `5113ad32…`. So the artifact moved twice after
`release/MANIFEST.jsonl` was written, and the manifest was not re-enumerated
either time. The drift predates E15 entirely and is not caused by it.

This matters for how P3.3 is read. Taken literally — "regenerating the artifacts
must leave **that** sha256 unchanged", where *that* is `679fe331…` — the
condition was **unsatisfiable at the moment it was pre-registered**, because the
tree already disagreed with the pin. Taken as it was plainly meant — *the E15
change must not move the artifact's hash* — it **passes**, cleanly and
reproducibly, and the counterfactual above shows the check has teeth. I record
the item as a pass on the intent and flag the literal wording as defective.

The stale pin is a live problem for someone, just not for this ticket:
`release/reproduce.py:204` compares each manifest hash against the working tree
and grades a mismatch `manifest-stale` — "the tree moved after MANIFEST.jsonl
was written; re-run `release/enumerate.py`". That is the other track's call to
make. **`release/MANIFEST.jsonl` was not edited by this verification**, per the
instruction and per `CLAUDE.md`'s rule against touching another track's files.

## Working-tree state after this verification

No tracked file was modified. `git status --porcelain engine-rig` lists only
untracked files, and `engine-rig/artifacts/` is clean. Files this verification
added, all inside this run directory:

* `runs/20260729T044500Z-E15-solver-status-bit/p3_check.py`
* `runs/20260729T044500Z-E15-solver-status-bit/p3_counterfactual.py`
* `runs/20260729T044500Z-E15-solver-status-bit/P3-VERIFICATION.md` (this file)

Nothing was committed.

## Note on a concurrent mutation battery

One intermediate `python -m pytest` reported 2 failures in
`tests/test_solver_status_bit.py`, including an assertion that
`zerospace.UNDETERMINED` was `'global_undetermined'`. That constant reads
`"undetermined"` in the file before and after. Another agent's P5 mutation
battery was transiently rewriting the source in this shared worktree. Those
failures were artifacts of that race, not real: a clean re-run gives **519
passed, 27 skipped**.

Because the source can change underneath a run, the final regeneration was
guarded — `engines/zero_space/zerospace.py` was hashed immediately before and
immediately after `run_all`, and was verified unchanged (`7a546f51…`) across the
run that produced the reported artifact hash. Anyone re-running these numbers
while the battery is live should do the same.
