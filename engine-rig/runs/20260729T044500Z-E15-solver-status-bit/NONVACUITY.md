# E15 P4 — the two negative controls, measured against the reverted engine

Pre-registration: `PREREGISTRATION.md` §P4 — *"With the structured result
collapsed back to a bare `None` (and, for N2, with the degraded `scope` restored
to `"global"`), both controls must exit 1. A control that stays green under the
reverted engine has not tested anything and this item is not done."*

This file is the measurement, not the claim. Every exit code below was observed.

## Result

| control | engine as committed | engine reverted | how it reported |
|---|---|---|---|
| `controls/n1_iteration_limit.py` | **exit 0** | **exit 1** | verdict artifact, 10 of 11 checks FAIL |
| `controls/n2_over_eight_colours.py` | **exit 0** | **exit 1** | verdict artifact, 6 of 11 checks FAIL |
| `python -m tools.check_status_bit` (the standing pair) | **exit 0** | **exit 1** | **originally: an uncaught `AttributeError` — see below** |

Both controls go red under the revert. Neither is vacuous.

### Correction: the third row was not the clean exit 1 this table implied

As first written this table listed all three exit codes side by side, which read
as three instruments reporting a regression. The two standalone controls did.
`tools/check_status_bit` did not: under the revert it exited 1 by **crashing** —

```
  File ".../tools/check_status_bit.py", line 105, in control_iteration_limit
    if baseline.status != lp_potential.CERTIFIED:
AttributeError: 'Certificate' object has no attribute 'status'
```

Two things were wrong with that, and an adversarial review named both. An
operator at a merge gate saw a stack trace instead of `FAILED N1-…`, so the
tool's own reporting path — the thing being trusted to *describe* a regression —
was never exercised by the case it exists for. And `main()` built its report list
eagerly, so **N1 crashing meant N2 never ran**: a simultaneous `zero_space`
regression would have been invisible behind an unrelated `lp_potential` one.

Fixed in `af884509`: each control body is wrapped, and an exception becomes a
FAILED verdict naming the exception. Re-measured on a fresh `git archive HEAD`
scratch copy with the same revert applied to `potential.py` and
`__init__.py` only:

```
FAILED N1-iteration-limit-is-not-an-infeasibility
       - the control could not complete: AttributeError: 'NoneType' object has no attribute 'as_json'
HELD   N2-truncated-enumeration-is-not-a-global-law
EXIT=1
```

N1 now reports rather than explodes, and N2 still runs and is still judged — it
holds there because that scratch revert touched only `lp_potential`, which is
exactly the independence that was missing. The exit code was always right; what
was missing was the ability to tell *which* property broke, which is this item's
own complaint applied to its own instrument.

## How it was measured

The revert was applied to a **scratch copy outside the repository**, never to the
worktree. Two reasons, and the second one was not anticipated:

1. Other agents hold P1/P2/P3/P5 of this ticket in the *same* worktree. Editing
   `engines/` in place would have corrupted their runs.
2. P5's mutation battery edits engine sources in place while it runs. A first
   attempt built the scratch tree with `shutil.copytree` of the working tree and
   caught a mutant mid-flight — `UNDETERMINED = "global_undetermined"` — which
   N2 promptly failed on (`FAIL nor any scope word a `'global' in scope` reader
   would accept -- ['global_undetermined']`). That is the control working, but it
   is not the engine as committed, so the reading was thrown away.

The scratch tree is therefore built from **git HEAD**, not from the working
tree:

```
git -C <worktree> archive HEAD -o head.tar \
    engine-rig/engines engine-rig/common engine-rig/fixtures \
    engine-rig/tools engine-rig/pytest.ini engine-rig/conftest.py
tar -xf head.tar -C <scratch>
```

Base commit: `9920447` — *"E15 items 1+3: the status bit survives to the caller,
and zero_space says when it degraded"*. The two control scripts and
`tools/check_status_bit.py` are untracked work in progress and were copied from
the working tree; the engine under test was not.

Each phase runs all three commands from the scratch `engine-rig/` with a plain
`subprocess.run`, and only the process exit code is read.

## The revert, exactly

Three edits, mechanical string replacements, reproducible from this file.

### R1 — `engines/lp_potential/potential.py`: the structured result collapsed

```python
# solve(), the non-certified branch
-    if word != CERTIFIED:
-        if result.success:
-            raise LpUnavailable(...)
-        return outcome
+    if word != CERTIFIED:
+        return None            # REVERTED to pre-E15: one value, four meanings

# solve(), the certified return
-    return LpOutcome(status=CERTIFIED, solver_status=int(result.status),
-                     solver_message=message, bound=bound, margin=margin,
-                     certificate=certificate)
+    return certificate         # REVERTED to pre-E15

# solve_certificate(), which no longer has a status word to branch on
-    outcome = solve(...)
-    if outcome.status == CERTIFIED: return outcome.certificate
-    if outcome.status == NO_LINEAR_PAGODA: return None
-    raise LpUnavailable(...)
+    return solve(graph, initial, goal_states=goal_states, margin=margin,
+                 bound=bound, solver_options=solver_options)   # REVERTED
```

