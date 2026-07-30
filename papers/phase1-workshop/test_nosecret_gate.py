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

import os
import re
import shutil
import subprocess
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


def run_d(tmp_path, monkeypatch, files: dict[str, str], env: str | None = None,
          min_scanned: int = 1):
    """`check_nosecret()` over a synthetic published tree.

    `HERE` and `ROOT` are module globals resolved at import, so they are
    redirected rather than the real tree copied -- the same technique the
    delegator's suite uses, and it keeps every case in a `tmp_path`.

    `MIN_SCANNED` is redirected too, and for the same reason: it is a floor on a
    real paper directory (40, against 165 tracked files), and every tree here is
    two or three files by design -- a case that wants to isolate one matcher
    should not have to fabricate forty documents to get past the floor. The floor
    itself is exercised at its real value in
    `test_a_collapsed_scan_is_a_broken_check_not_a_clean_tree`, which passes
    `min_scanned=vp.MIN_SCANNED`; leaving it out of *these* cases is the same
    trade `HERE` makes, not an exemption from it."""
    monkeypatch.setattr(vp, "MIN_SCANNED", min_scanned)
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


#: Real git, or the scope cases cannot run at all. They build their own
#: repository in `tmp_path` rather than leaning on the live `.pytest_cache`:
#: that directory is the bug's exhibit, but a suite that needs it is a suite
#: that only passes on the second run, and on the machine that ran it.
GIT = shutil.which("git")
needs_git = pytest.mark.skipif(GIT is None, reason="git is not on PATH")


def run_d_in_repo(tmp_path, monkeypatch, files: dict[str, str],
                  gitignore: str = "", track: tuple[str, ...] = (),
                  global_config: str | None = None,
                  local_exclude: str | None = None,
                  hostile_env: dict[str, str] | None = None,
                  min_scanned: int = 1):
    """`check_nosecret()` over a synthetic tree inside a **real** repository.

    `tmp_path` is both the repo root and `ROOT`; `tmp_path/paper` is `HERE`,
    exactly as in `run_d`. Names in `track` are staged, which is all "tracked"
    means to `git check-ignore` -- it consults the index, and that is the
    guarantee that keeps a tracked file in scope however many patterns match it.

    Global and system git config are pointed at files that do not exist, so that
    whoever runs this suite cannot change its verdict from their own
    `core.excludesFile`. A scope test whose answer depends on the reader's
    dotfiles is not a test. `global_config` overrides that with a real config
    file, which is how the pinning inside `_git_env()` gets tested rather than
    merely mirrored: the *test* hands git a hostile global config and the
    *implementation* has to be the thing that refuses it.

    `local_exclude` writes `$GIT_DIR/info/exclude`, the ignore surface no
    environment variable can switch off.

    `hostile_env` is applied **after** the repository is built, and that ordering
    is load-bearing rather than tidy. Setting `GIT_INDEX_FILE` before `git add`
    writes the index to the attacker's path, so the file is never staged, so the
    test fails for the wrong reason and would go on failing after the hole was
    closed. Attacks go in here, not in the test body: the hostile condition has to
    apply to the code under test and to nothing else.
    """
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(tmp_path / "no-global-config"))
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", str(tmp_path / "no-system-config"))
    monkeypatch.setattr(vp, "MIN_SCANNED", min_scanned)
    here = tmp_path / "paper"
    here.mkdir()
    (tmp_path / ".gitignore").write_text(gitignore, encoding="utf-8")
    for name, body in files.items():
        p = here / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")

    def git(*args):
        r = subprocess.run([GIT, *args], cwd=str(tmp_path),
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert r.returncode == 0, "git %s: %s" % (
            " ".join(args), r.stdout.decode("utf-8", "replace"))

    git("init", "-q")
    for name in track:
        git("add", "-f", "--", "paper/" + name)
    if local_exclude is not None:
        info = tmp_path / ".git" / "info"
        info.mkdir(parents=True, exist_ok=True)
        (info / "exclude").write_text(local_exclude, encoding="utf-8")
    if global_config is not None:
        cfg = tmp_path / "hostile-global-config"
        cfg.write_text(global_config, encoding="utf-8")
        monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(cfg))
    for k, v in (hostile_env or {}).items():
        monkeypatch.setenv(k, v)
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


