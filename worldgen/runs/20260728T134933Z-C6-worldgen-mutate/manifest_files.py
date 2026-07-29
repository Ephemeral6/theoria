"""Fill `MANIFEST.json`'s `files[]` with sha256 of everything this run produced."""

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

TRACKED = (
    "worldgen/mutate.py",
    "worldgen/build.py",
    "worldgen/verify.py",
    "worldgen/README.md",
    "worldgen/RUN_STATE.md",
    "worldgen/core/world.py",
    "worldgen/core/truth.py",
    "worldgen/core/spec.py",
    "worldgen/qc/run_qc.py",
    "worldgen/qc/PREREGISTERED_MUTANTS.md",
    "worldgen/tests/test_mutate.py",
    "worldgen/out/worlds/INDEX.json",
    "worldgen/out/worlds/MUTATIONS.json",
    "worldgen/out/qc/QC_MUTANTS.json",
)


def sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    path = os.path.join(HERE, "MANIFEST.json")
    with open(path, encoding="utf-8") as handle:
        manifest = json.load(handle)

    files = [{"path": rel, "sha256": sha256(os.path.join(ROOT, rel))}
             for rel in TRACKED if os.path.exists(os.path.join(ROOT, rel))]
    # Every mutant directory, by its six shipped artefacts.
    with open(os.path.join(ROOT, "worldgen/out/worlds/MUTATIONS.json"),
              encoding="utf-8") as handle:
        blob = json.load(handle)
    for row in blob["mutations"]:
        for name in ("spec.json", "raw_trace.jsonl", "ground_truth.json",
                     "GROUND_TRUTH.md", "coverage.json", "reversibility.json"):
            rel = "worldgen/out/worlds/%s/%s" % (row["variant_id"], name)
            full = os.path.join(ROOT, rel)
            if os.path.exists(full):
                files.append({"path": rel, "sha256": sha256(full)})

    manifest["files"] = sorted(files, key=lambda r: r["path"])
    manifest["status"] = "complete"
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("%d files hashed -> %s" % (len(files), path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
