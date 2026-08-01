# A20 + A21 — RUN_STATE

**Branch** `agent/a20-a21-proxy-seal-pair` · **base** `4c08ea6b` (newest master)
**Territory** `proxy` (only) · **Items** A20-model-side-bypass-negative (claimed,
W-A20) + A21-ablation-arm-name (delivered on the same branch by the monitor's
explicit authorisation — the board allows one claimed item per territory and both
are `proxy`; A21's claim/done bookkeeping is the monitor's after merge)

**Zero spend.** No network, no API call, no model call, $0.00. Every "vendor" and
"upstream" below is a `http.server` on 127.0.0.1.

---

## What was delivered

### A20-1 — the model side of the seal's right conjunct, as negative samples

`proxy/tests/test_model_side_seal.py` (new, 19 tests). Sibling of
`proxy/tests/test_seal.py`; written in the style of
`theoria-arm/tests/test_bypass_negative.py`, which is where the file the 工单
named actually lives (see *Inputs*). Two halves that fail for different reasons:

**(i) Credential hygiene, by variable NAME only.** `dotenv_names(path)` parses a
dotenv line by line and returns the declared **names**; the value side is never
returned, logged or compared, and that property is itself a test
(`test_the_reader_returns_names_and_never_values`) — a hygiene check that could
print a key into a CI log on failure would be a worse defect than the one it
detects. The live assertion is that `.env`'s name set stays inside
`{ARC_API_KEY}`; a silently added `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` /
`CLAUDE_CODE_OAUTH_TOKEN` / `OPENAI_API_KEY` turns it red. Stricter than
`redact.load_dotenv` in one deliberate way: an empty-valued
`ANTHROPIC_API_KEY=` is invisible to the injection map and *is* caught here,
because a variable declared and waiting to be filled in is a decision already
half-taken. False-red guards included: comments, blanks and `=`-less lines are
not declarations; `export FOO=...` is.

**(ii) Stripping and the 401, on a mock vendor.** A model proxy holding no vendor
credential forwards to an unauthenticated upstream and the call fails **401** —
reproducing offline what `verify-lab/DUAL_PROXY.md` S32 measured live and cited
in the test docstring: **65 of 65** `model_call` records at HTTP 401, **0** at
2xx. A client's own credential header (`Authorization` / `X-API-Key` /
`api-key`) never reaches the vendor, asserted over the **whole recorded request**
rather than over the ledger, because `_handle` only *records* a `bypass_attempt`
and falls through — the enforcement point is `_forward` rebuilding headers from
`PASSTHROUGH_REQUEST_HEADERS`. The sharpest case: a client presenting the
vendor's **valid** key still fails 401, because the proxy will not launder a
credential it did not inject.

Controls, because a test that cannot go red is not a test:

| control | what it pins |
|---|---|
| `test_the_positive_control_the_same_call_with_an_injected_key_succeeds` | the 401 is the absent credential, not a broken proxy (200 with a key) |
| `test_the_stripping_assertion_has_teeth` | widen `PASSTHROUGH_REQUEST_HEADERS` by `authorization` and the credential **does** arrive — so the stripping test measures the allowlist, not an accident |
| `redflip-dotenv.txt` | the live `.env` check made to fail on a temporary **gitignored** `.env`; failure output shows the **name only**; file removed, re-ran green |
| `test_a_dotenv_holding_only_the_arc_key_is_clean` | the checker does not simply refuse everything |

### A20-2 — the reading, recorded

`proxy/DECISIONS.md` **D-A20-001**: under the owner's 2026-08-01 subscription
ruling, the seal's right conjunct on the model side reads **"CLI envelope + no
vendor credential anywhere in the repo or arm environment"**, with the two test
halves as its executable form. The entry states explicitly that it does **not**
move the board colour — `Theoria.md:290` says model traffic is recorded *through
the proxy*, the CLI envelope achieves recording and not proxying, and rewriting
the obligation to match what was achieved is the move the board already refused.
It closes a narrower, real gap: the sealed reading had no executable form.

