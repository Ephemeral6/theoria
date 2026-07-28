"""Offline tests for the local-engine guard. No API, no network, no cache touched.

Every check here has a negative control, and the ones that matter most are the
ones asserting the guard goes RED. A whitelist that has never been seen to
refuse is not evidence that anything was contained -- `SCHEMA_PATH_A.md` §3.1 is
the case where a whitelist silently classified all 165 wanted files as unknown,
and only an assertion about the numbers caught it.

The `BYPASS` block near the bottom is the regression suite for an adversarial
review that ran against the first version of this guard and confirmed nine
working bypasses. Each one is now a named test. They are kept as a block because
the lesson generalises: the holes were not in the sealed-name matcher (which
held) but in the *reach* of the trigger list, in argv flattening, and in Python
truthiness -- i.e. everywhere except where the design attention had gone.

    cd arc-recon && python -m pytest test_local_engine_guard.py
"""

import json
import os

import pytest

import local_engine_guard as guard
from local_engine_guard import (
    ALLOW,
    DENY_DEFAULT_ALL,
    DENY_SEALED,
    DENY_UNFILTERED,
    DENY_UNKNOWN,
    LocalEngineRefusal,
)


IDX = guard.piles_index()
DEV = IDX["dev"]
SEALED = IDX["sealed"]

# The one invocation that upstream documents a filter for. `make play-local` is
# NOT here: no filter argument is documented for it -- see UNFILTERABLE_TARGETS.
FILTERED = "uv run main.py --agent=random --game=%s"


def verdict(command):
    return guard.classify_command(command)["verdict"]


# -- the cut itself ---------------------------------------------------------

def test_the_shipped_cut_hashes_to_the_value_claude_md_pins():
    doc = guard.load_piles()
    assert guard.cut_digest(doc) == guard.DECLARED_CUT_SHA256
    assert doc["sha256"] == guard.DECLARED_CUT_SHA256
    assert len(doc["dev_pile"]) == 4
    assert len(doc["sealed_pile"]) == 21


def test_a_tampered_cut_refuses_everything(tmp_path):
    doc = guard.load_piles()
    doc["dev_pile"] = doc["dev_pile"] + [doc["sealed_pile"][0]]   # widen the cut
    path = tmp_path / "piles.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    with pytest.raises(LocalEngineRefusal) as exc:
        guard.load_piles(str(path))
    assert "no longer hashes" in str(exc.value)


def test_a_missing_cut_refuses_rather_than_defaulting(tmp_path):
    with pytest.raises(LocalEngineRefusal):
        guard.load_piles(str(tmp_path / "absent.json"))


def test_unreadable_cut_makes_the_cli_exit_two(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "PILES_PATH", str(tmp_path / "absent.json"))
    assert guard.main(["check", "--", "uv", "run", "main.py", "--game=ar25"]) == 2


# -- rule 4: every sealed game, in every shape ------------------------------

TEMPLATES = (
    "uv run main.py --agent=random --game=%s",
    "uv run main.py --agent=random --game %s",
    'python -c \'import arc_agi_3; arc.make("%s")\'',
    "cat environment_files/%s/rules.py",
    "curl https://arcprize.org/tasks/%s",
    "uv run main.py --agent=x --game=%s,ar25",      # sealed alongside a dev game
)


@pytest.mark.parametrize("sealed", SEALED)
def test_every_sealed_game_is_refused_full_and_prefix(sealed):
    short = sealed.split("-")[0]
    for template in TEMPLATES:
        assert verdict(template % sealed) == DENY_SEALED, template
        assert verdict(template % short) == DENY_SEALED, template
        assert verdict(template % sealed.upper()) == DENY_SEALED, template


@pytest.mark.parametrize("dev", DEV)
def test_every_development_game_is_allowed_full_and_prefix(dev):
    short = dev.split("-")[0]
    assert verdict(FILTERED % dev) == ALLOW
    assert verdict(FILTERED % short) == ALLOW
    assert verdict("uv run main.py --agent=x --game %s" % short) == ALLOW


def test_the_whole_development_pile_at_once_is_allowed():
    assert verdict(FILTERED % ",".join(DEV)) == ALLOW
    assert verdict(FILTERED % ",".join(g.split("-")[0] for g in DEV)) == ALLOW


def test_one_sealed_game_among_four_development_ones_still_refuses():
    tokens = [g.split("-")[0] for g in DEV] + [SEALED[0].split("-")[0]]
    assert verdict(FILTERED % ",".join(tokens)) == DENY_SEALED


