"""Mutation harness for V22: break the new behaviour on purpose, one edit at a
time, and see whether anything goes red.

The point of the exercise is the *surface*, not the count. C11's lesson was 18
mutants that happened to line up one-to-one with 18 tests, which measures
nothing except that somebody wrote one test per mutant. So the mutants here are
generated from what the change could plausibly get wrong -- across every file
that carries the behaviour and both directions of every predicate -- and
several of them have no test named after them. Two are included that I expect
to **survive**: M14, a pure wording change to a note that nothing asserts on
character-by-character, and M33, which breaks `verify.py`'s stripper, a thing
`verify.py` rung 5 covers and pytest does not. A harness whose only possible
output is "all killed" cannot tell a strong suite from a lucky one, and a
survivor that is *predicted* is worth more than one that is explained
afterwards.

    python mutants.py --out <dir>

Writes `mutants.json` (the kill matrix) and `mutants.txt` (the log). Nothing is
left modified: each mutant is applied to a copy of the tree, not to the tree.
"""

import argparse
import json
import os
import shutil
import subprocess
import subprocess as sp
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROXY = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(PROXY)

V = "proxy/variants.py"
G = "proxy/tools/check_variant_degeneracy.py"
E = "proxy/env_proxy.py"

#: (id, file, old, new, why). `old` must appear exactly once in the file, or
#: the mutant is reported as `not-applied` rather than silently skipped -- a
#: mutation that did not land is not a mutation that was survived.
MUTANTS = [
    # -- the split itself --------------------------------------------------
    ("M01", V,
     "                if have is None:",
     "                if have is None or have < needed:",
     "revert the split entirely: absent and below collapse back together"),
    ("M02", V,
     '                              "degenerate": True,',
     '                              "degenerate": False,',
     "the bit is written, but always false"),
    ("M03", V,
     '                                    "degenerate": False,',
     '                                    "degenerate": True,',
     "the bit is written, but always true -- every shortfall looks degenerate"),
    ("M04", V,
     '                              "reason": REASON_ABSENT,',
     '                              "reason": REASON_BELOW,',
     "absent is labelled as a shortfall"),
    ("M05", V,
     '                                    "reason": REASON_BELOW,',
     '                                    "reason": REASON_ABSENT,',
     "a shortfall is labelled absent"),
    ("M06", V,
     '                              "degenerate": True,\n',
     "",
     "drop the bit from the record altogether"),
    ("M07", V,
     "                        self.degenerate_wins += 1",
     "                        self.degenerate_wins += 0",
     "the counter never moves, so nothing is ever the first rewrite"),
    ("M08", V,
     "                elif have < needed:",
     "                elif have <= needed:",
     "off-by-one on the surviving comparison"),
    ("M09", V,
     "                if have is None:\n                    # \"Absent\" is read as \"below\"",
     "                if have is None and needed < 0:\n                    # \"Absent\" is read as \"below\"",
     "the dangerous inverse: an absent score now *passes* the tightened win"),
    ("M10", V,
     "                    if occurrence == 1:",
     "                    if occurrence == 0:",
     "no rewrite is ever the first, so nothing is ever loud"),
    ("M11", V,
     "                    if occurrence == 1:",
     "                    if occurrence >= 1:",
     "every rewrite is the first: the sentence on every record"),
    ("M12", V,
     '                              "occurrence": occurrence,',
     '                              "occurrence": 1,',
     "the occurrence index is frozen"),
    ("M13", V,
     "        self.degenerate_wins = 0\n        self.first_degenerate: Optional[Dict[str, Any]] = None",
     "        self.degenerate_wins = 0\n        self.first_degenerate: Optional[Dict[str, Any]] = {}",
     "first_degenerate starts non-None, so 'nothing degenerate happened' is unsayable"),
    ("M26", V,
     "            self._degeneracy_unreported = False\n            return self.first_degenerate",
     "            return self.first_degenerate",
     "the handover never clears: every notifier gets the record, one incident per WIN"),
    ("M27", V,
     "                            self._degeneracy_unreported = True",
     "                            self._degeneracy_unreported = False",
     "the handover is never armed, so the incident is never written at all"),
    ("M14", V,
     "DEGENERATE_NOTE = (\n    \"this game reported no score",
     "DEGENERATE_NOTE = (\n    \"This game reported no score",
     "wording only -- EXPECTED TO SURVIVE; nothing should assert on the capital"),

    # -- the guard ---------------------------------------------------------
    ("M15", G,
     '            if applied.get("degenerate") is not True:',
     '            if applied.get("degenerate") is None:',
     "a false bit now counts as degenerate"),
    ("M16", G,
     '            if applied.get("degenerate") is not True:\n                continue',
     '            if applied.get("degenerate") is not True:\n                pass',
     "the guard flags every win_tighten record, degenerate or not"),
    ("M17", G,
     '            if applied.get("op") != "win_tighten":\n                continue',
     '            if applied.get("op") != "win_tighten":\n                pass',
     "the guard flags any operator that carries the key"),
    ("M18", G,
     '    if report["verdict"] == "REFUSED":\n        return 2',
     '    if report["verdict"] == "REFUSED":\n        return 0',
     "the guard reports but never exits non-zero -- the decoration failure"),
    ("M19", G,
     '            seen["exam_eligible"] = False',
     '            seen["exam_eligible"] = True',
     "R-V22's machine-readable half stops saying the item is ineligible"),
    ("M20", G,
     '    if applied.get("op") == "multiple":',
     '    if applied.get("op") == "never":',
     "nested applied records stop being unwrapped"),
    ("M28", G,
     '        verdict = "INCONCLUSIVE"',
     '        verdict = "PASS"',
     "an unreadable line goes back to reading as a clean stream"),
    ("M29", G,
     "                skipped += 1",
     "                skipped += 0",
     "unreadable lines stop being counted, so the verdict cannot see them"),
    ("M30", G,
     "        variant_records += 1",
     "        variant_records += 0",
     "'no degeneracy in 300 variant records' and 'I walked nothing' merge again"),
    ("M21", G,
     '    if findings:\n        verdict = "REFUSED"',
     '    if findings:\n        verdict = "PASS"',
     "the verdict is hard-coded green"),

    # -- the wiring --------------------------------------------------------
    ("M22", E,
     "        self._note_degeneracy(runtime, game_id)\n",
     "",
     "the incident consumer is never called"),
    ("M23", E,
     "        first = runtime.take_first_degenerate()",
     "        first = runtime.first_degenerate",
     "back to reading shared state instead of taking the handover: the F1 race"),
    ("M24", E,
     "        if first is None:\n            return",
     "        if first is None:\n            first = {}",
     "the notifier stops honouring the handover and writes an incident every time"),

    # -- R-V22 firing by itself on a real run ------------------------------
    ("M31", "proxy/runner.py",
     '        "verdict": degeneracy["verdict"],',
     '        "verdict": "PASS",',
     "the run record always says the rule passed"),
    ("M32", "proxy/runner.py",
     '        "exam_eligible": all(v["exam_eligible"] for v in degeneracy["variants"]),',
     '        "exam_eligible": True,',
     "the run record always says the item is exam-eligible"),
    ("M33", "proxy/verify.py",
     '            for applied in _applied_records((record.get("variant") or {}).get("applied")):\n'
     '                if applied.pop("degenerate", None) is not None:',
     '            applied = (record.get("variant") or {}).get("applied") or {}\n'
     '            if applied.pop("degenerate", None) is not None:',
     "rung 5's stripper stops recursing -- EXPECTED TO SURVIVE the suite; rung 5 "
     "is what covers this and rung 5 does not run under pytest"),

    # -- the mock the negative control is built on -------------------------
    ("M25", "proxy/mock/arc_mock.py",
     '            "score": None if self.scoreless else self.levels_completed,',
     '            "score": self.levels_completed,',
     "the scoreless world quietly starts scoring: the negative control's own fixture"),
]

