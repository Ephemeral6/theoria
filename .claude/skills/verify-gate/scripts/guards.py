#!/usr/bin/env python
"""verify-gate guards -- the three repo-wide red lines, as executable checks.

  guards.py boundary --base <sha> --territory <dir> [--allow <path>...]
  guards.py sealed    --base <sha> [--allow <path>...]
  guards.py secret    --base <sha>

Each exits 0 green, 1 red, 2 on a usage problem, and prints a checklist. They
are deliberately separate processes so `verify.sh` stays readable and any
harness in any language can gate on the exit codes.

`secret` never prints a credential: it reports file names and match counts.
"""

from __future__ import annotations

import pathlib
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fleet import Checklist, die, git, read_text, repo_root, say  # noqa: E402

# Files whose job is to hold these strings. Matches here are not violations.
SEALED_ALLOW_DEFAULT = (
    "arc-recon/data/piles.json",
    "arc-recon/data/contamination_log.jsonl",
    "arc-recon/data/claim_set.json",
    "arc-recon/data/incidents.jsonl",
    "arc-recon/data/canary.json",
)
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".gz", ".whl",
              ".so", ".dll", ".pyc", ".ico", ".woff", ".woff2"}


def changed_paths(root, base):
    """Everything this branch touches, committed or not, plus new untracked
    files. A guard that only looks at commits misses the file you were about
    to commit."""
    paths = set()
    rc, out, err = git(["diff", "--name-only", base], cwd=root)
    if rc != 0:
        die("git diff against %s failed: %s" % (base, err.strip()))
    paths.update(p for p in out.splitlines() if p.strip())
    rc, out, _ = git(["ls-files", "--others", "--exclude-standard"], cwd=root)
    paths.update(p for p in out.splitlines() if p.strip())
    return sorted(paths)


def readable_text(path):
    if path.suffix.lower() in BINARY_EXT:
        return None
    try:
        if path.stat().st_size > 32 * 1024 * 1024:
            return None
        return path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, ValueError):
        return None


# --------------------------------------------------------------------------


def cmd_boundary(args, root):
    """领地: nothing outside the declared territory may change. PARTNER_SYNC.md
    is the one shared file every ticket appends to."""
    allow = set(args.allow or []) | {"PARTNER_SYNC.md"}
    territory = args.territory.replace("\\", "/").rstrip("/")
    cl = Checklist("boundary -- territory %s" % territory)
    strays = []
    for p in changed_paths(root, args.base):
        if p in allow or p.startswith(territory + "/") or p == territory:
            continue
        if any(p.startswith(a.rstrip("/") + "/") for a in allow):
            continue
        strays.append(p)
    cl.add(not strays, "no file changed outside the territory",
           ("%d stray: " % len(strays)) + ", ".join(strays[:8]) if strays else "clean")
    if strays:
        say("")
        say("stray paths (each one is another track's ground unless the工单 said otherwise):")
        for p in strays:
            say("  " + p)
        say("If a stray is legitimate, pass --allow <path> and say why in RUN_STATE.")
    return cl.emit()


def cmd_sealed(args, root):
    """封存堆: no sealed game id may appear in anything this branch adds.
    Reading about a sealed game teaches its mechanics as surely as playing it,
    so an id showing up in a new artefact is a contamination event."""
    piles_path = root / "arc-recon" / "data" / "piles.json"
    cl = Checklist("sealed pile")
    if not piles_path.exists():
        cl.add(False, "piles.json present", str(piles_path))
        return cl.emit()
    piles = json.loads(read_text(piles_path))
    dev = set(piles.get("dev_pile") or [])
    sealed = sorted(set(piles.get("contamination_register") or {}) - dev) or \
        sorted(set(piles.get("sealed_pile") or []))
    cl.add(bool(sealed), "sealed set loaded", "%d sealed / %d dev" % (len(sealed), len(dev)))

    allow = set(SEALED_ALLOW_DEFAULT) | set(args.allow or [])
    hits = []
    for relp in changed_paths(root, args.base):
        if relp in allow:
            continue
        p = root / relp
        if not p.is_file():
            continue
        text = readable_text(p)
        if text is None:
            continue
        found = sorted({g for g in sealed if g in text})
        if found:
            hits.append((relp, found))
    cl.add(not hits, "no sealed game id in changed files",
           "%d file(s) hit" % len(hits) if hits else "%d file(s) scanned" %
           len(changed_paths(root, args.base)))
    if hits:
        say("")
        say("sealed ids found in files this branch changed:")
        for relp, found in hits:
            say("  %s  <-  %s" % (relp, ", ".join(found)))
        say("This is an incident unless the file's job is to register contamination.")
        say("Record it in arc-recon (INCIDENTS / contamination_log), or --allow the path.")
    return cl.emit()


