"""Write this run's MANIFEST.json from the tree, not from memory.

    cd papers/runs/20260804T143000Z-V31 && python _mkmanifest.py

`branch` and `base_commit` are read from git rather than typed, because a
manifest whose provenance fields were hand-copied is a manifest that can be
wrong about the only thing it exists to record. `utc` is the run-directory name,
which is the id the board and `prompt_id` already agree on -- not `now()`, so
re-running this does not move the stamp.
"""
import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RUN_ID = os.path.basename(HERE)
UTC = RUN_ID.split("-")[0]

#: Every file this ticket delivered, repo-relative. Listed rather than globbed:
#: a glob would quietly stop covering a file that moved, and the point of the
#: manifest is that a reader can tell what was claimed.
DELIVERED = [
    "papers/verify.py",
    "papers/phase1-workshop/verify_paper.py",
    "papers/phase1-workshop/test_deferred_uncited.py",
    "papers/phase1-workshop/figures/data/fig1_concept_timeline.json",
    "papers/phase1-workshop/figures/fig1_concept_timeline.txt",
    f"papers/runs/{RUN_ID}/NOTES.md",
    f"papers/runs/{RUN_ID}/E-UNCITED-DEFERRED.md",
    f"papers/runs/{RUN_ID}/RUN_STATE.md",
    f"papers/runs/{RUN_ID}/baseline-verify.txt",
    f"papers/runs/{RUN_ID}/baseline-verify_paper.txt",
    f"papers/runs/{RUN_ID}/after-verify-run1.txt",
    f"papers/runs/{RUN_ID}/after-verify-run2.txt",
    f"papers/runs/{RUN_ID}/_mkmanifest.py",
    f"papers/runs/{RUN_ID}/_probe.py",
]


def git(*args):
    return subprocess.run(["git", "-C", ROOT, *args],
                          capture_output=True, text=True).stdout.strip()


def sha256(rel):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, rel), "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    files = []
    missing = []
    for rel in DELIVERED:
        if os.path.isfile(os.path.join(ROOT, rel)):
            files.append({"path": rel, "sha256": sha256(rel)})
        else:
            missing.append(rel)
    doc = {
        "prompt_id": "V31-papers-gate-red-on-master",
        "prompt": "monitor/board/items/V31-papers-gate-red-on-master.md",
        "worker": "W-9208",
        "territory": "papers",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        # The branch point, not `origin/master` -- which moves under a long
        # ticket. The first version of this file read `rev-parse origin/master`
        # and quietly started recording a commit this work had never seen, three
        # merges after the one it was actually built on. A provenance field that
        # tracks the remote is not provenance.
        "base_commit": git("merge-base", "origin/master", "HEAD"),
        "merged_master_at": git("rev-parse", "origin/master"),
        "utc": f"{UTC[:4]}-{UTC[4:6]}-{UTC[6:8]}T{UTC[9:11]}:{UTC[11:13]}:{UTC[13:15]}Z",
        "seed": None,
        "spend": {"api_calls": 0, "usd": 0.0,
                  "note": "offline; no network, no model call, no game API"},
        "verdict": {
            "before": "papers: RED (4 problem(s)) -- exit 1",
            "after": "papers: green -- exit 0, twice consecutively",
            "deferred": 1,
        },
        "files": files,
    }
    if missing:
        doc["missing"] = missing
    out = os.path.join(HERE, "MANIFEST.json")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")
    print(f"wrote {out}: {len(files)} file(s)"
          + (f", {len(missing)} MISSING: {missing}" if missing else ""))


if __name__ == "__main__":
    main()
