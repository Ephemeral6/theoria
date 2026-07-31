"""One command. Re-run everything the repo can reproduce, and grade the rest.

    python release/reproduce.py

Runs each deterministic producer in `release/steps.py`, in phase order, then
asks the only question that matters: **is the tree byte-identical to the
manifest afterwards?** A pipeline that claims determinism and then rewrites its
own artefacts differently has not reproduced anything, and this says so.

    --quick       artefact regeneration only; skip the test suites
    --only ID     one step (or one territory) and nothing else
    --list        show the plan without running it
    --no-archive  do not write release/runs/<UTC>-p19/

Everything lands in `release/REPRODUCTION_REPORT.md` and, unless suppressed, in
a timestamped archive under `release/runs/`. Failures are archived exactly as
successes are: a reproduction kit that only keeps its good runs is advertising.
"""

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import manifest as M  # noqa: E402
from steps import STEPS, UNRUNNABLE  # noqa: E402

REPORT_PATH = os.path.join(HERE, "REPRODUCTION_REPORT.md")

REPRODUCED = "REPRODUCED"
UNSTABLE = "REPRODUCED_UNSTABLE"
NEEDS_API = "NEEDS_API"
NEEDS_TOOLCHAIN = "NEEDS_TOOLCHAIN"
KNOWN_GAP = "KNOWN_GAP"
FAILED = "FAILED"
SKIPPED = "SKIPPED"


def utc_stamp() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


# ---------------------------------------------------------------------------
# what the tree looks like right now, cheaply
# ---------------------------------------------------------------------------

def git_dirty() -> Dict[str, List[str]]:
    """Tracked files git thinks changed, plus untracked ones.

    `git status` is the fast filter; the manifest hash is the slow adjudicator.
    Asking git first means one hash pass over a handful of files instead of
    1,100 of them after every step.
    """
    out = subprocess.run(
        ["git", "status", "--porcelain", "-uall"],
        cwd=REPO, capture_output=True, text=True,
    ).stdout
    modified, untracked = [], []
    for line in out.replace("\r\n", "\n").split("\n"):
        if not line.strip():
            continue
        code, _, path = line[:2], line[2], line[3:]
        path = path.strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        (untracked if code.strip() == "??" else modified).append(path)
    return {"modified": sorted(set(modified)), "untracked": sorted(set(untracked))}


def manifest_hashes() -> Dict[str, str]:
    return {p: r["sha256"] for p, r in M.read_manifest().items()}


def drift_against_manifest(candidates: List[str],
                           expected: Dict[str, str]) -> Tuple[List[str], List[str]]:
    """(really_different, touched_but_identical) for the given paths."""
    different, identical = [], []
    for rel in candidates:
        if rel not in expected:
            continue
        abs_path = os.path.join(REPO, rel)
        if not os.path.exists(abs_path):
            different.append(rel)
            continue
        digest, _ = M.sha256_file(rel)
        (identical if digest == expected[rel] else different).append(rel)
    return sorted(different), sorted(identical)


# ---------------------------------------------------------------------------
# probes for the unrunnable half
# ---------------------------------------------------------------------------

def probe_unrunnable() -> List[Dict[str, Any]]:
    out = []
    for entry in UNRUNNABLE:
        rec = dict(entry)
        found = {}
        for binary in entry.get("probe", []):
            found[binary] = shutil.which(binary)
        for var in entry.get("env_probe", []):
            found["$" + var] = os.environ.get(var)
        rec["probe_result"] = found
        # A toolchain that turns out to be installed is not a NEEDS_TOOLCHAIN.
        if entry["grade"] == NEEDS_TOOLCHAIN and any(found.values()):
            rec["grade"] = NEEDS_TOOLCHAIN
            rec["note"] = ("Present on this machine: %s. The step is still listed as "
                           "NEEDS_TOOLCHAIN because the repo does not carry it; on "
                           "this machine it can actually be run."
                           % ", ".join(k for k, v in found.items() if v))
        out.append(rec)
    return out


# ---------------------------------------------------------------------------
# running one step
# ---------------------------------------------------------------------------

