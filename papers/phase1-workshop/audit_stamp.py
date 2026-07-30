"""Check G — an audit report must say what it audited, and be right about it.

This module exists because of a shape this repository keeps meeting, and which
`verify_paper.py`'s own docstring has described since the day it was written:

    `CITECHECK.md` is a *report*: a human-run audit against one sha256 of
    `PAPER.md`, which has since moved. A report cannot fail a build.

The file knew. It said so in its first paragraph, and then reported PASS (6/6)
for weeks while the audit it names went from covering the whole paper to
covering a third of it. Knowing in prose is not a check. What P18 found on
2026-07-30:

  * `CITECHECK.md` pins `PAPER.md` at sha `4208b69c`, 1318 lines, 75,885 bytes.
  * `REVIEW.md` pins **the same state** -- both audits are against commit
    `4959df1c`, the very first assembled draft.
  * `PAPER.md` is now 3,729 lines and 237,872 bytes.

So the standing pair of audits covers 31.9% of the paper by bytes, and §7 to
§12 -- the metrics battery, the exam, the live chain, the adjudication census,
the limitations and the related work -- had never been audited by anyone, while
the README, the board and this gate's own `--explain-uncited` text all pointed
at `CITECHECK.md` as the check that covers the numbers.

That is the same failure as `papers/verify.py`'s: **a check that was performed
once, reported as a property of the current object.** The gate there was real
and unfindable; the audit here is real and unpinned. Both read green.

## What the stamp is

Every audit report in this directory carries a fenced block, near the top, that
a machine reads and a human sees at a glance:

    ```audit-stamp
    target: papers/phase1-workshop/PAPER.md
    sha256: 6b633fcc35ae612f20f4028eb45aaca1b6ed86a24eb1304af555c46228325376
    lines: 3729
    bytes: 237872
    scope: full text
    status: binding
    date: 2026-07-30
    ```

`lines` is the count of newline bytes -- `wc -l` semantics, not `wc -l` plus
one. The convention is written down because the two old audits disagree about
it: `CITECHECK.md`'s prose says "1319 lines" of a blob with 1318 newlines, and
an off-by-one in a staleness stamp is indistinguishable from a paper that has
gained a line.

`status` has **two** values and there is deliberately no third:

  `binding`  -- this report asserts it covers `target` as it is right now.
  `stale`    -- this report is acknowledged not to cover the current target.
                It must name `superseded_by`.

A third value ("partial", "mostly current", "under review") is what this whole
finding is made of. `monitor/` learned the same lesson under S28 and it holds
here: the moment a status can mean "sort of", the stale case stops being loud.

## What goes red

  G1  an audit report with no parseable stamp. An unstamped report is the
      pre-P18 state exactly: a reader cannot tell what it covers without
      archaeology, so it is refused rather than skipped.
  G2  a stamp missing a required key, or with an unknown `status`, a
      non-integer `lines`/`bytes`, or a `sha256` that is not 64 hex.
  G3  `status: binding` and the pinned sha256 is not the target's current
      sha256. The finding prints both states and the drift, because "stale" is
      not actionable and "pinned at 1318 lines, target is now 3729, +2411" is.
  G4  `status: binding`, sha matches, but `lines` or `bytes` does not. A stamp
      whose numbers were typed rather than computed.
  G5  `status: stale` with no `superseded_by`. An audit may be retired; it may
      not be retired into nowhere, because the coverage claim it was carrying
      does not evaporate when the report does.
  G6  `superseded_by` naming a file that does not exist here, or one that is
      not itself a stamped audit. The chain has to terminate on something a
      reader can open.
  G7  no audit reports found at all. An empty walk satisfies every rule above
      it; `papers/verify.py` refuses the same silence for the same reason.
  G8  a stamp whose pinned sha256 IS retrievable from `PAPER.md`'s git history
      but whose `lines`/`bytes` disagree with that blob. This catches the
      copy-pasted stamp -- the one real way to defeat G3 is to stamp a sha you
      did not measure.

## What this gate does NOT do, stated because it is the obvious next question

**It makes staleness loud. It does not make staleness illegal.** Nothing here
requires that a binding audit exist. A worker who edits `PAPER.md` turns G3 red
and can clear it by flipping `binding` to `stale` and naming a successor -- a
two-line edit, not a re-audit.

That is a deliberate trade and the alternative was considered and rejected:
requiring at least one `binding` audit at all times freezes the draft, because
every edit to a live paper would be red until a full human audit re-ran. A gate
that blocks ordinary work is a gate that gets switched off, and this territory
has the receipt for that (`papers/verify.py`'s docstring, on a permanently red
check being "a check people learn to scroll past").

What is bought instead is that the acknowledgement becomes *mandatory and
written on the artefact*. Nobody can edit the paper and leave a report claiming
to cover it. The next reader of `CITECHECK.md` sees `status: stale` and the
name of what replaced it in the first twenty lines, rather than reconstructing
it from `git log` as P18 had to.

Two smaller gaps, reproduced rather than assumed:

  * **Scope is prose.** `scope: full text` versus `scope: lines 1-908` is not
    machine-checked against anything -- a report could claim full coverage and
    have audited one section. G3 pins *when*, not *how much*. Pinning coverage
    mechanically would need the audit to emit a per-line ledger, which is a
    bigger instrument than this finding justifies.
  * **Only this directory is scanned.** Reports under `runs/` are provenance:
    each is pinned by its run's `MANIFEST.json` and is historical by
    construction, so stamping them would be stamping the past. The files this
    gate scans are the ones the README and the board call "the audits".
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent

#: Filenames in this directory that are audit reports and must carry a stamp.
#: Written as explicit patterns rather than "anything shouty" so that adding a
#: report is a deliberate act. `REVIEW_TRIAGE.md` is excluded and does not match
#: any of these: it is a disposition record *about* an audit, not an audit, and
#: it pins nothing.
AUDIT_GLOBS = ("CITECHECK.md", "CITECHECK-*.md", "REVIEW.md", "REVIEW-*.md")

#: The fenced block, anywhere in the file. Non-greedy so the first fence wins;
#: a second stamp in the same file is a defect but the first one is the one a
#: reader sees, and G2 will catch a malformed one either way.
STAMP_RE = re.compile(r"^```audit-stamp\s*$(.*?)^```\s*$",
                      re.MULTILINE | re.DOTALL)

REQUIRED = ("target", "sha256", "lines", "bytes", "scope", "status", "date")
STATUSES = ("binding", "stale")
SHA_RE = re.compile(r"\A[0-9a-f]{64}\Z")


def parse_stamp(text: str) -> tuple[dict | None, str | None]:
    """`(fields, error)`. Exactly one is None.

    Returning the error rather than raising, because every caller here is a
    check that has to keep going and report on the other files."""
    m = STAMP_RE.search(text)
    if m is None:
        return None, "no ```audit-stamp block"
    fields: dict[str, str] = {}
    for raw in m.group(1).splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            return None, f"stamp line is not `key: value`: {line!r}"
        k, v = line.split(":", 1)
        fields[k.strip()] = v.strip()
    missing = [k for k in REQUIRED if k not in fields]
    if missing:
        return None, f"stamp is missing {', '.join(missing)}"
    if fields["status"] not in STATUSES:
        return None, (f"status {fields['status']!r} is not one of "
                      f"{'/'.join(STATUSES)} -- a third value is the defect "
                      f"this stamp exists to refuse")
    if not SHA_RE.match(fields["sha256"]):
        return None, f"sha256 {fields['sha256']!r} is not 64 lowercase hex"
    for k in ("lines", "bytes"):
        if not fields[k].isdigit():
            return None, f"{k} {fields[k]!r} is not an integer"
    return fields, None


def measure(path: Path) -> tuple[str, int, int]:
    """`(sha256, lines, bytes)` of `path`, with `wc -l` line semantics."""
    b = path.read_bytes()
    return hashlib.sha256(b).hexdigest(), b.count(b"\n"), len(b)


def audit_files(paper_dir: Path) -> list[Path]:
    """Every audit report directly in `paper_dir`, deduplicated and sorted.

    Sorted so the finding order is the same on every machine; determinism is a
    stated requirement of this repository, and a gate whose output reorders
    between runs cannot be diffed."""
    found: set[Path] = set()
    for pattern in AUDIT_GLOBS:
        found.update(p for p in paper_dir.glob(pattern) if p.is_file())
    return sorted(found)


def _history_blobs(root: Path, rel: str) -> dict[str, tuple[int, int]]:
    """`{sha256: (lines, bytes)}` for every past state of `rel` in git.

    Empty on any git failure. A missing history makes G8 unenforceable, and an
    unenforceable check must be silent about passing rather than claim a green
    it did not earn -- so `check()` reports it as *unverified*, not as ok."""
    try:
        log = subprocess.run(
            ["git", "log", "--format=%H", "--", rel],
            cwd=root, capture_output=True, text=True, timeout=120)
        if log.returncode != 0:
            return {}
        out: dict[str, tuple[int, int]] = {}
        for commit in log.stdout.split():
            show = subprocess.run(["git", "show", f"{commit}:{rel}"],
                                  cwd=root, capture_output=True, timeout=120)
            if show.returncode != 0:
                continue
            b = show.stdout
            out[hashlib.sha256(b).hexdigest()] = (b.count(b"\n"), len(b))
        return out
    except (OSError, subprocess.SubprocessError):
        return {}


def check(paper_dir: Path | None = None,
          root: Path | None = None) -> tuple[bool, list[str]]:
    """`(ok, notes)` -- the G AUDITSTAMP check.

    Parameters exist for the tests, which build synthetic paper directories.
    Nothing else should pass them."""
    paper_dir = HERE if paper_dir is None else paper_dir
    root = ROOT if root is None else root

    notes: list[str] = []
    problems: list[str] = []

    reports = audit_files(paper_dir)
    if not reports:
        # G7. The same silence `papers/verify.py` refuses one level up: with no
        # reports, every rule below this line is vacuously satisfied and the
        # check reports the identical green it would report for a fully
        # stamped, fully current set of audits.
        return False, [fail(f"no audit report in {paper_dir.name}/ "
                            f"(looked for {', '.join(AUDIT_GLOBS)}) -- an "
                            f"empty walk passes every rule below it, so it is "
                            f"refused here")]

    stamps: dict[Path, dict] = {}
    for path in reports:
        fields, err = parse_stamp(path.read_text(encoding="utf-8"))
        if err is not None:
            # G1/G2.
            problems.append(f"{path.name}: {err}")
            notes.append(fail(f"{path.name} -- {err}"))
            continue
        stamps[path] = fields

    histories: dict[str, dict[str, tuple[int, int]]] = {}
    for path, f in stamps.items():
        target = root / f["target"]
        rel = f["target"]
        if not target.is_file():
            problems.append(f"{path.name}: target {rel} does not exist")
            notes.append(fail(f"{path.name} -- stamped target `{rel}` does not "
                              f"exist; the report pins nothing"))
            continue
        cur_sha, cur_lines, cur_bytes = measure(target)
        pin_lines, pin_bytes = int(f["lines"]), int(f["bytes"])

        if f["status"] == "binding":
            if f["sha256"] != cur_sha:
                # G3. Both states and the drift, because "stale" is a label and
                # "+2411 lines" is something a reader can act on.
                problems.append(f"{path.name}: binding but stale")
                notes.append(fail(
                    f"{path.name} says `status: binding` but does not cover "
                    f"`{rel}` as it is now.\n"
                    f"            pinned  sha {f['sha256'][:8]}  "
                    f"{pin_lines} lines  {pin_bytes} bytes\n"
                    f"            current sha {cur_sha[:8]}  "
                    f"{cur_lines} lines  {cur_bytes} bytes\n"
                    f"            drift   {cur_lines - pin_lines:+d} lines  "
                    f"{cur_bytes - pin_bytes:+d} bytes  "
                    f"({_covered(pin_bytes, cur_bytes)} of the current text)\n"
                    f"            Re-run the audit, or set `status: stale` and "
                    f"name `superseded_by`."))
                continue
            if (pin_lines, pin_bytes) != (cur_lines, cur_bytes):
                # G4. The sha is right, so the numbers beside it were typed
                # rather than measured -- and those are what a human reads.
                problems.append(f"{path.name}: stamp numbers disagree")
                notes.append(fail(
                    f"{path.name} -- sha256 matches `{rel}` but the stamp says "
                    f"{pin_lines} lines / {pin_bytes} bytes and the file is "
                    f"{cur_lines} / {cur_bytes}. `lines` is newline count "
                    f"(`wc -l`), not newline count plus one."))
                continue
            notes.append(f"  ok        {path.name} -- binding on `{rel}` "
                         f"@ {cur_sha[:8]}, {cur_lines} lines, {cur_bytes} bytes")
        else:
            succ = f.get("superseded_by", "").strip()
            if not succ:
                # G5.
                problems.append(f"{path.name}: stale with no successor")
                notes.append(fail(
                    f"{path.name} -- `status: stale` with no `superseded_by`. "
                    f"An audit may be retired; the coverage it was carrying "
                    f"does not retire with it, so the replacement has to be "
                    f"named."))
                continue
            succ_path = paper_dir / succ
            if not succ_path.is_file():
                # G6, first half.
                problems.append(f"{path.name}: successor {succ} missing")
                notes.append(fail(f"{path.name} -- `superseded_by: {succ}` "
                                  f"names no file in {paper_dir.name}/"))
                continue
            _, succ_err = parse_stamp(succ_path.read_text(encoding="utf-8"))
            if succ_err is not None:
                # G6, second half: the chain has to terminate on something that
                # itself says what it covers, or the retirement just moves the
                # unpinned claim one file along.
                problems.append(f"{path.name}: successor {succ} unstamped")
                notes.append(fail(f"{path.name} -- `superseded_by: {succ}`, "
                                  f"but that file has no valid stamp "
                                  f"({succ_err})"))
                continue
            notes.append(f"  ok        {path.name} -- stale, pinned "
                         f"@ {f['sha256'][:8]} ({_covered(pin_bytes, cur_bytes)}"
                         f" of `{rel}` as it now is), superseded by {succ}")

        # G8, for binding and stale alike: a stamp can only be trusted about
        # the past if the past agrees with it.
        if rel not in histories:
            histories[rel] = _history_blobs(root, rel)
        hist = histories[rel]
        if not hist:
            notes.append(f"  --        {path.name} -- git history for `{rel}` "
                         f"unavailable; the pinned sha's line/byte counts are "
                         f"UNVERIFIED, not confirmed")
        elif f["sha256"] in hist:
            h_lines, h_bytes = hist[f["sha256"]]
            if (pin_lines, pin_bytes) != (h_lines, h_bytes):
                problems.append(f"{path.name}: stamp contradicts the blob")
                notes.append(fail(
                    f"{path.name} -- the stamped sha {f['sha256'][:8]} is in "
                    f"`{rel}`'s history at {h_lines} lines / {h_bytes} bytes, "
                    f"but the stamp says {pin_lines} / {pin_bytes}. A stamp "
                    f"whose numbers were not measured from the sha beside them "
                    f"is the one way to defeat G3."))
        # A sha absent from history is ordinary: audits legitimately run
        # against an uncommitted working tree -- CITECHECK.md records the paper
        # being edited underneath it mid-pass. Absence is not evidence here.

    return not problems, notes


def _covered(pinned: int, current: int) -> str:
    """How much of the current object the pinned state was, as a percentage."""
    if current <= 0:
        return "n/a"
    return f"{100.0 * pinned / current:.1f}%"


def binding_audits(prefix: str, paper_dir: Path | None = None,
                   root: Path | None = None) -> list[str]:
    """Names of the audits whose stamp is `binding` and whose name starts with
    `prefix` -- e.g. `"CITECHECK"`.

    Exists so that prose which points at an audit can point at whichever audit
    is *currently* binding instead of hard-coding a filename. `verify_paper.py`
    used to tell readers that "`CITECHECK.md` is the human audit that does
    that" while `CITECHECK.md` covered a third of the paper; the sentence was
    true when written and became false without anyone editing it, which is the
    same defect one level of indirection up."""
    paper_dir = HERE if paper_dir is None else paper_dir
    root = ROOT if root is None else root
    out = []
    for path in audit_files(paper_dir):
        if not path.name.startswith(prefix):
            continue
        fields, err = parse_stamp(path.read_text(encoding="utf-8"))
        if err is not None or fields["status"] != "binding":
            continue
        target = root / fields["target"]
        if target.is_file() and measure(target)[0] == fields["sha256"]:
            out.append(path.name)
    return out


def fail(msg: str) -> str:
    """Same shape `verify_paper.py` prints, so G's findings read like A-F's."""
    return f"  FAIL      {msg}"
