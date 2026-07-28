"""An independent recheck of the certificates the engines hand upstream.

Nothing in this package imports `engines`.  That is the point: `ic3_pdr` and
`deadlock_carver` already ship checkers that re-derive their own three
conditions, but those checkers are handed the *engine's* `System` object --
built by the same module that built the search.  A transcription bug in that
construction certifies itself.  This package takes two files instead:

  * a **rule set** -- finite variables with explicit domains, an initial
    assignment, a goal predicate, and a list of guarded rules;
  * a **certificate** -- the set of states it is about, either written as a
    predicate or, for a pagoda, declared as weights and a bound and derived from
    them, together with the claim it is supposed to license.

and re-derives the transition relation itself, by grounding the rules over the
full product of the declared domains.  It never reads a precomputed edge list,
never takes a state space from the certificate, and never asks the engine
anything.

See `README.md` for the format and for the forgeries it is built to refuse.
"""

from recheck.certificate import Certificate, CertificateError, load_certificate
from recheck.ruleset import RuleSet, RuleSetError, load_ruleset
from recheck.verify import Verdict, recheck

__all__ = [
    "Certificate",
    "CertificateError",
    "RuleSet",
    "RuleSetError",
    "Verdict",
    "load_certificate",
    "load_ruleset",
    "recheck",
]
