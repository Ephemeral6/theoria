"""A32: the desk replies the arm paid for and did not use.

Offline. No key, no network, no model call, no spend -- the archive and a
scripted desk are the whole material.

The file is organised by claim, and each claim gets its negative control in the
same block rather than in a section at the end, because a control that lives
somewhere else stops being read:

1. **The transport detector is arithmetic, and it says "I don't know".** The
   drop count comes from the arm's own usage records; the control is a usage
   block with no `iterations`, which must return `None` and not `0`.
2. **The classes partition the archive.** Every call lands in exactly one, and
   the money adds up to the bill; the control is a leg with no `desk/`, which
   must report absence rather than a clean sweep.
3. **The parser reads a qualified marker without believing it.** The control is
   that a `=== THEORY (continued ...) ===` fragment must NOT become
   `parsed["theory"]` -- writing half a manual into `theory.dsl` compiles green
   over half a world, which is worse than the refusal it replaces.
4. **The beat keeps what survived.** The control is an empty manual, where
   salvaging a playbook would put an unevidenced claim in the books, and the
   salvage must decline.
5. **The complaint names what happened.** The control is a call with no
   truncation, which must still get the old plain complaint.
6. **The loop refuses to buy the same question twice.** The control is a
   repair whose prompt legitimately differs, which must still be sent.
7. **The happy path did not move.** A clean three-block reply on a whole call
   behaves exactly as before, salvage and guard both untouched.
8. **The cache arithmetic can say "worth it".** The control is a synthetic
   archive whose read/write ratio clears the break-even, which must report a
   saving in the other direction -- otherwise the module is not measuring, it
   is asserting.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                     # noqa: E402,F401

from armtools import cache_premium, desk_discard      # noqa: E402
from harness import replywholeness                    # noqa: E402
from inner import deskdiet, theorize                  # noqa: E402
from inner.books import Books                         # noqa: E402
from inner.grammar_card import WORKED_EXAMPLE         # noqa: E402
from world.frames import FrameStore, Step             # noqa: E402

RUNS = os.path.join(ARM, "runs")


# ------------------------------------------------------------------ fixtures
def _grid(n, fill=0, mark=None):
    g = [[fill] * n for _ in range(n)]
    if mark:
        r, c = mark
        g[r][c] = 6
    return g


def _store(n_steps=6, size=6):
    store = FrameStore()
    store.add(Step(0, "RESET", [_grid(size, mark=(0, 0))], state="NOT_FINISHED"))
    for i in range(1, n_steps):
        store.add(Step(i, "ACTION%d" % (1 + i % 4),
                       [_grid(size, mark=(i % size, (i * 2) % size))],
                       state="NOT_FINISHED"))
    return store


def _engines():
    return {"window": {"box": [0, 5, 0, 5]},
            "mdl_segmenter": {"objects": [{"id": "obj0", "color": 6,
                                           "cells": [[0, 0]]}]}}


def _books(tmp_path, theory=""):
    books = Books(str(tmp_path))
    books.write(theory=theory, playbook="# nothing defensible yet\n")
    return books


def _candidates(tmp_path):
    path = os.path.join(str(tmp_path), "candidates.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('{"kind": "object", "status": "candidate"}\n')
    return path


class ScriptedDesk:
    """A desk that returns canned replies and reports a canned drop count."""

    def __init__(self, replies, dropped=None):
        self.replies = list(replies)
        self.prompts = []
        self.last_messages_dropped = dropped

    def call(self, prompt, *, beat, step_idx=None, label=None):
        assert self.replies, "the desk was called more times than scripted"
        self.prompts.append(prompt)
        return self.replies.pop(0)


def _reply(theory=None, playbook="# none\n", log="[]", theory_qualifier=""):
    parts = []
    if theory is not None:
        parts.append("=== THEORY%s ===\n```\n%s\n```" % (theory_qualifier, theory))
    if playbook is not None:
        parts.append("=== PLAYBOOK ===\n```\n%s\n```" % playbook)
    if log is not None:
        parts.append("=== LOG ===\n```json\n%s\n```" % log)
    return "\n\n".join(parts) + "\n"


def _usage(total, last, iterations=True):
    u = {"output_tokens": total}
    if iterations:
        u["iterations"] = [{"output_tokens": last}]
    return u


# ================================ 1. the transport detector, and its control
def test_drop_count_is_a_multiple_of_the_models_own_ceiling():
    n, why = replywholeness.messages_dropped(_usage(132309, 4309), cap=64000)
    assert n == 2
    assert "64000-token output ceiling" in why


def test_a_whole_call_reports_zero_not_none():
    n, _why = replywholeness.messages_dropped(_usage(45763, 45763), cap=64000)
    assert n == 0


def test_absence_of_iterations_is_recorded_as_absence_not_as_zero():
    """The control. A call whose per-message usage was never recorded has not
    been shown to be whole, and a detector that certifies exactly the calls it
    cannot see is worse than no detector."""
    n, why = replywholeness.messages_dropped({"output_tokens": 50000})
    assert n is None, "no `iterations` must be unknown, never 0"
    assert "neither known to be whole nor known to be truncated" in why
    n2, _ = replywholeness.messages_dropped({})
    assert n2 is None


def test_an_unexplained_remainder_is_reported_as_a_floor():
    n, why = replywholeness.messages_dropped(_usage(70000, 1000), cap=64000)
    assert n == 1
    assert "floor" in why


def test_the_ceiling_is_read_from_the_envelope_when_it_is_there():
    env = {"modelUsage": {"claude-opus-5": {"maxOutputTokens": 64000}}}
    assert replywholeness.ceiling_from_envelope(env, "claude-opus-5") == 64000
    assert replywholeness.ceiling_from_envelope(env, "other") is None
    assert replywholeness.ceiling_from_envelope({}, "claude-opus-5") is None


@pytest.mark.skipif(not os.path.isdir(RUNS), reason="no archive on this machine")
def test_every_archived_drop_is_an_exact_multiple_of_the_ceiling():
    """The claim that makes the count a count and not a ratio: across the whole
    archive the unaccounted output is either zero or an exact multiple of the
    ceiling. One remainder anywhere and this is a heuristic instead."""
    report = desk_discard.sweep(RUNS)
    seen = 0
    for leg in report["legs"]:
        for row in leg["calls"]:
            if row["messages_dropped"]:
                seen += 1
                assert "floor" not in row["why_messages_dropped"], (
                    "%s call %s has an unexplained remainder"
                    % (leg["leg"], row["call"]))
    assert seen == report["transport"]["calls_that_dropped_a_message"]
    assert seen >= 19, "the archive had 19 such calls when this was written"


# ==================================== 2. the classes partition, and its control
@pytest.mark.skipif(not os.path.isdir(RUNS), reason="no archive on this machine")
def test_every_call_lands_in_exactly_one_class_and_the_money_adds_up():
    report = desk_discard.sweep(RUNS)
    assert sum(report["counts"].values()) == report["calls"]
    assert sum(report["usd"].values()) == pytest.approx(report["usd_total"])
    for leg in report["legs"]:
        for row in leg["calls"]:
            assert row["verdict"] in desk_discard.CLASSES


def test_a_leg_with_no_transcripts_reports_absence_not_a_clean_sweep(tmp_path):
    """The control. `has_transcripts` False and a `why_no_calls` sentence --
    never a row of zeroes that reads as "asked and found nothing"."""
    leg = tmp_path / "20260101T0000Z-empty"
    leg.mkdir()
    out = desk_discard.sweep_leg(str(leg))
    assert out["has_transcripts"] is False
    assert "not the same as having made no call" in out["why_no_calls"]
    assert out["calls"] == []


def test_each_class_names_the_file_that_owns_its_repair():
    """The whole point of the module: five discards, five owners. A class with
    no owner must be one of the two that are not defects."""
    for cls in desk_discard.CLASSES:
        owner = desk_discard.OWNER[cls]
        if cls in ("used", "provider_refusal", "empty"):
            assert owner is None
        else:
            assert owner and ".py" in owner


# =================================== 3. the parser reads without believing
def test_a_qualified_theory_marker_is_read_as_a_fragment_not_as_the_manual():
    """The control that matters most in this file. The regex must find the
    block -- otherwise the arm cannot say why the call failed -- and the beat
    must NOT receive it as `theory`, or a remainder gets written into
    theory.dsl and compiles green over half a world."""
    text = _reply(theory="rule fragment\n",
                  theory_qualifier=" (continued -- the remainder of theory.dsl)")
    parsed = theorize.parse_reply(text)
    assert parsed["theory"] == "", "a fragment must never become the manual"
    assert "THEORY" not in parsed["blocks_found"]
    assert "THEORY" in parsed["markers_found"]
    assert "THEORY" in parsed["fragments"]
    assert "continued" in parsed["qualifiers"]["THEORY"]


def test_a_bare_marker_is_unchanged():
    parsed = theorize.parse_reply(_reply(theory="object Cart {}\n"))
    assert parsed["theory"] == "object Cart {}"
    assert parsed["blocks_found"] == ["LOG", "PLAYBOOK", "THEORY"]
    assert parsed["qualifiers"] == {}
    assert parsed["fragments"] == {}


def test_a_log_survives_a_qualified_marker_because_half_a_list_is_still_a_list():
    text = _reply(theory=None, playbook=None,
                  log='[{"id": "O-01", "verdict": "accept"}]')
    text = text.replace("=== LOG ===", "=== LOG (continued) ===")
    parsed = theorize.parse_reply(text)
    assert len(parsed["log"]) == 1
    assert parsed["log"][0]["id"] == "O-01"


def test_the_tolerance_does_not_swallow_the_closing_marker():
    """`[^=\\n]*` is deliberate: a greedy qualifier would match across `===`
    and turn two blocks into one."""
    parsed = theorize.parse_reply(_reply(theory="a\n", playbook="b\n", log="[]"))
    assert sorted(parsed["markers_found"]) == ["LOG", "PLAYBOOK", "THEORY"]


# ======================================= 4. the beat keeps what survived
def test_a_reply_with_no_manual_still_yields_its_playbook_and_its_log(tmp_path):
    books = _books(tmp_path, theory=WORKED_EXAMPLE)
    parsed = theorize.parse_reply(
        _reply(theory=None, playbook="prefer LEFT\n",
               log='[{"id": "R-01", "verdict": "accept"}]'))
    kept = theorize._salvage(books, parsed)
    assert kept["salvaged_log_entries"] == 1
    assert kept["salvaged_playbook"] is True
    assert "prefer LEFT" in books.playbook
    assert books.theory.strip() == WORKED_EXAMPLE.strip(), "the manual must not move"


def test_salvage_declines_to_write_a_playbook_against_an_empty_manual(tmp_path):
    """The control. A playbook with no manual behind it is a claim no evidence
    reaches, and the books are the only thing this system predicts from."""
    books = _books(tmp_path, theory="")
    parsed = theorize.parse_reply(_reply(theory=None, playbook="prefer LEFT\n"))
    kept = theorize._salvage(books, parsed)
    assert kept["salvaged_playbook"] is False
    assert "prefer LEFT" not in books.playbook


# ================================== 5. the complaint names what happened
def test_the_complaint_names_the_truncation_when_the_transport_lost_messages():
    parsed = theorize.parse_reply(_reply(theory=None, playbook="p\n"))
    out = theorize._missing_theory(parsed, dropped=1, allow_patch=False)
    assert "transport_truncation" in out
    assert "was never delivered" in out["transport_truncation"]
    assert "THEORY block ALONE" in out["what_to_do"]


def test_the_truncation_complaint_offers_the_patch_when_the_patch_is_on():
    parsed = theorize.parse_reply(_reply(theory=None))
    out = theorize._missing_theory(parsed, dropped=2, allow_patch=True)
    assert "THEORY-PATCH" in out["what_to_do"]


def test_the_complaint_names_the_qualifier_when_that_is_what_happened():
    parsed = theorize.parse_reply(
        _reply(theory="frag\n", theory_qualifier=" (continued)"))
    out = theorize._missing_theory(parsed, dropped=0, allow_patch=False)
    assert "transport_truncation" not in out
    assert "qualified" in out["reply"]


def test_with_nothing_known_the_complaint_is_the_plain_one():
    """The control. No truncation and no qualifier means the desk really did
    answer badly, and the old sentence is the right one."""
    parsed = theorize.parse_reply(_reply(theory=None, playbook="p\n"))
    for dropped in (0, None):
        out = theorize._missing_theory(parsed, dropped=dropped, allow_patch=False)
        assert out == {"reply": "the reply carried no === THEORY === block; "
                                "emit all three blocks"}


# ===================================== 6. the loop will not buy a repeat
def test_the_beat_refuses_a_repair_prompt_it_has_already_paid_for(tmp_path):
    """The archive's 11 identical re-asks were all `round3`: the old complaint
    for a missing THEORY block was a constant, so attempt 3 sent attempt 2's
    bytes. Here the complaint is forced constant to reproduce that exactly."""
    books = _books(tmp_path, theory=WORKED_EXAMPLE)
    desk = ScriptedDesk([_reply(theory=None, playbook="p\n"),
                         _reply(theory=None, playbook="p\n"),
                         _reply(theory=None, playbook="p\n")], dropped=None)
    saved = theorize._missing_theory
    theorize._missing_theory = lambda *a, **k: {"reply": "constant"}
    try:
        result = theorize.run(desk, books, _store(), _candidates(tmp_path),
                              engines=_engines())
    finally:
        theorize._missing_theory = saved

    assert result["calls"] == 2, "attempt 3 must not be sent, let alone paid for"
    assert len(desk.prompts) == 2
    last = result["rounds"][-1]
    assert last.get("not_sent") is True
    assert "byte-identical" in last["error"]


def test_a_repair_whose_prompt_genuinely_differs_is_still_sent(tmp_path):
    """The control. The guard must stop repeats, not repairs -- and with the
    real complaint (which varies with what happened) the bytes do differ."""
    books = _books(tmp_path, theory=WORKED_EXAMPLE)
    desk = ScriptedDesk([_reply(theory=None, playbook="p\n"),
                         _reply(theory=WORKED_EXAMPLE)], dropped=1)
    result = theorize.run(desk, books, _store(), _candidates(tmp_path),
                          engines=_engines())
    assert result["calls"] == 2
    assert desk.prompts[0] != desk.prompts[1]
    assert "was never delivered" in desk.prompts[1]


# ============================== 7. the happy path did not move
def test_a_clean_reply_on_a_whole_call_behaves_exactly_as_before(tmp_path):
    books = _books(tmp_path, theory="")
    desk = ScriptedDesk([_reply(theory=WORKED_EXAMPLE,
                                log='[{"id": "O-01", "verdict": "accept"}]')],
                        dropped=0)
    result = theorize.run(desk, books, _store(), _candidates(tmp_path),
                          engines=_engines())
    assert result["calls"] == 1
    assert len(result["rounds"]) == 1
    entry = result["rounds"][0]
    assert entry["blocks"] == ["LOG", "PLAYBOOK", "THEORY"]
    assert entry["messages_dropped"] == 0
    assert "salvaged_log_entries" not in entry, "salvage must not run on success"
    assert "word_table" in books.theory
    assert len(result["log"]) == 1


def test_a_desk_that_reports_no_drop_count_does_not_break_the_beat(tmp_path):
    """The control for the new coupling: `last_messages_dropped` is read with
    `getattr`, so a desk double that never heard of it still works."""
    class Bare:
        def __init__(self):
            self.replies = [_reply(theory=WORKED_EXAMPLE)]

        def call(self, prompt, *, beat, step_idx=None, label=None):
            return self.replies.pop(0)

    books = _books(tmp_path, theory="")
    result = theorize.run(Bare(), books, _store(), _candidates(tmp_path),
                          engines=_engines())
    assert result["rounds"][0]["messages_dropped"] is None


# ============================== 8. the cache arithmetic, and its control
@pytest.mark.skipif(not os.path.isdir(RUNS), reason="no archive on this machine")
def test_the_rate_table_rebuilds_the_clis_own_bill():
    """A rate column that cannot reproduce the provider's arithmetic has no
    business pricing a counterfactual from it."""
    out = cache_premium.report(RUNS)
    assert out["reproduces_bill"] is True
    assert out["reproduction"]["relative_residual"] < 0.01


@pytest.mark.skipif(not os.path.isdir(RUNS), reason="no archive on this machine")
def test_every_cached_token_in_the_archive_went_in_at_the_one_hour_ttl():
    out = cache_premium.report(RUNS)
    assert out["ttl_split"]["all_at_1h"] is True
    assert out["ttl_split"]["ephemeral_5m"] == 0


@pytest.mark.skipif(not os.path.isdir(RUNS), reason="no archive on this machine")
def test_the_reads_are_within_call_continuations_not_reuse():
    out = cache_premium.report(RUNS)
    t = out["totals"]
    assert t["calls_reading_cache"] >= 20
    # At most one call has ever read cache without also having been split
    # across messages. If this ever rises, the reads have become real reuse and
    # the finding needs re-reading.
    assert t["calls_reading_cache_single_message"] <= 1


def test_breakeven_is_arithmetic_and_matches_the_published_multiples():
    rates = cache_premium.RATES["claude-opus-5"]
    assert round(cache_premium.breakeven_read_ratio(rates, "1h"), 4) == 1.1111
    assert round(cache_premium.breakeven_read_ratio(rates, "5m"), 4) == 0.2778


def test_the_module_reports_a_win_when_the_reads_actually_clear_breakeven(tmp_path):
    """The control. A module that always answers "caching is a net loss" is
    asserting, not measuring. Here reads are 3x writes -- well past the 1.11
    break-even -- and dropping the cache must cost money, not save it."""
    leg = tmp_path / "20260101T0000Z-reused"
    leg.mkdir()
    with open(leg / "desk_log.json", "w", encoding="utf-8") as fh:
        json.dump([{"call": 1, "model": "claude-opus-5", "cli_cost_usd": 1.0,
                    "usage": {"input_tokens": 0, "output_tokens": 1000,
                              "cache_creation_input_tokens": 100000,
                              "cache_read_input_tokens": 300000,
                              "cache_creation": {"ephemeral_1h_input_tokens": 100000,
                                                 "ephemeral_5m_input_tokens": 0},
                              "iterations": [{"output_tokens": 1000}]}}], fh)
    out = cache_premium.report(str(tmp_path))
    assert out["read_write_ratio"] == 3.0
    assert out["savings_usd"]["dropping_the_cache"] < 0, (
        "with reads past break-even, dropping the cache must cost money")


@pytest.mark.skipif(not os.path.isdir(RUNS), reason="no archive on this machine")
def test_the_lever_the_arm_actually_holds_is_named_and_the_others_are_not():
    """Honesty about scope: three of the four levers are the CLI's, and the
    module must say so rather than recommending something the arm cannot do."""
    out = cache_premium.report(RUNS)
    actionable = [l for l in out["in_the_arms_control"] if l["actionable_now"]]
    assert len(actionable) == 1
    assert "deskdiet" in actionable[0]["why"]
    for lever in out["in_the_arms_control"]:
        if not lever["actionable_now"]:
            assert lever["held_by"] == "the CLI"


def test_the_diet_knobs_that_are_the_lever_are_still_default_off():
    """The negative control for the recommendation itself. The lever is only a
    lever while it is off; if a future change turns it on, this test fails and
    the finding must be re-measured rather than re-quoted."""
    diet = deskdiet.full()
    assert diet.evidence_delta is False
    assert diet.theory_patch is False


# ============================== 9. the replay is honest about its limits
@pytest.mark.skipif(not os.path.isdir(RUNS), reason="no archive on this machine")
def test_the_replay_recovers_adjudications_and_claims_no_manual():
    out = desk_discard.replay(RUNS)
    assert out["kept"]["log_entries"] >= 299
    assert out["complaints_still_the_old_constant"] == 0
    assert out["complaints_that_now_name_the_truncation"] >= 17
    # The five total-loss calls stay lost. The front of a truncated reply is
    # not in the envelope, the ledger or the transcript, so no offline repair
    # can reach it and the replay must not pretend otherwise.
    assert out["unrecoverable_by_replay"]["calls"] >= 5
    assert "NOT a claim that the manual was recovered" in out["caveat"]