### A21-1 — the ablation arm's ledger name

* `proxy/ledger.py`: `ARMS` gains **`ablation`** (7 names). Checked first —
  `CONTRACTS/` reserves no arm name, and `LEDGER_FORMAT.md` named no ablation arm.
* `proxy/LEDGER_FORMAT.md`: the `arm` row now lists the vocabulary in full.
* `proxy/DECISIONS.md` **D-A21-001**: why the name exists, why it is `ablation`
  and not the `theoria_ablate` that D-AB-004 records as requested, and that
  adopting it is the other arm's call.
* Tests (12): an `arm:"ablation"` record writes **and validates** under
  `proxy.tools.validate_ledger.validate_records`; every registered name in `ARMS`
  writes a record the validator accepts (parametrized, so a future name cannot be
  added without the validator agreeing); `theoria_ablate` is still refused, loudly.
* `proxy/CONTRACT_CHANGES.md` row **C-008** + re-pinned `proxy/canon_contract.json`.
  `ARMS` is a pinned contract surface, so this tripped
  `tests/test_contract_changes.py` — the announcement protocol working, not a
  defect. `python -m proxy.tools.contract` classified it
  `additive   arms gained 'ablation'` (`contract-verdict-before.txt`), and §2's
  table classes adding an arm as a **widening**: land it, record it in §5.

**A pre-existing drift found while doing it.** `LEDGER_FORMAT.md`'s `arm` row
listed five names while `ARMS` held six — `mock_arm` had been registered in code
and never written into the canon, and nothing compared the two.
`tests/test_ledger_format_sync.py` gained an arm-vocabulary gate with negative
controls in both directions (a name in the code and not the document; a name in
the document the writer would refuse).

### A21-2 — handover, not an edit

Nothing under `ablation-arm/` is touched. D-AB-004's premise ("there is no name")
is now false; whether and when to supersede it is that arm owner's call, and the
handover is the 下一步 line of the PARTNER_SYNC section.

---

## Inputs (read-only)

* `monitor/board/claimed/A20-model-side-bypass-negative.W-A20.md`,
  `monitor/board/items/A21-ablation-arm-name.md`
* `monitor/spec.py` — p1-proxy-model note, the closing owner-ruling paragraph
* `verify-lab/DUAL_PROXY.md` — S32 denominators (**cited, not edited**)
* `theoria-arm/tests/test_bypass_negative.py` — style reference. **The 工单 names
  `proxy/tests/test_bypass_negative.py`, which does not exist**; the file is in
  `theoria-arm/`. Read read-only; its three-property structure and its
  "assert on what the upstream received, not on what the ledger says" discipline
  are what the new file follows.
* `ablation-arm/DECISIONS.md` D-AB-004 + `ablcore/ledger_abl.py` — read to find
  the requested name. Not edited.
* `proxy/` own sources: `model_proxy.py`, `ledger.py`, `redact.py`, `paths.py`,
  `cli_transport.py`, `mock/`, `CONTRACT_CHANGES.md`, existing tests.

---

## Gaps — stated, not hidden

1. **`verify-lab/DUAL_PROXY.md` has no new appendix.** The board item's step 3
   asks for one ("附一段「右合取项模型侧的订阅传输读法」"). The dispatch forbids
   editing `verify-lab/`, and the dispatch wins. S32 is cited from the test
   docstring and from D-A20-001 instead. **If that appendix is wanted, it is a
   `verify-lab` ticket, not this one.**
2. **The board item also asks for the negative to cover "the arm process
   environment"**, not only `.env`. That half already exists and was not
   duplicated: `proxy/mock/arm_mock.py`'s `assert_sealed` / `FORBIDDEN_ENV`, with
   `test_seal.py::test_an_arm_that_can_see_a_credential_refuses_to_start`
   parametrized over every forbidden name. What is new is a test tying the two
   lists together
   (`test_the_dotenv_allowlist_and_the_arm_side_forbidden_list_agree`), so
   widening either has to confront the other. No *new* process-environment
   assertion was written.