# ------------------------------------------------- what is in scope at all
#
# The check's own word for what it reads is "published file(s)", and
# `CLAUDE.md` grounds it in a release manifest that publishes every *tracked*
# file. So the scan is over what git would publish. It was not: it read
# `.pytest_cache/v/cache/nodeids` -- pytest's record of the node ids of the tests
# *above*, which spell out every deliberately fake credential in this file -- and
# reported those as leaks. Red on its own negative control, on every machine
# where anyone had run the suite, and un-fixably, because the cache regenerates.
# Two checks in `verify_paper.py` already say what that ends in: a gate that is
# permanently red is a gate somebody switches off. This is the gate between the
# ARC key and the release manifest.

@needs_git
def test_a_gitignored_file_is_not_reported(tmp_path, monkeypatch):
    """The item, in one test. A gitignored path is not in the manifest and never
    will be, so a finding in it is one nobody can act on.

    `section.md` is here so that the tree is a paper directory with a cache in it
    rather than a cache on its own: with only the ignored file present the scan
    scans nothing, and `MIN_SCANNED` is entitled to red that. Both behaviours are
    wanted, and they are separated so that one cannot pass by masking the other.
    """
    ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                              {"cache/nodeids": f"ARC_API_KEY={SHAPED}",
                               "section.md": "nothing to see"},
                              gitignore="cache/\n")
    assert ok, "a gitignored file was still reported: %s" % notes
    assert "all 2 file(s) under this directory accounted for = 1 scanned + " \
        "1 skipped as gitignored under cache/" in "\n".join(notes), notes


@needs_git
def test_an_untracked_unignored_file_is_still_reported(tmp_path, monkeypatch):
    """The hole the fix must not open, and the reason the filter is on *ignored*
    rather than on *untracked*. Nothing ignores this file, so it is one `git add`
    from the manifest -- which is exactly the moment check D exists for."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                              {"fresh.md": f"ARC_API_KEY={SHAPED}"},
                              gitignore="cache/\n")
    assert not ok and "fresh.md" in "\n".join(notes), (
        "an untracked-but-publishable file fell out of scope: %s" % notes)


@needs_git
def test_a_tracked_file_is_still_reported(tmp_path, monkeypatch):
    """Unchanged, and the case the whole check is named for."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                              {"section.md": f"ARC_API_KEY={SHAPED}"},
                              track=("section.md",))
    assert not ok and "section.md" in "\n".join(notes)


@needs_git
def test_a_tracked_file_is_reported_even_when_a_pattern_matches_it(
        tmp_path, monkeypatch):
    """`git add -f` beats `.gitignore`, and then the file *is* published. The
    filter has to agree with git about that, and it does by letting
    `check-ignore` consult the index rather than matching patterns itself: an
    ignore rule is not a promise about a path already in the index. Matching
    `.gitignore` by hand would have skipped this one."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                              {"cache/forced.md": f"ARC_API_KEY={SHAPED}"},
                              gitignore="cache/\n", track=("cache/forced.md",))
    assert not ok and "forced.md" in "\n".join(notes), (
        "a force-added file is published and was not scanned: %s" % notes)


@needs_git
def test_the_green_note_says_how_many_it_skipped(tmp_path, monkeypatch):
    """Both counts, in the sentence a reader audits. A check that narrows its own
    scope silently is the defect one rung down from the one this item fixed --
    and "0 skipped" is the reading that distinguishes a clean tree from a scan
    that quietly stopped looking."""
    ok, notes = run_d_in_repo(
        tmp_path, monkeypatch,
        {"a.md": "x", "b.md": "y", "cache/c.md": "z", "cache/d.md": "w"},
        gitignore="cache/\n")
    blob = "\n".join(notes)
    assert ok, blob
    assert "2 published file(s) scanned" in blob, blob
    assert "2 skipped as gitignored" in blob, blob


@needs_git
def test_the_rule_is_ignore_status_not_a_forgiven_name(tmp_path, monkeypatch):
    """No path allowlist and no per-file exception. Put a credential in a
    directory called `.pytest_cache` in a repository that does not ignore it and
    it is still a finding: the rule is "git will not publish this", not a list of
    names. An exemption keyed on the name would be a documented place to hide the
    next key from all three scans -- which is the same hole this suite refused to
    open for its own filename, and why its fixtures are assembled at runtime."""
    ok, notes = run_d_in_repo(
        tmp_path, monkeypatch,
        {".pytest_cache/v/cache/nodeids": f"ARC_API_KEY={SHAPED}"})
    assert not ok and "nodeids" in "\n".join(notes), (
        "a name-based exemption, not an ignore-based one: %s" % notes)


@needs_git
def test_a_gitignored_dotenv_here_is_still_the_leak(tmp_path, monkeypatch):
    """The hole the ignore filter would otherwise have opened, and the sharpest
    one: root `.gitignore` ignores `.env` and `.env.*` by design, so filtering
    every mechanism by publication status would have retired the tripwire on the
    one filename this check is named after -- drop a real `.env` in here and the
    gate goes green. So the filename mechanism runs before the filter, on every
    file. Skipping a gitignored path is a judgement about publication; a
    credential file sitting in the publication directory is a finding about the
    machine, and those are different claims."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch, {".env": "ARC_API_KEY="},
                              gitignore=".env\n.env.*\n!.env.example\n")
    assert not ok and ".env" in "\n".join(notes), (
        "a gitignored .env in the publish directory went unreported: %s" % notes)


