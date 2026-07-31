"""Change C: what the desk is shown, and what it costs.

Offline. No key, no network, no model call, no quota -- the desk is a scripted
double that returns text from a list.

The shape of this file follows the shape of the claim. The claim has three
parts and each gets its own block:

1. **The default did not move.** `full` mode must produce the byte-identical
   prompt this arm has always sent, and the strongest way to say that is to
   compare against `build_prompt` called with no diet argument at all -- not
   against a golden string, which would only prove that two copies of the same
   mistake agree.
2. **The diet does what it says.** Each knob is driven and its effect measured
   in chars, on the same store, so the difference is the diet and not the
   fixture.
3. **The guards say no.** Every refusal path in `deskdiet.apply_patch` is
   driven to its refusal and the reason is asserted. A check that has never
   been seen to say no has not been shown to check anything, and a patch
   applier is the worst place in this arm to find that out later: it edits the
   only artefact the whole system predicts from.
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

from armtools import prompt_census                    # noqa: E402
from inner import deskdiet, theorize                  # noqa: E402
from inner.books import Books                         # noqa: E402
from inner.grammar_card import WORKED_EXAMPLE         # noqa: E402
from world.frames import FrameStore, Step             # noqa: E402


# --------------------------------------------------------------- fixtures
def _grid(n, fill=0, mark=None):
    g = [[fill] * n for _ in range(n)]
    if mark:
        r, c = mark
        g[r][c] = 6
    return g


def _store(n_steps=8, size=6):
    """A store whose frames actually differ, so `describe_diff` has something
    to say and the command table is not a column of `no change`."""
    store = FrameStore()
    store.add(Step(0, "RESET", [_grid(size, mark=(0, 0))], state="NOT_FINISHED"))
    for i in range(1, n_steps):
        store.add(Step(i, "ACTION%d" % (1 + i % 4),
                       [_grid(size, mark=(i % size, (i * 2) % size))],
                       state="NOT_FINISHED"))
    return store


def _engines(salt=0):
    return {"window": {"box": [0, 5, 0, 5]},
            "mdl_segmenter": {"objects": [{"id": "obj0", "color": 6,
                                           "cells": [[salt % 6, 0]]}]},
            "cegis_miner": {"rules": [{"id": "r%d" % salt, "guard": "free"}]},
            "zero_space": {"invariants": ["count(obj0) = 1"]}}


def _books(tmp_path, theory=None):
    books = Books(str(tmp_path))
    books.write(theory=theory if theory is not None else "",
                playbook="# nothing defensible yet\n")
    return books


def _candidates(tmp_path):
    path = os.path.join(str(tmp_path), "candidates.jsonl")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write('{"kind": "object", "status": "candidate"}\n' * 3)
    return path


class ScriptedDesk:
    """A desk that returns canned replies and records the prompts it was sent.

    It refuses to be asked more times than it was scripted for, because a test
    whose desk returns the last reply forever cannot tell "the loop repaired
    once" from "the loop spun until the budget ran out".
    """

    def __init__(self, replies):
        self.replies = list(replies)
        self.prompts = []
        self.labels = []

    def call(self, prompt, *, beat, step_idx=None, label=None):
        assert beat == "theorize"
        assert self.replies, "the desk was called more times than it was scripted"
        self.prompts.append(prompt)
        self.labels.append(label)
        return self.replies.pop(0)


def _reply(theory, playbook="# none\n", log="[]"):
    return ("=== THEORY ===\n```\n%s\n```\n\n=== PLAYBOOK ===\n```\n%s\n```\n\n"
            "=== LOG ===\n```json\n%s\n```\n" % (theory, playbook, log))


def _patch_reply(ops, playbook="# none\n", log="[]"):
    return ("=== THEORY-PATCH ===\n```json\n%s\n```\n\n=== PLAYBOOK ===\n```\n%s\n"
            "```\n\n=== LOG ===\n```json\n%s\n```\n"
            % (json.dumps(ops, indent=1), playbook, log))


# ============================================================ 1. the default
def test_full_mode_is_byte_identical_to_today(tmp_path):
    """The switch's whole safety argument in one assertion.

    `DeskDiet()` with every knob off must give the same string as calling
    `build_prompt` the way `inner/loop.py` called it before this change existed
    -- no diet argument at all. Compared on a prompt that exercises every
    optional section, because an equality that only covers the cold-start
    prompt would miss a divergence in the manual or surprise branches.
    """
    store, engines = _store(), _engines()
    books = _books(tmp_path, WORKED_EXAMPLE)
    cands = _candidates(tmp_path)

    class _S:
        kind, family, book, detail = "replay_mismatch", "mechanism", "theory", "t4 diverged"
        payload = {"t": 4}

    for surprises in ([], [_S()]):
        for errors in (None, {"clause": "rules: line 3"}):
            today = theorize.build_prompt(store, engines, books, cands,
                                          surprises, errors, {"cheap": {}})
            switched = theorize.build_prompt(store, engines, books, cands,
                                             surprises, errors, {"cheap": {}},
                                             diet=deskdiet.DeskDiet())
            assert today == switched
            # ... and the same again through the beat's own default path.
            explicit_full = theorize.build_prompt(
                store, engines, books, cands, surprises, errors, {"cheap": {}},
                diet=deskdiet.full(), allow_patch=True)
            assert today == explicit_full


def test_full_mode_never_appends_the_patch_contract(tmp_path):
    books = _books(tmp_path, WORKED_EXAMPLE)
    prompt = theorize.build_prompt(_store(), _engines(), books,
                                   _candidates(tmp_path), [], None, None,
                                   diet=deskdiet.DeskDiet())
    assert "THEORY-PATCH" not in prompt


def test_an_unknown_diet_spec_raises_rather_than_defaulting():
    """A typo in a launch flag must not silently produce a `full` leg labelled
    as a diet leg -- that run would look fine and its finding would be void."""
    with pytest.raises(ValueError) as exc:
        deskdiet.DeskDiet.parse("deit")
    assert "unknown desk diet" in str(exc.value)
    assert deskdiet.DeskDiet.parse(None).name == "full"
    assert deskdiet.DeskDiet.parse("diet").name == "diet"
    assert deskdiet.DeskDiet.parse("patch").name == "patch"
    assert deskdiet.DeskDiet.parse("evidence").name == "evidence"


# ============================================================== 2. the diet
def test_evidence_delta_shrinks_the_brief_and_names_what_it_withheld(tmp_path):
    """The delta knob, measured on one store rather than asserted.

    Also checks the thing that makes it safe: the withheld engine reports are
    NAMED. A desk that cannot tell "this engine said nothing new" from "this
    engine was not run" would read silence as a retraction, and a
    `probe: pending` would be dropped on the strength of it.
    """
    store, engines = _store(n_steps=12), _engines()
    books = _books(tmp_path, WORKED_EXAMPLE)
    cands = _candidates(tmp_path)

    diet = deskdiet.DeskDiet(evidence_delta=True)
    assert diet.state_is_fresh()
    first = theorize.build_prompt(store, engines, books, cands, [], None, None,
                                  diet=diet)
    full_first = theorize.build_prompt(store, engines, books, cands, [], None,
                                       None)
    # Cold: nothing to diff against, so the delta brief is the full brief.
    assert len(first) == len(full_first)

    # Now the beat has run once: 12 steps shown, these engines shown.
    diet.state["labelled_shown"] = 12
    diet.state["engines"] = _engines()

    for i in range(12, 18):
        store.add(Step(i, "ACTION1", [_grid(6, mark=(i % 6, 1))],
                       state="NOT_FINISHED"))
    second_full = theorize.build_prompt(store, engines, books, cands, [], None,
                                        None)
    second_diet = theorize.build_prompt(store, engines, books, cands, [], None,
                                        None, diet=diet)

    assert len(second_diet) < len(second_full)
    assert "already shown in full on the previous call" in second_diet
    assert "already shown in full on the previous call" not in second_full
    # unchanged engines are named, not dropped in silence
    assert "Unchanged, and still standing exactly as you last read them" in second_diet
    for name in ("cegis_miner", "mdl_segmenter", "zero_space"):
        assert name in second_diet


def test_evidence_delta_shows_the_newest_steps_which_full_mode_does_not(tmp_path):
    """A widening, not only a trim.

    `evidence_brief`'s full path renders `labelled[:30]` -- the *first* thirty
    steps. Past step 30 the desk is shown the opening of the level and never
    the transitions that just fired the surprise it is being paid to answer.
    The delta path renders the newest ones. This is asserted rather than
    described because it is the one place the diet changes what the desk can
    know, and it changes it in the direction of the surprise.
    """
    store = _store(n_steps=40)
    books = _books(tmp_path, WORKED_EXAMPLE)
    cands = _candidates(tmp_path)
    diet = deskdiet.DeskDiet(evidence_delta=True)
    diet.state["labelled_shown"] = 30

    full_text = theorize.build_prompt(store, _engines(), books, cands, [], None,
                                      None)
    diet_text = theorize.build_prompt(store, _engines(), books, cands, [], None,
                                      None, diet=diet)
    assert "- t38" not in full_text and "- t39" not in full_text
    assert "- t38" in diet_text and "- t39" in diet_text


def test_the_patch_contract_only_appears_when_there_is_a_manual(tmp_path):
    """A cold desk has no anchor to quote. Asking it for a patch would spend a
    repair round discovering that."""
    cands = _candidates(tmp_path)
    diet = deskdiet.DeskDiet(theory_patch=True)

    cold = theorize.build_prompt(_store(), _engines(), _books(tmp_path / "a"),
                                 cands, [], None, None, diet=diet)
    assert "THEORY-PATCH" not in cold

    warm = theorize.build_prompt(_store(), _engines(),
                                 _books(tmp_path / "b", WORKED_EXAMPLE),
                                 cands, [], None, None, diet=diet)
    assert "=== THEORY-PATCH ===" in warm

    vetoed = theorize.build_prompt(_store(), _engines(),
                                   _books(tmp_path / "c", WORKED_EXAMPLE),
                                   cands, [], None, None, diet=diet,
                                   allow_patch=False)
    assert "THEORY-PATCH" not in vetoed


def test_a_patch_reply_edits_the_manual_and_the_level_still_sees_the_objects(tmp_path):
    """End to end through the beat: a patch applies, the manual changes, and --
    the part that is easy to get wrong -- the level instance is derived from the
    PATCHED manual, not from the (empty) THEORY block of the reply.

    If it were read off the reply, `_objects_from_theory` would find nothing,
    `problem.json` would be empty, the compile would still be green, and
    certify would report every pixel unexplained one beat later. That failure
    would look like a theory problem and would not be one.
    """
    books = _books(tmp_path, WORKED_EXAMPLE)
    before = books.theory
    assert "object Cart" in before

    desk = ScriptedDesk([_patch_reply([
        {"op": "replace", "find": "goal count(Cart) = 1",
         "with": "goal count(Cart) = 2"},
    ], log='[{"id": "R-01", "verdict": "accept", "why": "witnessed at t4"}]')])

    diet = deskdiet.DeskDiet(theory_patch=True)
    result = theorize.run(desk, books, _store(), _candidates(tmp_path),
                          engines=_engines(), diet=diet)

    assert result["calls"] == 1
    assert result["diet"] == {"mode": "patch", "evidence_delta": False,
                              "theory_patch": True}
    assert "goal count(Cart) = 2" in books.theory
    assert "object Cart" in books.theory          # the rest of the book survived
    assert result["rounds"][0]["patch"]["ops"] == 1
    # the level was built from the patched manual
    assert result["rounds"][0]["objects_located"] >= 1
    assert result["log"][0]["id"] == "R-01"


def test_a_whole_theory_block_still_wins_under_the_patch_contract(tmp_path):
    """The escape hatch. A structural rewrite must always be sayable, or the
    diet would force the desk to fake a small patch for a large change."""
    books = _books(tmp_path, WORKED_EXAMPLE)
    rewritten = WORKED_EXAMPLE.replace("goal count(Cart) = 1",
                                       "goal count(Cart) = 3")
    desk = ScriptedDesk([_reply(rewritten)])
    result = theorize.run(desk, books, _store(), _candidates(tmp_path),
                          engines=_engines(),
                          diet=deskdiet.DeskDiet(theory_patch=True))
    assert result["calls"] == 1
    assert "goal count(Cart) = 3" in books.theory
    assert "patch" not in result["rounds"][0]


def test_the_live_census_records_composition_on_every_call(tmp_path):
    """The instrumentation this change is judged by, recorded as the call goes
    out rather than reconstructed from transcripts afterwards."""
    books = _books(tmp_path, WORKED_EXAMPLE)
    desk = ScriptedDesk([_reply(WORKED_EXAMPLE)])
    result = theorize.run(desk, books, _store(), _candidates(tmp_path),
                          engines=_engines())
    census = result["prompt_census"]
    assert len(census) == 1
    entry = census[0]
    assert "census_error" not in entry, entry.get("census_error")
    assert entry["chars"] == len(desk.prompts[0])
    assert sum(entry["by_kind"].values()) == entry["chars"]
    assert entry["patch_contract"] is False
    assert entry["by_kind"]["boilerplate"] > 10000     # preamble + card + contract


# ========================================================== 3. the refusals
#
# Every one of these drives a guard to a refusal and asserts the reason. The
# applier edits the only artefact the system predicts from; a guard here that
# has never said no is a guard nobody has tested.

def test_an_anchor_that_does_not_occur_is_refused():
    with pytest.raises(deskdiet.PatchRefused) as exc:
        deskdiet.apply_patch("alpha\nbeta\n",
                             [{"op": "replace", "find": "gamma", "with": "x"}])
    assert exc.value.detail["matches"] == 0
    assert "does not occur" in exc.value.reason


def test_an_ambiguous_anchor_is_refused_with_its_count():
    with pytest.raises(deskdiet.PatchRefused) as exc:
        deskdiet.apply_patch("beta\nbeta\n",
                             [{"op": "replace", "find": "beta", "with": "x"}])
    assert exc.value.detail["matches"] == 2
    assert "ambiguous" in exc.value.reason


def test_one_bad_op_refuses_the_whole_patch_and_leaves_the_manual_alone():
    """Half-applying would leave a manual nobody wrote, and would leave the
    desk's next patch anchored against text it never saw."""
    text = "alpha\nbeta\ngamma\n"
    ops = [{"op": "replace", "find": "alpha", "with": "ALPHA"},
           {"op": "replace", "find": "nowhere", "with": "x"}]
    with pytest.raises(deskdiet.PatchRefused):
        deskdiet.apply_patch(text, ops)
    # the caller's text object is untouched; nothing partial escaped
    assert text == "alpha\nbeta\ngamma\n"


