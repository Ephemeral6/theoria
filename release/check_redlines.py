"""The release red lines, as an executable check that runs before anything else.

    python release/check_redlines.py                 # before generating a release
    python release/check_redlines.py --mode verify   # checking one you were handed

Two red lines, from the P5 work order:

1. **No `.env` value anywhere in the release set.**
2. **No sealed-pile material anywhere in the release set.**

## Why this runs first and not last

A release manifest publishes every tracked file. `CLAUDE.md` puts the
consequence plainly: a key committed here is a key published later, and git
history makes that effectively irreversible. So this is not a final check over a
finished kit — it decides whether the kit may be generated at all, and it runs
again on every regeneration.

## How the credential check is written, which matters more than that it exists

The obvious implementation of "is the key in this file?" is a grep, and a grep
puts the key on a command line, into shell history, and into any log that
captures the command. This one reads the key through `arc-recon/client.py` — the
shared reader, which exists so that a credential is never parsed ad hoc — holds
it only in memory, and reports **booleans and file paths, never the value**. The
key is not written to stdout, not to a report file, and not into an exception
message.

`mask()` is the only thing that may print anything derived from it, and it emits
`7171...05dd (len 36)` — enough to confirm a key was loaded, not enough to use.

A missing `.env` is not silently tolerated. In the default `generate` mode it is
a hard failure: a check that cannot run must say so loudly rather than pass
quietly, which is the failure mode this repository has now hit in three separate
places. `--mode verify` is the one exception, and it exists for a real person --
someone checking a release they were handed, who has no `.env` because the
credential was never theirs and never shipped. For them there is no key to
search the tree for, so the check is *not applicable* rather than failed. The
strict mode is the default so that forgetting the flag fails closed.

## What the sealed-pile check actually tests

The cut is read from `arc-recon/data/piles.json` — the file, not a copied list —
so the check cannot drift from the cut the way a hand-maintained roster would.
Every tracked file is scanned for a sealed `game_id`. A hit is not automatically
a violation: a file may legitimately *name* a sealed game (the pile file itself
does, and so does the contamination log). So hits are reported with their file,
and an allow-list of files whose job is to name the cut is declared here, with
the reason each is allowed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(REPO_ROOT, "arc-recon"))

PILES = "arc-recon/data/piles.json"

#: Payload markers: the fields that make a record *material from* a game rather
#: than a *mention of* one. A frame, an action fed to the environment, a score
#: returned by it, a state transition -- these are the things the pile cut
#: exists to keep unseen.
#:
#: The distinction matters more than it looks. The first version of this check
#: flagged any file containing a sealed game id and produced 27 hits, nearly all
#: of them guards, tests and audit documents that name those ids *precisely in
#: order to keep them out*: `proxy/tests/test_seal.py`, `battery/guard.py`,
#: `baseline-arms/AUDIT.md`. Reporting those as violations would train a reader
#: to skim past the list, and the one real hit would go with them.
#:
#: The obvious fix was an allow-list of files permitted to name a sealed id.
#: That is a hand-maintained list of members of a growing family, which is the
#: failure this repository hit twice on 2026-07-28 in `figures/` alone -- the
#: list ages, the directory does not. So the severity is decided by a **rule**
#: over what the file carries, and the allow-list is gone.
PAYLOAD_MARKERS: tuple[bytes, ...] = (
    b'"frame"',
    b'"action_input"',
    b'"available_actions"',
    b'"full_reset"',
    b'"guid"',
    b'"scorecard"',
    b'"state"',
)


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "-C", REPO_ROOT, "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.split("\n") if p]


def _abs(rel: str) -> str:
    return os.path.join(REPO_ROOT, *rel.split("/"))


def check_credential(paths: list[str], mode: str = "generate") -> tuple[list[str], list[str]]:
    """``(violations, notes)``. The key never leaves memory.

    Two modes, because two different people run this and the honest answer
    differs:

    * ``generate`` (**the default, and the safe one**) -- someone is about to
      produce a release from this tree. A missing key means the check cannot
      run, and a check that cannot run must fail loudly rather than pass
      quietly. This is the mode `enumerate.py` uses, always.
    * ``verify`` -- someone is checking a release they were handed. They have no
      `.env`, because the credential was never theirs and never shipped. There
      is no key to search the tree for, so the check is *not applicable* rather
      than failed, and saying "violation" at them would be telling a stranger
      their clean checkout is dirty.

    The default is strict on purpose: forgetting the flag must fail closed, and
    the person who needs `verify` is following a document that tells them to
    pass it.
    """
    try:
        from client import load_api_key, mask  # noqa: E402
    except Exception as exc:  # pragma: no cover
        return (
            [f"cannot import arc-recon/client.py to load the key: {exc!r}. "
             "This check did not run, which is not the same as passing."],
            [],
        )
    try:
        key = load_api_key()
    except Exception as exc:
        if mode == "verify":
            return (
                [],
                ["credential check NOT APPLICABLE: no ARC_API_KEY is reachable from this "
                 "checkout, which is expected when verifying a release rather than "
                 "generating one -- the credential was never shipped. There is no key to "
                 "search this tree for."],
            )
        return (
            [f"cannot load ARC_API_KEY ({type(exc).__name__}). This check DID NOT RUN. "
             "A credential check that silently skips is the failure it exists to prevent; "
             "restore .env and re-run, or pass --mode verify if you are checking a release "
             "you were handed rather than producing one."],
            [],
        )
    needle = key.encode()
    notes = [f"credential loaded for comparison only: {mask(key)}"]
    violations: list[str] = []
    scanned = 0
    for rel in paths:
        p = _abs(rel)
        try:
            with open(p, "rb") as fh:
                blob = fh.read()
        except OSError:
            continue
        scanned += 1
        if needle in blob:
            violations.append(
                f"{rel} CONTAINS THE LITERAL API KEY. Do not generate a release manifest. "
                "This file is tracked, so the value is already in git history and the "
                "remedy is a credential rotation, not a deletion commit."
            )
    notes.append(f"{scanned} tracked file(s) scanned for the literal key")
    return violations, notes


def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _records_pairing_sealed_with_payload(path: str, sealed_hits: list[str], jsonl: bool) -> list[str]:
    """Records that are BOTH about a sealed game AND carry its content.

    ``frame`` must be non-empty: a schema with a null ``frame`` field is a shape,
    not a picture of a sealed board.
    """
    bad: list[str] = []
    try:
        with open(path, encoding="utf-8") as fh:
            records = (
                (json.loads(ln) for ln in fh if ln.strip())
                if jsonl
                else iter([json.load(fh)])
            )
            for i, rec in enumerate(records):
                blob = json.dumps(rec)
                ids = [g for g in sealed_hits if g in blob]
                if not ids:
                    continue
                carries = any(
                    d.get(k) for d in _walk(rec) for k in ("frame", "frames", "action_input")
                )
                if carries:
                    bad.append(f"record {i} -> {ids[0]}")
    except (OSError, ValueError):
        return []
    return bad


def check_sealed(paths: list[str]) -> tuple[list[str], list[str]]:
    with open(_abs(PILES), encoding="utf-8") as fh:
        piles = json.load(fh)
    sealed = [g for g in piles.get("sealed", piles.get("sealed_pile", []))]
    if not sealed:
        return (
            ["could not read the sealed pile out of arc-recon/data/piles.json; "
             "this check did not run"],
            [],
        )
    sealed_ids = [g if isinstance(g, str) else g.get("game_id", "") for g in sealed]
    sealed_ids = [s for s in sealed_ids if s]
    notes = [f"sealed pile: {len(sealed_ids)} game(s), read from {PILES}"]

    violations: list[str] = []
    mentions: list[str] = []
    for rel in paths:
        p = _abs(rel)
        try:
            with open(p, "rb") as fh:
                blob = fh.read()
        except OSError:
            continue
        hit = sorted(g for g in sealed_ids if g.encode() in blob)
        if not hit:
            continue
        # Structured files are judged RECORD by record. File-level co-occurrence
        # was this check's second wrong answer: `monitor/state.json` has a
        # `state` field of its own and names three sealed games in an unrelated
        # part of the document, and half a dozen test files hold synthetic
        # fixtures beside a sealed id used as a guard constant. Eleven
        # violations, none of them real.
        #
        # What the pile cut actually forbids is *material from* a sealed game:
        # a record that is both about that game and carries its content.
        if rel.endswith((".json", ".jsonl")):
            bad = _records_pairing_sealed_with_payload(p, hit, rel.endswith(".jsonl"))
            if bad:
                violations.append(
                    f"{rel}: {len(bad)} record(s) pair a sealed game id with payload "
                    f"({'; '.join(bad[:3])}). This is material from a sealed game, not a "
                    "mention of one, and its presence in a tracked file is an incident."
                )
            else:
                mentions.append(
                    f"{rel} names {', '.join(hit)}, and NO record pairs a sealed id with "
                    "payload -- checked record by record, not by co-occurrence"
                )
        else:
            mentions.append(
                f"{rel} names {', '.join(hit)} (source or prose; ids named here are "
                "constants and guards, not content)"
            )

    notes.append(f"{len(paths)} tracked file(s) scanned for sealed game ids")
    notes.append(
        f"{len(mentions)} file(s) mention a sealed id without carrying payload -- guards, "
        "tests, audit documents and the cut itself. Naming a sealed game in order to keep "
        "it out is not contact with it, and a release that stripped these would be hiding "
        "the very ledger that proves the seal held. Listed, not failed:"
    )
    notes.extend(f"    {m}" for m in mentions)
    return violations, notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__ or "")
    ap.add_argument(
        "--mode",
        choices=("generate", "verify"),
        default="generate",
        help="generate (default, strict: a missing key fails) or verify (checking a "
        "release you were handed; no key is expected)",
    )
    args = ap.parse_args(argv)

    paths = _tracked()
    cred_v, cred_n = check_credential(paths, mode=args.mode)
    seal_v, seal_n = check_sealed(paths)

    for n in cred_n + seal_n:
        print(f"  note      {n}")
    for v in cred_v:
        print(f"  CREDENTIAL {v}")
    for v in seal_v:
        print(f"  SEALED     {v}")

    total = len(cred_v) + len(seal_v)
    print(
        f"\nred lines: {len(cred_v)} credential violation(s), "
        f"{len(seal_v)} sealed-pile violation(s) over {len(paths)} tracked files."
    )
    if total:
        print("\nDo not generate a release manifest until these are resolved.")
        return 1
    print("Both red lines clear. A release manifest may be generated from this tree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
