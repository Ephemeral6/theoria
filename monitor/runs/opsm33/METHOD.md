# Cycle 33 — arm measurement method (pinned, so six agents measure the same thing)

**Base is pinned to `ea4f6af6`** (`origin/master` as of 2026-07-30T14:22Z, right
after I pushed cycle 32's verdict table). `ci_merge.py` is running concurrently
(pid 32352) and will move `origin/master` underneath us; a floating base would
make the six results incomparable, so everyone pins the same SHA.

Cycle 32 measured the control **at `cc7e414e`** and got 6 failures. That control
is not reusable here: the three commits since it touch `monitor/` — including
`monitor/ci/CONFLICT-*.md`, `monitor/board/`, and `monitor/ops-status/` — and
this repository has tests that assert on board and CI state. So the control is
re-measured at `ea4f6af6` by its own agent, in parallel with the arms.

## Per-arm procedure

```bash
cd /c/Users/user/Desktop/theoria
git worktree add --detach .worktrees/opsm33-<slug> ea4f6af6
cd .worktrees/opsm33-<slug>
git merge --no-ff --no-edit origin/agent/<branch>     # ci_merge uses --no-ff
```

Record whether the merge is clean or conflicted, and if conflicted the exact
conflicted paths (`git diff --name-only --diff-filter=U`). A conflicted arm stops
here — there is no tree to gate.

Then run the gate **exactly as `ci_merge.py:539-544` invokes it**:

* `cwd` = `<worktree>/<territory>` (e.g. `<wt>/monitor`), **not** the repo root;
* `PYTHONPATH` = the worktree root prepended (`gates.gate_env`) — without it a
  gate that imports its own package dies at import and is misreported as the
  territory failing its own check;
* timeout 1800.

Then, separately, `python -m pytest -q -rf` in the same territory to recover the
**full** failing-id set — the gate stops at the first red stage and therefore
undercounts.

## What a verdict means

**INNOCENT** = the arm's failing-id set is *set-equal* to the control's. The
branch did not break anything; the flag is the queue reporting a pre-existing
red as if the branch caused it.

**GUILTY** = ids present in the arm and absent from the control. Name them.

**THIRD CATEGORY** = the branch adds new tests that fail *against master's
existing code*. Then the red is the branch correctly catching a master defect —
neither innocent nor guilty, and it is adjudicated differently. Check for this
explicitly: compare collected counts and check whether the added test files pass
standalone. Cycle 32 checked this on `s40` and it did not fire; do not assume.

## Reporting

Each agent writes `monitor/runs/opsm33/arm-<slug>.md` **as it goes**, not at the
end, and returns a compact summary. Raw sorted failing-id lists go in the file.
Nothing lives only in an agent's context.
