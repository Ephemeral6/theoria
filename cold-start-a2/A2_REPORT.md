# A2_REPORT — the exhibit is built, the loop turns

**Verdict: both acceptance sentences pass.** `artifacts/loop_ledger.json`,
8 beats, 8 pass, 0 fail, 0 absent. `python run_all.py` is green in ~17 seconds;
`python -m pytest` is 44 passed. Artefacts are byte-reproducible across clean
runs.

---

## 1 · What was run instead of the literal A2, and what that costs

Phase 1's A2 item reads: *"把上游那个漏了传送规则的模型移植进 DSL，机器产出那条类型
检查通过、却对世界为假的不可达定理，再以已知规则为真值走完 打脸→定位→戳探→修订→
重证→解出 全回路。"*

The first clause collided with the pile cut. DC22 is in the sealed pile — its
id is in INC-004 and deliberately nowhere in this directory — and its
upstream artifacts teach the mechanics as well as playing does. The monitor
raised it as finding F-01; it is recorded as **INC-004**, and the owner ruled on
2026-07-28, option (b):

> A2 is fulfilled by a self-built world isomorphic to DC22's failure structure
> (a pushing world with a teleport rule; hole introduced by deleting that rule
> from an otherwise-certified manual). The isomorphism argument may cite only
> the structural description already printed in Theoria §1.3 — no upstream DC22
> artifact is ever read.

That is what this directory does. The same incident corrects DC22's
contamination level from `never_audited` to `design_document_disclosed`, on the
independent ground that Theoria.md itself discloses its mechanics in §1.3 and
§3.2 — the game was design-document-contaminated before the cut was made.

### The difference, stated plainly

| | original A2 | what was run |
|---|---|---|
| the world | DC22, a sealed public game | a self-built 9×9 pushing world |
| the holed model | ported from an upstream artifact | the pipeline's own induction, minus one rule deleted by hand |
| the missing rule | DC22's teleport | a teleport, and the only proposal in any A2 stream whose effect moves the mover more than one cell |
| the history | 175 frames of play, coverage unknown | 184 frames, **exhaustive over its strata but one pair** |
| ground truth for the loop | "已知规则" — the upstream rules | this world's own transition function, reached only through frames |

**What is lost.** No claim about DC22 itself is available or made: not its
geometry, not its 175 frames, not how its search actually failed. Anything this
project later says about DC22 must carry INC-004's
`design_document_disclosed` caveat.

**What is gained, and it is not nothing.** §1.3's claim is *constructive* — it is
about what past-facing checking can and cannot see, not about one game. A
self-built world can therefore make the claim **stronger** rather than merely
re-illustrate it, in three ways this run uses:

1. **The history is near-exhaustive.** DC22's 175 frames had unknown coverage,
   which leaves "they just didn't explore enough" open. A2's play record covers
   163 of the 164 reachable (state, action) pairs with the Cart in the left
   room, and omits exactly the pair that fires the deleted rule
   (`trace_summary.json`). The defect survives near-total evidence. It is not a
   coverage failure.
2. **The history is a prefix, not a separate experiment.**
   `history_trace = raw_trace[0 .. portal_transition]`, and the cut index is
   found by looking at the frames for the single non-adjacent Cart move. There
   is no room for the question "was the history curated?"
3. **The isomorphism is machine-checked, clause by clause** — see §2.

---

## 2 · The exhibit

`theory/theory_holed.dsl` is `theory/theory.dsl` minus one rule. Nothing else
differs; `diff` the files and the deletion is the whole diff.

```
rule teleport_down [ev: t183 cov: 1/1]
  when act=push(Cart, down) and colored(below(Cart), 3) then jumped(Cart, portal_exit)
```

The ordinary inner loop then runs, unaltered and unassisted, on the holed manual
and the play record:

| gate | result | artefact |
|---|---|---|
| certify, cheap | **GREEN** — 184 frames, 14 904 pixels, **0 anomalies** | `exhibit_report.json` |
| plan (`fd_adapter`) | **UNSAT** | `plan_holed.json` |
| certificate | `zero_space` → 21-cell occupancy law → 0/1 pagoda weight | `exhibit_report.json` |
| certify, expensive | **GREEN** — Lean 4.9.0, `decide` only, no `sorry` | `generated_holed/theory.lean` |
| `#print axioms unsolvable` | **`[]`** | ibid. |

`theorem unsolvable : ¬ ∃ s : St, Reachable s ∧ Goal s = true` — 148 states, all
decided by the kernel, no Mathlib, no `native_decide`, no axioms.

**And the world reaches the goal in 18 actions** (`refutation.json`,
`solved_episode.jsonl`).

Nothing in that column is broken. The planner is right: no plan exists *under
this manual*. The invariant really is closed under the manual's `step`. Lean
really did check it and the axiom list really is empty. **The manual is wrong,
and every check in the column is a check of the manual against its own past.**

### The isomorphism, clause by clause

