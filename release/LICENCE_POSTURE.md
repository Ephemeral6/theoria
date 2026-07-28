# release/LICENCE_POSTURE.md — what may be released, what needs permission, what may not

`P5-release`, RES-2. Step 1 of `release/PLAN.md`, written before the enumerator,
because a manifest built first is a manifest that has already classified
everything by omission.

Authority: `browser-ops/TERMS.md` §2, whose per-page provenance is in
`browser-ops/runs/2026-07-28-visits.md`. Quotations below are that file's
excerpts of <https://arcprize.org/terms> (last updated June 03 2024); the full
ToS is not reproduced here or there, by that document's own reading of §2.

## The two clauses that decide everything

**§2 INTELLECTUAL PROPERTY RIGHTS** — content is provided *"for your personal,
non-commercial use or internal business purpose only"*, and no part may be
*"copied, reproduced, aggregated, republished, uploaded, posted, publicly
displayed … without our express prior written permission"*.

**§4 PROHIBITED ACTIVITIES**, first item — *"Systematically retrieve data or
other content from the Services to create or compile, directly or indirectly, a
collection, compilation, database, or directory without written permission from
us"*.

## The correction this file makes to P5's own plan

`release/PLAN.md` framed the constraint as being about **frame data**. That was
too narrow, and it was too narrow in the dangerous direction. It came from
reading `R2`'s summary rather than `TERMS.md` itself.

§4's first prohibited activity names *"a collection, compilation, database"*.
**A ledger of API interactions is literally that**, and `browser-ops/TERMS.md`
§2.2 ruling 2 says so in as many words: the ledgers and trajectory collections
are what §4 names, internal analysis is fine under §2's "internal business
purpose", and **public release is the line**. So the constrained class is not
"frames"; it is *everything systematically retrieved from the API and compiled*
— frames, action sequences, scores, scorecards, and the ledgers that hold them.

Caching is separately and explicitly fine: `TERMS.md` §2.1 establishes from the
official docs that local caching is the designed behaviour and needs no extra
permission. **Holding is permitted; publishing is not.** These are two different
questions and the release kit must not merge them.

## Classification

| class | examples | verdict |
|---|---|---|
| **A. Self-built material** | `worldgen/`, `cold-start-a0/`, `cold-start-a2/`, `cold-start-a3/`, `engine-rig/`, `fuzzlab/`, `exam/`, `theory-compiler/`, `figures/`, `proxy/`, the two books in four forms, the Lean proofs, the candidate box | **RELEASABLE.** None of it is retrieved from the Services. This is the bulk of the repository and it is the part that carries the research claim. |
| **B. API-derived compilations** | `baseline-arms/ledger.jsonl`, `baseline-arms/out/shards/ledger.*.jsonl`, `baseline-arms/probe_log*.jsonl`, `arc-recon/data/recon_ledger.jsonl`, `theoria-arm/runs/*/ledger.jsonl`, any frame dump, any scorecard body | **NEEDS WRITTEN PERMISSION. Default: excluded.** §4 names this class exactly. Ship a **sha256 per file plus a reproduction script**, so a reader with their own key regenerates rather than receives. |
| **C. Statistics derived from B** | `battery/artifacts/*.json`, `figures/csv/*.csv`, the figures themselves, cost and turn counts quoted in the paper | **RELEASABLE, with one flag raised.** Precedent is the battery's own D-B-020, which keeps the `schema_traces` payload out and admits only aggregate statistics. The flag: §2's prohibited verbs include *"aggregated"*, so a maximally literal reading would catch aggregates too. That reading would also forbid publishing a mean score, which cannot be the intent — but the call is not mine. **`needs_human`.** |
| **D. Upstream third-party payload** | `baseline-arms/schema_traces/**` | **NOT RELEASABLE, for a different reason.** `SCHEMA_PATH_A.md` §7 records the upstream HF dataset as declaring **no licence at all**. `TERMS.md` closes by noting the two problems point opposite ways: ARC's says "not without permission", upstream's says nothing, and silence is not a grant. Already gitignored. |

## What is not decided here, and by whom

**Nobody on this track applies for permission.** `R2` is explicit that
approaching `team@arcprize.org` is a human decision. This file records what the
terms say and what the release kit will therefore do by default; it does not
seek, assume, or pre-empt a grant. If permission is later obtained, §2 attaches
an attribution obligation — ARC Prize must be named as owner and the copyright
notice preserved — and that obligation belongs in the manifest, not in a memory.

## The consequence for the paper's openness claim

`Theoria.md:379` sets the target as *"scale and openness reaching Schema's floor
(the full public set + artifacts)"*. **On class B that target cannot be met**,
and the release kit must not be built as though it could. What can be met is a
weaker and honestly-stated form: every class-A artefact in full, every class-B
artefact as a hash plus the script that regenerates it, and a statement of which
of the two a reader is holding. That sentence belongs in the paper's openness
section, and it is a real limitation rather than a formatting detail.

## Red lines: measured, not asserted

`release/check_redlines.py`, run against all **1,938** tracked files at
`398144e`:

* **credential — clear.** No tracked file contains the literal `ARC_API_KEY`
  value. The five tracked `probe_log*.jsonl` files, which battery's own
  provenance flags as carrying an `X-API-Key` request header, hold the string
  `"<redacted>"` in that header. The redaction discipline held.
* **sealed pile — clear.** No record in any tracked file pairs a sealed game id
  with payload. Twenty-seven files *name* sealed ids; all twenty-seven are
  guards, tests, audit documents, the cut itself, or the contamination ledger —
  files whose job is to name the sealed games in order to keep them out.

The check reports the value of neither: the key is loaded through
`arc-recon/client.py`, compared in memory, and only ever printed through
`mask()`. It runs **before** the enumerator and again on every regeneration,
because a release manifest publishes every tracked file and `CLAUDE.md` records
that a key committed here is a key published later, effectively irreversibly.
