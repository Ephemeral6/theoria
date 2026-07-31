import importlib.util, json, os, sys, copy
WT = sys.argv[1]
spec = importlib.util.spec_from_file_location("bbt", os.path.join(WT, "freeze", "build_budget_table.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

print("REPO =", m.REPO)
print("resolve_pool ->", m.resolve_pool("proxy/var/spend_gate.jsonl"))

# --- A. live pool vs committed pinned values
committed = json.load(open(os.path.join(WT, "freeze", "BUDGET_TABLE.json"), encoding="utf-8"))
live = m.build()
cp, lp = committed["pool"], live["pool"]
print("\n== A. pool section, committed vs live (pool reachable) ==")
for k in sorted(set(cp) | set(lp)):
    a, b = cp.get(k, "<absent>"), lp.get(k, "<absent>")
    if isinstance(a, (dict, list)) or isinstance(b, (dict, list)):
        same = a == b; a = b = "<container>" if same else "<container-DIFFERS>"
    if a != b or "DIFFERS" in str(a):
        print("  %-28s committed=%r live=%r" % (k, a, b))
print("  committed lines=%r live lines=%r" % (cp.get("lines"), lp.get("lines")))
print("  abspath_is_main_checkout: committed=%r live=%r" % (cp.get("abspath_is_main_checkout"), lp.get("abspath_is_main_checkout")))

# --- B. which top-level sections move
strip = lambda d: {k: v for k, v in d.items() if k != "generated_from"}
old, new = strip(committed), strip(live)
print("\n== B. sections that moved (pool reachable) ==", sorted(k for k in set(old)|set(new) if old.get(k)!=new.get(k)))

# --- C. simulate the queue's %TEMP% checkout: resolve_pool -> None
m.resolve_pool = lambda rel: None
live_np = m.build()
print("\n== C. pool-absent build ==")
print("  pool section:", json.dumps(live_np["pool"], ensure_ascii=False))
print("  sections that moved vs committed:", sorted(k for k in set(strip(committed))|set(strip(live_np)) if strip(committed).get(k)!=strip(live_np).get(k)))

# --- D. can a pool-ABSENT-generated table ever be green with a pool present?
np_text = json.dumps(live_np, indent=2, sort_keys=True, ensure_ascii=False)
print("\n== D. table generated pool-ABSENT, compared against a pool-PRESENT build ==")
a, b = strip(json.loads(np_text)), strip(live)
print("  sections that moved:", sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k)))
