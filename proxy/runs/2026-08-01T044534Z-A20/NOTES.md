# 2026-08-01T044534Z-A20 · running notes

Prompt A20 · branch agent/a20-a21-proxy-seal-pair · base 4c08ea6
Opened 2026-08-01T04:45:34Z

Two board items on one branch, both `proxy` territory, by the monitor's explicit
authorisation (the board allows one claimed item per territory, so A21 was hidden
from claiming; its claim/done bookkeeping is the monitor's after merge).

## Recon findings that changed the plan

1. **The sibling file named in the 工单 is not in this territory.**
   `proxy/tests/test_bypass_negative.py` does not exist; the file is
   `theoria-arm/tests/test_bypass_negative.py`. Read it read-only for style — its
   three-property structure (refusal / recording / stripping-asserted-as-outcome)
   is what the new file follows, including the discipline of asserting on *what
   the upstream received* rather than on what the ledger says.

2. **The ablation arm asked for a different name than the 工单 specifies.**
   `ablation-arm/DECISIONS.md` D-AB-004 and `ablcore/ledger_abl.py:9-30` record
   `requested_arm_name: "theoria_ablate"`. The 工单 says `ablation`, CONTRACTS/
   reserves nothing, and `LEDGER_FORMAT.md` named no ablation arm at all.
   Registered `ablation` per the 工单; the divergence is deliberate (a
   `theoria_`-prefixed name re-merges the two arms under any prefix group-by) and
   is pinned by a test plus handed to that arm's owner in PARTNER_SYNC.

3. **`.env` resolves through `proxy/paths.py`'s `__file__`**, so in a worktree it
   points at `.worktrees/a20/.env`, which does not exist (`.env` is gitignored).
   The hygiene test is written to be correct in both states: absence means an
   empty declared set, which is *stricter* than the assertion, and is the
   65-of-65 condition itself. The mechanism gets its red/green from tmp_path
   fixtures so it is never resting on the ambient file.

4. **`ARMS` is a pinned contract surface.** Adding a name tripped
   `tests/test_contract_changes.py`, which is the announcement protocol working
   rather than a defect. `CONTRACT_CHANGES.md` §2's table classes "adding an arm
   to `ARMS`" as a widening: land it, record it in §5. Did exactly that (row
   C-008) after `python -m proxy.tools.contract` classified it
   `additive   arms gained 'ablation'` (`contract-verdict-before.txt`).

5. **A pre-existing doc/code drift, found in passing.** `LEDGER_FORMAT.md`'s
   `arm` row listed five names while `ARMS` held six — `mock_arm` was registered
   in code and never written into the canon, and nothing compared the two. Both
   are now listed and `tests/test_ledger_format_sync.py` gained an
   arm-vocabulary gate with negative controls in both directions.

## Red-flip evidence (a test that cannot go red is not a test)

* `redflip-dotenv.txt` — the live `.env` assertion made to fail, by writing a
  temporary **gitignored** `.env` declaring `ANTHROPIC_API_KEY` with a synthetic
  value. Confirmed `git check-ignore` first, confirmed the failure output prints
  the **name only**, then removed the file and re-ran green. This is the
  demonstration that the live check is not vacuous in a checkout that has a
  `.env`.
* `test_the_stripping_assertion_has_teeth` — monkeypatches
  `PASSTHROUGH_REQUEST_HEADERS` to include `authorization` and asserts the
  client's credential *does* then reach the vendor. Without it the stripping
  test could be passing because the request never left, or because urllib
  dropped a header, and nobody would know.

## Scope discipline

* `verify-lab/` **not edited**. The board item's step 3 asks for an appendix in
  `verify-lab/DUAL_PROXY.md`; the dispatch forbids editing that territory. S32 is
  cited from the test docstring and D-A20-001 instead. Disclosed as a gap.
* `ablation-arm/` **not edited** (A21-2). Handover is the PARTNER_SYNC 下一步 line.
* No network, no API call, no model call, $0.00. Every "vendor" and "upstream" in
  the new tests is a `http.server` on 127.0.0.1.
* No credential value read, printed or written. The `.env` work is by variable
  **name** only, and the reader is itself tested for that property.
* No sealed-pile game id written anywhere. The new tests use `ar25-0c556536`
  (development pile) where they need an id at all.
