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

## Unreadable is not clean

There are three answers this check can give about a file, and the third one is
the one it kept losing: **violation**, **no finding**, and **could not decide**.
Every path that could not read, could not parse, or could not recognise a file
used to collapse into "no finding" -- `except OSError: continue`, `return []` --
and a green light came out the other end.

`enumerate.py` had already written the right answer next door: `_records_pairing`
returns `None` for a file it cannot parse, and the caller turns that into class
`?` / `needs_human`. One package, two behaviours, and the correct one was never
referenced by the other. So the judgement now lives in exactly one place --
`read_bytes`, `read_json_records`, `json_shaped` below -- and both files call it.
Two implementations of the same rule always drift; this repository has paid that
bill more than once.

Three consequences worth naming, because each was a way through the gate:

* **A file that will not open is reported, not skipped.** It also no longer
  inflates the coverage note: that note used to print `len(paths)`, the number of
  files the check was *handed*, while the loop had quietly skipped some of them.
* **A partial finding is never discarded into silence.** A `.jsonl` whose line 1
  pairs a sealed id with a frame and whose line 5000 is malformed used to return
  `[]` -- the accrued violation thrown away along with the parse error.
* **A file is judged by its bytes, not by its name.** The old code concluded
  "source or prose; ids named here are constants and guards" from the suffix
  alone, so a frame-bearing JSONL named `.log` was asserted innocent without a
  parse ever being attempted. `json_shaped` sniffs the content instead.

`needs_human` is not a softer violation. It fails the gate exactly as hard --
main() exits non-zero on either -- because the whole point is that a check which
could not run must not be reported as a check that passed.
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


def read_bytes(path: str) -> tuple[bytes | None, str | None]:
    """``(blob, None)`` or ``(None, reason)``. Never ``(b"", reason)``.

    The empty-bytes fallback is the specific mistake being designed out:
    `enumerate.build` used to answer an `OSError` with `blob = b""`, and an empty
    blob names no game, carries no marker and classifies as **A / releasable**
    with the evidence string "no ARC game id appears in this file" -- a positive
    claim about bytes nobody read.
    """
    try:
        with open(path, "rb") as fh:
            return fh.read(), None
    except OSError as exc:
        return None, f"{type(exc).__name__}: {exc}"


