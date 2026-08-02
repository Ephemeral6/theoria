"""Write this run's MANIFEST.json. Re-runnable; hashes every delivered file."""
import hashlib
import io
import json
import os

RUN = "freeze/runs/20260802T112508Z-S48-schema-column-withdrawal"
EXTRA = [
    "freeze/CLAIMS_TEXT.md",
    "freeze/schema_column_withdrawal.py",
    "freeze/verify.sh",
    "monitor/inbox/20260802T112508Z-W-9204-freeze-half-of-the-schema-withdrawal-has-landed.md",
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def main():
    files = []
    for dirpath, _dirs, names in os.walk(RUN):
        for name in sorted(names):
            if name == "MANIFEST.json":
                continue
            p = os.path.join(dirpath, name).replace("\\", "/")
            files.append({"path": p, "sha256": sha(p)})
    for p in EXTRA:
        files.append({"path": p, "sha256": sha(p)})
    files.sort(key=lambda r: r["path"])

    manifest = {
        "prompt_id": "S48-schema-column-withdrawal-claims-text",
        "cell": "S48",
        "territory": "freeze",
        "worker": "W-9204",
        "branch": "agent/s48-schema-column-withdrawal-claims-text",
        "base_commit": "9e478dd8",
        "utc": "2026-08-02T11:25:08Z",
        "seed": None,
        "source_proposal": (
            "monitor/inbox/20260801T0600Z-PROP-schema-column-withdrawal.md "
            "(baseline-arms, 2026-08-01); ruling baseline-arms/SCHEMA_ARM_RULING.md"
        ),
        "scope": (
            "freeze's half only: CLAIMS_TEXT.md. Theoria.md:271's main table, "
            "battery's arm rename and papers' follow-through are other "
            "territories and are asked for in monitor/inbox/, not edited."
        ),
        "spend": {"usd": 0.0, "api_calls": 0, "model_calls": 0,
                  "desk_calls": 0, "network": "none",
                  "sealed_pile_contact": "none"},
        "delivered": {
            "claims_text": (
                "four places landed verbatim per proposal 2.1-2.4, each dated "
                "2026-08-02, each new number carrying its coverage (dev pile 4 "
                "games / 8 runs / 1 of 2 collections records tokens)"),
            "gate": (
                "freeze/schema_column_withdrawal.py, wired into verify.sh as "
                "stage [21] with its selftest, in the shape stage [19] uses for "
                "the 3.0 withdrawal"),
            "negative_sample": (
                "a live citation of the withdrawn placeholder reds the gate; a "
                "mention within 2 lines of a withdrawal marker is acquitted, "
                "because recording a withdrawal necessarily names the thing "
                "withdrawn"),
            "positive_control": (
                "the schema_upstream reference row and its coverage must "
                "survive -- withdrawing a claim and deleting the evidence are "
                "different acts"),
        },
        "gates": {
            "verify": "exit 0",
            "selftest": (
                "11/11, exit 0; one control caught a real hole in the first "
                "draft, where the C2 check scanned a bare word that occurs "
                "twice in the file"),
            "verify_sh_syntax": "bash -n OK",
            "verify_sh_full": (
                "NOT RUN -- bash could not fork with ~3.6 GB free of 31.46 GB "
                "and the script never reached stage [0]. Recorded as an "
                "environmental block, not as a pass."),
        },
        "gaps": [
            "bash freeze/verify.sh is unverified on this machine (memory).",
            "schema_repro survives in MANIFEST_DRAFT.md:537, "
            "PENDING_FIVE.md:141,294 and STATS_RULES.md:26,2099 -- freeze files, "
            "but outside this ticket's scope; named and raised in inbox rather "
            "than swept in under this ticket.",
            "Theoria.md:271's main table, battery's arm rename and papers' "
            "follow-through are unmoved; all three are other territories.",
            "SCHEMA_LOCATE.md 1.1: the upstream spec is Zeng et al., not Feng "
            "et al. -- registered long ago, still uncorrected, in nobody's queue.",
        ],
        "files": files,
    }
    out = os.path.join(RUN, "MANIFEST.json")
    with io.open(out, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s with %d file hashes" % (out, len(files)))


if __name__ == "__main__":
    main()
