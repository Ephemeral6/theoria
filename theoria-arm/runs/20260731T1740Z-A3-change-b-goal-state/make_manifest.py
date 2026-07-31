"""Write this run's MANIFEST.json: the four required fields, plus a hash per
delivered file.

`CLAUDE.md` requires `prompt_id`, `branch`, `base_commit` and `utc`; a hash per
file is optional and is written here because change B's whole claim is that a
record can be checked rather than believed.

**`files[]` holds run-directory-relative paths and nothing else.**
`armtools/verify_provenance.py` check 10 resolves every entry against the run
directory and fails on any it cannot account for, so listing arm-relative source
paths there would put this run's manifest in breach of the archive's own
contract -- which is exactly what the first draft of this file did, and what
that check caught. The sources change B delivers are hashed under `sources[]`,
which is this manifest's own key and no reader's contract.

Byte-stable: sorted keys, LF, indent 1, and the file hashes are read in binary
so a CRLF checkout is a mismatch rather than a silent pass.

    python runs/20260731T1740Z-A3-change-b-goal-state/make_manifest.py
"""

import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(ARM)

#: The sources change B delivers, relative to the arm. Named rather than
#: walked: a walk would silently start hashing whatever a later session dropped
#: beside these files, and the manifest would still look complete.
SOURCES = (
    "inner/goal.py",
    "inner/loop.py",
    "inner/theorize.py",
    "inner/plan.py",
    "armtools/archive.py",
    "harness/campaign.py",
    "tests/test_goal_state.py",
)

#: This run directory's own contents, relative to it. These and only these may
#: appear in `files[]` (see the module docstring).
ARTEFACTS = (
    "RUN_STATE.md",
    "evidence.py",
    "evidence.json",
    "make_manifest.py",
)


def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                              text=True, timeout=30).stdout.strip()
    except Exception:                                   # noqa: BLE001
        return None


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    def hashed(root, names):
        out = []
        for rel in names:
            path = os.path.join(root, rel)
            if not os.path.exists(path):
                out.append({"path": rel, "sha256": None, "missing": True})
                continue
            out.append({"path": rel, "sha256": _sha256(path),
                        "bytes": os.path.getsize(path)})
        return out

    files = hashed(HERE, ARTEFACTS)
    sources = hashed(ARM, SOURCES)

    manifest = {
        "prompt_id": "A3-change-b",
        "slug": os.path.basename(HERE),
        "arm": "theoria",
        "territory": "theoria-arm",
        "utc": "2026-07-31T17:40:00Z",
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": _git("rev-parse", "master"),
        "head_commit": _git("rev-parse", "HEAD"),
        "seed": None,
        "seed_note": ("nothing here draws a random number. The evidence script "
                      "makes no model call and no network call, so its output "
                      "is a function of the sources hashed below and of "
                      "nothing else."),
        "spend": {"usd": 0.0, "arc_actions": 0, "model_calls": 0,
                  "note": "offline only: proxy/mock, a scratch spend pool in a "
                          "temp directory, and no desk."},
        "change": "B -- goal-absence as a first-class state (inner/goal.py)",
        "default_behaviour_unchanged": True,
        "files": files,
        "sources": sources,
        "sources_note": ("arm-relative, and deliberately NOT in `files[]`: "
                         "verify_provenance check 10 resolves `files[]` "
                         "against the run directory."),
    }

    path = os.path.join(HERE, "MANIFEST.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    print(json.dumps(manifest, indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
