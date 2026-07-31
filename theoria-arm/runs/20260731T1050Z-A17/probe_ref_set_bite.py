"""A17 measurement: can the ref set actually change a provenance verdict?

Run from the arm:  python runs/20260731T1050Z-A17/probe_ref_set_bite.py

Read-only with respect to this repository. It creates **no** tag, **no** branch
and **no** stash here; the one place it creates refs is a throwaway `git init`
fixture in a temp directory, which is also the only honest way to answer the
question -- `runs/20260730T0855Z-A17-MEASUREMENT/FINDINGS.md` §4 declined to
build a tag here for exactly the right reason (other sessions are measuring
provenance in this repo), and then had to leave the question open.

Four attempted triggers, then the bite, then the reverse control:

  T1  a tag on an off-mainline commit whose arm subtree is unique
      -> does the recorded hash go no_match -> matched?
  T2  a tag on an off-mainline commit whose arm subtree is a duplicate
      -> does the recorded hash go matched -> ambiguous?
  T3  the same as T1 with a plain branch instead of a tag
      -> is this about tags, or about refs?
  T4  a tag on a commit already reachable from HEAD
      -> the reverse control: nothing may move.

  BITE  does a changed verdict actually break anything, or is it cosmetic?
        Measured on the real archive, without creating anything, by handing
        `backfill.build` a table with one extra commit in it and diffing the
        rendered manifest bytes.

  TODAY does the read set change any of the 17 archived verdicts *here*?
"""

import copy
import json
import os
import subprocess
import sys
import tempfile

ARM = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))       # runs/<slug>/ -> arm
sys.path.insert(0, ARM)

import _bootstrap                                       # noqa: E402,F401
from armtools import armversion                         # noqa: E402

OUT = os.path.dirname(os.path.abspath(__file__))
RESULTS = {}


def git(*args, cwd, check=True):
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          encoding="utf-8", errors="replace")
    if check and proc.returncode != 0:
        raise RuntimeError("git %s -> %s\n%s" % (" ".join(args),
                                                 proc.returncode, proc.stderr))
    return proc.stdout.strip()


# --------------------------------------------------------------- the fixture

def build_fixture(root):
    """A real repository, with a real bare origin. Not a stub of one.

    The item is explicit about this and it is not pedantry: a fake git layer
    would be tested against itself. `scan()` runs `git rev-list`, `git
    cat-file --batch-check` and `git log` as subprocesses, and the whole
    question is what those commands see -- which only a real object database
    can answer.
    """
    work = os.path.join(root, "work")
    bare = os.path.join(root, "origin.git")
    os.makedirs(work)
    git("init", "--bare", "-b", "master", bare, cwd=root)
    git("init", "-b", "master", work, cwd=root)
    git("config", "user.email", "a17@probe.invalid", cwd=work)
    git("config", "user.name", "a17-probe", cwd=work)
    git("remote", "add", "origin", bare, cwd=work)

    arm = os.path.join(work, "theoria-arm")
    os.makedirs(arm)

    def commit(message, body):
        with open(os.path.join(arm, "mod.py"), "w", encoding="utf-8",
                  newline="\n") as fh:
            fh.write(body)
        git("add", "-A", cwd=work)
        git("commit", "-m", message, cwd=work)
        return git("rev-parse", "HEAD", cwd=work)

    base = commit("base", "V = 1\n")
    mainline = commit("mainline", "V = 2\n")
    git("push", "-q", "origin", "master", cwd=work)

    # An off-mainline commit carrying an arm state that exists nowhere else.
    git("checkout", "-q", "-b", "side", base, cwd=work)
    unique = commit("side: a unique arm state", "V = 99\n")
    # And one carrying the same arm state as `mainline`.
    duplicate = commit("side: the same arm state as mainline", "V = 2\n")
    git("checkout", "-q", "master", cwd=work)
    git("branch", "-q", "-D", "side", cwd=work)     # commits survive, ref gone
    git("update-ref", "-d", "refs/remotes/origin/side", cwd=work, check=False)

    return {"work": work, "bare": bare, "base": base, "mainline": mainline,
            "unique": unique, "duplicate": duplicate}


