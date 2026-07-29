"""P2: engines.lp_potential check_exactly's inv_closed uses `< 0` not `<= 0`."""
from engines.lp_potential import potential as P
def _bad(certificate):
    b = certificate.initial_potential
    return {
        "inv_init": certificate.potential(certificate.initial) <= b,
        "inv_closed": all(m.delta(certificate.weights) < 0 for m in certificate.moves),
        "goal_break": all(certificate.potential(g) - b >= certificate.margin
                          for g in certificate.goal_states),
    }
P.check_exactly = _bad
