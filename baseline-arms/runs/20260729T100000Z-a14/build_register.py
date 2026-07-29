"""Emit baseline-arms/COST_ARTEFACTS.json.

    cd baseline-arms && python runs/20260729T100000Z-a14/build_register.py --check
    cd baseline-arms && python runs/20260729T100000Z-a14/build_register.py --write

The policy fields (disposition, reason, provenance) are authored here in source;
the digests and byte counts are computed from the files, so no digest is ever
hand-transcribed.  `--check` re-derives the register and diffs it against the
committed one, which is what makes the committed JSON a generated artefact
rather than a hand-maintained list that silently rots.

`--check` is byte-exact on purpose: the register is itself a provenance record,
and "close enough" is not a property a provenance record may have.
"""

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TERRITORY = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(TERRITORY, "COST_ARTEFACTS.json")

BATTERY = "battery/runs/20260728T061147Z-v3/MANIFEST.json"

# The campaign that produced everything below: bare Claude Code, S1
# baseline-parity, haiku tier, over the four development-pile games, run
# 2026-07-27/28.  Per-game spend is read out of the campaign JSONs themselves
# (`cost_usd`), so the numbers here are not a second copy of the money.
CAMPAIGN_RUN = "phase3 bare_cc S1 baseline-parity, 2026-07-27..28, dev pile x 4"

GAMES = ["ar25", "g50t", "sk48", "tn36"]

ENTRIES = []

for g in GAMES:
    ENTRIES.append({
        "path": "out/campaign/campaign_%s.json" % g,
        "disposition": "committed",
        "cost_bearing": "arc-api-spend",
        "produced_by": CAMPAIGN_RUN,
        "consumed_by": [BATTERY + "#input_digests"],
        "reason":
            "The per-game roll-up of a paid campaign, and the only source for "
            "the bare-CC column of the main table. battery already cites its "
            "sha256 as evidence, so the question of whether it belongs in the "
            "repository was settled before A14 asked it. 4.5 kB.",
        "eol": "crlf",
        "eol_note":
            "Written by the harness in Python text mode on Windows. The pinned "
            "digest is over these CRLF bytes; .gitattributes disables eol "
            "translation for out/campaign/*.json so a clone reproduces them.",
    })

for g in GAMES:
    ENTRIES.append({
        "path": "out/shards/ledger.%s.jsonl" % g,
        "disposition": "committed",
        "cost_bearing": "arc-api-spend",
        "produced_by": CAMPAIGN_RUN,
        "consumed_by": [BATTERY + "#input_digests"],
        "reason":
            "The action-by-action ledger the campaign roll-up is computed "
            "from -- the frames and model calls that were actually paid for, "
            "and not derivable from anything else in the repository (the "
            "tracked ledger.jsonl is a different, shorter record, 560 lines "
            "against these 754-1347). battery pins its sha256 too. Large "
            "uncompressed because every row carries a full frame, but it is "
            "repetitive integer grids and packs at 50-76x, so the cost to the "
            "repository is well under a megabyte for all four.",
        "eol": "lf",
    })

for g in GAMES:
    ENTRIES.append({
        "path": "out/shards/probe_log.%s.jsonl" % g,
        "disposition": "committed",
        "cost_bearing": "arc-api-spend",
        "produced_by": CAMPAIGN_RUN,
        "consumed_by": [],
        "reason":
            "The HTTP-level record of the same paid campaign: it is what "
            "substantiates the http_calls counts and the retry envelope that "
            "AUDIT.md section 6 and INC-BA-002 argue from. Not pinned by "
            "battery, but its a7-* counterparts for the later campaign are "
            "already tracked, so leaving these out would make the record "
            "inconsistent across two runs of the same harness. Every "
            "X-API-Key occurrence is '<redacted>' (checked 1:1 over all four "
            "files, 14294 occurrences, 14294 redacted).",
        "eol": "lf",
    })

# Deliberately not committed.  The ignore rule for these predates A14 and A14
# does not overturn it -- it records the digests so that "gitignored" stops
# meaning "unrecorded".
for g in GAMES:
    ENTRIES.append({
        "path": "out/campaign/%s.log" % g,
        "disposition": "hash-only",
        "cost_bearing": "arc-api-spend",
        "produced_by": CAMPAIGN_RUN,
        "consumed_by": [],
        "reason":
            "Console transcript of the paid run. .gitignore has excluded "
            "out/campaign/*.log since before A14 and that call stands: the "
            "log is a human-readable shadow of the ledger, which is "
            "committed. Recorded here so the exclusion is a decision with a "
            "digest behind it rather than a silent gap.",
        "eol": "lf",
    })


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build():
    artefacts = []
    missing = []
    for entry in ENTRIES:
        full = os.path.join(TERRITORY, entry["path"].replace("/", os.sep))
        if not os.path.isfile(full):
            missing.append(entry["path"])
            continue
        row = dict(entry)
        row["sha256"] = _sha256(full)
        row["bytes"] = os.path.getsize(full)
        artefacts.append(row)
    if missing:
        raise SystemExit("refusing to build: %d source file(s) absent, so their "
                         "digests would be invented: %s"
                         % (len(missing), ", ".join(missing)))
    return {
        "schema": "baseline-arms/cost-artefacts@1",
        "generated_by":
            "baseline-arms/runs/20260729T100000Z-a14/build_register.py",
        "prompt_id": "A14-campaign-json-untracked",
        "rule":
            "An artefact whose creation spent money or hours is either "
            "committed, or has its sha256 and provenance recorded here. Never "
            "neither. Checked by harness.cost_artefacts, which baseline-arms/"
            "verify.py runs as part of rung 3.",
        "artefacts": sorted(artefacts, key=lambda r: r["path"]),
    }


def main(argv):
    doc = json.dumps(build(), indent=2, sort_keys=True) + "\n"
    if "--write" in argv:
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(doc)
        print("wrote %s (%d bytes)" % (OUT, len(doc.encode("utf-8"))))
        return 0
    if "--check" in argv:
        if not os.path.isfile(OUT):
            print("RED  %s does not exist" % OUT)
            return 1
        with open(OUT, "rb") as fh:
            on_disk = fh.read()
        if on_disk != doc.encode("utf-8"):
            print("RED  %s differs from a fresh re-derivation" % OUT)
            return 1
        print("ok   COST_ARTEFACTS.json matches a fresh re-derivation")
        return 0
    sys.stdout.write(doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