def verdicts(work, sha, ref_sets):
    """`locate()` for one hash under each candidate read set."""
    out = {}
    saved = _bootstrap.REPO
    _bootstrap.REPO = work
    try:
        for name, refs in ref_sets.items():
            table = armversion.scan(refs)
            found = armversion.locate(sha, table)
            out[name] = {"verdict": found["verdict"],
                         "commits": found["commits"]}
    finally:
        _bootstrap.REPO = saved
    return out


def arm_hash(work, commit):
    saved = _bootstrap.REPO
    _bootstrap.REPO = work
    try:
        return armversion.arm_version_at(commit)["sha256"]
    finally:
        _bootstrap.REPO = saved


# ------------------------------------------------------------ the four tries

def triggers():
    root = tempfile.mkdtemp(prefix="a17_fixture_")
    fx = build_fixture(root)
    work = fx["work"]
    sets = {"--all": "--all", "HEAD": "HEAD"}

    h_unique = arm_hash(work, fx["unique"])
    h_dup = arm_hash(work, fx["duplicate"])
    assert h_dup == arm_hash(work, fx["mainline"]), \
        "the fixture's duplicate is not actually a duplicate"

    rows = []

    def snap(label, sha, note):
        rows.append(dict(trigger=label, note=note, **verdicts(work, sha, sets)))
        return rows[-1]

    before_u = snap("T1 before: no ref holds the unique arm state", h_unique,
                    "the off-mainline commit is unreachable from every ref")
    before_d = snap("T2 before: no ref holds the duplicate", h_dup,
                    "only `mainline` carries this arm state")

    git("tag", "-a", "-m", "a milestone", "v-unique", fx["unique"], cwd=work)
    after_u = snap("T1 after: an annotated tag on the unique commit", h_unique,
                   "one tag, created by anyone, for any reason")

    git("tag", "-a", "-m", "another milestone", "v-dup", fx["duplicate"],
        cwd=work)
    after_d = snap("T2 after: an annotated tag on the duplicate commit", h_dup,
                   "the tagged commit's arm .py files equal mainline's")

    git("tag", "-d", "v-unique", cwd=work)
    git("tag", "-d", "v-dup", cwd=work)
    git("branch", "side-again", fx["unique"], cwd=work)
    after_b = snap("T3: a plain branch instead of a tag", h_unique,
                   "same commit, no tag involved")
    git("branch", "-D", "side-again", cwd=work)

    h_main = arm_hash(work, fx["mainline"])
    control_before = snap("T4 before (reverse control)", h_main,
                          "mainline's own arm state, reachable from HEAD")
    git("tag", "-a", "-m", "on the mainline", "v-onpath", fx["mainline"],
        cwd=work)
    control_after = snap("T4 after: a tag on a commit HEAD already reaches",
                         h_main, "the tag adds no commit to the reachable set")

    return {
        "rows": rows,
        "T1_constructible": (before_u["--all"]["verdict"] == "no_match"
                             and after_u["--all"]["verdict"] == "matched"
                             and after_u["HEAD"]["verdict"] == "no_match"),
        "T2_constructible": (before_d["--all"]["verdict"] == "matched"
                             and after_d["--all"]["verdict"] == "ambiguous"
                             and after_d["HEAD"]["verdict"] == "matched"),
        "T3_constructible": (after_b["--all"]["verdict"] == "matched"
                             and after_b["HEAD"]["verdict"] == "no_match"),
        "T4_unchanged": (control_before["--all"] == control_after["--all"]
                         and control_before["HEAD"] == control_after["HEAD"]),
        "fixture": {k: v for k, v in fx.items() if k not in ("work", "bare")},
    }


# ------------------------------------------------------------------ the bite

