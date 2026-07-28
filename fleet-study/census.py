#!/usr/bin/env python3
"""Recompute fleet-study/data/census.json -- the headline counts, with method.

Run from the repo root:  python fleet-study/census.py

Every number in EVIDENCE.md that is not a row count comes from here, and every
entry carries the command that produced it, so a reader can re-derive it.  This
exists because the study already caught itself quoting a number whose denominator
was wrong: "3184 sealed request bodies" turned out to be the *total line count*
of two files, drifting 3159/3184/3186 across commits, and it was being cited as
a count of requests.  A number without its method is a rumour.

Counts are taken over the whole repository, not one track: the subject of the
study is the fleet, and the fleet writes everywhere.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "census.json"

# Default to the repo's *main* working tree, not whatever worktree this script
# happens to be checked out in.  A census taken inside a feature worktree
# describes that branch's stale copy of board.log and PARTNER_SYNC.md, and would
# silently report the fleet as smaller than it is -- the exact "fails in the
# reassuring direction" shape this dataset is about.
ROOT = Path(__file__).resolve().parent.parent

# git commands run with TZ=UTC so %cd never picks up the host's +08:00.
ENV = {**os.environ, "TZ": "UTC0"}
UTC_FMT = "--date=format-local:%Y-%m-%dT%H:%M:%SZ"


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", env=ENV)
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def main_worktree() -> Path:
    """The primary checkout, even when we are running inside a linked worktree."""
    common = subprocess.run(["git", "rev-parse", "--path-format=absolute",
                             "--git-common-dir"],
                            cwd=Path(__file__).resolve().parent,
                            capture_output=True, text=True, env=ENV)
    if common.returncode == 0 and common.stdout.strip():
        return Path(common.stdout.strip()).parent
    return Path(__file__).resolve().parent.parent


def entry(value, method: str, caveat: str | None = None) -> dict:
    d = {"value": value, "method": method}
    if caveat:
        d["caveat"] = caveat
    return d


def main() -> int:
    global ROOT
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=None,
                    help="repo to census (default: the main working tree)")
    args = ap.parse_args()
    ROOT = (args.root or main_worktree()).resolve()

    utc = git("log", "-1", "--format=%cd", UTC_FMT, "HEAD").strip()
    head = git("rev-parse", "HEAD").strip()
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    first = git("log", "--reverse", "--format=%cd", UTC_FMT, "HEAD").splitlines()[0].strip()

    c: dict = {}

    c["censused_tree"] = entry(
        {"root": str(ROOT), "branch": branch},
        "git rev-parse --git-common-dir, to reach the main checkout even when "
        "this script runs from a linked worktree",
        "Counts below describe this tree. Run from a feature worktree without "
        "--root and you would census that branch's stale copies instead.")
    c["as_of_utc"] = entry(utc, f"TZ=UTC0 git log -1 --format=%cd {UTC_FMT} HEAD")
    c["head"] = entry(head, "git rev-parse HEAD")
    c["first_commit_utc"] = entry(
        first, f"TZ=UTC0 git log --reverse --format=%cd {UTC_FMT} HEAD | head -1",
        "The repo predates the fleet; this is the repo's start, not the fleet's.")

    c["commits_reachable_from_head"] = entry(
        int(git("rev-list", "--count", "HEAD").strip()),
        "git rev-list --count HEAD",
        "Excludes unmerged branch tips; see commits_all_refs for the wider figure.")

    c["commits_all_refs"] = entry(
        int(git("rev-list", "--count", "--all").strip()),
        "git rev-list --count --all",
        "Counts every commit on every ref, including branches never merged. "
        "This is the honest measure of work done, but not of work landed.")

    authors = {}
    for line in git("log", "--all", "--format=%an").splitlines():
        a = line.strip()
        if a:
            authors[a] = authors.get(a, 0) + 1
    c["commits_by_author"] = entry(
        dict(sorted(authors.items(), key=lambda kv: -kv[1])),
        "git log --all --format=%an | tally",
        "Git author is the machine identity, not the agent identity: every agent "
        "commits as the same user. Agent attribution lives in commit *messages* "
        "and in monitor/board.log, not here. This field measures nothing about "
        "the fleet's size -- it is included so nobody mistakes it for that.")

    branches = [b.strip() for b in git("branch", "-a", "--format=%(refname:short)").splitlines() if b.strip()]
    agent_branches = [b for b in branches if "agent/" in b]
    c["agent_branches"] = entry(
        len({b.split("agent/", 1)[1] for b in agent_branches}),
        "git branch -a --format='%(refname:short)' | grep agent/ | strip remote prefix | uniq",
        "One branch per board item worked, local and remote de-duplicated.")

    # --- PARTNER_SYNC paragraphs -------------------------------------------
    sync = ROOT / "PARTNER_SYNC.md"
    if sync.exists():
        text = sync.read_text(encoding="utf-8")
        heads = re.findall(r"^## \[([^\]]+)\]", text, re.M)
        per = {}
        for h in heads:
            per[h] = per.get(h, 0) + 1
        c["partner_sync_paragraphs"] = entry(
            len(heads),
            r"count of lines matching ^## \[<track>\] in PARTNER_SYNC.md",
            "Only paragraphs using the prescribed header form are counted; a "
            "paragraph appended with a malformed header is invisible here.")
        c["partner_sync_by_track"] = entry(
            dict(sorted(per.items(), key=lambda kv: -kv[1])),
            "same regex, grouped by the bracketed track name")

    # --- agent -> monitor reports ------------------------------------------
    inbox = ROOT / "monitor" / "inbox"
    if inbox.exists():
        live = sorted(p.name for p in inbox.glob("*.md"))
        c["inbox_reports_present"] = entry(
            len(live), "count of monitor/inbox/*.md in the worktree",
            "The inbox is swept: reports are deleted once read, so this "
            "undercounts. See inbox_reports_ever.")
    ever = set()
    for line in git("log", "--all", "--name-only", "--format=", "--", "monitor/inbox").splitlines():
        line = line.strip()
        if line.endswith(".md"):
            ever.add(line)
    c["inbox_reports_ever"] = entry(
        len(ever),
        "git log --all --name-only -- monitor/inbox | unique *.md paths",
        "Union over all history and all refs; the true count of reports an agent "
        "ever filed. Untracked reports never committed are invisible to this.")

    # --- incidents ----------------------------------------------------------
    # Two id vocabularies coexist and neither knows about the other: the
    # arc-recon ledger numbers incidents INC-001..INC-011 (with 'a'/'b'
    # amendments), while later fleet-side incidents took an INC-<AREA>-<n>
    # form (INC-BA-001). A regex written for either one silently misses the
    # other -- which is how the first pass of this census reported 10
    # incidents against a ledger holding 16.
    INC = re.compile(r"\bINC-(?:[A-Z]{1,4}-)?\d{1,4}[a-z]?\b")

    in_commits = set(INC.findall(git("log", "--all", "--format=%B")))
    c["incident_ids_named_in_commits"] = entry(
        sorted(in_commits),
        r"regex \bINC-(?:[A-Z]{1,4}-)?\d{1,4}[a-z]?\b over `git log --all --format=%B`",
        "Incidents *named in a commit message*. An incident recorded only in a "
        "file, or never recorded at all, does not appear here.")

    # The one real incident ledger. Everything else that mentions an INC- id is
    # prose citing it.
    ledger = ROOT / "arc-recon" / "data" / "incidents.jsonl"
    in_ledger = set()
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    in_ledger.add(json.loads(line).get("id", ""))
                except json.JSONDecodeError:
                    pass
        in_ledger.discard("")
        c["incidents_in_ledger"] = entry(
            sorted(in_ledger),
            "ids in arc-recon/data/incidents.jsonl",
            "The only structured incident ledger in the repo. It lives in "
            "arc-recon and covers that ground; fleet-level failures were never "
            "filed as incidents at all -- they live in commit messages, audits "
            "and inbox reports, which is why failures.jsonl had to be mined "
            "rather than read off a register.")

    in_tree = set()
    for p in ROOT.rglob("*"):
        if not p.is_file() or ".git" in p.parts or ".worktrees" in p.parts:
            continue
        if p.suffix.lower() not in {".md", ".py", ".json", ".jsonl", ".txt", ".sh"}:
            continue
        try:
            in_tree |= set(INC.findall(p.read_text(encoding="utf-8", errors="ignore")))
        except OSError:
            pass
    # Placeholders, fixtures and one typo. Kept visible rather than quietly
    # dropped: INC-0008 is a mis-typed INC-008 that reached a commit message,
    # which is the same id-drift the two vocabularies above illustrate, and
    # INC-00x/998/999 are template and test values. A census that silently
    # swallowed these would be reporting a tidier fleet than the real one.
    NOISE = {"INC-00x", "INC-998", "INC-999", "INC-0008"}
    everywhere = sorted(in_tree | in_commits)
    c["incident_ids_excluded_as_noise"] = entry(
        sorted(NOISE & set(everywhere)),
        "hand-adjudicated: template placeholders, test fixtures, and one typo",
        "INC-0008 is a typo for INC-008 that reached a commit message and is "
        "now permanent; INC-00x is a template; INC-998/999 are test fixtures.")
    c["incident_ids_anywhere"] = entry(
        [i for i in everywhere if i not in NOISE],
        "union of the commit-message regex and the same regex over tracked "
        "text files in the worktree (.md/.py/.json/.jsonl/.txt/.sh)",
        "The widest defensible count of distinct incidents, spanning both id "
        "vocabularies. Ids cited but never defined are included: citation is "
        "evidence the incident was real to whoever wrote it, but this is an "
        "upper bound, not a register. Note that no single register exists -- "
        "the ledger holds only arc-recon's, so this union is the closest thing "
        "the fleet has to a complete incident list, and it was assembled after "
        "the fact by a regex rather than maintained as the incidents happened.")

    # --- board --------------------------------------------------------------
    board_log = ROOT / "monitor" / "board.log"
    if board_log.exists():
        lines = [l for l in board_log.read_text(encoding="utf-8").splitlines() if l.strip()]
        verbs = {}
        for l in lines:
            m = re.search(r"\b(CLAIM|DONE|RELEASE|SWEEP|POST|ADD)\b", l)
            if m:
                verbs[m.group(1)] = verbs.get(m.group(1), 0) + 1
        c["board_events"] = entry(
            len(lines), "non-blank lines of monitor/board.log")
        c["board_events_by_verb"] = entry(
            dict(sorted(verbs.items(), key=lambda kv: -kv[1])),
            "regex for the event verb on each board.log line",
            "board.log is the fleet's only serialised record of who held what "
            "and when. Lines that do not match a known verb are omitted from "
            "this breakdown but counted in board_events.")

    # --- the sealed pile: the number the study previously got wrong ---------
    #
    # The claim under test is "zero contact with the sealed 21".  The right
    # denominator is *request bodies actually sent*, not lines of a log file.
    sealed_ids, dev_ids = [], []
    piles = ROOT / "arc-recon" / "data" / "piles.json"
    if piles.exists():
        pj = json.loads(piles.read_text(encoding="utf-8"))
        def _ids(v):
            if isinstance(v, list):
                return [x if isinstance(x, str) else x.get("id", "") for x in v]
            return []
        for k, v in pj.items():
            if "seal" in k.lower():
                sealed_ids = _ids(v)
            elif "dev" in k.lower():
                dev_ids = _ids(v)
        c["pile_cut"] = entry(
            {"development": len(dev_ids), "sealed": len(sealed_ids)},
            "arc-recon/data/piles.json, counting the two id lists",
            "Zero API contact is not the same as zero contamination: INC-BA-001 "
            "recorded knowledge contamination of 9 sealed games from a web "
            "search, and F-11 cut the claim set to 19. 'Untouched' and "
            "'uncontaminated' are different claims and the study must not merge them.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(c, indent=2, ensure_ascii=False, sort_keys=False) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}  ({len(c)} entries)")
    for k, v in c.items():
        val = v["value"]
        if isinstance(val, (dict, list)):
            val = f"<{len(val)} entries>"
        print(f"  {k:<34} {val}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
