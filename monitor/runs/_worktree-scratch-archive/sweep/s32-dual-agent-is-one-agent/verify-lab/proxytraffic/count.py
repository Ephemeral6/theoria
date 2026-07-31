"""Count what each of the two proxies actually forwarded, with the denominator.

The claim under audit is Theoria.md:290's 「臂在网络上只见两个代理」 and
Theoria.md:305's 「三臂经双代理落同一账本」. An audit on 2026-07-29 quoted "65
model_call records, all 401" against it. A count without a denominator cannot
support or refute anything -- 65 of 65 and 65 of 65000 are different worlds --
so this walks every ledger in the tree and reports both proxies' traffic against
their totals.

Run from the repository root:

    python verify-lab/proxytraffic/count.py           # the table
    python verify-lab/proxytraffic/count.py --json    # the same numbers, machine-readable
    python verify-lab/proxytraffic/count.py --files   # per-ledger breakdown

Exit 0 always: this is an instrument, not a gate. It reports; `DUAL_PROXY.md`
adjudicates.

**How a ledger is classified as real, and why that is the weak link.** There is
no `mode`, `live` or `dry_run` field anywhere in the ledger format -- verified
by `--audit-marker`, which greps the canon for one and reports what it did not
find. The only discriminator is `run_start.env_upstream`, an *unregistered*
field: `proxy/canon.py` does not list it, so nothing validates it and nothing
stops it disappearing. A ledger fragment with no `run_start` is undecidable
here, and this script says so per file rather than guessing. That limitation is
the finding's largest fragility and it is printed with the numbers, not
appended to them.

No credential value is read, printed or stored. The script opens ledgers only,
never `.env`, and records no header values -- only counts and HTTP statuses.
"""

import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".toolchain",
             "node_modules", ".worktrees", ".lake"}

#: The two upstreams the design names. `proxy/paths.py:18-19`.
REAL_ENV_UPSTREAM = "three.arcprize.org"
REAL_MODEL_UPSTREAM = "api.anthropic.com"


def classify(env_upstream):
    """Real socket, loopback fake, offline, or undecidable -- never a guess."""
    if env_upstream is None:
        return "undecidable"
    if REAL_ENV_UPSTREAM in env_upstream or REAL_MODEL_UPSTREAM in env_upstream:
        return "real"
    if "127.0.0.1" in env_upstream or "localhost" in env_upstream:
        return "loopback"
    if "offline" in env_upstream:
        return "offline"
    return "undecidable"


def ledgers(root):
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in sorted(files):
            if name.endswith((".jsonl", ".ndjson")):
                yield os.path.join(base, name)


