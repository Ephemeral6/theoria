import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return json.load(fh)


def row(r):
    b, g = r["base"], r["guarded"]
    return {
        "instance": r["instance"], "config": r["config_tag"], "search": r["search"],
        "expanded_base": b["expanded"], "expanded_guarded": g["expanded"],
        "delta": r["delta"],
        "h_init_base": b["initial_h"], "h_init_guarded": g["initial_h"],
        "translator_operators": [b["operators"], g["operators"]],
        "dead_ends": [b["dead_ends"], g["dead_ends"]],
        "expanded_until_last_jump": [b.get("expanded_until_last_jump"),
                                     g.get("expanded_until_last_jump")],
        "distinct_states_below_Cstar": [b.get("distinct_below_Cstar"),
                                        g.get("distinct_below_Cstar")],
        "logs": [b["log"], g["log"]],
    }


out = {
    "what": "independent verification of the two ipdb and four lmcut counterexamples "
            "to DEADLOCK_CLAIM.md's '0-3 expansions on an admissible heuristic'",
    "fast_downward": "24.06+ rev 7120aa0",
    "utc": subprocess.run([sys.executable, "-c",
                           "import datetime;print(datetime.datetime.now(datetime.timezone.utc)"
                           ".strftime('%Y-%m-%dT%H:%M:%SZ'))"],
                          capture_output=True, text=True).stdout.strip(),
    "pinned_patterns": [row(r) for r in load("pinned_patterns.json")],
    "swap_fixed_pattern_sweep": [
        {"tag": r["tag"], "n_patterns": r["n_patterns"],
         "h_init": [r["base"]["initial_h"], r["guarded"]["initial_h"]],
         "expanded": [r["base"]["expanded"], r["guarded"]["expanded"]]}
        for r in load("swap_sweep.json")],
    "swap_random_large_patterns": [
        {"tag": r["tag"], "pattern": r["pattern_names"],
         "h_init": [r["base"]["initial_h"], r["guarded"]["initial_h"]],
         "expanded": [r["base"]["expanded"], r["guarded"]["expanded"]]}
        for r in load("swap_bigpatterns.json")],
    "swap_winning_pattern": load("swap_winning_pattern.json"),
    "swap_ipdb_budget_ladder": [row(r) for r in load("swap_budget.json")],
    "far9_ipdb_budget_ladder": [row(r) for r in load("far9_budget.json")],
    "lmcut_rows": [row(r) for r in load("lmcut_rows.json")],
    "three_far8_rebuilt": [row(r) for r in load("three-far8_v2.json")],
    "three_far8_provenance": load("three-far8_provenance.json"),
    "dead_sets": load("deadsets.json"),
}
with open(os.path.join(HERE, "SUMMARY.json"), "w", encoding="utf-8", newline="\n") as fh:
    json.dump(out, fh, indent=2, sort_keys=False)
    fh.write("\n")
print("wrote SUMMARY.json", os.path.getsize(os.path.join(HERE, "SUMMARY.json")), "bytes")
