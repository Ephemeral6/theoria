"""Resource-side checks: invariants that belong to an artefact, not to a writer.

`arc-recon` is otherwise flat — every module sits beside the others and is
imported by bare name with the directory on `sys.path`. This is a package so
that `from tools import ledger_invariants` works from `arc-recon/` without a
second path insertion in every caller, and so that the distinction the
directory name makes is legible: nothing in here writes anything.
"""