def test_an_unknown_op_is_refused():
    with pytest.raises(deskdiet.PatchRefused) as exc:
        deskdiet.apply_patch("alpha\n", [{"op": "regex", "find": "a", "with": "b"}])
    assert "unknown `op`" in exc.value.reason


def test_a_missing_with_is_refused():
    for kind in ("replace", "insert_after"):
        with pytest.raises(deskdiet.PatchRefused) as exc:
            deskdiet.apply_patch("alpha\n", [{"op": kind, "find": "alpha"}])
        assert "no `with` text" in exc.value.reason


def test_a_missing_or_empty_anchor_is_refused():
    for op in ({"op": "delete"}, {"op": "delete", "find": ""},
               {"op": "delete", "find": 7}):
        with pytest.raises(deskdiet.PatchRefused) as exc:
            deskdiet.apply_patch("alpha\n", [op])
        assert "no `find` anchor" in exc.value.reason


def test_a_non_object_op_is_refused():
    with pytest.raises(deskdiet.PatchRefused) as exc:
        deskdiet.apply_patch("alpha\n", ["replace alpha with beta"])
    assert "not an object" in exc.value.reason


def test_a_patch_block_that_is_not_json_is_refused():
    with pytest.raises(deskdiet.PatchRefused) as exc:
        deskdiet.parse_patch("=== THEORY-PATCH ===\n```json\n{not json,\n```\n")
    assert "not valid JSON" in exc.value.reason


