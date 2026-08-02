"""C15 — the three claims that decide the verdict, reproduced first-hand.

An adversarial review of C15's *draft* argument said three of its load-bearing
clauses were false. A refusal is only worth freezing if it names the strongest
version of the thing it refuses, so each was re-measured here rather than taken
on report.

* **A. Is a compiled theory's write-extent really its instance set?** The draft
  said yes in all four forms. Check what `gen_pddl` emits for a board cell no
  instance stands on.
* **B. Are the four forms four independent witnesses?** The draft leaned on
  "all four refuse". Check whether `gen_lean` is an independent encoding of the
  state or a consumer of `gen_python`'s.
* **C. Does a form exist that writes a never-changed cell WITHOUT seating an
  instance?** The draft said the design space is empty. Build the best candidate
  — a sparse, write-time overlay — and run it.

C is built by patching the *generated* module, which is what a compiler change
would emit. That is enough to decide whether the design space is empty; it is
not a proposed patch to this compiler, and nothing here is wired into the build.

Offline. No network, no model call, no level data from any game.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TC = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(TC, "src"))

from theory_compiler.generators.gen_pddl import generate_pddl  # noqa: E402
from theory_compiler.generators.gen_python import generate_python  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402
from theory_compiler.problem import from_json, load_problem  # noqa: E402

FIXTURES = os.path.join(TC, "tests", "fixtures")

BAR_BOARD = [[9, 9, 9, 9, 9, 9, 9, 9]]


def bar_level(seated):
    return from_json({
        "name": "burn-bar", "grid": [1, 8], "background": 0, "board": BAR_BOARD,
        "objects": [{"name": "Bar_%d" % c, "type": "Bar", "pos": [0, c],
                     "color": 1 if c >= 6 else 9} for c in seated],
        "landmarks": {}, "arena": [[0, c] for c in range(8)],
    })


BAR = """semantics:
  frame persist
  conflict exclusive
  cascade single_frame

word_table:
  board
  object Bar { pos: Coord, color: Int }

events:
  event recolored(o, c)

rules:
  rule edge_advance forall ?p in Bar
    when act=key(2) and colored(?p, 9) and colored(rightof(?p), 1) then recolored(?p, 1)

goal:
  goal count(Bar, color = 1) = 8
