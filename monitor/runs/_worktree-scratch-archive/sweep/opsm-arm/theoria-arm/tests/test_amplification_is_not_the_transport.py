"""What `http_amplification` counts, and what a borrowed constant must admit.

Two committed numbers were wrong in the same way and neither was caught by a
test, because nothing asserted what either quantity *meant*:

* `Budget.as_json()["http_amplification"]` is `commands_sent / actions_ok`.
  `commands_sent` counts arm-level *attempts*, including attempts the proxy
  refuses before the wire. On `runs/20260729T004020Z-leg01` that was 2000
  attempts against 104 forwarded requests, so the field read 222.222 for a leg
  whose transport managed 11.6 -- and a mid-run reading of it, 86.7, went into a
  commit message, a class docstring and a test docstring as a measurement of the
  transport.
* `spend.HTTP_PER_COMMAND = 1.75` was commented as "measured post-cookie-fix",
  citing `Budget.as_json()["http_amplification"]`. No run of this arm has ever
  reported 1.75; it comes from INC-011's `bare_cc` cell, on a different arm,
  with cookies, in a different denominator.

Neither is fixed by choosing better numbers. They are fixed by making the code
state what it has and what it lacks, which is what these tests hold in place.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import budget as budget_mod                              # noqa: E402
from harness import spend as spend_mod                                # noqa: E402


def _budget(**kw):
    return budget_mod.Budget(actions=40, commands=2000, **kw)


def test_the_ratio_says_it_counts_attempts_not_outbound_requests():
    b = _budget()
    for _ in range(40):
        b.command()
    b.succeeded()
    payload = b.as_json()

    assert payload["attempt_amplification"] == 40.0
    assert payload["http_amplification"] == payload["attempt_amplification"]
    assert payload["http_amplification_is_really_attempts"] is True
    note = payload["http_amplification_note"]
    assert "never reached the network" in note
    assert "http.forwarded" in note, (
        "the note has to name the field that carries the real answer, or a "
        "reader who distrusts the number still cannot compute a better one")


def test_forty_attempts_for_one_action_is_not_forty_requests():
    """The storm's shape, in miniature: the ratio moves without the wire moving.

    This is the whole defect. `commands_sent` climbs on refusals, `actions_ok`
    does not, and the quotient grows without bound while nothing leaves the
    machine. A test that only checked `40.0 == 40.0` would pass on the broken
    reading too, so what is asserted is that the quantity is *labelled*.
    """
    b = _budget()
    b.succeeded()
    first = b.as_json()["attempt_amplification"]
    for _ in range(100):
        b.command()
    second = b.as_json()["attempt_amplification"]

    assert second > first
    assert b.actions_ok == 1, "no action succeeded; only the attempt counter moved"


def test_the_sizing_constant_admits_it_was_never_measured_here():
    assert spend_mod.HTTP_PER_COMMAND_IS_VALIDATED is False, (
        "if this arm has finally measured its own transport in this constant's "
        "denominator, replace the constant and flip this -- do not flip it alone")
    provenance = spend_mod.HTTP_PER_COMMAND_PROVENANCE
    assert "INC-011" in provenance
    assert "bare_cc" in provenance, "the borrowing arm must be named"
    assert "denominator" in provenance, (
        "the denominator mismatch is the part a reader is most likely to miss, "
        "because the value looks plausible either way")


def test_every_plan_carries_the_fact_that_its_constant_is_borrowed():
    """A reservation is a claim about the future. This one has to show its basis."""
    caps = spend_mod.plan_caps(actions=40, commands=2000, cost_ceiling_usd=20.0,
                               require_headroom=False)
    arithmetic = caps.arithmetic if hasattr(caps, "arithmetic") else caps["arithmetic"]
    assert arithmetic["http_per_command"] == spend_mod.HTTP_PER_COMMAND
    assert arithmetic["http_per_command_is_validated"] is False
    assert "INC-011" in arithmetic["http_per_command_provenance"]
