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

**Declared by rule, not only by list** (P8). Three of the inputs arrive as
*families* that grow: the theoria arm writes a new directory under
``theoria-arm/runs/`` every run, the baseline writes a new ``pilot_*.json``
roll-up, and the envelope campaign writes a new shard. Naming each file by hand
meant that a run which landed on disk did not reach the figure until somebody
edited two files, and P8 found two live cases where nobody had -- see
``figures/runs/20260728T110000Z-P8-billshape-pipeline/FINDINGS.md``.

A ``Rule`` is therefore a declaration too: it declares *the directory, the
filename pattern, and the floor*. Every file it finds becomes a real ``Source``
and lands in ``SOURCES.sha256`` exactly like a hand-written one, so nothing is
read unhashed. What changes is only who enumerates the family -- the filesystem
rather than a tuple that ages.

The floor is the part that makes this safe rather than merely convenient. A
glob that finds nothing is indistinguishable from a family that is empty, and
"the figure quietly lost an arm" would then look exactly like "the figure is
fine". Each rule records how many members were on disk when it was written; find
fewer and the build stops. An optional check is a check that does not run.
"""

from __future__ import annotations

import fnmatch
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
    # The per-run roll-ups, the envelope shards and the theoria arm's runs are
    # not listed here any more. They are families that grow, and they are
    # declared by rule in DISCOVERY below -- each member still becomes a Source
    # and still lands in SOURCES.sha256.
    #
    # fig02's shape metrics come from the battery's own capability_spectrum,
    # declared once below for every figure that reads it.
    # ---- fig03: capability spectrum ---------------------------------------
    Source(
        key="validation_material",
        path="battery/artifacts/validation_material.json",
        figures=("fig03_capability_spectrum",),
        what="control_arms -- the control/treatment split as a declared field, not an inference from arm names",
    ),
    # ---- fig03: capability spectrum ---------------------------------------
    Source(
        key="capability_spectrum",
        path="battery/artifacts/capability_spectrum.json",
        figures=(
            "fig02_bill_shape",
            "fig03_capability_spectrum",
            "fig05_a2_repair_loop",
            "fig07_a0_vs_a0prime",
        ),
        what="cards (id/family/direction/unit), runs.*.metrics.* with value+status+support, coverage. "
        "fig02 takes E2/E3/E4 from here rather than recomputing three Phase 4 endpoints",
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
    Source(
        key="a2_locate_report",
        path="cold-start-a2/artifacts/locate_report.json",
        figures=("fig05_a2_repair_loop",),
        what="L2: the three-way narrowing, and the one transition it lands on",
    ),
    Source(
        key="a2_probes",
        path="cold-start-a2/artifacts/probes.jsonl",
        figures=("fig05_a2_repair_loop",),
        what="L3 probe rows; P-03 carries no outcome fields at all -- designed and not separable in this world",
    ),
    Source(
        key="a2_exhibit_report",
        path="cold-start-a2/artifacts/exhibit_report.json",
        figures=("fig05_a2_repair_loop",),
        what="M5: the manual that replays green, is signed axiom-free, and is false of the world",
    ),
    Source(
        key="a2_plan_repaired",
        path="cold-start-a2/artifacts/plan_repaired.json",
        figures=("fig05_a2_repair_loop",),
        what="L6: SAT, length 18, and the world agreeing",
    ),
    Source(
        key="a2_trace_summary",
        path="cold-start-a2/artifacts/trace_summary.json",
        figures=("fig05_a2_repair_loop",),
        what="the evidence spine: raw vs history trace, and the one omitted pair that fires the deleted rule",
    ),
    # Declared after fig05's first pass named them: M0's setup and L4's
    # re-derivation were being described in muted text as "not a declared source
    # here -- so not drawn". M0's 23-rules-with-a-jump against 22-without IS the
    # hole the whole exhibit turns on; leaving it undrawn to avoid a Source entry
    # was the wrong trade.
    Source(
        key="a2_engines_diff",
        path="cold-start-a2/artifacts/engines_diff.json",
        figures=("fig05_a2_repair_loop",),
        what="M0: the sweep proposes 23 rules including one jump effect; the history proposes 22 and no jump -- the hole, made a number",
    ),
    Source(
        key="a2_engines_diff_probed",
        path="cold-start-a2/artifacts/engines_diff_probed.json",
        figures=("fig05_a2_repair_loop",),
        what="L4: the grown evidence re-proposes the jump rule at transition 194 -- re_derivable_from_grown_evidence, as a count rather than a boolean",
    ),
    # Markdown, and the only home of two numbers. Declared so they are hashed;
    # fig05 must still say they came from prose, because the cheap certify layer
    # caps its anomaly list and the JSON carries no pixel keys at all.
    Source(
        key="a2_report",
        path="cold-start-a2/A2_REPORT.md",
        figures=("fig05_a2_repair_loop",),
        what="the full-sweep RED pixel figures (128 unexplained of 20088 checked), which exist in no artefact",
    ),
    # ---- fig07: A0 vs A0' --------------------------------------------------
    Source(
        key="a0_score_vs_truth",
        path="cold-start-a0/artifacts/score_vs_truth.json",
        figures=("fig07_a0_vs_a0prime",),
        what="233/236 agreement and the three pairs R-05 named before the score existed",
    ),
    # A0' is cold-start-a0/prime/. P-21's PLAN.md read a0-spike as A0', which is
    # a different world run by the other track -- see PLAN.md section 2 for the
    # correction and papers/phase1-workshop/sections/03_a0.md for the source.
    Source(
        key="a0prime_report",
        path="cold-start-a0/prime/artifacts/prime_report.json",
        figures=("fig07_a0_vs_a0prime",),
        what="A0': run A coverage/accuracy, run B's seeded error, the probe counts",
    ),
    # ---- fig04: A3 transfer ------------------------------------------------
    Source(
        key="a3_bill_table",
        path="cold-start-a3/artifacts/bill_table.json",
        figures=("fig04_a3_transfer",),
        what="the like-for-line level-2 comparison: from-scratch vs transfer, per meter line, with the cross-level warning in `note`",
    ),
    Source(
        key="a3_score_vs_truth",
        path="cold-start-a3/artifacts/score_vs_truth.json",
        figures=("fig04_a3_transfer",),
        what="accuracy over every reachable (state, action) pair, with the real n (248/252/252)",
    ),
    Source(
        key="a3_bill_l2_transfer",
        path="cold-start-a3/artifacts/bill_l2_transfer.json",
        figures=("fig04_a3_transfer",),
        what="the transfer arm's bill as an event sequence: seq, amount, running_total, why",
    ),
    Source(
        key="a3_bill_l2_scratch",
        path="cold-start-a3/artifacts/bill_l2_from_scratch.json",
        figures=("fig04_a3_transfer",),
        what="the control arm's bill, same event shape",
    ),
    Source(
        key="a3_provenance_transfer",
        path="cold-start-a3/artifacts/provenance_l2_transfer.json",
        figures=("fig04_a3_transfer",),
        what="6 derived / 3 supplied -- the three level constants handed to every arm alike",
    ),
    Source(
        key="a3_negative_controls",
        path="cold-start-a3/artifacts/negative_controls.json",
        figures=("fig04_a3_transfer",),
        what="the safety valve: both rewired worlds caught, neither claimed a win, and static certify caught none of them",
    ),
    # The toolchain-tax count and several caveat quotations live only in the
    # report's prose. Declared so they are hashed: a figure asserting "2 of the
    # control arm's 5 theorize rounds were toolchain conformance" while the
    # report has moved on is exactly the drift this registry exists to catch.
    Source(
        key="a3_report",
        path="cold-start-a3/A3_REPORT.md",
        figures=("fig04_a3_transfer",),
        what="the toolchain-tax count, the broken-blind incident, levels-not-games, structural-not-economic -- prose that no JSON carries",
    ),
)

# --------------------------------------------------------------------------
# Declared by rule
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Rule:
    """A family of sources, declared by where it lives instead of by name.

    ``root`` is scanned (one level, sorted) for entries matching ``pattern``.
    ``members`` are the filenames taken from each matching directory, or -- when
    ``pattern`` matches files directly -- the single matched file.

    ``floor`` is how many members were on disk when this rule was written and
    checked. Finding fewer stops the build. Finding *more* is the point.
    """

    name: str
    root: str  # repo-relative, forward slashes
    pattern: str  # fnmatch, against the entry name inside root
    kind: str  # "dir" -- entries are run directories; "file" -- entries are files
    members: tuple[str, ...]  # for kind="dir": filenames required inside it
    figures: tuple[str, ...]
    what: str
    floor: int
    floor_note: str
    tracked: bool = True
    optional: bool = False
    #: Paths declared whether or not they exist. A known-absent input has to be
    #: *named* in SOURCES.sha256; a rule that simply finds nothing would erase
    #: the fact that the input was ever expected.
    expected: tuple[str, ...] = ()
    expected_note: str = ""

    @property
    def abs_root(self) -> str:
        return os.path.join(REPO_ROOT, *self.root.split("/"))


#: The three families fig02 reads. Each replaces a hand-maintained tuple that
#: had already gone stale by the time P8 read it.
DISCOVERY: tuple[Rule, ...] = (
    Rule(
        name="theoria_run",
        root="theoria-arm/runs",
        pattern="*",
        kind="dir",
        members=("cost_curve.json", "MANIFEST.json"),
        figures=("fig02_bill_shape",),
        what="a theoria-arm run: per-desk-call cost, and the manifest carrying "
        "arm/game_id/outcome and the arm's own cost reconciliation",
        floor=4,
        floor_note="4 of the 9 directories under theoria-arm/runs/ carried both a "
        "cost_curve.json and a MANIFEST.json on 2026-07-28. The other five are "
        "salvage and preflight directories with neither; they are skipped by the "
        "members rule, not by being absent from a list. Fewer than 4 means the arm "
        "lost a run and the bill would silently understate what it cost.",
    ),
    Rule(
        name="pilot_rollup",
        root="baseline-arms/out",
        pattern="pilot_*.json",
        kind="file",
        members=(),
        figures=("fig02_bill_shape",),
        what="per-run roll-up: cost_usd, model_calls, actions_ok/failed, outcome, budget. "
        "outcome is what draws a curve solid, dashed or dotted",
        floor=6,
        floor_note="6 pilot_*.json roll-ups are tracked in baseline-arms/out/. Four were "
        "named in the old ROLLUP_KEYS tuple; pilot_g50t_sonnet_rerun.json and "
        "pilot_sk48_sonnet_rerun.json were not, so two runs with committed outcomes were "
        "drawn as outcome-unknown -- one of them a model_error the plate exists to warn about.",
    ),
    Rule(
        name="envelope_ledger",
        root="baseline-arms/out/shards",
        pattern="ledger.*.jsonl",
        kind="file",
        members=(),
        figures=("fig02_bill_shape",),
        what="envelope campaign ledger shard, same two dialects as the pilot ledger",
        floor=0,
        floor_note="untracked in master by design, so the floor is zero: absent is the "
        "expected state, and a build that required them could not run from a clean "
        "checkout. The four known shard paths are declared below regardless, so the "
        "manifest names them as absent rather than forgetting them.",
        tracked=False,
        optional=True,
        expected=(
            "baseline-arms/out/shards/ledger.ar25.jsonl",
            "baseline-arms/out/shards/ledger.g50t.jsonl",
            "baseline-arms/out/shards/ledger.sk48.jsonl",
            "baseline-arms/out/shards/ledger.tn36.jsonl",
        ),
        expected_note="untracked in master; a figure built on it cannot be rebuilt from a "
        "clean checkout. Drop it in and it is picked up automatically -- and now so is any "
        "shard whose name nobody wrote down here.",
    ),
)


def _rule_key(rule: Rule, entry: str, member: str = "") -> str:
    """Stable key for a discovered source. Derived from the path, never counted.

    Positional keys (``theoria_run_1``) would renumber the moment a directory
    landed out of alphabetical order, silently repointing whatever referenced
    them.
    """
    stem = entry
    if member:
        stem = f"{entry}/{member}"
    return f"{rule.name}:{stem}"


def _tracked_paths(root: str) -> frozenset[str] | None:
    """Repo-relative paths git tracks under ``root``, or ``None`` if git cannot say.

    Discovery widened the blast radius of an untracked file: before, only the
    paths named here were read, so a stray ``pilot_scratch.json`` in
    ``baseline-arms/out/`` was invisible. A rule would pick it up, hash it into
    ``SOURCES.sha256`` and feed its rows to a figure -- on one machine and not
    on another, which is the determinism requirement failing at its root.

    So a ``tracked=True`` rule discovers only what git tracks. That is not a new
    policy, it is this module's third opening rule made to apply to rules as
    well as to names: a source that is not committed cannot be rebuilt from a
    clean checkout. It also keeps the promise the work order actually asked for
    -- a run that lands enters the figure with **no code edit** -- because
    committing the data is not a code edit.
    """
    try:
        proc = subprocess.run(
            ["git", "-C", REPO_ROOT, "ls-files", "-z", "--", root],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "GIT_PAGER": "cat"},
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return frozenset(p for p in proc.stdout.split("\0") if p)


#: Rules whose tracked-only filter could not be applied, with the reason. Empty
#: on any normal checkout. Reported by ``build_all.py`` rather than swallowed:
#: falling back to "discover everything" is a *weaker* guarantee, and a weaker
#: guarantee that nobody is told about is the failure mode this repository keeps
#: rediscovering.
TRACKING_UNAVAILABLE: list[str] = []


def _scan(rule: Rule) -> list[str]:
    """Entry names under ``rule.root`` matching ``rule.pattern``, sorted.

    Sorted because directory iteration order is not something to trust in a
    pipeline whose whole promise is byte-identical output. Returns ``[]`` when
    the root does not exist -- that is what the floor is for.
    """
    try:
        entries = os.listdir(rule.abs_root)
    except OSError:
        return []
    named = sorted(e for e in entries if fnmatch.fnmatch(e, rule.pattern))
    if not rule.tracked:
        return named  # untracked by design; the floor for these rules is zero

    tracked = _tracked_paths(rule.root)
    if tracked is None:
        TRACKING_UNAVAILABLE.append(
            f"rule {rule.name!r}: git could not list tracked files under {rule.root}/, "
            "so discovery fell back to every matching entry on disk. An untracked file "
            "here would enter the build on this machine and not on a clean checkout."
        )
        return named
    keep = []
    for entry in named:
        prefix = f"{rule.root}/{entry}"
        # A directory entry counts as tracked when git tracks anything inside
        # it; the member check below decides whether it is a run this rule
        # describes.
        if prefix in tracked or any(p.startswith(prefix + "/") for p in tracked):
            keep.append(entry)
    return keep


def _discover(rule: Rule) -> tuple[Source, ...]:
    found: list[Source] = []
    seen_paths: set[str] = set()
    tracked = _tracked_paths(rule.root) if rule.tracked else None

    def usable(rel: str, abs_path: str) -> bool:
        if not os.path.exists(abs_path):
            return False
        return tracked is None or rel in tracked

    for entry in _scan(rule):
        abs_entry = os.path.join(rule.abs_root, entry)
        if rule.kind == "dir":
            if not os.path.isdir(abs_entry):
                continue
            # Every member must be present **and tracked**. A run directory with
            # a manifest and no cost curve is not half a run; it is a directory
            # this rule does not describe, and guessing which half to use is how
            # a cost column silently becomes wrong. An untracked member is the
            # same problem wearing a different hat: it is there on this machine
            # and not on a clean checkout.
            if not all(
                usable(f"{rule.root}/{entry}/{m}", os.path.join(abs_entry, m))
                for m in rule.members
            ):
                continue
            for member in rule.members:
                rel = f"{rule.root}/{entry}/{member}"
                seen_paths.add(rel)
                found.append(
                    Source(
                        key=_rule_key(rule, entry, member),
                        path=rel,
                        figures=rule.figures,
                        what=f"{rule.what} [{member}]",
                        tracked=rule.tracked,
                        optional=rule.optional,
                        note=f"discovered by rule {rule.name!r}",
                    )
                )
        else:
            rel = f"{rule.root}/{entry}"
            if not os.path.isfile(abs_entry) or not usable(rel, abs_entry):
                continue
            seen_paths.add(rel)
            found.append(
                Source(
                    key=_rule_key(rule, entry),
                    path=rel,
                    figures=rule.figures,
                    what=rule.what,
                    tracked=rule.tracked,
                    optional=rule.optional,
                    note=f"discovered by rule {rule.name!r}",
                )
            )

    # Expected-but-absent paths stay declared, so the manifest still names them.
    for rel in rule.expected:
        if rel in seen_paths:
            continue
        found.append(
            Source(
                key=_rule_key(rule, rel.rsplit("/", 1)[-1]),
                path=rel,
                figures=rule.figures,
                what=rule.what,
                tracked=rule.tracked,
                optional=True,
                note=rule.expected_note or f"expected by rule {rule.name!r}",
            )
        )
    return tuple(found)


#: Discovered sources, per rule, in rule order then path order.
DISCOVERED: dict[str, tuple[Source, ...]] = {r.name: _discover(r) for r in DISCOVERY}

SOURCES = SOURCES + tuple(s for r in DISCOVERY for s in DISCOVERED[r.name])

BY_KEY = {s.key: s for s in SOURCES}

if len(BY_KEY) != len(SOURCES):
    raise RuntimeError("two sources share a key; discovery keys must be path-derived")

# A path declared twice would be hashed twice in SOURCES.sha256, and the second
# line would look like drift the first time one of the two entries was edited.
_seen_paths: dict[str, str] = {}
for _s in SOURCES:
    if _s.path in _seen_paths:
        raise RuntimeError(
            f"{_s.path} is declared twice ({_seen_paths[_s.path]!r} and {_s.key!r}); "
            "a discovery rule and a hand-written Source are covering the same file"
        )
    _seen_paths[_s.path] = _s.key


def rule(name: str) -> Rule:
    for r in DISCOVERY:
        if r.name == name:
            return r
    raise KeyError(f"{name!r} is not a declared discovery rule")


def discovered(name: str) -> tuple[Source, ...]:
    """Sources a rule found, in sorted path order. Empty is a legal answer."""
    rule(name)  # raises on a typo rather than returning nothing
    return DISCOVERED[name]


def discovered_groups(name: str) -> list[tuple[str, dict[str, Source]]]:
    """For ``kind='dir'`` rules: ``[(entry_name, {member: Source}), ...]``, sorted.

    The caller gets a run at a time instead of a flat file list, so it cannot
    accidentally pair one run's manifest with another's cost curve.
    """
    r = rule(name)
    if r.kind != "dir":
        raise ValueError(f"rule {name!r} is kind={r.kind!r}; it has no groups")
    groups: dict[str, dict[str, Source]] = {}
    for src in DISCOVERED[name]:
        entry, member = src.path[len(r.root) + 1 :].split("/", 1)
        groups.setdefault(entry, {})[member] = src
    return sorted(groups.items())


def floor_violations() -> list[str]:
    """Rules that found fewer members than were on disk when they were written."""
    out = []
    for r in DISCOVERY:
        if r.kind == "dir":
            n = len(discovered_groups(r.name))
        else:
            n = sum(1 for s in DISCOVERED[r.name] if s.exists())
        if n < r.floor:
            out.append(
                f"rule {r.name!r} found {n} member(s) under {r.root}/{r.pattern}, "
                f"floor is {r.floor}. {r.floor_note}"
            )
    return out

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
    """Everything that must be on disk and is not. Empty list means green.

    Two kinds of failure, deliberately reported through one door so that
    ``verify.sh`` gate 0 catches both: a *named* source that is missing, and a
    *rule* that came back under its floor. The second is the one that matters
    for a discovery registry -- a family that silently emptied out reads exactly
    like a family that is fine.
    """
    missing = [s.path for s in SOURCES if not s.optional and not s.exists()]
    return missing + floor_violations()
