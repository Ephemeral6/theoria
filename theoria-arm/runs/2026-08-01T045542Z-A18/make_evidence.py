"""A18 evidence: two mock games played end to end, and what the run-end scorer
said about each.

Run from the arm root:

    python runs/2026-08-01T045542Z-A18/make_evidence.py

Zero spend and no network: `proxy/mock/arc_mock.py` for the world, a scratch
spend pool this script owns for the money, `harness.run.FIXTURE_RUNS_DIR` for
the run directories -- nothing lands in `runs/` or in the fleet's shared pool.

The forged leg is the negative control. Its scorecard is *coherent*: the run's
actions, its environment's actions and the card total are all moved together,
so every check that reads the card alone still passes. The only witness left is
the ledger, which is the point of reconciling at all.
"""

import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, ARM)

import _bootstrap                                       # noqa: E402,F401

from harness import run as run_mod                      # noqa: E402
from inner.loop import TheoriaArm                       # noqa: E402
from proxy.ledger import read_ledger                    # noqa: E402
from proxy.mock.arc_mock import DEFAULT_KEY, MockArc    # noqa: E402
from proxy.spend_gate import SpendGate                  # noqa: E402

GAME = "g50t-5849a774"                                  # development pile
ACTIONS = 6
OUT = os.path.join(HERE, "evidence")


class _Forged:
    """The real arm, with three actions added to its closing scorecard."""

    def __init__(self, inner):
        self.inner = inner

    def play(self):
        return self._doctor(dict(self.inner.play()))

    def summary(self):
        return self._doctor(dict(self.inner.summary()))

    @staticmethod
    def _doctor(summary):
        if not summary.get("scorecard"):
            return summary
        card = json.loads(json.dumps(summary["scorecard"]))
        card["total_actions"] = (card.get("total_actions") or 0) + 3
        for env in card.get("environments") or []:
            env["actions"] = (env.get("actions") or 0) + 3
            for run in env.get("runs") or []:
                run["actions"] = (run.get("actions") or 0) + 3
        summary["scorecard"] = card
        return summary


def leg(name, forge):
    tmp = tempfile.mkdtemp(prefix="a18-evidence-")
    slug = "pytest-a18-evidence-" + name
    ledger_path = os.path.join(tmp, "ledger.jsonl")
    policy = run_mod._scratch_policy(os.path.join(tmp, "scratch-pool.jsonl"))
    gate = SpendGate(policy)

    def factory(env_base, run):
        arm = TheoriaArm(env_base=env_base, run=run, game_id=GAME,
                         budget_actions=ACTIONS, offline=True)
        return _Forged(arm) if forge else arm

    with MockArc(api_key=DEFAULT_KEY, games=[GAME]) as mock:
        summary = run_mod.play(
            GAME, slug, factory, env_upstream=mock.base_url,
            env_key=DEFAULT_KEY, require_key=False, spend_gate=gate,
            expect_pool={"pool": policy.pool,
                         "ledger_abspath": os.path.abspath(policy.ledger_path)},
            runs_root=run_mod.FIXTURE_RUNS_DIR,
            scores_dir=os.path.join(tmp, "scores"),
            ledger_path=ledger_path)

    run_dir = os.path.join(run_mod.FIXTURE_RUNS_DIR, slug)
    with open(os.path.join(run_dir, run_mod.SCORE_ARTEFACT), encoding="utf-8") as fh:
        report = json.load(fh)
    records = [r for r in read_ledger(ledger_path)
               if r["run_id"] == summary["run_id"]]
    return summary, report, records


def main():
    os.makedirs(OUT, exist_ok=True)
    index = {}
    for name, forge in (("clean", False), ("forged", True)):
        summary, report, records = leg(name, forge)
        # The report itself, minus the run-specific identifiers that move every
        # time this is regenerated, so a reader compares verdicts and numbers
        # rather than uuids.
        with open(os.path.join(OUT, "score_%s.json" % name), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump(report, fh, indent=2, sort_keys=True, default=str)
            fh.write("\n")
        s1 = [c for c in report["checks"] if c["id"] == "S-1"][0]
        incidents = [{"kind": r["kind"], "detail": r["detail"]}
                     for r in records if r["event"] == "incident"]
        index[name] = {
            "verdict": report["verdict"],
            "failed_checks": report["failed_checks"],
            "undetermined_checks": report["undetermined_checks"],
            "S-1": {"verdict": s1["verdict"],
                    "scorecard": s1.get("scorecard"),
                    "ledger": s1.get("ledger")},
            "scorer": report["scorer"],
            "actions_ok_in_ledger": report["ledger"]["actions_ok"],
            "events": [r["event"] for r in records][-3:],
            "incidents": incidents,
            "summary_score_verdict": summary["score_verdict"],
        }
    with open(os.path.join(OUT, "INDEX.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(index, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print(json.dumps(index, indent=2, sort_keys=True))
    # The fixtures themselves are not evidence and do not accumulate.
    for name in ("clean", "forged"):
        shutil.rmtree(os.path.join(run_mod.FIXTURE_RUNS_DIR,
                                   "pytest-a18-evidence-" + name),
                      ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
