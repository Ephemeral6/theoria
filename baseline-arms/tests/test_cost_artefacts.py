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
    """Pin the HEAD answer for tests that run over a scratch tree.

    `tmp_path` is not a git repository, so the real `_head_blobs` would fail
    and return None -- "unknown", which the module correctly refuses to treat
    as "committed". That is right behaviour but it is not what these tests are
    about, and leaving it in place would make them assert the git-unavailable
    branch by accident. This pins the answer to a working git holding nothing,
    which is the condition each test below actually names.

    Because this mock supplies the semantics rather than exercising them,
    `test_head_blobs_reports_head_not_the_index` tests the real query directly.
    Without that, a mock like this one hides exactly the index-vs-HEAD defect
    an adversarial review found here.
    """
    monkeypatch.setattr(cost_artefacts, "_head_blobs", lambda *a, **k: {})


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
    head = cost_artefacts._head_blobs()
    assert head is not None, "git could not read HEAD"
    for row in committed:
        assert row["path"] in head, "%s is not in HEAD" % row["path"]
        assert head[row["path"]] == row["sha256"], (
            "%s: the blob in HEAD does not hash to the pinned digest, so a "
            "clone would get different bytes" % row["path"])


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

    **The blob comparison alone is not the tripwire it looks like**, and an
    adversarial review caught this: removing an attribute does not rewrite an
    existing blob, so with the rule deleted `git show HEAD:` still returns the
    CRLF bytes and the comparison stays green until the next `git add` -- by
    which time the digest is already broken. So the attribute itself is
    asserted, and so is `git status` cleanliness, which is what actually goes
    red the moment the rule is dropped. (The earlier version of this docstring
    claimed `git status` reports the file clean either way. That was wrong: it
    reports ` M` immediately, and it was the one signal that would have caught
    the regression this test was missing.)
    """
    for rel in CAMPAIGN_JSONS:
        full = os.path.join(TERRITORY, rel.replace("/", os.sep))
        on_disk = open(full, "rb").read()
        assert b"\r\n" in on_disk, (
            "%s is no longer CRLF; if it was deliberately re-written, the "
            "digests in COST_ARTEFACTS.json and battery's manifest must be "
            "re-pinned in the same commit" % rel)

        attr = _git("check-attr", "text", "--", rel).stdout.decode("utf-8")
        assert attr.strip().endswith(": text: unset"), (
            "%s: the `out/campaign/*.json -text` rule in .gitattributes is "
            "gone (check-attr says %r). The bytes on disk are still right, but "
            "the next `git add` will normalise them and break the pinned "
            "digest." % (rel, attr.strip()))

        assert _git("status", "--porcelain", "--", rel).stdout == b"", (
            "%s: git reports the file modified against the index. Under a lost "
            "eol rule this is the first thing to go red." % rel)

        # "HEAD:./x" resolves against cwd; "HEAD:x" would resolve against the
        # repository root and look for a top-level out/ that does not exist.
        # `git show` emits the stored blob with no smudge filter, which is
        # exactly the comparison wanted: bytes in the object store vs bytes on
        # disk.
        blob = _git("show", "HEAD:./%s" % rel).stdout
        assert blob == on_disk, (
            "%s: the committed blob differs from the working tree byte-for-"
            "byte -- the eol translation rule has been lost" % rel)


def test_head_blobs_reports_head_not_the_index(tmp_path):
    """Staging is not committing, and the module must not confuse them.

    The defect this pins: `git ls-files` answers about the *index*, so a path
    that was added and never committed reads back as tracked. Since this repo
    commits by path rather than with `-a`, that is a routine state -- and it
    would have let an artefact that no clone possesses pass as safely stored.
    Nothing else in this file exercises the real git query; every other
    tracking test mocks it.
    """
    repo = tmp_path / "r"
    repo.mkdir()

    def git(*argv, **kw):
        return subprocess.run(["git"] + list(argv), cwd=str(repo),
                              capture_output=True, check=True, **kw)

    git("init", "-q", ".")
    git("config", "user.email", "t@example.invalid")
    git("config", "user.name", "t")
    (repo / "committed.json").write_bytes(b"paid for\n")
    git("add", "committed.json")
    git("commit", "-qm", "one")
    (repo / "staged.json").write_bytes(b"also paid for\n")
    git("add", "staged.json")

    blobs = cost_artefacts._head_blobs(str(repo))
    assert blobs is not None
    assert "committed.json" in blobs
    assert "staged.json" not in blobs, (
        "a staged-but-uncommitted path is being reported as in HEAD; the "
        "check is reading the index again")
    assert blobs["committed.json"] == hashlib.sha256(b"paid for\n").hexdigest()


def test_head_drift_is_red(tmp_path):
    """Right on disk, different in HEAD -- the eol failure, generalised.

    Constructed by committing LF bytes and then writing CRLF bytes to the
    working tree whose digest is the one the register pins. Disk matches, HEAD
    does not, and a clone would get the other file.
    """
    repo = tmp_path / "r"
    repo.mkdir()

    def git(*argv):
        return subprocess.run(["git"] + list(argv), cwd=str(repo),
                              capture_output=True, check=True)

    git("init", "-q", ".")
    git("config", "user.email", "t@example.invalid")
    git("config", "user.name", "t")
    (repo / ".gitattributes").write_bytes(b"* -text\n")
    (repo / "a.json").write_bytes(b"{}\n")            # LF into the object store
    git("add", ".gitattributes", "a.json")
    git("commit", "-qm", "one")
    (repo / "a.json").write_bytes(b"{}\r\n")          # CRLF in the working tree

    digest = hashlib.sha256(b"{}\r\n").hexdigest()
    reg = _register(tmp_path, [_entry("a.json", "committed", digest)])
    rows, problems = cost_artefacts.check(reg, str(repo))
    assert rows[0]["verdict"] == cost_artefacts.HEAD_DRIFT
    assert any("a clone would get different bytes" in p for p in problems)


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
    assert any("it is not in HEAD" in p for p in problems)


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

    If HEAD cannot be read, storage is unknown -- and unknown must not read as
    stored, or the register would go green on exactly the machine where it can
    least be trusted.

    The row-level assertion is the point. An earlier version checked only that
    a problem string appeared, while `check()` still returned `verdict: "ok"`
    for the entry -- so any caller adjudicating on rows (the obvious way to
    consume `--json`) would have certified it. The aggregate said no and the
    machine-readable form said yes.
    """
    digest = _write(tmp_path, "q.json", b"q")
    reg = _register(tmp_path, [_entry("q.json", "committed", digest)])
    monkeypatch.setattr(cost_artefacts, "_head_blobs", lambda *a, **k: None)
    rows, problems = cost_artefacts.check(reg, str(tmp_path))
    assert rows[0]["verdict"] == cost_artefacts.UNVERIFIED
    assert rows[0]["verdict"] != cost_artefacts.OK
    assert any("HEAD could not be read" in p for p in problems)


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


