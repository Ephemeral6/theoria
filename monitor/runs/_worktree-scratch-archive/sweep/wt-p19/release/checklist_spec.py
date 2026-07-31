"""The Phase 4 release checklist, as data.

`Theoria.md` Phase 4 names nine deliverables in one sentence:

    释出清单——全部账本、两本书(各形态)与 Lean 证明、候选箱、探针日志、
    电池代码与回算结果、冻结清单、incident ledger、复跑说明。

This module turns that sentence into a machine-checkable specification: each
item carries the path patterns that satisfy it and the gaps that do not. The
gaps are the point. A manifest that only lists what exists is a brochure; the
release is honest only if the holes ship with it.

`release/PLAN.md` is the prose form of this file. If they disagree, this one is
authoritative -- it is the one the manifester reads.
"""

from typing import Dict, List

# ---------------------------------------------------------------------------
# Status vocabulary. Nothing else may appear in a status field.
#
#   READY    -- a concrete artefact exists for every part of the item.
#   PARTIAL  -- artefacts exist but a named gap remains.
#   MISSING  -- the tree has nothing for this item.
# ---------------------------------------------------------------------------
READY = "READY"
PARTIAL = "PARTIAL"
MISSING = "MISSING"

# The dev pile, verbatim from arc-recon/data/piles.json. Duplicated here only so
# that a mismatch between the two is itself detectable; the manifester reads
# piles.json and asserts equality rather than trusting this copy.
DEV_PILE = [
    "ar25-0c556536",
    "g50t-5849a774",
    "sk48-d8078629",
    "tn36-ef4dde99",
]

PILES_SHA256_PREFIX = "3feca53e"  # CLAUDE.md quotes 3feca53e…41bbc19a


def _item(
    n: int,
    key: str,
    title: str,
    status: str,
    include: List[str],
    exclude: List[str] = None,
    gaps: List[Dict[str, str]] = None,
    notes: List[str] = None,
) -> Dict:
    return {
        "item": n,
        "key": key,
        "title": title,
        "status": status,
        "include": include,
        "exclude": exclude or [],
        "gaps": gaps or [],
        "notes": notes or [],
    }


