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
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

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
        # Present on enough items to be *testable*, not enough to be "the
        # paper's class". Those are different bars and the second one was too
        # high: a paper built from several item families has no field on 60% of
        # its items, so `p15-adaptation-a0` and `p15-handover-a0` derived **no
        # label set at all** and the metadata check ran on nothing -- 89 of 186
        # items, green because unexamined. A leak confined to one family is
        # still a leak. Four is the floor `_metadata_hits_within` already
        # applies before it will score anything, so anything above it is worth
        # handing over. Re-auditing all four papers under this wider net finds
        # ten more label fields and zero hits: the papers are clean, and now
        # they are clean *having been looked at*. (V21)
        if len(labels) < MIN_LABELLED:
            continue
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


#: Below this a field cannot be tested: `_metadata_hits_within` needs four
#: labelled items before it will score anything, so deriving a smaller set only
#: creates the appearance of a check.
MIN_LABELLED = 4


#: Fields that sit on every sheet item and are not question content.  These are
#: the ones nobody thinks of as carrying information, which is exactly why one
#: of them did.
#:
#: `item_id` was added in V21's second pass. An adversarial probe built a paper
#: whose ids read `q-dead-01`, and the gate passed it: the id is bookkeeping, not
#: content, and nothing was looking at it. The token check is what makes it worth
#: including -- whole-value bucketing can never score a field that is distinct on
#: every item, but a shared token inside the id is exactly a printed answer key.
#: All four shipped papers stay green with it in, so this buys coverage at no
#: false-positive cost on the papers we have.
#:
#: The list is an allowlist of *non-content* fields on purpose. Fields like
#: `board`, `definition` or `state` are the question, and a feature of the
#: question predicting the answer is the task, not a leak -- an independent audit
#: that scored them reported `count:board` "predicting" solvability at 1.000,
#: which is what solving the problem looks like.
METADATA_FIELDS = ("points", "tags", "kind", "item_id")


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
    hits, _unscored = metadata_scan(paper, answer_of, tolerance=tolerance)
    findings.extend(hits)
    return findings


