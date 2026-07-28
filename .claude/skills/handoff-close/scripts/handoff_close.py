#!/usr/bin/env python
"""handoff-close -- 收工 for a Theoria ticket.

  run-state   write RUN_STATE.md from the ticket context (delivered / gaps / budget)
  sync        append one correctly-formatted section to PARTNER_SYNC.md,
              refusing anything that is not a pure append at the tail
  commit      stage the declared territory only (never `git add -A` at the root)
  push        push the agent branch; refuses master
  close       the whole checklist, in order, and stop at the first thing missing

The PARTNER_SYNC guard is the load-bearing part: the board is append-only and
14 sessions share it. This will not let you edit, reflow or reorder one byte
another track wrote.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fleet import (  # noqa: E402
    Checklist, die, git, iso, load_ctx, read_text, rel, repo_root, save_ctx,
    say, utc_now, write_text,
)

SYNC = "PARTNER_SYNC.md"

RUN_STATE_TMPL = """# {prompt_id} · RUN_STATE

Prompt: `{prompt}` · branch `{branch}` · base `{base_short}` · {date}.
Territory: `{territory}`. Run archive: `{run_dir}`.

## Delivered

{delivered}

## Gaps — what the工单 asked for and did not get

{gaps}

## Verification

| | |
|---|---|
| verify.sh | {verify} |
| tests | {tests} |
| MANIFEST | {manifest} |
| sealed-pile API calls | {sealed} |
| boundary | touched `{territory}` only; `PARTNER_SYNC.md` appended, never edited |

## Open, and deliberately not closed here

