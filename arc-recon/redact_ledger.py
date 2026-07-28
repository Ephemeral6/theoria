"""INC-008 remediation: strip cookie VALUES from the call ledger, keep the names.

`data/recon_ledger.jsonl` is append-only, and this edits it. That needs a reason
better than tidiness, and there is one: the ledger's own invariant, stated in
`client.py`'s docstring and enforced by `_record`, is that **the credential never
reaches disk** -- `X-API-Key` has always been written as `<redacted>`. The
stickiness probe bypassed `_record` and wrote the raw `Set-Cookie` header, which
carries the values of `AWSALBAPP-*` (backend routing pins) and `GAMESESSION`
(a bearer token for a live game session). The ledger is tracked, and Phase 4
publishes every tracked file.

So this is not a rewrite of the record. It restores the invariant the record was
always supposed to have, and it is deliberately minimal:

  * only the `set_cookie` field is touched, and only its value;
  * the cookie NAMES are preserved in `set_cookie_names`, so every conclusion
    the field supported ("the server issued a GAMESESSION here", "this arm was
    echoing four pins by round 3") survives verbatim;
  * each edited entry is marked `redacted: "INC-008"`, so the edit is visible in
    the file rather than inferred from a diff;
  * nothing else in any entry changes -- not the status, not the response body,
    not the ordering.

WHAT THIS DOES NOT FIX. The values are already in git history (commit 29c631e,
pushed). Removing them there means rewriting a published branch, which is
destructive, affects anyone who has fetched it, and is not a call this script
makes. The exposure is bounded: these are session cookies for development-pile
games, the sessions are abandoned, and no sealed game is involved. Recorded in
INC-008 for the owner to decide.

    python redact_ledger.py --check     # report, change nothing
    python redact_ledger.py --apply
"""

import argparse
import json
import os
import shutil
import sys
import time
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from client import DATA_DIR, cookie_names        # noqa: E402

LEDGER_PATH = os.path.join(DATA_DIR, "recon_ledger.jsonl")
MARKER = "<redacted INC-008>"


def scan(path: str = LEDGER_PATH) -> Dict[str, Any]:
    """Which entries carry a cookie value? Values are counted, never returned."""
    offenders: List[Dict[str, Any]] = []
    total = 0
    for number, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        total += 1
        entry = json.loads(line)
        raw = entry.get("set_cookie")
        if isinstance(raw, str) and raw and raw != MARKER:
            offenders.append({"line": number, "t": entry.get("t"),
                              "note": entry.get("note"),
                              "names": sorted(set(cookie_names(raw)))})
    return {"total_lines": total, "entries_with_values": len(offenders),
            "offenders": offenders}


def apply(path: str = LEDGER_PATH) -> Dict[str, Any]:
    """Rewrite in place via a temp file, keeping a .pre-INC-008 copy alongside.

    The backup is deliberately NOT tracked (see .gitignore): it exists so the
    operator can verify the redaction locally, not so the values get a second
    home in the repository.
    """
    report = scan(path)
    if not report["entries_with_values"]:
        return {**report, "changed": 0, "note": "already clean"}

    backup = path + ".pre-INC-008"
    shutil.copy2(path, backup)
    temp = path + ".redacting"
    changed = 0
    # Byte-level, so an untouched entry is byte-IDENTICAL afterwards. Reading and
    # re-serialising every line would also rewrite the 790 lines that carry CRLF
    # from a checkout conversion, turning a 55-line fix into a whole-file diff --
    # and making "nothing else changes" false in the one place where the claim
    # has to be checkable.
    with open(path, "rb") as source, open(temp, "wb") as sink:
        for raw_line in source:
            body, ending = raw_line, b""
            for candidate in (b"\r\n", b"\n"):
                if raw_line.endswith(candidate):
                    body = raw_line[:-len(candidate)]
                    ending = candidate
                    break
            if not body.strip():
                sink.write(raw_line)
                continue
            entry = json.loads(body.decode("utf-8"))
            value = entry.get("set_cookie")
            if isinstance(value, str) and value and value != MARKER:
                entry["set_cookie_names"] = sorted(set(cookie_names(value)))
                entry["got_set_cookie"] = True
                entry["set_cookie"] = MARKER
                entry["redacted"] = "INC-008"
                changed += 1
                sink.write(json.dumps(entry, sort_keys=True,
                                      ensure_ascii=True).encode("utf-8"))
                sink.write(ending or b"\n")
            else:
                sink.write(raw_line)
    os.replace(temp, path)
    return {**report, "changed": changed, "backup": backup,
            "t": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(prog="redact_ledger.py",
                                     description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="report and change nothing (the default)")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)

    if not args.apply:
        report = scan()
        print("  %d ledger lines, %d carry a cookie value"
              % (report["total_lines"], report["entries_with_values"]))
        for row in report["offenders"][:5]:
            print("    line %-5d %s  names=%s"
                  % (row["line"], row["t"], ",".join(row["names"])))
        if report["entries_with_values"] > 5:
            print("    ... and %d more" % (report["entries_with_values"] - 5))
        print("  run with --apply to redact")
        return 1 if report["entries_with_values"] else 0

    result = apply()
    print("  redacted %d entries of %d lines; backup at %s"
          % (result["changed"], result["total_lines"],
             os.path.basename(result.get("backup", "-"))))
    after = scan()
    print("  re-scan: %d entries still carrying a value"
          % after["entries_with_values"])
    return 0 if after["entries_with_values"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
