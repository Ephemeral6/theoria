"""The model path's half of the sealing guarantee, which nothing was checking.

`test_bypass_negative.py` pins the **environment** path: a sealed id sent
through `Run` -> `EnvProxy` -> upstream is refused before a socket opens, and
the refusal is recorded. That test is real and it is green. It is also only
half the arm.

The **model** path does not traverse any of it. `harness/modelcall.py` starts a
`claude -p` subprocess and talks to a different upstream entirely; no
`SealedPileGuard` sits anywhere between the arm and the desk. A11 wrote the
consequence down as two of its three findings and neither had a test:

* **F2** -- the desk's `forbid_in_prompt` list held the id being played and
  nothing else, so a sealed id in a prompt was not merely unrefused, it was
  unexamined. `Theoria.md:353`'s fourth overfitting channel is model priors,
  sealed by the hard rule 硬规:游戏 ID 永不进模型上下文; naming a sealed game to
  a pretrained model is the same contamination `CLAUDE.md` forbids by reading.
* **F3** -- the desk subprocess inherited `ANTHROPIC_BASE_URL` from whatever
  shell launched the arm, under a comment saying it must not. One exported
  variable redirects every desk call to an endpoint this ledger never sees,
  and **nothing goes red**: the cost still comes back inside the CLI's own
  envelope, so the run still prices out and still looks complete.

Both tests below carry their positive control in the same function. A scrub
asserted only by absence passes just as well on an empty environment, and a
forbid-list asserted only by rejection passes just as well when it rejects
everything -- either way the assertion would survive the fix being reverted,
which is the failure mode this file exists to avoid.
"""

import os
import subprocess

import pytest

import _bootstrap                                     # noqa: F401  (sys.path)

from harness.modelcall import (SCRUBBED_FROM_DESK_ENV, AnonymityBreach,
                               ModelDesk)
from inner.loop import _forbidden_substrings

from proxy.guard import SealedPileGuard, stem


DEV_GAME = "g50t-5849a774"

#: Written out here rather than imported, and that is the whole point.
#:
#: The first version of the test below iterated `SCRUBBED_FROM_DESK_ENV` -- and
#: so it shrank whenever the constant shrank. Verified, not assumed: cutting
#: the constant back to `("ARC_API_KEY",)` left this file's other three tests
#: red and **this one green**, because a loop over a one-element tuple checked
#: one element. A test that reads its expectation out of the code under test
#: asserts that the code equals itself.
#:
#: So the list is duplicated on purpose. If someone deliberately narrows the
#: scrub, this goes red and the narrowing has to be argued for here.
MUST_NOT_REACH_THE_DESK = ("ARC_API_KEY", "ANTHROPIC_BASE_URL",
                           "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY")


# -- F2: the sealed pile is on the forbid list -----------------------------

def test_every_sealed_id_and_stem_is_forbidden_in_a_prompt():
    """The list is derived from the cut, so widening the cut cannot outrun it."""
    guard = SealedPileGuard()
    forbidden = set(_forbidden_substrings(DEV_GAME))

    assert guard.sealed, "the cut declares no sealed games; the rest is vacuous"
    missing = sorted(g for g in guard.sealed if g not in forbidden)
    assert missing == [], "sealed ids absent from the forbid list: %s" % missing
    missing_stems = sorted(stem(g) for g in guard.sealed
                           if stem(g) not in forbidden)
    assert missing_stems == [], (
        "sealed stems absent from the forbid list: %s" % missing_stems)

    # The game being played is still on the list -- the old behaviour is kept,
    # not replaced.
    assert DEV_GAME in forbidden
    assert stem(DEV_GAME) in forbidden

    # Positive control. The other three development-pile games are NOT
    # forbidden: they are ours to name. Without this, a `_forbidden_substrings`
    # that returned every id in the register would pass everything above while
    # making every prompt unsendable.
    others = [g for g in guard.dev if stem(g) != stem(DEV_GAME)]
    assert others, "the dev pile has one game; the control below is vacuous"
    for other in others:
        assert other not in forbidden, (
            "%s is a development-pile game and must remain nameable" % other)


