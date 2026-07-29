"""`python -m audit --out runs/<id>`

Runs every E7 measurement and writes `claim_audit.json` incrementally, so a run
that is interrupted still leaves the sections that finished.
"""

import argparse
import json
import sys

from audit import claim


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m audit")
    parser.add_argument("--out", required=True)
    parser.add_argument("--fd", default=None, help="path to fast-downward.py")
    args = parser.parse_args(argv)

    report = claim.run(args.out, executable=args.fd)
    print(json.dumps({
        "coverage": report["coverage"],
        "relaxation_vs_fd": {k: v for k, v in report["relaxation_vs_fd"].items()
                             if k != "rows"},
        "seconds": report["seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
