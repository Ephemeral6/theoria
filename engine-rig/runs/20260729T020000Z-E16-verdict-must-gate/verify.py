"""E16 acceptance, re-checked end to end and independently of the test suite.

The suite proves these too, and that is where they gate merges.  This script
exists because E16's own defect was a verdict living somewhere nothing read: a
run directory whose evidence is "the suite was green when I ran it" carries the
same shape.  Run it from `engine-rig/`:

    python -m runs.20260729T020000Z-E16-verdict-must-gate.verify   # (see below)
    python runs/20260729T020000Z-E16-verdict-must-gate/verify.py   # what works

Exit 0 and `ALL CHECKS PASS`, or exit 1 naming the check that failed.
"""

import os
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
RIG = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, RIG)

from common.jsonio import read_json, read_jsonl          # noqa: E402
from engines import deadlock_carver as dc                # noqa: E402
from engines import lp_potential                         # noqa: E402
from engines.fd_adapter import search as fd_search       # noqa: E402
from engines.fd_adapter.pddl import parse_domain, parse_problem   # noqa: E402
from engines.lp_potential.potential import moves_from_graph       # noqa: E402
from fixtures import peg4, sokoban                       # noqa: E402
from tools.validate_candidates import validate_rows      # noqa: E402

FAILURES = []


def check(name, condition, detail=""):
    print(("  PASS  " if condition else "  FAIL  ") + name + (" -- " + detail if detail else ""))
    if not condition:
        FAILURES.append(name)


def _read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


# ------------------------------------------------- 1. lp_potential's headline

print("1. lp_potential: `admissible` is derived, not a literal")
graph = read_json(peg4.GRAPH_PATH)
certificate, heuristic = lp_potential.run(graph, "1110")
rows = lp_potential.candidates(certificate, heuristic, graph, timestamp="2026-07-27T00:00:00Z")
payload = rows[1]["payload"]
check("the honest case still publishes admissible", payload["admissible"] is True)
check("the basis ships with it", payload["admissible_basis"]["certificate_holds"] is True)

# The negative sample E16 asks for: holds=False must reach the field.
from dataclasses import replace                          # noqa: E402
from interop import certificate_export as ce             # noqa: E402
from interop import peg1d                                # noqa: E402
for label, conditions in (
    ("a failed condition", {"inv_init": True, "inv_closed": False, "goal_break": True}),
    ("no conditions at all", {}),
):
    broken = replace(certificate, conditions=conditions)
    bad = lp_potential.heuristic_from(broken)
    check("holds=False (%s) forces admissible=False" % label,
          bad.as_json()["admissible"] is False)

# A certificate that holds and is still wrong about the world -- the shared
# premise of D-035 site 1, made executable.
partial = lp_potential.Certificate(
    weights=[Fraction(w) for w in (-4, 0, -4, -4)],
    initial="1110",
    goal_states=list(graph["goal_states"]),
    moves=[m for m in moves_from_graph(graph) if m.name() != "jump(3,2,1)"],
    margin=Fraction(1),
)
partial.conditions = lp_potential.check_exactly(partial)
partial_h = lp_potential.heuristic_from(partial)
report = lp_potential.admissibility_report(partial_h, graph)
check("a 3-of-4-move certificate passes all three exact conditions",
      partial.holds is True, str(partial.conditions))
check("and is refuted by the empirical check",
      [r["state"] for r in report if not r["admissible"]] == ["0011", "1101"])
check("so the headline reads False despite holds=True",
      partial_h.as_json(report)["admissible"] is False)

# The emitter is stricter still: it re-derives the premises from the graph and
# withholds BOTH rows.  Gating only the heuristic row -- which is what the first
# cut of this fix did -- left the invariant asserting `goal unreachable from X`
# beside a heuristic row whose counterexamples disprove it.  Found by an
# adversarial review of the fix, not by the fix.
check("the emitter withholds both rows, not just the heuristic",
      lp_potential.candidates(partial, partial_h, graph,
                              timestamp="2026-07-27T00:00:00Z") == [])
marked = lp_potential.candidates(partial, partial_h, graph,
                                 timestamp="2026-07-27T00:00:00Z", on_unsound="mark")
check("marked, both rows carry the defect",
      [r["payload"]["unsound"] for r in marked] == [True, True])
check("and the invariant row publishes holds=False",
      marked[0]["payload"]["holds"] is False)
premise = lp_potential.premises_against_graph(partial, graph)
check("the premise check asks the graph, not the certificate",
      premise["missing_moves"] == ["jump(3,2,1)"]
      and premise["moves_raising_potential"] == ["jump(3,2,1)"])
check("conditions alone cannot be read as a verdict",
      all(replace(certificate, conditions={}).as_json()["conditions"].values()) is True
      and replace(certificate, conditions={}).as_json()["holds"] is False)

# A certificate about other goals is legitimate; scoring it against the graph's
# distance table is not -- those distances measure a different question.
foreign_c, foreign_h = lp_potential.run(graph, "0111", goal_states=["1010"])
foreign = lp_potential.candidates(foreign_c, foreign_h, graph,
                                  timestamp="2026-07-27T00:00:00Z")[1]["payload"]
check("a foreign goal set is not scored against the graph's distances",
      foreign["admissible"] is True
      and "not comparable" in foreign["admissible_basis"]["empirical_check"]
      and "admissibility_check" not in foreign)
check("an empty report is vacuous, not a pass",
      "vacuous" in heuristic.as_json([])["admissible_basis"]["empirical_check"])

# ------------------------------------------------ 2. deadlock_carver's gate

