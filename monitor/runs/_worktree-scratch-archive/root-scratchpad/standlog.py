"""Histogram of standing.py skip reasons per agent, plus the OPS starvation view."""
import collections
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "monitor", "standing.log")

per = collections.defaultdict(collections.Counter)
starts = collections.Counter()
first, last = None, None
for line in open(LOG, encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line:
        continue
    ts = line.split(" ", 1)[0]
    if first is None:
        first = ts
    last = ts
    m = re.match(r"\S+ skip (\S+): (.*?) \[", line)
    if m:
        agent, why = m.group(1), m.group(2)
        why = re.sub(r"\d+", "N", why)
        per[agent][why] += 1
        continue
    m = re.match(r"\S+ START (\S+) ", line)
    if m:
        starts[m.group(1)] += 1

print("log window: %s .. %s" % (first, last))
print()
for agent in sorted(set(list(per) + list(starts))):
    print("%-8s starts=%d" % (agent, starts[agent]))
    for why, n in per[agent].most_common(6):
        print("    %4d  %s" % (n, why))
print()
print("== every line mentioning OPS-M ==")
for line in open(LOG, encoding="utf-8", errors="replace"):
    if "OPS-M" in line:
        print("  " + line.strip())
