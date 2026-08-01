"""The reply classifier, and the four things it must be able to say.

`armtools/replyloss.py` exists because `no THEORY block in the reply` was one
sentence covering three unrelated events. A classifier that cannot say no is
worth nothing here, so every class below has a test that FIRES it and at least
one that REFUSES it -- in particular `lost_continuation`, which is the finding,
is asserted absent on a well-formed reply, on an empty one, and on a provider
refusal. A detector that answered "lost" to all four inputs would pass a suite
that only checked the positive case.

The last two tests read the real archive. They are the ones that would notice
if a future harness change fixed the transport, and they are written so that
"the archive no longer contains this defect" fails loudly rather than passing
silently -- an assertion about a fixed number, with the reason in the message.
"""

import io
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                      # noqa: E402,F401

from armtools import replyloss                         # noqa: E402

RUNS = os.path.join(ARM, "runs")

WELL_FORMED = (
    "=== THEORY ===\n```\nsemantics:\n  grid 64x64\n```\n\n"
    "=== PLAYBOOK ===\n```\n# nothing defensible yet\n```\n\n"
    "=== LOG ===\n```json\n[]\n```\n")

#: The exact shape found on `R1b-sk48-b/desk/call-002`: the desk's own
#: continuation header, which only exists because the answer spanned messages.
A_REAL_TAIL = (
    "=== THEORY (continued -- the remainder of theory.dsl, appended to the "
    "block above) ===\n```\n  rule a1_step \"...\"\n```\n\n"
    "=== PLAYBOOK ===\n```\n# ...\n```\n")

#: The shape found on `R1b-g50t-a/desk/call-002` and three others: the LOG
#: block alone, arriving as its own message.
A_LOG_ONLY_TAIL = ('```json\n[\n  {"id": "P-02", "verdict": "probe-pending"}\n'
                   "]\n```\n")

SESSION_LIMIT = "You've hit your session limit - resets 8:20pm (Asia/Shanghai)\n"


# ------------------------------------------------------------ the four classes
def test_a_complete_reply_is_well_formed():
    out = replyloss.classify(WELL_FORMED)
    assert out["verdict"] == "well_formed"
    assert out["markers_present"] == ["=== THEORY ===", "=== PLAYBOOK ===",
                                      "=== LOG ==="]


def test_an_empty_reply_is_empty_and_is_not_a_loss():
    """The negative control that matters most for the headline number.

    An empty reply is a failed call. Counting it as a lost continuation would
    inflate the finding with calls that never produced anything to lose.
    """
    for blank in ("", "   ", "\n\n\n"):
        out = replyloss.classify(blank)
        assert out["verdict"] == "empty", blank
        assert out["verdict"] != "lost_continuation"


def test_a_provider_refusal_is_not_a_loss():
    out = replyloss.classify(SESSION_LIMIT)
    assert out["verdict"] == "provider_refusal"
    assert "never ran" in out["why"]


def test_a_tail_that_still_carries_its_own_continuation_header_is_a_loss():
    out = replyloss.classify(A_REAL_TAIL)
    assert out["verdict"] == "lost_continuation"
    # The evidence a reader needs: THEORY is missing, PLAYBOOK survived.
    assert out["has_theory_marker_anywhere"] is False
    assert "=== PLAYBOOK ===" in out["markers_present"]


def test_a_log_block_arriving_alone_is_a_loss():
    out = replyloss.classify(A_LOG_ONLY_TAIL)
    assert out["verdict"] == "lost_continuation"
    assert out["markers_present"] == []


def test_a_reply_quoting_the_refusal_phrase_is_not_a_provider_refusal():
    """The prefix match, negatively controlled.

    A desk that writes a theorem *about* hitting the session limit is
    answering. A substring search would have called this a provider refusal
    and dropped a real answer out of the count.
    """
    reply = (WELL_FORMED.replace(
        "# nothing defensible yet",
        "# last round I saw \"You've hit your session limit\" and lost a turn"))
    assert replyloss.classify(reply)["verdict"] == "well_formed"


def test_a_marker_that_is_present_but_not_first_is_still_a_loss():
    """The discriminator is position, not presence.

    `inner/theorize.py` looks for the marker anywhere, which is why it accepted
    nothing here; this module's stronger reading is that a reply beginning
    before its own first block began somewhere the arm never saw.
    """
    out = replyloss.classify("...end of the previous message.\n" + WELL_FORMED)
    assert out["verdict"] == "lost_continuation"
    assert out["has_theory_marker_anywhere"] is True


