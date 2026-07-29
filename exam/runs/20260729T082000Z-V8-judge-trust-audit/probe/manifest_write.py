import hashlib
import json
import os

base = os.path.dirname(os.path.abspath(__file__))
files = sorted(f for f in os.listdir(base)
               if f.endswith((".py", ".json")) and f != "MANIFEST.json")
man = {
    "prompt_id": "V8-judge-trust-audit-item2-handbuilt-discrimination",
    "branch": "worktree-agent-ac847fd12b35baecb",
    "base_commit": "c7a464c5d654a70e669de8cb3743b99bffb0fa82",
    "utc": "2026-07-29T08:20:00Z",
    "what": ("per-item discrimination (oracle/memoriser/bluffer, null excluded) "
             "over the five hand-built exam papers: heldout, handover, "
             "adaptation, verdict, handover_auto"),
    "rerun": "python <this dir>/disc_handbuilt.py && python <this dir>/report.py",
    "files": [{"path": "exam/runs/20260729T082000Z-V8-judge-trust-audit/probe/" + f,
               "sha256": hashlib.sha256(
                   open(os.path.join(base, f), "rb").read()).hexdigest()}
              for f in files],
}
with open(os.path.join(base, "MANIFEST.json"), "w", encoding="utf-8",
          newline="\n") as fh:
    json.dump(man, fh, indent=2, sort_keys=True)
    fh.write("\n")
print("wrote MANIFEST.json over", files)
