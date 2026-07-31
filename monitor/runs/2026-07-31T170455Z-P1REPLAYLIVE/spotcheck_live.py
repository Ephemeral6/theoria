"""P1REPLAYLIVE -- environment-side bit-exact replay spot check over the
REAL online ledgers of the canonical shared-ledger era (since S31), plus a
regression reproduction of the two archived spot checks and an integrity
sweep that recomputes every frame_hash from the stored frames.

This driver lives in the monitor territory's run archive.  It imports the
proxy territory's replay_spotcheck / ledger modules READ-ONLY and never
writes outside --out and --scratch.

Sessions fed to spotcheck():

  archive   -- reproduced canons (upgrade_ledger over the tracked
               baseline-arms shards, same commands as the P-9 and
               P1-replay-spotcheck-2 MANIFESTs) + the arc-recon precheck.
  live      -- theoria-arm run-dir ledgers (canonical v1.0).  Their openings
               are retried 400s occupying step_idx slots, so feeding them raw
               leaves zero clean sessions (verified).  The adapter follows the
               sessions_from_recon precedent: each SUCCESSFUL RESET opens a
               new pass, positions index SUCCESSFUL commands contiguously
               from 0; failed attempts returned no frame and are dropped.
  s31       -- the single real-online ar25 session in proxy/var/ledger.jsonl
               (gitignored), selected by run_start env_upstream == the real
               ARC host; the mock/loopback runs in the same file are excluded
               by the same rule, never by hand-picked run ids.

Determinism: every report is json.dumps(..., indent=2, sort_keys=True) + LF;
no wall-clock timestamp enters any output.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, REPO)

from proxy.ledger import frame_hash, read_ledger  # noqa: E402
from proxy.tools.replay_spotcheck import (  # noqa: E402
    _action_key,
    clean_prefix,
    sessions_from_canon,
    sessions_from_recon,
    spotcheck,
)

REAL_HOST = "three.arcprize.org"
GAME_AR25 = "ar25-0c556536"
GAME_G50T = "g50t-5849a774"
GAME_SK48 = "sk48-d8078629"

ARM_LEGS_G50T = [
    ("arm/20260731T1240Z-r1", "theoria-arm/runs/20260731T1240Z-A3-level2-carried/ledger.jsonl"),
    ("arm/20260731T1310Z-r2", "theoria-arm/runs/20260731T1310Z-A3-level2-carried-r2/ledger.jsonl"),
    ("arm/20260731T1430Z-r3", "theoria-arm/runs/20260731T1430Z-A3-level2-carried-r3/ledger.jsonl"),
]
ARM_LEGS_SK48 = [
    ("arm/20260728T072604Z-E3", "theoria-arm/runs/20260728T072604Z-E3-sk48-carried/ledger.jsonl"),
    ("arm/20260728T083400Z-E3v2", "theoria-arm/runs/20260728T083400Z-E3-sk48-carried-v2/ledger.jsonl"),
    ("arm/preflight-20260728T074237Z", "theoria-arm/runs/preflight-20260728T074237Z/ledger.jsonl"),
]
SHARDS = {
    "ar25": ("baseline-arms/out/shards/ledger.ar25.jsonl", "baseline-arms/out/shards/probe_log.ar25.jsonl"),
    "g50t": ("baseline-arms/out/shards/ledger.g50t.jsonl", "baseline-arms/out/shards/probe_log.g50t.jsonl"),
    "a7-g50t": ("baseline-arms/out/shards/ledger.a7-g50t.jsonl", "baseline-arms/out/shards/probe_log.a7-g50t.jsonl"),
    "a7up-opus-g50t": ("baseline-arms/out/shards/ledger.a7up-opus-g50t.jsonl", "baseline-arms/out/shards/probe_log.a7up-opus-g50t.jsonl"),
    "a7up-sonnet-g50t": ("baseline-arms/out/shards/ledger.a7up-sonnet-g50t.jsonl", "baseline-arms/out/shards/probe_log.a7up-sonnet-g50t.jsonl"),
}
RECON_LEDGER = "arc-recon/data/recon_ledger.jsonl"
P9_DIR = "proxy/runs/p9-shell-harden"
P1R2_DIR = "proxy/runs/20260731T154336Z-P1-replay-spotcheck-2"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, indent=2, sort_keys=True) + "\n")


def sessions_from_armrun(path, game_id, label):
    """Canonical v1.0 run-dir ledger -> passes of SUCCESSFUL steps.

    Precedent is sessions_from_recon: every successful RESET opens a new
    pass; within a pass, positions count successful commands contiguously
    from 0.  Failed attempts (non-200, or 200 with no frames) produced no
    frame to compare and are dropped -- they are retries of the same logical
    command, visible in the ledger under step_idx slots of their own.
    """
    records = [r for r in read_ledger(path)
               if r.get("event") == "env_step" and r.get("game_id") == game_id]
    records.sort(key=lambda r: r.get("seq", 0))
    passes = {}
    current = None
    n = 0
    for record in records:
        status = (record.get("http") or {}).get("status")
        ok = status == 200 and record.get("frames") is not None
        name = (record.get("action") or {}).get("name")
        if name == "RESET" and ok:
            n += 1
            current = []
            passes[label if n == 1 else "%s#%d" % (label, n)] = current
        if current is None or not ok:
            continue
        current.append({
            "step_idx": len(current),
            "action": _action_key(record.get("action") or {}),
            "frame_hash": record.get("frame_hash"),
            "ok": True,
        })
    return {k: v for k, v in passes.items() if v}


def live_runs_of(var_ledger_path):
    """run_id -> env_upstream for runs whose upstream is the real ARC host."""
    out = {}
    for record in read_ledger(var_ledger_path):
        if record.get("event") == "run_start":
            upstream = str(record.get("env_upstream") or "")
            if REAL_HOST in upstream:
                out[record.get("run_id")] = upstream
    return out


def merged(*session_dicts):
    out = {}
    for d in session_dicts:
        for name, steps in d.items():
            if name in out:
                raise SystemExit("session name collision: %s" % name)
            out[name] = steps
    return out


def summarize(report):
    return {
        "n_sessions": report["n_sessions"],
        "steps_compared": report["steps_compared"],
        "pairwise_comparisons": report["pairwise_comparisons"],
        "verdict": report["verdict"],
        "disagreements": len(report["disagreements"]),
    }


def adapter_honesty(paths):
    """The adapter drops failed attempts and re-bases positions, which is
    honest only if (1) no failed step carries a frame, (2) every failure is a
    retry of the command that next succeeds (no abandoned commands spliced
    over), and (3) each run-dir ledger holds a single run (the adapter is
    run_id-blind).  The audit's verification pass established all three by
    hand; this function makes them asserted, published facts."""
    out = {}
    for path in paths:
        all_records = read_ledger(path)
        records = sorted((r for r in all_records if r.get("event") == "env_step"),
                         key=lambda r: r.get("seq", 0))
        run_ids = sorted({r.get("run_id") for r in all_records if r.get("run_id")})
        failed = failed_with_frames = ok200_without_frames = abandoned = 0
        pending = []
        for r in records:
            status = (r.get("http") or {}).get("status")
            ok = status == 200 and r.get("frames") is not None
            name = (r.get("action") or {}).get("name")
            if ok:
                abandoned += sum(1 for n in pending if n != name)
                pending = []
            else:
                failed += 1
                if r.get("frames") is not None or r.get("frame_hash") is not None:
                    failed_with_frames += 1
                if status == 200:
                    ok200_without_frames += 1
                pending.append(name)
        out[path] = {
            "env_steps": len(records),
            "failed_steps": failed,
            "failed_carrying_frames": failed_with_frames,
            "status200_without_frames": ok200_without_frames,
            "abandoned_commands": abandoned,
            "trailing_failures": len(pending),
            "run_ids": run_ids,
            "single_run_id": len(run_ids) == 1,
        }
    return out


def pinned_digest_comparison(inputs, canon_digests, manifests):
    """Compare our input digests and rebuilt-canon digests against the pins
    in the two archived MANIFESTs.  The canon digests are expected to DRIFT:
    proxy/tools/upgrade_ledger.py embeds the literal command-line source path
    into lifted.source of every synthesised run_start, so the canon sha256 is
    a function of the invocation string, not of content.  The input digests
    are the real integrity channel; the session-level regression is the
    authority for the canons."""
    pinned_inputs = {}
    pinned_intermediates = {}
    for mdir, doc in manifests.items():
        for entry in doc.get("inputs", []):
            if entry.get("path") and entry.get("sha256"):
                pinned_inputs.setdefault(entry["path"], {})[mdir] = entry["sha256"]
        for name, meta in (doc.get("intermediate") or {}).items():
            if isinstance(meta, dict) and meta.get("sha256"):
                pinned_intermediates[name] = {"pinned_in": mdir, "sha256": meta["sha256"]}
    input_compare = {}
    for path, pins in sorted(pinned_inputs.items()):
        ours = inputs.get(path, {}).get("sha256")
        input_compare[path] = {
            "ours": ours,
            "pinned": pins,
            "match": ours is not None and all(v == ours for v in pins.values()),
        }
    canon_compare = {}
    for key, digest in sorted(canon_digests.items()):
        candidates = ["canon.%s.jsonl" % key, "%s_canon.jsonl" % key]
        pin = next((pinned_intermediates[c] for c in candidates if c in pinned_intermediates), None)
        canon_compare[key] = {
            "ours": digest,
            "pinned": pin,
            "match": pin is not None and pin["sha256"] == digest,
        }
    return {
        "inputs": input_compare,
        "inputs_all_match": all(v["match"] for v in input_compare.values()),
        "canons": canon_compare,
        "canon_drift_cause": "upgrade_ledger embeds the invocation source path in lifted.source, "
                             "so canon digests are path-dependent and carry no cross-run integrity "
                             "value; with inputs matching byte-for-byte, canon digest drift does NOT "
                             "mean the shards moved -- the session-level regression is the authority",
    }


def integrity_sweep(paths):
    """Recompute frame_hash from the stored frames for every env_step that
    carries frames.  The whole audit trusts the ledger's frame_hash field;
    this sweep is what makes 'bit-exact' a statement about the frames as
    stored, not about a field the writer could have miswritten."""
    results = {}
    for path in paths:
        checked = mismatched = 0
        examples = []
        for record in read_ledger(path):
            if record.get("event") != "env_step" or record.get("frames") is None:
                continue
            checked += 1
            recomputed = frame_hash(record.get("frames"))
            if recomputed != record.get("frame_hash"):
                mismatched += 1
                if len(examples) < 5:
                    examples.append({"seq": record.get("seq"),
                                     "stored": record.get("frame_hash"),
                                     "recomputed": recomputed})
        results[path] = {"steps_with_frames": checked,
                         "hash_mismatches": mismatched,
                         "examples": examples}
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--var-ledger", required=True,
                    help="absolute path to the main checkout's proxy/var/ledger.jsonl (gitignored)")
    ap.add_argument("--scratch", required=True, help="scratch dir for rebuilt canons")
    ap.add_argument("--out", default=HERE, help="output dir (default: this run dir)")
    ap.add_argument("--skip-canon", action="store_true",
                    help="reuse canons already present in --scratch")
    args = ap.parse_args()

    os.makedirs(args.scratch, exist_ok=True)
    inputs = {}

    def track(path):
        inputs[path if not os.path.isabs(path) else os.path.basename(path)] = {
            "abspath_hint": path if os.path.isabs(path) else None,
            "bytes": os.path.getsize(path),
            "sha256": sha256_file(path),
        }

    # ---- 1. rebuild the canons exactly as the archived MANIFESTs did ----
    canons = {}
    for key, (shard, probe_log) in sorted(SHARDS.items()):
        shard_abs = os.path.join(REPO, shard)
        probe_abs = os.path.join(REPO, probe_log)
        track(shard)
        track(probe_log)
        canon = os.path.join(args.scratch, "canon.%s.jsonl" % key)
        if not (args.skip_canon and os.path.exists(canon)):
            cmd = [sys.executable, "-m", "proxy.tools.upgrade_ledger", shard_abs,
                   "-o", canon, "--scorecards", probe_abs]
            proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
            if proc.returncode != 0:
                raise SystemExit("upgrade_ledger failed for %s:\n%s" % (key, proc.stderr[-2000:]))
        canons[key] = canon

    canon_digests = {k: sha256_file(v) for k, v in sorted(canons.items())}

    # pinned digests from the archived MANIFESTs, for drift detection
    pinned = {}
    for mdir in (P9_DIR, P1R2_DIR):
        with open(os.path.join(REPO, mdir, "MANIFEST.json"), encoding="utf-8") as f:
            pinned[mdir] = json.load(f)

    # ---- 2. regression: reproduce the two archived reports ----
    recon_abs = os.path.join(REPO, RECON_LEDGER)
    track(RECON_LEDGER)

    ar25_archive_sessions = merged(
        sessions_from_canon(canons["ar25"], GAME_AR25),
        sessions_from_recon(recon_abs, GAME_AR25),
    )
    ar25_regression = spotcheck(ar25_archive_sessions, GAME_AR25)

    g50t_archive_sessions = merged(
        sessions_from_canon(canons["g50t"], GAME_G50T),
        sessions_from_canon(canons["a7-g50t"], GAME_G50T),
        sessions_from_canon(canons["a7up-opus-g50t"], GAME_G50T),
        sessions_from_canon(canons["a7up-sonnet-g50t"], GAME_G50T),
        sessions_from_recon(recon_abs, GAME_G50T),
    )
    g50t_regression = spotcheck(g50t_archive_sessions, GAME_G50T)

    with open(os.path.join(REPO, P9_DIR, "replay_spotcheck_ar25.json"), encoding="utf-8") as f:
        ar25_archived_report = json.load(f)
    with open(os.path.join(REPO, P1R2_DIR, "replay_spotcheck_g50t.json"), encoding="utf-8") as f:
        g50t_archived_report = json.load(f)

    for rel in ("%s/replay_spotcheck_ar25.json" % P9_DIR,
                "%s/MANIFEST.json" % P9_DIR,
                "%s/replay_spotcheck_g50t.json" % P1R2_DIR,
                "%s/MANIFEST.json" % P1R2_DIR):
        track(rel)

    regression = {
        "ar25": {
            "reproduced": summarize(ar25_regression),
            "archived": summarize(ar25_archived_report),
            "match": summarize(ar25_regression) == summarize(ar25_archived_report),
        },
        "g50t": {
            "reproduced": summarize(g50t_regression),
            "archived": summarize(g50t_archived_report),
            "match": summarize(g50t_regression) == summarize(g50t_archived_report),
        },
        "canon_digests": canon_digests,
        "pinned_digest_comparison": pinned_digest_comparison(inputs, canon_digests, pinned),
    }
    dump(os.path.join(args.out, "regression_vs_archive.json"), regression)

    # ---- 3. live g50t: the three theoria-arm legs, alone and combined ----
    live_g50t = {}
    for label, rel in ARM_LEGS_G50T:
        track(rel)
        live_g50t = merged(live_g50t, sessions_from_armrun(os.path.join(REPO, rel), GAME_G50T, label))
    g50t_live_only = spotcheck(live_g50t, GAME_G50T)
    g50t_live_only["sources"] = [rel for _, rel in ARM_LEGS_G50T]
    dump(os.path.join(args.out, "replay_spotcheck_live_g50t.json"), g50t_live_only)

    g50t_combined = spotcheck(merged(g50t_archive_sessions, live_g50t), GAME_G50T)
    g50t_combined["sources"] = (["reproduced archive canons (see regression_vs_archive.json)",
                                 RECON_LEDGER] + [rel for _, rel in ARM_LEGS_G50T])
    g50t_combined["live_depth_note"] = (
        "the 3 live legs are present at all 6 compared positions; 971 of the 1304 pairwise "
        "comparisons are the archived P-9-era figure reproduced, 333 involve a live leg; "
        "live-vs-live depth (10 positions, 22 pairwise) is in replay_spotcheck_live_g50t.json")
    dump(os.path.join(args.out, "replay_spotcheck_combined_g50t.json"), g50t_combined)

    # ---- 4. live ar25: the S31 real-arm session vs the archive ----
    live_runs = live_runs_of(args.var_ledger)
    var_sessions = sessions_from_canon(args.var_ledger, GAME_AR25)
    s31_sessions = {"s31/%s" % run_id: steps
                    for run_id, steps in var_sessions.items() if run_id in live_runs}
    excluded = sorted(run_id for run_id in var_sessions if run_id not in live_runs)
    ar25_combined = spotcheck(merged(ar25_archive_sessions, s31_sessions), GAME_AR25)
    ar25_combined["sources"] = ["reproduced archive canon + recon (see regression_vs_archive.json)",
                                "proxy/var/ledger.jsonl (gitignored; live runs only, "
                                "selected by run_start env_upstream containing %r)" % REAL_HOST]
    ar25_combined["live_runs_included"] = sorted(s31_sessions)
    ar25_combined["var_runs_excluded_as_mock"] = excluded
    s31_pairwise = sum(c["sessions"] - 1 for c in ar25_combined["comparisons"]
                       if c["position"] < max((len(v) for v in s31_sessions.values()), default=0))
    ar25_combined["live_depth_note"] = (
        "the S31 live session is RESET-only: it participates at position 0 only "
        "(%d of the %d pairwise comparisons involve it); positions 1-8 are archive-era "
        "sessions agreeing with each other (the P-9 result reproduced)"
        % (s31_pairwise, ar25_combined["pairwise_comparisons"]))
    dump(os.path.join(args.out, "replay_spotcheck_combined_ar25.json"), ar25_combined)

    # ---- 5. sk48 supplement: earlier real-online legs (pre-S31, committed) ----
    live_sk48 = {}
    for label, rel in ARM_LEGS_SK48:
        track(rel)
        live_sk48 = merged(live_sk48, sessions_from_armrun(os.path.join(REPO, rel), GAME_SK48, label))
    sk48_sessions = merged(live_sk48, sessions_from_recon(recon_abs, GAME_SK48))
    sk48_supplement = spotcheck(sk48_sessions, GAME_SK48)
    sk48_supplement["sources"] = [rel for _, rel in ARM_LEGS_SK48] + [RECON_LEDGER]
    sk48_supplement["note"] = ("supplementary: pre-S31 committed real-online sk48 legs; "
                               "not part of the two-game claim, recorded as-is")
    dump(os.path.join(args.out, "replay_spotcheck_sk48_supplement.json"), sk48_supplement)

    # ---- 6. integrity sweep: recompute every frame_hash from stored frames ----
    sweep_paths = ([os.path.join(REPO, rel) for _, rel in ARM_LEGS_G50T + ARM_LEGS_SK48]
                   + [args.var_ledger] + [canons[k] for k in sorted(canons)])
    sweep = integrity_sweep(sweep_paths)
    sweep_rel = {os.path.relpath(p, REPO).replace("\\", "/") if p.startswith(REPO) else os.path.basename(p): v
                 for p, v in sweep.items()}
    total_checked = sum(v["steps_with_frames"] for v in sweep.values())
    total_bad = sum(v["hash_mismatches"] for v in sweep.values())
    dump(os.path.join(args.out, "integrity_hash_recompute.json"),
         {"files": sweep_rel, "total_steps_with_frames": total_checked,
          "total_hash_mismatches": total_bad})

    # ---- 7. snapshot the S31 live records out of the gitignored var ledger ----
    live_ids = set(live_runs)
    excerpt_path = os.path.join(args.out, "evidence", "s31_ar25_ledger_excerpt.jsonl")
    os.makedirs(os.path.dirname(excerpt_path), exist_ok=True)
    kept = 0
    with open(args.var_ledger, encoding="utf-8") as src, \
            open(excerpt_path, "w", encoding="utf-8", newline="\n") as dst:
        for line in src:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("run_id") in live_ids:
                dst.write(line + "\n")
                kept += 1
    track(os.path.relpath(args.var_ledger, REPO).replace("\\", "/")
          if args.var_ledger.startswith(REPO) else args.var_ledger)

    # ---- 8. adjudicate the arm-side replay_mismatch surprises ----
    adjudication = {
        "instrument": {
            "emitter": "theoria-arm/inner/certify.py cheap(): render(step(state, manual_action)) "
                       "vs the SINGLE recorded observation store.grids[t+1]; surprise minted in "
                       "surprises_from() as kind=replay_mismatch",
            "reads_environment_twice": False,
            "verdict": "arm-side theory instrument: a mismatch says the compiled manual "
                       "mispredicts a recorded frame; the environment is sampled once per "
                       "transition, so the record carries no information about environment "
                       "determinism in either direction",
        },
        "records": [],
    }
    for label, rel in ARM_LEGS_G50T:
        srel = os.path.dirname(rel) + "/surprises.jsonl"
        track(srel)
        spath = os.path.join(REPO, srel)
        with open(spath, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                s = json.loads(line)
                if s.get("kind") != "replay_mismatch":
                    continue
                payload = s.get("payload") or {}
                t = payload.get("t")
                position = None if t is None else t + 1
                cross = None
                if position is not None:
                    for comp in g50t_live_only["comparisons"]:
                        if comp["position"] == position:
                            cross = {"action": comp["action"],
                                     "frame_hash": comp["frame_hash"],
                                     "sessions": comp["sessions"],
                                     "agree": comp["agree"]}
                adjudication["records"].append({
                    "leg": label,
                    "seq": s.get("seq"),
                    "t": t,
                    "arc_action": payload.get("arc_action"),
                    "cells_wrong": payload.get("cells_wrong"),
                    "handled_by": s.get("handled_by"),
                    "position_in_spotcheck": position,
                    "environment_at_that_position": cross,
                })
    agreeing = [r for r in adjudication["records"]
                if r["environment_at_that_position"] and r["environment_at_that_position"]["agree"]]
    n_total = len(adjudication["records"])
    n_agree = len(agreeing)
    adjudication["summary"] = {
        "replay_mismatch_records": n_total,
        "records_whose_position_the_environment_reproduced_bit_exactly": n_agree,
        "conclusion": "%d of %d arm-side replay_mismatch records sit at positions where the "
                      "live environment returned the identical frame_hash across independent "
                      "sessions; the remaining %d lie past the point where the sessions "
                      "diverge (prefix divergence) and carry no cross-session evidence either "
                      "way. Structurally the verdict is the same for all %d: certify.py "
                      "compares the manual's prediction against a single recorded "
                      "observation, so a replay_mismatch is a statement about the theory, "
                      "not about environment determinism"
                      % (n_agree, n_total, n_total - n_agree, n_total),
    }
    dump(os.path.join(args.out, "adjudication_r3_replay_mismatch.json"), adjudication)

    # ---- 8b. adapter honesty: assert the properties the adapter relies on ----
    honesty = adapter_honesty([os.path.join(REPO, rel) for _, rel in ARM_LEGS_G50T + ARM_LEGS_SK48])
    honesty_rel = {os.path.relpath(p, REPO).replace("\\", "/"): v for p, v in honesty.items()}
    honesty_violations = sum(v["failed_carrying_frames"] + v["status200_without_frames"]
                             + v["abandoned_commands"] + (0 if v["single_run_id"] else 1)
                             for v in honesty.values())
    dump(os.path.join(args.out, "adapter_honesty.json"),
         {"files": honesty_rel, "violations": honesty_violations,
          "properties": ["no failed step carries frames or frame_hash",
                         "no status-200 step lacks frames",
                         "every failure is a retry of the command that next succeeds",
                         "each run-dir ledger holds exactly one run_id"]})

    # ---- 9. inputs + summary ----
    dump(os.path.join(args.out, "inputs.json"), inputs)
    summary = {
        "regression": {k: regression[k]["match"] for k in ("ar25", "g50t")},
        "pinned_inputs_all_match": regression["pinned_digest_comparison"]["inputs_all_match"],
        "live_g50t": summarize(g50t_live_only),
        "combined_g50t": summarize(g50t_combined),
        "combined_ar25": summarize(ar25_combined),
        "ar25_live_depth": ar25_combined["live_depth_note"],
        "sk48_supplement": summarize(sk48_supplement),
        "integrity": {"steps_with_frames": total_checked, "hash_mismatches": total_bad},
        "adapter_honesty_violations": honesty_violations,
        "s31_excerpt_lines": kept,
        "adjudication": adjudication["summary"],
    }
    dump(os.path.join(args.out, "summary.json"), summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    ok = (all(regression[k]["match"] for k in ("ar25", "g50t"))
          and g50t_live_only["verdict"] == "PASS"
          and g50t_combined["verdict"] == "PASS"
          and ar25_combined["verdict"] == "PASS"
          and total_bad == 0
          and honesty_violations == 0)
    print("OVERALL: %s" % ("PASS" if ok else "NOT-PASS"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