{open_items}
"""


def ctx_or_die(root):
    ctx = load_ctx(root)
    if not ctx.get("branch"):
        die("no ticket context in this worktree. Either run fleet-branch-ritual first, or "
            "pass every value explicitly (--branch --base-commit --territory --prompt-id).")
    return ctx


# --------------------------------------------------------------------------


def cmd_run_state(args, root):
    ctx = load_ctx(root)
    now = utc_now(args.now)
    run_dir = args.run or ctx.get("run_dir") or "(none)"
    territory = args.territory or ctx.get("territory") or "(unset)"
    body = RUN_STATE_TMPL.format(
        prompt_id=args.prompt_id or ctx.get("prompt_id") or "(unset)",
        prompt=args.prompt or ctx.get("prompt") or "(unset)",
        branch=args.branch or ctx.get("branch") or "(unset)",
        base_short=(args.base_commit or ctx.get("base_commit") or "-------")[:7],
        date=now.strftime("%Y-%m-%d"),
        territory=territory,
        run_dir=run_dir,
        delivered=args.delivered or
        "TODO — one numbered paragraph per item the工单 asked for. State what was\n"
        "built, where it lives, and the number that proves it. 'Done' without an\n"
        "artefact path is not a delivery.",
        gaps=args.gaps or
        "TODO — 做不到就如实报 gap (METHOD.md #3). If everything landed, write\n"
        "'none' and mean it. Never lower the acceptance line to reach 'none'.",
        verify=args.verify or "TODO — paste the checklist tail: `N/N green`",
        tests=args.tests or ctx.get("baseline_tests", {}).get("summary", "TODO"),
        manifest=("`%s/MANIFEST.json`" % run_dir) if run_dir != "(none)" else "TODO",
        sealed=args.sealed or "0",
        open_items=args.open_items or
        "TODO — what a later session must know: caveats, half-truths in the numbers,\n"
        "decisions you deferred, and anything you found that belongs to another track.",
    )
    out = Path(args.out) if args.out else (
        root / run_dir / "RUN_STATE.md" if run_dir != "(none)" else root / territory / "RUN_STATE.md")
    if not out.is_absolute():
        out = root / out
    if out.exists() and not args.force:
        die("%s already exists (use --force to overwrite)" % rel(out, root))
    write_text(out, body)
    ctx["run_state"] = rel(out, root)
    save_ctx(ctx, cwd=root)
    say(rel(out, root))
    say("  Fill every TODO. A RUN_STATE with TODOs left in it is a false handoff.")
    return 0


# --------------------------------------------------------------------------


def sync_versions(root, base):
    """(HEAD bytes, base bytes) of PARTNER_SYNC.md -- the two things your file
    must still start with."""
    out = {}
    for label, ref in (("head", "HEAD"), ("base", base)):
        if not ref:
            continue
        proc = git(["show", "%s:%s" % (ref, SYNC)], cwd=root)
        if proc[0] != 0:
            out[label] = None
        else:
            # re-read as bytes: git's text is UTF-8 in this repo
            out[label] = proc[1].encode("utf-8", "surrogateescape")
    return out


def append_only_ok(root, base):
    """Byte-prefix test against HEAD and against the branch base. Anything else
    -- a reflow, a fixed typo in someone else's paragraph, a reordered section
    -- is an edit, and this board does not take edits."""
    path = root / SYNC
    if not path.exists():
        return False, "%s is missing" % SYNC, {}
    current = path.read_bytes().replace(b"\r\n", b"\n")
    problems = []
    for label, blob in sync_versions(root, base).items():
        if blob is None:
            continue
        blob = blob.replace(b"\r\n", b"\n")
        if not current.startswith(blob):
            # find the first divergent byte for a useful message
            i = 0
            for i in range(min(len(blob), len(current))):
                if blob[i] != current[i]:
                    break
            if len(current) < len(blob):
                problems.append("%s: the file is SHORTER than %s -- content was deleted" % (label, label))
            else:
                line = current[:i].count(b"\n") + 1
                problems.append("%s: diverges at line %d -- existing text was modified" % (label, line))
    return (not problems), "; ".join(problems) or "pure append", {}


def cmd_sync(args, root):
    ctx = load_ctx(root)
    base = args.base_commit or ctx.get("base_commit")
    track = args.track or ctx.get("territory", "").strip("/").split("/")[-1]
    if not track:
        die("--track is required (the name that appears in `## [<track>] ...`)")
    now = utc_now(args.now)

    ok, why, _ = append_only_ok(root, base)
    if not ok:
        die("PARTNER_SYNC.md is already not a pure append (%s).\n"
            "Restore it before adding your section:  git checkout %s -- %s\n"
            "and re-append. Never repair another track's paragraph -- the board is a "
            "board, not a conversation." % (why, base or "HEAD", SYNC))

    if args.body_file:
        section = read_text(root / args.body_file if not Path(args.body_file).is_absolute()
                            else args.body_file).strip("\n")
    else:
        for field in ("status", "tests", "blocked", "next"):
            if getattr(args, field) is None:
                die("--%s is required (or use --body-file). The board's four lines are "
                    "状态/测试/阻塞/下一步 and none of them is optional." % field)
        section = ("## [%s] %s %s\n状态：%s\n测试：%s\n阻塞：%s\n下一步：%s"
                   % (track, iso(now), args.tag, args.status.strip(), args.tests.strip(),
                      args.blocked.strip(), args.next.strip()))

    # format gate
    cl = Checklist("PARTNER_SYNC section")
    head = section.splitlines()[0] if section.splitlines() else ""
    cl.add(bool(re.match(r"^## \[[^\]]+\] \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z \S", head)),
           "header is `## [track] <ISO8601> <tag>`", head[:90])
    for label in ("状态：", "测试：", "阻塞：", "下一步："):
        cl.add(any(l.startswith(label) for l in section.splitlines()), "has %s line" % label.strip("："))
    cl.add(("[%s]" % track) in head, "track matches --track", track)
    if cl.failed:
        say(cl.render())
        die("section rejected before it touched the file")

    path = root / SYNC
    current = read_text(path)
    tail = current if current.endswith("\n") else current + "\n"
    if not tail.endswith("\n\n"):
        tail += "\n"
    write_text(path, tail + section.rstrip("\n") + "\n")

    ok, why, _ = append_only_ok(root, base)
    if not ok:
        die("post-write check failed (%s) -- this should be impossible; do not commit" % why)
    say(cl.render())
    say("")
    say("appended %d line(s) to %s; verified as a pure append against HEAD and base."
        % (len(section.splitlines()), SYNC))
    return 0


# --------------------------------------------------------------------------


def cmd_commit(args, root):
    ctx = ctx_or_die(root)
    territory = args.territory or ctx["territory"]
    paths = [territory] + list(args.also or []) + [SYNC]
    rc, out, err = git(["add", "--"] + paths, cwd=root)
    if rc != 0:
        die("git add failed: %s%s" % (out, err))
    rc, out, _ = git(["diff", "--cached", "--name-only"], cwd=root)
    staged = [p for p in out.splitlines() if p.strip()]
    strays = [p for p in staged
              if p != SYNC and not any(p == a or p.startswith(a.rstrip("/") + "/")
                                       for a in [territory] + list(args.also or []))]
    if strays:
        die("staged paths outside the territory: %s\nUnstage them. `git add -A` at the repo "
            "root is never correct here -- other tracks have work in flight." % ", ".join(strays[:8]))
    if not staged:
        say("nothing staged; working tree already matches HEAD")
        return 0
    say("staged %d path(s) under %s" % (len(staged), ", ".join(paths)))
    if args.dry_run:
        for p in staged[:40]:
            say("  " + p)
        return 0
    message = args.message or "%s: %s" % (ctx.get("prompt_id", "ticket"), args.tag or "收工")
    rc, out, err = git(["commit", "-m", message], cwd=root)
    say(out.strip() or err.strip())
    return 0 if rc == 0 else 1


def cmd_push(args, root):
    ctx = ctx_or_die(root)
    rc, out, _ = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    branch = out.strip()
    if branch in ("master", "main", "HEAD"):
        die("refusing to push %s. Ticket work goes on agent/<ticket>-<slug>; only M-0 "
            "touches master." % branch)
    if ctx.get("branch") and branch != ctx["branch"]:
        die("on branch %s but the ticket context says %s -- check out the right branch first"
            % (branch, ctx["branch"]))
    rc, out, _ = git(["status", "--porcelain"], cwd=root)
    dirty = [l for l in out.splitlines() if l.strip() and not l.startswith("??")]
    if dirty and not args.allow_dirty:
        die("uncommitted changes in tracked files:\n  %s\nCommit them first "
            "(`handoff_close.py commit`) or pass --allow-dirty." % "\n  ".join(dirty[:10]))
    if args.dry_run:
        say("would push: git push -u %s %s" % (args.remote, branch))
        return 0
    rc, out, err = git(["push", "-u", args.remote, branch], cwd=root)
    say((out + err).strip())
    if rc != 0:
        return 1
    say("")
    say("pushed %s. master untouched; M-0 merges." % branch)
    return 0


# --------------------------------------------------------------------------


def cmd_close(args, root):
    ctx = ctx_or_die(root)
    base = ctx.get("base_commit")
    cl = Checklist("handoff-close  %s" % ctx.get("prompt_id", "?"))

    run_dir = ctx.get("run_dir")
    cl.add(bool(run_dir), "run archive exists", run_dir or "none -- skill runs-archive")
    if run_dir:
        cl.add((root / run_dir / "MANIFEST.json").exists(), "MANIFEST.json written",
               "%s/MANIFEST.json" % run_dir)
    rs = ctx.get("run_state")
    cl.add(bool(rs) and (root / rs).exists(), "RUN_STATE.md written", rs or "none")
    if rs and (root / rs).exists():
        text = read_text(root / rs)
        cl.add("TODO" not in text, "RUN_STATE has no TODO left",
               "%d TODO marker(s)" % text.count("TODO"))
    vs = ctx.get("verify_sh")
    cl.add(bool(vs) and (root / vs).exists(), "verify.sh generated", vs or "none -- skill verify-gate")

    ok, why, _ = append_only_ok(root, base)
    cl.add(ok, "PARTNER_SYNC is a pure append", why)
    sync_text = read_text(root / SYNC) if (root / SYNC).exists() else ""
    mine = ctx.get("territory", "").strip("/").split("/")[-1]
    cl.add(("[%s]" % (args.track or mine)) in sync_text.split("\n## ")[-1]
           if sync_text else False,
           "your section is the last one on the board", args.track or mine)

    rc, out, _ = git(["status", "--porcelain"], cwd=root)
    dirty = [l for l in out.splitlines() if l.strip() and not l.startswith("??")]
    cl.add(not dirty, "nothing uncommitted", "%d tracked file(s) dirty" % len(dirty) if dirty else "clean")

    rc, out, _ = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    cl.add(out.strip() not in ("master", "main"), "not on master", out.strip())

    code = cl.emit()
    if code:
        say("")
        say("Close the red lines above before pushing. Each one is something a reader of")
        say("the board would otherwise have to take on trust.")
        return code
    if args.push:
        return cmd_push(argparse.Namespace(remote=args.remote, dry_run=args.dry_run,
                                           allow_dirty=False), root)
    say("")
    say("ready. push with:  python .claude/skills/handoff-close/scripts/handoff_close.py push")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Theoria fleet: 收工")
    ap.add_argument("--now", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("run-state", help="write RUN_STATE.md")
    for f in ("prompt-id", "prompt", "branch", "base-commit", "territory", "run", "out",
              "delivered", "gaps", "verify", "tests", "sealed", "open-items"):
        p.add_argument("--" + f, default=None)
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_run_state)

    p = sub.add_parser("sync", help="append a section to PARTNER_SYNC.md")
    p.add_argument("--track", default=None)
    p.add_argument("--tag", required=True, help="milestone tag, e.g. p24-fleet-skills")
    p.add_argument("--status", default=None)
    p.add_argument("--tests", default=None)
    p.add_argument("--blocked", default=None)
    p.add_argument("--next", dest="next", default=None)
    p.add_argument("--body-file", default=None, help="a pre-written section (still format-checked)")
    p.add_argument("--base-commit", default=None)
    p.set_defaults(fn=cmd_sync)

    p = sub.add_parser("commit", help="stage the territory only, then commit")
    p.add_argument("--territory", default=None)
    p.add_argument("--also", action="append", help="extra path the工单 authorised")
    p.add_argument("-m", "--message", default=None)
    p.add_argument("--tag", default=None)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_commit)

    p = sub.add_parser("push", help="push the agent branch")
    p.add_argument("--remote", default="origin")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--allow-dirty", action="store_true")
    p.set_defaults(fn=cmd_push)

    p = sub.add_parser("close", help="the whole 收工 checklist")
    p.add_argument("--track", default=None)
    p.add_argument("--push", action="store_true")
    p.add_argument("--remote", default="origin")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_close)

    args = ap.parse_args(argv)
    return args.fn(args, repo_root(Path.cwd()))


if __name__ == "__main__":
    raise SystemExit(main())
