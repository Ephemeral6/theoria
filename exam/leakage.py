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

import itertools
import re
from collections import Counter
from functools import lru_cache
from math import comb
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
                  tolerance: float = 0.90, with_cuts: bool = False
                  ) -> Tuple[Any, ...]:
    """Both halves of the metadata check in one pass: hits, and what went unscored.

    `metadata_hits` and `metadata_coverage` are the two projections of this, and
    they are projections rather than two traversals on purpose -- a caller that
    wants the verdict *and* the coverage (`check_paper` does) must not be able to
    obtain them from two walks that could disagree.

    `with_cuts=True` adds a third member: what the multiplicity apparatus has to
    say about this scan *whether or not anything fired* -- the cuts tried, the
    family-wise rate they carry, and each group's power. It is a flag rather than a
    third always-returned value only because two callers already unpack the pair;
    it is not optional information, and `check_paper` always asks for it. Attaching
    those numbers to findings alone published nothing on a clean paper, and every
    paper we ship is clean.

    **Scope of the multiplicity correction, stated because it is not total.** One
    call covers one answer key, so `p_fire_familywise_in_label_set` pays for every
    cut tried under that key and no more. `check_paper` calls this once per label
    set it derives -- up to four on the shipped papers -- and those are further
    chances to fire that no number here pays for. The count of label sets is
    already in `report["label_sets_checked"]`, so the remaining layer is bounded
    and visible rather than hidden; what is not honest is calling a partial
    correction "the" correction, which is why both scopes are named in the key.
    """
    hits: List[Dict[str, Any]] = []
    unscored: List[Dict[str, Any]] = []
    # Every cut tried anywhere under this answer key, so the multiplicity a
    # finding is charged for is not just its own field's. Keyed by (field, cut),
    # because the same cut of the same items tested through two different fields
    # really is two chances to fire, while the same cut reached twice through one
    # field -- a token and its complement -- is one. (V25)
    cuts: Dict[Tuple[str, Tuple[str, ...]], float] = {}
    for group in _by_answer_alphabet(paper, answer_of):
        group_hits, group_unscored, group_cuts = _metadata_hits_within(
            group, answer_of, tolerance)
        hits.extend(group_hits)
        unscored.extend(group_unscored)
        cuts.update(group_cuts)

    # The correction one level out. Without this the published rate would pay for
    # the cuts tried on one field of one answer-alphabet group and stay silent
    # about the rest of the same scan -- a partial correction wearing the name of
    # the correction, which is worse than none because it reads as complete.
    # Small on the shipped papers (2, 3, 2 and 0 cuts per paper against 1-3 per
    # field group), and published anyway: the number is what makes it checkable
    # that it is small.
    survives = 1.0
    for probability in cuts.values():
        survives *= (1.0 - probability)
    familywise = 1.0 - survives
    for hit in hits:
        if "token" not in hit:
            continue
        hit["cuts_tried_in_label_set"] = len(cuts)
        hit["p_fire_familywise_in_label_set"] = round(familywise, 6)
        # Judged at the widest scope this traversal can see. A reader who is
        # told a red is strong must not have to re-derive the correction to find
        # out it was strong only against part of the search.
        hit["weak_evidence"] = familywise >= ALPHA
    if not with_cuts:
        return hits, unscored
    return hits, unscored, {           # type: ignore[return-value]
        "cuts_tried_in_label_set": len(cuts),
        "p_fire_familywise_in_label_set": round(familywise, 6),
        "cuts": sorted("%s:%s" % (field, "|".join(cut))
                       for field, cut in cuts),
        "group_power": [group_power(
            Counter(answer_of[i.item_id] for i in group), tolerance)
            for group in _by_answer_alphabet(paper, answer_of)],
    }


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
                          ) -> Tuple[List[Dict[str, Any]],
                                     List[Dict[str, Any]],
                                     Dict[Tuple[str, Tuple[str, ...]], float]]:
    # An unscorable *group* is the same defect one level up, so it is recorded
    # rather than returned as an empty pair. Two of these in a row and a paper's
    # metadata check has examined nothing while reporting the same green as a
    # check that examined everything. (V21, second pass)
    if len(labelled) < 4:
        # too few to distinguish a key from a coincidence
        return [], [{"field": None, "group_items": len(labelled),
                     "declined": "fewer than 4 labelled items",
                     "scored_values": 0}], {}
    alphabet = {answer_of[i.item_id] for i in labelled}
    if len(alphabet) < 2:
        return [], [{"field": None, "group_items": len(labelled),
                     "declined": "one possible answer",
                     "scored_values": 0}], {}
    majority = Counter(answer_of[i.item_id] for i in labelled).most_common(1)[0][1]
    floor = majority / len(labelled)

    findings: List[Dict[str, Any]] = []
    declined: List[Dict[str, Any]] = []
    cuts: Dict[Tuple[str, Tuple[str, ...]], float] = {}
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
            if not buckets:
                # Absent on every item: there is nothing to tokenise, so the token
                # pass has nothing to say and skipping it hides nothing.
                declined.append({
                    "field": field_name,
                    "declined": "single-holder tokens are not scorable",
                    "single_holder_tokens": 0, "constant_tokens": 0,
                    "scored_tokens": 0})
                continue
            # A constant whole value was previously `continue`d here on the
            # argument that its tokens must be constant too. That argument is one
            # `canonical()` away from being wrong -- two raw values can canonicalise
            # alike and tokenise differently -- and "the check did not run because
            # someone proved it need not" is the exact shape this file keeps being
            # bitten by. So the token pass runs, and if there is genuinely nothing
            # it reports nothing at a cost of one pass over a constant field.
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
        token_findings, token_declined, field_cuts = _token_hits_within(
            labelled, answer_of, tolerance, field_name, floor)
        findings.extend(token_findings)
        declined.extend(token_declined)
        cuts.update(field_cuts)
        # What the single-holder guard costs on this field, always, not only
        # when something was skipped. A coverage number that appears only when
        # it is bad is a coverage number nobody calibrates against. (V25)
        # Emitted unconditionally. The first pass wrote the comment above and then
        # guarded the record with `if coverage["single_holder"]:`, so a field that
        # scored three tokens and skipped none said nothing at all -- which is the
        # very thing the comment forbids, three lines under it. Two of the four
        # shipped papers published no token coverage whatsoever because of it.
        coverage = single_holder_coverage(labelled, answer_of, field_name)
        declined.append({
            "field": field_name,
            "declined": "single-holder tokens are not scorable",
            "single_holder_tokens": coverage["single_holder"],
            "constant_tokens": coverage["constant"],
            # Not `scored_values`: that key belongs to the whole-value check above
            # and a reader summing it would silently under-count. (V25)
            "scored_tokens": coverage["scored"],
        })
    return findings, declined, cuts


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