#: The whole suite, which is what `PREREGISTRATION.md` P4 asked for. An earlier
#: run of this harness narrowed it to three files; that deviation was
#: conservative (a smaller test set makes a mutant harder to kill, so it can
#: only understate the kill count) but it was a deviation from a written
#: criterion and it was not flagged, which is the part that mattered. It also
#: excluded `test_spend_gate.py`, the file whose one-character credential
#: poisons the redaction vault -- so the harness could not see that interaction
#: in either direction.
TESTS = ["-m", "pytest", "proxy", "-q", "-x", "--no-header"]


def build_tree(dst):
    """A copy of the repo's `proxy/`, plus the one file outside it that the
    package resolves against the repo root.

    `proxy/paths.py` puts `PILES` at `<repo>/arc-recon/data/piles.json` and
    `guard.py` reads it on every command, so a tree without it fails every test
    at collection -- which the first run of this harness reported as 25 kills
    out of 25. That is the failure this whole exercise exists to catch, and it
    happened to the exercise: a mutant "killed" by an error that would have
    killed the unmutated tree too measures nothing. Hence the copy below, and
    hence `BASELINE`, which is run first and must pass.
    """
    shutil.copytree(os.path.join(REPO, "proxy"), os.path.join(dst, "proxy"),
                    ignore=shutil.ignore_patterns("__pycache__", "var",
                                                  ".pytest_cache", "runs"))
    piles_dst = os.path.join(dst, "arc-recon", "data")
    os.makedirs(piles_dst)
    shutil.copy2(os.path.join(REPO, "arc-recon", "data", "piles.json"),
                 os.path.join(piles_dst, "piles.json"))
    # `test_chain.py::test_the_runners_default_head_location_is_gitignored`
    # shells out to `git check-ignore`, which exits 128 outside a repository --
    # so with the test surface widened to the whole suite (P4 as written), the
    # control failed and the harness refused to report, which is the control
    # working. An empty repo plus the copied `proxy/.gitignore` is enough for
    # that test to mean what it means in the real checkout.
    subprocess.run(["git", "init", "-q", dst], capture_output=True)


