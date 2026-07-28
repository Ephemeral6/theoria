"""Verify a ledger's hash chain, and compute the head that makes it mean anything.

    python -m proxy.tools.verify_chain <ledger.jsonl>
    python -m proxy.tools.verify_chain <ledger.jsonl> --json
    python -m proxy.tools.verify_chain <ledger.jsonl> --expect-head sha256:9a4e…

Exit 0 if the chain verifies, 1 if it is broken, 2 if the stream carries no
chain at all.  Those are three different answers and this tool refuses to
collapse them: "unchained" reported as "verified" would be the fifth check in
this repo to pass because it never ran.

## What this proves, and what it does not

RED-40, from the P-9 red team: nothing authenticates a record.  `reconcile.py`
and the frozen scorer check the file against itself -- every check is internal
consistency, so a file no proxy ever wrote reconciles clean if it is written
carefully enough.  P-9 raised the price of forgery; a price is not a proof.

The chain closes the *tamper-after-the-fact* half.  Each record's `prev` is the
sha256 of the previous line's bytes as written, including that line's own
`prev`, so editing one field, deleting a line, inserting one, or swapping two
adjacent records breaks every link after the change.

It does **not** stop anyone rewriting the whole file and recomputing the chain
end to end.  What stops that is the **head published outside the file**:
`runs/<id>/MANIFEST.json` records `{last_seq, sha256}` and goes into git, which
is itself a hash chain, and gets pushed to a remote -- so the witness lives on
another machine.  Forging then means rewriting git history and the remote too,
which is a much more expensive and much more detectable act.

So the honest claim is: **tamper-evident after the head is published**, not
"authenticated".  Nothing local can prove the frames came from ARC; only an
API-signed receipt could, and the API offers none.

## Why the hash is over bytes

A verifier that re-serialises each record before hashing is checking that
today's `canonical()` agrees with the one that wrote the file.  Change that
function's behaviour once and every ledger ever written goes red simultaneously,
which trains everyone to ignore the alarm.  Hashing the bytes on disk asks the
only question worth asking.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from proxy.ledger import line_hash                          # noqa: E402


def verify(path, expect_seq=None):
    """Walk the chain byte-wise.  Returns a report dict; never raises on content.

    `expect_seq` asks for the head *as of* that seq, recorded in
    `head_at_seq` -- the prefix a published head witnesses.  Whole-file
    comparison is the wrong question for this ledger: it is one shared
    append-only file, so the next honest run makes every previously published
    head mismatch, and an alarm that fires on honest files is one nobody reads.
    """
    report = {
        "path": path,
        "lines": 0,
        "chained": 0,
        "unchained": 0,
        "first_break": None,
        "breaks": [],
        "head": None,
        "head_at_seq": None,
        "reached_seq": False,
        "last_seq": None,
        "verdict": None,
    }
    if not os.path.exists(path):
        report["verdict"] = "MISSING"
        return report

    prev_hash = None
    prev_lineno = None
    with open(path, "rb") as fh:
        for lineno, raw in enumerate(fh, 1):
            stripped = raw.rstrip(b"\r\n")
            if not stripped.strip():
                # The writer never emits one, and a blank line does not take
                # part in the chain -- so skipping it silently would let an
                # attacker insert any number of them, head unchanged.  No
                # payload can hide there, but "any edit is detectable" has to
                # mean it, so it is a break rather than a shrug.
                report["breaks"].append({
                    "line": lineno, "kind": "blank_line",
                    "detail": "the writer never emits a blank line"})
                continue
            report["lines"] += 1
            try:
                record = json.loads(stripped.decode("utf-8"))
            except (ValueError, UnicodeDecodeError) as exc:
                # RED-44: one unreadable line must not destroy the whole file.
                # It still occupies its place in the chain, so the walk carries
                # on with its bytes as the predecessor.
                report["breaks"].append({
                    "line": lineno, "kind": "unreadable",
                    "detail": str(exc)[:200]})
                prev_hash, prev_lineno = line_hash(stripped), lineno
                continue

            claimed = record.get("prev", "__absent__")
            if claimed == "__absent__":
                report["unchained"] += 1
            elif prev_hash is None:
                # First record of the file: `prev` must be null.  A non-null
                # `prev` here claims a predecessor the file does not contain,
                # which is what a truncated-from-the-front file looks like.
                if claimed is not None:
                    report["breaks"].append({
                        "line": lineno, "kind": "orphan_head",
                        "detail": "first record claims prev %r, but nothing "
                                  "precedes it in this file" % claimed})
                else:
                    report["chained"] += 1
            elif claimed != prev_hash:
                report["breaks"].append({
                    "line": lineno, "kind": "broken_link",
                    "detail": "prev is %r; line %d hashes to %r"
                              % (claimed, prev_lineno, prev_hash)})
            else:
                report["chained"] += 1

            if isinstance(record.get("seq"), int):
                report["last_seq"] = record["seq"]
            prev_hash, prev_lineno = line_hash(stripped), lineno

            if expect_seq is not None and record.get("seq") == expect_seq:
                report["head_at_seq"] = prev_hash
                report["reached_seq"] = True

    report["head"] = prev_hash
    if expect_seq is not None and not report["reached_seq"]:
        # The file stops before the seq that was witnessed.  Nothing chains to
        # a last line, so truncating the tail breaks no link -- this is the
        # only thing that sees it, and it is the tamper with the clearest
        # motive: delete the end of the run that went badly.
        report["breaks"].append({
            "line": report["lines"], "kind": "truncated_tail",
            "detail": "a head was published at seq %s but the file ends at seq "
                      "%s -- records that were witnessed are gone"
                      % (expect_seq, report["last_seq"])})

    report["breaks"] = report["breaks"][:50]
    report["first_break"] = report["breaks"][0]["line"] if report["breaks"] else None

    if report["lines"] == 0:
        # An empty file is not a verified file.  "Two builds that produced
        # nothing are byte-identical" is a real bug elsewhere in this repo;
        # the same shape is refused here.
        report["verdict"] = "EMPTY"
    elif report["breaks"]:
        report["verdict"] = "FAIL"
    elif report["chained"] == 0:
        report["verdict"] = "UNCHAINED"
    elif report["unchained"]:
        # A stream lifted from v0, or one written across the change that
        # introduced the chain.  Reported as its own thing so nobody reads a
        # partially chained file as a fully chained one.
        report["verdict"] = "PARTIAL"
    else:
        report["verdict"] = "PASS"
    return report


# UNCHAINED gets its own code.  Sharing 2 with MISSING and EMPTY meant a
# wrapper testing `rc != 1` read a stream whose `prev` fields had been stripped
# wholesale as a benign missing file -- the downgrade attack reading as an
# absent one.
EXIT = {"PASS": 0, "FAIL": 1, "PARTIAL": 1, "UNCHAINED": 3,
        "EMPTY": 2, "MISSING": 2}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--expect-head",
                    help="a published head hash.  Compared against the whole "
                         "file unless --expect-seq is given; prefer "
                         "--expect-head-file, which carries both.")
    ap.add_argument("--expect-seq", type=int,
                    help="the seq the published head was taken at.  With it, "
                         "the comparison is against the file's prefix, so "
                         "later honest appends do not raise a false alarm and "
                         "a truncated tail does raise a real one.")
    ap.add_argument("--expect-head-file", metavar="PATH",
                    help="a head written earlier by --emit-head.  Uses its "
                         "last_seq and sha256 together, which is the check you "
                         "almost always want.")
    ap.add_argument("--emit-head", metavar="PATH",
                    help="write the head to PATH as JSON, for committing.  "
                         "PATH must be somewhere git actually tracks: writing "
                         "a head into an ignored directory publishes nothing, "
                         "and an unpublished head is not a witness to anything."
                         "  Refused if the chain does not verify.")
    args = ap.parse_args(argv)

    expect_head, expect_seq = args.expect_head, args.expect_seq
    if args.expect_head_file:
        with open(args.expect_head_file, encoding="utf-8") as fh:
            published = json.load(fh)
        expect_head = published.get("sha256")
        expect_seq = published.get("last_seq")
        if not expect_head:
            print("%s carries no sha256; it is not a head"
                  % args.expect_head_file, file=sys.stderr)
            return 2

    report = verify(args.path, expect_seq=expect_seq)
    if expect_head:
        report["expected_head"] = expect_head
        report["expected_seq"] = expect_seq
        # Against the prefix when we know which seq was witnessed, against the
        # whole file only when we do not.  The prefix form is the one that
        # survives an append-only file being appended to.
        actual = report["head_at_seq"] if expect_seq is not None else report["head"]
        if actual != expect_head:
            report["breaks"].append({
                "line": report["lines"], "kind": "head_mismatch",
                "detail": "published head %r at seq %s; this file gives %r"
                          % (expect_head, expect_seq, actual)})
        if report["breaks"]:
            report["verdict"] = "FAIL"
            report["first_break"] = report["breaks"][0]["line"]

    if args.emit_head:
        if report["verdict"] != "PASS":
            print("refusing to publish a head for a %s stream: a head that "
                  "witnesses an unverified file is worse than no head, because "
                  "it looks like one." % report["verdict"], file=sys.stderr)
            return EXIT[report["verdict"]] or 1
        head = {"path": os.path.abspath(args.path), "last_seq": report["last_seq"],
                "sha256": report["head"], "lines": report["lines"],
                "verdict": report["verdict"]}
        os.makedirs(os.path.dirname(os.path.abspath(args.emit_head)) or ".",
                    exist_ok=True)
        with open(args.emit_head, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(head, fh, indent=2, sort_keys=True)
            fh.write("\n")
        print("head written to %s -- it is only published once that file is "
              "committed and pushed" % args.emit_head)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("%s: %s" % (args.path, report["verdict"]))
        print("  lines %d  chained %d  unchained %d"
              % (report["lines"], report["chained"], report["unchained"]))
        print("  head  %s  last_seq %s" % (report["head"], report["last_seq"]))
        for b in report["breaks"][:10]:
            print("  BREAK line %d [%s] %s" % (b["line"], b["kind"], b["detail"]))
    return EXIT[report["verdict"]]


if __name__ == "__main__":
    raise SystemExit(main())
