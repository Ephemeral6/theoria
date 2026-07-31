import json
import sys

trees = ["master", "v21", "v25"]
rows = {}
for t in trees:
    rows[t] = {}
    with open("C:/Users/user/AppData/Local/Temp/adv4_%s.jsonl" % t) as fh:
        for line in fh:
            d = json.loads(line)
            rows[t][d["id"]] = d

ids = sorted(rows["master"])
# oracle must agree across trees (it is tree-independent) -- assert it
for i in ids:
    assert rows["master"][i]["leaky"] == rows["v25"][i]["leaky"] == \
        rows["v21"][i]["leaky"], i
n = len(ids)
print("sheets: %d" % n)
leaky = [i for i in ids if rows["master"][i]["leaky"]]
clean = [i for i in ids if not rows["master"][i]["leaky"]]
print("leaky by oracle: %d   clean by oracle: %d" % (len(leaky), len(clean)))
print()
print("%-8s %8s %8s %8s %8s %8s %8s" %
      ("tree", "fires", "TP", "FP", "FN", "recall", "precis"))
for t in trees:
    f = [i for i in ids if rows[t][i]["fired"]]
    tp = len([i for i in f if rows[t][i]["leaky"]])
    fp = len(f) - tp
    fn = len(leaky) - tp
    print("%-8s %8d %8d %8d %8d %8.3f %8.3f" %
          (t, len(f), tp, fp, fn,
           tp / len(leaky) if leaky else 0,
           tp / len(f) if f else 0))
print()
print("DOMINANCE  v21 fires => v25 fires :",
      all(rows["v25"][i]["fired"] for i in ids if rows["v21"][i]["fired"]),
      " (v21 fires on %d)" % sum(rows["v21"][i]["fired"] for i in ids))
print("           v25 fires => v21 fires :",
      all(rows["v21"][i]["fired"] for i in ids if rows["v25"][i]["fired"]))
print("           master fires => v25 fires :",
      all(rows["v25"][i]["fired"] for i in ids if rows["master"][i]["fired"]))
print()
lost = [i for i in ids if rows["master"][i]["fired"]
        and not rows["v25"][i]["fired"]]
print("MASTER FIRES BUT V25 SILENT: %d sheets" % len(lost))
lost_leaky = [i for i in lost if rows["master"][i]["leaky"]]
print("   of which genuinely leaky by oracle: %d (%.1f%%)"
      % (len(lost_leaky), 100.0 * len(lost_leaky) / len(lost) if lost else 0))
print("   of which NOT leaky (master false positive): %d"
      % (len(lost) - len(lost_leaky)))
print()
gained = [i for i in ids if rows["v25"][i]["fired"]
          and not rows["master"][i]["fired"]]
print("V25 FIRES BUT MASTER SILENT: %d sheets" % len(gained))
gl = [i for i in gained if rows["master"][i]["leaky"]]
print("   of which genuinely leaky by oracle: %d (%.1f%%)"
      % (len(gl), 100.0 * len(gl) / len(gained) if gained else 0))
print()
print("--- sample of the master-fires/v25-silent set that IS leaky ---")
for i in lost_leaky[:3]:
    d = rows["master"][i]
    print("  id=%d loo=%.3f base=%.3f rule=%s" % (i, d["loo"], d["base"], d["rule"]))
print("--- sample of the master-fires/v25-silent set that is NOT leaky ---")
for i in [x for x in lost if x not in lost_leaky][:3]:
    d = rows["master"][i]
    print("  id=%d loo=%.3f base=%.3f rule=%s" % (i, d["loo"], d["base"], d["rule"]))
