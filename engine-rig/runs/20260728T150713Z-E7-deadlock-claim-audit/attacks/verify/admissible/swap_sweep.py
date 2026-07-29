"""Same pattern, both tasks: does the guard raise h, or does iPDB just get lucky?

For a fixed pattern P the guarded task's operator set is a subset of the base
task's, so h_P(guarded) >= h_P(base) always.  The question the reviewer's
"pin the generator" test asks badly is whether that inequality is ever *strict
enough to reach infinity* on a pattern nobody chose after seeing the answer.

Patterns are named by the atoms they project onto, then translated to each
task's own variable indices, so the two runs really do evaluate the same
projection.  The player and box variables happen to land on the same indices in
both tasks; the `clear` variables are permuted, and the mapping is by name.
"""
import itertools, json, os, sys
import run as R
import sasvars

A = R.ATTACKS
BASE_D, BASE_P = R.DOMAIN, os.path.join(A, "work", "a5", "swap", "swap-passage.pddl")
G_D = os.path.join(A, "work", "a5", "swap", "singleton", "sokoban_guarded_singleton_domain.pddl")
G_P = os.path.join(A, "work", "a5", "swap", "singleton", "swap-passage_guarded_singleton.pddl")

bv = sasvars.variables(sasvars.translate(BASE_D, BASE_P))
gv = sasvars.variables(sasvars.translate(G_D, G_P))


def key(v):
    """A name for a variable that means the same thing in both tasks."""
    vals = [x for x in v["values"] if not x.startswith("Atom clear") or True]
    for x in v["values"]:
        if x.startswith("Atom clear("):
            return "clear:" + x[len("Atom clear("):-1]
        if x.startswith("Atom at-player("):
            return "player"
        if x.startswith("Atom at(b"):
            return "box:" + x[len("Atom at("):].split(",")[0]
    return "?" + v["values"][0]


bmap = {key(v): v["index"] for v in bv}
gmap = {key(v): v["index"] for v in gv}
assert set(bmap) == set(gmap), (sorted(set(bmap) ^ set(gmap)))
CLEARS = sorted(k for k in bmap if k.startswith("clear:"))
CORE = ["box:b1", "box:b2"]


def collection(names_list, m):
    return "[" + ",".join("[" + ",".join(str(m[n]) for n in names) + "]"
                          for names in names_list) + "]"


def probe(tag, names_list):
    b = R.run(BASE_D, BASE_P,
              "astar(cpdbs(patterns=manual_patterns(%s)))" % collection(names_list, bmap),
              "swap.sweep.%s.base" % tag)
    g = R.run(G_D, G_P,
              "astar(cpdbs(patterns=manual_patterns(%s)))" % collection(names_list, gmap),
              "swap.sweep.%s.guarded" % tag)
    print("  %-22s n_patterns=%-5d h(init) %-8s -> %-8s   exp %6s -> %-6s"
          % (tag, len(names_list), b["initial_h"], g["initial_h"],
             b["expanded"], g["expanded"]), flush=True)
    return {"tag": tag, "n_patterns": len(names_list), "base": b, "guarded": g}


if __name__ == "__main__":
    recs = []
    recs.append(probe("boxes", [CORE]))
    recs.append(probe("boxes+player", [CORE + ["player"]]))
    recs.append(probe("boxes+1clear", [CORE + [c] for c in CLEARS]))
    recs.append(probe("boxes+player+1clear", [CORE + ["player", c] for c in CLEARS]))
    recs.append(probe("boxes+2clear", [CORE + list(c) for c in itertools.combinations(CLEARS, 2)]))
    recs.append(probe("boxes+player+2clear",
                      [CORE + ["player"] + list(c) for c in itertools.combinations(CLEARS, 2)]))
    recs.append(probe("boxes+player+3clear",
                      [CORE + ["player"] + list(c) for c in itertools.combinations(CLEARS, 3)]))
    recs.append(probe("all-vars", [CORE + ["player"] + CLEARS]))
    json.dump(recs, open("swap_sweep.json", "w"), indent=2)
    print("WROTE swap_sweep.json")
