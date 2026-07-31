"""Build every P-21 paper figure, in a fixed order.

    python figures/build_all.py            # build into figures/{csv,out}
    python figures/build_all.py --list     # what would be built

Environment overrides, used by ``verify.sh`` to build twice into separate trees:

    FIGURES_OUT   where images go   (default figures/out)
    FIGURES_CSV   where CSVs go     (default figures/csv)
    FIGURES_SHA   where the source hash manifest goes (default figures/SOURCES.sha256)

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

import sources  # noqa: E402
import theme  # noqa: E402

#: Fixed build order. Paper order, not dependency order -- the figures are
#: independent of each other by construction.
FIGURES: tuple[str, ...] = (
    "fig02_bill_shape",
    "fig03_capability_spectrum",
    "fig05_a2_repair_loop",
    "fig06_concept_timeline",
    "fig07_a0_vs_a0prime",
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

    wanted = tuple(args.only) if args.only else FIGURES
    unknown = [w for w in wanted if w not in FIGURES]
    if unknown:
        print(f"FAIL: unknown figure(s): {', '.join(unknown)}", file=sys.stderr)
        return 2

    print(f"out : {theme.out_root()}")
    print(f"csv : {theme.csv_root()}")
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
        if len(images) != expected:
            failures.append(name)
            print(f"  -> FAILED: expected {expected} images, got {len(images)}")
        print()

    if not args.no_manifest:
        manifest = sources.write_manifest()
        print(f"sources hashed -> {os.path.relpath(manifest, _HERE)}")

    if failures:
        print(f"\nFAIL: {len(failures)} figure(s) failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    print(f"\nOK: {len(wanted)} figure(s) built.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
