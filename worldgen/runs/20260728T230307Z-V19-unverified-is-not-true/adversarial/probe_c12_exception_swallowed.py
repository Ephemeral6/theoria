"""F1 / mutant C12, demonstrated in one process: swallow the exception and a
check that raised on every state reports `holds`.

`check_invariants` files a raising `check` as `violated`, and nothing tested
that it does.  Replace the `except` body with `continue` — the whole of mutant
C12 — and an invariant whose predicate raises on all 24 reachable states of
`t1-walk-maze` comes back

    {'states_checked': 24, 'verified': True, 'holds': True, 'status': 'holds'}
    all_invariants_hold: True

which is V19's own sentence, reconstructed: "I could not check this" written
as "this holds", with a callable in the row so nobody thinks to look.  Under
C12 both `python -m pytest worldgen -q` and `python -m worldgen.build` stayed
green.

**This probe reads the source as reviewed — `git show <REVIEWED>:...` — not the
working tree.**  The review examined commit `23ec179`; F1 was reported against
that code and repairs were landing while this file was being written, so a
probe anchored to the working tree would break within the hour and, worse,
would silently start measuring something else.  If the anchor is gone from the
reviewed blob too, the probe says so and stops rather than guessing.

Re-running it against a *repaired* tree is a legitimate second question and the
probe answers it if you pass `--worktree`: the expected outcome after F1 is
fixed is that the anchor no longer matches, or that the row no longer comes
back `holds`.

    python worldgen/runs/*-V19-*/adversarial/probe_c12_exception_swallowed.py
    python worldgen/runs/*-V19-*/adversarial/probe_c12_exception_swallowed.py --worktree
"""

import os
import subprocess
import sys
import types

# Four up from `adversarial/` is the checkout root, whatever the cwd is.
ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
sys.path.insert(0, ROOT)

from worldgen.tests import support

#: The commit the adversarial review examined.  See ../ADVERSARIAL-VERBATIM.md.
REVIEWED = "23ec179"
RELPATH = "worldgen/core/truth.py"

ANCHOR = ('                except Exception as exc:\n'
          '                    violations.append({"state": list(state.key()), '
          '"error": repr(exc)})\n'
          '                    break\n')
MUTANT = '                except Exception:\n                    continue\n'


def reviewed_source():
    out = subprocess.run(["git", "show", "%s:%s" % (REVIEWED, RELPATH)],
                         cwd=ROOT, capture_output=True)
    if out.returncode != 0:
        raise SystemExit("could not read %s at %s:\n%s"
                         % (RELPATH, REVIEWED,
                            out.stderr.decode("utf-8", "replace")))
    return out.stdout.decode("utf-8")


def worktree_source():
    with open(os.path.join(ROOT, RELPATH), encoding="utf-8") as handle:
        return handle.read()


use_worktree = "--worktree" in sys.argv
src = worktree_source() if use_worktree else reviewed_source()
label = "the working tree" if use_worktree else "%s (as reviewed)" % REVIEWED

found = src.count(ANCHOR)
print("source: %s" % label)
if found != 1:
    print("the C12 anchor occurs %d times (expected 1) — the except branch has "
          "moved or been repaired.\nThis probe does not guess at a new anchor: "
          "a re-anchored mutant is a different experiment.\nCompare against "
          "`git show %s:%s` and ../ADVERSARIAL-VERBATIM.md §F1."
          % (found, REVIEWED, RELPATH))
    raise SystemExit(0 if use_worktree else 1)

module = types.ModuleType("truth_c12")
module.__name__ = "worldgen.core.truth"
module.__package__ = "worldgen.core"
sys.modules["truth_c12"] = module
exec(compile(src.replace(ANCHOR, MUTANT), "truth_c12.py", "exec"),
     module.__dict__)

table = module.invariant_table


def with_a_raising_check(world):
    rows = table(world)
    rows.append({"name": "always_raises",
                 "statement": "a predicate that raises on every state",
                 "check": lambda _w, _s: (_ for _ in ()).throw(RuntimeError("nope"))})
    return rows


module.invariant_table = with_a_raising_check

rows = module.check_invariants(support.world("t1-walk-maze"))
row = [r for r in rows if r["name"] == "always_raises"][0]
print("row:", {k: v for k, v in row.items() if k != "statement"})
print("all_invariants_hold:", module.all_invariants_hold(rows))
