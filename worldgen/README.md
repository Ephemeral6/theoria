# worldgen — the world factory

`Theoria.md` Phase 1's A0 dividend is a clause, not a suggestion: **"提示词的开发
迭代全部发生在自建世界族，ARC 开发堆只作验证"**. A族 of four hand-built worlds is
not a family. This is a parameterised mechanism library and twenty worlds
generated from it, each shipping its own ground truth.

```bash
python -m worldgen.verify                     # everything: build, tests, QC
python -m worldgen.build --check              # the twenty + fifteen, byte-reproducible
python -m worldgen.build t1-switch-toggle     # one
python -m worldgen.mutate --list              # the mutation corpus
python -m worldgen.mutate --knobs             # the declared semantic knobs
python -m worldgen.qc.run_qc                  # three worlds through cold-start-a0
python -m worldgen.qc.run_qc --mutants        # four mutants, against their bases
python -m worldgen.qc.diagnose_miner <id>     # why did the miner refuse this world?
```

## What a world ships

`worldgen/out/worlds/<world_id>/`, and the read licence is cold-start-a0's split
— it is the only thing standing between this catalogue and a rigged evaluation:

| file | who may read it |
|---|---|
| `raw_trace.jsonl` | **anyone.** The discovery input. Byte-format-identical to `cold-start-a0`'s producer: one JSON object per line, keys exactly `{t, frame, action, win}`, `sort_keys=True`, `separators=(",",":")`, LF, last row `"action": null`. Downstream needs zero changes. |
| `spec.json` | anyone — the picture and the legend, already parsed |
| `ground_truth.json`, `GROUND_TRUTH.md` | **scoring only** |
| `coverage.json` | scoring only |
| `reversibility.json` | scoring only — the A0′ stamp |

`out/worlds/INDEX.json` is the roster with every measured property per world.

## The mechanism library

Seven families, composable, each owning a disjoint slice of a flat integer state
vector so that a mechanism can be written and reviewed in isolation and still
compose with six others in one grid:

`push` · `gravity` · `switch_door` (toggle **and** latch, OR-networks, either
polarity) · `portal` (one-way, two-way, momentum-paired) · `count_lock`
(collect k) · `color_cycle` (order-k phase gate) · `consumable` (one-shot floor).

Three predicates decide where things may go, and the distinction is load-bearing
rather than pedantic — collapsing any two of them was a shipped defect:

