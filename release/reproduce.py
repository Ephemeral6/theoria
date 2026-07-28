"""Re-run the deterministic artefacts and compare them against the manifest.

    python release/reproduce.py              # run the default set
    python release/reproduce.py --all        # include the slow targets
    python release/reproduce.py --list       # what would run, and what would not

Step 4 of `release/PLAN.md`. Produces `release/REPRODUCTION_REPORT.md`.

## What this measures, and what it cannot

The manifest says what the tree contains. This asks a harder question: **can a
stranger regenerate it?** For each territory that publishes a regeneration
command, the command is run and the resulting artefacts are hashed against
`MANIFEST.jsonl`.

Grades, and the point is that most of them are not `reproduced`:

* `reproduced` — ran, and every artefact hashes to what the manifest recorded.
* `drifted` — ran, and something did not. This is the interesting one: it means
  the committed artefact is not what the current code produces.
* `needs-api` — regenerating requires live API calls against the benchmark. Not
  run, and it would cost money and touch the pile if it were.
* `needs-ground-truth` — regenerating requires material this release does not
  and cannot contain.
* `declared-not-run` — a real command, deliberately skipped in this invocation
  (slow, or `--all` not given). **Not the same as reproduced**, and the report
  never lets it read as though it were.

A report that lists only what succeeded measures nothing. The tally at the top
counts all five states, and the reproduced count is stated as a fraction of the
declared targets rather than of the ones that ran.

## The tree is restored afterwards

Generators write in place. Anything that changes is restored with `git checkout`
after hashing, so running this leaves the working tree exactly as it was found.
A target that drifts is *reported*, not committed — deciding what to do about a
committed artefact that no longer matches its generator is not this script's
call.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from dataclasses import dataclass, field

_HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(_HERE)
MANIFEST = os.path.join(_HERE, "MANIFEST.jsonl")
OUT = os.path.join(_HERE, "REPRODUCTION_REPORT.md")


@dataclass(frozen=True)
class Target:
    territory: str
    what: str
    #: ``None`` means the artefacts cannot be regenerated here; ``grade`` says why.
    command: tuple[str, ...] | None
    cwd: str
    #: Manifest paths this target claims to regenerate, as prefixes.
    covers: tuple[str, ...] = ()
    grade: str = ""  # for command=None targets
    slow: bool = False
    note: str = ""


#: Declared per territory, from that territory's own README/CLAUDE entry. A
#: territory absent from this table is a territory nobody has claimed can be
#: regenerated, and the report says so rather than implying coverage.
TARGETS: tuple[Target, ...] = (
    Target(
        territory="figures",
        what="six paper plates, their CSV audit layer and the source hash manifest",
        command=("python", "build_all.py"),
        cwd="figures",
        covers=("figures/csv/", "figures/out/", "figures/SOURCES.sha256"),
        note="the strongest determinism claim in the repository: verify.sh builds twice "
        "into separate trees and requires byte identity, plus a gate that the committed "
        "tree equals a fresh build",
    ),
    Target(
        territory="papers/phase1-workshop",
        what="PAPER.md, assembled from the section files",
        command=("python", "assemble.py"),
        cwd="papers/phase1-workshop",
        covers=("papers/phase1-workshop/PAPER.md",),
    ),
    Target(
        territory="engine-rig",
        what="the synthetic fixtures the six engines are validated against",
        command=("python", "-m", "fixtures.generate_all"),
        cwd="engine-rig",
        covers=("engine-rig/fixtures/data/",),
        note="declared byte-stable for a fixed seed in CLAUDE.md",
    ),
    Target(
        territory="battery",
        what="the capability spectrum and the rest of the battery artefacts",
        command=("python", "-m", "battery.run_battery"),
        cwd=".",
        covers=("battery/artifacts/",),
        slow=True,
    ),
    Target(
        territory="exam",
        what="the exam papers",
        command=("python", "-m", "exam.tools.build_papers"),
        cwd=".",
        covers=("exam/papers/",),
        slow=True,
    ),
    Target(
        territory="baseline-arms",
        what="the pilot and envelope ledgers",
        command=None,
        cwd=".",
        covers=("baseline-arms/ledger.jsonl", "baseline-arms/out/", "baseline-arms/probe_log"),
        grade="needs-api",
        note="regenerating means replaying the games against the live benchmark: real "
        "money, real rate limits, and the pile discipline applies to every call",
    ),
    Target(
        territory="theoria-arm",
        what="the arm's run ledgers and cost curves",
        command=None,
        cwd=".",
        covers=("theoria-arm/runs/",),
        grade="needs-api",
        note="same, plus a model call per desk turn",
    ),
    Target(
        territory="arc-recon",
        what="the API recon ledger",
        command=None,
        cwd=".",
        covers=("arc-recon/data/recon_ledger.jsonl",),
        grade="needs-api",
    ),
    Target(
        territory="baseline-arms/schema_traces",
        what="upstream Schema trajectories",
        command=None,
        cwd=".",
        covers=("baseline-arms/schema_traces/",),
        grade="needs-ground-truth",
        note="third-party payload this release does not and cannot contain; the upstream "
        "declares no licence at all",
    ),
)


def manifest_hashes() -> dict[str, str]:
    with open(MANIFEST, encoding="utf-8") as fh:
        return {r["path"]: r["sha256"] for r in (json.loads(ln) for ln in fh if ln.strip())}


def _sha256(path: str) -> str | None:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def covered(hashes: dict[str, str], target: Target) -> list[str]:
    return sorted(p for p in hashes if any(p.startswith(c) for c in target.covers))


def _git_restore(paths: list[str]) -> None:
    if not paths:
        return
    subprocess.run(
        ["git", "-C", REPO_ROOT, "checkout", "--", *paths],
        capture_output=True,
        text=True,
    )


def run_target(target: Target, hashes: dict[str, str]) -> dict:
    paths = covered(hashes, target)
    result = {
        "territory": target.territory,
        "what": target.what,
        "note": target.note,
        "n_artefacts": len(paths),
    }
    if target.command is None:
        result["grade"] = target.grade
        result["detail"] = "not regenerable in this environment"
        return result

    # encoding pinned, errors replaced. `text=True` alone decodes with the
    # locale codec, which on a zh-CN Windows box is GBK; the first run of this
    # script died in subprocess's reader thread on a UnicodeDecodeError while
    # the target build was reporting a real failure underneath it. That is the
    # same defect P4 documented for build_all.py's own stdout, arriving from
    # the parent side -- and it turned a diagnosable error into a bare
    # non-zero exit.
    proc = subprocess.run(
        list(target.command),
        cwd=os.path.join(REPO_ROOT, *target.cwd.split("/")) if target.cwd != "." else REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        result["grade"] = "command-failed"
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-3:]
        result["detail"] = (
            f"`{' '.join(target.command)}` exited {proc.returncode}: " + " / ".join(tail)
        )
        _git_restore(paths)
        return result

    changed = [p for p in paths if _sha256(os.path.join(REPO_ROOT, *p.split("/"))) != hashes[p]]
    _git_restore(changed)
    if changed:
        result["grade"] = "drifted"
        result["detail"] = (
            f"{len(changed)} of {len(paths)} artefact(s) hash differently after "
            f"regeneration: {', '.join(changed[:5])}"
            + (f" and {len(changed) - 5} more" if len(changed) > 5 else "")
            + ". The committed artefact is not what the current code produces. Restored."
        )
    else:
        result["grade"] = "reproduced"
        result["detail"] = f"all {len(paths)} artefact(s) hash exactly as the manifest records"
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__ or "")
    ap.add_argument("--all", action="store_true", help="include targets marked slow")
    ap.add_argument("--list", action="store_true", help="show the plan and exit")
    ap.add_argument("--dry-run", action="store_true", help="run nothing, write nothing")
    args = ap.parse_args(argv)

    hashes = manifest_hashes()
    if args.list:
        for t in TARGETS:
            state = (
                t.grade
                or ("declared-not-run (slow)" if t.slow and not args.all else "would run")
            )
            print(f"  {state:26s} {t.territory}  ({len(covered(hashes, t))} artefact(s))")
        return 0

    results = []
    for t in TARGETS:
        if t.command is not None and t.slow and not args.all:
            results.append(
                {
                    "territory": t.territory,
                    "what": t.what,
                    "note": t.note,
                    "n_artefacts": len(covered(hashes, t)),
                    "grade": "declared-not-run",
                    "detail": f"`{' '.join(t.command)}` is declared and was skipped in this "
                    "invocation (slow). Run with --all. This is NOT a reproduction.",
                }
            )
            continue
        if args.dry_run:
            continue
        print(f"running {t.territory} ...", flush=True)
        results.append(run_target(t, hashes))

    tally: dict[str, int] = {}
    for r in results:
        tally[r["grade"]] = tally.get(r["grade"], 0) + 1
    declared = len(TARGETS)
    repro = tally.get("reproduced", 0)

    lines = [
        "# release/REPRODUCTION_REPORT.md",
        "",
        "Generated by `release/reproduce.py`. For each territory that publishes a",
        "regeneration command, the command was run and its artefacts hashed against",
        "`release/MANIFEST.jsonl`.",
        "",
        f"**{repro} of {declared} declared targets reproduced.** The denominator is every",
        "declared target, not only the ones that ran — a reproduction rate computed over",
        "the targets that happened to execute would be a number about this invocation",
        "rather than about the release.",
        "",
        "| grade | targets |",
        "|---|---|",
    ]
    for g in sorted(tally):
        lines.append(f"| `{g}` | {tally[g]} |")
    lines += [
        "",
        "`declared-not-run`, `needs-api` and `needs-ground-truth` are **not** partial",
        "credit. They mean a reader cannot regenerate that material from this release:",
        "for the API-bound territories, because doing so costs money and touches the",
        "benchmark under a pile discipline; for the upstream payload, because the release",
        "does not contain it and its licence does not permit that it should.",
        "",
        "---",
        "",
    ]
    for r in results:
        lines.append(f"### {r['territory']} — {r['what']}")
        lines.append("")
        lines.append(f"**`{r['grade']}`** · {r['n_artefacts']} artefact(s) in the manifest")
        lines.append("")
        lines.append(r["detail"])
        if r.get("note"):
            lines.append("")
            lines.append(f"> {r['note']}")
        lines.append("")

    if args.dry_run:
        print("dry run: nothing written")
        return 0
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))
    print(f"\n{repro}/{declared} reproduced; wrote {os.path.relpath(OUT, REPO_ROOT)}")
    for r in results:
        print(f"  {r['grade']:20s} {r['territory']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