@needs_git
def test_a_gitignored_dotenv_example_is_still_allowed(tmp_path, monkeypatch):
    """The documented way to publish a variable *name* stays allowed on both
    sides of the filter."""
    ok, _ = run_d_in_repo(tmp_path, monkeypatch, {".env.example": "ARC_API_KEY="},
                          gitignore=".env\n.env.*\n!.env.example\n")
    assert ok


def test_ignore_filtering_unavailable_widens_the_scan(tmp_path, monkeypatch):
    """No `.git` anywhere above the tree -- which is what an unpacked release
    tarball is, the one tree where being wrong about scope matters most. It is
    also the shape of every other failure mode (no git on PATH, a timeout, an
    unreadable reply): each one has to mean "scan everything", never "skip
    everything". A git failure that shrinks coverage is a silent hole with an
    external trigger."""
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", tmp_path.as_posix())
    ok, notes = run_d(tmp_path, monkeypatch,
                      {"cache/nodeids": f"ARC_API_KEY={SHAPED}"})
    blob = "\n".join(notes)
    assert not ok, "a git failure silently shrank the scan: %s" % blob
    assert "WIDENED" in blob, (
        "the scan widened without saying so, which is the same audit problem "
        "read from the other side: %s" % blob)


# ------------------------------------------------- the floor under the scope
#
# Narrowing the scan re-opened the hole the rewrite closed. The original defect
# was not "the matcher was weak" -- it was a green issued over an empty loop:
# "the secret list came back empty, the loop iterated zero times, and the check
# returned True". An ignore filter is a second road to the same place. Point
# `HERE` at the wrong directory, run against a tree that never unpacked, or write
# one ignore rule that swallows the paper, and the walk collapses while the line
# on screen still reads `[PASS] D NOSECRET`.

def test_the_floor_is_a_floor_and_not_a_gesture():
    """0 or 1 would catch only a *totally* empty walk. The failure being guarded
    is a collapsed one -- a handful of files where there should be 165 -- and a
    threshold of 1 passes that happily."""
    assert vp.MIN_SCANNED > 1


def test_a_collapsed_scan_is_a_broken_check_not_a_clean_tree(tmp_path, monkeypatch):
    """The floor at its real value, on a tree with nothing wrong in it. Three
    clean files is not a clean paper, it is a scan that did not happen, and the
    two must not print the same verdict."""
    ok, notes = run_d(tmp_path, monkeypatch,
                      {"a.md": "x", "b.md": "y", "c.md": "z"},
                      min_scanned=vp.MIN_SCANNED)
    assert not ok, "3 files scanned and the gate went green: %s" % notes


def test_the_collapsed_scan_message_does_not_read_as_a_leak(tmp_path, monkeypatch):
    """Whoever reads this line at 3am must not file an incident. "0 files
    scanned" is not evidence about the tree in either direction, and reporting a
    broken instrument as a finding is the mirror image of the defect this check
    was rewritten to remove."""
    ok, notes = run_d(tmp_path, monkeypatch, {"a.md": "x"},
                      min_scanned=vp.MIN_SCANNED)
    blob = "\n".join(notes)
    assert not ok
    assert "BROKEN CHECK" in blob, blob
    assert "not a leak" in blob, blob
    assert "the scan did not happen" in blob, blob


