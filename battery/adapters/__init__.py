"""Adapters: whatever a source produces -> `battery.model.Run`.

Adding a source means adding a module here.  No metric changes.
"""

from battery.adapters.a0 import load_a0_runs
from battery.adapters.a0_spike import load_a0_spike_runs
from battery.adapters.a2 import load_a2_runs
from battery.adapters.ledger_jsonl import load_campaigns, load_ledger_runs

__all__ = ["load_a0_runs", "load_a0_spike_runs", "load_a2_runs",
           "load_campaigns", "load_ledger_runs"]
