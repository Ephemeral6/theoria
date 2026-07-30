"""Build every P-21 paper figure, in a fixed order.

    python figures/build_all.py            # build into figures/{csv,out}
    python figures/build_all.py --list     # what would be built

Environment overrides, used by ``verify.sh`` to build twice into separate trees:

    FIGURES_OUT     where images go   (default figures/out)
    FIGURES_CSV     where CSVs go     (default figures/csv)
    FIGURES_SHA     where the source hash manifest goes (default figures/SOURCES.sha256)
    FIGURES_PAPER   where the publication profile goes (default figures/paper)

Every figure module exposes the same two names, and that is the whole contract:

    NAME : str          the figure's slug, matching its filename
    build() -> dict     writes the CSV and both themes, returns
                        {"csv": <path>, "images": [<path>, ...], "notes": [str]}

Ordering is explicit here rather than discovered from the filesystem, because
directory iteration order is not something to trust in a pipeline whose whole
promise is byte-identical output.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import paper_index  # noqa: E402
import paper_map  # noqa: E402
import sources  # noqa: E402
import theme  # noqa: E402

# Notes carry non-ASCII -- fig03's demoted-tier dagger, fig05's bilingual beat
# names. When stdout is a terminal Python picks a workable encoding; when it is
# redirected to a file (which is exactly what verify.sh does) it falls back to
# the locale codec, and on a zh-CN Windows box that is GBK, which cannot encode
# them. The build then dies inside a print() with the figures already correct.
# Pin it, so the gate does not depend on the operator's locale.
#
# `newline` matters as much as `encoding`: on Windows a text stream translates
# \n to \r\n, so `--list` emitted names with a trailing CR and verify.sh built
# paths ending in one -- every artefact then looked missing while the build had
# in fact just written it.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", newline="\n")
    except (AttributeError, OSError):  # pragma: no cover - not a text stream
        pass

#: Fixed build order. Paper order, not dependency order -- the figures are
#: independent of each other by construction.
FIGURES: tuple[str, ...] = (
    "fig02_bill_shape",
    "fig03_capability_spectrum",
    "fig04_a3_transfer",
    "fig05_a2_repair_loop",
    "fig06_concept_timeline",
    "fig07_a0_vs_a0prime",
)

# A paper figure that names a plate this build does not produce is a citation
# with nothing behind it -- "see Figure 4" pointing at a file that was never
# written. `paper_map` cannot check this itself without importing this module
# and closing an import cycle, so the check lives on this side of it, at import
# time, where it fails the build rather than a later gate.
_UNBUILT = sorted(set(paper_map.BY_PIPELINE) - set(FIGURES))
if _UNBUILT:
    raise RuntimeError(
        f"paper_map declares figure(s) for plate(s) this build does not produce: "
        f"{', '.join(_UNBUILT)}. Either add them to FIGURES or drop the paper entry."
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__ or "")
    ap.add_argument("--list", action="store_true", help="list figures and exit")
    ap.add_argument("--only", action="append", default=None, help="build one figure (repeatable)")
    ap.add_argument("--no-manifest", action="store_true", help="skip SOURCES.sha256")
    args = ap.parse_args(argv)

    if args.list:
        for name in FIGURES:
            print(name)
        return 0

    missing = sources.check_required()
    if missing:
        print("FAIL: required data sources are missing:", file=sys.stderr)
        for m in missing:
            print(f"  {m}", file=sys.stderr)
        return 2

    # A discovery rule that could not apply its tracked-only filter still built
    # a figure -- with a weaker guarantee than the one this pipeline advertises.
    # Printed rather than swallowed, because a silently weaker guarantee is
    # indistinguishable from the strong one right up until it is not.
    for warning in sources.TRACKING_UNAVAILABLE:
        print(f"WARN: {warning}", file=sys.stderr)
    for warning in sources.untracked_inclusions():
        print(f"WARN: {warning}", file=sys.stderr)
    # The status column of SOURCES.sha256 is the one field in it that is asserted
    # rather than measured, so it is the one field a regeneration cannot correct.
    # Warned here at build time, and checked against git by check_tracking.py at
    # gate 14 -- because for two days the manifest said [untracked] about fifteen
    # committed files and every gate agreed with it.
    for warning in sources.tracking_mismatches():
        print(f"WARN: {warning}", file=sys.stderr)
    # A file that matches a rule, is on disk, and is not committed. The
    # tracked-only filter drops it -- correctly, for determinism -- and dropping
    # a cost-bearing ledger silently is how "paid data nobody draws" comes to
    # look exactly like "no such data".
    for warning in sources.untracked_but_present():
        print(f"WARN: {warning}", file=sys.stderr)
    # GIT_DEGRADED is populated during the build, not before it, so it is
    # reported again at the end -- see the second loop after the figures run.

    wanted = tuple(args.only) if args.only else FIGURES
    unknown = [w for w in wanted if w not in FIGURES]
    if unknown:
        print(f"FAIL: unknown figure(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    print(f"out  : {theme.out_root()}")
    print(f"csv  : {theme.csv_root()}")
    print(f"paper: {theme.paper_root()}")
    print()

    failures: list[str] = []
    for name in wanted:
        print(f"[{name}]")
        try:
            mod = importlib.import_module(name)
            if getattr(mod, "NAME", None) != name:
                raise AssertionError(
                    f"module {name} declares NAME={getattr(mod, 'NAME', None)!r}; "
                    "the slug must match the filename"
                )
            result = mod.build()
        except Exception:  # noqa: BLE001 -- report every failure, keep going
            failures.append(name)
            traceback.print_exc()
            print(f"  -> FAILED\n")
            continue

        csv_path = result.get("csv")
        images = result.get("images") or []
        if csv_path:
            print(f"  csv  {os.path.relpath(csv_path, _HERE)}")
        for img in images:
            print(f"  img  {os.path.relpath(img, _HERE)}")
        for note in result.get("notes") or []:
            print(f"  note {note}")
        expected = len(theme.THEMES) * len(theme.FORMATS)
        if paper_map.for_pipeline(name) is not None:
            expected += len(theme.THEMES) * len(paper_map.PUB_FORMATS)
        if len(images) != expected:
            failures.append(name)
            print(f"  -> FAILED: expected {expected} images, got {len(images)}")
        print()

    # The index and the captions hash the images, so they are written after
    # every figure is on disk -- and only for a whole build. On `--only` the
    # other plates' digests would be whatever the previous build left, and an
    # index that is right about one figure and stale about five is worse than
    # one that was not regenerated at all, because it looks current.
    if args.only:
        print("index/captions skipped: --only builds a partial tree, and a partially "
              "regenerated index reads as a whole one.")
    elif not failures:
        written = paper_index.write_all()
        for path in written:
            print(f"paper index -> {os.path.relpath(path, _HERE)}")

    if not args.no_manifest:
        manifest = sources.write_manifest()
        print(f"sources hashed -> {os.path.relpath(manifest, _HERE)}")

    # Populated while the figures ran, so it can only be reported here. A build
    # that fell back to a weaker axis produced a different figure, and the only
    # place that difference is currently visible is the plate's own small print.
    for warning in sources.GIT_DEGRADED:
        print(f"WARN: {warning}", file=sys.stderr)

    if failures:
        print(f"\nFAIL: {len(failures)} figure(s) failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"\nOK: {len(wanted)} figure(s) built.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