def test_the_floor_does_not_swallow_a_real_finding(tmp_path, monkeypatch):
    """A truncated tree that also leaks reports both. The floor is an extra
    finding, not a replacement verdict -- a broken scope is no reason to drop the
    one thing the scan did manage to see."""
    ok, notes = run_d(tmp_path, monkeypatch,
                      {"leak.md": f"ARC_API_KEY={SHAPED}"},
                      min_scanned=vp.MIN_SCANNED)
    blob = "\n".join(notes)
    assert not ok
    assert "leak.md" in blob, blob
    assert "BROKEN CHECK" in blob, blob


@needs_git
def test_an_ignore_rule_that_swallows_the_tree_hits_the_floor(tmp_path, monkeypatch):
    """The route the ignore filter itself opened, end to end: one `.gitignore`
    line, every file legitimately out of scope, and without the floor a green
    reading "0 published file(s) scanned"."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                              {"a.md": "x", "b.md": "y"},
                              gitignore="*\n", min_scanned=vp.MIN_SCANNED)
    blob = "\n".join(notes)
    assert not ok, blob
    assert "BROKEN CHECK" in blob and "0 file(s) were scanned" in blob, blob


# ------------------------------------------- whose ignore rules this obeys
#
# Every case below builds the hostile condition rather than a proxy for it, and
# each attack that git honours has a control proving git honours it -- otherwise a
# green here would be indistinguishable from a git that never implemented the
# lever. All three were live against `4f28ce37` and were found by a refuter, not
# by the author.

def _raw_check_ignore(tmp_path, name, env_extra):
    """`git check-ignore` with nothing pinned: the attack as the attacker runs it.

    The controls need this. `test_..._cannot_hide_...` above each control would
    pass just as happily against a git that had never honoured the lever being
    defended against, and a defence with no demonstrated attack is a comment."""
    r = subprocess.run([GIT, "check-ignore", "-v", "--", name],
                       cwd=str(tmp_path), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True,
                       env={**os.environ, **env_extra})
    return r.returncode, r.stdout


@needs_git
def test_a_hostile_git_index_file_cannot_hide_a_tracked_file(tmp_path, monkeypatch):
    """`GIT_INDEX_FILE` at a nonexistent path makes git read an *empty* index, and
    an empty index makes a tracked file matching `*.txt` report as ignored. That
    is the whole defence of narrowing this scan -- "a tracked file is never
    skipped, because check-ignore consults the index" -- defeated from the process
    environment, which is true of `.gitignore` patterns and false of `os.environ`.
    Not exotic either: `git commit --only`, `git stash`, `git rebase`,
    `git filter-branch` and any hook running over a temporary index export it, and
    this gate is meant to run before every push."""
    ok, notes = run_d_in_repo(
        tmp_path, monkeypatch, {"leak.txt": f"ARC_API_KEY={SHAPED}"},
        gitignore="*.txt\n", track=("leak.txt",),
        hostile_env={"GIT_INDEX_FILE": str(tmp_path / "nonexistent-index")})
    assert not ok and "leak.txt" in "\n".join(notes), (
        "GIT_INDEX_FILE emptied the index and a tracked leak fell out of the "
        "scan: %s" % notes)


@needs_git
def test_the_hostile_git_index_file_would_otherwise_have_worked(tmp_path):
    """Control for the attack above."""
    (tmp_path / ".gitignore").write_text("*.txt\n", encoding="utf-8")
    (tmp_path / "leak.txt").write_text("x", encoding="utf-8")
    subprocess.run([GIT, "init", "-q"], cwd=str(tmp_path), check=True)
    subprocess.run([GIT, "add", "-f", "--", ".gitignore", "leak.txt"],
                   cwd=str(tmp_path), check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    rc_honest, _ = _raw_check_ignore(tmp_path, "leak.txt", {})
    rc_attack, out = _raw_check_ignore(
        tmp_path, "leak.txt", {"GIT_INDEX_FILE": str(tmp_path / "nonexistent")})
    assert rc_honest == 1, "the index is not being consulted at all: %s" % out
    assert rc_attack == 0, (
        "GIT_INDEX_FILE does not empty the index on this git, so the test above "
        "proves nothing: %s" % out)


@needs_git
def test_a_global_excludesfile_cannot_hide_a_leak(tmp_path, monkeypatch):
    """`core.excludesFile` in somebody's `~/.gitconfig` is an ignore rule this
    check would otherwise obey -- one line in a file that is not in the
    repository, not in review, and not on the next machine, and a leaking file
    leaves the scan."""
    (tmp_path / "hostile-excludes").write_text("fresh.md\n", encoding="utf-8")
    ok, notes = run_d_in_repo(
        tmp_path, monkeypatch, {"fresh.md": f"ARC_API_KEY={SHAPED}"},
        global_config="[core]\n\texcludesFile = %s\n" % (
            (tmp_path / "hostile-excludes").as_posix()))
    assert not ok and "fresh.md" in "\n".join(notes), (
        "a global core.excludesFile removed a file from the scan: %s" % notes)


@needs_git
def test_the_hostile_global_config_would_otherwise_have_worked(tmp_path):
    """Control for the test above, which would pass just as happily if
    `core.excludesFile` had never been honoured by anything."""
    (tmp_path / "excludes").write_text("fresh.md\n", encoding="utf-8")
    (tmp_path / "cfg").write_text(
        "[core]\n\texcludesFile = %s\n" % (tmp_path / "excludes").as_posix(),
        encoding="utf-8")
    (tmp_path / "fresh.md").write_text("x", encoding="utf-8")
    subprocess.run([GIT, "init", "-q"], cwd=str(tmp_path), check=True)
    rc, out = _raw_check_ignore(tmp_path, "fresh.md", {
        "GIT_CONFIG_GLOBAL": str(tmp_path / "cfg"),
        "GIT_CONFIG_SYSTEM": str(tmp_path / "nosuch")})
    assert rc == 0 and "excludes" in out, (
        "this git does not honour core.excludesFile, so the pinning test above "
        "proves nothing: %s" % out)


@needs_git
def test_planting_a_file_at_the_pinned_config_path_does_not_revive_excludesfile(
        tmp_path, monkeypatch):
    """The refuter's second attack, run at full strength. The first pin was
    `HERE / ".check-d-no-global-git-config"` -- absent by convention, on no ignore
    list, inside the directory being audited. Creating it with a `[core]
    excludesFile` line brought the lever back and hid a planted credential behind
    a green gate. "Pinned at an absent path" is a claim about the future.

    Here the test is *handed* the pinned path and creates it deliberately, which
    is stronger than the refuter's version: even an attacker who knows the path
    gains nothing, because `-c core.excludesFile=` on the command line outranks
    every config file. The absent path is now the second mechanism, not the
    load-bearing one."""
    (tmp_path / "hostile-excludes").write_text("fresh.md\n", encoding="utf-8")
    vp._ABSENT_GIT_CONFIG.write_text(
        "[core]\n\texcludesFile = %s\n" % (tmp_path / "hostile-excludes").as_posix(),
        encoding="utf-8")
    try:
        ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                                  {"fresh.md": f"ARC_API_KEY={SHAPED}"})
        assert not ok and "fresh.md" in "\n".join(notes), (
            "a file planted at the pinned config path revived core.excludesFile: "
            "%s" % notes)
    finally:
        vp._ABSENT_GIT_CONFIG.unlink(missing_ok=True)


def test_the_pinned_config_path_is_outside_the_audited_tree():
    """Where the first version went wrong, pinned as a property rather than as a
    string. Unpredictable, so it cannot be pre-created; outside `HERE` and `ROOT`,
    so nothing the check audits can reach it."""
    p = vp._ABSENT_GIT_CONFIG
    assert not p.exists()
    for anchor in (vp.HERE, vp.ROOT):
        with pytest.raises(ValueError):
            p.resolve().relative_to(anchor.resolve())


def test_the_git_environment_is_an_allowlist_not_a_denylist():
    """Completeness is the claim, and it does not rest on the author having
    enumerated git's variables. Every `GIT_*` in the caller's environment is
    deleted unless it is on a two-entry keep-list, so a variable nobody here has
    heard of -- or one added by a future git -- is gone by default. Both keepers
    can only *widen* the scan: they stop git finding the repository, which makes
    the ignore list unavailable, which scans everything and says so."""
    hostile = {
        "GIT_INDEX_FILE": "x", "GIT_DIR": "x", "GIT_WORK_TREE": "x",
        "GIT_COMMON_DIR": "x", "GIT_OBJECT_DIRECTORY": "x",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": "x", "GIT_CONFIG": "x",
        "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.excludesFile",
        "GIT_CONFIG_VALUE_0": "x", "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NOGLOB_PATHSPECS": "1", "GIT_ICASE_PATHSPECS": "1",
        "GIT_NAMESPACE": "x", "GIT_TRACE": "1",
        "GIT_SOME_VARIABLE_INVENTED_IN_A_FUTURE_RELEASE": "x",
    }
    env = dict(os.environ)
    env.update(hostile)
    saved, os.environ = os.environ, env
    try:
        got = vp._git_env()
    finally:
        os.environ = saved
    for name in hostile:
        assert name not in got, "%s survived into the git environment" % name
    assert got["GIT_CONFIG_NOSYSTEM"] == "1"
    assert vp.GIT_ENV_KEEP == {"GIT_CEILING_DIRECTORIES",
                               "GIT_DISCOVERY_ACROSS_FILESYSTEM"}


@needs_git
def test_the_xdg_default_ignore_file_cannot_hide_a_leak(tmp_path, monkeypatch):
    """A hole neither the refuter nor the two earlier patches named. Git's
    *default* for `core.excludesFile` is `$XDG_CONFIG_HOME/git/ignore`, falling
    back to `~/.config/git/ignore`. That is a built-in default, not a setting, so
    pinning `GIT_CONFIG_GLOBAL` never disabled it: a line in that file removed
    files from this scan on any machine that had one, with no config anywhere to
    show for it. `-c core.excludesFile=` is what closes it, and closing it is the
    reason the pin is a command-line override rather than an absent path."""
    xdg = tmp_path / "xdg"
    (xdg / "git").mkdir(parents=True)
    (xdg / "git" / "ignore").write_text("fresh.md\n", encoding="utf-8")
    ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                              {"fresh.md": f"ARC_API_KEY={SHAPED}"},
                              hostile_env={"XDG_CONFIG_HOME": str(xdg)})
    assert not ok and "fresh.md" in "\n".join(notes), (
        "git's default excludes file hid a leak: %s" % notes)


@needs_git
def test_the_xdg_default_ignore_file_would_otherwise_have_worked(tmp_path):
    """Control. Note the pinned global config and `GIT_CONFIG_NOSYSTEM` in the
    hostile environment: this file is obeyed *despite* both, which is exactly why
    the earlier patch's config pinning was not enough."""
    xdg = tmp_path / "xdg"
    (xdg / "git").mkdir(parents=True)
    (xdg / "git" / "ignore").write_text("fresh.md\n", encoding="utf-8")
    (tmp_path / "fresh.md").write_text("x", encoding="utf-8")
    subprocess.run([GIT, "init", "-q"], cwd=str(tmp_path), check=True)
    rc, out = _raw_check_ignore(tmp_path, "fresh.md", {
        "XDG_CONFIG_HOME": str(xdg),
        "GIT_CONFIG_GLOBAL": str(tmp_path / "absent"),
        "GIT_CONFIG_SYSTEM": str(tmp_path / "absent"),
        "GIT_CONFIG_NOSYSTEM": "1"})
    assert rc == 0 and "ignore" in out, (
        "this git does not honour the XDG default excludes file, so the test "
        "above proves nothing: %s" % out)


