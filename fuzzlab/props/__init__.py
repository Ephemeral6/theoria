"""Per-engine property modules.

Each `fuzzlab/props/<engine>.py` exposes the same three names, so the campaign
can drive all six without knowing anything about any of them:

    FAMILY      the world family this engine is fuzzed with
    INVARIANTS  {name: callable(world) -> list[Finding]}
    check(world) -> list[Finding]

and `fuzzlab/props/test_<engine>.py` is the pytest/hypothesis front end for the
same functions.  The split is deliberate: the campaign needs findings it can
count and rank, pytest needs assertions, and neither should be reimplemented in
terms of the other.
"""

from fuzzlab.props import finding  # noqa: F401

ENGINES = (
    "mdl_segmenter",
    "cegis_miner",
    "zero_space",
    "lp_potential",
    "fd_adapter",
    "probe_frontier",
)


def load(engine: str):
    """Import a property module by engine name."""
    import importlib

    return importlib.import_module("fuzzlab.props.%s" % engine)
