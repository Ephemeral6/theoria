"""Negative and positive controls for `master_tree_guard`.

S39 requirement 3, verbatim: a real miswrite must go RED (constructed: touch
`monitor/scan.py` on master's tree) and a normal board action must stay GREEN
(constructed: `board.py claim` rewriting `monitor/board/items/`).

Both controls run in a throwaway git repository built by the fixture, not
against the live repo. That is not squeamishness -- a test that dirtied
master's working tree to prove the guard notices dirty working trees would be
the exact defect S39 exists to stop, and it would also race every other agent
in the fleet.

The live tree is exercised separately and READ-ONLY by
`test_live_master_tree_is_judgeable`, which asserts only that the guard can
parse and classify the real ~200-path status without falling over. It asserts
nothing about the colour: the real tree's colour changes minute to minute as
the fleet works, and a test that pinned it would fail for the wrong reason.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import master_tree_guard as g  # noqa: E402


def _git(repo, *args):
    subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


@pytest.fixture()
def repo(tmp_path):
    """A miniature of the real layout: fleet state plus real source."""
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "master")
    _git(r, "config", "user.email", "t@example.invalid")
    _git(r, "config", "user.name", "t")
    _git(r, "config", "commit.gpgsign", "false")

    (r / "monitor").mkdir()
    (r / "monitor" / "board" / "items").mkdir(parents=True)
    (r / "monitor" / "ops-status").mkdir()
    (r / "monitor" / "bus" / "RES-4").mkdir(parents=True)
    (r / "engine-rig").mkdir()

    # Real source -- must never be dirty on the shared tree.
    (r / "monitor" / "scan.py").write_text("# the monitor\n", encoding="utf-8")
    (r / "monitor" / "reflex.py").write_text("# reflex\n", encoding="utf-8")
    (r / "engine-rig" / "solver.py").write_text("# solver\n", encoding="utf-8")
    # Fleet live state -- dirty here is the normal condition.
    (r / "monitor" / "board" / "items" / "S1-a.md").write_text("a\n", encoding="utf-8")
    (r / "monitor" / "ops-status" / "RES-4.json").write_text("{}\n", encoding="utf-8")
    (r / "monitor" / "bus" / "RES-4" / "out.jsonl").write_text("", encoding="utf-8")
    (r / "monitor" / "board.log").write_text("", encoding="utf-8")
    (r / "monitor" / "state.json").write_text("{}\n", encoding="utf-8")
    (r / "monitor" / "res").mkdir()
    (r / "monitor" / "res" / "RES-4.md").write_text("contract\n", encoding="utf-8")
    # The guard itself, so the installed hook can find it the way it does in
    # the real tree. Copied rather than imported: the hook shells out to
    # `$(git rev-parse --show-toplevel)/monitor/master_tree_guard.py`, and a
    # test that stubbed that path would not be testing the hook.
    shutil.copyfile(g.__file__, r / "monitor" / "master_tree_guard.py")

    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "base")
    return r


# --------------------------------------------------------------------------
# Requirement 3, negative control: a real miswrite must be RED.
# --------------------------------------------------------------------------


def test_touching_monitor_scan_on_master_is_red(repo):
    """The exact shape of the S38 incident: source edited on the shared tree."""
    (repo / "monitor" / "scan.py").write_text("# the monitor\n# edited\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert result["miswrites"] == 1
    assert result["miswrite_paths"][0]["path"] == "monitor/scan.py"
    assert result["miswrite_paths"][0]["code"] == " M"


def test_miswrite_outside_monitor_is_red(repo):
    """The guard is not monitor-specific -- any tracked source counts."""
    (repo / "engine-rig" / "solver.py").write_text("# solver\n# edited\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert [e["path"] for e in result["miswrite_paths"]] == ["engine-rig/solver.py"]


def test_deleting_a_tracked_source_file_is_red(repo):
    """A miswrite can also be a deletion -- the S38 revert direction."""
    (repo / "monitor" / "reflex.py").unlink()

    result = g.report(str(repo))

    assert result["red"] is True
    assert [e["path"] for e in result["miswrite_paths"]] == ["monitor/reflex.py"]


def test_exit_code_is_2_on_red(repo, capsys):
    (repo / "monitor" / "scan.py").write_text("x\n", encoding="utf-8")
    assert g.main(["-C", str(repo)]) == 2


# --------------------------------------------------------------------------
# Requirement 3, positive control: normal fleet operation must be GREEN.
# --------------------------------------------------------------------------


def test_a_board_claim_is_green(repo):
    """`board.py claim` moves an item and rewrites the board -- normal, green."""
    items = repo / "monitor" / "board" / "items"
    (items / "S1-a.md").write_text("a\nclaimed-by: RES-4\n", encoding="utf-8")
    (repo / "monitor" / "board" / "claimed").mkdir()
    (repo / "monitor" / "board" / "claimed" / "S1-a.RES-4.md").write_text(
        "a\n", encoding="utf-8"
    )
    (repo / "monitor" / "board.log").write_text("claim S1-a RES-4\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is False
    assert result["miswrites"] == 0


def test_heartbeat_and_bus_traffic_are_green(repo):
    """The two things every agent does every cycle must never gate."""
    (repo / "monitor" / "ops-status" / "RES-4.json").write_text(
        '{"cycle": 49}\n', encoding="utf-8"
    )
    (repo / "monitor" / "ops-status" / "RES-4.lock").write_text("now\n", encoding="utf-8")
    (repo / "monitor" / "bus" / "RES-4" / "out.jsonl").write_text(
        '{"seq": 1}\n', encoding="utf-8"
    )
    (repo / "monitor" / "state.json").write_text('{"x": 1}\n', encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is False
    assert g.main(["-C", str(repo)]) == 0


def test_a_full_normal_cycle_stays_green(repo):
    """All the fleet-state writes of one cycle at once, tracked and untracked."""
    (repo / "monitor" / "board" / "items" / "S1-a.md").write_text("edited\n", encoding="utf-8")
    (repo / "monitor" / "ops-status" / "RES-4.json").write_text("{}\n", encoding="utf-8")
    (repo / "monitor" / "bus" / "RES-4" / "cursor.json").write_text("{}\n", encoding="utf-8")
    (repo / "monitor" / "inbox").mkdir()
    (repo / "monitor" / "inbox" / "20260730T0500Z-RES-4-x.md").write_text(
        "proposal\n", encoding="utf-8"
    )
    (repo / "monitor" / "ci").mkdir()
    (repo / "monitor" / "ci" / "merge.log").write_text("merged\n", encoding="utf-8")
    (repo / "monitor" / "reflex.log").write_text("tick\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is False
    assert result["miswrites"] == 0


# --------------------------------------------------------------------------
# Tier 3: untracked outside fleet state. Reported separately, gates the same.
# --------------------------------------------------------------------------


def test_untracked_scratch_gates(repo):
    """The first version made this amber and exit 0, and THIS TEST asserted it
    -- codifying the implementation's behaviour as the requirement. An
    adversarial review showed the cost: the S38 incident was "scan.py plus two
    new files", and new files are untracked, so the gate exempted most of the
    incident it was built for."""
    (repo / "scratchpad").mkdir()
    (repo / "scratchpad" / "notes.md").write_text("x\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert result["unfiled"] == 1
    assert result["unfiled_paths"][0]["verdict"] == g.VERDICT_UNFILED
    assert g.main(["-C", str(repo)]) == 2


def test_brand_new_files_on_the_shared_tree_gate(repo):
    """The S38 shape exactly: an edit PLUS two new files. Replayed against the
    first version -- with S39's own deliverables as the new files -- this
    scored red=False, miswrites=0, exit 0."""
    (repo / "monitor" / "scan.py").write_text("# edited\n", encoding="utf-8")
    (repo / "monitor" / "newguard.py").write_text("# new\n", encoding="utf-8")
    (repo / "monitor" / "newguard_notes.md").write_text("# new\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert result["miswrites"] == 1, "the edit to a tracked file"
    assert result["unfiled"] == 2, "the two new files -- untracked, still gating"
    assert g.main(["-C", str(repo)]) == 2


def test_code_dropped_into_a_whitelisted_directory_is_red(repo):
    """A bare `startswith` whitelist let a whitelisted directory launder source:
    `monitor/board/helper.py` classified as fleet state and was reported at no
    tier at all. Found by an adversarial review."""
    for rel in ("monitor/board/helper.py", "monitor/ci/patcher.py",
                "monitor/audit/drift_tool.py"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text("# code\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert result["fleet_state"] == 0
    assert result["unfiled"] == 3


def test_amber_and_red_are_counted_separately(repo):
    (repo / "monitor" / "scan.py").write_text("x\n", encoding="utf-8")
    (repo / "scratch.txt").write_text("x\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["miswrites"] == 1
    assert result["unfiled"] == 1
    assert result["red"] is True


# --------------------------------------------------------------------------
# The whitelist's own failure modes.
# --------------------------------------------------------------------------


def test_prefix_match_is_boundary_anchored(repo):
    """`monitor/boardgame.py` must NOT be excused by the `monitor/board/` prefix."""
    (repo / "monitor" / "boardgame.py").write_text("# not the board\n", encoding="utf-8")
    _git(repo, "add", "monitor/boardgame.py")
    _git(repo, "commit", "-q", "-m", "add lookalike")
    (repo / "monitor" / "boardgame.py").write_text("# edited\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert [e["path"] for e in result["miswrite_paths"]] == ["monitor/boardgame.py"]


def test_a_log_in_a_subdirectory_is_not_excused_as_a_monitor_log(repo):
    """The log rule is `monitor/*.log`, one level -- not `monitor/**/*.log`.

    Note what git reports here: an untracked DIRECTORY collapses to one entry
    (`monitor/engine/`), it does not enumerate its files. That is git's default
    and the guard keeps it deliberately -- `-uall` on the live tree would
    expand `.claude/worktrees/` into a hundred whole checkouts. The consequence
    is stated in the module docstring: one amber line can stand for a directory
    of any size. It does not affect the RED tier, which only ever concerns
    tracked files, and those are never collapsed.
    """
    (repo / "monitor" / "engine").mkdir()
    (repo / "monitor" / "engine" / "run.log").write_text("x\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["unfiled"] == 1
    assert result["unfiled_paths"][0]["path"] == "monitor/engine/"
    assert result["unfiled_paths"][0]["verdict"] == g.VERDICT_UNFILED
    assert result["fleet_state"] == 0, "must not be excused as a monitor log"


def test_a_tracked_log_in_a_subdirectory_is_red(repo):
    """The same rule on the RED side, where collapsing cannot hide it."""
    (repo / "monitor" / "engine").mkdir()
    (repo / "monitor" / "engine" / "run.log").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "monitor/engine/run.log")
    _git(repo, "commit", "-q", "-m", "track a nested log")
    (repo / "monitor" / "engine" / "run.log").write_text("y\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert [e["path"] for e in result["miswrite_paths"]] == ["monitor/engine/run.log"]


def test_a_researcher_contract_is_fleet_state_but_a_notes_dir_under_it_is_not(repo):
    """`monitor/res/` is flat: the contracts are fleet state, subdirs are not.

    The adjudication (FINDINGS.md §1) judged `monitor/res/RES-3-notes/` a real
    MISWRITE -- per-item working notes written onto the shared tree while the
    items were worked on branches. A plain `monitor/res/` prefix would excuse
    it, which is a false negative on an instance from this guard's own sample.
    """
    (repo / "monitor" / "res" / "RES-4.md").write_text("retuned\n", encoding="utf-8")

    result = g.report(str(repo))
    assert result["red"] is False, "a retuned contract is fleet state"
    assert result["fleet_state"] == 1

    (repo / "monitor" / "res" / "RES-3-notes").mkdir()
    (repo / "monitor" / "res" / "RES-3-notes" / "V6-recon.md").write_text(
        "notes\n", encoding="utf-8"
    )

    result = g.report(str(repo))
    assert result["unfiled"] == 1
    assert result["unfiled_paths"][0]["path"] == "monitor/res/RES-3-notes/"


def test_a_tracked_source_file_under_a_flat_prefix_is_red(repo):
    """The same rule where it bites: a `.py` dropped into `monitor/res/x/`."""
    (repo / "monitor" / "res" / "tools").mkdir()
    (repo / "monitor" / "res" / "tools" / "helper.py").write_text("# x\n", encoding="utf-8")
    _git(repo, "add", "monitor/res/tools/helper.py")
    _git(repo, "commit", "-q", "-m", "track it")
    (repo / "monitor" / "res" / "tools" / "helper.py").write_text("# edited\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert [e["path"] for e in result["miswrite_paths"]] == ["monitor/res/tools/helper.py"]


def test_the_generated_dashboard_is_not_red_for_being_html(repo):
    """`monitor/index.html` is generated by every scan, and `.html` is a code
    suffix. Checking suffixes first made it a permanent false red on the live
    tree; the explicitly named file must win."""
    (repo / "monitor" / "index.html").write_text("<p>x</p>\n", encoding="utf-8")
    _git(repo, "add", "monitor/index.html")
    _git(repo, "commit", "-q", "-m", "dashboard")
    (repo / "monitor" / "index.html").write_text("<p>y</p>\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is False, "the generated dashboard is fleet state"


def test_a_source_html_in_the_same_directory_is_still_red(repo):
    """...but only the NAMED one. `monitor/app.html` is a source frontend that
    scan.py never writes, so it must not ride along on its neighbour."""
    (repo / "monitor" / "app.html").write_text("<p>x</p>\n", encoding="utf-8")
    _git(repo, "add", "monitor/app.html")
    _git(repo, "commit", "-q", "-m", "frontend")
    (repo / "monitor" / "app.html").write_text("<p>edited</p>\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert [e["path"] for e in result["miswrite_paths"]] == ["monitor/app.html"]


def test_an_untracked_whitelisted_directory_does_not_swallow_its_contents(repo):
    """git collapses an untracked directory to one entry; a whitelisted one
    would then be excused as a unit, hiding any code inside it."""
    (repo / "monitor" / "ci").mkdir()
    (repo / "monitor" / "ci" / "merge.log").write_text("ok\n", encoding="utf-8")
    (repo / "monitor" / "ci" / "patcher.py").write_text("# code\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert [e["path"] for e in result["unfiled_paths"]] == ["monitor/ci/patcher.py"]
    assert result["fleet_state"] == 1, "the log inside it is still fleet state"


def test_whitelist_prefixes_all_end_in_a_slash():
    """The boundary anchor is supplied by the trailing slash; assert it exists."""
    for prefix in g.FLEET_STATE_PREFIXES:
        assert prefix.endswith("/"), prefix


def test_clean_tree_is_green(repo):
    result = g.report(str(repo))
    assert result["total"] == 0
    assert result["red"] is False


# --------------------------------------------------------------------------
# Tree selection: a linked worktree must NOT be judged.
# --------------------------------------------------------------------------


def test_linked_worktree_is_refused_by_default(repo, tmp_path):
    """Dirty source in a linked worktree is an agent working, not a miswrite."""
    wt = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", "-b", "agent/x", str(wt))
    (wt / "monitor" / "scan.py").write_text("# branch work\n", encoding="utf-8")

    with pytest.raises(g.GuardError):
        g.report(str(wt))

    # ... and with the override it is judged, which is how the tests above work
    result = g.report(str(wt), require_main=False)
    assert result["red"] is True


def test_main_worktree_is_found_from_a_linked_one(repo, tmp_path):
    """`git worktree list` covers both worktree directories; a glob would not."""
    wt = tmp_path / "wt2"
    _git(repo, "worktree", "add", "-q", "-b", "agent/y", str(wt))

    assert os.path.normcase(g.main_worktree(str(wt))) == os.path.normcase(
        os.path.realpath(str(repo))
    ) or os.path.normcase(g.main_worktree(str(wt))) == os.path.normcase(str(repo))
    assert g.is_main_worktree(str(repo)) is True
    assert g.is_main_worktree(str(wt)) is False


# --------------------------------------------------------------------------
# Parsing: the flattened-path filename that motivated `-z`.
# --------------------------------------------------------------------------


def test_status_parser_handles_a_path_needing_quoting(repo):
    """A filename with a colon-ish/high byte must parse, not crash.

    The live tree carries `C:UsersuserDesktoptheoriamonitorpermtest.txt` with a
    U+F03A in place of the colon -- in non-`-z` porcelain that renders as octal
    escapes inside double quotes. `-z` emits raw bytes instead.
    """
    weird = repo / "CUsersuserDesktoptheoriamonitorpermtest.txt"
    weird.write_text("x\n", encoding="utf-8")

    result = g.report(str(repo))

    assert result["red"] is True
    assert result["unfiled"] == 1
    assert "permtest" in result["unfiled_paths"][0]["path"]


def test_parse_status_z_consumes_the_rename_source_field():
    raw = "R  new.py\0old.py\0 M monitor/scan.py\0"
    assert g.parse_status_z(raw) == [("R ", "new.py"), (" M", "monitor/scan.py")]


def test_parse_status_z_rejects_a_malformed_record():
    with pytest.raises(g.GuardError):
        g.parse_status_z("XY\0")


def test_a_rename_of_a_tracked_source_file_is_red(repo):
    _git(repo, "mv", "monitor/reflex.py", "monitor/reflex2.py")

    result = g.report(str(repo))

    assert result["red"] is True
    assert [e["path"] for e in result["miswrite_paths"]] == ["monitor/reflex2.py"]


# --------------------------------------------------------------------------
# Reporting must not die on the path it was built to catch.
# --------------------------------------------------------------------------


def test_human_report_survives_an_unencodable_path(monkeypatch):
    """Regression: the first live run crashed here.

    The console on this machine is cp936/GBK, and the live tree carries
    `C:UsersuserDesktoptheoriamonitorpermtest.txt` with U+F03A standing in for
    the eaten colon. GBK cannot encode it, so `print` raised
    UnicodeEncodeError *after* the guard had already found its three miswrites
    -- the finding was made and then thrown away, which reads from outside like
    a broken script rather than a red gate.

    This rebuilds that stream exactly: a strict GBK text wrapper.
    """
    import io

    stream = io.TextIOWrapper(io.BytesIO(), encoding="gbk", errors="strict")
    monkeypatch.setattr(sys, "stdout", stream)

    result = {
        "tree": "C:/repo",
        "total": 2,
        "fleet_state": 0,
        "unfiled": 1,
        "miswrites": 1,
        "red": True,
        "miswrite_paths": [
            {"path": "monitor/sc\uf03aan.py", "code": " M"},
        ],
        "unfiled_paths": [
            {"path": "C\uf03aUsersuserDesktoptheoriamonitorpermtest.txt", "code": "??"},
        ],
    }

    g._emit_human(result)  # must not raise

    stream.flush()
    written = stream.buffer.getvalue().decode("gbk", "replace")
    assert "permtest" in written
    assert "monitor/sc" in written


def test_json_output_escapes_an_unencodable_path(repo, capsys):
    """The machine-readable path was never at risk; assert it stays that way."""
    weird = repo / "C\uf03aflattened.txt"
    weird.write_text("x\n", encoding="utf-8")

    assert g.main(["-C", str(repo), "--json"]) == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["unfiled"] == 1
    assert any("flattened" in e["path"] for e in payload["unfiled_paths"])


# --------------------------------------------------------------------------
# The commit-time half: the pre-commit hook.
# --------------------------------------------------------------------------


def test_precommit_refuses_a_staged_source_file(repo):
    """The blocking half of requirement 2, at the moment it must fire."""
    (repo / "monitor" / "scan.py").write_text("# swept in\n", encoding="utf-8")
    _git(repo, "add", "monitor/scan.py")

    assert g.precommit(str(repo)) == 1


def test_precommit_allows_a_staged_board_action(repo):
    """The positive control, at the same moment. Must never block the fleet."""
    (repo / "monitor" / "board" / "items" / "S1-a.md").write_text("x\n", encoding="utf-8")
    (repo / "monitor" / "ops-status" / "RES-4.json").write_text("{}\n", encoding="utf-8")
    _git(repo, "add", "monitor/board/items/S1-a.md", "monitor/ops-status/RES-4.json")

    assert g.precommit(str(repo)) == 0


def test_precommit_allows_a_newly_added_source_file_only_via_override(repo, monkeypatch):
    """A brand-new source file is the same class -- `A`, not `M`."""
    (repo / "monitor" / "newthing.py").write_text("# new\n", encoding="utf-8")
    _git(repo, "add", "monitor/newthing.py")

    monkeypatch.delenv(g.OVERRIDE_ENV, raising=False)
    assert g.precommit(str(repo)) == 1

    monkeypatch.setenv(g.OVERRIDE_ENV, "1")
    assert g.precommit(str(repo)) == 0


def test_precommit_is_silent_in_a_linked_worktree(repo, tmp_path):
    """Branch work is the whole point of a worktree; the hook must not fire."""
    wt = tmp_path / "wt3"
    _git(repo, "worktree", "add", "-q", "-b", "agent/z", str(wt))
    (wt / "monitor" / "scan.py").write_text("# legitimate branch work\n", encoding="utf-8")
    _git(wt, "add", "monitor/scan.py")

    assert g.precommit(str(wt)) == 0


def test_precommit_allows_when_it_cannot_decide(tmp_path):
    """A guard that cannot run must say so, not wedge every commit on the box."""
    notrepo = tmp_path / "notrepo"
    notrepo.mkdir()

    assert g.precommit(str(notrepo)) == 0


def test_install_hook_is_idempotent_and_then_detected(repo):
    assert g.hook_installed(str(repo)) is False

    changed, _ = g.install_hook(str(repo))
    assert changed is True
    assert g.hook_installed(str(repo)) is True

    changed_again, _ = g.install_hook(str(repo))
    assert changed_again is False


def test_install_hook_refuses_to_clobber_a_foreign_hook(repo):
    path = g.hook_path(str(repo))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("#!/bin/sh\necho somebody else's hook\n")

    changed, message = g.install_hook(str(repo))

    assert changed is False
    assert "refusing to overwrite" in message
    assert g.hook_installed(str(repo)) is False

    changed, _ = g.install_hook(str(repo), force=True)
    assert changed is True


def test_hook_path_uses_the_common_git_dir_from_a_linked_worktree(repo, tmp_path):
    """A linked worktree's `--git-dir` has no `hooks/`; installing there would
    cover one tree and miss the main one -- requirement 4's mistake."""
    wt = tmp_path / "wt4"
    _git(repo, "worktree", "add", "-q", "-b", "agent/w", str(wt))

    assert os.path.normcase(g.hook_path(str(wt))) == os.path.normcase(
        g.hook_path(str(repo))
    )


