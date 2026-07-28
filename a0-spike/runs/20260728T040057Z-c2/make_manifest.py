"""Write this run's MANIFEST.json, per CLAUDE.md's provenance convention.

Required keys: prompt_id, branch, base_commit, utc. Optional: files[].sha256 --
taken here over every file the run produced or changed, so the manifest pins the
artefacts rather than merely describing them.

Deterministic apart from `utc` and `generated_from_commit`, which are passed in
rather than read from the clock, so re-running this does not silently restamp a
manifest that was meant to record a different moment.

Run:  python runs/20260728T040057Z-c2/make_manifest.py --utc <ISO8601Z>
"""

import argparse
import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SPIKE = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(SPIKE)

# Everything this run wrote or changed, repo-relative. Listed explicitly rather
# than globbed: a manifest that quietly grows a file is a manifest nobody reads.
TRACKED = [
    "a0-spike/.gitattributes",
    "a0-spike/THEORIZE_LOG.md",
    "a0-spike/theory/theory.dsl",
    "a0-spike/pipeline/gen_exec.py",
    "a0-spike/pipeline/cross_form.py",
    "a0-spike/probes/__init__.py",
    "a0-spike/probes/semantics_probe.py",
    "a0-spike/tests/test_a0.py",
    "a0-spike/artifacts/theory_exec.py",
    "a0-spike/artifacts/A0.lean",
    "a0-spike/artifacts/a0_report.json",
    "a0-spike/artifacts/pddl/domain.pddl",
    "a0-spike/artifacts/pddl/problem_match.pddl",
    "a0-spike/artifacts/pddl/problem_mismatch.pddl",
    "a0-spike/runs/20260728T040057Z-c2/PLAN.md",
    "a0-spike/runs/20260728T040057Z-c2/RUN_STATE.md",
    "a0-spike/runs/20260728T040057Z-c2/ADVERSARIAL_REVIEW.md",
    "a0-spike/runs/20260728T040057Z-c2/semantics_probe.json",
    "a0-spike/runs/20260728T040057Z-c2/make_manifest.py",
]


def digest(path: str):
    full = os.path.join(REPO, path)
    if not os.path.isfile(full):
        return None
    with open(full, "rb") as fh:
        data = fh.read()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", REPO] + list(args),
                          capture_output=True, text=True).stdout.strip()


