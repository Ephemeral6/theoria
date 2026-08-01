"""`LEDGER_FORMAT.md` §3 and `reconcile.py` must say the same thing.

The reconciliation obligation lives in two places on purpose. `LEDGER_FORMAT.md`
is normative -- F-16 ruled it the canon -- and `reconcile.py` is what actually
runs. Nothing has ever obliged them to agree, and the last time they disagreed
the document stated an obligation no code could discharge, which is the defect
`reconcile.py`'s own module docstring opens by describing.

The failure mode this guards is narrow and has already happened twice on this
item. Both are about a **non-voting gap being written up as a voting leg**:

* the ticket that opened S31 asked for reconciliation on a
  `(cost, actions, turns)` triple. `turns` is not a leg -- no turn index exists
  in the ledger at all -- and F-19, the finding that asked for it, withdrew it
  the same day. A document that had listed it as the third leg would have made
  a check with no failing path look like the specification;
* the same paragraph nearly widened "per-*step* score is not cross-verifiable"
  to "score is not cross-verifiable", which would have discarded the per-*run*
  scorecard check that works.

So the check is keyed to the two things that can drift: the **set and order of
voting legs**, and the requirement that **every gap the reconciler reports is
named in the document as a gap and never as a leg**. Both sides are read at run
time -- the key from `reconcile.RECONCILIATION_KEY`, the gap names from a real
`reconcile_run` report, the legs from the document's own table -- so neither can
be satisfied by a constant somebody copied.

It is deliberately not a digest. `LEDGER_FORMAT.md` is still being edited, and a
byte check would go red on somebody else's correct prose while staying green on
a leg quietly renamed inside the table.
"""
import os
import re

import pytest

from test_reconcile import GAME, RUN, _card

from proxy.ledger import Ledger, RunLedger
from proxy.reconcile import RECONCILIATION_KEY, reconcile_run

DOC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "LEDGER_FORMAT.md")

SECTION = "### Reconciliation obligation"


def section(text=None):
    """§3's reconciliation subsection, up to the next heading of any rank."""
    text = open(DOC, encoding="utf-8").read() if text is None else text
    start = text.find(SECTION)
    assert start >= 0, "%s no longer contains %r" % (DOC, SECTION)
    rest = text[start + len(SECTION):]
    end = rest.find("\n## ")
    return rest if end < 0 else rest[:end]


def legs_named(body):
    """The leg names the document's table declares, in the order it lists them.

    The first cell of each table row is a bolded human name -- `**actions**`,
    `**score, per run**` -- and is normalised to the code's identifier by
    keeping the word characters: `score, per run` -> `score_per_run`. Doing it
    this way rather than with a lookup table is the point: a row renamed to
    something the code does not have becomes a mismatch instead of a silent
    miss.
    """
    names = []
    for line in body.splitlines():
        match = re.match(r"^\|\s*\*\*(.+?)\*\*\s*\|", line.strip())
        if match:
            names.append("_".join(re.findall(r"[a-z0-9]+", match.group(1).lower())))
    return names