def test_the_installed_hook_actually_blocks_a_real_commit(repo):
    """End to end through git itself, not just the python entry point."""
    g.install_hook(str(repo))
    (repo / "monitor" / "scan.py").write_text("# swept in\n", encoding="utf-8")
    _git(repo, "add", "monitor/scan.py")

    proc = subprocess.run(
        ["git", "commit", "-m", "sweep"],
        cwd=repo,
        capture_output=True,
    )

    assert proc.returncode != 0, "the hook let the commit through"
    assert b"REFUSED" in proc.stderr
    # ... and the commit really did not happen
    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=repo, capture_output=True, text=True
    )
    assert log.stdout.count("\n") == 1, "only the fixture's base commit should exist"


def test_the_installed_hook_lets_a_board_commit_through(repo):
    """The companion green, end to end. A hook that blocks everything is worse
    than none: the fleet would learn to pass --no-verify by reflex."""
    g.install_hook(str(repo))
    (repo / "monitor" / "board" / "items" / "S1-a.md").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "monitor/board/items/S1-a.md")

    proc = subprocess.run(
        ["git", "commit", "-m", "board: claim"],
        cwd=repo,
        capture_output=True,
    )

    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")


def test_the_hook_fails_open_when_the_guard_is_not_in_the_checkout(repo):
    """The hook lives in `.git/`, which no commit can change, so it survives a
    checkout of a commit from before the guard existed -- and a bisect that
    walks through one. Hard-failing there would block every commit on the
    machine for a reason unrelated to the commit, and would teach the fleet
    `--no-verify` by reflex. Found by a test failure, not by inspection."""
    g.install_hook(str(repo))
    _git(repo, "rm", "-q", "monitor/master_tree_guard.py")
    (repo / "monitor" / "scan.py").write_text("# would otherwise be refused\n", encoding="utf-8")
    _git(repo, "add", "monitor/scan.py")

    proc = subprocess.run(["git", "commit", "-m", "x"], cwd=repo, capture_output=True)

    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    assert b"not in this checkout" in proc.stderr