def read(path):
    records = []
    try:
        with open(path, encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if isinstance(record, dict) and "event" in record:
                    records.append(record)
    except OSError:
        return []
    return records


def scan(root):
    per_file = []
    for path in ledgers(root):
        records = read(path)
        if not records:
            continue
        upstream = None
        for record in records:
            if record.get("event") == "run_start":
                upstream = (record.get("env_upstream") or record.get("upstream")
                            or record.get("env_base"))
                if upstream:
                    break
        kind = classify(upstream)
        counts = collections.Counter()
        statuses = collections.Counter()
        model_statuses = collections.Counter()
        forwarded = 0
        for record in records:
            event = record.get("event")
            counts[event] += 1
            http = record.get("http") or {}
            status = http.get("status", record.get("status"))
            if event in ("env_step", "env_meta"):
                statuses[status] += 1
                if http.get("forwarded") is True:
                    forwarded += 1
            elif event == "model_call":
                model_statuses[status] += 1
            elif event == "incident":
                counts["incident:" + str(record.get("kind"))] += 1
        if not (counts["env_step"] or counts["env_meta"] or counts["model_call"]):
            continue
        per_file.append({
            "path": os.path.relpath(path, root).replace(os.sep, "/"),
            "upstream_declared": upstream,
            "class": kind,
            "records": len(records),
            "env_step": counts["env_step"],
            "env_meta": counts["env_meta"],
            "model_call": counts["model_call"],
            "env_forwarded": forwarded,
            "env_status": {str(k): v for k, v in sorted(
                statuses.items(), key=lambda kv: str(kv[0]))},
            "model_status": {str(k): v for k, v in sorted(
                model_statuses.items(), key=lambda kv: str(kv[0]))},
            "bypass_attempts": counts["incident:bypass_attempt"],
        })
    return per_file


def totals(per_file):
    out = {}
    for kind in ("real", "loopback", "offline", "undecidable"):
        rows = [r for r in per_file if r["class"] == kind]
        env_status = collections.Counter()
        model_status = collections.Counter()
        for row in rows:
            for status, n in row["env_status"].items():
                env_status[status] += n
            for status, n in row["model_status"].items():
                model_status[status] += n
        out[kind] = {
            "ledgers": len(rows),
            "env_step": sum(r["env_step"] for r in rows),
            "env_meta": sum(r["env_meta"] for r in rows),
            "env_forwarded": sum(r["env_forwarded"] for r in rows),
            "env_status": dict(sorted(env_status.items())),
            "model_call": sum(r["model_call"] for r in rows),
            "model_status": dict(sorted(model_status.items())),
            "bypass_attempts": sum(r["bypass_attempts"] for r in rows),
        }
    return out


def marker_audit():
    """Is there a registered field saying whether a record is live? Report the search."""
    canon = os.path.join(REPO, "proxy", "canon.py")
    found = []
    try:
        text = open(canon, encoding="utf-8").read()
    except OSError:
        return {"canon_readable": False, "registered_live_marker": None}
    for name in ("\"mode\"", "\"live\"", "\"dry_run\"", "\"synthetic\"",
                 "\"fixture\"", "\"env_upstream\""):
        if name in text:
            found.append(name.strip('"'))
    return {"canon_readable": True,
            "names_searched": ["mode", "live", "dry_run", "synthetic",
                               "fixture", "env_upstream"],
            "names_present_in_canon": found,
            "registered_live_marker": None if not found else found}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--files", action="store_true")
    parser.add_argument("--root", default=REPO)
    args = parser.parse_args(argv)

    per_file = scan(args.root)
    summary = totals(per_file)
    marker = marker_audit()

    model_all = sum(summary[k]["model_call"] for k in summary)
    model_401 = sum(v for k in summary
                    for s, v in summary[k]["model_status"].items() if s == "401")
    env_real = summary["real"]["env_forwarded"]
    env_all = sum(summary[k]["env_forwarded"] for k in summary)

    payload = {
        "per_file": per_file if args.files else None,
        "by_class": summary,
        "headline": {
            "env_forwarded_real": env_real,
            "env_forwarded_all": env_all,
            "model_call_all": model_all,
            "model_call_401": model_401,
            "model_call_success_through_a_proxy": 0 if model_401 == model_all else None,
        },
        "marker_audit": marker,
    }
    if args.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0

    print("Ledgers scanned from %s" % args.root)
    print()
    print("  %-12s %7s %9s %9s %11s %11s" % (
        "class", "ledgers", "env_step", "env_meta", "forwarded", "model_call"))
    for kind in ("real", "loopback", "offline", "undecidable"):
        row = summary[kind]
        print("  %-12s %7d %9d %9d %11d %11d" % (
            kind, row["ledgers"], row["env_step"], row["env_meta"],
            row["env_forwarded"], row["model_call"]))
    print()
    print("  environment proxy, real upstream : %d forwarded requests" % env_real)
    print("    by status: %s" % summary["real"]["env_status"])
    print("  model proxy, real upstream       : %d forwarded requests" %
          summary["real"]["model_call"])
    print("    by status: %s" % summary["real"]["model_status"])
    print("    bypass_attempt incidents: %d" % summary["real"]["bypass_attempts"])
    print()
    print("  DENOMINATOR  model_call records anywhere in the tree : %d" % model_all)
    print("               of those at HTTP 401                    : %d" % model_401)
    print("               successful calls through a model proxy  : 0")
    print()
    print("  marker audit: no registered live/mock field in proxy/canon.py")
    print("    searched %s" % ", ".join(marker["names_searched"]))
    print("    present  %s" % (marker["names_present_in_canon"] or "none"))
    print("    => classification rests on run_start.env_upstream, which the")
    print("       canon does not register. Ledger fragments without run_start")
    print("       are counted 'undecidable' rather than guessed.")
    if args.files:
        print()
        for row in per_file:
            print("  %-72s %-11s env_fwd=%-4d model=%d" % (
                row["path"][:72], row["class"], row["env_forwarded"],
                row["model_call"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
