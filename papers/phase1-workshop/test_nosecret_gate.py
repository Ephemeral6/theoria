"""Negative control for verify_paper.py's check D.

Check D is the check standing between the ARC key and the Phase 4 release
manifest, which `CLAUDE.md` says publishes every tracked file. It was a no-op
everywhere that mattered: its secret list was built from `ROOT/.env`, `.env` is
gitignored, so in the worktree `monitor/ci_merge.py` checks out the list was
empty, the comparison loop iterated zero times, and the check returned True
saying "no .env present to check against (nothing to leak)". A file holding a
key-shaped credential passed `[PASS] D NOSECRET`, `PASS (6/6)`, exit 0 on any
fresh clone.

Every test here therefore runs with **no `.env` at all** unless it is the one
testing the exact-value scan. That is the configuration CI uses, and it is the
configuration in which the check used to assert nothing.

No test contains the real credential. The fixture below is a UUID built out of
the four development-pile game ids, which are public and in `CLAUDE.md`; it has
the key's *shape* and none of its bytes. Planting the real value in a test
fixture is the exact thing `CLAUDE.md` forbids -- and a leak detector whose own
suite leaks would be a poor advertisement.

Run:  python -m pytest papers/phase1-workshop/test_nosecret_gate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_paper as vp  # noqa: E402

#: Key-shaped, not the key. Digits lifted from the four public development-pile
#: game ids (ar25-0c556536, g50t-5849a774, sk48-d8078629, tn36-ef4dde99).
SHAPED = "0c556536-5849-4774-8629-ef4dde99a1b2"

#: Fixtures for the two mechanisms that do not depend on shape. Bound to names
#: and interpolated everywhere below, never spelled inline, because **check D
#: reads this file too**: written as literal `secret=...` lines they took the
#: check red on its own negative control, which is how the first run of this
#: suite failed. The alternative was a declared exemption for this filename, and
#: that would have been a hole -- an exemption from the name- and shape-based
#: scans is a place to hide a key from them. A negative control for a scanner
#: has to be assembled at runtime rather than written out.
ROTATED = "8Kd93jf" + "KAlq02mfhSKQ92mfhalq0"     # a key of some other shape
WEAK = "hunter2" + "hunter2hunter2"               # not the ARC key at all
EXACT = "aQ2mfhal" + "q0293mfhSK"                 # only the .env scan sees this


def run_d(tmp_path, monkeypatch, files: dict[str, str], env: str | None = None):
    """`check_nosecret()` over a synthetic published tree.

    `HERE` and `ROOT` are module globals resolved at import, so they are
    redirected rather than the real tree copied -- the same technique the
    delegator's suite uses, and it keeps every case in a `tmp_path`."""
    here = tmp_path / "paper"
    here.mkdir()
    for name, body in files.items():
        p = here / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    if env is not None:
        (tmp_path / ".env").write_text(env, encoding="utf-8")
    monkeypatch.setattr(vp, "HERE", here)
    monkeypatch.setattr(vp, "ROOT", tmp_path)
    return vp.check_nosecret()


# ------------------------------------------------- the regression this item is

def test_a_planted_key_is_caught_with_no_env_present(tmp_path, monkeypatch):
    """The item, in one test. Before this change: PASS, exit 0, on every fresh
    checkout. `.env` is deliberately absent -- that is CI's configuration."""
    ok, notes = run_d(tmp_path, monkeypatch, {"leak.md": f"ARC_API_KEY={SHAPED}"})
    assert not ok, "a planted ARC_API_KEY passed with no .env present: %s" % notes


def test_the_note_never_claims_nothing_to_leak(tmp_path, monkeypatch):
    """The old green said "no .env present to check against (nothing to leak)".
    A note asserting a check that did not run is the defect, not the wording:
    the sentence is what a reader audits, and it said the tree was clean when
    nothing had looked at it."""
    ok, notes = run_d(tmp_path, monkeypatch, {"clean.md": "no secrets here"})
    blob = "\n".join(notes)
    assert ok
    assert "nothing to leak" not in blob
    assert "SKIPPED" in blob, (
        "a green that does not say the exact-value scan was skipped: %s" % blob)
    assert "scanned" in blob


def test_the_green_note_says_how_many_files_it_read(tmp_path, monkeypatch):
    """A count is the difference between "scanned and found nothing" and
    "scanned nothing" -- the two the old note could not tell apart."""
    ok, notes = run_d(tmp_path, monkeypatch,
                      {"a.md": "x", "b.md": "y", "sub/c.md": "z"})
    assert ok and "3 published file(s) scanned" in "\n".join(notes)


# ------------------------------------------------- what must be caught

@pytest.mark.parametrize("body,why", [
    (f"ARC_API_KEY={SHAPED}", "the documented variable name"),
    (f"api_key: {SHAPED}", "yaml-style"),
    (f'"apikey": "{SHAPED}"', "json-style"),
    (f"Authorization: Bearer {SHAPED}", "an http header"),
    (f"X-API-Key: {SHAPED}", "the header arc-recon actually sends"),
    (f"curl -H 'x-api-key: {SHAPED}' https://example.invalid/", "a pasted curl"),
    (f"token: {SHAPED}", "bare 'token' plus key shape"),
    (f"access_token={SHAPED}", "a compound that only means a credential"),
    (f"secret={ROTATED}", "a rotated key of a different shape"),
    (f"password: {WEAK}", "not the ARC key at all"),
])
def test_these_are_caught(tmp_path, monkeypatch, body, why):
    ok, notes = run_d(tmp_path, monkeypatch, {"leak.md": body})
    assert not ok, "%s was not caught: %s" % (why, notes)


