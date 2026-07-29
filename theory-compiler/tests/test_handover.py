"""What a handover package must be true of, tested against the two shipped ones.

The properties here are the ones a reader's score cannot distinguish from their
own failure: a package that quietly lost a form, or shipped a board it did not
build, or carried a sentence that only makes sense to someone with the
repository open, produces a reader who looks incompetent. Each of those is a
test rather than a habit.
"""

import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
TRACK = os.path.dirname(HERE)
REPO = os.path.dirname(TRACK)
sys.path.insert(0, os.path.join(TRACK, "tools"))

from theory_compiler import handover                                  # noqa: E402
from theory_compiler.parser.theory_parser import parse_theory         # noqa: E402
import build_handover_packages as builder                             # noqa: E402

PACKAGE_ROOT = os.path.join(TRACK, "handover_packages")
NAMES = sorted(builder.PACKAGES)


@pytest.fixture(scope="module")
def built():
    return {name: handover.build_files(builder.PACKAGES[name]())
            for name in NAMES}


# =========================================================================
# determinism and agreement with what is checked in
# =========================================================================

@pytest.mark.parametrize("name", NAMES)
def test_build_is_byte_reproducible(name):
    once, _ = handover.build_files(builder.PACKAGES[name]())
    twice, _ = handover.build_files(builder.PACKAGES[name]())
    assert once == twice


@pytest.mark.parametrize("name", NAMES)
def test_checked_in_package_matches_the_builder(name, built):
    want, _manifest = built[name]
    have = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    assert sorted(have) == sorted(want)
    for path in sorted(want):
        assert have[path] == want[path], path


@pytest.mark.parametrize("name", NAMES)
def test_manifest_digests_are_of_the_files_present(name):
    files = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    manifest = json.loads(files["MANIFEST.json"])
    assert sorted(manifest["files"]) == sorted(p for p in files
                                               if p != "MANIFEST.json")
    for path, digest in manifest["files"].items():
        assert handover._sha256(files[path]) == digest, path


# =========================================================================
# the seal
# =========================================================================

@pytest.mark.parametrize("name", NAMES)
def test_no_blocking_context_leak(name):
    files = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    blocking = [f for f in handover.context_report(files)
                if f.severity == "blocking"]
    assert blocking == []


@pytest.mark.parametrize("name", NAMES)
def test_seal_report_counts_agree_with_a_fresh_scan(name):
    files = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    manifest = json.loads(files["MANIFEST.json"])
    findings = handover.context_report(files)
    citations = len([f for f in findings if f.severity == "citation"])
    assert manifest["context_scan"]["citations"] == citations
    assert manifest["context_scan"]["blocking"] == 0
    assert "citations: %d" % citations in files["SEAL.md"]


def test_a_normative_leak_is_refused_not_recorded():
    """A path outside the bundle in a *rule* must stop the build.

    The citation exemption is for comments only. Widening it by accident — say,
    by scanning with the comment prefix of the wrong file type — would turn the
    seal into a formality, so the refusal is pinned by a test rather than by the
    docstring that describes it.
    """
    files = {"manual/MANUAL.md": "The Cart moves as ../artifacts/trace.jsonl "
                                 "shows.\n"}
    findings = handover.context_report(files)
    assert findings and all(f.severity == "blocking" for f in findings)


def test_a_comment_leak_is_a_citation():
    files = {"manual/MANUAL.dsl": "rule walk  # see ../THEORIZE_LOG.md T-9\n"}
    findings = handover.context_report(files)
    assert findings and all(f.severity == "citation" for f in findings)


@pytest.mark.parametrize("name", NAMES)
def test_scan_exclusions_are_declared_to_the_reader(name):
    files = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    for excluded in handover.SCAN_EXCLUDE:
        assert excluded in files["SEAL.md"]


# =========================================================================
# self-containedness of the content
# =========================================================================

@pytest.mark.parametrize("name", NAMES)
def test_two_boards_and_they_differ(name):
    files = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    boards = sorted({p.split("/")[1] for p in files
                     if p.startswith("levels/")})
    assert len(boards) >= 2
    payloads = {b: files["levels/%s/LEVEL.json" % b] for b in boards}
    assert len(set(payloads.values())) == len(boards)


