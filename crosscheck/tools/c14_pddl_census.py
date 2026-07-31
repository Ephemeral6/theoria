"""C14 -- how much of the fourth form is actually there.

The framework's headline claim is that two books compile to four co-derived
forms (Lean / Python / PDDL / Markdown).  This script measures the fourth one
and nothing else.  It answers exactly one question, per action, mechanically:

    of the actions the DSL can currently express, how many compile to PDDL
    that means something?

"Means something" is not a matter of taste here.  An action is counted GOOD
only if all four hold:

  * its ``:precondition`` has at least one literal -- an empty one is an
    action that is always applicable, which is a different world;
  * its ``:effect`` has at least one literal -- ``gen_pddl`` writes the
    placeholder ``(and)`` when it does not know the event, so the action
    changes nothing and the planner is free to ignore it;
  * every ``?var`` it mentions appears in its own ``:parameters`` -- an
    undeclared variable is not weak PDDL, it is malformed PDDL;
  * every predicate it mentions is declared in the domain's ``:predicates``
    -- likewise malformed.

The population is every rule in every DSL theory in the repository, as
``theory_compiler.generators.gen_pddl`` itself sees it.  That is deliberate:
the claim under test is about *the compiler*, so the compiler's own front end
defines the corpus.  Files whose PDDL form the generator refuses outright are
counted too -- a refusal is zero actions delivered, not zero actions owed, and
folding refusals out of the denominator is how a 3-of-4 becomes a 4-of-4 on
paper.

Nothing here modifies ``theory-compiler/``; it is imported read-only.  No
network, no API, no sealed-pile contact.

    python -m crosscheck.tools.c14_pddl_census --out <dir>

Writes ``census.json`` (the machine record), ``census.md`` (the per-action
table) and ``fd_translate/`` (one log per domain fed to Fast Downward).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import traceback

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The generator lives in the other track.  Read-only import.
sys.path.insert(0, os.path.join(REPO, "theory-compiler", "src"))

# Directories that are not part of the corpus: nested checkouts, caches, and
# the generator's own PDDL *fixtures* (hand-written, not compiled from a book).
#
# `worktrees` is listed bare as well as `.worktrees`: the CLAUDE.md convention
# puts them at `.worktrees/`, but the agent harness also makes checkouts under
# `.claude/worktrees/`, and matching is by directory *name*.  Missing those made
# the denominator depend on which checkout you ran from -- 59 DSL files from
# inside a worktree, 237 from the main checkout, because four nested agent
# checkouts each carry a full copy of the corpus.  A census whose population
# changes with the caller's cwd is not a measurement.
SKIP_DIRS = {".worktrees", "worktrees", ".claude", ".git", "__pycache__",
             ".pytest_cache", ".toolchain", "node_modules", ".venv"}

# ------------------------------------------------------------------ PDDL reading
#
# A small reader, written here rather than reused from either track, so that the
# classification does not inherit the generator's assumptions or the engine
# adapter's.  It only needs to find blocks and atoms.

ACTION_RE = re.compile(r"\(:action\s+(\S+)")
ATOM_RE = re.compile(r"\(\s*([A-Za-z][A-Za-z0-9_\-]*)")
VAR_RE = re.compile(r"\?([A-Za-z][A-Za-z0-9_\-]*)")

# Atoms that are PDDL syntax, not world predicates.
LOGICAL = {"and", "or", "not", "when", "forall", "exists", "imply", "="}


def _balanced_block(text: str, head: str) -> str:
    """The body of ``(head ...)``, found by counting parens rather than by regex.

    This was a regex (``\\(:predicates(.*?)\\n\\s*\\)``) and it had a silent false
    negative: it required the block to close on a line of its own, so a domain
    that wrote ``… (holding ?x))`` inline matched nothing, ``declared_predicates``
    returned the empty set, and **every** action in that domain was reported
    ``undeclared-predicate``.  Demonstrated on
    ``engine-rig/engines/fd_adapter/domain.pddl`` -- a gripper domain Fast Downward
    solves -- which scored 0 of 3.

    ``gen_pddl`` always formats ``\\n  )``, so this never bit the C14 numbers; it
    would have bitten the first person to point the instrument at PDDL from
    anywhere else, which is exactly what the positive control now does.
    """
    at = text.find(head)
    if at < 0:
        return ""
    depth, i = 0, at
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return text[at + len(head):i]
        i += 1
    return text[at + len(head):]


def declared_predicates(domain: str) -> set:
    """Names inside the domain's ``(:predicates ...)`` block."""
    body = _balanced_block(domain, "(:predicates")
    if not body:
        return set()
    return {name for name in ATOM_RE.findall(body) if name not in LOGICAL}


