import difflib, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap
from armtools import backfill, armversion
runs_root = _bootstrap.path("runs")
table = armversion.scan()
print("SCAN: commits_scanned=%s carrying=%s distinct_subtrees=%s distinct_versions=%s"
      % (table["commits_scanned"], table["commits_carrying_the_arm"],
         table["distinct_arm_subtrees"], table["distinct_arm_versions"]))
for row in backfill.survey(runs_root):
    if not row["archive_material"] or not row["has_manifest"]:
        continue
    slug = row["slug"]
    p = os.path.join(runs_root, slug, "MANIFEST.json")
    on_disk = open(p,"rb").read()
    bf = backfill._is_backfilled(runs_root, slug)
    if bf:
        payload = backfill.build(slug, runs_root=runs_root, table=table)
    else:
        r = backfill.amend_payload(slug, runs_root=runs_root, table=table)
        payload = r[0] if r else None
    got = backfill.render(payload) if payload is not None else b"<None>"
    if got != on_disk:
        print("\n### DRIFT %s (backfilled=%s)" % (slug, bf))
        d = list(difflib.unified_diff(on_disk.decode("utf-8","replace").splitlines(),
                                      got.decode("utf-8","replace").splitlines(),
                                      "on_disk","re-derived", lineterm="", n=1))
        print("\n".join(d[:80]))