def test_a_sealed_stem_in_a_prompt_is_refused_before_the_subprocess(monkeypatch):
    """Refused where it costs nothing: before the gate, before the process."""
    started = []
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: started.append(a) or _unreachable())

    desk = ModelDesk(_FakeRun(), model="claude-opus-5",
                     forbid_in_prompt=_forbidden_substrings(DEV_GAME))

    sealed_id = sorted(SealedPileGuard().sealed)[0]
    carrier = (
        "the manual failed to compile:\n"
        "  OSError: [Errno 28] No space left on device: "
        "'/tmp/runs/20260730T0100Z-%s/books/manual.lean'\n" % stem(sealed_id))

    with pytest.raises(AnonymityBreach) as exc:
        desk.call(carrier, beat="theorize")
    assert stem(sealed_id) in str(exc.value)
    assert started == [], "the prompt reached a subprocess before being checked"
    assert desk.calls == 0 and desk.cli_cost_usd == 0.0

    # Positive control: the identical traceback shape carrying no forbidden id
    # gets past the anonymity check. It fails later -- there is no spend
    # binding on a `_FakeRun` -- and *that* is the point: the failure has moved
    # past the check under test, so the check is not simply refusing everything.
    with pytest.raises(Exception) as ok:
        desk.call(carrier.replace(stem(sealed_id), "zzzz"), beat="theorize")
    assert not isinstance(ok.value, AnonymityBreach)


# -- F3: the desk subprocess cannot be redirected by inheritance -----------

def test_the_desk_subprocess_inherits_no_redirect_and_no_game_credential(
        monkeypatch):
    """Asserted on the env actually handed to the process, not on the constant."""
    for var in MUST_NOT_REACH_THE_DESK:
        monkeypatch.setenv(var, "set-by-the-shell-that-launched-the-arm")
    monkeypatch.setenv("THEORIA_DESK_CONTROL", "must-survive")

    seen = {}

    def _capture(cmd, **kw):
        seen.update(kw.get("env") or {})
        raise subprocess.TimeoutExpired(cmd, 1)

    monkeypatch.setattr(subprocess, "run", _capture)

    desk = ModelDesk(_FakeRun(), model="claude-opus-5")
    with pytest.raises(Exception):
        desk._invoke("hello", "claude-opus-5")

    assert seen, "no environment was captured; the assertions below are vacuous"
    leaked = sorted(v for v in MUST_NOT_REACH_THE_DESK if v in seen)
    assert leaked == [], "the desk inherited %s" % leaked

    # Positive control, and it is the load-bearing half. `env=` is built from
    # `os.environ`, so an empty or wrongly-built dict would satisfy every
    # assertion above. This pins that the rest of the environment did travel:
    # the desk is being scrubbed, not starved.
    assert seen.get("THEORIA_DESK_CONTROL") == "must-survive"
    assert "PATH" in seen or "Path" in seen


def test_anthropic_base_url_is_named_by_the_scrub_list():
    """The one variable this repo has actually exported at the desk before.

    `harness/modelcall.py`'s module docstring records the live attempt:
    `ANTHROPIC_BASE_URL=<model proxy> claude -p ...`. It is not a hypothetical
    name, which is why it is pinned separately from the loop above.
    """
    assert "ANTHROPIC_BASE_URL" in SCRUBBED_FROM_DESK_ENV
    assert "ARC_API_KEY" in SCRUBBED_FROM_DESK_ENV


# -- fixtures --------------------------------------------------------------

def _unreachable():
    raise AssertionError("subprocess.run must not be reached")


class _FakeRun:
    """The narrowest thing `ModelDesk` needs: an id, and no spend binding.

    No binding is deliberate. `call()` raises rather than spending when it
    cannot find one, so every path through these tests that gets past the
    anonymity check dies before money, and a mistake in this file cannot
    become a charge.
    """

    run_id = "test-desk-sealing"
    dir = os.devnull
    spend_binding = None

    def model_call(self, *a, **k):                     # pragma: no cover
        raise AssertionError("no call should be recorded by this file")