def action_blocks(domain: str) -> list:
    """``[(name, text), ...]`` -- each ``(:action ...)`` block, in file order."""
    out = []
    hits = list(ACTION_RE.finditer(domain))
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(domain)
        out.append((m.group(1), domain[m.start():end]))
    return out


def _section(block: str, head: str, nexts) -> str:
    """The text of ``head`` in ``block``, up to whichever of ``nexts`` comes first."""
    at = block.find(head)
    if at < 0:
        return ""
    at += len(head)
    end = len(block)
    for nxt in nexts:
        j = block.find(nxt, at)
        if 0 <= j < end:
            end = j
    return block[at:end]


def literals(text: str) -> list:
    """World literals in a precondition/effect body, ``(and)`` not counted.

    ``gen_pddl`` emits the literal string ``(and)`` as its empty-effect
    placeholder, so a body consisting only of ``and``-atoms has no content.
    """
    return [name for name in ATOM_RE.findall(text) if name not in LOGICAL]


def classify(name: str, block: str, declared: set) -> dict:
    """One action's verdict.  ``defects`` empty <=> semantically non-empty PDDL."""
    params = _section(block, ":parameters", (":precondition", ":effect"))
    precond = _section(block, ":precondition", (":effect",))
    effect = _section(block, ":effect", ("\n  )",))

    declared_vars = set(VAR_RE.findall(params))
    used_vars = set(VAR_RE.findall(precond)) | set(VAR_RE.findall(effect))
    undeclared_vars = sorted(used_vars - declared_vars)

    prec_lits = literals(precond)
    eff_lits = literals(effect)
    used_preds = sorted(set(prec_lits) | set(eff_lits))
    undeclared_preds = sorted(p for p in used_preds if p not in declared)

    defects = []
    if not prec_lits:
        defects.append("empty-precondition")
    if not eff_lits:
        defects.append("empty-effect")
    if undeclared_vars:
        defects.append("undeclared-variable")
    if undeclared_preds:
        defects.append("undeclared-predicate")

    return {
        "action": name,
        "n_precondition_literals": len(prec_lits),
        "n_effect_literals": len(eff_lits),
        "undeclared_variables": undeclared_vars,
        "undeclared_predicates": undeclared_preds,
        "defects": defects,
        "semantically_non_empty": not defects,
    }


GOAL_RE = re.compile(r"\(:goal(.*?)\n\s*\)\s*\n\s*\)", re.S)


def goal_verdict(problem: str) -> dict:
    """The problem half's ``(:goal ...)``, and whether it says anything.

    Added after Fast Downward's translator did not merely reject four of these
    problems but *crashed* on them with ``TypeError: unhashable type: 'list'``.
    The cause is a goal of the literal form ``(= (and) 1)`` -- the generator
    compared the logical connective ``and`` with the number 1.  The action
    census could not see this: a domain can be flawless and still ship a
    problem with no goal, and a planning form whose goal is nonsense is not a
    planning form.  Verdict is textual and mechanical, no judgement:

      * ``placeholder`` -- the goal contains the bare ``(and)`` placeholder;
      * ``empty``       -- no goal block, or nothing in it;
      * ``stated``      -- something else, i.e. it at least names a predicate.
    """
    m = GOAL_RE.search(problem)
    if not m:
        return {"verdict": "empty", "text": "", "why": "no (:goal ...) block"}
    text = " ".join(m.group(1).split())
    if not text:
        return {"verdict": "empty", "text": "", "why": "empty (:goal) block"}
    if re.search(r"\(\s*and\s*\)", text):
        return {"verdict": "placeholder", "text": text,
                "why": "contains the bare (and) placeholder"}
    if not literals(text):
        return {"verdict": "empty", "text": text, "why": "no world predicate"}
    return {"verdict": "stated", "text": text, "why": ""}


# ------------------------------------------------------------------ the corpus

def dsl_files() -> list:
    """Every ``.dsl`` in the repo, repo-relative, sorted, nested checkouts out."""
    found = []
    for root, dirs, files in os.walk(REPO):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.endswith(".dsl"):
                rel = os.path.relpath(os.path.join(root, fn), REPO)
                found.append(rel.replace(os.sep, "/"))
    return sorted(found)


