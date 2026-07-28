"""The call ledger's invariant, asserted on the file rather than on its writers.

```bash
cd arc-recon && python tools/ledger_invariants.py            # our ledger
cd arc-recon && python tools/ledger_invariants.py --all      # every track's
cd arc-recon && python tools/ledger_invariants.py --json
```

## Why this is not a check inside a writer

`recon_ledger.jsonl` is tracked, Phase 4 publishes every tracked file, and its
stated invariant is that **no credential ever reaches it**. That discipline lived
in `client._record`, which writes `X-API-Key` as `<redacted>`. Then
`probe_stickiness.py` needed response headers `_record` did not capture, opened
the file itself, and wrote 55 raw `Set-Cookie` headers — values included, one of
them a bearer token for a live game session — straight past the discipline and
into a pushed commit. That is INC-008, and its recorded lesson is the whole
argument for this file:

> "A rule enforced in one function holds only for callers of that function. The
> probe wrote its own ledger writer because it needed response headers `_record`
> did not capture, which is exactly when a second writer appears and exactly when
> the invariant needs re-checking rather than assuming it was inherited."

The repair is **not** to make `_record` the only writer. The second writer is
still there, still legitimate — a probe that needs response headers is not abuse
— and the invariant holds anyway, because it moved onto the artefact. Single
entry points are worth it only where a capability can genuinely be taken away
(`proxy`'s no-bypass seal works because the arm never holds the credential at
all); everywhere else "one writer" is a wish about code organisation, and the
next instrument that needs a field the writer does not carry will go around it.

So: **who can write the ledger is not enumerable, and does not need to be.** What
is on disk is checkable.

## The four tiers, and what each can and cannot catch

**Tier 1 — field-scoped, exact.** The fields whose contents are known: every
`request_headers` value, the cookie-name lists, `set_cookie`, the URL's query
string. Zero heuristics, zero false positives, and it is the tier that would
have caught INC-008 on the first line written.

**Tier 2 — the literal secret.** Does any byte of the file contain the actual
`ARC_API_KEY`? Exact, unfoolable by a field name nobody predicted, and the only
tier that does not depend on knowing the schema. It needs `.env`, which is
gitignored and absent in a fresh worktree, so when the key cannot be loaded this
tier reports `unavailable` **and the report says so** rather than counting a
check that did not run as a check that passed. (`client.load_api_key` already
walks back to the main checkout, so it usually can.)

**Tier 3 — undeclared credential-shaped fields.** Any key matching
`cookie|token|auth|secret|session|bearer|credential|password|api[-_]?key` that is
not in `DECLARED_FIELDS`. This is the tier aimed at the *next* INC-008: a writer
that adds `session_token` gets a red build and has to declare the field, which is
the moment the invariant gets re-checked. It fails closed — an unrecognised
credential-shaped field is a violation, not a warning.

**Tier 4 — bearer/JWT shapes in the fields that could carry one.** `eyJ` (base64
`{"`) and `Bearer ` inside header values, cookie fields and URLs. Deliberately
**not** applied to `response_body`: game frames are arbitrary data, a base64
prefix there is not evidence of anything, and a check that cries wolf on every
run is one nobody reads. Tier 2 covers the response body for the credential that
actually matters.

## Two rules this file follows without exception

**Values are counted and located, never returned.** A violation is
`(line, field, shape)`. A scanner that echoed the offending value into a report
would put the credential in a second file, and reports get pasted into commit
messages.

**Every check has a negative control.** `test_ledger_invariants.py` plants a
synthetic offender of each shape and asserts the scanner goes red, then asserts a
clean row stays green. `test_hygiene.py`'s own docstring is the reason: INC-003
is the case where a comparison that could not fail reported PASS for two runs
that had both died.
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
ARC_RECON = os.path.dirname(HERE)
sys.path.insert(0, ARC_RECON)

from client import DATA_DIR, REDACTED, _COOKIE_TOKEN, load_api_key   # noqa: E402

LEDGER_PATH = os.path.join(DATA_DIR, "recon_ledger.jsonl")

#: Ledgers other tracks keep, mirroring `contamination.OTHER_LEDGERS`. Read,
#: never written. Absent ones are reported as absent rather than skipped: a
#: file that is not there is not a file that is clean.
OTHER_LEDGERS: Tuple[str, ...] = (
    os.path.join(ARC_RECON, os.pardir, "baseline-arms", "ledger.jsonl"),
    os.path.join(ARC_RECON, os.pardir, "baseline-arms", "probe_log.jsonl"),
)

#: What a redacted value is allowed to look like. `client.REDACTED` is the
#: forward form; `<redacted INC-008>` is what `redact_ledger.py` wrote over the
#: 55 lines it repaired. Prefix-matched so a future incident marker inherits it.
REDACTION_PREFIX = "<redacted"

#: Header names whose value must be redacted outright.
SECRET_HEADERS = ("x-api-key", "authorization", "cookie", "proxy-authorization")

#: Fields that carry cookie NAMES and nothing else. A name is an RFC 6265 token,
#: so anything containing `=` is a value that got through.
COOKIE_NAME_FIELDS = ("set_cookie_names", "cookies_held", "cookies_sent",
                      "cookies_held_after")

#: Every credential-shaped field this ledger is known to contain, with the tier-1
#: rule that governs it. Tier 3 refuses any *other* field whose name looks like a
#: credential — that refusal is the point, so this list is a declaration and not
#: a suppression: adding to it is how a writer says "I thought about this one".
DECLARED_FIELDS: Dict[str, str] = {
    "request_headers": "every value redacted if the header name is secret",
    "set_cookie": "the redaction marker, or absent",
    "set_cookie_names": "bare cookie tokens",
    "cookies_held": "bare cookie tokens",
    "cookies_sent": "bare cookie tokens",
    "cookies_held_after": "bare cookie tokens",
    "cookies_enabled": "boolean",
    "got_set_cookie": "boolean",
}

CREDENTIAL_NAME = re.compile(
    r"cookie|token|auth|secret|session|bearer|credential|password|api[-_]?key",
    re.IGNORECASE)

#: A JWT's first three bytes base64 are `eyJ`; `Bearer ` is the RFC 6750 prefix.
BEARER_SHAPE = re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}|\bBearer\s+\S{8,}")

#: `?key=...` / `&token=...` in a URL.
QUERY_PARAM = re.compile(r"[?&]([^=&#]+)=([^&#]*)")


class LedgerInvariantError(RuntimeError):
    """Raised by `assert_clean`. Carries counts and locations, never values."""


def _is_redacted(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(REDACTION_PREFIX)


def _violation(line: int, field: str, shape: str) -> Dict[str, Any]:
    """The only record shape this module emits. No value, ever."""
    return {"line": line, "field": field, "shape": shape}


# ----------------------------------------------------------------- the tiers

def _tier1_known_fields(number: int, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    headers = entry.get("request_headers")
    if isinstance(headers, dict):
        for name, value in sorted(headers.items()):
            if str(name).lower() in SECRET_HEADERS and not _is_redacted(value):
                out.append(_violation(number, "request_headers.%s" % name,
                                      "secret header carries a value"))
            elif isinstance(value, str) and BEARER_SHAPE.search(value):
                out.append(_violation(number, "request_headers.%s" % name,
                                      "bearer or JWT shape in a header value"))

    for field in COOKIE_NAME_FIELDS:
        names = entry.get(field)
        if names is None:
            continue
        if not isinstance(names, list):
            out.append(_violation(number, field, "cookie-name field is not a list"))
            continue
        for name in names:
            # A bare RFC 6265 token. `GAMESESSION=v1,eyJ...` is not one, which is
            # exactly the shape the redactor once let through as if it were a
            # name — see `client.cookie_names`' comment on the comma trap.
            if not _COOKIE_TOKEN.match(str(name)):
                out.append(_violation(number, field, "not a bare cookie token"))

    raw = entry.get("set_cookie")
    if isinstance(raw, str) and raw and not _is_redacted(raw):
        out.append(_violation(number, "set_cookie", "raw header retained"))

    url = entry.get("url")
    if isinstance(url, str):
        if BEARER_SHAPE.search(url):
            out.append(_violation(number, "url", "bearer or JWT shape in the URL"))
        for name, value in QUERY_PARAM.findall(url):
            if CREDENTIAL_NAME.search(name) and value and not _is_redacted(value):
                out.append(_violation(number, "url?%s" % name,
                                      "credential-shaped query parameter"))
    return out


def _tier3_undeclared_fields(number: int,
                             entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Fail closed on a credential-shaped field nobody declared.

    The tier aimed at the next INC-008 rather than the last one. A writer adding
    `session_token` does not have to be predicted, enumerated, or routed through
    anybody's function; it has to add a line to `DECLARED_FIELDS`, and that line
    is the moment somebody looks at whether the value is safe.
    """
    out: List[Dict[str, Any]] = []
    for name, value in sorted(entry.items()):
        if name in DECLARED_FIELDS or not CREDENTIAL_NAME.search(name):
            continue
        if value is None or isinstance(value, bool):
            continue
        out.append(_violation(number, name,
                              "undeclared credential-shaped field; add it to "
                              "DECLARED_FIELDS with the rule that governs it"))
    return out


