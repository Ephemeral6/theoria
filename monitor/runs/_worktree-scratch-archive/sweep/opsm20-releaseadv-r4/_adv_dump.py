"""Adversarial re-derivation: dump one classifier's full verdict over a FIXED tree.

    python _adv_dump.py <classifier-dir> <out.jsonl>

Deliberately different from _opsm20_classify.py in three ways that matter:
  * paths come from `git ls-files -z` (NUL-delimited), not `.split()` on
    whitespace -- a path with a space would silently become two bogus paths;
  * every field of every row is dumped, not just `class`, so a change in
    `verdict`/`evidence`/`review` cannot hide inside an unchanged class letter;
  * rulings are explicitly passed as {} for r4 so the comparison isolates the
    classifier from RULINGS.jsonl. A second pass runs with real rulings.
"""
import importlib
import json
import os
import subprocess
import sys

cls_dir = os.path.abspath(sys.argv[1])
out_path = os.path.abspath(sys.argv[2])
with_rulings = "--with-rulings" in sys.argv
root = os.path.dirname(cls_dir)   # classifier dir sits directly under the worktree

sys.path.insert(0, cls_dir)
for m in ("check_redlines", "enumerate"):
    sys.modules.pop(m, None)
R = importlib.import_module("check_redlines")
E = importlib.import_module("enumerate")
assert os.path.dirname(os.path.abspath(E.__file__)) == cls_dir, E.__file__
assert E.REPO_ROOT == root, (E.REPO_ROOT, root)

raw = subprocess.run(["git", "-C", root, "ls-files", "-z"],
                     capture_output=True, check=True).stdout
paths = sorted(p.decode("utf-8") for p in raw.split(b"\x00") if p)

try:
    if "rulings" in E.build.__code__.co_varnames[:E.build.__code__.co_argcount]:
        rows = E.build(paths, None if with_rulings else {})
    else:
        rows = E.build(paths)
except Exception as exc:
    print("!! build RAISED %s: %s" % (type(exc).__name__, exc))
    raise

assert len(rows) == len(paths), (len(rows), len(paths))
seen = [r["path"] for r in rows]
assert seen == paths, "row order/identity diverged from the input path list"

with open(out_path, "w", encoding="utf-8", newline="\n") as fh:
    for r in rows:
        fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")

from collections import Counter
c = Counter(r["class"] for r in rows)
print("%-18s paths=%d rows=%d  %s  payload_keys=%d"
      % (os.path.basename(cls_dir), len(paths), len(rows),
         sorted(c.items()), len(E.PAYLOAD_KEYS)))
