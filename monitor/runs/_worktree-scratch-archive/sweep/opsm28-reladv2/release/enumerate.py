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
#:
#: **Derived, never re-typed.** This was a four-field literal
#: (`frame, frames, action_input, available_actions`) beside
#: `check_redlines.PAYLOAD_MARKERS`, which declares eight. An adversarial review
#: of this very change caught the consequence: widening the constant in
#: `check_redlines` and leaving the literal here reproduced, one level up, the
#: defect this work order is named after -- **the guard went into one of the two
#: readers.** Eleven files carrying `scorecard` or `state` bodies stayed class C
#: under the positive sentence "no record pairs an id with environment payload",
#: and one of them (`theoria-arm/runs/20260728T235841Z-leg01/run.json`) is a
#: literal ARC scorecard response, `card_id` and `guid` and all.
#:
#: `enumerate.py`'s own docstring had already named `scorecard` as class-B
#: payload; only the literal disagreed.
PAYLOAD_KEYS = redlines.PAYLOAD_FIELDS

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


class PileCutUnreadable(RuntimeError):
    """The cut file is not the shape this reader expects, so nothing was read.

    Raised, never warned. Every classification below `classify`'s first branch is
    a statement about which ARC games a file names, and with no ids to look for
    the only statement it can make is "none" -- for every file, in the permissive
    direction. A classifier that cannot read its own id list must not produce a
    verdict at all.
    """


def _cut_pile(piles: dict, *keys: str) -> list[str]:
    """One pile out of the cut file, as game ids. Same reader as `check_sealed`.

    Entries are strings today and may be objects tomorrow; both spellings are
    accepted, and an entry that yields no id is dropped here so the caller's
    count comparison sees the shortfall.
    """
    entries: list = []
    for key in keys:
        if key in piles:
            entries = piles[key] or []
            break
    ids = [g if isinstance(g, str) else g.get("game_id", "") for g in entries]
    return [g for g in ids if g]


