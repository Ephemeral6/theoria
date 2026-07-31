"""Read-only: which leaf fields of BUDGET_TABLE.json differ from a fresh build()?

Usage: python fielddiff.py <path-to-a-checkout>
Imports that checkout's freeze/build_budget_table.py, calls build(), and diffs
against that checkout's committed freeze/BUDGET_TABLE.json. Writes nothing.
"""
import importlib.util
import json
import os
import sys

WT = os.path.abspath(sys.argv[1])
spec = importlib.util.spec_from_file_location(
    "bbt", os.path.join(WT, "freeze", "build_budget_table.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print("REPO seen by the module: %s" % m.REPO)
print("pool resolves to: %r" % m.resolve_pool("proxy/var/spend_gate.jsonl"))

fresh = m.build()
disk = json.load(open(os.path.join(WT, "freeze", "BUDGET_TABLE.json"),
                      encoding="utf-8"))


def walk(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            walk(a.get(k, "<absent>"), b.get(k, "<absent>"), path + "/" + str(k))
        return
    if a != b:
        sa, sb = repr(a), repr(b)
        if len(sa) > 90:
            sa = sa[:90] + "..."
        if len(sb) > 90:
            sb = sb[:90] + "..."
        print("  %-58s on-disk=%s  fresh=%s" % (path, sa, sb))


print("\n--- leaf fields where committed BUDGET_TABLE.json != fresh build() ---")
for section in sorted(set(disk) | set(fresh)):
    if section == "generated_from":
        continue
    if disk.get(section) != fresh.get(section):
        print("[%s]" % section)
        walk(disk.get(section), fresh.get(section), section)
