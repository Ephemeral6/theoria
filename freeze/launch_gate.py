"""May the sealed campaign start spending?  One question, one exit code.

## Why this file exists

`freeze/verify.sh` deliberately exits 0 while ⛔ items are outstanding: it
checks that the *draft* is complete, and "drafted" and "ready" are different
states (its own header says so).  That is the right disposition for a draft
checker and the wrong one for money.  Nothing else was reading `freeze/` at
all -- `theoria-arm/armtools/preflight.py` opens a scorecard and a RESET, and
never looks at the rules.

So `STATS_RULES.md` §9 could say **开跑前置条件 · 未实现不得开跑** about three
rows and no code anywhere would stop a launch.  The S4 N-4 adversarial round
wrote that down as the one hole it had not plugged:

> 判据 (c) 仍然没有实现，而「开跑前置条件」目前只有散文在拦。

This is the executable half.  It fails **closed**: silence, a parse failure, a
missing registry entry and an unimplemented blocker all read the same as "not
cleared", because the failure mode that matters is a gate that says yes when
nobody taught it to say no.

## What clears a blocker

Not a sentence.  Each row declared 开跑前置条件 in §9 needs an entry in
`freeze/launch_blockers.json` carrying **one command template** and **two
targets**:

    cmd                ["python", "-m", "…", "--theory", "{target}"]
    positive_target    an artefact the check must accept   -> exit 0
    negative_target    an artefact the check must reject   -> exit != 0
    negative_exit      optional: the exact code that rejection must carry

The two runs use the same template, differing only in the substituted path.
That is the point.  "Implemented" and "implemented but stubbed" are
indistinguishable from a check that only ever runs on things it should pass;
pointing `cmd` at `true` would clear the blocker in one line.  Requiring the
same program to *reject* a known-bad artefact costs an attacker a
purpose-built liar rather than a one-word edit.

**The honest limit, stated once**: a purpose-built liar still gets through.  A
program that inspects its argument and answers by filename passes both runs.
This gate closes "declared but never implemented" and "implemented but not
discriminating".  It does not close "implemented dishonestly", and no gate in
this file could -- that one is caught by reading the check's source, which is
why the registry records where the source lives.

For §9.2 the negative target is not invented here: `STATS_RULES.md` names
`cold-start-a3/theory/generated_l1_vacuous/` as the artefact criterion (c)
must catch, and D-A3-007 records that vacuous certificate happening on its
own, unprompted -- three obligations green, `#print axioms` empty, nothing
proved.

## Exit codes

    0   every declared launch blocker cleared -- spending may begin
    1   at least one blocker outstanding -- do not launch
    2   the gate could not evaluate itself -- do not launch

1 and 2 are both "no".  They are separate so a caller can tell "the rules say
no" from "this script is broken", and never so a caller can treat 2 as a pass.

Usage:
    python freeze/launch_gate.py            # human-readable
    python freeze/launch_gate.py --json     # for a caller that gates on it
"""

import argparse
import json
import os
import re
import subprocess
import sys

# The rows this gate prints are quoted from STATS_RULES.md, which is Chinese
# prose full of ⟨…⟩ placeholders.  On a CJK-locale Windows console stdout
# defaults to GBK, which has no U+27E8, so printing a blocker's reason raised
# UnicodeEncodeError and the gate died with a traceback -- exit 1 from the
# interpreter, not the exit 2 this gate promises when it cannot evaluate
# itself, and no verdict at all.  A gate that crashes on the text of the thing
# it is gating is worse than one that says no.  Same fix as
# build_budget_table.py:958.  (Found 2026-07-29 registering §9.15/§9.16, whose
# clears_when carries a ⟨c_min⟩.)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # already-wrapped or non-reconfigurable
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RULES = os.path.join(HERE, "STATS_RULES.md")
REGISTRY = os.path.join(HERE, "launch_blockers.json")

#: Marks that turn a 开跑前置条件 back into something weaker.  Same list as
#: verify.sh stage 10, for the same reason: a row can be neutralised without
#: deleting the words, and a substring test for the words alone is fooled by
#: `~~开跑前置条件~~ → needs_impl（降级）` (bypass B7 in the N-4 round).
RETRACTION_MARKS = ("~~", "降级", "暂缓", "豁免")