# --------------------------------------- no name-based exemption, and no file
# --------------------------------------- missing from the arithmetic
#
# `if p.is_file() and "__pycache__" not in p.parts` was a path allowlist eight
# lines from the docstring forbidding one, and worse than the gitignored skip on
# both axes used to justify that skip: the files are publishable, and they were in
# neither printed number. 181 files existed, 165 were scanned, 5 were reported
# skipped, and 11 vanished.

@needs_git
def test_a_tracked_pycache_file_is_still_scanned(tmp_path, monkeypatch):
    """Force-added bytecode is tracked, so `git ls-files` publishes it and
    `git check-ignore` agrees it is not ignored. The old rule dropped it anyway,
    silently, on the strength of its directory name."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                              {"__pycache__/leak.txt": f"ARC_API_KEY={SHAPED}"},
                              gitignore="__pycache__/\n",
                              track=("__pycache__/leak.txt",))
    assert not ok and "leak.txt" in "\n".join(notes), (
        "a tracked, publishable __pycache__ file was exempt: %s" % notes)


@needs_git
def test_a_tracked_pycache_dotenv_is_still_the_leak(tmp_path, monkeypatch):
    """The name-based skip removed the file from `candidates` outright, so it
    bypassed the `.env` filename tripwire too -- the one mechanism deliberately
    placed above the ignore filter to survive exactly this kind of narrowing."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                              {"__pycache__/.env": "ARC_API_KEY="},
                              gitignore="__pycache__/\n",
                              track=("__pycache__/.env",))
    assert not ok and ".env" in "\n".join(notes)


