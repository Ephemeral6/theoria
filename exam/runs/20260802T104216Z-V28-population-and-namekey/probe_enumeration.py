"""Scratch: do exam's and freeze's book enumerations actually agree here?"""
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "exam"))

import u3_census  # noqa: E402
from freeze import u3  # noqa: E402

exam_dirs = {s.directory.resolve() for s in u3_census.discover_books(REPO)}

freeze_dirs = set()
for t in u3.expand_targets([REPO], record_exclusions=[]):
    if u3.find_books(t):
        freeze_dirs.add(Path(t).resolve())

print("exam   :", len(exam_dirs))
print("freeze :", len(freeze_dirs))
print("agree  :", exam_dirs == freeze_dirs)
only_exam = sorted(p.relative_to(REPO).as_posix() for p in exam_dirs - freeze_dirs)
only_frz = sorted(p.relative_to(REPO).as_posix() for p in freeze_dirs - exam_dirs)
print("only exam   (%d): %s" % (len(only_exam), only_exam))
print("only freeze (%d): %s" % (len(only_frz), only_frz))
print("--- intersection, sorted ---")
for p in sorted((exam_dirs & freeze_dirs)):
    print("  ", p.relative_to(REPO).as_posix())
