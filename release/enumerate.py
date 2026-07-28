"""Enumerate the release set, classify it by licence, and hash it.

    python release/enumerate.py            # writes release/MANIFEST.jsonl
    python release/enumerate.py --dry-run  # classify and report, write nothing

Step 2 of `release/PLAN.md`. Produces one JSON object per tracked file:
path, size, sha256, licence class, verdict, and the evidence the verdict rests
on.

## The red lines gate this, not the other way round

`check_redlines.py` runs **first**, and a red result aborts before a single hash
is written. A release manifest publishes every tracked file; `CLAUDE.md` records
that a key committed here is a key published later and that git history makes
that effectively irreversible. Generating the manifest is therefore the
consequential step, and it does not happen over a tree that has not been
cleared.

## Classification is a rule over evidence, never a list of paths

The tempting implementation is a table mapping directories to licence classes.
This repository broke that pattern three times on 2026-07-28 alone -- twice in
`figures/`, where hand-written tuples of source keys fell behind their
directories and two runs' evidence silently left a plate, and once in this
directory's own red-line check, whose first fix was going to be an allow-list.
A path table ages; the tree does not stop growing.

So each file is classified by **what it contains**:

* **D — upstream payload.** Third-party material whose own licence is absent.
  `SCHEMA_PATH_A.md` §7 records the upstream HF dataset as declaring no licence
  at all, and silence is not a grant.
* **B — API-derived compilation.** The file carries a record that pairs an ARC
  `game_id` with environment payload (a frame, an action fed to the environment,
  a scorecard body), or it is a log of API transactions. This is what ToS §4's
  first prohibited activity calls "a collection, compilation, database", and
  `browser-ops/TERMS.md` §2.2 rules that internal analysis is fine and public
  release is the line.
* **C — statistics derived from B.** The file mentions ARC games but carries no
  environment payload: counts, means, metric cells, CSV audit surfaces.
* **A — self-built.** Everything else. Nothing in it was retrieved from the
  Services. This is the bulk of the repository and the part carrying the
  research claim -- including every synthetic world, whose traces contain
  `frame` fields that are *ours*, drawn by our own generators, and are not ARC
  content in any sense.

The distinction between A and B is exactly "does an ARC `game_id` appear in the
same record as the payload" -- which is why `cold-start-a0`'s traces are class A
despite being full of frames, and `baseline-arms/ledger.jsonl` is class B.

## Where the rule cannot decide, it says so

A file that mentions an ARC game and carries payload the parser cannot read --
a binary, an unparseable JSON -- is `needs_human`, never a guess. A release kit
that quietly excluded something is as wrong as one that quietly included it, and
only one of those two is recoverable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import check_redlines as redlines  # noqa: E402

MANIFEST = os.path.join(_HERE, "MANIFEST.jsonl")

#: Environment payload: the fields that make a record *material from* a game.
PAYLOAD_KEYS = ("frame", "frames", "action_input", "available_actions")

#: Markers of an API transaction log, independent of game id -- a probe log of
#: requests is a compilation of retrieved data even where a record names no game.
API_TRANSACTION_MARKERS = (b'"X-API-Key"', b"arcprize.org/api", b'"kind": "arc_api_call"')

#: Upstream third-party payload, by the only thing that identifies it: where the
#: upstream dropped it. This IS a path, and it is the one place a path is right:
#: the class is defined by provenance, not by content, and the content is
#: gitignored so no rule could read it.
UPSTREAM_PAYLOAD_PREFIX = "baseline-arms/schema_traces/"

CLASSES = {
    "A": ("self-built", "releasable"),
    "B": ("api-derived-compilation", "needs-written-permission"),
    "C": ("derived-statistics", "releasable-flagged"),
    "D": ("upstream-payload", "not-releasable"),
    "?": ("undetermined", "needs_human"),
}


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "-C", REPO_ROOT, "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    return sorted(p for p in out.split("\n") if p)


def _abs(rel: str) -> str:
    return os.path.join(REPO_ROOT, *rel.split("/"))


def _sha256(path: str) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
            size += len(chunk)
    return h.hexdigest(), size


def _arc_game_ids() -> list[str]:
    with open(_abs("arc-recon/data/piles.json"), encoding="utf-8") as fh:
        piles = json.load(fh)
    ids: list[str] = []
    for family in piles.get("strata", {}).values():
        ids.extend(family)
    return sorted(set(ids))


def classify(rel: str, blob: bytes, game_ids: list[str]) -> dict:
    """``{class, verdict, evidence}``. Never guesses."""
    if rel.startswith(UPSTREAM_PAYLOAD_PREFIX):
        return {
            "class": "D",
            "evidence": "under baseline-arms/schema_traces/; upstream declares no licence "
            "(SCHEMA_PATH_A.md 7), and silence is not a grant",
        }

    # The transaction-log rule applies to DATA files only. Source code that sets
    # an `X-API-Key` header, and prose that quotes the terms, both contain the
    # marker and neither is a compilation of retrieved data. The first version of
    # this rule put `arc-recon/client.py`, `proxy/env_proxy.py`,
    # `baseline-arms/harness/arc_client.py` and `browser-ops/TERMS.md` into the
    # needs-permission class -- our own code and our own licence analysis,
    # withheld from a release on the grounds that they mention the header they
    # exist to set. Mention is not material; that distinction has now been the
    # answer three times in this directory.
    if rel.endswith((".json", ".jsonl")):
        for marker in API_TRANSACTION_MARKERS:
            if marker in blob:
                return {
                    "class": "B",
                    "evidence": f"data file carrying API transaction marker "
                    f"{marker.decode()!r}: a log of retrieved data is a compilation under "
                    "ToS 4 regardless of which games it names",
                }

    named = sorted(g for g in game_ids if g.encode() in blob)
    if not named:
        return {"class": "A", "evidence": "no ARC game id appears in this file"}

    if not rel.endswith((".json", ".jsonl")):
        return {
            "class": "C",
            "evidence": f"names ARC game(s) {', '.join(named)} in source or prose; ids used as "
            "constants, guards or narrative carry no environment payload",
        }

    verdict = _records_pairing(_abs(rel), named, rel.endswith(".jsonl"))
    if verdict is None:
        return {
            "class": "?",
            "evidence": f"names ARC game(s) {', '.join(named)} but could not be parsed as "
            "JSON, so whether it carries environment payload is undetermined",
        }
    if verdict:
        return {
            "class": "B",
            "evidence": f"{verdict} record(s) pair an ARC game id with environment payload "
            f"({', '.join(PAYLOAD_KEYS)})",
        }
    return {
        "class": "C",
        "evidence": f"names ARC game(s) {', '.join(named)}; no record pairs an id with "
        "environment payload -- statistics about the games, not material from them",
    }


def _is_payload(value) -> bool:
    """Is this value environment payload, or a field that merely shares its name?

    An ARC frame is a **grid**: a list of rows of ints. `action_input` is a
    structured object. Neither is ever a sentence.

    Testing truthiness of a key called `frame` was this enumerator's second wrong
    answer, and it was a quiet one. `battery/artifacts/capability_spectrum.json`
    carries two metric cells whose `frame` field is the *sampling frame*,
    described in prose -- "3 state-action pair(s) the full-history trace never
    covered ...". On the key name alone, the battery's central artefact was
    classified as needing written permission before release: the one file the
    paper's whole capability claim rests on, withheld because a statistician and
    an environment designer chose the same English word.
    """
    return isinstance(value, (list, dict)) and bool(value)


def _records_pairing(path: str, named: list[str], jsonl: bool) -> int | None:
    """Count of records pairing an ARC id with payload; ``None`` if unparseable."""
    try:
        with open(path, encoding="utf-8") as fh:
            records = (
                (json.loads(ln) for ln in fh if ln.strip()) if jsonl else iter([json.load(fh)])
            )
            n = 0
            for rec in records:
                blob = json.dumps(rec)
                if not any(g in blob for g in named):
                    continue
                if any(_is_payload(d.get(k)) for d in redlines._walk(rec) for k in PAYLOAD_KEYS):
                    n += 1
            return n
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def _review_note(rel: str, blob: bytes, cls: str) -> str | None:
    """Flag a class-B file that looks synthetic rather than retrieved.

    `battery/tests/fixtures/ledger_fixture.jsonl` is the live case: it carries
    4x4 frames and a real dev-pile `game_id`, and it is written by
    `battery/tests/make_fixture.py`. Nothing in it came from the Services, so on
    provenance it is class A -- but nothing in the *file* proves that, and
    mistaking retrieved data for synthetic is the one error here that cannot be
    walked back.

    So the rule does not reclassify. It keeps the cautious verdict and makes the
    doubt visible, because the failure to avoid is not "excluded something" but
    "excluded something **silently**". A human overturns this in one line; a
    licence violation in a published manifest is not undone in one line.
    """
    if cls != "B":
        return None
    synthetic = b"-fixture" in blob or b"/fixtures/" in rel.encode() or "/fixtures/" in rel
    if not synthetic:
        return None
    return (
        "CANDIDATE RECLASSIFICATION -> A, human call. This looks synthetic: it lives under "
        "a fixtures path and/or carries `-fixture` run ids, which in this repository means "
        "it was written by a tracked generator rather than retrieved from the Services. "
        "Held at B because provenance cannot be proven from the file alone, and mistaking "
        "retrieved data for synthetic is the error that cannot be undone."
    )


def build(paths: list[str]) -> list[dict]:
    game_ids = _arc_game_ids()
    rows: list[dict] = []
    for rel in paths:
        p = _abs(rel)
        blob, why = redlines.read_bytes(p)
        if blob is None:
            # Neither `continue` nor `b""`. Both were here, and both answered an
            # unreadable file with a sentence about its contents: `continue`
            # dropped the row so the file left the manifest entirely -- a manifest
            # whose job is to enumerate *every* tracked file, quietly one short --
            # and `b""` classified it A/releasable on the evidence "no ARC game id
            # appears in this file", a positive claim about bytes nobody read.
            rows.append(
                {
                    "path": rel,
                    "sha256": None,
                    "size": None,
                    "class": "?",
                    "class_name": CLASSES["?"][0],
                    "verdict": CLASSES["?"][1],
                    "evidence": f"tracked, but this enumerator could not read it ({why}); "
                    "its licence class is undetermined. It is listed rather than dropped "
                    "because a file missing from the manifest is a file nobody rules on.",
                }
            )
            continue
        try:
            digest, size = _sha256(p)
        except OSError as exc:  # pragma: no cover -- read_bytes already succeeded
            digest, size = None, None
            del exc
        verdict = classify(rel, blob, game_ids)
        name, disposition = CLASSES[verdict["class"]]
        row = {
            "path": rel,
            "sha256": digest,
            "size": size,
            "class": verdict["class"],
            "class_name": name,
            "verdict": disposition,
            "evidence": verdict["evidence"],
        }
        review = _review_note(rel, blob, verdict["class"])
        if review:
            row["review"] = review
        rows.append(row)
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__ or "")
    ap.add_argument("--dry-run", action="store_true", help="classify and report; write nothing")
    ap.add_argument(
        "--mode",
        choices=("generate", "verify"),
        default="generate",
        help="generate (default, strict: a missing credential fails) or verify (checking a "
        "release you were handed; no credential expected). Passed through to the red-line "
        "check.",
    )
    # This flag was accepted only by check_redlines.py while THIS script's abort
    # message told the reader to pass it here. A stranger following
    # REPRODUCING.md hit that dead end on the document's second command: the step
    # failed demanding a credential, the error named a remedy, and the remedy did
    # not parse. An error that advertises a flag the program rejects is worse
    # than one that says nothing.
    args = ap.parse_args(argv)

    paths = _tracked()
    cred_v, cred_h, cred_n = redlines.check_credential(paths, mode=args.mode)
    for _n in cred_n:
        print(f"  note {_n}")
    seal_v, seal_h, _ = redlines.check_sealed(paths)
    # `needs_human` aborts the manifest exactly as a violation does. This
    # enumerator is the one caller that MUST NOT be lenient about it: it is about
    # to write a document asserting a licence class for every tracked file, and a
    # file the red-line check could not read is a file it has no basis to assert
    # anything about.
    if cred_v or seal_v or cred_h or seal_h:
        print("ABORT: the red lines are not clear; no manifest generated.", file=sys.stderr)
        for v in cred_v + seal_v:
            print(f"  {v}", file=sys.stderr)
        for h in cred_h + seal_h:
            print(f"  NEEDS HUMAN {h}", file=sys.stderr)
        # Non-zero even under --dry-run. It used to print ABORT and exit 0, so
        # anything scripting it read a clean pass off a refusal.
        return 2
    print(f"red lines clear over {len(paths)} tracked files")

    rows = build(paths)
    counts: dict[str, int] = {}
    bytes_by: dict[str, int] = {}
    for r in rows:
        counts[r["class"]] = counts.get(r["class"], 0) + 1
        bytes_by[r["class"]] = bytes_by.get(r["class"], 0) + r["size"]
    for cls in sorted(CLASSES):
        if cls not in counts:
            continue
        name, disposition = CLASSES[cls]
        print(
            f"  {cls}  {counts[cls]:5d} file(s)  {bytes_by[cls] / 1e6:8.2f} MB  "
            f"{name} -> {disposition}"
        )

    if args.dry_run:
        print("\ndry run: nothing written")
        return 0

    body = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows) + "\n"
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print(f"\nwrote {os.path.relpath(MANIFEST, REPO_ROOT)} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
