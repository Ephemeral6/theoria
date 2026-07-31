"""The two things master's gate was missing, ported out of the P-12 branch.

That branch rebuilt the gate's clocks (sittings, G6c) and the rebuild was not
adopted -- master's adjudicated-stop design is the one this track keeps, see
DECISIONS.md D-022. Two of its findings were not about the design at all, and
would have been thrown away with it:

  * `elapsed_seconds` read the machine's clock with no way to inject one, so
    G6a could be deleted outright and the suite would stay green. The branch
    measured exactly that.
  * `write_gate` opened the standing verdict in text mode. On Windows that
    writes CRLF, `.gitattributes` normalises it back to LF on the way into git,
    and the file on disk stops being byte-equal to the file in the tree with no
    error anywhere. Determinism is a requirement in this repo, not a nicety.

Both are pinned here so that a future edit to the gate has to take them down on
purpose.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import run_campaign as rc                              # noqa: E402


def _cell(started, **kw):
    base = {"game_id": "ar25-0c556536", "model": rc.CAMPAIGN_TIER,
            "campaign": rc.CAMPAIGN_NAME, "run_id": "r-" + started,
            "started": started, "outcome": "budget_exhausted",
            "actions_ok": 30, "actions_failed": 0, "cost_usd": 0.1,
            "http_calls_gameplay": 90, "wall_seconds": 600.0,
            "levels_completed": 0, "repeat": 1}
    base.update(kw)
    return base


def _epoch(stamp):
    return time.mktime(time.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone


# ------------------------------------------------------------- injectable clock
def test_elapsed_seconds_takes_an_injected_clock():
    cells = [_cell("2026-07-28T00:00:00Z"), _cell("2026-07-28T01:00:00Z")]
    now = _epoch("2026-07-28T03:00:00Z")
    assert rc.elapsed_seconds(cells, now=now) == 3 * 3600


def test_elapsed_seconds_still_defaults_to_the_real_clock():
    """The parameter is an addition; omitting it must not change the answer."""
    cells = [_cell("2026-07-28T00:00:00Z")]
    injected = rc.elapsed_seconds(cells, now=time.time())
    real = rc.elapsed_seconds(cells)
    assert abs(injected - real) < 5


def test_elapsed_seconds_is_utc_not_local():
    """`started` is written with a Z. Reading it through the local timezone
    would shift the clock by the offset of whatever machine ran the test."""
    cells = [_cell("2026-07-28T00:00:00Z")]
    assert rc.elapsed_seconds(cells, now=_epoch("2026-07-28T00:00:00Z")) == 0


def test_g6a_can_be_made_to_fire():
    """The clause was previously unreachable from a test, which is the same as
    saying nothing checked it was there."""
    cells = [_cell("2026-07-28T00:00:00Z")]
    over = _epoch("2026-07-28T00:00:00Z") + rc.ELAPSED_SECONDS_CAP + 60
    gate = rc.evaluate_gate(cells, now=over)
    assert any(t.startswith("G6a") for t in gate["tripped"]), gate["tripped"]
    assert gate["state"] == "red"


def test_g6a_does_not_fire_below_the_cap():
    cells = [_cell("2026-07-28T00:00:00Z")]
    under = _epoch("2026-07-28T00:00:00Z") + rc.ELAPSED_SECONDS_CAP - 60
    gate = rc.evaluate_gate(cells, now=under)
    assert not any(t.startswith("G6a") for t in gate["tripped"]), gate["tripped"]


def test_deleting_the_g6a_clause_would_be_caught():
    """A guard on the guard: the pair above only proves the clause exists if the
    two calls actually disagree."""
    cells = [_cell("2026-07-28T00:00:00Z")]
    zero = _epoch("2026-07-28T00:00:00Z")
    fired = rc.evaluate_gate(cells, now=zero + rc.ELAPSED_SECONDS_CAP + 60)
    quiet = rc.evaluate_gate(cells, now=zero + rc.ELAPSED_SECONDS_CAP - 60)
    assert fired["tripped"] != quiet["tripped"]


# ------------------------------------------------------------------- LF on disk
def test_write_gate_writes_lf_even_on_windows(tmp_path, monkeypatch):
    monkeypatch.setattr(rc, "OUT_DIR", str(tmp_path))
    monkeypatch.setattr(rc, "GATE_PATH", str(tmp_path / "campaign_gate.json"))
    monkeypatch.setattr(rc.ledger, "probe", lambda *a, **k: None)
    rc.write_gate(rc.evaluate_gate([_cell("2026-07-28T00:00:00Z")]))
    raw = (tmp_path / "campaign_gate.json").read_bytes()
    assert b"\r\n" not in raw
    assert b"\n" in raw
    assert json.loads(raw.decode("utf-8"))["totals"]["cells"] == 1
