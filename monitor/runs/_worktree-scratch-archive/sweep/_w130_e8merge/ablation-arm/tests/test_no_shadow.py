"""No arm-owned top-level name may be silently answered by another tree.

`_bootstrap`'s docstring states the rule this file enforces: *"package names
never shadow. Everything this arm owns is under `ablcore`, `arms` or `tests`."*
When that sentence was written it was true. It stopped being true at S14
(127edab, 2026-07-28T23:38), which gave eleven territories a top-level
`verify.py` — and this arm's root is *behind* four upstream roots on `sys.path`,
so from that commit `import verify` in `tests/test_verify.py` returned
`cold-start-a2/verify.py`. Ten tests went red. The arm's own gate ran them last,
so `verify.sh` went red too, and it stayed that way because nothing in the arm
could say *why*.

The failure is not that `verify` collided. It is that a collision could happen
without any test naming it. So this file does not assert "there are no
collisions" — there is one, it is real, and `_armimport.arm_module` handles it.
It asserts that **every collision is one the arm has declared**, so the next one
fails here, immediately, with the offending path in the message.
"""

from __future__ import annotations

import os
import sys

import pytest

import _bootstrap
from _armimport import arm_module

ARM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Names this arm owns at its own root that an upstream root also answers.
#: Every entry is a live shadow, and every entry must be loaded through
#: `_armimport.arm_module`. Adding a name here is a deliberate act; the test
#: below fails when reality grows one that is not listed.
DECLARED_SHADOWS = {
    "verify": "S14 127edab gave eleven territories a top-level verify.py",
}


def _arm_top_level_names() -> set[str]:
    """Every top-level module and package name the arm root offers."""
    names = set()
    for entry in os.listdir(ARM):
        full = os.path.join(ARM, entry)
        if entry.startswith((".", "_")):
            continue
        if entry.endswith(".py") and os.path.isfile(full):
            names.add(entry[:-3])
        elif os.path.isdir(full) and os.path.isfile(os.path.join(full, "__init__.py")):
            names.add(entry)
    return names


def _shadowing_root(name: str) -> str | None:
    """The first `sys.path` entry ahead of ARM that also answers `name`."""
    for root in sys.path:
        if not root or os.path.abspath(root) == ARM:
            return None                      # the arm answers first: no shadow
        if not os.path.isdir(root):
            continue
        if (os.path.isfile(os.path.join(root, name + ".py"))
                or os.path.isfile(os.path.join(root, name, "__init__.py"))):
            return root
    return None


def test_every_shadowed_name_is_one_the_arm_declared():
    """A new collision must fail here, not eighty minutes later in a gate."""
    found = {n: _shadowing_root(n) for n in sorted(_arm_top_level_names())}
    shadowed = {n: r for n, r in found.items() if r is not None}
    undeclared = {n: r for n, r in shadowed.items() if n not in DECLARED_SHADOWS}
    assert not undeclared, (
        "arm-owned top-level name(s) answered by another tree first: "
        + "; ".join(f"{n} <- {r}" for n, r in sorted(undeclared.items()))
        + ". Load them through tests/_armimport.arm_module and declare them in "
          "DECLARED_SHADOWS, or the next `import` of one silently tests "
          "somebody else's code."
    )


def test_the_declared_shadows_are_still_real():
    """The other direction. A stale declaration hides a rule that came back."""
    for name in DECLARED_SHADOWS:
        assert name in _arm_top_level_names(), f"{name}: the arm no longer owns it"
        assert _shadowing_root(name) is not None, (
            f"{name}: declared as shadowed, but nothing on sys.path ahead of the "
            "arm answers it any more. Drop it from DECLARED_SHADOWS and let the "
            "plain import back."
        )


def test_the_shadow_this_arm_has_is_the_one_it_thinks_it_has():
    """`verify` really does resolve upstream, and `arm_module` really fixes it.

    The negative control for the two tests above: if `import verify` had quietly
    started resolving to the arm again, they would both still pass while saying
    nothing.
    """
    import verify as plainly_imported                              # noqa: PLC0415

    assert os.path.abspath(plainly_imported.__file__) != os.path.join(ARM, "verify.py")
    assert not hasattr(plainly_imported, "_assertions"), (
        "the upstream verify.py grew an `_assertions`; this test can no longer "
        "tell the two apart by shape and must compare paths only"
    )

    ours = arm_module("verify")
    assert os.path.abspath(ours.__file__) == os.path.join(ARM, "verify.py")
    assert hasattr(ours, "_assertions") and hasattr(ours, "_recorded")


def test_the_detector_fires_on_a_planted_collision(tmp_path, monkeypatch):
    """A guard nobody has seen refuse is a guard nobody has tested."""
    decoy = tmp_path / "decoy_root"
    decoy.mkdir()
    (decoy / "run_arm.py").write_text("# not this arm's\n", encoding="utf-8")
    monkeypatch.syspath_prepend(str(decoy))

    assert _shadowing_root("run_arm") == str(decoy)
    with pytest.raises(AssertionError, match="run_arm"):
        test_every_shadowed_name_is_one_the_arm_declared()


def test_bootstrap_is_why(monkeypatch):
    """Name the mechanism, so the fix is not mistaken for a test quirk."""
    arm_index = sys.path.index(ARM) if ARM in sys.path else len(sys.path)
    for root in _bootstrap.UPSTREAM_ROOTS:
        if root in sys.path:
            assert sys.path.index(root) < arm_index, (
                "this test encodes the observed order (upstream roots ahead of "
                "the arm). If that has been changed deliberately, the shadow may "
                "be gone and DECLARED_SHADOWS should shrink."
            )
