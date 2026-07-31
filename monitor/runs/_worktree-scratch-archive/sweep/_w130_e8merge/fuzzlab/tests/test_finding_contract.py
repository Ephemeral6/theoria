"""No property may pass a keyword that collides with `finding`'s own parameters.

This test exists because the collision happened, silently, and survived a full
green campaign.

`props/probe_frontier.py:91` reported a `partition_matches_truth` violation as

    finding.violated(ENGINE, "partition_matches_truth", world, detail,
                     action=action, engine=normalised, truth=expected)

and `finding.violated(engine, invariant, world, detail, **data)` already binds
`engine` positionally. So the call raised `TypeError: violated() got multiple
values for argument 'engine'` — meaning **the only path that could report this
invariant could not report it**. The invariant was not weak; it was incapable.

Nothing caught it, and the reason is worth keeping:

* the line only runs when the engine partitions *wrongly*, and it never did, so
  the collision was never executed;
* had it executed, `run_invariants` would have converted the `TypeError` into a
  `raised` finding — the battery would have reported a crash where it meant to
  report a violation, and `BUGS.md`'s headline "0 violations" would have stayed
  true while a real defect went past;
* the standing campaign therefore reported this invariant as *checked* on 500
  worlds, and it was checked in the sense that it ran, never in the sense that
  it could have said no.

The mutation battery found it: four separate partition mutants produced
`raised` and zero `violated`. That is what a dead reporting path looks like from
outside.

The guard is parsed rather than grepped, for the reason `figures/verify.sh`
gate 7 gives: its first regex version's first finding was a phrase inside a
docstring, and a gate whose failures are mostly false is a gate people learn to
ignore. `ast` sees calls, not prose.
"""

import ast
import pathlib

import pytest

PROPS = pathlib.Path(__file__).resolve().parent.parent / "props"

# The positional parameters of each constructor in `props/finding.py`. A data
# key with one of these names is bound twice and the call dies.
RESERVED = {
    "violated": {"engine", "invariant", "world", "detail"},
    "skipped": {"engine", "invariant", "world", "reason"},
    "raised": {"engine", "invariant", "world", "exc"},
}


