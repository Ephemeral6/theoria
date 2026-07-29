# E15-solver-status-bit — adversarial review

Reviewer: an agent with no hand in the implementation. Everything below was
**run**, not read. Commands and their output are inline.

Worktree `.worktrees/e15-solver-status-bit`. Zero network, zero API calls,
nothing written outside this run directory. `engines/`, `tests/`, `tools/` were
not modified; every mutation was applied to a scratch copy built with
`git archive HEAD` under the session scratchpad.

**A note on the moving target.** This review started at HEAD `9920447` (items
1+3) with the P2/P4/P5 deliverables untracked in the working tree. Mid-review the
implementer committed `d2b75c26`, which *changed `engines/lp_potential/potential.py`
again* (the M30 fix) and swept the results in. Every measurement below was
re-taken against `d2b75c26` after that landed, and where the two commits differ I
say so. `d2b75c26` also committed three files this review had written in flight
(`adversarial_rederive.py`, `REDERIVED.json`, `rederived.jsonl`) into the run's
`MANIFEST.json` as if they were the item's own deliverables. They are mine; the
manifest hashes verify, so nothing is corrupt, but the provenance is wrong.

Baseline, current HEAD, clean tree:

```
$ cd engine-rig && python -m pytest -p no:cacheprovider
528 passed, 27 skipped in 43.01s
EXIT=0
$ git status --porcelain
(empty)
```

**Headline: the work holds up.** (b) reproduces exactly under an independent
re-derivation, (c) reaches the emitted product and the pinned hash does not move,
(d)'s controls are constructionally red and are not satisfiable by a cheaply
broken engine. The real findings are three: a stale `MUTATION.json` that
contradicts the shipped engine, a pre-registered P5 criterion quietly re-read,
and one control tool that reports a regression as a stack trace instead of a
verdict. Details below.

---

## (a) Is the structured result branched on semantically, or is it `None` with a new name?

**Verdict: it is genuinely branched on — at four sites. Every other consumer is
correct only *by delegation*, because `run` / `solve_certificate` raise. No call
site anywhere catches `LpUnavailable` and swallows it.**

### Every reference to the entry points

```
$ grep -rn "LpUnavailable" --include=*.py .  | grep -v engine-rig/engines/lp_potential
./engine-rig/runs/.../controls/n1_iteration_limit.py:152:    except potential.LpUnavailable as exc:
./engine-rig/tests/test_solver_status_bit.py:263,301   (pytest.raises)
./engine-rig/tests/test_tool_failure_is_not_truth.py:270 (pytest.raises)
./engine-rig/tools/check_status_bit.py:156:    except lp_potential.LpUnavailable as exc:
```

Four `except`/`raises` sites, all of which then read `exc.outcome.status`. **No
site catches it and continues.** The "a call site that swallows `LpUnavailable`
is the same defect" attack finds nothing inside `engine-rig/`.

| call site | what it does | distinguishes? |
|---|---|---|
| `engine-rig/tools/run_all.py:115` | `lp_potential.run(...)`; `if certificate is None: raise RuntimeError`. No `except`. | **No** — but it cannot confuse them, because `run` raises on 1/3/4. Safe by delegation. |
| `engine-rig/tools/check_status_bit.py:104,115,155` | `decide(...)`, branches on `.status`/`.decided`/`.no_linear_pagoda` by name | **Yes** |
| `engine-rig/runs/.../census.py:141` | `decide(...)`; `row["silent"] = outcome.status != CERTIFIED` | **Yes** |
| `engine-rig/runs/.../controls/n1_iteration_limit.py` | `solve`/`run`, branches by name | **Yes** |
| `engine-rig/engines/lp_potential/__init__.py:run` | branches `NO_LINEAR_PAGODA` / `CERTIFIED` / else-raise | **Yes** (this is the fix) |
| `engine-rig/tests/test_lp_potential.py:100,108,116,363,386` | `run(...)`, `solve_certificate(...) is None` | No (tests; correct under the new contract) |
| `engine-rig/tests/test_ic3_pdr.py:37,123` | `solve_certificate(...) is/is not None` | No (same) |
| `engine-rig/tests/test_interop.py:56,65,74,83,154,176` | `solve_certificate(...)` | No (same) |
| `engine-rig/tests/test_tool_failure_is_not_truth.py:270,277` | asserts `LpUnavailable` on a stub 1, `None` on a stub 2 | **Yes** |