def test_parse_name_status_z_consumes_the_rename_destination():
    raw = "R100\0old.py\0new.py\0M\0monitor/scan.py\0"
    assert g.parse_name_status_z(raw) == [("R100", "new.py"), ("M", "monitor/scan.py")]


# --------------------------------------------------------------------------
# Probe injection: the manufactured red, its companion green, registration.
# The local norm -- `monitor/tests/test_probes_injection.py`.
# --------------------------------------------------------------------------


def _scan():
    import scan

    return scan


def test_probe_is_registered():
    """A probe that exists and is not wired in is the purest form of this bug."""
    scan = _scan()
    assert scan.PROBES["master_tree"] is scan.probe_master_tree


def test_probe_goes_red_on_a_manufactured_miswrite(repo, monkeypatch):
    scan = _scan()
    monkeypatch.setattr(scan, "ROOT", str(repo))
    (repo / "monitor" / "scan.py").write_text("# miswritten\n", encoding="utf-8")

    result = scan.probe_master_tree()

    assert result["status"] == "risk"
    assert "monitor/scan.py" in result["detail"]


def test_probe_is_not_red_on_a_normal_fleet_cycle(repo, monkeypatch):
    """The companion green: a probe hardwired to `risk` would pass the red half
    and be exactly as useless."""
    scan = _scan()
    monkeypatch.setattr(scan, "ROOT", str(repo))
    (repo / "monitor" / "board" / "items" / "S1-a.md").write_text("x\n", encoding="utf-8")
    (repo / "monitor" / "ops-status" / "RES-4.json").write_text("{}\n", encoding="utf-8")

    result = scan.probe_master_tree()

    assert result["status"] != "risk"


