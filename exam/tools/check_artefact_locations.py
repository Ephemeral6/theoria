"""No tracked generated artefact may record where its builder stood.

`exam/artifacts/build_manifest.json` recorded twelve absolute paths -- four
papers times `sheet_path` / `key_path` / `cheater_brief_path` -- naming whichever
worktree last ran `build_papers`. The cost was never a typo: every delivery in
this territory carried twelve lines of pseudo-diff whose two sides mean the same
thing, and `exam/tools/archive_run.py` folds this file into the manifest it
writes for each archived run, so the leak reaches the provenance canon and from
there a Phase 4 release manifest that publishes every tracked file.

What this checks, and what it deliberately does not:

* **Checked.** Every tracked file under `exam/artifacts/` is scanned for values
  that can only be true on one machine -- Windows or POSIX absolute paths, the
  building user's home directory, a temporary directory, or a `.worktrees/`
  segment. These are the channel through which a build's location reaches its
  output, and the scan is exhaustive over that channel.
* **Not checked.** Whether two builds in two different directories agree byte
  for byte. That is the empirical form of the same question and it catches
  channels nobody enumerated; it lives in `exam/verify.py`'s `location` stage.
  This scan is the cheap always-on half, not a replacement for it.

`exam/verify.py`'s determinism stage cannot see any of this by construction: it
compares two in-process builds' sheet digests and never reads
`build_manifest.json` at all (`grep -n build_manifest exam/verify.py` is empty).
So the artefacts it certifies as deterministic are deterministic -- the marked
sheets really are location-independent -- and this file covers a dimension that
stage was never measuring. That distinction is worth keeping straight: the
determinism gate was not falsely green, it was answering a narrower question.

    python -m exam.tools.check_artefact_locations        # 0 clean, 1 findings
"""
from __future__ import annotations

import getpass
import json
import os
import re
import subprocess
import sys
from typing import List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SCANNED = "exam/artifacts"

#: A drive-letter path, a POSIX path under a home or temp root, or a worktree
#: segment. Deliberately not "any string containing a slash": repo-relative
#: paths are the fix, so they must not trip this.
PATTERNS: List[Tuple[str, "re.Pattern[str]"]] = [
    ("windows absolute path", re.compile(r"[A-Za-z]:[\\/]")),
    ("posix home path", re.compile(r"/(?:home|Users)/[^\"\s]+")),
    ("temp directory", re.compile(r"(?i)(?:/tmp/|[\\/]Temp[\\/]|TMPDIR)")),
    ("worktree segment", re.compile(r"[\\/]?\.worktrees[\\/]")),
    ("backslash path separator", re.compile(r"[A-Za-z0-9_.\-]\\[A-Za-z0-9_.\-]")),
]


def _username_pattern():
    """The building user's name, which is location by another route.

    Skipped when the name is too short or too common to search for without
    matching ordinary prose -- a false red here would be worse than the gap,
    because the absolute-path patterns already catch the paths it would appear in.
    """
    try:
        user = getpass.getuser()
    except Exception:                                     # pragma: no cover
        return None
    if len(user) < 4:
        return None
    return ("building user's name", re.compile(re.escape(user)))


def tracked_artefacts() -> List[str]:
    out = subprocess.run(["git", "ls-files", SCANNED], cwd=REPO,
                         capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p.strip()]


def _searchable(rel: str, raw: str) -> str:
    """What to search: decoded string values for JSON, raw text otherwise.

    The first version of this scanner searched raw bytes and reported seven
    findings in four exam papers, every one of them false. JSON escapes a
    newline as the two characters backslash-n, so a paper whose prose contains
    "asked:" followed by a line break literally holds `asked:
` on disk --
    which matches a drive-letter pattern and a backslash-separator pattern
    alike. A location scanner that fires on ordinary prose would be turned off
    within a day, so it decodes first and searches the values a reader would
    actually see.
    """
    if not rel.endswith(".json"):
        return raw
    try:
        doc = json.loads(raw)
    except ValueError:
        return raw
    found: List[str] = []

    def walk(node):
        if isinstance(node, str):
            found.append(node)
        elif isinstance(node, dict):
            for k, v in node.items():
                found.append(str(k))
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(doc)
    return chr(10).join(found)


def scan() -> List[Tuple[str, str, str]]:
    """-> [(path, what, the offending text)]"""
    patterns = list(PATTERNS)
    user = _username_pattern()
    if user:
        patterns.append(user)
    findings: List[Tuple[str, str, str]] = []
    for rel in tracked_artefacts():
        full = os.path.join(REPO, rel)
        if not os.path.exists(full):
            continue
        try:
            raw = open(full, encoding="utf-8").read()
        except (UnicodeDecodeError, OSError):
            continue
        text = _searchable(rel, raw)
        for what, rx in patterns:
            m = rx.search(text)
            if m:
                start = max(0, m.start() - 30)
                findings.append((rel, what, text[start:m.end() + 40]
                                 .replace("\n", " ")))
    return findings


def main(argv=None) -> int:
    findings = scan()
    n = len(tracked_artefacts())
    if not findings:
        print("artefact locations: %d tracked files under %s, none records "
              "where it was built" % (n, SCANNED))
        return 0
    print("artefact locations: %d finding(s) in %d tracked files under %s"
          % (len(findings), n, SCANNED))
    for rel, what, sample in findings:
        print("  %-52s %-24s %s" % (rel, what, sample[:90]))
    print("\nA tracked generated artefact must not record where its builder "
          "stood: it churns on every rebuild, it is a merge-conflict generator "
          "between two branches that agree, and archive_run.py carries it into "
          "the release manifest. Fix the generator, then regenerate -- generated "
          "files are never hand-edited.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