def compile_one(rel: str) -> dict:
    """Parse + compile one DSL file.  Never raises; records what happened."""
    from theory_compiler.generators.gen_pddl import generate_pddl
    from theory_compiler.parser.theory_parser import parse_theory

    rec = {"dsl": rel, "outcome": None, "n_rules": None, "rules": [],
           "actions": [], "error": None}
    text = open(os.path.join(REPO, rel), encoding="utf-8").read()

    try:
        ast = parse_theory(text)
    except Exception as exc:                                  # noqa: BLE001
        rec["outcome"] = "not-a-theory"
        rec["error"] = "%s: %s" % (type(exc).__name__, exc)
        return rec

    rules = list(getattr(ast.rules, "rules", []) or []) if ast.rules else []
    rec["n_rules"] = len(rules)
    rec["rules"] = [r.name for r in rules]
    if not rules:
        rec["outcome"] = "no-rules"          # a playbook, or a manual with none
        return rec

    try:
        domain, problem = generate_pddl(ast)
    except Exception as exc:                                  # noqa: BLE001
        rec["outcome"] = "refused"
        rec["error"] = "%s: %s" % (type(exc).__name__, exc)
        return rec

    rec["outcome"] = "compiled"
    rec["domain"] = domain
    rec["problem"] = problem
    rec["goal"] = goal_verdict(problem)
    declared = sorted(declared_predicates(domain))
    rec["declared_predicates"] = declared
    rec["actions"] = [classify(n, b, set(declared))
                      for n, b in action_blocks(domain)]
    return rec


# ------------------------------------------------- independent planner check (2)

def find_fd_translate() -> str:
    """The FD translator package dir, or ``""``.

    FD 24.06 has no ``translate.py``; the entry point is the ``translate``
    package (``python -m translate``).  ``.toolchain/`` is gitignored and
    machine-local by design, so absence here is a skip, not a failure.
    """
    env = os.environ.get("C14_FD_TRANSLATE_DIR")
    if env and os.path.isdir(env):
        return env

    # Roots to search.  A worktree is one of them, and `.toolchain/` is
    # gitignored, so it exists only in the main checkout -- looking in REPO
    # alone silently skips the whole independent check and reports "0 domains
    # accepted", which reads identically to "every domain rejected".  Ask git
    # where the main checkout is.
    roots = [REPO]
    try:
        common = subprocess.run(["git", "rev-parse", "--path-format=absolute",
                                 "--git-common-dir"], cwd=REPO, capture_output=True,
                                text=True, timeout=30)
        if common.returncode == 0:
            main_checkout = os.path.dirname(common.stdout.strip())
            if main_checkout and main_checkout not in roots:
                roots.append(main_checkout)
    except Exception:                                         # noqa: BLE001
        pass

    for root in roots:
        for base in ("cold-start-a0", "engine-rig", "."):
            cand = os.path.join(root, base, ".toolchain", "downward",
                                "builds", "release", "bin", "translate")
            if os.path.isfile(os.path.join(cand, "__main__.py")):
                return os.path.dirname(cand)
    return ""


def relativize_machine_path(path: str) -> str:
    """A recorded toolchain path must not name the build machine.

    An absolute path in a tracked artefact trips the release location gate
    (tools/check_locations.py); everything under the checkout (or a sibling
    worktree root) is rewritten to a <checkout>/ prefix.
    """
    if not path:
        return path
    norm = path.replace(os.sep, "/")
    roots = sorted({REPO.replace(os.sep, "/"),
                    os.path.dirname(REPO.replace(os.sep, "/"))},
                   key=len, reverse=True)
    for root in roots:
        if root and norm.startswith(root + "/"):
            return "<checkout>/" + norm[len(root) + 1:]
    return norm

def fd_translate(domain_path: str, problem_path: str, binroot: str) -> dict:
    """Feed one domain+problem to Fast Downward's translator.

    FD's translator has never heard of ``gen_pddl``; that is the whole point of
    running it.  Exit 0 means it built a SAS task, 31 is its parse-error code.
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = binroot
    proc = subprocess.run(
        [sys.executable, "-m", "translate", "--sas-file", os.devnull,
         domain_path, problem_path],
        cwd=binroot, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300)
    out = (proc.stdout or "") + (proc.stderr or "")
    return {"tool": "fast-downward-translate", "returncode": proc.returncode,
            "accepted": proc.returncode == 0, "output": out}


def pddl_lib_parse(domain_path: str, problem_path: str) -> dict:
    """Second blind reader: the ``pddl`` package's PDDL 3.1 parser, if installed."""
    proc = subprocess.run([sys.executable, "-m", "pddl", domain_path, problem_path],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=300)
    out = (proc.stdout or "") + (proc.stderr or "")
    return {"tool": "pddl-3.1-parser", "returncode": proc.returncode,
            "accepted": proc.returncode == 0, "output": out}