`interop/`, `recheck/`, `bench/`, `engines/ic3_pdr/` contain **zero** calls —
verified, not assumed:

```
$ grep -rn "solve_certificate(\|lp_potential.run(\|lp_potential.decide(\|potential.solve(" interop/ recheck/ engines/ic3_pdr/ bench/
none
```

`engines/ic3_pdr` only borrows the `lp_potential` *enum name* for its rows
(D-018); it never calls the LP.

### Outside `engine-rig/` (noted, not edited)

* **`fuzzlab/props/lp_potential.py:115` — `_solve()` → `engine.run(...)`.** Four
  invariants funnel through it. It catches `CertificateError` only. `if cert is
  None:` → `_skip_no_certificate(..., cause="no_certificate")`. Under the new
  contract that `None` is unambiguous, so the label is now *more* accurate than
  it was — but the site itself still treats every silence identically and has
  no idea a status word exists.
* **`fuzzlab/props/finding.py:98 — `run_invariants`** catches bare `Exception`
  and files it as a `raised` finding; `failures()` (line 103) counts only
  `VIOLATED`. So an `LpUnavailable` escaping a fuzz campaign is **recorded but
  does not fail the run**. This is the closest thing in the repository to a
  swallow. It is outside `engine-rig/` and outside E15's pre-registered scope
  ("nothing outside `engine-rig/` is written"), so it is not a finding against
  this item — it is the next ticket.
* `fuzzlab/mutants/lp_potential.py` patches the *seam* (`_solve`), not source
  anchors, so it is not broken by the change. Its docstring is stale on a
  different axis ("Every one of the four invariants opens with `if cert is None:
  return []`" — that was replaced by `finding.skipped` in V-13). Pre-existing.
* `worldgen/`, `verify-lab/`, `theoria-arm/`, `monitor/`, `theory-compiler/`
  mention `lp_potential` in prose or config only. No calls.

**Conclusion for (a).** Not `None` with a new name. The two-valued wrapper
survives, but it survives *narrowed*: `solve_certificate` returning `None` now
provably means status 2 and nothing else, and the widening happens through an
exception no one catches. The honest caveat is that the semantic branch lives at
four sites, three of which are this item's own instruments; the one long-standing
production consumer (`tools/run_all.py`) is protected by the raise, not by
reading the word.

---

## (b) Do the 639 reconcile bit-for-bit with E11?

**Verdict: yes. Confirmed by a fully independent re-derivation, row by row, on
all 3000 worlds. Nothing differs. I believe both sides.**

I did not trust `census.jsonl`. `adversarial_rederive.py` (in this directory)
rebuilds the LP itself with `scipy.optimize.linprog` and reads `result.status`
directly. It **does not import `engines.lp_potential` at all**, it builds the
constraint rows from `spec.triples` rather than from `graph["edges"]` (the
engine's `moves_from_graph` reads `edges`, so a shared-failure oracle was worth
ruling out), and ground truth is its own forward BFS.

```
$ cd engine-rig && python runs/20260729T044500Z-E15-solver-status-bit/adversarial_rederive.py
{
  "worlds": 3000,
  "highs_status_counts": {"0": 1550, "2": 1450},
  "goal_truly_unreachable": 2189,
  "no_certificate": 1450,
  "silent_and_truly_unreachable": 639,
  "status_2_at_bound_10": 639,
  "incompleteness_rate_pct": 29.2,
  "still_infeasible_when_widened": 638,
  "feasible_when_widened": 1,
  "n_rows_status0": 1550,
  "n_status0_exact_recheck_bad": 0,
  "triple_set_mismatch_count": 0,
  "widened_box_rows": [{"index": 2302, "seed": 17475932563032345095,
    "first": {"bound": 100, "highs_status": 0,
      "exact": {"holds": true, "inv_closed": true, "goal_break": true,
                "initial_potential": "9", "goal_gaps": ["1", "13"],
                "weights": ["12","9","3","7","-1","11","10","-4"]}}}]
}
```

Every pre-registered integer: **3000 / 2189 / 1550 / 639 / 29.2 % / 639 status-2
at `bound=10` / 638 still infeasible / 1 feasible at `bound=100`, seed
17475932563032345095, index 2302, weights `[12,9,3,7,-1,11,10,-4]`** — all
reproduce, exactly, from a second implementation. The weight vector re-checks in
exact `Fraction` arithmetic on my side too (`holds: true`). `triple_set_mismatch_count: 0`
also disposes of the "the engine's move list might differ from the world's
triples" hypothesis on all 3000 worlds.

Row-by-row, not just totals:

```
$ python  # census.jsonl vs rederived.jsonl, joined on index
rows compared: 3000
seed mismatches: 0
ground-truth mismatches: 0
HiGHS status mismatches at bound=10: 0
wider-box mismatches: 0
word/integer disagreements: 0
bounds on census rows: {10} margins: {1}
```

3000/3000 agree on the ground truth, on HiGHS's integer at `bound=10`, and on all
three widened-box statuses. The engine's `status` word and `solver_status`
integer never disagree. Every census row carries `bound=10, margin=1` — the
default box is genuinely unchanged, as pre-registered.

I also checked E11's source directly
(`runs/20260729T000000Z-E11-engine-crosscheck-deep/partials/lp_potential-via-exhaustive.md`
§4.1, §4.3, §6): 2189 / 1550 / 1450 / 639/2189 = 29.2 % / 639 status 2 at
`bound=10` / 638 / 1 / the same seed and weights. `RECONCILIATION.md`'s divergence
#1 is correct: the *ticket prose* ("638 of the 639 were status 2") is wrong and
E11 §6 says 639/639. The census tests E11, which was the pre-registered choice.

### Can 29.2 % be read off the artifact without re-deriving?

**Off `census.jsonl`, yes. Off the engine's own product, no — and the
pre-registration overstates this.** The command from `RUN_STATE.md` works:

```
$ cd engine-rig && python - <<'PY'
import json
rows = [json.loads(l) for l in open(
    "runs/20260729T044500Z-E15-solver-status-bit/census.jsonl", encoding="utf-8")]
