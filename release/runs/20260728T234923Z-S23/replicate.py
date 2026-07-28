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
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))
RELEASE_DIR = os.path.join(REPO_ROOT, "release")
ARC_DIR = os.path.join(REPO_ROOT, "arc-recon")
PILES = os.path.join(ARC_DIR, "data", "piles.json")

BASE_REF = os.environ.get("S23_BASE_REF", "master")

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


def scenario_redlines(out_dir: str) -> list[str]:
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
            path = os.path.join(out_dir, label, "check_redlines.planted.txt")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(f"# {label}: release/check_redlines.py at "
                         f"{BASE_REF if label == 'before' else 'this working tree'}\n")
                fh.write("# input: a throwaway git repo containing\n")
                fh.write("#   corrupt.jsonl  -- names a sealed game, invalid UTF-8\n")
                fh.write("#   vanished.md    -- tracked by git, deleted from the tree\n\n")
                fh.write(text)
                fh.write(f"\nexit code: {code}\n")
            summary.append(f"check_redlines {label}: exit {code}")
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    return summary


# --------------------------------------------------------------- scenario two


def scenario_contamination(out_dir: str) -> list[str]:
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
            path = os.path.join(out_dir, label, "contamination.planted.txt")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(f"# {label}: arc-recon/contamination.py at "
                         f"{BASE_REF if label == 'before' else 'this working tree'}\n")
                fh.write("# input: the real contamination log plus one planted record\n")
                fh.write(f"#   {game} registered with claims='quarantined' (a typo:\n")
                fh.write("#   not one of CLAIM_STATES, so it is in no settled bucket)\n")
                fh.write("# and a DATA_DIR with no recon_ledger.jsonl in it at all.\n\n")
                fh.write(text)
                fh.write(f"\nexit code: {code}\n")
            summary.append(f"contamination {label}: exit {code}")
    finally:
        shutil.rmtree(data, ignore_errors=True)
        # `contamination` was mutated in place; reload it so an importing process
        # does not inherit a module pointed at a deleted temp directory.
        importlib.reload(new_module)
    return summary


def main() -> int:
    out_dir = HERE
    lines = []
    lines += scenario_redlines(out_dir)
    lines += scenario_contamination(out_dir)
    print(f"base ref: {BASE_REF}")
    for line in lines:
        print("  " + line)
    print(f"\nwrote before/ and after/ under {os.path.relpath(out_dir, REPO_ROOT)}")

    verdicts = dict(
        (part.rsplit(":", 1)[0].strip(), part.rsplit(" ", 1)[1]) for part in lines
    )
    # The point of the archive, asserted rather than left for a reader to notice.
    bad = [k for k, v in verdicts.items() if k.endswith("before") and v != "0"]
    if bad:
        print(f"\nUNEXPECTED: {bad} did not report clean before the fix; "
              "the archived diff does not demonstrate what it claims.")
        return 1
    bad = [k for k, v in verdicts.items() if k.endswith("after") and v == "0"]
    if bad:
        print(f"\nUNEXPECTED: {bad} still reports clean after the fix.")
        return 1
    print("\nBefore: both checks reported CLEAN on inputs they could not read.")
    print("After:  both report the failure and exit non-zero.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
