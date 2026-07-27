"""The double proxy: Phase 1's record surface.

Two HTTP proxies stand between an arm and the outside world:

    proxy.env_proxy     the arm's only route to the ARC environment
    proxy.model_proxy   the arm's only route to a model provider

An arm changes one environment variable each and is otherwise untouched. It
holds no credential: both keys are injected inside the proxies. Sealing is
therefore a property of the construction, not of anyone's discipline.

`LEDGER_FORMAT.md` is the normative spec; `proxy.ledger` is its executable
form.
"""

__version__ = "1.0"

LEDGER_VERSION = "1.0"
