"""Play the two sessions the negative control uses and keep the raw output.

Four files, and the pairs are the point:

    evidence-scoreless.txt          the guard refuses  (exit 2)
    evidence-scoreless-unmarked.txt the same stream, marker stripped -> passes
    evidence-scoring.txt            a real shortfall, the guard passes (exit 0)
    evidence-scoring-forged.txt     the same stream, one marker forged -> refused

Nothing here writes into the tracked tree except under `--out`, and both the
spend pool and the scored-artefact directory are redirected into a scratch
directory the way `verify.py` does it. No key, no socket to anywhere but the
loopback mocks.

    python collect_evidence.py --out <dir>
"""

import argparse
import functools
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, REPO)

SCRATCH = tempfile.mkdtemp(prefix="v22-evidence-")

from proxy import redact, scoring                                    # noqa: E402
from proxy.spend_gate import (SpendGate, SpendPolicy,                # noqa: E402
                              set_default_gate)

scoring.score_run = functools.partial(scoring.score_run,
                                      scores_dir=os.path.join(SCRATCH, "scores"))
set_default_gate(SpendGate(SpendPolicy({
    "v": "1.0", "pool": "v22-evidence-scratch",
    "usd_ceiling": 1000.0, "action_ceiling": 100000,
    "ledger": os.path.join(SCRATCH, "spend_gate.jsonl"),
    "default_ttl_seconds": 3600, "lock_timeout_seconds": 30.0,
    "default_run_caps": {"usd": 5.0, "actions": 600},
}, source=None)))

from proxy.ledger import read_ledger                                 # noqa: E402
from proxy.mock.arc_mock import (DEFAULT_GAME,                       # noqa: E402
                                 DEFAULT_KEY as ARC_KEY, MockArc)
from proxy.mock.model_mock import (DEFAULT_KEY as MODEL_KEY,         # noqa: E402
                                   MockProvider)
from proxy.runner import run_game                                    # noqa: E402
from proxy.variants import Variant                                   # noqa: E402


def variant(require, variant_id):
    return Variant({
        "variant_id": variant_id, "base_game": DEFAULT_GAME,
        "claim": "unsolvable",
        "operators": [{"op": "win_tighten",
                       "require": {"kind": "score_at_least", "value": require}}],
        "justification": "The server's win is kept and a score floor is added "
                         "on top of it, so the tightened win is a strict "
                         "subset of the original one.",
    })


def play(name, spec, scoreless):
    path = os.path.join(SCRATCH, name + ".jsonl")
    with MockArc(api_key=ARC_KEY, games=[DEFAULT_GAME], scoreless=scoreless) as arc, \
            MockProvider(api_key=MODEL_KEY) as provider:
        run_game(DEFAULT_GAME, arm="mock_arm", budget=60,
                 env_upstream=arc.base_url, model_upstream=provider.base_url,
                 env_key=ARC_KEY, model_key=MODEL_KEY, require_keys=False,
                 variant=spec, ledger_path=path,
                 runs_dir=os.path.join(SCRATCH, name + "-runs"))
    return path


def guard(path):
    proc = subprocess.run(
        [sys.executable, "-m", "proxy.tools.check_variant_degeneracy", path],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8",
        errors="replace")
    return proc.returncode, proc.stdout + proc.stderr


def rewrite(path, out_path, fn):
    n = 0
    with open(path, encoding="utf-8") as src, \
            open(out_path, "w", encoding="utf-8", newline="\n") as dst:
        for line in src:
            if not line.strip():
                continue
            record = json.loads(line)
            n += 1 if fn(record) else 0
            dst.write(json.dumps(record, sort_keys=True) + "\n")
    return n


def applied_of(record):
    applied = (record.get("variant") or {}).get("applied")
    return applied if isinstance(applied, dict) else None


def write(out, name, lines):
    with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
    print("wrote", name)


