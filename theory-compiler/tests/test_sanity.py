"""Sanity check: package is importable."""


def test_import():
    import theory_compiler
    assert theory_compiler.__doc__ is not None
