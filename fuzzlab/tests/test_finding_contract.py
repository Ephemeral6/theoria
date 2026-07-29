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