# -- rule 1: the default is the dangerous case ------------------------------

@pytest.mark.parametrize("command", [
    "uv run main.py --agent=random",
    "uv run main.py --agent=langgraph_random",
    "python main.py --agent=random --tags=demo",
    "ls environment_files/",
    "rm -rf environment_files",
])
def test_an_unfiltered_local_engine_command_is_refused(command):
    assert verdict(command) == DENY_DEFAULT_ALL


@pytest.mark.parametrize("target", ["play-local", "list-games", "verify-local"])
def test_the_unfilterable_targets_are_refused_outright(target):
    result = guard.classify_command("make " + target)
    assert result["verdict"] == DENY_UNFILTERED
    assert result["reasons"], "a refusal with no reason is not usable"


@pytest.mark.parametrize("command", [
    "make list-games GAME=ar25",
    "make verify-local GAME=ar25",
    "make play-local GAME=ar25",
])
def test_naming_a_dev_game_does_not_rescue_an_unfilterable_target(command):
    assert verdict(command) == DENY_UNFILTERED


# -- rule 2: the selector must be exact -------------------------------------

@pytest.mark.parametrize("token", ["s", "a", "", "*", "all", "public", "ar", "ar255", "ar25x"])
def test_a_loose_selector_token_is_refused(token):
    assert guard.classify_selector_token(token)[0] in (DENY_UNKNOWN, DENY_SEALED)


def test_a_loose_selector_token_refuses_the_whole_command():
    # `--game=s` would widen to sk48 AND five sealed games (s5i5, sb26, sc25,
    # sp80, su15). Upstream reads the value as a prefix, so this is the real
    # shape of the risk, not a hypothetical one.
    assert verdict("uv run main.py --agent=x --game=s") == DENY_UNKNOWN


def test_quoted_and_spaced_selector_forms_are_all_parsed():
    assert guard.selector_tokens('--game="ar25,g50t"') == ["ar25", "g50t"]
    assert guard.selector_tokens("--game ar25") == ["ar25"]
    assert guard.selector_tokens("GAME=ar25") == ["ar25"]
    assert guard.selector_tokens("--games=ar25,g50t") == ["ar25", "g50t"]


# -- boundary anchoring: SCHEMA_PATH_A §3.1's failure, in this guard ---------

@pytest.mark.parametrize("text", [
    "blobs/9ar25f0e/data.bin",
    "cache/xxar25xx.json",
    "logs/ar25f0e1.txt",
    "runs/9ls20a/frame.json",       # a sealed prefix buried mid-hash
])
def test_a_prefix_buried_in_a_hash_does_not_read_as_a_game(text):
    assert guard.classify_name(text)[0] == DENY_UNKNOWN


@pytest.mark.parametrize("text", [
    "environment_files/ar25-0c556536/rules.py",
    "environment_files/ar25/rules.py",
    "ar25_frames.jsonl",
    "summary.ar25.json",
])
def test_a_properly_delimited_prefix_does_read_as_a_game(text):
    assert guard.classify_name(text)[0] == ALLOW


def test_the_two_piles_prefixes_are_disjoint_and_unnested():
    # Prefix matching is only safe under this premise, so it is a test, not a note.
    dev_p, sealed_p = set(IDX["dev_prefix"]), set(IDX["sealed_prefix"])
    assert not (dev_p & sealed_p)
    for d in dev_p:
        for s in sealed_p:
            assert not d.startswith(s) and not s.startswith(d)
    assert len(dev_p) == 4 and len(sealed_p) == 21


# -- rule 4 as a catch-all --------------------------------------------------

def test_a_sealed_game_is_refused_even_outside_a_known_runner():
    assert verdict("curl https://arcprize.org/tasks/ls20") == DENY_SEALED
    assert verdict("open https://arcprize.org/scorecards/re86-8af5384d") == DENY_SEALED


def test_an_unrelated_command_gets_no_opinion():
    result = guard.classify_command("python -m pytest -q")
    assert result["verdict"] == ALLOW
    assert result["triggers"] == []


# ==========================================================================
# BYPASS -- regressions for the nine holes an adversarial review confirmed
# against the first version of this guard. Each was a working `allow`.
# ==========================================================================

