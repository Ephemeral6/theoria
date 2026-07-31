"""The data-source registry: every file a figure is allowed to read.

Three reasons this is a module and not a handful of ``open()`` calls scattered
through the figure scripts:

1. **Read-only, and provably so.** Every path a figure touches is declared
   here. Nothing in ``figures/`` writes outside ``figures/``.
2. **Hashed.** ``figures/SOURCES.sha256`` is regenerated from this registry on
   every build. A figure whose input changed under it is a figure that lies,
   and the hash file is what catches that.
3. **Tracked-only.** A source that is not committed cannot be rebuilt from a
   clean checkout, which defeats the whole determinism requirement. Untracked
   inputs are declared here too -- with ``tracked=False`` -- so that they are
   *named* as known-absent rather than silently missing.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)


@dataclass(frozen=True)
class Source:
    key: str
    path: str  # repo-relative, forward slashes
    figures: tuple[str, ...]
    what: str
    tracked: bool = True
    optional: bool = False
    note: str = ""

    @property
    def abspath(self) -> str:
        return os.path.join(REPO_ROOT, *self.path.split("/"))

    def exists(self) -> bool:
        return os.path.exists(self.abspath)


SOURCES: tuple[Source, ...] = (
    # ---- fig02: bill shape -------------------------------------------------
    Source(
        key="pilot_ledger",
        path="baseline-arms/ledger.jsonl",
        figures=("fig02_bill_shape",),
        what="pilot ledger; model-call records carry total_cost_usd, usage and step_idx",
    ),
    Source(
        key="pilot_ar25",
        path="baseline-arms/out/pilot_ar25-0c556536.json",
        figures=("fig02_bill_shape",),
        what="per-run roll-up, cross-checks the curve endpoint against the ledger total",
    ),
    Source(
        key="pilot_g50t",
        path="baseline-arms/out/pilot_g50t-5849a774.json",
        figures=("fig02_bill_shape",),
        what="per-run roll-up",
    ),
    Source(
        key="pilot_sk48",
        path="baseline-arms/out/pilot_sk48-d8078629.json",
        figures=("fig02_bill_shape",),
        what="per-run roll-up",
    ),
    Source(
        key="pilot_tn36",
        path="baseline-arms/out/pilot_tn36-ef4dde99.json",
        figures=("fig02_bill_shape",),
        what="per-run roll-up",
    ),
    # Declared, absent, and named as such. See PLAN.md section 3.
    Source(
        key="envelope_ledger_ar25",
        path="baseline-arms/out/shards/ledger.ar25.jsonl",
        figures=("fig02_bill_shape",),
        what="envelope campaign ledger",
        tracked=False,
        optional=True,
        note="untracked in master; a figure built on it cannot be rebuilt from a "
        "clean checkout. Drop it in and it is picked up automatically.",
    ),
    Source(
        key="envelope_ledger_g50t",
        path="baseline-arms/out/shards/ledger.g50t.jsonl",
        figures=("fig02_bill_shape",),
        what="envelope campaign ledger",
        tracked=False,
        optional=True,
        note="untracked in master.",
    ),
    Source(
        key="envelope_ledger_sk48",
        path="baseline-arms/out/shards/ledger.sk48.jsonl",
        figures=("fig02_bill_shape",),
        what="envelope campaign ledger",
        tracked=False,
        optional=True,
        note="untracked in master.",
    ),
    Source(
        key="envelope_ledger_tn36",
        path="baseline-arms/out/shards/ledger.tn36.jsonl",
        figures=("fig02_bill_shape",),
        what="envelope campaign ledger",
        tracked=False,
        optional=True,
        note="untracked in master.",
    ),
    # The theoria arm's cost ledger, when it exists. The interface the brief
    # asked to leave open: adding a column here is the whole change.
    Source(
        key="theoria_arm_ledger",
        path="theoria-arm/runs/ledger.jsonl",
        figures=("fig02_bill_shape",),
        what="theoria arm cost ledger -- the third column of figure 2",
        tracked=False,
        optional=True,
        note="does not exist yet. The extractor keys on the record's own 'arm' "
        "field, so when this appears the renderer needs no change.",
    ),
    # ---- fig03: capability spectrum ---------------------------------------
    Source(
        key="capability_spectrum",
        path="battery/artifacts/capability_spectrum.json",
        figures=("fig03_capability_spectrum", "fig05_a2_repair_loop", "fig07_a0_vs_a0prime"),
        what="cards (id/family/direction/unit), runs.*.metrics.* with value+status+support, coverage",
    ),
    Source(
        key="arm_contrast",
        path="battery/artifacts/arm_contrast.json",
        figures=("fig03_capability_spectrum",),
        what="which metrics have cross-arm overlap (7 of 38) and the control arm",
    ),
    Source(
        key="gaming_audit",
        path="battery/artifacts/gaming_audit.json",
        figures=("fig03_capability_spectrum",),
        what="tier demotions -- K4 must never be rendered without K2 beside it",
    ),
    # ---- fig05: the A2 repair loop ----------------------------------------
    Source(
        key="a2_loop_ledger",
        path="cold-start-a2/artifacts/loop_ledger.json",
        figures=("fig05_a2_repair_loop",),
        what="the six-beat account: beat, name, claim, status, detail, evidence",
    ),
    Source(
        key="a2_repair_report",
        path="cold-start-a2/artifacts/repair_report.json",
        figures=("fig05_a2_repair_loop",),
        what="what the repair changed",
    ),
    Source(
        key="a2_probe_report",
        path="cold-start-a2/artifacts/probe_report.json",
        figures=("fig05_a2_repair_loop",),
        what="L3: designed / executed / refuted / not-separable",
    ),
    Source(
        key="a2_refutation",
        path="cold-start-a2/artifacts/refutation.json",
        figures=("fig05_a2_repair_loop",),
        what="L1: the solved episode that contradicts the machine-checked theorem",
    ),
    # ---- fig06: concept-birth timeline ------------------------------------
    Source(
        key="a0_theorize_log",
        path="cold-start-a0/THEORIZE_LOG.md",
        figures=("fig06_concept_timeline",),
        what="adjudication blocks (O-/R-/L-/P-/E-) with verdicts, and the revision-history table",
    ),
    Source(
        key="a0_concept_accounts",
        path="cold-start-a0/artifacts/concept_accounts.json",
        figures=("fig06_concept_timeline",),
        what="per-concept verdict, script_delta_bits, the laws and rules that name it",
    ),
    Source(
        key="a0_candidates",
        path="cold-start-a0/artifacts/candidates.jsonl",
        figures=("fig06_concept_timeline",),
        what="the 28 engine proposals as they arrived -- the evidence end of the timeline",
    ),
    # ---- fig07: A0 vs A0' --------------------------------------------------
    Source(
        key="a0_score_vs_truth",
        path="cold-start-a0/artifacts/score_vs_truth.json",
        figures=("fig07_a0_vs_a0prime",),
        what="233/236 agreement and the three pairs R-05 named before the score existed",
    ),
)

BY_KEY = {s.key: s for s in SOURCES}

#: The commit the figures were built from, for the git-timestamp axis in
#: fig06. Resolved through the registry so the subprocess call has one home.
GIT_TIMELINE_PATH = "cold-start-a0/THEORIZE_LOG.md"


def get(key: str) -> Source:
    try:
        return BY_KEY[key]
    except KeyError:
        raise KeyError(
            f"{key!r} is not a declared source. Add it to figures/sources.py "
            "so it gets hashed -- reading an undeclared file defeats the point."
        ) from None


def path(key: str) -> str:
    """Absolute path to a declared source. Raises if a required one is absent."""
    src = get(key)
    if not src.exists():
        if src.optional:
            raise FileNotFoundError(
                f"{src.path} is declared optional and is absent. {src.note}"
            )
        raise FileNotFoundError(f"declared source missing: {src.path}")
    return src.abspath


def maybe_path(key: str) -> str | None:
    """Absolute path, or ``None`` if an optional source is absent."""
    src = get(key)
    return src.abspath if src.exists() else None


def read_json(key: str):
    with open(path(key), encoding="utf-8") as fh:
        return json.load(fh)


def read_jsonl(key: str) -> list:
    out = []
    with open(path(key), encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def read_text(key: str) -> str:
    with open(path(key), encoding="utf-8") as fh:
        return fh.read()


def sha256_file(abspath: str) -> str:
    h = hashlib.sha256()
    with open(abspath, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def git_log(rel_path: str) -> list[dict]:
    """``git log --follow`` over one path, oldest first.

    Committer timestamps are in ISO-8601 UTC. Returns ``[]`` rather than
    raising when git is unavailable, and the caller degrades to the ordinal
    axis -- a figure should not fail to build because a checkout is shallow.
    """
    try:
        proc = subprocess.run(
            [
                "git",
                "-C",
                REPO_ROOT,
                "log",
                "--follow",
                "--date=format-local:%Y-%m-%dT%H:%M:%SZ",
                "--format=%H%x1f%cd%x1f%s",
                "--",
                rel_path,
            ],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "TZ": "UTC", "GIT_PAGER": "cat"},
        )
    except (OSError, subprocess.CalledProcessError):
        return []
    rows = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        rows.append({"sha": parts[0], "when": parts[1], "subject": parts[2]})
    rows.reverse()  # oldest first
    return rows


def manifest_rows() -> list[tuple[str, str, str]]:
    """``(sha256 | 'ABSENT', path, status)`` for every declared source, sorted."""
    rows = []
    for src in sorted(SOURCES, key=lambda s: s.path):
        if src.exists():
            rows.append((sha256_file(src.abspath), src.path, "tracked" if src.tracked else "untracked"))
        else:
            rows.append(("ABSENT" + "0" * 58, src.path, "absent-optional" if src.optional else "absent-REQUIRED"))
    return rows


def write_manifest(target: str | None = None) -> str:
    """Regenerate ``figures/SOURCES.sha256``."""
    target = target or os.environ.get("FIGURES_SHA") or os.path.join(_HERE, "SOURCES.sha256")
    lines = [
        "# sha256 of every input the P-21 figure pipeline reads.",
        "# Regenerated by figures/build_all.py; checked by figures/verify.sh.",
        "# 'ABSENT000...' marks a source declared in sources.py that is not on disk.",
        "",
    ]
    for digest, rel, status in manifest_rows():
        lines.append(f"{digest}  {rel}  [{status}]")
    body = "\n".join(lines) + "\n"
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return target


def check_required() -> list[str]:
    """Paths of required sources that are missing. Empty list means green."""
    return [s.path for s in SOURCES if not s.optional and not s.exists()]