#: A token test may fire on noise no more often than this, after the group's
#: multiplicity is paid for. Above it the gate cannot tell a leak from luck, and
#: firing anyway would be a coin toss wearing a verdict's clothes.
#:
#: 0.05 is conventional rather than derived, and the consequence is stated in the
#: report rather than buried: a group small enough that no token can clear this
#: is recorded as **untestable**, not as clean. That distinction is the whole of
#: V21 restated one level down -- "nothing fired" and "nothing could have fired"
#: print the same and mean opposite things.
ALPHA = 0.05

#: The name a pooled single-holder cut is reported under. Angle brackets because
#: `_TOKEN_SPLIT` eats them, so no literal token from a paper can ever collide
#: with it -- a derived finding that could be mistaken for a token someone wrote
#: would send a reader looking for a string that is not there.
PRIVATE_MARKER_CUT = "<private-marker>"


def _fires(best: int, n: int, tolerance: float, floor: float) -> bool:
    """The gate's own firing predicate, in terms of the two class maxima.

    Written once and shared by the counter and its oracle, so that neither can
    drift from `_token_hits_within`'s threshold while still looking correct: a
    false-positive rate computed against a *different* threshold than the one
    that fires is worse than no rate at all, because it reads as a calibration.

    One mutation of this line is unkillable and that is not a coverage gap: dropping
    the `1e-9` changes nothing *here*, because `best` is an integer and `floor` is
    `max(sizes)/n` over the same denominator, so `best/n > floor` already means
    `best > max(sizes)`. Measured across 7548 configurations with no change in the
    count. The slack is load-bearing only in the whole-value path, where the rate is
    over the scored subset and the floor over the whole group -- different
    denominators, hence a real float comparison. Written down so the next person to
    run a mutation report does not go looking for a test that cannot exist.
    """
    rate = best / n
    return rate > tolerance and rate > floor + 1e-9


