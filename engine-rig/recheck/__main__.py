"""`python -m recheck <ruleset.json> <certificate.json> [--json out.json]`

Exit codes are the verdict, because a script that reads only the exit status
should still be able to tell the three apart:

    0  ACCEPT        the three conditions hold
    1  REJECT        at least one fails; the witnesses are on stdout
    3  INCONSISTENT  the conditions hold and the goal is reachable anyway --
                     a defect in this checker, escalated rather than rounded
                     down to a pass
    2  the input would not load at all
    4  the recheck itself failed

`4` exists because an uncaught exception used to leave Python's own exit status
of 1, which is `REJECT` -- so a crash and a refused certificate looked identical
to any caller reading only the status. An adversarial review pointed that out
while this file was being edited underneath it, which is about as direct a
demonstration as one could ask for.
"""

import argparse
import json
import sys
import traceback

from recheck.certificate import CertificateError, load_certificate
from recheck.ruleset import RuleSetError, load_ruleset
from recheck.verify import INCONSISTENT, REJECT, recheck

EXIT = {"ACCEPT": 0, REJECT: 1, INCONSISTENT: 3}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m recheck",
        description="Recheck an engine certificate against a rule set, using "
                    "neither the engine nor its checker.")
    parser.add_argument("ruleset")
    parser.add_argument("certificate")
    parser.add_argument("--json", dest="json_out", default=None,
                        help="write the full verdict here")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    try:
        ruleset = load_ruleset(args.ruleset)
        certificate = load_certificate(args.certificate)
    except (RuleSetError, CertificateError, ValueError, RecursionError, OSError) as exc:
        print("could not load: %s" % exc, file=sys.stderr)
        return 2

    try:
        verdict = recheck(ruleset, certificate)
    except Exception:                       # noqa: BLE001 -- deliberately broad
        traceback.print_exc()
        print("the recheck itself failed; this is not a REJECT", file=sys.stderr)
        return 4

    if not args.quiet:
        print(verdict.report())
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(verdict.as_json(), indent=2, sort_keys=True) + "\n")
    return EXIT[verdict.verdict]


if __name__ == "__main__":
    raise SystemExit(main())
