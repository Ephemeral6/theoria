"""The arm's own tooling, kept out of `tools/` on purpose.

`cold-start-a2/`, `cold-start-a3/`, `engine-rig/`, `theory-compiler/` and `exam/`
each ship a top-level `tools/` package, and several of them sit ahead of this arm
on `sys.path`. A `tools/` here would therefore be answered by somebody else's
code, which is precisely what `tests/test_no_shadow.py` exists to forbid -- and
it duly turned `verify.sh` red the first time A15 put a module in `tools/`.

`theoria-arm/armtools/` solved the same problem the same way; this is that
convention, applied to the ablation arm.
"""