#: The blockers on record when this gate was written (S4, 2026-07-29).  This is
#: a third copy of a fact that already lives in §9 and in the registry, and a
#: third copy is the point: dropping a blocker requires editing all three, and
#: this one sits in reviewed source next to the reason it exists.  Adding a
#: blocker does NOT require touching this list -- §9 is the authority for what
#: is declared; the floor only stops declarations from quietly disappearing.
FLOOR = {
    "9.2": "U3 criterion (c): the non-triviality check",
    "9.11": "envelope re-run (INC-BA-003 + abort-threshold scaling)",
    "9.14": "U3 attainment rate has no implementation at all",
}

TIMEOUT = 300


class GateError(Exception):
    """The gate cannot evaluate itself.  Exit 2, never 0."""


# ------------------------------------------------------------------ §9 table

def parse_blockers(text):
    """Row ids in §9 whose type column declares them launch blockers.

    Returns {row_id: subject}.  Scoped to the §9 section: a table elsewhere in
    the file must not be able to donate rows, and -- more to the point -- a row
    inserted above §9 must not be able to redirect the parse.
    """
    start = re.search(r"^##\s*9\.\s", text, re.M)
    if not start:
        raise GateError(
            "STATS_RULES.md has no '## 9.' section -- the gate cannot tell "
            "what the launch blockers are, so it cannot clear any")
    rest = text[start.end():]
    end = re.search(r"^##\s", rest, re.M)
    section = rest[:end.start()] if end else rest

    found = {}
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        row = cells[0].replace("*", "").replace("`", "").strip()
        if not re.fullmatch(r"9\.\d+", row):
            continue
        kind = cells[2]
        if "开跑前置条件" not in kind:
            continue
        marks = [m for m in RETRACTION_MARKS if m in kind]
        if marks:
            # Declared and retracted in the same cell.  Not a blocker, and not
            # silently dropped either -- surfaced as its own finding below.
            found[row] = {"subject": cells[1], "retracted_by": marks}
        else:
            found[row] = {"subject": cells[1], "retracted_by": []}
    return found


# ------------------------------------------------------------------ registry

def load_registry(path=None):
    path = path or REGISTRY
    if not os.path.exists(path):
        raise GateError("freeze/launch_blockers.json is missing -- with no "
                        "registry no blocker can be shown cleared")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except ValueError as exc:
        raise GateError("freeze/launch_blockers.json is not valid JSON: %s" % exc)
    entries = data.get("blockers")
    if not isinstance(entries, dict):
        raise GateError("freeze/launch_blockers.json has no 'blockers' object")
    return entries