def verify() -> int:
    """Do the recorded digests match what git actually stores?

    Worth its own mode because they silently did not, once. On Windows with
    `core.autocrlf=true` an editor writes CRLF, git stores LF, and a manifest
    built from the *working copy* pins bytes no fresh checkout will ever
    reproduce -- 7 of 19 entries, undetectable by reading either file. A manifest
    whose digests do not match the repository is worse than no manifest: it looks
    like verification and answers a question nobody asked.

    Compares against the index (`git show :<path>`), which is what will be
    committed and therefore what a clone receives.
    """
    path = os.path.join(HERE, "MANIFEST.json")
    if not os.path.isfile(path):
        print("no MANIFEST.json to verify")
        return 1
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)

    bad = []
    for name, record in sorted(manifest.get("files", {}).items()):
        # Test the exit code, never the emptiness of stdout: `probes/__init__.py`
        # is a legitimately empty file, and reading "no bytes" as "no such blob"
        # reported it as missing when it was staged and correct. A verifier that
        # cries wolf on an empty file gets switched off.
        shown = subprocess.run(["git", "-C", REPO, "show", ":" + name],
                               capture_output=True)
        blob = shown.stdout
        if shown.returncode != 0:
            bad.append((name, "not in the index"))
        elif hashlib.sha256(blob).hexdigest() != record["sha256"]:
            bad.append((name, "digest differs from the stored blob (line endings?)"))

    for name, why in bad:
        print("  MISMATCH %s -- %s" % (name, why))
    print("%d files; %d mismatched" % (len(manifest.get("files", {})), len(bad)))
    return 1 if bad else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--utc", help="ISO8601 Z, the run's stamp")
    parser.add_argument("--verify", action="store_true",
                        help="check recorded digests against the git index")
    args = parser.parse_args()
    if args.verify:
        return verify()
    if not args.utc:
        parser.error("--utc is required unless --verify is given")

    files = {}
    missing = []
    for path in sorted(TRACKED):
        entry = digest(path)
        if entry is None:
            missing.append(path)
        else:
            files[path] = entry

    manifest = {
        "prompt_id": "C2-semantics-migrate",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "utc": args.utc,
        "measured_on": {
            "commit": "3205992",
            "note": (
                "Every number in `evidence` was first measured with a0-spike at "
                "3205992. `base_commit` above is later: master gained ten "
                "monitor/ops commits mid-run and was merged in, and `git diff "
                "3205992 e182c95 -- a0-spike/ theory-compiler/ CONTRACTS/` is "
                "empty, so none of them can touch these numbers. All three gates "
                "(pytest, run_a0, semantics_probe) were re-run green on the "
                "merged tree rather than argued about."
            ),
        },
        "run_id": "20260728T040057Z-c2",
        "track": "engine-rig",
        "territory": "a0-spike/ only; PARTNER_SYNC.md appended",
        "contract": "CONTRACTS/dsl_grammar_v0.2.md revision item 1 (ledger E-03)",
        "what": (
            "Migrate a0-spike's manual from dsl_grammar v0.1 to v0.2 by "
            "adjudicating the three `semantics:` statements as facts about the "
            "A0 world, each by refuting its alternative against ground truth."
        ),
        "adjudicated": {
            "frame": "persist",
            "conflict": "exclusive",
            "cascade": "single_frame",
        },
        "evidence": {
            "instrument": "a0-spike/probes/semantics_probe.py",
            "representable_state_action_pairs": 47040,
            "levels": 5,
            "frame_persist_only_wrong": 0,
            "frame_reset_only_wrong": 45630,
            "cascade_single_frame_only_wrong": 0,
            "cascade_multi_frame_only_wrong": 27030,
            "conflict_max_rules_claiming_one_object": 1,
            "both_readings_wrong": 52,
            "both_readings_wrong_disposition": (
                "a push2 guard defect (ledger X-5), evidence about neither "
                "statement; not filtered out, reported"
            ),
        },
        "tests": "python -m pytest -q -> 44 passed, 0 failed, 0 error "
                 "(baseline at base_commit: 32 FAILED/ERROR, 6 passed)",
        "pipeline": "python -m pipeline.run_a0 -> exit 0; certify exact, "
                    "held-out 39960 states 0 mismatches, lean=py 9408/9408",
        "adversarial_review": (
            "One pass, commissioned to refute and told its report would be filed "
            "unedited. Confirmed all three values SOUND against world/sokoban2.py; "
            "landed four hits on the evidence, all accepted: the on-wall exclusion "
            "was a reachability argument in disguise (render is injective -- 2352 "
            "states, 2352 frames, 0 collisions), the 52 are a push2 guard defect "
            "(X-5), the generated step() declared `exclusive` without enforcing it, "
            "and `frame persist` holds only under the wide reading of the compound "
            "`slid` event (the narrow reading costs 376 mismatches, X-1). "
            "runs/20260728T040057Z-c2/ADVERSARIAL_REVIEW.md"
        ),
        "open_ledger_entries": ["X-1", "X-2", "X-3", "X-4", "X-5"],
        "determinism": (
            "The probe and all four forms are deterministic: no seed, no clock, "
            "no network. One field is not byte-reproducible across machines -- "
            "a0_report.json records the absolute path of the Lean binary that "
            "ran; ledger X-4, recorded not fixed."
        ),
        "network": "none. No API calls, no sealed-pile contact.",
        "files": files,
    }
    if missing:
        manifest["files_declared_but_absent"] = sorted(missing)

    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(manifest, indent=2, sort_keys=True,
                            ensure_ascii=False) + "\n")
    print("-> %s (%d files digested, %d absent)"
          % (out, len(files), len(missing)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
