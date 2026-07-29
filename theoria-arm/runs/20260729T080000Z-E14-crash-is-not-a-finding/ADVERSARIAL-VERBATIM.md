# ADVERSARIAL REVIEW — verbatim

Stored verbatim, not paraphrased, per the work order. The reviewing subagent
reported its findings as text rather than writing into this tree; what follows
is its final message, unedited, including the parts that refute me. Its
preamble line ("Restored the tree and re-ran both suites clean.") is kept.

---

Restored the tree and re-ran both suites clean. Here is the review.

---

# Adversarial review — E14 `crash-is-not-a-finding`

Worktree `C:\Users\user\Desktop\theoria\.worktrees\e14-crash-is-not-a-finding\`, branch `agent/e14-crash-is-not-a-finding`, base `bcea980`. Zero API calls, zero network. Everything below is `pytest`, direct calls into `inner/` and `pipeline/`, and `git show`.

Baseline confirmed first:

```
$ cd theoria-arm && python -m pytest -q     ->  56 passed
$ cd a0-spike   && python -m pytest -q      ->  48 passed
```

---

## (a) Is the crash count actually blocking the field?

### VERDICT: **REFUTED**

I constructed four crash shapes the implementer did not: a *partial* crash (one action only), a crash on a path exiting via **`sat`**, crashes raised from `nxt.key()` / `is_goal(nxt)` rather than `step`, and a `BaseException`. Script: `scratchpad/attack_a.py`, `scratchpad/attack_sat.py`, `scratchpad/attack_a0.py`.

**What held.** A partial crash goes red correctly, and the gate survives the trip up to the caller:

```
A1  partial crash (one action only), queue drains
raised=1 status=unsat_unsound exhaustive=False crashes=1

A5  certify._ambiguity, crash on SOME pairs only
raised=1 ok=False crashes=1 pairs 0/1

A7  does the gate survive to cheap()'s report['ok'] ?
cheap ok = False
unambiguous ok = False crashes = 1
```

`armtools/timeline.py:190` reads `checks["unambiguous"]["ok"]` through `_tick()`, so a crashed constraint-9 prints `**FAIL**`, not a tick. And `run_a0.main()` really does return 1 — I verified it end-to-end rather than by grep (their test only greps the source):

```
=== 1. run_a0.main() with a crashing synthesize ===
synthesize calls = 12
run_a0.main() EXIT CODE = 1
mine.all_guards_searched = False
mine.synthesis_crashes   = 12
```

Crashes from `nxt.key()`, from `is_goal(nxt)`, and `BaseException` out of `step` all **propagate** rather than being swallowed — loud, so no laundering. I attacked this and found nothing:

```
A3  PROPAGATED out of _tier_bfs: RuntimeError: injected: key() fell over
A3  is_goal PROPAGATED: RuntimeError: injected: is_goal fell over
A4  PROPAGATED: KeyboardInterrupt: SELECTIVE injected crash on ('key', 1)
```

### REFUTATION 1 — the `sat` exit path publishes a **false zero**

`plan.py:214` sets `entry["step_crashes"] = crashes.as_json()` **before** the search. `as_json()` returns a fresh dict, i.e. a snapshot at count 0. It is refreshed on the timeout return (`:244`) and on the drain return (`:275`) — but **not** on the `ok: True` return at `:265-268`. So a search that crashes and then finds the goal reports zero crashes.

```
$ cd theoria-arm && python .../scratchpad/attack_sat.py

--- _tier_bfs entry -------------------------------------------------
ok            = True
actions       = [['key', 2], ['key', 2]]
raised (real) = 2
REPORTED COUNT= 0

--- plan() top level ------------------------------------------------
status        = sat
optimal       = True
plan          = [['key', 2], ['key', 2]]
raised (real) = 2
step_crashes.count REPORTED = 0

VERDICT: false zero on the sat path -> True

