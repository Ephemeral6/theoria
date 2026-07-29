"""Generate `freeze/MANIFEST.json` — the hash table, derived, never typed.

## Why this is a program and not a table in a Markdown file

The two hand-written drafts of this manifest were one day old when they were
checked against the tree.  **Nineteen of the thirty-three hashes one of them
quotes were already wrong**, and two of its verdicts had flipped outright: an
item marked ⛔ 缺 ("the ablation arm does not exist, so C5 and C2 cannot be
separated") had been solved and merged, and an item marked ✅ pointed at a file
that is not on master at all.

That is not carelessness by either author.  It is what a hand-copied hash table
does, and the freeze list is the worst possible place for it: a manifest exists
to say "these exact bytes are what the campaign ran against", so a manifest that
quietly disagrees with the tree is not a weaker guarantee than none — it is a
false one, and it is false in the direction of claiming more.

This repository has now hit the same defect in four places in two days: an
upstream fingerprint nothing ever compared (`monitor/inbox/20260728T082700Z-
W-1521`), a scorer that hardcoded a number another file states, a docstring
naming a test that did not exist, and this.  The pattern is always the same — a
record of what another file says, with nothing that rereads it.  So the rule
here is:

    the manifest is generated from git at a pinned commit, and `verify` fails
    if the tree it is regenerated against no longer produces it.

The prose files next to it (`STATS_RULES.md`, `CLAIMS_TEXT.md`,
`PENDING_FIVE.md`) stay hand-written, because they are judgements — thresholds,
rulings, pre-registered sentences — and a judgement is exactly the thing that
must not be regenerated.  What gets generated is only the part that is a fact
about bytes.

## Usage

    python freeze/build_manifest.py              # write freeze/MANIFEST.json
    python freeze/build_manifest.py --verify     # exit 1 if it has drifted

`--verify` is what belongs in a gate.  It answers "does this manifest still
describe this tree", which is the only question the file is for.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT = os.path.join(HERE, "MANIFEST.json")

#: The thirteen, verbatim from `Theoria.md:368`, each mapped to the paths that
#: *are* that thing today.  A path that does not exist is recorded as absent
#: rather than dropped — an item nobody can point at is the single most
#: important thing a freeze manifest can tell you, and dropping it would turn a
#: blocker into a silence.
#:
#: `status` is this file's own judgement and is written down so it can be
#: argued with:
#:   ready    — everything listed exists and carries a version handle
#:   partial  — exists, but no version string, or split across tracks
#:   blocked  — the thing does not exist, or exists only off master
ITEMS = [
    {
        "n": 1, "name": "内环代码", "status": "partial",
        "paths": ["theoria-arm/inner", "theoria-arm/harness",
                  "theoria-arm/world", "theoria-arm/armtools",
                  "ablation-arm/ablcore", "ablation-arm/run_arm.py"],
        "note": "No `__version__` and no tag in the `theoria-arm` namespace, so "
                "the only handle is the commit. The ablation arm's loop is a "
                "separate implementation that the thirteen do not name and "
                "Theoria.md:376 makes mandatory; hashed here rather than left "
                "to be noticed later.",
    },
    {
        "n": 2, "name": "DSL 语法版本（两本书）", "status": "partial",
        "paths": ["CONTRACTS/dsl_grammar_v0.1.md",
                  "CONTRACTS/dsl_grammar_v0.2.md",
                  "CONTRACTS/dsl_grammar_v0.3.md",
                  "theory-compiler/src/theory_compiler/parser/theory_parser.py",
                  "theory-compiler/src/theory_compiler/parser/playbook_parser.py"],
        "note": "**v0.3 is current and the campaign should compile against it** "
                "-- it is the version the running validator implements "
                "(`theory_parser.py:296,328`, `writes.py:25-26`) and its "
                "additions-only property is tested. v0.2 and v0.3 both carry "
                "`Effective: 2026-07-28`, so that field cannot discriminate "
                "them and the manifest pins the blob instead. Three places "
                "still name v0.2 and have not been told: `grammar_card.py:5`, "
                "`theory_parser.py:35,77`, `CLAUDE.md:64`. Also: v0.2 says it "
                "is 'frozen at the tag that carries this line' and **that tag "
                "does not exist** -- the theory-compiler track has cut none. "
                "v0.3 inherits the same dangling reference verbatim. "
                "`theory_grammar.lark` is a dead file and is excluded on "
                "purpose (its own header says it is not the parser in use).",
    },
    {
        "n": 3, "name": "生成器", "status": "partial",
        "paths": ["theory-compiler/src/theory_compiler/generators",
                  "theory-compiler/pyproject.toml",
                  "cold-start-a0/compile"],
        "note": "Reading (a), the compiler back-ends: the freeze list's "
                "neighbours trace the DSL->four-forms chain. `worldgen/` is a "
                "*world* generator and is hashed under item 9, where its "
                "mutation operators actually belong. `pyproject.toml` says "
                "0.1.0; `gen_pddl.py:5` still cites the v0.1 contract, two "
                "versions behind.",
    },
    {
        "n": 4, "name": "提示词", "status": "partial",
        "paths": ["theoria-arm/inner/theorize.py",
                  "theoria-arm/inner/grammar_card.py",
                  "baseline-arms/harness/bare_cc.py"],
        "note": "There is no `prompts/` directory: the live prompts are string "
                "constants (`theorize.py:122 PREAMBLE`, `:169 "
                "OUTPUT_CONTRACT`, `:204 build_prompt`, `grammar_card.py:16 "
                "CARD`). Hashing the whole module is therefore coarser than "
                "the item asks -- an unrelated edit to `theorize.py` moves the "
                "hash. No `PROMPT_VERSION` exists anywhere. Theoria.md:353 "
                "requires prompts to carry no game-specific content; that has "
                "been *measured* clean once, by hand, and there is no "
                "automated check.",
    },
    {
        "n": 5, "name": "引擎清单与版本", "status": "blocked",
        "paths": ["engine-rig/engines", "engine-rig/STATUS.md",
                  "engine-rig/ENGINE_TABLE.md", "engine-rig/artifacts/candidates.jsonl"],
        "note": "**There is no engine manifest file.** The roster exists only "
                "as prose in STATUS.md. Eight engines are on disk; `CLAUDE.md:51` "
                "still says six (Theoria.md never enumerates them -- the 'six' "
                "is CLAUDE.md's claim, and earlier drafts mis-cited it). Worse "
                "for a manifest: two engines report someone else's name -- "
                "`deadlock_carver/__init__.py:43` sets `ENGINE = \"fd_adapter\"` "
                "and `ic3_pdr/__init__.py:51` sets `ENGINE = \"lp_potential\"` "
                "(D-018, the frozen enum), so 'eight engines, eight tags' "
                "cannot be read off the enum by any consumer.",
    },
    {
        "n": 6, "name": "戳探策略", "status": "blocked",
        "paths": ["theoria-arm/inner/probe.py", "engine-rig/engines/probe_frontier"],
        "note": "No policy document exists. The strategy lives as docstrings in "
                "two packages on two tracks that do not import each other and "
                "may already have diverged; hashing both does not reconcile "
                "them.",
    },
    {
        "n": 7, "name": "规划器配置", "status": "blocked",
        "paths": ["theoria-arm/inner/plan.py", "engine-rig/engines/fd_adapter",
                  "engine-rig/bench/ladder.py",
                  "engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md"],
        "note": "**No configuration file exists** -- every knob is a source "
                "literal. FD is built and connected, but two holes are on the "
                "record and both bite a frozen campaign: no LP solver (CMake "
                "could not find Cplex, which disables `lp_potential` and any "
                "seq-opt config), and FD time/memory caps cannot be enforced "
                "on Windows (`preexec_fn` raises). `theoria-arm`'s planner call "
                "passes no `prefer=`, so which rung of the ladder runs depends "
                "on the environment rather than on anything hashed here.",
    },
    {
        "n": 8, "name": "指标电池 v1", "status": "blocked",
        "paths": ["battery/metrics", "battery/METRICS.md", "battery/PREDICTIONS.md",
                  "battery/audit", "battery/run_battery.py", "battery/PREREG_V9.md",
                  "battery/BATTERY_V1.md"],
        "note": "`battery/BATTERY_V1.md` is the artefact that claims to *be* "
                "this item and **it is not on master** -- it lives on the "
                "unmerged branch `agent/v5-battery-freeze` with a parked merge "
                "conflict. Four version strings disagree (`METRICS.md:1` v1, "
                "`run_battery.py:290` v2, `__init__.py:8` 0.1.0, "
                "`PREDICTIONS.md` v2.1); the ruling on that branch is 'freeze "
                "the SHA, not the label', which this manifest follows by "
                "construction. Two independent gaps remain open: 0 of 38 "
                "metrics passed discrimination, and **U3 achievement rate -- a "
                "primary endpoint -- has no prediction and no battery id** "
                "(`PREDICTIONS.md:585`, corroborated at "
                "`battery/runs/…V18…/ENDPOINTS.md:15`, which calls it "
                "unfalsifiable).",
    },
    {
        "n": 9, "name": "变体算子库", "status": "partial",
        "paths": ["proxy/variants.py", "proxy/variants",
                  "worldgen/mutate.py", "worldgen/out/worlds/MUTATIONS.json",
                  "exam/papers/adaptation.py", "exam/artifacts/variant_specs"],
        "note": "**Three disjoint operator algebras, not one and not two.** "
                "(a) `proxy/variants.py:34 LEGAL_OPERATORS` -- the wrapper-legal "
                "set, no version; (b) `worldgen/mutate.py` + `MUTATIONS.json`, "
                "`schema_version: worldgen/mutations/v0.2` -- **the only one "
                "carrying a version string**, and it defines a "
                "`flags[\"forbidden_action\"]` that is the same concept as (a)'s "
                "`forbid_action` in an unrelated algebra; (c) "
                "`exam/papers/adaptation.py:153 _VARIANT_GRID`, `exam/v0.1`. "
                "All three are hashed separately here. Which one the campaign "
                "freezes is a human ruling this file does not make.",
    },
    {
        "n": 10, "name": "统计裁决规则", "status": "partial",
        "paths": ["freeze/STATS_RULES.md", "battery/audit/stats.py"],
        "note": "The rules are written (this kit) and the machinery exists "
                "(`stats.py` implements the sign test and Wilcoxon "
                "deterministically, no scipy). **They are not wired to each "
                "other**: the three endpoint definitions in STATS_RULES.md do "
                "not correspond to any function in `stats.py`, and no test "
                "proves the two compute the same thing. Until this kit is on "
                "master the rules are one `rm -rf .worktrees/` from "
                "nonexistent, which is how both earlier drafts of them were "
                "nearly lost.",
    },
    {
        "n": 11, "name": "claim 逐字文本与双结局", "status": "partial",
        "paths": ["freeze/CLAIMS_TEXT.md"],
        "note": "This kit. Note that `arc-recon/data/claim_set.json` is a false "
                "friend and holds no claims -- it is the 19-game sealed-pile "
                "roster after F-11's quarantine. Theoria.md:359-364 has the "
                "C1-C5 menu only, not verbatim text and not the two outcomes.",
    },
    {
        "n": 12, "name": "预算表", "status": "blocked",
        "paths": ["proxy/pricing/pricing_v1.json", "proxy/cost.py",
                  "theoria-arm/harness/budget.py", "baseline-arms/BUDGET_REPORT.md",
                  "baseline-arms/out/campaign_gate.json"],
        "note": "The price table is real and versioned (`table: pricing_v1`, "
                "`effective: 2026-07-28`, referenced by hash from every ledger "
                "entry). The three numbers Theoria.md:377 actually asks to "
                "freeze -- $/game hard cap, total games, stop-loss -- are still "
                "written as ⟨…⟩. See PENDING_FIVE.md.",
    },
    {
        "n": 13, "name": "每格重复数 ⟨n⟩", "status": "blocked",
        "paths": ["baseline-arms/STATUS.md", "baseline-arms/DECISIONS.md",
                  "baseline-arms/out/campaign_cells.jsonl"],
        "note": "**No value exists anywhere on master**, and this is blocked "
                "upstream rather than by paperwork: the variance campaign that "
                "would decide it is gated red at 1 game of 4 (`STATUS.md:12`), "
                "all three cells `api_unusable`, $2.5275 spent. `DECISIONS.md:176` "
                "states the trap plainly -- using an n=2 sample to choose n is "
                "circular -- and `:188` says ⟨n⟩ must be remeasured. Two tags "
                "STATUS.md names against its own rows do not exist in `git tag`: "
                "`baseline-arms-m5-variance` and `baseline-arms-m6-path-a`. "
                "Any earlier draft that recorded 'n = 2, ruled' was citing an "
                "unmerged file and is withdrawn.",
    },
]

#: Not one of the thirteen, and the most conspicuous omission in both earlier
#: drafts: a file literally named `campaign_freeze.json`, referenced by
#: thirteen-plus tracked files including two live readers, which does not exist.
EXTRA = [
    {
        "n": "X-1", "name": "campaign_freeze.json（清单外，但缺得最响）",
        "status": "blocked",
        "paths": ["arc-recon/data/campaign_freeze.json"],
        "note": "Absent from disk and from git, and read by "
                "`arc-recon/canary.py:71` and "
                "`baseline-arms/harness/transport_ab.py:53`. "
                "`release/CHECKLIST.md:89` already records that a reader handed "
                "this release would find no frozen campaign roster. Neither "
                "earlier draft names it.",
    },
    {
        "n": "X-2", "name": "外部工具链（不在仓库里，因此只能记指纹）",
        "status": "partial",
        "paths": ["engine-rig/runs/p13-fd-real/TOOLCHAIN_MANIFEST.md",
                  "theory-compiler/lean/lean-toolchain",
                  "theory-compiler/lean/lake-manifest.json"],
        "note": "`.toolchain/` is gitignored: the Fast Downward binary is not "
                "in the repository and cannot be rebuilt from it, so the "
                "manifest pins its recorded sha256 and nothing more. **There is "
                "no Python dependency lock anywhere in the tree** -- no "
                "requirements.txt, no poetry.lock, no uv.lock, no environment "
                "export. A manifest claiming 全部哈希 has no pin on the "
                "interpreter or the libraries it ran under.",
    },
]


def git(*args):
    result = subprocess.run(("git",) + args, cwd=REPO, capture_output=True,
                            text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_tracked(rel):
    """sha256 of what git *stores*, not of what is on this disk.

    This distinction is the difference between a manifest that reproduces on
    another machine and one that only describes this one.  The repository has no
    root `.gitattributes` beyond a single `merge=union` line, and on this
    checkout `CONTRACTS/dsl_grammar_v0.2.md` and `v0.3.md` are **CRLF on disk**
    while `v0.1.md` is LF.  Hashing disk bytes would therefore bake one
    developer's `core.autocrlf` into the freeze manifest, and the failure mode
    is the worst available: every hash would differ on a fresh clone, so the
    verify step would go red for a tree that is in fact identical, and whoever
    hit that would quite reasonably start regenerating the manifest to make it
    green.

    So tracked files are hashed from the blob.  Untracked files are hashed from
    disk -- there is nothing else to hash -- and marked, because an untracked
    input to a freeze manifest is itself a finding.
    """
    blob = subprocess.run(("git", "show", "HEAD:%s" % rel), cwd=REPO,
                          capture_output=True)
    if blob.returncode != 0:
        return None
    return hashlib.sha256(blob.stdout).hexdigest()


def _tracked_files_under(rel):
    listing = git("ls-files", "-z", "--", rel)
    if listing is None:
        return []
    return sorted(p for p in listing.split("\0") if p)


def hash_path(rel):
    """`(kind, sha256, file count, source)` for a file or a directory.

    A directory is hashed as the sorted list of `relative path + sha256` of
    every file under it, so the result changes if a file is added, removed,
    renamed or edited.  `git`'s own tree hash would be cheaper and is not used:
    it is a sha1 over a format that also encodes mode bits, and this manifest
    wants a content hash a reader can reproduce with `sha256sum`.
    """
    full = os.path.join(REPO, rel.replace("/", os.sep))
    tracked = _tracked_files_under(rel)

    if os.path.isfile(full):
        if tracked == [rel]:
            digest = sha256_tracked(rel)
            if digest is not None:
                return "file", digest, 1, "git-blob"
        return "file", sha256_file(full), 1, "worktree"

    if os.path.isdir(full):
        if tracked:
            digest = hashlib.sha256()
            for path in tracked:
                blob = sha256_tracked(path)
                if blob is None:                      # staged but not committed
                    blob = sha256_file(os.path.join(REPO,
                                                    path.replace("/", os.sep)))
                digest.update(path.encode("utf-8"))
                digest.update(blob.encode("ascii"))
            return "dir", digest.hexdigest(), len(tracked), "git-blob"
        digest = hashlib.sha256()
        count = 0
        for base, dirs, files in os.walk(full):
            dirs[:] = sorted(d for d in dirs
                             if d not in ("__pycache__", ".pytest_cache"))
            for name in sorted(files):
                path = os.path.join(base, name)
                key = os.path.relpath(path, full).replace(os.sep, "/")
                digest.update(key.encode("utf-8"))
                digest.update(sha256_file(path).encode("ascii"))
                count += 1
        return "dir", digest.hexdigest(), count, "worktree"

    return "absent", None, 0, None


def build():
    entries = []
    for item in ITEMS + EXTRA:
        paths = []
        for rel in item["paths"]:
            kind, digest, count, source = hash_path(rel)
            paths.append({"path": rel, "kind": kind, "sha256": digest,
                          "files": count, "hashed_from": source,
                          "tracked": bool(git("ls-files", "--error-unmatch", rel))})
        missing = [p["path"] for p in paths if p["kind"] == "absent"]
        entries.append({
            "n": item["n"], "name": item["name"],
            "status": item["status"], "note": item["note"],
            "paths": paths, "absent": missing,
        })

    ready = sum(1 for e in entries if e["status"] == "ready")
    return {
        "format": "theoria/freeze-manifest/1",
        "source": "Theoria.md:368 冻结清单（13 项）+ 两项清单外补录",
        "generated_from": {
            "commit": git("rev-parse", "HEAD"),
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "dirty": bool(git("status", "--porcelain")),
        },
        "verdict": {
            "items": len(ITEMS),
            "ready": ready,
            "partial": sum(1 for e in entries if e["status"] == "partial"),
            "blocked": sum(1 for e in entries if e["status"] == "blocked"),
            "absent_paths": sorted(p for e in entries for p in e["absent"]),
            "freeze_ready": ready == len(ITEMS),
            "statement": (
                "%d of the %d freeze-list items are ready. The campaign may not "
                "start until every one is: `Theoria.md:368` requires the list "
                "committed and hashed *before the first game*, and an item that "
                "is `partial` is one whose bytes can still change without "
                "anybody noticing." % (ready, len(ITEMS))),
        },
        "entries": entries,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true",
                        help="exit 1 if MANIFEST.json no longer describes the tree")
    args = parser.parse_args()

    manifest = build()
    text = json.dumps(manifest, indent=2, sort_keys=True,
                      ensure_ascii=False) + "\n"

    if args.verify:
        if not os.path.exists(OUT):
            print("freeze/MANIFEST.json does not exist; run without --verify")
            return 1
        with open(OUT, "r", encoding="utf-8") as handle:
            on_disk = handle.read()
        # `generated_from` moves with every commit and is not the thing under
        # test; the hashes are.
        strip = lambda blob: {k: v for k, v in json.loads(blob).items()
                              if k != "generated_from"}
        if strip(on_disk) != strip(text):
            print("DRIFT: freeze/MANIFEST.json no longer describes this tree.")
            print("       regenerate it and read the diff before freezing.")
            return 1
        print("freeze/MANIFEST.json still describes this tree (%s)"
              % manifest["verdict"]["statement"])
        return 0

    with open(OUT, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print("wrote freeze/MANIFEST.json")
    print("  %s" % manifest["verdict"]["statement"])
    if manifest["verdict"]["absent_paths"]:
        print("  absent paths (%d):" % len(manifest["verdict"]["absent_paths"]))
        for path in manifest["verdict"]["absent_paths"]:
            print("    %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