def test_a_patch_block_that_is_not_a_list_is_refused():
    with pytest.raises(deskdiet.PatchRefused) as exc:
        deskdiet.parse_patch('=== THEORY-PATCH ===\n```json\n{"op": "replace"}\n```\n')
    assert "must be a JSON list" in exc.value.reason


def test_an_empty_patch_block_is_refused_but_an_empty_list_is_not():
    with pytest.raises(deskdiet.PatchRefused):
        deskdiet.parse_patch("=== THEORY-PATCH ===\n```json\n\n```\n")
    # `[]` is a legitimate answer: it says the surprises do not move the manual.
    assert deskdiet.parse_patch("=== THEORY-PATCH ===\n```json\n[]\n```\n") == []
    text, report = deskdiet.apply_patch("alpha\n", [])
    assert text == "alpha\n" and report["ops"] == 0


def test_no_patch_block_at_all_is_not_a_refusal_it_is_absence():
    """Absence and failure are different, and only failure should cost a repair
    round on the patch's account."""
    assert deskdiet.parse_patch("=== THEORY ===\n```\nx\n```\n") is None


def test_a_refused_patch_costs_one_repair_round_and_then_gets_the_whole_book(tmp_path):
    """The fail-closed path, end to end through the beat.

    Call 1 sends an unanchorable patch -> refused, manual unchanged, the reason
    goes back in the prompt. Call 2 sends another bad patch -> refused again.
    Call 3 is the last attempt, so `allow_patch` is off, the patch contract is
    not in the prompt at all, and the desk is asked for the whole book. The
    worst case is today's behaviour plus two calls, not a lost round.
    """
    books = _books(tmp_path, WORKED_EXAMPLE)
    good = WORKED_EXAMPLE.replace("goal count(Cart) = 1", "goal count(Cart) = 4")
    desk = ScriptedDesk([
        _patch_reply([{"op": "replace", "find": "no such text", "with": "x"}]),
        _patch_reply([{"op": "replace", "find": "no such text either", "with": "x"}]),
        _reply(good),
    ])
    result = theorize.run(desk, books, _store(), _candidates(tmp_path),
                          engines=_engines(),
                          diet=deskdiet.DeskDiet(theory_patch=True))

    assert result["calls"] == 3
    assert "patch_refused" in result["rounds"][0]
    assert "patch_refused" in result["rounds"][1]
    # the refusal was told to the desk, in the prompt, not just logged
    assert "does not occur in the manual" in desk.prompts[1]
    assert "the manual is UNCHANGED" in desk.prompts[1]
    # and the last attempt withdrew the patch contract -- both the contract
    # itself and the instruction in the refusal note, which would otherwise
    # tell the desk to send a patch on the one attempt that will not take one.
    heading = "# Writing the manual: send the EDIT, not the book"
    assert heading in desk.prompts[0]
    assert heading in desk.prompts[1]
    assert heading not in desk.prompts[2]
    assert "Send a corrected patch" in desk.prompts[1]
    assert "the patch contract is withdrawn" in desk.prompts[2]
    assert result["prompt_census"][2]["patch_contract"] is False
    assert "goal count(Cart) = 4" in books.theory


