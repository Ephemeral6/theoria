"""The §9 launch gate, on the path that actually spends.

`freeze/launch_gate.py` has existed and been self-tested (12/12, including the
case that proves green is reachable) since S4, and until now nothing that could
stop a launch ever asked it anything: `freeze/verify.sh` prints its verdict as a
NOTE, and `verify.sh` is not a path that spends money. So
`freeze/STATS_RULES.md` §9's **未实现不得开跑** was prose with no executor --
which is the exact failure the gate itself was built to end, one level up.

This file tests the wire, and it tests it **both ways on purpose**.

A test suite that only ever observes a refusal cannot tell three states apart:

* the wire works and today's answer is no;
* the wire is connected backwards;
* the wire is not connected at all, and something else is refusing.

So there are three anchors here rather than one:

1. **REFUSE** -- the real `freeze/launch_gate.py` against the real
   `STATS_RULES.md` and the real registry, through the real
   `Campaign.__init__`, must refuse a sealed roster and name the outstanding
   rows.
2. **LAUNCH** -- the same wire, handed a gate that reports `clear`, must let
   the launch through. Built the way
   `freeze/runs/20260729T155500Z-S4-launch-gate/probe_r4_clearing_path.py`
   builds it: the **real** `launch_gate.gate()` over the **real**
   `STATS_RULES.md`, with only the registry synthesised, and each entry a
   genuinely discriminating check (it accepts one artefact and rejects
   another) so that "clear" is earned rather than asserted.
3. **UNAFFECTED** -- a development-pile roster must not invoke the gate at all.
   Not "invoke it and ignore the answer": the A3 campaign is running on those
   four games and the gate is about the sealed confirmation, so the two must
   not be able to interfere even in principle.

Anchor 2 needs a driver script because `launch_gate.py --json` has no flags for
pointing at a scratch registry, and `freeze/` is another territory that this
arm may not edit. The driver reproduces `launch_gate.main()`'s contract exactly
(same JSON keys, same 0/1/2), and
`test_the_driver_agrees_with_the_real_binary_on_the_real_state` pins that claim
against the real binary rather than leaving it as a comment.

Zero network, zero spend, zero sealed-pile contact: the one sealed id these
tests use is read out of `arc-recon/data/piles.json` at runtime and never
written down here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from harness import campaign as camp

FREEZE = os.path.join(camp.REPO, "freeze")
REAL_RULES = os.path.join(FREEZE, "STATS_RULES.md")


# -- helpers ----------------------------------------------------------------

def _a_sealed_id() -> str:
    """One sealed game id, from the cut itself. Never a literal in this file."""
    with open(os.path.join(camp.REPO, "arc-recon", "data", "piles.json"),
              encoding="utf-8") as fh:
        return json.load(fh)["sealed_pile"][0]


#: A check that genuinely discriminates: it accepts a target containing the
#: word and rejects one that does not. Copied in spirit from
#: `launch_gate.py:_FAKE_CHECK`, which is the shape the gate's own selftest
#: uses to show that "implemented" and "implemented but stubbed" are different.
_DISCRIMINATING = '''import sys
sys.exit(0 if "NONTRIVIAL" in open(sys.argv[1], encoding="utf-8").read() else 1)
'''

#: `launch_gate.main()`, reproduced over `gate()`'s three parameters. Every
#: line of the contract that matters is here: the JSON keys a caller reads and
#: the 0/1/2 exit codes. Pinned against the real binary by a test below.
_DRIVER = '''import json, os, sys
sys.path.insert(0, %(freeze)r)
import launch_gate as G
try:
    verdict, findings = G.gate(rules=%(rules)r, registry_path=%(reg)r,
                               root=%(root)r)
except G.GateError as exc:
    print(json.dumps({"verdict": "error", "error": str(exc),
                      "may_launch": False}, ensure_ascii=False))
    sys.exit(2)
print(json.dumps({"verdict": verdict, "may_launch": verdict == "clear",
                  "blockers": findings}, ensure_ascii=False))
sys.exit(0 if verdict == "clear" else 1)
'''


def _clearing_driver(tmp_path, rules_path=None):
    """A `launch_gate --json` command that reports **clear**, honestly.

    "Honestly" is the whole point and it is worth spelling out. The rules are
    the repository's real `STATS_RULES.md`, so the row set is whatever §9
    actually declares today -- if a row is added tomorrow this control keeps
    covering it instead of going stale. Only the registry is synthetic, and
    every entry in it points at a check that must accept `good.txt` **and**
    reject `vacuous.txt`; `launch_gate.evaluate` runs both and refuses the
    entry if either half fails. So the `clear` this returns is produced by the
    real gate logic doing its real work, not by a stub that says yes.
    """
    rules_path = rules_path or REAL_RULES
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    (root / "check.py").write_text(_DISCRIMINATING, encoding="utf-8")
    (root / "good.txt").write_text("NONTRIVIAL theorem\n", encoding="utf-8")
    (root / "vacuous.txt").write_text("proves nothing\n", encoding="utf-8")

    sys.path.insert(0, FREEZE)
    try:
        import launch_gate as gate_mod                  # noqa: PLC0415
        with open(rules_path, encoding="utf-8") as fh:
            declared = gate_mod.parse_blockers(fh.read())
    finally:
        sys.path.remove(FREEZE)

    registry = {row: {"state": "implemented",
                      "cmd": [sys.executable, "check.py", "{target}"],
                      "positive_target": "good.txt",
                      "negative_target": "vacuous.txt"}
                for row in declared}
    reg_path = tmp_path / "registry.json"
    reg_path.write_text(json.dumps({"blockers": registry}, ensure_ascii=False),
                        encoding="utf-8")

    driver = tmp_path / "driver.py"
    driver.write_text(_DRIVER % {"freeze": FREEZE, "rules": str(rules_path),
                                 "reg": str(reg_path), "root": str(root)},
                      encoding="utf-8")
    return [sys.executable, str(driver)]


def _script(tmp_path, name, body):
    path = tmp_path / name
    path.write_text(body, encoding="utf-8")
    return [sys.executable, str(path)]


# -- 1. REFUSE: the real state, through the real constructor ----------------

def test_the_real_gate_refuses_a_sealed_launch(tmp_path):
    """Today's answer is no, and it is *this* wire saying so.

    Asserting only "it raised" would pass even if `assert_dev_pile` were the
    one refusing and the gate were never called, which is the failure this
    whole item is about. So the message must carry the gate's own reasoning --
    the §9 row numbers -- and the detail must carry the exit code.
    """
    sealed = _a_sealed_id()
    with pytest.raises(camp.CampaignStopped) as caught:
        camp.Campaign(prompt_id="A16-negative-control",
                      out_dir=str(tmp_path / "out"), games=[sealed],
                      offline=True)
    stop = caught.value
    assert sealed in str(stop), str(stop)
    assert "launch refused" in str(stop)
    assert "§9" in str(stop) or "launch_gate" in str(stop)
    # The gate ran, and its non-zero exit is what refused.
    assert stop.detail["exit_code"] != 0, stop.detail
    assert stop.detail["outstanding"], stop.detail
    # Named, not merely counted: a refusal that will not say which rows are
    # outstanding cannot be acted on.
    assert all(row["row"] for row in stop.detail["outstanding"])


def test_the_real_gate_binary_is_the_one_being_asked(tmp_path):
    """The refusal above must come from `freeze/launch_gate.py` itself.

    `assert_launch_cleared` builds its command from `camp.LAUNCH_GATE`; if that
    path were wrong, or the subprocess were never launched, the refusals in
    this file would still all pass (everything fails closed). Point the
    constant at nothing and the failure mode has to change *shape* -- from "§9
    has N blockers outstanding" to "the gate could not be read" -- which is
    only possible if the real file is what was being read before.
    """
    assert os.path.exists(camp.LAUNCH_GATE), camp.LAUNCH_GATE
    real = camp.assert_launch_cleared  # sanity: the symbol exists

    sealed = _a_sealed_id()
    with pytest.raises(camp.CampaignStopped) as caught:
        real([sealed])
    from_real = str(caught.value)
    assert "outstanding" in from_real

    missing = tmp_path / "no_such_gate.py"
    with pytest.raises(camp.CampaignStopped) as caught:
        real([sealed], gate_cmd=[sys.executable, str(missing), "--json"])
    from_missing = str(caught.value)
    assert "readable JSON object" in from_missing
    assert from_missing != from_real


# -- 2. LAUNCH: the same wire, with the gate reporting clear ----------------

def test_a_cleared_gate_lets_a_launch_through(tmp_path):
    """The half that "only test the refusal" cannot reach.

    Without this, a wire that raises unconditionally -- or one hooked up to the
    wrong signal -- is indistinguishable from a working one, because the real
    answer is `blocked` and will stay `blocked` until someone implements §9.2,
    §9.14 and the rest.
    """
    sealed = _a_sealed_id()
    doc = camp.assert_launch_cleared([sealed],
                                     gate_cmd=_clearing_driver(tmp_path))
    assert doc["verdict"] == "clear", doc
    assert doc["may_launch"] is True
    assert doc["blockers"], "a clear verdict over an empty row set is the one " \
                            "way this gate must never go green"
    assert all(b["cleared"] for b in doc["blockers"])


def test_the_driver_agrees_with_the_real_binary_on_the_real_state():
    """The clearing control drives `gate()` directly; this pins that to the CLI.

    `_DRIVER` is a second copy of `launch_gate.main()`'s contract, and a second
    copy can drift. Run both against the **real** registry and require the same
    verdict, the same `may_launch` and the same exit code. If `main()` ever
    changes shape, this goes red and the clearing control above is known to be
    testing something the arm no longer talks to.
    """
    import tempfile                                     # noqa: PLC0415

    # `encoding=` for the same reason `assert_launch_cleared` needs it: §9 is
    # Chinese prose and `text=True` decodes with the locale codec.
    real = subprocess.run([sys.executable, camp.LAUNCH_GATE, "--json"],
                          cwd=camp.REPO, capture_output=True,
                          encoding="utf-8", errors="replace",
                          timeout=camp.LAUNCH_GATE_TIMEOUT)
    with tempfile.TemporaryDirectory() as tmp:
        driver = os.path.join(tmp, "driver.py")
        with open(driver, "w", encoding="utf-8") as fh:
            fh.write(_DRIVER % {"freeze": FREEZE, "rules": REAL_RULES,
                                "reg": os.path.join(FREEZE,
                                                    "launch_blockers.json"),
                                "root": camp.REPO})
        mirrored = subprocess.run([sys.executable, driver], cwd=camp.REPO,
                                  capture_output=True,
                                  encoding="utf-8", errors="replace",
                                  timeout=camp.LAUNCH_GATE_TIMEOUT)

    assert real.returncode == mirrored.returncode, (real.stdout, mirrored.stdout)
    a, b = json.loads(real.stdout), json.loads(mirrored.stdout)
    assert a["verdict"] == b["verdict"]
    assert a["may_launch"] == b["may_launch"]
    assert ([(x["row"], x["cleared"]) for x in a["blockers"]]
            == [(x["row"], x["cleared"]) for x in b["blockers"]])


# -- 3. UNAFFECTED: the development pile ------------------------------------

def test_a_development_roster_never_invokes_the_gate(tmp_path, monkeypatch):
    """A3's four games must not be able to be stopped by §9, at all.

    Proved by making the gate impossible to run -- `LAUNCH_GATE` pointed at a
    path that does not exist -- and then constructing a real dev-pile
    `Campaign`. Everything in `assert_launch_cleared` fails closed, so if the
    gate were invoked this would raise. It does not, which is only possible if
    the roster was judged sealed-free before any subprocess was considered.
    """
    monkeypatch.setattr(camp, "LAUNCH_GATE",
                        str(tmp_path / "definitely-not-here.py"))
    campaign = camp.Campaign(prompt_id="A16-dev-unaffected",
                             out_dir=str(tmp_path / "out"),
                             games=list(camp.DEV_PILE), offline=True)
    assert campaign.games == list(camp.DEV_PILE)
    assert camp.assert_launch_cleared(camp.DEV_PILE) is None


def test_the_dev_roster_is_judged_by_piles_json_not_by_a_list_here():
    """`sealed_among` asks the cut. A roster copied into this module would be a
    place for a typo to become a sealed-pile contact."""
    with open(os.path.join(camp.REPO, "arc-recon", "data", "piles.json"),
              encoding="utf-8") as fh:
        piles = json.load(fh)
    assert camp.sealed_among(piles["dev_pile"]) == []
    assert camp.sealed_among(piles["sealed_pile"]) == piles["sealed_pile"]
    assert camp.sealed_among(["not-a-real-game"]) == []

    # And no sealed id is written down in the module that does the judging.
    with open(camp.__file__, encoding="utf-8") as fh:
        source = fh.read()
    assert not [g for g in piles["sealed_pile"] if g in source]


# -- fail closed, in every direction ----------------------------------------

def test_exit_two_refuses_exactly_like_exit_one(tmp_path):
    """"The gate could not evaluate itself" is not a pass.

    `launch_gate.py`'s own docstring: *1 and 2 are both "no" ... never so a
    caller can treat 2 as a pass.* A caller that tested only exit 1 would obey
    the letter of that and still launch on a broken gate -- and a broken gate
    is exactly the state an attacker (or a bad merge) produces most cheaply.
    """
    sealed = _a_sealed_id()
    cmd = _script(tmp_path, "err.py", 'import json, sys\n'
                  'print(json.dumps({"verdict": "error", "may_launch": False,'
                  ' "error": "STATS_RULES.md is missing"}))\n'
                  'sys.exit(2)\n')
    with pytest.raises(camp.CampaignStopped) as caught:
        camp.assert_launch_cleared([sealed], gate_cmd=cmd)
    assert "could not evaluate itself" in str(caught.value)
    assert caught.value.detail["exit_code"] == 2


def test_exit_zero_without_may_launch_is_not_a_pass(tmp_path):
    """The exit code and the document have to agree before anything spends."""
    sealed = _a_sealed_id()
    cmd = _script(tmp_path, "half.py", 'import json\n'
                  'print(json.dumps({"verdict": "clear", "may_launch": False,'
                  ' "blockers": []}))\n')
    with pytest.raises(camp.CampaignStopped) as caught:
        camp.assert_launch_cleared([sealed], gate_cmd=cmd)
    assert "disagree" in str(caught.value)


def test_a_truthy_may_launch_that_is_not_true_is_not_a_pass(tmp_path):
    """`may_launch: "yes"` is a string, and a string is truthy.

    The check is `is True` rather than a bare truth test, because the JSON
    comes from another territory's file and the one value that must never be
    accepted loosely is the one that authorises spending.
    """
    sealed = _a_sealed_id()
    cmd = _script(tmp_path, "truthy.py", 'import json\n'
                  'print(json.dumps({"verdict": "clear", "may_launch": "yes",'
                  ' "blockers": []}))\n')
    with pytest.raises(camp.CampaignStopped):
        camp.assert_launch_cleared([sealed], gate_cmd=cmd)


def test_unreadable_output_refuses(tmp_path):
    """Silence, or prose, is not consent."""
    sealed = _a_sealed_id()
    cmd = _script(tmp_path, "chatty.py",
                  'print("everything looks fine to me")\n')
    with pytest.raises(camp.CampaignStopped) as caught:
        camp.assert_launch_cleared([sealed], gate_cmd=cmd)
    assert "readable JSON object" in str(caught.value)
    assert caught.value.detail["exit_code"] == 0


def test_valid_json_that_is_not_an_object_refuses(tmp_path):
    """`json.loads` accepts `null`, a list and a bare number.

    Each of those would reach `doc.get(...)` as an AttributeError rather than
    as a refusal -- a traceback out of a money gate, which is not the same
    thing as a no even when it happens to stop the run.
    """
    sealed = _a_sealed_id()
    for name, body in (("null.py", 'print("null")\n'),
                       ("list.py", 'print("[1, 2, 3]")\n'),
                       ("number.py", 'print("0")\n')):
        with pytest.raises(camp.CampaignStopped) as caught:
            camp.assert_launch_cleared([sealed],
                                       gate_cmd=_script(tmp_path, name, body))
        assert "readable JSON object" in str(caught.value), name


def test_a_gate_that_cannot_be_launched_refuses(tmp_path):
    """`FileNotFoundError` on the interpreter itself, or on the script."""
    sealed = _a_sealed_id()
    with pytest.raises(camp.CampaignStopped) as caught:
        camp.assert_launch_cleared(
            [sealed], gate_cmd=[str(tmp_path / "no-such-binary")])
    assert "could not be run" in str(caught.value)


def test_a_gate_that_hangs_refuses(tmp_path, monkeypatch):
    """A timeout is a refusal. Anything else makes hanging a way to launch."""
    monkeypatch.setattr(camp, "LAUNCH_GATE_TIMEOUT", 1)
    sealed = _a_sealed_id()
    cmd = _script(tmp_path, "hang.py", 'import time\ntime.sleep(30)\n')
    with pytest.raises(camp.CampaignStopped) as caught:
        camp.assert_launch_cleared([sealed], gate_cmd=cmd)
    assert "could not be run" in str(caught.value)
    assert "Timeout" in str(caught.value)


def test_a_mixed_roster_is_judged_by_its_sealed_members(tmp_path):
    """One sealed id among the four dev games is enough to summon the gate."""
    sealed = _a_sealed_id()
    roster = list(camp.DEV_PILE) + [sealed]
    assert camp.sealed_among(roster) == [sealed]
    with pytest.raises(camp.CampaignStopped) as caught:
        camp.assert_launch_cleared(roster)
    assert sealed in str(caught.value)
    # Only the sealed member is named as the reason.
    assert caught.value.detail["game_ids"] == [sealed]