def cmd_secret(args, root):
    """密钥: ARC_API_KEY must never reach a tracked file. Phase 4 publishes
    every tracked file and git history makes it irreversible."""
    cl = Checklist("credential sealing")
    # .env is gitignored, so it exists only in the main checkout; a guard
    # that reads it relative to a worktree passes green because the check
    # never ran (the repo's recurring failure shape). Resolve the main
    # checkout root through git, and treat a missing .env as RED.
    rc, common, _ = git(["rev-parse", "--git-common-dir"], cwd=root)
    main_root = pathlib.Path(common.strip()).resolve().parent if rc == 0 else root
    env = main_root / ".env"
    cl.add(env.exists(), ".env found at the main checkout",
           str(env) if env.exists() else
           "MISSING at %s -- the credential guard cannot run; this is red, "
           "not vacuously green" % env)
    rc, out, _ = git(["check-ignore", "-q", ".env"], cwd=root)
    cl.add(rc == 0 or not env.exists(), ".env is gitignored",
           "ignored" if rc == 0 else ("absent" if not env.exists() else "TRACKED -- fix now"))

    rc, out, _ = git(["ls-files", "--error-unmatch", ".env"], cwd=root)
    cl.add(rc != 0, ".env is not tracked", "not tracked" if rc != 0 else "TRACKED")

    secrets = []
    if env.exists():
        for line in read_text(env).splitlines():
            m = re.match(r"\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$", line)
            if not m:
                continue
            value = m.group(2).strip().strip('"').strip("'")
            if len(value) >= 12:
                secrets.append((m.group(1), value))
    cl.add(True, "secrets loaded from .env", "%d variable(s) long enough to leak" % len(secrets))

    leaks = []
    if secrets:
        rc, out, err = git(["ls-files"], cwd=root)
        tracked = [p for p in out.splitlines() if p.strip()]
        scan = set(tracked) | set(changed_paths(root, args.base))
        for relp in sorted(scan):
            p = root / relp
            if not p.is_file():
                continue
            text = readable_text(p)
            if text is None:
                continue
            for name, value in secrets:
                if value in text:
                    leaks.append((relp, name))
        cl.add(not leaks, "no secret value in any tracked file",
               "%d leak(s)" % len(leaks) if leaks else "%d file(s) scanned" % len(scan))
    else:
        cl.add(True, "no secret value in any tracked file", "no .env values to look for")

    if leaks:
        say("")
        say("A credential value appears in these tracked files (value withheld):")
        for relp, name in leaks:
            say("  %s  <-  $%s" % (relp, name))
        say("Do not commit. Remove the value, use arc-recon/client.py load_api_key()/mask(),")
        say("and file an incident -- a committed key is a published key.")
    return cl.emit()


# --------------------------------------------------------------------------


def main(argv=None):
    ap = argparse.ArgumentParser(description="Theoria fleet: repo-wide guards")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, needs_territory in (("boundary", cmd_boundary, True),
                                      ("sealed", cmd_sealed, False),
                                      ("secret", cmd_secret, False)):
        p = sub.add_parser(name)
        p.add_argument("--base", required=True, help="base commit this branch forked from")
        p.add_argument("--allow", action="append", help="repo-relative path to exempt")
        if needs_territory:
            p.add_argument("--territory", required=True)
        p.set_defaults(fn=fn)
    args = ap.parse_args(argv)
    return args.fn(args, repo_root(Path.cwd()))


if __name__ == "__main__":
    raise SystemExit(main())
