"""How strong is the leak the merged gate is silent about?
Leave-one-out accuracy of the sheet-visible feature "does another item share my
tags value?" on CASE1, using v21's own a12_independent_audit framing."""
from collections import Counter
UNIQ = ["zephyr","kumquat","obsidian","marzipan","trellis",
        "walrus","flotsam","gherkin","pumice","yardarm"]
rows  = [(f"ya{k}", "alpha", "yes") for k in range(5)]
rows += [(f"yb{k}", "bravo", "yes") for k in range(5)]
rows += [(f"nz{k}", w, "no") for k, w in enumerate(UNIQ)]
n = len(rows)
ans = {i: a for i, (_, _, a) in enumerate(rows)}
val = {i: v for i, (_, v, _) in enumerate(rows)}

def feature(i, pool):
    """Sheet-visible: is this item's tags value shared with another item?"""
    return sum(1 for j in pool if val[j] == val[i]) > 1

# baseline: majority class
base = Counter(ans.values()).most_common(1)[0][1] / n
correct = 0
for i in range(n):
    pool = [j for j in range(n) if j != i]
    tbl = {}
    for j in pool:
        tbl.setdefault(feature(j, pool), Counter())[ans[j]] += 1
    pred = tbl.get(feature(i, pool), Counter())
    if pred and pred.most_common(1)[0][0] == ans[i]:
        correct += 1
print("n                       :", n)
print("majority baseline       : %.3f" % base)
print("LOO acc of 'value shared': %.3f  (%d/%d)" % (correct / n, correct, n))
print()
print("Same feature on the LIVE v11-handover-a0 optimal_action group (n=8):")
live = [("stile","false"),("flume","true"),("warren","true"),("cairn","false"),
        ("kiln","true"),("warren","true"),("flume","true"),("kiln","true")]
m = len(live)
lv = {i: live[i][0] for i in range(m)}
la = {i: live[i][1] for i in range(m)}
c = 0
for i in range(m):
    pool = [j for j in range(m) if j != i]
    tbl = {}
    for j in pool:
        sh = sum(1 for k in pool if lv[k] == lv[j]) > 1
        tbl.setdefault(sh, Counter())[la[j]] += 1
    shi = sum(1 for k in pool if lv[k] == lv[i]) > 1
    p = tbl.get(shi, Counter())
    if p and p.most_common(1)[0][0] == la[i]:
        c += 1
print("  majority baseline     : %.3f" % (Counter(la.values()).most_common(1)[0][1]/m))
print("  LOO acc               : %.3f  (%d/%d)" % (c/m, c, m))
