"""The register of paid-for artefacts, and the ways it is supposed to go red.

A14 (2026-07-29) found $50.39 of ARC spend sitting untracked in the working
tree while five other territories cited its sha256 as evidence. The register
exists so that state is nameable; these tests exist so the register is not
merely decorative. Every check below has its negative control: the clean case
AND the case it is supposed to catch, because a checker that has only ever been
run against a passing register has not been shown to fail.

The sharpest test here is `test_committed_campaign_json_bytes_survive_git`.
The four campaign checkpoints are CRLF on disk and their pinned digests were
taken over those CRLF bytes, but `baseline-arms/.gitattributes` sets
`* text eol=lf` -- so without the `out/campaign/*.json -text` rule A14 added,
`git add` would silently normalise them and every clone would hold a file whose
digest no longer matched the one battery already cited. Nothing would have
errored. That test is the tripwire on the rule: delete the rule and it fails.
"""

import hashlib
import json
import os

import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import cost_artefacts  # noqa: E402

TERRITORY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMPAIGN_JSONS = ["out/campaign/campaign_%s.json" % g
                  for g in ("ar25", "g50t", "sk48", "tn36")]


def _git(*argv):
    return subprocess.run(["git"] + list(argv), cwd=TERRITORY,
                          capture_output=True, check=True)


def _register(tmp_path, entries):
    """A register over a private tree. Never the tracked one."""
    path = tmp_path / "COST_ARTEFACTS.json"
    path.write_text(json.dumps({
        "schema": cost_artefacts.SCHEMA,
        "rule": "test",
        "artefacts": entries,
    }), encoding="utf-8")
    return str(path)


def _entry(path, disposition, sha256):
    return {"path": path, "disposition": disposition, "sha256": sha256}


@pytest.fixture
def git_says_nothing_is_tracked(monkeypatch):
    """Pin the tracking answer for tests that run over a scratch tree.

    `tmp_path` is not a git repository, so the real `_tracked_paths` would fail
    and return None -- "unknown", which the module correctly refuses to treat
    as "tracked". That is right behaviour but it is not what these tests are
    about, and leaving it in place would make them assert the git-unavailable
    branch by accident. This pins the answer to a working git that tracks
    nothing, which is the condition each test below actually names.
    """
    monkeypatch.setattr(cost_artefacts, "_tracked_paths", lambda *a, **k: set())


def _write(tmp_path, name, payload):
    full = tmp_path / name
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


# ------------------------------------------------------------------ the rule


def test_the_real_register_is_green():
    rows, problems = cost_artefacts.check()
    assert problems == [], "the committed register is RED: %s" % problems
    assert rows, "an empty register is not a clean one"


def test_every_committed_entry_is_actually_tracked():
    rows, _ = cost_artefacts.check()
    committed = [r for r in rows if r["disposition"] == "committed"]
    assert len(committed) >= 12, (
        "expected at least the 4 checkpoints + 4 ledgers + 4 probe logs A14 "
        "rescued, found %d" % len(committed))
    tracked = cost_artefacts._tracked_paths()
    assert tracked is not None, "git could not list tracked files"
    for row in committed:
        assert row["path"] in tracked, "%s is not tracked" % row["path"]


def test_battery_pins_are_still_satisfied():
    """The digests battery consumed as evidence still describe these bytes.

    Not a restatement of the register: this reads the *other* territory's
    manifest, so it fails if the register were ever regenerated over altered
    files (which would make the register self-consistent and still wrong).
    """
    manifest = os.path.join(os.path.dirname(TERRITORY), "battery", "runs",
                            "20260728T061147Z-v3", "MANIFEST.json")
    if not os.path.isfile(manifest):
        pytest.skip("battery v3 manifest absent")
    with open(manifest, encoding="utf-8") as fh:
        pinned = json.load(fh)["input_digests"]

    checked = 0
    for path, digest in pinned.items():
        if not path.startswith("baseline-arms/out/"):
            continue
        full = os.path.join(TERRITORY, path[len("baseline-arms/"):]
                            .replace("/", os.sep))
        if not os.path.isfile(full):
            continue
        assert cost_artefacts._sha256(full) == digest, (
            "%s no longer matches the digest battery consumed" % path)
        checked += 1
    assert checked >= 8, ("expected battery to pin at least the 4 checkpoints "
                          "and 4 ledgers, checked %d" % checked)


