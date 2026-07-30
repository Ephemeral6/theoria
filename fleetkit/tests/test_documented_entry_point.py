"""S42 defect 3: the first command in both documents did not exist.

`README.md` line 13 and `fleetkit/__init__.py` line 8 both open with

    python -m fleetkit init --prefix MyFleet-

and `fleetkit/fleetkit/__main__.py` was not in the package, so that command --
the first thing anybody deploying the kit types -- died with
`No module named fleetkit.__main__; 'fleetkit' is a package and cannot be
directly executed`.

`verify.py` did not see it because it called `config.write_default()` directly
instead of the CLI. That is the deeper half of this defect: the gate was green
on top of a front door that had never once been opened. A gate that cannot see
a broken entry point is not measuring the thing the README promises.

These tests run the documented commands as written, as subprocesses. Nothing
here imports its way around the CLI, because importing your way around the CLI
is exactly how the CLI got to stay broken.
"""

import json
import os
import subprocess
import sys

import pytest

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KIT)

from fleetkit import config                                     # noqa: E402


def _run(args, cwd, env_extra=None, expect=0):
    env = dict(os.environ)
    env["PYTHONPATH"] = KIT + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("FLEET_HOME", None)
    env.pop("FLEET_ROOT", None)
    if env_extra:
        env.update(env_extra)
    r = subprocess.run([sys.executable, "-m", "fleetkit"] + list(args),
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=env, cwd=str(cwd))
    assert r.returncode == expect, (args, r.returncode, r.stdout, r.stderr)
    return r.stdout + r.stderr


def _documented_lines(path, token):
    """Every fenced/indented line of a document that invokes the CLI."""
    text = open(path, encoding="utf-8").read()
    return [l.strip() for l in text.splitlines() if l.strip().startswith(token)]


# --------------------------------------------------- the command as written

def test_the_readme_first_command_actually_runs(tmp_path):
    """`python -m fleetkit init --prefix MyFleet-`, verbatim, in a fresh repo.

    Pre-S42: `No module named fleetkit.__main__`, exit 1.
    """
    root = tmp_path / "newproject"
    root.mkdir()

    out = _run(["init", "--prefix", "MyFleet-"], cwd=root)

    assert "No module named" not in out, out
    cfg_path = root / config.CONFIG_NAME
    assert cfg_path.exists(), (
        "the documented init command left no %s: %s" % (config.CONFIG_NAME, out))
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert data["task_prefix"] == "MyFleet-"
    assert config.load(str(root)).task_prefix == "MyFleet-"


def test_the_documented_board_and_bus_verbs_run(tmp_path):
    """`python -m fleetkit board list` and `... bus say`, as documented."""
    root = tmp_path / "newproject"
    (root / "src").mkdir(parents=True)
    (root / "docs").mkdir()
    _run(["init", "--prefix", "MyFleet-"], cwd=root)
    home = root / ".fleet"
    home.mkdir()
    env = {"FLEET_HOME": str(home)}

    out = _run(["board", "list"], cwd=root, env_extra=env)
    assert "available" in out, out

    out = _run(["bus", "say", "RES-1", "a message"], cwd=root, env_extra=env)
    assert os.path.exists(home / "bus" / "RES-1" / "out.jsonl"), out


def test_every_cli_line_the_readme_prints_is_a_verb_that_exists():
    """The documents and the code, checked against each other rather than by
    eye. A README command that no longer parses is the same defect again."""
    readme = os.path.join(KIT, "README.md")
    init_py = os.path.join(KIT, "fleetkit", "__init__.py")
    lines = (_documented_lines(readme, "python -m fleetkit")
             + _documented_lines(init_py, "python -m fleetkit"))
    assert lines, "neither document shows a single invocation any more"

    from fleetkit import __main__ as entry
    known = {"init", "board", "bus"}
    for line in lines:
        verb = line.split()[3]              # python -m fleetkit <verb> ...
        assert verb in known, "%r documents an unknown verb %r" % (line, verb)
    assert hasattr(entry, "main")


def test_the_two_ways_of_naming_the_board_are_the_same_command(tmp_path):
    """`python -m fleetkit board` and `python -m fleetkit.board` must not be
    allowed to drift apart -- one of them rotting unnoticed is this defect."""
    root = tmp_path / "newproject"
    (root / "src").mkdir(parents=True)
    _run(["init", "--prefix", "MyFleet-", "--territories", "src"], cwd=root)
    home = root / ".fleet"
    home.mkdir()
    env = dict(os.environ)
    env["PYTHONPATH"] = KIT + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONIOENCODING"] = "utf-8"
    env["FLEET_HOME"] = str(home)

    outs = []
    for argv in (["-m", "fleetkit", "board", "list"],
                 ["-m", "fleetkit.board", "list"]):
        r = subprocess.run([sys.executable] + argv, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           env=env, cwd=str(root))
        assert r.returncode == 0, (argv, r.stdout, r.stderr)
        outs.append(r.stdout)
    assert outs[0] == outs[1], outs


# ------------------------------------------------------------ how it refuses

def test_init_refuses_to_silently_overwrite_an_existing_fleet(tmp_path):
    """task_prefix is the fleet's identity: overwrite it and every worker
    already running under the old one reads as dead on the next sweep."""
    root = tmp_path / "newproject"
    root.mkdir()
    _run(["init", "--prefix", "First-"], cwd=root)

    out = _run(["init", "--prefix", "Second-"], cwd=root, expect=2)

    assert "INIT-REFUSED" in out, out
    assert config.load(str(root)).task_prefix == "First-"
    _run(["init", "--prefix", "Second-", "--force"], cwd=root)
    assert config.load(str(root)).task_prefix == "Second-"


def test_an_unknown_verb_is_refused_rather_than_ignored(tmp_path):
    out = _run(["frobnicate"], cwd=tmp_path, expect=2)
    assert "unknown verb" in out, out


def test_init_refuses_a_config_that_would_not_validate(tmp_path):
    """An empty prefix is the field whose silent default reports every worker
    dead, so the front door must refuse it too, not only `config.load`."""
    root = tmp_path / "newproject"
    root.mkdir()

    out = _run(["init", "--prefix", "P-", "--territories", ","], cwd=root,
               expect=2)

    assert "INIT-REFUSED" in out, out
    assert not (root / config.CONFIG_NAME).exists()


def test_everything_the_entry_point_prints_survives_cp936():
    from fleetkit import __main__ as entry
    for text in (entry.__doc__, entry.cmd_init.__doc__):
        text.encode("cp936")
