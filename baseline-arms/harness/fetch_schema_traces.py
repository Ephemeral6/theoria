"""Path A: fetch the upstream Schema trajectories, but only the 4 development-pile games.

`Theoria.md` line 311 permits exactly this and nothing wider: the Phase-2 metric
battery may read "Schema (reproduction bucket + *the games in the upstream
artifacts that belong to the development pile*)", and sealed-pile trajectories
are forbidden "including the parts of upstream released artifacts belonging to
sealed games -- reading those teaches us that game's mechanics just as well".

The upstream dataset covers all 25 games, so a whole-repo pull would contaminate
21 sealed games at once, with material that is *worse* than playing them: each
game directory carries that game's finished `world_model_v*.py` and the author's
`notes.md` -- the answer, not the puzzle. INC-BA-001 is the local proof that the
danger is real and that it arrives during retrieval, before anyone has decided
to read anything.

So the guard here is structural, in three parts:

  * **Positive allowlist, default deny.** A path is fetched only if it contains
    one of the 4 development-pile game ids. Not "fetched unless it names a
    sealed game" -- a denylist fails open on any path shape we did not predict,
    and the failure is irreversible.
  * **The filter runs on the file *listing*, before a single byte of content is
    requested.** Names are cheap and safe; content is neither.
  * **Nothing here decodes, prints or summarises what it downloads.** Bytes go
    from the socket to disk to a sha256, and the only thing that comes back up
    is the manifest. A downloader that reports what it found has already leaked.

    python -m harness.fetch_schema_traces --dry-run   # listing + partition only
    python -m harness.fetch_schema_traces             # fetch the allowed subset

The payload lands in `schema_traces/` and is gitignored: it is third-party data
with no declared licence (SCHEMA_LOCATE.md section 4), so this track records its
provenance and hashes rather than re-publishing it. See DECISIONS.md D-011.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from . import arc_client, ledger

TRACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(TRACK, "schema_traces")
MANIFEST_PATH = os.path.join(DEST, "MANIFEST.json")

DATASET = "schema-harness/arc-agi-3-schema-traces"
HF_API = "https://huggingface.co/api/datasets/%s" % DATASET
HF_RESOLVE = "https://huggingface.co/datasets/%s/resolve/%%s/%%s" % DATASET
UA = {"User-Agent": "theoria-baseline-arms/0.1", "Accept": "application/json"}

MAX_TOTAL_BYTES = 512 * 1024 * 1024      # a wrong filter should hit a wall, not a bill


class WhitelistError(RuntimeError):
    """Raised when a path that is not positively allowed reaches a fetch."""


# ------------------------------------------------------------------ the guard
def dev_ids() -> List[str]:
    return sorted(arc_client.dev_pile())


def sealed_ids() -> List[str]:
    return sorted(arc_client.sealed_pile())


def piles_digest() -> Dict[str, Any]:
    """Both hashes of the pile cut, each with its convention named.

    `piles.json` carries a `sha256` field, and CLAUDE.md cites that value as the
    identity of the cut. A file cannot contain its own raw hash, so the two are
    necessarily different numbers, and a manifest that recorded only the raw one
    would look like evidence of a tampered cut to anyone diffing it against
    CLAUDE.md. Record both, say which is which, and check the declared one.
    """
    raw = open(arc_client.PILES_PATH, "rb").read()
    doc = json.loads(raw)
    declared = doc.get("sha256")
    body = {k: v for k, v in doc.items() if k != "sha256"}
    canonical = hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "file_sha256": hashlib.sha256(raw).hexdigest(),
        "file_sha256_convention": "sha256 of the raw bytes of arc-recon/data/piles.json",
        "declared_sha256": declared,
        "recomputed_declared_sha256": canonical,
        "declared_sha256_convention": ("sha256 of json.dumps(doc minus the 'sha256' key, "
                                       "sort_keys=True, separators=(',',':'))"),
        "declared_sha256_verified": declared == canonical,
        "cut_version": doc.get("cut_version"),
    }


def names_game(path_lower: str, game_id: str) -> bool:
    """Does this path name this game?

    Upstream never writes the full pile id -- directories are named with the
    4-character prefix alone (`..._max_ar25_100.0`). So matching has to be on
    the prefix, and the prefix has to be boundary-anchored: a bare substring
    test would match those four characters anywhere inside a hash, and a
    *sealed* prefix matching a hash by accident would deny a file we wanted,
    while a *dev* prefix matching one would fetch a file we must not have.
    """
    if game_id in path_lower:
        return True
    prefix = re.escape(game_id.split("-")[0])
    return re.search(r"(^|[^a-z0-9])%s([^a-z0-9]|$)" % prefix, path_lower) is not None


def match_dev(path: str, dev: List[str]) -> Optional[str]:
    lowered = path.lower()
    for gid in dev:
        if names_game(lowered, gid):
            return gid
    return None


def classify(path: str, dev: List[str], sealed: List[str]) -> Tuple[str, Optional[str]]:
    """(verdict, game_id). verdict is "allow", "deny_sealed" or "deny_unknown".

    Order matters: sealed is tested *first*, so that a path naming both a sealed
    and a development game (a cross-game summary file, say) is denied rather
    than allowed. And anything naming no game at all is denied, not allowed --
    top-level aggregate files such as the evaluation CSVs carry per-game rows
    for all 25 games, which is `scores_only` contamination for 21 of them.
    """
    lowered = path.lower()
    for gid in sealed:
        if names_game(lowered, gid):
            return "deny_sealed", gid
    gid = match_dev(path, dev)
    return ("allow", gid) if gid else ("deny_unknown", None)


def partition(paths: List[str]) -> Dict[str, Any]:
    dev, sealed = dev_ids(), sealed_ids()
    allow: List[str] = []
    denied_sealed: Dict[str, int] = {}
    denied_unknown: List[str] = []
    for path in paths:
        verdict, gid = classify(path, dev, sealed)
        if verdict == "allow":
            allow.append(path)
        elif verdict == "deny_sealed":
            denied_sealed[gid] = denied_sealed.get(gid, 0) + 1
        else:
            denied_unknown.append(path)

    # Belt and braces: re-check every allowed path against every sealed id, so a
    # bug in `classify` cannot quietly let one through.
    # Deliberately a *stricter* test than `classify` uses: a bare substring,
    # unanchored. If this ever disagrees with the boundary-anchored test above,
    # the disagreement resolves as "deny".
    for path in allow:
        for gid in sealed:
            if gid.split("-")[0] in path.lower() or gid in path.lower():
                raise WhitelistError("allowed path %r names sealed game %s" % (path, gid))

    return {"allow": sorted(allow),
            "denied_sealed_counts": dict(sorted(denied_sealed.items())),
            "denied_unknown": sorted(denied_unknown)}


# -------------------------------------------------------------------- transport
def _get(url: str, tries: int = 5, binary: bool = False):
    last = None
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA),
                                        timeout=60) as response:
                data = response.read()
                return data if binary else json.loads(data), dict(response.headers)
        except Exception as exc:                       # HF resets connections at random
            last = exc
            time.sleep(1.0 * (k + 1))
    raise RuntimeError("GET %s failed after %d tries: %s: %s"
                       % (url.split("?")[0], tries, type(last).__name__, last))


def repo_revision() -> str:
    meta, _ = _get(HF_API)
    return meta["sha"]


def list_tree(revision: str) -> List[Dict[str, Any]]:
    """Every file in the repo -- names, sizes and blob oids only, no content."""
    url = "%s/tree/%s?recursive=true&expand=true" % (HF_API, revision)
    entries: List[Dict[str, Any]] = []
    while url:
        page, headers = _get(url)
        entries.extend(e for e in page if e.get("type") == "file")
        link = headers.get("Link") or headers.get("link") or ""
        match = re.search(r'<([^>]+)>;\s*rel="next"', link)
        url = match.group(1) if match else None
    return entries


def size_of(entry: Dict[str, Any]) -> int:
    lfs = entry.get("lfs") or {}
    return int(lfs.get("size") or entry.get("size") or 0)


def oid_of(entry: Dict[str, Any]) -> Optional[str]:
    lfs = entry.get("lfs") or {}
    return lfs.get("oid") or entry.get("oid")


# ---------------------------------------------------------------------- fetch
def fetch(entry: Dict[str, Any], revision: str, allow: set) -> Dict[str, Any]:
    path = entry["path"]
    if path not in allow:                              # the guard, at the socket
        raise WhitelistError("refusing to fetch %r: not on the allowlist" % path)
    url = HF_RESOLVE % (revision, urllib.request.quote(path))
    blob, _ = _get(url, binary=True)
    target = os.path.join(DEST, path.replace("/", os.sep))
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "wb") as fh:                     # bytes only; never decoded here
        fh.write(blob)
    return {"path": path, "bytes": len(blob),
            "sha256": hashlib.sha256(blob).hexdigest(),
            "hf_oid": oid_of(entry)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    dev, sealed = dev_ids(), sealed_ids()
    print("development pile (allowlist): %s" % ", ".join(dev))
    print("sealed pile: %d ids, all denied" % len(sealed))

    revision = repo_revision()
    entries = list_tree(revision)
    by_path = {e["path"]: e for e in entries}
    part = partition(list(by_path))

    allow = part["allow"]
    total_bytes = sum(size_of(by_path[p]) for p in allow)
    per_game: Dict[str, Dict[str, int]] = {}
    for p in allow:
        gid = match_dev(p, dev)
        row = per_game.setdefault(gid, {"files": 0, "bytes": 0})
        row["files"] += 1
        row["bytes"] += size_of(by_path[p])

    print("\nrevision %s | %d files in repo" % (revision, len(by_path)))
    print("  allowed        %4d files, %.1f MB" % (len(allow), total_bytes / 1e6))
    print("  denied sealed  %4d files across %d sealed games"
          % (sum(part["denied_sealed_counts"].values()), len(part["denied_sealed_counts"])))
    print("  denied unknown %4d files (no game id in path -- default deny)"
          % len(part["denied_unknown"]))
    for gid, row in sorted(per_game.items()):
        print("    %s  %3d files  %.1f MB" % (gid, row["files"], row["bytes"] / 1e6))

    if total_bytes > MAX_TOTAL_BYTES:
        print("\nallowed set is %.0f MB, over the %.0f MB ceiling -- refusing"
              % (total_bytes / 1e6, MAX_TOTAL_BYTES / 1e6))
        return 4

    manifest = {
        "source": {"kind": "huggingface_dataset", "id": DATASET, "revision": revision,
                   "url": "https://huggingface.co/datasets/%s" % DATASET,
                   "licence": "not declared upstream (see SCHEMA_LOCATE.md section 4)"},
        "authority": "Theoria.md:311 -- development-pile games only",
        "piles_json": piles_digest(),
        "dev_pile": dev,
        "repo_files_total": len(by_path),
        "allowed_files": len(allow),
        "denied_sealed_files": sum(part["denied_sealed_counts"].values()),
        "denied_sealed_counts": part["denied_sealed_counts"],
        "denied_unknown_files": len(part["denied_unknown"]),
        "denied_unknown_paths": part["denied_unknown"],
        "per_game": per_game,
        "fetched_at": ledger.utcnow(),
    }

    if args.dry_run:
        manifest["dry_run"] = True
        manifest["files"] = [{"path": p, "bytes": size_of(by_path[p]),
                              "hf_oid": oid_of(by_path[p])} for p in allow]
        print(json.dumps({k: manifest[k] for k in
                          ("source", "allowed_files", "denied_sealed_files",
                           "denied_unknown_files", "per_game")},
                         indent=2, sort_keys=True))
        return 0

    os.makedirs(DEST, exist_ok=True)
    allow_set = set(allow)
    files: List[Dict[str, Any]] = []
    for i, path in enumerate(allow, 1):
        files.append(fetch(by_path[path], revision, allow_set))
        if i % 25 == 0 or i == len(allow):
            print("  fetched %d/%d" % (i, len(allow)), flush=True)
    manifest["files"] = files
    manifest["fetched_bytes"] = sum(f["bytes"] for f in files)
    manifest["payload_sha256"] = hashlib.sha256(
        "\n".join("%s %s" % (f["sha256"], f["path"]) for f in
                  sorted(files, key=lambda f: f["path"])).encode()).hexdigest()

    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
    ledger.probe("schema_traces_fetch", {
        "dataset": DATASET, "revision": revision,
        "allowed_files": len(files), "fetched_bytes": manifest["fetched_bytes"],
        "denied_sealed_files": manifest["denied_sealed_files"],
        "denied_unknown_files": manifest["denied_unknown_files"],
        "payload_sha256": manifest["payload_sha256"],
    })
    print("\nwrote %s (%d files, %.1f MB, payload sha256 %s)"
          % (MANIFEST_PATH, len(files), manifest["fetched_bytes"] / 1e6,
             manifest["payload_sha256"][:16]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
