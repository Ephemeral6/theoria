"""Q7: forbid every action in every catalogue world; look for crashes,
non-termination, wrong reachability, and silently-broken downstream analyses."""
import signal, sys, time
from worldgen.core import explorer, reversibility as rev, solvability, truth
from worldgen.core.world import GridWorld
from worldgen.core.types import ACTIONS
from worldgen.generate import CATALOGUE
from worldgen import mutate

print("%-24s %-6s %-7s %-7s %-8s %-6s %s" %
      ("world", "act", "states", "solv", "corr", "walk", "notes"))
for spec in CATALOGUE:
    for act in ACTIONS:
        try:
            mspec = mutate._apply_one(spec, {"op": "forbid_action", "action": act})
        except Exception as exc:
            print("%-24s %-6s SKIP %r" % (spec.world_id, act, exc)); continue
        notes = []
        t0 = time.time()
        try:
            w = GridWorld(mspec)
            st = w.reachable()
            solve = solvability.report(w, diagnose=False)
            corr = truth.rule_correspondence(w)
            states, actions = explorer.explore(w)
            inv = truth.check_invariants(w, st)
            stamp = rev.audit(w, truth.rule_table(w))
            fds = truth.frame_determines_state(w, st)
        except Exception as exc:
            print("%-24s %-6s EXCEPTION %r" % (spec.world_id, act, exc)); continue
        dt = time.time() - t0
        if not corr["agrees"]:
            notes.append("CORR:%s/%s" % (corr["declared_never_fires"], corr["fired_undeclared"]))
        bad = [i["name"] for i in inv if i.get("verified") and not i.get("holds")]
        if bad:
            notes.append("INV_VIOLATED:%s" % bad)
        if not fds["injective"]:
            notes.append("FRAME_COLLISION")
        if stamp["claim_disagreements"]:
            notes.append("CLAIM:%s" % stamp["claim_disagreements"])
        if dt > 20:
            notes.append("SLOW:%.1fs" % dt)
        print("%-24s %-6s %-7d %-7s %-8s %-6d %s" %
              (spec.world_id, act, len(st), solve["solvable"], corr["agrees"],
               len(actions) - 1, " ".join(notes)))