@pytest.mark.parametrize("command", [
    "make -C ARC-AGI-3-Agents play-local",
    "make -f Makefile play-local",
    "make -s play-local",
    "make -j4 play-local",
    "make --directory=agents play-local",
    "gmake play-local",
    "mingw32-make play-local",
    "make -C agents list-games",
])
def test_bypass_make_flags_between_make_and_the_target(command):
    """The trigger anchored on `make\\s+<target>`; any make flag broke it.

    There is no Makefile in this repo, so the upstream agent repo has to be a
    subdirectory and `make -C <dir> play-local` is the *natural* invocation --
    the bypass was more likely than the form the guard recognised.
    """
    assert verdict(command) == DENY_UNFILTERED


def test_bypass_a_generator_of_game_ids_failed_open():
    """`if not game_ids` is false for any generator, so the refusal was skipped.

    `[g for g in cfg if want(g)]` is safe; `(g for g in cfg if want(g))` -- the
    same expression without brackets -- returned an empty allowlist and the
    caller then pulled with no filter. Invisible at the call site, which is what
    made it the worst of the nine.
    """
    with pytest.raises(LocalEngineRefusal):
        guard.assert_local_pull_allowed(g for g in [])
    with pytest.raises(LocalEngineRefusal):
        guard.assert_local_pull_allowed(filter(None, []))
    with pytest.raises(LocalEngineRefusal):
        guard.assert_local_pull_allowed(x for x in [] if x)


def test_bypass_play_local_with_an_invented_variable():
    """`GAME=` was a spelling this guard invented; no filter is documented.

    `browser-ops/TERMS.md` §4.2 documents `--game` for the swarm runner only,
    and `make play-local` as "Runs your agent against every game in the
    dataset" with no argument. make accepts an unreferenced variable override
    silently, so a Makefile that ignores `GAME` plays all 25 while the command
    line looks filtered -- and looking filtered is worse than looking dangerous.
    """
    for command in ("make play-local GAME=ar25",
                    "make play-local GAMES=ar25",
                    "make play-local -g ar25",
                    "make play-local GAME=ar25-0c556536"):
        assert verdict(command) == DENY_UNFILTERED, command


@pytest.mark.parametrize("command", [
    "uv run main.py --agent=x --game=ar25 && uv run main.py",
    "uv run main.py --agent=x --game=ar25 ; uv run main.py",
    "uv run main.py --agent=x --game=ar25 & uv run main.py",
    "uv run main.py --agent=x --game=ar25 || uv run main.py",
    "uv run main.py --agent=x --game=ar25\nuv run main.py",
    "bash -c echo --game=ar25 && uv run main.py --agent=x",
    'uv run main.py --agent=x "#" --game=ar25',
    "uv run main.py --agent=x # --game=ar25",
])
def test_bypass_one_dev_token_licensing_a_whole_chained_line(command):
    """argv was flattened to one string, so a token in *any* statement counted.

    It even counted from inside an echoed string or behind a comment marker.
    Each segment is now judged alone and the most severe verdict wins.
    """
    assert verdict(command) != ALLOW


@pytest.mark.parametrize("command", [
    "uv run main.py --agent=x --game=ar25 --game=",
    'uv run main.py --agent=x --game=ar25 --game=""',
    "uv run main.py --agent=x --game ar25 all",
    "uv run main.py --agent=x --game ar25 *",
    "uv run main.py --agent=x --game",
])
def test_bypass_selector_values_that_only_look_like_a_filter(command):
    """Empty values were dropped instead of refused; extra values never classified.

    With last-wins flag semantics `--game=ar25 --game=` is an empty filter, i.e.
    all 25 games, wearing the costume of a filtered run.
    """
    assert verdict(command) in (DENY_UNKNOWN, DENY_SEALED)


@pytest.mark.parametrize("command", [
    "uv run main.py",
    "python main.py --config=run.yaml",
    "python main.py -a random",
    "python -m main --agent=random",
    "python -m agents.main --agent=x",
    "python swarm_runner.py --agent=random",
])
def test_bypass_swarm_runner_forms_that_missed_the_trigger(command):
    """The trigger needed `main.py` AND `--agent` on the same line.

    `uv run main.py` is the documented quickstart minus one flag; the runner
    surely has a default agent. `main.py` alone is now the trigger, which is
    safe because an unfiltered run denies by default anyway.
    """
    assert verdict(command) == DENY_DEFAULT_ALL


