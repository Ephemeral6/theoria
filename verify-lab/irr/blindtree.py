"""Build a judging tree with the answer key removed, then measure what is left.

V15 exported `git archive HEAD` minus `verify-lab/` and called the judges blind.
Its own adversarial pass measured the breach: `PARTNER_SYNC.md` is tracked, sits
at the root, and carries V11's aggregate (`有负控「否」35`), V14's `FNR 32%`, and
a per-file probe verdict on the one false positive in the pinned matrix. 29 of
126 judged paths (23%) were named in a tracked file that also discusses negative
controls; the exposed group's present rate was 0.55 against 0.34, p = 0.055.

    python verify-lab/irr/blindtree.py --out <dir>          # build + measure
    python verify-lab/irr/blindtree.py --out <dir> --json <f>

Two classes of file mention negative controls, and only one of them is a leak:

  **answer key** -- a file carrying V11/V14/V15's own verdicts, counts or matrix.
      `PARTNER_SYNC.md`, `monitor/board/`, `monitor/inbox/`, `monitor/bus/`,
      `monitor/mailbox/`, `monitor/audit/`, `monitor/ci/`, `monitor/state.json`,
      and `verify-lab/` itself. All removed.
  **domain content** -- a file describing a negative control this repository
      actually runs: `fuzzlab/MUTATION.md`, `cold-start-a3/README.md`,
      `papers/phase1-workshop/PAPER.md` §4.3. Removing these would delete the
      evidence a judge is *supposed* to weigh, so they stay, and the residue is
      measured and published instead of being asserted away.

The removal list is a prefix list, not a content filter, so it is auditable: a
reader can check it against `git ls-files` without running anything.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

#: Prefixes deleted from the judging tree. Every one of these carries, or can
#: carry, a verdict of V11 / V14 / V15 rather than evidence about the repository.
STRIP = (
    "verify-lab/",
    "PARTNER_SYNC.md",
    "monitor/board/",
    "monitor/inbox/",
    "monitor/mailbox/",
    "monitor/bus/",
    "monitor/audit/",
    "monitor/ci/",
    "monitor/state.json",
    "monitor/board.log",
)

#: A file containing one of these could tell a judge what the answer is.
TOPIC = ("负控", "negative control", "negative-control", "FNR", "混淆矩阵",
         "confusion matrix", "KNOWN_GAPS", "有负控", "退出码诚实")

#: ... and one of these means it is talking about *this lab's* verdicts, not
#: about a control the repository runs.
VERDICT_MARKERS = ("有负控", "退出码诚实", "混淆矩阵", "KNOWN_GAPS", "FNR",
                   "confusion matrix", "negative-control census", "负控普查")

TEXT_EXT = (".md", ".json", ".txt", ".jsonl")


def tracked(root: str) -> List[str]:
    out = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True,
                         text=True, encoding="utf-8", check=True)
    return [l.strip().replace("\\", "/") for l in out.stdout.splitlines() if l.strip()]


def build(root: str, out: str) -> Dict[str, object]:
    """Copy every tracked file except the strip list. Returns what was removed."""
    if os.path.exists(out):
        shutil.rmtree(out)
    kept: List[str] = []
    removed: List[str] = []
    for rel in tracked(root):
        if any(rel == p or rel.startswith(p) for p in STRIP):
            removed.append(rel)
            continue
        src = os.path.join(root, rel)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        kept.append(rel)
    return {"kept": len(kept), "removed": removed}


def residue(out: str, paths: Sequence[str]) -> Dict[str, object]:
    """Which sampled paths are still named in a topic-bearing file, and where.

    Reported in two tiers, because they are not the same risk: a file that also
    carries this lab's *verdict vocabulary* could hand a judge an answer; a file
    that merely discusses a control the repository runs is evidence.
    """
    named: Dict[str, List[str]] = {p: [] for p in paths}
    verdicty: Dict[str, List[str]] = {p: [] for p in paths}
    for base, _dirs, files in os.walk(out):
        for name in files:
            if not name.endswith(TEXT_EXT):
                continue
            full = os.path.join(base, name)
            rel = os.path.relpath(full, out).replace("\\", "/")
            try:
                text = open(full, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if not any(w in text for w in TOPIC):
                continue
            hot = any(w in text for w in VERDICT_MARKERS)
            for path in paths:
                if path in text:
                    named[path].append(rel)
                    if hot:
                        verdicty[path].append(rel)
    return {
        "sampled": len(paths),
        "named_in_topic_file": sorted(p for p in paths if named[p]),
        "named_in_verdict_file": sorted(p for p in paths if verdicty[p]),
        "where": {p: sorted(set(v)) for p, v in named.items() if v},
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--sample", help="sample.json, for the residue measurement")
    ap.add_argument("--json", metavar="OUT")
    args = ap.parse_args(argv)

    rep: Dict[str, object] = {"root": REPO, "out": args.out}
    rep["build"] = build(REPO, args.out)
    print("judging tree: %d files kept, %d removed"
          % (rep["build"]["kept"], len(rep["build"]["removed"])))  # type: ignore[index]
    if args.sample:
        paths = [r["path"] for r in json.load(open(args.sample, encoding="utf-8"))["rows"]]
        rep["residue"] = residue(args.out, paths)
        res = rep["residue"]
        print("residual exposure: %d/%d sampled paths named in a topic file; "
              "%d in a file carrying this lab's verdict vocabulary"
              % (len(res["named_in_topic_file"]), res["sampled"],      # type: ignore[index]
                 len(res["named_in_verdict_file"])))                    # type: ignore[index]
        for path in res["named_in_verdict_file"]:                       # type: ignore[index]
            print("   HOT  %-55s %s" % (path, ", ".join(res["where"][path][:3])))  # type: ignore[index]
    if args.json:
        with open(args.json, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(rep, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
