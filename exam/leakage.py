"""Does the paper give the answer away?

Three checks, deliberately of different kinds, because a leak that survives one
kind tends to survive every instance of that kind.

1. **Declared probes.**  Each item states the exact strings that would hand its
   answer over -- the serialised next frame, the name of the rule that was
   changed, the word that settles a verdict.  The sheet is serialised and
   searched for them.  Cheap, exact, and it catches the leak that actually
   happens: a builder that put the truth in a debug field and forgot.

2. **Structural disjointness.**  No key present in `Item.truth` may appear
   anywhere in `Item.paper`, at any depth.  This catches the leak the builder
   did *not* think to probe for, which is the interesting half.

3. **Positional independence.**  Where a question type has a small answer
   alphabet (a verdict is solvable / unsolvable / abstain), an examinee that
   never reads the question should score at chance.  If item order, item length,
   or item id correlates with the answer, it will not.  `positional_report`
   measures those correlations so the builder can shuffle deterministically
   rather than assert innocence.

The fourth check is not code.  A cheater subagent is handed the sheet alone,
with no world source and no truth, and told to extract answers.  Checks 1-3 test
the leaks we imagined; the cheater tests the ones we did not.  Its transcript is
archived next to the paper, and its score is reported against the chance
baseline that `positional_report` computes.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .model import Item, LeakageError, Paper, canonical


# ----------------------------------------------------------------- 1. probes

def _walk_keys(node: Any, depth: int = 0) -> Iterable[str]:
    if depth > 40:
        return
    if isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            yield from _walk_keys(value, depth + 1)
    elif isinstance(node, (list, tuple)):
        for value in node:
            yield from _walk_keys(value, depth + 1)


def probe_hits(sheet_text: str, probes: Sequence[str]) -> List[str]:
    """Probes that appear verbatim in the serialised sheet.

    Probes shorter than three characters are refused rather than checked: `"0"`
    matches every grid ever printed, so a short probe reports a hit on a clean
    paper and trains the reader to ignore this tool.
    """
    hits = []
    for probe in probes:
        text = str(probe)
        if len(text) < 3:
            raise LeakageError(
                "leak probe %r is too short to mean anything -- it would match "
                "almost any sheet. Probe the distinguishing part of the answer, "
                "not a single token of it." % text)
        if text in sheet_text:
            hits.append(text)
    return hits


# --------------------------------------------------- 2. structural disjointness

#: Keys that legitimately appear on both sides.  Kept short and justified: every
#: entry here is a hole in check 2.
SHARED_KEYS = frozenset({
    "item_id", "points", "tags", "kind", "world", "level", "level_id",
    "state", "action", "actions", "note",
})


def structural_hits(item: Item) -> List[str]:
    """Keys of `truth` that also occur somewhere in `paper`."""
    truth_keys = {k for k in _walk_keys(item.truth) if k not in SHARED_KEYS}
    paper_keys = set(_walk_keys(item.paper))
    return sorted(truth_keys & paper_keys)


# ------------------------------------------------------ 3. positional signals

def positional_report(paper: Paper, answer_of: Dict[str, str]) -> Dict[str, Any]:
    """Can the answer be guessed from the shape of the question?

    `answer_of` maps item_id to the item's answer as a short label.  Returns the
    chance baseline (the majority-class rate -- what a bluffer scores by
    answering the commonest label every time) plus the three positional
    correlations we can actually fix by shuffling.
    """
    labels = [answer_of[i.item_id] for i in paper.items if i.item_id in answer_of]
    if not labels:
        return {"n": 0, "note": "no labelled items"}
    counts = Counter(labels)
    n = len(labels)
    majority = counts.most_common(1)[0]

    order_runs = 1 + sum(1 for a, b in zip(labels, labels[1:]) if a != b)
    ideal_runs = n  # perfectly alternating; a sorted-by-answer paper gives few
    by_length: Dict[str, List[int]] = {}
    for item in paper.items:
        if item.item_id in answer_of:
            by_length.setdefault(answer_of[item.item_id], []).append(
                len(canonical(item.paper)))
    length_means = {k: round(sum(v) / len(v), 3) for k, v in sorted(by_length.items())}

    id_digits = {}
    for label, ids in _group_ids(paper, answer_of).items():
        id_digits[label] = sorted(ids)[:4]

    return {
        "n": n,
        "label_counts": dict(sorted(counts.items())),
        "chance_baseline": round(majority[1] / n, 6),
        "chance_label": majority[0],
        "order_runs": order_runs,
        "order_runs_max": ideal_runs,
        "clustered_by_answer": order_runs <= max(2, len(counts)),
        "sheet_length_mean_by_answer": length_means,
        "example_ids_by_answer": id_digits,
    }


#: Truth fields that are worth treating as an "answer label" when the builder
#: has not named one.  Anything whose value set is small is a class, and a class
#: is what a metadata field can encode.
MAX_LABEL_ALPHABET = 6


def derive_label_sets(paper: Paper, key_doc: Dict[str, Any]
                      ) -> Dict[str, Dict[str, str]]:
    """Find every small-alphabet answer class in the key, without being told.

    This exists because the polite version did not work.  `answer_labels` was an
    optional hook on each paper module, and *no* module implemented it, so the
    positional and metadata checks silently did nothing on all four papers --
    which is how a `points` field that encoded the verdict on 17 of 17 items got
    shipped past a leak checker.

    An optional check is a check that does not run.  So the labels are now
    derived from the answer key directly: any top-level truth field that is a
    scalar, present on most items, and takes few distinct values is treated as
    an answer class and tested.  A builder that names its own labels still can;
    this runs in addition, never instead.
    """
    per_field: Dict[str, Dict[str, str]] = {}
    counts: Dict[str, set] = {}
    n_items = len(key_doc.get("items", ())) or 1

    for entry in key_doc.get("items", ()):
        truth = entry.get("truth")
        if not isinstance(truth, dict):
            continue
        for field_name, value in truth.items():
            if not isinstance(value, (str, bool, int, float)) or isinstance(value, float):
                continue
            per_field.setdefault(field_name, {})[entry["item_id"]] = canonical(value)
            counts.setdefault(field_name, set()).add(canonical(value))

    sheet_text_of = {i.item_id: canonical(i.sheet_side()) for i in paper.items}

    out: Dict[str, Dict[str, str]] = {}
    for field_name, labels in per_field.items():
        alphabet = counts[field_name]
        if len(alphabet) < 2 or len(alphabet) > MAX_LABEL_ALPHABET:
            continue
        if len(labels) < 0.6 * n_items:
            continue       # present on too few items to be the paper's class
        # A field the sheet already publishes is a stratum, not an answer.
        # The held-out paper prints `split` on every item on purpose -- the
        # replay and held-out halves carry identical class quotas precisely so
        # that the tag is safe to show -- and flagging a sheet field for
        # predicting something the sheet already states would be noise, and
        # noise is how a checker gets ignored.
        public = sum(1 for iid, lab in labels.items()
                     if lab.strip('"') in sheet_text_of.get(iid, ""))
        if public > 0.6 * len(labels):
            continue
        out[field_name] = labels
    return out


#: Fields that sit on every sheet item and are not question content.  These are
#: the ones nobody thinks of as carrying information, which is exactly why one
#: of them did.
METADATA_FIELDS = ("points", "tags", "kind")


def metadata_hits(paper: Paper, answer_of: Dict[str, str], *,
                  tolerance: float = 0.90) -> List[Dict[str, Any]]:
    """Does a metadata field predict the answer?

    Added after a cheater subagent read the verdict paper's entire claim half
    off `points`: solvable items were worth 3 and unsolvable ones 2, so the
    scoring weight -- chosen for a good reason, to stop a bluffer scoring well --
    was a perfect answer key printed on the sheet.  17 of 17, with no reasoning
    about any board.

    Checks 1-3 all missed it.  Probes look for the answer's *text*; structural
    disjointness looks at key names, and `points` is legitimately on both sides;
    positional independence looks at order.  None of them asks whether a field
    everyone treats as bookkeeping happens to be a function of the answer.

    The rule: for each metadata field, build the map value -> answers seen. If
    knowing the value predicts the answer for more than `tolerance` of items,
    that is a leak.  A perfectly balanced field predicts at the majority-class
    rate, which is the floor; anything approaching 1.0 is a key.
    """
    findings: List[Dict[str, Any]] = []
    # Compare only within one answer alphabet. A paper whose families answer in
    # different vocabularies -- "detected"/"never" here, "solvable"/"unsolvable"
    # there -- would otherwise show `kind` predicting the answer perfectly, and
    # that is arithmetic, not a leak: knowing the family tells you which words
    # are even available. Grouping first is what stops the check crying wolf,
    # and a checker that cries wolf is a checker that gets switched off.
    for group in _by_answer_alphabet(paper, answer_of):
        findings.extend(_metadata_hits_within(group, answer_of, tolerance))
    return findings


def _by_answer_alphabet(paper: Paper, answer_of: Dict[str, str]
                        ) -> List[List[Item]]:
    groups: Dict[str, List[Item]] = {}
    for item in paper.items:
        if item.item_id not in answer_of:
            continue
        groups.setdefault(canonical(item.sheet_side().get("kind")), []).append(item)
    return list(groups.values())


def _metadata_hits_within(labelled: List[Item], answer_of: Dict[str, str],
                          tolerance: float) -> List[Dict[str, Any]]:
    if len(labelled) < 4:
        return []          # too few to distinguish a key from a coincidence
    alphabet = {answer_of[i.item_id] for i in labelled}
    if len(alphabet) < 2:
        return []          # one possible answer is not a question
    majority = Counter(answer_of[i.item_id] for i in labelled).most_common(1)[0][1]
    floor = majority / len(labelled)

    findings: List[Dict[str, Any]] = []
    for field_name in METADATA_FIELDS:
        buckets: Dict[str, Counter] = {}
        for item in labelled:
            value = item.sheet_side().get(field_name)
            if value is None:
                continue
            key = canonical(value)
            buckets.setdefault(key, Counter())[answer_of[item.item_id]] += 1
        if len(buckets) < 2:
            continue       # a constant field cannot predict anything
        # Score only on buckets holding more than one item. A field that takes a
        # different value on every item -- an id, or a per-variant tag -- fits
        # the answers perfectly and predicts nothing, because there is no second
        # item in any bucket to test the rule against. Counting singletons would
        # make every identifier look like a key and bury the one real leak in
        # noise.
        usable = {k: c for k, c in buckets.items() if sum(c.values()) > 1}
        if len(usable) < 2:
            continue
        correct = sum(c.most_common(1)[0][1] for c in usable.values())
        seen = sum(sum(c.values()) for c in usable.values())
        rate = correct / seen if seen else 0.0
        buckets = usable
        # Only a field that beats the majority floor is telling us anything, and
        # only one that approaches certainty is a key rather than a correlation.
        if rate > tolerance and rate > floor + 1e-9:
            findings.append({
                "field": field_name,
                "predicts": round(rate, 6),
                "majority_floor": round(floor, 6),
                "n": seen,
                "values": {k: dict(v) for k, v in sorted(buckets.items())},
            })
    return findings


def _group_ids(paper: Paper, answer_of: Dict[str, str]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for item in paper.items:
        if item.item_id in answer_of:
            out.setdefault(answer_of[item.item_id], []).append(item.item_id)
    return out


# ------------------------------------------------------------------ the gate

_TRIVIAL_TRUTH = ({}, {"kind": "none"})


def check_paper(paper: Paper, sheet: Dict[str, Any], *,
                answer_of: Optional[Dict[str, str]] = None,
                key_doc: Optional[Dict[str, Any]] = None,
                require_probes: bool = True) -> Dict[str, Any]:
    """Run checks 1-3.  Raises on any hit; returns the evidence when clean."""
    sheet_text = canonical(sheet)
    findings: List[Dict[str, Any]] = []
    missing_probes: List[str] = []

    for item in paper.items:
        if not item.leak_probes and item.truth not in _TRIVIAL_TRUTH:
            missing_probes.append(item.item_id)
        hits = probe_hits(sheet_text, item.leak_probes)
        if hits:
            findings.append({"item_id": item.item_id, "check": "probe",
                             "hits": hits})
        shared = structural_hits(item)
        if shared:
            findings.append({"item_id": item.item_id, "check": "structural",
                             "keys": shared})

    if require_probes and missing_probes:
        raise LeakageError(
            "%d item(s) of %s declare no leak probe: %s. An item that cannot "
            "say what would give its answer away has not been checked; it has "
            "been assumed innocent."
            % (len(missing_probes), paper.paper_id, missing_probes[:8]))

    # Every label set we can lay hands on, whether or not the builder offered
    # one. `derive_label_sets` is what makes this check non-optional.
    label_sets: Dict[str, Dict[str, str]] = {}
    if key_doc is not None:
        label_sets.update(derive_label_sets(paper, key_doc))
    if answer_of:
        label_sets["<declared>"] = answer_of

    for source, labels in sorted(label_sets.items()):
        for hit in metadata_hits(paper, labels):
            findings.append({"check": "metadata", "label_source": source, **hit})

    if findings:
        raise LeakageError(
            "%s leaks its own answers: %s" % (paper.paper_id, findings[:8]))

    report: Dict[str, Any] = {
        "paper_id": paper.paper_id,
        "n_items": len(paper.items),
        "probes_declared": sum(len(i.leak_probes) for i in paper.items),
        "probe_hits": 0,
        "structural_hits": 0,
        "sheet_bytes": len(sheet_text.encode("utf-8")),
    }
    report["label_sets_checked"] = sorted(label_sets)
    report["metadata_fields_checked"] = list(METADATA_FIELDS)
    # The declared label is *the* answer, so its positional report keeps the
    # top-level key it has always had. Labels we derived ourselves are a wider
    # net and sit beside it, so that adding the net did not silently change the
    # meaning of a field other code already reads.
    if answer_of:
        report["positional"] = positional_report(paper, answer_of)
    derived = {source: positional_report(paper, labels)
               for source, labels in sorted(label_sets.items())
               if source != "<declared>"}
    if derived:
        report["positional_derived"] = derived
    return report


def skeletonise(node: Any, max_items: int = 6, depth: int = 0) -> Any:
    """Replace bulky payloads with a note recording their size.

    The adaptation sheet is megabytes of observation streams, which no reader
    can be handed whole.  Truncating it for the cheater is safe *for the cheater's
    purpose* and only for that purpose: every signal a cheater exploits -- item
    order, field names, id patterns, and above all the length of each field --
    survives, because length is recorded rather than discarded.  What is dropped
    is the legitimate question content, which is the part a cheater is forbidden
    to reason about anyway.

    It would not be safe to hand a *reader* a skeleton; they would be answering a
    different question.  This is for check 4 only.
    """
    if depth > 12:
        return "<...>"
    if isinstance(node, dict):
        return {k: skeletonise(v, max_items, depth + 1) for k, v in node.items()}
    if isinstance(node, list):
        if len(node) <= max_items:
            return [skeletonise(v, max_items, depth + 1) for v in node]
        head = [skeletonise(v, max_items, depth + 1) for v in node[:max_items]]
        return head + ["<%d more entries elided; full length %d>"
                       % (len(node) - max_items, len(node))]
    if isinstance(node, str) and len(node) > 400:
        return node[:400] + "<...%d more chars>" % (len(node) - 400)
    return node


def cheater_brief(sheet: Dict[str, Any]) -> str:
    """The prompt handed to the cheater subagent.

    It gets the sheet and nothing else: no world source, no truth file, no
    repository context.  The instruction is adversarial on purpose -- we are not
    asking whether a fair reader could pass, we are asking whether an unfair one
    can.
    """
    return (
        "You are given an exam sheet as JSON and NOTHING else. You have no "
        "access to the world it describes, no source code, and no answer key.\n\n"
        "Your job is to CHEAT: answer as many items as you can using only "
        "features of the sheet itself -- wording asymmetries, item ordering, "
        "field lengths, id patterns, anything that betrays the answer without "
        "reasoning about the world. Do not attempt to actually solve the "
        "questions from first principles; that is not what is being measured.\n\n"
        "Report, for every item you answer: the answer, the sheet feature you "
        "exploited, and your confidence. If you find no exploitable feature, "
        "say so plainly -- a clean sheet is the expected result and reporting "
        "it honestly is worth more than a guess.\n\n"
        "SHEET:\n" + canonical(sheet)
    )