@needs_git
def test_an_ignored_pycache_file_is_skipped_and_counted(tmp_path, monkeypatch):
    """The ordinary case still ends up out of scope -- but through the general
    rule, and inside the arithmetic rather than beside it."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                              {"__pycache__/x.pyc": f"ARC_API_KEY={SHAPED}",
                               "section.md": "clean"},
                              gitignore="__pycache__/\n")
    blob = "\n".join(notes)
    assert ok, blob
    assert "1 skipped as gitignored under __pycache__/" in blob, blob


def test_the_note_accounts_for_every_file_on_the_live_tree():
    """The arithmetic, checked against the disk rather than against itself. Two
    numbers that do not close are how a scope hole hides in plain sight on a green
    line, and the previous note printed 165 + 5 against 181 files."""
    on_disk = sum(1 for p in vp.HERE.rglob("*") if p.is_file())
    ok, notes = vp.check_nosecret()
    blob = "\n".join(notes)
    assert ok, blob
    m = re.search(r"all (\d+) file\(s\) under this directory accounted for = "
                  r"(\d+) scanned \+ (\d+) skipped", blob)
    assert m, blob
    total, scanned, skipped = (int(g) for g in m.groups())
    assert total == on_disk, "%d in the note, %d on disk" % (total, on_disk)
    unreadable = re.search(r"(\d+) UNREADABLE", blob)
    assert scanned + skipped + (int(unreadable.group(1)) if unreadable else 0) \
        == total, blob


@needs_git
def test_a_skipped_top_level_file_is_not_labelled_with_its_own_name(
        tmp_path, monkeypatch):
    """`skipped_under` labelled a file directly under `HERE` with its own
    filename, so the note could read "skipped as gitignored under leak.txt" -- a
    filename presented as a directory, in the one line a reader consults to see
    whether the scope moved."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch,
                              {"leak.txt": f"ARC_API_KEY={SHAPED}",
                               "section.md": "clean"},
                              gitignore="leak.txt\n")
    blob = "\n".join(notes)
    assert ok, blob
    assert "1 skipped as gitignored under ./" in blob, blob
    assert "under leak.txt" not in blob, blob