def read_json_records(path: str, jsonl: bool) -> tuple[list | None, str | None]:
    """``(records, None)`` or ``(None, reason)``. Never ``([], reason)``.

    THE decision this package shares. `[]` means "read it, found nothing";
    `None` means "did not read it", and the two must never be spelled the same
    way. `UnicodeDecodeError` is a `ValueError` subclass, so a non-UTF-8 file
    lands here too -- which is the case `check_redlines` used to swallow.

    Records are materialised eagerly on purpose. The old code parsed lazily
    inside a generator, so a malformed line thousands of records in unwound the
    loop and discarded every finding already made.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            if not jsonl:
                return [json.load(fh)], None
            records = []
            for i, line in enumerate(fh, 1):
                if line.strip():
                    try:
                        records.append(json.loads(line))
                    except ValueError as exc:
                        return None, f"line {i}: {type(exc).__name__}: {exc}"
            return records, None
    except (OSError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


#: A file is JSON-shaped if it is *named* like JSON or *reads* like it. The
#: suffix alone was the old test, and it let the check assert innocence from a
#: filename: a JSONL of frames named `.log`, `.ndjson` or nothing at all took the
#: "source or prose" branch without a parse ever being attempted.
JSON_SUFFIXES = (".json", ".jsonl")


def json_shaped(rel: str, blob: bytes) -> tuple[bool, bool]:
    """``(is_json_shaped, treat_as_jsonl)`` from the name *and* the bytes.

    The name alone was the old test, and it let the check assert innocence from
    a filename: a JSONL of frames named `.log`, `.ndjson` or nothing at all took
    the "source or prose" branch without a parse ever being attempted.

    Sniffing the first byte alone is not enough either, in the other direction.
    A Markdown file may open with a link reference -- `[spec]: ./spec.md` -- and
    handing that to the JSON reader produces a parse failure, which is now
    `needs_human`, which is a **false red on a prose file**. A gate that reddens
    on ordinary documents is one somebody switches off, and then the true reds go
    with it. So a file that merely *opens* like JSON has to show more evidence
    than its first character before it is judged as JSON.
    """
    if rel.endswith(JSON_SUFFIXES):
        return True, rel.endswith(".jsonl")
    if blob.lstrip()[:1] not in (b"{", b"["):
        return False, False
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        # Opens like JSON and is not even text, in a file that names a sealed
        # game. Whatever it is, nothing has read it: undetermined, not prose.
        return True, True
    # A stream of JSON documents: two or more whole lines that parse. One is not
    # enough -- a fenced `{}` inside a Markdown code block would qualify.
    parsed = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            json.loads(line)
        except ValueError:
            continue
        parsed += 1
        if parsed >= 2:
            return True, True
    try:
        json.loads(text)
    except ValueError:
        # Opens like JSON, is valid text, and is not JSON. That is prose.
        return False, False
    return True, False


def _tracked() -> list[str]:
    out = subprocess.run(
        ["git", "-C", REPO_ROOT, "ls-files"], capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.split("\n") if p]


def _abs(rel: str) -> str:
    return os.path.join(REPO_ROOT, *rel.split("/"))


def check_credential(
    paths: list[str], mode: str = "generate"
) -> tuple[list[str], list[str], list[str]]:
    """``(violations, needs_human, notes)``. The key never leaves memory.

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
            [],
        )
    try:
        key = load_api_key()
    except Exception as exc:
        if mode == "verify":
            return (
                [],
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
            [],
        )
    needle = key.encode()
    notes = [f"credential loaded for comparison only: {mask(key)}"]
    violations: list[str] = []
    needs_human: list[str] = []
    scanned = 0
    for rel in paths:
        blob, why = read_bytes(_abs(rel))
        if blob is None:
            needs_human.append(
                f"{rel} could not be opened ({why}), so it has NOT been searched for the "
                "literal key. This is a tracked file: it ships in the manifest whether or "
                "not this check could read it."
            )
            continue
        scanned += 1
        if needle in blob:
            violations.append(
                f"{rel} CONTAINS THE LITERAL API KEY. Do not generate a release manifest. "
                "This file is tracked, so the value is already in git history and the "
                "remedy is a credential rotation, not a deletion commit."
            )
    notes.append(
        f"{scanned} of {len(paths)} tracked file(s) scanned for the literal key"
        + (f"; {len(needs_human)} could not be opened" if needs_human else "")
    )
    return violations, needs_human, notes


def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk(v)


def _records_pairing_sealed_with_payload(
    path: str, sealed_hits: list[str], jsonl: bool
) -> tuple[list[str] | None, str | None]:
    """Records that are BOTH about a sealed game AND carry its content.

    ``(bad, None)``, or ``(None, reason)`` when the file could not be read --
    never ``([], reason)``. The old signature had no way to say the third thing,
    so it said the second, and the caller printed "NO record pairs a sealed id
    with payload -- checked record by record" about a file it had never parsed.

    ``frame`` must be non-empty: a schema with a null ``frame`` field is a shape,
    not a picture of a sealed board.
    """
    records, why = read_json_records(path, jsonl)
    if records is None:
        return None, why
    bad: list[str] = []
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
    return bad, None