unreachable = [r for r in rows if r["goal_truly_unreachable"]]
silent = [r for r in unreachable if r["engine"]["status"] != "certified"]
print(len(silent), "/", len(unreachable), "= %.1f%%" % (100.0*len(silent)/len(unreachable)))
PY
639 / 2189 = 29.2%
```

But note what that reads. The numerator is the engine's `status` string. **The
denominator, `goal_truly_unreachable`, is the harness's own BFS** — not an engine
field, not a status string. And the engine's shipped artifact carries nothing at
all:

```
$ grep -c "no_linear_pagoda\|lp_outcome\|solver_status" artifacts/candidates.jsonl
0
```

A declined LP emits no candidate row (by design — `decide`'s docstring says so),
so the rate is not derivable from `candidates.jsonl` under any reading; it needs
`census.jsonl`, which is a *run* artifact pairing the engine's word with an
independent oracle.

`PREREGISTRATION.md` §P2.2 says `SUMMARY.json` is "derived from that file by
**counting `status` strings alone**, reports the incompleteness rate", and
`RECONCILIATION.md` §3 repeats "Every count below is a tally of the engine's own
`status` strings". That is false for the rate and for `goal_truly_unreachable`
(2189) and `goal_truly_reachable` (811). It is true for the numerator and for the
histogram. `RECONCILIATION.md` §2's ownership table and `RUN_STATE.md`'s
"The only engine field read is `status`" both get it right, so the artifact is
not deceptive — but two sentences claim more than the code does. **Overturned as
wording, not as substance.**

---

## (c) Does the zero_space downgrade reach the product?

**Verdict: yes, in the emitted rows, and the pinned hash does not move. Verified
independently. One concrete gap, already half-flagged by the implementer, which
I made reproducible.**

### The emitted stream

```
$ python runs/.../controls/n2_over_eight_colours.py     # writes real candidate rows
  PASS  the fixture really crosses the enumeration limit -- truncated_cells=[0, 1]
  PASS  no emitted payload claims scope == 'global' -- 0 row(s) still claim it
  PASS  nor any scope word a `'global' in scope` reader would accept -- []
  ... 11/11 PASS
N2_EXIT=0

$ python -m tools.validate_candidates runs/.../controls/artifacts/n2-candidates-10colour.jsonl
OK  (11 rows)   EXIT=0

$ python -c "...read the emitted jsonl..."
scopes: Counter({'undetermined': 9, 'cell_local': 2})
any global substring: []
degraded payload keys: ['coefficients','difference_rank','error','features','form',
 'modulus','rendering','scope','scope_note','scope_proved','space_dimension',
 'subset_enumeration_limit','support','truncated_cells','value']
