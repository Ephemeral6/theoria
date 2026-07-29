"""Q4 continued: (a) can one mechanism's render ever paint over another's cells
(which is what a cross-mechanism frame-read dependency would need)?
(b) do mutant-only claims ever exist, and can they be flagged?
(c) do invariant STATEMENTS change without the claim being flagged?
"""
import json
from worldgen.core import truth
from worldgen.core.world import GridWorld
from worldgen.core.types import AGENT, FLOOR, WALL
from worldgen import mutate
from worldgen.generate import CATALOGUE, BY_ID

print("=== (a) does any mechanism's render overwrite another's live cell? ===")
bad = 0
for spec in CATALOGUE:
    w = GridWorld(spec)
    for state in w.reachable():
        # render each mechanism alone, then together, and diff
        solo = {}
        for m in w.mechanisms:
            f = [[FLOOR] * spec.width for _ in range(spec.height)]
            m.render(spec, w.mine(m), w.view(m, state), f)
            for r in range(spec.height):
                for c in range(spec.width):
                    if f[r][c] != FLOOR:
                        solo.setdefault((r, c), []).append((m.name, f[r][c]))
        full = w.render(state)
        for cell, painters in solo.items():
            if len(painters) > 1:
                print("  OVERLAP %s %s %s" % (spec.world_id, cell, painters)); bad += 1
            r, c = cell
            if full[r][c] != painters[-1][1] and cell != state.agent and full[r][c] != WALL:
                print("  OVERWRITTEN %s %s solo=%s full=%d"
                      % (spec.world_id, cell, painters, full[r][c])); bad += 1
        if bad > 8:
            break
    if bad > 8:
        break
print("  overlaps/overwrites found:", bad)

print("\n=== (b)/(c) mutant-only claims and statement drift ===")
blob = json.load(open("worldgen/out/worlds/MUTATIONS.json", encoding="utf-8"))
rows = {r["variant_id"]: r for r in blob["mutations"]}
for eid, edit in sorted(mutate.MUTANT_BY_ID.items()):
    b = GridWorld(BY_ID[edit.base]); m = GridWorld(edit.spec())
    bi = {i["name"]: i for i in truth.invariant_table(b)}
    mi = {i["name"]: i for i in truth.invariant_table(m)}
    added = sorted(set(mi) - set(bi)); removed = sorted(set(bi) - set(mi))
    drift = sorted(n for n in set(bi) & set(mi)
                   if bi[n]["statement"] != mi[n]["statement"])
    row = rows[eid]
    reex = set(row["collateral"]["claims_to_reexamine"])
    unflagged = [n for n in drift if n not in reex
                 and n not in row["collateral"]["claims_now_false"]]
    deps = blob["claim_dependencies"][edit.base]["claims"]
    unrepresented = [n for n in added if n not in deps]
    if added or removed or drift:
        print("%-12s added=%s removed=%s statement_drift=%s UNFLAGGED_DRIFT=%s "
              "ADDED_WITH_NO_DEP_ROW=%s"
              % (eid, added, removed, drift, unflagged, unrepresented))
