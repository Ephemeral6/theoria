"""Recompute every hash in figures/SOURCES.sha256 and report drift.

V-26 was asked one question about this file — do any of the drifted entries
point at a fuzzlab artifact — and the answer is no, because none of the entries
point at fuzzlab at all. The rest of the output is reported to the V-23 holder
rather than acted on: `figures/` is not this territory.

    python fuzzlab/runs/20260731T000000Z-V26-.../sources_audit.py    # from the repo root
"""

import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
MANIFEST = os.path.join(ROOT, "figures", "SOURCES.sha256")


def main() -> int:
    ok, drifted, missing, territories = 0, [], [], {}
    with open(MANIFEST, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            digest, rel = line.split()[0], line.split()[1]
            territories[rel.split("/")[0]] = territories.get(rel.split("/")[0], 0) + 1
            path = os.path.join(ROOT, rel)
            if not os.path.exists(path):
                missing.append(rel)
                continue
            with open(path, "rb") as source:
                actual = hashlib.sha256(source.read()).hexdigest()
            if actual == digest:
                ok += 1
            else:
                drifted.append((rel, digest, actual))

    print("entries by territory:")
    for name in sorted(territories):
        print("  %-16s %d" % (name, territories[name]))
    print()
    print("fuzzlab entries: %d" % territories.get("fuzzlab", 0))
    print("match %d, drifted %d, missing %d" % (ok, len(drifted), len(missing)))
    for rel, want, got in drifted:
        print("  DRIFT %s" % rel)
        print("        manifest %s" % want)
        print("        on disk  %s" % got)
        # A CRLF checkout would explain a hash mismatch without any real drift,
        # so ask git what the committed bytes are rather than assuming.
        blob = subprocess.run(["git", "show", "HEAD:" + rel], cwd=ROOT,
                              capture_output=True).stdout
        committed = hashlib.sha256(blob).hexdigest()
        print("        committed %s  (%s)"
              % (committed,
                 "same as disk — committed drift, not a checkout effect"
                 if committed == got else "differs from disk — checkout effect"))
    for rel in missing:
        print("  MISSING %s" % rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())