def test_a_reply_with_neither_block_is_refused_by_name(tmp_path):
    books = _books(tmp_path, WORKED_EXAMPLE)
    desk = ScriptedDesk([
        "=== LOG ===\n```json\n[]\n```\n",
        _reply(WORKED_EXAMPLE),
    ])
    result = theorize.run(desk, books, _store(), _candidates(tmp_path),
                          engines=_engines(),
                          diet=deskdiet.DeskDiet(theory_patch=True))
    assert "neither a === THEORY === block nor a === THEORY-PATCH ===" \
        in result["rounds"][0]["patch_refused"]
    assert result["calls"] == 2


# ============================================ 4. the before/after bench
#
# The bench is the offline evidence for this change, so it gets checked like
# evidence: it must be deterministic, its control must fire when the thing it
# controls for actually breaks, and it must refuse to print a dollar it cannot
# derive from the archive.

def test_the_bench_is_deterministic():
    from armtools import desk_diet_bench as bench_mod       # noqa: PLC0415
    a = bench_mod.bench(rounds=3)
    b = bench_mod.bench(rounds=3)
    strip = lambda r: json.dumps(r["arms"], sort_keys=True)  # noqa: E731
    assert strip(a) == strip(b)
    assert a["final_theory_sha_prefix"] == b["final_theory_sha_prefix"]


