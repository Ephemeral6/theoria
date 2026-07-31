"""Run the *old* code and the *new* code over the same planted negative samples.

    python release/runs/20260728T234923Z-S23/replicate.py

The work order for S23 asks for "before" and "after" outputs of a real check,
because the value of this fix is entirely in the difference between them. A
"before" captured on a healthy tree would show nothing: the defect is latent --
every tracked file in this repository currently decodes, so the gate's wrong
answer is never provoked. Capturing two green runs and calling that evidence is
the same species of claim as the bug.

So this script provokes it. For each scenario it plants an input that the check
cannot read, then runs **the version of the code on `BASE_REF`** and **the
version in the working tree** over that same input, and records both verdicts.

## How the old code is obtained, and why not a stash

`git show BASE_REF:<path>` is written beside its real sibling under a temporary
name and imported. It has to live in the real directory: `check_redlines`
computes `REPO_ROOT` from `__file__` in order to put `arc-recon/` on the path for
the credential reader, and `contamination` resolves `DATA_DIR` the same way. A
copy in a temp directory would silently take a different branch. The temporary
files are removed in a `finally`.

Nothing here touches the network, the API, or `arc-recon/data/`. Every planted
artefact lives under a `tempfile.mkdtemp()` that is deleted on the way out, and
the sealed game ids used are read from the cut rather than written down --
naming a sealed id in order to keep it out is not contact with it.

## This script does not write into `before/` or `after/`

It did, and that is a defect with a history. `verify.sh` runs it on every green
run, so the archive that exists to record what the old code did was rewritten by
the new code every time anybody verified anything -- an in-place mutation of a
write-once record, which has already corrupted this record twice. An archive
that is rewritten by the check that reads it cannot disagree with the check, and
a comparison that cannot fail is not a comparison.

So: this run's output goes to `current/` (untracked, beside the archive), and is
then **compared** against `before/` and `after/`. Nothing under `before/` or
`after/` is opened for writing except under `--adopt`, which is a deliberate
human act -- `verify.sh` never passes it.

## The two sides are not the same kind of claim

`before/` is the output of `BASE_REF`'s code, and `BASE_REF` is a commit hash.
Its content is a function of a frozen input, so it is strictly reproducible and
a mismatch is **red**.

`after/` is the output of *the working tree on the day this run was archived*.
The working tree has moved since -- `1050b001` (A13, 2026-07-29) changed the
sealed audit's line from "N calls" to "N records (N episode)", so today's replay
disagrees with the archive for a reason that has nothing to do with what the
archive claims. Making that red would be the same mistake as pinning `BASE_REF`
to `master`: a gate permanently red about the calendar. The durable claim on
this side is the **verdict** -- the fixed code exits non-zero where the old code
exited 0 -- and that is asserted directly. A content difference is reported as a
note, and the archive stays as first written. `e184942e` had to restore these
two files by hand after a rerun overwrote them; this is the fix that commit said
was queued.

`check_redlines.full_tree.txt` is a note on both sides: it counts tracked files,
and archiving the count adds tracked files, so it disagrees with its archived
copy by construction. It is produced only under `--full-tree`.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))
RELEASE_DIR = os.path.join(REPO_ROOT, "release")
ARC_DIR = os.path.join(REPO_ROOT, "arc-recon")
PILES = os.path.join(ARC_DIR, "data", "piles.json")

#: The commit this work started from, pinned by hash and NOT by branch name.
#:
#: This was `master` for its first few hours, which is a bug with a fuse in it.
#: `verify.sh` runs this script on every green run; the moment the branch lands,
#: `git show master:release/check_redlines.py` returns the **fixed** file, "before"
#: stops reporting clean, the assertion at the bottom of `main()` fires, and the
#: release gate is permanently RED for a reason that has nothing to do with the
#: tree. And because the captures are written before that assertion runs, the
#: first post-merge verify would have overwritten `before/*.txt` with
#: after-content first: the gate destroying the archive it exists to protect,
#: and then failing.
#:
#: A hash cannot move. `bac8282` is the base recorded in MANIFEST.json.
BASE_REF = os.environ.get("S23_BASE_REF", "bac8282")

UNDECODABLE = b"\x80\x81\xfe\xff"


def _git(*args: str, cwd: str = REPO_ROOT) -> str:
    """`encoding="utf-8"` is not optional here.

    `text=True` alone decodes with the process locale, which is GBK on the
    machine this was written on, and `git show` of a file containing an em-dash
    then dies with a `UnicodeDecodeError` -- or, with the wrong error handler,
    returns silently mangled source. Pinning the codec is the same rule this
    whole work order is about, applied to a subprocess instead of a file.
    """
    out = subprocess.run(["git", "-C", cwd, *args], check=True,
                         capture_output=True, encoding="utf-8").stdout
    if out is None:
        raise RuntimeError(f"git {' '.join(args)} produced no decodable output")
    return out


def _sealed_id() -> str:
    with open(PILES, encoding="utf-8") as fh:
        piles = json.load(fh)
    sealed = piles.get("sealed", piles.get("sealed_pile", []))
    ids = sorted(g if isinstance(g, str) else g.get("game_id", "") for g in sealed)
    return [i for i in ids if i][0]


@contextlib.contextmanager
def old_version(rel_path: str, module_name: str):
    """Import `BASE_REF`'s copy of a module, beside its real sibling."""
    directory = os.path.join(REPO_ROOT, os.path.dirname(rel_path))
    tmp_name = "_s23_old_" + os.path.basename(rel_path)
    tmp_path = os.path.join(directory, tmp_name)
    source = _git("show", f"{BASE_REF}:{rel_path}")
    with open(tmp_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(source)
    if directory not in sys.path:
        sys.path.insert(0, directory)
    try:
        spec = importlib.util.spec_from_file_location(module_name, tmp_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(module_name, None)
        with contextlib.suppress(OSError):
            os.remove(tmp_path)


def run_capture(fn, *args, **kwargs) -> tuple[str, object]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            result = fn(*args, **kwargs)
        except BaseException as exc:  # noqa: BLE001 -- the verdict includes crashes
            result = f"RAISED {type(exc).__name__}: {exc}"
    return buf.getvalue(), result


def scrub(text: str, *volatile: str) -> str:
    """Replace this run's temp paths with a stable placeholder.

    `verify.sh` re-runs this script, so its output is written on every green
    run. A `FileNotFoundError` message carries the absolute path of the
    `mkdtemp()` that produced it, which differs every time -- so the archive
    would show a diff after every verification, and an artefact that changes
    whenever you look at it teaches a reader to ignore its diff. That is the
    same lesson as the bug: a signal that always fires carries nothing.
    """
    for path in volatile:
        for form in (path, path.replace("\\", "\\\\"), path.replace("\\", "/")):
            text = text.replace(form, "<TMP>")
    return text


# --------------------------------------------------------------- scenario one


def build_planted_tree() -> str:
    """A throwaway git repo holding one undecodable, sealed-naming tracked file."""
    root = tempfile.mkdtemp(prefix="s23-tree-")
    os.makedirs(os.path.join(root, "arc-recon", "data"))
    shutil.copyfile(PILES, os.path.join(root, "arc-recon", "data", "piles.json"))
    with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("an ordinary file\n")
    # The negative sample: names a sealed game AND cannot be decoded as UTF-8.
    with open(os.path.join(root, "corrupt.jsonl"), "wb") as fh:
        fh.write(json.dumps({"game_id": _sealed_id()}).encode() + b"\n")
        fh.write(UNDECODABLE + b"\n")
    # A second sample: tracked by git, absent from the working tree.
    with open(os.path.join(root, "vanished.md"), "w", encoding="utf-8") as fh:
        fh.write("staged, then deleted\n")
    _git("init", "-q", cwd=root)
    _git("add", "-A", cwd=root)
    os.remove(os.path.join(root, "vanished.md"))
    return root


def scenario_redlines(captures: list) -> list[str]:
    tree = build_planted_tree()
    summary = []
    try:
        for label, loader in (("before", lambda: old_version(
                "release/check_redlines.py", "_s23_old_redlines")),
                ("after", None)):
            if loader is None:
                sys.path.insert(0, RELEASE_DIR)
                import check_redlines as module  # noqa: PLC0415
                real_root = module.REPO_ROOT
                module.REPO_ROOT = tree
                text, code = run_capture(module.main, ["--mode", "verify"])
                module.REPO_ROOT = real_root
            else:
                with loader() as module:
                    real_root = module.REPO_ROOT
                    module.REPO_ROOT = tree
                    text, code = run_capture(module.main, ["--mode", "verify"])
                    module.REPO_ROOT = real_root
            header = (
                f"# {label}: release/check_redlines.py at "
                f"{BASE_REF if label == 'before' else 'this working tree'}\n"
                "# input: a throwaway git repo containing\n"
                "#   corrupt.jsonl  -- names a sealed game, invalid UTF-8\n"
                "#   vanished.md    -- tracked by git, deleted from the tree\n"
                "# <TMP> stands in for this run's temp directory.\n\n"
            )
            captures.append((os.path.join(label, "check_redlines.planted.txt"),
                             header + scrub(text, tree) + f"\nexit code: {code}\n"))
            summary.append(f"check_redlines {label}: exit {code}")
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    return summary


# --------------------------------------------------------------- scenario two


def scenario_contamination(captures: list) -> list[str]:
    """Two plants at once: a NEEDS ADJUDICATION record, and a deleted ledger."""
    sys.path.insert(0, ARC_DIR)
    import contamination as new_module  # noqa: PLC0415

    data = tempfile.mkdtemp(prefix="s23-data-")
    summary = []
    try:
        # Replay the real register, then append an unrecognised claim state.
        game = new_module.claim_set()["claim_set"][0]
        log_path = os.path.join(data, "contamination_log.jsonl")
        with open(log_path, "w", encoding="utf-8", newline="\n") as fh:
            for entry in new_module.entries():
                fh.write(json.dumps(entry, sort_keys=True) + "\n")
            fh.write(json.dumps({
                "game_id": game, "level": "filename_only",
                "claims": "quarantined",  # a typo: not a member of CLAIM_STATES
                "note": "S23 negative control -- planted, not a real registration",
                "t": "2026-07-29T00:00:00Z"}, sort_keys=True) + "\n")
        # `data` deliberately holds NO recon_ledger.jsonl: the sealed-contact
        # audit therefore runs over a ledger that is not there.

        def _point_at(module):
            module.DATA_DIR = data
            module.LOG_PATH = log_path
            module.PILES_PATH = PILES
            module.CLAIM_SET_PATH = os.path.join(data, "claim_set.json")
            module.OTHER_LEDGERS = list(module.OTHER_LEDGERS)

        for label in ("before", "after"):
            if label == "after":
                _point_at(new_module)
                text, code = run_capture(new_module.main, [])
            else:
                with old_version("arc-recon/contamination.py",
                                 "_s23_old_contamination") as module:
                    _point_at(module)
                    text, code = run_capture(module.main, [])
            header = (
                f"# {label}: arc-recon/contamination.py at "
                f"{BASE_REF if label == 'before' else 'this working tree'}\n"
                "# input: the real contamination log plus one planted record\n"
                f"#   {game} registered with claims='quarantined' (a typo:\n"
                "#   not one of CLAIM_STATES, so it is in no settled bucket)\n"
                "# and a DATA_DIR with no recon_ledger.jsonl in it at all.\n"
                "# <TMP> stands in for this run's temp directory.\n\n"
            )
            captures.append((os.path.join(label, "contamination.planted.txt"),
                             header + scrub(text, data) + f"\nexit code: {code}\n"))
            summary.append(f"contamination {label}: exit {code}")
    finally:
        shutil.rmtree(data, ignore_errors=True)
        # `contamination` was mutated in place; reload it so an importing process
        # does not inherit a module pointed at a deleted temp directory.
        importlib.reload(new_module)
    return summary


def scenario_full_tree(captures: list) -> list[str]:
    """Both versions over the REAL tree, unplanted, in the same run.

    The planted scenarios show the defect. This one shows the other half of the
    claim, which is just as load-bearing and much easier to skip: that on a tree
    where nothing is wrong, the stricter checks say exactly what the old ones
    said. A gate that reddens on a healthy repository is one somebody switches
    off, and then the planted evidence above protects nothing.

    An earlier run directory holds a pre-fix full-tree capture with no `after/`
    beside it. It is not comparable to anything now -- it was taken at a
    different base over 2817 tracked files, and the tree holds more than that
    today -- so this pairs the two over one tree at one moment instead.

    Only the tail is archived. The full output names every file that mentions a
    sealed id, which is hundreds of lines that say the same thing.
    """
    summary = []
    sys.path.insert(0, RELEASE_DIR)
    import check_redlines as new_module  # noqa: PLC0415

    for label in ("before", "after"):
        if label == "after":
            text, code = run_capture(new_module.main, ["--mode", "verify"])
        else:
            with old_version("release/check_redlines.py",
                             "_s23_old_redlines_full") as module:
                text, code = run_capture(module.main, ["--mode", "verify"])
        tail = "\n".join(text.strip().splitlines()[-6:])
        captures.append((
            os.path.join(label, "check_redlines.full_tree.txt"),
            f"# {label}: release/check_redlines.py at "
            f"{BASE_REF if label == 'before' else 'this working tree'}\n"
            "# input: the real tree, nothing planted. Tail only -- the full output\n"
            "#   names every file that mentions a sealed id, which is hundreds of\n"
            "#   lines all saying the same thing.\n"
            "# A DATED MEASUREMENT, not a reproducible check: the tracked-file count\n"
            "#   below includes this very file, so rerunning gives a larger number.\n"
            "#   Regenerate deliberately with `replicate.py --full-tree`.\n\n"
            + tail + f"\n\nexit code: {code}\n"))
        summary.append(f"full tree {label}: exit {code}")
    return summary


#: Where this run's output goes. Untracked (see the .gitignore beside it), so
#: running the gate never dirties the tree, and readable, so a failed comparison
#: leaves both sides on disk to diff.
CURRENT = "current"

#: Compared, but a difference is a note rather than a failure -- the capture
#: reports a tracked-file count and archiving it changes that count.
DATED_MEASUREMENTS = ("check_redlines.full_tree.txt",)

#: The side whose content is a function of a frozen commit, and therefore the
#: only side a difference can be red about. See the module docstring.
STRICT_SIDE = "before"


#: The one line in these captures that counts a live, append-only file.
#:
#: `contamination.main()` audits `baseline-arms/ledger.jsonl` and
#: `probe_log.jsonl`, which other sessions append to. Comparing those counts
#: literally would make the archive disagree with itself for a reason that is
#: not about the code -- the archive drifted from 1955 to 1956 while this fix
#: was being written -- and a comparison that fails for reasons nobody can act
#: on gets switched off. The counts stay in the file, where a reader sees them;
#: they are masked only when deciding whether two captures agree.
_VOLATILE_COUNT = re.compile(r"^(\s*ledger audit:.*)$", re.M)
_DIGITS = re.compile(r"\d[\d,]*")


def _norm(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _comparable(text: str) -> str:
    return _VOLATILE_COUNT.sub(
        lambda m: _DIGITS.sub("<N>", m.group(1)), _norm(text))


def write_current(captures: list[tuple[str, str]]) -> None:
    for rel, body in captures:
        path = os.path.join(HERE, CURRENT, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)


def compare_with_archive(captures: list[tuple[str, str]]) -> tuple[list, list]:
    """-> (differences, notes). Reads the archive; never writes it."""
    differences, notes = [], []
    for rel, body in captures:
        side = rel.replace("\\", "/").split("/")[0]
        soft = (os.path.basename(rel) in DATED_MEASUREMENTS
                or side != STRICT_SIDE)
        archived = os.path.join(HERE, rel)
        if not os.path.exists(archived):
            (notes if soft else differences).append(
                (rel.replace("\\", "/"), "no archived copy to compare against"))
            continue
        with open(archived, encoding="utf-8") as fh:
            want = _comparable(fh.read())
        if _comparable(body) != want:
            (notes if soft else differences).append(
                (rel.replace("\\", "/"), "this run's output differs from the archived copy"))
    return differences, notes


def adopt(captures: list[tuple[str, str]]) -> None:
    """The ONLY path that writes into `before/` or `after/`.

    Reached solely by an explicit `--adopt` on the command line. It exists
    because an archive nobody can legitimately update is an archive somebody
    edits by hand, which is worse. `verify.sh` does not pass it, and the verdict
    assertions below run first, so an archive can only be replaced by a run that
    still demonstrates what the archive claims.
    """
    for rel, body in captures:
        path = os.path.join(HERE, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)


def main() -> int:
    captures: list[tuple[str, str]] = []
    lines = []
    lines += scenario_redlines(captures)
    lines += scenario_contamination(captures)
    # Off by default, and that is not laziness. This capture reports the number
    # of tracked files, and archiving it under `runs/` ADDS tracked files -- so
    # rerunning it always disagrees with the copy on disk, by exactly the number
    # of files it just wrote. `verify.sh` runs this script on every green run, so
    # leaving it on would dirty the tree forever and teach a reader to ignore the
    # diff. The planted scenarios above are the reproducible check; this pair is
    # a dated measurement, regenerated deliberately with --full-tree.
    full = scenario_full_tree(captures) if "--full-tree" in sys.argv else []
    print(f"base ref: {BASE_REF}")
    for line in lines + full:
        print("  " + line)

    # The full-tree pair is evidence, not a trigger: both sides must be 0,
    # because the tree is healthy and the whole point is that the fix does not
    # change that. If either side is non-zero, something in the tree wants
    # looking at and this script should not be the thing that says so.
    if any(not v.endswith("0") for v in full):
        print("\nNOTE: the full-tree run is not clean on one side. That is a fact about "
              "the tree, not about this archive; read the capture.")

    verdicts = dict(
        (part.rsplit(":", 1)[0].strip(), part.rsplit(" ", 1)[1]) for part in lines
    )
    # This run's output always lands in `current/`, whatever the verdict, so a
    # failure leaves both sides on disk to diff. `current/` is untracked; the
    # archive is not written here at all.
    write_current(captures)
    here_rel = os.path.relpath(HERE, REPO_ROOT).replace(os.sep, "/")
    print(f"\nwrote this run's output to {here_rel}/{CURRENT}/")

    # The point of the archive, asserted rather than left for a reader to notice.
    bad = [k for k, v in verdicts.items() if k.endswith("before") and v != "0"]
    if not bad:
        bad = [k for k, v in verdicts.items() if k.endswith("after") and v == "0"]
    if bad:
        print(f"\nUNEXPECTED: {bad} -- the archived diff no longer demonstrates what it "
              f"claims. The archive under {here_rel} was NOT touched; compare it "
              f"against {CURRENT}/.")
        print(f"If this is the post-merge run, S23_BASE_REF is {BASE_REF} and the fix is "
              "presumably in it; that ref is meant to be the pre-fix commit.")
        return 1

    # The comparison the old code could not make, because it was the thing
    # overwriting the answer.
    differences, notes = compare_with_archive(captures)
    for rel, why in notes:
        print(f"  note: {rel}: {why}. Not red: this side is a dated measurement "
              f"or the working tree's output on the day it was archived, and the "
              f"claim it carries is the verdict, which held. The archive was not "
              f"touched; {CURRENT}/ holds today's.")
    if "--adopt" in sys.argv:
        # Checked before the mismatch gate, not after: adopting only when the
        # archive already matches would be a no-op. The verdict assertions above
        # have already run, so this can only replace an archive with a run that
        # still demonstrates what the archive claims.
        adopt(captures)
        print(f"\n--adopt: replaced before/ and after/ under {here_rel} "
              f"({len(differences)} file(s) differed). This is a deliberate act; "
              "verify.sh never passes it.")
        return 0
    if differences:
        print("\nARCHIVE MISMATCH -- the replay no longer reproduces what is on disk:")
        for rel, why in differences:
            print(f"  {rel}: {why}")
        print(f"\nThe archive under {here_rel} was NOT rewritten. Diff it against "
              f"{CURRENT}/ and decide: either the replay regressed, or the archive is "
              "genuinely out of date and a human adopts the new one with "
              "`replicate.py --adopt`. A check does not get to settle that by "
              "overwriting the record it is checking -- doing exactly that is how "
              "this archive was corrupted twice.")
        return 1

    strict = sum(1 for rel, _ in captures
                 if rel.replace("\\", "/").split("/")[0] == STRICT_SIDE)
    print(f"\narchive reproduces: {strict} strict capture(s) match {STRICT_SIDE}/, "
          f"{len(notes)} note(s), 0 file(s) rewritten")
    print("Before: both checks reported CLEAN on inputs they could not read.")
    print("After:  both report the failure and exit non-zero.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