def test_committed_campaign_json_bytes_survive_git():
    """`git add` must not rewrite the bytes the pinned digests were taken over.

    The tripwire on `.gitattributes`' `out/campaign/*.json -text` rule. These
    files are CRLF; under the territory-wide `* text eol=lf` they would be
    normalised into the object store and a clone would get different bytes.
    Comparing the on-disk digest to the *blob* digest is what catches that,
    because `git status` reports the file clean either way.
    """
    for rel in CAMPAIGN_JSONS:
        full = os.path.join(TERRITORY, rel.replace("/", os.sep))
        on_disk = open(full, "rb").read()
        assert b"\r\n" in on_disk, (
            "%s is no longer CRLF; if it was deliberately re-written, the "
            "digests in COST_ARTEFACTS.json and battery's manifest must be "
            "re-pinned in the same commit" % rel)
        # "HEAD:./x" resolves against cwd; "HEAD:x" would resolve against the
        # repository root and look for a top-level out/ that does not exist.
        # `git show` emits the stored blob with no smudge filter, which is
        # exactly the comparison wanted: bytes in the object store vs bytes on
        # disk.
        blob = _git("show", "HEAD:./%s" % rel).stdout
        assert blob == on_disk, (
            "%s: the committed blob differs from the working tree byte-for-"
            "byte -- the eol translation rule has been lost" % rel)


# ------------------------------------------------------- the negative controls


def test_drifted_file_is_red(tmp_path, git_says_nothing_is_tracked):
    _write(tmp_path, "a.json", b"after")
    reg = _register(tmp_path, [_entry("a.json", "committed",
                                      hashlib.sha256(b"before").hexdigest())])
    rows, problems = cost_artefacts.check(reg, str(tmp_path))
    assert rows[0]["verdict"] == cost_artefacts.DRIFTED
    assert any("altered after it was recorded" in p for p in problems)


def test_missing_committed_file_is_red(tmp_path, git_says_nothing_is_tracked):
    reg = _register(tmp_path, [_entry("gone.json", "committed", "0" * 64)])
    rows, problems = cost_artefacts.check(reg, str(tmp_path))
    assert rows[0]["verdict"] == cost_artefacts.MISSING
    assert problems


def test_untracked_committed_file_is_red(tmp_path, git_says_nothing_is_tracked):
    """The exact A14 failure: present, correct, and in nobody's git."""
    digest = _write(tmp_path, "loose.json", b"paid for")
    reg = _register(tmp_path, [_entry("loose.json", "committed", digest)])
    rows, problems = cost_artefacts.check(reg, str(tmp_path))
    assert rows[0]["verdict"] == cost_artefacts.UNTRACKED
    assert any("git does not track it" in p for p in problems)


def test_absent_hash_only_file_is_not_red(tmp_path, git_says_nothing_is_tracked):
    """hash-only accepts absence -- that is what the disposition buys."""
    reg = _register(tmp_path, [_entry("gone.log", "hash-only", "a" * 64)])
    rows, problems = cost_artefacts.check(reg, str(tmp_path))
    assert rows[0]["verdict"] == cost_artefacts.ABSENT
    assert problems == []


def test_present_but_drifted_hash_only_file_is_red(tmp_path, git_says_nothing_is_tracked):
    """...but it does not accept a *different* file wearing the same name."""
    _write(tmp_path, "x.log", b"rewritten")
    reg = _register(tmp_path, [_entry("x.log", "hash-only", "b" * 64)])
    rows, problems = cost_artefacts.check(reg, str(tmp_path))
    assert rows[0]["verdict"] == cost_artefacts.DRIFTED
    assert problems