def test_probe_separates_the_observing_half_from_the_blocking_half(repo, monkeypatch):
    """Clean tree + no hook is `partial`, not green.

    The 2026-07-30 drift audit found seven guards green in git and absent in
    production. This probe must not become the eighth by reporting the tree it
    watches while staying silent about the fact that it cannot stop anything.
    """
    scan = _scan()
    monkeypatch.setattr(scan, "ROOT", str(repo))

    assert scan.probe_master_tree()["status"] == "partial"

    g.install_hook(str(repo))

    assert scan.probe_master_tree()["status"] == "green"


def test_probe_never_emits_amber(repo, monkeypatch):
    """`amber` is ranked in _VERDICT_RANK but has no LABEL, no STATUS_SCORE and
    no CSS pill -- emitting it can KeyError the renderer."""
    scan = _scan()
    monkeypatch.setattr(scan, "ROOT", str(repo))
    (repo / "monitor" / "scan.py").write_text("# x\n", encoding="utf-8")

    for status in (
        scan.probe_master_tree()["status"],
    ):
        assert status in {"green", "partial", "risk", "blocked", "missing"}


def test_probe_returns_missing_rather_than_raising(tmp_path, monkeypatch):
    """Crash is not a finding, and crash is not green -- the repo's fourth time."""
    scan = _scan()
    notrepo = tmp_path / "notrepo"
    notrepo.mkdir()
    monkeypatch.setattr(scan, "ROOT", str(notrepo))

    result = scan.probe_master_tree()

    assert result["status"] == "missing"
    # NOT `or "无法断言"` -- that string is hard-coded in the only `missing`
    # template, so the assertion was unconditionally true.
    assert "GuardError" in result["detail"]