@pytest.mark.parametrize("command", [
    "python -c 'import arc_agi_3'",
    "python -c 'from arc_agi_3.arcade import Arcade'",
    "pip install arc-agi-3-agents",
])
def test_bypass_the_package_name_the_trigger_could_never_match(command):
    """`arc_agi` fired only when followed by a non-word char -- never for `arc_agi_3`.

    A trigger anchored so tightly that it excludes the real spelling of the
    thing it guards is not a loose trigger, it is an absent one.
    """
    assert verdict(command) != ALLOW


@pytest.mark.parametrize("command", [
    "curl https://arcprize.org/tasks/LS20",
    "wget https://x/LS20-9607627B.zip",
    "python -c 'arc.make(\"Ls20\")'",
])
def test_bypass_a_capitalised_sealed_id(command):
    """Matching was case-sensitive, so a shouted URL defeated the rule-4 catch-all."""
    assert verdict(command) == DENY_SEALED


@pytest.mark.parametrize("command", ["ls ENVIRONMENT_FILES", "ls Environment_Files"])
def test_bypass_a_capitalised_cache_path(command):
    assert verdict(command) != ALLOW


def test_bypass_an_empty_sealed_directory_read_as_clean(tmp_path):
    """`os.walk` was consumed for filenames only, so directory names were never judged.

    An interrupted download leaves `environment_files/<sealed-id>/` holding
    nothing, and a files-only sweep called that clean.
    """
    root = tmp_path / "environment_files"
    (root / "ls20-9607627b").mkdir(parents=True)
    report = guard.scan_dir(str(root))
    assert report["clean"] is False
    assert report["counts"][DENY_SEALED] == 1


def test_bypass_scanning_a_file_rather_than_a_directory(tmp_path):
    """`os.path.isdir` false meant `exists: False, clean: True` -- a sealed file
    handed to `scan` directly reported clean."""
    root = tmp_path / "environment_files" / "ls20-9607627b"
    root.mkdir(parents=True)
    target = root / "game.py"
    target.write_text("SEALED SOURCE", encoding="utf-8")
    report = guard.scan_dir(str(target))
    assert report["exists"] is True
    assert report["clean"] is False
    assert guard.main(["scan", str(target)]) == 2


def test_bypass_json_flag_stolen_from_the_child_command(monkeypatch):
    """`--json` was stripped from anywhere in argv, including the child's own flags."""
    called = []
    monkeypatch.setattr(guard.subprocess, "call", lambda argv: called.append(argv) or 0)
    assert guard.main(["run", "--", "uv", "run", "main.py", "--game=ar25", "--json"]) == 0
    assert called == [["uv", "run", "main.py", "--game=ar25", "--json"]]


@pytest.mark.parametrize("value", [None, b"make play-local", 17])
def test_a_non_string_command_refuses_rather_than_crashing(value):
    """These crashed with TypeError -- fail-closed by accident, but a caller
    catching LocalEngineRefusal would not have seen a refusal."""
    with pytest.raises(LocalEngineRefusal):
        guard.classify_command(value)


def test_a_non_string_game_id_refuses_rather_than_crashing():
    with pytest.raises(LocalEngineRefusal):
        guard.assert_local_pull_allowed(["ar25", None])
    with pytest.raises(LocalEngineRefusal):
        guard.assert_local_pull_allowed("ar25")     # a bare string, not a sequence


# -- the programmatic entry point -------------------------------------------

def test_a_pull_with_no_game_list_is_refused():
    with pytest.raises(LocalEngineRefusal) as exc:
        guard.assert_local_pull_allowed(None)
    assert DENY_DEFAULT_ALL in str(exc.value)
    with pytest.raises(LocalEngineRefusal):
        guard.assert_local_pull_allowed([])


def test_a_pull_of_the_development_pile_resolves_to_full_ids():
    assert guard.assert_local_pull_allowed(["ar25", "g50t"]) == [
        "ar25-0c556536", "g50t-5849a774",
    ]


@pytest.mark.parametrize("sealed", SEALED)
def test_a_pull_naming_any_sealed_game_raises(sealed):
    with pytest.raises(LocalEngineRefusal):
        guard.assert_local_pull_allowed([sealed])
    with pytest.raises(LocalEngineRefusal):
        guard.assert_local_pull_allowed(["ar25", sealed.split("-")[0]])


def test_assert_command_allowed_raises_and_names_the_verdict():
    with pytest.raises(LocalEngineRefusal) as exc:
        guard.assert_command_allowed(["make", "play-local"])
    assert DENY_UNFILTERED in str(exc.value)
    guard.assert_command_allowed(["uv", "run", "main.py", "--game=ar25"])   # control


