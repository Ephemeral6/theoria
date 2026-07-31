"""The freeze holds — and, more importantly, it is seen to fire.

A freeze that has never refused anything is a comment. Most of this file is
negative controls: each breaks the tree in one specific way and asserts that
`freeze.check()` names it. Every control here corresponds to an attack that
actually moved a published number while the gate stayed green, before the check
was widened to cover it — an ordering worth preserving, because a test written
from an attack that landed is worth more than one written from an intention.
"""

import os
import shutil
import types

import pytest

from battery import freeze


@pytest.fixture
def tree(tmp_path):
    """A copy of battery/ (plus the pile cut) that a test may vandalise.

    `check(root=...)` against it is the real check, not a simulation.
    """
    shutil.copytree(os.path.join(freeze.ROOT, "battery"), tmp_path / "battery",
                    ignore=shutil.ignore_patterns("__pycache__",
                                                  ".pytest_cache", "runs"))
    cut = tmp_path / "arc-recon" / "data"
    cut.mkdir(parents=True)
    shutil.copy(os.path.join(freeze.ROOT, *freeze.CUT.split("/")),
                cut / "piles.json")
    return str(tmp_path)


def test_the_freeze_holds_on_the_real_tree():
    assert freeze.check() == []


def test_the_fixture_reproduces_the_real_verdict(tree):
    """Otherwise every negative control below is testing the fixture."""
    assert freeze.check(root=tree) == []


def test_the_record_pins_every_bucket():
    rec = freeze.read_record()
    for name, bucket in freeze.BUCKETS:
        assert set(rec[name]) == set(bucket), name
    assert rec["prereg"]["path"] == freeze.PREREG
    assert rec["cut"] == freeze.CUT_DIGEST


def test_the_pinned_cut_is_the_one_claude_md_publishes():
    """CLAUDE.md publishes 3feca53e…41bbc19a as the binding cut."""
    assert freeze.CUT_DIGEST.startswith("3feca53e")
    assert freeze.CUT_DIGEST.endswith("41bbc19a")
    assert freeze.canonical_cut() == freeze.CUT_DIGEST


def _defining_module(fn):
    """The metric body behind `metric()`'s needs-guard.

    The decorator (battery/metrics/__init__.py:130) wraps without
    functools.wraps, so `fn.__module__` is the wrapper's module, not the
    metric's. The real function is the closed-over one.
    """
    for cell in (fn.__closure__ or ()):
        inner = cell.cell_contents
        if isinstance(inner, types.FunctionType):
            return inner.__module__
    return fn.__module__


def test_every_metric_module_is_inside_the_freeze():
    """The registry's 38 metrics must all be computed by frozen files."""
    from battery.metrics import REGISTRY
    assert len(REGISTRY) == 38
    for mid, card in REGISTRY.items():
        mod = _defining_module(card.fn).replace(".", "/") + ".py"
        assert mod in freeze.CODE, "%s computes %s from outside the freeze" % (
            mod, mid)


# --- negative controls: the instrument -----------------------------------

