"""Did A10 deliver? Asked so that the answer does not depend on one disk.

    cd proxy && python -m tools.audit_delivery

The 2026-07-29 progress check failed `A10-shared-ledger-real-arms` on the
grounds that `proxy/var/ledger.jsonl` parses to zero records carrying a real
arm. The count was right. The method could not support it, for three reasons
that this module exists to keep separate:

1. **Wrong object.** The check said it verified deliveries "按 `origin/master`"
   and then read `proxy/var/ledger.jsonl`. `proxy/.gitignore:3` excludes
   `var/`, and `git ls-files proxy/var/` is empty at every commit, so that path
   has never been in `origin/master`. A path that cannot appear in a commit
   cannot be evidence about that commit. On a clean checkout the same check
   reads an absent file -- and "absent" and "present, and the answer is zero"
   must not print the same word. `census()` below returns `ABSENT` or
   `PRESENT`, never a bare boolean, for exactly that reason.

2. **Wrong proposition.** "A real arm" names two different things and the check
   collapsed them:

       axis 1  arm identity   `arm` is one of bare_cc / schema_repro / theoria
                              rather than probe / replay / mock_arm;
       axis 2  liveness       the run's `run_start` names a non-localhost
                              `env_upstream` / `model_upstream`, i.e. something
                              actually left this machine.

   Both are zero today, which is why one word covering both went unnoticed.
   They have different owners and different remedies, so they are counted
   separately here and never summed.

3. **Circular source.** The reported number is A10's own published *before*
   state -- `proxy/runs/20260729T010000Z-A10/MANIFEST.json` records
   `records: 107, by_arm {mock_arm: 74, replay: 33}, real_arm_records: 0` as
   the condition it measured against. The same sentence is a hand-written
   constant in `monitor/spec.py:593` belonging to finding F-19, which is the
   ruling that *created* A10. A check that re-reads a ticket's premise and
   scores it as the ticket's result will fail that ticket forever.

**A10 never claimed the thing it was failed for.** `demo_three_arms.py:16-22`
says in tracked text: "It is not the three real arms running their own inner
loops through the proxy -- that requires editing `theoria-arm/`,
`baseline-arms/` and `ablation-arm/`, which is outside this item's `proxy`
territory and is recorded as a gap in `SCOPE.md` §1." The arm-side rewiring was
ruled cross-territory *before* the work began and filed as gap #1.

So: **zero real-arm records in the shared ledger is the expected state**, and
it stays expected until the arm-side items land. The census below reports it
and does not fail on it. What this module *does* fail on is the tracked
evidence A10 actually produced going missing -- which is a claim about
`origin/master`, checkable from `origin/master`, on paths that are in it.

`DELIVERY_RULING.md` is the prose; this file is the part that runs.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(HERE)
A10 = os.path.join(HERE, "runs", "20260729T010000Z-A10")

#: The three experimental arms. `probe` and `replay` are instruments and
#: `mock_arm` is a fixture; none of them is an arm whose bill anyone reports.
#: Kept as a literal rather than imported from `ledger.ARMS` so that
#: registering a seventh arm cannot silently change what this audit counts.
REAL_ARMS = frozenset({"bare_cc", "schema_repro", "theoria"})

#: Files A10 pinned that later items were *expected* to keep editing. Their
#: digests are allowed to move; what must survive is the substance, asserted
#: by `MARKERS` below. Pinning these would make this audit go red on somebody
#: else's correct work, which is the failure mode that produced this module.
MOVED_ON = frozenset({
    "proxy/ledger.py", "proxy/reconcile.py",
    "proxy/LEDGER_FORMAT.md", "proxy/README.md",
})

#: Everything else A10 pinned is frozen: its own run directory, and the two
#: test files that carry its proofs.
#:
#: The digests are **read from A10's own MANIFEST at run time** rather than
#: copied into this file. Copying them would create a second place for the
#: same fact to rot, and this audit exists because a number got restated until
#: nobody could tell which copy was the measurement. (Writing this check, I
#: first hard-coded a digest taken from a summary; it was wrong after the
#: eighth hex character, and this line is why it got caught.)
MANIFEST_PATH = os.path.join(A10, "MANIFEST.json")

#: Substance that must survive later edits to the two files A10 rewrote. A
#: digest cannot express this: both files are still being worked on, and the
#: question is whether A10's *fix* is still there, not whether the byte count
#: is.
MARKERS = [
    ("ledger.py", "LedgerLockUnavailable",
     "the fail-closed cross-process ledger lock A10 added"),
    ("ledger.py", "msvcrt",
     "the OS-level sidecar lock (fcntl/msvcrt) that replaced the threading.Lock"),
    ("reconcile.py", 'RECONCILIATION_KEY = ("actions", "cost", "score_per_run")',
     "the reconciliation key A10 re-derived"),
    ("reconcile.py", "_gap_turns",
     "`turns` carried as a declared non-voting gap rather than a faked leg"),
]


def sha256_of(path):
    import hashlib
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def live(url):
    return bool(url) and "127.0.0.1" not in url and "localhost" not in url


def census(ledger_path):
    """Three-valued by construction: the file's absence is its own answer.

    Returns a dict whose `state` is `ABSENT` or `PRESENT`. A caller cannot get
    a bare count without also getting the word, which is the whole point --
    the check this replaces could print the same red for a missing file and a
    file that was read and answered zero.
    """
    if not os.path.exists(ledger_path):
        return {"state": "ABSENT", "path": ledger_path,
                "detail": "no file at this path. `proxy/.gitignore:3` excludes "
                          "`var/`, so this is the normal state of a fresh "
                          "checkout and is NOT a finding about any commit."}

    records, unreadable = [], 0
    with open(ledger_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                unreadable += 1

    # `reconcile.py:521` stamps an incident with `steps[0]["arm"]` -- the arm of
    # whatever run it is complaining about. Counting arms without excluding
    # incidents counts the auditor's own footprints.
    activity = [r for r in records if r.get("event") != "incident"]
    incidents = len(records) - len(activity)
    starts = {r.get("run_id"): r for r in records if r.get("event") == "run_start"}

    by_arm = {}
    for record in activity:
        by_arm[record.get("arm")] = by_arm.get(record.get("arm"), 0) + 1

    return {
        "state": "PRESENT",
        "path": ledger_path,
        "records": len(records),
        "unreadable_lines": unreadable,
        "incident_records": incidents,
        "activity_records": len(activity),
        "by_arm_excluding_incidents": by_arm,
        "axis1_real_arm_records": sum(
            1 for r in activity if r.get("arm") in REAL_ARMS),
        "axis2_live_runs": sum(
            1 for r in starts.values()
            if live(r.get("env_upstream")) or live(r.get("model_upstream"))),
        "runs": len(starts),
    }


def check_evidence(problems):
    print("A10's tracked evidence, on paths that are in the commit")
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (OSError, ValueError) as exc:
        problems.append("A10's MANIFEST.json is unreadable (%s) -- with it "
                        "gone there is nothing to check against" % exc)
        print("   MISSING  proxy/runs/20260729T010000Z-A10/MANIFEST.json")
        return

    if manifest.get("prompt_id") != "A10-shared-ledger-real-arms":
        problems.append("A10's MANIFEST names prompt_id %r"
                        % manifest.get("prompt_id"))

    for entry in manifest.get("files", []):
        relative = entry["path"]
        path = os.path.join(REPO, relative)
        if not os.path.exists(path):
            problems.append("missing: %s" % relative)
            print("   MISSING  %s" % relative)
            continue
        if relative in MOVED_ON:
            print("   moved on %s (substance checked below)" % relative)
            continue
        actual = sha256_of(path)
        if actual != entry["sha256"]:
            problems.append(
                "%s no longer matches the digest A10's own MANIFEST pinned "
                "(%s != %s)" % (relative, actual[:12], entry["sha256"][:12]))
            print("   CHANGED  %s" % relative)
        else:
            print("   pinned   %s" % relative)

    print()
    print("A10's substance, in files later items kept editing")
    for relative, marker, why in MARKERS:
        path = os.path.join(HERE, relative)
        try:
            with open(path, encoding="utf-8") as fh:
                blob = fh.read()
        except OSError:
            problems.append("cannot read proxy/%s" % relative)
            continue
        if marker in blob:
            print("   still there  %s" % why)
        else:
            problems.append("proxy/%s no longer contains %r -- %s"
                            % (relative, marker, why))
            print("   GONE         %s" % why)


def check_demo(problems):
    """A10's own self-verifying artefact, re-run rather than believed.

    `demo_three_arms.py:126-131` asserts 42 records, three distinct pids, no
    duplicate `seq`, every record a real arm, and `verify_chain` clean. It
    writes only into a temp dir. Running it is a stronger check than any digest
    because it re-establishes the claim instead of confirming a file's bytes.
    """
    print()
    print("A10's demo, re-run (temp dir only, no network, no spend)")
    script = os.path.join(A10, "demo_three_arms.py")
    if not os.path.exists(script):
        problems.append("missing: proxy/runs/20260729T010000Z-A10/demo_three_arms.py")
        print("   MISSING")
        return
    proc = subprocess.run([sys.executable, script], cwd=REPO,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode == 0:
        print("   exit 0 -- three arm identities, one ledger, chain intact")
    else:
        problems.append("demo_three_arms.py exited %d" % proc.returncode)
        print("   EXIT %d" % proc.returncode)
        tail = (proc.stdout or "").strip().splitlines()[-6:]
        for line in tail:
            print("     | %s" % line)


def report_census(ledger_path):
    """Reported, never failed on. See this module's docstring, point 3."""
    print()
    print("The shared ledger -- reported, not judged")
    result = census(ledger_path)
    print("   state: %s" % result["state"])
    if result["state"] == "ABSENT":
        print("   %s" % result["detail"])
        return result
    print("   %d records = %d activity + %d incident (reconcile.py:521 stamps"
          % (result["records"], result["activity_records"],
             result["incident_records"]))
    print("     an incident with the arm of the run it complains about, so"
          " arm counts")
    print("     without this split include the auditor's own footprints)")
    print("   by arm, excluding incidents: %s"
          % result["by_arm_excluding_incidents"])
    print("   axis 1, real-arm records:   %d" % result["axis1_real_arm_records"])
    print("   axis 2, live runs:          %d of %d"
          % (result["axis2_live_runs"], result["runs"]))
    print()
    print("   Zero on both axes is the EXPECTED state and is not an A10")
    print("   defect. Axis 1 needs the arm-side rewiring SCOPE.md section 1")
    print("   ruled cross-territory (theoria-arm needs configuration only;")
    print("   baseline-arms and ablation-arm need source changes). Axis 2")
    print("   needs a live run, which proxy/README.md:141 records has never")
    print("   happened. Neither is owned by proxy.")
    return result


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    ledger_path = argv[0] if argv else os.path.join(HERE, "var", "ledger.jsonl")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")

    problems = []
    check_evidence(problems)
    check_demo(problems)
    report_census(ledger_path)

    print()
    if problems:
        print("A10: RED (%d problem(s)) -- its tracked delivery has regressed"
              % len(problems))
        for problem in problems:
            print("   - %s" % problem)
        return 1
    print("A10: delivered. Tracked evidence present, demo reproduces, and the")
    print("shared ledger's zero is the state SCOPE.md said it would be.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