def run_step(step: Dict[str, Any], expected: Dict[str, str],
             log_dir: Optional[str]) -> Dict[str, Any]:
    cwd = os.path.join(REPO, step["cwd"]) if step["cwd"] != "." else REPO
    before = git_dirty()
    started = time.time()
    env = dict(os.environ)
    env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        proc = subprocess.run(
            step["argv"], cwd=cwd, capture_output=True, text=True,
            errors="replace", timeout=step.get("timeout", 1800), env=env,
        )
        rc, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        rc, timed_out = -1, True
        stdout = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(
            exc.stdout, bytes) else (exc.stdout or "")
        stderr = "TIMEOUT after %ss" % step.get("timeout", 1800)
    elapsed = time.time() - started

    after = git_dirty()
    new_modified = [p for p in after["modified"] if p not in before["modified"]]
    new_untracked = [p for p in after["untracked"] if p not in before["untracked"]]
    different, identical = drift_against_manifest(new_modified, expected)

    if rc != 0:
        grade = FAILED
    elif different:
        grade = UNSTABLE
    else:
        grade = REPRODUCED

    if log_dir:
        safe = step["id"].replace("/", "_")
        with open(os.path.join(log_dir, "%s.log" % safe), "w",
                  encoding="utf-8", newline="\n") as fh:
            fh.write("$ cd %s && %s\n\n" % (step["cwd"], " ".join(step["argv"])))
            fh.write("exit=%s  elapsed=%.1fs  grade=%s\n\n" % (rc, elapsed, grade))
            fh.write("--- stdout ---\n%s\n--- stderr ---\n%s\n" % (stdout, stderr))

    return {
        "id": step["id"],
        "territory": step["territory"],
        "phase": step["phase"],
        "command": "cd %s && %s" % (step["cwd"], " ".join(
            ["python" if a == sys.executable else a for a in step["argv"]])),
        "claim": step["claim"],
        "source": step.get("source", ""),
        "note": step.get("note", ""),
        "kind": step.get("kind", "artifact"),
        "exit_code": rc,
        "timed_out": timed_out,
        "elapsed_s": round(elapsed, 1),
        "grade": grade,
        "bytes_differ_from_manifest": different,
        "rewritten_identically": identical,
        "new_untracked": new_untracked[:40],
        "new_untracked_count": len(new_untracked),
        "untracked_expected": bool(step.get("creates_untracked")),
        "tail": _tail(stdout, stderr),
    }


def _tail(stdout: str, stderr: str, lines: int = 12) -> str:
    body = (stdout or "").rstrip().split("\n")[-lines:]
    err = (stderr or "").rstrip().split("\n")[-lines:]
    parts = [ln for ln in body if ln.strip()]
    if any(ln.strip() for ln in err):
        parts += ["[stderr] " + ln for ln in err if ln.strip()]
    return "\n".join(parts[-lines:])


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------

GRADE_ORDER = [REPRODUCED, UNSTABLE, FAILED, NEEDS_API, NEEDS_TOOLCHAIN,
               KNOWN_GAP, SKIPPED]


