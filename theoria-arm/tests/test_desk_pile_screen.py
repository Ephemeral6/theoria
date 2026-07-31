"""The pile cut, enforced on the **model path**, by the desk itself.

`Theoria.md:353` is a hard rule -- 游戏 ID 永不进模型上下文, 全程匿名化 -- and
until this file existed the arm enforced it with one mechanism:
`inner/loop.py:_forbidden_substrings` builds a list and hands it to
`ModelDesk(forbid_in_prompt=...)`, which tests each entry with a bare `in`.

That is the right first move and it is not enough, for two reasons that pull in
opposite directions:

* **It is only as good as the caller.** A `ModelDesk` constructed anywhere else
  -- a smoke script, a new beat, a future campaign driver, a test -- gets the
  default empty tuple and screens *nothing*. The rule lived in the loop, so
  every other builder of a desk silently opted out of it.
* **A bare `in` over twenty-five stems is unusable.** `sk48` fires inside
  `task48`, `ar25` inside `similar25`. A guard that refuses ordinary English is
  a guard somebody switches off, and then the twenty-one that matter are
  unscreened too.

So the rule now lives in the desk, sourced from `arc-recon/data/piles.json` at
construction and never hard-coded, and scanned with the proxy's own
`SealedPileGuard.game_ids_in_text` -- token-bounded, percent-decoding,
NFKC-normalising, zero-width-stripping, one level of base64. The loop's
substring list stays behind it as a blunter belt that catches an id welded into
a longer token, which a token-bounded scan deliberately does not.

The three outcomes are checked separately below, and so are both false-positive
controls, because a screen that over-refuses and a screen that under-refuses
fail in ways that look nothing alike from the outside.

No game content is read anywhere here. The identifiers come out of the cut,
which is the split itself and not a description of any game, and no call ever
reaches the `claude -p` seam -- every test asserts the seam counter is empty.
The loop-level half of this rule (that the refusal ends the run rather than
being filed as a desk failure) is pinned in `test_arm.py`; the loop's own
substring list is pinned in `test_desk_sealing.py`.
"""

import json
import os
import sys
from typing import Any, Dict, List

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
if ARM not in sys.path:
    sys.path.insert(0, ARM)

import _bootstrap                                          # noqa: E402,F401

from harness.spend import NoSpendBinding                   # noqa: E402
from proxy.paths import PILES                              # noqa: E402


def _cut() -> Dict[str, Any]:
    with open(PILES, encoding="utf-8") as fh:
        return json.load(fh)


def dev_id() -> str:
    return sorted(_cut()["dev_pile"])[0]


class _LedgerRun:
    """A `RunLedger` stand-in that only remembers incidents."""

    run_id = "r-pile-screen"
    spend_binding = None

    def __init__(self) -> None:
        self.incidents: List[Dict[str, Any]] = []

    def incident(self, kind: str, detail: Any, **fields: Any) -> None:
        self.incidents.append(dict(fields, kind=kind, detail=detail))

    def model_call(self, **fields):                    # pragma: no cover
        raise AssertionError("no call should be recorded by this file")


def _screening_desk(run=None):
    """A desk whose only seam that costs money is replaced by a counter."""
    from harness.modelcall import ModelDesk            # noqa: PLC0415

    desk = ModelDesk(run if run is not None else _LedgerRun(),
                     model="mock-desk-1", cost_ceiling_usd=20.0)
    calls: List[str] = []

    def _invoke(prompt, model):
        calls.append(prompt)
        return {"result": "ok", "total_cost_usd": 0.0,
                "usage": {"input_tokens": 1, "output_tokens": 1}}, 1, ""

    desk._invoke = _invoke
    desk.invoked = calls
    return desk


@pytest.mark.parametrize("sealed_id", sorted(_cut()["sealed_pile"]))
def test_every_sealed_id_in_the_cut_is_refused_in_a_prompt(sealed_id):
    """All twenty-one, by identifier only.

    Parametrised over the cut rather than over a sample: the sealed pile is a
    fixed enumeration and a screen that covered twenty of them would be a
    screen with one hole in it. The prompt is shaped like the channel that
    actually carries an id by accident -- an engine traceback with an absolute
    path in it -- rather than like a hand-written mention, because nobody was
    ever going to type one.
    """
    from harness.modelcall import SealedPileBreach      # noqa: PLC0415

    desk = _screening_desk()
    prompt = ("the manual failed to compile:\n  OSError: no space left on "
              "device: '/tmp/runs/20260730T0100Z-%s/books/manual.lean'\n"
              % sealed_id)
    with pytest.raises(SealedPileBreach) as exc:
        desk.call(prompt, beat="theorize")
    assert sealed_id in str(exc.value)
    assert desk.invoked == [], "the prompt reached the subprocess seam"
    assert desk.calls == 0 and desk.cli_cost_usd == 0.0