def gap_keys():
    """The gaps a real report carries, read off the report and not a list."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "l.jsonl")
        run = RunLedger(Ledger(path), RUN, "mock_arm", game_id=GAME)
        run.run_start(game_id=GAME, card_id="c1")
        run.env_step(GAME, {"name": "RESET", "id": None, "data": None},
                     frames=[[[0]]], card_id="c1", guid="g",
                     levels_completed=0, response={"win_levels": 8},
                     http={"status": 200})
        run.run_end(outcome="done", steps=0, model_calls=0,
                    scorecard=_card(actions=0))
        return sorted(reconcile_run(RUN, path, write_incident=False)["gaps"])


def problems(body, key, gaps):
    """Every way the document and the code can disagree, as sentences.

    A list rather than an assertion so the negative controls below can call it
    on a mutated document and see it go red without a test having to fail.
    """
    found = []
    named = legs_named(body)

    if named != list(key):
        found.append(
            "the table declares legs %s and RECONCILIATION_KEY is %s"
            % (named, list(key)))

    for gap in gaps:
        if gap in named:
            found.append(
                "`%s` is a non-voting gap in the report and the document lists "
                "it as a leg of the obligation" % gap)
        if "`gaps.%s`" % gap not in body:
            found.append(
                "the report carries `gaps.%s` and the document never names it, "
                "so a reader cannot tell the quantity is reported-but-not-voting"
                % gap)

    return found


# -- the gate ---------------------------------------------------------------

def test_the_document_and_the_reconciler_declare_the_same_legs():
    assert problems(section(), RECONCILIATION_KEY, gap_keys()) == []


def test_the_document_states_the_count_it_lists():
    """"keyed to **three quantities**" and a four-row table is a contradiction
    a reader will resolve in favour of the prose."""
    body = section()
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    match = re.search(r"keyed to \*\*(\w+) quantities", body)
    assert match, "§3 no longer states how many quantities it is keyed to"
    assert words[match.group(1)] == len(RECONCILIATION_KEY) == len(legs_named(body))


# -- negative controls: each check, made to fail on purpose ------------------

@pytest.mark.parametrize("mutate,expect", [
    # A leg renamed inside the table. The prose above it still reads correctly,
    # which is exactly why prose is not the check.
    (lambda b: b.replace("| **cost** |", "| **spend** |"),
     "RECONCILIATION_KEY"),
    # The ticket's own mistake: `turns` promoted from a declared gap to a
    # fourth leg of the obligation.
    (lambda b: b.replace("| **score, per run** |",
                         "| **turns** | recorded | the turn counts agree |\n"
                         "| **score, per run** |"),
     "lists it as a leg"),
    # The gap silently dropped from the document, leaving a quantity the
    # reconciler reports and the canon does not mention.
    (lambda b: b.replace("`gaps.turns`", "somewhere"),
     "never names it"),
    (lambda b: b.replace("`gaps.score_per_step`", "somewhere"),
     "never names it"),
])
def test_red_a_mutated_document_is_caught(mutate, expect):
    body = mutate(section())
    assert body != section(), "the mutation did not apply; the check is vacuous"
    found = problems(body, RECONCILIATION_KEY, gap_keys())
    assert found, "a mutated document passed the check"
    assert any(expect in p for p in found), found


def test_red_a_leg_added_to_the_code_and_not_the_document_is_caught():
    """The drift in the other direction. `RECONCILIATION_KEY` is a module
    constant, so this is the shape a future leg would arrive in."""
    found = problems(section(), RECONCILIATION_KEY + ("turns",), gap_keys())
    assert found and "RECONCILIATION_KEY" in found[0], found


# -- the same obligation, applied to the arm vocabulary ----------------------
#
# Added with D-A21-001, and not speculatively: the `arm` row listed five names
# while `ledger.ARMS` held six. `mock_arm` had been registered in code and never
# written into the canon, and nothing noticed for as long as the row existed.
# `arm` is one of the two **hard refusals** in the whole format (§5), so the
# document being wrong about it is the document being wrong about the only part
# of the vocabulary that can stop a run on its first record.

def arms_named(text=None):
    """The arm names the `arm` row of §2's table declares.

    Read out of the row's own prose with a backtick scan rather than a
    hand-maintained list, so a name added to the table in any phrasing counts
    and a name deleted from it stops counting.
    """
    text = open(DOC, encoding="utf-8").read() if text is None else text
    for line in text.splitlines():
        if line.startswith("| `arm` |"):
            return set(re.findall(r"`([a-z0-9_]+)`", line)) - {"arm", "string"}
    raise AssertionError("%s no longer has an `arm` row in its field table" % DOC)


def test_the_document_lists_exactly_the_registered_arm_names():
    from proxy.ledger import ARMS                            # noqa: PLC0415

    declared = arms_named()
    assert declared == set(ARMS), (
        "the canon and `ledger.ARMS` disagree about the arm vocabulary; "
        "only in the document: %s; only in the code: %s"
        % (sorted(declared - set(ARMS)), sorted(set(ARMS) - declared)))


@pytest.mark.parametrize("mutate", [
    # A name registered in code and never written into the canon. This is the
    # exact drift that was found and fixed when the check was written.
    lambda t: t.replace("`mock_arm`, ", ""),
    # A name in the document that the writer would refuse.
    lambda t: t.replace("`ablation`,", "`ablation`, `theoria_ablate`,"),
])
def test_red_an_arm_vocabulary_that_drifts_is_caught(mutate):
    from proxy.ledger import ARMS                            # noqa: PLC0415

    text = mutate(open(DOC, encoding="utf-8").read())
    assert text != open(DOC, encoding="utf-8").read(), (
        "the mutation did not apply; the check is vacuous")
    assert arms_named(text) != set(ARMS)
