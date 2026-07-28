# Territory map — who has a suite, and how it is run

Surveyed 2026-07-28 against `master` at `dc9fad1`. The rule is uniform enough
that `start_ritual.py` autodetects it: **if a territory has `pytest.ini`,
`conftest.py`, `tests/` or `test_*.py`, run `python -m pytest` from the
territory root.** This table exists for the exceptions and the extras.

| territory | suite | how | notes |
|---|---|---|---|
| `engine-rig/` | yes | `python -m pytest` | 150 pass / 1 skip. Extras: `python -m fixtures.generate_all` (byte-stable), `python -m tools.run_all --force` (all six engines). `.gitattributes` pins LF here. |
| `theory-compiler/` | yes | `python -m pytest` | the DSL and its four generators |
| `proxy/` | yes | `python -m pytest` | 180 pass incl. 44 red-team attacks; all offline |
| `battery/` | yes | `python -m pytest` | |
| `exam/` | yes | `python -m pytest` | |
| `theoria-arm/` | yes | `python -m pytest` | 47 pass. Extra preflight: `python -m armtools.preflight` |
| `cold-start-a0/` | yes | `python -m pytest` | **off limits to engine-rig** (CLAUDE.md) |
| `cold-start-a2/` | yes | `python -m pytest` | plus `python tools/verify_readonly.py` |
| `cold-start-a3/` | yes | `python -m pytest` | plus `python tools/verify_readonly.py` |
| `a0-spike/` | yes | `python -m pytest` | engine-rig's A0 cold start |
| `baseline-arms/` | yes | `python -m pytest` | tests live in `tests/`, no pytest.ini |
| `arc-recon/` | yes | `python -m pytest` | single file `test_hygiene.py` at the root; 40 pass, offline. **Shared ground** — read before anything that touches the live API |
| `papers/` | no | — | prose. 测试：不适用 |
| `browser-ops/` | no | — | prose + visit ledger |
| `monitor/` | no | — | monitor's own; execution sessions write only `monitor/inbox/*.md` |
| `CONTRACTS/` | frozen | — | `candidates_schema.md` is frozen v0.1; validate streams with `cd engine-rig && python -m tools.validate_candidates <path>` |
| `.claude/skills/` | no | — | shared ground; **only add directories, never edit another skill** |

## Cross-cutting checks that are not any one territory's suite

* **Candidate streams** — `cd engine-rig && python -m tools.validate_candidates <path>`
  is the executable form of the frozen schema and will check any stream.
* **Sealed pile** — `arc-recon/data/piles.json` (sha256 `3feca53e…41bbc19a`).
  Four development games are playable; the other 21 must not be played,
  inspected, or read about. `verify-gate` ships this as a standard check.
* **Credential** — `ARC_API_KEY` lives in `.env`, gitignored, read through
  `arc-recon/client.py`'s `load_api_key()`. It must never reach a tracked
  file. `verify-gate` ships this as a standard check too.

## Naming, as the fleet actually uses it

* branch — `agent/<ticket lowercased>-<slug>`, e.g. `agent/p24-fleet-skills`
* worktree — `<repo parent>/theoria-wt-<ticket>`, e.g. `../theoria-wt-p24`.
  (`.claude/worktrees/<slug>` is the harness's own convention and is also in
  use; either is fine, both are outside every territory.)
* runs — `<territory>/runs/<UTC>-<slug>/`