--- optimality laundered --------------------------------------------
length found  = 3  optimal claimed = True
crashes really= 6  crashes reported = 0
```

This is the ticket's own disease, intact, at the site the ticket named. Three things are wrong at once:

1. `optimal: True` (`plan.py:150-151`) **is** an exhaustiveness claim — BFS length-optimality holds only if no successor was dropped. Six successors were dropped without adjudication and the field is `True`. In the second case the crashing action was deliberately the *shortcut*: BFS reports length 3 and `optimal: True` when a 2-step route existed and was pruned.
2. The crash count printed beside it is **0**. The implementer's own docstring (`plan.py:74-76`) says "a zero that is printed is evidence, a zero that is absent is indistinguishable from a report that never looked." A printed zero that is false is worse than either.
3. The stale snapshot is copied verbatim into the top-level report by `plan.py:145-147`, so the laundering reaches the caller.

Deliverable (1) — "any field claiming exhaustiveness/coverage/no-violation must appear beside the crash count and must be false when the count is non-zero" — fails here.

### REFUTATION 2 — `adapt.repair()` counts and then ignores

The implementer changed `a0-spike/pipeline/adapt.py` for this ticket, adding `synthesis_crashes` and `all_guards_searched` next to the claims. They did not make the claims false:

```
=== 2. adapt.repair() with a crashing synthesize ===
variant             = push1
synthesis_crashes   = 12
all_guards_searched = False
replay_exact        = True     <-- coverage claim
exactly_one_successor = True   <-- no-violation claim
n_rules             = 16
```

`adapt.main()` (`adapt.py:242-273`) `return 0` unconditionally, and its printed verdict table has no crash column at all. `a0-spike/artifacts/adaptation.json` is a committed artifact carrying four such rows. Same for `a0_report.json` under a crashed miner:

```
certify.replay_exact           = True
certify.exactly_one_successor  = True
certify_generated.replay_exact = True
held_out.exact                 = True
levels[*].theorem.unsolvable   = {'match': False, 'mismatch': True}
```

`run_a0.main`'s exit code is gated, so the *run* is red — but every field in the artifact stays green, including a literal `unsolvable: true`.

### REFUTATION 3 — `pairs_checked` can exceed `pairs_nominal`, with crash count 0

`certify.py:238` is `ambiguous = namespace.get("AmbiguousTransition", Exception)`. When that key is absent, `except ambiguous` becomes `except Exception` and every crash is filed as a constraint-9 **clash** instead of a crash:

```
A6  certify._ambiguity when the namespace lacks AmbiguousTransition
raised=1 ok=False crash_count=0 n_clashes=1 pairs 2/1
detail: 1 ambiguous transitions found
```

`pairs_checked: 2` of `pairs_nominal: 1` — 200% coverage — with `step_crashes.count: 0` on a run that crashed. `ok` still goes False, so it is not a full whitewash, but both instrumented fields lie and the crash is reported as a *finding about the world* (an ambiguity). Today `gen_python` always emits `AmbiguousTransition`, so this is latent — but the `.get(..., Exception)` default exists precisely for the branch where it is not there.

### Also live, disclosed but unfixed

`certify.py:166-168` writes `unambiguous = {"ok": True, "scope": "not_attempted"}` when the initial state will not render, and `timeline.py:190` prints that as **constraint 9 PASS**. The implementer names this in "Left undone". It is a `no-violation: true` field with no crash count anywhere near it, in the same check, in the same file, printed as a tick to a human. Naming it is not fixing it.

---

## (b) Is the negative sample constructionally guaranteed to go red?

### VERDICT: **PARTIALLY REFUTED** (the tests are load-bearing; one ablation is mis-caveated and one test is decorative)

I did not take the tests' word for it. I backed up the three sources (sha256 verified against `MANIFEST.json`: `f91fb4f0…`, `90df5770…`, `1a99d74c…`), reverted **only the gate** in each, ran the new tests, then restored and re-verified the hashes.

```
plan.py     :  "if crashes.count:"                 -> "if False:  # REVERTED GATE"
certify.py  :  "if crashes.count:"                 -> "if False:  # REVERTED GATE"
stages.py   :  all_guards_searched -> return True ; unsound_after_crash -> return False
```

```
$ cd theoria-arm && python -m pytest -q -k "crash or crashing or unpoisoned or constraint_9"
FAILED tests/test_arm.py::test_a_crashing_step_turns_the_planner_red_not_clean
FAILED tests/test_arm.py::test_a_crashing_step_cannot_certify_constraint_9
    >       assert report["ok"] is False
    E       assert True is False

$ cd a0-spike && python -m pytest -q -k "crash or finding or green_light"
FAILED tests/test_a0.py::test_a_crashing_synthesis_is_not_a_finding
    >       assert account.all_guards_searched is False
    E       assert True is False