| Theoria §1.3 | A2's check | result |
|---|---|---|
| "漏了一条传送规则" | `engines_diff.json` — the only proposal with \|dy\|+\|dx\| > 1 | `obj1_jump_DOWN`, 1/1 |
| "那条规则从未触发" | `trace_summary.json` — the history's one omitted pair | `cart=(6,4) pressed=1 act=DOWN` |
| "不欠任何一帧" | `certify_cheap` on the play record | 184/184, 0 anomalies |
| "重放全对" | the miner on the history proposes **no** jump | `history_proposes_a_jump: false` |
| "完备搜索'正确地'证明了目标不可达" | plan UNSAT + Lean `unsolvable`, axioms `[]` | green |
| "而这一关人类可解" | an 18-action episode ends with `win: true` | refuted |

### The claim is bounded, and the bound is reported

The same holed manual against the **full sweep** is RED — 128 unexplained pixels
across 20 088 checked, 44 anomalies recorded (the cheap layer caps its anomaly
list), the first at t184, cell (6,4), where the manual keeps the Cart that the
world has already teleported away (`certify_cheap_vs_full_sweep`). The hole is invisible
*relative to the evidence its theorizer had*, which is exactly §1.3's claim and
exactly its limit. Reporting only the first half would be the kind of result
this project exists to refuse to write.

---

## 3 · The loop

Six beats, each with an artefact that settles it without re-running it. Truth is
the referee throughout, and it reaches the manual only as frames:
`refute.py` writes the world's solved episode out as a four-field trace, and
`locate.py` and `probe.py` import no world module at all.

| beat | claim | evidence | result |
|---|---|---|---|
| **打脸** | the theorem is false | `refutation.json` | 18 actions, `win` on frame 18 |
| **定位** | §1.4's three-way narrows it | `locate_report.json` | board ✗, goal test ✗, **step ✓ at t=11** |
| **戳探** | predictions first, then execute | `probes.jsonl` | 5 designed, 4 run, 1 recorded unrunnable |
| **修订** | rewritten from the probe record | `theory_repaired.dsl` | re-derivable from grown evidence |
| **重证** | old certificate dies, true one replaces it | `repair_report.json` | Lean RED then GREEN |
| **解出** | plan, and the world agrees | `plan_repaired.json` | SAT in 18, 0 mismatches |

Three things in that table are worth more than a row.

**定位 is a three-check, not a search.** §1.4 says the error is *necessarily* on
the witness path and in one of three places. All three are run rather than
stopping at the first, because "step 12 disagrees" without "and the goal test
and the board were fine" has narrowed nothing. Result: at t=11 the Cart is at
(6,4), the action is DOWN, the manual **fires nothing** and predicts it stays,
the world puts it at (7,6). Since no rule in the manual moves the mover more
than one cell, the diagnosis is sharper than "wrong": it is a **missing rule**.
Nothing can be corrected; something has to be added.

**One probe could not be run, and that is in the record.** R-05's guard frontier
never closed: `tcolor(DOWN)==3` and `at(6,4)` both fit the single witness, and
separating them needs a configuration this level cannot reach — there is exactly
one Portal. `probe_frontier` ranks the experiment at 1.0 bits and classifies it
hypothetical. P-03 records that with its reason, and the manual carries
`teleport_is_colour_triggered [probe: pending]` rather than quietly claiming the
question is settled.

**The refuted certificate has a corpse.** `theory/generated_repaired_stale/`
holds the exhibit's invariant regenerated against the repaired `step`. Lean
fails it at line 769: `tactic 'decide' proved that the proposition ... is
false`. A repaired manual that simply stopped mentioning its refuted theorem
would have been edited, not corrected.

---

## 4 · The two Lean files

This is the headline artefact and it is a pair, not a file.

| | `generated_holed/theory.lean` | `generated_repaired/theory.lean` |
|---|---|---|
| theorem | `unsolvable` | `unsolvable` |
| goal | the goal cell (2,7) | the sealed pocket (7,1) |
| invariant | 0/1 pagoda weight, 0 on 21 cells | 0/1 pagoda weight, 0 on 35 cells |
| tactic | `decide` | `decide` |
| Mathlib | none | none |
| `#print axioms` | `[]` | `[]` |
| status | **GREEN** | **GREEN** |
| **true of the world** | **NO** — 18-action witness | **YES** — 0 of 55 reachable states |

They differ in their weight table and in nothing else. The generator, the
tactic, the dependency surface and the axiom list are identical. **The
instrument cannot tell them apart, and it is not supposed to be able to.** Lean
guarantees *true relative to the manual*; whether the manual matches the world is
settled by §1.4's refutation loop and nowhere else. That is Theoria §1.10a's
two-layer regime as two files you can diff — figure 5's content, in a form a
referee can rerun.

---

## 5 · Was the repair remembered or re-derived?

A fair objection to any self-built A2: the repairer already knows the answer,
because the control manual is sitting in the same directory. Three checks
address it and none of them is "trust us".