# --------------------------------------------------------- evidence, not test
def test_the_token_ratio_is_carried_but_does_not_decide():
    """The ratio was the obvious detector and it does not work.

    `claude -p` bills thinking tokens that never appear in `result`, so a
    well-formed reply can sit at 0.3 chars per output token. Asserted here so
    nobody reintroduces the threshold: the same ratio is attached to a
    well-formed reply and to a lost one, and only the structure separates them.
    """
    good = replyloss.classify(WELL_FORMED, output_tokens=60000)
    bad = replyloss.classify(A_LOG_ONLY_TAIL, output_tokens=60000)
    assert good["verdict"] == "well_formed"
    assert bad["verdict"] == "lost_continuation"
    assert good["chars_per_output_token"] < 0.01
    assert bad["chars_per_output_token"] < 0.01


# ---------------------------------------------------------------- the archive
def test_every_reply_the_arm_accepted_begins_with_the_marker():
    """The claim the whole classifier rests on, checked against every leg.

    If a single accepted reply began somewhere else, `well_formed` would be
    the wrong name for the class and the 11 would be an overcount.
    """
    report = replyloss.sweep(RUNS)
    assert report["calls"] > 50, "the archive sweep read almost nothing"
    for leg in report["legs"]:
        for row in leg["calls"]:
            if row["verdict"] != "well_formed":
                continue
            assert row["begins_with"].startswith("=== THEORY ==="), (
                leg["leg"], row["transcript"])


def test_the_archive_still_holds_the_eleven_lost_replies():
    """The measurement, pinned.

    This number is a fact about files that are committed, so it does not drift
    on its own. It moves when a leg is added or when the transport is fixed and
    a leg is re-run -- and in both cases somebody should have to come here and
    say so in the diff rather than watch a green suite.
    """
    report = replyloss.sweep(RUNS)
    assert report["counts"]["lost_continuation"] == 11, report["counts"]
    assert report["counts"]["provider_refusal"] == 24, report["counts"]
    assert report["counts"]["empty"] == 1, report["counts"]
    # $31.05 of $108.54. Compared loosely so a re-priced archive does not fail
    # here for a rounding reason -- the point is the order of magnitude.
    assert 30.0 < report["usd_lost_to_lost_continuation"] < 32.0
    assert 0.25 < report["share_of_desk_spend_lost"] < 0.32


def test_a_leg_with_no_transcripts_says_so_rather_than_reporting_zero():
    """Absence recorded as absence, per the arm's own rule."""
    out = replyloss.sweep_leg(os.path.join(RUNS, "does-not-exist"))
    assert out["has_transcripts"] is False
    assert out["calls"] == []
    assert "not the same as having made no call" in out["why_no_calls"]


def test_the_reading_refuses_to_call_an_empty_sweep_clean(tmp_path):
    empty = str(tmp_path)
    report = replyloss.sweep(empty)
    assert report["calls"] == 0
    assert "not a clean sweep" in report["reading"]


def test_the_transcript_reader_returns_none_for_a_file_it_does_not_understand(
        tmp_path):
    path = os.path.join(str(tmp_path), "call-001-theorize-round1.md")
    with io.open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("# not a transcript\n")
    assert replyloss.read_transcript(path) is None


@pytest.mark.parametrize("leg,call,verdict", [
    ("20260801T001851Z-R1b-g50t-a", 2, "lost_continuation"),
    ("20260801T001851Z-R1b-g50t-a", 3, "well_formed"),
    ("20260801T001851Z-R1b-sk48-b", 2, "lost_continuation"),
    ("20260728T083400Z-E3-sk48-carried-v2", 7, "provider_refusal"),
])
def test_named_archived_calls_classify_as_recorded(leg, call, verdict):
    """Four hand-read transcripts, pinned to what a human found in them.

    The pair on `R1b-g50t-a` is the point: call 2 lost the answer to the first
    goal proposal, call 3 -- the repair round the loss forced -- carried it,
    and the two sit next to each other in the same beat.
    """
    out = replyloss.sweep_leg(os.path.join(RUNS, leg))
    row = [r for r in out["calls"] if r["call"] == call]
    assert row, (leg, call)
    assert row[0]["verdict"] == verdict, row[0]["begins_with"]
