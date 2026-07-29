"""Show that `verify.py` rung 5 can go red -- in both of its directions.

A gate that has never been observed to fail is not evidence that anything
passed (D-014). Rung 5 makes two demands of the guard, so there are two ways to
break it, and each one has to be seen breaking:

    neutered  the guard always exits 0 -> the marked stream is not refused
    paranoid  the guard always exits 2 -> the stripped stream is not passed

Both are applied to a **copy** of the tree in a temp directory. Nothing in the
working tree is modified.

    python rung5_red.py --out <dir>
"""

import argparse
import importlib.util
import io
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))

RETURN_LINE = '    return 2 if report["verdict"] == "REFUSED" else 0'
BREAKS = [
    ("neutered  (guard always exits 0)", "    return 0"),
    ("paranoid  (guard always exits 2)", "    return 2"),
]


def build(dst):
    shutil.copytree(os.path.join(REPO, "proxy"), os.path.join(dst, "proxy"),
                    ignore=shutil.ignore_patterns("__pycache__", "var",
                                                  ".pytest_cache", "runs"))
    os.makedirs(os.path.join(dst, "arc-recon", "data"))
    shutil.copy2(os.path.join(REPO, "arc-recon", "data", "piles.json"),
                 os.path.join(dst, "arc-recon", "data", "piles.json"))


def attempt(label, replacement, lines):
    tmp = tempfile.mkdtemp(prefix="rung5-")
    scratch = tempfile.mkdtemp(prefix="rung5-scratch-")
    try:
        build(tmp)
        if replacement is not None:
            guard = os.path.join(tmp, "proxy", "tools",
                                 "check_variant_degeneracy.py")
            source = io.open(guard, encoding="utf-8").read()
            assert source.count(RETURN_LINE) == 1
            io.open(guard, "w", encoding="utf-8", newline="\n").write(
                source.replace(RETURN_LINE, replacement))
        spec = importlib.util.spec_from_file_location(
            "v5_" + label[:4], os.path.join(tmp, "proxy", "verify.py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        problems = []
        module.rung_degeneracy_guard(problems, scratch)
        lines.append("-- %s" % label)
        lines.append("   problems: %d" % len(problems))
        for problem in problems:
            lines.append("   " + problem.splitlines()[0][:300])
        lines.append("")
        return len(problems)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(scratch, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    lines = ["verify.py rung 5, deliberately broken two ways",
             "=" * 46, ""]
    counts = {"unmodified": attempt("unmodified (the shipped guard)", None, lines)}
    for label, replacement in BREAKS:
        counts[label.split()[0]] = attempt(label, replacement, lines)

    lines.append("unmodified=%(unmodified)d neutered=%(neutered)d "
                 "paranoid=%(paranoid)d" % counts)
    lines.append("")
    lines.append("A rung that only ever prints ok would show 0 0 0.")
    with open(os.path.join(args.out, "evidence-rung5-red.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
    print("\n".join(lines))
    return 0 if counts["unmodified"] == 0 and counts["neutered"] and counts["paranoid"] else 1


if __name__ == "__main__":
    sys.exit(main())