# ------------------------------------------------------------------ reporting

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="output directory")
    args = ap.parse_args(argv)

    outdir = os.path.abspath(args.out)
    os.makedirs(outdir, exist_ok=True)
    fddir = os.path.join(outdir, "fd_translate")
    os.makedirs(fddir, exist_ok=True)

    binroot = find_fd_translate()
    records = []
    for rel in dsl_files():
        try:
            rec = compile_one(rel)
        except Exception:                                     # noqa: BLE001
            rec = {"dsl": rel, "outcome": "census-crashed",
                   "error": traceback.format_exc(), "actions": [], "rules": []}
        records.append(rec)

    # Independent check: only files that produced a domain can be fed to a planner.
    # Slugs are short by index rather than by path: Windows MAX_PATH truncates
    # `cold-start-a3/artifacts/.../domain_l2_scratch_agent_gate.dsl` into a
    # FileNotFoundError, and a census that silently skips its longest paths is
    # measuring the wrong corpus.  `slug` is recorded per file in census.json.
    for i, rec in enumerate(records):
        if rec["outcome"] != "compiled":
            continue
        slug = "%03d-%s" % (i, os.path.basename(rec["dsl"])[:-4])
        rec["slug"] = slug
        dpath = os.path.join(fddir, slug + ".domain.pddl")
        ppath = os.path.join(fddir, slug + ".problem.pddl")
        with open(dpath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(rec.pop("domain"))
        with open(ppath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(rec.pop("problem"))
        checks = []
        if binroot:
            checks.append(fd_translate(dpath, ppath, binroot))
        else:
            checks.append({"tool": "fast-downward-translate", "returncode": None,
                           "accepted": None,
                           "output": "SKIPPED: no FD build found (.toolchain is "
                                     "gitignored and machine-local)"})
        try:
            checks.append(pddl_lib_parse(dpath, ppath))
        except Exception as exc:                              # noqa: BLE001
            checks.append({"tool": "pddl-3.1-parser", "returncode": None,
                           "accepted": None, "output": "SKIPPED: %s" % exc})
        rec["independent_checks"] = checks
        for chk in checks:
            with open(os.path.join(fddir, "%s.%s.log" % (slug, chk["tool"])),
                      "w", encoding="utf-8", newline="\n") as fh:
                fh.write("returncode: %s\n\n%s" % (chk["returncode"], chk["output"]))

    summary = tally(records)
    payload = {"prompt_id": "C14-four-forms-is-three-and-a-half",
               "fd_translate_dir": relativize_machine_path(binroot) or None,
               "summary": summary, "files": records}
    with open(os.path.join(outdir, "census.json"), "w", encoding="utf-8",
              newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")
    with open(os.path.join(outdir, "census.md"), "w", encoding="utf-8",
              newline="\n") as fh:
        fh.write(render(records, summary, binroot))

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def tally(records: list) -> dict:
    """The headline numbers.  Owed = every rule in a theory the DSL accepts."""
    owed = good = 0
    by_defect = {}
    refused_files, refused_rules = 0, 0
    for rec in records:
        if rec["outcome"] == "refused":
            refused_files += 1
            refused_rules += rec.get("n_rules") or 0
            owed += rec.get("n_rules") or 0
            by_defect["file-refused"] = (by_defect.get("file-refused", 0)
                                         + (rec.get("n_rules") or 0))
        elif rec["outcome"] == "compiled":
            owed += len(rec["actions"])
            for act in rec["actions"]:
                if act["semantically_non_empty"]:
                    good += 1
                for d in act["defects"]:
                    by_defect[d] = by_defect.get(d, 0) + 1
    theories = [r for r in records if r["outcome"] in ("compiled", "refused")]
    accepted = [r for r in records if r["outcome"] == "compiled"]
    fd_ok = [r for r in accepted
             if any(c["tool"] == "fast-downward-translate" and c["accepted"]
                    for c in r.get("independent_checks", []))]
    goals = {}
    for rec in accepted:
        v = rec.get("goal", {}).get("verdict", "unmeasured")
        goals[v] = goals.get(v, 0) + 1
    return {
        "problem_goals_by_verdict": dict(sorted(goals.items())),
        "actions_owed": owed,
        "actions_semantically_non_empty": good,
        "actions_defective": owed - good,
        "fraction_good": round(good / owed, 4) if owed else None,
        "by_defect": dict(sorted(by_defect.items())),
        "dsl_files_seen": len(records),
        "theories_with_rules": len(theories),
        "theories_compiled": len(accepted),
        "theories_refused": refused_files,
        "rules_lost_to_refusal": refused_rules,
        "domains_fast_downward_accepted": len(fd_ok),
    }


def render(records: list, summary: dict, binroot: str) -> str:
    L = []
    A = L.append
    A("# C14 -- the fourth form, measured\n")
    A("Generated by `crosscheck/tools/c14_pddl_census.py`. Do not hand-edit.\n")
    A("## The number\n")
    A("| | |")
    A("|---|---|")
    A("| actions the DSL expresses (owed a PDDL form) | **%d** |"
      % summary["actions_owed"])
    A("| of those, compiled to semantically non-empty, well-formed PDDL | **%d** |"
      % summary["actions_semantically_non_empty"])
    A("| defective (empty precondition, empty effect, undeclared name, or refused) | **%d** |"
      % summary["actions_defective"])
    A("| fraction good | **%s** |"
      % ("%.1f%%" % (100 * summary["fraction_good"])
         if summary["fraction_good"] is not None else "n/a"))
    A("")
    A("Defect counts (one action can carry several):\n")
    A("| defect | actions |")
    A("|---|---|")
    for k, v in summary["by_defect"].items():
        A("| `%s` | %d |" % (k, v))
    A("")
    rel_bin = relativize_machine_path(binroot)
    A("Independent planner: %s\n"
      % (("Fast Downward translator at `%s`" % rel_bin)
         if binroot else "**not run** -- no FD build on this machine"))
    A("| | |")
    A("|---|---|")
    A("| DSL theories with at least one rule | %d |" % summary["theories_with_rules"])
    A("| of those, the generator produced a domain for | %d |"
      % summary["theories_compiled"])
    A("| of those, Fast Downward's translator accepted | **%d** |"
      % summary["domains_fast_downward_accepted"])
    A("| theories the generator refused outright | %d (%d rules) |"
      % (summary["theories_refused"], summary["rules_lost_to_refusal"]))
    A("")
    A("## The problem half\n")
    A("A domain is only half of a planning task. Verdicts on the generated "
      "`(:goal ...)`:\n")
    A("| goal verdict | problems |")
    A("|---|---|")
    for k, v in summary["problem_goals_by_verdict"].items():
        A("| `%s` | %d |" % (k, v))
    A("")
    A("| DSL | goal verdict | generated goal |")
    A("|---|---|---|")
    for rec in records:
        if rec["outcome"] == "compiled":
            g = rec.get("goal", {})
            A("| `%s` | %s | `%s` |"
              % (rec["dsl"], g.get("verdict", "?"), g.get("text", "")[:90]))
    A("")
    A("## Per action\n")
    A("`prec`/`eff` are literal counts; an action is good only with both "
      "non-zero, no undeclared variable and no undeclared predicate.\n")
    A("| DSL | action | prec | eff | undeclared var | undeclared pred | verdict |")
    A("|---|---|---|---|---|---|---|")
    for rec in records:
        if rec["outcome"] == "refused":
            for name in rec["rules"]:
                A("| `%s` | %s | – | – | – | – | **REFUSED** (whole file) |"
                  % (rec["dsl"], name))
        elif rec["outcome"] == "compiled":
            for act in rec["actions"]:
                A("| `%s` | %s | %d | %d | %s | %s | %s |"
                  % (rec["dsl"], act["action"],
                     act["n_precondition_literals"], act["n_effect_literals"],
                     ", ".join(act["undeclared_variables"]) or "–",
                     ", ".join(act["undeclared_predicates"]) or "–",
                     "GOOD" if act["semantically_non_empty"]
                     else "**" + ", ".join(act["defects"]) + "**"))
    A("")
    A("## Files carrying no action\n")
    A("| DSL | outcome | why |")
    A("|---|---|---|")
    for rec in records:
        if rec["outcome"] in ("not-a-theory", "no-rules", "census-crashed"):
            why = (rec.get("error") or "").splitlines()[:1]
            A("| `%s` | %s | %s |" % (rec["dsl"], rec["outcome"],
                                      (why[0] if why else "–")[:160]))
    A("")
    A("## Refusals, in the generator's own words\n")
    for rec in records:
        if rec["outcome"] == "refused":
            A("* `%s` (%d rules) -- %s\n" % (rec["dsl"], rec["n_rules"] or 0,
                                             rec["error"]))
    A("## What Fast Downward said\n")
    for rec in records:
        for chk in rec.get("independent_checks", []):
            tail = [ln for ln in chk["output"].splitlines() if ln.strip()][-6:]
            A("* `%s` -- %s: returncode `%s`\n" % (rec["dsl"], chk["tool"],
                                                   chk["returncode"]))
            A("  ```")
            for ln in tail:
                A("  " + ln)
            A("  ```")
    A("")
    return "\n".join(L)


if __name__ == "__main__":
    raise SystemExit(main())