def write_report(results: List[Dict[str, Any]], unrunnable: List[Dict[str, Any]],
                 meta: Dict[str, Any]) -> None:
    counts = {g: sum(1 for r in results if r["grade"] == g) for g in GRADE_ORDER}
    out: List[str] = []
    w = out.append

    w("# REPRODUCTION_REPORT")
    w("")
    w("Generated by `release/reproduce.py`. Do not hand-edit.")
    w("")
    w("| | |")
    w("|---|---|")
    w("| run | `%s` |" % meta["stamp"])
    w("| commit | `%s` |" % meta["commit"])
    w("| platform | %s, Python %s |" % (meta["platform"], meta["python"]))
    w("| mode | %s |" % meta["mode"])
    w("| wall clock | %.1f s |" % meta["elapsed_s"])
    w("| steps attempted | %d |" % len(results))
    w("")
    w("**%d REPRODUCED · %d REPRODUCED_UNSTABLE · %d FAILED · %d skipped by request**"
      % (counts[REPRODUCED], counts[UNSTABLE], counts[FAILED], counts[SKIPPED]))
    w("")
    verdict = "GREEN" if (counts[FAILED] == 0 and counts[UNSTABLE] == 0) else "RED"
    w("Verdict: **%s**" % verdict)
    w("")
    if verdict == "RED":
        w("> A red report is a result, not a broken tool. The failing rows below are")
        w("> archived under `release/runs/` exactly as the passing ones are.")
        w("")

    w("## What ran")
    w("")
    w("| step | grade | exit | secs | bytes differ | note |")
    w("|---|---|---|---|---|---|")
    for r in results:
        w("| `%s` | **%s** | %s | %s | %s | %s |" % (
            r["id"], r["grade"], r["exit_code"], r["elapsed_s"],
            len(r["bytes_differ_from_manifest"]) or "—",
            ("+%d untracked" % r["new_untracked_count"])
            if r["new_untracked_count"] else "—",
        ))
    w("")

    w("## Step by step")
    w("")
    for r in results:
        w("### `%s` — %s" % (r["id"], r["grade"]))
        w("")
        w("```")
        w(r["command"])
        w("```")
        w("")
        w("*claims:* %s" % r["claim"])
        if r["source"]:
            w("")
            w("*documented in:* `%s`" % r["source"])
        if r["note"]:
            w("")
            w("*note:* %s" % r["note"])
        w("")
        w("exit `%s` · %.1f s · %s" % (
            r["exit_code"], r["elapsed_s"],
            "tree byte-identical to the manifest afterwards"
            if not r["bytes_differ_from_manifest"]
            else "**%d file(s) differ from the manifest**"
                 % len(r["bytes_differ_from_manifest"])))
        w("")
        if r["bytes_differ_from_manifest"]:
            w("Files whose bytes changed:")
            w("")
            for p in r["bytes_differ_from_manifest"][:30]:
                w("* `%s`" % p)
            w("")
        if r["rewritten_identically"]:
            w("Rewritten with identical bytes (%d): %s"
              % (len(r["rewritten_identically"]),
                 ", ".join("`%s`" % p for p in r["rewritten_identically"][:8])))
            w("")
        if r["new_untracked_count"]:
            label = ("expected — this step creates run output"
                     if r["untracked_expected"]
                     else "**unexpected** — this step was not declared as one that "
                          "creates files")
            w("New untracked paths: %d (%s)" % (r["new_untracked_count"], label))
            w("")
            for p in r["new_untracked"][:10]:
                w("* `%s`" % p)
            w("")
        if r["grade"] in (FAILED, UNSTABLE) and r["tail"]:
            w("Output tail:")
            w("")
            w("```")
            for line in r["tail"].split("\n"):
                w(line)
            w("```")
            w("")
        elif r["tail"]:
            w("<details><summary>output tail</summary>")
            w("")
            w("```")
            for line in r["tail"].split("\n"):
                w(line)
            w("```")
            w("")
            w("</details>")
            w("")

    w("## What could not run, and why")
    w("")
    w("These are graded, not omitted. Every one of them is a real limit on what a")
    w("stranger can check, and the release is only honest if the limits ship with it.")
    w("")
    w("| what | grade | territory |")
    w("|---|---|---|")
    for u in unrunnable:
        w("| %s | **%s** | %s |" % (u["what"], u["grade"], u["territory"]))
    w("")
    for u in unrunnable:
        w("### %s — %s" % (u["id"], u["grade"]))
        w("")
        w("*what:* %s" % u["what"])
        w("")
        w("*needs:* %s" % u["needs"])
        w("")
        w("*why it matters:* %s" % u["why_it_matters"])
        if u.get("probe_result"):
            w("")
            w("*probed on this machine:* %s" % ", ".join(
                "%s=%s" % (k, v or "absent") for k, v in u["probe_result"].items()))
        if u.get("note"):
            w("")
            w("*note:* %s" % u["note"])
        w("")

    w("## The grades")
    w("")
    w("| grade | meaning |")
    w("|---|---|")
    w("| `REPRODUCED` | re-ran, and every byte matched `MANIFEST.jsonl` |")
    w("| `REPRODUCED_UNSTABLE` | re-ran, output differs in bytes; the paths are named above |")
    w("| `NEEDS_API` | needs the live ARC API, a model API, or quota |")
    w("| `NEEDS_TOOLCHAIN` | needs a local binary the repo does not ship |")
    w("| `KNOWN_GAP` | no regeneration path exists in the tree at all |")
    w("| `FAILED` | ran, and did not succeed |")
    w("")
    w("A skipped step is never graded `REPRODUCED`.")
    w("")

    with open(REPORT_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")


# ---------------------------------------------------------------------------

def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quick", action="store_true",
                    help="artefact regeneration only; skip the test suites")
    ap.add_argument("--only", default=None,
                    help="run only steps whose id or territory matches")
    ap.add_argument("--list", action="store_true", help="show the plan, run nothing")
    ap.add_argument("--no-archive", action="store_true")
    args = ap.parse_args(argv)

    plan = list(STEPS)
    if args.quick:
        plan = [s for s in plan if s.get("kind") != "suite"]
    if args.only:
        plan = [s for s in plan
                if args.only in (s["id"], s["territory"]) or
                s["id"].startswith(args.only)]
        if not plan:
            print("no step matches %r" % args.only)
            return 2
    plan.sort(key=lambda s: (s["phase"], s["id"]))

    if args.list:
        for s in plan:
            print("%-28s phase %s  cd %s && %s"
                  % (s["id"], s["phase"], s["cwd"], " ".join(
                      ["python" if a == sys.executable else a for a in s["argv"]])))
        print("\nnot runnable here:")
        for u in UNRUNNABLE:
            print("%-28s %s" % (u["id"], u["grade"]))
        return 0

    stamp = utc_stamp()
    log_dir = None
    if not args.no_archive:
        log_dir = os.path.join(HERE, "runs", "%s-p19" % stamp)
        os.makedirs(log_dir, exist_ok=True)

    expected = manifest_hashes()
    if not expected:
        print("MANIFEST.jsonl is absent. Run `python release/manifest.py` first.")
        return 2

    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO,
                            capture_output=True, text=True).stdout.strip()

    print("reproducing %d steps against %d manifest hashes" % (len(plan), len(expected)))
    started = time.time()
    results = []
    for i, step in enumerate(plan, 1):
        print("[%d/%d] %-28s " % (i, len(plan), step["id"]), end="", flush=True)
        rec = run_step(step, expected, log_dir)
        results.append(rec)
        print("%-20s %5.1fs%s" % (
            rec["grade"], rec["elapsed_s"],
            "  (%d file(s) differ)" % len(rec["bytes_differ_from_manifest"])
            if rec["bytes_differ_from_manifest"] else ""))

    elapsed = time.time() - started
    unrunnable = probe_unrunnable()
    meta = {
        "stamp": stamp, "commit": commit, "elapsed_s": elapsed,
        "platform": sys.platform, "python": sys.version.split()[0],
        "mode": "quick" if args.quick else ("only=%s" % args.only if args.only
                                            else "full"),
    }
    write_report(results, unrunnable, meta)

    if log_dir:
        with open(os.path.join(log_dir, "results.json"), "w",
                  encoding="utf-8", newline="\n") as fh:
            json.dump({"meta": meta, "results": results, "unrunnable": unrunnable},
                      fh, indent=2, sort_keys=True, ensure_ascii=False)
        shutil.copyfile(REPORT_PATH, os.path.join(log_dir,
                                                  "REPRODUCTION_REPORT.md"))
        print("archived -> %s" % os.path.relpath(log_dir, REPO))

    failed = [r for r in results if r["grade"] in (FAILED, UNSTABLE)]
    print("wrote %s" % os.path.relpath(REPORT_PATH, REPO))
    print("%d/%d REPRODUCED, %d not" % (len(results) - len(failed), len(results),
                                        len(failed)))
    for r in failed:
        print("  %-28s %s" % (r["id"], r["grade"]))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
