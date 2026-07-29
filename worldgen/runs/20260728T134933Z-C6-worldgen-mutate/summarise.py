"""Read MUTATIONS.json and print one line per mutation.  Provenance helper."""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PATH = os.path.join(ROOT, "worldgen", "out", "worlds", "MUTATIONS.json")


def main() -> int:
    with open(PATH, encoding="utf-8") as handle:
        blob = json.load(handle)
    for row in blob["mutations"]:
        det, col, rep = row["detection"], row["collateral"], row["repair"]
        print("%-12s %-26s %-22s det=%-5s eq=%-5s %-10s flip=%-5s"
              % (row["variant_id"], row["edit_family"], row["base_world_id"],
                 det["earliest_actions"], det["observationally_equivalent"],
                 col["verdict"], col["verdict_flipped"]))
        print("             name=%s" % row["transparent_name"])
        print("             streams=%s budget=%s classes=%s/%s div=%s/%s"
              % ({k: v["index"] for k, v in det["streams"].items()},
                 rep["greedy_witness_budget"],
                 rep["classes_witnessable_in_mutant"], rep["classes_total"],
                 rep["divergent_observations"],
                 rep["divergent_observations"] + rep["agreeing_observations"]))
        print("             falsified=%s" % ",".join(col["rules_falsified"]))
        print("             reexamine=%s now_false=%s added=%s removed=%s"
              % (col["claims_to_reexamine"], col["claims_now_false"],
                 col["claims_added"], col["claims_removed"]))
        print("             witness_changes=%s"
              % json.dumps(col["rule_witness_changes"], sort_keys=True))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
