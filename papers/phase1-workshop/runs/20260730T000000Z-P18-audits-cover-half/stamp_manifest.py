"""Stamp this run's MANIFEST.json over the bytes git publishes.

`files` was an empty list while fifteen artefacts sat in the directory, and
`baseline_gate` still recorded a gate state from before the run started. That is
the same defect this run was commissioned to fix, one directory down: a record
that describes a state its subject left.

Two disciplines, both learned the expensive way in `exam` on 2026-07-30 and
carried here rather than rediscovered:

* hash what git will publish, not the working copy. `git diff` cannot show the
  difference -- check-in normalisation makes a CRLF working copy equal to its LF
  blob on the way into the index -- so a stamp taken from disk can be wrong at
  the very commit that carries it, and nothing in git will say so.
* re-stamp by script. Six rounds of hand maintenance in the exam run left six
  stale hashes and one unlisted file.

Usage:  python stamp_manifest.py [--check]
"""
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "MANIFEST.json")
REPO = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=HERE,
                      capture_output=True, text=True, check=True).stdout.strip()
REL = os.path.relpath(HERE, REPO).replace(os.sep, "/")

EXCLUDED = {"MANIFEST.json", "stamp_manifest.py"}


def tracked():
    out = subprocess.run(["git", "ls-files", REL], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout
    names = [p[len(REL) + 1:] for p in out.split("\n") if p.strip()]
    return sorted(n for n in names if n not in EXCLUDED)


def published(name):
    """Bytes in the index. Falls back to disk for a file not yet added, and
    says so, because a stamp over an unstaged file is a promise about nothing."""
    r = subprocess.run(["git", "show", ":%s/%s" % (REL, name)], cwd=REPO,
                       capture_output=True)
    if r.returncode == 0:
        return r.stdout, True
    return open(os.path.join(HERE, name), "rb").read(), False


def main():
    m = json.load(open(MANIFEST, encoding="utf-8"))
    fresh, unstaged = [], []
    for name in tracked():
        data, from_index = published(name)
        if not from_index:
            unstaged.append(name)
        fresh.append({"path": name,
                      "sha256": hashlib.sha256(data).hexdigest()})
    if "--check" in sys.argv:
        old = {e["path"]: e["sha256"] for e in m.get("files") or []}
        new = {e["path"]: e["sha256"] for e in fresh}
        bad = False
        for p in sorted(set(old) | set(new)):
            if p not in old:
                print("UNLISTED  %s" % p); bad = True
            elif p not in new:
                print("ABSENT    %s" % p); bad = True
            elif old[p] != new[p]:
                print("STALE     %s" % p); bad = True
        print("MANIFEST %s (%d entries)" % ("STALE" if bad else "matches", len(new)))
        return 1 if bad else 0
    m["files"] = fresh
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(m, indent=1, sort_keys=True, ensure_ascii=False) + "\n")
    print("stamped %d entries" % len(fresh))
    if unstaged:
        print("WARNING hashed from the working copy, not the index: %s"
              % ", ".join(unstaged))
    return 0


if __name__ == "__main__":
    sys.exit(main())
