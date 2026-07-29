# A4a — the build plan, written before the code

Worker RES-1, lane `campaign`, territory `ablation-arm`, branch
`agent/a4a-ablation-build` off `d1733df`.

**Why this file exists at all.** Two workers took the whole of A4 and gave it
back: `W-1611` proved the precondition (P-18's offline calibration) had never
run, and `W-1540` read the acceptance gate and judged that one context could not
hold it. The item was then split, and this half is implementation only — no
calibration, no comparison, those are A4b.

Neither predecessor left an ordered build list. That is the thing that makes a
job like this survivable across a context boundary, so it is the first artefact
of this run rather than the last. **Everything below is derived from interfaces
that already exist in `ablcore/`, not invented here** — the arm's 8 modules
(~900 lines) are P-18's, they import cleanly, and they have simply never been
driven.

## The cut, restated from the item and `DESIGN.md`

Keep: the DSL, objectification, the replay-layer `certify` — every cheap layer.
Cut: all proof obligation — no Lean, no certificates, UNSAT believed bare,
playbook entries demoted from theorem-grade to empirical-grade. **Everything
else in the inner loop and the engine calls is unchanged to the byte**, because
the difference is only attributable if nothing else moved.

## Build order, and why this order

Each row lists what forces it to come before the next. `ablcore` is the
existing library; `→` names the module that will not run until the row is done.

| # | deliverable | blocked-on | what it unblocks |
|---|---|---|---|
| 1 | `worlds/a0_abl.py`, `worlds/a2_abl.py` | nothing | `plan_abl.run_plan(world=…)` has nothing to pass until these exist; every exhibit and the driver sit on top |
| 2 | `theory/` — the arm's own DSL copy, laws demoted | 1 (needs the world the laws describe) | `downgrade.py` and `playbook.py` have no input; they are pure text transforms with nothing to transform |
| 3 | the driver — the beats composed into a loop | 1, 2 | the arm cannot be run end to end; `DESIGN.md` §12 lists it only implicitly, which is part of why it was never written |
| 4 | `exhibits/e1_a0.py`, `e2_a2.py`, `e3_charitable.py` | 3 | E2 is the A2 false-theorem exhibit the whole A4 ticket is about |
| 5 | `tests/` | 3, 4 | three source files already **claim** these tests exist (see below) |
| 6 | `verify.sh` | all | the arm's own completion gate |
| 7 | `README.md`, `DECISIONS.md`, `RUN_STATE.md` | all | `ledger_abl.py:15` and `:59` cite `DECISIONS.md` |

`artifacts/` and `upstream_pin.json` are outputs of 6, not separate work.

## Three claims in the source that the tests must make true

`STATUS.md` recorded these as false-at-the-time and deliberately left P-18's code
uncorrected, which was right — editing it would have misrepresented what P-18
wrote. Building the tests is what makes them true, so each is a named test
rather than a line in a docstring:

| source claim | test that must exist |
|---|---|
| `_bootstrap.py:24` "`tests/test_readonly.py` … so none of the above is on the honour system" | `test_readonly.py` — hash the upstream trees around a full run via `pin.hash_tree`, assert `pin.changed()` is empty |
| `certify_abl.py:33` "`tests/test_incision.py` asserts that nothing calls it" | `test_incision.py` — assert `certify_abl.expensive` is unreachable from any beat, and that calling it raises `ObligationCut` |
| `downgrade.py:22` "`test_incision.py` asserts it again on every generated file" | same file — assert no `[status: proven]` survives in any file under `theory/` |

## The acceptance surface, mapped

`DESIGN.md` §12 sets the gate: *`verify.sh` 的断言就是 §8 的七条预注册 + §6 的
四道影子逐条数出来 + 上游树 0 改动。不绿不许收工。* Split by what A4a can
actually settle:

| gate | A4a (this item) | A4b (calibration) |
|---|---|---|
| P-1 replay accuracy byte-equal to the full arm | produce the number | compare to the full arm |
| P-2 behavioural / held-out equal | produce the number | compare |
| P-3 seven surprises become six, "proof failed" impossible by construction | **assertable here** — it is a property of `surprise.IMPOSSIBLE_WHEN_ABLATED`, not of a run | — |
| P-4 this arm is cheaper, not dearer | produce the cost line | compare |
| P-5 A0 verdict identical and correct | produce the verdict | compare |
| P-6 A2: UNSAT believed, loop does not turn, `exhibit_is_false_of_the_world` found by nobody | **assertable here** — E2 is an offline exhibit on a self-built world | — |
| P-7 the U ladder caps at U2, constructively | **assertable here** | — |
| §6 shadow 1 directed probes gone | assertable | — |
| §6 shadow 2 dependency-driven re-proof gone | assertable | — |
| §6 shadow 3 `ArenaEscape` gone | assertable | — |
| §6 shadow 4 "proof failed" gone | assertable (same as P-3) | — |
| upstream trees unchanged | assertable via `pin.hash_tree` | — |

So **A4a's `verify.sh` can be green on 4 of 7 predictions and all 4 shadows and
the read-only pin**, and must *record* the other three as numbers without
comparing them. That split is the item's own instruction — 标定与对照留给 A4b —
and writing it down here is what stops A4b from finding a verify.sh that quietly
asserted a comparison it had no second arm to make.

## Standing constraints

* **Zero API, zero network, zero dollars.** `ledger_abl.py:9` says so of the
  arm; it is also true of this build. Every world here is self-built; the sealed
  pile is not touched, read about, or named.
* **Upstream is read-only.** `cold-start-a0`, `cold-start-a2`, `theory-compiler`
  and `engine-rig` are other tracks' territory. This arm reads them and pins
  their hashes; it does not write one byte into them, and `test_readonly.py` is
  what makes that checkable rather than promised.
* **`ledger_abl.ARM` is already `"theoria"` with an `ABLATION_BLOCK`**, not the
  unregistered `"theoria_ablate"` that `STATUS.md` flagged as a cross-track
  blocker. To be re-verified against `proxy/tools/validate_ledger.py` in step 6
  before anything is claimed about it — if it holds, the blocker STATUS
  describes does not apply to the code as written, and STATUS should say so.

## Progress

* `2026-07-28T13:05Z` — worktree and branch created off `d1733df`; run directory
  and this plan written before any code, deliberately: the plan is the artefact
  the two previous attempts did not leave behind.

* `2026-07-28T13:25Z` — **step 1 done: `worlds/a0_abl.py`, `worlds/a2_abl.py`.**

  Both are selectors, not reimplementations. `A0World` and `A2World` already
  expose the exact four methods `plan_abl.run_plan` asks a world for —
  `initial` / `step` / `render` / `is_win` — so upstream objects are handed
  through unwrapped. That is a constraint rather than convenience: every line
  of adapter between the arm and the world is a place a *second* difference
  could enter, and P-1/P-2 would then be testing the adapter instead of the cut.

  One wrapper exists, in `a2_abl`, and it is the exhibit. Upstream documents
  `A2World.step_holed` as *"not a variant of the world … the referee's copy of
  what the holed manual claims"*, so it is given the world's interface as
  `HoledManualWorld`, carries `is_a_world = False`, and every method except
  `step` delegates. The two must be nameable separately and never confused,
  because confusing them is precisely the failure E2 exists to display.

  `a2_abl.disagreement()` computes the difference rather than asserting it, and
  the first run is a good sign for the exhibit:

  ```
  55 reachable states explored, 1 disagreement
  state (6,4,1) + DOWN:  world goes to (7,6,1);  manual says (6,4,1)
  ```

  **Exactly one transition** out of the whole reachable set, and it is the
  teleport. That is the exhibit in one line: the holed manual is right about
  everything except the single rule that makes the level solvable, which is
  what makes "unsolvable" a theorem true of the manual and false of the world —
  and what makes it invisible to an arm that owes no certificate.

  A count of zero here would have meant the exhibit exhibits nothing; the
  function is written to make that loud rather than quiet.

## Handoff — where the next session picks this up

**A4a is claimed by RES-1 and is not finished.** The board lock is deliberate:
this is a resumption, not a fresh claim. A restarted RES-1 must read this file
and continue at step 2 rather than run `board.py claim`.

Done: step 1 (worlds).
Next: **step 2, `theory/`** — the arm's own DSL copy with the laws section
demoted. `downgrade.py` is a pure text transform and already asserts, in
`downgrade_text`, that no `[status: proven]` survives; it needs a source DSL to
transform, which is `cold-start-a0`'s manual, copied into `ablation-arm/theory/`
and never edited in place. Then step 3, the driver, which is the piece
`DESIGN.md` §12 lists only implicitly and which is why the arm has never run
end to end.

Nothing in this run has made an API call, opened a socket, or touched the
sealed pile, and no byte has been written into any upstream tree.

* `2026-07-28T14:10Z` — **step 2 done: `theory/`, cut rather than copied.**

  `build_theory.py` produces five files — four manuals and a playbook — from
  upstream sources through `ablcore.downgrade` / `ablcore.playbook` and nothing
  else. A builder rather than five hand-edited copies, because a hand-edited
  copy is a *claim* that only the laws section moved, and `Theoria.md:280`'s
  attributability requirement is exactly the thing this arm may not take on
  trust. `downgrade_text` asserts the byte-identity of everything outside
  `laws:` on every run, so routing every file through it turns the claim into a
  check; `--check` rebuilds in memory and diffs, so a hand-edited generated file
  is a red build.

  ```
  a0_base.dsl        <- cold-start-a0/theory/theory.dsl            2 invariants demoted, 1 theorem deleted
  a0_no_button.dsl   <- cold-start-a0/theory/theory_no_button.dsl  1 invariant  demoted, 1 theorem deleted
  a2_base.dsl        <- cold-start-a2/theory/theory.dsl            2 invariants demoted, 1 theorem deleted
  a2_holed.dsl       <- cold-start-a2/theory/theory_holed.dsl      2 invariants demoted, 1 theorem deleted
  a0_playbook.dsl    <- cold-start-a0/theory/playbook.dsl          2 entries demoted (1 soundness-bearing)
  ```

  **The cut is checked in the parser, not in a grep.** A grep says the text no
  longer contains `[status: proven]`; the file the arm actually runs on is the
  AST. `verify_ast()` reads all four manuals back through the real
  `parse_theory` + `parse_semantics` and asserts **0 theorems** and every
  invariant `empirical`:

  ```
  a0_base.dsl        invariants=2 ['empirical']  theorems=0
  a0_no_button.dsl   invariants=1 ['empirical']  theorems=0
  a2_base.dsl        invariants=2 ['empirical']  theorems=0
  a2_holed.dsl       invariants=2 ['empirical']  theorems=0
  ```

  It also settles, at the earliest possible point, something step 3 depends on
  absolutely: `compile_ablated` calls `parse_semantics`, which **raises if the
  manual does not declare semantics**, and all four of these do. That failure is
  not hypothetical — the V4 run found `a0-spike`'s v0.1 manual refused by the
  v0.2 grammar for precisely that reason. Had one of these been v0.1, it would
  have blown up inside the driver in step 3, three steps from its cause.

  **Both failure modes were watched refusing**, because a check nobody has seen
  fail is a check nobody has tested: appending one comment line to a generated
  file turns `--check` red on the byte diff, and putting a single
  `[status: proven]` back turns it red on **both** the byte diff *and* the
  parser independently. The AST check is not decoration over the grep.

  Byte-reproducible: rebuilt under `PYTHONHASHSEED` 7 and 99, zero files
  changed. `ablation-arm/.gitattributes` pins LF, because `core.autocrlf` on a
  fresh clone would otherwise make `--check` fail *and report the failure as a
  hand-edit* — the one thing it exists to catch, for the one reason that is not
  it.

  ### What the four deleted theorems are, and why the list is the exhibit

  | manual | theorem deleted |
  |---|---|
  | `a0_base` | `press_is_direction_free` |
  | `a0_no_button` | **`unsolvable_no_button`** |
  | `a2_base` | `teleport_is_colour_triggered` |
  | `a2_holed` | **`right_room_locked`** |

  The two in bold are E1 and E2, and losing them together is the whole point.
  `unsolvable_no_button` is a **true** impossibility claim about a world that
  really is unsolvable; `right_room_locked` is a **false** one, true of a manual
  missing the teleport rule and false of the world. After the cut the arm cannot
  state either, and what is left in both cases is the same sentence: *the
  planner returned UNSAT and nobody owes a certificate.* An arm that cannot tell
  those two apart is precisely what P-6 predicts, and the prediction now has its
  material standing ready rather than being an argument on paper.

  One observation recorded without interpretation, for A4b: the name
  `right_room_locked` appears as a demoted **invariant** in `a0_no_button` and
  as a deleted **theorem** in `a2_holed`. Whether the two are the same claim at
  different grades is a question for whoever calibrates, not for the builder.

  The soundness-bearing demotion is the one `ablcore/playbook.py` warned about:
  `prune w_room(Cart) > 0 and no_button => dead`, whose proof was what licensed
  the planner to discard those nodes. Demoted, it can prune a branch holding a
  real solution and nothing in this arm would notice.

Next: **step 3, the driver.** `compile_ablated(dsl_path, trace_path,
problem_name, out_dir)` needs a **trace**, which is the first thing in this
build that is not already sitting upstream in finished form — the explorers
(`cold-start-a0/world/explorer.py`, `cold-start-a2/a2world/explorer.py`) produce
them, and whether to re-explore or read an existing artefact is step 3's first
decision. Everything else the driver needs now exists.

* `2026-07-28T15:05Z` — **step 3 done: `run_arm.py`. The arm has now run end to
  end, which it never had before.**

  ```
  a0-base        SAT    verdict=solvable    surprises=0  loop_turns=False
  a0-no-button   UNSAT  verdict=unsolvable  surprises=0  loop_turns=False  [E1]
  a2-base        SAT    verdict=solvable    surprises=0  loop_turns=False
  a2-holed       UNSAT  verdict=unsolvable  surprises=0  loop_turns=False  [E2]
       sweep (raw_trace.jsonl, off the bus): green=False anomalies=44
  E1 (true impossibility) vs E2 (false one): 10/10 decision fields identical
  surprise kinds: 7 in the taxonomy, 6 available to this arm
  P-1 pre-registered counts hold: True
  upstream trees unchanged: True (386 files hashed)
  ```

  ### The loop is not a step table with the repair beats deleted

  `DESIGN.md` §7.2 is the sentence this file had to obey: 不能把
  refute/locate/probe/repair 从步骤表里删掉,然后报告「消融臂修不好」. So the
  driver has all six beats including `theorize`, and the schedule is one line —
  `if bus.turns_the_loop()` — which is `Theoria.md:233` verbatim and identical
  in both arms. Whether the loop turns is then decided by *what can reach the
  bus*, and that is decided by the incision. It is derived, not arranged.

  Theorize is reached when the bus says so and records **that a turn is owed and
  what owes it**, then stops: theorize is the LLM's beat and this arm is offline
  by construction. Recording the debt is honest; inventing the turn would not be.

  ### The result the ticket asks for

  E1 is a **true** impossibility (A0 with no Button really is unsolvable). E2 is
  a **false** one (the holed manual's world is solvable in 18 moves). The driver
  computes the comparison rather than leaving it to a reader:

  | field | E1 `a0-no-button` | E2 `a2-holed` | |
  |---|---|---|---|
  | verdict | unsolvable | unsolvable | same |
  | settled / settled_by | True / search | True / search | same |
  | certificate_owed | False | False | same |
  | directed_probes_scheduled | 0 | 0 | same |
  | distinguishes_proof_from_exhaustion | False | False | same |
  | cheap layer green | True | True | same |
  | surprises on the bus | 0 | 0 | same |
  | loop turns / theorize owed | False / False | False / False | same |

  **10 of 10 decision-carrying fields identical.** One of those two verdicts is
  true and the other is false, and nothing this arm records tells them apart.
  Not because of a bug — the fields match precisely because the cut removed the
  only machinery whose output would have differed: the certificate obligation
  and the directed probes it schedules. That is P-6, and it is the ticket's
  question answered with a table instead of an argument.

  ### The driver's first run was wrong, and what caught it

  On its first run `a2-holed` came back with **3 surprises and a turning loop**,
  which reads as P-6 falsified. It was not. I had pointed the holed manual at
  `raw_trace.jsonl` — the right rule applied to the wrong artefact.
  `cold-start-a2/artifacts/exhibit_report.json` names the holed manual's
  evidence as **`history_trace.jsonl`**, and records both readings itself:

  * `certify_cheap` on the evidence: **green**, 184 frames, 14904 pixels;
  * `certify_cheap_vs_full_sweep`: **red**, 44 anomalies, first at t=184 cell
    (6,4) — with upstream's own reading, that the hole is invisible to the
    evidence its theorizer had, which is exactly Theoria §1.3's claim and
    exactly its limit.

  My run had reproduced the **sweep**, not the evidence. `trace_summary.json`
  states the cut rule — `history_trace = raw_trace[0 .. portal_transition]`,
  omitting **exactly one** pair, `cart=(6,4) pressed=1 act=DOWN` — the same
  single disagreement `a2_abl.disagreement()` computed in step 1, arrived at
  from the other side.

  Three things changed as a result, and the third is the one that matters:

  1. `a2-holed`'s evidence is now `history_trace.jsonl`;
  2. the fuller record is kept as a **sweep**: run, reported, and explicitly
     **off the bus**, because a surprise the arm could not have had is not a
     surprise — putting it on the bus would turn the loop on the referee's
     knowledge and destroy the exhibit. Its 44 anomalies match upstream's 44
     through a different code path, which is an independent reproduction rather
     than a copied number;
  3. **P-1's pre-registered counts are now asserted at run time.** `DESIGN.md`
     §8 does not state P-1 as "accuracy is equal", it states the counts — A0
     base 22356 pixels 0 anomalies, A2 holed 14904 pixels 0 anomalies. Those
     counts are a fingerprint of **which record was replayed**, so checking them
     catches exactly this mistake. All three worlds that state a number hit it
     (22356 / 20088 / 14904), and a wrong trace now turns the run red instead of
     producing a plausible finding.

  The general lesson, recorded because it will recur: *read the artefact the
  full arm read* is not a rule a driver can follow by itself. Which artefact
  that is has to be read out of upstream's own report, per manual.

  ### Determinism, and the one exemption

  `run_arm.py --twice` runs everything into two roots and compares: **30 files,
  deterministic: True.** Two things are handled rather than ignored:

  * the **ledger is compared modulo `ts`** — `proxy.ledger` stamps every record
    with a wall clock, which is right in a record of an event. Verified that
    `ts` is the *only* differing field, not assumed;
  * the **output root is normalised**, because the two runs are handed different
    roots and a report that faithfully records where it wrote is right to
    differ. Comparing raw bytes there would be calling a difference in the
    inputs a defect in the outputs.

  `__pycache__` is excluded (bytecode for the generated `theory.py`, embeds a
  source mtime) and gitignored.

  ### A cross-track blocker retired with evidence

  `STATUS.md` records `theoria_ablate` as a blocker needing the proxy track:
  `RunLedger(arm="theoria_ablate")` constructs silently and then fails
  `validate_ledger` on every line. **It does not apply to the code as written.**
  `ledger_abl.ARM` is `theoria` with an `ABLATION_BLOCK` carrying
  `requested_arm_name`, and both episodes validate:

  ```
  ablation-arm/artifacts/a0-base/episode.jsonl: PASS (15 records, 0 problem(s))
  ablation-arm/artifacts/a2-base/episode.jsonl: PASS (21 records, 0 problem(s))
  ```

  The two UNSAT worlds have no episode, and the report says so with a reason
  rather than omitting the key. STATUS.md is to be corrected in step 7.

Next: **step 4, the exhibits.** E1 and E2 now have their runs and their
comparison; `exhibits/e1_a0.py` and `e2_a2.py` are the modules that present
them, and `e3_charitable.py` is the one with real work left — it needs
`compile_ablated(addressable=False)`, the encoding-defect branch, which the
driver already exposes as a per-world flag but no world uses yet.

* `2026-07-28T16:20Z` — **step 4 done: `exhibits/`. Two hold, and the third is a
  pre-registered falsifier rather than a missing deliverable.**

  ```
  E1   holds=True   (i) small-space unsolvable -- exhaustive search is feasible
  E2   holds=True   (iii) the specificity failure -- unsolvable on a solvable level
  E3   holds=False  the adversarial-review control, not a verdict class
  ```

  ### E1 — 判决相同,理由蒸发

  | | |
  |---|---|
  | this arm's verdict | `unsolvable`, settled_by `search`, and **correct** |
  | the full arm's reason | `[{"axioms": [], "name": "unsolvable"}]` — an `#print axioms` report with an empty axiom list |
  | this arm's reason | `certificate: None`, `certificate_owed: False`, `directed_probes: 0` |

  Measured at the verdict the two arms are indistinguishable, which is the half
  of the testimony that makes the other half readable: **an evaluation that
  scores answers would report this ablation as having cost nothing.**

  ### E2 — 照信不误, plus the charity control

  Green over 184/184 frames of its own evidence, planner UNSAT, world solvable
  in 18, bus empty, loop still. And the control that answers the review's first
  punch — 你没给它反例,当然它修不好:

  ```
  charity control: given the world's solved episode for free,
                   culprits = ['mispredicted_step'], exactly 1 step diff,
                   upstream_unchanged = True
  ```

  **The ablated arm localises correctly when it is handed the counterexample.**
  That is recorded inside E2, the exhibit it threatens, because it sharpens the
  finding rather than weakening it: the ablation did not remove the ability to
  repair, it removed the thing that *produces* the counterexample. The repair
  machinery is intact and idle, and idle for a reason derived from the incision.

  ### E3 — the designed construction no longer exists, and the module says so

  §E3's recipe was: complete manual + `pddl_addressable(enabled=False)` → UNSAT
  → hand it the solution path → three checks green, empty culprit set. Five
  measurements, all performed by the module rather than quoted from a session:

  | | |
  |---|---|
  | **M1** | `enabled=False` and `enabled=True` emit **byte-identical** `problem.pddl` and `domain.pddl` |
  | **M2** | why: the generator names **38** cell objects where the derived arena holds **37**, and `c7-4` is grounded with the patch off. D-A2-006's gap was closed upstream; `compile_abl.pddl_addressable` is dead code on this input |
  | **M3** | so the complete manual plans **SAT** either way, `teleport-down` in the plan. The construction cannot start |
  | **M4** | the nearest live UNSAT on a manual with nothing wrong with it — complete manual, *truncated* evidence: cheap green over 184 frames, planner UNSAT — but its `theory.py` **raises** a missing-landmark `KeyError` on the witness path, because the landmark is derived from evidence that stops before that cell is seen. `locate` cannot return a culprit set at all |
  | **M5** | the empty culprit set does exist — complete manual, full evidence: zero culprits, zero step diffs — but that manual plans SAT, so there is no false impossibility for the empty set to be empty *about* |

  E3 needs the **conjunction** (UNSAT ∧ locate all-green ∧ a claim that is
  false). M3/M4/M5 are the three ways it comes apart here, and no two can be
  brought together on this repository's material.

  `DESIGN.md` §10 item 3 pre-registered 三查没有全绿 as a falsifier requiring
  §9's argument to be withdrawn. What is refuted is narrower and more specific:
  **not the reading of D-A2-006 but its continued existence.** The point E3
  defended survives, measured in E2's charity control. What is genuinely lost is
  E3's other half — a clean demonstration that a planner's UNSAT can be a fact
  about the encoding rather than the world, which is what makes
  `Theoria.md:43`'s three-way non-exhaustive without a proof. M4 is weaker
  evidence for it (a reader can fairly say the fault is the truncated evidence,
  not the encoding) and is recorded as a gap for A4b.

  `run_exhibits.py` exits **0 even when an exhibit does not hold**: a falsifier
  that turns the build red is a falsifier nobody will ever report. The status
  code is for a broken run, not for a finding that goes against the design.

  ### Housekeeping this step turned up

  * `a2-charitable` is on the driver as E3's **material** and carries **no
    exhibit tag** — the planner returns SAT there, and a world tagged E3 in a
    report that says SAT would read as an exhibit that passed.
  * the determinism harness had a second path-shape bug: `certify.replay`
    records its theory path relative to the **current working directory**, so
    which spelling appears depends on where the run was launched. Now normalised
    on the two-component tail, and checked from both `ablation-arm/` and the
    repo root: **38 files, deterministic from either.**
  * three ledgers now, all `PASS (0 problems)` under `proxy validate_ledger`.

Next: **step 5, `tests/`.** The three source claims in `_bootstrap.py:24`,
`certify_abl.py:33` and `downgrade.py:22` name tests that do not exist; the
material for all three is now on disk, and `pin.hash_tree` has been running
either side of every command in this run, so `test_readonly.py` is writing down
a check that has already been passing rather than inventing one.

* `2026-07-28T17:15Z` — **step 5 done: `tests/`. 45 passed in 3.8s.**

  Five files. Two of them exist because P-18's source names them, and `STATUS.md`
  recorded both sentences as false-at-the-time while deliberately leaving the
  source uncorrected. They are true now.

  | file | tests | what it settles |
  |---|---|---|
  | `test_readonly.py` | 5 | `_bootstrap.py:24` — the upstream trees, hashed around a *full* run |
  | `test_incision.py` | 13 | `certify_abl.py:33` and `downgrade.py:22` — the cut, at every place the source claims it is asserted |
  | `test_loop.py` | 11 | the schedule is the bus predicate, and P-6 |
  | `test_exhibits.py` | 10 | E1, E2, and the falsifier E3 |
  | `test_build_and_determinism.py` | 6 | generated files stay generated; two runs stay one run |

  ### A blind spot in the read-only pin, found while writing the test for it

  `pin.SKIP_DIRS` excludes `artifacts/` and `runs/`, and P-18's reason is sound
  as far as it goes — they are the other tracks' own outputs and hashing them
  would make the pin noisy. But it is a blind spot **exactly where this arm's
  newest code reaches**: `e2_a2.charity_control` and `e3_charitable` call into
  `cold-start-a2/a2pipeline`, whose `main()` functions write into
  `cold-start-a2/artifacts/`. Only `locate()` is called and only `locate()`
  reads — but *only reads* is a claim that is cheap to check and expensive to be
  wrong about, so `test_readonly.py` now hashes those two directories itself, by
  name, around the full run. Clean.

  The pin is also shown **firing**, against a doctored `before` rather than a
  real edit: proving the alarm works by writing into another track's tree would
  be committing the offence to test the alarm.

  ### `nothing calls it` is parsed, not grepped

  `certify_abl.py:33` claims nothing calls the expensive layer. The test walks
  every `ast.Call` in the arm's own sources rather than grepping for
  `expensive(` — a grep misses `getattr(certify_abl, "expensive")()` and trips
  over the word in a docstring. Result: no caller, and `expensive()` still
  raises `ObligationCut` when called directly.

  ### Both of `downgrade.py:22`'s halves, separated

  The in-function assertion checks the transform **as it runs**, on whatever
  text it is handed. The test checks **the files that shipped** — a different
  claim, and the one a reader of `theory/` actually depends on. Both are here,
  and the in-function one is watched refusing on a manual whose `laws:` section
  is last, which is where a section-boundary bug would run past the end.

  ### The tests that assert a negative result

  `test_exhibits.py` asserts E3 is **not** constructible, with its five
  measurements. That reads oddly until you consider the alternative: a test that
  skipped E3, or asserted `holds is True` and got deleted when it failed, would
  leave the repository with no record that a designed exhibit had expired. If
  someone later restores the mechanism, the test fails — and the assertion
  message says to rebuild E3 and rewrite the test rather than relax it.

  Same shape in `test_loop.py`: the comparator is fed a doctored report to prove
  it can say `different`, and the driver's source is checked for an
  `"owed": True` branch — because a driver with no such branch would produce an
  empty bus in every run and prove nothing about the incision.

  ### One defect the suite found in itself

  `test_the_comparison_would_report_a_difference_if_there_were_one` called
  `run_all` with a **three-world subset**, which overwrote the checked-in
  five-world `artifacts/run_all.json`. A test suite that quietly downgrades the
  deliverable it is testing is worse than no suite. `run_all` now takes
  `write=False` for subset callers, with the reason in its docstring, and after
  a full `pytest` run the only modified artefacts are the three ledgers —
  differing in `ts`, which is the documented exemption.

Next: **step 6, `verify.sh`** — the arm's own completion gate, and the place
`BUILD_PLAN`'s acceptance table has to be honoured: A4a's gate may assert 4 of
the 7 pre-registered predictions plus all four shadows plus the read-only pin,
and must *record* P-1/P-2/P-4 as numbers without comparing them, because the
comparison needs a second arm and that is A4b.

* `2026-07-28T18:10Z` — **step 6 done: `verify.sh`. GREEN.** 56 tests, five
  stages, ten assertions, five recorded numbers.

  ```
  == the gate: what A4a asserts
    P-3  ok   P-5(correct)  ok   P-6  ok   P-7  ok
    shadow-1 ok  shadow-2 ok  shadow-3 ok  shadow-4 ok
    read-only ok   P-1(counts) ok
  == recorded for A4b -- NOT asserted, and cannot turn this red
    P-1  P-2  P-4  P-5(identical)  E3
  == stages
    build_theory --check | pytest | run_arm | run_arm --twice | run_exhibits
  ```

  ### A correction to this plan's own acceptance table

  The table above under *The acceptance surface, mapped* says A4a's gate can be
  green on **4 of 7** predictions. That count was loose. P-5 is one prediction
  with two halves — *identical to the full arm* **and** *correct* — and only the
  correctness half is settleable without a second arm. The gate therefore
  asserts **three and a half of seven**, and it names the halves separately
  (`P-5(correct)` asserted, `P-5(identical)` recorded) rather than rounding.
  Corrected here by appending rather than by editing the earlier table, so a
  reader who saw the first version can see what changed.

  ### P-7 stopped being a claim and became a measurement

  The U ladder is assembled from numbers the run already produced:

  | rung | state | evidence |
  |---|---|---|
  | U1 对上过去了吗 | **attained** | cheap replay green on all five worlds |
  | U2 说得清吗 | **attained** | every manual parses; 3 of 4 forms emitted |
  | U3 证得动吗 | **unreachable by construction** | 0 certificates owed, expensive layer omitted and raising, 0 theorems survive the cut |
  | U4 修得好吗 | **unreachable by consequence** | 0 loops turned, 0 directed probes scheduled |

  U4's row is the one worth reading twice. It is out of reach **not because
  repair is broken** — E2's charity control localises correctly when handed a
  counterexample — but because the refutation never arrives. That distinction is
  the whole of E2, and P-7 now carries it.

  ### The gate was watched refusing, and it had two defects when it did

  A gate nobody has seen refuse is a gate nobody has tested, so `run_all.json`
  was doctored — `available` kinds back to 7, a certificate marked owed — and
  the gate went red on exactly `P-3`, `P-7`, `shadow-1`, `shadow-4`, exit 1.
  Two real defects surfaced on the way:

  1. **The first version read a missing field as a failure.** `plan_abl` writes
     `certificate_owed` and `directed_probes_scheduled` only on the UNSAT
     branch, because a SAT plan has no impossibility claim to certify — the
     witness *is* the answer. The fields are **absent** on a SAT world, not
     zero. The repair was deliberately *not* to default them to 0: a gate that
     defaults a missing field to the value it wants would pass a run in which
     the field had silently vanished. It now asks the question only of the
     worlds where it arises, and treats absence on an UNSAT world as a failure.
  2. **The gate crashed while building the evidence for a red claim** —
     `KeyError` on the same missing field — which would have lost the report and
     every other claim in it. A gate that cannot explain why it refused is
     barely better than one that never does.

  ### The footgun that fired twice, closed at the source

  Step 5 recorded one test overwriting the checked-in five-world
  `run_all.json` with a three-world subset. Running the full suite turned up a
  **second** one, in a different file, which broke `test_verify` outright.
  Two occurrences in two files settles it: a rule every caller has to remember
  is a rule that gets forgotten. `run_all` now writes **only when every world
  ran**, decided by itself, with `write=True` available to override
  deliberately, `is_full_run` recorded in the payload, and a test that pins the
  behaviour because the default is invisible at every call site relying on it.

  ### The cross-track blocker, retired with evidence

  `STATUS.md` records `theoria_ablate` as needing the proxy track. Re-checked
  here as this plan said it would be:

  ```
  proxy.ledger.ARMS      = [bare_cc, mock_arm, probe, replay, schema_repro, theoria]
  ledger_abl.ARM         = 'theoria'          -> in ARMS: True
  requested_arm_name     = 'theoria_ablate'   -> in ARMS: False, and nothing uses it
                                                 as the arm field; it is metadata
                                                 inside the ablation block
  three episodes         -> PASS (0 problems) each
  ```

  The blocker is real about the *name* and does not apply to the *code as
  written*. STATUS.md says otherwise and is corrected in step 7.

Next: **step 7, the documents** — `README.md`, `DECISIONS.md`, `RUN_STATE.md`,
and the STATUS.md corrections this run has accumulated: three source claims that
are now true, one blocker that does not apply, and one exhibit that expired.
