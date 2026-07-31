#!/usr/bin/env python
"""runs-archive -- 留痕 for a Theoria ticket: the run directory, the running
notes, and the MANIFEST that makes a claim traceable back to the prompt.

Subcommands
  new       create <territory>/runs/<UTC>-<slug>/ and remember it
  note      append a timestamped paragraph to the run's NOTES.md (write as you go)
  record    merge a key into the run's results.json (numbers, incrementally)
  manifest  generate MANIFEST.json: prompt_id / prompt / branch / base_commit /
            seed / t / title / per-file sha256 + bytes / results
  check     recompute every hash in an existing MANIFEST and report drift

Every write is UTF-8 with LF and sorted keys, so a rerun with the same inputs
and the same --now produces byte-identical output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fleet import (  # noqa: E402
    Checklist, die, git, iso, load_ctx, read_text, rel, repo_root, save_ctx,
    say, sha256_file, utc_now, write_text,
)


# --------------------------------------------------------------------------


def resolve_run(root, given):
    """A run dir from the flag, else the one `new` recorded in ticket context."""
    if given:
        p = Path(given)
        return (p if p.is_absolute() else root / p).resolve()
    ctx = load_ctx(root)
    if ctx.get("run_dir"):
        return (root / ctx["run_dir"]).resolve()
    die("no run dir: pass --run <path>, or create one with `runs_archive.py new`")


def stamp(now, precise):
    return now.strftime("%Y-%m-%dT%H%M%SZ") if precise else now.strftime("%Y-%m-%d")


def cmd_new(args, root):
    now = utc_now(args.now)
    ctx = load_ctx(root)
    territory = args.territory or ctx.get("territory")
    if not territory:
        die("--territory is required (no ticket context found; run fleet-branch-ritual first)")
    base = root / territory / "runs"
    name = "%s-%s" % (stamp(now, args.precise), args.slug)
    run_dir = base / name
    n = 2
    while run_dir.exists() and any(run_dir.iterdir()):
        run_dir = base / ("%s-%d" % (name, n))
        n += 1
    run_dir.mkdir(parents=True, exist_ok=True)
    write_text(run_dir / "NOTES.md",
               "# %s · running notes\n\nPrompt %s · branch %s · base %s\nOpened %s\n" % (
                   name, ctx.get("prompt_id", "?"), ctx.get("branch", "?"),
                   (ctx.get("base_commit") or "?")[:7], iso(now)))
    ctx["run_dir"] = rel(run_dir, root)
    save_ctx(ctx, cwd=root)
    say(rel(run_dir, root))
    return 0


def cmd_note(args, root):
    run_dir = resolve_run(root, args.run)
    if not run_dir.is_dir():
        die("run dir does not exist: %s" % run_dir)
    target = run_dir / (args.file or "NOTES.md")
    text = args.text if args.text is not None else sys.stdin.read()
    body = "\n## %s\n\n%s\n" % (iso(utc_now(args.now)), text.strip())
    prev = read_text(target) if target.exists() else ""
    write_text(target, prev + body)
    say(rel(target, root))
    return 0


def cmd_record(args, root):
    run_dir = resolve_run(root, args.run)
    target = run_dir / (args.file or "results.json")
    data = json.loads(read_text(target)) if target.exists() else {}
    if args.json is not None:
        try:
            value = json.loads(args.json)
        except json.JSONDecodeError as exc:
            die("--json is not valid JSON: %s" % exc)
    else:
        value = args.value
    node = data
    parts = args.key.split(".")
    for part in parts[:-1]:
        node = node.setdefault(part, {})
        if not isinstance(node, dict):
            die("key path %s collides with a non-object at %s" % (args.key, part))
    node[parts[-1]] = value
    write_text(target, json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    say(rel(target, root))
    return 0


# --------------------------------------------------------------------------


def collect(root, run_dir, includes, include_tracked, skip_run_files):
    """Returns {repo-relative path: abs path}. Run-dir files by default, plus
    whatever the ticket declares as its delivered artefacts."""
    picked = {}

    def add(p):
        p = Path(p)
        if p.is_file() and p.name != "MANIFEST.json":
            picked[rel(p, root)] = p

    if not skip_run_files:
        for p in sorted(run_dir.rglob("*")):
            add(p)
    for pattern in includes or []:
        matches = sorted(root.glob(pattern))
        if not matches:
            die("--include %r matched nothing (patterns are repo-relative globs)" % pattern)
        for p in matches:
            add(p)
    for d in include_tracked or []:
        rc, out, err = git(["ls-files", "-z", "--", d], cwd=root)
        if rc != 0:
            die("git ls-files %s failed: %s" % (d, err.strip()))
        for name in out.split("\0"):
            if name:
                add(root / name)
    return picked


def eol_note(root, paths):
    """The P-11 manifest had to bolt this on afterwards: file-level hashes taken
    on a `core.autocrlf=true` checkout do not reproduce elsewhere unless the
    directory pins eol. Detect it and say so in the artefact, up front."""
    rc, out, _ = git(["config", "--get", "core.autocrlf"], cwd=root)
    autocrlf = out.strip().lower() if rc == 0 else ""
    if autocrlf not in ("true", "input"):
        return None
    unpinned = set()
    for p in paths:
        top = p.split("/")[0]
        if not (root / top / ".gitattributes").exists() and not (root / ".gitattributes").exists():
            unpinned.add(top)
    if not unpinned:
        return None
    return ("These sha256 values are over working-copy bytes on a checkout with "
            "core.autocrlf=%s, and no .gitattributes covers %s. Committed blobs may carry "
            "CRLF while appends carry LF, so file-level hashes will NOT reproduce on a "
            "checkout with different eol settings. Content-level hashes (canonical "
            "re-serialisations, payload hashes) are unaffected." %
            (autocrlf, ", ".join(sorted(unpinned)) or "these paths"))


def cmd_manifest(args, root):
    run_dir = resolve_run(root, args.run)
    if not run_dir.is_dir():
        die("run dir does not exist: %s" % run_dir)
    ctx = load_ctx(root)
    now = utc_now(args.now)

    prompt_id = args.prompt_id or ctx.get("prompt_id")
    branch = args.branch or ctx.get("branch")
    base_commit = args.base_commit or ctx.get("base_commit")
    if not (prompt_id and branch and base_commit):
        die("prompt_id / branch / base_commit are mandatory for 溯源 (METHOD.md #8). "
            "Run fleet-branch-ritual, or pass --prompt-id --branch --base-commit.")

    picked = collect(root, run_dir, args.include, args.include_tracked, args.no_run_files)
    if not picked:
        die("no artefacts to hash. The run dir is empty and nothing was --include'd.")

    artifacts = {}
    for relpath in sorted(picked):
        p = picked[relpath]
        artifacts[relpath] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}

    results = {}
    res_path = run_dir / (args.results or "results.json")
    if res_path.exists():
        results = json.loads(read_text(res_path))

    seed = args.seed if args.seed is not None else ctx.get("seed")
    manifest = {
        "prompt_id": prompt_id,
        "prompt": args.prompt or ctx.get("prompt"),
        "branch": branch,
        "base_commit": base_commit,
        "seed": seed,
        "t": iso(now),
        "title": args.title or "",
        "run_dir": rel(run_dir, root),
        "determinism": args.determinism or (
            "No stochastic step; seed is null." if seed is None else
            "Every stochastic step is seeded with %s; rerunning with that seed reproduces "
            "these artefacts byte for byte." % seed),
        "artifacts": artifacts,
        "results": results,
    }
    if args.tests:
        manifest["tests"] = args.tests
    elif ctx.get("baseline_tests"):
        manifest["baseline_tests"] = ctx["baseline_tests"]
    note = eol_note(root, artifacts.keys())
    if note:
        manifest["artifacts_note"] = note
    for extra in args.set or []:
        if "=" not in extra:
            die("--set expects key=json, got %r" % extra)
        k, v = extra.split("=", 1)
        try:
            manifest[k] = json.loads(v)
        except json.JSONDecodeError:
            manifest[k] = v

    out = run_dir / "MANIFEST.json"
    write_text(out, json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    say(rel(out, root))
    say("  %d artefact(s), %d bytes total" %
        (len(artifacts), sum(a["bytes"] for a in artifacts.values())))
    if seed is None:
        say("  seed is null -- fine only if nothing stochastic ran. If something did, "
            "pass --seed: METHOD.md #9 wants failures replayable too.")
    return 0


def cmd_check(args, root):
    run_dir = resolve_run(root, args.run)
    man_path = run_dir / "MANIFEST.json"
    if not man_path.exists():
        die("no MANIFEST.json in %s" % run_dir)
    man = json.loads(read_text(man_path))
    cl = Checklist("MANIFEST check  %s" % rel(man_path, root))
    for field in ("prompt_id", "branch", "base_commit"):
        cl.add(bool(man.get(field)), "has %s" % field, str(man.get(field)))
    cl.add("seed" in man, "declares seed", repr(man.get("seed")))
    arts = man.get("artifacts") or {}
    cl.add(bool(arts), "has artefacts", "%d file(s)" % len(arts))
    missing, drifted = [], []
    for relpath, meta in sorted(arts.items()):
        p = root / relpath
        if not p.is_file():
            missing.append(relpath)
            continue
        if sha256_file(p) != meta.get("sha256") or p.stat().st_size != meta.get("bytes"):
            drifted.append(relpath)
    cl.add(not missing, "every artefact present",
           "missing: " + ", ".join(missing[:5]) if missing else "%d/%d" % (len(arts), len(arts)))
    cl.add(not drifted, "every hash reproduces",
           "drifted: " + ", ".join(drifted[:5]) if drifted else "%d/%d" % (len(arts), len(arts)))
    return cl.emit()


# --------------------------------------------------------------------------


def main(argv=None):
    ap = argparse.ArgumentParser(description="Theoria fleet: run archive + MANIFEST")
    ap.add_argument("--now", default=None, help="fixed UTC instant (rehearsals/tests)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("new", help="create <territory>/runs/<UTC>-<slug>/")
    p.add_argument("--slug", required=True)
    p.add_argument("--territory", default=None, help="default: from ticket context")
    p.add_argument("--precise", action="store_true", help="stamp to the second, not the day")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("note", help="append a timestamped paragraph to NOTES.md")
    p.add_argument("--run", default=None)
    p.add_argument("--file", default=None, help="default NOTES.md")
    p.add_argument("--text", default=None, help="omit to read stdin")
    p.set_defaults(fn=cmd_note)

    p = sub.add_parser("record", help="merge a key into results.json")
    p.add_argument("--run", default=None)
    p.add_argument("--file", default=None, help="default results.json")
    p.add_argument("--key", required=True, help="dotted path, e.g. tests.engine_rig")
    p.add_argument("--value", default=None, help="string value")
    p.add_argument("--json", default=None, help="JSON value (wins over --value)")
    p.set_defaults(fn=cmd_record)

    p = sub.add_parser("manifest", help="generate MANIFEST.json")
    p.add_argument("--run", default=None)
    p.add_argument("--prompt-id", default=None)
    p.add_argument("--prompt", default=None)
    p.add_argument("--branch", default=None)
    p.add_argument("--base-commit", default=None)
    p.add_argument("--title", default=None)
    p.add_argument("--seed", default=None)
    p.add_argument("--determinism", default=None)
    p.add_argument("--tests", default=None, help='e.g. "150 passed, 1 skipped"')
    p.add_argument("--include", action="append", help="repo-relative glob of delivered files")
    p.add_argument("--include-tracked", action="append",
                   help="hash every git-tracked file under this dir")
    p.add_argument("--results", default=None, help="default results.json in the run dir")
    p.add_argument("--no-run-files", action="store_true",
                   help="hash only --include/--include-tracked, not the run dir")
    p.add_argument("--set", action="append", help="extra key=json field")
    p.set_defaults(fn=cmd_manifest)

    p = sub.add_parser("check", help="recompute hashes and report drift")
    p.add_argument("--run", default=None)
    p.set_defaults(fn=cmd_check)

    args = ap.parse_args(argv)
    root = repo_root(Path.cwd())
    return args.fn(args, root)


if __name__ == "__main__":
    raise SystemExit(main())
