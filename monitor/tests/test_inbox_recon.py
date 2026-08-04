"""The inbox reconciler, and the three ways it could lie.

The reconciler exists to answer one question -- does anyone downstream sweep
`monitor/inbox/` -- and a tool that answers it wrongly is worse than no tool,
because the answer is a number and numbers get quoted. So the negative controls
here are the acceptance:

* an ask that nobody cites must read `uncited`, and not be quietly dropped;
* an ask **with no addressee** must read `seen_by_addressee: None`, never
  `False` -- nobody was named, so nobody failed to read it, and reporting a
  False there would manufacture nine negligent territories out of a naming
  convention;
* a citation from *outside* the addressee's territory must not count as the
  addressee having seen it. This is the one that matters: 217 of the 225
  unaddressed asks on 2026-08-04 were "cited", almost entirely by the
  monitor's own audit files, and a reconciler that accepted those as delivery
  would report a healthy channel over a dead one.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import inbox_recon  # noqa: E402


def _git(cwd, *args):
    subprocess.run(("git",) + args, cwd=cwd, check=True,
                   capture_output=True, text=True)


@pytest.fixture()
def repo(tmp_path):
    """A miniature repo shaped like this one: an inbox and some territories."""
    root = tmp_path / "repo"
    (root / "monitor" / "inbox").mkdir(parents=True)
    (root / "monitor" / "audit").mkdir(parents=True)
    (root / "exam").mkdir()
    (root / "freeze").mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t")
    _git(root, "config", "user.name", "t")
    return root


def _write(root, rel, text):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_an_ask_nobody_names_reads_uncited(repo):
    _write(repo, "monitor/inbox/20260804T0100Z-freeze-to-exam-a-thing.md",
           "please look at this")
    _write(repo, "monitor/inbox/README.md", "the drop box")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "one ask")

    out = inbox_recon.reconcile(str(repo))
    assert out["open"] == 1
    assert out["uncited"] == 1
    assert out["cited"] == 0
    assert out["rows"][0]["addressee"] == "exam"
    assert out["rows"][0]["seen_by_addressee"] is False


def test_no_addressee_is_none_and_never_false(repo):
    """Absence is recorded as absence.

    `20260731T1600Z-W-1800-iteration-prior-art-brief.md` names a *worker*, not
    a territory. Scoring it `False` would say a territory ignored it; there is
    no territory to have ignored it. 225 of the 235 open asks on 2026-08-04 are
    this shape, which is the finding, not a rounding error.
    """
    _write(repo, "monitor/inbox/20260804T0200Z-W-1800-a-brief.md", "hello")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "unaddressed ask")

    out = inbox_recon.reconcile(str(repo))
    row = out["rows"][0]
    assert row["addressee"] is None
    assert row["seen_by_addressee"] is None
    assert out["unseen_by_addressee"] == 0
    assert out["no_addressee_to_have_seen_it"] == 1


def test_a_citation_from_the_wrong_territory_is_not_delivery(repo):
    """The load-bearing control.

    The monitor citing an ask in its own audit file proves the monitor read
    it. The ask was addressed to exam. If this test passes with `seen` true,
    every number this tool prints is an artefact of the monitor talking to
    itself.
    """
    name = "20260804T0300Z-freeze-to-exam-your-tests-must-flip.md"
    _write(repo, "monitor/inbox/" + name, "four of your tests must flip")
    _write(repo, "monitor/audit/WIP-cycle99-evidence.md",
           "seen while sweeping: monitor/inbox/" + name)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "cited by the monitor only")

    out = inbox_recon.reconcile(str(repo))
    row = out["rows"][0]
    assert row["cited"] is True, "the citation is real and must be reported"
    assert row["seen_by_addressee"] is False, (
        "a monitor-side citation is not the addressee having seen it")
    assert out["cited"] == 1 and out["seen_by_addressee"] == 0


def test_a_citation_from_the_addressee_is_delivery(repo):
    """The positive. A gate that only ever says no is the same as a broken one."""
    name = "20260804T0400Z-exam-to-freeze-u3-vacuous-label.md"
    _write(repo, "monitor/inbox/" + name, "your label covers two things")
    _write(repo, "freeze/DECISIONS.md",
           "ruled, per monitor/inbox/" + name)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "the addressee answered")

    out = inbox_recon.reconcile(str(repo))
    row = out["rows"][0]
    assert row["seen_by_addressee"] is True
    assert row["seen_in"] == ["freeze/DECISIONS.md"]


def test_archive_is_not_counted_as_open(repo):
    """A file in `archive/` was adjudicated. That is the sweep, done by hand.

    Counting it open would report the one part of the mechanism that works as
    part of the failure.
    """
    _write(repo, "monitor/inbox/archive/20260701T0000Z-old-to-exam-done.md", "x")
    _write(repo, "monitor/inbox/20260804T0500Z-new-to-exam-open.md", "y")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "one archived, one open")

    out = inbox_recon.reconcile(str(repo))
    assert out["open"] == 1
    assert out["archived"] == 1
    assert out["rows"][0]["file"].startswith("20260804T0500Z")


def test_the_longest_territory_name_wins(repo):
    """`-to-theoria-arm-` is not `theoria` plus noise.

    There is no `theoria` territory today, so this cannot misfire yet. It is
    pinned because the failure it prevents is silent: an ask would be scored
    against a territory whose directory does not exist, and every citation
    check against it would return empty -- i.e. it would read `unseen` forever
    and look exactly like a real finding.
    """
    assert inbox_recon.addressee_of(
        "20260801T0000Z-P12-proxy-to-theoria-arm-the-cli.md") == "theoria-arm"
    assert inbox_recon.addressee_of(
        "20260801T0400Z-theoria-arm-to-proxy-refusal-wave.md") == "proxy"
    assert inbox_recon.addressee_of("20260801T0600Z-PROP-schema.md") is None


def test_the_real_inbox_is_readable_and_the_counts_are_consistent():
    """Runs against this repository, and only checks arithmetic identities.

    No count is hard-coded: the numbers move every day and a test that pinned
    them would be red by tomorrow and deleted by the day after. What cannot
    move is that the parts sum to the whole.
    """
    out = inbox_recon.reconcile()
    assert out["open"] > 0
    assert out["cited"] + out["uncited"] == out["open"]
    assert out["addressed"] + out["unaddressed"] == out["open"]
    assert (out["seen_by_addressee"] + out["unseen_by_addressee"]
            + out["no_addressee_to_have_seen_it"]) == out["open"]
    assert out["no_addressee_to_have_seen_it"] == out["unaddressed"]
    for row in out["rows"]:
        if row["seen_by_addressee"]:
            assert row["cited"], "seen implies cited, by construction"
