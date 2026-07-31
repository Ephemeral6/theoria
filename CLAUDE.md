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

## Territories (formerly "two independent tracks")

The repo began as two non-communicating Claude Code tracks
(`theory-compiler` and `engine-rig`), mutually visible only through git
history and `PARTNER_SYNC.md`. It has since grown into a fleet: each
top-level directory is a territory with an owner. Territories as of
2026-07-31 also include `proxy/`, `battery/`, `exam/`, `figures/`,
`papers/`, `release/`, `freeze/`, `crosscheck/`, `a2_crosscheck/`, the
arms (`baseline-arms/`, `theoria-arm/`, `ablation-arm/`), the rigs
(`fuzzlab/`, `verify-lab/`, `worldgen/`, `fleetkit/`, `fleet-study/`) and
the cold starts (`cold-start-a2/`, `cold-start-a3/`).

| Track | Directory | Scope |
|---|---|---|
| `theory-compiler` | `/theory-compiler/` | the DSL and its generators (two books → four forms) |
| `engine-rig` | `/engine-rig/` | the six engines, validated offline against synthetic fixtures |

`/arc-recon/` is shared ground, not a track: the API access check and the pile
cut. Read it before doing anything that touches the live API.

`/a0-spike/` is the engine-rig track's A0 cold start. **`/cold-start-a0/` is the
theory-compiler track's and is off limits to engine-rig** -- it had uncommitted
work in flight, which is why a second directory exists rather than one shared one.

**Stay inside your own territory.** Do not edit another territory's files.
Shared surfaces are `/CONTRACTS/` and `PARTNER_SYNC.md`; cross-territory
requests go through `PARTNER_SYNC.md` or `monitor/inbox/`, never direct
edits.

## Frozen contracts — `/CONTRACTS/`

| File | Status |
|---|---|
| `candidates_schema.md` | **frozen v0.1 — the only candidates contract in force.** Neither track may modify it. |
| `candidates_schema_v0.2.md` | draft, awaiting engine-rig countersign; until then v0.1 governs. |
| `dsl_grammar_v0.1.md` | frozen; owned by the theory-compiler track. |
| `dsl_grammar_v0.2.md` / `dsl_grammar_v0.3.md` | final; theory-compiler sole owner (no countersign required). |
| `pagoda_certificate_v0.1.md` | landed by C13, written from existing code on both ends. |
| `deadlock_certificate_v0.1.md` | draft, awaiting engine-rig countersign. |
| `ic3_certificate_v0.1.md` | **countersigned 2026-07-31** (engine-rig; emitting half landed by E8). |
| `verify.py` | the contracts' completion gate — frozen specs must agree with the code. |

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

All nine milestones are done and tagged (`engine-rig-m1-fixtures` …
`engine-rig-m9-deadlock-ic3-probe`). Eight engines: `mdl_segmenter`,
`cegis_miner`, `zero_space`, `lp_potential`, `fd_adapter`, `probe_frontier`,
`deadlock_carver`, `ic3_pdr`. Suite as measured 2026-07-31: 584 passed, 27
skipped, 0 failed (skip count is environment-dependent, e.g. the gitignored
FD toolchain — re-run for your machine's numbers rather than trusting this
line). Everything runs offline against self-generated synthetic fixtures — no
LLM calls, no game API, no network.

```bash
cd engine-rig && python -m pytest              # the suite
cd engine-rig && python -m fixtures.generate_all   # regenerate fixtures (byte-stable)
cd engine-rig && python -m tools.run_all --force   # all eight engines end to end
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

`arc-recon/data/piles.json` splits the 25 public
games into a **development pile of 4** (`ar25-0c556536`, `g50t-5849a774`,
`sk48-d8078629`, `tn36-ef4dde99`) and a **sealed pile of 21**. The cut's
guard fingerprint is the file's own `sha256` field: `3feca53e…41bbc19a`.
That value is a **content digest, not the file's hash** — sha256 over the
JSON document with the `sha256` key removed, serialised canonically
(`json.dumps(doc, sort_keys=True, separators=(",", ":"))`). Recompute it
that way (`arc-recon/cut_piles.py` is the reference implementation); hashing
the raw bytes gives `d3140eff…4dd5b8c9` instead, which moves on any
reformatting. Every existing reference to `3feca53e…` means the content
digest. If a recompute mismatches, the cut itself changed — that is an
incident, not a checksum nit.

Do not play, inspect, or read about a sealed game — including upstream released
artifacts belonging to it, since reading those teaches the mechanics just as well
as playing. Phase 3 iterates until it gets results, which is only honest if the
confirmation runs on unseen problems. Changing the cut after play has begun is an
incident and must be recorded as one.

**The local engine defaults to all 25 games — filter first, or it is refused.**
`arc-recon/ACCESS_CHECK.md` §8a concluded that caching ARC data locally is
permitted and needs no permission. That is about licensing, and **permission is
not containment**: upstream's first run downloads *the game source* for all 25
games into `environment_files/`, and `make play-local`, `make verify-local` and
the swarm runner's `--game` flag all default to every game in the dataset
(`browser-ops/TERMS.md` §4.2). Source is worse than trajectories — it hands over
the finished answer to the mechanics. So:

* Any path that pulls `environment_files/`, or runs the swarm runner, **must
  name the four development-pile games explicitly**. Unfiltered means all 25.
* `make play-local`, `make list-games` and `make verify-local` are **refused
  outright**: no filter argument is documented for any of them, and make accepts
  an unreferenced `GAME=` override in silence — so a filter we invented would
  play all 25 while looking filtered. Use the swarm runner with `--game=`.
* This is enforced in code, not by memory — `arc-recon/local_engine_guard.py`
  is a positive whitelist that defaults to deny. Put it in front of the call:

  ```bash
  cd arc-recon
  python local_engine_guard.py check -- <command...>   # 0 allowed, 2 REFUSED
  python local_engine_guard.py run   -- <command...>   # vets, then execs if allowed
  python local_engine_guard.py scan  environment_files # names-only cache sweep
  ```

  It is a **pre-flight, not a sandbox**: a process that never calls it can still
  run anything. `scan` is the after-the-fact detector for that case, and it is
  in `verify.sh` for exactly that reason.

* A local run makes **no API call**, so it leaves no trace in
  `data/recon_ledger.jsonl` and `contamination.py`'s audit stays green right
  through it. Do not read a green audit as evidence that this path was not
  taken; the guard is the only instrument that sees it.
* `environment_files/` is gitignored. Downloading is not reading — but nothing
  under it may be opened, summarised, or fed to a model except the four
  development-pile games.

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
