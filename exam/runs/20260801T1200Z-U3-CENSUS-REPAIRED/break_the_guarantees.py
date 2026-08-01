# -*- coding: utf-8 -*-
"""Break each new guarantee on purpose; a test that cannot go red checks nothing.

Each breakage is applied in-process, then the exam census tests are run against
it.  A breakage that leaves the suite green is reported as such.
"""
import sys, subprocess, json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]

PLUGINS = {
# ---------------------------------------------------------------- BREAK 1
"name_keying": '''
"""Put the prefix name-matcher back in charge of the KIND."""
import sys
sys.path.insert(0, r"%(repo)s")
from freeze import theorem_shape as S
from freeze import u3

_real = S.parse_development

def _by_name(src):
    dev = _real(src)
    for name, thm in dev.theorems.items():
        hint = S.name_hint(name)
        thm.kind = hint or S.UNCLASSIFIED_KIND
        thm.basis = {"rule": "kind taken from the NAME (deliberate breakage)"}
    return dev

S.parse_development = _by_name
u3._shape.parse_development = _by_name
''',
# ---------------------------------------------------------------- BREAK 2
"coverage_collapse": '''
"""Fold permanent non-attainers back in with real gaps -- the pre-split state."""
import sys
sys.path.insert(0, r"%(repo)s")
from exam import u3_census

_real = u3_census.kind_coverage

def _collapsed(rows):
    out = _real(rows)
    out["coverage_gaps"] = out["kinds_that_can_never_attain"]
    out["permanent_non_attainers"] = []
    return out

u3_census.kind_coverage = _collapsed
''',
# ---------------------------------------------------------------- BREAK 3
"gap_detector_dead": '''
"""Restore the substring sniff that stopped matching -- the silent all-clear."""
import sys
sys.path.insert(0, r"%(repo)s")
from exam import u3_census

u3_census.CHECKED_KINDS = frozenset()  # nothing has a check ...
_real = u3_census.kind_coverage

def _sniffing(rows):
    out = _real(rows)
    # ... but the old detector keyed on a sentence E1 no longer writes, so it
    # reported no gaps at all.
    for v in out["kinds"].values():
        v["no_check_implemented"] = False
    out["kinds_that_can_never_attain"] = []
    out["coverage_gaps"] = []
    out["permanent_non_attainers"] = []
    return out

u3_census.kind_coverage = _sniffing
''',
# ---------------------------------------------------------------- BREAK 4
"fallback_removed": '''
"""Delete the census's direct-source fallback route."""
import sys
sys.path.insert(0, r"%(repo)s")
from exam import u3_census
from freeze import u3

def _dir_only(site, probe=False, lean_bin=None):
    v = dict(u3.evaluate(site.directory, probe=probe, lean_bin=lean_bin))
    v["census_route"] = "u3.evaluate"
    v["run"] = str(site.directory)
    v["territory"] = site.territory
    v["discovery_route"] = site.route
    v["lean_files"] = [f.name for f in site.lean_files]
    return v

u3_census.adjudicate_site = _dir_only
''',
}

scratch = Path(__file__).parent  # writes brk_*.py plugins beside itself
results = {}
for name, body in PLUGINS.items():
    p = scratch / ("brk_%s.py" % name)
    p.write_text(body % {"repo": str(REPO)}, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_u3_census.py", "-q",
         "-p", "brk_%s" % name],
        cwd=str(REPO / "exam"),
        env={**__import__("os").environ,
             "PYTHONPATH": str(scratch) + ";" + str(REPO)},
        capture_output=True, text=True)
    tail = [l for l in proc.stdout.splitlines() if l.startswith("FAILED")]
    summary = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "?"
    results[name] = {"summary": summary, "failed": tail}
    print("=" * 70)
    print("BREAK:", name)
    print("  ", summary)
    for l in tail:
        print("   ", l)
print()
print(json.dumps({k: v["summary"] for k, v in results.items()}, indent=1))
