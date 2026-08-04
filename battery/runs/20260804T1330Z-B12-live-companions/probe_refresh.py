"""Did anything move?  Regenerate every live companion and diff it, by digest.

B12's premise was that the battery's live readings predate several legs (the
R1, R1b, R2, R2b rounds).  This probe answers that with hashes rather than
with a story: each companion is rebuilt in-process from the current tree and
its canonical bytes are compared against the committed file.  A companion
whose digest is unchanged did not move, and every metric it carries is
therefore unchanged too -- which is a stronger statement than listing the
metrics that happen to look the same.

    cd <repo> && python battery/runs/<this>/probe_refresh.py

Writes `refresh.json` beside itself.  Reads only; writes nothing under
`battery/artifacts_live/` and nothing at all under `battery/artifacts/`.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path):
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return sha256_text(fh.read().replace("\r\n", "\n"))


def main():
    from battery.audit import (frontload, gaming, live_arm, live_census,
                               live_economy, live_tiers, threat)

    modules = [
        ("live_arm_readings.json", live_arm),
        ("live_economy.json", live_economy),
        ("gaming_audit.live.json", live_tiers),
        ("frontload_e2l.json", frontload),
        ("threat_model.json", threat),
        ("live_census.json", live_census),
    ]
    rows = {}
    for name, module in modules:
        path = module.DEFAULT_OUT
        recomputed = module.serialise(module.build())
        committed = sha256_file(path) if os.path.exists(path) else None
        rows[name] = {
            "committed_sha256": committed,
            "recomputed_sha256": sha256_text(recomputed),
            "moved": committed != sha256_text(recomputed),
            "present_on_disk": os.path.exists(path),
        }

    doc = {
        "what": ("every battery/artifacts_live/ companion rebuilt in-process "
                 "from the tree and compared with the committed file by "
                 "canonical-bytes digest. `moved: false` means not one metric "
                 "in that companion changed."),
        "companions": rows,
        "n_moved": sum(1 for r in rows.values() if r["moved"]),
        "note": ("gaming is imported but not probed: its live companion is "
                 "written by live_tiers, which is probed. A companion absent "
                 "from disk reports present_on_disk false and moved true -- "
                 "absence, not agreement."),
    }
    dest = os.path.join(HERE, "refresh.json")
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s -- %d of %d companion(s) moved"
          % (dest, doc["n_moved"], len(rows)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