### R1 (cont.) — `engines/lp_potential/__init__.py`: no sidecar, no status branch

```python
# decide()
-    outcome = solve(...)
-    if outcome_path: <write outcome.as_json()>
-    return outcome
+    return solve(graph, initial, goal_states=goal_states, margin=margin,
+                 bound=bound, solver_options=solver_options)   # REVERTED

# run()
-    outcome = decide(...)
-    if outcome.status == NO_LINEAR_PAGODA: return None, None
-    if outcome.status != CERTIFIED: raise LpUnavailable(...)
-    certificate = outcome.certificate
+    certificate = decide(...)
+    if certificate is None:                # REVERTED to pre-E15: the collapse
+        return None, None
```

### R2 — `engines/zero_space/zerospace.py`: the degraded scope restored

```python
-    quotient_scope = GLOBAL if not truncated_cells else UNDETERMINED
+    quotient_scope = GLOBAL        # REVERTED to pre-E15: the budget promotes
```

One line, and it reverts the whole degradation: `Law.as_json` gates the
`scope_proved` / `subset_enumeration_limit` / `truncated_cells` / `error` /
`scope_note` keys on `scope == UNDETERMINED`, so restoring the label also
removes the budget from every payload — which is exactly the pre-E15 product.

## What went red, check by check

### N1 under R1 — 10 of 11 checks fail

```
FAIL  the budgeted call really reached a HiGHS iteration limit -- solver_status=None (want 1); None
FAIL  the engine hands back a structured outcome, not a bare value -- got 'NoneType'
FAIL  its status word names the budget -- status=None
FAIL  it is NOT no_linear_pagoda -- status=None no_linear_pagoda=None
FAIL  decided is false -- decided=None
FAIL  the public entry refuses instead of returning (None, None) -- (None, None)
FAIL  the refusal carries the specific status word -- exception.outcome.status=None
FAIL  unbudgeted, the SAME configuration is a proved infeasibility -- status=None
PASS  and (None, None) is still what that returns -- run(...) -> (None, None)
FAIL  the engine wrote a sidecar a consumer can read the classification off -- keys=None
FAIL  and the sidecar says budget, undecided -- {"decided": null, ... "status": null}
```

The one line that stays green is the point of the whole item: under the reverted
engine, `run(graph, "0111")` returns `(None, None)` **and so does**
`run(graph, "0111", solver_options={"maxiter": 0})`. A proved infeasibility and
an iteration limit arrive at the caller as the same value, and the caller's
docstring reads that value as the geometric fact. The control's remaining checks
are the ones that can tell them apart, and every one of them fails.

Note the direction of the failures: under the revert the observed values are
`None`, not `False`. Each check is written `condition is True` rather than on
truthiness, precisely so that `not None` cannot pass for a refuted claim.

### N2 under R2 — 6 of 11 checks fail

```
PASS  the fixture really crosses the enumeration limit -- truncated_cells=[0, 1]
PASS  the run emitted candidate rows to read back -- 11 row(s)
FAIL  no emitted payload claims scope == 'global' -- 9 row(s) still claim it
FAIL  nor any scope word a `'global' in scope` reader would accept -- ['global']
FAIL  the quotient representatives are published, under the degraded word -- 0 payload(s)
FAIL  every degraded payload carries the budget keys -- missing []
FAIL  and the budget it carries is the one that actually bit -- 0 payload(s)
FAIL  every degraded payload names the cells that went unenumerated -- run truncated [0, 1]
PASS  under the limit nothing is truncated -- truncated_cells=[]
PASS  and `global` is still emitted where it was proved -- scopes={'cell_local': 2, 'global': 1}
PASS  an exhaustive row carries no degradation keys
```

Nine laws recovered from a trajectory whose colour subsets were never
exhaustively enumerated go out labelled `scope: "global"` — published as facts
about the *world* on the strength of a search that was cut short. The three
checks that stay green are the control's own guards: the fixture still crosses
the limit, and the label is still earned on a two-colour run. Those three are
what stop the control from being satisfiable by an engine that has simply
deleted the word `global`, which would be the same defect from the other side.

## Two things this does not measure

* **The revert is a reconstruction, not the pre-E15 file.** `git show
  e942ee6:engine-rig/engines/lp_potential/potential.py` is the real ancestor;
  R1 reproduces its *return contract* (`Certificate | None`, one value for four
  reasons) rather than its text, because the point is the collapse and not the
  1500 lines around it. A reader who wants the literal ancestor has the commit.
* **N1's exit 1 is over-determined under R1.** Ten checks fail at once, so the
  measurement shows the control is not vacuous but does not isolate which single
  field carries the property. The per-field isolation is P5's job (the mutation
  battery), and the two were kept apart deliberately: a control that is also a
  mutation harness reports one number for two questions.