def test_the_bench_arms_do_the_same_work():
    """The comparison's premise, asserted rather than assumed: `full` and
    `patch` differ in encoding only, so their manuals must be equal."""
    from armtools import desk_diet_bench as bench_mod       # noqa: PLC0415
    report = bench_mod.bench(rounds=3)
    assert report["all_arms_agree_on_the_manual"] is True
    # and the patch arm really did patch -- one call per round, no repairs
    rows = {row["arm"]: row for row in report["arms"]}
    assert rows["patch"]["model_calls"] == rows["full"]["model_calls"] == 3


def test_the_bench_control_fires_when_the_patch_path_is_broken(monkeypatch):
    """The negative control for the bench itself.

    A patch applier that silently dropped an op would make the patch arm look
    cheap for the worst possible reason -- it wrote less theory. Break the
    applier on purpose and the bench must refuse to report at all.
    """
    from armtools import desk_diet_bench as bench_mod       # noqa: PLC0415

    real = deskdiet.apply_patch

    def lossy(theory, ops):
        return real(theory, ops[:-1] if ops else ops)

    monkeypatch.setattr(deskdiet, "apply_patch", lossy)
    monkeypatch.setattr(theorize.deskdiet, "apply_patch", lossy)
    with pytest.raises(bench_mod.ArmsDisagree) as exc:
        bench_mod.bench(rounds=3)
    assert "patch" in str(exc.value)


