import json, os, run

A = run.ATTACKS
TARGETS = [
    ("three-far8", os.path.join(A, "work", "a3", "three-far8")),
    ("hunt0021", os.path.join(A, "work", "a7", "hunt0021")),
    ("hunt0037", os.path.join(A, "work", "a7", "hunt0037")),
    ("hunt0070", os.path.join(A, "work", "a7", "hunt0070")),
]
TB = {
    "astar-default": "astar(lmcut())",
    "tb-h": "eager(tiebreaking([sum([g(),lmcut()]),lmcut()]),reopen_closed=true,f_eval=sum([g(),lmcut()]))",
    "tb-g": "eager(tiebreaking([sum([g(),lmcut()]),g()]),reopen_closed=true,f_eval=sum([g(),lmcut()]))",
    "tb-f-only": "eager(tiebreaking([sum([g(),lmcut()])]),reopen_closed=true,f_eval=sum([g(),lmcut()]))",
}
recs = []
for name, d in TARGETS:
    bp = os.path.join(d, "%s.pddl" % name)
    gd = os.path.join(d, "singleton", "sokoban_guarded_singleton_domain.pddl")
    gp = os.path.join(d, "singleton", "%s_guarded_singleton.pddl" % name)
    print("===", name)
    for tag, s in TB.items():
        r = run.pair(name, bp, gd, gp, s, tag)
        for side in ("base", "guarded"):
            m = r[side]
            if m["expanded_until_last_jump"] is not None:
                m["distinct_below_Cstar"] = (m["expanded_until_last_jump"]
                                             - (m["reopened_until_last_jump"] or 0))
        print("      until-last-jump  %s -> %s   distinct<C*  %s -> %s"
              % (r["base"]["expanded_until_last_jump"], r["guarded"]["expanded_until_last_jump"],
                 r["base"].get("distinct_below_Cstar"), r["guarded"].get("distinct_below_Cstar")))
        recs.append(r)
json.dump(recs, open("lmcut_rows.json", "w"), indent=2)
print("WROTE lmcut_rows.json")