def _tier4_bearer_shapes(number: int, entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Bearer/JWT shapes in the fields that could legitimately carry one.

    `response_body` is excluded on purpose: game frames are arbitrary data and a
    base64 prefix there is not evidence. Tier 2 is what covers the body.
    """
    out: List[Dict[str, Any]] = []
    for field in ("note", "final_url", "transport_error") + COOKIE_NAME_FIELDS:
        value = entry.get(field)
        parts: Iterable[Any] = value if isinstance(value, list) else [value]
        for part in parts:
            if isinstance(part, str) and BEARER_SHAPE.search(part):
                out.append(_violation(number, field, "bearer or JWT shape"))
    return out


def _tier2_literal_secret(number: int, line: str,
                          secret: Optional[str]) -> List[Dict[str, Any]]:
    if secret and secret in line:
        return [_violation(number, "<whole line>", "contains the live API key")]
    return []


def _entry_violations(number: int, entry: Dict[str, Any], line: str,
                      secret: Optional[str]) -> List[Dict[str, Any]]:
    return (_tier1_known_fields(number, entry)
            + _tier2_literal_secret(number, line, secret)
            + _tier3_undeclared_fields(number, entry)
            + _tier4_bearer_shapes(number, entry))


# ---------------------------------------------------------------- the scanner

def _load_secret() -> Tuple[Optional[str], str]:
    """The live key, for tier 2, or `None` with the reason it is unavailable.

    Never returned to a caller that logs. `scan` uses it for one `in` test and
    drops it; it is not stored in the report, and the report says only whether
    the tier ran.
    """
    try:
        return load_api_key(), "loaded"
    except Exception as exc:                                   # noqa: BLE001
        return None, "unavailable (%s)" % type(exc).__name__


def scan(path: str = LEDGER_PATH,
         secret: Optional[str] = None,
         check_secret: bool = True) -> Dict[str, Any]:
    """Every violation in one ledger file. Locations and shapes; no values.

    `check_secret=False` is for the negative controls, which must not depend on
    a `.env` being present, and for scanning another track's ledger where the
    key comparison is the same test and the cost is a whole extra read.
    """
    secret_state = "not requested"
    if check_secret and secret is None:
        secret, secret_state = _load_secret()
    elif check_secret:
        secret_state = "supplied by caller"

    violations: List[Dict[str, Any]] = []
    total = 0
    malformed: List[int] = []
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                entry = json.loads(line)
            except ValueError:
                malformed.append(number)
                # Still worth the literal-secret test: a line this module cannot
                # parse is a line whose contents nothing else here has checked.
                violations.extend(_tier2_literal_secret(number, line, secret))
                continue
            if not isinstance(entry, dict):
                malformed.append(number)
                continue
            violations.extend(_entry_violations(number, entry, line, secret))

    return {
        "path": os.path.relpath(path, os.path.dirname(ARC_RECON)).replace(os.sep, "/"),
        "total_lines": total,
        "malformed_lines": malformed,
        "violations": violations,
        "violation_count": len(violations),
        "clean": not violations and not malformed,
        # Named so a reader can tell a check that passed from one that did not
        # run. The whole point of INC-003 was a comparison that could not fail
        # being read as a comparison that passed.
        "live_key_comparison": secret_state,
    }


def scan_rows(rows: Iterable[Tuple[int, Dict[str, Any]]],
              secret: Optional[str] = None) -> List[Dict[str, Any]]:
    """The predicate alone, over `(line_number, entry)` pairs.

    Exists so the negative controls can plant a synthetic offender without
    writing one to disk — a fixture file holding a credential-shaped string is
    the thing this module exists to prevent, even when the string is fake.
    """
    out: List[Dict[str, Any]] = []
    for number, entry in rows:
        line = json.dumps(entry, sort_keys=True, ensure_ascii=True)
        out.extend(_entry_violations(number, entry, line, secret))
    return out


def audit_all(path: str = LEDGER_PATH) -> Dict[str, Any]:
    """This ledger and every other track's, in one report.

    Shaped after `contamination.all_ledger_audit`, including its caveat: a clean
    result is evidence over the files scanned, not a proof over all traffic ever
    sent. Other tracks keep records this list does not name.
    """
    secret, secret_state = _load_secret()
    reports: Dict[str, Any] = {}
    first = scan(path, secret=secret)
    first["live_key_comparison"] = secret_state
    reports[first["path"]] = first

    for other in OTHER_LEDGERS:
        label = os.path.relpath(other, os.path.dirname(ARC_RECON)).replace(os.sep, "/")
        if not os.path.exists(other):
            reports[label] = {"path": label, "present": False, "clean": None,
                              "note": "not present in this checkout"}
            continue
        report = scan(other, secret=secret)
        report["present"] = True
        report["live_key_comparison"] = secret_state
        reports[label] = report

    scanned = [r for r in reports.values() if r.get("clean") is not None]
    return {
        "ledgers": reports,
        "ledgers_scanned": len(scanned),
        "all_clean": all(r["clean"] for r in scanned),
        "live_key_comparison": secret_state,
        "caveat": ("Evidence over the files scanned, not a proof over all "
                   "traffic ever sent: other tracks may keep records this list "
                   "does not name, and the live-key comparison does not run "
                   "where `.env` is absent."),
    }


def assert_clean(path: str = LEDGER_PATH) -> Dict[str, Any]:
    """`scan`, raising on any violation. The form a test or a gate wants."""
    report = scan(path)
    if not report["clean"]:
        raise LedgerInvariantError(
            "%s: %d violation(s) across %d line(s); first: %s"
            % (report["path"], report["violation_count"], report["total_lines"],
               report["violations"][:3] or report["malformed_lines"][:3]))
    return report


# ======================================================================= cli

def _print(report: Dict[str, Any]) -> None:
    print("  %-44s %5d lines  %s"
          % (report["path"], report["total_lines"],
             "clean" if report["clean"]
             else "%d VIOLATION(S)" % report["violation_count"]))
    for row in report["violations"][:8]:
        print("      line %-6d %-28s %s" % (row["line"], row["field"], row["shape"]))
    if report["violation_count"] > 8:
        print("      ... and %d more" % (report["violation_count"] - 8))
    for number in report["malformed_lines"][:5]:
        print("      line %-6d %-28s %s" % (number, "<whole line>", "not JSON"))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="ledger_invariants.py",
        description="assert the call ledger's invariant on the file itself")
    parser.add_argument("--all", action="store_true",
                        help="every track's ledger, not just this one")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("path", nargs="?", default=LEDGER_PATH)
    args = parser.parse_args(argv)

    if args.all:
        report = audit_all(args.path)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            for row in report["ledgers"].values():
                if row.get("present") is False:
                    print("  %-44s absent" % row["path"])
                else:
                    _print(row)
            print("  live key comparison: %s" % report["live_key_comparison"])
            print("  %s" % report["caveat"])
        return 0 if report["all_clean"] else 1

    report = scan(args.path)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print(report)
        print("  live key comparison: %s" % report["live_key_comparison"])
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
