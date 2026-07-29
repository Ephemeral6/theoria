"""Differential: recheck rule set `step` vs cold-start-a2's compiled predictors.

Read-only against cold-start-a2 (sys.dont_write_bytecode is set before any
import so no __pycache__ is created there).
"""

import sys
sys.dont_write_bytecode = True

import importlib.util
import json
import os

RIG = r"C:\Users\user\Desktop\theoria\.worktrees\e5-cert-recheck\engine-rig"
A2 = r"C:\Users\user\Desktop\theoria\cold-start-a2\theory"
sys.path.insert(0, RIG)

from recheck.ruleset import load_ruleset  # noqa: E402


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


world = load_module("a2_world_theory", os.path.join(A2, "generated", "theory.py"))
holed = load_module("a2_holed_theory", os.path.join(A2, "generated_holed", "theory.py"))

CASES = os.path.join(RIG, "recheck", "cases")


def parse_cell(name):
    r, c = name.split(",")
    return (int(r), int(c))


def compare(rs_path, mod, label):
    rs = load_ruleset(rs_path)
    names = [v.name for v in rs.variables]
    assert names == ["button", "cart", "door"], names
    states = rs.states()
    print("== %s (%s)" % (label, os.path.basename(rs_path)))
    print("   variables=%s n_states=%d actions=%s n_rules=%d"
          % (names, len(states), list(rs.actions), len(rs.rules)))

    # --- init
    rs_init = rs.init[0]
    t_init = mod.initial_state()
    init_ok = (rs_init == (t_init.Button_colour,
                           "%d,%d" % t_init.Cart_pos,
                           "yes" if t_init.Door_present else "no"))
    print("   init: ruleset=%s  theory=(%s,%s,%s)  MATCH=%s"
          % (rs_init, t_init.Button_colour, t_init.Cart_pos,
             t_init.Door_present, init_ok))

    def to_state(s):
        button, cart, door = s
        return mod.State(
            Button_pos=(1, 1), Button_colour=button,
            Cart_pos=parse_cell(cart), Cart_colour=6,
            Door_pos=(6, 4), Door_colour=5, Door_present=(door == "yes"))

    # --- board literal
    board_tbl = rs.tables["board"]
    board_bad = []
    for r in range(9):
        for c in range(9):
            got = board_tbl.lookup(("%d,%d" % (r, c),))
            if got != mod.BOARD[r][c]:
                board_bad.append(((r, c), got, mod.BOARD[r][c]))
    print("   BOARD literal: %d/81 cells agree, %d differ" % (81 - len(board_bad), len(board_bad)))
    for b in board_bad[:10]:
        print("      board mismatch", b)

    # --- rendered / free, over every state x every cell
    rendered = rs.scope.macros["rendered"]
    free = rs.scope.macros["free"]
    r_bad = f_bad = 0
    r_ex = []
    for s in states:
        ts = to_state(s)
        grid = mod.render(ts)
        for r in range(9):
            for c in range(9):
                got = rendered(s, None, ("%d,%d" % (r, c),))
                if got != grid[r][c]:
                    r_bad += 1
                    if len(r_ex) < 5:
                        r_ex.append((rs.render_state(s), (r, c), got, grid[r][c]))
                gotf = free(s, None, ("%d,%d" % (r, c),))
                if gotf != mod._free(ts, (r, c)):
                    f_bad += 1
    total = len(states) * 81
    print("   rendered(): %d/%d agree, %d differ" % (total - r_bad, total, r_bad))
    print("   free():     %d/%d agree, %d differ" % (total - f_bad, total, f_bad))
    for e in r_ex:
        print("      rendered mismatch", e)

    # --- goal
    g_bad = [s for s in states if rs.goal(s) != mod.is_goal(to_state(s))]
    print("   is_goal: %d/%d agree, %d differ" % (len(states) - len(g_bad), len(states), len(g_bad)))

    # --- step, over the whole product
    dirmap = {"up": "up", "down": "down", "left": "left", "right": "right"}
    agree = disagree = 0
    fired_bad = 0
    examples = []
    for s in states:
        ts = to_state(s)
        for a in rs.actions:
            try:
                nxt = rs.step(s, a)
            except Exception as exc:  # noqa: BLE001
                disagree += 1
                if len(examples) < 8:
                    examples.append((rs.render_state(s), a, "RULESET-ERROR %s" % exc))
                continue
            act = ("push", "Cart", dirmap[a])
            try:
                tn = mod.step(ts, act)
                tn_tuple = (tn.Button_colour, "%d,%d" % tn.Cart_pos,
                            "yes" if tn.Door_present else "no")
            except Exception as exc:  # noqa: BLE001
                disagree += 1
                if len(examples) < 8:
                    examples.append((rs.render_state(s), a, "THEORY-ERROR %s" % exc))
                continue
            if nxt == tn_tuple:
                agree += 1
            else:
                disagree += 1
                if len(examples) < 8:
                    examples.append((rs.render_state(s), a, nxt, tn_tuple))
            rf = sorted(rs.fired(s, a))
            tf = sorted(mod.fired(ts, act))
            if rf != tf:
                fired_bad += 1
                if len(examples) < 12:
                    examples.append(("FIRED", rs.render_state(s), a, rf, tf))
    print("   step: %d agree, %d disagree (out of %d state-action pairs)"
          % (agree, disagree, len(states) * len(rs.actions)))
    print("   fired-rule-name sets differing: %d" % fired_bad)
    for e in examples:
        print("      ", e)

    # --- obligations
    ob = rs.obligations()
    print("   obligations:", json.dumps(ob.conditions, sort_keys=True))
    for k, v in ob.witnesses.items():
        print("      ", k, v[:3])
    print()
    return disagree + len(g_bad) + len(board_bad) + r_bad + f_bad + (0 if init_ok else 1)


bad = 0
bad += compare(os.path.join(CASES, "a2-world.rules.json"), world, "a2-world vs generated/")
bad += compare(os.path.join(CASES, "a2-holed.rules.json"), holed, "a2-holed vs generated_holed/")

# cross-check: a2-world must NOT match the holed predictor and vice versa
rs = load_ruleset(os.path.join(CASES, "a2-world.rules.json"))
diff = 0
for s in rs.states():
    ts = holed.State(Button_pos=(1, 1), Button_colour=s[0],
                     Cart_pos=parse_cell(s[1]), Cart_colour=6,
                     Door_pos=(6, 4), Door_colour=5, Door_present=(s[2] == "yes"))
    for a in rs.actions:
        n = rs.step(s, a)
        t = holed.step(ts, ("push", "Cart", a))
        if n != (t.Button_colour, "%d,%d" % t.Cart_pos, "yes" if t.Door_present else "no"):
            diff += 1
print("sanity: a2-world rules vs HOLED predictor -> %d disagreements (must be > 0)" % diff)

print("TOTAL DISCREPANCY COUNT:", bad)
