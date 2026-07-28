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
