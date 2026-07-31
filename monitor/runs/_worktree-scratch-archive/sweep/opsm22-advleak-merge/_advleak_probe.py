"""Differential probe: run this tree's exam.leakage.metadata_hits over a shared
corpus and print one JSON line per case.  Run the SAME corpus under the master
worktree and the merge worktree; any case where master fires and merge does not
is a candidate refutation of "the resolution cannot loosen the gate".

Read-only: writes nothing but stdout.
"""
import json
import sys

from exam.model import Item, Paper
from exam import leakage


def build(case):
    items = []
    answer_of = {}
    for spec in case["items"]:
        items.append(Item(
            item_id=spec["item_id"],
            rubric_id="r1",
            points=spec["points"],
            paper={"kind": spec["kind"], "board": spec.get("board", "b")},
            truth={"solvable": spec["answer"]},
            leak_probes=("zzz-never-appears",),
            tags=tuple(spec["tags"]),
        ))
        answer_of[spec["item_id"]] = spec["answer"]
    paper = Paper(paper_id=case["id"], question_type="verdict",
                  instructions="i", items=items)
    return paper, answer_of


def main():
    corpus = json.load(open(sys.argv[1], encoding="utf-8"))
    for case in corpus:
        paper, answer_of = build(case)
        try:
            hits = leakage.metadata_hits(paper, answer_of)
            err = None
        except Exception as exc:                      # noqa: BLE001
            hits, err = [], "%s: %s" % (type(exc).__name__, exc)
        rec = {
            "id": case["id"],
            "fired": bool(hits),
            "n_hits": len(hits),
            # normalised so the two trees are comparable: master has no tokens
            "whole_value": sorted(
                (h["field"], h["predicts"], h["majority_floor"], h["n"])
                for h in hits if "token" not in h),
            "token": sorted(
                (h["field"], h["token"], h["predicts"], h["n"])
                for h in hits if "token" in h),
            "err": err,
        }
        print(json.dumps(rec, sort_keys=True))


if __name__ == "__main__":
    main()
