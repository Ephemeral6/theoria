"""Regenerate `engine-rig/ENGINE_TABLE.md` from the artifacts under `runs/`.

The paper's §3 table has one row per engine: what it solves, the fixture it was
validated on, how the claim was re-checked, and its **known boundary**. This
module builds that table.

Design rule, and the whole point of the file
--------------------------------------------
**No number in the table is written here.** Every cell value is *probed* out of
an artifact on disk — a JSON field, or a regex anchored in a run's Markdown
report — and the table is rendered from what the probe returned. The `expect`
field beside each probe is a tripwire, not the source: if an artifact changes
under us, `probe() != expect` and this script exits **non-zero** instead of
quietly publishing a new number under an old claim.

That is deliberate. This repository's most common defect, counted across a
whole-repo sweep on 2026-07-28, is a verdict computed correctly and then wired
to nothing. So:

    python -m tools.engine_table            # verify every fact, rewrite the table
    python -m tools.engine_table --check    # verify only; non-zero if drifted

Exit codes
----------
0   every fact verified; table written (or, under --check, already current)
1   a fact disagrees with its artifact, or the table on disk is stale
3   an artifact is missing or a probe could not run at all

3 is kept apart from 1 on purpose (D-024, D-031): a checker that fell over must
not share a return value with a checker that returned a verdict.

Determinism: the output contains no timestamp, no wall clock and no path from
this machine. Two runs are byte-identical.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

RIG = Path(__file__).resolve().parent.parent
REPO = RIG.parent
TABLE = RIG / "ENGINE_TABLE.md"

E11 = "engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep"
E2 = "engine-rig/runs/20260728T072633Z-E2-fd-ladder-bench"
E5 = "engine-rig/runs/20260728T141724Z-E5-cert-recheck"
P13 = "engine-rig/runs/p13-fd-real"
V10 = "fuzzlab/runs/20260728T152000Z-V10-fuzz-mutation-power"
G50T = "theoria-arm/runs/20260728T015354Z-g50t-first-contact"


class ProbeError(RuntimeError):
    """An artifact is missing, or a probe could not be evaluated at all."""


# --------------------------------------------------------------------------
# probes
# --------------------------------------------------------------------------

_JSON_CACHE: dict[str, object] = {}
_TEXT_CACHE: dict[str, str] = {}


def _load_json(rel: str):
    if rel not in _JSON_CACHE:
        path = REPO / rel
        if not path.exists():
            raise ProbeError(f"missing artifact: {rel}")
        _JSON_CACHE[rel] = json.loads(path.read_text(encoding="utf-8"))
    return _JSON_CACHE[rel]


def _load_text(rel: str) -> str:
    if rel not in _TEXT_CACHE:
        path = REPO / rel
        if not path.exists():
            raise ProbeError(f"missing artifact: {rel}")
        _TEXT_CACHE[rel] = path.read_text(encoding="utf-8")
    return _TEXT_CACHE[rel]


def _load_jsonl(rel: str) -> list:
    path = REPO / rel
    if not path.exists():
        raise ProbeError(f"missing artifact: {rel}")
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def md(rel: str, pattern: str):
    """Capture group 1 of `pattern` in a Markdown artifact.

    A regex that stops matching is a ProbeError, not a mismatch: the report was
    rewritten and nobody re-read it, which is a different failure from a number
    having changed.
    """

    def probe():
        m = re.search(pattern, _load_text(rel))
        if not m:
            raise ProbeError(f"pattern not found in {rel}: {pattern!r}")
        return m.group(1)

    probe.where = f"{rel} :: /{pattern}/"
    return probe


def jf(rel: str, fn, where: str):
    """A value computed from a JSON (or JSONL) artifact by `fn`."""

    def probe():
        return fn(_load_json(rel))

    probe.where = f"{rel} :: {where}"
    return probe


def jlf(rel: str, fn, where: str):
    def probe():
        return fn(_load_jsonl(rel))

    probe.where = f"{rel} :: {where}"
    return probe


# -- helpers used by the JSON probes ---------------------------------------


def _fd_row(div, instance: str, guard: str, rung: str):
    for r in div["results"]:
        if r["instance"] != instance:
            continue
        for f in r["fd"]:
            if f["guard"] == guard and f["rung"] == rung:
                return f
    raise ProbeError(f"no fd row {instance}/{guard}/{rung}")


def _fd_pair(instance: str, guard: str, rung: str):
    def fn(div):
        f = _fd_row(div, instance, guard, rung)
        return f"{f['expansions_before']} -> {f['expansions_after']}"

    return fn


def _zs_groups(rows):
    """(n_features, space_dimension, difference_rank, coverage) -> row count."""
    c = collections.Counter()
    for o in rows:
        if o.get("engine") != "zero_space":
            continue
        p = o["payload"]
        c[(len(p["features"]), p["space_dimension"], p["difference_rank"], o["evidence"]["coverage"])] += 1
    return c


# --------------------------------------------------------------------------
# the facts
# --------------------------------------------------------------------------
# key -> (expected value, probe). Nothing below is a claim about an engine; it
# is a claim about what an artifact says. The prose that turns these into claims
# lives in ROWS, and every number there is a {key} substitution.

FACTS: dict[str, tuple[object, object]] = {
    # ---- mdl_segmenter (E11, reconstruction) ----
    "mdl.worlds": ("300", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"(\d+) `gridworld` worlds, seeds")),
    "mdl.cells": ("506 302", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"\| cells total \| ([\d ]+) \|")),
    "mdl.cells_wrong": ("0", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"cells \*\*wrong\*\*.*?\| \*\*(\d+) \(0\.0000 %\)\*\* \|")),
    "mdl.unrecoverable": ("18 118", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"cells \*\*unrecoverable\*\*.*?\| \*\*([\d ]+) \(3\.5785 %\)\*\* \|")),
    "mdl.unrecoverable_pct": ("3.5785", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"unrecoverable.*?\((\d\.\d+) %\)")),
    "mdl.objid_worlds": ("126", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"n_tracks > 2\*\*b_objid` \| \*\*(\d+) / 300")),
    "mdl.objid_undercharge": ("5.7", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"9675 bits over 168 843 bits of script \((\d\.\d) %\)")),
    "mdl.verdict_flips": ("10", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"stop beating the baseline once the id is honest \| \*\*(\d+)\*\*")),
    "mdl.operator_same": ("0 / 800", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"`segment_operator` string differs \| \*\*(\d+ / \d+)\*\*")),
    "mdl.operator_differs": ("479 / 800", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"produce \*\*different track counts\*\* \| \*\*(\d+ / \d+)")),
    "mdl.events_repriced": ("6939", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"every individual event's `bits` field\*\* \((\d+) events\)")),
    "mdl.unaudited": ("8", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| mdl_segmenter \| 18 \| 8 \| 2 \| \*\*(\d+)\*\*")),
    # ---- cegis_miner (E11, brute force + adversarial) ----
    "cegis.worlds": ("193", md(f"{E11}/partials/cegis_miner-via-bruteforce.md", r"\| `gridworld` seeds 1–200 \| (\d+) judged")),
    "cegis.ground": ("932", md(f"{E11}/partials/cegis_miner-via-bruteforce.md", r"judged, 7 unminable \| 4 277 \| (\d+) \|")),
    "cegis.lifted": ("149", md(f"{E11}/partials/cegis_miner-via-bruteforce.md", r"unminable \| 4 277 \| 932 \| (\d+) \|")),
    "cegis.frontier_missing_within": ("0", md(f"{E11}/partials/cegis_miner-via-bruteforce.md", r"own `frontier_max_size` \| 0 \| (\d+) \(depth 3")),
    "cegis.lifted_tautological": ("104", md(f"{E11}/partials/cegis_miner-via-bruteforce.md", r"\*\*(\d+) of 149 lifted rules carry the tautological guard")),
    "cegis.lifted_bad": ("91", md(f"{E11}/partials/cegis_miner-via-bruteforce.md", r"\*\*(\d+) of 149 lifted rules \(61 %\), 342 rows, 90 worlds\*\*")),
    "cegis.lifted_bad_rows": ("342", md(f"{E11}/partials/cegis_miner-via-bruteforce.md", r"91 of 149 lifted rules \(61 %\), (\d+) rows")),
    "cegis.applicable_not_derivable": ("131 / 149", md(f"{E11}/ADVERSARIAL-cegis.md", r"lifted rules whose published `applicable` != the guard's firing set : (\d+ / \d+)")),
    "cegis.track0_worlds": ("72", md(f"{E11}/ADVERSARIAL-cegis.md", r"track0 NOT mover   : (\d+)")),
    "cegis.track0_rows": ("1209", md(f"{E11}/ADVERSARIAL-cegis.md", r"MOVE events in those worlds               : (\d+)")),
    "cegis.track0_motionless": ("72", md(f"{E11}/ADVERSARIAL-cegis.md", r"tracked object motionless in EVERY frame  : (\d+)")),
    "cegis.battery_green": ("188", md(f"{E11}/ADVERSARIAL-cegis.md", r"battery verdict over the union           : \{'EMPTY': (\d+)\}")),
    "cegis.unaudited": ("14", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| cegis_miner \| 20 \| 3 \| 3 \| \*\*(\d+)\*\*")),
    # ---- zero_space (E11 + adversarial; D-003 is the exemption) ----
    "zs.worlds": ("200", md(f"{E11}/partials/zero_space-via-lp.md", r"N = \*\*(\d+)\*\* 个 `parityworld` 世界")),
    "zs.falsified_laws": ("102", md(f"{E11}/ADVERSARIAL-zero_space.md", r"13 个种子完全相同，(\d+) 条、1832 vs 1788 完全相同")),
    "zs.dirty_worlds": ("13", md(f"{E11}/partials/zero_space-via-lp.md", r"世界一致，(\d+)/200 不一致")),
    "zs.k2_clean": ("0/135", md(f"{E11}/partials/zero_space-via-lp.md", r"k=2 世界 (\d+/\d+) 受影响")),
    "zs.k3_dirty": ("13/65", md(f"{E11}/partials/zero_space-via-lp.md", r"k≥3 世界 (\d+/\d+) 受影响")),
    "zs.same_span": ("200/200", md(f"{E11}/ADVERSARIAL-zero_space.md", r"(\d+/\d+) 与独立 oracle 同张成")),
    "zs.g50t_rows": (1821, jlf(f"{G50T}/candidates.jsonl", lambda rs: sum(1 for o in rs if o.get("engine") == "zero_space"), "count(engine==zero_space)")),
    "zs.g50t_worst": ("370 features, 6 transitions, difference_rank 4, 366-dim law space", jlf(
        f"{G50T}/candidates.jsonl",
        lambda rs: (lambda g: (lambda k: f"{k[0]} features, {int(k[3].split('/')[1])} transitions, difference_rank {k[2]}, {k[1]}-dim law space")(max(g, key=lambda k: g[k])))(_zs_groups(rs)),
        "modal (n_features, space_dimension, difference_rank, coverage) group")),
    "zs.g50t_coverage_full": (True, jlf(f"{G50T}/candidates.jsonl", lambda rs: all(
        o["evidence"]["coverage"].split("/")[0] == o["evidence"]["coverage"].split("/")[1]
        for o in rs if o.get("engine") == "zero_space"), "every zero_space row has coverage k == n")),
    "zs.unaudited": ("5", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| zero_space \| 11 \| 3 \| 3 \| \*\*(\d+)\*\*")),
    # ---- lp_potential (E11, exhaustive enumeration) ----
    "lp.worlds": ("3000", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"\* \*\*(\d+) worlds\.\*\* `n_pos` 4–9")),
    "lp.states": ("505 312", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"most \*\*512 states per world\*\*; ([\d ]+) states enumerated")),
    "lp.unreachable": ("2189", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"unreachable\*\* \(exhaustive\) \| (\d+) \|")),
    "lp.certificates": ("1550", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"certificate issued \| (\d+) \| 51\.7 %")),
    "lp.false_certificates": ("0", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"certificate issued on a \*\*reachable\*\* world \| 1550 certificates \| \*\*(\d+)\*\*")),
    "lp.admissibility_checks": ("42 090", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"`h\(s\) > true distance\(s\)` \| ([\d ]+) comparisons")),
    "lp.incomplete": ("639 / 2189 = 29.2 %", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"incompleteness rate is \*\*(639 / 2189 = 29\.2 %)")),
    "lp.incomplete_of_all": ("21.3", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"of truly\nunreachable worlds\*\* \((\d+\.\d) % of all worlds\)")),
    "lp.correct_decline": ("24.0", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"because the goal \*\*is reachable\*\* — \*correct\* \| (\d+\.\d) % \|")),
    "lp.headline_46": ("46.6", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"at the campaign's own N = 500 I get \*\*(\d+\.\d) %")),
    "lp.box_blocked": ("1", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"\*\*feasible once the box is widened\*\* \| \*\*(\d+)\*\* \|")),
    "lp.no_farkas": ("638", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"For the (\d+) worlds I call\n  genuinely incomplete")),
    "lp.heuristic_none_when_solvable": ("811", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"solvable configuration\*\* . on all (\d+)\ngenuinely reachable worlds")),
    "lp.unaudited": ("14", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| lp_potential \| 26 \| 4 \| 8 \| \*\*(\d+)\*\*")),
    # ---- fd_adapter (E2 bench, P13 cross-check, E11 grounder) ----
    "fd.crosscheck_agree": ("7 / 7", jf(f"{P13}/dividend.json", lambda d: f"{sum(1 for c in d['cross_check'] if c['agree'])} / {len(d['cross_check'])}", "cross_check[*].agree")),
    "fd.open4far_actions": ("112", md(f"{E11}/partials/deadlock-via-reachability.md", r"\| `sokoban-open4far` \| (\d+) \| 3352")),
    "fd.open4far_states": ("3352", md(f"{E11}/partials/deadlock-via-reachability.md", r"\| `sokoban-open4far` \| 112 \| (\d+) \|")),
    "fd.open4far_optimal": ("11", md(f"{E11}/partials/deadlock-via-reachability.md", r"\| `sokoban-open4far` \| 112 \| 3352 \| 9552 \| 14 \| 448 \| 2904 \| yes \| \*\*(\d+)\*\*")),
    "fd.startup_ms": ("140 and 260", md("engine-rig/STATUS.md", r"sits between (\d+ and \d+) ms almost regardless of instance")),
    "fd.search_share": ("4.1 ms of a 181 ms bill", md("engine-rig/STATUS.md", r"the search itself is (4\.1 ms of a 181 ms bill)")),
    "fd.crossover": ("gripper-08", md("engine-rig/STATUS.md", r"crossover against the bundled\n  rung is at `([\w-]+)`")),
    "fd.never_fuzzed": ("stub-bfs", md("fuzzlab/MUTATION.md", r"`choose_tier`'s third clause\n\(`backends.py:152-154`\) forces `([\w-]+)` for exactly that case")),
    "fd.mutants": (6, jf("fuzzlab/out/mutation.fd_adapter.json", lambda d: len(d["mutants"]), "len(mutants)")),
    "fd.undetermined": (1, jf("fuzzlab/out/mutation.fd_adapter.json", lambda d: sum(1 for m in d["mutants"] if m.get("undetermined")), "count(undetermined)")),
    "fd.unaudited": ("4", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| fd_adapter \| 7 \| 3 \| 0 \| \*\*(\d+)\*\*")),
    # ---- probe_frontier (E11, brute force) ----
    "pf.worlds": ("4000", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"\*\*(\d+) 个世界\*\*，逐世界逐动作比对划分")),
    "pf.partition_mismatch": ("0", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"\| 划分 = 预测表分组 \| \*\*(\d+)\*\* \|")),
    "pf.entropy_dev": ("1.11e-15", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"最大偏差 `(1\.11e-15)`")),
    "pf.real_reorderings": ("0", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"\*\*(\d+) 例真实重排")),
    "pf.zero_cost_bug": ("82 / 4000", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"\| \*\*(\d+ / 4000)（2\.05 %）\*\* \| \*\*缺陷 E11-PF-1")),
    "pf.infinity_rows": ("1633 / 4000", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"\| \*\*(\d+ / 4000)\*\* \| \*\*缺陷 E11-PF-3")),
    "pf.states": ("15 290", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"每个单障碍位置 = \*\*([\d ]+) 个状态\*\*")),
    "pf.teleport_guards": ("21", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"`teleport`：\*\*(\d+) 条 guard")),
    "pf.teleport_worlds": ("18", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"`teleport`：\*\*21 条 guard，只有 (\d+) 个可区分世界")),
    "pf.unaudited": ("19", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| probe_frontier \| 29 \| 4 \| 6 \| \*\*(\d+)\*\*")),
    # ---- deadlock_carver (E11 reachability, E5 recheck, E2 dividend) ----
    "dl.claims": ("50 CONFIRMED, 0 refuted", md(f"{E11}/partials/deadlock-via-reachability.md", r"\*\*(50 CONFIRMED, 0 refuted)\.\*\*")),
    "dl.theorems": ("36 of 36", md(f"{E11}/partials/deadlock-via-reachability.md", r"### 6a · Deadlock claims — (36 of 36) CONFIRMED")),
    "dl.coverage_open4far": ("55.9", md(f"{E11}/partials/deadlock-via-reachability.md", r"`sokoban-open4far` \| 16 \| \*\*0\*\* \| 0 \| 1624 \| 1624 / 2904 = \*\*(\d+\.\d) %")),
    "dl.recheck_dead_regions": (18, jf(f"{E5}/recheck_report.json", lambda d: sum(1 for m in d["matrix"] if "dead" in m["certificate"]), "count(matrix[*].certificate ~ dead)")),
    "dl.far6_blind": ("3070 -> 2762", jf(f"{E2}/dividend.json", _fd_pair("far6", "singleton", "fd-optimal/blind"), "far6/singleton/blind expansions")),
    "dl.far6_lmcut": ("47 -> 47", jf(f"{E2}/dividend.json", _fd_pair("far6", "singleton", "fd-optimal/lmcut"), "far6/singleton/lmcut expansions")),
    "dl.far6_ipdb": ("18 -> 18", jf(f"{E2}/dividend.json", _fd_pair("far6", "singleton", "fd-optimal/ipdb"), "far6/singleton/ipdb expansions")),
    "dl.far6_indexed_lmcut": ("47 -> 66", jf(f"{E2}/dividend.json", _fd_pair("far6", "indexed", "fd-optimal/lmcut"), "far6/indexed/lmcut expansions")),
    "dl.full_guard_refused": (True, jf(f"{E2}/dividend.json", lambda d: "does not support axioms" in (_fd_row(d, "far6", "full", "fd-optimal/lmcut")["guard_refused"] or ""), "far6/full/lmcut guard_refused")),
    "dl.ringstuck_fd": ("0 -> 0", jf(f"{E2}/dividend.json", _fd_pair("ringstuck4", "singleton", "fd-optimal/blind"), "ringstuck4/singleton/blind expansions")),
    "dl.uncovered": ("44.1", md(f"{E11}/partials/deadlock-via-reachability.md", r"adjudicated\.\*\* (\d+\.\d) % of\n  `open4far`'s dead reachable states")),
    "dl.candidates": (17, jlf("engine-rig/artifacts/candidates.jsonl", lambda rs: sum(1 for o in rs if o.get("payload", {}).get("producer") == "deadlock_carver"), "count(payload.producer == deadlock_carver)")),
    # ---- ic3_pdr (one point, no line) ----
    "ic3.candidates": (1, jlf("engine-rig/artifacts/candidates.jsonl", lambda rs: sum(1 for o in rs if o.get("payload", {}).get("producer") == "ic3_pdr"), "count(payload.producer == ic3_pdr)")),
    "ic3.recheck_rows": (2, jf(f"{E5}/recheck_report.json", lambda d: sum(1 for m in d["matrix"] if "ic3" in m["certificate"]), "count(matrix[*].certificate ~ ic3)")),
    "ic3.recheck_verdict": ("ACCEPT against peg4-0111, REJECT against peg4-1101", jf(
        f"{E5}/recheck_report.json",
        lambda d: ", ".join(f"{m['verdict']} against {m['ruleset']}" for m in d["matrix"] if "ic3" in m["certificate"]),
        "matrix[ic3][*].verdict + .ruleset")),
    "ic3.states": ("16", md(f"{E11}/partials/deadlock-via-reachability.md", r"successor relation over all (\d+) states")),
    "ic3.fuzz_engines": (0, jf("fuzzlab/out/campaign.json", lambda d: sum(1 for e in d["engines"] if e["engine"] == "ic3_pdr"), "count(engines[*].engine == ic3_pdr)")),
    # ---- cross-cutting ----
    "rig.candidates": (44, jlf("engine-rig/artifacts/candidates.jsonl", len, "line count")),
    "rig.campaign_worlds": (500, jf("fuzzlab/out/campaign.json", lambda d: d["worlds_per_engine"], "worlds_per_engine")),
    "rig.campaign_violations": (0, jf("fuzzlab/out/campaign.json", lambda d: sum(e["violated"] for e in d["engines"]), "sum(engines[*].violated)")),
    "rig.published_fields": ("111", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| \*\*合计\*\* \| \*\*(\d+)\*\*")),
    "rig.unaudited_fields": ("64", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| \*\*合计\*\* \| \*\*111\*\* \| \*\*25\*\* \| \*\*22\*\* \| \*\*(\d+)\*\*")),
    "rig.mutants": (55, jf("fuzzlab/out/mutation.cegis_miner.json", lambda _: sum(
        len(json.loads((REPO / f"fuzzlab/out/mutation.{e}.json").read_text(encoding="utf-8"))["mutants"])
        for e in ("cegis_miner", "fd_adapter", "lp_potential", "mdl_segmenter", "probe_frontier", "zero_space")),
        "sum over the six mutation.<engine>.json of len(mutants)")),
    "rig.survivors": (15, jf("fuzzlab/out/mutation.cegis_miner.json", lambda _: sum(
        sum(1 for m in json.loads((REPO / f"fuzzlab/out/mutation.{e}.json").read_text(encoding="utf-8"))["mutants"] if m.get("survived"))
        for e in ("cegis_miner", "fd_adapter", "lp_potential", "mdl_segmenter", "probe_frontier", "zero_space")),
        "sum over the six mutation.<engine>.json of count(survived)")),
    "e5.forgeries": (31, jf(f"{E5}/recheck_report.json", lambda d: d["counts"]["forgeries"], "counts.forgeries")),
    "e5.forgeries_accepted": (2, jf(f"{E5}/recheck_report.json", lambda d: d["forgeries"]["n_accepted"], "forgeries.n_accepted")),
    "e5.matrix_rows": (22, jf(f"{E5}/recheck_report.json", lambda d: d["counts"]["matrix_rows"], "counts.matrix_rows")),
    "e5.green": (True, jf(f"{E5}/recheck_report.json", lambda d: d["green"], "green")),
    # ---- denominators and fixture sizes, so that no bare numeral in the table
    #      is unbacked. Added after a self-audit found 40 of them.
    "mdl.frames": ("6993", md(f"{E11}/partials/mdl_segmenter-via-reconstruction.md", r"`\[0,300\)`; grids 5x5 to 12x12, (\d+) frames")),
    "mdl.published": ("18", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| mdl_segmenter \| (\d+) \|")),
    "cegis.published": ("20", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| cegis_miner \| (\d+) \|")),
    "zs.published": ("11", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| zero_space \| (\d+) \|")),
    "lp.published": ("26", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| lp_potential \| (\d+) \|")),
    "fd.published": ("7", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| fd_adapter \| (\d+) \|")),
    "pf.published": ("29", md(f"{V10}/PUBLISHED_VS_AUDITED.md", r"\| probe_frontier \| (\d+) \|")),
    "cegis.fixtureA_transitions": ("49", md(f"{E11}/partials/cegis_miner-via-bruteforce.md", r"\| Fixture A \(cart world\) \| 1 \| (\d+) \|")),
    "cegis.transitions": ("4 277", md(f"{E11}/partials/cegis_miner-via-bruteforce.md", r"\| `gridworld` seeds 1–200 \| 193 judged, 7 unminable \| ([\d ]+) \|")),
    "cegis.depth4_subsets": ("635", md(f"{E11}/partials/cegis_miner-via-bruteforce.md", r"`C\(\|V\|,4\)` with\n  `\|V\| ≈ 64` is ~(\d+) k subsets")),
    "lp.max_npos": ("9", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"\* \*\*3000 worlds\.\*\* `n_pos` 4–(\d+)")),
    "lp.max_states": ("512", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"so at\n  most \*\*(\d+) states per world\*\*")),
    "lp.weight_bound": ("10", md(f"{E11}/partials/lp_potential-via-exhaustive.md", r"`solve_certificate\(\.\.\., margin: int = 1, bound: int = (\d+)\)`")),
    "pf.rules": ("9", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"的 \*\*(\d+) 条规则\*\*（guard 数")),
    "pf.evals_per_rule": ("61 160", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"每条规则 ([\d ]+) 次\n?探针求值")),
    "pf.ulp": ("5", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"约 (\d+) ULP")),
    "pf.argmax_states": ("16", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"argmax \*\*在 (\d+) 个状态上改变\*\*")),
    "zs.fixtureB_features": ("16", md(f"{E11}/partials/probe_frontier-via-bruteforce.md", r"`analyse` 给出：(\d+) 个特征")),
    "dl.far6_blind_pct": ("-10.0", jf(f"{E2}/dividend.json", lambda d: (lambda f: f"{100 * (f['expansions_after'] - f['expansions_before']) / f['expansions_before']:.1f}")(_fd_row(d, "far6", "singleton", "fd-optimal/blind")), "far6/singleton/blind, (after-before)/before")),
    "dl.m9_ringstuck": ("44 → 22", md("engine-rig/STATUS.md", r"M9's (44 → 22) is a fact about the bundled search")),
}


# --------------------------------------------------------------------------
# the table
# --------------------------------------------------------------------------
# Each row is (engine, solves, fixture, recheck, boundary). Every numeral in the
# strings below is a {key} into FACTS. `boundary` may never be empty — the
# renderer refuses to emit a row whose boundary cell is blank, and a process
# whose boundary was never measured must say so in those words.

UNMEASURED = "边界未测"

ROWS = [
    dict(
        engine="`mdl_segmenter`",
        solves="Trajectory → objects and events, priced in bits. The segmentation with the shortest description wins.",
        fixture="Fixture A `cart_world`; {mdl.worlds} `gridworld` worlds, {mdl.frames} frames, {mdl.cells} cells, {mdl.events_repriced} events (E11)",
        recheck="**Independent checker.** The published payload alone is replayed back into frames by a reconstructor the rig does not contain; the cost model is re-derived from the README's bit table, not imported from `costs.py`; all {mdl.events_repriced} events are re-priced individually.",
        boundary=(
            "**Measured.** Geometry is exact — **{mdl.cells_wrong} wrong cells in {mdl.cells}** — but per-cell colour of non-uniform objects is not published at all: "
            "{mdl.unrecoverable} cells ({mdl.unrecoverable_pct} %) are unrecoverable, and `color: null` is a perfect predictor of which. "
            "The `objid` field is sized from the components in one *frame* while tracks span the trajectory, so **{mdl.objid_worlds}/{mdl.worlds} worlds cannot number their own tracks**; "
            "correcting the {mdl.objid_undercharge} % undercharge makes **{mdl.verdict_flips} worlds stop beating the per-pixel baseline**, on this engine's own headline comparison. "
            "`segment_operator` is a string literal: {mdl.operator_same} payloads differ across the two operators where {mdl.operator_differs} real track counts do. "
            "{mdl.unaudited} of {mdl.published} published fields are asserted by no invariant."
        ),
    ),
    dict(
        engine="`cegis_miner`",
        solves="Counterexample-guided synthesis of guarded rules against an exact ledger, plus the frontier of minimal guards the evidence cannot yet separate.",
        fixture="Fixture A ({cegis.fixtureA_transitions} transitions); {cegis.worlds} `gridworld` worlds, {cegis.transitions} transitions, {cegis.ground} ground + {cegis.lifted} lifted rules (E11)",
        recheck="**Independent checker + adversarial re-run.** A second guard evaluator and an exhaustive minimal-guard enumerator, written from `atoms.py`'s definitions without executing it; a hostile reviewer reproduced every count bit-for-bit and overturned one of the conclusions.",
        boundary=(
            "**Measured.** Frontier completeness holds *within* each rule's declared `frontier_max_size` — **{cegis.frontier_missing_within} omissions** — and the published field is accurate; the module constant's comment promising depth 3 is not. "
            "Lifted rules are the boundary: **{cegis.lifted_tautological}/{cegis.lifted} carry the guard `[\"act==?dir\"]`**, **{cegis.lifted_bad}/{cegis.lifted} fire on transitions where the promised move does not occur** ({cegis.lifted_bad_rows} rows), and **{cegis.applicable_not_derivable}** publish an `applicable` that is not derivable from their own guard. "
            "`transitions_from_segmentation` defaults to `tracks[0]`, so **{cegis.track0_worlds}/{cegis.worlds} worlds mine a static obstacle** — the {cegis.track0_rows} resulting rows are *true statements about that rock* ({cegis.track0_motionless}/{cegis.track0_worlds} worlds: zero displacement throughout), and the defect is that `rule_hypothesis` carries no object binding while `object_hypothesis` beside it does. "
            "The fuzz battery returns **zero findings on all {cegis.battery_green}** affected worlds; {cegis.unaudited} of {cegis.published} published fields are asserted by no invariant. "
            "Minimal guards of 4+ literals, and every world family but the grid, are **{unmeasured}**: `C(|V|,4)` at |V| ~ 64 is ~{cegis.depth4_subsets} k subsets per rule and a sampled sweep reported as a pass would claim coverage it does not have."
        ),
    ),
    dict(
        engine="`zero_space`",
        solves="GF(2) null space of the observed difference vectors → the linear conservation laws the evidence supports, split into encoding-local and world-level.",
        fixture="Fixture B `pair_flip` ({zs.fixtureB_features} features); {zs.worlds} `parityworld` worlds (E11); {zs.g50t_rows} laws published on the live ARC game `g50t` (development pile)",
        recheck="**Independent checker, plus a borrowed quantifier.** A second GF(2) implementation agrees on the span in **{zs.same_span}** worlds; separately, `lp_potential`'s condition shape — exact `Fraction`, per move-instance, quantified over transitions rather than over the sampled trajectory — is applied to the output.",
        boundary=(
            "**Measured, and it is a pre-registered boundary rather than a defect.** Under the engine's declared quantifier (the observed trajectory) the output is correct everywhere. "
            "Strengthen the quantifier to *all legal transitions of the world* and **{zs.falsified_laws} laws in {zs.dirty_worlds}/{zs.worlds} worlds stop holding** — {zs.k2_clean} worlds at k=2, {zs.k3_dirty} at k≥3. "
            "`DECISIONS.md` **D-003** names this mechanism and rules it *still sound*: less observed difference space means a larger recovered invariant space. An adversarial review reproduced every number and overturned the word \"defect\". "
            "The scale on real data is the thing worth quoting: on `g50t` the worst group is **{zs.g50t_worst}**, and **every published row carries `coverage` k = n** — the frozen contract has no field in which evidence thinness can be stated, so a law resting on a handful of transitions and one resting on a whole campaign are indistinguishable. That gap belongs to `/CONTRACTS/`, not to this engine. "
            "{zs.unaudited} of {zs.published} published fields are asserted by no invariant. Behaviour on any family but `parityworld` and `g50t` is **{unmeasured}**."
        ),
    ),
    dict(
        engine="`lp_potential`",
        solves="Linear pagoda certificate that a goal is unreachable, verified exactly over the rationals, doubling as an admissible heuristic.",
        fixture="Fixture C `peg4` ({ic3.states} states); **{lp.worlds}** `jumpgraph` worlds, **{lp.states}** states enumerated exhaustively, no budget exhausted (E11)",
        recheck="**Certificate + independent checker.** The three conditions are re-derived in exact `Fraction` arithmetic from `spec.triples` — the world's definition — rather than from the engine's own move list, and admissibility is checked against forward BFS distances the engine never sees.",
        boundary=(
            "**Measured, and the circulating number was wrong.** Soundness is clean: **{lp.certificates} certificates, {lp.false_certificates} false**, {lp.admissibility_checks} admissibility comparisons with no violation. "
            "Incompleteness is **{lp.incomplete}** of genuinely unreachable worlds ({lp.incomplete_of_all} % of all {lp.worlds}). The **{lp.headline_46} %** figure that circulates is the *no-certificate rate*, not the incompleteness rate: {lp.correct_decline} pp of it is the engine correctly declining to prove a statement that is false. Quoting {lp.headline_46} % overstates the boundary by about 2×. "
            "Exactly **{lp.box_blocked}** of the silences is the hard-coded `bound={lp.weight_bound}` weight box rather than the mathematics. "
            "Two limits are honestly **{unmeasured}**: for the other **{lp.no_farkas}** worlds \"no linear pagoda exists\" rests on HiGHS returning float infeasibility — no exact Farkas dual was produced, so that is a solver's claim and not a proof; and `n_pos ≤ {lp.max_npos}` is the whole corpus, so nothing above {lp.max_states} states was examined and the silence-vs-size trend must not be extrapolated. "
            "One design consequence, measured: no public path yields a heuristic for a solvable configuration, so all **{lp.heuristic_none_when_solvable}** reachable worlds get no bound at all — the heuristic exists only where no search would be run. {lp.unaudited} of {lp.published} published fields are asserted by no invariant."
        ),
    ),
    dict(
        engine="`fd_adapter`",
        solves="One `solve(domain, problem)` interface over a three-rung planner ladder — bundled BFS, Fast Downward optimal, LAMA satisficing — and the rule that decides when \"no plan\" is a proof.",
        fixture="Fixture D sokoban (four levels) and a gripper size ladder (E2); the generated cold-start domains, {fd.crosscheck_agree} of them (P13)",
        recheck="**Differential + independent checker.** Every rung is run against the others on the same instance — **{fd.crosscheck_agree}** agree on plan length and on unsolvability, three of them FD independently proving an UNSAT the bundled search found — and a from-scratch grounder and BFS reproduce `open4far` at {fd.open4far_actions} ground actions, {fd.open4far_states} reachable states, optimal {fd.open4far_optimal}.",
        boundary=(
            "**Measured on cost, and explicitly {unmeasured} on the one comparison the paper wants.** "
            "The property battery has **never run against any Fast Downward rung**: `props/fd_adapter.py` calls `solve_parsed` with in-memory objects, and `choose_tier`'s third clause forces `{fd.never_fuzzed}` for that call shape — a *structural* fall-back, not an environmental one, so it holds on a machine that does have a build. Everything the fuzz campaign reports about this engine is about the bundled BFS, and **the stub-versus-real-FD difference under the battery is therefore {unmeasured}**. Measuring it needs `props` to hand `solve()` real file paths *and* an FD build; `.toolchain/` is gitignored by design, so the second half is per-machine. "
            "Of {fd.mutants} mutants one is `undetermined` — it never ran — and that column exists only because an adversarial pass found `survived` did not require the mutant to have executed. "
            "What is measured is the price: FD's cost here is startup, not search — every FD row sits between {fd.startup_ms} ms almost regardless of instance, and on `sokoban-far6` the search is {fd.search_share}. The crossover against the bundled rung is at `{fd.crossover}`, above every instance this rig generates. "
            "Exit codes cannot separate a proof from a shrug (D-024), and a cross-track audit found `cold-start-a0` reading exit 12 as a proof from the exception string alone — latent, because that pipeline runs the stub. {fd.unaudited} of {fd.published} published fields are asserted by no fuzz invariant (all four are pinned by engine-rig unit tests)."
        ),
    ),
    dict(
        engine="`probe_frontier`",
        solves="Chooses the next experiment: partitions the surviving hypotheses by predicted observation and ranks actions by information gained per unit cost.",
        fixture="{pf.worlds} synthetic hypothesis worlds; the `cart_world` frontier exhaustively — **{pf.rules}** rules × **{pf.states}** states, {pf.evals_per_rule} probe evaluations per rule (E11)",
        recheck="**Independent checker.** Entropy is recomputed by an algebraically equivalent but numerically different formula, the ranking key is rewritten rather than read, and the truth partition is taken from the raw prediction table so the input cannot grade the output.",
        boundary=(
            "**Measured.** The arithmetic is clean: {pf.partition_mismatch} partition mismatches, {pf.partition_mismatch} entropy mismatches (largest deviation {pf.entropy_dev}, about {pf.ulp} ULP), **{pf.real_reorderings} real reorderings** across {pf.worlds} worlds. "
            "The boundaries are all degeneracies and seams. A zero-cost useless action scores `inf`, ranks first, and makes `best_probe` return `None` — **{pf.zero_cost_bug} worlds discard an available 1-bit experiment** because a free option was offered. The same package holds two opposite definitions of value at cost 0 (`inf` versus `0.0`). Bare `Infinity`, which is not JSON, reaches the shared candidate stream in **{pf.infinity_rows}** rows and the frozen contract's validator passes it. "
            "And the ranking is decided by an upstream bookkeeping choice rather than by the world: `cegis_miner` deliberately keeps extensionally equal atoms apart (D-002), so `teleport`'s **{pf.teleport_guards} guards are only {pf.teleport_worlds} distinguishable worlds** — counting one vote per distinguishable world instead of one per guard moves the argmax on {pf.argmax_states} states. `Hypothesis.weight` is always 1.0, so cegis's MDL prior over guards is discarded. "
            "{pf.unaudited} of {pf.published} published fields are asserted by no invariant. The planner-backed path (`run_with_planner` / `ExecutableProbe`) has **no brute-force comparison at all — {unmeasured}** — because it needs a real Fast Downward build."
        ),
    ),
    dict(
        engine="`deadlock_carver`",
        solves="Conditional mini-unsolvability theorems, `pattern AND not-goal => dead`, proved by localised enumeration over the grounded task plus h² mutexes. The same theorem is a candidate and a planner pruner.",
        fixture="sokoban `open4` / `open4far` / `ring` / `ringstuck`; {dl.candidates} theorems in the committed candidate stream",
        recheck="**Three independent routes.** `recheck/` derives the transition relation from a rule set nobody grounded for it (**{dl.recheck_dead_regions}** `dead_region` certificates green); an E11 grounder and exhaustive reachability adjudicate **{dl.theorems}** theorems with two negative controls correctly rejected; and the theory-compiler track carries two of them as axiom-free Lean.",
        boundary=(
            "**Measured, in both directions, and one half of the original claim did not survive.** "
            "Truth is clean — across the whole unsolvability inventory, **{dl.claims}**. "
            "Completeness is capped by the evidence, not by a budget: `MAX_PATTERN = 2` is the width of an h² mutex, so the theorems cover {dl.coverage_open4far} % of `open4far`'s dead reachable states and **{dl.uncovered} % are dead for reasons no 2-atom pattern can state**. Widening it means implementing h^m, which is a different engine. "
            "The speed-up half of Theoria 1.9 **does not survive a real planner**: on `far6` the theorems buy `{dl.far6_blind}` expansions against a blind search ({dl.far6_blind_pct} %) and **`{dl.far6_lmcut}` against `lmcut`, `{dl.far6_ipdb}` against `ipdb`**. A proved deadlock is a substitute for a heuristic, not an addition to one. "
            "Pair deadlocks reach the admissible rungs only through a second encoding, and doing so is a net loss — the natural guard becomes an FD axiom and `lmcut`/`ipdb` refuse the task outright, while the STRIPS `indexed` re-encoding is accepted and expands *more* (`far6` `{dl.far6_indexed_lmcut}`). "
            "On `ringstuck` FD expands `{dl.ringstuck_fd}` either way — its translator settles the instance before search — so M9's {dl.m9_ringstuck} is a fact about the bundled BFS and never was a dividend a real planner would have collected."
        ),
    ),
    dict(
        engine="`ic3_pdr`",
        solves="The fallback inductive invariant, for the shapes where the LP is infeasible — it answers `lp_potential`'s unfinished business and reports the same three conditions.",
        fixture="Fixture C `peg4` `0111`, {ic3.states} states. **One configuration of one fixture, and nothing else.**",
        recheck="**Certificate + two independent checkers.** `check.py` re-derives the three conditions without importing the search; `recheck/` verifies it against rule sets it derives itself, as a **{ic3.recheck_rows}-row differential — {ic3.recheck_verdict}**, so the certificate is bound to the configuration it names; E11 re-checked the CNF against its own successor relation over all {ic3.states} states; the theory-compiler track carries it as Lean.",
        boundary=(
            "**{unmeasured}.** This is the honest row and it is the most useful cell in the table. "
            "The engine has exactly **{ic3.candidates}** certificate in the committed stream, on **one** configuration of **one** {ic3.states}-state fixture. Nothing measures where it stops: no state-space ladder, no predicate-count ladder, no timeout, no failure-shape census. "
            "It also has **no property module in the fuzz battery at all** — `fuzzlab/props/` covers six engines and this is not one of them, and the campaign contains **{ic3.fuzz_engines}** rows for it — so none of the {rig.campaign_worlds}-world campaign, none of the {rig.mutants} mutants and none of the {rig.published_fields}-field publication audit touches it. "
            "**What testing it would take**, concretely: a graded corpus of unsolvable configurations on which `lp_potential` is infeasible — E11's exhaustive sweep already identifies {lp.no_farkas} such `jumpgraph` worlds, though both engines hard-code peg-jump semantics, so a second world family has to be built before the ladder means anything — and, per rung, solve time, invariant size, and whether the independent checker still accepts, with the failure *shape* recorded (timeout / failed to generalise / certificate not recheckable). "
            "This is the open item `monitor/board/items/E8-ic3-scale.md`, whose own wording is the right summary: there is one point, so no line can be drawn. Until it runs, the paper may say the LP's gap is *covered on `0111`*, and may not say it is covered."
        ),
    ),
]


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------


def verify() -> tuple[dict[str, str], list[str]]:
    """Probe every fact. Returns (values, mismatches)."""
    values: dict[str, str] = {"unmeasured": UNMEASURED}
    mismatches: list[str] = []
    for key in sorted(FACTS):
        expect, probe = FACTS[key]
        got = probe()
        if got != expect:
            mismatches.append(f"  {key}: artifact says {got!r}, table expects {expect!r}\n      at {probe.where}")
        values[key] = str(got)
    return values, mismatches


_PLACEHOLDER = re.compile(r"\{([a-z0-9_.]+)\}")


def sub(text: str, values: dict[str, str]) -> str:
    """Substitute `{fact.key}` placeholders.

    `str.format` cannot do this: it reads the dot as attribute access. An
    unknown key raises rather than leaving a silent gap in the table.
    """

    def one(m):
        key = m.group(1)
        if key not in values:
            raise ProbeError(f"table references unknown fact {key!r}")
        return values[key]

    return _PLACEHOLDER.sub(one, text)


def _cell(text: str, values: dict[str, str]) -> str:
    return sub(text, values).replace("|", r"\|").replace("\n", " ")


def render(values: dict[str, str]) -> str:
    lines: list[str] = []
    w = lines.append
    w("# engine-rig · the eight processes, and what each one is worth")
    w("")
    w("Generated by `python -m tools.engine_table`. **Do not edit by hand** — every")
    w("number here is probed out of an artifact under `runs/`, and the generator exits")
    w("non-zero if any of them has drifted. The provenance table at the end names the")
    w("file and the field each number came from.")
    w("")
    w("One row per process: what it solves, where it was validated, how the claim was")
    w("re-checked by something that did not produce it, and its **known boundary**.")
    w("")
    w("**The boundary column is never blank.** Where a boundary has not been measured")
    w(f"the cell says **{UNMEASURED}** and states what measuring it would take. A table")
    w("with every cell confidently filled would suggest every cell had been tested, and")
    w("for one of these eight processes that is not true.")
    w("")
    w("## The table")
    w("")
    w("| # | 工序 | 它解决什么 | 在哪个 fixture 上被验证 | 复核方式 | 已知边界 |")
    w("|---|---|---|---|---|---|")
    for i, row in enumerate(ROWS, 1):
        boundary = row["boundary"]
        if not boundary or not boundary.strip():
            raise ProbeError(f"row {row['engine']} has an empty boundary cell")
        cells = [
            row["engine"],
            _cell(row["solves"], values),
            _cell(row["fixture"], values),
            _cell(row["recheck"], values),
            _cell(boundary, values),
        ]
        w(f"| {i} | " + " | ".join(cells) + " |")
    w("")
    w("## How to read the boundary column")
    w("")
    w("Three things are kept apart, because collapsing them is how a table like this")
    w("lies:")
    w("")
    w("* **Measured boundary** — somebody drew the line and reports where it is.")
    w("* **Pre-registered boundary** — the line was written down in `DECISIONS.md`")
    w("  before it was hit, and a later measurement quantified it. `zero_space`'s")
    w("  quantifier (D-003) and `lp_potential`'s incompleteness (D-014) are these; an")
    w("  adversarial review overturned the word \"defect\" on the first of them.")
    w(f"* **{UNMEASURED}** — nobody has drawn the line. `ic3_pdr` entire; the fuzz")
    w("  battery's view of a real Fast Downward rung; `lp_potential`'s infeasibility")
    w("  claim as a proof rather than a solver's word; `cegis_miner` past 3 literals")
    w("  and past the grid family; `probe_frontier`'s planner-backed path.")
    w("")
    w("Two numbers are corrections of figures that were circulating, and both run")
    w("against the rig's own interest:")
    w("")
    w(sub("* `lp_potential`'s incompleteness is **{lp.incomplete}**, not the {lp.headline_46} %", values))
    w(sub("  often quoted — that figure is the no-certificate rate, and {lp.correct_decline} pp of it is the", values))
    w("  engine correctly refusing to prove something false.")
    w("* `deadlock_carver`'s pruning dividend is real against a blind search and **zero**")
    w(sub("  against an admissible heuristic ({dl.far6_lmcut} on `lmcut`). The frequency half of", values))
    w("  Theoria 1.9 stands; the speed-up half does not.")
    w("")
    w("## What audits all eight, and what it does not reach")
    w("")
    w(f"* The property battery runs {values['rig.campaign_worlds']} worlds per engine with {values['rig.campaign_violations']} violations, and")
    w(f"  {values['rig.mutants']} injected defects establish that every invariant has a working detection")
    w(f"  path — {values['rig.survivors']} of them survive, which is the honest half of that sentence.")
    w(f"* It covers **six** of the eight. `deadlock_carver` and `ic3_pdr` have no property")
    w("  module. `deadlock_carver` is nonetheless the most independently adjudicated")
    w("  process here — three separate routes, one of them Lean — and `ic3_pdr` is the")
    w("  least.")
    w(f"* Of the **{values['rig.published_fields']}** leaf fields the six engines publish into `candidates.jsonl`,")
    w(f"  **{values['rig.unaudited_fields']}** are asserted by no invariant. These reach the manual, and from there")
    w("  the adjudicating LLM's beliefs, carrying no evidence at all.")
    w(f"* The certificate rechecker catalogues {values['e5.forgeries']} ways to lie to it and refuses all but")
    w(f"  {values['e5.forgeries_accepted']}; the one that works is `delete-the-rule` — a certificate true of a rule set")
    w("  with a rule missing — which is Theoria §1.3 entire and which no certificate")
    w("  checker can see.")
    w("")
    w("## Provenance")
    w("")
    w("Every number above, and where it was probed from. A number that could not be")
    w("pointed back at a run does not appear in the table.")
    w("")
    w("| key | value | artifact :: locator |")
    w("|---|---|---|")
    for key in sorted(FACTS):
        _, probe = FACTS[key]
        where = probe.where.replace("|", r"\|")
        w(f"| `{key}` | `{values[key]}` | `{where}` |")
    w("")
    w("Runs referenced: `engine-rig/runs/20260729T000000Z-E11-engine-crosscheck-deep`")
    w("(six cross-checks + two adversarial reviews), `.../20260728T072633Z-E2-fd-ladder-bench`")
    w("(the ladder and the deadlock dividend), `.../20260728T141724Z-E5-cert-recheck`")
    w("(the independent rechecker), `.../p13-fd-real` (Fast Downward connected),")
    w("`fuzzlab/runs/20260728T152000Z-V10-fuzz-mutation-power` (mutation power and the")
    w("published-versus-audited census), and `theoria-arm/runs/20260728T015354Z-g50t-first-contact`")
    w("(the one live-game artifact quoted). The generator reads them; it writes only this file.")
    w("")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="verify only; do not write")
    args = ap.parse_args(argv)

    try:
        values, mismatches = verify()
        text = render(values)
    except ProbeError as exc:
        print(f"engine_table: PROBE FAILED: {exc}", file=sys.stderr)
        return 3

    if mismatches:
        print(f"engine_table: {len(mismatches)} fact(s) disagree with their artifacts:", file=sys.stderr)
        for m in mismatches:
            print(m, file=sys.stderr)
        print("\nThe table was NOT written. Re-read the run, then update the expectation.", file=sys.stderr)
        return 1

    if args.check:
        if not TABLE.exists():
            print(f"engine_table: {TABLE.name} does not exist", file=sys.stderr)
            return 1
        current = TABLE.read_text(encoding="utf-8")
        if current != text:
            print(f"engine_table: {TABLE.name} is stale; re-run without --check", file=sys.stderr)
            return 1
        print(f"engine_table: {len(FACTS)} facts verified; {TABLE.name} is current")
        return 0

    TABLE.write_text(text, encoding="utf-8", newline="\n")
    print(f"engine_table: {len(FACTS)} facts verified against {len(set(p.where.split(' :: ')[0] for _, p in FACTS.values()))} artifacts")
    print(f"engine_table: wrote {TABLE.relative_to(REPO)} ({len(text)} bytes, {len(ROWS)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
