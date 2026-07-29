"""Attack 4: can `fire_the_guard` pass while the guard is broken?"""
import json
import os
import re
import sys
import tempfile

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from exam import guard
from exam.tools import sealed_drill

RUN = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

print("=" * 72)
print("A4-1  baseline: the guard as shipped")
print("=" * 72)
ev = sealed_drill.fire_the_guard()
print(json.dumps({k: v for k, v in ev.items() if k != "checks"}, indent=1))
for c in ev["checks"]:
    print("   %-18s passed=%-5s %s" % (c["check"], c["passed"], c["detail"][:70]))

piles = guard.load_piles()
sealed = list(piles.sealed_pile)
print("\n  sealed pile holds %d ids; fire_the_guard probes exactly one: sealed_pile[0]" % len(sealed))

print()
print("=" * 72)
print("A4-2  a guard broken for 20 of the 21 sealed ids still 'fires'")
print("=" * 72)
real = guard.assert_synthetic_world
ONLY = sealed[0]


def one_id_guard(world_id, **kw):
    """Refuses exactly sealed_pile[0] and its stem. Everything else sails."""
    key = (world_id or "").strip().lower()
    if key in (ONLY.lower(), ONLY.split("-", 1)[0].lower()):
        raise guard.SealedPileError("%r is in the sealed pile." % world_id)
    return "generated"


sealed_drill.guard.assert_synthetic_world = one_id_guard
ev2 = sealed_drill.fire_the_guard()
print("  fired = %s" % ev2["fired"])
for c in ev2["checks"]:
    print("   %-18s passed=%s" % (c["check"], c["passed"]))
leaked = [g for g in sealed[1:] if one_id_guard(g) == "generated"]
print("  ...yet this guard ACCEPTS %d of the %d sealed ids (%s of them silently)"
      % (len(leaked), len(sealed), len(leaked)))
print("  and it accepts every dev-pile id too: %s"
      % [one_id_guard(g) for g in piles.dev_pile])

print()
print("=" * 72)
print("A4-3  a guard that accepts only the one negative control still 'fires'")
print("=" * 72)
CONTROL = sealed_drill.VARIANTS[0]["world"]


def one_world_guard(world_id, **kw):
    """Accepts exactly the drill's first world; refuses literally everything
    else with SealedPileError -- including the other 19 worldgen worlds."""
    if world_id == CONTROL:
        return "generated"
    raise guard.SealedPileError("%r is in the sealed pile." % world_id)


sealed_drill.guard.assert_synthetic_world = one_world_guard
ev3 = sealed_drill.fire_the_guard()
print("  fired = %s" % ev3["fired"])
for c in ev3["checks"]:
    print("   %-18s passed=%s" % (c["check"], c["passed"]))
print("  ...this guard refuses t1-fragile-bridge, which the drill itself uses,")
print("  and refuses every dev-pile and unknown id as SEALED. It is useless,")
print("  and fire_the_guard reports it as fired.")

sealed_drill.guard.assert_synthetic_world = real

print()
print("=" * 72)
print("A4-4  a doctored piles.json")
print("=" * 72)
doc = json.load(open(guard.load_piles.__defaults__ and
                     os.path.join(REPO, "arc-recon", "data", "piles.json"),
                     encoding="utf-8"))
tmp = tempfile.mkdtemp(prefix="v6-piles-")
bad = os.path.join(tmp, "piles.json")
doc2 = dict(doc)
doc2["sealed_pile"] = list(doc["sealed_pile"])[1:]        # quietly free one game
with open(bad, "w", encoding="utf-8") as fh:
    json.dump(doc2, fh)
try:
    guard.load_piles(bad)
    print("  ACCEPTED a doctored cut")
except guard.CutIntegrityError as exc:
    print("  CutIntegrityError, as advertised: %s" % str(exc)[:120])
print("  -> but note the failure mode inside the drill: fire_the_guard() calls")
print("     load_piles() unguarded, so this raises out of run() and the drill")
print("     dies with a traceback -- no DRILL.json, no RED report, exit != 1.")

print()
print("=" * 72)
print("A4-5  does any sealed id or short stem reach ANY file the drill writes?")
print("=" * 72)
stems = sorted({g.split("-", 1)[0] for g in sealed})
hits = []
scanned = 0
for root, dirs, files in os.walk(RUN):
    dirs[:] = [d for d in dirs if d != "adversarial"]
    for name in files:
        path = os.path.join(root, name)
        scanned += 1
        try:
            text = open(path, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        low = text.lower()
        for gid in sealed:
            if gid.lower() in low:
                hits.append((path, "FULL", gid))
        for stem in stems:
            for m in re.finditer(r"(?<![0-9a-z])" + re.escape(stem) + r"(?![0-9a-z])", low):
                hits.append((path, "STEM", stem))
                break
print("  scanned %d files under %s (adversarial/ excluded)" % (scanned, RUN))
if hits:
    for h in hits:
        print("   LEAK %s  %s  %r" % (h[1], os.path.relpath(h[0], RUN), h[2]))
else:
    print("  no sealed full id and no bare sealed stem found.")
print()
print("  for contrast, what IS in sheet.json's `world` block:")
sheet = json.load(open(os.path.join(RUN, "sheet.json"), encoding="utf-8"))
print("   ", json.dumps(sheet["world"]))
print("  -> all four DEV-pile ids are published verbatim on the examinee's sheet.")
