"""Mutation harness for V19 review.

Each mutant gets its own copy of the `worldgen` package under a scratch root.
Runs `python -m pytest worldgen -q` and `python -m worldgen.build --into <out>`
inside that root and records both exit codes.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

SRC = r"C:\Users\user\Desktop\theoria\.worktrees\v19-unverified-is-not-true\worldgen"
SCRATCH = r"C:\Users\user\AppData\Local\Temp\claude\C--Users-user-Desktop-theoria\9c21443e-474e-49a2-9789-41ea1e7d33ac\scratchpad\mut"
SKIP = ("__pycache__", ".pytest_cache", ".pytest-runs", "runs")


class Failed(RuntimeError):
    pass


def apply_edits(root, edits):
    for rel, old, new in edits:
        path = os.path.join(root, "worldgen", rel.replace("/", os.sep))
        with open(path, encoding="utf-8", newline="") as h:
            text = h.read()
        n = text.count(old)
        if n != 1:
            raise Failed("anchor occurs %d times in %s: %r" % (n, rel, old[:80]))
        with open(path, "w", encoding="utf-8", newline="") as h:
            h.write(text.replace(old, new))


def run_one(name, edits):
    root = tempfile.mkdtemp(prefix="v19-" + name[:20] + "-", dir=SCRATCH)
    try:
        shutil.copytree(SRC, os.path.join(root, "worldgen"),
                        ignore=shutil.ignore_patterns(*SKIP))
        try:
            apply_edits(root, edits)
        except Failed as exc:
            return {"mutant": name, "error": str(exc)}
        env = dict(os.environ)
        env["PYTHONPATH"] = root
        env["PYTHONIOENCODING"] = "utf-8"
        env.pop("PYTHONDONTWRITEBYTECODE", None)
        pt = subprocess.run([sys.executable, "-m", "pytest", "worldgen", "-q",
                             "-p", "no:cacheprovider"],
                            cwd=root, env=env, capture_output=True, timeout=1800)
        outdir = os.path.join(root, "buildout")
        bd = subprocess.run([sys.executable, "-m", "worldgen.build",
                             "--into", outdir, "--quiet"],
                            cwd=root, env=env, capture_output=True, timeout=1800)
        ptail = (pt.stdout + pt.stderr).decode("utf-8", "replace")
        btail = (bd.stdout + bd.stderr).decode("utf-8", "replace")
        return {
            "mutant": name,
            "pytest_rc": pt.returncode,
            "build_rc": bd.returncode,
            "pytest_tail": ptail[-1200:],
            "build_tail": btail[-1500:],
        }
    finally:
        shutil.rmtree(root, ignore_errors=True)


def main():
    spec_path = sys.argv[1]
    out_path = sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    with open(spec_path, encoding="utf-8") as h:
        mutants = json.load(h)
    os.makedirs(SCRATCH, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(run_one, m["name"], m["edits"]) for m in mutants]
        for f in futs:
            r = f.result()
            results.append(r)
            print(json.dumps({k: v for k, v in r.items()
                              if k in ("mutant", "pytest_rc", "build_rc", "error")}),
                  flush=True)
    with open(out_path, "w", encoding="utf-8") as h:
        json.dump(results, h, indent=1)


if __name__ == "__main__":
    main()
