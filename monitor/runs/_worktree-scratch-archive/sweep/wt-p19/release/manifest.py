"""The Phase 4 artefact manifester.

Enumerates everything the release publishes, sha256s it file by file into
`release/MANIFEST.jsonl`, ticks or flags each of the nine checklist items from
`Theoria.md` Phase 4, and re-proves two red lines every single run:

  R-1  no credential value is anywhere in the release set
  R-2  no sealed-pile frame data is anywhere in the release set

Both are recomputed, never remembered. A previous run's green is not evidence
about this tree.

Usage:
    python release/manifest.py                # write MANIFEST.jsonl + the docs
    python release/manifest.py --check        # recompute and diff; nonzero on drift
    python release/manifest.py --redlines-only

Determinism: the manifest carries no wall clock and no commit id, so two runs
over an unchanged tree produce byte-identical output. The timestamps live in
`release/runs/<UTC>-p19/`, which is where volatile things belong.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from checklist_spec import (  # noqa: E402
    CHECKLIST,
    DEV_PILE,
    MISSING,
    PARTIAL,
    PILES_SHA256_PREFIX,
    READY,
    STANDING_FINDINGS,
)

MANIFEST_PATH = os.path.join(HERE, "MANIFEST.jsonl")
CHECKLIST_PATH = os.path.join(HERE, "CHECKLIST.md")
INCIDENTS_INDEX_PATH = os.path.join(HERE, "INCIDENTS_INDEX.md")

SCHEMA = "theoria-release-manifest/v1"
PROMPT_ID = "P-19"

# Outputs whose content depends on when they were produced, or which would
# hash themselves. Excluded from the release set; listed in the header so the
# exclusion is visible rather than silent.
#
# CHECKLIST.md is here for a specific reason, not for convenience: it prints the
# release set's own total byte count, so hashing it inside the pass that writes
# it has no fixed point -- each run would report the previous run's file. Its
# integrity check is `git diff` after regeneration, which is what verify.sh
# does, and which is strictly stronger than a hash of a file that cannot settle.
VOLATILE = [
    "release/MANIFEST.jsonl",
    "release/CHECKLIST.md",
    "release/REPRODUCTION_REPORT.md",
    "release/runs/**",
    "**/__pycache__/**",
    "**/*.pyc",
]


# ---------------------------------------------------------------------------
# path matching
# ---------------------------------------------------------------------------

def match(path: str, pattern: str) -> bool:
    """fnmatch, plus `a/**` meaning 'anything at or under a/'.

    fnmatch's `*` happily crosses `/`, which makes plain globs far too greedy
    here; `**` is spelled out instead so a pattern says what it means.
    """
    if "**" in pattern:
        head, _, tail = pattern.partition("**")
        if not path.startswith(head):
            return False
        rest = path[len(head):]
        if tail in ("", "/"):
            return True
        return fnmatch.fnmatch(rest, tail.lstrip("/")) or fnmatch.fnmatch(
            rest, "*" + tail
        )
    return fnmatch.fnmatch(path, pattern)


def matches_any(path: str, patterns: Iterable[str]) -> bool:
    return any(match(path, p) for p in patterns)


# ---------------------------------------------------------------------------
# the release set
# ---------------------------------------------------------------------------

def git_tracked() -> List[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.replace("\r\n", "\n").split("\n") if line]


def present_under_release() -> List[str]:
    """Files under release/ that exist on disk.

    The manifester has to run before the commit that tracks its own output, so
    `git ls-files` alone would report the release kit as absent on its first
    run and present on every run after -- a manifest that changes meaning
    depending on commit order. Unioning in what is actually on disk under
    release/ makes the answer the same either way.
    """
    found = []
    for root, dirs, names in os.walk(os.path.join(REPO, "release")):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in names:
            rel = os.path.relpath(os.path.join(root, name), REPO).replace(os.sep, "/")
            found.append(rel)
    return found


def release_set() -> List[str]:
    paths = set(git_tracked()) | set(present_under_release())
    keep = [p for p in paths if not matches_any(p, VOLATILE)]
    keep = [p for p in keep if os.path.exists(os.path.join(REPO, p))]
    return sorted(keep)


def sha256_file(path: str) -> Tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with open(os.path.join(REPO, path), "rb") as fh:
        while True:
            chunk = fh.read(1 << 20)
            if not chunk:
                break
            size += len(chunk)
            h.update(chunk)
    return h.hexdigest(), size


# ---------------------------------------------------------------------------
# classification against the checklist
# ---------------------------------------------------------------------------

def classify(path: str) -> List[str]:
    keys = []
    for item in CHECKLIST:
        if matches_any(path, item["exclude"]):
            continue
        if matches_any(path, item["include"]):
            keys.append(item["key"])
    return keys


DIALECTS = [
    ("proxy-canon-v1.0", ["theoria-arm/runs/**/ledger.jsonl", "proxy/runs/**"]),
    ("legacy-baseline-arms", ["baseline-arms/ledger.jsonl"]),
    ("recon-http-capture", ["arc-recon/data/recon_ledger.jsonl",
                            "baseline-arms/probe_log.jsonl"]),
    ("a2-loop-beats", ["cold-start-a2/artifacts/loop_ledger.json"]),
    ("incident-jsonl", ["arc-recon/data/incidents.jsonl",
                        "arc-recon/data/contamination_log.jsonl"]),
    ("incident-markdown", ["baseline-arms/INCIDENTS.md", "theoria-arm/INCIDENTS.md"]),
]


def dialect_of(path: str) -> Optional[str]:
    for name, patterns in DIALECTS:
        if matches_any(path, patterns):
            return name
    return None


STUB_PATTERNS = ["theoria-arm/runs/*salvage*/**"]


# ---------------------------------------------------------------------------
# R-1 -- no credential value in the release set
# ---------------------------------------------------------------------------

DOTENV_CANDIDATES = ["/.env"]

KEYISH = re.compile(
    rb"sk-[A-Za-z0-9_\-]{16,}"
)
UUIDISH = re.compile(
    rb"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

# Structural fields whose values are UUID-shaped by design. Lifted from
# proxy/redact.py's STRUCTURAL_KEYS so the release check and the vault agree on
# what a UUID is allowed to be, with the plural containers added -- `card_ids`
# holds exactly what `card_id` holds and the singular-only set let them through.
STRUCTURAL_UUID_KEYS = {
    "card_id", "card_ids", "guid", "guids", "run_id", "run_ids", "id", "ids",
    "sha256", "frame_hash", "request_sha256", "cut_sha256", "source_sha256",
    "out_sha256", "spec_sha256", "piles_sha256", "session_id", "trace_id",
    "call_id", "candidate_id", "parent_id", "scorecard_id", "scorecard_ids",
    "uuid", "game_uuid",
}

# `sk-` shaped strings that are known, deliberate test material. Every entry is
# a synthetic value in a red-team fixture; if one of these files stops being a
# fixture the allowlist stops covering it and the redline goes red.
SK_ALLOWLIST = {
    "proxy/tests/test_ledger.py": "synthetic redaction fixtures (sk-ant-abcdef...)",
    "proxy/tests/test_seal.py": "synthetic seal-test key",
}

# UUID-shaped literals that are not credentials, allowlisted by *value* rather
# than by file. Allowlisting a file would mean a real key pasted into that file
# goes unnoticed; allowlisting the literal cannot, because the ARC key is not
# any of these. Each entry names why the constant exists.
UUID_ALLOWLIST = {
    "6ba7b812-9dad-11d1-80b4-00c04fd430c8":
        "RFC 4122 NAMESPACE_OID -- the uuid5 namespace engine-rig derives "
        "deterministic candidate ids from (engine-rig/common/candidates.py)",
    "b3f1a3a0-0000-4000-8000-000000000000":
        "synthetic fixed id in engine-rig/tests/test_integration.py",
    "7f1e2d3c-4b5a-6978-8796-a5b4c3d2e1f0":
        "synthetic key-shaped value in proxy/tests/test_redteam.py, the fixture "
        "that proves the vault catches a UUID-shaped credential (RED-16)",
}


def find_dotenv() -> Optional[str]:
    """Locate .env without ever putting its contents anywhere but memory.

    A worktree does not carry .env (it is gitignored), so the main checkout's
    copy is the fallback. A stranger's clone has neither, and that is the
    normal case -- R-1 then runs in shape mode and says so.
    """
    tries = [os.path.join(REPO, ".env")]
    try:
        common = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"], cwd=REPO,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if common:
            common = os.path.abspath(os.path.join(REPO, common))
            tries.append(os.path.join(os.path.dirname(common), ".env"))
    except Exception:
        pass
    for path in tries:
        if os.path.isfile(path):
            return path
    return None


def read_secret_values(path: str) -> Dict[str, str]:
    """name -> value. The values are used for substring search and discarded."""
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip().strip('"').strip("'")
        if value:
            out[name] = value
    return out


def _structural_key(key: Optional[str]) -> bool:
    if not key:
        return False
    k = key.lower()
    if k in STRUCTURAL_UUID_KEYS:
        return True
    # A dict keyed by game id, whose value is that game's scorecard guid --
    # theoria-arm/runs/*/run.json does this. The key is data, so it cannot be
    # in a fixed set; its shape is what makes it structural.
    return bool(GAME_ID_RE.fullmatch(k))


def _walk_json_uuids(node: Any, key: Optional[str], out: List[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            _walk_json_uuids(v, k if isinstance(k, str) else None, out)
    elif isinstance(node, list):
        for v in node:
            _walk_json_uuids(v, key, out)
    elif isinstance(node, str):
        if _structural_key(key):
            return
        if node in UUID_ALLOWLIST:
            return
        if UUIDISH.fullmatch(node.encode("utf-8", "ignore")):
            out.append(node)


def _json_records(abs_path: str) -> Iterable[Any]:
    if abs_path.endswith(".jsonl"):
        with open(abs_path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except ValueError:
                    continue
    else:
        try:
            with open(abs_path, encoding="utf-8", errors="replace") as fh:
                yield json.load(fh)
        except ValueError:
            return


def redline_env(paths: List[str]) -> Dict[str, Any]:
    dotenv = find_dotenv()
    secrets = read_secret_values(dotenv) if dotenv else {}
    needles = [(name, value.encode("utf-8")) for name, value in secrets.items()]

    exact_hits: List[Dict[str, str]] = []
    sk_hits: List[Dict[str, str]] = []
    uuid_hits: List[Dict[str, Any]] = []
    scanned = 0

    for rel in paths:
        abs_path = os.path.join(REPO, rel)
        try:
            blob = open(abs_path, "rb").read()
        except OSError:
            continue
        scanned += 1

        for name, needle in needles:
            if needle in blob:
                # The value is never written out -- only the fact and the place.
                exact_hits.append({"path": rel, "secret_name": name})

        for m in KEYISH.finditer(blob):
            reason = SK_ALLOWLIST.get(rel)
            if reason is None:
                sk_hits.append({"path": rel, "shape": "sk-*",
                                "excerpt_len": len(m.group(0))})

        # UUID-shaped strings are only meaningful once structural fields are
        # taken out, and that needs the JSON structure, not a regex.
        if UUIDISH.search(blob) and rel.endswith((".json", ".jsonl")):
            found: List[str] = []
            for rec in _json_records(abs_path):
                _walk_json_uuids(rec, None, found)
                if len(found) > 25:
                    break
            if found:
                uuid_hits.append({"path": rel, "count": len(found),
                                  "sample_len": len(found[0])})
        elif UUIDISH.search(blob) and not rel.endswith((".json", ".jsonl")):
            # No JSON structure to lean on here, so only the value allowlist
            # applies. A UUID in a .py or .md file that is not a declared
            # constant is exactly the thing this check exists to catch.
            found = [m.group(0).decode("ascii", "ignore")
                     for m in UUIDISH.finditer(blob)]
            unexplained = [u for u in found if u not in UUID_ALLOWLIST]
            if unexplained:
                uuid_hits.append({
                    "path": rel, "count": len(unexplained), "sample_len": 36,
                    "note": "non-JSON file; only the value allowlist applies",
                })

    green = not exact_hits and not sk_hits and not uuid_hits
    return {
        "record": "redline",
        "id": "R-1",
        "claim": "no credential value appears anywhere in the release set",
        "mode": "exact+shape" if dotenv else "shape-only",
        "dotenv_present": bool(dotenv),
        "secrets_checked": sorted(secrets.keys()),
        "files_scanned": scanned,
        "exact_hits": exact_hits,
        "unexplained_sk_shaped": sk_hits,
        "unexplained_uuid_shaped": uuid_hits,
        "sk_allowlist": SK_ALLOWLIST,
        "verdict": "GREEN" if green else "RED",
        "limits": [
            "Substring search finds a credential stored verbatim. It does not find "
            "one that has been base64'd, split across fields, or otherwise encoded.",
            "shape-only mode (no .env on this machine) cannot prove the real value is "
            "absent -- it proves nothing key-shaped is unexplained. A release "
            "gate must be run at least once on a machine that has .env.",
        ],
    }


# ---------------------------------------------------------------------------
# R-2 -- no sealed-pile frame data in the release set
# ---------------------------------------------------------------------------

GAME_ID_RE = re.compile(r"\b[a-z0-9]{2,4}[0-9a-z]?-[0-9a-f]{8}\b")


def load_cut() -> Dict[str, Any]:
    """Load the pile cut through the battery's own guard.

    The first version of this check hashed piles.json's bytes and compared them
    to the digest CLAUDE.md quotes. They did not match, and the check was
    wrong, not the tree: piles.json carries its own `sha256` field, so the
    published digest is over the canonical JSON *with that field removed*
    (battery/guard.py:70, arc-recon/cut_piles.py:116). Reusing
    `battery.guard.Piles` instead of reimplementing it means the release redline
    and the battery cannot drift apart about what "sealed" means -- and its
    `classify` already resolves the short form (`g50t` -> dev), which a
    hand-rolled set comparison does not.
    """
    if REPO not in sys.path:
        sys.path.insert(0, REPO)
    doc_path = os.path.join(REPO, "arc-recon", "data", "piles.json")
    doc = json.load(open(doc_path, encoding="utf-8"))
    try:
        from battery.guard import Piles  # type: ignore
        piles = Piles(doc, verify=False)
        return {
            "doc": doc,
            "classify": piles.classify,
            "recorded_digest": piles.recorded_digest,
            "computed_digest": piles.computed_digest,
            "digest_ok": piles.recorded_digest == piles.computed_digest,
            "guard": "battery.guard.Piles",
        }
    except Exception as exc:  # the guard must not be the single point of failure
        payload = {k: v for k, v in doc.items() if k != "sha256"}
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        computed = hashlib.sha256(body.encode("utf-8")).hexdigest()
        dev = {g.split("-", 1)[0] for g in doc["dev_pile"]} | set(doc["dev_pile"])
        sealed = {g.split("-", 1)[0] for g in doc["sealed_pile"]} | set(
            doc["sealed_pile"])

        def classify(gid: str) -> str:
            k = gid.strip().lower()
            s = k.split("-", 1)[0]
            if k in sealed or s in sealed:
                return "sealed"
            if k in dev or s in dev:
                return "dev"
            return "unknown"

        return {
            "doc": doc, "classify": classify,
            "recorded_digest": doc.get("sha256"), "computed_digest": computed,
            "digest_ok": doc.get("sha256") == computed,
            "guard": "release/manifest.py fallback (battery.guard unavailable: %r)"
                     % (exc,),
        }


def _looks_like_grid(node: Any) -> bool:
    """A frame is a rectangle of small ints. Deliberately loose."""
    if not isinstance(node, list) or len(node) < 2:
        return False
    rows = 0
    for row in node:
        if isinstance(row, list) and len(row) >= 2 and all(
            isinstance(c, int) for c in row[:8]
        ):
            rows += 1
        elif isinstance(row, list):
            return _looks_like_grid(row)
        else:
            return False
    return rows >= 2


def _collect(node: Any, key: Optional[str], game_ids: Set[str],
             grids: List[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            kl = k.lower() if isinstance(k, str) else ""
            if kl in ("game_id", "gameid") and isinstance(v, str):
                game_ids.add(v)
            _collect(v, kl, game_ids, grids)
    elif isinstance(node, list):
        if key in ("frame", "frames") and _looks_like_grid(node):
            grids.append(key)
        else:
            if _looks_like_grid(node):
                grids.append(key or "<anon>")
            for v in node:
                _collect(v, key, game_ids, grids)
    elif isinstance(node, str):
        # recon_ledger stores response bodies as JSON *strings*; a frame hides
        # one level of encoding down. Peel it, or the check reads clean while
        # 180 frames sit in plain sight.
        if len(node) > 200 and node.lstrip().startswith(("{", "[")):
            try:
                _collect(json.loads(node), key, game_ids, grids)
            except ValueError:
                pass


def redline_sealed(paths: List[str]) -> Dict[str, Any]:
    cut = load_cut()
    doc = cut["doc"]
    classify = cut["classify"]
    dev = sorted(doc["dev_pile"])
    sealed = sorted(doc["sealed_pile"])

    problems: List[str] = []
    if dev != sorted(DEV_PILE):
        problems.append("piles.json dev_pile disagrees with checklist_spec.DEV_PILE")
    if not cut["digest_ok"]:
        problems.append(
            "piles.json does not hash to its own recorded digest (recorded %s, "
            "computed %s)" % (cut["recorded_digest"], cut["computed_digest"]))
    if not str(cut["computed_digest"]).startswith(PILES_SHA256_PREFIX):
        problems.append(
            "the cut digest no longer starts with the prefix CLAUDE.md pins (%s)"
            % PILES_SHA256_PREFIX)

    frames_by_game: Dict[str, int] = {}
    frame_files: Dict[str, Dict[str, int]] = {}
    synthetic_grids: List[Dict[str, Any]] = []
    review_grids: List[Dict[str, Any]] = []
    mentions: Dict[str, int] = {}
    scanned = 0

    for rel in paths:
        if not rel.endswith((".json", ".jsonl")):
            continue
        abs_path = os.path.join(REPO, rel)
        scanned += 1
        per_file: Dict[str, int] = {}
        anon = 0
        file_has_game_id = False
        for rec in _json_records(abs_path):
            ids: Set[str] = set()
            grids: List[str] = []
            _collect(rec, None, ids, grids)
            if ids:
                file_has_game_id = True
            if not grids:
                continue
            if ids:
                for gid in ids:
                    per_file[gid] = per_file.get(gid, 0) + len(grids)
            else:
                anon += len(grids)
        if per_file:
            frame_files[rel] = dict(sorted(per_file.items()))
            for gid, n in per_file.items():
                frames_by_game[gid] = frames_by_game.get(gid, 0) + n
        if anon:
            entry = {"path": rel, "grid_payloads": anon}
            # A grid in a file that names no game anywhere is a self-built
            # world -- the A0/A2/A3 sokoban and cart worlds, the exam's
            # synthetic papers. A grid in a file that *does* traffic in game ids
            # but left this one unlabelled is the case worth a human look.
            (synthetic_grids if not file_has_game_id else review_grids).append(entry)

    # Textual mentions of a sealed id, anywhere. Metadata, not frames -- but the
    # release should be able to say exactly where the sealed ids appear.
    sealed_set = set(sealed)
    for rel in paths:
        abs_path = os.path.join(REPO, rel)
        try:
            text = open(abs_path, "rb").read().decode("utf-8", "ignore")
        except OSError:
            continue
        hit = {g for g in GAME_ID_RE.findall(text) if g in sealed_set}
        if hit:
            mentions[rel] = len(hit)

    verdicts = {gid: classify(gid) for gid in frames_by_game}
    sealed_frames = {g: n for g, n in frames_by_game.items()
                     if verdicts[g] == "sealed"}
    unknown_frames = {g: n for g, n in frames_by_game.items()
                      if verdicts[g] == "unknown"}
    resolved_short = {g: classify(g) for g in frames_by_game
                      if g not in set(dev) | sealed_set}

    green = (not sealed_frames and not unknown_frames and not review_grids
             and not problems)

    return {
        "record": "redline",
        "id": "R-2",
        "claim": "no sealed-pile frame data appears in the release set",
        "cut_guard": cut["guard"],
        "piles_recorded_digest": cut["recorded_digest"],
        "piles_computed_digest": cut["computed_digest"],
        "piles_digest_ok": cut["digest_ok"],
        "piles_digest_prefix_expected": PILES_SHA256_PREFIX,
        "integrity_problems": problems,
        "dev_pile": dev,
        "sealed_count": len(sealed),
        "json_files_scanned": scanned,
        "frames_by_game": dict(sorted(frames_by_game.items())),
        "frame_pile_verdicts": dict(sorted(verdicts.items())),
        "short_form_ids_resolved": dict(sorted(resolved_short.items())),
        "frame_files": dict(sorted(frame_files.items())),
        "sealed_frames": sealed_frames,
        "frames_for_unregistered_game_ids": unknown_frames,
        "grids_in_files_that_name_no_game": sorted(
            synthetic_grids, key=lambda d: -d["grid_payloads"])[:10],
        "grids_needing_review": review_grids,
        "files_mentioning_a_sealed_id": len(mentions),
        "verdict": "GREEN" if green else "RED",
        "limits": [
            "Grid detection is shape-based (a rectangle of ints >= 2x2) and "
            "attribution is by game_id in the same record. A frame stored with its "
            "game_id stripped lands in grids_needing_review if the file names any "
            "game at all, and in grids_in_files_that_name_no_game otherwise; "
            "neither bucket is discarded.",
            "Pile membership is decided by battery.guard.Piles.classify, the same "
            "code the battery refuses sealed trajectories with, so the release "
            "cannot disagree with the battery about what is sealed. It resolves the "
            "short form the API also accepts (`g50t` -> g50t-5849a774 -> dev).",
            "Textual mentions of a sealed id are counted, not blocked. Sealed ids "
            "legitimately appear in piles.json, the contamination register, and the "
            "denial records that are themselves the hygiene evidence. See findings "
            "R-2a and R-2b for the two mentions that need a human ruling.",
        ],
    }


# ---------------------------------------------------------------------------
# candidate-stream validation (gap C-1: the live stream nothing ever checked)
# ---------------------------------------------------------------------------

def validate_candidate_streams(paths: List[str]) -> Dict[str, Any]:
    sys.path.insert(0, os.path.join(REPO, "engine-rig"))
    try:
        from tools.validate_candidates import validate_file  # type: ignore
    except Exception as exc:  # pragma: no cover - reported, not raised
        return {"record": "validation", "id": "candidates",
                "verdict": "UNAVAILABLE", "error": repr(exc), "streams": {}}

    streams = {}
    for rel in sorted(p for p in paths if match(p, "**/candidates*.jsonl")):
        try:
            errors = validate_file(os.path.join(REPO, rel))
        except Exception as exc:
            streams[rel] = {"status": "ERROR", "detail": repr(exc)}
            continue
        streams[rel] = {
            "status": "PASS" if not errors else "FAIL",
            "error_count": len(errors),
            "first_errors": errors[:3],
        }
    passed = sum(1 for v in streams.values() if v["status"] == "PASS")
    return {
        "record": "validation",
        "id": "candidates",
        "contract": "CONTRACTS/candidates_schema.md (frozen v0.1)",
        "validator": "engine-rig/tools/validate_candidates.py",
        "streams": streams,
        "passed": passed,
        "total": len(streams),
        "verdict": "GREEN" if passed == len(streams) else "MIXED",
        "note": "Gap C-1: theoria-arm's live stream had never been validated by "
                "anything in the tree. Whatever the verdict below says, it is the "
                "first time it has been asked.",
    }


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------

def build(paths: List[str]) -> Dict[str, Any]:
    files = []
    per_item_files: Dict[str, int] = {k["key"]: 0 for k in CHECKLIST}
    per_item_bytes: Dict[str, int] = {k["key"]: 0 for k in CHECKLIST}
    total_bytes = 0
    unclassified = 0

    for rel in paths:
        digest, size = sha256_file(rel)
        items = classify(rel)
        rec = {
            "record": "file",
            "path": rel,
            "sha256": digest,
            "bytes": size,
            "checklist": items,
        }
        d = dialect_of(rel)
        if d:
            rec["dialect"] = d
        if matches_any(rel, STUB_PATTERNS):
            rec["kind"] = "stub"
        files.append(rec)
        total_bytes += size
        if not items:
            unclassified += 1
        for key in items:
            per_item_files[key] += 1
            per_item_bytes[key] += size

    checklist_records = []
    for item in CHECKLIST:
        checklist_records.append({
            "record": "checklist",
            "item": item["item"],
            "key": item["key"],
            "title": item["title"],
            "status": item["status"],
            "files": per_item_files[item["key"]],
            "bytes": per_item_bytes[item["key"]],
            "gaps": item["gaps"],
            "notes": item["notes"],
        })

    header = {
        "record": "header",
        "schema": SCHEMA,
        "prompt_id": PROMPT_ID,
        "release_set": "git-tracked files, plus everything on disk under release/",
        "excluded_volatile": VOLATILE,
        "file_count": len(files),
        "total_bytes": total_bytes,
        "unclassified_files": unclassified,
        "checklist_items": len(CHECKLIST),
        "ready": sum(1 for i in CHECKLIST if i["status"] == READY),
        "partial": sum(1 for i in CHECKLIST if i["status"] == PARTIAL),
        "missing": sum(1 for i in CHECKLIST if i["status"] == MISSING),
        "note": "No wall clock and no commit id by design: two runs over an "
                "unchanged tree are byte-identical. Timestamps live in release/runs/.",
    }

    return {
        "header": header,
        "files": files,
        "checklist": checklist_records,
        "findings": [dict(f, record="finding") for f in STANDING_FINDINGS],
        "redlines": [redline_env(paths), redline_sealed(paths)],
        "validations": [validate_candidate_streams(paths)],
    }


def dump(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def write_manifest(built: Dict[str, Any]) -> None:
    lines = [dump(built["header"])]
    lines += [dump(r) for r in built["files"]]
    lines += [dump(r) for r in built["checklist"]]
    lines += [dump(r) for r in built["findings"]]
    lines += [dump(r) for r in built["redlines"]]
    lines += [dump(r) for r in built["validations"]]
    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# human-readable siblings
# ---------------------------------------------------------------------------

BADGE = {READY: "OK", PARTIAL: "PARTIAL", MISSING: "MISSING"}


def write_checklist(built: Dict[str, Any]) -> None:
    h = built["header"]
    out = []
    w = out.append
    w("# 释出清单 — Phase 4 checklist, ticked against the tree")
    w("")
    w("Generated by `release/manifest.py` from `release/checklist_spec.py`. ")
    w("Do not hand-edit: the next run overwrites it.")
    w("")
    w("This file is not listed in `MANIFEST.jsonl` — it reports the release set's")
    w("own byte total, so hashing it inside the pass that writes it has no fixed")
    w("point. Its integrity check is `git diff` after regeneration, which")
    w("`release/verify.sh` runs.")
    w("")
    w("`Theoria.md` Phase 4 names nine deliverables in one sentence. Each has a row.")
    w("A row is `OK` only when every part of it has an artefact; a named gap keeps it")
    w("`PARTIAL` however much else is present.")
    w("")
    w("| # | item | status | files | bytes | gaps |")
    w("|---|---|---|---|---|---|")
    for rec in built["checklist"]:
        w("| %d | %s | **%s** | %d | %s | %s |" % (
            rec["item"], rec["title"], BADGE[rec["status"]], rec["files"],
            f"{rec['bytes']:,}",
            ", ".join(g["id"] for g in rec["gaps"]) or "—",
        ))
    w("")
    w("Release set: **%d files, %s bytes**. %d ready, %d partial, %d missing."
      % (h["file_count"], f"{h['total_bytes']:,}", h["ready"], h["partial"],
         h["missing"]))
    w("")

    w("## Gaps, in full")
    w("")
    for rec in built["checklist"]:
        if not rec["gaps"]:
            continue
        w("### %d. %s" % (rec["item"], rec["title"]))
        w("")
        for g in rec["gaps"]:
            w("* **%s — %s.** %s" % (g["id"], g["what"], g["detail"]))
        w("")

    w("## Notes carried with the artefacts")
    w("")
    for rec in built["checklist"]:
        if not rec["notes"]:
            continue
        w("**%s**" % rec["title"])
        w("")
        for n in rec["notes"]:
            w("* %s" % n)
        w("")

    w("## Red lines")
    w("")
    for r in built["redlines"]:
        w("### %s — %s" % (r["id"], r.get("claim", "")))
        w("")
        w("Verdict: **%s**" % r["verdict"])
        w("")
        if r["id"] == "R-1":
            w("* mode: `%s` (.env %s on this machine)" % (
                r["mode"], "present" if r["dotenv_present"] else "absent"))
            w("* files scanned: %d; secrets checked by name: %s"
              % (r["files_scanned"], ", ".join(r["secrets_checked"]) or "none"))
            w("* verbatim-value hits: %d" % len(r["exact_hits"]))
            w("* unexplained key-shaped strings: %d `sk-*`, %d UUID-shaped"
              % (len(r["unexplained_sk_shaped"]), len(r["unexplained_uuid_shaped"])))
        else:
            w("* cut guard: `%s`" % r.get("cut_guard", "?"))
            w("* piles.json digest `%s` — recorded matches computed: %s"
              % (r.get("piles_computed_digest", "?"),
                 "yes" if r.get("piles_digest_ok") else "**NO**"))
            w("* dev pile: %s" % ", ".join(r.get("dev_pile", [])))
            w("* JSON files scanned: %d" % r.get("json_files_scanned", 0))
            w("* frames found, by game: %s" % (
                ", ".join("%s=%d" % kv for kv in r.get("frames_by_game", {}).items())
                or "none"))
            w("* every one of those ids classified: %s" % (
                ", ".join("%s→%s" % kv
                          for kv in r.get("frame_pile_verdicts", {}).items())
                or "n/a"))
            w("* frames belonging to a sealed game: **%d**"
              % sum(r.get("sealed_frames", {}).values()))
            w("* grid payloads needing review (unlabelled, in a file that does "
              "name games): **%d**" % len(r.get("grids_needing_review", [])))
            w("* grid payloads in files that name no game at all (self-built "
              "worlds): %d files" % len(r.get("grids_in_files_that_name_no_game", [])))
            w("* files mentioning a sealed id at all (metadata, not frames): %d"
              % r.get("files_mentioning_a_sealed_id", 0))
        w("")
        for lim in r.get("limits", []):
            w("> %s" % lim)
            w("")

    w("## Findings a reviewer will otherwise find first")
    w("")
    for f in built["findings"]:
        w("### %s — %s" % (f["id"], f["title"]))
        w("")
        w("*severity:* %s · *where:* `%s`" % (f["severity"], f["where"]))
        w("")
        w(f["detail"])
        w("")

    w("## Candidate streams, validated against the frozen contract")
    w("")
    v = built["validations"][0]
    w("Validator: `%s` · contract: `%s` · verdict: **%s** (%d/%d pass)"
      % (v.get("validator", "?"), v.get("contract", "?"), v["verdict"],
         v.get("passed", 0), v.get("total", 0)))
    w("")
    w("| stream | status | errors |")
    w("|---|---|---|")
    for path, res in v.get("streams", {}).items():
        w("| `%s` | %s | %s |" % (path, res["status"], res.get("error_count", "—")))
    w("")
    w("> %s" % v.get("note", ""))
    w("")

    with open(CHECKLIST_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")


INCIDENT_SOURCES = [
    ("arc-recon/data/incidents.jsonl", "jsonl", "INC-NNN"),
    ("arc-recon/data/contamination_log.jsonl", "jsonl", "contamination entries"),
    ("baseline-arms/INCIDENTS.md", "markdown", "INC-BA-NNN"),
    ("theoria-arm/INCIDENTS.md", "markdown", "INC-TA-NNN"),
]

INC_HEADING = re.compile(r"^#{2,3}\s*(INC-[A-Z]*-?\d+)", re.M)


def write_incidents_index() -> Dict[str, Any]:
    """A read-only index over four incident files in two schemas.

    It does not merge, renumber, or rewrite: three of the four belong to other
    territories. The release checklist says 'incident ledger', singular; this
    says out loud that it is four files, and points at each.
    """
    rows = []
    for rel, fmt, family in INCIDENT_SOURCES:
        abs_path = os.path.join(REPO, rel)
        ids: List[str] = []
        if not os.path.exists(abs_path):
            rows.append({"path": rel, "format": fmt, "family": family,
                         "count": 0, "ids": [], "missing": True})
            continue
        if fmt == "jsonl":
            for rec in _json_records(abs_path):
                if isinstance(rec, dict):
                    ids.append(str(rec.get("id") or rec.get("game_id") or "?"))
        else:
            text = open(abs_path, encoding="utf-8").read()
            ids = INC_HEADING.findall(text)
        rows.append({"path": rel, "format": fmt, "family": family,
                     "count": len(ids), "ids": ids, "missing": False})

    out = []
    w = out.append
    w("# incident ledger — index over four files in two schemas")
    w("")
    w("Generated by `release/manifest.py`. Read-only: it indexes, it does not merge.")
    w("Three of the four originals belong to other territories and are theirs to edit.")
    w("")
    w("`Theoria.md` Phase 4 lists `incident ledger` in the singular. The tree has")
    w("three id families, two schemas, and four files, plus a fifth surface that is")
    w("defined and never used (`proxy/LEDGER_FORMAT.md` section 6 specifies an")
    w("`incident` record type inside the run ledger; nothing has ever written one).")
    w("Unifying them is a real piece of work and it is not P-19's. Naming the split is.")
    w("")
    w("| file | schema | id family | records |")
    w("|---|---|---|---|")
    for r in rows:
        w("| `%s` | %s | %s | %s |" % (
            r["path"], r["format"], r["family"],
            "**MISSING**" if r["missing"] else r["count"]))
    w("")
    w("Total records across all four: **%d**." % sum(r["count"] for r in rows))
    w("")
    for r in rows:
        if r["missing"] or not r["ids"]:
            continue
        w("### `%s`" % r["path"])
        w("")
        w(", ".join("`%s`" % i for i in r["ids"]))
        w("")
    with open(INCIDENTS_INDEX_PATH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(out) + "\n")
    return {"record": "incidents_index", "sources": rows,
            "total": sum(r["count"] for r in rows)}


# ---------------------------------------------------------------------------
# --check
# ---------------------------------------------------------------------------

def read_manifest() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not os.path.exists(MANIFEST_PATH):
        return out
    with open(MANIFEST_PATH, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("record") == "file":
                out[rec["path"]] = rec
    return out


def check(built: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    old = read_manifest()
    new = {r["path"]: r for r in built["files"]}
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(
        p for p in set(old) & set(new) if old[p]["sha256"] != new[p]["sha256"]
    )
    redlines_green = all(r["verdict"] == "GREEN" for r in built["redlines"])
    ok = not added and not removed and not changed and redlines_green
    return ok, {
        "manifest_present": bool(old),
        "added": added, "removed": removed, "changed": changed,
        "redlines": {r["id"]: r["verdict"] for r in built["redlines"]},
        "redlines_green": redlines_green,
    }


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="recompute and diff against MANIFEST.jsonl; do not write")
    ap.add_argument("--redlines-only", action="store_true",
                    help="run R-1 and R-2 and nothing else")
    ap.add_argument("--json", action="store_true", help="machine-readable summary")
    args = ap.parse_args(argv)

    paths = release_set()

    if args.redlines_only:
        results = [redline_env(paths), redline_sealed(paths)]
        for r in results:
            print("%s %s  %s" % (r["id"], r["verdict"], r.get("claim", "")))
            if r["verdict"] != "GREEN":
                print(dump(r))
        return 0 if all(r["verdict"] == "GREEN" for r in results) else 1

    if not args.check:
        # Generated docs first, then the hash pass, so the manifest describes the
        # tree it was written against rather than the one before it.
        write_incidents_index()

    built = build(paths)

    if args.check:
        ok, detail = check(built)
        if args.json:
            print(dump(detail))
        else:
            if not detail["manifest_present"]:
                print("MANIFEST.jsonl is absent -- nothing to check against.")
            print("added:   %d" % len(detail["added"]))
            for p in detail["added"][:20]:
                print("  + %s" % p)
            print("removed: %d" % len(detail["removed"]))
            for p in detail["removed"][:20]:
                print("  - %s" % p)
            print("changed: %d" % len(detail["changed"]))
            for p in detail["changed"][:20]:
                print("  ~ %s" % p)
            print("redlines: %s" % detail["redlines"])
            print("VERDICT: %s" % ("GREEN" if ok else "RED"))
        return 0 if ok else 1

    write_checklist(built)
    write_manifest(built)

    h = built["header"]
    print("release set: %d files, %s bytes" % (h["file_count"], f"{h['total_bytes']:,}"))
    print("checklist:   %d ready, %d partial, %d missing"
          % (h["ready"], h["partial"], h["missing"]))
    for r in built["redlines"]:
        print("%s: %s (%s)" % (r["id"], r["verdict"], r.get("mode", "")))
    v = built["validations"][0]
    print("candidates:  %s (%s/%s streams pass)"
          % (v["verdict"], v.get("passed"), v.get("total")))
    print("wrote %s" % os.path.relpath(MANIFEST_PATH, REPO))
    print("wrote %s" % os.path.relpath(CHECKLIST_PATH, REPO))
    print("wrote %s" % os.path.relpath(INCIDENTS_INDEX_PATH, REPO))
    return 0 if all(r["verdict"] == "GREEN" for r in built["redlines"]) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
