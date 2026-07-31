import json, os, subprocess, sys
here = os.path.abspath("release")
sys.path.insert(0, here)
root = os.path.abspath(".")
import check_redlines as R
import enumerate as E
paths = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True,
                       text=True, encoding="utf-8").stdout.split()
rows = E.build(paths)
out = {r["path"]: r["class"] for r in rows}
json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), sort_keys=True)
from collections import Counter
print(sys.argv[1], len(out), sorted(Counter(out.values()).items()))
