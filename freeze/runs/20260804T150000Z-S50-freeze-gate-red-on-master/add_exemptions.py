"""S50 · insert the eleven dated run exemptions `tools/check_locations.py` asks for.

Run once, from the repo root:

    python freeze/runs/20260804T150000Z-S50-freeze-gate-red-on-master/add_exemptions.py

It is idempotent (a `dir` already present is left alone) and it round-trips the
file byte-for-byte apart from the insertions: the allowlist is `indent=1`,
CRLF, with a trailing newline, and that was verified before anything was
written rather than assumed.

Kept as evidence, not as a tool: the entries below are the signatures, and a
reader who wants to know what was signed for should read them here next to the
run that signed them.
"""
import io
import json
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PATH = os.path.join(REPO, "tools", "locations_allowlist.json")

NEW = [
    {
        "dir": "baseline-arms/runs/2026-08-01T044513Z-A19",
        "dated": "2026-08-04",
        "files": 1,
        "reason": "hand-written RUN_STATE prose, not a captured path: the sentence records why A19 refused to commit the archive rebuild, and the path in it is already elided to an ellipsis by its author -- it names no drive and no account. Signed rather than 'fixed' because the only available fix would be editing a sentence that is about this very defect. Landed 2026-08-01 by db33f983 (merge f9a61c0c), after this allowlist was last generated on 2026-08-01",
    },
    {
        "dir": "exam/runs/20260801T0400Z-U3-CENSUS",
        "dated": "2026-08-04",
        "files": 1,
        "reason": "write-once census record; census.json carries the worktree it was measured in under `root`, written by exam/u3_census.py:511 (`root.as_posix()`, the one field census() does not pass through u3.sanitize_paths). THE GENERATOR STILL DOES THIS, so this exemption covers the landed measurement only and the source fix is reported to exam/ separately; it is not a licence for the next census. Landed 2026-08-01 by 77f18b41 (merge 01d627e3), after this allowlist was last generated",
    },
    {
        "dir": "exam/runs/20260801T1200Z-U3-CENSUS-REPAIRED",
        "dated": "2026-08-04",
        "files": 1,
        "reason": "write-once census record, the repaired re-run of the above; same unsanitised `root` field from exam/u3_census.py:511, naming a different worktree because it was measured from one. Same standing caveat: the generator is unfixed and this signature does not extend to future censuses. Landed 2026-08-01 by 0acc8b8f (merge 327ad0b0), after this allowlist was last generated",
    },
    {
        "dir": "proxy/runs/2026-08-01T044534Z-A20",
        "dated": "2026-08-04",
        "files": 3,
        "reason": "write-once captured console output: GATES.txt is the verify.sh transcript naming the Git-for-Windows bash that ran it, and contract-verdict-before.txt / contract-update.txt are proxy/tools/contract.py's stdout echoing back the argv path it was pointed at. Rewriting a transcript falsifies what the tool said, which the checker's own guidance rules out. Landed 2026-08-01 by 05b8ee99 (merge e51e0ebe), after this allowlist was last generated",
    },
    {
        "dir": "theoria-arm/runs/2026-08-01T045542Z-A18",
        "dated": "2026-08-04",
        "files": 1,
        "reason": "write-once captured console output: verify_out.txt is the verify.sh transcript, and the path it names is the Git-for-Windows bash interpreter that executed it, not a build product of this repository. Landed 2026-08-01 by 8ec111fb (merge 7c61d107), after this allowlist was last generated",
    },
    {
        "dir": "theoria-arm/runs/20260801T001851Z-R1b-g50t-a",
        "dated": "2026-08-04",
        "files": 23,
        "reason": "write-once paid run record. Three sources, none scrubbable: `ledger_abspath` is the spend gate's one-true-pool fingerprint (theoria-arm/harness/spend.py:160), absolute BY DESIGN so that ~50 worktrees cannot become ~50 pools each carrying the full ceiling -- theoria-arm/tests/test_desk_gate.py:516 asserts '.worktrees' is absent from it, so relativising this field would break the money single-truth mechanism; the `traceback` fields are verbatim CPython output captured at theoria-arm/world/adapt.py:53 and are embedded unchanged inside the desk/call-*.md prompts the model was actually shown, so editing them would claim the model saw text it did not; env_proxy.log is the proxy's own console. CAVEAT ON THE COUNT: 7 of these 23 are the checker misreading the playbook comment `up/home/undo` -- ARC action names -- as a POSIX home path, so 23 is what the checker sees today and not a claim that 23 files name a machine; if that false positive is later fixed the count shrinks, which the checker reports as a note rather than a red. Landed 2026-08-01 by 445c647e (merge e8345aff), after this allowlist was last generated",
    },
    {
        "dir": "theoria-arm/runs/20260801T001851Z-R1b-sk48-b",
        "dated": "2026-08-04",
        "files": 7,
        "reason": "write-once paid run record, the sk48 leg of the same R1b round: the spend gate's `ledger_abspath` (absolute by design, harness/spend.py:160), the run's own ledger path, the transfer record's `source_books_dir`, and the env proxy console banner. Landed 2026-08-01 by 445c647e (merge e8345aff), after this allowlist was last generated",
    },
    {
        "dir": "theoria-arm/runs/20260801T043743Z-R2-g50t-a",
        "dated": "2026-08-04",
        "files": 5,
        "reason": "write-once paid run record for the R2 round: the spend gate's `ledger_abspath` (absolute by design, harness/spend.py:160), the ledger's own path, transfer's `source_books_dir`, and the env proxy console banner. Landed 2026-08-01 by d10788f7, on master by 2026-08-02, after this allowlist was last generated",
    },
    {
        "dir": "theoria-arm/runs/20260801T043743Z-R2-sk48-b",
        "dated": "2026-08-04",
        "files": 5,
        "reason": "write-once paid run record, the sk48 leg of the R2 round; identical sources to its g50t sibling and equally unscrubbable for the same reason -- the pool fingerprint is what stops a worktree from minting its own budget. Landed 2026-08-01 by d10788f7, on master by 2026-08-02, after this allowlist was last generated",
    },
    {
        "dir": "theoria-arm/runs/20260801T044640Z-R2b-g50t-a",
        "dated": "2026-08-04",
        "files": 16,
        "reason": "write-once paid run record for the R2b round that produced the kept generated frontier (containment 9.6% to 78%). Nine of the sixteen are desk/call-*.md, the prompts the model was shown, which embed engine tracebacks captured verbatim at theoria-arm/world/adapt.py:53; the rest are the spend-gate fingerprint, the compiled forms' paths in theorize.json and the env proxy banner. Landed 2026-08-01 by d10788f7, on master by 2026-08-02, after this allowlist was last generated",
    },
    {
        "dir": "theoria-arm/runs/20260801T044640Z-R2b-sk48-b",
        "dated": "2026-08-04",
        "files": 7,
        "reason": "write-once paid run record, the sk48 leg of the R2b round: the spend gate's `ledger_abspath`, the ledger path, transfer's `source_books_dir`, theorize.json's compiled-form paths and the env proxy console banner. Landed 2026-08-01 by d10788f7, on master by 2026-08-02, after this allowlist was last generated",
    },
]


def main():
    raw = io.open(PATH, "rb").read()
    doc = json.loads(raw.decode("utf-8"))
    have = {e["dir"] for e in doc["runs"]}
    added = [e for e in NEW if e["dir"] not in have]
    doc["runs"] = sorted(doc["runs"] + added, key=lambda e: e["dir"])
    out = (json.dumps(doc, indent=1) + "\n").replace("\n", "\r\n").encode("utf-8")
    io.open(PATH, "wb").write(out)
    print("added %d exemption(s); runs now %d" % (len(added), len(doc["runs"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
