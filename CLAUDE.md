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
track's. It is a board, not a conversation — nobody replies. Format:

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

* **Fast Downward is not connected.** `fd_adapter` runs a grounded-STRIPS BFS
  stub behind the same `solve(domain, problem)` interface (length-optimal for
  unit costs). Install FD and put it on PATH, or set `FAST_DOWNWARD`, and the
  adapter picks it up with no caller changes.
* **`lp_potential` is sound but incomplete.** It never certifies a solvable
  configuration, but some genuinely unsolvable ones admit no linear pagoda.

## Conventions

* Python 3.13; numpy / scipy / pytest available.
* Determinism is a requirement, not a nicety: fixtures and artifacts are
  byte-reproducible for a fixed seed. `engine-rig/.gitattributes` pins LF so
  `core.autocrlf` cannot corrupt them.
* Commit only your own track's paths. Never `git add -A` at the repo root —
  the other track's work-in-progress lives there too.
