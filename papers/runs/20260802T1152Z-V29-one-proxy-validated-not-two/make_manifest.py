"""Regenerate this run's MANIFEST.json. Offline and deterministic.

It hashes what the run delivered and what it read, and it re-runs the instrument
rather than quoting it: the census numbers in the manifest are measured at
generation time, because the whole point of V29 is that a copied number and an
invented one look the same on the page.

    cd papers/runs/20260802T1152Z-V29-one-proxy-validated-not-two
    python make_manifest.py
"""

import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUN = "papers/runs/20260802T1152Z-V29-one-proxy-validated-not-two"

#: Pinned, not derived. Master moves while a ticket is open, and a manifest whose
#: provenance follows it records the reader's day rather than the run's.
BASE_COMMIT = "9e478dd8"

DELIVERED = [
    "papers/phase1-workshop/verify_paper.py",
    "papers/phase1-workshop/test_dualproxy_gate.py",
    RUN + "/NOTES.md",
    RUN + "/RUN_STATE.md",
    RUN + "/baseline_verify.txt",
    RUN + "/after_verify.txt",
    RUN + "/census.json",
    RUN + "/make_manifest.py",
    ("monitor/inbox/20260802T1200Z-W-9203-to-RES-2"
     "-the-v29-gate-is-built-and-S32s-numbers-have-moved.md"),
]

#: Read, not written. The instrument belongs to `verify-lab`; the prose belongs
#: to RES-2. Hashing both is how "I did not touch these" stops being a promise.
EVIDENCE = [
    "verify-lab/dualagent/count.py",
    "verify-lab/DUAL_PROXY.md",
    "papers/phase1-workshop/sections/09_preflight.md",
    "papers/phase1-workshop/PAPER.md",
    "monitor/inbox/20260731T1800Z-S32-to-RES-2-one-proxy-validated-not-two.md",
    "monitor/CHARTER.md",
]


def digest(path):
    sha = hashlib.sha256()
    with open(os.path.join(ROOT, path), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            sha.update(chunk)
    return "sha256:" + sha.hexdigest()


def entries(paths):
    out = []
    for path in paths:
        full = os.path.join(ROOT, path)
        if os.path.exists(full):
            out.append({"path": path, "sha256": digest(path)})
        else:
            out.append({"path": path, "sha256": None, "absent": True})
    return out


def census():
    """Re-run the instrument. Measured at generation time, never quoted."""
    sys.path.insert(0, os.path.join(ROOT, "verify-lab", "dualagent"))
    try:
        import count
        return count.census()
    except Exception as exc:                       # pragma: no cover
        return {"error": "%s: %s" % (type(exc).__name__, exc)}


def git(*args):
    return subprocess.run(("git",) + args, cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


def main():
    live = census()
    env = live.get("env_proxy", {})
    model = live.get("model_proxy", {})

    manifest = {
        "prompt_id": "V29-one-proxy-validated-not-two",
        "prompt": ("the paper's 'dual proxy' is supported by evidence for one "
                   "and a half; make the numbers checkable rather than copied"),
        "territory": "papers",
        "worker": "W-9203",
        "branch": "agent/v29-one-proxy-validated-not-two",
        "base_commit": BASE_COMMIT,
        "head_commit": git("rev-parse", "HEAD"),
        "utc": "2026-08-02T11:51:51Z",
        "seed": None,

        "spend_usd": 0.0,
        "api_calls": 0,
        "network": "none",
        "sealed_pile_contact": "none",

        "scope": {
            "delivered": "the gate: papers/ checks its dual-proxy numbers "
                         "against verify-lab/dualagent/count.py, with a "
                         "negative control that mutates the instrument",
            "not_delivered": "the WP2 prose. monitor/CHARTER.md:22-28 reserves "
                             "writing the paper's body text to RES-2; handed "
                             "over in monitor/inbox/ with paste-ready text",
            "charter": "monitor/CHARTER.md:22-28 -- W-* may 改代码 inside the "
                       "assigned territory, may not 写论文正文",
        },

        # Measured now. The env figures rise whenever any arm plays a leg; the
        # model figures cannot move until a funded provider key exists, which is
        # the gap the paper is being asked to state.
        "census_measured": {
            "env_ledgers": env.get("ledgers"),
            "env_requests_total": env.get("requests_total"),
            "env_requests_live_upstream": env.get("requests_live_upstream"),
            "env_requests_fixture_upstream": env.get("requests_fixture_upstream"),
            "model_calls": model.get("model_calls"),
            "model_refused_401": model.get("refused_401"),
            "model_bypass_attempts": model.get("bypass_attempts"),
            "model_succeeded": model.get("succeeded"),
        },
        "census_as_S32_wrote_it_20260731": {
            "env_ledgers": 24, "env_requests_total": 1009,
            "env_requests_live_upstream": 924,
            "env_requests_fixture_upstream": 85,
            "model_calls": 65, "model_refused_401": 65,
            "model_bypass_attempts": 66, "model_succeeded": 0,
            "note": ("the four env figures are stale and the four model figures "
                     "are bit-stable; the verdict (b) is unchanged and "
                     "strengthened. This is why the gate compares env as a "
                     "floor and model for equality."),
        },

        "baseline": {
            "papers_verify": "RED, 4 problems, at 9e478dd8 before this branch",
            "problems": ["case-studies: no PAPER.md",
                         "related-work: no PAPER.md",
                         "verify_paper: FAIL (3/7) -- C FIGDATA, E UNCITED, F BARE",
                         "pytest exited 1: 1 failed, 10 passed"],
            "none_fixed_here": True,
            "why_it_matters": ("adding a check to an already-failing gate means "
                               "the gate's colour is not evidence about this "
                               "work; only the named check and its negative "
                               "control are"),
        },

        "files": entries(DELIVERED),
        "evidence_read_not_written": entries(EVIDENCE),

        "reproduce": [
            "python -c \"import sys;sys.path.insert(0,'verify-lab/dualagent');"
            "import count,json;print(json.dumps(count.census(),indent=2,sort_keys=True))\"",
            "cd papers/phase1-workshop && python verify_paper.py",
            "cd papers && python -m pytest phase1-workshop/test_dualproxy_gate.py -q",
            "python papers/verify.py",
        ],
    }

    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("wrote %s (%d delivered, %d evidence)"
          % (out, len(manifest["files"]), len(manifest["evidence_read_not_written"])))
    print("census: env %s/%s over %s ledgers | model %s calls, %s answered"
          % (env.get("requests_live_upstream"), env.get("requests_total"),
             env.get("ledgers"), model.get("model_calls"), model.get("succeeded")))


if __name__ == "__main__":
    main()
