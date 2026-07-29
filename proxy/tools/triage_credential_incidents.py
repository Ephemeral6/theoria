"""Triage `credential_in_body` incidents without ever reading a credential out.

    python -m proxy.tools.triage_credential_incidents
    python -m proxy.tools.triage_credential_incidents --json out.json

807 of these incidents are on record and nobody knew whether any was real. The
audit was right not to look: deciding means reading request bodies, and reading
request bodies risks reading a key. But it could not stay open either --
**807 false positives is how an alarm gets switched off, which is how the real
leak gets through.**

So this decides it by shape and by hash, and never by eye.

## What leaves this module

Per matched fragment: which alternative of the heuristic fired, its length, its
character-class profile, the field name it sat under, and **`sha256(fragment)`**.
Never the fragment. The printed report is counts only.

## How a real leak would be recognised

`sha256` of each fragment is compared against `sha256` of the live key, read
through `arc-recon/client.load_api_key`. Equality is proof; inequality over the
whole corpus is proof of absence for that key. Neither comparison requires the
value to be displayed, written, or returned.

**If any fragment matches, that is an incident, not a heuristic bug.** Tighten
nothing until it has been handled -- the ticket is explicit that getting that
order backwards is the expensive mistake.

## The red line

CLAUDE.md's sealing discipline, verbatim: the key's value goes into no tracked
file, no log, no report, not once. This module holds it only as a digest, and
the digest of a 36-character secret is not a way back to it.
"""

import argparse
import collections
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "arc-recon"))
sys.path.insert(0, REPO)

from proxy.redact import _KEYISH                                # noqa: E402

#: The heuristic's three alternatives, named so a report can say which fired.
SHAPES = [
    ("sk_prefixed", re.compile(r"sk-[A-Za-z0-9_\-]{16,}")),
    ("uuid", re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
                        r"-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")),
    ("long_alnum", re.compile(r"[A-Za-z0-9]{32,}")),
]

#: Field names whose contents are known to be UUID-shaped and harmless. Named
#: rather than pattern-matched, because "it looked like an id" is exactly the
#: reasoning that would excuse a real key sitting in an unexpected field.
BENIGN_FIELDS = ("guid", "card_id", "game_id", "run_id", "scorecard_id")


def key_digest():
    """sha256 of the live key, or None if there is no `.env` here.

    Returns a digest and nothing else. The value is never returned, printed,
    stored, or logged.
    """
    try:
        from client import load_api_key
        return hashlib.sha256(load_api_key().encode("utf-8")).hexdigest()
    except Exception:
        return None


def profile(fragment):
    """Shape metadata for one match. No content."""
    return {
        "len": len(fragment),
        "digits": sum(c.isdigit() for c in fragment),
        "alpha": sum(c.isalpha() for c in fragment),
        "upper": sum(c.isupper() for c in fragment),
        "hyphens": fragment.count("-"),
        "sha256": hashlib.sha256(fragment.encode("utf-8")).hexdigest(),
        "shape": next((n for n, p in SHAPES if p.fullmatch(fragment)), "other"),
    }


def _walk(node, path=""):
    """Yield (field_path, string) for every string in a nested structure."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, "%s.%s" % (path, k) if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk(v, "%s[%d]" % (path, i))
    elif isinstance(node, str):
        yield path, node


def scan_stream(path, digest):
    """Triage one ledger. Returns aggregate rows -- never any fragment."""
    rows, incidents = [], 0
    with open(path, "rb") as fh:
        for raw in fh:
            stripped = raw.strip()
            if not stripped:
                continue
            try:
                rec = json.loads(stripped.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if rec.get("event") == "incident" and \
                    rec.get("kind") == "credential_in_body":
                incidents += 1
            body = rec.get("request", {}).get("body") if isinstance(
                rec.get("request"), dict) else None
            for field, text in _walk(body if body is not None else rec):
                for m in _KEYISH.finditer(text):
                    frag = m.group(0)
                    p = profile(frag)
                    p["field"] = field.split(".")[-1][:40]
                    p["benign_field"] = p["field"] in BENIGN_FIELDS
                    p["is_the_key"] = (digest is not None
                                       and p["sha256"] == digest)
                    p["file"] = os.path.relpath(path, REPO).replace("\\", "/")
                    rows.append(p)
    return rows, incidents


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", metavar="PATH",
                    help="write the metadata rows (no fragments) to PATH")
    ap.add_argument("--root", default=REPO)
    args = ap.parse_args()

    digest = key_digest()
    rows, incidents, files = [], 0, 0
    for dirpath, dirs, names in os.walk(args.root):
        dirs[:] = [d for d in dirs
                   if d not in (".git", ".worktrees", "__pycache__", "node_modules")]
        for name in names:
            if not name.endswith(".jsonl"):
                continue
            files += 1
            r, inc = scan_stream(os.path.join(dirpath, name), digest)
            rows.extend(r)
            incidents += inc

    real = [r for r in rows if r["is_the_key"]]
    by_shape = collections.Counter(r["shape"] for r in rows)
    by_field = collections.Counter(r["field"] for r in rows)
    benign = sum(1 for r in rows if r["benign_field"])

    print("scanned %d jsonl file(s); %d credential_in_body incident record(s)"
          % (files, incidents))
    print("heuristic matches: %d" % len(rows))
    for shape, n in by_shape.most_common():
        print("   %-12s %d" % (shape, n))
    print("under a known-benign id field: %d of %d (%.1f%%)"
          % (benign, len(rows), 100.0 * benign / len(rows) if rows else 0.0))
    print("top fields: %s" % ", ".join("%s×%d" % (f, n)
                                        for f, n in by_field.most_common(6)))
    if digest is None:
        print("\nNO .env HERE -- the hash comparison did not run. That is "
              "'not checked', not 'clean'; rerun where the key lives.")
    elif real:
        print("\n*** %d FRAGMENT(S) HASH TO THE LIVE KEY. This is an incident, "
              "not a heuristic defect. Handle it before touching the "
              "heuristic. ***" % len(real))
        for r in real[:10]:
            print("    %s field=%s len=%d" % (r["file"], r["field"], r["len"]))
    else:
        print("\nno fragment hashes to the live key: %d matches, 0 real. "
              "The heuristic is reporting noise." % len(rows))

    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"files": files, "incidents": incidents,
                       "matches": len(rows), "real": len(real),
                       "by_shape": dict(by_shape), "benign_field": benign,
                       "key_digest_available": digest is not None,
                       "rows": rows},
                      fh, indent=2, sort_keys=True, ensure_ascii=False)
            fh.write("\n")
        print("metadata (no fragments) -> %s" % args.json)
    return 1 if real else 0


if __name__ == "__main__":
    raise SystemExit(main())