# -- the cache sweep, which reads names and never bytes ---------------------

def test_a_cache_holding_only_development_games_is_clean(tmp_path):
    root = tmp_path / "environment_files"
    (root / "ar25-0c556536").mkdir(parents=True)
    (root / "ar25-0c556536" / "game.py").write_text("x", encoding="utf-8")
    (root / "g50t-5849a774").mkdir()
    (root / "g50t-5849a774" / "game.py").write_text("x", encoding="utf-8")
    report = guard.scan_dir(str(root))
    assert report["clean"] is True
    assert report["counts"][ALLOW] == 4        # two directories and two files


def test_a_cache_holding_a_sealed_game_is_refused(tmp_path):
    root = tmp_path / "environment_files"
    (root / "ls20-9607627b").mkdir(parents=True)
    (root / "ls20-9607627b" / "game.py").write_text("SEALED SOURCE", encoding="utf-8")
    report = guard.scan_dir(str(root))
    assert report["clean"] is False
    assert report["counts"][DENY_SEALED] == 2  # the directory and the file under it
    assert guard.main(["scan", str(root)]) == 2


def test_an_unrecognised_file_is_refused_not_ignored(tmp_path):
    root = tmp_path / "environment_files"
    root.mkdir(parents=True)
    (root / "README.md").write_text("x", encoding="utf-8")
    report = guard.scan_dir(str(root))
    assert report["clean"] is False
    assert report["counts"][DENY_UNKNOWN] == 1


def test_the_sweep_never_opens_a_file(tmp_path, monkeypatch):
    root = tmp_path / "environment_files"
    (root / "ls20-9607627b").mkdir(parents=True)
    (root / "ls20-9607627b" / "game.py").write_text("SEALED SOURCE", encoding="utf-8")

    real_open = open
    opened = []

    def watched(path, *args, **kwargs):
        opened.append(str(path))
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", watched)
    guard.scan_dir(str(root))
    assert not [p for p in opened if str(root) in p], (
        "the guard opened a file under the cache it was refusing: %s" % opened
    )


def test_a_missing_cache_is_not_an_error(tmp_path):
    report = guard.scan_dir(str(tmp_path / "nothing-here"))
    assert report["exists"] is False and report["clean"] is True
    assert guard.main(["scan", str(tmp_path / "nothing-here")]) == 0


def test_several_cache_roots_are_swept_and_the_worst_wins(tmp_path):
    clean = tmp_path / "a" / "environment_files"
    (clean / "ar25-0c556536").mkdir(parents=True)
    dirty = tmp_path / "b" / "environment_files"
    (dirty / "ls20-9607627b").mkdir(parents=True)
    assert guard.main(["scan", str(clean)]) == 0
    assert guard.main(["scan", str(clean), str(dirty)]) == 2


# -- the CLI contract a scheduler reads -------------------------------------

@pytest.mark.parametrize("argv,code", [
    (["check", "--", "make", "play-local"], 2),
    (["check", "--", "make", "list-games"], 2),
    (["check", "--", "uv", "run", "main.py", "--agent=random"], 2),
    (["check", "--", "uv", "run", "main.py", "--game=ls20"], 2),
    (["check", "--", "uv", "run", "main.py", "--game=ar25"], 0),
    (["check", "--json", "--", "uv", "run", "main.py", "--game=ar25"], 0),
    (["selftest"], 0),
    ([], 1),
    (["check"], 1),
    (["nonsense"], 1),
])
def test_cli_exit_codes(argv, code):
    assert guard.main(argv) == code


def test_run_refuses_without_executing(monkeypatch):
    called = []
    monkeypatch.setattr(guard.subprocess, "call", lambda argv: called.append(argv) or 0)
    assert guard.main(["run", "--", "make", "play-local"]) == 2
    assert called == [], "a refused command reached subprocess.call"


def test_run_executes_only_once_the_selector_is_clean(monkeypatch):
    called = []
    monkeypatch.setattr(guard.subprocess, "call", lambda argv: called.append(argv) or 0)
    assert guard.main(["run", "--", "uv", "run", "main.py", "--game=ar25"]) == 0
    assert called == [["uv", "run", "main.py", "--game=ar25"]]


# -- the guard's own claims -------------------------------------------------

def test_selftest_is_green():
    assert guard.selftest() == []
