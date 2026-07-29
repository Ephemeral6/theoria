"""The same *large* pattern on both tasks.

iPDB's winning collections are `{b1, b2, player}` plus 7 (base) or 8 (guarded)
`clear` variables -- read off the PDB sizes: base max 1362944 = 22*22*22*2^7,
guarded max 1103872 = 14*14*22*2^8.  So the honest fixed-pattern test is at that
size, not at systematic(2)/(3), whose patterns are far too small to see anything
on either side.  Random patterns, drawn once, evaluated on both tasks.
"""
import json, random, sys
import run as R
import swap_sweep as S

rng = random.Random(20260729)
recs = []
for k in (6, 7, 8):
    inf_g = inf_b = 0
    for trial in range(12):
        names = S.CORE + ["player"] + rng.sample(S.CLEARS, k)
        tag = "big%d-%02d" % (k, trial)
        r = S.probe(tag, [names])
        r["pattern_names"] = names
        recs.append(r)
        inf_b += r["base"]["initial_h"] == "infinity"
        inf_g += r["guarded"]["initial_h"] == "infinity"
    print("== k=%d clears: h(init)=infinity on base %d/12, on guarded %d/12"
          % (k, inf_b, inf_g), flush=True)
json.dump(recs, open("swap_bigpatterns.json", "w"), indent=2)
print("WROTE swap_bigpatterns.json")
