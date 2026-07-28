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
