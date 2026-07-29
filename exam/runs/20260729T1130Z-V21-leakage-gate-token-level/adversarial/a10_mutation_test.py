"""A10 -- mutation testing of exam/tests/test_leakage_tokens.py.

The real exam/leakage.py is never written to.  Its *source text* is read, a
mutation is applied in memory, the result is exec'd into a module object that is
installed as `exam.leakage`, and the test module is then imported fresh so its
`from exam import leakage` binds the mutant.  Each test function is run and its
pass/fail recorded.

A test that passes against a broken implementation is worse than no test.
"""
import importlib
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, REPO)

SRC = os.path.join(REPO, "exam", "leakage.py")
TESTS = os.path.join(REPO, "exam", "tests", "test_leakage_tokens.py")
ORIGINAL = open(SRC, encoding="utf-8").read()

MUTATIONS = [
    ("BASELINE (unmutated)", []),
    ("A: token check deleted",
     [("        findings.extend(_token_hits_within(labelled, answer_of, tolerance,\n"
       "                                           field_name, floor))",
       "        pass  # token check deleted")]),
    ("B: _token_hits_within stubbed to []",
     [("    findings: List[Dict[str, Any]] = []\n    for token, holders in sorted(carriers.items()):",
       "    findings: List[Dict[str, Any]] = []\n    return findings\n    for token, holders in sorted(carriers.items()):")]),
    ("C: both holder guards removed",
     [("        if len(holders) < 2 or len(holders) == n:\n            continue",
       "        if False:\n            continue")]),
    ("D: `len(holders) == n` guard removed",
     [("        if len(holders) < 2 or len(holders) == n:",
       "        if len(holders) < 2:")]),
    ("E: `len(holders) < 2` guard removed",
     [("        if len(holders) < 2 or len(holders) == n:",
       "        if len(holders) == n:")]),
    ("F: MIN_TOKEN = 1",
     [("MIN_TOKEN = 3", "MIN_TOKEN = 1")]),
    ("G: MIN_TOKEN = 99 (no token ever survives)",
     [("MIN_TOKEN = 3", "MIN_TOKEN = 99")]),
    ("H: MIN_LABELLED = 1",
     [("MIN_LABELLED = 4", "MIN_LABELLED = 1")]),
    ("I: MIN_LABELLED = 99 (no label set derived)",
     [("MIN_LABELLED = 4", "MIN_LABELLED = 99")]),
    ("J: derive_label_sets reverted to the 60% floor",
     [("        if len(labels) < MIN_LABELLED:", "        if len(labels) < 0.6 * n_items:")]),
    ("K: singleton counting removed",
     [('            declined.append({"field": field_name, "singleton_values": dropped,\n'
       '                             "scored_values": len(usable)})',
       "            pass  # singletons discarded again")]),
    ("K2: constant/absent fields silently skipped again",
     [('            declined.append({\n'
       '                "field": field_name, "scored_values": 0,\n'
       '                "declined": "absent" if not buckets else "constant"})\n'
       "            continue",
       "            continue")]),
    ("K3: unscorable groups return an empty pair again",
     [('        return [], [{"field": None, "group_items": len(labelled),\n'
       '                     "declined": "fewer than 4 labelled items", "scored_values": 0}]',
       "        return [], []")]),
    ("K4: coverage dropped from the report",
     [('    if unscored:\n        report["metadata_unscored"] = unscored',
       "    pass  # coverage not reported")]),
    ("K5: item_id removed from the allowlist",
     [('METADATA_FIELDS = ("points", "tags", "kind", "item_id")',
       'METADATA_FIELDS = ("points", "tags", "kind")')]),
    ("L: degenerate-subset guard removed (pre-V21 behaviour)",
     [("            if (len(scored) >= 2 and rate > tolerance\n"
       "                    and rate > floor_here + 1e-9):",
       "            if rate > tolerance and rate > floor + 1e-9:")]),
    ("M: the `continue` bug reintroduced",
     [("            if (len(scored) >= 2 and rate > tolerance\n"
       "                    and rate > floor_here + 1e-9):",
       "            if len(scored) < 2:\n                continue\n"
       "            if rate > tolerance and rate > floor_here + 1e-9:")]),
    ("N: subset floor assigned back to the group floor",
     [("            floor_here = max(\n"
       "                floor, scored.most_common(1)[0][1] / seen if seen else 0.0)",
       "            floor = floor_here = max(\n"
       "                floor, scored.most_common(1)[0][1] / seen if seen else 0.0)")]),
    ("O: METADATA_FIELDS narrowed to ('points',)",
     [('METADATA_FIELDS = ("points", "tags", "kind", "item_id")',
       'METADATA_FIELDS = ("points",)')]),
    ("P: token-level floor comparison weakened to >=",
     [("        if rate > tolerance and rate > floor + 1e-9:",
       "        if rate > tolerance and rate >= floor:")]),
    ("Q: field_tokens always returns the empty set",
     [("    text = canonical(value).lower()\n"
       "    return {t for t in _TOKEN_SPLIT.split(text) if len(t) >= MIN_TOKEN}",
       "    return set()")]),
    ("R: floor contamination, spelled to EVADE test 3's source grep",
     [("            floor_here = max(\n"
       "                floor, scored.most_common(1)[0][1] / seen if seen else 0.0)",
       "            floor = floor_here = max(\n"
       "                floor, scored.most_common(1)[0][1] / seen if seen else 0.0)")]),
    ("S: floor contamination, spelled the exact way test 3 greps for",
     [("            floor_here = max(\n"
       "                floor, scored.most_common(1)[0][1] / seen if seen else 0.0)",
       "            floor = max(\n"
       "                floor, scored.most_common(1)[0][1] / seen if seen else 0.0)\n"
       "            floor_here = floor")]),
]


