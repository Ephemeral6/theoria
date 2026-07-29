"""Re-derive the leakage auditor's claims from scratch, independently.

`STATUS.md` open weakness 14: every cheater claim must be scored against the key
before it is believed or acted on. Two of the four cheater claims recorded in
this territory did not survive that step. So this script does not reuse the
auditor's code; it recomputes each claim from `build()` and the key.

Run from the repo root:
    PYTHONPATH=. python exam/runs/<this run>/verify_leak_claims.py
"""

from collections import Counter

from exam.grading.registry import digest, module_digests
from exam.leakage import derive_label_sets, metadata_hits
from exam.papers.verdict import build


def main():
    paper = build()
    rubric_digest = digest()
    module_digest = module_digests().get("exam.grading.rubrics_verdict")
    sheet = paper.sheet(rubric_digest, module_digest)
    key_doc = paper.key(rubric_digest)

    truth_claim = {e["item_id"]: e["truth"]["claim"] for e in key_doc["items"]}
    sheet_of = {i["item_id"]: i for i in sheet["items"]}
    n = len(truth_claim)
    majority = Counter(truth_claim.values()).most_common(1)[0]
    baseline = majority[1] / n
    print("items=%d  answers=%s  majority baseline=%d/%d=%.4f"
          % (n, dict(Counter(truth_claim.values())), majority[1], n, baseline))

    # -- CLAIM 0: production's metadata check never sees the real answer ------
    print("\n--- CLAIM 0: does derive_label_sets surface `claim`? ---")
    derived = derive_label_sets(paper, key_doc)
    print("label sets derived from the key :", sorted(derived))
    print("`claim` among them              :", "claim" in derived)
    # why: the guard counts items whose label text already appears on the sheet
    public = sum(1 for iid, lab in
                 {e["item_id"]: e["truth"]["claim"] for e in key_doc["items"]}.items()
                 if lab in str(sheet_of[iid]))
    print("items whose own answer word is printed on their sheet: %d/%d "
          "(guard drops the field above %.1f)" % (public, n, 0.6 * n))
    print("metadata_hits AGAINST THE REAL ANSWER (never run in production):",
          metadata_hits(paper, truth_claim))

    # -- the sheet-visible features ------------------------------------------
    def feature(iid, name):
        item = sheet_of[iid]
        board = item["board"]
        if name == "level_id":
            return item["level_id"]
        if name == "grid":
            return "\n".join(board["grid"])
        if name == "height":
            return len(board["grid"])
        if name == "n_hazards":
            return len(item["hazards"])
        raise KeyError(name)

    def repetition_rule(name):
        """`a board the paper bothered to reuse is a trap board` -- key-free."""
        counts = Counter(feature(i, name) for i in truth_claim)
        hits = sum(1 for i, t in truth_claim.items()
                   if ("solvable" if counts[feature(i, name)] > 1 else "unsolvable") == t)
        return hits

    print("\n--- CLAIM 1/2: repetition of a sheet-visible board identity ---")
    for name in ("level_id", "grid"):
        counts = Counter(feature(i, name) for i in truth_claim)
        singles = [v for v, c in counts.items() if c == 1]
        single_answers = Counter(
            truth_claim[i] for i in truth_claim if counts[feature(i, name)] == 1)
        hits = repetition_rule(name)
        print("  %-8s distinct=%2d  appearing once=%2d  their answers=%s"
              % (name, len(counts), len(singles), dict(single_answers)))
        print("           rule 'reused => solvable' scores %d/%d = %.4f "
              "(baseline %.4f)" % (hits, n, hits / n, baseline))

    print("\n--- CLAIM 3: len(hazards) ---")
    buckets = {}
    for i, t in truth_claim.items():
        buckets.setdefault(feature(i, "n_hazards"), Counter())[t] += 1
    for value in sorted(buckets):
        print("  hazards=%d -> %s" % (value, dict(buckets[value])))
    hits = sum(buckets[v].most_common(1)[0][1] for v in buckets)
    print("  bucket-majority rule scores %d/%d = %.4f (baseline %.4f)"
          % (hits, n, hits / n, baseline))

    print("\n--- CLAIM 3b: board height ---")
    buckets = {}
    for i, t in truth_claim.items():
        buckets.setdefault(feature(i, "height"), Counter())[t] += 1
    for value in sorted(buckets):
        print("  height=%d -> %s" % (value, dict(buckets[value])))

    print("\n--- combined: reuse rule, overridden by exactly one hazard ---")
    counts = Counter(feature(i, "level_id") for i in truth_claim)
    hits = 0
    for i, t in truth_claim.items():
        guess = "solvable" if counts[feature(i, "level_id")] > 1 else "unsolvable"
        if feature(i, "n_hazards") == 1:
            guess = "unsolvable"
        hits += (guess == t)
    print("  scores %d/%d = %.4f (baseline %.4f)" % (hits, n, hits / n, baseline))


if __name__ == "__main__":
    main()
