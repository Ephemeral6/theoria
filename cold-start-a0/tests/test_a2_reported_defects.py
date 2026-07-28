"""The two defects `cold-start-a2` reported on PARTNER_SYNC (2026-07-28T08:05Z).

Both were invisible from inside A0 and both were found by running A0's own
instruments on a second world. They are recorded as `cold-start-a2/DECISIONS.md`
D-A2-006 and D-A2-007; A2 worked around them in its own directory and did not
edit this track's files, so the fixes land here.

Each test below fails on the code as it stood before this module existed. That
is the point of writing them: a regression test that never went red is a test of
nothing.
"""

import io
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import _bootstrap  # noqa: F401,E402

from certify import lean_check  # noqa: E402

GENERATED = os.path.join(ROOT, "theory", "generated")
GENERATED_NB = os.path.join(ROOT, "theory", "generated_no_button")

needs_generated = pytest.mark.skipif(
    not os.path.exists(os.path.join(GENERATED, "domain.pddl")),
    reason="run `python run_all.py` first",
)


# ------------------------------------------------------- D-A2-006 · grounding

def _parameter_types(domain_text):
    """Every type that appears as an action parameter, per action."""
    out = {}
    for match in re.finditer(r"\(:action\s+(\S+)(.*?)\n\s*\)", domain_text, re.S):
        name, body = match.group(1), match.group(2)
        params = re.search(r":parameters\s*\((.*?)\)", body, re.S)
        if not params:
            continue
        out[name] = set(re.findall(r"-\s*(\S+)", params.group(1)))
    return out


def _object_types(problem_text):
    """Type -> the object names declared with it, from the `:objects` block."""
    block = re.search(r"\(:objects(.*?)\n\s*\)", problem_text, re.S).group(1)
    out = {}
    for line in block.splitlines():
        if "-" not in line:
            continue
        names, _, type_name = line.rpartition("-")
        out.setdefault(type_name.strip(), set()).update(names.split())
    return out


@needs_generated
@pytest.mark.parametrize("directory", [GENERATED, GENERATED_NB])
def test_every_action_parameter_type_has_an_instance(directory):
    """A typed parameter with no inhabitant makes its action vanish silently.

    D-A2-006's failure mode exactly: `teleport-down` takes `?p - markedcell`,
    the Portal is a *static* coloured cell so it is in neither `problem.arena`
    nor the emitted `:objects`, no `markedcell` instance exists, the action
    never grounds, and the planner reports UNSAT on a manual that contains the
    teleport rule. Nothing errors. A0 got a correct answer anyway because its
    goal was reachable through the Door; A2's was not, and the control manual
    came back UNSAT on the first attempt.
    """
    domain_path = os.path.join(directory, "domain.pddl")
    problem_path = os.path.join(directory, "problem.pddl")
    if not os.path.exists(domain_path):
        pytest.skip("%s not generated" % directory)

    domain = open(domain_path, encoding="utf-8").read()
    problem = open(problem_path, encoding="utf-8").read()
    by_action = _parameter_types(domain)
    instances = _object_types(problem)

    # Subtypes count as inhabitants of their supertype.
    subtypes = {}
    types_block = re.search(r"\(:types(.*?)\)", domain, re.S).group(1)
    for line in types_block.splitlines():
        if "-" not in line:
            continue
        names, _, parent = line.partition("-")
        for name in names.split():
            subtypes.setdefault(parent.strip(), set()).add(name)

    def inhabited(type_name):
        if instances.get(type_name):
            return True
        return any(inhabited(child) for child in subtypes.get(type_name, ()))

    empty = sorted({(action, t) for action, types in by_action.items()
                    for t in types if not inhabited(t)})
    assert not empty, (
        "these action parameters have no object of their type in %s, so the "
        "action grounds to nothing and the planner answers UNSAT without "
        "saying why: %s" % (problem_path, empty))


@needs_generated
def test_the_portal_cell_is_addressable_but_not_occupiable():
    """The narrow claim, so the fix cannot be "make everything passable".

    A cell a guard names by colour must exist as an object (so `teleport-down`
    grounds) and must **not** be `passable` (so a move action still cannot step
    onto it). Addressable, not occupiable — A2's phrasing, and the reason its
    workaround touched only the PDDL side while Lean and Python kept the
    unaugmented arena.
    """
    problem = open(os.path.join(GENERATED, "problem.pddl"), encoding="utf-8").read()
    instances = _object_types(problem)
    marked = instances.get("markedcell", set())
    assert marked, "no markedcell instance: the Portal has no PDDL object"
    passable = set(re.findall(r"\(passable (\S+)\)", problem))
    assert not (marked & passable), (
        "markedcell(s) %s are passable; a move action can step onto the Portal"
        % sorted(marked & passable))