def _run(cmd, cwd):
    try:
        proc = subprocess.run(cmd, cwd=cwd, timeout=TIMEOUT,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except FileNotFoundError:
        return None, "command not found: %s" % cmd[0]
    except subprocess.TimeoutExpired:
        return None, "timed out after %ss" % TIMEOUT
    except OSError as exc:
        return None, "could not run: %s" % exc
    return proc.returncode, (proc.stdout or b"").decode("utf-8", "replace")[-2000:]


def evaluate(row, entry, root=None):
    """Clear this blocker, or say why not.  Anything unexpected is 'not'."""
    root = root or ROOT
    state = entry.get("state")
    if state != "implemented":
        return False, "state=%s -- %s" % (
            state or "absent", entry.get("why") or "no implementation recorded")

    cmd = entry.get("cmd")
    if not isinstance(cmd, list) or not cmd:
        return False, "state=implemented but no cmd template"
    if not any("{target}" in str(part) for part in cmd):
        return False, ("cmd has no {target} placeholder -- then the positive "
                       "and negative runs are the same run, and the negative "
                       "control proves nothing")

    cwd = os.path.join(root, entry.get("cwd", "."))
    if not os.path.isdir(cwd):
        return False, "cwd does not exist: %s" % entry.get("cwd")

    targets = {}
    for key in ("positive_target", "negative_target"):
        rel = entry.get(key)
        if not rel:
            return False, "no %s declared" % key
        path = os.path.join(root, rel)
        if not os.path.exists(path):
            # An absent negative target is the cheapest fake pass available:
            # the check errors out on a path that is not there, which looks
            # exactly like a correct rejection.
            return False, "%s does not exist on disk: %s" % (key, rel)
        targets[key] = rel

    pos_cmd = [str(p).replace("{target}", targets["positive_target"]) for p in cmd]
    code, out = _run(pos_cmd, cwd)
    if code is None:
        return False, "positive run: %s" % out
    if code != 0:
        return False, ("the check rejects its own positive target %s (exit %s) "
                       "-- either the check or the target is wrong\n%s"
                       % (targets["positive_target"], code, out.strip()[:400]))

    neg_cmd = [str(p).replace("{target}", targets["negative_target"]) for p in cmd]
    code, out = _run(neg_cmd, cwd)
    if code is None:
        return False, "negative control: %s" % out
    if code == 0:
        return False, ("negative control did not fire: the check ACCEPTS %s, "
                       "which it exists to reject -- it is not discriminating"
                       % targets["negative_target"])

    # Optional, and the rows that carry it are the ones whose blocker is about
    # *which* rejection happened.  Without it "rejects" means only "did not
    # exit 0", and that is weaker than it reads: a negative target that makes
    # the check crash -- a file that exists but is not of the expected kind --
    # exits non-zero too, so a garbage path satisfies the contract exactly as
    # well as a purpose-built liar.  Declaring the code closes that, and buys
    # one more thing: §2.3.2 ruling 2 makes 不成立 (3) and 不可结论 (4)
    # DIFFERENT verdicts on purpose -- an arm that never answered has not been
    # refuted -- and a gate that collapses them cannot witness the distinction
    # its own row exists to pin.  (Added 2026-08-02, S45, on the S45 audit
    # finding that rows 9.15/9.16 differ precisely in this digit.)
    want = entry.get("negative_exit")
    if want is not None:
        if not isinstance(want, int) or isinstance(want, bool):
            return False, ("negative_exit must be an integer exit code, got %r "
                           "-- an unparseable expectation is not an expectation"
                           % (want,))
        if code != want:
            return False, ("negative control fired with exit %s, but this row "
                           "declares exit %s for %s -- 'did not exit 0' is not "
                           "the same as 'was rejected for the stated reason'"
                           "\n%s"
                           % (code, want, targets["negative_target"],
                              out.strip()[:400]))
        return True, ("accepts %s, rejects %s (exit %s, as declared)"
                      % (targets["positive_target"],
                         targets["negative_target"], code))

    return True, ("accepts %s, rejects %s (exit %s)"
                  % (targets["positive_target"], targets["negative_target"], code))


# ---------------------------------------------------------------------- main

def gate(rules=None, registry_path=None, root=None):
    """Returns (verdict, findings) where verdict is 'clear' or 'blocked'.

    The three paths are parameters only so `--selftest` can drive this
    against synthetic fixtures.  Nothing in normal operation passes them.
    """
    rules = rules or RULES
    root = root or ROOT
    if not os.path.exists(rules):
        raise GateError("freeze/STATS_RULES.md is missing")
    with open(rules, encoding="utf-8") as fh:
        declared = parse_blockers(fh.read())

    if not declared:
        raise GateError(
            "§9 declares no launch blockers at all.  Three were on record when "
            "this gate was written; an empty result means the table changed "
            "shape or the parser broke, and 'no blockers found' must never be "
            "the way this gate goes green")

    registry = load_registry(registry_path)
    findings = []

    for row, why in sorted(FLOOR.items()):
        if row not in declared:
            findings.append({"row": row, "cleared": False, "subject": why,
                             "detail": "§9 no longer declares this a launch "
                                       "blocker, and it was one when the gate "
                                       "was written -- a downgrade, not a pass"})

    for row in sorted(declared, key=lambda r: [int(p) for p in r.split(".")]):
        info = declared[row]
        if info["retracted_by"]:
            findings.append({
                "row": row, "cleared": False, "subject": info["subject"],
                "detail": "§9 carries 开跑前置条件 alongside marks of its own "
                          "retraction (%s)" % ", ".join(info["retracted_by"])})
            continue
        entry = registry.get(row)
        if entry is None:
            findings.append({
                "row": row, "cleared": False, "subject": info["subject"],
                "detail": "declared a launch blocker in §9 with no entry in "
                          "launch_blockers.json -- a new blocker defaults to "
                          "outstanding, never to cleared"})
            continue
        cleared, detail = evaluate(row, entry, root)
        findings.append({"row": row, "cleared": cleared,
                         "subject": info["subject"], "detail": detail})

    for row in sorted(registry):
        if row not in declared:
            findings.append({
                "row": row, "cleared": False,
                "subject": registry[row].get("subject", ""),
                "detail": "the registry carries this blocker but §9 no longer "
                          "declares it -- the rules and the registry disagree, "
                          "and disagreement is not clearance"})

    verdict = "clear" if all(f["cleared"] for f in findings) else "blocked"
    return verdict, findings


# ------------------------------------------------------------------ selftest
#
# This gate ships red, and it should: all three blockers are genuinely
# outstanding.  But a gate that has only ever been observed saying "no" is
# untested in the direction that will matter later -- the day someone
# legitimately clears 9.2, "it still says no" and "it can only say no" look
# identical.  So the clearing path is exercised here against synthetic
# fixtures, and so is every way of faking it that occurred to me.

_FAKE_CHECK = '''import sys
# A genuinely discriminating check: the target must say NONTRIVIAL.
sys.exit(0 if "NONTRIVIAL" in open(sys.argv[1], encoding="utf-8").read() else 1)
'''

_ALWAYS_OK = "import sys; sys.exit(0)\n"

#: A check with a *graded* rejection, like `exam.tools.endpoint_verdict`:
#: 0 accepted, 3 refuted, 4 declined-to-judge, and anything it cannot parse
#: blows up into exit 1.  The last line is the point -- it is how a negative
#: target that is merely the WRONG KIND OF FILE still exits non-zero.
_CODED_CHECK = '''import sys
t = open(sys.argv[1], encoding="utf-8").read()
if "GOOD" in t: sys.exit(0)
if "REFUTED" in t: sys.exit(3)
if "INCONCLUSIVE" in t: sys.exit(4)
raise SystemExit("cannot read this at all")
'''

_ROWS = {
    "9.2": "U3 criterion (c)",
    "9.11": "envelope re-run",
    "9.14": "U3 has no implementation",
}


def _fake_rules(rows):
    """A minimal §9 section.  `rows` maps id -> the type-column cell."""
    body = ["## 9. needs_human / needs_impl", "",
            "| # | 事项 | 类型 | 建议 |", "|---|---|---|---|"]
    for row, kind in rows.items():
        body.append("| %s | %s | %s | -- |" % (row, _ROWS.get(row, row), kind))
    body += ["", "## 10. next section"]
    return "\n".join(body)


def selftest():
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="launch_gate_selftest_")
    results = []

    def case(name, expect, rules_text, blockers, want_error=False):
        rp = os.path.join(tmp, "rules.md")
        gp = os.path.join(tmp, "reg.json")
        with open(rp, "w", encoding="utf-8") as fh:
            fh.write(rules_text)
        with open(gp, "w", encoding="utf-8") as fh:
            json.dump({"blockers": blockers}, fh, ensure_ascii=False)
        try:
            verdict, _ = gate(rules=rp, registry_path=gp, root=tmp)
        except GateError:
            verdict = "error"
        ok = (verdict == expect)
        results.append((ok, name, expect, verdict))
        return ok

    try:
        # fixtures the synthetic checks run against
        with open(os.path.join(tmp, "check.py"), "w", encoding="utf-8") as fh:
            fh.write(_FAKE_CHECK)
        with open(os.path.join(tmp, "always_ok.py"), "w", encoding="utf-8") as fh:
            fh.write(_ALWAYS_OK)
        with open(os.path.join(tmp, "good.txt"), "w", encoding="utf-8") as fh:
            fh.write("NONTRIVIAL theorem\n")
        with open(os.path.join(tmp, "vacuous.txt"), "w", encoding="utf-8") as fh:
            fh.write("proves nothing\n")
        with open(os.path.join(tmp, "coded.py"), "w", encoding="utf-8") as fh:
            fh.write(_CODED_CHECK)
        for name, body in (("good2.txt", "GOOD\n"),
                           ("refuted.txt", "REFUTED\n"),
                           ("inconclusive.txt", "INCONCLUSIVE\n"),
                           ("wrong_kind.txt", "a file of some other sort\n")):
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                fh.write(body)

        def entry(**over):
            base = {"state": "implemented",
                    "cmd": [sys.executable, "check.py", "{target}"],
                    "positive_target": "good.txt",
                    "negative_target": "vacuous.txt"}
            base.update(over)
            return base

        all_declared = {r: "**开跑前置条件**" for r in _ROWS}
        all_ok = {r: entry() for r in _ROWS}

        # 1. the clearing path is reachable at all
        case("green is reachable: all three implemented and discriminating",
             "clear", _fake_rules(all_declared), all_ok)

        # 2. a check that accepts everything is not implemented
        bad = dict(all_ok)
        bad["9.2"] = entry(cmd=[sys.executable, "always_ok.py", "{target}"])
        case("stub check (accepts the vacuous artefact too)",
             "blocked", _fake_rules(all_declared), bad)

        # 3. a negative target that is not on disk -- the cheapest fake pass,
        #    since the check errors out and that reads like a rejection
        bad = dict(all_ok)
        bad["9.2"] = entry(negative_target="not_there.txt")
        case("negative target absent from disk",
             "blocked", _fake_rules(all_declared), bad)

        # 4. no {target}: both runs are the same run
        bad = dict(all_ok)
        bad["9.2"] = entry(cmd=[sys.executable, "check.py", "good.txt"])
        case("cmd with no {target} placeholder",
             "blocked", _fake_rules(all_declared), bad)

        # 5. state asserted without a command behind it
        bad = dict(all_ok)
        bad["9.2"] = {"state": "implemented"}
        case("state=implemented with no cmd",
             "blocked", _fake_rules(all_declared), bad)

        # 6. a blocker §9 declares that the registry has never heard of
        bad = {k: v for k, v in all_ok.items() if k != "9.2"}
        case("declared in §9, absent from the registry",
             "blocked", _fake_rules(all_declared), bad)

        # 7. a new blocker appears -- defaults to outstanding
        more = dict(all_declared)
        more["9.15"] = "**开跑前置条件**"
        case("a newly declared blocker defaults to outstanding",
             "blocked", _fake_rules(more), all_ok)

        # 8. downgrade in place: the words kept, the meaning retracted (B7)
        down = dict(all_declared)
        down["9.2"] = "~~开跑前置条件~~ → needs_impl（降级）"
        case("downgraded in place (strikethrough + 降级)",
             "blocked", _fake_rules(down), all_ok)

        # 9. the row deleted outright -- caught by the floor, not by §9
        gone = {k: v for k, v in all_declared.items() if k != "9.11"}
        case("a floor row deleted from §9 entirely",
             "blocked", _fake_rules(gone), all_ok)

        # 10. registry and rules disagree in the other direction
        gone = {k: v for k, v in all_declared.items() if k != "9.11"}
        case("registry carries a blocker §9 no longer declares",
             "blocked", _fake_rules(gone), all_ok)

        # 11. the table emptied: 'found no blockers' must never mean 'clear'
        case("§9 emptied of blockers", "error",
             _fake_rules({}), all_ok)

        # 12. §9 gone: the gate cannot evaluate itself, and says so
        case("§9 section missing entirely", "error",
             "## 8. something else\n\nno section nine here\n", all_ok)

        # --- negative_exit: rows whose blocker is about WHICH rejection ------

        def coded(**over):
            base = {"state": "implemented",
                    "cmd": [sys.executable, "coded.py", "{target}"],
                    "positive_target": "good2.txt",
                    "negative_target": "refuted.txt",
                    "negative_exit": 3}
            base.update(over)
            return base

        # 13. the declared code is the one the check actually returns
        ok13 = dict(all_ok)
        ok13["9.2"] = coded()
        case("negative_exit declared and matched",
             "clear", _fake_rules(all_declared), ok13)

        # 14. THE HOLE THIS FIELD CLOSES.  `wrong_kind.txt` exists and makes
        #     the check die (exit 1).  Without negative_exit that reads as a
        #     correct rejection; with it, it does not.
        bad = dict(all_ok)
        bad["9.2"] = coded(negative_target="wrong_kind.txt")
        case("negative target merely CRASHES the check (exit 1, not 3)",
             "blocked", _fake_rules(all_declared), bad)

        # 15. the two controls swapped: rejected, but for the other reason.
        #     This is 9.15-vs-9.16 -- 不成立 (3) and 不可结论 (4) are
        #     different verdicts and the row names which one it means.
        bad = dict(all_ok)
        bad["9.2"] = coded(negative_target="inconclusive.txt")
        case("negative control fires with the OTHER verdict (4, declared 3)",
             "blocked", _fake_rules(all_declared), bad)

        # 16. an expectation that is not an exit code is not an expectation
        bad = dict(all_ok)
        bad["9.2"] = coded(negative_exit="3")
        case("negative_exit is a string, not an int",
             "blocked", _fake_rules(all_declared), bad)

        # 17. `True` is an int in Python and would compare equal to 1; a
        #     JSON `true` here must not be read as "exit 1 is fine".
        bad = dict(all_ok)
        bad["9.2"] = coded(negative_exit=True)
        case("negative_exit is a bool (JSON true)",
             "blocked", _fake_rules(all_declared), bad)

        # 18. the field stays optional -- rows without it behave as before
        ok18 = dict(all_ok)
        ok18["9.2"] = coded(negative_exit=None)
        del ok18["9.2"]["negative_exit"]
        case("negative_exit absent: the old contract still clears",
             "clear", _fake_rules(all_declared), ok18)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("=" * 62)
    print(" launch_gate.py --selftest")
    print("=" * 62)
    for ok, name, expect, got in results:
        print("  %s %-52s (want %s, got %s)"
              % ("PASS" if ok else "FAIL", name, expect, got))
    failed = [r for r in results if not r[0]]
    print("=" * 62)
    print(" %d/%d" % (len(results) - len(failed), len(results)))
    return 1 if failed else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true",
                    help="machine-readable, for a caller that gates on it")
    ap.add_argument("--selftest", action="store_true",
                    help="prove both directions against synthetic fixtures")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    try:
        verdict, findings = gate()
    except GateError as exc:
        if args.json:
            print(json.dumps({"verdict": "error", "error": str(exc),
                              "may_launch": False}, ensure_ascii=False, indent=1))
        else:
            print("GATE ERROR: %s" % exc)
            print("\nExit 2 -- the gate could not evaluate itself. "
                  "This is not a pass.")
        return 2

    if args.json:
        print(json.dumps({"verdict": verdict,
                          "may_launch": verdict == "clear",
                          "blockers": findings},
                         ensure_ascii=False, indent=1))
    else:
        print("=" * 62)
        print(" freeze/launch_gate.py -- may the sealed campaign spend?")
        print("=" * 62)
        for f in findings:
            mark = "CLEAR " if f["cleared"] else "BLOCK "
            print("  %s §%-5s %s" % (mark, f["row"], f["subject"]))
            for line in str(f["detail"]).splitlines():
                print("           %s" % line)
        print("=" * 62)
        if verdict == "clear":
            print(" CLEAR -- every declared launch blocker is implemented and")
            print(" its check demonstrably rejects a known-bad artefact.")
        else:
            n = sum(1 for f in findings if not f["cleared"])
            print(" BLOCKED -- %d launch blocker(s) outstanding." % n)
            print(" The sealed campaign must not spend. See STATS_RULES.md §9.")
        print("=" * 62)

    return 0 if verdict == "clear" else 1


if __name__ == "__main__":
    sys.exit(main())