def _arc_game_ids() -> list[str]:
    """Every ARC game id in the cut. Refuses rather than returning a short list.

    This used to be `piles.get("strata", {})` and a comprehension, and the
    combination has no failure mode: a missing or renamed key is swallowed into
    an empty dict, the comprehension over an empty dict is a legal empty list,
    and `classify` then finds no game id in any file and falls through to
    **class A / releasable** with the evidence "no ARC game id appears in this
    file" -- a positive claim, on a tree nothing was searched for. Measured on
    this repository at base 7852ef3: 37 files B -> A and 247 files C -> A, all
    of them into the class that ships.

    `check_redlines.check_sealed` already carries this guard, and the comment
    beside it records what the missing version did: it "scanned 2817 files with
    an empty id list and then printed `Both red lines clear`". The guard went
    into one of the two id readers and not the other, which is the drift this
    package keeps paying for -- so this one is written to the same shape.

    The cross-check is between two independent statements the cut file makes
    about itself: `strata` partitions the public set by tag family, and
    `dev_pile` / `sealed_pile` partition the same set by the cut. They must
    describe the same games. Comparing the *sets* rather than only the counts is
    deliberate -- a renamed id keeps the count and changes the answer.
    """
    with open(_abs(redlines.PILES), encoding="utf-8") as fh:
        piles = json.load(fh)

    dev = _cut_pile(piles, "dev", "dev_pile")
    sealed = _cut_pile(piles, "sealed", "sealed_pile")
    if not dev or not sealed:
        raise PileCutUnreadable(
            f"{redlines.PILES} yielded {len(dev)} development and {len(sealed)} sealed "
            "game id(s); the cut this enumerator classifies against is unreadable, so NO "
            "file has been classified. This is a refusal, not a finding: with an empty id "
            "list every tracked file classifies as A / releasable on the evidence that no "
            "ARC game id appears in it."
        )

    ids: list[str] = []
    for family in piles.get("strata", {}).values():
        ids.extend(g if isinstance(g, str) else g.get("game_id", "") for g in family)
    ids = sorted({g for g in ids if g})

    cut = sorted(set(dev) | set(sealed))
    if len(ids) != len(dev) + len(sealed) or ids != cut:
        raise PileCutUnreadable(
            f"{redlines.PILES} is not the shape this reader expects: its strata yield "
            f"{len(ids)} game id(s) while the cut declares {len(dev)} development + "
            f"{len(sealed)} sealed = {len(dev) + len(sealed)}"
            + (f" (differing on {', '.join(sorted(set(ids) ^ set(cut)))})"
               if set(ids) ^ set(cut) else "")
            + ". The id list this enumerator classifies against DID NOT LOAD, and every "
            "file it would have ruled on is unclassified rather than releasable."
        )
    return ids


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
    #
    # `json_shaped`, not `rel.endswith((".json", ".jsonl"))`. The suffix test was
    # this enumerator's third wrong answer and it is the one that reads as an
    # assertion: identical bytes were class B named `.jsonl` and class C named
    # `.log`, and the class C branch does not merely decline to rule -- it states
    # that the ids in the file are "constants, guards or narrative" carrying "no
    # environment payload", about a file no parser had opened. `check_redlines`
    # grew `json_shaped` to close exactly this hole, and its docstring says the
    # judgement now lives in one place and "both files call it". This file was the
    # one that did not, so the sentence was true of the module and false of the
    # package.
    structured, jsonl = redlines.json_shaped(rel, blob)

    # OPSM28 ADVERSARIAL PROBE -- NOT A PROPOSAL, NOT COMMITTED ANYWHERE.
    # `json_shaped` returns (True, True) on a strict-decode failure, and its own
    # docstring scopes that to `check_sealed`, which only reaches it for a file
    # that already matched an id in its raw bytes. `classify` calls it BEFORE the
    # id match, so the precondition does not hold -- and a PDF, which is a stray
    # binary, is judged a record stream. Re-asking the same record question over
    # a lenient decode answers it honestly instead of abstaining.
    if structured and not rel.endswith(redlines.JSON_SUFFIXES):
        try:
            blob.decode("utf-8-sig")
        except UnicodeDecodeError:
            structured, jsonl = redlines.json_shaped(
                rel, blob.decode("utf-8-sig", errors="replace").encode("utf-8"))

    if structured:
        for marker in API_TRANSACTION_MARKERS:
            if marker in blob:
                return {
                    "class": "B",
                    "evidence": f"data file carrying API transaction marker "
                    f"{marker.decode()!r}: a log of retrieved data is a compilation under "
                    "ToS 4 regardless of which games it names",
                }

    # A *negative* conclusion from a byte scan is only worth the encoding it was
    # run over. `g.encode()` builds a UTF-8 needle, and in a UTF-16 file every
    # character carries an interleaved NUL, so no id can ever match -- and the
    # branch below then prints "no ARC game id appears in this file", which is
    # this work order's title sentence, about a comparison that was blind.
    # Demonstrated on five records of `{"game_id": "<dev id>", "frame": [[...]]}`
    # written as UTF-16: class A, releasable, on that exact evidence string.
    #
    # `check_redlines` grew `unsearchable_encoding` for this and wired it into
    # its own two scans. This file did not call it -- the same "true of the
    # module, false of the package" split as defect 3, in the same function,
    # three lines away. An adversarial review of this change found it.
    #
    # Order matters: the API-transaction scan above stays where it is, because a
    # marker that *matched* is a positive finding and blindness cannot make a
    # match false. Only the absence conclusion has to be withheld.
    blind = redlines.unsearchable_encoding(blob)
    if blind:
        return {
            "class": "?",
            "evidence": f"{blind}, so the UTF-8 byte scan that decides which ARC games "
            "this file names could not see its text -- whether it names any is undetermined",
        }

    named = sorted(g for g in game_ids if g.encode() in blob)
    if not named:
        return {"class": "A", "evidence": "no ARC game id appears in this file"}

    if not structured:
        return {
            "class": "C",
            "evidence": f"names ARC game(s) {', '.join(named)} in source or prose; ids used as "
            "constants, guards or narrative carry no environment payload",
        }

    verdict, why = _records_pairing(_abs(rel), named, jsonl)
    if verdict is None:
        # `why` comes from `redlines.read_json_records`, which knows which of
        # several things went wrong. It used to be discarded here and replaced
        # with the flat phrase "could not be parsed as JSON" -- which was wrong
        # for every row it was actually printed over. All three `?` rows on this
        # tree take the *first* early return in `json_shaped`
        # (`blob.decode("utf-8-sig")` raises), so nothing was ever handed to a
        # JSON parser; `pytest-baseline.txt` holds 45 lines of which none begins
        # with `{`, and its only defect is three mojibake byte pairs. A gate that
        # misnames its own reason is the disease this work order is about, so it
        # does not get to have it.
        return {
            "class": "?",
            "evidence": f"names ARC game(s) {', '.join(named)} but {why}, so whether it "
            "carries environment payload is undetermined",
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


def _records_pairing(path: str, named: list[str], jsonl: bool) -> tuple[int | None, str | None]:
    """``(count, None)`` of records pairing an ARC id with payload, or ``(None, why)``.

    The reason travels with the refusal, as it already did in
    `check_redlines._records_pairing_sealed_with_payload`. Returning a bare
    `None` let the caller substitute a reason of its own invention -- it printed
    "could not be parsed as JSON" over three files that never reached a JSON
    parser, because `json_shaped` had already refused them at
    `blob.decode("utf-8-sig")`. Misnaming the reason a gate went red is how the
    gate gets cleared by someone fixing the wrong thing.

    The `None` was already right here when `check_redlines` was still answering
    the same question with `[]`. What was wrong is that it was right *separately*
    -- its own `try`, its own tuple of exception types, one package holding two
    implementations of one rule. That is the arrangement that produced the split
    in the first place, so reading through `redlines.read_json_records` is the
    part of this that has to hold: whichever way the rule moves next, it moves
    once.

    It also inherits the eager read, which fixes a defect this copy shared: the
    lazy generator unwound on a malformed line thousands of records in, throwing
    away every count already made.
    """
    records, why = redlines.read_json_records(path, jsonl)
    if records is None:
        return None, why
    n = 0
    for rec in records:
        blob = json.dumps(rec, default=str)
        if not any(g in blob for g in named):
            continue
        if _pairs_in_scope(rec, named):
            n += 1
    return n, None


def _pairs_in_scope(rec, named: list[str]) -> bool:
    """Does this record pair an id with payload *the record ties to that id*?

    The old test was `any(g in json.dumps(rec))` and then a payload field
    **anywhere beneath the record**. That is co-occurrence with an extra step,
    and `check_redlines._pairings` was rewritten on this same branch to stop
    doing exactly it -- with the reason written down: record-level pairing reads
    as record-by-record only while records are small, and a whole-document
    `.json` parses as exactly ONE record, at which point "record by record"
    degrades into "somewhere in this file". Leaving the loose version here would
    have been the third pair of drifting readers this work order produced.

    So the scope comes from `redlines._walk_scoped`: an id owns a payload field
    when it is named in that node's own scalar fields or an ancestor's, or when
    it is **inside the payload value itself** (a scorecard keyed by game id names
    no sibling `game_id`).

    What deliberately does **not** come from `check_redlines` is the fill test.
    `_filled` there counts `False` and `"a sentence"` as present, because
    `"full_reset": false` is a real command sent to a real game and the sealed
    red line must see it. Here the question is a licence class, and
    `battery/artifacts/capability_spectrum.json` carries a `frame` field holding
    a *sampling* frame described in prose. Two different questions, two
    justified answers -- and the difference is written down here so that the
    next person to notice it finds a reason rather than a drift.
    """
    for node, in_scope in redlines._walk_scoped(rec, named):
        for field in PAYLOAD_KEYS:
            value = node.get(field)
            if not _is_payload(value):
                continue
            if in_scope or any(g in json.dumps(value, default=str) for g in named):
                return True
    return False


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
                    # 0, not None. Every consumer sums this field
                    # (`enumerate.main` and `checklist.report` both do
                    # `total + row["size"]`), so a None here is a TypeError in
                    # two places -- and in `checklist` it lands *before* the
                    # UNDETERMINED verdict can be returned, so the report dies on
                    # a traceback instead of refusing. An unreadable file
                    # contributes no known bytes; `sha256: None` is where the
                    # "unknown" is said, and nothing arithmetic reads that.
                    "size": 0,
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

    # A `?` row is a file this enumerator refused to rule on, and the manifest's
    # whole job is to state a licence class for every tracked file. The rows are
    # still written -- dropping them is the defect above, and a human needs the
    # list -- but the exit code must not say the enumeration succeeded.
    #
    # This is reachable without any unreadable file: an unparseable `.json`
    # naming a *dev-pile* id is invisible to `check_sealed`, which scans only
    # sealed ids, so nothing upstream aborts and the count arrives here.
    undetermined = [r for r in rows if r["class"] == "?"]

    if args.dry_run:
        print("\ndry run: nothing written")
    else:
        body = "\n".join(
            json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows) + "\n"
        with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        print(f"\nwrote {os.path.relpath(MANIFEST, REPO_ROOT)} ({len(rows)} rows)")

    if undetermined:
        print(
            f"\n{len(undetermined)} tracked file(s) could not be classified and are in the "
            "manifest as class ? / needs_human. A licence class has NOT been established "
            "for them, so this enumeration is not a finished manifest:",
            file=sys.stderr,
        )
        for r in undetermined[:20]:
            print(f"  {r['path']}: {r['evidence']}", file=sys.stderr)
        if len(undetermined) > 20:
            print(f"  ... and {len(undetermined) - 20} more", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