| predicate | question |
|---|---|
| `occupied` | is this cell solid right now? |
| `is_free` | may an **object** be left standing here? (excludes gates, mouths, the agent's cell) |
| `can_rest` | may the **agent** be *deposited* here — teleported in, dropped by gravity — without skipping somebody's `interact`? |

## Reversibility is measured, not claimed

A0′ (`cold-start-a0/prime/A0P_REPORT.md` §1) is the reason this library exists in
this shape: **reversibility of the mechanisms matters more than the breadth of
the trajectory.** A0 saw 99 % of its state-action pairs and shipped a manual
wrong in three places; A0′ saw 47 % and shipped a perfect one, because A0's latch
gave `press_left` exactly one witness and no way to obtain a second.

So every world is stamped, per rule, with the **maximum number of times one
trajectory can witness it** — computed from the strongly-connected condensation
of the reachable graph, not asserted. `max_witnesses == 1` is the A0 failure
mode, named in advance instead of discovered in a post-mortem.

Two axes, and keeping them apart is the point:

* **`reversible`** — can the effect be undone? `collect_token`: no.
* **`re_witnessable`** — A0′'s property. `collect_token` in a three-token world:
  **yes, three times**, because each token is a fresh witness of the same rule.

They come apart in both directions and the catalogue has instances of each:
`collect_token` is one-way with three witnesses; `advance_cycler` has order k and
destroys nothing yet measures a **single witness** in two worlds, because nothing
routes the agent back to a shut phase. Conflating them is what made seven worlds
ship a claim disagreement that was not one.

## Controlled variant pairs — `worldgen/mutate.py`

A world plus **one rule-level edit**, with the edit written down in a form an
exam can compute against. Four families (`forbid_action`, `change_guard`,
`reversible_to_irreversible`, `move_portal_exit`), fifteen instances, shipped
into `out/worlds/` under opaque ids so that the id itself cannot leak an answer.

`mutate.KNOBS` declares the semantic parameters — which entity props a mechanism
actually branches on — and a test perturbs every one of them and requires the
world to move, because a knob table nothing exercises is a comment. Exactly one
knob is new (`flags["forbidden_action"]`); the rest already existed and had
simply never been declared.

`out/worlds/MUTATIONS.json` is scoring-only and carries, per edit: the operators,
the exact **detection latency** (BFS over the product of the two worlds, so it is
a minimum over every strategy rather than over one walk), the **collateral**
(rules falsified both directions, claims now false, claims to re-examine via a
computed claim→rule dependency graph, verdict and whether it flipped), and what
this territory can honestly say about **repair cost** — with the part that needs
another track's miner emitted as `null` next to its blocker rather than
approximated.

## The build gates

`python -m worldgen.build --check` refuses to ship a catalogue where any of these
fails. Every one of them was, at some point, a thing this library measured,
printed, and then exited 0 on.

1. **frame determines state** — no two distinct reachable states render alike.
   Currently 0 collisions across all 20 worlds. Nothing else means anything
   without it;
2. **solvability matches intent** — `spec.intended_solvable` against the
   exhaustive reachability decision. Exactly one world is unsolvable and it is
   the one named `t2-unsolvable-nodoor`;
3. **rule correspondence** — the set of `Outcome.rule` tags the world actually
   emits equals the set of declared primary rules. `cascade` rules (fire inside
   `settle`, so they never carry a tag) and `clause` rules (the negative branch
   of a positive rule, dormant where the geometry never presents the case) are
   exempt, reported, and each exemption is a claim;
4. **invariants** — every declared invariant, checked on every reachable state;
5. **claims** — every mechanism's `re_witnessable` claim against the measurement;
6. **determinism** — a second build in a **separate interpreter** at a different
   `PYTHONHASHSEED`, diffed byte for byte. `INDEX.json` and `MUTATIONS.json` are
   in the diff too; they were outputs nothing compared;
7. **edit family** — a mutation's declared family against what its operators
   touch, and for `reversible_to_irreversible` against the two measured
   reversibility stamps;
8. **mutant solvability** — a mutation's `intended_solvable` claim against the
   exhaustive decision. Separate from gate 2 only because a mutant's `spec.json`
   deliberately leaves the field blank: `spec.json` is open, and for a verdict
   item that field is the answer.

## Registered uses

| user | what it takes from here |
|---|---|
| prompt iteration | the whole family — this is the Phase 1 clause's "自建世界族", so theorize-prompt work happens here and the ARC development pile stays a verification set |
| `V2-exam-on-worldgen` | 20 worlds with ground truth. **The claim this row used to make was refuted from the exam's side** — it said the four variant pairs were "ready-made 改规则适应 question stems", and `exam/runs/…-V2-…/GAPS.md` established that they are not: `variant_delta` is free prose, and three of the four pairs differ in *geometry* rather than in a rule, so nothing can compute a detection latency or a collateral set from them. What is ready-made is `out/worlds/MUTATIONS.json` — see the row below |
| `C6` mutation corpus | 15 controlled variant pairs: one base world, one rule-level edit, a new measured truth, and a machine-readable descriptor carrying 检测延迟 / 连带作废 exactly and 修复成本 partly. Includes the two properties `exam.papers.adaptation.build()` refuses a paper without — an undetectable variant and verdict flips in both directions — and the solvable/unsolvable near-twins on identical boards that `GAPS.md` asks for by name. Interface: `RUN_STATE.md` §the interface |
| `E4-property-fuzz` | high-level world source; `GridWorld.explain` gives a labelled oracle per transition |
| ablation-arm calibration | tier 1/2/3 with measured reachable-state counts, and one world (`t2-lock-fragile`) known to sit **outside** the current engine vocabulary — a fixed capability-boundary fixture |
| upstream engine work | `worldgen/qc/diagnose_miner.py` localises a mining refusal to one transition pair and says whether the world or the vocabulary is at fault |

## Honest state

`worldgen/qc/PREREGISTERED.md` fixed the acceptance bar before the harness ran.
The family **missed** it — see `worldgen/qc/QC_REPORT.md` for the numbers and the
per-transition causes. The bar was not moved. What the miss is made of is the
useful part, and it is written down.