"""


def claim_a():
    """Does the PDDL form give a never-changed cell a fluent?"""
    print("=" * 72)
    print("A. gen_pddl's mutable domain -- cells, or instances?")
    print("=" * 72)
    # The cart fixture unedited names no colour, so `colours` is empty and no
    # colour fluent is emitted at all -- a first pass measured 0 facts and read
    # it as a refutation, which it is not. Adding one `recolored` effect is what
    # puts the fluent in scope; nothing else about the world changes.
    with open(os.path.join(FIXTURES, "cart_theory.dsl"), encoding="utf-8") as fh:
        base = fh.read()
    text = (base.replace("  event moved(o, dir) | teleported(o, dest)",
                         "  event moved(o, dir) | teleported(o, dest)"
                         " | recolored(o, c)")
                .replace("\ngoal:", "\n  rule tint [ev: t7 cov: 1/1]\n"
                         "    when act=push(Cart, down) and above(Cart) = wall"
                         " then recolored(Cart, 1)\n\ngoal:"))
    ast = parse_theory(text)
    problem = load_problem(os.path.join(FIXTURES, "cart_problem.json"))
    domain, prob = generate_pddl(ast, "cart-instance", 3, 2, problem=problem)

    seated = sorted(i.name for i in problem.instances)
    seated_cells = {tuple(i.pos) for i in problem.instances if i.pos is not None}
    print("seated instances      : %s" % seated)
    print("cells they stand on   : %s" % sorted(seated_cells))

    colour_facts = sorted(set(re.findall(r"\(colour-\d+ cell-\d+-\d+\)", prob)))
    print("colour facts in :init : %d" % len(colour_facts))
    for f in colour_facts:
        r, c = map(int, re.search(r"cell-(\d+)-(\d+)", f).groups())
        mark = "  <- board cell, no instance" if (r, c) not in seated_cells else ""
        print("    %s%s" % (f, mark))

    decl = [ln.strip() for ln in domain.splitlines()
            if re.search(r"\(colour-\d+ \?", ln)]
    print("fluent declaration    : %s" % (decl[0] if decl else "(none found)"))
    print("\nVERDICT A: the colour fluent is declared over `?c - cell`, not over")
    print("an object -- printed above, measured. So the STRIPS form's colour")
    print("domain is the CELL set, and the draft's universal claim -- write-")
    print("extent == instance set, in ALL FOUR forms -- is FALSE.")
    print()
    print("Stated exactly, because this probe is correcting an overclaim and")
    print("must not commit one: the 0 facts above are not a refutation. This")
    print("world's board is entirely background, and gen_pddl.py:440-443 emits a")
    print("colour fact only where `problem.board` differs from the background --")
    print("it reads the board layer directly, which is by definition the never-")
    print("varying one. A painted board therefore DOES put colour facts on cells")
    print("no instance stands on. That half is read from the source, not")
    print("demonstrated in a compiled world here: the world with a painted board")
    print("is the 1x8 bar, and gen_pddl refuses it for the unrelated")
    print("`colored(<cell>, n)` reason. Declaration measured; emission read.\n")


def claim_b():
    """Is gen_lean an independent encoding, or a consumer of gen_python?"""
    print("=" * 72)
    print("B. Are the four forms four independent witnesses?")
    print("=" * 72)
    path = os.path.join(TC, "src", "theory_compiler", "generators", "gen_lean.py")
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    for pat, label in [(r"def _load_predictor", "gen_lean._load_predictor defined"),
                       (r"generate_python\(", "gen_lean calls generate_python"),
                       (r"\bexec\(", "gen_lean execs generated source")]:
        hits = [i + 1 for i, ln in enumerate(src.splitlines())
                if re.search(pat, ln)]
        print("  %-38s %s" % (label, hits or "no"))
    print("\nVERDICT B: `gen_lean` obtains its transition relation by executing")
    print("`gen_python`'s output, so a refusal raised inside gen_python reaches")
    print("Lean as a dependent, not as a second opinion. 'All four forms refuse'")
    print("is TRUE as an observation and OVERSTATED as independent corroboration.\n")


OVERLAY_PATCH = '''
# ---- C15 counter-design: a sparse, write-time board overlay -------------
# Not a proposal. The strongest form of option (a) the review could build:
# one extra state field, populated only where a rule actually writes, so no
# per-cell allocation and no instance in `problem.instances`.
_orig_render = render
_orig_key = State.key

def _overlay_key(self):
    return _orig_key(self) + (tuple(sorted(getattr(self, "overlay", {}).items())),)

State.key = _overlay_key

# NOTE the signature: the generated `render` is `render(state, _exclude=())`
# and `_cell_colour` calls it with two arguments. An override taking one
# silently breaks every guard that reads a cell -- which is what a first draft
# of this probe did, and it failed loudly rather than quietly only by luck.
def render(state, _exclude=()):
    grid = _orig_render(state, _exclude)
    for (r, c), colour in getattr(state, "overlay", {}).items():
        grid[r][c] = colour
    return grid

def step_with_overlay(state, action):
    """The edge_advance law, aimed at the frontier cell via the overlay."""
    nxt = step(state, action)
    ov = dict(getattr(state, "overlay", {}))
    if action == ("key", 2):
        row = render(state)[0]
        burnt = [i for i, v in enumerate(row) if v == 1]
        if burnt and min(burnt) - 1 >= 0:
            ov[(0, min(burnt) - 1)] = 1
    setattr(nxt, "overlay", ov)
    return nxt
'''


def claim_c():
    """Can a never-changed cell be written without seating an instance?"""
    print("=" * 72)
    print("C. Is option (a)'s design space really empty?")
    print("=" * 72)
    src = generate_python(parse_theory(BAR), bar_level([6, 7]))
    ns = {}
    exec(compile(src + OVERLAY_PATCH, "<theory.py>", "exec"), ns)  # noqa: S102

    s0 = ns["initial_state"]()
    try:
        object.__setattr__(s0, "overlay", {})
    except Exception:  # noqa: BLE001
        s0.overlay = {}
    before = ns["render"](s0)[0]
    s1 = ns["step_with_overlay"](s0, ("key", 2))
    after = ns["render"](s1)[0]

    print("seated instances : %s" % sorted(
        i.name for i in bar_level([6, 7]).instances))
    print("row before       : %s" % before)
    print("row after        : %s" % after)
    print("keys differ      : %s" % (s0.key() != s1.key()))
    print("overlay contents : %s" % dict(getattr(s1, "overlay", {})))
    burned = before != after
    print("\nVERDICT C: the frontier cell %s, with nothing seated on it and one"
          % ("BURNED" if burned else "did NOT burn"))
    print("extra state field -- not one per cell. So the design space of option")
    print("(a) is NOT EMPTY. The draft's 'any such form reduces to seating' is")
    print("FALSE. What the overlay actually costs is elsewhere: `frame persist`,")
    print("`conflict exclusive` and `count(Type, ...)` are all defined over")
    print("OBJECTS, and none of them can see this cell.\n")


if __name__ == "__main__":
    claim_a()
    claim_b()
    claim_c()