print("2. deadlock_carver: a refuted theorem does not reach the stream")
domain = parse_domain(_read(sokoban.DOMAIN_PATH))
problem = parse_problem(_read(sokoban.OPEN4.path))
task = dc.Task.build(domain, problem)
theorems = dc.carve(task)
check("the fixture carves something", bool(theorems), "%d theorems" % len(theorems))

refuted = dc.PruningReport(
    "refuted", len(theorems),
    fd_search.SearchResult(["a", "b", "c"], 100, 120, 0, 9, 500000, True),
    fd_search.SearchResult(None, 40, 50, 30, 9, 500000, True),
)
check("the report really is refuting", refuted.same_answer is False)

withheld = dc.candidates(theorems, task, report=refuted, timestamp="2026-07-27T00:00:00Z")
check("no invariant survives the refutation", [r["kind"] for r in withheld] == ["plan"])
check("the withholding is on the record",
      withheld[0]["payload"]["invariants_withheld"] == len(theorems))
check("the account still validates", validate_rows(withheld) == [])

marked = dc.candidates(theorems, task, report=refuted,
                       timestamp="2026-07-27T00:00:00Z", on_refutation="mark")
invariants = [r for r in marked if r["kind"] == "invariant"]
check("mark mode keeps the rows", len(invariants) == len(theorems))
check("every kept row carries a machine-readable marker",
      all(r["payload"]["refuted"] is True for r in invariants))
check("marked rows still validate", validate_rows(marked) == [])

passed = dc.pruning_report(domain, problem, theorems)
clean = dc.candidates(theorems, task, report=passed, timestamp="2026-07-27T00:00:00Z")
check("a passing verdict changes nothing",
      len([r for r in clean if r["kind"] == "invariant"]) == len(theorems))
check("and stamps no refutation key",
      "refuted" not in [r for r in clean if r["kind"] == "plan"][0]["payload"])

try:
    dc.candidates(theorems, task, report=dc.PruningReport(
        "p", 1,
        fd_search.SearchResult(None, 10, 10, 0, 3, 500000, True),
        fd_search.SearchResult(None, 10, 10, 0, 3, 500000, False)))
    check("an unfinished comparison neither clears nor refutes", False, "no raise")
except dc.UnfinishedComparison:
    check("an unfinished comparison neither clears nor refutes", True)

# --------------------------------------------------- 3. the published artefact

print("3. the committed artefact carries the derived field")
artefact = read_jsonl(os.path.join(RIG, "artifacts", "candidates.jsonl"))
check("row count unchanged", len(artefact) == 44, "%d rows" % len(artefact))
heuristics = [r for r in artefact
              if r["kind"] == "heuristic" and r["engine"] == "lp_potential"]
check("the heuristic row ships a basis",
      len(heuristics) == 1 and "admissible_basis" in heuristics[0]["payload"])
account = [r for r in artefact
           if r["kind"] == "plan" and r["payload"].get("producer") == "deadlock_carver"]
check("the carver's account is unrefuted, so carries no refuted key",
      len(account) == 1 and "refuted" not in account[0]["payload"])

# ------------------------------------------------------ 4. the wording is split

print("4. D-035: the overclaims are gone")
decisions = _read(os.path.join(RIG, "DECISIONS.md"))
check("D-034 is recorded", "## D-034" in decisions)
check("D-035 is recorded", "## D-035" in decisions)
for path, gone in (
    ("engines/fd_adapter/validate.py", "The only code shared with the planner is the parser"),
    ("interop/README.md", "recomputes everything from the document's own contents"),
    ("engines/zero_space/README.md",
     "Soundness has an independent check on top"),
    ("engines/deadlock_carver/README.md",
     "That referee shares nothing with the proof or with the planner"),
):
    text = _read(os.path.join(RIG, path))
    check("%s no longer overclaims" % path, gone not in text, gone[:44] + "...")

# ------------------------- 5. the same shape, found by attacking the fix itself

print("5. the sites an adversarial review of this fix turned up")

# interop: `conclusion` was a literal written above the line computing `verified`.
goal = ["01000"]
peg5 = peg1d.build_graph(5, "11011", goal_states=goal)
good = lp_potential.solve_certificate(peg5, "11011", goal_states=goal, bound=10000)
document = ce.build(good, peg5, claim_name="ok")
check("a discharged document still concludes", document["verified"] is True
      and document["conclusion"].startswith("no goal state is reachable"))
broken_doc = ce.build(replace(good, weights=[Fraction(9)] + list(good.weights[1:])),
                      peg5, claim_name="broken")
check("a failing document states no conclusion",
      broken_doc["verified"] is False
      and "nothing follows" in broken_doc["conclusion"])
check("checked_over says what was actually checked",
      "move instances this document lists"
      in document["obligations"]["inv_closed"]["checked_over"])

# run_all: the RING theorems drive a published reachability verdict.
runall = _read(os.path.join(RIG, "tools", "run_all.py"))
check("the probe planner's pruner has a verdict taken at its own site",
      "ring_report = deadlock_carver.pruning_report" in runall
      and "if not ring_report.same_answer:" in runall)

# p13: the prose had no branch for a refuted row.
p13 = _read(os.path.join(RIG, "tools", "p13_fd_dividend.py"))
check("the FD dividend prose branches on a refuted verdict first",
      'elif row["same_answer"] is False:' in p13
      and p13.index('elif row["same_answer"] is False:') < p13.index("elif before == after:"))

# DECISIONS: D-010 and D-028 asserted what D-035 falsified.
check("D-010 and D-028 are superseded on their independence clause",
      "**D-010** reads" in decisions and "**D-028** reads" in decisions)

print()
if FAILURES:
    print("FAILED: " + ", ".join(FAILURES))
    sys.exit(1)
print("ALL CHECKS PASS")