# ---------------------------------------------------------------------------
# The nine, in the order Theoria.md names them, plus one appendix item.
#
# Patterns are fnmatch globs against repo-relative POSIX paths. `**` is handled
# by the matcher in manifest.py (fnmatch alone does not cross separators the way
# we need), so `a/**` means "anything under a/".
# ---------------------------------------------------------------------------
CHECKLIST = [
    _item(
        1, "ledgers", "全部账本 — all ledgers", PARTIAL,
        include=[
            "proxy/LEDGER_FORMAT.md",
            "proxy/CANON_MIGRATION.md",
            "proxy/ledger.py",
            "proxy/canon.py",
            "proxy/cost.py",
            "proxy/redact.py",
            "proxy/reconcile.py",
            "proxy/tools/validate_ledger.py",
            "proxy/tools/upgrade_ledger.py",
            "baseline-arms/ledger.jsonl",
            "baseline-arms/harness/ledger.py",
            "baseline-arms/harness/merge_ledger.py",
            "arc-recon/data/recon_ledger.jsonl",
            "arc-recon/data/contamination_log.jsonl",
            "arc-recon/data/canary_runs.jsonl",
            "arc-recon/redact_ledger.py",
            "cold-start-a2/a2pipeline/ledger.py",
            "cold-start-a2/artifacts/loop_ledger.json",
            "battery/adapters/ledger_jsonl.py",
            "battery/tests/fixtures/ledger_fixture.jsonl",
            "theoria-arm/runs/**/ledger.jsonl",
            "theoria-arm/runs/**/cost_curve.json",
            "monitor/history.jsonl",
        ],
        gaps=[
            {
                "id": "L-1",
                "what": "two ledger dialects ship side by side",
                "detail": "baseline-arms/harness/ledger.py still writes the legacy "
                          "dialect. F-16 ruled it must migrate to the proxy canon; it "
                          "has not. The manifest labels each ledger's dialect rather "
                          "than implying one format.",
            },
            {
                "id": "L-2",
                "what": "the proxy has never written a live ledger",
                "detail": "proxy/var/ is gitignored -- the format is tracked, the data "
                          "a run produces is not -- and per proxy/README.md no live run "
                          "has yet gone through the proxies. proxy/runs/p9-shell-harden/ "
                          "is cross-session determinism evidence, not a campaign ledger.",
            },
        ],
        notes=[
            "Live-API-derived ledger bytes (baseline-arms + arc-recon + theoria-arm) "
            "are NOT reproducible offline. They are evidence, not output.",
        ],
    ),
    _item(
        2, "books", "两本书(各形态) — the two books, in each form", PARTIAL,
        include=[
            "**/*.dsl",
            "**/theory/generated*/**",
            "**/prime/theory/generated*/**",
            "theoria-arm/runs/**/books/**",
            "a0-spike/artifacts/theory_exec.py",
            "a0-spike/artifacts/pddl/**",
            "theory-compiler/src/**",
            "theory-compiler/tools/**",
            "theory-compiler/tests/**",
            "CONTRACTS/dsl_grammar_v0.1.md",
            "CONTRACTS/dsl_grammar_v0.2.md",
            "exam/handover_bundles/**",
        ],
        gaps=[
            {
                "id": "B-1",
                "what": "the playbook has no generated forms",
                "detail": "All four generators consume TheoryAST only; "
                          "`grep playbook theory-compiler/src/theory_compiler/"
                          "generators/*.py` returns nothing. The manual compiles to "
                          "four forms; the playbook exists only as DSL. "
                          "exam/handover_bundles/*/PLAYBOOK.md is hand-written "
                          "(MANIFEST.json: written_for=this exam) while the sibling "
                          "MANUAL.md is generated with model_calls=0. So the checklist "
                          "phrase '两本书(各形态)' currently means four forms of one book "
                          "and one form of the other.",
            },
            {
                "id": "B-2",
                "what": "gen_pddl ignores ProblemSpec",
                "detail": "theory-compiler/runs/P-10/RUN_STATE.md: the shared PDDL "
                          "generator emits a 2x3 toy grid regardless of the problem, so "
                          "'the PDDL column of the four-form regression has limited "
                          "meaning'.",
            },
        ],
        notes=[
            "Three generated dirs are deliberately incomplete and self-reported: "
            "cold-start-a2/theory/generated_repaired_stale/ is a red exhibit (README:56); "
            "theoria-arm run books have no Lean because inner/books.py:38 sets "
            "LEAN_STATE_CEILING = 200_000 and certify.expensive reports available:false "
            "on a real level -- an unavailable proof layer is never a passed one.",
        ],
    ),
    _item(
        3, "lean", "Lean 证明 — the Lean proofs", READY,
        include=[
            "**/*.lean",
            "theory-compiler/lean/lean-toolchain",
            "theory-compiler/lean/lake-manifest.json",
            "theory-compiler/tests/test_gen_lean.py",
            "cold-start-a0/certify/**",
        ],
        gaps=[
            {
                "id": "X-1",
                "what": "nothing regenerates theory-compiler/lean/TheoriaLean.lean",
                "detail": "test_gen_lean.py:274 points at the README; README.md:41-55 "
                          "writes a differently-named file. The test docstring says it "
                          "outright: 'nothing regenerates it on its own -- so it drifts "
                          "silently. It did.' The staleness test is the only guard. The "
                          "reproducer grades this KNOWN_GAP rather than pretending the "
                          "Lean column round-trips.",
            },
        ],
        notes=[
            "Real toolchain, not a stub: tests shell out to `lean` and assert "
            "returncode==0; THEORIA_REQUIRE_LEAN=1 turns a missing toolchain into a "
            "UsageError instead of a skip; the negative control was actually run "
            "(STATUS.md:202-205 -- flipping one pagoda weight made all four theorems "
            "depend on sorryAx and lean exit 1).",
            "lake-manifest.json has \"packages\": [] -- no Mathlib, so `lake build` is "
            "offline once the toolchain is installed.",
        ],
    ),
    _item(
        4, "candidates", "候选箱 — the candidate box", READY,
        include=[
            "CONTRACTS/candidates_schema.md",
            "CONTRACTS/candidates_schema_v0.2.md",
            "engine-rig/tools/validate_candidates.py",
            "engine-rig/common/candidates.py",
            "theory-compiler/tools/validate_candidates_v02.py",
            "**/candidates*.jsonl",
            "engine-rig/artifacts/**",
        ],
        gaps=[
            {
                "id": "C-1",
                "what": "the only live candidate stream is never validated",
                "detail": "theoria-arm/runs/*/candidates.jsonl (2,959 lines) has no "
                          "validator invocation anywhere in the tree. The manifester "
                          "runs the v0.1 validator over every candidates stream it "
                          "finds and records the verdict per file, pass or fail.",
            },
            {
                "id": "C-2",
                "what": "two contracts are still unsigned drafts",
                "detail": "CONTRACTS/candidates_schema_v0.2.md and "
                          "CONTRACTS/ic3_certificate_v0.1.md await engine-rig's "
                          "counter-signature. v0.1 remains the frozen one.",
            },
        ],
    ),
    _item(
        5, "probes", "探针日志 — the probe logs", PARTIAL,
        include=[
            "baseline-arms/probe_log.jsonl",
            "baseline-arms/harness/probe_api.py",
            "baseline-arms/harness/probe_action_variants.py",
            "theoria-arm/runs/**/probes.jsonl",
            "theoria-arm/inner/probe.py",
            "cold-start-a2/artifacts/probes.jsonl",
            "cold-start-a2/artifacts/probed_trace.jsonl",
            "cold-start-a2/artifacts/probe_report.json",
            "cold-start-a2/a2pipeline/probe.py",
            "cold-start-a0/prime/artifacts/probes_run*.jsonl",
            "cold-start-a0/prime/probe_runner.py",
            "cold-start-a0/prime/coverage_probe.py",
            "arc-recon/probe_stickiness.py",
            "arc-recon/data/stickiness_probe.json",
            "engine-rig/engines/probe_frontier/**",
        ],
        gaps=[
            {
                "id": "P-1",
                "what": "probe logs are heterogeneous and have no schema contract",
                "detail": "baseline-arms/probe_log.jsonl is an HTTP transcript "
                          "(kind/method/url/status); the rest are probe-design records "
                          "(hypothesis/cost/bits). The field sets do not intersect. "
                          "Candidates have a frozen contract; probes have none. The "
                          "manifest groups them by dialect instead of implying one "
                          "format.",
            },
            {
                "id": "P-2",
                "what": "one probe log is an empty file",
                "detail": "cold-start-a0/prime/artifacts/probes_runA.jsonl is 0 records. "
                          "Shipped as-is; an empty log is a result.",
            },
        ],
    ),
    _item(
        6, "battery", "电池代码与回算结果 — battery code and recomputation", READY,
        include=["battery/**"],
        gaps=[],
        notes=[
            "Fully offline and byte-deterministic: no sockets, no wall clock in any "
            "artefact (input digests instead), hand-rolled statistics rather than scipy, "
            "and tests/test_determinism.py sha256s four artefacts.",
            "Self-reported weaknesses that ship with it (battery/STATUS.md): 21 of 38 "
            "metrics have never been computed on a control arm; no metric reaches "
            "p<0.05 on current data (W-3); the economy family has zero data on any arm "
            "carrying a theory (W-5).",
        ],
    ),
    _item(
        7, "freeze", "冻结清单 — the freeze manifest", MISSING,
        include=[
            "theoria-arm/inner/**",
            "engine-rig/fixtures/generate_all.py",
            "engine-rig/engines/fd_adapter/**",
            "engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md",
            "proxy/variants.py",
            "exam/artifacts/variant_specs/**",
            "a0-spike/pipeline/adapt.py",
            "baseline-arms/BUDGET_REPORT.md",
            "baseline-arms/harness/summarise_campaign.py",
            "browser-ops/TERMS.md",
        ],
        gaps=[
            {"id": "F-04", "what": "prompts are not isolated",
             "detail": "No theoria-arm/prompts/ directory; the arm's prompts are inline "
                       "in inner/theorize.py and friends. monitor/prompts/ holds work "
                       "orders, not arm prompts. A freeze must hash a file."},
            {"id": "F-05", "what": "engines have no version strings",
             "detail": "The engine list is the ENGINES set at "
                       "engine-rig/tools/validate_candidates.py:22-29. Grep for "
                       "ENGINE_VERSION returns nothing. Theoria.md freezes '引擎清单与版本'; "
                       "the versions do not exist."},
            {"id": "F-07", "what": "the planner binary is not in the repo",
             "detail": "Fast Downward lives in the gitignored .toolchain/. The config is "
                       "committed; the thing it configures is not. NEEDS_TOOLCHAIN."},
            {"id": "F-09", "what": "three disjoint variant-operator libraries",
             "detail": "proxy/variants.py, exam/artifacts/variant_specs/ (17 specs), and "
                       "a0-spike/pipeline/adapt.py (4 variants) do not share a registry."},
            {"id": "F-10", "what": "statistical adjudication rules exist only as prose",
             "detail": "Theoria.md names three primary endpoints and paired sign/Wilcoxon "
                       "tests. There is no rulebook file. battery/audit/stats.py is "
                       "hand-rolled math, not the adjudication rule."},
            {"id": "F-11", "what": "no claim text, no dual-outcome text",
             "detail": "C1-C5 exist as Theoria.md prose. The 双结局 (pre-registered "
                       "both-ways outcome) text does not exist anywhere in the tree. "
                       "Phase 4 cannot adjudicate against a document that is not written."},
            {"id": "F-12", "what": "no frozen budget table",
             "detail": "baseline-arms/BUDGET_REPORT.md is a per-arm envelope. The frozen "
                       "'$/局硬顶、总局数、止损' table does not exist."},
            {"id": "F-13", "what": "n is computable but not frozen",
             "detail": "baseline-arms/harness/summarise_campaign.py computes the "
                       "per-cell repeat count and names Theoria.md Phase 4 as its "
                       "consumer. The value itself is written down nowhere."},
            {"id": "F-TBD", "what": "all five pre-freeze TBDs are unfilled",
             "detail": "⟨N⟩, dev-pile size, model version string, ⟨B, Δ, k, m, n⟩, and "
                       "target venue + deadline. None has a file."},
        ],
        notes=[
            "freeze/ does not exist. arc-recon/data/campaign_freeze.json is the canary "
            "drift gate written by arc-recon/canary.py:153 -- unrelated to the Phase 4 "
            "freeze. The work order for the real one is monitor/prompts/P-22-freeze-kit.md, "
            "not yet executed.",
            "Of the 13 frozen entries Theoria.md names, 2 are ready (DSL grammar version, "
            "battery v1), 2 are outright missing (statistical rules, claim text), and the "
            "rest exist as code without a frozen, hashed specification.",
            "P-19 does not fill these -- that is P-22's territory. P-19's job is to make "
            "the hole visible inside the released artefact instead of inside someone's head.",
        ],
    ),
    _item(
        8, "incidents", "incident ledger", PARTIAL,
        include=[
            "arc-recon/data/incidents.jsonl",
            "arc-recon/data/contamination_log.jsonl",
            "baseline-arms/INCIDENTS.md",
            "theoria-arm/INCIDENTS.md",
        ],
        gaps=[
            {
                "id": "I-1",
                "what": "there is no single incident ledger",
                "detail": "Three id families (INC-NNN, INC-BA-NNN, INC-TA-NNN), two "
                          "schemas (JSONL and Markdown), four files. "
                          "proxy/LEDGER_FORMAT.md section 6 also defines an `incident` "
                          "record type inside the run ledger that nothing has ever "
                          "written -- a fourth surface. The checklist says 'incident "
                          "ledger', singular. The honest release declares the collection "
                          "explicitly and ships release/INCIDENTS_INDEX.md as a read-only "
                          "index over the four originals; it does not rewrite another "
                          "track's records.",
            },
        ],
    ),
    _item(
        9, "reproducing", "复跑说明 — reproduction instructions", READY,
        include=[
            "release/PLAN.md",
            "release/REPRODUCING.md",
            "release/checklist_spec.py",
            "release/manifest.py",
            "release/reproduce.py",
            "release/verify.sh",
            "release/INCIDENTS_INDEX.md",
        ],
        gaps=[],
        notes=[
            "Before P-19 the tree had no cross-territory reproduction document at all; "
            "the commands were spread across ten READMEs. This item is P-19's own "
            "deliverable, which is why it is the only one that starts empty and ends "
            "READY.",
        ],
    ),
    _item(
        10, "runs", "runs 档案 — the run archives (appendix)", PARTIAL,
        include=["**/runs/**"],
        exclude=["release/runs/**"],
        gaps=[
            {
                "id": "R-1arch",
                "what": "three salvage dirs are near-empty stubs",
                "detail": "theoria-arm/runs/*-salvage*/ contain only a 4-12 line "
                          "ledger.jsonl. They are shipped and labelled `stub` so a reader "
                          "does not have to guess why they are empty.",
            },
        ],
        notes=[
            "Not named in the release sentence, but '这些台账就是我们在地板之上叠的层' "
            "is what the run archives are. theoria-arm is 97% of the bytes, and 30 of its "
            "32 MB is three candidates.jsonl files -- generated theory, not API records.",
        ],
    ),
]