def test_a_bare_sealed_stem_is_refused_and_an_embedded_one_is_not():
    """The false-positive control, which is what makes the screen usable.

    A bare stem is a game id -- INC-005 recorded that the live API answers
    short ids with a fake 200 -- so it must be refused. The same four
    characters inside a longer token are not a game id, and a desk that refused
    ordinary English is a desk somebody switches off. The proxy's scanner is
    token-bounded, which is the whole reason it is reused here instead of a
    `for stem in sealed: if stem in prompt`.
    """
    from harness.modelcall import SealedPileBreach      # noqa: PLC0415
    from proxy.guard import stem                        # noqa: PLC0415

    sealed_stem = stem(sorted(_cut()["sealed_pile"])[0])

    desk = _screening_desk()
    with pytest.raises(SealedPileBreach):
        desk.call("the run under %s failed to certify" % sealed_stem,
                  beat="theorize")
    assert desk.invoked == []

    # ... and the control. Same characters, welded into a longer token.
    #
    # "Allowed" is asserted as `NoSpendBinding` rather than as a completed
    # call: `_LedgerRun` deliberately has no claim on the shared pool, so any
    # prompt that gets past the screen dies at the gate instead of at the
    # screen. That is the assertion -- the failure has moved past the check
    # under test -- and it also means a mistake in this file cannot become a
    # charge.
    desk = _screening_desk()
    with pytest.raises(NoSpendBinding):
        desk.call("the run under z%szz failed to certify" % sealed_stem,
                  beat="probe_design")
    assert desk.invoked == [], "the seam runs after the gate, not before it"


def test_a_refusal_is_recorded_before_it_is_raised():
    """An incident that exists only in a traceback exists in a terminal
    somebody has already closed."""
    from harness.modelcall import SealedPileBreach      # noqa: PLC0415

    run = _LedgerRun()
    desk = _screening_desk(run)
    sealed_id = sorted(_cut()["sealed_pile"])[0]
    with pytest.raises(SealedPileBreach):
        desk.call("evidence from %s" % sealed_id, beat="theorize")

    assert len(run.incidents) == 1, run.incidents
    entry = run.incidents[0]
    assert entry["kind"] == "sealed_pile_in_prompt"
    assert entry["rule"] == "sealed_pile_in_prompt"
    assert sealed_id in entry["game_ids"], entry["game_ids"]
    assert entry["cut_sha256"]


def test_a_development_id_is_refused_under_the_lesser_class():
    """The hard rule is about every game id, not only the sealed ones -- but
    the two are different incidents and must be told apart in a traceback.

    A dev-pile leak makes one run inadmissible and is undone by repeating it
    with a game-free slug. A sealed leak teaches a model a game the exam has
    not run yet, and no repetition un-teaches that.
    """
    from harness.modelcall import AnonymityBreach, SealedPileBreach  # noqa: PLC0415

    desk = _screening_desk()
    with pytest.raises(AnonymityBreach) as exc:
        desk.call("frames from %s look wrong" % dev_id(), beat="theorize")
    assert not isinstance(exc.value, SealedPileBreach)
    assert desk.invoked == []


def test_an_id_shaped_string_that_is_no_game_is_allowed_through():
    """The other false-positive control, and the reason `unknown` is allowed.

    `<two-to-six alphanumerics>-<eight hex>` is a shape ordinary text hits by
    accident: a branch name, a run slug, half a digest. The sealed pile is a
    fixed enumeration, so a shape that is not in the register is not a sealed
    game -- refusing it would buy nothing and would make the desk unusable.
    The proxy's request path can afford `unknown_policy = deny` because a
    request names one game deliberately; a 20,000-character prompt is not that.
    """
    desk = _screening_desk()
    with pytest.raises(NoSpendBinding):
        desk.call("see runs/build-deadbeef and commit abc-0123abcd for context",
                  beat="theorize")


def test_the_screen_is_the_desks_own_and_not_the_callers():
    """A desk built with no `forbid_in_prompt` at all still refuses.

    This is the difference between the fix and the one before it. The loop's
    substring list is passed *in*; anything that builds a `ModelDesk` without
    it -- a smoke script, a new beat, a test -- used to get no screening
    whatever. The cut is now loaded by the desk itself.
    """
    from harness.modelcall import ModelDesk, SealedPileBreach  # noqa: PLC0415

    desk = ModelDesk(_LedgerRun(), model="mock-desk-1")
    assert desk.forbid_in_prompt == ()
    with pytest.raises(SealedPileBreach):
        desk.call("about %s" % sorted(_cut()["sealed_pile"])[0],
                  beat="theorize")


def test_the_desk_refuses_to_exist_when_the_cut_cannot_be_read():
    """Fail-closed: a desk that cannot enumerate the sealed pile cannot promise
    it kept the pile out of a prompt, so it does not get built."""
    from proxy.guard import PilesIntegrityError, SealedPileGuard  # noqa: PLC0415
    from harness.modelcall import ModelDesk             # noqa: PLC0415

    with pytest.raises((OSError, PilesIntegrityError, ValueError)):
        ModelDesk(_LedgerRun(), model="mock-desk-1",
                  pile_guard=SealedPileGuard(piles_path=os.path.join(
                      os.path.dirname(PILES), "no-such-cut.json")))
