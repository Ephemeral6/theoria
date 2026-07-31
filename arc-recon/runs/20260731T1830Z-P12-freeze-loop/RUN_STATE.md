# P-12 · the campaign-freeze loop's remaining half

Territory: `arc-recon`. Offline throughout — no API call, no model call, no
dollars. Development-pile game ids only (`ar25-0c556536`, `g50t-5849a774`,
`sk48-d8078629`); no sealed-pile id appears in anything written here.

## What the ticket said, and what was actually there

The ticket described `campaign_freeze.json` as absent and the circuit as
detection-only. That was true when it was written and is not true now:
commit `5def1911` (2026-07-31) landed the writing half — drift freezes, a
green sweep refreshes, `init-freeze` creates the file offline, a green sweep
never thaws — and `theoria-arm/harness/freeze_gate.py` landed the reading half
and is called from `campaign.py`'s launch path beside `assert_launch_cleared`
and `assert_dev_pile`. So the arm-side wiring the ticket asked me to propose
already exists, and proposing it again would be noise.

Three things genuinely did not exist. Two are now built; the third is a
finding this territory cannot fix alone and went to the inbox.

## 1 · `how_to_clear` had no command behind it

Every frozen file since the first commit has carried a `how_to_clear`
paragraph saying clearing is *"an owner decision recorded as an incident, not
a housekeeping step"*. Nothing implemented it. The only available clearing was
opening the tracked JSON and changing `true` to `false` — which records no
reason, names no owner, files no incident, and in a diff is indistinguishable
from vandalism.

`canary.py clear-freeze` is that command. It is deliberately more expensive
than the edit it replaces:

* `--reason` is required and stored verbatim in the state file *and* in the
  append-only log, where nobody can soften it later;
* `--by` is required — the tooling does not get to be the owner;
* `--adjudication INC-0NN` must name an incident that already exists in
  `incidents.jsonl`; citing an adjudication nobody wrote down is refused;
* clearing files its own incident, so it is as visible as the drift was;
* **`checked_utc` is not restored.** An owner adjudicating a past observation
  has not made a new one. Only `replay --write-freeze` may stamp
  `checked_utc`, and until one runs the file says so in its `note`.

## 2 · The state file could be thawed with `rm`

`init_freeze_from_runs` refused to *overwrite* an existing file. It did not
refuse to *create* one. So `rm data/campaign_freeze.json && python canary.py
init-freeze` rebuilt an unfrozen file from `canary_runs.jsonl` with no memory
of any freeze written since that run — a thaw costing one deletion and one
offline command, in an instrument whose entire design forbids self-healing
(the `refresh_freeze` docstring spends a paragraph refusing exactly this for
green sweeps).

The fix is to ask the half that cannot be rewritten. `campaign_freeze.json` is
overwritten in place; `campaign_freeze_log.jsonl` is append-only. So:

* `canary.py freeze-audit` compares them — exit 0 `OK`, 1 `DIVERGED`,
  2 `UNADJUDICABLE_LOG`;
* `init-freeze` refuses when the log's last state-bearing event is a freeze
  whose incident really was filed;
* `assert_campaigns_unfrozen()` — the gate every track calls — now refuses on
  `DIVERGED` as well as on `frozen`;
* `clear-freeze` works even when the state file is missing, so deleting it is
  not a cheaper route than adjudicating it.

`green-while-frozen` is deliberately *not* state-bearing: a sweep that changed
nothing must not be able to answer "what should the state file say".

The rule that keeps `UNADJUDICABLE_LOG` from being an escape hatch: the drift
path files the incident *before* it freezes, so a `frozen` log entry naming an
id absent from `incidents.jsonl` never came from drift. And `incidents.jsonl`
is append-only too — the only way to make a fake freeze look real is to file a
real incident, at which point it is one.

## 3 · The suite was writing into `data/` — found by running it

`freeze-audit` on this repository's own data returns **`UNADJUDICABLE_LOG`,
6 entries** (`freeze_audit.json` beside this file): `campaign_freeze_log.jsonl`
was committed carrying `INC-TEST` / `INC-998` / `INC-999` lines that name
incidents which do not exist.

Chasing where they came from found a live defect. `test_hygiene.py::sandbox`
and `test_canary_schedule.py::sandbox` both promise *"nothing here touches
data/"* and both redirected only the four `*_PATH` constants that existed when
they were written. `FREEZE_LOG_PATH` was added to `canary.py` later and never
added to either fixture — so **every full run of the arc-recon suite appended
six fabricated freeze events to the tracked, append-only log.** The count went
7 → 13 → 19 across two baseline runs in this session before I noticed. The
first six were committed with the instrument itself.

That is worse than untidy: the log is the record the state file is *audited
against*. A suite that can append freeze transitions to it can manufacture the
evidence the audit reads.

Fixed in both fixtures, and the promise is executable now —
`arc-recon/conftest.py` holds one autouse `stat`-snapshot guard that fails any
test which changes, adds or removes a file in `arc-recon/data/`. It is a
detector, not a sandbox: a test that wrote and restored byte-for-byte would
pass. That is the right trade — the failure it exists for is the silent
accumulating append, not a forger.

The 12 lines written during this session were reverted with `git checkout`;
they were accidental writes to a tracked file, not history. The 6 committed
lines were **not** touched — the log is append-only and rewriting it to make
my own audit green would be the exact disease. They are reported instead.

## Gates

```
cd arc-recon && python -m pytest -q      →  349 passed in 525.40s
```

337 before (baseline on `master`), 349 after: +12 for `clear-freeze`,
`freeze-audit` and the `rm`-thaw negative control. The autouse guard added no
new failures, which is the useful part — after the two fixtures were fixed,
nothing else in the suite writes to `data/`.

## One more thing this run tripped over

`python canary.py freeze-audit --json > freeze_audit.json` produced a **CRLF**
file: Python's text-mode stdout translates on the way out on Windows. Git
stored the blob as LF, so the sha256 in the first draft of `MANIFEST.json` was
over bytes no checkout would ever contain. A manifest that cannot be
reproduced from a fresh checkout is a manifest you have to take on trust.

`arc-recon/.gitattributes` now pins LF, carrying over the rule
`proxy/.gitattributes` has had for the same reason, and the artefact was
rewritten through an explicit `newline=""` writer. The published digest
`sha256:5243cdff…5effd1a7` matches `git show`'s blob, checked rather than
assumed.

## Residual gaps, stated plainly

* **The arm reads only the state file.** `freeze_gate.assert_unfrozen()` opens
  `campaign_freeze.json` and nothing else, so the `DIVERGED` verdict that now
  stops `arc-recon`'s own gate is invisible to the arm's launch path. Delete
  the state file and the arm still launches. Filed as an inbox proposal with
  the exact patch — it is arm territory and I did not touch it.
* **The six committed log entries stay unadjudicable.** Annulling them is an
  owner decision; there is no command for it and I did not invent one.
* **`clear-freeze` has never run on a real freeze**, because no real freeze has
  ever occurred. Every path is covered by tests over sandboxed files.
* **`freeze-audit` is not in `arc-recon/verify.sh`.** Adding a gate that
  currently exits 2 on the repository's own data would turn `verify.sh` red for
  a condition an owner has to adjudicate, so wiring it belongs with the
  annulment, not before it.
