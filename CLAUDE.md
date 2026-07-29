# Theoria — shared repository context

Research framework in which an LLM maintains an explicit **world theory** instead
of modelling the world implicitly in weights. The LLM writes two books (the
manual: what the world is; the playbook: how to win), which compile to four
co-derived forms (Lean / Python / PDDL / Markdown). The precise work — segmentation,
rule mining, linear algebra, search — is outsourced to engines. Engines propose,
the LLM adjudicates.

Full design: [Theoria.md](Theoria.md). Read it before substantive work.

## Credentials — read this before touching anything network-facing

**The ARC API key lives in `.env` at the repo root, as `ARC_API_KEY`. `.env` is
gitignored and must stay that way.**

```bash
set -a; . ./.env; set +a      # load into the environment
```

```python
import sys; sys.path.insert(0, "<repo>/arc-recon")
from client import load_api_key, mask
key = load_api_key()          # reads .env; raises if it is missing
print(mask(key))              # "7171...05dd (len 36)" -- safe to log
```

`arc-recon/client.py` is the shared reader. Prefer it over parsing `.env`
yourself: it also redacts the key in every ledger entry it writes, so an agent
using it cannot leak the value into an artefact by accident.

Never write the key's value into any tracked file — not source, not Markdown, not
CLAUDE.md, not a commit message, not a test fixture. This is not general caution;
it is [Theoria.md](Theoria.md) Phase 1's sealing discipline, verbatim: the credential is
injected only inside the environment proxy, and does not enter the repository,
the design document, or any arm. The Phase 4 release manifest publishes every
tracked file, so a key committed here is a key published later, and git history
makes that effectively irreversible.

If you need a new secret, add it to `.env` and document the *variable name* in
`.env.example`.

## Two independent tracks

Two Claude Code instances work this repo concurrently and do **not** communicate.
They are mutually visible only through git history and `PARTNER_SYNC.md`.

| Track | Directory | Scope |
|---|---|---|
| `theory-compiler` | `/theory-compiler/` | the DSL and its generators (two books → four forms) |
| `engine-rig` | `/engine-rig/` | the six engines, validated offline against synthetic fixtures |

`/arc-recon/` is shared ground, not a track: the API access check and the pile
cut. Read it before doing anything that touches the live API.

`/a0-spike/` is the engine-rig track's A0 cold start. **`/cold-start-a0/` is the
theory-compiler track's and is off limits to engine-rig** -- it had uncommitted
work in flight, which is why a second directory exists rather than one shared one.

**Stay inside your own directory.** Do not edit the other track's files. Shared
surfaces are `/CONTRACTS/` and `PARTNER_SYNC.md`.

## Frozen contracts — `/CONTRACTS/`

| File | Status |
|---|---|
| `candidates_schema.md` | frozen v0.1. Neither track may modify it. |
| `dsl_grammar_v0.1.md` | owned by the theory-compiler track. |

`candidates.jsonl` is **append-only**, and `status` is always `"candidate"` —
engines never adjudicate. `engine-rig/tools/validate_candidates.py` is the
executable form of the schema and will check any stream:

```bash
cd engine-rig && python -m tools.validate_candidates <path>
```

## PARTNER_SYNC.md

Append-only status board. Write only your own paragraphs; never edit the other
track's. It is a board, not a conversation — nobody replies.

**Where append-only starts.** A paragraph is published once it is on the
mainline; from then on, correct it only by appending a new one that
supersedes it. On a branch it is still a draft — fix it until it is right
before the merge. (Two sessions read this differently on 2026-07-28, which
is why the line is written down.) Format:

```
## [<track>] <ISO8601> <milestone-tag>
状态：<one line>
测试：<pass/fail summary>
阻塞：<none / description>
下一步：<one line>
```

## engine-rig — current state

All eight milestones are done and tagged (`engine-rig-m1-fixtures` …
`engine-rig-m8-integration`). Six engines: `mdl_segmenter`, `cegis_miner`,
`zero_space`, `lp_potential`, `fd_adapter`, `probe_frontier`. 150 tests pass, 1
skipped. Everything runs offline against self-generated synthetic fixtures — no
LLM calls, no game API, no network.

```bash
cd engine-rig && python -m pytest              # the suite
cd engine-rig && python -m fixtures.generate_all   # regenerate fixtures (byte-stable)
cd engine-rig && python -m tools.run_all --force   # all six engines end to end
```

Design calls and their reasons: `engine-rig/DECISIONS.md`. Milestone state and
the Fast Downward attempt log: `engine-rig/STATUS.md`.

Two standing caveats worth knowing before you build on it:

* **Fast Downward is connected** (P-13, 2026-07-28): a real FD 24.06+ build
  behind the same `solve(domain, problem)` interface, with a three-rung ladder
  (`stub-bfs` / `fd-optimal` / `fd-satisficing`); provenance in
  `engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md`. `.toolchain/` is
  gitignored by design, so on a machine without the build the adapter falls
  back to the BFS stub and 3 tests skip — that is expected, not a defect.
* **`lp_potential` is sound but incomplete.** It never certifies a solvable
  configuration, but some genuinely unsolvable ones admit no linear pagoda.

## The pile cut — binding on both tracks

`arc-recon/data/piles.json` (sha256 `3feca53e…41bbc19a`) splits the 25 public
games into a **development pile of 4** (`ar25-0c556536`, `g50t-5849a774`,
`sk48-d8078629`, `tn36-ef4dde99`) and a **sealed pile of 21**.

Do not play, inspect, or read about a sealed game — including upstream released
artifacts belonging to it, since reading those teaches the mechanics just as well
as playing. Phase 3 iterates until it gets results, which is only honest if the
confirmation runs on unseen problems. Changing the cut after play has begun is an
incident and must be recorded as one.

**Status (2026-07-28):** the development pile has been played — all four
games are registered `trajectories_reviewed` in
`arc-recon/data/contamination_log.jsonl`. The sealed pile has had zero API
contact, but INC-BA-001 recorded knowledge contamination of 9 sealed games
from a web search; F-11 ruled the claim set down to 19
(`arc-recon/data/claim_set.json`, ls20/ft09 quarantined).

## Conventions

* **Worktrees live inside the repo**: `.worktrees/<branch-slug>/` (gitignored). Never create sibling checkouts on the desktop — 22 of them
  accumulated there before this rule existed.

* **Provenance is canonical**: every experiment writes
  `runs/<id>/MANIFEST.json` — required `prompt_id`, `branch`,
  `base_commit`, `utc`; optional `files[].sha256`. Human narrative goes in
  `RUN_STATE.md`, never in place of the manifest. Write as you go: a
  session's context evaporates, the disk is the memory.

* Python 3.13; numpy / scipy / pytest available.
* Determinism is a requirement, not a nicety: fixtures and artifacts are
  byte-reproducible for a fixed seed. `engine-rig/.gitattributes` pins LF so
  `core.autocrlf` cannot corrupt them.
* Commit only your own track's paths. Never `git add -A` at the repo root —
  the other track's work-in-progress lives there too.
