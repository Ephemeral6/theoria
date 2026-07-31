"""Build this run's MANIFEST.json. Deterministic: re-running rewrites the same
bytes for the same inputs (the utc field is fixed, not the wall clock)."""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def sha(path):
    with open(path, "rb") as fh:
        return "sha256:" + hashlib.sha256(fh.read()).hexdigest()


artifacts = {}
for name in sorted(os.listdir(HERE)):
    if name in ("MANIFEST.json", "build_manifest.py"):
        continue
    artifacts[name] = sha(os.path.join(HERE, name))

spot = json.load(open(os.path.join(HERE, "replay_spotcheck_g50t.json")))
regress = json.load(open(os.path.join(HERE, "replay_spotcheck_ar25_regression.json")))

manifest = {
    "prompt_id": "P1-replay-spotcheck-2",
    "title": "Phase 1 acceptance: the second game's replay spot check (g50t-5849a774)",
    "branch": "closeout/p1-replay-2",
    "base_commit": "f6a9571938d55faf6194337db537075d1258d596",
    "utc": "2026-07-31T15:43:36Z",
    "seed": None,
    "_seed_note": "no randomness: migration, validation and the spot check are "
                  "deterministic over fixed inputs.",
    "cost": {
        "api_calls": 0, "model_calls": 0, "usd": 0.0,
        "_note": "zero network, zero dollars: like P-9's ar25 check, the replay "
                 "evidence was read out of ledgers that already existed.",
    },
    "pile_discipline": {
        "games_touched": ["g50t-5849a774", "ar25-0c556536"],
        "api_calls": 0,
        "sealed_pile_requests": 0,
        "_note": "both are development pile. ar25 appears only as the regression "
                 "control for the adapted recon reader.",
    },
    "inputs": [
        {"path": "baseline-arms/out/shards/ledger.g50t.jsonl", "read_only": True,
         "sha256": "sha256:7fd8aa904542532b51a727d7c4844c41d7eedac8d166fb283eb650e642ce7ea5",
         "_note": "snapshot digest; another territory's campaign output, read never written"},
        {"path": "baseline-arms/out/shards/ledger.a7-g50t.jsonl", "read_only": True,
         "sha256": "sha256:0ed50729f2027487d6fa8e4b38c4b934c2e73a8a46b0f7da3165e2be25a542ae"},
        {"path": "baseline-arms/out/shards/ledger.a7up-opus-g50t.jsonl", "read_only": True,
         "sha256": "sha256:b91bd475049b8c1dd3969a10c587af57561d8d4788ffd17536f461c9578e53b5"},
        {"path": "baseline-arms/out/shards/ledger.a7up-sonnet-g50t.jsonl", "read_only": True,
         "sha256": "sha256:89adeb35a84a32762911946676c6cad422ac3feda9b913628b65b300b1a721e1"},
        {"path": "baseline-arms/out/shards/probe_log.g50t.jsonl", "read_only": True,
         "sha256": "sha256:b6609065cf354cb51578aa9194c4977a1fa2e400ee95efd1031afe036754a899"},
        {"path": "baseline-arms/out/shards/probe_log.a7-g50t.jsonl", "read_only": True,
         "sha256": "sha256:528d4a21e0e031880c6398dfa6d198eadc597bdc210eb271f7b5d99f25124221"},
        {"path": "baseline-arms/out/shards/probe_log.a7up-opus-g50t.jsonl", "read_only": True,
         "sha256": "sha256:e1f3776dd837de1cfc33d8d0839b228a294b0850c0ad73323496383a5b935d87"},
        {"path": "baseline-arms/out/shards/probe_log.a7up-sonnet-g50t.jsonl", "read_only": True,
         "sha256": "sha256:466a921d504d94bbdcc062ca8589653d01e8deff5c1bd0bd05f167a90018bfdc"},
        {"path": "arc-recon/data/recon_ledger.jsonl", "read_only": True,
         "_note": "the determinism precheck's raw HTTP exchanges; the "
                  "cross-campaign second witness, as in the ar25 check"},
    ],
    "intermediate": {
        "canon.g50t.jsonl": {"sha256": "sha256:b845841263af1a08dbee39bdfe2fc861ae65edd2d3bb2541362da438b83b2d67"},
        "canon.a7-g50t.jsonl": {"sha256": "sha256:0954b40be786fe06c74c1e604cf11d18f5a3837e98d6ecc38404a400d3399b63"},
        "canon.a7up-opus-g50t.jsonl": {"sha256": "sha256:7dac28bbc2ec0c5e467382bd7302e6970173b08e81eed3c8637b0400732d6370"},
        "canon.a7up-sonnet-g50t.jsonl": {"sha256": "sha256:b9d481ad266fa2ce89ffca4de1efbd29733268bc8ca55779e6b45b99e82fadc8"},
        "_note": "the lifted canonical ledgers (~33 MB of frames) are not "
                 "archived; reproduce with the commands below and compare digests.",
    },
    "reproduce": [
        "python -m proxy.tools.upgrade_ledger baseline-arms/out/shards/ledger.g50t.jsonl -o canon.g50t.jsonl --scorecards baseline-arms/out/shards/probe_log.g50t.jsonl",
        "  (and likewise for the a7-g50t / a7up-opus-g50t / a7up-sonnet-g50t shards)",
        "python -m proxy.tools.validate_ledger --json canon.g50t.jsonl",
        "python -m proxy.tools.replay_spotcheck --canon canon.g50t.jsonl --canon canon.a7-g50t.jsonl --canon canon.a7up-opus-g50t.jsonl --canon canon.a7up-sonnet-g50t.jsonl --recon arc-recon/data/recon_ledger.jsonl --game g50t-5849a774",
    ],
    "results": {
        "replay_spotcheck_g50t": {
            "verdict": spot["verdict"],
            "sessions": spot["n_sessions"],
            "steps_compared": spot["steps_compared"],
            "pairwise_comparisons": spot["pairwise_comparisons"],
            "disagreements": len(spot["disagreements"]),
            "_claim": "cross-session, cross-campaign bit-exact agreement of the "
                      "environment on g50t-5849a774: 26 independent sessions "
                      "(19 baseline-arms across three campaigns + 7 arc-recon "
                      "precheck passes) agree hash-for-hash on the shared "
                      "opening RESET..ACTION5. With P-9's ar25 check this "
                      "completes the two-game Phase 1 acceptance line. Still "
                      "not a replay through these proxies (proxy/replay.py "
                      "live replay remains owed).",
        },
        "ar25_regression": {
            "verdict": regress["verdict"],
            "sessions": regress["n_sessions"],
            "steps_compared": regress["steps_compared"],
            "pairwise_comparisons": regress["pairwise_comparisons"],
            "disagreements": len(regress["disagreements"]),
            "_note": "the adapted recon reader reproduces P-9's archived ar25 "
                     "numbers exactly (16 sessions / 9 steps / 372 pairwise / 0).",
        },
        "validation": "all four lifted g50t ledgers PASS proxy.tools.validate_ledger",
        "tests": {"passed": 426, "failed": 0,
                  "_note": "full proxy suite; includes 5 new tests for the "
                           "recon pass-splitting and step_idx-contiguity rules, "
                           "with negative controls."},
    },
    "tool_changes": {
        "proxy/tools/replay_spotcheck.py": [
            "sessions_from_recon: every successful RESET opens a new pass; "
            "passes are separate sessions (recon/<label>, recon/<label>#2, ...). "
            "The g50t precheck has aborted and partial passes under one label; "
            "folding them stacked two RESETs at position 0.",
            "clean_prefix: truncate at the first step_idx discontinuity. The "
            "precheck's short-game-id rows fail the game filter and leave "
            "holes; without the rule, a step at step_idx 6 lands at position 3 "
            "and misalignment reads as disagreement.",
        ],
    },
    "artifacts": artifacts,
}

out = os.path.join(HERE, "MANIFEST.json")
with open(out, "w", encoding="utf-8", newline="") as fh:
    fh.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
print("wrote", out)