```

These are rows read back **off disk** through `common.jsonio`, not in-memory
objects. `"global" in scope` returns nothing — `undetermined` is deliberately not
a superstring. The budget (`subset_enumeration_limit: 8`), the cells
(`truncated_cells`), the negative bit (`scope_proved: false`) and the prose
(`error`, `scope_note`) are all on the emitted payload.

### The byte-identity claim

I regenerated it myself rather than believing `P3-VERIFICATION.md`:

```
$ git show HEAD:engine-rig/artifacts/candidates.jsonl | sha256sum
5113ad321f680af0133ae17e2a549a8c75edd90ebfbcd69d9cb076b86daded8a
$ sha256sum artifacts/candidates.jsonl
5113ad321f680af0133ae17e2a549a8c75edd90ebfbcd69d9cb076b86daded8a
$ python -m tools.run_all --out artifacts/candidates.jsonl --deterministic --force
  candidates: 44 -> artifacts/candidates.jsonl
  SCHEMA    : OK
$ sha256sum artifacts/candidates.jsonl
5113ad321f680af0133ae17e2a549a8c75edd90ebfbcd69d9cb076b86daded8a
$ git status --porcelain artifacts/
(empty)
```

**Unchanged. No restore was needed.** `python -m tools.validate_candidates
artifacts/candidates.jsonl` → `OK (44 rows)`, exit 0.

The stale-pin finding also checks out: `release/MANIFEST.jsonl:667` pins
`679fe331…` / 47054 bytes for this path, and the tree is `5113ad32…` / 47705
bytes and was already `5113ad32…` at the branch's base. `P3-VERIFICATION.md`'s
reading — the literal P3.3 condition was unsatisfiable when it was written,
scored on intent, and reported rather than quietly relaxed — is correct and is
the right call. **Not an E15 failure.**

### The gap, made concrete

`P3-VERIFICATION.md` notes that `ZeroSpaceResult.as_json()` (`"form":
"zero_space_run"`) never reaches an artifact, so a truncated run whose null space
happens to be fully explained by *found* cell-local laws would emit no
`undetermined` row and therefore leave **no trace of the truncation in
`candidates.jsonl` at all**. It calls that hypothetical. It is not:

```
$ python  # 400 random 10-colour trajectories
FOUND a truncated run with zero undetermined laws
states: [['j', 'a'], ['j', 'j'], ['g', 'a']]
truncated_cells: [0, 1]  laws: 18  cell_local: 18  global: 0  undetermined: 0
run-level error: over budget: cell-local enumeration capped at 8 colours per cell...
payload keys of a law: ['coefficients','features','form','modulus','rendering','scope','support','value']
```

Every one of those 18 payloads has `scope_exhaustive is False` internally and
carries **no** budget key. Nothing false is published — a found cell-local law
really was found — but the pre-registration's P3.2 ("the degradation is written
*positively* into the payload") is satisfied only on runs that happen to produce
a quotient representative. Confirmed that no `zero_space_run` row is ever
emitted: `zero_space_run rows in stream: 0`. Recorded as OPTIONAL below, because
no claim is over-stated by it.

---

## (d) Are the negative controls constructionally guaranteed to go red?

**Verdict: yes. Reproduced independently against the *current* HEAD, and they are
not satisfiable by a trivially broken engine. One real weakness in
`tools/check_status_bit.py`.**

Scratch tree from `git archive HEAD engine-rig`; the revert applied there only.
Sanity first — unreverted scratch: `N1=0 N2=0 CSB=0`.

Revert applied (`potential.py`: non-certified branch → bare `None`, certified
branch → bare `Certificate`, `solve_certificate` → passthrough;
`__init__.py`: `decide` → passthrough with no sidecar, `run` → `if outcome is
None`; `zerospace.py`: `quotient_scope = GLOBAL` unconditionally). All six
substitutions asserted to match exactly once.

```
=== N1 under revert ===
  FAIL  the budgeted call really reached a HiGHS iteration limit -- solver_status=None
  FAIL  the engine hands back a structured outcome, not a bare value -- got 'NoneType'
  FAIL  its status word names the budget -- status=None
  FAIL  it is NOT no_linear_pagoda -- status=None no_linear_pagoda=None
  FAIL  decided is false -- decided=None
  FAIL  the public entry refuses instead of returning (None, None) -- (None, None)
  FAIL  the refusal carries the specific status word
  FAIL  unbudgeted, the SAME configuration is a proved infeasibility -- status=None
  PASS  and (None, None) is still what that returns -- run(...) -> (None, None)
  FAIL  the engine wrote a sidecar a consumer can read the classification off
  FAIL  and the sidecar says budget, undecided