def _fire_count_bruteforce(sizes: Sequence[int], k: int,
                           tolerance: float) -> int:
    """Every split of the k carriers across answer classes, literally.

    Exponential in the number of answer classes -- prod(s_i + 1) splits, of
    which all but a thin shell are discarded for having the wrong total. Kept,
    and never called by the gate, because `_fire_count`'s pruning is only
    trustworthy if something this obvious agrees with it everywhere it can be
    run at all (`test_the_fast_count_agrees_with_the_oracle_everywhere`).
    """
    n = sum(sizes)
    floor = max(sizes) / n
    hits = 0
    for split in itertools.product(*[range(s + 1) for s in sizes]):
        if sum(split) != k:
            continue
        ways = 1
        for size, take in zip(sizes, split):
            ways *= comb(size, take)
        best = max(split) + max(s - t for s, t in zip(sizes, split))
        if _fires(best, n, tolerance, floor):
            hits += ways
    return hits


def _fire_count(sizes: Sequence[int], k: int, tolerance: float) -> int:
    """The same count, over states instead of splits.

    Which split of the carriers occurred does not matter to the predicate --
    only the largest carrier class and the largest non-carrier class do. So the
    classes are consumed one at a time carrying `(taken, max_with, max_without)`
    and nothing else, and any state whose most optimistic completion still
    cannot fire is dropped on the spot.

    This is not an optimisation looking for a problem. The literal enumeration
    is exponential in the number of *answer classes*, and it is the answer
    classes we do not control: an exam whose answers are integers (`plan_len`)
    or short strings has as many classes as it has distinct answers. Measured on
    the shipped set, `_fire_count_bruteforce` takes 0.4s on the largest real
    group (6 classes, n=80) and 15s on a synthetic 8-class one; at 12 classes it
    does not finish. A gate slow enough to be switched off is a gate that is not
    there, which is the failure mode this whole lane exists to catch, so the
    pruning is part of the check rather than a footnote about it.
    """
    n = sum(sizes)
    floor = max(sizes) / n
    # Biggest classes first: they pin `max_without` high early, so the optimistic
    # bound below starts discarding states in the first few layers instead of the
    # last.
    sizes = sorted(sizes, reverse=True)
    m = len(sizes)
    suffix_max = [0] * (m + 1)
    suffix_sum = [0] * (m + 1)
    for i in range(m - 1, -1, -1):
        suffix_max[i] = max(sizes[i], suffix_max[i + 1])
        suffix_sum[i] = sizes[i] + suffix_sum[i + 1]

    states: Dict[Tuple[int, int, int], int] = {(0, 0, 0): 1}
    for i, size in enumerate(sizes):
        reachable = suffix_max[i + 1]
        nxt: Dict[Tuple[int, int, int], int] = {}
        for (taken, max_with, max_without), ways in states.items():
            lo = max(0, k - taken - suffix_sum[i + 1])
            for take in range(lo, min(size, k - taken) + 1):
                got = taken + take
                with_ = take if take > max_with else max_with
                left = size - take
                without = left if left > max_without else max_without
                # Upper bound on each maximum over every way the remaining
                # classes could split -- a bound on the sum, hence sound to
                # prune on even where the two are not achievable together.
                if not _fires(max(with_, min(k - got, reachable))
                              + max(without, reachable),
                              n, tolerance, floor):
                    continue
                key = (got, with_, without)
                nxt[key] = nxt.get(key, 0) + ways * comb(size, take)
        states = nxt

    return sum(ways for (taken, with_, without), ways in states.items()
               if taken == k and _fires(with_ + without, n, tolerance, floor))


def token_fire_probability(label_counts: Dict[str, int], k: int,
                           tolerance: float = 0.90) -> float:
    """P(this gate fires on a token carried by k items) when nothing leaks.

    The null is the gate's own conditioning: the answers are what they are, and
    the k carriers are an arbitrary k-subset of the group. Counted exactly over
    how the carriers can split across answer classes -- the multivariate
    hypergeometric -- rather than sampled.

    Exact rather than sampled on purpose. V21 measured this by shuffling labels
    2000 times, which put a seed (`random.Random(20260729)`) and a Monte-Carlo
    error bar between the reader and the number, and made every published rate a
    function of the order in which papers happened to be scanned. The count here
    is closed-form, so it is: same answer, no seed, byte-reproducible.

    Not to be confused with "how surprising is this token" -- that conditions on
    the rate observed, and on a clean paper it is 1.0 by construction. This one
    conditions on the *threshold*, and is the false-positive rate.
    """
    sizes = tuple(sorted((label_counts[c] for c in label_counts), reverse=True))
    n = sum(sizes)
    if n == 0 or not 0 < k < n:
        return 0.0
    return _cached_fire_probability(sizes, k, tolerance)


