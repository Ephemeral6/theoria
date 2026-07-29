# RUN_STATE — cold-start-a3

Work order **P-17** (`monitor/prompts/P-17-a3-transfer.md`), branch
`agent/p17-a3-transfer`, worktree `theoria-wt-p17`.

## Status

**Complete.**  All five deliverables in the work order are done, plus two the
order did not ask for (a second negative control, and a blind control arm for
the theorize step).

| # | work order item | state |
|---|---|---|
| 1 | level 1 cold start, whole ring, `domain` + `problem₁`, playbook with a theorem-grade entry | **done** |
| 2 | level 2 zero-relearn with the carried books, metered against level 1 | **done** |
| 3 | control arm — level 2 from scratch, two-column cost table | **done**, and made *blind* rather than self-reported |
| 4 | negative control — one mechanism changed, the valve must catch it | **done**, two controls instead of one |
| 5 | `A3_REPORT.md` bounding C3 offline | **done** |

## Self-reported results, and how to check each without trusting this file

| claim | check |
|---|---|
| level 2 solved carrying the books, nothing relearned | `artifacts/bill_l2_transfer.json` — `engine_stages`, `candidates_adjudicated`, `theorize_rounds`, `dsl_clauses_written` all `0` |
| the domain travelled | `diff theory/generated_l1/theory.py theory/generated_l2/theory.py` — 35 lines, all level data |
| the transfer arm planned before spending an action | `cost_to_first_plan.world_actions == 0` in the same file |
| a wrong carried domain is caught | `artifacts/negative_controls.json` — `all_caught: true`, `none_claimed_a_win: true` |
| the books are not a private convention | `artifacts/domain_agreement.json` — `canonical_only_in_left: []` |
| nothing was faked | `python -m pytest` |

## Reproduce

```bash
cd cold-start-a3
python run_all.py                    # every arm, in order
python -m pytest                     # the suite
python -m tools.verify_readonly      # other tracks hashed before and after
```

## Ritual

* `runs/p-17/` — every artefact plus `MANIFEST.json` with `prompt_id`,
  `branch`, `base_commit`, `head_commit`, the determinism pins, and a sha256
  for each artefact and each book.
* `PARTNER_SYNC.md` — appended, own paragraphs only.
* branch pushed; `master` untouched.

## Territory

Created `cold-start-a3/` only.  `cold-start-a0`, `cold-start-a2`, `engine-rig`,
`theory-compiler`, `a0-spike`, `baseline-arms`, `battery`, `proxy`, `monitor`
and `arc-recon` were read and never written; `CONTRACTS/` is byte-unchanged and
a test asserts it.  Zero API calls, zero network, zero contact with the sealed
pile.

## Open, and deliberately not closed here

* **Four defects in the reused instrument** (D-A3-003/004/005/006/007) are
  reported to their owning tracks on `PARTNER_SYNC.md` and worked around inside
  `cold-start-a3/`.  None was fixed in place.
* **R-09** — the backend cannot compile a `?dir`-lifted rule — was confirmed a
  second time, blind, and cost the control arm a theorize round.  It is an
  expressiveness gap in the Python backend, not something this track can fix.
* **The theorize step is still a person.**  The control arm answers the
  "you already knew the answer" objection; it does not turn theorize into a
  measured component.  `A3_REPORT.md` §6.
* **No repair loop was run** on the caught negative controls.  A3 tests the
  valve; A2 ran the repair loop end to end on a different defect.


---

# A6 — the transfer protocol, as an interface