@needs_git
def test_a_local_exclude_with_rules_is_announced(tmp_path, monkeypatch):
    """`$GIT_DIR/info/exclude` is the half that cannot be closed: it is not
    config, so no variable disables it, and it is untracked, so nothing in a
    review shows it. Announced with a count, not failed on -- these patterns are
    ordinary, and this repository's own ten are editor and harness state."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch, {"a.md": "x"},
                              local_exclude="# a comment\n\nbuild/\n*.tmp\n")
    blob = "\n".join(notes)
    assert ok, blob
    assert "info/exclude carries 2 pattern line(s)" in blob, blob


@needs_git
def test_a_stock_local_exclude_is_not_announced(tmp_path, monkeypatch):
    """Git writes a comments-only `info/exclude` into every repository it
    creates. Announcing that would put a scope caveat on every clone in
    existence, and a caveat that is always printed is one nobody reads."""
    ok, notes = run_d_in_repo(tmp_path, monkeypatch, {"a.md": "x"},
                              local_exclude="# nothing but comments\n#*.[oa]\n\n")
    assert ok and "info/exclude" not in "\n".join(notes)


def test_the_live_tree_reports_both_counts():
    """Positive control for the scope claim, beside the one for the verdict. The
    conditional half is the real exhibit: if the cache is on disk and nothing was
    skipped, the filter is not running on the tree it was written for."""
    ok, notes = vp.check_nosecret()
    blob = "\n".join(notes)
    assert ok, blob
    assert "published file(s) scanned" in blob and "skipped as gitignored" in blob
    if (vp.HERE / ".pytest_cache").is_dir():
        m = re.search(r"(\d+) skipped as gitignored", blob)
        assert m and int(m.group(1)) > 0, (
            "the pytest cache is on disk and the scan skipped nothing: %s" % blob)


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
