"""P1REPLAYLIVE addendum -- run the frozen scorer over the tracked
theoria-arm live ledgers and the rebuilt archive canons, as monitor audit
evidence for the p1-scorer note.

Zero writes to any ledger: every invocation carries --no-incident
--no-artifact (proxy/DELIVERY_RULING.md par.5 records what happens without
them: score_run appends incidents and writes proxy/var/scores/, with no
idempotency key).  This is monitor's own audit output, not proxy's
deliverable; the reproduce commands are the evidence contract.
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

THEORIA_LEDGERS = [
    "theoria-arm/runs/20260731T1240Z-A3-level2-carried/ledger.jsonl",
    "theoria-arm/runs/20260731T1310Z-A3-level2-carried-r2/ledger.jsonl",
    "theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/ledger.jsonl",
    "theoria-arm/runs/20260731T1500Z-A3-sk48-carried-l1/ledger.jsonl",
]
CANONS = ["ar25", "g50t", "a7-g50t", "a7up-opus-g50t", "a7up-sonnet-g50t"]


def run_cli(args_list):
    proc = subprocess.run([sys.executable, "-m", "proxy.scoring"] + args_list,
                          cwd=REPO, capture_output=True, text=True)
    return {"argv": args_list, "exit": proc.returncode,
            "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()[-1000:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True, help="dir holding canon.<key>.jsonl")
    ap.add_argument("--out", default=HERE)
    args = ap.parse_args()

    report = {"freeze_fingerprint": run_cli(["--verify-only"]), "ledgers": {}}
    for rel in THEORIA_LEDGERS:
        report["ledgers"][rel] = run_cli(
            ["--ledger", os.path.join(REPO, rel), "--all", "--no-incident", "--no-artifact"])
    for key in CANONS:
        canon = os.path.join(args.scratch, "canon.%s.jsonl" % key)
        report["ledgers"]["canon.%s.jsonl (rebuilt, see regression_vs_archive.json)" % key] = run_cli(
            ["--ledger", canon, "--all", "--no-incident", "--no-artifact"])

    verdict_counts = {}
    for entry in report["ledgers"].values():
        for token in ("PASS", "FAIL", "UNDETERMINED"):
            verdict_counts[token] = verdict_counts.get(token, 0) + entry["stdout"].count(token)
    report["verdict_token_counts_in_stdout"] = verdict_counts
    report["all_exit_zero"] = all(e["exit"] == 0 for e in report["ledgers"].values())

    out_path = os.path.join(args.out, "score_corpus.json")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_exit_zero": report["all_exit_zero"],
                      "verdicts": verdict_counts}, indent=2, sort_keys=True))
    return 0 if report["all_exit_zero"] else 1


if __name__ == "__main__":
    sys.exit(main())
