"""Shared helpers for the four fleet skills.

This file is duplicated verbatim into each skill's `scripts/` directory so that
every skill is self-contained (a skill must work even if the other three are
removed). If you change it, change all four copies; `_fleet.py` carries its own
sha256 in FLEET_COMMON_VERSION so drift is detectable.

Nothing here touches the network, and nothing here ever prints a credential.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FLEET_COMMON_VERSION = "1"

# --------------------------------------------------------------------------
# process


def run(cmd, cwd=None, check=False):
    """Run a command, return (rc, stdout, stderr). Never raises on non-zero
    unless check=True. Output is decoded as UTF-8 with replacement, because
    this repo's tracked prose is UTF-8 while Windows consoles are not."""
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    if check and proc.returncode != 0:
        raise RuntimeError(
            "command failed (%d): %s\n%s\n%s" % (proc.returncode, " ".join(cmd), out, err)
        )
    return proc.returncode, out, err


def git(args, cwd=None, check=False):
    return run(["git"] + list(args), cwd=cwd, check=check)


# --------------------------------------------------------------------------
# repo geometry


def repo_root(cwd=None):
    rc, out, err = git(["rev-parse", "--show-toplevel"], cwd=cwd)
    if rc != 0:
        die("not inside a git repository: %s" % err.strip())
    return Path(out.strip())


def git_dir(cwd=None):
    """The *worktree's* git dir. For a linked worktree this is
    <main>/.git/worktrees/<name>, which is never tracked and never committed --
    the right place to park per-ticket scratch state."""
    rc, out, err = git(["rev-parse", "--absolute-git-dir"], cwd=cwd)
    if rc != 0:
        die("not inside a git repository: %s" % err.strip())
    return Path(out.strip())


def ctx_path(cwd=None):
    return git_dir(cwd) / "fleet-ticket.json"


def load_ctx(cwd=None):
    """Ticket context written by fleet-branch-ritual: prompt_id, branch,
    base_commit, territory, worktree, baseline test result. Returns {} when the
    ritual was not used (every skill must still work without it)."""
    p = ctx_path(cwd)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_ctx(data, cwd=None):
    p = ctx_path(cwd)
    p.parent.mkdir(parents=True, exist_ok=True)
    write_text(p, json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    return p


# --------------------------------------------------------------------------
# text / time / hashing -- all deterministic, all LF, all UTF-8


def read_text(path):
    return Path(path).read_text(encoding="utf-8")


def write_text(path, text):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return p


def utc_now(override=None):
    """UTC now, or a fixed instant. `override` (or $FLEET_NOW) makes every
    artefact this repo generates byte-reproducible for a rehearsal or a test."""
    src = override or os.environ.get("FLEET_NOW")
    if src:
        return datetime.fromisoformat(src.replace("Z", "+00:00")).astimezone(timezone.utc)
    return datetime.now(timezone.utc)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------
# territory conventions


def detect_test_cmd(territory_abs):
    """The repo's convention is uniform: every territory that has tests runs
    them with `python -m pytest` from the territory root (engine-rig,
    theory-compiler, proxy, battery, exam, theoria-arm, cold-start-a*, a0-spike
    keep pytest.ini or tests/ there; arc-recon keeps test_hygiene.py at its
    root). Returns None for prose-only territories -- papers/, browser-ops/,
    monitor/, CONTRACTS/, .claude/skills/ -- where the honest report is
    '不适用', not a fabricated green."""
    t = Path(territory_abs)
    if not t.is_dir():
        return None
    markers = ["pytest.ini", "conftest.py", "pyproject.toml", "tox.ini", "setup.cfg"]
    if any((t / m).exists() for m in markers):
        return [sys.executable, "-m", "pytest"]
    if (t / "tests").is_dir():
        return [sys.executable, "-m", "pytest"]
    if any(t.glob("test_*.py")) or any(t.glob("*_test.py")):
        return [sys.executable, "-m", "pytest"]
    return None


def summarise_pytest(out, err):
    """Pull pytest's own last summary line out, so the report quotes the tool
    rather than paraphrasing it."""
    text = (out or "") + (err or "")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in reversed(lines):
        stripped = line.strip("= ").strip()
        if any(w in stripped for w in ("passed", "failed", "error", "no tests ran", "skipped")):
            return stripped
    return lines[-1] if lines else "(no output)"


def rel(path, root):
    try:
        return str(Path(path).resolve().relative_to(Path(root).resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


# --------------------------------------------------------------------------
# reporting


def die(msg, code=2):
    sys.stderr.write("fleet: %s\n" % msg)
    raise SystemExit(code)


def say(msg=""):
    sys.stdout.write(msg + "\n")


class Checklist:
    """A checklist that keeps going after a failure and prints every line.
    '不绿报清单': a red run must show the whole list, not just the first stop."""

    def __init__(self, title):
        self.title = title
        self.rows = []

    def add(self, ok, name, detail=""):
        self.rows.append({"ok": bool(ok), "name": name, "detail": detail})
        return ok

    @property
    def failed(self):
        return [r for r in self.rows if not r["ok"]]

    def render(self):
        lines = ["", "== %s ==" % self.title]
        for r in self.rows:
            mark = "PASS" if r["ok"] else "FAIL"
            lines.append("[%s] %s%s" % (mark, r["name"], (" -- " + r["detail"]) if r["detail"] else ""))
        n = len(self.rows)
        bad = len(self.failed)
        lines.append("-- %d/%d green%s" % (n - bad, n, "" if not bad else "  <<< NOT GREEN"))
        return "\n".join(lines)

    def emit(self):
        say(self.render())
        return 0 if not self.failed else 1
