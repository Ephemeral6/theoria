"""Spike: does the positional encoding need a well-formedness hypothesis?

Kept as a run artefact because its answer decided the shape of the emitted Lean.
Two questions, both answered by exhaustive enumeration over the 16^3 encodable
states of `sokoban-open4far`:

1. Does the encoding agree with the STRIPS task?  (Answer: on well-formed
   states yes, on degenerate ones no -- two things in one cell has no atom-set
   counterpart, since `clear` is one atom and would have to be both.)
2. Does pattern closure survive on the degenerate states anyway, under the
   *encoded* semantics?  If yes, the emitted theorem needs no `wf` hypothesis
   and the case split shrinks by a factor of one cell per unpinned box.
"""

import itertools
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))

from theory_compiler import strips                      # noqa: E402
from theory_compiler.strips import Atom                 # noqa: E402

FIX = os.path.join(HERE, "..", "..", "tests", "fixtures", "strips")
task = strips.load_task(os.path.join(FIX, "sokoban_domain.pddl"),
                        os.path.join(FIX, "sokoban_open4far.pddl"))
CELLS = task.objects_of("cell")
BOXES = task.objects_of("box")


def encoded(action):
    """(guard, effect) in the positional encoding, read off the ground action."""
    guard_player, guard_box, guard_clear = None, {}, []
    for atom in sorted(action.pre):
        if atom.name == "at-player":
            guard_player = atom.args[0]
        elif atom.name == "at":
            guard_box[atom.args[0]] = atom.args[1]
        elif atom.name == "clear":
            guard_clear.append(atom.args[0])
    effect_player, effect_box = None, {}
    for atom in sorted(action.add):
        if atom.name == "at-player":
            effect_player = atom.args[0]
        elif atom.name == "at":
            effect_box[atom.args[0]] = atom.args[1]
    return (guard_player, guard_box, tuple(guard_clear)), (effect_player, effect_box)


ENC = {a: encoded(a) for a in task.actions}


def legal(state, action):
    (gp, gb, gc), _ = ENC[action]
    if gp is not None and state[0] != gp:
        return False
    for box, cell in gb.items():
        if state[1 + BOXES.index(box)] != cell:
            return False
    return all(c not in state for c in gc)


def apply_move(state, action):
    _, (ep, eb) = ENC[action]
    out = list(state)
    if ep is not None:
        out[0] = ep
    for box, cell in eb.items():
        out[1 + BOXES.index(box)] = cell
    return tuple(out)


PATTERNS = {
    "b1c11": lambda s: s[1] == "c11",
    "b1c12_b2c13": lambda s: s[1] == "c12" and s[2] == "c13",
}

if __name__ == "__main__":
    rows = []
    for name, pat in PATTERNS.items():
        broke_wf = broke_degenerate = holds = 0
        for state in itertools.product(CELLS, repeat=3):
            if not pat(state):
                continue
            for action in task.actions:
                if not legal(state, action):
                    continue
                if pat(apply_move(state, action)):
                    holds += 1
                elif len(set(state)) == 3:
                    broke_wf += 1
                    print("WF COUNTEREXAMPLE", name, state, action)
                else:
                    broke_degenerate += 1
                    if broke_degenerate <= 3:
                        print("degenerate counterexample", name, state, action)
        rows.append((name, holds, broke_wf, broke_degenerate))

    print()
    for name, holds, bad_wf, bad_degenerate in rows:
        print("%-12s legal-from-pattern %5d   closure breaks: wf %d  degenerate %d"
              % (name, holds + bad_wf + bad_degenerate, bad_wf, bad_degenerate))
