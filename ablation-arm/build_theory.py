"""Step 2 — build this arm's `theory/` by cutting, never by copying out.

```bash
python ablation-arm/build_theory.py           # write theory/
python ablation-arm/build_theory.py --check   # rebuild and diff; writes nothing
```

`DESIGN.md` §12 lists `theory/` as 本臂自己的 DSL 副本(laws 段降级).  Five files:
four manuals and one playbook, each produced from an upstream source by
`ablcore.downgrade` or `ablcore.playbook` and by nothing else.

**Why a builder rather than five edited files.** A hand-edited copy is a claim
that the only difference is the laws section, and a claim is exactly what this
arm may not rely on: `Theoria.md:280`'s attributability requirement says a
difference in the arms' behaviour is pinnable on the cut only if nothing else
moved.  `downgrade_text` already asserts that byte-for-byte on every run, so
routing every file through it converts the claim into a check.  It also makes
the copies reproducible — `--check` rebuilds and diffs, so a copy that was
touched by hand is a red build rather than a silent divergence.

**The upstream sources are read, hashed, and never written.**  Their sha256 goes
into the report, so a later reader can prove which revision of which manual this
arm's copy was cut from.  `cold-start-a0/` and `cold-start-a2/` belong to another
track; `tests/test_readonly.py` is what makes "never written" checkable rather
than promised.

**This is not a theorize step and may not become one.**  Nothing here decides
anything about the world.  Two of these manuals are *wrong about their world* on
purpose — `a2_holed` is missing the teleport rule, which is the whole of exhibit
E2 — and repairing one here would delete the experiment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from ablcore import downgrade, playbook                            # noqa: E402

THEORY_DIR = os.path.join(HERE, "theory")
REPORT_PATH = os.path.join(THEORY_DIR, "DOWNGRADE_REPORT.json")

#: (arm-side name, upstream source, kind, what it is for).
#:
#: The two "wrong" manuals are here on purpose and are labelled as such, because
#: the one mistake that would quietly destroy this arm is a later session
#: deciding one of them is a bug and fixing it.
SOURCES: Tuple[Tuple[str, str, str, str], ...] = (
    ("a0_base.dsl", "cold-start-a0/theory/theory.dsl", "manual",
     "the solvable A0 world. P-1/P-2 read replay and held-out accuracy off it, "
     "P-5 reads the verdict."),
    ("a0_no_button.dsl", "cold-start-a0/theory/theory_no_button.dsl", "manual",
     "A0 with no Button, so the Door never opens. Constructively unsolvable and "
     "the manual says so truthfully -- exhibit E1, a TRUE impossibility, where "
     "the full arm owes a certificate and this arm settles on bare search."),
    ("a2_base.dsl", "cold-start-a2/theory/theory.dsl", "manual",
     "the A2 world, teleport rule present and correct."),
    ("a2_holed.dsl", "cold-start-a2/theory/theory_holed.dsl", "manual",
     "**deliberately wrong**: the teleport rule is missing, so this manual "
     "derives `unsolvable` for a world that is solvable. Exhibit E2, the false "
     "theorem the A4 ticket is about. DO NOT REPAIR -- repairing it deletes the "
     "experiment."),
    ("a0_playbook.dsl", "cold-start-a0/theory/playbook.dsl", "playbook",
     "the A0 playbook. Its `prune` entry is the demotion that costs soundness "
     "rather than only standing -- see ablcore/playbook.py."),
)

#: What must not survive anywhere under `theory/`, and why each one matters.
#: `verify.sh` re-asserts these; they are here too so a bad build never lands.
FORBIDDEN: Tuple[Tuple[str, str], ...] = (
    ("[status: proven]",
     "an invariant may still be observed, never guaranteed (C-5)"),
    ("[proof: lean]",
     "the playbook's theorem tier is gone (C-5)"),
    ("[admissible: lean]",
     "with no admissibility proof this arm's plans are plans, never optimal "
     "plans (ablcore/playbook.py)"),
)


def sha256_file(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _forbidden_hits(text: str) -> List[str]:
    return [token for token, _why in FORBIDDEN if token in text]


def _theorem_lines(text: str) -> List[str]:
    return [line.strip() for line in text.splitlines()
            if line.strip().startswith("theorem ")]


def verify_ast(names: Optional[List[str]] = None) -> Dict[str, Any]:
    """Read the cut manuals back through the real parser and check the cut there.

    A grep says the text no longer contains `[status: proven]`.  That is worth
    much less than it looks: the file the arm actually runs on is the **AST**,
    and a cut that satisfies a grep while leaving a theorem the parser can still
    see would be a cut in name only.  So the check that matters is the one the
    compiler itself performs — parse each manual and assert that the laws
    section has **no theorems at all** and that every surviving invariant reads
    `empirical`.

    It doubles as the earliest possible check on something step 3 depends on
    absolutely: `compile_abl.compile_ablated` calls `parse_theory` and then
    `parse_semantics`, *which raises if the manual does not declare semantics*.
    A manual that survives the cut but cannot be parsed would not fail here, it
    would fail three steps later inside the driver, where the cause is much
    harder to see.  (That failure is not hypothetical — `a0-spike`'s v0.1 manual
    is refused by the v0.2 grammar for exactly this reason.)
    """
    import _bootstrap                                              # noqa: F401
    from compile.dialect import parse_semantics                    # noqa: E402
    from theory_compiler.parser.theory_parser import parse_theory  # noqa: E402

    wanted = names or [n for n, _s, kind, _p in SOURCES if kind == "manual"]
    out: Dict[str, Any] = {}
    failures: List[str] = []
    for name in wanted:
        path = os.path.join(THEORY_DIR, name)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        ast = parse_theory(text)
        semantics = parse_semantics(text)
        laws = ast.laws
        invariants = list(getattr(laws, "invariants", ()) or ())
        theorems = list(getattr(laws, "theorems", ()) or ())
        statuses = sorted({str(getattr(i, "status", None)) for i in invariants})
        out[name] = {"invariants": len(invariants), "theorems": len(theorems),
                     "invariant_statuses": statuses,
                     "semantics": repr(semantics)}
        if theorems:
            failures.append("%s: the parser still sees %d theorem(s) after the "
                            "cut" % (name, len(theorems)))
        bad = [s for s in statuses if s != "empirical"]
        if bad:
            failures.append("%s: invariant status %s survived the cut; every "
                            "one must read `empirical`" % (name, bad))
    return {"per_manual": out, "failures": failures, "clean": not failures}


def build(check: bool = False) -> Dict[str, Any]:
    """Cut every source into `theory/`.  With `check`, compare instead of write."""
    os.makedirs(THEORY_DIR, exist_ok=True)
    entries: List[Dict[str, Any]] = []
    differences: List[str] = []

    for name, rel_source, kind, purpose in SOURCES:
        source = os.path.join(REPO, rel_source)
        if not os.path.exists(source):
            raise FileNotFoundError(
                "%s is missing. This arm cuts its manuals from upstream and "
                "does not carry its own copy of the source; a missing source "
                "is a broken checkout, not something to work around." % source)
        destination = os.path.join(THEORY_DIR, name)

        with open(source, encoding="utf-8") as handle:
            before = handle.read()
        if kind == "manual":
            after, report = downgrade.downgrade_text(before)
        elif kind == "playbook":
            after, report = playbook.demote_text(before)
        else:                                        # pragma: no cover - typo guard
            raise ValueError("unknown source kind %r for %s" % (kind, name))

        # Never land a build that still carries a proof marker: the cut is the
        # product, so a leftover marker is a failed cut and not a warning.
        hits = _forbidden_hits(after)
        if hits:
            raise AssertionError(
                "%s still carries %s after the cut. The whole point of this "
                "arm is that those markers are gone." % (name, hits))
        survivors = _theorem_lines(after)
        if survivors:
            raise AssertionError(
                "%s still declares %d theorem(s) after the cut: %s. A theorem "
                "is a standing proof obligation and this arm has no layer that "
                "could discharge one." % (name, len(survivors), survivors[:3]))

        entry: Dict[str, Any] = {
            "name": name,
            "kind": kind,
            "purpose": purpose,
            "source": rel_source,
            "source_sha256": sha256_file(source),
            "result_sha256": hashlib.sha256(after.encode("utf-8")).hexdigest(),
            "bytes": len(after.encode("utf-8")),
            "report": report,
        }
        entries.append(entry)

        if check:
            if not os.path.exists(destination):
                differences.append("%s: missing; run build_theory.py" % name)
            else:
                with open(destination, encoding="utf-8") as handle:
                    on_disk = handle.read()
                if on_disk != after:
                    differences.append(
                        "%s: on disk differs from a fresh cut of %s. Generated "
                        "files are not hand-edited -- change the source or the "
                        "transform." % (name, rel_source))
        else:
            with open(destination, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(after)

    # The AST check runs against what is on disk, so it has to come after the
    # write -- and in `--check` mode it reads the existing files, which is what
    # it should be checking anyway.
    ast_report = verify_ast()

    summary = _summarise(entries)
    payload = {
        "ast_check": ast_report,
        "what": "ablation-arm/theory/ -- upstream manuals with the laws section "
                "cut, produced by ablcore.downgrade and ablcore.playbook",
        "builder": "ablation-arm/build_theory.py",
        "forbidden_after_the_cut": {token: why for token, why in FORBIDDEN},
        "files": entries,
        "summary": summary,
    }

    differences.extend(ast_report["failures"])

    if check:
        payload["differences"] = differences
        if not os.path.exists(REPORT_PATH):
            differences.append("DOWNGRADE_REPORT.json: missing")
        payload["clean"] = not differences
    elif ast_report["failures"]:
        raise AssertionError(
            "the cut satisfies a grep and not the parser:\n  %s"
            % "\n  ".join(ast_report["failures"]))
    else:
        with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True,
                      ensure_ascii=False)
            handle.write("\n")
    return payload


def _summarise(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The counts `verify.sh` asserts, counted here rather than eyeballed.

    `DESIGN.md` §12: *verify.sh 的断言就是 §8 的七条预注册 + §6 的四道影子逐条
    数出来*.  Two of those shadows are countable right here — every deleted
    theorem is one directed-probe target that no longer exists (shadow 1) and one
    entry that dependency-driven re-proof can no longer invalidate (shadow 2) —
    so the count is produced at cut time and stored, instead of being recomputed
    later by something that might count differently.
    """
    demoted: List[str] = []
    deleted: List[Dict[str, Any]] = []
    playbook_entries: List[Dict[str, Any]] = []
    soundness_bearing: List[Dict[str, Any]] = []
    for entry in entries:
        report = entry["report"]
        for name in report.get("invariants_demoted", ()):
            demoted.append("%s::%s" % (entry["name"], name))
        for item in report.get("theorems_deleted", ()):
            deleted.append({"file": entry["name"], "theorem": item["name"]})
        for item in report.get("entries_demoted", ()) or ():
            record = dict(item, file=entry["name"])
            playbook_entries.append(record)
            if item.get("form") in playbook.SOUNDNESS_BEARING:
                soundness_bearing.append(record)
    return {
        "manuals_cut": sum(1 for e in entries if e["kind"] == "manual"),
        "playbooks_cut": sum(1 for e in entries if e["kind"] == "playbook"),
        "invariants_demoted": sorted(demoted),
        "n_invariants_demoted": len(demoted),
        "theorems_deleted": deleted,
        "n_theorems_deleted": len(deleted),
        "playbook_entries_demoted": playbook_entries,
        "n_playbook_entries_demoted": len(playbook_entries),
        "soundness_bearing_demotions": soundness_bearing,
        "n_soundness_bearing": len(soundness_bearing),
        "shadow_1_directed_probe_targets_removed": len(deleted),
        "shadow_2_entries_no_longer_re_provable": len(deleted),
        "note": ("A deleted theorem is simultaneously one directed-probe target "
                 "that no longer has a subject (DESIGN.md §6 shadow 1) and one "
                 "entry that dependency-driven re-proof can no longer "
                 "invalidate (shadow 2). They are the same count because they "
                 "are the same cut, which is the argument §6 makes: four "
                 "shadows, one blade."),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="rebuild in memory and diff against disk; write "
                             "nothing, exit 1 on any difference")
    args = parser.parse_args(argv)

    payload = build(check=args.check)
    summary = payload["summary"]
    print("theory/ -- %d manual(s) + %d playbook(s) cut from upstream"
          % (summary["manuals_cut"], summary["playbooks_cut"]))
    for entry in payload["files"]:
        report = entry["report"]
        detail = []
        if report.get("invariants_demoted"):
            detail.append("%d invariant(s) demoted" % len(report["invariants_demoted"]))
        if report.get("theorems_deleted"):
            detail.append("%d theorem(s) deleted" % len(report["theorems_deleted"]))
        if report.get("entries_demoted"):
            detail.append("%d playbook entr(ies) demoted"
                          % len(report["entries_demoted"]))
        print("  %-18s <- %-42s %s" % (entry["name"], entry["source"],
                                       ", ".join(detail) or "no laws section"))
    print("  totals: %d invariants demoted, %d theorems deleted, "
          "%d playbook entries demoted (%d soundness-bearing)"
          % (summary["n_invariants_demoted"], summary["n_theorems_deleted"],
             summary["n_playbook_entries_demoted"], summary["n_soundness_bearing"]))

    ast_report = payload["ast_check"]
    print("  parser's reading of the cut manuals:")
    for name, entry in sorted(ast_report["per_manual"].items()):
        print("    %-18s invariants=%d %s  theorems=%d"
              % (name, entry["invariants"], entry["invariant_statuses"],
                 entry["theorems"]))

    if args.check:
        if payload["differences"]:
            print("\nDIFFERENCES -- theory/ is not what the builder produces:")
            for line in payload["differences"]:
                print("  " + line)
            return 1
        print("\nclean: theory/ is byte-identical to a fresh cut")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