def load_mutant(text):
    mod = types.ModuleType("exam.leakage")
    mod.__file__ = SRC
    mod.__package__ = "exam"
    exec(compile(text, SRC, "exec"), mod.__dict__)
    return mod


def run(name, patches):
    text = ORIGINAL
    for old, new in patches:
        if old not in text:
            return name, None, "PATCH DID NOT APPLY"
        text = text.replace(old, new, 1)
    import exam
    for m in [m for m in sys.modules if m.startswith("exam")]:
        if m not in ("exam", "exam.model"):
            del sys.modules[m]
    try:
        mutant = load_mutant(text)
    except Exception as exc:                      # pragma: no cover
        return name, None, "IMPORT ERROR %s" % exc
    sys.modules["exam.leakage"] = mutant
    exam.leakage = mutant

    spec = importlib.util.spec_from_file_location("tlt_%d" % abs(hash(name)), TESTS)
    tm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tm)

    results = {}
    for fn in sorted(d for d in dir(tm) if d.startswith("test_")):
        try:
            getattr(tm, fn)()
            results[fn] = "pass"
        except Exception as exc:
            results[fn] = "FAIL(%s)" % type(exc).__name__
    return name, results, None


base_name, baseline, err = run(*MUTATIONS[0])
assert baseline and all(v == "pass" for v in baseline.values()), baseline
names = sorted(baseline)
short = {n: n.replace("test_", "")[:38] for n in names}

print("Tests (baseline all pass):")
for i, n in enumerate(names):
    print("  %2d  %s" % (i, n))
print()
print("A '.' means the test still PASSED against the broken implementation")
print("(i.e. it does not pin that behaviour); 'X' means it caught the mutation.")
print()
header = "".join("%3d" % i for i in range(len(names)))
print("%-52s %s   caught" % ("mutation", header))
stale, unpinned = [], []
for name, patches in MUTATIONS[1:]:
    nm, res, err = run(name, patches)
    if res is None:
        print("%-52s  %s" % (nm, err))
        stale.append(nm)
        continue
    caught = sum(1 for n in names if res[n] != "pass")
    if not caught:
        unpinned.append(nm)
    row = "".join(("  X" if res[n] != "pass" else "  .") for n in names)
    kinds = sorted({v for v in res.values() if v != "pass"})
    print("%-52s %s   %d/%d  %s"
          % (nm, row, caught, len(names), ",".join(kinds)))

# A mutation whose patch no longer applies prints one quiet line and reads exactly
# like a harmless row -- which is how `K` survived a rename unnoticed for a whole
# pass. Both failure modes are restated at the bottom and set the exit code, so
# nobody has to notice a blank row to notice a hole.
print()
if stale:
    print("STALE (patch text no longer matches the source, so these mutations "
          "tested nothing): %s" % ", ".join(stale))
if unpinned:
    print("UNPINNED (no test caught these): %s" % ", ".join(unpinned))
if not stale and not unpinned:
    print("OK: %d mutations, every one caught by at least one test."
          % (len(MUTATIONS) - 1))
sys.exit(1 if (stale or unpinned) else 0)