```

Restored:

```
theoria-arm/inner/plan.py f91fb4f05395076b OK
theoria-arm/inner/certify.py 90df577072b380ba OK
a0-spike/pipeline/stages.py 1a99d74cf759edbf OK
```

So the three substantive tests genuinely fail on un-fixed code. And the poisoned runs are not red for an unrelated reason — A1 above shows a *partial* crash (2 of 3 states still enumerated, queue still drains through a live successor) also goes `unsat_unsound`. The redness tracks the crash count, not an empty state set or an early-exit branch.

**What broke.**

1. **`test_the_green_light_reads_the_crash_count` is worthless as written.** It greps `inspect.getsource(run_a0.main)` for a substring. Under my reversion — `all_guards_searched` hardcoded to `True`, gate semantically dead — that test **still passed**. The property does hold (I verified exit code 1 empirically above), but their test does not check it.

2. **The certify ablation has exactly the residual-mechanism problem they caveated only for a0.** From their own `raw/negative_sample.json`, `certify.counting_removed`:

   ```
   "ok": true, "pairs_checked": 0, "pairs_nominal": 1,
   "detail": "no (state, action) among 1 x 1 admitted two rules, and all 1 pairs were adjudicated -- no call to `step` raised"
   ```

   `pairs_checked: 0` vs `pairs_nominal: 1` is a complete second detector (`pairs_checked` increments only on a non-raise, so `pairs_checked < pairs_nominal` <=> a crash occurred), and it survives the ablation. Pre-E14 `_ambiguity` had **neither** field:

   ```
   $ git show HEAD:theoria-arm/inner/certify.py | sed -n '/def _ambiguity/,/^def expensive/p'
   ...
       return {
           "ok": not clashes, "scope": "sampled", "states": len(states),
           "actions": len(actions), "clashes": clashes[:12],
           "detail": ("no (state, action) among %d x %d admitted two rules" ...
   ```

   So the certify "counting removed" column is an ablation of the *gate*, not a reproduction of the pre-E14 code — the same caveat REPORT.md gives for a0 and explicitly withholds from certify. (Note also that the `detail` sentence says "all 1 pairs were adjudicated" while `pairs_checked` is 0, because that string is built from `pairs_nominal`, not `pairs_checked`.)

3. **The plan.py ablation is honest** — I checked. `git show HEAD:theoria-arm/inner/plan.py` shows pre-E14 emitted `status/expansions/reachable_states/detail` with the same "the whole reachable set (%d states) was enumerated" sentence and no crash-sensitive field. The ablated output adds only `exhaustive: True` (which is the wrongness being demonstrated) and `search_ceiling` (not a detector). No complaint here.

---

## (c) Is the reconciliation number (0) read in the implementer's favour?

### VERDICT: **PARTIALLY REFUTED**

**What held, and I genuinely attacked it.** The certify re-run *is* a faithful reproduction. Committed vs re-run, both from `raw/theoria-arm-recertify.json` and `runs/20260728T015354Z-g50t-first-contact/certify_reconstructed.json`:

```
COMMITTED: {"actions": 1, "clashes": [], "ok": true, "states": 8,
            "detail": "no (state, action) among 8 x 1 admitted two rules"}
RERUN    : {"actions": 1, "ok": true, "states": 8, "states_reconstructed": 8,
            "pairs_checked": 8, "pairs_nominal": 8, "replay_truncated_by_crash": false}
```

Same 8 states, same 8x1, and the replay `first_divergence` cells are byte-identical between the two files. That zero is real for this instance.

**Corpus depth: I looked where they were told to look, and their sweep was complete on the arm side.** The other archived runs carry no certify/plan report — `20260728T012311Z-*` and `20260728T014402Z-*` have only ledgers plus a `SALVAGE.json` whose keys are `card_ids/env_steps/records/trace/...`; `20260728T015354Z`'s `SALVAGE.json.recertify` is `{"cheap_green": false, "compile_ok": true, "plan_status": "no_goal_declared", "proof_layer_available": false}` — no unambiguous detail and, again, no `unsat`. `grep -rln "unambiguous|reachable set|all_guards|replay_exact|exactly_one_successor" ablation-arm/ baseline-arms/` returns one BUILD_PLAN.md prose hit and nothing else. So "1 run deep" is the honest state of the corpus, not laziness, and they say so.

**They also do not conflate "no crash recorded" with "no crash happened"** — REPORT.md lines 34-38 and `reconciliation.json.reading` both draw that line explicitly and correctly. Credit where due.

Now the failures.

### REFUTATION 1 — the report contradicts its own machine artifact

REPORT.md's headline table, row 1:

> `ok: true`, crashes **0**, **1/1 pairs adjudicated**

`raw/reconciliation.json` for the same finding:

```json
"rerun_pairs_checked": 8, "rerun_pairs_nominal": 8
```

It swept 8 pairs, not 1. The "1/1" appears to be copied from the negative-sample control. In a ticket whose entire thesis is that the human-readable claim drifts from what the computation did, the human-readable claim has drifted from what the computation did.

### REFUTATION 2 — the stated reason for bypassing `plan()` is factually wrong, and the bypass is what hid finding (a)

`reconcile.py:100-109` justifies calling `_tier_bfs` directly instead of the real entry point:

> "the PDDL tier answers first and answers wrongly … so `plan()` returned `sat` with an empty plan and the ladder never descended to BFS."

I ran `plan()` on that exact instance (same books, same unreachable goal):

```
GOAL: goal Cart.pos = (2, 2)
  status= unsat plan= None exhaustive= True crashes= 0
   tier: {"tier": "pddl+fd_adapter", "ok": false, "detail": "the grounded task has no plan (1 expansions)"}
   tier: {"tier": "object-state-bfs", "ok": false, "expansions": 3, "reachable_states": 3, "status": "unsat", "exhaustive": true, ...}

GOAL: goal count(Cart) = 1
  status= sat plan= [] exhaustive= None crashes= 0
   tier: {"tier": "pddl+fd_adapter", "ok": false, "detail": "TypeError: unhashable type: 'list'", "refused_by": "pddl"}
   tier: {"tier": "object-state-bfs", "ok": true, "actions": [], "expansions": 0, "detail": "already at the goal"}
```

The PDDL tier does **not** answer `sat`; it refuses correctly, the ladder **does** descend to BFS, and `plan()` returns exactly the `unsat` / `exhaustive: true` / `crashes 0` the audit wanted. The "sat with an empty plan" behaviour they describe happens on the *original* `count(Cart) = 1` goal and comes from the **BFS** tier's "already at the goal" branch, not from PDDL at all.

This is not a nitpick. Both the fourth reconciliation instance and both new plan tests call `_tier_bfs` directly, on a technicality that does not hold. The one layer they skipped — `plan()`'s aggregation at `plan.py:141-161` — is precisely where the false zero in (a) lives. The disease reappeared in the blind spot the excuse created.

### REFUTATION 3 — the denominator of 3 excludes committed claims from a site they themselves patched

`a0-spike/artifacts/adaptation.json` is a committed artifact, in an audited territory, whose four `repair` blocks each carry `exactly_one_successor: true` and `replay_exact`, produced by `stages.mine` — the exact call site under audit. The implementer edited `adapt.py` in this ticket, so the dependency was known. None of the four claims are in the denominator; `adapt.main()` was never re-run; and as shown in (a) those fields stay `true` under 12 injected crashes.

Likewise `a0-spike/artifacts/a0_report.json` contributes exactly one claim to the audit ("4 of 12 effect classes disjunctive") while the same file also publishes `certify.replay_exact`, `certify.exactly_one_successor`, `certify_generated.replay_exact`, `held_out.exact` ("39960 unobserved-inclusive states … mismatches=0") and `levels.mismatch.theorem.unsolvable: true` — all resting on the mined rule set, all of which my poisoned run leaves `true`. A denominator of 3 out of a corpus that contains at least ~9 committed coverage/no-violation claims in the two territories is chosen, not found.

The "1 NOT EXERCISED" classification is *not* the dishonest part — the archived manual genuinely declares no goal, `plan()` genuinely stops at `no_goal_declared`, and reporting it separately rather than folding it into the clean column is the right call (and cuts against them). The dishonest-by-omission part is on the a0 side.

### Observation — the re-run uses a generator that has moved since the claim was made

`plan.py`/`certify.py` compile the archived books through `theory-compiler/src/theory_compiler/generators/gen_python.py`, the *other track's* file. The committed artifact was written at `9ba0786 2026-07-28 10:45:49`; `gen_python.py` has changed twice since (`3787e2d` 19:02, `76e7560` 22:41). So the deliverable zero is "today's generator, applied to those books, does not crash" — not "the generator that produced that claim did not crash". The identical `8 x 1` string and identical divergence cells make it very likely equivalent, but the report does not say this and it is exactly the "different computation" hazard the brief asked about.

---

## Housekeeping

I dirtied `theoria-arm/inner/plan.py`, `theoria-arm/inner/certify.py`, `a0-spike/pipeline/stages.py` (gate reversion) and `a0-spike/artifacts/` (poisoned `run_a0.main()`). All restored and verified: the three sources match their `MANIFEST.json` sha256, `artifacts/` restored byte-identical (`snapshot(after) == snapshot(before) -> True`), and `git status --short` shows only the ticket's own seven modified files plus its run directory. Both suites re-run green afterwards (56 / 48). No committed artifact was modified. Scratch scripts live under the session scratchpad, not in the repo.

---

## REQUIRED CORRECTIONS

1. **`plan.py:265-268` — refresh the crash account on the `sat` return.** `entry["step_crashes"] = crashes.as_json()` must be re-emitted on every exit, not on two of four. Right now a successful plan reports `count: 0` after N real crashes. Reproduction: `scratchpad/attack_sat.py`.
2. **`plan.py:150-151` — gate `optimal`.** BFS length-optimality is an exhaustiveness claim. With `crashes.count > 0` it must be `optimal: False` plus an `error`, per the `ladder.py:74-82` shape the ticket claims to be copying. Currently `optimal: True` is emitted on a search that pruned the shorter route.
3. **`adapt.py:169-180` — gate `replay_exact` and `exactly_one_successor`**, and make `adapt.main()` return non-zero (and print the crash line) when `all_guards_searched` is false. Deliverable (1) says the field must be *false* when the count is non-zero; today it is merely *adjacent* to it.
4. **REPORT.md table row 1 — "1/1 pairs adjudicated" is wrong; the artifact says 8/8.** Fix the report or explain the notation.
5. **`reconcile.py:100-109` — the justification for calling `_tier_bfs` directly is false.** `plan()` on that instance returns `unsat` / `exhaustive: true` / crashes 0 via BFS after a correct PDDL refusal; the "sat with an empty plan" arises on a different goal and from the BFS tier. Either re-run the instance through `plan()` (which would have surfaced correction 1) or replace the stated reason with a true one.
6. **Extend the audit denominator to `adaptation.json` (4 claims) and to the remaining `a0_report.json` claims** (`certify.replay_exact`, `certify_generated.replay_exact`, `held_out.exact`, `levels[*].theorem.unsolvable`), or state explicitly and defensibly why claims produced by the audited call site are outside the audit. "3 committed claims" as currently drawn is not the population.
7. **Give the certify ablation the same caveat as the a0 one.** `pairs_checked` / `pairs_nominal` survive the `record`-removal and are a complete second detector; pre-E14 `_ambiguity` had neither. The `counting_removed` column is an ablation of the gate at *both* sites, not a byte-faithful pre-E14 reproduction at one of them.
8. **Replace `test_the_green_light_reads_the_crash_count` with a behavioural test.** It greps source and passes on semantically reverted code — verified. Assert `run_a0.main() != 0` under an injected crash (backing up `artifacts/`), or refactor the verdict into a pure function and test that.

## OPTIONAL

9. `certify.py:166-168` + `timeline.py:190`: `{"ok": True, "scope": "not_attempted"}` prints as **constraint 9 PASS**. Disclosed as out of scope, but it is a `no-violation: true` with no crash count in the same check the ticket is about. Cheapest fix: make `_tick` render `scope == "not_attempted"` as `n/a`.
10. `certify.py:238` `namespace.get("AmbiguousTransition", Exception)`: when the key is missing every crash becomes a "clash" and `pairs_checked` (2) exceeds `pairs_nominal` (1) with `count: 0`. Default to a private sentinel exception class instead of `Exception`.
11. `certify.py:256-257`: the reconstruct loop `break`s silently on `arc_action is None`, shrinking the sampled denominator with no flag (`replay_truncated_by_crash` covers only the crash case). Same shape as the disease, different cause.
12. `timeline.py` never prints the plan status, so `unsat_unsound` never reaches the human-readable artifact at all.
13. State in REPORT.md that the re-run compiles the archived books with a `gen_python.py` that has moved twice since the audited artifact was committed, and that the identical `8 x 1` detail string and divergence cells are the evidence that this did not matter.