3. **A21's inbox notification was not filed.** The board item's step 2 says
   "inbox 通知 ablation-arm 属主"; the dispatch routes the handover through the
   PARTNER_SYNC 下一步 line instead. Done as dispatched. If the monitor wants an
   `monitor/inbox/` item as well, it is one file and outside this territory.
4. **`p1-same-shell`'s "three arms" is now possible at the vocabulary layer only.**
   No ablation record has ever been written under the new name — that requires a
   change in `ablation-arm/`, which is theirs.
5. **`GATES.txt` is deliberately not hashed in `MANIFEST.json`.** It is the
   gate's own output, and running the gate rewrites it, so hashing it makes the
   manifest fail against itself on the next run. The manifest is built with
   `--no-run-files` and an explicit include list for that reason; every other
   run-dir artefact is hashed.

6. **The live `.env` assertion is vacuous in a worktree**, where `.env` does not
   exist (it is gitignored, and `paths.DOTENV` resolves from `proxy/paths.py`'s
   `__file__`). Absence is a *stricter* state than the assertion — a proxy with
   no dotenv has nothing to inject — and the mechanism's red/green comes from
   `tmp_path` fixtures, not from the ambient file. The red-flip on the real path
   was demonstrated separately (`redflip-dotenv.txt`) and the temporary file
   removed.

---

## Gate output, verbatim

```
== verify.sh :: A20 :: agent/a20-a21-proxy-seal-pair ==
[PASS] tests -- proxy
[PASS] MANIFEST hashes reproduce
[PASS] boundary -- only proxy changed
[PASS] sealed pile untouched
[PASS] credential never entered a tracked file
[PASS] delivered: proxy/runs/2026-08-01T044534Z-A20/MANIFEST.json
-- 6/6 green
```

**One `--allow`, disclosed: `PARTNER_SYNC.md`.** Appending this ticket's section
puts that file in the branch's diff, and the sealed-pile scanner then reports the
ids sitting in **other tracks' historic paragraphs** further up the file. They
provably predate this branch, and the proof is machine-checked rather than
asserted — `sealed-allow-proof.txt`, regenerable:

* this branch's diff against `4c08ea6b` on `PARTNER_SYNC.md` is **6 added lines,
  0 removed** (a pure append; nothing another track wrote was rewritten);
* **0** sealed ids and **0** sealed stems occur in those 6 added lines;
* **4** occur in the pre-existing body, which is where the report comes from.

Ids are counted there, never written down — not in the proof file, not here.
`proxy/` itself needed no allow: `proxy/tests/test_seal.py` carries a sealed id
and predates this branch, but it was not modified, so it never entered the diff.

The first gate run (before the PARTNER_SYNC append) was 6/6 green with no allow
at all; the allow is a consequence of the handoff step, not of the code change.

**Territory suite**, `cd proxy && python -m pytest`:
**497 passed, 0 failed, exit 0** — baseline at 开工 was **466 passed**, so **+31**,
which is exactly the 19 + 12 tests added. No test was deleted, skipped or
xfailed to get there.

**Contract detector**, `python -m proxy.tools.contract` before the re-pin:

```
ADDITIVE
  additive   arms gained 'ablation'
```

---

## Red lines

* No credential **value** read, printed, or written anywhere. The `.env` work is
  by variable **name** only, and the reader's value-blindness is a test.
* No sealed-pile game id written into any file. Where the new tests need an id
  they use `ar25-0c556536` (development pile).
* Nothing outside `proxy/` modified. `PARTNER_SYNC.md` via the sync script is the
  single declared exception.
* No `git add -A`, no merge to master, no `board.py done`.
