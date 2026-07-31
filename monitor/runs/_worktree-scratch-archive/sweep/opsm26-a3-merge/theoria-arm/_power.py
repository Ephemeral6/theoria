import difflib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap
from armtools import backfill, armversion
runs_root = _bootstrap.path("runs")
table = armversion.scan()
rows = backfill.survey(runs_root)
print("archive_material with manifest: routing and result")
for row in rows:
    if not row["archive_material"] or not row["has_manifest"]:
        print("  SKIPPED BY CHECK 8: %-42s archive_material=%s has_manifest=%s"
              % (row["slug"], row["archive_material"], row["has_manifest"]))
        continue
    slug = row["slug"]
    on_disk = open(os.path.join(runs_root, slug, "MANIFEST.json"), "rb").read()
    bf = backfill._is_backfilled(runs_root, slug)
    # as-shipped route
    if bf:
        shipped = backfill.build(slug, runs_root=runs_root, table=table)
    else:
        r = backfill.amend_payload(slug, runs_root=runs_root, table=table)
        shipped = r[0] if r else None
    # forced build() route
    try:
        forced = backfill.build(slug, runs_root=runs_root, table=table)
        ferr = None
    except Exception as e:
        forced, ferr = None, "%s: %s" % (type(e).__name__, e)
    sd = "SAME" if shipped is not None and backfill.render(shipped) == on_disk else "DRIFT"
    if ferr:
        fd = "EXC(%s)" % ferr
    else:
        fd = "SAME" if forced is not None and backfill.render(forced) == on_disk else "DRIFT"
    print("  %-42s backfilled=%-5s shipped=%-5s forced_build=%s" % (slug, bf, sd, fd))