N1_EXIT=1
N2_EXIT=1   (6 FAIL / 5 PASS, identical to NONVACUITY.md's table)
CSB_EXIT=1
```

**`NONVACUITY.md` is accurate.** 10 of 11 N1 checks red, 6 of 11 N2 checks red,
all three commands exit 1 — I got byte-for-byte the same rows the file reports,
including the single N1 check that stays green (`(None, None)` for the honest
infeasibility), which is exactly the point being made. I also re-ran the whole
experiment at the earlier HEAD `9920447` and got the same result, so the M30 fix
did not change it.

### Is a trivially broken engine let through?

Two cheap breaks, each on a fresh `git archive HEAD` copy:

**cheap-1 — an engine that never certifies** (`word = NO_LINEAR_PAGODA`, forced):

```
  FAIL  its status word names the budget -- status='no_linear_pagoda'
  FAIL  it is NOT no_linear_pagoda -- no_linear_pagoda=True
  FAIL  decided is false -- decided=True
  FAIL  the public entry refuses instead of returning (None, None) -- (None, None)
  FAIL  and the sidecar says budget, undecided
CHEAP1_N1_EXIT=1
```

**cheap-2 — the word `global` deleted** (`quotient_scope = UNDETERMINED`,
unconditionally):

```
  FAIL  and `global` is still emitted where it was proved -- scopes={'cell_local': 2, 'undetermined': 1}
  FAIL  an exhaustive row carries no degradation keys
CHEAP2_N2_EXIT=1
```

Both caught. The "guard against the cheap pass" in N2 (the 2-colour contrast run)
and in N1 (`baseline.status != CERTIFIED` in `check_status_bit`, and the
`no_linear_pagoda` baseline in the standalone) do the work they claim to.

### The weakness `NONVACUITY.md` does not disclose

`python -m tools.check_status_bit` exits 1 under the revert — but by **crashing**,
not by reporting:

```
  File ".../tools/check_status_bit.py", line 105, in control_iteration_limit
    if baseline.status != lp_potential.CERTIFIED:
AttributeError: 'Certificate' object has no attribute 'status'
CSB_EXIT=1
```

`NONVACUITY.md`'s table reports this as a clean `exit 1` beside the two
standalone controls, which report properly. Two consequences:

1. An operator hitting this at a merge gate sees a stack trace, not
   `FAILED N1-…`. The tool has a failure-reporting path (`failures.append`,
   `HELD`/`FAILED` printing) and it is not reached.
2. More materially: `main()` builds `[control() for control in CONTROLS]`
   eagerly, so **when N1's engine is broken, N2's control never runs at all.**
   A simultaneous `zero_space` regression would be invisible from this tool. The
   two standalone control scripts do not have this problem — they wrap their runs
   in `try/except` and score `condition is True`.

This is a real defect in the standing check, small, and easy to fix (wrap each
control body, or catch per-control). It does not weaken the E15 property; it
weakens the instrument.

---

## Other findings

### 1. `MUTATION.json` is stale and contradicts the shipped engine — REQUIRED

`MUTATION.json` (mtime 13:09:55) predates `engines/lp_potential/potential.py`
(13:12:16), `tests/test_solver_status_bit.py` (13:12:30) and `mutate.py`
(13:13:36). It reports **30 mutants, 26 killed, 4 survivors**, and lists

```json
{"id": "M30-success-status-disagreement-ignored", "outcome": "survived",
 "note": "a linprog result whose `success` and `status` disagree is classified
          anyway instead of refusing"}
```

The shipped engine does not have that hole — the M30 fix landed in `d2b75c26`,
and `mutate.py` has since gained `M31` for the one-directional variant. I re-ran
the battery from `git archive HEAD` in an isolated scratch copy:

```
$ cd <scratch>/engine-rig && python runs/.../mutate.py
{
  "mutants": 31, "killed": 28, "survived": 3, "not_applied": 0,
  "killed_only_by_suite": ["M06...","M14...","M17...","M20...","M28...",
                           "M30-success-status-disagreement-ignored",
                           "M31-disagreement-guard-only-one-way"],
  "killed_only_by_the_older_c11_file": ["M02-solve_certificate-collapses-to-none"],
  "survivors": [M27, M29, M25],
  "wall_seconds": 199.2
}
```

**31 / 28 / 3, with M30 and M31 both killed.** `RUN_STATE.md` ("30 mutants … 26
killed, 4 survived"), `MANIFEST.json` (`"pass (30 mutants, 26 killed, 4
survivors)"`) and the commit message all repeat the stale counts. `RUN_STATE.md`
*is* honest in prose that M30 "was acted on rather than filed", so the narrative
is not misleading — but the machine-readable artifact says the shipped engine has
an unguarded branch, and a reader who trusts `MUTATION.json` over the prose gets
a wrong answer about the code they are about to merge. Regenerate it, or stamp it
with the commit it was taken against.

### 2. Are the mutants a 1:1 mirror of the tests, and is `not_applied` honest?

**Both good.** `not_applied` is computed from an anchor-occurrence count
(`occurrences != 1` → `not_applied`, never `killed`) and reported as its own
field; `main()` returns 1 if any stray exists. `not_applied: 0` in both my run
and theirs, and I confirmed independently that all 31 anchors match. Judges are
kept separate, so the report can say *which* defence caught what — `M02` killed
only by C11's older file is genuinely disclosed rather than averaged away, and
`M29` is disclosed as caught by a test outside this battery's judges. Survivors
are reported with notes, including `M25` which is labelled a design alternative
expected to survive. This is not the C11 failure mode.

### 3. P5's pre-registered criterion is not met as written, and the re-reading is not flagged — REQUIRED (disclosure)

`PREREGISTRATION.md` §P5: *"The mutation battery must contain strictly **more
mutants than the number of assertions** written for this item."*

```
$ grep -c "assert " tests/test_solver_status_bit.py            → 82
   n1_iteration_limit.py check() calls                          → 11
   n2_over_eight_colours.py check() calls                       → 11
   check_status_bit.py failures.append() conditions             → 18
   total assertions for this item                               → 122
   mutants                                                      →  31
$ python -m pytest tests/test_solver_status_bit.py --collect-only -q | tail -1
28
```

31 mutants < 122 assertions. The criterion **fails as literally written**. It
passes under the reading `RUN_STATE.md` actually uses — "30 mutants against 25
test cases, deliberately not one-to-one" (now 31 against 28) — which is the more
sensible criterion and is the one C11's finding was about. But
`MANIFEST.json` scores P5 as a flat `"pass"` with no note, and the substitution
of *test cases* for *assertions* is never stated. Compare P3.3, where an
unsatisfiable literal condition **was** flagged, scored on intent, and written up.
The same treatment is owed here. This is a disclosure fix, not a re-run: I do not
think the item needs 123 mutants.

### 4. Pre-registration ordering — verified, holds

```
$ git log --format="%H %ad %s" --date=iso
d2b75c26 2026-07-29 13:20:38  E15: the 29.2% is now readable off the artifact...
99204472 2026-07-29 12:50:22  E15 items 1+3: the status bit survives to the caller...
72b4eb87 2026-07-29 12:41:12  E15: pre-registration -- what counts as passing, before anything was run
$ git log --diff-filter=A -- .../PREREGISTRATION.md    → 72b4eb87 (added there, nowhere else)
$ git merge-base --is-ancestor 72b4eb87 d2b75c26 && echo ANCESTOR
ANCESTOR
```

The pre-registration is a strict ancestor of both the engine commit and the
results commit, and was never amended (`git log -p` shows one add, no
modifications). The claim is checkable exactly as `MANIFEST.json` says.

### 5. Does anything call the documented incompleteness a defect? — No

```
$ grep -rn "defect\|bug" <all deliverables + changed sources>  # minus "not a defect" phrasings
```

Every surviving hit refers to the *status-collapse* or to a mutation, never to
the incompleteness. The framing is held explicitly and repeatedly:
`PREREGISTRATION.md` §"What this item is and is not", `RUN_STATE.md` §"What was
wrong", `tools/check_status_bit.py`'s module docstring, and
`tests/test_solver_status_bit.py`'s docstring all state that silence is a correct
answer and that no acceptance criterion improves if the silence rate falls. I
went looking for the overclaim and it is not there. Say that plainly: **this part
is done well.**

### 6. Does anything claim a proof where it has a HiGHS status? — Mostly no; one spot in the *product*

The prose is scrupulous. `RECONCILIATION.md` §6, `RUN_STATE.md` §"What this does
not establish", and `PREREGISTRATION.md`'s out-of-scope list all say "no exact
rational infeasibility certificate (Farkas dual) is produced; this remains a
HiGHS claim, not a proof".

The **emitted payload** is less careful. `LpOutcome.as_json()` publishes

```
"meaning": "HiGHS proved the LP infeasible: no weight function of this shape
            exists with |w_i| <= bound"
```

and `LpOutcome.no_linear_pagoda`'s docstring says "True only where HiGHS
*proved* the LP infeasible." The existence claim in the second clause is
unhedged, and it is asserted in the one place E15 says a reader should be able to
look. It *is* attributed to HiGHS, and `scope_of_claim` correctly names the box
on every row, which mitigates it — but the "floating point, no Farkas dual"
caveat lives only in Markdown. One clause in `STATUS_MEANINGS` closes it.

### 7. Provenance nits

* `MANIFEST.json` records `base_commit: 99204472`, which is **not** the engine
  that ships: `potential.py` changed again in `d2b75c26` (the M30 fix). All 34
  file hashes verify (`mismatches: 0`), so the manifest is internally consistent;
  the base commit is just one behind the artifact it describes.
* `d2b75c26` committed this reviewer's in-flight files (`adversarial_rederive.py`,
  `REDERIVED.json`, `rederived.jsonl`) into the run directory and manifest without
  attribution. Harmless to correctness, wrong as provenance.
