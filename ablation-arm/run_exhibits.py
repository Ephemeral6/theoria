"""Run the three calibration exhibits and write the report.

```bash
python ablation-arm/run_exhibits.py          # all three
python ablation-arm/run_exhibits.py --json   # as data
```

Exit status is **0 even when an exhibit does not hold**, and that is deliberate.
E3's designed construction no longer exists in this repository, `DESIGN.md` §10
pre-registered that class of outcome as a falsifier, and a falsifier that turns
the build red is a falsifier nobody will ever report. What the status code is
for is a broken run -- a missing artefact, an exhibit that cannot read the arm's
own output -- not a finding that goes against the design.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from exhibits import run_all                                       # noqa: E402

REPORT = os.path.join(HERE, "artifacts", "exhibits.json")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    payload = run_all()
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))
        return 0

    for name, report in payload["exhibits"].items():
        print("%-4s holds=%-6s %s" % (name, report["holds"], report["class"]))
    print()
    print("all hold: %s" % payload["all_hold"])
    if payload["not_holding"]:
        print("not holding: %s -- see artifacts/exhibits.json; a pre-registered "
              "falsifier is a result, not a red build"
              % ", ".join(payload["not_holding"]))
    print("wrote %s" % REPORT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
