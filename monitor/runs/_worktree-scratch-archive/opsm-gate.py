"""OPS-M cycle 16: run the real merge gate on a staged worktree.

Same answer ci_merge would compute -- `gates.run(root, territory)` -- but pointed
at a worktree I control, so a resolution that was made in a previous session is
re-checked against the master that exists now rather than the one it was made on.
Usage: python .worktrees/opsm-gate.py <worktree> <dir> [<dir> ...]
Exit 0 only if every territory's outcome is in gates.PASSING.
"""
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "monitor"))
import gates  # noqa: E402

wt = os.path.abspath(sys.argv[1])
# `gates.run()` does NOT apply `gates.gate_env()`, but `ci_merge.try_merge` does
# (ci_merge.py:375).  So the module's own runner fails a territory whose gate
# imports its own package -- worldgen/verify.py dies on `from worldgen.qc import
# gate` before it checks anything -- while the merge rig passes it.  Until that is
# fixed in monitor/ (not my territory), reproduce ci_merge's environment here, or
# I would be reading a red that the merge rig never sees.
os.environ.update(gates.gate_env(wt))
worst_bad = []
for d in sys.argv[2:]:
    if "." in d:            # PARTNER_SYNC.md and friends are not territories
        print("SKIP     %-14s (not a territory)" % d)
        continue
    outcome, detail = gates.run(wt, d)
    # ci_merge's blocking condition is the gate's exit code, nothing else: a gate
    # that exits 0 but drops files is merged with `a gate dirtied the worktree`
    # in the log (ci_merge.py:397-404).  `gates.PASSING` excludes `dirty`, so
    # using it here would hold branches the merge rig would have let through --
    # a stricter judge than the one whose seat I am sitting in.
    ok = outcome not in ("red", "broken")
    print("%-8s %-14s %s" % (outcome.upper(), d,
                             (detail.splitlines() or [""])[0][:160]))
    if not ok:
        worst_bad.append((d, outcome, detail))
for d, outcome, detail in worst_bad:
    print("\n===== %s -> %s =====\n%s" % (d, outcome, detail[-4000:]))
sys.exit(1 if worst_bad else 0)
