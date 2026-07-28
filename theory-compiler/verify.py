"""theory-compiler's completion gate.

    cd theory-compiler && python verify.py

Three rungs, and the territory is finished only if all three are green:

  1. the suite passes;
  2. the real pipeline runs once, offline -- both handover packages are built
     from their sources, out of tree;
  3. the artefacts that run produced have the fields they claim to have, and
     every sha256 the manifest declares is the digest of the file beside it.

Rung 3 is the one that is usually missing.  A green suite says the compiler
does what its author thought; it does not say two books compiled to four forms
this afternoon, and it does not say the manifest describing the result is a
description of the result.  The two are different claims and only the second
one is "this territory is done".

Three rules this gate keeps, because breaking any of them is how gates in this
repo have failed before:

**It does not write into the working tree.**  `tools/build_handover_packages`
has no `--out`; its `OUT_ROOT` is the tracked `handover_packages/`.  So the
real run here is not that CLI but the two package specs it defines, handed to
`theory_compiler.handover.write_package` with a destination inside a mkdtemp
that is removed on the way out.  Same specs, same builder, same code path --
only the destination differs, and it differs because a gate that rewrites the
artefact it is checking is checking its own output.  (`--check` is still run,
below, as a *note*: it rebuilds in memory and diffs against what is shipped.)

**An empty result is not a pass.**  Every count is checked against a floor
written down here with its reason.  A manifest with zero files, zero levels and
every form `refused` is a structurally perfect manifest; `figures/verify.sh`
currently prints "ok" when both of its builds produced nothing at all, because
two empty trees are byte-identical.  Zero goes red here.

**A missing toolchain does not quietly drop a check.**  `tools/verify_c4.py`
proves the Lean forms by shelling out to `lean`, and its `lean_binary()`
returns `None` when `lean` is not on PATH -- so on a machine without elan the
Lean rung does not skip loudly, it breaks in a way that reads like a different
failure.  This gate therefore does not call it, and says so rather than
appearing to cover it: **the Lean forms are generated and their bytes are
checked here, but they are not proof-checked.**  `python -m tools.verify_c4`
remains the thing that proof-checks them, and it needs `lean` on PATH.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))

# Every top-level key a package manifest must carry.  Read off the shipped
# `handover_packages/a0-cart/MANIFEST.json`, which is `package_format`
# `theoria-handover/1`.
MANIFEST_REQUIRED = (
    "bundle_digest", "compile_warnings", "context_scan", "files", "forms",
    "forms_by_level", "levels", "package_format", "provenance", "tier",
    "title", "world_id",
)

PACKAGE_FORMAT = "theoria-handover/1"

# Floors.  Not decoration: the number below which "the pipeline ran" stops
# being true.
#
# 2 packages: the track ships exactly two, and they were chosen to be the two
# manuals that exist rather than two convenient ones -- one at tier
# `manual+playbook` and one at tier `manual`.  One package means a delivery
# tier vanished without anyone saying so.
MIN_PACKAGES = 2
# 12 files: the shipped packages carry 16 and 14.  A package is the manual, its
# primitives, glossary, readme, seal, manifest, and four files per level over
# at least two levels.  Under 12 a level or a whole form has gone missing and
# the manifest would still be well formed.
MIN_FILES = 12
# 2 levels: `PackageSpec` requires at least two boards, because one board
# cannot show a rule generalising past the board it was written on.
MIN_LEVELS = 2
# 3 generated forms: five are attempted (english, executable, planning_domain,
# planning_problem, proof).  `planning_domain` and `planning_problem` refuse
# today on a declared, recorded ground -- an undeclared `adjacent-above`.  The
# other three generate.  A build in which fewer than three generate is a
# compiler that stopped compiling, and every form `refused` is still a valid
# manifest, which is exactly why this floor is here.
MIN_GENERATED_FORMS = 3
# Exact, not a floor.  `context_scan.blocking` counts citations that would leak
# something out of the bundle.  Zero is the only acceptable number, and "0 of 0
# citations" is caught separately by MIN_FILES.
MAX_BLOCKING = 0


def sh(argv, cwd=HERE, stdin=None):
    """Run a stage, decoding as UTF-8 rather than as the host locale.

    `text=True` alone decodes with cp936 on this box; a child printing UTF-8 --
    and the package titles contain an em dash -- then either mojibakes or
    raises UnicodeDecodeError inside subprocess.run, and a checker that dies
    decoding its child is a checker that did not check.

    The child's environment has the credentials removed.  Nothing in this
    territory is network-facing, so this costs nothing and makes "offline" a
    property of the run rather than a claim about it.
    """
    env = dict(os.environ)
    for name in ("ARC_API_KEY", "ANTHROPIC_API_KEY"):
        env.pop(name, None)
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", env=env,
                          input=stdin)


def fail(problems, message):
    print("   FAIL  %s" % message)
    problems.append(message)


def rung_tests(problems):
    print("[1/3] suite")
    r = sh([sys.executable, "-m", "pytest", "-q"])
    if r.returncode == 5:
        # pytest found nothing to run.  Read as green this would be one more
        # instance of this repo mistaking a check that could not run for one
        # that passed.
        fail(problems, "pytest collected nothing -- testpaths misconfigured, "
                       "which is a broken gate, not a passing one")
        return
    if r.returncode != 0:
        fail(problems, "suite red (exit %d)\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return
    print("   ok    %s" % (r.stdout.strip().splitlines() or ["(no output)"])[-1])


# The real run.  `tools/build_handover_packages` owns the two specs; this asks
# it for them and builds them somewhere else.  Fed on stdin so the gate creates
# no file anywhere but the mkdtemp.
BUILD = r'''
import json, os, sys
sys.path.insert(0, os.getcwd())
from tools.build_handover_packages import PACKAGES
from theory_compiler.handover import write_package

out_root = sys.argv[1]
built = {}
for name in sorted(PACKAGES):
    manifest = write_package(PACKAGES[name](), os.path.join(out_root, name))
    built[name] = {"files": len(manifest["files"]), "tier": manifest["tier"]}
sys.stdout.write("BUILT " + json.dumps(built, sort_keys=True) + "\n")
'''


def rung_real_run(problems, out_root):
    print("[2/3] one real run -- both handover packages built from source, offline")
    r = sh([sys.executable, "-", out_root], stdin=BUILD)
    if r.returncode != 0:
        fail(problems, "the package build exited %d\n%s"
             % (r.returncode, (r.stdout + r.stderr)[-3000:]))
        return []
    names = sorted(n for n in os.listdir(out_root)
                   if os.path.isdir(os.path.join(out_root, n)))
    if len(names) < MIN_PACKAGES:
        fail(problems, "the build exited 0 and produced %d package(s) (%s), "
                       "floor is %d -- an empty build is not a pass"
             % (len(names), ", ".join(names) or "none", MIN_PACKAGES))
        return []
    print("   ok    built %s" % ", ".join(names))
    return names


def rung_artifact_fields(problems, out_root, names):
    print("[3/3] artefact self-check")
    # Repeated from rung 2 on purpose.  `main` only reaches here with a
    # non-empty list, so this is unreachable today -- and it is exactly the
    # line whose absence would let a future refactor print "ok  0 package(s),
    # 0 files, every declared sha256 matches" and exit 0.  A loop over an
    # empty list passes every check inside it.
    if len(names) < MIN_PACKAGES:
        fail(problems, "%d package(s) to check, floor is %d -- there is "
                       "nothing here to be green about"
             % (len(names), MIN_PACKAGES))
        return
    total_files = 0
    for name in names:
        manifest_path = os.path.join(out_root, name, "MANIFEST.json")
        if not os.path.exists(manifest_path):
            fail(problems, "%s has no MANIFEST.json" % name)
            continue
        with open(manifest_path, encoding="utf-8") as fh:
            try:
                manifest = json.load(fh)
            except json.JSONDecodeError as exc:
                fail(problems, "%s/MANIFEST.json is not JSON: %s" % (name, exc))
                continue

        # Deliberately not `manifest.get(key, <what we want>)`.  A gate that
        # defaults a missing field to the value it hopes for passes a build in
        # which the field silently disappeared.
        missing = [k for k in MANIFEST_REQUIRED if k not in manifest]
        if missing:
            fail(problems, "%s/MANIFEST.json is missing %s"
                 % (name, ", ".join(missing)))
            continue

        if manifest["package_format"] != PACKAGE_FORMAT:
            fail(problems, "%s declares package_format %r, not %r"
                 % (name, manifest["package_format"], PACKAGE_FORMAT))

        files = manifest["files"]
        if len(files) < MIN_FILES:
            fail(problems, "%s declares %d file(s), floor is %d -- a package "
                           "that lost a level or a form is not a pass"
                 % (name, len(files), MIN_FILES))
        total_files += len(files)

        if len(manifest["levels"]) < MIN_LEVELS:
            fail(problems, "%s carries %d level(s) (%s), floor is %d"
                 % (name, len(manifest["levels"]),
                    ", ".join(map(str, manifest["levels"])) or "none",
                    MIN_LEVELS))

        forms = manifest["forms"]
        generated = []
        for key in sorted(forms):
            entry = forms[key]
            if "status" not in entry:
                fail(problems, "%s form %r has no status" % (name, key))
                continue
            if entry["status"] == "generated":
                generated.append(key)
            elif not entry.get("why"):
                # A refusal without a reason is indistinguishable from a form
                # that was never attempted.
                fail(problems, "%s form %r is %r with no `why`"
                     % (name, key, entry["status"]))
        if len(generated) < MIN_GENERATED_FORMS:
            fail(problems, "%s generated %d form(s) (%s), floor is %d -- a "
                           "manifest in which every form refused is still a "
                           "well-formed manifest"
                 % (name, len(generated), ", ".join(generated) or "none",
                    MIN_GENERATED_FORMS))

        scan = manifest["context_scan"]
        if "blocking" not in scan:
            fail(problems, "%s context_scan has no `blocking` count" % name)
        elif scan["blocking"] > MAX_BLOCKING:
            fail(problems, "%s context_scan reports %d blocking leak(s); the "
                           "only acceptable number is %d"
                 % (name, scan["blocking"], MAX_BLOCKING))

        # The manifest is a claim about bytes.  Check the bytes.
        bad = []
        for rel in sorted(files):
            full = os.path.join(out_root, name, rel.replace("/", os.sep))
            if not os.path.exists(full):
                bad.append("%s (declared, absent)" % rel)
                continue
            with open(full, "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            if digest != files[rel]:
                bad.append("%s (declared %s, is %s)"
                           % (rel, str(files[rel])[:12], digest[:12]))
        if bad:
            fail(problems, "%s: %d file(s) do not match their declared sha256\n"
                           "     %s"
                 % (name, len(bad), "\n     ".join(bad[:10])))

    if not problems:
        print("   ok    %d package(s), %d files, every declared sha256 matches, "
              "0 blocking leaks" % (len(names), total_files))


def shipped_drift():
    """Do the tracked packages still match what the code produces?

    Reported, not fatal -- the same shape as engine-rig/verify.py's reference
    check, and for the same reason: the run this gate owns is the out-of-tree
    one, and turning a stale committed artefact into a red gate here would
    conflate "the compiler is broken" with "somebody has not re-run the
    writer".  `python -m tools.build_handover_packages --check` is the command
    that answers it, and it writes nothing.
    """
    r = sh([sys.executable, "-m", "tools.build_handover_packages", "--check"])
    if r.returncode == 0:
        return None
    return ("handover_packages/ differs from a fresh build (exit %d)\n         %s"
            % (r.returncode,
               "\n         ".join((r.stdout + r.stderr).strip().splitlines()[:12])))


def main():
    problems = []
    scratch = tempfile.mkdtemp(prefix="theory-compiler-verify-")
    try:
        out_root = os.path.join(scratch, "handover_packages")
        os.makedirs(out_root)
        rung_tests(problems)
        names = rung_real_run(problems, out_root)
        if names:
            rung_artifact_fields(problems, out_root, names)
        drift = shipped_drift()
        if drift:
            print("   note  %s" % drift)
        print("   note  the Lean forms are generated and byte-checked here, "
              "not proof-checked; `python -m tools.verify_c4` does that and "
              "needs `lean` on PATH")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print()
    if problems:
        print("theory-compiler: RED (%d problem(s))" % len(problems))
        return 1
    print("theory-compiler: green -- suite, one real run, artefact fields")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
