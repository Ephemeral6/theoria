#!/usr/bin/env python
"""fleet-branch-ritual -- the start-of-ticket ritual, in one command.

  python .claude/skills/fleet-branch-ritual/scripts/start_ritual.py \
      --ticket P-24 --slug fleet-skills --territory .claude/skills

Does, in order:
  1. fetch origin (tolerated offline),
  2. resolve the newest master (origin/master when it is ahead of local),
  3. cut `agent/<ticket>-<slug>` from it and add an isolated worktree,
  4. print the PARTNER_SYNC.md tail and the territory's STATUS/DECISIONS files,
  5. run the territory's test suite in the new worktree as a *baseline*,
  6. write the ticket context to the worktree's git dir, where runs-archive,
     verify-gate and handoff-close pick it up (never a tracked file).

Nothing is committed and nothing is pushed. Run it from the main checkout.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fleet import (  # noqa: E402
    Checklist, detect_test_cmd, die, git, iso, load_ctx, read_text, rel,
    repo_root, run, save_ctx, say, summarise_pytest, utc_now,
)


def sync_tail(sync_path, sections):
    """Last N `## [track] ...` sections of PARTNER_SYNC.md. The board is
    append-only, so the tail is the whole of what is new since you last looked."""
    if not sync_path.exists():
        return "(PARTNER_SYNC.md not found)"
    text = read_text(sync_path)
    parts = re.split(r"(?m)^(?=## )", text)
    tail = [p for p in parts if p.strip()][-sections:]
    return "".join(tail).rstrip()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Theoria fleet: start-of-ticket ritual")
    ap.add_argument("--ticket", required=True, help="prompt id, e.g. P-24 / A-1 / R-1")
    ap.add_argument("--slug", required=True, help="branch slug, e.g. fleet-skills")
    ap.add_argument("--territory", required=True,
                    help="repo-relative directory this ticket may write to, e.g. engine-rig")
    ap.add_argument("--worktree", default=None,
                    help="worktree path (default: <repo-parent>/theoria-wt-<ticket lowercased>)")
    ap.add_argument("--branch", default=None, help="override branch name")
    ap.add_argument("--base", default=None, help="override base ref (default: newest master)")
    ap.add_argument("--sections", type=int, default=3, help="PARTNER_SYNC sections to show")
    ap.add_argument("--no-tests", action="store_true", help="skip the baseline test run")
    ap.add_argument("--no-fetch", action="store_true", help="skip `git fetch origin`")
    ap.add_argument("--prompt", default=None,
                    help="path to the prompt file (default: monitor/prompts/<TICKET>-<slug>.md if present)")
    ap.add_argument("--now", default=None, help="fixed UTC instant (rehearsals/tests)")
    args = ap.parse_args(argv)

    root = repo_root(Path.cwd())
    cl = Checklist("fleet-branch-ritual  %s" % args.ticket)

    ticket = args.ticket.strip()
    short = ticket.lower().replace("-", "")
    branch = args.branch or "agent/%s-%s" % (ticket.lower(), args.slug)
    wt = Path(args.worktree) if args.worktree else root.parent / ("theoria-wt-%s" % short)

    # 1 -- fetch
    if args.no_fetch:
        cl.add(True, "fetch origin", "skipped (--no-fetch)")
    else:
        rc, _, err = git(["fetch", "origin"], cwd=root)
        cl.add(True, "fetch origin",
               "ok" if rc == 0 else "offline/failed, using local refs (%s)" % err.strip().splitlines()[:1])

    # 2 -- newest master
    if args.base:
        base_ref = args.base
    else:
        rc_o, out_o, _ = git(["rev-parse", "--verify", "-q", "origin/master"], cwd=root)
        rc_l, out_l, _ = git(["rev-parse", "--verify", "-q", "master"], cwd=root)
        if rc_o == 0 and rc_l == 0:
            # origin/master unless local master already contains it
            rc_a, _, _ = git(["merge-base", "--is-ancestor", "origin/master", "master"], cwd=root)
            base_ref = "master" if rc_a == 0 else "origin/master"
        elif rc_l == 0:
            base_ref = "master"
        elif rc_o == 0:
            base_ref = "origin/master"
        else:
            die("neither master nor origin/master exists")
    rc, out, err = git(["rev-parse", base_ref], cwd=root)
    if rc != 0:
        die("cannot resolve base ref %s: %s" % (base_ref, err.strip()))
    base_commit = out.strip()
    cl.add(True, "base = newest master", "%s (%s)" % (base_commit[:7], base_ref))

    # 3 -- branch + worktree
    rc, _, _ = git(["rev-parse", "--verify", "-q", "refs/heads/" + branch], cwd=root)
    if rc == 0:
        die("branch %s already exists. Pick another slug (e.g. --slug %s-v2) or reuse its "
            "existing worktree; this script never moves an existing branch." % (branch, args.slug))
    if wt.exists() and any(wt.iterdir()):
        die("worktree path %s exists and is not empty" % wt)
    rc, out, err = git(["worktree", "add", "-b", branch, str(wt), base_commit], cwd=root)
    if rc != 0:
        die("git worktree add failed: %s%s" % (out, err))
    cl.add(True, "worktree", "%s  ->  %s" % (branch, wt))

    # 4 -- orientation reading
    territory_abs = (wt / args.territory).resolve()
    prompt_rel = args.prompt
    if prompt_rel is None:
        guess = root / "monitor" / "prompts" / ("%s-%s.md" % (ticket, args.slug))
        prompt_rel = rel(guess, root) if guess.exists() else None

    say("")
    say("=" * 72)
    say("PARTNER_SYNC.md -- last %d section(s)" % args.sections)
    say("=" * 72)
    say(sync_tail(wt / "PARTNER_SYNC.md", args.sections))

    status_files = []
    for name in ("STATUS.md", "DECISIONS.md", "RUN_STATE.md", "INCIDENTS.md", "README.md"):
        p = territory_abs / name
        if p.exists():
            status_files.append(rel(p, wt))
    say("")
    say("=" * 72)
    say("territory %s -- orientation files" % args.territory)
    say("=" * 72)
    say("\n".join("  " + s for s in status_files) if status_files
        else "  (none -- new territory)")
    if prompt_rel:
        say("  prompt: " + prompt_rel)
    cl.add(True, "orientation", "SYNC tail + %d territory file(s)" % len(status_files))

    # 5 -- baseline tests
    test_cmd = detect_test_cmd(territory_abs)
    baseline = {"command": None, "summary": "not applicable (no test suite in this territory)",
                "green": None}
    if args.no_tests:
        baseline["summary"] = "skipped (--no-tests)"
        cl.add(True, "baseline tests", baseline["summary"])
    elif test_cmd is None:
        cl.add(True, "baseline tests", baseline["summary"])
    else:
        say("")
        say("running baseline: %s  (cwd=%s)" % (" ".join(test_cmd[1:]), args.territory))
        rc, out, err = run(test_cmd, cwd=territory_abs)
        summary = summarise_pytest(out, err)
        baseline = {"command": " ".join(test_cmd[1:]), "summary": summary, "green": rc == 0}
        if rc != 0:
            say(out[-4000:])
            say(err[-2000:])
        cl.add(rc == 0, "baseline tests", summary)

    # 6 -- ticket context, parked in the worktree's git dir (never tracked)
    now = utc_now(args.now)
    ctx = {
        "prompt_id": ticket,
        "prompt": prompt_rel,
        "branch": branch,
        "base_commit": base_commit,
        "base_ref": base_ref,
        "territory": args.territory,
        "worktree": str(wt),
        "repo_root": str(root),
        "started_at": iso(now),
        "baseline_tests": baseline,
        "seed": None,
    }
    p = save_ctx(ctx, cwd=wt)
    cl.add(True, "ticket context", rel(p, root))

    code = cl.emit()
    say("")
    say("next: cd %s   -- then work only inside %s/" % (wt, args.territory))
    say("      留痕  ->  skill runs-archive")
    say("      验收  ->  skill verify-gate")
    say("      收工  ->  skill handoff-close")
    if code:
        say("")
        say("BASELINE IS RED. That is a finding about master, not about your ticket:")
        say("record it in PARTNER_SYNC before you change anything, so a later red")
        say("cannot be blamed on you -- and do not 'fix' it silently inside this ticket.")
    return 0  # the ritual itself succeeded; a red baseline is reported, not fatal


if __name__ == "__main__":
    raise SystemExit(main())
