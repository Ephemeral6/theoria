"""Tools that operate on ledgers rather than producing them.

`LEDGER_FORMAT.md` promised two of these before either existed. They exist now:

    python -m proxy.tools.validate_ledger <path>     # §18: check any stream
    python -m proxy.tools.upgrade_ledger  <path>     # §7: lift v0 into v1.0
"""
