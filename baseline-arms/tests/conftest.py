"""Shared fixtures. Chiefly: a spend pool that is not the real one.

`proxy/var/spend_gate.jsonl` is the machine's single register of money spent
against one ARC key and one Anthropic bill, and it is append-only because it is
money. A test that reserved against it would put fictional dollars into a total
other sessions make decisions from, and nothing could take them out again. So
every test here gets its own pool under `tmp_path`, constructed from a literal
policy rather than the tracked one -- the same escape hatch
`proxy/tests/conftest.py` uses, and for the same reason.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from harness import spend  # noqa: E402


@pytest.fixture
def scratch_gate(tmp_path):
    """A `SpendGate` on a private pool. Never the tracked one."""
    return spend.SpendGate(policy=spend_policy(tmp_path))


def spend_policy(tmp_path, usd_ceiling=10.0, action_ceiling=500):
    from proxy.spend_gate import SpendPolicy
    return SpendPolicy({
        "pool": "test-pool",
        "usd_ceiling": usd_ceiling,
        "action_ceiling": action_ceiling,
        "ledger": str(tmp_path / "spend_gate.jsonl"),
        "default_run_caps": {"usd": 1.0, "actions": 10},
        "default_ttl_seconds": 600,
    })


@pytest.fixture
def scratch_binding(scratch_gate):
    """A live claim on the private pool, ready to hand to an ArcClient."""
    reservation = scratch_gate.reserve("test-campaign", 5.0, 200)
    return spend.SpendBinding(scratch_gate, reservation)
