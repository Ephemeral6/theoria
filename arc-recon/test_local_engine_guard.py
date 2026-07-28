"""Offline tests for the local-engine guard. No API, no network, no cache touched.

Every check here has a negative control, and the ones that matter most are the
ones asserting the guard goes RED. A whitelist that has never been seen to
refuse is not evidence that anything was contained -- `SCHEMA_PATH_A.md` §3.1 is
the case where a whitelist silently classified all 165 wanted files as unknown,
and only an assertion about the numbers caught it.

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
    assert guard.main(["check", "--", "make", "play-local", "GAME=ar25"]) == 2


# -- rule 1/2: every sealed game, in every shape ----------------------------

TEMPLATES = (
    "make play-local GAME=%s",
    "uv run main.py --agent=random --game=%s",
    "uv run main.py --agent=random --game %s",
    'python -c \'import arc_agi; arc.make("%s")\'',
    "cat environment_files/%s/rules.py",
    "make play-local GAME=%s,ar25",          # sealed alongside a dev game
)


@pytest.mark.parametrize("sealed", SEALED)
def test_every_sealed_game_is_refused_full_and_prefix(sealed):
    short = sealed.split("-")[0]
    for template in TEMPLATES:
        assert verdict(template % sealed) == DENY_SEALED, template
        assert verdict(template % short) == DENY_SEALED, template


@pytest.mark.parametrize("dev", DEV)
def test_every_development_game_is_allowed_full_and_prefix(dev):
    short = dev.split("-")[0]
    assert verdict("make play-local GAME=%s" % dev) == ALLOW
    assert verdict("make play-local GAME=%s" % short) == ALLOW
    assert verdict("uv run main.py --agent=x --game=%s" % dev) == ALLOW
    assert verdict("uv run main.py --agent=x --game %s" % short) == ALLOW


def test_the_whole_development_pile_at_once_is_allowed():
    assert verdict("uv run main.py --agent=x --game=%s" % ",".join(DEV)) == ALLOW
    assert verdict(
        "uv run main.py --agent=x --game=%s" % ",".join(g.split("-")[0] for g in DEV)
    ) == ALLOW


def test_one_sealed_game_among_four_development_ones_still_refuses():
    tokens = [g.split("-")[0] for g in DEV] + [SEALED[0].split("-")[0]]
    assert verdict("make play-local GAME=%s" % ",".join(tokens)) == DENY_SEALED


# -- rule 1: the default is the dangerous case ------------------------------

@pytest.mark.parametrize("command", [
    "make play-local",
    "make play",
    "uv run main.py --agent=random",
    "uv run main.py --agent=langgraph_random",
    "python main.py --agent=random --tags=demo",
    "ls environment_files/",
    "rm -rf environment_files",
])
def test_an_unfiltered_local_engine_command_is_refused(command):
    assert verdict(command) == DENY_DEFAULT_ALL


@pytest.mark.parametrize("target,expected", [
    ("make list-games", DENY_UNFILTERED),
    ("make verify-local", DENY_UNFILTERED),
])
def test_the_unfilterable_targets_are_refused_outright(target, expected):
    result = guard.classify_command(target)
    assert result["verdict"] == expected
    assert result["reasons"], "a refusal with no reason is not usable"


def test_naming_a_dev_game_does_not_rescue_list_games():
    # list-games takes no filter; a GAME= on the line is decoration, not a filter.
    assert verdict("make list-games GAME=ar25") == DENY_UNFILTERED


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


# -- rule 4: a sealed name anywhere, trigger or not -------------------------

def test_a_sealed_game_is_refused_even_outside_a_known_runner():
    assert verdict("curl https://arcprize.org/tasks/ls20") == DENY_SEALED
    assert verdict("open https://arcprize.org/scorecards/re86-8af5384d") == DENY_SEALED


def test_an_unrelated_command_gets_no_opinion():
    result = guard.classify_command("python -m pytest -q")
    assert result["verdict"] == ALLOW
    assert result["triggers"] == []


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
    assert DENY_DEFAULT_ALL in str(exc.value)
    guard.assert_command_allowed(["make", "play-local", "GAME=ar25"])   # control


# -- the cache sweep, which reads names and never bytes ---------------------

def test_a_cache_holding_only_development_games_is_clean(tmp_path):
    root = tmp_path / "environment_files"
    (root / "ar25-0c556536").mkdir(parents=True)
    (root / "ar25-0c556536" / "game.py").write_text("x", encoding="utf-8")
    (root / "g50t-5849a774").mkdir()
    (root / "g50t-5849a774" / "game.py").write_text("x", encoding="utf-8")
    report = guard.scan_dir(str(root))
    assert report["clean"] is True
    assert report["counts"][ALLOW] == 2


def test_a_cache_holding_a_sealed_game_is_refused(tmp_path):
    root = tmp_path / "environment_files"
    (root / "ls20-9607627b").mkdir(parents=True)
    (root / "ls20-9607627b" / "game.py").write_text("SEALED SOURCE", encoding="utf-8")
    report = guard.scan_dir(str(root))
    assert report["clean"] is False
    assert report["counts"][DENY_SEALED] == 1
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


# -- the CLI contract a scheduler reads -------------------------------------

@pytest.mark.parametrize("argv,code", [
    (["check", "--", "make", "play-local"], 2),
    (["check", "--", "make", "list-games"], 2),
    (["check", "--", "uv", "run", "main.py", "--agent=random"], 2),
    (["check", "--", "make", "play-local", "GAME=ls20"], 2),
    (["check", "--", "make", "play-local", "GAME=ar25"], 0),
    (["check", "--json", "--", "make", "play-local", "GAME=ar25"], 0),
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
    assert guard.main(["run", "--", "make", "play-local", "GAME=ar25"]) == 0
    assert called == [["make", "play-local", "GAME=ar25"]]


# -- the guard's own claims -------------------------------------------------

def test_selftest_is_green():
    assert guard.selftest() == []
