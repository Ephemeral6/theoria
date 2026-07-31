"""The campaign-freeze gate, read on the arm's own live paths.

`arc-recon/canary.py` detects same-ID behaviour drift and writes
`arc-recon/data/campaign_freeze.json` when it finds any (Theoria.md Phase 1,
接入核查: 漂移 = incident 并冻结战役). Until this module, that circuit was
detection-only from the arm's point of view: the file could say FROZEN in
capital letters and `harness/run.py` would start a live run anyway, because
nothing on the spending path ever opened it. This is the reader.

Three answers, and what each one does to a live launch:

* **frozen** -- hard stop, naming the incident, the games and the reason. A
  frozen campaign file means the environment the arm is about to spend money
  measuring has been observed behaving differently under an unchanged
  `game_id`, so every action spent before an owner adjudicates the drift is an
  action spent measuring an unknown world.
* **clear** (`frozen: false`) -- proceed. `checked_utc` says when the canary
  last vouched for the environment.
* **missing** -- proceed, with a loud warning. Missing is NOT treated as
  frozen, for a reason worth writing down: the file is created once
  (`canary.py init-freeze`, 2026-07-31) and tracked, so on any checkout from
  after that date absence means someone deleted it or the checkout predates
  the instrument -- and the instrument is new enough that a hard stop on
  absence would brick every stale worktree and teach people to work around
  the gate rather than read it. The warning names the expected path so the
  deletion cannot pass silently. If the freeze discipline ever hardens,
  flipping `MISSING_IS_FATAL` is the one-line change, and the tests cover
  both readings.

Mock and offline paths never consult this gate: the freeze is about the real
ARC environment, and a rehearsal against `proxy/mock` cannot be invalidated by
drift in a world it never touches.

Read-only by design. The arm never writes the freeze file -- writing is
`arc-recon/canary.py`'s job (drift freezes, green sweeps refresh, owners
clear), and arc-recon is shared ground this territory does not edit.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(HERE)
REPO = os.path.dirname(ARM)

#: The one authority. `canary.py` owns the writing side; this constant is the
#: reading side's copy of the address, and the arm test that matters most
#: (`test_freeze_preflight.py::test_the_path_is_the_one_canary_writes`) pins
#: the two together so they cannot drift apart silently.
FREEZE_PATH = os.path.join(REPO, "arc-recon", "data", "campaign_freeze.json")

#: Missing = warn-and-proceed today (see the module docstring for why). This
#: is a named constant rather than an inline default so that hardening it is
#: a visible one-line decision, not a hunt.
MISSING_IS_FATAL = False


class CampaignFrozen(RuntimeError):
    """The freeze file says frozen; a live run must not start."""


def freeze_state(path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """The file's content, or None when it does not exist.

    An unreadable file raises rather than returning None: a freeze file that
    cannot be parsed is not the same thing as one that was never written, and
    collapsing the two would let a corrupted (or truncated) freeze pass as
    'instrument not yet created'.
    """
    path = path or FREEZE_PATH
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    if not isinstance(doc, dict):
        raise CampaignFrozen(
            "%s is valid JSON but not an object; a freeze gate whose verdict "
            "cannot be read has not said proceed" % path)
    return doc


def assert_unfrozen(path: Optional[str] = None,
                    warn=None) -> Dict[str, Any]:
    """The preflight. Raises `CampaignFrozen` on frozen; returns the reading.

    Fail-closed on everything except a genuinely absent file: a file that
    exists but cannot be parsed, or parses to a non-object, refuses -- the
    same rule `campaign.assert_launch_cleared` applies to the §9 gate, and
    for the same reason (a gate that cannot be read has not said yes).
    """
    warn = warn or (lambda msg: print(msg, file=sys.stderr))
    path = path or FREEZE_PATH
    try:
        state = freeze_state(path)
    except CampaignFrozen:
        raise
    except Exception as exc:                           # noqa: BLE001
        raise CampaignFrozen(
            "%s exists but could not be read (%s: %s). A freeze file that "
            "cannot be read has not said proceed; fix or adjudicate it first."
            % (path, type(exc).__name__, exc))

    if state is None:
        message = (
            "WARNING: %s is missing. The campaign-freeze file is tracked and "
            "was created 2026-07-31 (canary.py init-freeze), so on a current "
            "checkout absence means it was deleted or this checkout predates "
            "the instrument. Proceeding -- missing is not frozen -- but the "
            "canary has not vouched for the environment this run is about to "
            "spend against. Run `cd arc-recon && python canary.py "
            "init-freeze` (offline) or a sweep with --write-freeze." % path)
        if MISSING_IS_FATAL:
            raise CampaignFrozen(message)
        warn(message)
        return {"state": "missing", "path": path}

    if state.get("frozen"):
        raise CampaignFrozen(
            "campaigns are FROZEN (%s): %s -- incident %s, games %s, since "
            "%s. The canary observed same-ID behaviour drift; every action "
            "spent before an owner adjudicates it measures an unknown "
            "environment. Clearing is an owner decision recorded as an "
            "incident (see the file's how_to_clear), never a launch-time "
            "override."
            % (path, state.get("reason", "(no reason recorded)"),
               state.get("incident"), ", ".join(state.get("games") or []),
               state.get("since")))

    return {"state": "clear", "path": path,
            "checked_utc": state.get("checked_utc")}