@lru_cache(maxsize=4096)
def _cached_fire_probability(sizes: Tuple[int, ...], k: int,
                            tolerance: float) -> float:
    """Memoised because the same group is asked the same question many times.

    `check_paper` scans each answer-alphabet group once per metadata field and once
    per label set, and `group_power` sweeps every k on the same group -- so the
    unmemoised call count is roughly `fields x label_sets x n`. Keyed on the sorted
    sizes, which is exactly what the count depends on: the class *names* cannot
    change the answer, and normalising here rather than at the call site is what
    lets two different fields share one entry.

    A cache is only safe because the function is pure and deterministic, which is
    the same property that made the exact count worth having in the first place.
    """
    # p(k) == p(n - k): complementing a k-subset swaps `max_with` and
    # `max_without`, and the predicate reads only their sum. So half the range is
    # the whole range, which also halves `group_power`. Measured over 45,470
    # (k, n-k) pairs with no asymmetry, and pinned by
    # `test_a_cut_and_its_complement_have_the_same_null`.
    n = sum(sizes)
    k = min(k, n - k)
    return _fire_count(sizes, k, tolerance) / comb(n, k)


def group_power(label_counts: Dict[str, int],
                tolerance: float = 0.90) -> Dict[str, Any]:
    """The strongest evidence this group could produce, over every possible token.

    `ALPHA`'s docstring promises that a group too small for any token to clear it
    is recorded as *untestable* rather than clean. Nothing computed that, so the
    promise was prose: on a paper with no hits the report said "no hits" and left
    a reader to assume the check had power it may not have had. That is V21's
    defect verbatim, one level in -- and this time inside V25's own fix, which is
    where it was found.

    So: minimise the false-positive rate over the carrier counts a cut could have,
    **k = 1 .. n-1**. The minimum is the best case available to *anything* the check
    can test in this group, leak or luck. If even that does not clear alpha, no red
    from this group can ever be strong evidence, and the honest word for the group
    is untestable.

    k = 1 is in the range, and the first version left it out on the grounds that a
    single-holder token is never scored. That was true of *tokens* and false of the
    check: the pooled private-marker cut can hold one item, and on the M5 fixture it
    does and it fires. Excluding it understated the power of exactly the groups this
    function exists to describe.

    Cheap because it depends only on the answer counts, not on the field, so it is
    computed once per answer-alphabet group rather than once per token; and the
    sweep runs to n//2 only, since complementing a cut swaps the two maxima and the
    predicate reads their sum.
    """
    n = sum(label_counts.values())
    best = 1.0
    best_k = None
    for k in range(1, n // 2 + 1):
        probability = token_fire_probability(label_counts, k, tolerance)
        # A k at which nothing can fire is not a stronger test, it is no test.
        if probability <= 0.0:
            continue
        if probability < best:
            best, best_k = probability, k
    if best_k is None:
        # No cut of any size can trip the threshold here. Not "clean" and not
        # "weak" -- the check cannot speak about this group at all.
        return {"n": n, "best_p_fire": None, "best_k": None,
                "untestable_at_alpha": True, "can_fire_at_all": False}
    return {"n": n,
            # Six *significant* digits, not six decimals. Rounding a genuine
            # 1.5e-27 to 0.0 would print it identically to the impossible case
            # above, whose `best_p_fire` is `None` -- and "vanishingly unlikely" and
            # "cannot happen" printing alike is the exact confusion this whole
            # function was added to end.
            "best_p_fire": float("%.6g" % best), "best_k": best_k,
            "untestable_at_alpha": best >= ALPHA, "can_fire_at_all": True}


def _partition_key(held: Set[str], universe: Set[str]) -> Tuple[str, ...]:
    """A token and its complement cut the group the same way.

    The multiplicity a correction must pay for is the number of distinct *cuts*,
    not the number of tokens. Measured on the shipped papers, the difference is
    not cosmetic: `p15-adaptation-a0`/`exact_on_heldout` scores four tokens --
    `tags:narrow`, `tags:wide`, `item_id:narrow`, `item_id:wide` -- which are one
    single cut wearing four names, because `narrow` and `wide` are complements
    and `item_id` repeats `tags` item for item. Charging four tests for one
    inflates the correction fourfold on exactly the papers we ship.
    """
    return min(tuple(sorted(held)), tuple(sorted(universe - held)))


def _token_hits_within(labelled: List[Item], answer_of: Dict[str, str],
                       tolerance: float, field_name: str,
                       floor: float
                       ) -> Tuple[List[Dict[str, Any]],
                                  List[Dict[str, Any]],
                                  Dict[Tuple[str, Tuple[str, ...]], float]]:
    n = len(labelled)
    carriers: Dict[str, List[Item]] = {}
    for item in labelled:
        for token in field_tokens(item.sheet_side().get(field_name)):
            carriers.setdefault(token, []).append(item)

    counts = Counter(answer_of[i.item_id] for i in labelled)
    universe = {i.item_id for i in labelled}

    # Two passes, because the correction for a token depends on how many other
    # cuts were tried beside it, which is not known until they have all been
    # collected. Scoring and correcting in one pass would charge each token only
    # for the tokens sorted before it.
    def score(held: Set[str]) -> Tuple[int, float]:
        with_token = Counter(answer_of[i] for i in held)
        without = Counter(answer_of[i.item_id] for i in labelled
                          if i.item_id not in held)
        correct = (with_token.most_common(1)[0][1]
                   + without.most_common(1)[0][1])
        return correct, token_fire_probability(counts, len(held), tolerance)

    scored: List[Tuple[str, Set[str], int, float]] = []
    for token, holders in sorted(carriers.items()):
        if len(holders) < 2 or len(holders) == n:
            # An identifier, or a constant: neither states a rule *as a token*.
            # What that costs is reported by `single_holder_coverage`, and the
            # part of it that is recoverable is recovered by the pooled cut below.
            continue
        held = {i.item_id for i in holders}
        correct, p_fire = score(held)
        scored.append((token, held, correct, p_fire))

    # --- the private markers, pooled into one cut ------------------------
    #
    # V25's first pass ruled the single-holder gap unclosable, and an adversarial
    # review refuted it. The proof was sound and the conclusion drawn from it was
    # not: a token on one item is unscorable *as a token* -- all its statistics
    # are functions of its carrier alone, so `ridge` on the one `dead` item and
    # `tag07` on that same item are identical digit for digit -- but that is a
    # statement about per-token rules, not about this check. The field's whole
    # carrier map separates them, and this function already has it.
    #
    # So the question is asked once for the field instead of once per token:
    # **does carrying a private marker in this field predict the answer?** One
    # cut, one test, and the two cases fall on opposite sides of it by arithmetic
    # rather than by taste:
    #
    #   * a real leak marks a few items       -> k < n, scorable, fires if it predicts;
    #   * an identifier family marks every one -> k == n, dropped by the same
    #     constant guard the tokens use, because an enumeration predicts nothing.
    #
    # This is not hypothetical. On `v11-handover-a0`/`solvable` the two `false`
    # items are exactly the two whose `level:` name occurs once (`stile`, `cairn`)
    # while every `true` item shares its level name with another -- so "is my
    # level name unique on this sheet?" answers the paper 8 of 8, at an exact
    # false-positive rate of 0.0357. The shipped gate scored none of it: each
    # `level:` token sits on one or two items, and `flume` at k=2 scores exactly
    # the majority floor.
    #
    # Known evasion, stated rather than papered over: padding every item with a
    # decoy private marker pushes k to n and silences this. That is measured in
    # `runs/20260729T1820Z-V25-leakage-loo-and-multiplicity/b5_pooled_private_cut.py`
    # along with the rule that survives it (deviation from the field's modal
    # private-marker count), which is not shipped here -- it is a second design
    # decision, and V25 already learned what happens when two go into one diff.
    private = {holders[0].item_id for holders in carriers.values()
               if len(holders) == 1}
    if 0 < len(private) < n:
        correct, p_fire = score(private)
        scored.append((PRIVATE_MARKER_CUT, private, correct, p_fire))

    # Family-wise over the distinct cuts: P(at least one of them fires on noise).
    cuts: Dict[Tuple[str, ...], float] = {}
    for _token, held, _correct, p_fire in scored:
        cuts.setdefault(_partition_key(held, universe), p_fire)
    survives = 1.0
    for p_fire in cuts.values():
        survives *= (1.0 - p_fire)
    familywise = 1.0 - survives

    findings: List[Dict[str, Any]] = []
    declined: List[Dict[str, Any]] = []
    for token, held, correct, p_fire in scored:
        # `_fires`, not a second spelling of it. Its docstring claims the counter
        # and the gate "cannot drift" because they share this predicate -- and until
        # V25's adversarial pass this line wrote the comparison out inline instead,
        # so the promise was a copy rather than a call. Two mutations of `_fires`
        # (`>=` for `>`, and dropping the 1e-9) survived all 66 tests in this area,
        # and the `>=` one matters: 9/10, 72/80 and every multiple of ten land
        # exactly on the double 0.90, so on the largest real group the published
        # false-positive rate would have been computed against a threshold the gate
        # does not fire on. Pinned by
        # `test_the_published_rate_and_the_gate_agree_on_the_exact_tie`.
        if not _fires(correct, n, tolerance, floor):
            continue
        # The correction is published, NOT applied as a suppressor. V25 built it
        # as a gate first and measured what that costs: at n=6 with three cuts
        # tried it silences `test_a_degenerate_whole_value_subset_does_not_
        # disable_the_token_check`, a leak V21 planted on purpose and a human
        # can see by eye. The arithmetic is right -- such a token does arise by
        # chance 18.7% of the time at that size -- but the conclusion drawn from
        # it would be wrong, because of what this gate *does* when it fires.
        #
        # STATUS.md already fixed those semantics: firing means "stop and let a
        # human adjudicate", not "leak proven". Under those semantics a false
        # alarm costs one person one look, and a miss costs a published paper
        # built on a leaked exam. Trading the second for the first is a bad
        # trade at any alpha, and the item's own warning -- treat one side only
        # and the gate ends up either crying wolf or playing dead -- is exactly
        # what applying this would have done. So every red carries the number
        # that says what it is worth, and a reader who wants to discount a weak
        # one can; the gate does not discount it for them.
        findings.append({
            "field": field_name,
            "token": token,
            "predicts": round(correct / n, 6),
            "majority_floor": round(floor, 6),
            "n": n,
            "carried_by": len(held),
            "with_token": dict(Counter(answer_of[i] for i in held)),
            "without_token": dict(Counter(answer_of[i.item_id] for i in labelled
                                          if i.item_id not in held)),
            # Which items the cut holds. On the pooled cut the "token" is derived
            # rather than literal, so without this a reader cannot check it.
            "carrier_ids": sorted(held),
            # Published with every red, because "the gate went off" is not a
            # number and a reader is entitled to know what it is worth. V21 put
            # this in prose in STATUS.md; prose does not travel with the finding.
            "p_fire": round(p_fire, 6),
            # Named for their scope, because an unqualified "familywise" would be
            # read as covering the whole scan and this one covers one field of one
            # answer-alphabet group. `metadata_scan` adds the wider pair
            # (`..._in_label_set`) and sets `weak_evidence` from that.
            "p_fire_familywise_in_field": round(familywise, 6),
            "cuts_tried_in_field": len(cuts),
            # The one-word form of the same thing, so that a red which noise
            # could plausibly have produced cannot be quoted as if it could not.
            # Overwritten one level out, at the wider scope; the value here is
            # what this field alone would say, and is never the last word.
            "weak_evidence": familywise >= ALPHA,
        })
    return findings, declined, {(field_name, cut): p
                                for cut, p in cuts.items()}


def single_holder_coverage(labelled: List[Item], answer_of: Dict[str, str],
                           field_name: str) -> Dict[str, Any]:
    """How many of a field's tokens are not scorable one at a time, and why not.

    A token carried by exactly one item is not scorable **as a token**. Every
    statistic available for it -- the in-sample rate, a leave-one-out accuracy,
    an exact p -- is a function of *which item it sits on* and nothing else, so a
    real leak (`ridge`, on the one item whose answer is `dead`) and a bookkeeping
    identifier (`tag07`, on that same item) are identical digit for digit, and no
    per-token rule can fire on the first while staying silent on the second.
    Measured across three such rules -- the shipped one, a12's leave-one-out
    framework, and the exact test -- in
    `runs/20260729T1820Z-V25-leakage-loo-and-multiplicity/b2_three_rules_on_fixtures.py`.

    **That is a statement about per-token rules, and V25's first pass wrongly read
    it as a statement about this check.** An adversarial review refuted the wider
    claim by building the counterexample: the field's *whole carrier map* does
    separate the pair, because one private token in a field is an anomaly while
    twelve are an enumeration. `_token_hits_within` now pools a field's private
    markers into a single cut and scores that, which fires on the leak and is
    dropped as a constant on the identifier family. The first thing it found was a
    real leak in `v11-handover-a0` that the shipped gate scored none of.

    So the guard on individual tokens stays -- it is right about tokens -- and
    what this function reports is how much of the field is out of reach of the
    per-token question, on the honest denominator. On the four shipped papers,
    counting distinct (field, token) pairs, 97 of 106 are single-holder (91.5%).
    An earlier number, 237 of 261, is wrong to quote for the shipped set and is
    kept here so it can be traced rather than silently dropped: it counts
    (paper, label set, group, field, token) *scan slots* across five papers --
    `v11-handover-a0` included, along with its declared label set, and a paper
    scanned under two label sets contributes its tokens twice. On the same slot
    basis the four shipped papers are 219 of 230, and over derived label sets
    only, five papers are 228 of 247 (`b5_pooled_private_cut.py`, section 4, which
    prints all four denominators side by side). Every ratio is 90-95%, which is
    why the mis-scoping survived a pass: the percentage was insensitive to the
    unit, and nobody was checking the unit.
    """
    n = len(labelled)
    carriers: Dict[str, List[Item]] = {}
    for item in labelled:
        for token in field_tokens(item.sheet_side().get(field_name)):
            carriers.setdefault(token, []).append(item)
    singles = sorted(t for t, h in carriers.items() if len(h) == 1)
    constants = sorted(t for t, h in carriers.items() if len(h) == n)
    return {"field": field_name, "tokens": len(carriers),
            "single_holder": len(singles), "constant": len(constants),
            "scored": len(carriers) - len(singles) - len(constants)}


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
    # What the multiplicity apparatus would have to say about this scan whether or
    # not anything fired. Attached to findings only, it publishes nothing at all on
    # a clean paper -- and every paper we ship is clean, so V25's whole correction
    # was invisible in the artefact. That is V21's defect verbatim ("no hits" and
    # "no power" printing the same), reproduced inside V25's own fix, and it is the
    # second time this exact shape has been caught in this file.
    multiplicity: Dict[str, Any] = {}
    for source, labels in sorted(label_sets.items()):
        # Not `hits`: that name is taken by the per-item probe result above, and
        # this file is the wrong place to make a reader check which one is meant.
        metadata_findings, declined, scan_cuts = metadata_scan(
            paper, labels, with_cuts=True)
        for hit in metadata_findings:
            findings.append({"check": "metadata", "label_source": source, **hit})
        if declined:
            unscored[source] = declined
        multiplicity[source] = scan_cuts

    if findings:
        # Sliced per class rather than off the front. Metadata findings are
        # appended after every probe and structural one, so a plain `findings[:8]`
        # truncates them away on any paper with eight probe hits -- taking `p_fire`
        # and `weak_evidence` with them, exactly when a human is being summoned to
        # adjudicate and needs to know what the red is worth.
        metadata_findings = [f for f in findings if f.get("check") == "metadata"]
        others = [f for f in findings if f.get("check") != "metadata"]
        error = LeakageError(
            "%s leaks its own answers: %s"
            % (paper.paper_id, others[:4] + metadata_findings[:4]))
        # The message is prose; these are the same findings as data, so a caller
        # that wants to adjudicate does not have to parse an f-string.
        error.findings = findings
        error.multiplicity = multiplicity
        error.metadata_unscored = unscored
        raise error

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
    # Published on every paper, findings or none: how many distinct cuts the token
    # check tried under each answer key, the family-wise rate that many tests
    # carries, and -- per answer-alphabet group -- the strongest evidence any token
    # could have produced there. The last is what separates "nothing fired" from
    # "nothing could have fired", which is the whole of V21 restated at the level of
    # the statistic. (V25)
    report["metadata_multiplicity"] = multiplicity
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
