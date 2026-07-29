"""One-off: build KNOWN_GAPS.json's `entries` from the tree + the V11 census.

Kept in the run directory rather than in negctl/ on purpose. A pin that can be
regenerated on demand is a pin nobody has to think about before editing, which is
the failure `worldgen/qc/KNOWN_MISS.json._how_to_change_it` warns about. This
script produced the file once; changing an entry afterwards is a hand edit.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
NEGCTL = os.path.join(os.path.dirname(os.path.dirname(HERE)), "negctl")
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, NEGCTL)
import criterion, probe, calibrate

OWNERS = {
    "engine-rig": "track: engine-rig",
    "a0-spike": "track: engine-rig (its A0 cold start)",
    "theory-compiler": "track: theory-compiler",
    "cold-start-a0": "track: theory-compiler (off limits to engine-rig)",
    "cold-start-a2": "track: theory-compiler (A2 cold start)",
    "cold-start-a3": "track: theory-compiler (A3 transfer)",
    "arc-recon": "shared ground -- the pile cut and the API access check",
    "proxy": "lane: proxy / spend gate",
    "worldgen": "lane: worldgen", "fuzzlab": "lane: worldgen",
    "exam": "lane: exam / battery", "battery": "lane: exam / battery",
    "figures": "lane: figures / release", "papers": "lane: figures / release",
    "release": "lane: figures / release",
    "ablation-arm": "lane: arms", "baseline-arms": "lane: arms",
    "theoria-arm": "lane: arms",
    "monitor": "lane: monitor",
    "verify-lab": "lane: verify (RES-3) -- this probe's own territory",
}

index = criterion.Index.build(REPO)
verdicts = criterion.Verdicts(
    a=criterion.scan_tests(index, absence=True),
    a_strict=criterion.scan_tests(index, absence=False),
    b=criterion.scan_selftests(index),
    naive=criterion.scan_naive(index))

census = {}
for row in calibrate.parse_census():
    rel = calibrate.entry_path(row["entry"], REPO)
    if rel and rel.endswith(".py"):
        census.setdefault(rel, []).append(calibrate.gold_of(row["has_negctl"]))

entries = {}
for rel in probe.enumerate_entry_points(index):
    top = rel.split("/")[0]
    measured = verdicts.verdict(rel, "A-B")
    rec = {"verdict": measured,
           "owner": OWNERS.get(top, "UNASSIGNED -- %s" % top)}
    gold = census.get(rel)
    if gold:
        rec["census_v11"] = "/".join(sorted(set(gold)))
        if measured == "absent" and any(g in ("yes", "partial") for g in gold):
            rec["note"] = ("V11's auditors credited this entry point with a negative "
                           "control the criterion cannot see. Pinned absent so the "
                           "probe is quiet about it; this is a KNOWN FALSE NEGATIVE "
                           "of the criterion, not a gap in the territory.")
        elif measured == "absent":
            rec["note"] = "V11 agrees: no executable demonstration that this can fail."
    elif measured == "absent":
        rec["note"] = "not surveyed by V11; the criterion finds no negative control."
    entries[rel] = rec

with open(os.path.join(HERE, "entries.generated.json"), "w",
          encoding="utf-8", newline="\n") as fh:
    json.dump(entries, fh, indent=2, sort_keys=True, ensure_ascii=False)
    fh.write("\n")
print("%d entries; %d absent; %d flagged as known false negatives"
      % (len(entries),
         sum(1 for v in entries.values() if v["verdict"] == "absent"),
         sum(1 for v in entries.values() if "KNOWN FALSE NEGATIVE" in v.get("note", ""))))
