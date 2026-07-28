"""Archive one run under `runs/`, with the provenance the method sheet requires.

`monitor/METHOD.md` rows 2, 8 and 9: the standard tail is
`RUN_STATE.md` + a `runs/` archive + `PARTNER_SYNC` + a pushed branch, the
manifest carries `prompt_id` / `branch` / `base_commit` so an artefact can be
traced back to the work order that produced it, and a **failed run is archived
on the same terms as a successful one** — more so, since a failure that cannot
be replayed is not a finding.

    python -m tools.archive_run P-17

Everything recorded here is read off the repository or the artefacts.  Nothing
is typed in, because a hand-entered provenance field is a provenance field that
can be wrong.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from typing import Dict, List

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
ARTIFACTS = os.path.join(HERE, "artifacts")
RUNS = os.path.join(HERE, "runs")

#: Determinism is a repo-wide requirement, so the "seed" is the pair of
#: environment pins `run_all.py` sets rather than an RNG seed: there is no
#: randomness in A3 at all, and saying `seed: 0` would imply there was.
SEED = {
    "THEORIA_DETERMINISTIC_IDS": "1",
    "THEORIA_FIXED_TIME": "2026-07-28T00:00:00Z",
    "rng": "none — A3 draws no random numbers; determinism is structural",
}


def _git(*args: str) -> str:
    out = subprocess.run(("git",) + args, cwd=REPO,
                         capture_output=True, text=True, timeout=60)
    return out.stdout.strip()


def _sha256(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _tree(root: str) -> Dict[str, str]:
    digests: Dict[str, str] = {}
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for name in sorted(files):
            path = os.path.join(base, name)
            digests[os.path.relpath(path, HERE).replace("\\", "/")] = _sha256(path)
    return digests


def archive(prompt_id: str, status: str = "complete",
            note: str = "") -> str:
    stamp = prompt_id.lower().replace("/", "-")
    out_dir = os.path.join(RUNS, stamp)
    os.makedirs(out_dir, exist_ok=True)

    copied: List[str] = []
    for name in sorted(os.listdir(ARTIFACTS)):
        src = os.path.join(ARTIFACTS, name)
        if not os.path.isfile(src):
            continue
        shutil.copy2(src, os.path.join(out_dir, name))
        copied.append(name)

    theory_dir = os.path.join(HERE, "theory")
    manifest = {
        "prompt_id": prompt_id,
        "status": status,
        "note": note,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "head_commit": _git("rev-parse", "HEAD"),
        "base_commit": _git("merge-base", "HEAD", "master"),
        "dirty": bool(_git("status", "--porcelain", "cold-start-a3")),
        "seed": SEED,
        "python": sys.version.split()[0],
        "artifacts": {name: _sha256(os.path.join(out_dir, name))
                      for name in copied},
        "books": {rel: digest for rel, digest in sorted(_tree(theory_dir).items())
                  if rel.endswith(".dsl")},
        "generated_forms": {rel: digest
                            for rel, digest in sorted(_tree(theory_dir).items())
                            if not rel.endswith(".dsl")},
    }

    path = os.path.join(out_dir, "MANIFEST.json")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return path


def main() -> int:
    prompt_id = sys.argv[1] if len(sys.argv) > 1 else "P-17"
    status = sys.argv[2] if len(sys.argv) > 2 else "complete"
    path = archive(prompt_id, status)
    manifest = json.load(open(path, encoding="utf-8"))
    print("archived %d artefacts + %d books to %s"
          % (len(manifest["artifacts"]), len(manifest["books"]),
             os.path.relpath(os.path.dirname(path), HERE)))
    print("branch=%s head=%s base=%s dirty=%s"
          % (manifest["branch"], manifest["head_commit"][:12],
             manifest["base_commit"][:12], manifest["dirty"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
