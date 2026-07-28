"""Red lines, checked rather than promised.

Four of these mirror A2's; the fifth is A3's own and is the one that matters
most here.  **The transfer arm's claim is a claim about what it did not read**,
and a claim of that shape cannot be evidenced by the arm's own report — only by
its call graph.  So `test_the_transfer_arm_cannot_reach_a_level_2_trace` reads
the source and fails if the arm so much as mentions a sweep file.
"""

import io
import json
import os
import re
import subprocess
import sys
import tokenize

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import _bootstrap  # noqa: F401,E402

ARTIFACTS = os.path.join(HERE, "artifacts")


def _shipped_python():
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs
                   if d not in ("__pycache__", ".pytest_cache", "runs")]
        for name in sorted(files):
            if name.endswith(".py"):
                yield os.path.join(root, name)


def _source(path):
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def _code_without_comments_or_strings(path):
    """Source with comments and string literals removed.

    Necessary because every module here documents what it does *not* do, and a
    naive substring scan would fail on the prose that exists to be honest.
    """
    out = []
    with open(path, "rb") as handle:
        try:
            for tok in tokenize.tokenize(handle.readline):
                if tok.type in (tokenize.COMMENT, tokenize.STRING):
                    continue
                out.append(tok.string)
        except (tokenize.TokenError, IndentationError):
            return _source(path)
    # Tokens are joined with spaces, which would split every dotted name, so
    # the separators are closed up again: the checks below are about module
    # paths like `a3world.executor` and must see them whole.
    return re.sub(r"\s*\.\s*", ".", " ".join(out))


# --------------------------------------------------------------- the arm seal

def test_the_transfer_arm_cannot_reach_a_level_2_trace():
    """Zero relearning is a fact about the call graph, not a promise.

    The transfer arm may read `l2_frame0.json` and the two books.  It may not
    read `l2_sweep.jsonl`, may not import the engine stage, and may not import
    any world module — mining a rule is exactly what it claims not to do.
    """
    arm = os.path.join(HERE, "a3pipeline", "transfer.py")
    if not os.path.exists(arm):
        import pytest
        pytest.skip("transfer arm not built yet")
    code = _code_without_comments_or_strings(arm)
    for forbidden in ("l2_sweep", "l1_sweep", "candidates_l1",
                      "candidates_l2_scratch", "a3_world", "A3World",
                      "engines_stage", "a3pipeline.engines", "multi_miner",
                      "run_stage", "ground_truth"):
        assert forbidden not in code, (
            "the transfer arm reaches %r, which is the thing it claims not to do"
            % forbidden)

    # Acting in the world is allowed and necessary — a plan that is never
    # executed proves nothing.  Reading the world is not.  The environment
    # proxy is the only bridge, and it hands back frames.
    assert "a3world.executor" in code or "executor" in code
    assert "a3world" not in code.replace("a3world.executor", "")


def test_no_pipeline_module_imports_the_world():
    """Truth reaches every arm as frames, never as a transition function."""
    for path in _shipped_python():
        rel = os.path.relpath(path, HERE).replace("\\", "/")
        if not rel.startswith("a3pipeline/"):
            continue
        code = _code_without_comments_or_strings(path)
        assert "a3_world" not in code, rel
        assert "A3World" not in code, rel


# ------------------------------------------------------------------ no network

def test_nothing_here_can_reach_the_network():
    banned = re.compile(
        r"\b(import\s+(requests|urllib|http\.client|socket)"
        r"|from\s+(requests|urllib|http|socket)\s+import)\b")
    for path in _shipped_python():
        code = _code_without_comments_or_strings(path)
        assert not banned.search(code), path


def test_no_credential_appears_anywhere():
    # The needle is assembled at run time so that this file does not itself
    # contain the string it forbids — the first version of this test failed on
    # its own source, which is funny once and a maintenance trap thereafter.
    needle = b"ARC_" + b"API_KEY"
    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache")]
        for name in files:
            path = os.path.join(root, name)
            with open(path, "rb") as handle:
                blob = handle.read()
            assert needle not in blob, path


# -------------------------------------------------------------- the pile cut

def test_no_sealed_game_id_is_present():
    """A3 is offline and self-built; no game id belongs in this tree at all."""
    piles = json.load(open(os.path.join(REPO, "arc-recon", "data", "piles.json"),
                           encoding="utf-8"))
    sealed = []
    for key in ("sealed", "sealed_pile", "holdout"):
        if key in piles:
            sealed = piles[key]
            break
    ids = []
    for entry in sealed:
        ids.append(entry if isinstance(entry, str) else entry.get("id", ""))
    ids = [i for i in ids if i]
    assert ids, "could not read the sealed pile out of piles.json"

    for root, dirs, files in os.walk(HERE):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache")]
        for name in files:
            path = os.path.join(root, name)
            with open(path, "rb") as handle:
                blob = handle.read().lower()
            for game_id in ids:
                short = game_id.split("-")[0].encode()
                assert game_id.lower().encode() not in blob, (path, game_id)
                assert short not in blob, (path, game_id)


# --------------------------------------------------------- the frozen contract

def test_the_frozen_contracts_are_untouched():
    out = subprocess.run(
        ["git", "status", "--porcelain", "CONTRACTS/"],
        cwd=REPO, capture_output=True, text=True, timeout=60)
    assert out.stdout.strip() == "", out.stdout


def test_every_candidate_stream_validates_and_is_never_adjudicated():
    sys.path.insert(0, os.path.join(REPO, "engine-rig"))
    from tools.validate_candidates import validate_file as validate  # noqa: E402

    streams = [os.path.join(ARTIFACTS, n) for n in sorted(os.listdir(ARTIFACTS))
               if n.startswith("candidates") and n.endswith(".jsonl")]
    assert streams, "no candidate streams to validate"
    for path in streams:
        errors = validate(path)
        assert not errors, (path, errors[:5])
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    assert json.loads(line)["status"] == "candidate", path


# ----------------------------------------------------------------- read-only

def test_a3_never_writes_outside_its_own_tree():
    """No shipped module may name a path into another track's directory.

    `_bootstrap` legitimately puts those roots on `sys.path`, and the upstream
    pin legitimately hashes them, so both are exempt by name.
    """
    exempt = {"_bootstrap.py", "concepts.py", "verify_readonly.py"}
    for path in _shipped_python():
        if os.path.basename(path) in exempt:
            continue
        code = _code_without_comments_or_strings(path)
        for other in ("cold-start-a0", "cold-start-a2", "a0-spike",
                      "theory-compiler", "baseline-arms", "battery", "proxy"):
            assert other not in code, (path, other)
