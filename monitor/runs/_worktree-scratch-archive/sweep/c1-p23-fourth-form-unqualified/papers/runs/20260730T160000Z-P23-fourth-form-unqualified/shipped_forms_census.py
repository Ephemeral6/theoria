#!/usr/bin/env python3
"""P23 — what the repository actually ships from the two books.

The abstract says the two books are "compiled to four co-derived forms — Lean,
Python, PDDL and Markdown".  C14 measured that claim by running the
theory-compiler backend over every `.dsl` in the tree: a population defined by
*input*.  C14's own §0 records that this scoping nearly published a wrong
headline, because a second PDDL backend leaves no trace in an input-defined
corpus.

This tool measures a different population, chosen because it is the one the
abstract's sentence is about and the one a referee can inspect without running
anything: **the artefacts the repository ships**.  A compile site is a directory
holding generated forms; the question asked of each is which of the four forms
is present, and — for the PDDL form — whether its actions say anything.

Two numbers come out, and they must not be merged:

  * form presence  — of the four forms, how many exist at each site;
  * form content   — for the PDDL that does exist, how many actions are
                     well-formed and non-vacuous.

A missing form and a vacuous form are different failures.  The paper's sentence
is falsified by either, but the honest correction depends on which.

Run:  python shipped_forms_census.py <repo-root>
Writes out/shipped_forms.json and prints the tables.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

# --- the four forms, by the extension each is published under ---------------
# Keyed by the paper's own names.  `dsl` is the *source* (the two books), not a
# form; it is tracked separately so that a site holding only sources is not
# scored as if it had compiled.
FORM_GLOBS = {
    "Lean": ("*.lean",),
    "Python": ("*.py",),
    "PDDL": ("domain.pddl", "problem.pddl", "*.pddl"),
    "Markdown": ("*.md",),
}

# A compile site is a directory that a generator writes into.  Found by name
# rather than by a hand-list, so a site added later is picked up.
SITE_DIR_NAMES = ("generated",)

# Backend attribution.  Backend B stamps its output; backend A does not, so
# "no stamp" is the discriminator and is verified below by checking that no
# stamped file is ever scored as backend A's.
BACKEND_B_STAMP = "gen_pddl_a0.py"

ACTION_RE = re.compile(r"\(:action\s+([A-Za-z0-9_\-]+)(.*?)(?=\n\s*\(:action|\n\s*\)\s*$|\Z)", re.S)
PARAMS_RE = re.compile(r":parameters\s*\((.*?)\)", re.S)
VAR_RE = re.compile(r"\?[A-Za-z0-9_\-]+")
PRED_RE = re.compile(r"\(([A-Za-z][A-Za-z0-9_\-]*)")
# Connectives are not predicates.
CONNECTIVES = {"and", "or", "not", "when", "forall", "exists", "=", "imply"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _section(body: str, keyword: str) -> str:
    """Return the balanced s-expression following `:keyword` in an action body."""
    i = body.find(f":{keyword}")
    if i < 0:
        return ""
    j = body.find("(", i)
    if j < 0:
        return ""
    depth = 0
    for k in range(j, len(body)):
        if body[k] == "(":
            depth += 1
        elif body[k] == ")":
            depth -= 1
            if depth == 0:
                return body[j : k + 1]
    return body[j:]


def _literals(sexp: str) -> list[str]:
    """Predicate names in a formula, connectives excluded.

    `(and )` and `(and (and))` therefore yield [] — which is the point: those
    are the two shapes the failing backend emits for "I have no event model",
    and neither asserts anything.
    """
    return [p for p in PRED_RE.findall(sexp) if p not in CONNECTIVES]


def declared_predicates(text: str) -> set[str]:
    i = text.find("(:predicates")
    if i < 0:
        return set()
    depth = 0
    for k in range(i, len(text)):
        if text[k] == "(":
            depth += 1
        elif text[k] == ")":
            depth -= 1
            if depth == 0:
                block = text[i : k + 1]
                break
    else:
        block = text[i:]
    # A declaration is a top-level `(name ?a - t ...)` inside the block.
    return {
        m.group(1)
        for m in re.finditer(r"\(\s*([A-Za-z][A-Za-z0-9_\-]*)", block)
        if m.group(1) != "predicates"
    }


def classify_actions(text: str) -> list[dict]:
    """One verdict per action.  GOOD requires all four criteria.

    The criteria are validity and non-vacuity, not style:
      1. the precondition asserts at least one literal;
      2. the effect asserts at least one literal;
      3. every ?var used in the body is bound by :parameters;
      4. every predicate used is declared in (:predicates ...).

    The bar is a ceiling on correctness, not a floor on brokenness: an action
    can pass all four and still be wrong (an inverted guard, a parameter that
    grounds to nothing).  Passing is necessary, not sufficient.
    """
    declared = declared_predicates(text)
    out = []
    for m in ACTION_RE.finditer(text):
        name, body = m.group(1), m.group(2)
        pm = PARAMS_RE.search(body)
        bound = set(VAR_RE.findall(pm.group(1))) if pm else set()
        pre = _section(body, "precondition")
        eff = _section(body, "effect")
        pre_lits, eff_lits = _literals(pre), _literals(eff)
        used_vars = set(VAR_RE.findall(pre)) | set(VAR_RE.findall(eff))
        used_preds = set(pre_lits) | set(eff_lits)
        defects = []
        if not pre_lits:
            defects.append("empty-precondition")
        if not eff_lits:
            defects.append("empty-effect")
        if used_vars - bound:
            defects.append("undeclared-variable")
        if declared and (used_preds - declared):
            defects.append("undeclared-predicate")
        out.append(
            {
                "action": name,
                "good": not defects,
                "defects": defects,
                "unbound_vars": sorted(used_vars - bound),
                "undeclared_preds": sorted(used_preds - declared) if declared else [],
            }
        )
    return out


def main(root: Path) -> int:
    sites = []
    for d in sorted(root.rglob("*")):
        if not d.is_dir() or d.name not in SITE_DIR_NAMES:
            continue
        if ".worktrees" in d.parts or ".git" in d.parts:
            continue
        rel = d.relative_to(root).as_posix()
        present = {}
        for form, globs in FORM_GLOBS.items():
            hits = []
            for g in globs:
                hits += [p.name for p in d.glob(g)]
            present[form] = sorted(set(hits))
        domain = d / "domain.pddl"
        pddl = None
        if domain.exists():
            text = domain.read_text(encoding="utf-8", errors="replace")
            verdicts = classify_actions(text)
            pddl = {
                "path": domain.relative_to(root).as_posix(),
                "sha256": sha256(domain),
                "backend": "B (gen_pddl_a0.py, stamped)"
                if BACKEND_B_STAMP in text
                else "A (theory_compiler.generators.gen_pddl, unstamped)",
                "actions": len(verdicts),
                "good": sum(1 for v in verdicts if v["good"]),
                "verdicts": verdicts,
            }
        sites.append(
            {
                "site": rel,
                "forms_present": {k: bool(v) for k, v in present.items()},
                "forms_present_count": sum(1 for v in present.values() if v),
                "files": present,
                "pddl": pddl,
            }
        )

    # --- handover packages: the shipped product, form inventory by manifest --
    packages = []
    hp = root / "theory-compiler" / "handover_packages"
    if hp.is_dir():
        for pkg in sorted(p for p in hp.iterdir() if p.is_dir()):
            mf = pkg / "MANIFEST.json"
            forms = {}
            if mf.exists():
                data = json.loads(mf.read_text(encoding="utf-8"))
                forms = {
                    k: v.get("status") if isinstance(v, dict) else v
                    for k, v in (data.get("forms") or {}).items()
                }
            packages.append(
                {
                    "package": pkg.relative_to(root).as_posix(),
                    "forms": forms,
                    "pddl_files_on_disk": [
                        p.relative_to(pkg).as_posix() for p in sorted(pkg.rglob("*.pddl"))
                    ],
                    "extension_census": _ext_census(pkg),
                }
            )

    result = {"sites": sites, "packages": packages}
    out = root / "papers/runs/20260730T160000Z-P23-fourth-form-unqualified/out"
    out.mkdir(parents=True, exist_ok=True)
    (out / "shipped_forms.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _print(result)
    return 0


def _ext_census(pkg: Path) -> dict:
    census: dict[str, int] = {}
    for p in pkg.rglob("*"):
        if p.is_file():
            census[p.suffix or "(none)"] = census.get(p.suffix or "(none)", 0) + 1
    return dict(sorted(census.items()))


def _print(result: dict) -> None:
    print("== compile sites: which of the four forms is present ==")
    print(f"{'site':66} {'Lean':>5} {'Py':>4} {'PDDL':>5} {'MD':>4} {'n/4':>4}")
    for s in result["sites"]:
        f = s["forms_present"]
        print(
            f"{s['site']:66} {'yes' if f['Lean'] else 'NO':>5} "
            f"{'yes' if f['Python'] else 'NO':>4} {'yes' if f['PDDL'] else 'NO':>5} "
            f"{'yes' if f['Markdown'] else 'NO':>4} {s['forms_present_count']:>4}"
        )
    print()
    print("== the PDDL that does exist: actions that say something ==")
    print(f"{'site':52} {'backend':10} {'actions':>8} {'good':>5}")
    for s in result["sites"]:
        p = s["pddl"]
        if p:
            print(f"{s['site']:52} {p['backend'][:9]:10} {p['actions']:>8} {p['good']:>5}")
    print()
    print("== shipped handover packages ==")
    for pkg in result["packages"]:
        print(f"{pkg['package']}")
        for k, v in pkg["forms"].items():
            print(f"    {k:22} {v}")
        print(f"    .pddl files on disk: {len(pkg['pddl_files_on_disk'])}")
        print(f"    extensions: {pkg['extension_census']}")


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()))
