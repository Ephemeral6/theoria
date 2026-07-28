"""`raw_trace.jsonl` is the downstream-zero-change contract with cold-start-a0.

The whole point of copying the format instead of improving on it is that
`cold-start-a0` and its `prime` spike can consume a worldgen world with no edit
at all.  That promise is a byte-level one, and every clause below is a way a
reader has actually been broken by a generator:

* **keys are exactly `{t, frame, action, win}`** — an extra key is not benign,
  because the downstream reader treats a row as a record and a schema check
  upstream is the only place a stray field gets caught (`trace.append_probe`
  writes a fifth key, `probe`, and it must not appear in a shipped trace);
* **compact separators, sorted keys, no CR, trailing newline** — the file is
  compared byte-for-byte by the build's determinism gate, and a `core.autocrlf`
  checkout that inserted CRs would silently defeat it;
* **the last row's `action` is present and null** — the terminal frame has no
  successor, and a reader that pairs row `t` with row `t+1` needs the sentinel
  rather than a short row or a missing key.

These run against the artefacts committed under `worldgen/out/worlds/`, not
against a freshly generated trace, because the contract is about what is
*shipped*.
"""

import json
import os

import pytest

from worldgen.tests import support

ALL = support.WORLD_IDS
KEYS = {"t", "frame", "action", "win"}


def _raw(world_id: str) -> bytes:
    path = support.trace_path(world_id)
    if not os.path.exists(path):
        pytest.skip("no shipped trace at %s — run `python -m worldgen.build`" % path)
    with open(path, "rb") as handle:
        return handle.read()


@pytest.mark.parametrize("world_id", ALL)
def test_trace_is_lf_terminated_and_free_of_cr(world_id):
    raw = _raw(world_id)
    assert raw, "%s: shipped trace is empty" % world_id
    assert b"\r" not in raw, "%s: shipped trace contains CR" % world_id
    assert raw.endswith(b"\n"), "%s: shipped trace has no trailing newline" % world_id


@pytest.mark.parametrize("world_id", ALL)
def test_trace_rows_round_trip_byte_for_byte(world_id):
    text = _raw(world_id).decode("utf-8")
    lines = text.split("\n")[:-1]
    rebuilt = []
    for i, line in enumerate(lines):
        row = json.loads(line)
        assert set(row) == KEYS, "%s row %d: keys are %r" % (world_id, i, sorted(row))
        rebuilt.append(json.dumps(row, sort_keys=True, separators=(",", ":")))
    assert "\n".join(rebuilt) + "\n" == text, (
        "%s: re-serialising the rows does not reproduce the file" % world_id)


@pytest.mark.parametrize("world_id", ALL)
def test_last_row_carries_a_null_action(world_id):
    lines = _raw(world_id).decode("utf-8").split("\n")[:-1]
    last = json.loads(lines[-1])
    assert "action" in last, "%s: terminal row has no `action` key" % world_id
    assert last["action"] is None, (
        "%s: terminal row's action is %r, expected null" % (world_id, last["action"]))
    for i, line in enumerate(lines[:-1]):
        assert json.loads(line)["action"] is not None, (
            "%s row %d: a non-terminal row carries a null action" % (world_id, i))
