"""exam -- the active half of the evaluation protocol (Theoria.md 1.11).

The battery is passive: it reads ledgers that already exist, costs nothing, and
can be recomputed over history.  The exam is active: it *sets questions* and
needs a new run.  Two instruments together are the protocol; neither alone is.

Nothing in this package opens a socket or spends an API call.  Every question is
set in a self-built world (A0 / A0' / A2), which is what makes the dress
rehearsal honest: by Phase 4 the question-setting procedure is already proven,
and only the per-game justification is constructed fresh.
"""

__all__ = ["model", "guard", "papers", "grading", "examinees", "leakage"]