Board item `A6-transfer-protocol`, branch `agent/a6-transfer-protocol`, run
`runs/20260728T1800Z-A6-transfer-protocol/`.  P-17 above is A3 and is unchanged
by this; nothing in `a3pipeline/`, `a3world/` or `theory/` (except
`theory/push/`, which is A6's own) was edited.

**This section is the deliverable the item asks for: the interface
`theoria-arm` calls.**  It is written here rather than in that directory
because A6 may not edit another arm's tree.

## Reproduce

```bash
cd cold-start-a3
python run_a6.py            # five arms, four controls, a verdict artefact
python -m a6carry.score     # every reachable transition of both worlds
python -m tools.a6_manifest # provenance
python -m pytest            # 93 tests
```

## The interface

```python
from a6carry.pack import Pack
from a6carry import protocol, pack as packlib

# 1. build a pack once, from two books
packlib.build(pack_dir=..., domain_path=..., playbook_path=..., pack_id=...,
              origin={...},                      # opaque provenance, yours
              object_colours={"Cart": [6], "Block": [2]})

# 2. carry it onto a level, as often as you like
report = protocol.carry(
    pack=Pack(pack_dir),
    executor=<your Executor>,     # the ONLY thing that knows a world
    out_dir=...,                  # compiled forms land here
    artefacts=...,                # frame, provenance, bill, arm report
    constants=None,               # taken from executor.constants() if omitted
    invariant_builder=None,       # required for a Lean form; withheld without
    on_drift="refuse",            # or "warn"; anything else is a ValueError
    arm=None)                     # defaults to "carry_<level>"
```

`Executor` is two methods and deliberately no more
(`a6carry/executor_api.py`) — a third that answered "would this state have
won?" would hand over the answer key for free, and the quota model exists to
price exactly that question:

```python
class Executor:
    name: str
    def first_frame(self) -> List[List[int]]:  ...   # 1 frame, 0 actions
    def execute(self, actions) -> Dict:         ...   # {frames, wins, actions, win}
```

Optionally `constants() -> {"goal_cell": (r, c), ...}` for the level values no
frame can show.  `a6carry/executors.py` has two working adapters
(`WorldgenExecutor`, `A3Executor`); write a third against a live API and
nothing else changes.

`report["outcome"]` is one of `pack_tampered`, `dependency_drift`,
`rebuild_refused`, `static_certify_red`, `no_planning_form`, `no_plan`, `win`,
`replay_mismatch`, `no_win`.  The first five cost **zero world actions** —
that is the point of the order the steps run in.

## What the run establishes, and what it does not

| | |
|---|---|
| the manual wins a world from another track's factory it has never seen | `t1-push-corridor`, 5 actions, optimal is 5, replay green |
| nothing was relearned to do it | `theorize_rounds` `dsl_clauses_written` `candidates_adjudicated` `engine_stages` all 0 |
| it planned before spending | `cost_to_first_plan.world_actions == 0`, one frame in |
| A3's two negative controls are still caught | both `replay_mismatch`, neither claimed a win |
| the pack's hashes and fingerprint refuse | tampered book and drifted fingerprint both stop before frame 1 |

**Four things it does not establish**, each with an artefact rather than a
promise:

1. **A green carry is about the path, not the world.**  The same pack on
   `t1-cycler-gate` — a mechanism the manual does not model — returns `win`
   with a green replay and zero unexplained pixels, because the planner routed
   around the part it is wrong about.  Driven down `RIGHT RIGHT RIGHT` the same
   manual on the same world produces eight anomalies.  Both halves are in
   `a6_acceptance.json` and both are asserted in `tests/test_a6.py`.
2. **The transfer world never exercises a shove, and the sharpest form of that
   is a coincidence worth stating plainly.**  `t1-push-corridor`'s optimal route
   walks around the block, so the transfer arm executed
   `DOWN DOWN RIGHT RIGHT RIGHT` — **byte-identical to the actions the
   wrong-world arm executed on `t1-cycler-gate`**, the arm this same file calls
   a world the manual is wrong about.  The end-to-end evidence the transfer
   produced is therefore not, by itself, distinguishable from the evidence
   produced by carrying the same pack somewhere it does not belong.  A manual
   that modelled the block as an immovable wall would have produced the same
   plan and the same green replay.  `acceptance.transfer_evidence_is_
   indistinguishable_from_the_wrong_world_arm` asserts it.

   What the carry does establish: the domain *renders, rebuilds a problem from
   one frame, compiles, plans and predicts every frame of* a new layout at zero
   relearning cost.  `a6carry/score.py` is what establishes the rest, and it had
   to be built for exactly this reason.
3. **The whole generalisation rests on two transitions.**  Not two per clause —
   two, in the 256.  `scoring_push_manual.json` reports four clauses
   `checked_and_right` with one exercising transition each, but `shove_d` and
   `block_d` compile to byte-identical guards and cannot fire apart, so those
   four counts are the same two transitions counted twice.  Both are in
   `t1-push-open`; the world the pack was carried to contributes **zero**.  The
   remaining two clauses — `shove_left`, `block_left` — are exercised by zero
   transitions in either world, because neither layout lets the agent reach the
   block's right-hand side.  They are unrefuted and unvindicated, which is not
   the same as correct, and `never_checked` is kept in a separate list from
   `checked_and_right` so the two cannot be added up.

   "256 transitions, zero disagreements" is a statement about coverage of the
   state space, not about how much of it tests the part of the manual that was
   guessed.
4. **The mover must still be named `Cart`, and the failure is quieter than
   "would not compile" suggests.**  Verified by renaming it and watching:

   * `gen_pddl_a0.py:113` — `next(o for o in problem.objects if o.name ==
     "Cart")` raises a bare `StopIteration` with no message.  Loud, but
     uninformative.
   * `compile_a3.bind_goal:125` builds `FieldAccess(obj="Cart", …)`
     **unconditionally**, ignoring the pack's `mover`.  `forms.py:78` calls it
     and then passes the correct `mover=` to `generate_python`, so `theory.py`
     — the only predictor in the system — is emitted **silently, with a goal
     about an object the manual does not contain**.
   * `a3pipeline/plan.py:133-139` hard-codes both `state.Cart_pos` and the
     action verb `("push", "Cart", direction)`.
   * `pack.py:_mover` refuses a domain with more than one acted-on object but
     never refuses one named anything else, and nothing in `build()` or
     `carry()` validates the name.

   `requires.mover` and `requires.action_vocabulary` are recorded in `PACK.json`
   and **read by nothing on the carry path** — the same defect class as the
   fingerprint that started this item, at smaller scale, inside the artefact
   built to answer it.  The push manual names its agent `Cart` for this reason
   and says so at `theory/push/domain.dsl:65-70`.  The coupling is in another
   track's generator; the honest description of it is not.

## Defects this item opened

| id | what |
|---|---|
| D-A6-001 | `gen_pddl_a0` models a level as one cell plus one boolean, so a pushable block compiles to an immovable wall and the planner returns a confident UNSAT for a correct manual.  Worked around in `a6carry/pddl_push.py`, not fixed in place. |
| D-A6-002 | `gen_lean_a0.build_axes` admits only non-mover `_colour`/`_present` fields as state axes, so a second moving object's position is not in the Lean state type.  The pack withholds the Lean form rather than emit a green certificate about a projection of the manual. |
| D-A6-003 | **A3's own `theory/playbook.dsl` does not parse** — line 81 writes `[ev: 2/2 levels, n=2 — indicative only]` where `_parse_prefer` accepts only `[ev: k/n]` — and A3 never found out, because A3 compiles its domain and never hands its playbook to a parser.  carrypack carries what parses and names the rest under `entries_unparsed`. |
| D-A6-004…007 | `actions_spent` KeyError after the actions were spent; unpadded `wins` raising IndexError mid trace-write; `on_drift` treating any string but `"refuse"` as consent to spend on a drifted toolchain; `forms_emitted` listing forms the pack never authorised.  All four fixed here with tests. |

## What was read, and when

The push manual was adjudicated from `t1-push-open`'s `raw_trace.jsonl` and its
`spec.json` legend, and its header says so.  `ground_truth.json`,
`coverage.json` and `reversibility.json` are marked *scoring only* in
`worldgen/README.md` and were not opened before the manual was written.

They were opened afterwards, and by two different readers, both for scoring:

* `a6carry/score.py` reads each world's per-transition rule tags, to check that
  the manual's guards fire where the world's own rules say they should — the
  difference between predicting the right frames and predicting them for the
  right reasons.
* RES-1 read `solvability.optimal_length` (5 for both worlds) to check the claim
  "solved in the optimal number of actions" rather than assert it from the plan
  it happened to get.  An independent BFS agrees.

Reading the answer key to *grade* a manual that is already written and hashed is
what the file is for.  Reading it to write one would not be, and the ordering is
the whole difference; it is recorded here so the ordering is checkable rather
than promised.

## Corrections made after adversarial review (2026-07-29)

Three independent adversarial passes were run before delivery.  They confirmed
the four headline claims and refuted a fifth, and the fifth is the one worth
recording here:

**The sealing claim was false as written.**  This file and `protocol.py` both
said that nothing the driver imports knows a world.  One line refutes it:

```
python -c "import a6carry.protocol, sys; print('world.a0_world' in sys.modules)"
True
```

`cold-start-a0/world/a0_world.py` — a simulator with a hardcoded 9x9 level, a
palette and a `GOAL_CELL` — arrives through `certify_a3 -> certify.replay ->
world.ground_truth`.  The test that certified the seal passed only because the
import closure it walked **stopped at the track boundary, one hop before the
leak**.  A test that misses the thing it certifies is worse than no test: it
converts an open question into a settled one.

The claim is now the narrow true one — no world *under test* (`worldgen`,
`a3world`) is reachable from the driver; those still arrive only as an
`Executor` — and the A0 leak is on the record in `KNOWN_WORLD_LEAKS` with its
import chain, with a test that fails if a new one appears and a second test that
fails if the recorded one disappears.  `cold-start-a0/` belongs to the
theory-compiler track, so the import cannot be removed from here.

Also corrected: the scorer graded a predictor without checking the manual it
parsed had produced it (demonstrated live — a mutated manual still scored zero
disagreements); `first_frame_note` claimed the frame-0 check tested the
relative-shove theorem when no rule is evaluated there at all; 22 orphan
artefacts from a superseded arm naming were being hashed into `MANIFEST.json`,
publishing two contradictory reports per wrong-mechanism world; and
`scoring_push_manual.json` had no producer anywhere in the test suite, so the
three tests carrying the only real evidence about the push mechanism passed
because the file happened to be on disk.