@needs_generated
def test_teleport_down_can_actually_ground():
    """The end-to-end form: at least one binding satisfies the static facts."""
    domain = open(os.path.join(GENERATED, "domain.pddl"), encoding="utf-8").read()
    problem = open(os.path.join(GENERATED, "problem.pddl"), encoding="utf-8").read()
    if "teleport-down" not in domain:
        pytest.skip("this manual has no teleport rule")
    marked = _object_types(problem).get("markedcell", set())
    adj_down = set(re.findall(r"\(adj-down (\S+) (\S+)\)", problem))
    assert any(below in marked for _above, below in adj_down), (
        "no cell has a markedcell below it, so `(adj-down ?from ?p)` with "
        "`?p - markedcell` has no binding and teleport-down still cannot fire")


# ---------------------------------------------------- D-A2-007 · the decoding

class _FakeCompleted:
    def __init__(self, stdout, stderr=b"", returncode=1):
        self.stdout, self.stderr, self.returncode = stdout, stderr, returncode


# Lean's own error prose. U+2019 and the anonymous-constructor brackets are the
# two that bit A2; under a GBK console `text=True` raises UnicodeDecodeError
# while decoding them, so the diagnostic is destroyed exactly when there is one.
LEAN_ERROR = (
    "theory.lean:769:2: error: decide proved that the proposition\n"
    "  ⟨inv, closed⟩ ’s invariant holds\n"
    "is false\n"
).encode("utf-8")


def test_lean_output_is_decoded_as_utf8_not_by_the_process_locale(monkeypatch):
    """`text=True` decodes with the locale encoding. Here that is GBK.

    A0 never had a red Lean file, so it never hit this. A2 keeps one on purpose
    — `generated_repaired_stale/` holds the refuted certificate and its error
    message *is* the evidence — and lost the message to a `UnicodeDecodeError`
    raised inside subprocess's reader thread.
    """
    calls = {}

    def fake_run(argv, **kwargs):
        calls.update(kwargs)
        return _FakeCompleted(LEAN_ERROR)

    monkeypatch.setattr(lean_check, "find_lean", lambda: "lean")
    monkeypatch.setattr(subprocess, "run", fake_run)

    report = lean_check.check(os.path.join(GENERATED, "theory.lean"))

    assert not calls.get("text"), (
        "the toolchain is still being read in text mode, i.e. decoded with "
        "whatever the process locale happens to be")
    assert not report["green"]
    assert any("decide proved" in line for line in report["errors"]), (
        "the error line did not survive decoding: %r" % (report["errors"],))
    assert any("’" in line for line in report["output"]), (
        "the non-ASCII characters were lost or mangled")


def test_undecodable_bytes_do_not_take_the_diagnostic_down(monkeypatch):
    """Malformed UTF-8 must degrade to replacement characters, never raise.

    `errors="replace"` and not `errors="strict"`: a mangled byte in the middle
    of a stack trace is not a reason to lose the whole report.
    """
    monkeypatch.setattr(lean_check, "find_lean", lambda: "lean")
    monkeypatch.setattr(
        subprocess, "run",
        lambda argv, **kw: _FakeCompleted(b"error: bad byte \xff here\n"))
    report = lean_check.check(os.path.join(GENERATED, "theory.lean"))
    assert not report["green"]
    assert any("bad byte" in line for line in report["errors"])


def test_a_green_report_still_reads_the_axiom_lines(monkeypatch):
    """The positive control: fixing the decoding must not change the verdict."""
    monkeypatch.setattr(lean_check, "find_lean", lambda: "lean")
    monkeypatch.setattr(
        subprocess, "run",
        lambda argv, **kw: _FakeCompleted(
            b"'unsolvable' does not depend on any axioms\n", returncode=0))
    report = lean_check.check(os.path.join(GENERATED, "theory.lean"))
    assert report["green"]
    assert report["axiom_reports"] == [{"name": "unsolvable", "axioms": []}]


# ------------------------------- found while verifying the two fixes above

@needs_generated
@pytest.mark.parametrize("directory", [GENERATED, GENERATED_NB])
def test_the_semantics_section_is_rendered_exactly_once(directory):
    """Two renderings of the same three facts, in two wordings, one document.

    `compile_a0.render_markdown` appended its own "How a Turn Works" from the
    A0 dialect, from back when the shared `gen_markdown` had none. The shared
    one has had it since `semantics:` was adopted into the contract, so every
    `theory.md` carried the section twice — once in place after the word table
    ("if no rule applies to something…") and once stranded at the end after the
    laws ("if no rule applies to an object…").

    Noticed by `cold-start-a2` while running these backends on a second world.
    A duplicated section is not a typo: a reader who finds two statements of
    the frame axiom has to work out whether they say the same thing, and the
    whole point of the section is that this fact be unambiguous.
    """
    path = os.path.join(directory, "theory.md")
    if not os.path.exists(path):
        pytest.skip("%s not generated" % directory)
    text = open(path, encoding="utf-8").read()
    assert text.count("## How a Turn Works") == 1, (
        "%s renders the semantics section %d times"
        % (path, text.count("## How a Turn Works")))