#: The control. Not a mutation: the anchor is replaced by itself, so this run
#: exercises exactly the code under test in exactly the tree the mutants get.
#: If it does not pass, every "killed" below is meaningless and the harness
#: says so instead of printing a clean sweep.
BASELINE = ("M00", V, "REASON_ABSENT = ", "REASON_ABSENT = ",
            "control: no mutation at all; must NOT be killed")


def run_one(mutant, keep_log):
    mid, relpath, old, new, why = mutant
    tmp = tempfile.mkdtemp(prefix="mutant-%s-" % mid)
    try:
        build_tree(tmp)
        path = os.path.join(tmp, relpath.replace("/", os.sep))
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        count = source.count(old)
        if count != 1:
            return {"id": mid, "file": relpath, "why": why,
                    "verdict": "not-applied",
                    "detail": "the anchor appears %d times, not once" % count}
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(source.replace(old, new))

        env = dict(os.environ)
        env["PYTHONPATH"] = tmp
        env["PYTHONIOENCODING"] = "utf-8"
        for name in ("ARC_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(name, None)
        started = time.time()
        proc = sp.run([sys.executable] + TESTS, cwd=tmp, env=env,
                      capture_output=True, text=True, encoding="utf-8",
                      errors="replace")
        tail = (proc.stdout + proc.stderr).strip().splitlines()
        keep_log.append("== %s %s (%s)\n%s\n"
                        % (mid, relpath, why, "\n".join(tail[-12:])))
        return {"id": mid, "file": relpath, "why": why,
                "verdict": "killed" if proc.returncode != 0 else "SURVIVED",
                "exit": proc.returncode,
                "seconds": round(time.time() - started, 1),
                "last_line": tail[-1] if tail else ""}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="comma-separated mutant ids")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    wanted = set(args.only.split(",")) if args.only else None
    results, log = [], []

    control = run_one(BASELINE, log)
    print("%-4s %-34s %s" % (control["id"], control["file"], control["verdict"]),
          flush=True)
    if control["verdict"] != "SURVIVED":
        print("CONTROL FAILED: the unmutated tree does not pass in this "
              "harness, so nothing below would mean anything. Exit %s: %s"
              % (control.get("exit"), control.get("last_line")))
        with open(os.path.join(args.out, "mutants.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump({"control": control, "verdict": "harness-invalid"},
                      fh, indent=2, sort_keys=True)
        with open(os.path.join(args.out, "mutants.txt"), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(log))
        return 1

    for mutant in MUTANTS:
        if wanted and mutant[0] not in wanted:
            continue
        result = run_one(mutant, log)
        results.append(result)
        print("%-4s %-34s %s" % (result["id"], result["file"], result["verdict"]),
              flush=True)

    survivors = [r for r in results if r["verdict"] == "SURVIVED"]
    unapplied = [r for r in results if r["verdict"] == "not-applied"]
    summary = {"control": control,
               "mutants": len(results),
               "killed": len([r for r in results if r["verdict"] == "killed"]),
               "survived": len(survivors),
               "not_applied": len(unapplied),
               "expected_survivors": ["M14", "M33"],
               "results": results}
    with open(os.path.join(args.out, "mutants.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    with open(os.path.join(args.out, "mutants.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(log))
    print(json.dumps({k: summary[k] for k in summary if k != "results"},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