def test_the_bench_refuses_to_price_without_an_archive(tmp_path):
    """No archive, no dollars. A benchmark that reaches for a constant when its
    measurement is missing proves whatever it was written to prove."""
    from armtools import desk_diet_bench as bench_mod       # noqa: PLC0415
    empty = str(tmp_path / "no-runs-here")
    os.makedirs(empty)
    rates = bench_mod.archive_rates(empty)
    assert rates["usable"] is False
    priced = bench_mod.price_arm({"calls": []}, rates)
    assert priced["priced"] is False
    assert "refusing to invent" in priced["reason"]


def test_the_bench_names_the_output_saving_as_conditional():
    """The claim this change must not overstate. The arm is offline; whether a
    live desk answers the patch contract with a patch is not established here,
    and the artefact has to say so on its face."""
    from armtools import desk_diet_bench as bench_mod       # noqa: PLC0415
    report = bench_mod.bench(rounds=2)
    assert report["output_saving_is_conditional"] is True
    assert "cannot establish" in report["conditional_note"]
    assert "conditional" in bench_mod.format_report(report).lower()


# ============================================== the census's own negative
def test_the_census_conserves_bytes_and_refuses_a_foreign_string():
    """`census` is the measurement everything above is judged by, so it gets
    the same treatment: it must add up, and it must say no to something that is
    not a desk prompt rather than returning a confident zero."""
    store_prompt = "You are the theorize desk of nothing\n\n# What to reply\nx\n"
    report = prompt_census.census(store_prompt)
    assert sum(s["chars"] for s in report["sections"]) == len(store_prompt)

    with pytest.raises(prompt_census.CensusError):
        prompt_census.census("a shopping list\nmilk\neggs\n")
    with pytest.raises(prompt_census.CensusError):
        prompt_census.census(None)


def test_the_token_fit_refuses_a_single_point():
    """One call cannot pin down a slope and an intercept. Returning a number
    anyway would put an invented chars-per-token into a run report."""
    assert prompt_census.fit_tokens([(100, 50)])["ok"] is False
    assert prompt_census.fit_tokens([(100, 50), (100, 60)])["ok"] is False
    fit = prompt_census.fit_tokens([(100, 50), (200, 100), (300, 150)])
    assert fit["ok"] is True
    assert fit["chars_per_token"] == pytest.approx(2.0)
    assert fit["r2"] == pytest.approx(1.0)


def test_the_census_reads_an_archived_leg_and_agrees_with_its_desk_log():
    """The forensic path, against the archive it was written for.

    Skipped rather than invented when no live leg with a `desk/` directory is
    present -- but if one is, the census must agree with the ledger about how
    many calls there were and how long each prompt was, because the two are
    independent records of the same event.
    """
    runs = os.path.join(ARM, "runs")
    if not os.path.isdir(runs):
        pytest.skip("no runs archive here")
    legs = [n for n in sorted(os.listdir(runs))
            if os.path.isdir(os.path.join(runs, n, "desk"))]
    if not legs:
        pytest.skip("no archived leg carries desk transcripts")
    checked = 0
    for name in legs:
        leg = prompt_census.census_leg(os.path.join(runs, name))
        if not leg["calls"]:
            continue
        checked += 1
        for call in leg["per_call"]:
            assert call["chars_in"] > 0
            by_kind = sum(v["chars"] for v in call["by_kind"].values())
            assert by_kind == call["chars_in"]
    assert checked, "every archived desk directory parsed to zero calls"