def test_an_edited_metric_refuses_to_verify(tree):
    """The offence the freeze exists for: a number moved without a new version."""
    target = os.path.join(tree, "battery", "metrics", "economy.py")
    with open(target, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n# the eight-turn floor was lowered here\n")
    fails = freeze.check(root=tree)
    assert any("economy.py" in f and "edited in place" in f for f in fails), fails
    assert any("BATTERY_V2" in f for f in fails), fails


def test_a_new_unregistered_metric_module_refuses_to_verify(tree):
    """The thirty-ninth metric must not arrive unhashed.

    Every listed digest still matches here — this is the failure a file-list
    fingerprint catches only if it also checks for files outside the list.
    """
    with open(os.path.join(tree, "battery", "metrics", "sneaky.py"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("# a metric the freeze never saw\n")
    fails = freeze.check(root=tree)
    assert any("sneaky.py" in f and "no freeze bucket covers it"
               in f for f in fails), fails


def test_a_deleted_frozen_file_refuses_to_verify(tree):
    os.remove(os.path.join(tree, "battery", "audit", "gaming.py"))
    fails = freeze.check(root=tree)
    assert any("gaming.py" in f and "not on disk" in f for f in fails), fails


# --- negative controls: the gate's own plumbing --------------------------
#
# Each of these was a landed attack: the number moved and `verify` exited 0.

def test_an_edited_metrics_doc_refuses_to_verify(tree):
    """METRICS.md states what the instrument is; readers parse it as truth."""
    target = os.path.join(tree, "battery", "METRICS.md")
    blob = open(target, encoding="utf-8").read()
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        needle = "**Main table (0):**"
        assert needle in blob, "the vandalism must land, or this tests nothing"
        fh.write(blob.replace(needle, "**Main table (12):**", 1))
    fails = freeze.check(root=tree)
    assert any("METRICS.md" in f and "edited in place" in f for f in fails), fails


def test_a_conftest_under_tests_refuses_to_verify(tree):
    """`tests/` is half the gate, so nothing may appear in it unregistered.

    A conftest fixture that rebinds a module is ordinary practice and an
    ordinary accident; it is also enough to make the suite stop objecting.
    """
    with open(os.path.join(tree, "battery", "tests", "conftest.py"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("# a fixture the freeze never saw\n")
    fails = freeze.check(root=tree)
    assert any("conftest.py" in f for f in fails), fails


def test_an_edited_pytest_ini_refuses_to_verify(tree):
    """One `addopts` line can deselect whichever test would have objected."""
    target = os.path.join(tree, "battery", "pytest.ini")
    with open(target, "a", encoding="utf-8", newline="\n") as fh:
        fh.write('addopts = -k "not freeze"\n')
    fails = freeze.check(root=tree)
    assert any("pytest.ini" in f and "edited in place" in f for f in fails), fails


def test_an_edited_test_refuses_to_verify(tree):
    """A suite that can be edited freely can be made to stop objecting."""
    target = os.path.join(tree, "battery", "tests", "test_guard.py")
    with open(target, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n# the sealed-pile assertions were relaxed here\n")
    fails = freeze.check(root=tree)
    assert any("test_guard.py" in f and "edited in place"
               in f for f in fails), fails


# --- negative controls: the pile cut -------------------------------------

def test_a_doctored_pile_cut_refuses_to_verify(tree):
    """piles.json's own sha256 field is self-referential and cannot catch this.

    Moving a game from sealed to dev and re-writing the field loads clean
    through guard.py. Only an externally pinned digest sees it.
    """
    import json
    from battery.guard import canonical_digest
    path = os.path.join(tree, "arc-recon", "data", "piles.json")
    doc = json.load(open(path, encoding="utf-8"))
    doc["dev_pile"].append(doc["sealed_pile"].pop())
    doc["sha256"] = canonical_digest(doc)     # the doctored cut re-seals itself
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True, ensure_ascii=False)
    fails = freeze.check(root=tree)
    assert any("piles.json" in f and "contract, not a reading"
               in f for f in fails), fails


# --- negative controls: the record itself --------------------------------

def test_a_repeated_digest_line_refuses_to_parse(tmp_path):
    """Last-wins on a duplicate key is a silent way to re-point one digest."""
    record = tmp_path / "rec.md"
    text = open(freeze.RECORD, encoding="utf-8").read()
    fake = "sha256:" + "0" * 64
    text = text.replace(
        "```freeze:code\n",
        "```freeze:code\n%s  battery/model.py\n" % fake, 1)
    record.write_text(text, encoding="utf-8", newline="")
    with pytest.raises(freeze.FreezeDriftError, match="appears twice"):
        freeze.read_record(str(record))


def test_a_second_block_of_the_same_name_refuses_to_parse(tmp_path):
    record = tmp_path / "rec.md"
    text = open(freeze.RECORD, encoding="utf-8").read()
    text += "\n```freeze:code\nsha256:%s  battery/model.py\n```\n" % ("0" * 64)
    record.write_text(text, encoding="utf-8", newline="")
    with pytest.raises(freeze.FreezeDriftError, match="2 `freeze:code` blocks"):
        freeze.read_record(str(record))


def test_a_second_prefix_line_refuses_to_parse(tmp_path):
    record = tmp_path / "rec.md"
    text = open(freeze.RECORD, encoding="utf-8").read()
    text = text.replace("prefix-bytes: ", "prefix-bytes: 1\nprefix-bytes: ", 1)
    record.write_text(text, encoding="utf-8", newline="")
    with pytest.raises(freeze.FreezeDriftError, match="prefix-bytes"):
        freeze.read_record(str(record))


# --- negative controls: the pre-registration -----------------------------

def test_a_rewritten_prediction_refuses_to_verify(tree):
    """PREDICTIONS.md:5 — a prediction that can be edited is not a prediction.

    The rewrite keeps the byte count identical, so the only thing that can
    catch it is the prefix digest. A length check would not have seen this.
    """
    target = os.path.join(tree, "battery", "PREDICTIONS.md")
    blob = bytearray(open(target, "rb").read())
    at = len(blob) // 2
    blob[at] = ord("~") if blob[at] != ord("~") else ord("!")
    with open(target, "wb") as fh:
        fh.write(bytes(blob))
    fails = freeze.check(root=tree)
    assert any("edited after the fact" in f for f in fails), fails
    assert not any("has grown since" in f for f in fails), fails


def test_a_prediction_appended_after_the_freeze_refuses_to_verify(tree):
    """Legitimate work, illegitimate freeze — and it reads differently."""
    target = os.path.join(tree, "battery", "PREDICTIONS.md")
    with open(target, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n# v3 — predicted after the instrument was frozen\n")
    fails = freeze.check(root=tree)
    assert any("has grown since" in f for f in fails), fails
    assert not any("edited after the fact" in f for f in fails), fails


def test_a_truncated_prereg_refuses_to_verify(tree):
    target = os.path.join(tree, "battery", "PREDICTIONS.md")
    blob = open(target, "rb").read()
    with open(target, "wb") as fh:
        fh.write(blob[:100])
    fails = freeze.check(root=tree)
    assert any("append-only" in f for f in fails), fails


# --- the readings are recorded, not gated --------------------------------

def test_an_edited_artefact_is_reported_but_does_not_fail(tree):
    """Phase 4 must be able to recompute. Silence would be the wrong answer too."""
    target = os.path.join(tree, "battery", "artifacts", "gaming_audit.json")
    with open(target, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n")
    assert freeze.check(root=tree) == []
    drift = freeze.readings_drift(root=tree)
    assert drift == ["battery/artifacts/gaming_audit.json"], drift


# --- the hash itself -----------------------------------------------------

def test_the_digest_survives_a_crlf_checkout(tmp_path):
    """A clone with core.autocrlf=true must produce the same record.

    battery/.gitattributes pins LF here, which is why that file is itself
    frozen; normalising in the hasher is the belt to its braces.
    """
    lf = tmp_path / "lf.py"
    crlf = tmp_path / "crlf.py"
    lf.write_bytes(b"one\ntwo\n")
    crlf.write_bytes(b"one\r\ntwo\r\n")
    assert freeze.sha256_file(str(lf)) == freeze.sha256_file(str(crlf))


def test_the_prefix_byte_count_is_an_lf_count(tmp_path):
    """So the append-only prefix does not shift on a CRLF checkout."""
    lf = tmp_path / "lf.md"
    crlf = tmp_path / "crlf.md"
    lf.write_bytes(b"a\nb\nc\n")
    crlf.write_bytes(b"a\r\nb\r\nc\r\n")
    assert freeze.sha256_prefix(str(lf), 4) == freeze.sha256_prefix(str(crlf), 4)


def test_rendering_the_blocks_reproduces_the_record():
    """The document is the record: what freeze.py renders is what it reads."""
    rendered = freeze.render_blocks()
    record = open(freeze.RECORD, encoding="utf-8").read()
    for block in rendered.split("\n\n"):
        assert block in record, block.splitlines()[0]
