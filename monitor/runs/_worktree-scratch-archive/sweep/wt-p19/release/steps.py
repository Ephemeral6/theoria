"""What a stranger can re-run, what they cannot, and why.

Every deterministic producer in the tree gets one entry. Entries that cannot run
without a live API, a credential, or a binary the repo does not carry are listed
too -- with the reason -- because a reproduction report that silently omits the
unrunnable half is a brochure.

Grades (the only five words the report may use for an outcome, plus FAILED):

    REPRODUCED           re-ran, and every byte matched the manifest
    REPRODUCED_UNSTABLE  re-ran, output is semantically equivalent but differs
                         in bytes; the differing paths are named
    NEEDS_API            needs the live ARC API, a model API, or quota
    NEEDS_TOOLCHAIN      needs a local binary the repo does not ship
    KNOWN_GAP            no regeneration path exists in the tree at all
    FAILED               ran, and did not succeed

A skipped step is never graded REPRODUCED. An environment problem is not an
excuse; it is a grade.
"""

import sys

PY = sys.executable

# `phase`: steps run in phase order. Fixtures before the engines that consume
# them, compilers before the suites that assert on their output.
STEPS = [
    # ---- phase 1: the engine rig -------------------------------------------
    {
        "id": "engine-rig.fixtures",
        "territory": "engine-rig",
        "phase": 1,
        "cwd": "engine-rig",
        "argv": [PY, "-m", "fixtures.generate_all"],
        "claim": "the six engines' synthetic fixtures regenerate byte-identically",
        "source": "engine-rig/README.md",
        "timeout": 900,
    },
    {
        "id": "engine-rig.run_all",
        "territory": "engine-rig",
        "phase": 1,
        "cwd": "engine-rig",
        "argv": [PY, "-m", "tools.run_all", "--out", "artifacts/candidates.jsonl",
                 "--deterministic", "--force"],
        "claim": "all engines end to end reproduce artifacts/candidates.jsonl",
        "source": "engine-rig/README.md",
        "timeout": 1800,
    },
    {
        "id": "engine-rig.pytest",
        "territory": "engine-rig",
        "phase": 1,
        "cwd": "engine-rig",
        "argv": [PY, "-m", "pytest", "-q"],
        "claim": "the engine suite passes offline",
        "source": "engine-rig/README.md",
        "kind": "suite",
        "timeout": 1800,
    },

    # ---- phase 2: the cold starts, in the order they were built ------------
    {
        "id": "a0-spike.run",
        "territory": "a0-spike",
        "phase": 2,
        "cwd": "a0-spike",
        "argv": [PY, "-m", "pipeline.run_a0"],
        "claim": "A0 regenerates its Lean/Python/PDDL artefacts from the self-built world",
        "source": "a0-spike/README.md",
        "timeout": 1800,
        "note": "The Lean stage skips itself when no toolchain is present and says so.",
    },
    {
        "id": "a0-spike.pytest",
        "territory": "a0-spike",
        "phase": 2,
        "cwd": "a0-spike",
        "argv": [PY, "-m", "pytest", "-q"],
        "claim": "the A0 suite passes offline",
        "source": "a0-spike/README.md",
        "kind": "suite",
        "timeout": 1800,
    },
    {
        "id": "cold-start-a0.run_all",
        "territory": "cold-start-a0",
        "phase": 2,
        "cwd": "cold-start-a0",
        "argv": [PY, "run_all.py"],
        "claim": "the A0 cold start recompiles the manual into all four forms",
        "source": "cold-start-a0/README.md",
        "timeout": 1800,
        "note": "Another track's directory. Run, never edited -- see CLAUDE.md.",
    },
    {
        "id": "cold-start-a2.run_all",
        "territory": "cold-start-a2",
        "phase": 2,
        "cwd": "cold-start-a2",
        "argv": [PY, "run_all.py"],
        "claim": "A2's full ring, including the deliberately-false 'holed' exhibit",
        "source": "cold-start-a2/README.md",
        "timeout": 1800,
    },
    {
        "id": "cold-start-a2.pytest",
        "territory": "cold-start-a2",
        "phase": 2,
        "cwd": "cold-start-a2",
        "argv": [PY, "-m", "pytest", "-q"],
        "claim": "the A2 suite passes offline",
        "source": "cold-start-a2/README.md",
        "kind": "suite",
        "timeout": 1800,
    },
    {
        "id": "cold-start-a3.run_all",
        "territory": "cold-start-a3",
        "phase": 2,
        "cwd": "cold-start-a3",
        "argv": [PY, "run_all.py"],
        "claim": "A3's six arms, all four forms each",
        "source": "cold-start-a3/README.md",
        "timeout": 1800,
        "note": "cold-start-a3/README.md:109 -- 'there is no seed, because there is "
                "no randomness; determinism here is structural.'",
    },
    {
        "id": "cold-start-a3.pytest",
        "territory": "cold-start-a3",
        "phase": 2,
        "cwd": "cold-start-a3",
        "argv": [PY, "-m", "pytest", "-q"],
        "claim": "the A3 suite passes offline",
        "source": "cold-start-a3/README.md",
        "kind": "suite",
        "timeout": 1800,
    },

    # ---- phase 3: the compiler (the two books -> four forms) ---------------
    {
        "id": "theory-compiler.pytest",
        "territory": "theory-compiler",
        "phase": 3,
        "cwd": "theory-compiler",
        "argv": [PY, "-m", "pytest", "-q"],
        "claim": "the four generators, the parsers, and the staleness guard on "
                 "lean/TheoriaLean.lean",
        "source": "theory-compiler/README.md",
        "kind": "suite",
        "timeout": 1800,
        "note": "Without a Lean toolchain the Lean-compiling tests skip. "
                "test_the_committed_lean_artifact_is_not_stale runs either way -- it "
                "byte-compares the committed proof against fresh generator output.",
    },

    # ---- phase 4: the metrics battery --------------------------------------
    {
        "id": "battery.run",
        "territory": "battery",
        "phase": 4,
        "cwd": ".",
        "argv": [PY, "-m", "battery.run_battery"],
        "claim": "38 metrics recomputed over the existing traces, byte-identically",
        "source": "battery/README.md",
        "timeout": 1800,
    },
    {
        "id": "battery.docs",
        "territory": "battery",
        "phase": 4,
        "cwd": ".",
        "argv": [PY, "-m", "battery.docs"],
        "claim": "METRICS.md regenerates from the metric registry",
        "source": "battery/README.md",
        "timeout": 600,
    },
    {
        "id": "battery.pytest",
        "territory": "battery",
        "phase": 4,
        "cwd": ".",
        "argv": [PY, "-m", "pytest", "battery/tests", "-q"],
        "claim": "the battery suite, including its own determinism test",
        "source": "battery/README.md",
        "kind": "suite",
        "timeout": 1800,
    },

    # ---- phase 5: shell, arm, exam -----------------------------------------
    {
        "id": "proxy.pytest",
        "territory": "proxy",
        "phase": 5,
        "cwd": "proxy",
        "argv": [PY, "-m", "pytest", "-q"],
        "claim": "the environment/model proxies, the vault, and the red-team fixtures",
        "source": "proxy/README.md",
        "kind": "suite",
        "timeout": 1800,
    },
    {
        "id": "proxy.runner_mock",
        "territory": "proxy",
        "phase": 5,
        "cwd": ".",
        "argv": [PY, "-m", "proxy.runner", "--mock"],
        "claim": "both proxies run end to end against the mock environment",
        "source": "proxy/README.md",
        "timeout": 900,
        "creates_untracked": True,
        "note": "Writes into proxy/var/, which is gitignored: the format is tracked, "
                "the data a run produces is not.",
    },
    {
        "id": "theoria-arm.pytest",
        "territory": "theoria-arm",
        "phase": 5,
        "cwd": "theoria-arm",
        "argv": [PY, "-m", "pytest", "-q"],
        "claim": "the inner loop's five beats and ten constraints, offline",
        "source": "theoria-arm/README.md",
        "kind": "suite",
        "timeout": 1800,
    },
    {
        "id": "theoria-arm.mock_run",
        "territory": "theoria-arm",
        "phase": 5,
        "cwd": "theoria-arm",
        "argv": [PY, "-m", "harness.run", "--mock", "--budget", "8",
                 "--slug", "p19-repro-smoke"],
        "claim": "the arm turns a full loop with no key, no socket, no model call",
        "source": "theoria-arm/README.md",
        "timeout": 900,
        "creates_untracked": True,
        "note": "Creates a new run directory. Dry-run slugs are gitignored by "
                "theoria-arm/.gitignore.",
    },
    {
        "id": "exam.pytest",
        "territory": "exam",
        "phase": 5,
        "cwd": "exam",
        "argv": [PY, "-m", "pytest", "-q"],
        "claim": "the exam builder, its leakage guard, and its zero-network tripwire",
        "source": "exam/README.md",
        "kind": "suite",
        "timeout": 1800,
    },
    {
        "id": "exam.build_papers",
        "territory": "exam",
        "phase": 5,
        "cwd": ".",
        "argv": [PY, "-m", "exam.tools.build_papers"],
        "claim": "the handover bundles regenerate, model_calls: 0",
        "source": "exam/README.md",
        "timeout": 900,
    },

    # ---- phase 6: the release kit checks itself ----------------------------
    {
        "id": "release.manifest_check",
        "territory": "release",
        "phase": 6,
        "cwd": ".",
        "argv": [PY, "release/manifest.py", "--check"],
        "claim": "after everything above re-ran, every hash still matches the "
                 "manifest and both red lines are still green",
        "source": "release/REPRODUCING.md",
        "timeout": 900,
    },
]