def check_sealed(paths: list[str]) -> tuple[list[str], list[str], list[str]]:
    """``(violations, needs_human, notes)``."""
    with open(_abs(PILES), encoding="utf-8") as fh:
        piles = json.load(fh)
    sealed = [g for g in piles.get("sealed", piles.get("sealed_pile", []))]
    if not sealed:
        return (
            ["could not read the sealed pile out of arc-recon/data/piles.json; "
             "this check did not run"],
            [],
            [],
        )
    sealed_ids = [g if isinstance(g, str) else g.get("game_id", "") for g in sealed]
    sealed_ids = [s for s in sealed_ids if s]
    # A non-empty pile that yields no usable ids means the cut file changed shape
    # under this reader. The guard above only catches an *empty* pile, so this
    # case used to sail through and scan every tracked file for an empty list of
    # ids -- 2817 files, zero hits, "Both red lines clear."
    if len(sealed_ids) != len(sealed):
        return (
            [f"arc-recon/data/piles.json lists {len(sealed)} sealed entries but only "
             f"{len(sealed_ids)} yielded a game id; the cut file is not the shape this "
             "reader expects and the sealed check DID NOT RUN over the whole pile"],
            [],
            [],
        )
    notes = [f"sealed pile: {len(sealed_ids)} game(s), read from {PILES}"]

    violations: list[str] = []
    needs_human: list[str] = []
    mentions: list[str] = []
    scanned = 0
    for rel in paths:
        blob, why = read_bytes(_abs(rel))
        if blob is None:
            needs_human.append(
                f"{rel} could not be opened ({why}), so it has NOT been checked for sealed "
                "material. A tracked file this check could not read is not a tracked file "
                "with nothing in it."
            )
            continue
        scanned += 1
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
        structured, jsonl = json_shaped(rel, blob)
        if structured:
            bad, why = _records_pairing_sealed_with_payload(_abs(rel), hit, jsonl)
            if bad is None:
                needs_human.append(
                    f"{rel} names {', '.join(hit)} and could NOT be parsed ({why}), so no "
                    "record in it has been judged. An unparseable file that names a sealed "
                    "game is the one case where 'no finding' and 'did not look' are easiest "
                    "to confuse and most expensive to get wrong."
                )
            elif bad:
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

    # `scanned`, not `len(paths)`. The old note counted the files this check was
    # *handed* while the loop had silently skipped some of them, so the coverage
    # figure was guaranteed to be right only when nothing had gone wrong.
    notes.append(
        f"{scanned} of {len(paths)} tracked file(s) scanned for sealed game ids"
        + (f"; {len(needs_human)} could not be read or parsed" if needs_human else "")
    )
    notes.append(
        f"{len(mentions)} file(s) mention a sealed id without carrying payload -- guards, "
        "tests, audit documents and the cut itself. Naming a sealed game in order to keep "
        "it out is not contact with it, and a release that stripped these would be hiding "
        "the very ledger that proves the seal held. Listed, not failed:"
    )
    notes.extend(f"    {m}" for m in mentions)
    return violations, needs_human, notes


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
    cred_v, cred_h, cred_n = check_credential(paths, mode=args.mode)
    seal_v, seal_h, seal_n = check_sealed(paths)

    for n in cred_n + seal_n:
        print(f"  note      {n}")
    for v in cred_v:
        print(f"  CREDENTIAL {v}")
    for v in seal_v:
        print(f"  SEALED     {v}")
    for h in cred_h:
        print(f"  NEEDS HUMAN (credential) {h}")
    for h in seal_h:
        print(f"  NEEDS HUMAN (sealed)     {h}")

    violations = len(cred_v) + len(seal_v)
    unread = len(cred_h) + len(seal_h)
    print(
        f"\nred lines: {len(cred_v)} credential violation(s), "
        f"{len(seal_v)} sealed-pile violation(s), "
        f"{unread} file(s) this check could not read over {len(paths)} tracked files."
    )
    if violations:
        print("\nDo not generate a release manifest until these are resolved.")
        return 1
    # A separate exit code, and deliberately not a separate severity. `needs_human`
    # blocks the release exactly as hard as a violation, because the question it
    # leaves open is the one the gate exists to close. It gets its own code only so
    # that a caller can tell "we found something" from "we could not look" without
    # parsing prose -- the distinction the old `return []` erased.
    if unread:
        print(
            "\nNo violation was found, but this check DID NOT COVER every tracked file, "
            "and a release manifest publishes the files it could not read along with the "
            "ones it could. Resolve or explicitly waive each NEEDS HUMAN line above; "
            "unreadable is not clean."
        )
        return 2
    print("Both red lines clear. A release manifest may be generated from this tree.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