* `P3-VERIFICATION.md` reports `python -m pytest → 519 passed, 27 skipped`; the
  tree now gives **528 passed, 27 skipped**. Explained by the suite growing after
  that verification ran, but the number in the file is no longer current.

### 8. The suite, exactly

```
$ cd engine-rig && python -m pytest -p no:cacheprovider
........................................................................ [ 90%]
.s...........ssss..................................                      [100%]
528 passed, 27 skipped in 43.01s
EXIT=0
```

Green. One caution for future reviewers, learned the hard way here: writing an
analysis script under `engine-rig/` can turn the suite red, because
`tests/test_tool_failure_is_not_truth.py::test_the_standing_check_is_green_on_this_territory`
runs `tools/check_solver_status` over the whole territory. My first draft bound
`sum(1 for r in rows if r["highs_status_bound10"] == 0)` to
`certificate_issued_status0` and the check flagged it — correctly. E15's own
deliverables pass that check cleanly:

```
$ python -m tools.check_solver_status runs/.../census.py runs/.../reconcile.py \
    runs/.../mutate.py runs/.../controls tools/check_status_bit.py tests/test_solver_status_bit.py
no claim about the world is decided by a bare tool status   (7 files, 0 notes)
EXIT=0
```

---

## What I could NOT check

* **That HiGHS status 2 is *true*.** I re-derived it with the same solver. Both
  the census and my re-derivation call `linprog(method="highs")` in floating
  point, so my agreement with E11 confirms the *reading* of the status, not the
  infeasibility. No Farkas dual was produced on either side. The one positive
  result (index 2302) I did verify exactly, in `Fraction` arithmetic, from
  `spec.triples` — that one does not rest on the solver.