def metadata_scan(paper: Paper, answer_of: Dict[str, str], *,
                  tolerance: float = 0.90
                  ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Both halves of the metadata check in one pass: hits, and what went unscored.

    `metadata_hits` and `metadata_coverage` are the two projections of this, and
    they are projections rather than two traversals on purpose -- a caller that
    wants the verdict *and* the coverage (`check_paper` does) must not be able to
    obtain them from two walks that could disagree.
    """
    hits: List[Dict[str, Any]] = []
    unscored: List[Dict[str, Any]] = []
    for group in _by_answer_alphabet(paper, answer_of):
        group_hits, group_unscored = _metadata_hits_within(
            group, answer_of, tolerance)
        hits.extend(group_hits)
        unscored.extend(group_unscored)
    return hits, unscored


def metadata_coverage(paper: Paper, answer_of: Dict[str, str], *,
                      tolerance: float = 0.90) -> List[Dict[str, Any]]:
    """What `metadata_hits` declined to score, so a green gate can be read.

    "No hits" and "nothing was scored" print the same and mean opposite things.
    This is the second half of the V21 fix: the count of values the whole-value
    check skipped as singletons is now reportable rather than discarded inside
    a comprehension.
    """
    _hits, unscored = metadata_scan(paper, answer_of, tolerance=tolerance)
    return unscored


def _by_answer_alphabet(paper: Paper, answer_of: Dict[str, str]
                        ) -> List[List[Item]]:
    groups: Dict[str, List[Item]] = {}
    for item in paper.items:
        if item.item_id not in answer_of:
            continue
        groups.setdefault(canonical(item.sheet_side().get("kind")), []).append(item)
    return list(groups.values())


def _metadata_hits_within(labelled: List[Item], answer_of: Dict[str, str],
                          tolerance: float
                          ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    # An unscorable *group* is the same defect one level up, so it is recorded
    # rather than returned as an empty pair. Two of these in a row and a paper's
    # metadata check has examined nothing while reporting the same green as a
    # check that examined everything. (V21, second pass)
    if len(labelled) < 4:
        # too few to distinguish a key from a coincidence
        return [], [{"field": None, "group_items": len(labelled),
                     "declined": "fewer than 4 labelled items", "scored_values": 0}]
    alphabet = {answer_of[i.item_id] for i in labelled}
    if len(alphabet) < 2:
        return [], [{"field": None, "group_items": len(labelled),
                     "declined": "one possible answer", "scored_values": 0}]
    majority = Counter(answer_of[i.item_id] for i in labelled).most_common(1)[0][1]
    floor = majority / len(labelled)

    findings: List[Dict[str, Any]] = []
    declined: List[Dict[str, Any]] = []
    for field_name in METADATA_FIELDS:
        buckets: Dict[str, Counter] = {}
        for item in labelled:
            value = item.sheet_side().get(field_name)
            if value is None:
                continue
            key = canonical(value)
            buckets.setdefault(key, Counter())[answer_of[item.item_id]] += 1
        if len(buckets) < 2:
            # A constant whole value cannot predict anything -- and its tokens
            # are constant too, so the token check below would find nothing
            # either. Skipping outright is correct here, but only for that
            # reason; it is spelled out because the *other* early exits in this
            # loop were skipping the token check by accident.
            #
            # Correct, and still worth printing. On `p15-verdict-a2` all three
            # metadata fields are constant, so the check scores nothing on any of
            # its four derived label sets -- 17 items whose green means "there was
            # nothing here to check", which is a true statement no reader could
            # previously distinguish from "checked and clean". (V21, second pass)
            declined.append({
                "field": field_name, "scored_values": 0,
                "declined": "absent" if not buckets else "constant"})
            continue
        # Score only on buckets holding more than one item. A field that takes a
        # different value on every item -- an id, or a per-variant tag -- fits
        # the answers perfectly and predicts nothing, because there is no second
        # item in any bucket to test the rule against. Counting singletons would
        # make every identifier look like a key and bury the one real leak in
        # noise.
        usable = {k: c for k, c in buckets.items() if sum(c.values()) > 1}
        # Singleton buckets are not scored -- a value seen once states no rule
        # there is a second item to test -- but they are no longer *discarded*.
        # A singleton means "this item's value is unique", and that is two very
        # different situations wearing one face: nothing leaked, or the leak is
        # so complete that the value identifies the item outright. The count is
        # carried into the report so a reader can see how much of the field this
        # check declined to score. (V21)
        dropped = len(buckets) - len(usable)
        if dropped:
            declined.append({"field": field_name, "singleton_values": dropped,
                             "scored_values": len(usable)})
        if len(usable) >= 2:
            correct = sum(c.most_common(1)[0][1] for c in usable.values())
            seen = sum(sum(c.values()) for c in usable.values())
            rate = correct / seen if seen else 0.0
            # The floor has to be recomputed over the items actually scored.
            # Dropping singletons can leave a subset with only one answer in it,
            # and then `rate` is 1.0 by arithmetic while `floor` still reflects
            # the whole group -- a field "predicting" an answer that is the only
            # answer left. `v11-handover-a0` is the live case: three tag buckets
            # of two items each, every one `solvable: true`, flagged at 1.000
            # against a 0.750 floor. One possible answer is not a question, and
            # that is already this function's rule two lines up; it just was not
            # applied to the subset it ends up scoring. Found by V21's wider net.
            scored = Counter()
            for counter in usable.values():
                scored.update(counter)
            # A *local* floor. Assigning back to `floor` would raise it for the
            # token check below and for every later field in this loop, quietly
            # desensitising checks that have nothing to do with this subset --
            # a per-subset correction leaking into a per-group value.
            floor_here = max(
                floor, scored.most_common(1)[0][1] / seen if seen else 0.0)
            # `continue` here would skip the token check for this field, which
            # is the one thing this function was changed to add. A degenerate
            # whole-value subset says nothing about whether a *token* leaks.
            if (len(scored) >= 2 and rate > tolerance
                    and rate > floor_here + 1e-9):
                findings.append({
                    "field": field_name,
                    "predicts": round(rate, 6),
                    "majority_floor": round(floor_here, 6),
                    "n": seen,
                    "values": {k: dict(v) for k, v in sorted(usable.items())},
                })

        # --- token level ------------------------------------------------
        # Whole-value bucketing has a blind spot with a sharp edge: one unique
        # token anywhere in the value -- a `level:` marker, a per-item id --
        # makes every bucket a singleton, every bucket is then unscored, and a
        # genuine leak sharing the *rest* of the value becomes structurally
        # invisible. `tags: [..., "dead"]` on the three dead items is the case
        # that motivated this: the full tag list differs per item, so nothing
        # above ever sees it.
        #
        # So each value is also split into tokens, and each token is tested as a
        # binary rule: does knowing "this item carries token t" predict the
        # answer? A token must sit on at least two items to be scored, for the
        # same reason a value must -- one item is an identifier, not a rule --
        # and a token on every item predicts nothing and is skipped.
        findings.extend(_token_hits_within(labelled, answer_of, tolerance,
                                           field_name, floor))
    return findings, declined


#: Tokens shorter than this are punctuation and stopword noise, not labels.
MIN_TOKEN = 3
_TOKEN_SPLIT = re.compile(r"[^0-9a-z]+")


def field_tokens(value: Any) -> Set[str]:
    """The distinct tokens of a metadata value, lowercased.

    Deliberately crude: `canonical` first, so a list, a dict and a string are
    all reduced the same way, then split on anything that is not a letter or a
    digit. A leak does not have to arrive in a tidy field, and a tokeniser that
    only understood the shapes we already thought of would be checking our
    imagination rather than the sheet.
    """
    if value is None:
        return set()
    text = canonical(value).lower()
    return {t for t in _TOKEN_SPLIT.split(text) if len(t) >= MIN_TOKEN}


def _token_hits_within(labelled: List[Item], answer_of: Dict[str, str],
                       tolerance: float, field_name: str,
                       floor: float) -> List[Dict[str, Any]]:
    n = len(labelled)
    carriers: Dict[str, List[Item]] = {}
    for item in labelled:
        for token in field_tokens(item.sheet_side().get(field_name)):
            carriers.setdefault(token, []).append(item)

    findings: List[Dict[str, Any]] = []
    for token, holders in sorted(carriers.items()):
        if len(holders) < 2 or len(holders) == n:
            continue        # an identifier, or a constant: neither is a rule
        held = {i.item_id for i in holders}
        with_token = Counter(answer_of[i.item_id] for i in holders)
        without = Counter(answer_of[i.item_id] for i in labelled
                          if i.item_id not in held)
        correct = (with_token.most_common(1)[0][1]
                   + without.most_common(1)[0][1])
        rate = correct / n
        if rate > tolerance and rate > floor + 1e-9:
            findings.append({
                "field": field_name,
                "token": token,
                "predicts": round(rate, 6),
                "majority_floor": round(floor, 6),
                "n": n,
                "carried_by": len(holders),
                "with_token": dict(with_token),
                "without_token": dict(without),
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

    unscored: Dict[str, List[Dict[str, Any]]] = {}
    for source, labels in sorted(label_sets.items()):
        # Not `hits`: that name is taken by the per-item probe result above, and
        # this file is the wrong place to make a reader check which one is meant.
        metadata_findings, declined = metadata_scan(paper, labels)
        for hit in metadata_findings:
            findings.append({"check": "metadata", "label_source": source, **hit})
        if declined:
            unscored[source] = declined

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
    # How much of the whole-value check declined to score, per label source and
    # field. Without this the report is only readable as "no hits", and "no hits"
    # is what a check that examined nothing also prints -- which is the defect
    # V21 was opened about, one level up. The function to compute it existed at
    # the end of the first pass but nothing called it outside the tests, so the
    # shipped artefact still could not be read. (V21)
    if unscored:
        report["metadata_unscored"] = unscored
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
