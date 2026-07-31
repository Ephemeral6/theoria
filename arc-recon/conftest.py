"""One autouse guard: no test may write into `arc-recon/data/`.

Every fixture in this suite that redirects a writer says some version of
"nothing here touches data/". On 2026-07-31 two of them were wrong, and had
been for as long as `campaign_freeze_log.jsonl` had existed:
`test_hygiene.py::sandbox` and `test_canary_schedule.py::sandbox` redirected
`CANARY_PATH`, `RUNS_PATH`, `FREEZE_PATH` and `INCIDENTS_PATH` -- the four
constants that existed when they were written -- and never learned about
`FREEZE_LOG_PATH`, which `canary.freeze_campaigns` began appending to later.
So every full run of this suite appended six fabricated freeze events
(INC-TEST, INC-998, INC-999) to a tracked, append-only file, and the first six
of them were committed with the instrument itself.

That is worse than untidy. `campaign_freeze_log.jsonl` is the record the
overwritable state file is audited *against* (`canary.freeze_audit`); a suite
that can write freeze transitions into it can manufacture the evidence the
audit reads. A comment promising isolation is not isolation, and the promise
had already gone stale once by the time anyone checked.

So the promise is executable now. The guard is a `stat` snapshot rather than a
digest: it is per-test and has to be cheap, and size-plus-mtime catches an
append, a rewrite and a deletion, which is every way a test can leave a mark.
It is a detector, not a sandbox -- a test that writes and restores byte for
byte would pass. That is the right trade: the failure mode it exists for is
the silent accumulating append, not a forger.

New files count too: a test that creates `data/whatever.json` is exactly as
much of a leak as one that appends to a tracked file, and is likelier to be
missed because nothing shows up in `git diff` for an ignored name.
"""

import os

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")


def _snapshot():
    if not os.path.isdir(DATA_DIR):
        return {}
    out = {}
    for name in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, name)
        if os.path.isfile(path):
            info = os.stat(path)
            out[name] = (info.st_size, info.st_mtime_ns)
    return out


@pytest.fixture(autouse=True)
def data_dir_is_read_only():
    before = _snapshot()
    yield
    after = _snapshot()
    changed = sorted(
        name for name in set(before) | set(after)
        if before.get(name) != after.get(name)
    )
    assert not changed, (
        "this test wrote into arc-recon/data/: %s. That directory is the "
        "programme's record -- the ledgers, the incident file and the "
        "append-only campaign_freeze_log.jsonl the freeze audit reads. "
        "Redirect the writer with monkeypatch (see test_campaign_freeze.py's "
        "sandbox fixture, which patches every *_PATH constant canary.py "
        "writes to) rather than letting the suite edit the record."
        % ", ".join(changed))