# ---------------------------------------------------------------------------
# Findings the manifester must surface every run. These are not blockers -- the
# redlines are -- but the release is dishonest without them.
# ---------------------------------------------------------------------------
STANDING_FINDINGS = [
    {
        "id": "R-2a",
        "severity": "review",
        "title": "sealed-game difficulty metadata sits in a released ledger",
        "where": "arc-recon/data/recon_ledger.jsonl (the GET /api/games responses)",
        "detail": "The catalogue response lists all 25 games with a `baseline_actions` "
                  "array -- per-level human action counts, e.g. wa30-ee6fef47: "
                  "[71,119,183,98,368,68,79,442,415]. That is not a frame, but it is a "
                  "quantitative difficulty signal about sealed levels, inside an artefact "
                  "we intend to publish. It needs an explicit ruling before release, not "
                  "silence.",
    },
    {
        "id": "R-2b",
        "severity": "review",
        "title": "a sealed game's mechanics are printed in the design document",
        "where": "Theoria.md:161 (teleport rule + unsolvable_L3 parity argument), "
                 "Theoria.md:416 (planned figure 5), and ~50 downstream files",
        "detail": "dc22-fdcac232 is in the sealed pile. This is already adjudicated -- "
                  "arc-recon/data/contamination_log.jsonl records INC-004 setting dc22 to "
                  "design_document_disclosed with claims=retained_with_sensitivity_analysis, "
                  "and the a2 loop ledger carries the authority string ('a self-built world "
                  "isomorphic to DC22's failure structure. No upstream DC22 artefact was "
                  "read'). Not a new leak. But a sealed game's failure structure ships with "
                  "the released prose and figures, so every statistic over the sealed claim "
                  "set carries a sensitivity-analysis obligation, and the release manifest "
                  "is where a reader should meet that fact.",
    },
    {
        "id": "R-2c",
        "severity": "correctness",
        "title": "a contamination-level rationale contradicts the ledger it cites",
        "where": "baseline-arms/TOUCHED_GAMES.md vs baseline-arms/ledger.jsonl",
        "detail": "TOUCHED_GAMES.md defends the scores_only level for sk48-d8078629 on the "
                  "grounds that frames exist only as '<1 frame(s)>' shape summaries and no "
                  "pixels were written to disk. That is true of probe_log.jsonl. It is false "
                  "of ledger.jsonl, which stores 45 full 64x64 pixel arrays for sk48 (plus "
                  "74 ar25, 48 g50t, 18 tn36). All four are dev-pile games, so nothing is "
                  "sealed-breaking -- but the stated rationale is wrong and a reviewer will "
                  "find it. Fixing the wording belongs to the baseline-arms track; naming it "
                  "belongs here.",
    },
]
