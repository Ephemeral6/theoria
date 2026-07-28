import os
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if REPO not in sys.path:
    sys.path.insert(0, REPO)


@pytest.fixture(scope="session", autouse=True)
def _scratch_spend_pool(tmp_path_factory):
    """Every test in this suite spends against a throwaway pool, not the real one.

    The proxies now take a spend reservation before they will open a socket, so
    without this fixture a test that constructs an `EnvProxyConfig` would append
    its fictional dollars to `proxy/var/spend_gate.jsonl` -- the tracked,
    shared, cross-session pool a live campaign reads to decide whether it may
    spend. Test money in that file is not a cosmetic problem: it would eat real
    headroom, and the gate is deliberately unable to tell the difference.

    Session-scoped and autouse, so it holds for tests that have not been written
    yet. That is the point -- the failure it guards against is somebody adding a
    proxy test without knowing the pool exists, which is the same shape as the
    failure the gate itself was raised to stop.
    """
    from proxy.spend_gate import SpendGate, SpendPolicy, set_default_gate

    directory = tmp_path_factory.mktemp("spend-pool")
    policy = SpendPolicy({
        "v": "1.0", "pool": "test-scratch",
        "usd_ceiling": 1_000_000.0, "action_ceiling": 100_000_000,
        "ledger": str(directory / "spend_gate.jsonl"),
        "default_ttl_seconds": 86400, "lock_timeout_seconds": 30.0,
        # Small per-proxy defaults against an enormous ceiling: the
        # suite builds well over a hundred proxies, each of which claims a
        # default reservation, and held headroom accumulates until the
        # holder releases. That accumulation is the gate working -- so the
        # scratch pool is sized for it rather than the gate loosened.
        "default_run_caps": {"usd": 1.0, "actions": 100},
    }, source=None)
    previous = set_default_gate(SpendGate(policy))
    try:
        yield
    finally:
        set_default_gate(previous)