1. **The repair was written from `probes.jsonl`**, whose P-01 record contains
   the holed manual's own prediction — written before the action was taken and
   refuted by the outcome.
2. **The grown evidence re-proposes the rule.** Running the miner on
   `probed_trace.jsonl` proposes a jump effect again
   (`engines_diff_probed.json`), so `theory_repaired.dsl` is derivable from the
   evidence the theorizer holds after M8.
3. **The agreement with the control is a test, not an assumption.**
   `test_the_repair_agrees_with_the_control_on_that_rule` asserts the two
   `when` clauses are byte-identical. It passes — which is a *result*: the same
   frontier survived the same description-length adjudication twice.

What is *not* claimed: that the repaired manual is uniquely determined. P-03
says the opposite, on the record.

---

## 6 · Two defects found in the reused compiler

A2 writes no engine and no generator: the engines are `engine-rig`'s, the parser
is the frozen v0.1 contract's, the compile backends and certify layer are
`cold-start-a0`'s, imported unmodified. An exhibit produced by a compiler
written for the exhibit would prove nothing about the instrument. Running that
instrument on a second world found two things A0 could not have seen.

**The PDDL backend cannot ground a teleport (D-A2-006).** `gen_pddl_a0` emits a
cell object only for cells in the derived arena, and a static coloured cell — a
Portal entry — is never in it. `teleport-down`'s `?p - markedcell` parameter
therefore has no inhabitant, the action never grounds, and the planner returns
**UNSAT on a manual containing the teleport rule**. A0's goal was reachable
through the Door, so no A0 plan ever needed the jump to ground: the bug was
latent and returned a correct answer by luck. A2's control manual came back
UNSAT on the first attempt. Worked around PDDL-only in
`compile_a2.pddl_addressable`; the Lean and Python forms keep the unaugmented
arena, since the Cart is never on the Portal.

**`lean_check` destroys the diagnostic when there is one (D-A2-007).** It decodes
the toolchain's output with the process locale; Lean's error messages contain
U+2019, this box is GBK, and the subprocess reader raises exactly when a proof
fails. A0 never had a red Lean file. A2 has one on purpose.

Neither was fixed upstream: `cold-start-a0/` is the theory-compiler track's
directory. Both are on `PARTNER_SYNC.md`, and
`artifacts/upstream_pin.json` hashes every upstream file A2 imports, so "which
compiler produced this exhibit" is a question the artefacts answer themselves.

---

## 7 · Red lines held

* **Zero contact with the sealed pile.** No API call, no network, no upstream
  artifact. The isomorphism argument cites only Theoria §1.3, as INC-004
  requires. The sealed game's id is not carried in this directory at all, and
  `test_no_dc22_artifact_is_present` enforces that byte-wise.
* **`cold-start-a0` is read-only, and this is verified rather than asserted.**
  `python -m tools.verify_readonly` hashes every file under `cold-start-a0`,
  `engine-rig`, `theory-compiler` and `CONTRACTS`, runs the whole pipeline, and
  hashes again: **258 files, 0 changed.** Where reuse would have meant writing
  there — A0's `plan_stage` reports into its own `artifacts/` — the driver is
  rewritten and the logic kept. `test_a2_never_writes_into_the_other_track`
  additionally restricts references to the upstream root to the bootstrap and
  the hasher. (The verifier is a script, not a pytest case: another session
  works this repo concurrently, so its files legitimately change while A2 runs
  and a test would be flaky for a reason unrelated to A2.)
* **No credential is anywhere near this.** `test_nothing_here_can_reach_the_network`
  scans every shipped file for network imports and for `ARC_API_KEY`.
* **The frozen contract is untouched.** Every candidate stream validates against
  `CONTRACTS/candidates_schema.md`; every row's `status` is `"candidate"`;
  `git status CONTRACTS/` is clean, and a test asserts it.

---

## 8 · What A2 does not show

* **Nothing about DC22.** See §1.
* **Nothing about whether an LLM would have written these manuals.** The
  theorize step is done by hand here, as in A0 — the DSL files are checked in as
  artefacts. A2 tests the instrument and the loop, not the theorizer.
* **Nothing about scale.** 55 reachable states, 148 in the Lean enumeration,
  `decide` over the whole space. The invariant is found because a wall separates
  two rooms; a world needing a genuinely clever pagoda is what A1 is for.
* **`fd_adapter` is still the bundled BFS stub**, not Fast Downward. Optimal for
  unit costs, so `SAT`/`UNSAT` and plan length are sound here; the standing
  caveat in `engine-rig/STATUS.md` is unchanged.
* **The `?dir`-parameterised rules are not used.** The miner's better manual —
  one `obj1_step` at 189/189 instead of four ground rules — cannot be compiled,
  because the Python backend's guard subset takes a literal direction. That is an
  expressiveness gap in the backend, logged here rather than worked around.