def _collisions(path: pathlib.Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name not in RESERVED:
            continue
        for keyword in node.keywords:
            if keyword.arg in RESERVED[name]:
                out.append((path.name, node.lineno, name, keyword.arg))
    return out


@pytest.mark.parametrize("path", sorted(PROPS.glob("*.py")), ids=lambda p: p.name)
def test_no_property_shadows_a_finding_parameter(path):
    found = _collisions(path)
    assert not found, "\n".join(
        "%s:%d passes %s=... to finding.%s(), which already binds it "
        "positionally -- this call raises TypeError instead of reporting"
        % (name, line, kw, fn) for name, line, fn, kw in found)


def test_the_guard_itself_catches_the_original_defect(tmp_path):
    """The negative control: shown failing on the code it was written for.

    A guard that has only ever been observed passing is a green light with
    nothing behind it — the standard this repository states in
    `figures/verify.sh` gate 8 and applies unevenly. So the pre-fix line is
    reconstructed here and the guard is required to see it.
    """
    original = tmp_path / "probe_frontier_before_fix.py"
    original.write_text(
        "from fuzzlab.props import finding\n"
        "def partition_matches_truth(world):\n"
        "    return [finding.violated(\n"
        "        'probe_frontier', 'partition_matches_truth', world, 'detail',\n"
        "        action='a', engine={'x': 1}, truth={'y': 2})]\n",
        encoding="utf-8")
    found = _collisions(original)
    assert [(f[2], f[3]) for f in found] == [("violated", "engine")]


def test_the_collision_really_is_fatal_at_runtime():
    """Not a style rule: pin that the shape the guard bans actually explodes.

    If `finding.violated`'s signature ever changed so that this became legal,
    the guard above would go on failing builds for a reason that had stopped
    being true.
    """
    from fuzzlab.props import finding

    class _World:
        family = "hypset"
        seed = 1

    with pytest.raises(TypeError, match="engine"):
        finding.violated("probe_frontier", "partition_matches_truth",
                         _World(), "detail", engine={"x": 1})


# ---------------------------------------------- every skip declares its cause
#
# V-21. `skipped` was one integer covering two questions with opposite answers:
# "the engine looked and correctly has nothing to say" and "a tool could not
# compute, so nobody knows". Summed, they cancel — which is how a starved solver
# spent a release looking like coverage. `cause` is now required by the
# signature; this is the second lock, because a signature only catches the call
# that runs, and the reporting lines here are the ones that run rarely.


class _World:
    family = "jumpgraph"
    seed = 1


def _skip_calls(path: pathlib.Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name == "skipped":
            yield node


@pytest.mark.parametrize("path", sorted(PROPS.glob("*.py")), ids=lambda p: p.name)
def test_every_skip_declares_a_cause(path):
    from fuzzlab.props import finding

    missing, undeclared = [], []
    for node in _skip_calls(path):
        keywords = {k.arg: k.value for k in node.keywords}
        if "cause" not in keywords:
            missing.append(node.lineno)
            continue
        value = keywords["cause"]
        # A literal, so the table in `CAUSE_CLASS` can be checked statically.
        # A computed cause would classify itself at runtime, which is the bucket
        # nobody reviews.
        if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
            undeclared.append((node.lineno, "not a string literal"))
        elif value.value not in finding.CAUSE_CLASS:
            undeclared.append((node.lineno, value.value))
    assert not missing, (
        "%s: finding.skipped() without a cause at line(s) %s -- a world nobody "
        "judged has to say why, or the coverage column cannot be audited"
        % (path.name, missing))
    assert not undeclared, (
        "%s: cause not declared in finding.CAUSE_CLASS: %s" % (path.name, undeclared))


def test_an_undeclared_cause_is_refused_at_the_call():
    """The signature's half of the lock, shown failing."""
    from fuzzlab.props import finding

    with pytest.raises(ValueError, match="undeclared skip cause"):
        finding.skipped("lp_potential", "three_conditions_hold", _World(),
                        "reason", cause="whatever_seemed_fine_at_the_time")


def test_a_missing_cause_is_a_type_error():
    from fuzzlab.props import finding

    with pytest.raises(TypeError, match="cause"):
        finding.skipped("lp_potential", "three_conditions_hold", _World(),
                        "reason")


def test_the_guard_catches_a_cause_that_was_never_classified(tmp_path):
    """The negative control for the `ast` guard, not only for the signature."""
    from fuzzlab.props import finding

    original = tmp_path / "props_with_a_new_bucket.py"
    original.write_text(
        "from fuzzlab.props import finding\n"
        "def p(world):\n"
        "    return [finding.skipped('e', 'i', world, 'r', cause='brand_new')]\n",
        encoding="utf-8")
    causes = [k.value.value for node in _skip_calls(original)
              for k in node.keywords if k.arg == "cause"]
    assert causes == ["brand_new"]
    assert "brand_new" not in finding.CAUSE_CLASS


def test_every_declared_cause_has_a_class():
    from fuzzlab.props import finding

    for cause, klass in finding.CAUSE_CLASS.items():
        assert klass in finding.CAUSE_CLASSES, (cause, klass)
    assert finding.CAUSE_CLASS["solver_unavailable"] == finding.UNAVAILABLE
    assert finding.CAUSE_CLASS["no_certificate"] == finding.DECLINED


# ------------------------------------------------ failures(): prose == code

def test_failures_counts_an_unexpected_raise():
    """V-21: the docstring said "violations and unexpected raises" and the body
    returned violations. The prose was the wider one, which is the direction that
    misleads. This pins the alignment in the direction the fix went."""
    from fuzzlab.props import finding

    world = _World()
    try:
        raise RuntimeError("nobody wrote a policy for this")
    except RuntimeError as exc:
        crash = finding.raised("lp_potential", "three_conditions_hold", world, exc)
    skip = finding.skipped("lp_potential", "three_conditions_hold", world,
                           "documented", cause="no_certificate")
    bad = finding.violated("lp_potential", "three_conditions_hold", world, "no")

    assert finding.failures([crash]) == [crash]
    assert finding.failures([bad]) == [bad]
    assert finding.failures([skip]) == [], (
        "a world nobody judged is not a world the engine got wrong; that is the "
        "coverage column's question, not this one")
    assert finding.failures([skip, crash, bad]) == [crash, bad]


def test_a_raised_finding_records_which_exception_it_was():
    from fuzzlab.props import finding

    try:
        raise ValueError("x")
    except ValueError as exc:
        crash = finding.raised("e", "i", _World(), exc)
    assert crash.cause == "ValueError"
    # `raised` is deliberately outside the taxonomy: it is the bucket nobody has
    # classified yet, and giving it a cause_class would imply someone had.
    assert crash.cause_class == ""
