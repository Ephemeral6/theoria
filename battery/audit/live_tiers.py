"""The live tier companion to the frozen gaming audit.

`battery/artifacts/gaming_audit.json` is frozen: it was written before B17 and
V9, its main table names nine metrics, and `PREREG_V9.md` §5 forbids rewriting
it — 不修改任何已提交产物, V9 的结论另开文件, 冲突留在明面上. This module is
that separate file, executed. It recomputes every metric's tier from the live
code (`battery.audit.gaming.tier_of`, which consults the V9 blind round first),
carries the V9 demotion evidence per PREREG R3 (a demotion names a run and a
number), and states the frozen-vs-live divergence explicitly instead of leaving
it for a reader to rediscover — an adversarial-review subagent already read the
stale nine off the frozen file once (W-1671 §1).

The output is a **tracked, byte-reproducible** artefact:

* no timestamp, no commit hash, no absolute path — for a fixed tree, two runs
  produce identical bytes (the repository's determinism rule);
* `frozen_sha256` pins the exact frozen artefact the diff was computed against,
  so `battery/verify.py` can turn red the moment either side moves without the
  other: a rewritten baseline is a PREREG violation, and a live artefact that
  no longer matches a recompute is the same staleness this file exists to make
  visible, one level up.

It writes only under `battery/artifacts_live/`. A destination that resolves
inside `battery/artifacts/` is refused outright rather than warned about: the
frozen directory is the baseline the whole comparison depends on, and the
registered "裸跑覆盖" hazard (PREREG_V9 §5) is exactly a generator that would
write there by accident.

    python -m battery.audit.live_tiers            # writes the tracked default
    python -m battery.audit.live_tiers --out P    # anywhere except artifacts/
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Dict

HERE = os.path.dirname(os.path.abspath(__file__))          # battery/audit
BATTERY = os.path.dirname(HERE)                            # battery
REPO = os.path.dirname(BATTERY)

#: The frozen baseline this artefact diffs against. Never written here.
FROZEN = os.path.join(BATTERY, "artifacts", "gaming_audit.json")
FROZEN_REL = "battery/artifacts/gaming_audit.json"

#: The tracked default output. `battery/freeze.py` lists it under READINGS.
DEFAULT_OUT = os.path.join(BATTERY, "artifacts_live", "gaming_audit.live.json")

#: The disclosure sentence `battery/verify.py` pins into STATUS.md while the
#: frozen and live audits diverge. The count is read from the frozen file, so
#: the sentence must track the artefact: regenerating the baseline with a
#: different main table makes the old sentence fail the gate.
STALE_CLAIM = "committed 的 `artifacts/gaming_audit.json` 仍写着 %d 条主表指标"


def frozen_sha256(path: str = FROZEN) -> str:
    """LF-normalised digest of the frozen artefact, `battery.freeze`'s hash.

    One definition, imported: the freeze record and this artefact must not be
    able to disagree about what hashing the baseline means.
    """
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.freeze import sha256_file
    return sha256_file(path)


def refuse_frozen_destination(out_path: str) -> str:
    """Resolve `out_path`; raise if it lands inside `battery/artifacts/`.

    Resolution first (`realpath`, then case-normalised on this platform), so a
    relative path, a `..` hop or a symlink cannot reach the frozen directory
    while looking like somewhere else. Returns the resolved path on success.
    """
    resolved = os.path.realpath(os.path.abspath(out_path))
    frozen_dir = os.path.realpath(os.path.join(BATTERY, "artifacts"))
    a = os.path.normcase(resolved)
    b = os.path.normcase(frozen_dir)
    if a == b or a.startswith(b + os.sep):
        raise ValueError(
            "refusing to write %s: it resolves inside battery/artifacts/, the "
            "frozen baseline (PREREG_V9.md §5 — 不修改"
            "任何已提交产物). The live tiers "
            "belong in battery/artifacts_live/." % out_path)
    return resolved


def build(frozen_path: str = FROZEN) -> Dict[str, object]:
    """The live audit, recomputed in-process, plus its diff against the frozen.

    Everything here is derived: the tier from `gaming.tier_of` (V9 outranks the
    sighted evidence and only ever demotes), the demotion evidence from
    `v9_demotions` (attack, value, target, claim — PREREG R3), the diff from
    reading the frozen file. Nothing is typed in, so this module cannot hold an
    opinion of its own about any metric.
    """
    import sys
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    from battery.audit.gaming import tier_of
    from battery.audit.v9.verdict import v9_demotions
    from battery.metrics import REGISTRY

    with open(frozen_path, encoding="utf-8") as fh:
        frozen = json.load(fh)

    demotions = v9_demotions()
    metrics: Dict[str, Dict[str, object]] = {}
    for metric_id in sorted(REGISTRY):
        row: Dict[str, object] = {"tier": tier_of(metric_id)}
        if metric_id in demotions:
            row["v9_demotion"] = demotions[metric_id]
        metrics[metric_id] = row

    frozen_metrics = frozen.get("metrics", {})
    diff = []
    for metric_id in sorted(set(frozen_metrics) | set(metrics)):
        frozen_tier = frozen_metrics.get(metric_id, {}).get("tier")
        live_tier = metrics.get(metric_id, {}).get("tier")
        if frozen_tier != live_tier:
            diff.append({"metric": metric_id,
                         "frozen": frozen_tier, "live": live_tier})

    return {
        "what": ("per-metric live tier from battery.audit.gaming.tier_of "
                 "(V9 blind round consulted first; V9 only demotes), with the "
                 "V9 demotion evidence per PREREG_V9 R3 and the divergence "
                 "against the frozen 2026-07-28 baseline, which PREREG_V9 "
                 "§5 forbids rewriting. No timestamp on purpose: for a "
                 "fixed tree this file is byte-reproducible."),
        "frozen_artifact": FROZEN_REL,
        "frozen_sha256": frozen_sha256(frozen_path),
        "frozen_main": sorted(frozen.get("main", [])),
        "metrics": metrics,
        "main": sorted(m for m in metrics if metrics[m]["tier"] == "main"),
        "reference": sorted(m for m in metrics
                            if metrics[m]["tier"] == "reference"),
        "diff_vs_frozen": diff,
        "n_diverging": len(diff),
    }


def serialise(doc: Dict[str, object]) -> str:
    """Canonical bytes: sorted keys, two-space indent, LF, trailing newline."""
    return json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write(out_path: str = DEFAULT_OUT, frozen_path: str = FROZEN) -> str:
    """Build and write. Refuses the frozen directory before touching anything."""
    resolved = refuse_frozen_destination(out_path)
    doc = build(frozen_path)
    os.makedirs(os.path.dirname(resolved), exist_ok=True)
    with open(resolved, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(serialise(doc))
    return resolved


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="write the live-tier companion to the frozen gaming audit")
    parser.add_argument("--out", default=DEFAULT_OUT,
                        help="destination (default: %(default)s); anything "
                             "resolving inside battery/artifacts/ is refused")
    args = parser.parse_args(argv)
    try:
        path = write(args.out)
    except ValueError as exc:
        print("REFUSED: %s" % exc)
        return 2
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