def report(path, header):
    records = read_ledger(path)
    lines = [header, "=" * len(header), ""]
    win = [r for r in records if (applied_of(r) or {}).get("op") == "win_tighten"]
    lines.append("env_step records carrying a win_tighten rewrite: %d of %d"
                 % (len(win), len(records)))
    lines.append("")
    for record in win[:3]:
        lines.append("  seq %-4s %s" % (record["seq"],
                                        json.dumps(applied_of(record),
                                                   sort_keys=True)[:400]))
    if len(win) > 3:
        lines.append("  ... %d more, identical but for `occurrence`" % (len(win) - 3))
    lines.append("")
    incidents = [r for r in records
                 if r.get("event") == "incident"
                 and r.get("kind") == "variant_degenerate"]
    lines.append("variant_degenerate incidents: %d" % len(incidents))
    for record in incidents:
        lines.append("  " + json.dumps({k: v for k, v in record.items()
                                        if k in ("seq", "kind", "variant_id",
                                                 "reason", "require_score",
                                                 "game_id")},
                                       sort_keys=True))
    lines.append("")
    return lines, records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    # The vault is process-global and `test_spend_gate.py` is not running here,
    # so nothing has poisoned it; the filter is kept anyway so this script's
    # output does not depend on what ran before it in the same interpreter.
    redact.VAULT._secrets[:] = [s for s in redact.VAULT._secrets
                                if len(s) >= redact.MIN_SECRET_LEN]

    # -- the scoreless session ---------------------------------------------
    scoreless = play("scoreless", variant(2, "t-absent"), scoreless=True)
    lines, _ = report(scoreless, "SCORELESS SESSION -- the world reports no score")
    code, out = guard(scoreless)
    lines += ["$ python -m proxy.tools.check_variant_degeneracy <ledger>",
              out.rstrip(), "exit=%d" % code, ""]
    write(args.out, "evidence-scoreless.txt", lines)

    unmarked = os.path.join(SCRATCH, "scoreless-unmarked.jsonl")

    def strip(record):
        applied = applied_of(record)
        return bool(applied and applied.pop("degenerate", None) is not None)

    removed = rewrite(scoreless, unmarked, strip)
    code_u, out_u = guard(unmarked)
    write(args.out, "evidence-scoreless-unmarked.txt", [
        "SCORELESS SESSION, `degenerate` marker removed from %d record(s)" % removed,
        "=" * 70, "",
        "The same bytes otherwise. If this still went red, the guard would be "
        "reading something other than the marker and the marker would be "
        "load-bearing for nothing.", "",
        "$ python -m proxy.tools.check_variant_degeneracy <stripped ledger>",
        out_u.rstrip(), "exit=%d" % code_u, ""])

    # -- the scoring session ------------------------------------------------
    scoring_path = play("scoring", variant(99, "t-below"), scoreless=False)
    lines, records = report(scoring_path,
                            "SCORING SESSION -- the world scores; the floor is "
                            "above anything it can reach, so win_tighten fires "
                            "for a genuine shortfall")
    code_s, out_s = guard(scoring_path)
    lines += ["$ python -m proxy.tools.check_variant_degeneracy <ledger>",
              out_s.rstrip(), "exit=%d" % code_s, ""]
    write(args.out, "evidence-scoring.txt", lines)

    forged = os.path.join(SCRATCH, "scoring-forged.jsonl")
    state = {"planted": 0}

    def plant(record):
        applied = applied_of(record)
        if state["planted"] or not applied or applied.get("op") != "win_tighten":
            return False
        applied["degenerate"] = True
        state["planted"] = 1
        return True

    planted = rewrite(scoring_path, forged, plant)
    code_f, out_f = guard(forged)
    write(args.out, "evidence-scoring-forged.txt", [
        "SCORING SESSION with %d forged `degenerate` marker" % planted,
        "=" * 70, "",
        "The other half of the negative control. A guard that passes a scoring "
        "session because it cannot fire on one has not been tested on it.", "",
        "$ python -m proxy.tools.check_variant_degeneracy <forged ledger>",
        out_f.rstrip(), "exit=%d" % code_f, ""])

    print(json.dumps({"scoreless_exit": code, "unmarked_exit": code_u,
                      "scoring_exit": code_s, "forged_exit": code_f,
                      "markers_removed": removed, "markers_planted": planted},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
