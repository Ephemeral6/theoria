import difflib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap
from armtools import backfill, armversion
runs_root = _bootstrap.path("runs")
table = armversion.scan()
for row in backfill.survey(runs_root):
    if not row["archive_material"] or not row["has_manifest"]:
        continue
    slug = row["slug"]
    if backfill._is_backfilled(runs_root, slug):
        continue
    on_disk = open(os.path.join(runs_root, slug, "MANIFEST.json"), "rb").read()
    try:
        forced = backfill.build(slug, runs_root=runs_root, table=table)
    except Exception as e:
        print("### %s EXC %s" % (slug, e)); continue
    got = backfill.render(forced)
    if got == on_disk: continue
    print("\n### FORCED-BUILD DRIFT %s" % slug)
    d=list(difflib.unified_diff(on_disk.decode('utf-8','replace').splitlines(),
        got.decode('utf-8','replace').splitlines(),'on_disk','forced_build',lineterm='',n=0))
    print("\n".join(d[:45]))