def test_bad_disposition_is_red(tmp_path, git_says_nothing_is_tracked):
    digest = _write(tmp_path, "y.json", b"y")
    reg = _register(tmp_path, [_entry("y.json", "probably-fine", digest)])
    _, problems = cost_artefacts.check(reg, str(tmp_path))
    assert any("is not one of" in p for p in problems)


def test_malformed_digest_is_red(tmp_path, git_says_nothing_is_tracked):
    _write(tmp_path, "z.json", b"z")
    reg = _register(tmp_path, [_entry("z.json", "committed", "DEADBEEF")])
    _, problems = cost_artefacts.check(reg, str(tmp_path))
    assert any("64 lowercase hex" in p for p in problems)


def test_duplicate_path_is_red(tmp_path, git_says_nothing_is_tracked):
    digest = _write(tmp_path, "d.json", b"d")
    reg = _register(tmp_path, [_entry("d.json", "hash-only", digest),
                               _entry("d.json", "hash-only", digest)])
    _, problems = cost_artefacts.check(reg, str(tmp_path))
    assert any("listed twice" in p for p in problems)


def test_wrong_schema_is_refused(tmp_path):
    path = tmp_path / "COST_ARTEFACTS.json"
    path.write_text(json.dumps({"schema": "something-else", "artefacts": [1]}),
                    encoding="utf-8")
    with pytest.raises(ValueError, match="schema"):
        cost_artefacts.check(str(path), str(tmp_path))


def test_empty_register_is_refused(tmp_path):
    reg_path = tmp_path / "COST_ARTEFACTS.json"
    reg_path.write_text(json.dumps({"schema": cost_artefacts.SCHEMA,
                                    "artefacts": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="non-empty"):
        cost_artefacts.check(str(reg_path), str(tmp_path))


def test_unavailable_git_does_not_certify(tmp_path, monkeypatch):
    """An unanswerable question is not a yes.

    If `git ls-files` fails, tracking is unknown -- and unknown must not read
    as tracked, or the register would go green on exactly the machine where it
    can least be trusted.
    """
    digest = _write(tmp_path, "q.json", b"q")
    reg = _register(tmp_path, [_entry("q.json", "committed", digest)])
    monkeypatch.setattr(cost_artefacts, "_tracked_paths", lambda *a, **k: None)
    _, problems = cost_artefacts.check(reg, str(tmp_path))
    assert any("git ls-files failed" in p for p in problems)


# --------------------------------------------------------- the generated form


def test_register_matches_a_fresh_rederivation():
    """COST_ARTEFACTS.json is generated; a hand-edit must show up as red."""
    builder = os.path.join(TERRITORY, "runs", "20260729T100000Z-a14",
                           "build_register.py")
    if not os.path.isfile(builder):
        pytest.skip("A14 run directory absent")
    env = dict(os.environ)
    env.pop("ARC_API_KEY", None)
    proc = subprocess.run([sys.executable, builder, "--check"], cwd=TERRITORY,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=env)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_no_credential_in_any_committed_artefact():
    """The rescue must not have carried the key into the repository.

    Reads the key only to search for it, never prints or logs it, and skips
    rather than passing if `.env` is absent -- a check that cannot run is not a
    check that passed.
    """
    env_path = os.path.join(os.path.dirname(TERRITORY), ".env")
    if not os.path.isfile(env_path):
        pytest.skip(".env absent, so the key cannot be searched for")
    key = ""
    for line in open(env_path, encoding="utf-8"):
        if line.startswith("ARC_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if len(key) < 12:
        pytest.skip("no usable ARC_API_KEY in .env")

    rows, _ = cost_artefacts.check()
    needle = key.encode("utf-8")
    checked = 0
    for row in rows:
        if row["disposition"] != "committed":
            continue
        full = os.path.join(TERRITORY, row["path"].replace("/", os.sep))
        # Overlap successive chunks by len(needle)-1 bytes, or a key straddling
        # a chunk boundary would slip through and the test would pass wrongly.
        tail = b""
        with open(full, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                assert needle not in tail + chunk, (
                    "credential value in %s" % row["path"])
                tail = chunk[-(len(needle) - 1):]
        checked += 1
    assert checked >= 12