def test_probe_writes_nothing_into_the_tree(repo, monkeypatch):
    """Probes must be read-only: a probe that drops a file turns verify:monitor
    red, and can turn the NEXT territory's gate red too (S13)."""
    scan = _scan()
    monkeypatch.setattr(scan, "ROOT", str(repo))
    before = subprocess.run(
        ["git", "status", "--porcelain", "-uall"],
        cwd=repo,
        capture_output=True,
        text=True,
    ).stdout

    scan.probe_master_tree()

    after = subprocess.run(
        ["git", "status", "--porcelain", "-uall"],
        cwd=repo,
        capture_output=True,
        text=True,
    ).stdout
    assert before == after


# --------------------------------------------------------------------------
# The live tree, read-only.
# --------------------------------------------------------------------------


def test_live_master_tree_is_judgeable():
    """The guard must survive the real ~200-path status. Colour not asserted."""
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        main = g.main_worktree(here)
    except g.GuardError as exc:  # pragma: no cover - only if git is absent
        pytest.skip(f"no git worktree information: {exc}")

    result = g.report(main)

    # NOT `total >= 0` and NOT just the tier partition: both hold for any
    # classifier, including one sabotaged to return fleet-state for
    # everything -- verified, it passed. Assert something only a WORKING
    # classifier satisfies: the live tree is known to carry ~150 dirty paths,
    # of which the board/heartbeat/bus traffic must be recognised as fleet
    # state, and the guard must have actually parsed each one.
    # S39 pinned `total > 50` because the shared tree carried ~150 uncommitted
    # fleet-state paths the day it was written. The cleanup campaign committed
    # that snapshot, so the live tree is quiet now and a fixed floor asserts
    # that the fleet is running, not that the classifier works. Keep the
    # anti-sabotage property only where it does not depend on the weather:
    # when there IS fleet traffic, it must be recognised as fleet traffic.
    if result["total"] > 50:
        assert result["fleet_state"] > 50, "board/bus/heartbeat traffic must be recognised"
    assert (
        result["fleet_state"] + result["unfiled"] + result["miswrites"]
        == result["total"]
    ), "every dirty path must land in exactly one tier"
    assert result["red"] == bool(result["miswrites"] or result["unfiled"])
