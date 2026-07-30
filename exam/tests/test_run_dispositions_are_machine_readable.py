"""A disposition declared in prose must also be declared in the JSON.

V26 ruled `-r2` annulled as an instrument and wrote the ruling as Markdown. An
adversarial review then measured what that remedy was worth to a machine:
`git diff` over the r2 run directory touched **one file, RESULTS.md, +24 lines**.
`RESULTS.json` -- which is where `tier_means`, `per_item`, `by_family` and
`delta` live, and therefore what any automated consumer actually reads -- was
byte-identical, still saying `58.0/58.0` and `matches_preregistration: true`.

That is the same defect the exam track has been chasing since V19 under a
different name: a check, or here a correction, that prints without being able to
speak to anyone who is listening. The ruling's own argument for why cohort 1's
void "did real work" was machine-level -- it kept six answer files out of any
`RESULTS.json`. By that standard the annulment did none.

So the invariant is general rather than a pin on r2: if any prose artefact under
`exam/runs/` declares a disposition about a run, that run's `RESULTS.json` must
carry a machine-readable one too. This test is what stops the next remedy from
being inert.
"""

from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.path.join(HERE, "runs")

#: Words that, next to a run's own directory name in prose, mean somebody has
#: ruled on that run rather than merely mentioned it.
DISPOSITION_WORDS = ("voided", "void", "annul", "annulled", "overturned",
                     "withdrawn", "retracted")

#: Any one of these keys in `RESULTS.json` counts as the disposition being
#: machine-readable. Deliberately a set: a void, an annulment and a withdrawal
#: are different severities and must not be forced to share a spelling -- that
#: flattening is the thing V26's ruling declined to do.
DISPOSITION_KEYS = ("annulment", "voided", "voided_reason", "withdrawn",
                    "disposition")


def _run_dirs():
    if not os.path.isdir(RUNS):
        return []
    return sorted(d for d in os.listdir(RUNS)
                  if os.path.isdir(os.path.join(RUNS, d)))


def _prose_under_runs():
    for root, _dirs, names in os.walk(RUNS):
        for name in sorted(names):
            if name.endswith(".md"):
                path = os.path.join(root, name)
                with open(path, encoding="utf-8") as handle:
                    yield os.path.relpath(path, HERE), handle.read()


def test_a_disposition_in_prose_is_also_in_the_json():
    ruled = {}
    for rel, text in _prose_under_runs():
        lowered = text.lower()
        for run in _run_dirs():
            if run.lower() not in lowered:
                continue
            # The mention has to sit near a disposition word to count, so that a
            # run merely citing another run's data does not implicate it.
            for match in re.finditer(re.escape(run.lower()), lowered):
                window = lowered[max(0, match.start() - 400):match.end() + 400]
                hit = [w for w in DISPOSITION_WORDS
                       if re.search(r"\b%s\b" % re.escape(w), window)]
                if hit:
                    ruled.setdefault(run, set()).add((rel, hit[0]))

    offenders = []
    for run, why in sorted(ruled.items()):
        results = os.path.join(RUNS, run, "RESULTS.json")
        if not os.path.exists(results):
            # No machine-readable result to mislead anyone with. A void whose
            # run never produced a RESULTS.json is cohort 1's case, and the
            # ruling is right that the void already did the work there.
            continue
        with open(results, encoding="utf-8") as handle:
            payload = json.load(handle)
        if not any(key in payload for key in DISPOSITION_KEYS):
            offenders.append((run, sorted(why)))

    assert not offenders, (
        "these runs are ruled on in prose but their RESULTS.json says nothing, "
        "so every automated reader still sees an unmarked run -- add one of %s "
        "to the JSON: %s" % (list(DISPOSITION_KEYS), offenders))


def test_the_r2_annulment_says_what_it_annuls_and_what_survives():
    """The regression pin, because r2 is the case that produced the rule.

    Asserting the key exists is not enough: an empty `annulment: {}` would pass
    the general test above while telling a reader nothing. What has to be present
    is the scope (so a consumer knows which numbers are dead) and the survivors
    (so the annulment is not read as repudiating the whole run).
    """
    path = os.path.join(RUNS, "20260728T202540Z-V11-handover-auto-r2",
                        "RESULTS.json")
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)

    ann = payload["annulment"]
    assert ann["status"] == "annulled_as_instrument", ann["status"]
    assert ann["scope_families"] == ["optimal_action"], ann["scope_families"]
    assert sorted(ann["scope_items"]) == ["v11-opt-01", "v11-opt-04"]
    assert ann["numbers_that_stand"].strip(), "no survivors recorded"
    assert os.path.exists(os.path.join(HERE, os.pardir, ann["ruling"])), (
        "the annulment cites a ruling that is not on disk: %s" % ann["ruling"])

    # The family the annulment names must itself be flagged where the numbers
    # are, not only at the top level -- `by_family` is what a table generator
    # reads, and it would otherwise print `delta 0.0` as a null result.
    family = payload["by_family"]["optimal_action"]
    assert family.get("annulled") is True, (
        "by_family.optimal_action still reads as an ordinary null result: %s"
        % family)
