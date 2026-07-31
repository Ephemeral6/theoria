"""Attack line 4: where does every symbol in the "genuine pre-2a1c30d module" come from?

Run: cd engine-rig && python runs/20260730T120000Z-E18/adversarial/old_module_provenance.py

The hypothesis under test is that `_load_old_potential()` imports a file by path
and that file then silently resolves its dependencies against *today's*
`sys.path`, so "old code" is really a mix.  Three ways to catch that:

1. Diff `sys.modules` across the load.  Anything new that lives under
   `engine-rig/engines/` would be today's code being pulled in behind the
   extracted file.
2. For every callable/class reachable from the loaded module, print the file its
   code object actually came from.  A symbol whose `co_filename` is under
   `engine-rig/engines/` is contaminated.
3. Byte-compare the materialised file against `git show`, and check that
   `solve_certificate` closes over nothing from HEAD (`__globals__` identity).
"""

import hashlib
import inspect
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE_RIG = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REPO = os.path.dirname(ENGINE_RIG)
for p in (REPO, ENGINE_RIG):
    if p not in sys.path:
        sys.path.insert(0, p)

sys.path.insert(0, ENGINE_RIG)
from tools.survey_numbers import lp_incomplete       # noqa: E402
from engines.lp_potential import potential as head_potential  # noqa: E402

ENGINES_DIR = os.path.join(ENGINE_RIG, "engines")


def main():
    before = dict(sys.modules)
    old, path = lp_incomplete._load_old_potential()
    after = dict(sys.modules)

    new_modules = {}
    for name in sorted(set(after) - set(before)):
        mod = after[name]
        new_modules[name] = getattr(mod, "__file__", None)

    # (1) did anything under engines/ get imported as a side effect?
    engine_side_effects = {
        n: f for n, f in new_modules.items()
        if f and os.path.abspath(f).startswith(ENGINES_DIR)
    }

    # (2) provenance of every symbol on the loaded module
    provenance = {}
    contaminated = {}
    for name in sorted(vars(old)):
        if name.startswith("__"):
            continue
        obj = vars(old)[name]
        f = None
        try:
            f = inspect.getfile(obj)
        except (TypeError, OSError):
            mod = getattr(obj, "__module__", None)
            m = sys.modules.get(mod) if mod else None
            f = getattr(m, "__file__", None)
        provenance[name] = f
        if f and os.path.abspath(f).startswith(ENGINES_DIR):
            contaminated[name] = f

    # (3) bytes and globals
    rev = "%s^:%s" % (lp_incomplete.CALIBER_COMMIT, lp_incomplete.OLD_POTENTIAL_PATH)
    want = subprocess.run(["git", "show", rev], cwd=REPO,
                          capture_output=True, check=True).stdout
    with open(path, "rb") as fh:
        got = fh.read()

    g = old.solve_certificate.__globals__
    head_g = head_potential.solve_certificate.__globals__

    # symbols the old solve_certificate actually reads at call time
    reads = sorted(set(old.solve_certificate.__code__.co_names))

    out = {
        "materialised_at": path,
        "materialised_under_engines": os.path.abspath(path).startswith(ENGINES_DIR),
        "bytes_match_git_show": want == got,
        "sha256": hashlib.sha256(got).hexdigest(),
        "modules_added_to_sys_modules_by_the_load": new_modules,
        "engine_side_effect_imports": engine_side_effects,
        "loaded_module_registered_in_sys_modules":
            "_e18_potential_pre_2a1c30d" in sys.modules,
        "symbol_provenance": provenance,
        "symbols_coming_from_engines_dir": contaminated,
        "globals_is_head_globals": g is head_g,
        "solve_certificate_co_filename": old.solve_certificate.__code__.co_filename,
        "head_solve_certificate_co_filename":
            head_potential.solve_certificate.__code__.co_filename,
        "old_solve_certificate_is_head_object":
            old.solve_certificate is head_potential.solve_certificate,
        "old_CertificateError_is_head_class":
            old.CertificateError is head_potential.CertificateError,
        "old_Move_is_head_Move": old.Move is head_potential.Move,
        "old_has_LpUnavailable": hasattr(old, "LpUnavailable"),
        "old_has_LpOutcome": hasattr(old, "LpOutcome"),
        "old_has_STATUS_WORDS": hasattr(old, "STATUS_WORDS"),
        "solve_certificate_reads_names": reads,
        "names_resolved_from_old_module_globals": {
            n: (n in g) for n in reads
        },
        "shared_by_design": {
            "linprog_is_same_object": old.linprog is head_potential.linprog,
            "numpy_is_same_module": old.np is head_potential.np,
        },
    }
    json.dump(out, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
