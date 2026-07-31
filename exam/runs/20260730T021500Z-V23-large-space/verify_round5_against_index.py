"""Re-check this run's manifest audits against published bytes, at their own commits.

Round five reported "17 of the then 23 entries matched and 6 did not". Cycle 107
found that audit had hashed the *working copy*, which under
`exam/.gitattributes`'s LF pin can hide a mismatch but can never invent one --
so its 6 should survive and its 17 is a statement about one checkout. That is an
argument, and this is the measurement.

For each commit given on the command line, the manifest in that commit's tree is
checked against the blobs in that same tree: entirely inside git, so no working
copy participates. A mismatching entry is then re-hashed over the blob with LF
turned back into CRLF; if *that* matches, the entry was never stale in content
-- the stamp was taken from a Windows working copy and the file itself was
correct all along. Distinguishing the two is the whole point, because they call
for opposite fixes: regenerate the artefact, or normalise the line endings.

  python verify_round5_against_index.py <commit> [<commit> ...]
"""
import hashlib
import json
import subprocess
import sys

RUN = "exam/runs/20260730T021500Z-V23-large-space"


def blob(commit, repo_rel):
    r = subprocess.run(["git", "show", "%s:%s" % (commit, repo_rel)],
                       capture_output=True)
    return r.stdout if r.returncode == 0 else None


def check(commit):
    raw = blob(commit, "%s/MANIFEST.json" % RUN)
    if raw is None:
        print("%s  no manifest in this tree" % commit[:8])
        return
    m = json.loads(raw.decode("utf-8"))
    matched, eol_only, stale, missing = [], [], [], []
    for e in m.get("files", []):
        data = blob(commit, "%s/%s" % (RUN, e["path"]))
        if data is None:
            missing.append(e["path"])
        elif hashlib.sha256(data).hexdigest() == e["sha256"]:
            matched.append(e["path"])
        elif hashlib.sha256(data.replace(b"\n", b"\r\n")).hexdigest() == e["sha256"]:
            eol_only.append(e["path"])
        else:
            stale.append(e["path"])
    print("%s  entries=%-3d matched=%-3d stale=%-2d eol-only=%-2d missing=%d"
          % (commit[:8], len(m.get("files", [])), len(matched), len(stale),
             len(eol_only), len(missing)))
    for label, items in (("stale", stale), ("eol-only", eol_only),
                         ("missing", missing)):
        for p in items:
            print("      %-9s %s" % (label + ":", p))


if __name__ == "__main__":
    for c in sys.argv[1:]:
        check(c)
