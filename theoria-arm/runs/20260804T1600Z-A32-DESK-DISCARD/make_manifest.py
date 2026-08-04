"""Write this run's MANIFEST.json from what is actually on disk.

The hashes are computed here rather than typed, for the reason
`armtools/verify_provenance.py` exists: a manifest whose digests were written by
hand records what someone believed was delivered, not what was.

    python runs/20260804T1600Z-A32-DESK-DISCARD/make_manifest.py
"""

import hashlib
import io
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ARM = os.path.dirname(os.path.dirname(HERE))

SKIP = {"MANIFEST.json"}


def sha256(path):
    h = hashlib.sha256()
    with io.open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args):
    return subprocess.check_output(("git",) + args, cwd=ARM,
                                   encoding="utf-8").strip()


def main():
    files = []
    for root, _dirs, names in os.walk(HERE):
        for name in sorted(names):
            if name in SKIP:
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, HERE).replace(os.sep, "/")
            files.append({"path": rel, "bytes": os.path.getsize(full),
                          "sha256": sha256(full)})
    files.sort(key=lambda f: f["path"])

    manifest = {
        "prompt_id": "A32-desk-discard-classes-and-cache-premium",
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "base_commit": git("rev-parse", "HEAD"),
        "utc": "2026-08-04T16:00:00Z",
        "territory": "theoria-arm",
        "lane": "campaign",
        "leg": "offline forensics and repair -- no model call, no API call, no spend",
        "seed": None,
        "spend": {"usd": 0.0, "model_calls": 0,
                  "note": "reads archived records only; the repaired paths are "
                          "replayed against transcripts already on disk"},
        "sealed_pile_contact": (
            "none -- every leg read is a development-pile game, and nothing "
            "under environment_files/ was opened"),
        "built_by": [
            "armtools/desk_discard.py (new) -- the discard census and the replay",
            "armtools/cache_premium.py (new) -- the TTL and break-even arithmetic",
            "harness/replywholeness.py (new) -- the transport-loss detector",
            "armtools/replyloss.py -- the start-of-reply classifier, used as given",
        ],
        "inputs": [
            "runs/*/desk/*.md -- 104 archived desk transcripts",
            "runs/*/desk_log.json -- 103 priced calls with usage blocks",
            "runs/*/ledger.jsonl -- the CLI envelopes, read only for maxOutputTokens",
            "runs/*/theorize.json -- the beat's own round records, read for corroboration",
        ],
        "changed_outside_this_run": [
            "inner/theorize.py -- tolerant marker read as a fragment, block "
            "salvage, truthful truncation complaint, identical-prompt guard",
            "harness/modelcall.py -- records messages_dropped per call and "
            "exposes last_messages_dropped",
            "tests/test_desk_discard.py (new) -- 31 checks, each with its "
            "negative control in the same block",
        ],
        "not_done": [
            "the transport repair itself (--output-format stream-json). It "
            "cannot be verified offline against a live CLI and "
            "harness/modelcall.py is on the path of the A26b round running now. "
            "$13.6544 of total loss stays open and is named as open.",
        ],
        "files": files,
        "what": (
            "The 74% was five defects wearing one sentence. Over 104 archived "
            "desk transcripts and $147.5803 of spend, $52.0245 (35.3%) bought a "
            "reply the arm did not use -- but the largest slice is the beat, "
            "not the transport: $35.5789 across 11 calls arrived carrying a "
            "complete PLAYBOOK and 19-31 adjudications each and was discarded "
            "whole for want of a THEORY block. The transport-loss discriminator "
            "is arithmetic the arm already had: output_tokens minus "
            "iterations[-1].output_tokens is zero or an exact multiple of the "
            "model's own 64000-token ceiling on all 103 calls, no remainder, 19 "
            "calls affected. The repair loop paid for a byte-identical prompt 11 "
            "times ($9.1993 billed), every one labelled round3, because the "
            "missing-THEORY complaint was a constant string. Replayed offline, "
            "the repaired paths recover 299 adjudications and 10 playbooks from "
            "$38.3701 of the $52.0245 (73.8%) and no manual at all -- a "
            "truncated manual is deliberately refused rather than written. "
            "Separately: every one of the 4,058,283 cached tokens the arm has "
            "ever written went in at the ONE-HOUR TTL, cache_read is non-zero on "
            "20 of 103 calls and 19 of those are within-call continuations, and "
            "at a read/write ratio of 0.169 against break-evens of 1.11 (1h) and "
            "0.28 (5m) prompt caching is a net loss at either TTL -- $17.1984, "
            "11.7% of the bill. Three of the four cache levers belong to the "
            "CLI; the one the arm holds is the token count, and deskdiet's two "
            "knobs that shrink it defaulted OFF on every leg in this archive."),
    }

    with io.open(os.path.join(HERE, "MANIFEST.json"), "w",
                 encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("wrote MANIFEST.json with %d files" % len(files))


if __name__ == "__main__":
    main()