@pytest.mark.parametrize("name", NAMES)
def test_every_primitive_the_manual_uses_is_defined(name):
    files = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    ast = parse_theory(files["manual/MANUAL.dsl"])
    page = files["manual/PRIMITIVES.md"]
    for primitive in handover._primitives_used(ast):
        assert "`%s" % primitive in page, primitive


@pytest.mark.parametrize("name", NAMES)
def test_every_declared_event_says_what_it_does(name):
    """The manual declares `slid(o, p, dir)` and never says how far a slide goes.

    That number decides every step-semantics answer, so a package that shipped
    the declaration alone would be unreadable on its central question. The
    check is that each declared event's name reaches `PRIMITIVES.md`.
    """
    files = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    ast = parse_theory(files["manual/MANUAL.dsl"])
    page = files["manual/PRIMITIVES.md"]
    alternatives = handover._event_alternatives(ast)
    assert alternatives
    for alt in alternatives:
        assert "`%s(" % alt.name in page, alt.name


@pytest.mark.parametrize("name", NAMES)
def test_glossary_shows_the_level_data_seam(name):
    files = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    glossary = files["GLOSSARY.md"]
    assert "Supplied by each board" in glossary
    assert "**differs**" in glossary, (
        "a glossary in which nothing differs between the two boards is not "
        "demonstrating the domain/problem split, it is asserting it")


@pytest.mark.parametrize("name", NAMES)
def test_readme_states_every_missing_form(name):
    files = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    manifest = json.loads(files["MANIFEST.json"])
    for key, value in manifest["forms"].items():
        if value["status"] != "generated":
            assert key in files["README.md"], (
                "form %s was refused and README.md does not say so; a reader "
                "would look for it and conclude they had missed it" % key)


@pytest.mark.parametrize("name", NAMES)
def test_no_plan_is_shipped(name):
    """1.9's anti-cheat, checked on the artefact rather than on the grammar.

    The playbook grammar has no sentence form for a sequence of actions, so a
    plan cannot arrive through the playbook. It could still arrive through a
    file somebody added to the package, and the handover degenerates into
    passing notes the moment one does.
    """
    files = handover.read_package(os.path.join(PACKAGE_ROOT, name))
    for path, text in files.items():
        if path.endswith(".lean") or path.endswith("predictor.py"):
            continue
        lowered = text.lower()
        for phrase in ("the solution is", "the plan is", "optimal plan",
                       "solution:", "plan:"):
            assert phrase not in lowered, "%s: %r" % (path, phrase)


# =========================================================================
# refusals
# =========================================================================

def test_one_board_is_refused():
    spec = builder.cart_package()
    one = handover.PackageSpec(
        world_id=spec.world_id, title=spec.title, manual_dsl=spec.manual_dsl,
        playbook_dsl=spec.playbook_dsl, levels=(spec.levels[0],))
    with pytest.raises(handover.HandoverError, match="two boards"):
        handover.build_files(one)


def test_an_undefined_primitive_is_refused():
    manual = (
        "word_table:\n"
        "  board\n"
        "  object Cart { pos: Coord }\n"
        "semantics:\n"
        "  frame persist\n"
        "  conflict exclusive\n"
        "  cascade single_frame\n"
        "events:\n"
        "  event moved(o, dir)\n"
        "rules:\n"
        "  rule drift\n"
        "    when act=push(Cart, up) and glimmers(above(Cart)) "
        "then moved(Cart, up)\n"
        "goal:\n"
        "  goal Cart.pos = (0, 0)\n")
    ast = parse_theory(manual)
    with pytest.raises(handover.UnrenderableClause, match="glimmers"):
        handover.render_primitives(ast)


def test_an_undeclared_event_meaning_is_refused():
    manual = (
        "word_table:\n"
        "  board\n"
        "  object Cart { pos: Coord }\n"
        "semantics:\n"
        "  frame persist\n"
        "  conflict exclusive\n"
        "  cascade single_frame\n"
        "events:\n"
        "  event shimmered(o, dir)\n"
        "rules:\n"
        "  rule drift\n"
        "    when act=push(Cart, up) and free(above(Cart)) "
        "then shimmered(Cart, up)\n"
        "goal:\n"
        "  goal Cart.pos = (0, 0)\n")
    ast = parse_theory(manual)
    with pytest.raises(handover.UnrenderableClause, match="shimmered/2"):
        handover.render_primitives(ast)