* **Statuses 3 and 4 against real HiGHS.** `unbounded` and `numerical` occur 0
  times in 3000 worlds and are reachable in the tests only through the
  `_Stopped` stub. Status 1 *is* driven for real (`maxiter: 0`). The
  `success`/`status` disagreement guard (M30/M31) is likewise defended only by a
  synthetic `_Contradictory` — `RUN_STATE.md` says so itself, which is the right
  disclosure.
* **The literal pre-E15 engine.** `NONVACUITY.md`'s revert is a reconstruction of
  the *return contract*, not `git show e942ee6:…potential.py`. I reproduced their
  reconstruction, not the ancestor file. Their note saying so is accurate.
* **Anything outside `engine-rig/`.** I read `fuzzlab/props/lp_potential.py` and
  `fuzzlab/props/finding.py` and report what they do, but I did not run a fuzz
  campaign against the new engine, so I cannot say how many `raised` findings an
  `LpUnavailable` would now produce in practice — plausibly zero, since no world
  in 3000 hit status 1/3/4.
* **A concurrency-free reading.** HEAD moved under me mid-review (`9920447` →
  `d2b75c26`), and `P3-VERIFICATION.md` records the mutation battery rewriting
  tracked sources in this shared worktree earlier. All numbers above were taken
  on a tree verified clean by `git status --porcelain` immediately before and
  after, but I cannot certify that no other agent touched the tree between two
  of my commands.
