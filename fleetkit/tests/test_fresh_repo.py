"""The acceptance line: a fleet stood up in an empty repo actually coordinates.

S18's bar is *"initialise fleetkit in a brand-new empty repository, start two
workers, have them claim two toy items off the board and deliver them -- it
counts only if it runs."*

This file runs that, with one substitution stated plainly: the two workers are
**processes, not language models**. They are real OS processes running the real
board CLI against a real filesystem, so everything the kernel is responsible
for -- atomic claiming, territory exclusivity, delivery, the log -- is exercised
for real. What is simulated is the part fleetkit does not provide: the judgment
inside a worker.

That substitution is the honest limit of this file and it is why S18 is not
finished by it. The remaining half of the acceptance -- two *live* agent
sessions -- costs quota and is recorded as outstanding rather than quietly
redefined into what was convenient to test. This repository has a name for the
other choice, and a taxonomy entry for it: announcement diverging from fact.
"""

import json
import os
import subprocess
import sys
import textwrap

import pytest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit import config                                     # noqa: E402


def _fleet(tmp_path):
    """A brand-new repo with fleetkit initialised in it."""
    root = tmp_path / "newproject"
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    config.write_default(str(root), task_prefix="NewProjectAgent-",
                         territories=["src", "docs"])
    home = root / ".fleet"
    home.mkdir()
    return root, home


def _board(home, *args, expect=0):
    env = dict(os.environ)
    env["FLEET_HOME"] = str(home)
    env["PYTHONPATH"] = KIT + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    r = subprocess.run([sys.executable, "-m", "fleetkit.board"] + list(args),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, cwd=str(home))
    assert r.returncode == expect, (args, r.returncode, r.stdout, r.stderr)
    return r.stdout


def _put_item(home, iid, cell, territory, lane=None):
    items = home / "board" / "items"
    items.mkdir(parents=True, exist_ok=True)
    body = "priority: 2\ncell: %s\nterritory: %s\ndeps: none\n" % (cell, territory)
    if lane:
        body += "lane: %s\n" % lane
    body += "\n# %s\n\nA toy item.\n" % iid
    (items / ("%s.md" % iid)).write_text(body, encoding="utf-8")


def test_a_fresh_repo_gets_a_config_that_validates(tmp_path):
    root, _ = _fleet(tmp_path)
    cfg = config.load(str(root))
    assert cfg.task_prefix == "NewProjectAgent-"
    assert cfg.territories == ["src", "docs"]


def test_an_empty_task_prefix_is_refused_at_load(tmp_path):
    """The field whose silent default would report every worker dead."""
    root = tmp_path / "p"
    root.mkdir()
    (root / config.CONFIG_NAME).write_text(
        json.dumps({"task_prefix": "", "territories": ["src"]}),
        encoding="utf-8")
    with pytest.raises(config.ConfigError) as exc:
        config.load(str(root))
    assert "liveness" in str(exc.value)


def test_a_missing_config_is_an_error_not_a_default(tmp_path):
    root = tmp_path / "bare"
    root.mkdir()
    with pytest.raises(config.ConfigError):
        config.load(str(root))


# ------------------------------------------------- the acceptance itself

def test_two_workers_claim_and_deliver_two_items(tmp_path):
    """The S18 acceptance, with process workers instead of model workers."""
    _root, home = _fleet(tmp_path)
    _put_item(home, "T1-first", "T1", "src")
    _put_item(home, "T2-second", "T2", "docs")

    out1 = _board(home, "claim", "W-1")
    out2 = _board(home, "claim", "W-2")
    assert "CLAIM" in out1 and "CLAIM" in out2
    first = out1.splitlines()[0].split()[1]
    second = out2.splitlines()[0].split()[1]
    assert {first, second} == {"T1-first", "T2-second"}, (out1, out2)

    claimed = sorted(os.listdir(home / "board" / "claimed"))
    assert len(claimed) == 2, claimed

    _board(home, "done", first, "W-1")
    _board(home, "done", second, "W-2")
    done = sorted(os.listdir(home / "board" / "done"))
    assert len(done) == 2, done
    assert not os.listdir(home / "board" / "claimed")

    log = (home / "board" / "board.log").read_text(encoding="utf-8")
    for token in ("CLAIM", "DONE", "T1-first", "T2-second", "W-1", "W-2"):
        assert token in log, token


def test_two_workers_cannot_take_the_same_territory(tmp_path):
    """Territory exclusivity is the property the whole board exists for.

    Without it two sessions edit one directory and the merge is a coin toss.
    """
    _root, home = _fleet(tmp_path)
    _put_item(home, "T1-a", "T1", "src")
    _put_item(home, "T2-b", "T2", "src")          # same territory

    out1 = _board(home, "claim", "W-1")
    assert "CLAIM" in out1
    # Exit 3 / BOARD-EMPTY, not exit 0 with no claim: "there is nothing you may
    # take" is a distinct answer from "here is your item", and a caller that
    # could not tell them apart would loop forever thinking it had work.
    out2 = _board(home, "claim", "W-2", expect=3)
    assert out2.strip() == "BOARD-EMPTY", (
        "the second worker took an item in a territory already held: %s" % out2)


def test_a_delivered_item_frees_its_territory(tmp_path):
    _root, home = _fleet(tmp_path)
    _put_item(home, "T1-a", "T1", "src")
    _put_item(home, "T2-b", "T2", "src")
    taken = _board(home, "claim", "W-1").splitlines()[0].split()[1]
    _board(home, "done", taken, "W-1")
    assert "CLAIM" in _board(home, "claim", "W-2")