def bite():
    """Does a changed verdict break anything? Measured on the real archive.

    `locate()`'s whole answer -- including the `commits` **list** -- is copied
    verbatim into `MANIFEST.json` by `backfill.provenance`, and
    `verify_provenance` check 8 re-derives every manifest and compares it
    **byte for byte**. So one extra commit in one hash's group is not a
    cosmetic difference: it is check 8 going red on 17 manifests that nobody
    touched.

    Measured without creating a single ref, by handing `backfill.build` a
    scan table with one extra commit spliced into it -- which is exactly the
    table a tag would have produced.
    """
    from armtools import backfill                       # noqa: PLC0415

    runs_root = _bootstrap.path("runs")
    # `--all` explicitly, not the module default: this measures the bite of one
    # extra commit, and mixing in a change of read set would confound it.
    table = armversion.scan("--all")
    findings = []
    for slug in sorted(os.listdir(runs_root)):
        manifest = os.path.join(runs_root, slug, "MANIFEST.json")
        if not os.path.exists(manifest):
            continue
        with open(manifest, "rb") as fh:
            on_disk = fh.read()
        doc = json.loads(on_disk.decode("utf-8"))
        lookup = ((doc.get("provenance") or {}).get("arm_version_lookup")
                  or {})
        sha = lookup.get("arm_sha256")
        if not sha or lookup.get("verdict") not in ("matched", "ambiguous"):
            continue
        if not backfill._is_backfilled(runs_root, slug):
            continue

        doctored = copy.deepcopy(table)
        group = doctored["by_hash"][sha]
        ghost = dict(group[0])
        ghost["commit"] = "0" * 40           # stands for "one more tagged commit"
        ghost["unix"] = group[-1]["unix"] + 1
        group.append(ghost)
        doctored["commits"].append(ghost)

        before = backfill.render(backfill.build(slug, runs_root=runs_root,
                                                table=table))
        after = backfill.render(backfill.build(slug, runs_root=runs_root,
                                               table=doctored))
        findings.append({
            "slug": slug,
            "recorded_verdict": lookup.get("verdict"),
            "matches_disk_today": before == on_disk,
            "bytes_change_when_one_tagged_commit_is_added": before != after,
        })
    return findings


# ----------------------------------------------------------------- today, here

def today():
    """The three candidate read sets, over the 17 archived manifests."""
    runs_root = _bootstrap.path("runs")
    sets = {
        "--all": "--all",
        "HEAD": "HEAD",
        "branches+remotes+HEAD": ["--branches", "--remotes", "HEAD"],
    }
    tables = {name: armversion.scan(refs) for name, refs in sets.items()}
    shape = {name: {k: t[k] for k in
                    ("commits_scanned", "commits_carrying_the_arm",
                     "distinct_arm_subtrees", "distinct_arm_versions")}
             for name, t in tables.items()}

    rows = []
    for slug in sorted(os.listdir(runs_root)):
        manifest = os.path.join(runs_root, slug, "MANIFEST.json")
        if not os.path.exists(manifest):
            continue
        with open(manifest, encoding="utf-8") as fh:
            doc = json.load(fh)
        sha = ((doc.get("provenance") or {}).get("arm_version_lookup")
               or {}).get("arm_sha256")
        if not sha:
            continue
        row = {"slug": slug}
        for name, table in tables.items():
            found = armversion.locate(sha, table)
            row[name] = "%s/%d" % (found["verdict"], len(found["commits"]))
        rows.append(row)

    agree = all(r["--all"] == r["branches+remotes+HEAD"] for r in rows)
    head_agrees = all(r["--all"] == r["HEAD"] for r in rows)
    return {"shape": shape, "rows": rows,
            "chosen_set_agrees_with_all_on_every_manifest": agree,
            "head_only_agrees_with_all_on_every_manifest": head_agrees}


def main():
    RESULTS["triggers"] = triggers()
    RESULTS["bite"] = bite()
    RESULTS["today"] = today()
    path = os.path.join(OUT, "measurement.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(RESULTS, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps({
        "T1_constructible": RESULTS["triggers"]["T1_constructible"],
        "T2_constructible": RESULTS["triggers"]["T2_constructible"],
        "T3_constructible": RESULTS["triggers"]["T3_constructible"],
        "T4_unchanged": RESULTS["triggers"]["T4_unchanged"],
        "manifests_whose_bytes_move": sum(
            1 for f in RESULTS["bite"]
            if f["bytes_change_when_one_tagged_commit_is_added"]),
        "manifests_probed": len(RESULTS["bite"]),
        "chosen_set_agrees_with_all": RESULTS["today"][
            "chosen_set_agrees_with_all_on_every_manifest"],
        "head_only_agrees_with_all": RESULTS["today"][
            "head_only_agrees_with_all_on_every_manifest"],
    }, indent=1))
    print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
