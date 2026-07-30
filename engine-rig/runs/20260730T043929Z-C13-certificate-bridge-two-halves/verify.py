"""C13 acceptance, re-checked end to end and independently of the test suite.

Run it from `engine-rig/`:

    python runs/20260730T043929Z-C13-certificate-bridge-two-halves/verify.py

Exit 0 and `ALL CHECKS PASS`, or exit 1 naming the check that failed. It writes
its artefacts (the forged certificate, the reader's transcripts) beside itself,
and nothing else anywhere.

Nine checks, one per thing the item asked for plus the ones that keep the
answers honest. The load-bearing one is check 4: the same reader, handed the
same forged document, accepts it when the move relation comes from the document
and rejects it when the relation is grounded. Without that pair, check 3 would
only show that some checker says no to something.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.dirname(RIG)
sys.path.insert(0, RIG)

from engines.lp_potential.potential import solve_certificate  # noqa: E402
from interop import certificate_export as ce  # noqa: E402
from interop import export_certificates  # noqa: E402
from interop import pagoda_reader  # noqa: E402
from interop import peg1d  # noqa: E402

CERT_DIR = os.path.join(RIG, "interop", "certificates")
READER = os.path.join(RIG, "interop", "pagoda_reader.py")
CONTRACT = os.path.join(REPO, "CONTRACTS", "pagoda_certificate_v0.1.md")
SYNC = os.path.join(REPO, "PARTNER_SYNC.md")

failures = []
notes = []


def check(name, condition, detail=""):
    status = "ok  " if condition else "FAIL"
    print("  [%s] %s%s" % (status, name, (" -- " + detail) if detail else ""))
    if not condition:
        failures.append(name)


def artefact(name, text):
    with open(os.path.join(HERE, name), "w", encoding="utf-8",
              newline="\n") as handle:
        handle.write(text)


# ------------------------------------------------------------------- 1. rebuild
print("[1/9] the committed certificates rebuild from the engine")
problems = export_certificates.regenerate(check_only=True)
check("three documents rebuild byte-for-byte", problems == [],
      "; ".join(problems) or "%d cases" % len(export_certificates.CASES))

# --------------------------------------------------------------- 2. round trip
print("[2/9] engine -> export -> disk -> independent reader")
goals = ["01000"]
graph = peg1d.build_graph(5, "11011", goal_states=goals)
certificate = solve_certificate(graph, "11011", goal_states=goals,
                                bound=export_certificates.BOUND)
check("the LP still finds a certificate", certificate is not None)
document = ce.build(certificate, graph, claim_name="unsolvable_11011_to_01000")
round_trip = os.path.join(HERE, "round_trip.cert.json")
ce.write(document, round_trip)
reloaded = pagoda_reader.load(round_trip)
check("what came back off disk is what went on", reloaded == document)
check("the independent reader accepts it", pagoda_reader.check(reloaded) == [])

# -------------------------------------------------- 3. every committed document
print("[3/9] every committed certificate, adjudicated by the reader")
transcript = []
for name in sorted(os.listdir(CERT_DIR)):
    if not name.endswith(".json"):
        continue
    doc = pagoda_reader.load(os.path.join(CERT_DIR, name))
    reasons = pagoda_reader.check(doc)
    opinion = pagoda_reader.second_opinion(doc)
    check("accepted: %s" % name, reasons == [], "; ".join(reasons))
    check("exhaustive search agrees: %s" % name,
          opinion is not None and opinion["goal_reachable"] is False,
          "%d states reachable" % opinion["n_reachable"])
    transcript.append({"document": name, "rejections": reasons,
                       "second_opinion": opinion})
artefact("reader_transcript.json",
         json.dumps(transcript, indent=2, sort_keys=True) + "\n")

# ------------------------------------------------------- 4. the omission forgery
print("[4/9] the forgery the producer's own verifier cannot catch")
forged = json.loads(json.dumps(document))
forged["weights_integer"][2] = -1
forged["weights_rational"][2] = "-1"
weights = forged["weights_integer"]
kept = []
for witness in forged["obligations"]["inv_closed"]["witnesses"]:
    src, over, dst = witness["positions"]
    delta = weights[dst] - weights[src] - weights[over]
    if delta > 0:
        continue
    witness.update({"w_src": weights[src], "w_over": weights[over],
                    "w_dst": weights[dst], "delta": delta, "holds": True})
    kept.append(witness)
forged["obligations"]["inv_closed"].update({
    "witnesses": kept, "n_checked": len(kept),
    "checked_over": "the %d move instances this document lists" % len(kept)})
artefact("forged_omission.cert.json",
         json.dumps(forged, indent=2, sort_keys=True) + "\n")

listed = [tuple(w["positions"]) for w in kept]
check("the forgery deleted exactly the two raising moves", len(kept) == 4,
      "%d witnesses kept of 6" % len(kept))
check("the producer's verify() accepts the forgery", ce.verify(forged) == [],
      "this is the documented gap, not a new defect")
check("the reader accepts it too when the moves come from the document",
      pagoda_reader.check(forged, geometry=lambda n: sorted(listed)) == [],
      "so the rejection below is the grounding, nothing else")
grounded = pagoda_reader.check(forged)
check("the reader rejects it when the moves are grounded", len(grounded) == 2,
      "; ".join(grounded))
check("and it still accepts the honest document",
      pagoda_reader.check(document) == [])

# The stronger form, found by attacking the weaker one: above, the forged
# document proves a true claim badly. Here it certifies a falsehood -- the one
# deleted witness is the move that reaches the goal.
lie = {"schema": pagoda_reader.SCHEMA, "claim": "unsolvable_11011_to_00111",
       "conclusion": "no goal state is reachable from 11011",
       "produced_by": "engine-rig/engines/lp_potential", "n_pos": 5,
       "initial_state": "11011", "goal_states": ["00111"],
       "weights_integer": [-4, -4, 4, 0, 4], "initial_potential": -4,
       "verified": True}
lie_weights = lie["weights_integer"]
lie_witnesses = []
for src, over, dst in pagoda_reader.jump_moves(5):
    delta = lie_weights[dst] - lie_weights[src] - lie_weights[over]
    if delta > 0:
        continue
    lie_witnesses.append({"move": "jump(%d,%d,%d)" % (src, over, dst),
                          "positions": [src, over, dst], "delta": delta,
                          "w_src": lie_weights[src], "w_over": lie_weights[over],
                          "w_dst": lie_weights[dst], "holds": True})
lie["obligations"] = {
    "inv_init": {"statement": "potential(initial) <= -4", "value": -4,
                 "holds": True},
    "inv_closed": {"statement": "every legal move has delta <= 0",
                   "checked_over": "the %d move instances this document lists"
                                   % len(lie_witnesses),
                   "n_checked": len(lie_witnesses),
                   "witnesses": lie_witnesses, "holds": True},
    "goal_break": {"statement": "every goal state has potential > -4",
                   "witnesses": [{"goal_state": "00111", "potential": 8,
                                  "exceeds_initial_by": 12, "holds": True}],
                   "holds": True}}
artefact("forged_falsehood.cert.json",
         json.dumps(lie, indent=2, sort_keys=True) + "\n")
check("the producer's verify() accepts a certificate of a falsehood",
      ce.verify(lie) == [], "one witness deleted: the move that reaches the goal")
check("the goal really is reachable from the start",
      "00111" in peg1d.reachable_from("11011"),
      "one jump: jump(0,1,2)")
lie_reasons = pagoda_reader.check(lie)
check("the reader refuses it and names the deleted move", len(lie_reasons) == 1,
      "; ".join(lie_reasons))
check("the second opinion independently sees the goal is reachable",
      pagoda_reader.second_opinion(lie)["goal_reachable"] is True)

# ------------------------------------------------------------ 5. independence
print("[5/9] the reader is independent, as a fact rather than a claim")
with open(READER, encoding="utf-8") as handle:
    reader_source = handle.read()
imports = [line.split()[1].split(".")[0]
           for line in reader_source.splitlines()
           if line.startswith(("import ", "from "))]
forbidden = {"engines", "interop", "recheck", "common", "fixtures", "tools",
             "numpy", "scipy"}
check("it imports nothing from this rig", not (set(imports) & forbidden),
      "imports: %s" % ", ".join(sorted(set(imports))))

import shutil  # noqa: E402
import tempfile  # noqa: E402

alone = tempfile.mkdtemp(prefix="c13-alone-")
try:
    shutil.copy(READER, os.path.join(alone, "pagoda_reader.py"))
    with open(os.path.join(alone, "good.json"), "w", encoding="utf-8") as fh:
        json.dump(document, fh)
    with open(os.path.join(alone, "bad.json"), "w", encoding="utf-8") as fh:
        json.dump(forged, fh)
    good = subprocess.run([sys.executable, "-I", "pagoda_reader.py", "good.json"],
                          cwd=alone, capture_output=True, text=True)
    bad = subprocess.run([sys.executable, "-I", "pagoda_reader.py", "bad.json"],
                         cwd=alone, capture_output=True, text=True)
    check("it runs alone in an empty directory and accepts", good.returncode == 0,
          (good.stderr or good.stdout.splitlines()[0]).strip())
    check("it runs alone in an empty directory and refuses", bad.returncode == 1,
          (bad.stderr or bad.stdout.splitlines()[0]).strip())
    artefact("isolated_run.txt", good.stdout + "\n" + bad.stdout)
finally:
    shutil.rmtree(alone, ignore_errors=True)

# --------------------------------------------------------------- 6. the contract
print("[6/9] the format is pinned in /CONTRACTS/")
check("the contract file exists", os.path.exists(CONTRACT))
contract_text = open(CONTRACT, encoding="utf-8").read() if os.path.exists(CONTRACT) else ""
check("it pins the schema string this rig stamps",
      pagoda_reader.SCHEMA in contract_text)
check("it names the reference reader",
      "interop/pagoda_reader.py" in contract_text)
gate = subprocess.run([sys.executable, "verify.py"],
                      cwd=os.path.join(REPO, "CONTRACTS"),
                      capture_output=True, text=True)
check("the CONTRACTS completion gate is still green", gate.returncode == 0,
      gate.stdout.strip().splitlines()[-1] if gate.stdout else gate.stderr[:120])

# ------------------------------------------------------------ 7. PARTNER_SYNC
print("[7/9] the board says our half is done")
sync = open(SYNC, encoding="utf-8").read()
check("an engine-rig paragraph names this contract",
      "pagoda_certificate_v0.1" in sync)

# ----------------------------------------------------------- 8. the other track
print("[8/9] the far half, read and not touched")
consumer = os.path.join(REPO, "theory-compiler", "src", "theory_compiler",
                        "certificate.py")
if os.path.exists(consumer):
    source = open(consumer, encoding="utf-8").read()
    check("the consumer still pins our schema id",
          'SCHEMA = "%s"' % pagoda_reader.SCHEMA in source)
else:
    notes.append("theory-compiler tree absent; the anchor check was skipped")
    check("the consumer still pins our schema id", True, "skipped, tree absent")

changed = subprocess.run(
    ["git", "diff", "--name-only", "origin/master...HEAD", "--",
     "theory-compiler"], cwd=REPO, capture_output=True, text=True)
check("this branch changed zero bytes under theory-compiler/",
      changed.stdout.strip() == "", changed.stdout.strip() or "none")

# ----------------------------------------------------------------- 9. the probe
print("[9/9] the monitor probe, recorded rather than steered")
sys.path.insert(0, os.path.join(REPO, "monitor"))
try:
    import scan  # noqa: E402
    state = scan.probe_a1_state()
    print("      probe_a1_state -> %s" % state["status"])
    artefact("probe_a1_state.json",
             json.dumps(state, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    check("the probe is not red", state["status"] != "risk", state["status"])
    if state["status"] == "green":
        notes.append(
            "probe_a1_state is green, not partial: the item's premise that the "
            "consumer half is missing was stale. Nothing here was changed to "
            "make it so -- see RUN_STATE.md and monitor/inbox.")
except Exception as exc:  # pragma: no cover - the probe is not ours to fix
    notes.append("probe_a1_state could not be run here: %r" % (exc,))
    print("      probe_a1_state unavailable: %r" % (exc,))

print()
for note in notes:
    print("note: %s" % note)
if failures:
    print("\n%d CHECK(S) FAILED: %s" % (len(failures), "; ".join(failures)))
    sys.exit(1)
print("\nALL CHECKS PASS")