def test_a_published_dotenv_is_itself_the_leak(tmp_path, monkeypatch):
    """Whatever is inside it. The filename is the finding."""
    ok, _ = run_d(tmp_path, monkeypatch, {".env": "ARC_API_KEY="})
    assert not ok


def test_dotenv_example_is_allowed(tmp_path, monkeypatch):
    """`.env.example` is the documented way to publish a variable *name*."""
    ok, _ = run_d(tmp_path, monkeypatch, {".env.example": "ARC_API_KEY="})
    assert ok


def test_the_exact_value_scan_still_runs_when_env_exists(tmp_path, monkeypatch):
    """The original mechanism is kept, not replaced: on the author's machine it
    is the only one of the three with no false positives at all. Note the value
    here is not key-shaped and sits in no credential context, so *only* the
    exact-value scan can catch it."""
    ok, notes = run_d(tmp_path, monkeypatch,
                      {"leak.md": f"the run used {EXACT} today"},
                      env=f"ARC_API_KEY={EXACT}\n")
    assert not ok and any(".env value appears" in n for n in notes)


def test_the_value_is_never_printed(tmp_path, monkeypatch):
    """A leak detector that prints the leak has moved it into the CI log."""
    value = EXACT
    ok, notes = run_d(tmp_path, monkeypatch,
                      {"leak.md": f"oops {value}"},
                      env=f"ARC_API_KEY={value}\n")
    assert not ok
    assert value not in "\n".join(notes)


def test_a_shaped_token_is_not_printed_either(tmp_path, monkeypatch):
    ok, notes = run_d(tmp_path, monkeypatch, {"leak.md": f"api_key: {SHAPED}"})
    assert not ok and SHAPED not in "\n".join(notes)


# ------------------------------------------------- what must NOT be caught
#
# Each of these is a real line from this repository, or the shape of one. A
# permanently red gate is one somebody switches off, and this is the last gate
# before publication -- so the false positives matter as much as the misses.

@pytest.mark.parametrize("body,why", [
    (f"the run id is {SHAPED} and nothing else", "a bare shaped token"),
    (f"see https://repositories.lib.utexas.edu/items/{SHAPED}",
     "P7's search traces, live in this tree"),
    ("E-08 wanted: a guard that counts (`count(Token, present = false)`)",
     "prose about citation tokens"),
    ("B never saw the token: a citation nobody resolves",
     "'token:' followed by a sentence"),
    ('"token": "A0_REPORT.md"', "P17's census.json, live in this tree"),
    ('"token": "playbook.dsl"', "the same, another row"),
    ("ARC_API_KEY=", ".env.example's own line"),
    ("ARC_API_KEY=<your-key-here>", "a placeholder"),
    ("ARC_API_KEY=${ARC_API_KEY}", "a shell indirection"),
    ("api_key: REDACTED", "a redaction"),
    ("print(mask(key))  # 7171...05dd -- safe to log", "documented mask output"),
    ("secret: xxx", "too short to be a credential"),
    ("ROTATED = 'somepart' + 'anotherpartentirely'",
     "a fixture assembled at runtime -- this suite's own trick, and the reason "
     "the scanner does not red on its own negative control"),
])
def test_these_are_not_caught(tmp_path, monkeypatch, body, why):
    ok, notes = run_d(tmp_path, monkeypatch, {"doc.md": body})
    assert ok, "false positive on %s: %s" % (why, notes)


def test_the_live_tree_is_green():
    """Positive control, on the real directory rather than a synthetic one. If
    this reds, either something leaked or the matcher just grew a false positive
    -- and the notes say which."""
    ok, notes = vp.check_nosecret()
    assert ok, "check D is red on the live tree: %s" % "\n".join(notes)


def test_the_documented_promise_is_now_executable():
    """The module docstring has promised "nothing shaped like the ARC key" since
    it was drafted, and until this item there was no shape or entropy test in
    `check_nosecret` at all -- the docstring was the only place the second half
    of the check existed."""
    assert "shaped like the ARC key" in vp.__doc__
    assert vp.UUID_SHAPED.search(SHAPED)
    assert vp._shaped_in_context(f"api_key: {SHAPED}")
    assert not vp._shaped_in_context(f"item {SHAPED} in a catalogue listing")


def test_a_finding_survives_a_root_that_is_not_an_ancestor(tmp_path, monkeypatch):
    """`relative_to` raises when ROOT is not above the file being named. ROOT is
    always an ancestor in production, so this is a crash path rather than a
    verdict path -- and a leak detector that raises while naming what it caught
    reports nothing. Found by a probe that redirected ROOT alone; kept because
    the next probe will do the same thing."""
    here = tmp_path / "paper"
    here.mkdir()
    (here / "leak.md").write_text(f"api_key: {SHAPED}", encoding="utf-8")
    monkeypatch.setattr(vp, "HERE", here)
    monkeypatch.setattr(vp, "ROOT", tmp_path / "elsewhere")
    ok, notes = vp.check_nosecret()
    assert not ok and "leak.md" in "\n".join(notes)