* **Whether 44 rows / 9 zero_space rows is the right coverage** for the byte-
  identity claim. No checked-in fixture has more than 2 colours, so the degraded
  path never appears in `artifacts/candidates.jsonl`. That is what makes the hash
  stable, and it also means the stability result is evidence about the gating,
  not about the degraded payload's stability.

---

## REQUIRED FIXES

1. **Regenerate `MUTATION.json`, or stamp it with the commit it was run
   against.** As committed it reports `M30-success-status-disagreement-ignored`
   as a **survivor** of an engine that has since been fixed, and reports
   `30 / 26 / 4` where the shipped tree gives **`31 / 28 / 3`** (M30 and M31 both
   killed; survivors M25, M27, M29). Propagate the corrected counts to
   `RUN_STATE.md` §"The mutation battery, and its survivors" and to
   `MANIFEST.json`'s `pass_conditions.P5_…`.
2. **Disclose the P5 re-reading.** The pre-registered criterion is "strictly more
   mutants than the number of **assertions**" (122 assertions vs 31 mutants —
   fails). The item was scored against **test cases** (28 vs 31 — passes), which
   is the better criterion but is a substitution. Record it the way P3.3's stale
   pin was recorded, in `MANIFEST.json`'s notes and `RUN_STATE.md`; do not score
   P5 as a bare `"pass"`.
3. **Fix `tools/check_status_bit.py` so a broken engine produces a verdict, not a
   traceback — and so one control cannot mask the other.** Under the revert it
   dies with `AttributeError` on line 105 before N2 ever runs. Wrap each control
   body (or build the report list with per-control error capture) so
   `main()` still prints `FAILED N1-…` / `HELD N2-…` and exercises the reporting
   path it already has. Then correct `NONVACUITY.md`'s table, which currently
   lists this `exit 1` beside two properly-reported ones.
4. **Correct the two sentences that claim the rate is a tally of status strings
   alone** — `PREREGISTRATION.md` §P2.2 and `RECONCILIATION.md` §3. The
   denominator (2189 genuinely unreachable) is the harness's forward BFS, not an
   engine field, and `candidates.jsonl` carries no lp_potential status at all
   (`grep -c` → 0). §2's ownership table and `RUN_STATE.md` already state this
   correctly; the two headline sentences should match them.

## OPTIONAL

* Add the floating-point caveat to `STATUS_MEANINGS[NO_LINEAR_PAGODA]` (and to
  `LpOutcome.no_linear_pagoda`'s docstring). "HiGHS proved … no weight function
  of this shape exists" is the one unhedged existence claim that reaches the
  emitted payload, while the "not a proof" caveat lives only in Markdown.
* Emit the run-level degradation record, or carry a minimal truncation marker on
  every row of a truncated run. Witness that the gap is real, not hypothetical:
  `states=[['j','a'],['j','j'],['g','a']]` over a 10-colour palette truncates both
  cells, produces 18 cell-local laws and **zero** `undetermined` ones, so
  `candidates.jsonl` records the truncation nowhere. Nothing false is published;
  the budget simply is not in the product on that run. (Any fix must not add a
  key to the exhaustive path — that is what keeps the sha256 pinned.)
* Update `MANIFEST.json`'s `base_commit` to the commit that carries the shipped
  `potential.py`, and note that `adversarial_rederive.py` / `REDERIVED.json` /
  `rederived.jsonl` are this review's files, not the item's deliverables.
* Refresh `P3-VERIFICATION.md`'s `519 passed` to the current `528 passed`.
* Next ticket, outside `engine-rig/`: `fuzzlab/props/finding.py:run_invariants`
  turns an escaping `LpUnavailable` into a `raised` finding that
  `failures()` does not count, so a solver refusal cannot fail a fuzz campaign.
  E15 was right to scope this out; someone should scope it in.
