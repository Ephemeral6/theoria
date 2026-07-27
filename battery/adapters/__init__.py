"""Adapters: whatever a source produces -> `battery.model.Run`.

Adding a source means adding a module here.  No metric changes.
"""

from battery.adapters.a0 import load_a0_runs
from battery.adapters.ledger_jsonl import load_ledger_runs

__all__ = ["load_a0_runs", "load_ledger_runs"]