def _scan(path, needle):
    """True if `needle` occurs in the file, chunk boundaries included."""
    tail = b""
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            if needle in tail + chunk:
                return True
            tail = chunk[-(len(needle) - 1):]
    return False


def test_the_credential_scanner_finds_a_planted_key(tmp_path):
    """Positive control for the scan below.

    Without this, `test_no_credential_in_any_committed_artefact` could pass by
    never matching anything -- a scanner that finds nothing and a scanner that
    cannot find anything look identical from the outside. The needle is planted
    across a 1 MiB chunk boundary, which is the one case the chunked reader
    could plausibly miss.
    """
    needle = b"NOT-A-REAL-KEY-0123456789abcdef"
    planted = tmp_path / "planted.bin"
    boundary = (1 << 20) - (len(needle) // 2)
    planted.write_bytes(b"." * boundary + needle + b"." * 4096)
    assert _scan(str(planted), needle), "the scanner cannot find a planted key"

    clean = tmp_path / "clean.bin"
    clean.write_bytes(b"." * ((1 << 20) + 4096))
    assert not _scan(str(clean), needle), "the scanner reports a false positive"


def test_no_credential_in_any_committed_artefact():
    """The rescue must not have carried the key into the repository.

    Reads the key only to search for it, never prints or logs it.

    `.env` lives at the *main checkout's* root and is gitignored, so it is in
    neither a worktree nor a clone. Resolving it as the territory's parent made
    this test skip in every worktree, silently -- and `--show-toplevel` does
    not help, since in a linked worktree that is the worktree. `--git-common-dir`
    is the one that points back at the shared `.git`, whose parent is the main
    checkout. A skip here is still honest: a check that cannot run is not a
    check that passed.
    """
    roots = []
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            cwd=TERRITORY, capture_output=True, check=True,
        ).stdout.decode("utf-8").strip()
        if common:
            roots.append(os.path.dirname(os.path.abspath(
                os.path.join(TERRITORY, common))))
    except (OSError, subprocess.CalledProcessError):
        pass
    roots.append(os.path.dirname(TERRITORY))

    env_path = next((os.path.join(r, ".env") for r in roots
                     if r and os.path.isfile(os.path.join(r, ".env"))), None)
    if env_path is None:
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
        assert not _scan(full, needle), "credential value in %s" % row["path"]
        checked += 1
    assert checked >= 12