# ---------------------------------------------------------------------------
# The half a stranger cannot run. Each entry says what would be needed.
# ---------------------------------------------------------------------------
UNRUNNABLE = [
    {
        "id": "lean.lake_build",
        "territory": "theory-compiler",
        "grade": "NEEDS_TOOLCHAIN",
        "what": "cd theory-compiler/lean && lake build",
        "needs": "leanprover/lean4:v4.9.0 via elan. lake-manifest.json has "
                 "\"packages\": [] -- no Mathlib -- so the build itself is offline "
                 "once the toolchain is installed.",
        "probe": ["lean", "lake"],
        "why_it_matters": "Without it the 12 Lean-compiling tests skip rather than "
                          "run, and a default-green suite has not checked the axiom "
                          "sets it is about to be quoted for. Set "
                          "THEORIA_REQUIRE_LEAN=1 to turn the skip into an error.",
    },
    {
        "id": "engine-rig.fast_downward",
        "territory": "engine-rig",
        "grade": "NEEDS_TOOLCHAIN",
        "what": "engine-rig's fd_adapter against real Fast Downward",
        "needs": "Fast Downward on PATH or $FAST_DOWNWARD. The repo ships the "
                 "config (engines/fd_adapter/backends.py) and the toolchain "
                 "manifest, not the binary; .toolchain/ is gitignored.",
        "probe": ["fast-downward.py"],
        "env_probe": ["FAST_DOWNWARD"],
        "why_it_matters": "Without it fd_adapter falls back to a grounded-STRIPS BFS "
                          "stub behind the same solve(domain, problem) interface. "
                          "Length-optimal for unit costs, so the tests pass either "
                          "way -- but the planner column of the release is a stub "
                          "unless this is installed.",
    },
    {
        "id": "arc.live_play",
        "territory": "theoria-arm / baseline-arms / arc-recon / proxy",
        "grade": "NEEDS_API",
        "what": "every ledger row that came from three.arcprize.org, and every "
                "model_call row",
        "needs": "ARC_API_KEY in a gitignored .env, an Anthropic key, quota, and "
                 "money. The rate gate is 600 RPM (browser-ops/TERMS.md).",
        "why_it_matters": "This is the honest floor of the release: "
                          "baseline-arms/ledger.jsonl, arc-recon's recon ledger, and "
                          "theoria-arm's nine run archives are EVIDENCE, not output. "
                          "A stranger can audit them -- the schema validators, the "
                          "replay spot-check, and the scorer all run offline over the "
                          "committed bytes -- but cannot regenerate them, and re-running "
                          "them would not reproduce them anyway: the API is a live "
                          "system.",
    },
    {
        "id": "lean.regenerate_flagship",
        "territory": "theory-compiler",
        "grade": "KNOWN_GAP",
        "what": "regenerating theory-compiler/lean/TheoriaLean.lean",
        "needs": "nothing exists. tests/test_gen_lean.py:274 points at the README; "
                 "README.md:41-55 writes a different filename. The test's own "
                 "docstring: 'nothing regenerates it on its own -- so it drifts "
                 "silently. It did.'",
        "why_it_matters": "The staleness test is the only guard on the flagship "
                          "proof. It is a real hole in the four-form story and it is "
                          "reported here rather than rounded off.",
    },
    {
        "id": "freeze.manifest",
        "territory": "(none yet)",
        "grade": "KNOWN_GAP",
        "what": "the Phase 4 freeze manifest",
        "needs": "freeze/ does not exist. Of Theoria.md's 13 frozen entries, the "
                 "statistical adjudication rules and the claim/dual-outcome text "
                 "have no file at all, and the five pre-freeze TBDs are unfilled.",
        "why_it_matters": "Phase 4 adjudicates against pre-registered text. There is "
                          "nothing yet to adjudicate against. Tracked as P-22; named "
                          "here so the release does not imply otherwise.",
    },
]
