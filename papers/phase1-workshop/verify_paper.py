"""Mechanical gate for the Phase 1 workshop draft.

`CITECHECK.md` is a *report*: a human-run audit against one sha256 of `PAPER.md`,
which has since moved. A report cannot fail a build. This is the executable half
of the same rule, and it is meant to be run before every push that touches
`papers/phase1-workshop/`.

That first paragraph was written on day one and was true on day one. By
2026-07-30 "which has since moved" had grown from a caveat into the finding:
both standing audits pinned the *same* first draft, 1318 lines / 75,885 bytes,
while `PAPER.md` had reached 3,729 lines / 237,872 bytes -- so §7 through §12
had been audited by nobody, and this file reported PASS (6/6) throughout.
Check G exists so that the sentence cannot go quietly false again.

Seven checks, each independently reported, exit code 1 if any fails:

  A. GENERATED   `PAPER.md` is byte-identical to `assemble.py`'s output from
                 `sections/*.md`. The header says "do not hand-edit"; this is the
                 test of it.
  B. PATHS       Every path-like token cited in backticks in `sections/*.md`
                 resolves. Seven verdicts, not two -- "it resolved" was one word
                 covering several different ways of not resolving for a reader:
                   ok          -- resolves repo-relative, unambiguously
                   AMBIGUOUS   -- the token's leading directory exists BOTH at
                                  the repo root and beside PAPER.md, so a reader
                                  resolving it locally lands somewhere else or
                                  nowhere. `figures/` is the live instance: the
                                  paper cites the root pipeline's fig05/06/07
                                  while sitting next to a local `figures/`
                                  holding three homonymous plates. A ruling in
                                  `ADJUDICATED_AMBIGUITY` turns one into `ruled`;
                                  a ruling whose ambiguity has gone is STALE.
                   LOCAL       -- resolves beside PAPER.md and not from the repo
                                  root, which is the root the paper's own binding
                                  rule names
                   MISCASED    -- resolves only because this filesystem ignores
                                  case; BROKEN on the Linux clone CI and the
                                  release tarball are read on
                   UNSHAREABLE -- names a checkout rather than the repository
                                  (`.worktrees/`, `.git/`, `.claude/`): one
                                  machine's scratch at one moment
                   ELIDED      -- `.../MANIFEST.json`, a typographic ellipsis
                   BROKEN      -- resolves nowhere
                 The last three, and the stale detector, landed under P20 with no
                 instance of any of them in the paper. That is deliberate: each
                 was a way for a citation to be *skipped* rather than judged, and
                 a hole is cheapest to close while nothing is standing in it.
  C. FIGDATA     The three local figure extractors are byte-deterministic: rerun
                 into a scratch tree and compare against `figures/data/*.json`.
  D. NOSECRET    No `.env` value, and nothing shaped like the ARC key, appears in
                 any file this directory publishes.
  E. UNCITED     Every *quantitative* claim block in the body cites something.
                 Check B asks "does this cited path resolve?", which means an
                 assertion citing nothing at all is invisible to it: unreferenced
                 and referenced-correctly are the same green. The paper's binding
                 rule -- "every quantitative claim in the body carries the
                 repo-relative path of the artefact it came from" -- therefore had
                 no executor until this check, and P15 found the hole the
                 expensive way, with a paragraph carrying six quantities, no
                 paths, and two numbers that did not reproduce, while
                 verify_paper reported PASS (4/4).

                 What it proves is weaker than the rule, and the gap is stated
                 rather than papered over: it proves that no quantitative block
                 is *entirely* uncited. It does not check that a number matches
                 the artefact beside it -- `CITECHECK.md` is the human audit that
                 does that, and nothing here replaces it.

                 Known gaps, from two adversarial passes. These are decisions,
                 not oversights; each was reproduced against the live scanner
                 and left open on purpose:

                   * **Any real path satisfies the block.** A claim cited with
                     a path that has nothing to do with it passes. This is the
                     "weaker than the rule" gap above, in its sharpest form.
                   * **A block, not a sentence.** One path and six unrelated
                     numbers in one paragraph passes. Sentence granularity
                     flags every subordinate clause and gets the gate switched
                     off, which is worse.
                   * **Balanced code fences are skipped.** Claims pasted as
                     tool output are not read -- and, mirror image, a path
                     cited only inside a repro command does not count for the
                     prose around it.
                   * **The continuation merge is unbounded.** A list or table
                     inherits a citation from any distance above it, so long as
                     no heading intervenes.
                   * **`one`..`ten` are not quantities.** 608 of the 805
                     spelled-out numbers in the sections are determiners; the
                     fraction and multiplier vocabulary is covered, the bare
                     small cardinals are not.
                   * **`section-word` ranges are greedy.** "Steps 3 to 4200"
                     exempts 4200 as part of a step range.

  F. BARE        No body citation is a bare filename that could mean several
                 files. Check B skips a token with no `/` **by design** -- it
                 resolves paths, and a bare filename is not one -- while check E
                 accepts it if the basename exists anywhere. So `MANIFEST.json`,
                 125 real files here, satisfied both while pointing a reader at
                 none of them. The bar is ambiguity, not bareness: one candidate
                 is locatable, and flagging every `Theoria.md` would make the
                 gate noise.

                 Known gaps, all reproduced against the live scanner:

                   * **Uniqueness is not findability, and it is the proxy this
                     check is built on.** The sharpest case is in the paper:
                     §10 cites four `SURVEY-*.md` bare, each unique, so F passes
                     them -- while §10.7 says those files exist only as
                     untracked files in a machine-local worktree on a branch
                     that was never pushed. F calls the paper's least
                     resolvable citations locatable. It is also unstable:
                     deleting a file takes a token from one candidate to zero.
                   * **A path is a free exit.** F skips anything with a `/` and
                     defers to B, which does not catch `/STATUS.md`,
                     `figures/*.csv`, or a directory-only `engine-rig/`.
                   * **One character outside the token class hides a citation
                     from all three checks.** `STATUS.md#seal`, `~/STATUS.md`,
                     `**STATUS.md**` and `STATUS.md:L12` never match
                     `CITE_TOKEN` at all, so they are not read rather than
                     failed. `:L12` reopens exactly what the `:722-724` support
                     closed.
                   * **The candidate set is the working tree, not the commit.**
                     `_candidates` walks the filesystem, so untracked scratch
                     changes a verdict. `git ls-files` would fix it.
                   * **Nothing checks the anchor inside the file.** F resolves
                     `THEORIZE_LOG.md` to one path; that the entry id beside it
                     is right is unchecked, and P17 shipped a wrong one
                     (`O-01` for what the log calls `D-A0-007`).
                   * **False positives F does flag:** a directory supplied in
                     the same sentence, a verbatim blockquote from another
                     document, a repro instruction. It also reports per
                     occurrence, so one name used seven times prints seven
                     findings -- pressure toward exactly the section-wide
                     ruling the BROAD guard now limits.

  G AUDITSTAMP  Every audit report in this directory carries a machine-readable
                 stamp naming the sha256, line count and byte count of what it
                 audited, and that stamp is true: `binding` reports must pin the
                 target's current state, `stale` ones must name their successor,
                 and a stamp whose numbers disagree with the blob its own sha
                 names is refused. Full rationale, the two-value `status`
                 vocabulary, and the gaps left open are in `audit_stamp.py`.

                 The gap worth knowing before relying on it: this makes
                 staleness *loud*, not *illegal*. Editing the paper turns G red,
                 and a worker may clear it by marking the audit stale rather
                 than by re-auditing. Requiring a binding audit at all times was
                 considered and rejected -- it freezes a live draft, and a gate
                 that blocks ordinary work gets switched off.

Run:  python papers/phase1-workshop/verify_paper.py
      python papers/phase1-workshop/verify_paper.py --quiet   (verdict lines only)
      python papers/phase1-workshop/verify_paper.py --explain-uncited  (E, verbose)

No network, no API key, no model call, no game spend.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import audit_stamp

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SECTIONS = HERE / "sections"

# A backticked token counts as a path claim if it has a directory separator and
# a plausible extension, or ends in a separator. This deliberately misses bare
# filenames (`PAPER.md`) -- those are the 31 non-repo-relative citations
# CITECHECK already counted, and they are a style finding, not a broken link.
# `{a0-base,a2-base,a2-charitable}` is how section 7 cites three sibling
# artefacts at once. Without braces and commas in the class the token does not
# match at all, so the citation was invisible to this check -- it was neither ok
# nor BROKEN, it simply was not there. Found by check E's triage, and it was
# check B's blind spot first.
# The `:722-724` tail is optional. It was added so that a line-anchored citation
# would be matched *at all* -- before it, a path B never matched was a path B
# never resolved, so `no/such/dir/thing.md:3` was accepted by check E and called
# broken by nobody, and adding a line number to a citation was a way to stop it
# being checked. It was then thrown away, which is the other half of the same
# hole and what P21 closes: the number is now captured and checked against the
# file's length. See `anchor_overruns`.
PATH_TOKEN = re.compile(
    r"`([A-Za-z0-9_.\-/{},]+/[A-Za-z0-9_.\-/{},]*?)"
    r"(?::(?P<anchor>\d+(?:[-–]\d+)?))?`")

# Tokens that look like paths but are not repository paths.
NOT_A_PATH = re.compile(
    r"^(https?:|arxiv|doi|[0-9]+/[0-9]+$)"  # urls, dois, and fractions like 276/276
    r"|^[0-9]+/[0-9]+"                       # 34/38, 252/252, ...
)

# Directories that legitimately do not exist in a checkout. Each is absent for a
# reason a reader can act on: `.toolchain/` is rebuilt by the documented Fast
# Downward build, `figures/.verify/` by rerunning the figure pipeline. A citation
# into one of them names something the reader can produce.
#
# `.worktrees/` used to be on this list and is not, because it fails that test.
# A worktree path names one machine's scratch checkout of one branch at one
# moment; no reader can produce it and no reader can follow it. It was also the
# one prefix all three path checks agreed to ignore -- B skipped it here, F skips
# anything with a `/`, and E only asks that *a* citation be present -- so
# `.worktrees/anything/at/all.md` satisfied the binding rule against every check
# in this file at once. §10.7 already concedes the paper's least resolvable
# citations are exactly of this kind (the four `SURVEY-*.md`, untracked, in a
# machine-local worktree, on a branch never pushed). See UNSHAREABLE in
# `classify`.
GITIGNORED_BY_DESIGN = (
    ".toolchain/",
    "figures/.verify/",
)

#: Path prefixes that name a checkout rather than the repository. Kept separate
#: from the list above because the verdict is the opposite one.
UNSHAREABLE_PREFIXES = (".worktrees/", ".git/", ".claude/")

# Ambiguities that have been looked at and ruled on, each with its adjudication.
# The rule is `figures/PARITY.md`'s: the paper cites the repository-root figure
# pipeline, and the three homonymous plates under `papers/phase1-workshop/figures/`
# are kept deliberately as a second opinion rather than deleted. An ambiguity NOT
# listed here fails, because it is new and nobody has ruled on it. A permanently
# red check is a check people learn to scroll past; a check that hides its
# rulings is worse than no check.
ADJUDICATED_AMBIGUITY = {
    token: "repo-root figure pipeline; the local figures/ is the witness (figures/PARITY.md)"
    for token in (
        "figures/fig05_a2_repair_loop.py",
        "figures/fig06_concept_timeline.py",
        "figures/fig07_a0_vs_a0prime.py",
        "figures/out/light/fig05_a2_repair_loop.svg",
        "figures/out/light/fig06_concept_timeline.svg",
        "figures/out/light/fig07_a0_vs_a0prime.svg",
        "figures/out/dark/fig06_concept_timeline.svg",
        "figures/csv/fig05_a2_repair_loop.csv",
        "figures/csv/fig06_concept_timeline.csv",
        "figures/csv/fig07_a0_vs_a0prime.csv",
    )
}


def fail(msg: str) -> str:
    return msg


#: A paper has an abstract and at least one body section. Below this there is
#: nothing to check and every loop in this file succeeds by having nothing to
#: iterate over: `sections/` emptied gives `PASS (6/6)`, and check E printed
#: `-1 body sections` on the way past because it subtracts the exempt abstract
#: from a count of zero.
#:
#: The floor is the same device, and the same reasoning, as `MIN_PAPERS` in
#: `papers/verify.py`: a walk over nothing satisfies every check written above
#: it, so "there was nothing to check" must never be reported the way
#: "everything checked out" is. That file refuses an empty `papers/`; this one
#: refuses an empty `sections/`. One directory apart, one level of the same hole.
MIN_SECTIONS = 2


def body_sections() -> list[Path]:
    """The sections check E and F are responsible for: everything but the
    abstract, which is the paper's one declared exemption."""
    return [p for p in sorted(SECTIONS.glob("*.md"))
            if p.name not in EXEMPT_SECTIONS]


def _below_floor() -> list[str] | None:
    """Failure notes if `sections/` cannot support a check, else None."""
    found = sorted(SECTIONS.glob("*.md"))
    if len(found) >= MIN_SECTIONS and len(found) > len(EXEMPT_SECTIONS):
        return None
    return [
        fail(f"  sections/ holds {len(found)} section(s); a paper is an abstract "
             f"and at least one body section ({MIN_SECTIONS} files)."),
        fail("  Every check in this file walks sections/, so below the floor "
             "they all pass by having nothing to read -- which is why the floor"),
        fail("  is here and not left to the individual checks."),
    ]


def check_generated() -> tuple[bool, list[str]]:
    """A. PAPER.md must equal a fresh assemble of sections/.

    Carries the section floor, because it is the check that owns the
    relationship between `PAPER.md` and `sections/`. With `sections/` emptied,
    `parts` is `[]`, `expected` is the banner alone, and a `PAPER.md` holding
    just the banner is byte-identical to it -- so the strictest check in the file
    passed a paper with no content in it.
    """
    notes: list[str] = []
    below = _below_floor()
    if below is not None:
        return False, below
    banner = (
        "<!-- GENERATED by assemble.py from sections/*.md — edit the sections, "
        "not this file. -->\n\n"
    )
    parts = [p.read_text(encoding="utf-8").rstrip("\n") for p in sorted(SECTIONS.glob("*.md"))]
    expected = banner + "\n\n---\n\n".join(parts) + "\n"
    actual = (HERE / "PAPER.md").read_text(encoding="utf-8")
    if actual == expected:
        notes.append(f"  {len(parts)} sections, {len(expected.split())} words, byte-identical")
        return True, notes
    notes.append(fail("  PAPER.md differs from assemble.py's output -- it was hand-edited,"))
    notes.append(fail("  or a section changed and assemble.py was not rerun. Run:"))
    notes.append(fail("      python papers/phase1-workshop/assemble.py"))
    if len(actual) != len(expected):
        notes.append(f"  ({len(actual)} bytes on disk vs {len(expected)} regenerated)")
    return False, notes


BRACE = re.compile(r"\{([^{}]*)\}")


def expand_braces(token: str) -> list[str]:
    """`a/{x,y}/c.json` -> [`a/x/c.json`, `a/y/c.json`]; anything else unchanged.

    A brace citation names several sibling artefacts, and it resolves only if
    every one of them does -- which is the claim the prose is making when it
    writes them that way.
    """
    m = BRACE.search(token)
    if not m:
        return [token]
    out = []
    for alt in m.group(1).split(","):
        out.extend(expand_braces(token[:m.start()] + alt.strip() + token[m.end():]))
    return out


def exists_exact(base: Path, token: str) -> bool:
    """`(base / token).exists()`, but case-exact on every filesystem.

    `Path.exists()` asks the filesystem, and this one is NTFS, which does not
    care about case. So `Engine-Rig/STATUS.md` and `engine-rig/status.md` were
    both `ok` here and both `BROKEN` on a Linux clone: the gate's verdict
    depended on the machine it ran on, and it ran on the machine where the
    answer is always yes. Everything the gate exists to protect -- CI, a fresh
    clone, the Phase 4 release tarball -- is somewhere else.

    Walking the components against `os.listdir` is the portable form of the
    question "is this the name the repository actually uses". On Linux it is
    exactly `exists()` and costs a directory read per component; on Windows it is
    the check `exists()` cannot make.
    """
    cur = base
    for part in token.strip("/").split("/"):
        if part in ("", "."):
            continue
        try:
            names = os.listdir(cur)
        except OSError:
            return False
        if part not in names:
            return False
        cur = cur / part
    return cur != base and cur.exists()


#: Worst-first. Every verdict `classify` can return has to appear here, or a
#: brace citation carrying one falls through the loop and comes back `skip` --
#: which is how a citation stops being checked rather than failing.
VERDICT_ORDER = ("BROKEN", "MISCASED", "UNSHAREABLE", "LOCAL", "ELIDED",
                 "AMBIGUOUS", "RULED", "ok")


def classify(token: str) -> str:
    """One of `VERDICT_ORDER`, or `skip`, for one cited path token."""
    if NOT_A_PATH.search(token):
        return "skip"
    if "{" in token or "}" in token:
        verdicts = {classify(t) for t in expand_braces(token)}
        for worst in VERDICT_ORDER:
            if worst in verdicts:
                return worst
        return "skip"
    if any(token.startswith(p) or f"/{p}" in token for p in UNSHAREABLE_PREFIXES):
        return "UNSHAREABLE"
    if token.startswith(".../") or "/.../" in token:
        # `.../MANIFEST.json` is a typographic elision, not a link. It still
        # breaks the binding rule -- a reader cannot resolve it -- so it is
        # reported, but it is a different defect from a path that does not exist.
        return "ELIDED"
    if any(token.startswith(g) or f"/{g}" in token for g in GITIGNORED_BY_DESIGN):
        return "skip"

    at_root = exists_exact(ROOT, token)
    at_local = exists_exact(HERE, token)

    head = token.split("/", 1)[0]
    head_both = (ROOT / head).is_dir() and (HERE / head).is_dir()

    if at_root and at_local and (ROOT / token).resolve() == (HERE / token).resolve():
        return "ok"

    if at_root or at_local:
        # Resolves -- but if the leading directory also exists in both trees, a
        # reader resolving relative to PAPER.md lands somewhere else or nowhere.
        if (at_root and at_local) or head_both:
            return "RULED" if token in ADJUDICATED_AMBIGUITY else "AMBIGUOUS"
        if at_local and not at_root:
            # Resolves beside PAPER.md and nowhere else. The binding rule the
            # paper sets itself asks for "the repo-relative path of the artefact
            # it came from", and this is not one: a reader following it from the
            # repository root -- which is where the paper says to stand -- lands
            # nowhere. `ok` said the citation resolved without saying from where,
            # so the one verdict covered both the rule and its violation.
            return "LOCAL"
        return "ok"

    if (ROOT / token).exists() or (HERE / token).exists():
        # Only `exists()` finds it, and `exists()` is case-blind here. The
        # citation is spelled in a case the repository does not use.
        return "MISCASED"
    return "BROKEN"


def resolve_cited(token: str) -> Path | None:
    """The file a resolving citation points at, or None."""
    for base in (ROOT, HERE):
        if (base / token).is_file():
            return base / token
    return None


def anchor_overruns(path: Path, anchor: str) -> tuple[int, int] | None:
    """`(last line named, lines in the file)` if the anchor runs off the end.

    P19 measured this at **zero yield on the paper** -- 22 line-anchored
    citations, 22 in range -- and adopted it anyway, for two reasons worth
    keeping beside the code. It is free exactly once: today nothing has to be
    rewritten to make it pass, and that stops being true the moment somebody
    cites line 900 of a 300-line file. And it cannot silently degrade
    afterwards.

    **What it catches is not what P18 got wrong.** P18's `:148` for a line that
    is at `:149` is in range and wrong, and no range check can see that. P19
    built the content-anchor gate that could, measured it at 2 HIT / 12 MISS / 8
    NOQUOTE, hand-checked two of the twelve MISSes and found both false, and
    ruled against shipping it: twelve false reds is a gate somebody switches off
    inside one session, and a switched-off gate is worse than a written-down
    limit because it reads like coverage. That ruling stands. So the sentence
    this check is allowed to print is the narrow one -- *in range* -- and never
    *correct*.
    """
    last = int(re.split(r"[-–]", anchor)[-1])
    try:
        n = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return None
    return (last, n) if last > n else None


def check_paths() -> tuple[bool, list[str]]:
    """B. Every cited path resolves, and unambiguously.

    Three verdicts were added under P20, all of them latent when they landed --
    the paper has no instance of any of the three, which is the point of adding
    them before it does:

    * `MISCASED` -- resolved only because NTFS is case-blind. Green here, BROKEN
      on the Linux clone CI and the release tarball are read on.
    * `LOCAL` -- resolves beside `PAPER.md` and not from the repository root,
      which is the root the paper's own binding rule names.
    * `UNSHAREABLE` -- points into a worktree or a `.git`; nobody but the author
      can follow it, and until now nothing in this file looked at it.

    And a stale detector for `ADJUDICATED_AMBIGUITY`, which checks E and F have
    each had for their own ruling tables and this one did not. A ruling is
    written about a live ambiguity; when the ambiguity goes, the ruling stays
    behind and silently excuses the *next* token that happens to have that name.
    """
    notes: list[str] = []
    seen: dict[str, tuple[str, str]] = {}  # token -> (verdict, first section seen in)
    anchored: dict[tuple[str, str], str] = {}  # (token, anchor) -> first section
    for section in sorted(SECTIONS.glob("*.md")):
        for m in PATH_TOKEN.finditer(section.read_text(encoding="utf-8")):
            token, anchor = m.group(1), m.group("anchor")
            if anchor:
                anchored.setdefault((token, anchor), section.name)
            if token in seen:
                continue
            verdict = classify(token)
            if verdict != "skip":
                seen[token] = (verdict, section.name)

    overrun: list[str] = []
    for (token, anchor), where in sorted(anchored.items()):
        if seen.get(token, ("skip",))[0] not in ("ok", "RULED"):
            continue  # the path itself is already a finding; do not report twice
        path = resolve_cited(token)
        if path is None:
            continue
        span = anchor_overruns(path, anchor)
        if span is not None:
            last, total = span
            overrun.append(
                f"  OUTOFRANGE {token}:{anchor}   ({where}) -- the file resolves "
                f"and has {total} lines, so line {last} is not in it. The path "
                f"half of this citation was checked and the number half was "
                f"parsed and thrown away")

    def of(kind: str) -> list[str]:
        return sorted(t for t, (v, _) in seen.items() if v == kind)

    ok, ruled = of("ok"), of("RULED")
    amb, elided, broken = of("AMBIGUOUS"), of("ELIDED"), of("BROKEN")
    miscased, local, unshareable = of("MISCASED"), of("LOCAL"), of("UNSHAREABLE")

    # A ruling that no longer excuses anything. Same rule, and the same words,
    # as check E's and check F's: it is removed, not left sitting there to
    # excuse whatever next arrives under that name.
    stale = sorted(set(ADJUDICATED_AMBIGUITY) - set(ruled))

    notes.append(f"  {len(seen)} distinct path citations: {len(ok)} ok, "
                 f"{len(ruled)} ambiguous-but-ruled, {len(amb)} ambiguous-unruled, "
                 f"{len(elided)} elided, {len(broken)} broken, "
                 f"{len(miscased)} miscased, {len(local)} paper-local, "
                 f"{len(unshareable)} unshareable, {len(stale)} stale rulings")
    notes.append(f"  {len(anchored)} of them carry a line anchor: "
                 f"{len(overrun)} run off the end of the file. In range is not "
                 f"the same as correct -- see anchor_overruns()")
    notes.extend(fail(o) for o in overrun)
    for t in broken:
        notes.append(fail(f"  BROKEN    {t}   ({seen[t][1]}) -- resolves from neither the repo "
                          f"root nor beside PAPER.md"))
    for t in miscased:
        notes.append(fail(f"  MISCASED  {t}   ({seen[t][1]}) -- resolves only because this "
                          f"filesystem ignores case. On a Linux clone -- CI, and the release "
                          f"tarball -- it is BROKEN. Spell it the way the repository does"))
    for t in unshareable:
        notes.append(fail(f"  UNSHARE.  {t}   ({seen[t][1]}) -- names a checkout, not the "
                          f"repository: one machine's worktree at one moment. No reader can "
                          f"follow it, and B, E and F all used to skip it, so it satisfied "
                          f"the binding rule against every check at once"))
    for t in local:
        notes.append(fail(f"  LOCAL     {t}   ({seen[t][1]}) -- resolves beside PAPER.md and "
                          f"not from the repo root, which is the root the binding rule names. "
                          f"Cite papers/phase1-workshop/{t}"))
    for t in elided:
        notes.append(fail(f"  ELIDED    {t}   ({seen[t][1]}) -- an ellipsis is not a path a "
                          f"reader can follow; the binding rule wants the whole thing"))
    for t in amb:
        notes.append(fail(f"  AMBIGUOUS {t}   ({seen[t][1]}) -- `{t.split('/', 1)[0]}/` exists "
                          f"both at the repo root and beside PAPER.md, and nobody has ruled "
                          f"which one this means"))
    for t in ruled:
        notes.append(f"  ruled     {t} -- {ADJUDICATED_AMBIGUITY[t]}")
    for t in stale:
        notes.append(fail(
            f"  STALE     {t} is ruled ambiguous and is not ambiguous any more -- the "
            f"citation is gone, or the collision behind it is. A ruling that excuses "
            f"nothing is removed, not left to excuse the next token by that name."))
    return not (broken or amb or elided or miscased or local
                or unshareable or stale or overrun), notes


def check_figdata() -> tuple[bool, list[str]]:
    """C. The local figure extractors are byte-deterministic.

    They are run *in place*, not in a scratch copy: each one locates the
    repository by walking up from its own `__file__`, so a copied script reads a
    different tree and the test would measure the harness instead of the code.
    Running in place is safe precisely because the property under test is
    idempotence -- if the extractors are deterministic and the committed payloads
    are current, the run is a no-op. If it is not a no-op that is the finding, and
    the original bytes are restored before returning either way.

    Two holes closed here, both found by an adversarial audit under S34.

    **The payload was compared against itself.** The snapshot was taken from the
    committed files, the extractor then ran *in place*, and the comparison read
    the file back. An extractor that produced nothing at all left the committed
    payload sitting there untouched -- `payload.exists()` was true, the bytes
    matched, and the `was not regenerated` branch could never execute. A gutted
    extractor was reported as `reran in place`. So the payloads are now *removed*
    before the rerun: the extractor has to produce its own output, which is the
    property the check claims to test. The bytes are held in memory and restored
    in the `finally` either way, so the tree survives an extractor that fails
    halfway.

    **A payload with no extractor was invisible.** The summary counted `scripts`
    and `before` separately and printed both, so renaming one script out of the
    `fig[0-9]*.py` glob printed `2 extractors reran in place, 3 payloads
    unchanged` and passed. Two numbers that must agree, printed side by side and
    compared by nobody. They are reconciled now: an orphan payload fails.
    """
    notes: list[str] = []
    scripts = sorted(HERE.glob("figures/fig[0-9]*.py"))
    if not scripts:
        return False, [fail("  no figure extractors found under figures/")]

    data_dir = HERE / "figures" / "data"
    before = {p: p.read_bytes() for p in sorted(data_dir.glob("*.json"))}
    expected = {data_dir / f"{s.stem}.json" for s in scripts}
    drifted: list[str] = []

    for orphan in sorted(set(before) - expected):
        drifted.append(f"{orphan.name} has no extractor under figures/ -- either "
                       f"the script was renamed out of the fig[0-9]*.py glob or "
                       f"the payload outlived it; nothing regenerates this file")

    try:
        for path in before:
            if path in expected:
                path.unlink()
        for script in scripts:
            r = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True, text=True, cwd=str(HERE),
            )
            if r.returncode != 0:
                last = (r.stderr or r.stdout).strip().splitlines()[-1:] or ["(no output)"]
                drifted.append(f"{script.name} exited {r.returncode}: {last[0]}")
                continue
            payload = data_dir / f"{script.stem}.json"
            if not payload.exists():
                drifted.append(f"{script.stem}.json was not regenerated -- the "
                               f"extractor exited 0 and produced no payload")
            elif payload not in before:
                drifted.append(f"{script.stem}.json is new: the extractor produces "
                               f"a payload that was never committed")
            elif payload.read_bytes() != before[payload]:
                drifted.append(f"{script.stem}.json changed on rerun -- the committed payload "
                               f"is stale, or the extractor is not deterministic")
    finally:
        for path, blob in before.items():
            if not path.exists() or path.read_bytes() != blob:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(blob)

    if drifted:
        notes.extend(fail(f"  {d}") for d in drifted)
        return False, notes
    notes.append(f"  {len(scripts)} extractors each removed and regenerated their "
                 f"payload byte-for-byte ({len(before)} payloads, no orphans)")
    return True, notes


# The ARC key's *shape*: a canonical UUID -- 36 characters, hex with dashes at
# 8/13/18/23. Established by reading `.env` through `arc-recon/client.py` and
# printing properties only (length, charset predicates, dash positions); the
# value was never printed and is not here.
#
# Encoding the shape is not encoding the value, and it is the only way to write
# the check this docstring has promised since it was first drafted ("nothing
# shaped like the ARC key"). A 36-character UUID mask discloses no part of the
# 128 bits inside it -- the format is public, guessable, and shared with every
# other UUID in the repository, which is exactly why the shape alone cannot be
# the trigger. See `CREDENTIAL_CONTEXT`.
UUID_SHAPED = re.compile(
    r"\b[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}\b")

# Why shape alone must not fail the check: 4467 UUID-shaped tokens sit in 140
# tracked files (game session ids, ledger rows, canary runs), and two are inside
# this directory already -- both `https://repositories.lib.utexas.edu/items/<uuid>`
# in P7's search traces. A check that reds on those is red on arrival, and the
# reasoning recorded for check E applies with more force here: a permanently red
# gate is a gate somebody switches off, and this is the gate standing between
# the credential and the Phase 4 release manifest. So a shaped token fails only
# in a *credential context*, which is what distinguishes a pasted key from a
# library URL.
CREDENTIAL_CONTEXT = re.compile(
    r"(?i)\b(?:arc[-_ ]?api[-_ ]?key|api[-_ ]?key|apikey|secret|token|bearer"
    r"|authorization|x-api-key|passwd|password|credential)\b")

# Values that name the absence of a value. `.env.example` ships
# `ARC_API_KEY=` empty on purpose, `mask()` output is documented as safe to log
# ("7171...05dd"), and a placeholder in a worked example is not a leak. Without
# this the check reds on its own documentation, which is the same self-inflicted
# red as above.
PLACEHOLDER = re.compile(
    r"(?i)^(?:|<[^>]*>|\{[^}]*\}|x{3,}|\*{3,}|\.{3,}|-+|none|null|unset|todo"
    r"|redacted|your[-_ ]?key[-_ ]?here|changeme|placeholder|\$\{?[A-Z_]+\}?)$")

#: Length at or above which a right-hand side is substantial enough to be a
#: credential rather than a flag or an enum.
MIN_SECRET_LEN = 12


# A credential name *immediately* before its separator, then a value with no
# whitespace in it. Both halves were learned by running the first draft over this
# directory, which produced four false positives and no true ones: prose and code
# discussing the word "token" -- `count(Token, present = false)`, `B never saw
# the token: a citation nobody...`. The first draft matched a credential word
# anywhere in the line prefix, so any sentence with "token" before a colon was a
# leak.
#
# Whitespace is the discriminator that does the work: a secret is one opaque run
# of characters and a sentence is not. `a citation *nobody*` is 19 characters and
# was flagged; it cannot be, once the value may not contain a space.
#
# Bare `token` is absent here and present in `CREDENTIAL_CONTEXT`, which is the
# one piece of local vocabulary this check has to know. In this repository
# `token` overwhelmingly means *citation token*: P17's census.json is a list of
# `"token": "A0_REPORT.md"` records, and check B's own `PATH_TOKEN` uses the word
# the same way. Bare `token` plus any opaque 12 characters produced 31 false
# positives here and no true ones. Bare `token` plus something *shaped like the
# key* is still flagged, by `_shaped_in_context` -- the compounds that only ever
# mean a credential (`access_token`, `auth_token`, ...) stay in this pattern.
CREDENTIAL_ASSIGNMENT = re.compile(
    r"""(?ix)
    (?:^|[\s,{\[(<"'])                     # a delimiter, not mid-word
    ["']?
    (?: arc[-_ ]?api[-_ ]?key | api[-_ ]?key | apikey | secret
      | (?: access | auth | api | refresh | session ) [-_ ]? token
      | bearer | authorization | x-api-key | passwd | password | credential )
    ["']?
    \s* [:=] \s*                           # the separator, adjacent
    ["']?
    (?P<value> [A-Za-z0-9_\-.+/=]{12,})    # one opaque run, no whitespace
    """)

# A value that names a file is a filename, not a secret. `A0_REPORT.md`,
# `playbook.dsl` and `THEORIZE_LOG.md` are all 12+ opaque characters. A UUID
# never matches this -- it ends in twelve hex digits with no dot.
FILENAME_SHAPED = re.compile(r"\.[A-Za-z][A-Za-z0-9]{1,4}$")

# `Authorization: Bearer <token>` puts the secret one word further out, past a
# space rather than a separator, so the pattern above cannot see it.
BEARER_VALUE = re.compile(
    r"(?i)\bbearer\s+([A-Za-z0-9_\-.+/=]{12,})")


#: How near a credential word has to be for a shaped token to count. Proximity
#: rather than "anywhere on the line", because a search trace discussing tokens
#: and quoting a URL with a UUID in it is one line away from a false positive,
#: and this file's own P7 traces are that line.
CONTEXT_WINDOW = 40


def _shaped_in_context(line: str) -> bool:
    """A key-shaped token sitting next to a word that makes it a credential.

    What this deliberately cannot catch, stated so nobody reads more into a
    green than is there: a *bare* shaped token with no credential word near it.
    There are 4467 of those in 140 tracked files -- session ids, ledger rows,
    canary runs -- and two inside this directory, both a Texas library URL in
    P7's search traces. Flagging bare shape would red the gate on arrival, and
    check E's reasoning applies with more force here: a permanently red gate is
    one somebody switches off, and this is the gate between the credential and
    the release manifest. The exact-value scan is what covers that case, and it
    only runs where `.env` exists -- which is the residual gap, named in the run
    record rather than papered over."""
    for m in UUID_SHAPED.finditer(line):
        lo = max(0, m.start() - CONTEXT_WINDOW)
        window = line[lo:m.end() + CONTEXT_WINDOW]
        if CREDENTIAL_CONTEXT.search(window):
            return True
    return False


def _assignment_hits(text: str) -> list[str]:
    """Lines assigning a substantial opaque value to a credential-shaped name.

    Shape-independent on purpose: this is the mechanism that catches the *next*
    secret, which will not be a UUID. `ARC_API_KEY=<36 chars of anything>` is a
    leak whatever the 36 characters are, and a check that only knows today's key
    shape learns nothing the day the key is rotated into a different one."""
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for rx in (CREDENTIAL_ASSIGNMENT, BEARER_VALUE):
            for m in rx.finditer(line):
                value = m.group(1) if rx is BEARER_VALUE else m.group("value")
                if PLACEHOLDER.match(value) or FILENAME_SHAPED.search(value):
                    continue
                out.append(f"line {lineno}: a credential-named field carries a "
                           f"{len(value)}-character opaque value")
    return out


#: How long to wait for the one `git check-ignore` call before giving up on it.
#: Expiring is a git failure like any other and widens the scan rather than
#: narrowing it, so a slow filesystem costs a slow run, never a quiet one.
GITIGNORE_TIMEOUT = 60


#: The floor on files actually content-scanned. Below this, check D reports a
#: broken check rather than a clean tree.
#:
#: This exists because narrowing the scan re-opened the exact hole the rewrite
#: closed. The docstring below records the original defect as "the secret list
#: came back empty, the loop iterated zero times, and the check returned True" --
#: a green earned by examining nothing. An ignore filter is a second way in: get
#: `HERE` wrong, run against a tree that never unpacked, or hand git an ignore
#: rule that swallows the directory, and the walk collapses to a handful of files
#: while the note still reads `[PASS] D NOSECRET`.
#:
#: 40, and the number is chosen from the inventory rather than picked round.
#: `git ls-files papers/phase1-workshop` is 165 files, of which 117 are under
#: `runs/` -- run records accumulate and may be pruned, so they cannot hold up a
#: floor. The 48 that remain are structural: 13 `sections/`, 13 `figures/`, and
#: the top-level machinery (`PAPER.md`, this file, `audit_stamp.py`, the review
#: and citation reports, the suites). 40 sits just under that 48, so pruning a
#: few structural files does not red the gate, and four times above the largest
#: tree any test in the suite builds. A collapsed walk lands at 0-3; it never
#: lands at 40. `MIN_SECTIONS` above is the same device one directory in: a walk
#: over nothing satisfies every loop written above it, so "there was nothing to
#: check" must never be printed the way "everything checked out" is.
MIN_SCANNED = 40


#: An absent config path, outside the audited tree and unguessable.
#:
#: The first version of this pin was `HERE / ".check-d-no-global-git-config"` --
#: absent by convention, on no ignore list, inside the very directory the check
#: audits. A refuter created that file with a `[core] excludesFile` line in it and
#: `core.excludesFile` was live again, hiding a planted credential behind a green
#: gate. "Pinned at an absent path" is a claim about the future, and the one
#: directory it was staked on is the one directory guaranteed to be writable by
#: whatever is being audited.
#:
#: So: the system temp directory, a name carrying this process's pid and eight
#: random bytes, computed once per interpreter and never created. Nothing can
#: pre-create a path it cannot predict. This is the *second* of two independent
#: mechanisms, not the load-bearing one -- `GIT_CONFIG_PIN` below does not depend
#: on any path being absent, and closes the same hole even if this one is somehow
#: made present.
_ABSENT_GIT_CONFIG = Path(tempfile.gettempdir()) / (
    "check-d-absent-git-config-%d-%s" % (os.getpid(), os.urandom(8).hex()))


#: Command-line config that outranks every config file, so it needs no absent
#: path to work. `-c` beats system, global, XDG and repository config alike, and
#: (verified against git 2.54) it also beats `GIT_CONFIG_COUNT`/`KEY_n`/`VALUE_n`
#: injection.
#:
#: `core.excludesFile=` (empty) is the load-bearing one, and it closes a hole
#: neither the refuter nor the first patch named: git's *default* for
#: `core.excludesFile` is `$XDG_CONFIG_HOME/git/ignore`, falling back to
#: `~/.config/git/ignore`. That is a built-in default, not a config-file setting,
#: so pinning `GIT_CONFIG_GLOBAL` never disabled it -- a line in
#: `~/.config/git/ignore` silently removed files from this scan on any machine
#: that had one, with no config anywhere to show for it. Verified: with global
#: config pinned and `GIT_CONFIG_NOSYSTEM=1` set, that file is still obeyed; with
#: `-c core.excludesFile=` it is not.
#:
#: `core.excludesFile` is the only ignore lever config has. Repository
#: `.gitignore` and `$GIT_DIR/info/exclude` are files, not config, and the first
#: is the authority this check is *supposed* to obey.
GIT_CONFIG_PIN = ("-c", "core.excludesFile=")


#: Environment variables kept when calling git. Everything else named `GIT_*` is
#: deleted.
#:
#: A denylist here was the defect: `_git_env()` copied `os.environ` wholesale and
#: pinned the three variables the author had thought of, so `GIT_INDEX_FILE`
#: pointed at a nonexistent path made git read an empty index -- and the empty
#: index made a **tracked, committed** file matching `*.txt` and holding a
#: 36-character credential report as ignored, skipped, and green. The entire
#: defence of narrowing the scan is "a tracked file is never skipped, because
#: check-ignore consults the index"; that is true of `.gitignore` patterns and
#: false of the process environment. Nor is it exotic: `git commit --only`,
#: `git stash`, `git rebase`, `git filter-branch` and any hook running over a
#: temporary index all export `GIT_INDEX_FILE`, and this file's header asks to be
#: run before every push.
#:
#: The list below is an **allowlist**, which is why it is complete: it does not
#: rest on having enumerated git's variables correctly, only on git's convention
#: that they are all named `GIT_*`. A variable this author has never heard of, or
#: one added in a future git, is deleted by default. `GIT_CONFIG_COUNT` and its
#: `GIT_CONFIG_KEY_n`/`VALUE_n` companions go with them, as do `GIT_DIR`,
#: `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`, the `*_PATHSPECS`
#: family and the `GIT_TRACE*` family, none of which are enumerated here because
#: none of them need to be.
#:
#: Two are kept deliberately, both because they can only ever *widen* the scan:
#: `GIT_CEILING_DIRECTORIES` and `GIT_DISCOVERY_ACROSS_FILESYSTEM` can stop git
#: finding the repository, which makes the ignore list unavailable, which scans
#: everything and says so. Removing them would buy nothing and would take away
#: the honest way to exercise the release-tarball path.
GIT_ENV_KEEP = frozenset({
    "GIT_CEILING_DIRECTORIES",          # can only prevent discovery -> widens
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",  # likewise
})


def _git_env() -> dict[str, str]:
    """The environment every git call in this check runs under.

    `HOME`/`USERPROFILE`/`XDG_CONFIG_HOME` are left alone on purpose. They are
    not git variables, stripping them changes how git resolves a dozen unrelated
    things, and the only ignore surface they reach -- `~/.config/git/ignore` via
    the `core.excludesFile` default -- is already disabled by `GIT_CONFIG_PIN`.
    """
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("GIT_") or k in GIT_ENV_KEEP}
    env["GIT_CONFIG_GLOBAL"] = str(_ABSENT_GIT_CONFIG)
    env["GIT_CONFIG_SYSTEM"] = str(_ABSENT_GIT_CONFIG)
    env["GIT_CONFIG_NOSYSTEM"] = "1"   # the pre-2.32 spelling of half of it
    return env


#: A pattern line: not blank, not a comment. The stock `info/exclude` git writes
#: into every new repository is nothing but comments, so counting raw lines would
#: announce a live exclusion on every clone in existence and the note would mean
#: nothing. What is worth announcing is somebody having added a rule.
_EXCLUDE_PATTERN = re.compile(r"^\s*(?!#)\S")


def _local_exclude_note() -> str | None:
    """`$GIT_COMMON_DIR/info/exclude`, announced rather than obeyed or refused.

    This is the half of the ignore-config hole that cannot be closed: unlike
    `core.excludesFile` it is not config, so no environment variable disables it.
    A single untracked line here silences the content scans for a path on this
    clone alone -- it is per-repository, it is not in the tree, and nothing in a
    review would show it. So the note says it is there and how many rules it
    holds. Not a failure: these patterns are ordinary, and this repository's own
    are editor and harness state. (No count in this sentence: the first draft said
    "eleven" where the file held ten and the gate printed ten, which is a poor
    look in a docstring about counting.) A reader who sees a surprising number has
    the one place to look, which is all this can honestly offer."""
    git = shutil.which("git")
    if git is None:
        return None
    try:
        r = subprocess.run([git, "--no-optional-locks", *GIT_CONFIG_PIN,
                            "rev-parse", "--git-common-dir"],
                           cwd=str(HERE), env=_git_env(), text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=GITIGNORE_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if r.returncode != 0 or not r.stdout.strip():
        return None
    common = Path(r.stdout.strip())
    if not common.is_absolute():
        common = HERE / common
    exclude = common / "info" / "exclude"
    try:
        body = exclude.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    n = sum(1 for line in body.splitlines() if _EXCLUDE_PATTERN.match(line))
    if not n:
        return None
    return (f"  note: $GIT_COMMON_DIR/info/exclude carries {n} pattern line(s). "
            f"It is untracked and per-clone, no config setting disables it, and "
            f"anything it ignores drops out of the counts below on this machine "
            f"only -- announced, not failed on")


def _gitignored(paths: list[Path]) -> tuple[set[Path], str | None]:
    """Which of `paths` git would refuse to publish -- in **one** batched call.

    This is the scope of check D, and it is a claim about publication, not about
    tidiness. `CLAUDE.md` grounds this whole check in the Phase 4 release
    manifest publishing every *tracked* file; a gitignored path is not in that
    manifest and never will be, so scanning it can only produce findings nobody
    can act on. It produced exactly that: `.pytest_cache/v/cache/nodeids` is
    pytest's own record of this gate's negative-control test *names*, which spell
    out deliberately fake credentials, so check D went red on its own fixtures
    and stayed red on every machine where anyone had ever run the suite -- the
    cache regenerates, so there was no fixing it in the tree. Twice over, this
    file records why that ending is fatal: a gate that is permanently red is a
    gate somebody switches off, and a leak detector that cries wolf at its own
    test names is one nobody believes on the day it is right.

    Three things this deliberately is not:

    * **not a path allowlist.** `.pytest_cache` is nowhere in this function. The
      rule is "git will not publish this", and a named exemption would be a
      declared place to hide a key from all three scans -- the same hole the
      negative-control suite refused to open for its own filename.
    * **not a narrowing of *untracked*.** Untracked-but-not-ignored files stay in
      scope. `git check-ignore` consults the index, so a tracked file is never
      reported here even when a pattern matches it; and an untracked file that
      nothing ignores is one `git add` away from the manifest, which is precisely
      the moment this check exists for.
    * **not trusted to fail closed.** Every failure mode -- no git, no
      repository (a release tarball has no `.git`), a non-{0,1} exit, a timeout,
      or output this function cannot map back onto its own input -- returns an
      empty set and a reason. The caller then scans everything and says so. A
      check that silently shrinks its own scope is the defect one rung down from
      the one this fixes.
    * **not the reader's `.gitconfig`, and not the caller's environment.**
      `GIT_CONFIG_PIN` puts `core.excludesFile=` on the command line, above every
      config file and above git's own `~/.config/git/ignore` default; `_git_env()`
      deletes every `GIT_*` variable that is not on a two-entry keep-list, so
      neither `GIT_INDEX_FILE` nor anything else can redirect the index, the work
      tree or the ignore list. Only the repository's own `.gitignore` and index
      decide, plus `$GIT_COMMON_DIR/info/exclude`, which no setting can disable
      and which `_local_exclude_note()` therefore announces instead.

    Returns `(ignored, unavailable)`; `unavailable` is None when the answer can
    be trusted, otherwise a short phrase naming why it cannot.
    """
    if not paths:
        return set(), None
    git = shutil.which("git")
    if git is None:
        return set(), "git is not on PATH"
    # Relative to HERE and NUL-delimited: `-z --stdin` echoes back the pathnames
    # verbatim, so the reply maps onto the request by string identity. One call,
    # not one per file -- there are hundreds under here once figures and runs are
    # counted, and a per-file subprocess is a check nobody waits for.
    index: dict[str, Path] = {}
    for p in paths:
        try:
            index[p.relative_to(HERE).as_posix()] = p
        except ValueError:
            continue
    if not index:
        return set(), None
    payload = b"\0".join(k.encode("utf-8") for k in index) + b"\0"
    try:
        # `--no-optional-locks` so a read-only check never writes a refreshed
        # index; the in-memory index is still consulted, which is what keeps a
        # force-added file in scope.
        r = subprocess.run([git, "--no-optional-locks", *GIT_CONFIG_PIN,
                            "check-ignore", "-z", "--stdin"],
                           input=payload, cwd=str(HERE), env=_git_env(),
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=GITIGNORE_TIMEOUT)
    except subprocess.TimeoutExpired:
        return set(), f"git check-ignore did not finish in {GITIGNORE_TIMEOUT}s"
    except OSError as exc:
        return set(), f"git check-ignore could not be run ({type(exc).__name__})"
    # 0 = some path is ignored, 1 = none is. Anything else is an error, and 128
    # is the ordinary one: not a git repository, which is what an unpacked
    # release tarball looks like.
    if r.returncode not in (0, 1):
        return set(), f"git check-ignore exited {r.returncode} (no usable ignore list)"
    ignored = {index[name] for name in r.stdout.decode("utf-8", "replace").split("\0")
               if name in index}
    if r.returncode == 0 and r.stdout and not ignored:
        # git answered, and none of the answer is recognisable as something that
        # was asked. Rather than conclude "nothing is ignored" from a reply this
        # function failed to read, widen.
        return set(), "git check-ignore output did not match the paths submitted"
    return ignored, None


def check_nosecret() -> tuple[bool, list[str]]:
    """D. No credential value anywhere under this directory.

    Three mechanisms, reported separately, because the one this check was built
    on does not run where it matters. The exact-value scan compares published
    files against `ROOT/.env` -- and `.env` is gitignored, so it does not exist
    in the worktree `monitor/ci_merge.py` checks out. The secret list came back
    empty, the loop iterated zero times, and the check returned True with the
    note "no .env present to check against (nothing to leak)". That sentence was
    false in the only direction that matters: nothing had been checked. A file
    holding an ARC-key-shaped value passed `[PASS] D NOSECRET`, `PASS (6/6)`,
    exit 0 on any fresh checkout -- and `CLAUDE.md` makes this Phase 1 sealing
    discipline and notes that the Phase 4 release manifest publishes every
    tracked file, so the verdict this check exists to give was never given on a
    tree anybody would publish.

    The two added mechanisms need no untracked file, so they run in CI, on a
    fresh clone, and against a release tarball:

    * a **credential-named assignment** carrying a substantial value, whatever
      its shape -- the mechanism that catches the next secret, which will not
      be a UUID;
    * a **key-shaped token in a credential context** -- the promise in this
      module's docstring, finally executed.

    The exact-value scan is kept and still runs when `.env` is present, because
    it is the only one of the three that recognises *this* key with no false
    positives at all. It is now reported as what it is: a bonus available on the
    author's machine, not the floor.

    **Scope: what git would publish, and nothing dropped off the books.** Every
    file under this directory lands in exactly one of three buckets -- scanned,
    skipped as gitignored, or unreadable -- and every non-zero bucket is printed,
    with the directories the skipped files came from. There is no name-based
    exemption. `__pycache__` used to be one, and it was the worst kind: eleven
    files on the live tree dropped by `"__pycache__" not in p.parts`, reported in
    no number, while `git check-ignore` says git does *not* consider a tracked one
    ignored -- so `release/enumerate.py`'s `git ls-files` would have put a tracked
    `__pycache__/leak.txt` straight into `MANIFEST.jsonl` past a green gate, and a
    tracked `__pycache__/.env` past the filename tripwire too. `_gitignored`'s own
    docstring forbids exactly that eight lines above where the caller did it.
    Bytecode is skipped now only because git ignores it, which is the general rule
    doing the work, and it is counted when it is.

    Untracked-but-not-ignored files are in scope on purpose -- they are one
    `git add` from the manifest. When the ignore list cannot be obtained the scan
    widens to everything and the note says so. `MIN_SCANNED` is the floor under
    all of it: a scan that collapses reports a broken check, never a clean tree,
    because "returned True having examined nothing" is the original defect and an
    ignore filter is a second route to it.
    """
    notes: list[str] = []
    env = ROOT / ".env"
    secrets = []
    if env.exists():
        for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                value = line.split("=", 1)[1].strip().strip("'\"")
                if len(value) >= MIN_SECRET_LEN:
                    secrets.append(value)

    # Every file, with no name-based exemption: what is dropped is dropped by
    # `_gitignored` and counted where it is dropped.
    candidates = [p for p in sorted(HERE.rglob("*")) if p.is_file()]
    ignored, unavailable = _gitignored(candidates)
    if unavailable:
        notes.append(f"  ignore-filtering unavailable ({unavailable}): scan WIDENED "
                     f"to every file under this directory, gitignored or not")
    else:
        # Only worth announcing when the filter is actually in play: a widened
        # scan obeyed no ignore rule, so there is nothing for `info/exclude` to
        # have hidden.
        local = _local_exclude_note()
        if local:
            notes.append(local)

    hits: list[str] = []
    scanned = 0
    skipped = 0
    unreadable: list[str] = []
    skipped_under: dict[str, None] = {}   # insertion-ordered set, for the note
    for path in candidates:
        # `relative_to` raises when ROOT is not an ancestor -- which it always is
        # in production and was not under a probe that redirected only ROOT. The
        # finding is worth more than the tidy path: a leak detector that raises
        # while naming the file it caught has caught nothing anybody will read.
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            rel = path
        # A .env here is the leak itself, whatever is in it -- and this one
        # mechanism runs *before* the ignore filter, on every file. Root
        # `.gitignore` ignores `.env` and `.env.*` by design, so filtering this
        # by publication status would have quietly retired the tripwire: drop a
        # real `.env` into this directory and the gate would have gone green on
        # the one filename it is named after. Skipping a gitignored file is a
        # judgement about *publication*; a credential file sitting in the
        # publication directory is a finding about the *machine*, and those are
        # not the same claim. Widening here can only add findings.
        if path.name == ".env" or path.name.startswith(".env."):
            if path.name != ".env.example":
                hits.append(f"  a .env file is published at {rel}")
        if path in ignored:
            skipped += 1
            # Where the skipping happened, not just how much of it. A count alone
            # cannot distinguish "the caches were skipped" from "a directory of
            # the paper was", and the second is a scope regression a reader has to
            # be able to see in the note. The *containing directory*, not the first
            # path component: with `__pycache__` no longer exempt the skipped set
            # spans several of them, and a first-component label reads
            # "skipped under figures/" when what was skipped is
            # `figures/__pycache__/`. A file directly under HERE is labelled `./`,
            # because the first draft labelled it with its own filename and the
            # note could read "skipped as gitignored under leak_global.txt".
            try:
                parent = path.relative_to(HERE).parent
            except ValueError:
                parent = path.parent
            skipped_under[("." if parent == Path(".") else parent.as_posix())
                          + "/"] = None
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            # Neither scanned nor skipped-as-gitignored, and before this it was in
            # no bucket and no number at all: 165 + 5 printed against 181 files on
            # disk. An unreadable file in a credential audit is a gap in the audit
            # and gets its own line.
            unreadable.append(str(rel))
            continue
        scanned += 1
        for value in secrets:
            if value in text:
                # Never print the value.
                hits.append(f"  a .env value appears in {rel}")
        for detail in _assignment_hits(text):
            hits.append(f"  {rel}: {detail}")
        for lineno, line in enumerate(text.splitlines(), 1):
            if _shaped_in_context(line):
                hits.append(f"  {rel}: line {lineno}: an ARC-key-shaped token "
                            f"sits within {CONTEXT_WINDOW} characters of a "
                            f"credential word")
                break

    # The floor, and it is reported as a hit so that a collapsed walk can never
    # end in a green -- not even a green carrying a small number nobody read. The
    # message names itself a broken check, because "0 files scanned" is not
    # evidence about the tree and must not be filed as though it were: the
    # original defect here was a clean verdict issued over an empty loop, and
    # somebody reading this line as a leak report would be making the mirror-image
    # mistake. Placed after the content scan so that a real finding in a truncated
    # tree is still reported alongside it, rather than replaced by it.
    if scanned < MIN_SCANNED:
        hits.append(f"  BROKEN CHECK, not a leak: only {scanned} file(s) were "
                    f"scanned under {HERE.name}/ and this check is meaningless "
                    f"below {MIN_SCANNED} (`MIN_SCANNED`). Nothing here is a "
                    f"finding about the tree -- the scan did not happen. Look at "
                    f"whether the directory is the right one, whether it unpacked, "
                    f"and at the {skipped} file(s) skipped as gitignored")

    if hits:
        notes.extend(fail(h) for h in dict.fromkeys(hits))
        return False, notes

    # The note states which mechanisms ran, and says so out loud when the
    # exact-value scan did not. "Nothing to leak" was the old sentence and it
    # asserted a check that had not executed.
    #
    # The three buckets partition `candidates`, the arithmetic is printed so a
    # reader can check that they do, and every non-zero one is named. The previous
    # note printed two numbers that did not add up to the tree -- 165 scanned plus
    # 5 skipped against 181 files -- with eleven dropped by a name-based exemption
    # and the remainder by an `except OSError: continue` above the counter. Numbers
    # that do not close are how a scope hole hides in plain sight on a green line.
    where = (" under " + ", ".join(sorted(skipped_under))) if skipped_under else ""
    buckets = [f"{scanned} scanned", f"{skipped} skipped as gitignored{where}"]
    if unreadable:
        buckets.append(f"{len(unreadable)} UNREADABLE and therefore not scanned "
                       f"({', '.join(sorted(unreadable))})")
    notes.append(f"  {scanned} published file(s) scanned: no credential-named "
                 f"assignment, no key-shaped token in a credential context")
    notes.append(f"  all {len(candidates)} file(s) under this directory accounted "
                 f"for = " + " + ".join(buckets))
    notes.append(f"  {len(secrets)} .env value(s) also compared byte-for-byte: absent"
                 if secrets
                 else "  exact-value scan SKIPPED: no .env in this tree (gitignored, "
                      "so absent in CI and in any fresh clone). The two shape- and "
                      "name-based scans above carry this check on their own; that "
                      "is the point of them")
    return True, notes


# ---------------------------------------------------------------- E. UNCITED

# The abstract is the paper's one declared exemption, stated in its own front
# matter ("**The abstract is the one exemption, by convention**"), and it holds
# only because every figure in it recurs, cited, in the body. Failing it would
# put ~40 unfixable flags on every run, and a gate that is permanently red is a
# gate somebody switches off -- which is how the rule would lose its executor a
# second time.
EXEMPT_SECTIONS = {"00_abstract.md"}

# A citation, here, is a backticked token that *points at an artefact* -- it has
# a directory separator, or a filename with an artefact extension. Whether the
# pointer resolves is check B's question, deliberately not this one: B already
# reports BROKEN and AMBIGUOUS, and folding that in would make one red mean two
# unrelated defects. E asks only whether the author pointed at anything.
#
# The split matters for the bare-filename citations CITECHECK counted -- section
# 10 cites `SURVEY-solver-status.md:16`, which exists but not at a path a reader
# resolves. That is a style finding B owns; calling it "uncited" would be false.
# The trailing `:170-171` is a line anchor, not part of the name -- and it is
# captured rather than discarded, because 14 of the paper's 22 line-anchored
# citations are bare filenames, which check B never sees. A range check wired
# into B alone would cover 8 of 22.
CITE_TOKEN = re.compile(
    r"`([A-Za-z0-9_.\-/{},]+)(?::(?P<anchor>\d+(?:[-–]\d+)?))?`")
ARTEFACT_SUFFIX = (
    ".md", ".json", ".jsonl", ".py", ".lean", ".dsl", ".bib",
    ".csv", ".svg", ".txt", ".toml", ".yaml", ".yml", ".sh",
    # A citation of a real artefact type that was not on this list did not read
    # as a citation, so a properly-cited claim was flagged. A gate with false
    # positives is a gate that gets switched off, and these are all real kinds
    # of artefact in this tree. Widening still costs the inventor something:
    # `_basename_exists` requires the file to be there.
    ".log", ".png", ".pdf", ".tex", ".tsv", ".ipynb", ".pddl", ".lock",
)

# Token classes that carry a digit without asserting a quantity. Each is named
# and narrow rather than one permissive regex, on `engine-rig`'s rule for the
# same problem: exempt by *class*, so widening the exemption is a line somebody
# adds and can be argued with, not a quietly loosened character range.
STRUCTURAL = (
    ("section-ref", re.compile(r"§\s*\d+(?:\.\d+)*[a-z]?")),
    ("section-word", re.compile(
        r"\b(?:Sections?|Parts?|constraints?|steps?|beats?|rungs?|layers?|waves?"
        r"|checks?|passes|rounds?|items?|levels?)"
        r"\s+\d+(?:\s*(?:,|and|to|[-–])\s*\d+)*", re.IGNORECASE)),
    ("figure-ref", re.compile(r"\b(?:Figure|Fig\.|Table|Plate|Appendix)\s+\d+\b")),
    ("phase-ref", re.compile(r"\bPhase\s+\d\b")),
    ("arc-agi", re.compile(r"\bARC-AGI-\d\b")),
    ("version", re.compile(r"\bv\d+(?:\.\d+)*\b")),
    ("lean-version", re.compile(r"\bLean\s+\d+(?:\.\d+)*\b")),
    ("timestamp", re.compile(r"\b20\d{6}T\d{6}Z\b")),
    ("iso-date", re.compile(r"\b20\d\d-\d\d-\d\d\b")),
    ("clock", re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")),
    # At least one a-f, or the class eats any 7-digit quantity -- "1750000
    # cache tokens" was read as a commit hash and vanished.
    ("commit-sha", re.compile(r"\b(?=[0-9a-f]{7,40}\b)[0-9a-f]*[a-f][0-9a-f]*\b")),
    ("digest-elision", re.compile(r"\b[0-9a-f]{6,}…(?:[0-9a-f]+)?")),
    # `E2`, `K12`, `P4`, `M3`, `X1`, `L1`, `C5`, `A0`, `T-10`, `D-B-011`,
    # `INC-BA-001`, `F-11`, `R-05`, `W-1660`. Identifiers, not measurements.
    ("id-code", re.compile(r"\b[A-Z]{1,4}(?:-[A-Z0-9]{1,4})*-?\d{1,4}[a-z′]?\b")),
    ("milestone", re.compile(r"\bm[0-9]\b")),
    # Grid cells and Lean tuples: (2, 4) is a position, not a measurement.
    ("coordinate", re.compile(r"\(\s*-?\d+\s*,\s*-?\d+\s*\)")),
    # `[7, 0, 0, 0, 0, 0, 0]`, `[-1, 1, 0, 1, -1]` -- quoted payloads.
    ("vector", re.compile(r"\[\s*-?\d+(?:\s*,\s*-?\d+)+\s*\]")),
    # Binary configuration labels (`11011`) are exempted in `_mark_citations`,
    # where the backticks that make them labels are still visible. As a bare
    # STRUCTURAL class it also ate "a hard cap of 10000 actions".
    ("complexity", re.compile(r"O\(\s*[0-9a-z^ⁿ²³]+\s*\)")),
    ("superscript-pow", re.compile(r"\b\d+[⁰-₟²³¹]+")),
    ("list-ordinal", re.compile(r"^\s*\d+\.\s", re.MULTILINE)),
    # `(?<![\w'’])` and a required `=`: the bare `\b` matched the `t` in a
    # contraction, so "the regression wasn't 40 percent" was read as frame
    # index 40 and disappeared. `t 40` was never the notation anyway; `t=40` is.
    ("frame-index", re.compile(r"(?<![\w'’])t\s*=\s*\d+\b")),
)

# Digits, including the paper's space-grouped thousands (`22 356`, `116 470`).
DIGIT = re.compile(
    # A leading-dot decimal is a quantity and was unreachable: the `(?<![\w.])`
    # lookbehind blocked the digit after the dot, and every later digit was
    # blocked by the digit before it. `.562` and `p = .003` are the standard
    # way to write an effect size, so that whole register was invisible.
    r"\.\d+(?![\w.])"
    r"|(?<![\w.])\d[\d  ]*(?:[  ]\d{3})*(?:\.\d+)?")

#: A number carrying a unit: `41s`, `1.4GB`, `4.7x`, `3pp`. Alphanumeric, so
#: `_mark_citations`'s name branch used to erase it whole.
MEASURED = re.compile(r"\d+(?:\.\d+)?\s?[A-Za-z%]{1,4}")

# Spelled-out cardinals. `one`..`ten` are excluded: 608 of the 805 spelled-out
# numbers in the sections are those words used as determiners ("one further
# finding", "the two tracks"), so flagging them would bury the check in noise.
# From `eleven` up, and `zero`, the word is almost always load-bearing -- and
# `zero` carries several of the paper's most important negative results
# ("moved the unvalidated count by **zero**"). This is also the hole the item's
# adversarial step names: writing 37 as "thirty-seven" must not buy an evasion.
# `(?<!non-)` because "three non-zero values exist in the tree" asserts the
# absence of a quantity, not one. The bare `\b` fired after the hyphen.
WORDNUM = re.compile(
    r"(?<!non-)\b(?:zero|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|"
    r"hundred|thousand|million)(?:-(?:one|two|three|four|five|six|seven|eight|"
    r"nine))?\b"
    # Magnitude language is a quantitative claim without a numeral, and it is
    # the natural register for an unfalsifiable improvement: "twice the ground,
    # an order of magnitude cheaper". A gate that only reads digits reads none
    # of it.
    r"|\b(?:twice|thrice|dozen|halved|doubled|tripled|quadrupled|"
    r"\w+fold|orders? of magnitude)\b"
    # Fractions and multipliers are the register a result slides into when it
    # has no artefact: "the bill fell by a factor of three", "half of them did
    # so without a repair pass", "coverage was double the baseline". None of it
    # contains a digit, and none of it was read. Free on the current draft --
    # this vocabulary adds zero flags to the 12 body sections.
    r"|\b(?:a half|halves|a third|two thirds|a quarter|three quarters|"
    r"doubles?|triples?|a factor of)\b",
    re.IGNORECASE,
)

# Chunks that continue the claim above them rather than starting a new one.
CONTINUES = re.compile(r"^\s*(?:\||[-*+]\s|\d+\.\s|>)")

#: `### 7.2a `, `## 10 ` -- a heading's own number, which is structure.
HEADNUM = re.compile(r"^\s*#+\s*\d+(?:\.\d+)*[a-z]?\s*")

#: Quantitative blocks that have been looked at and ruled not to need a path,
#: each with the ruling. Keyed by (section, a verbatim anchor from the block) so
#: that rewriting the claim retires its exemption and forces a fresh ruling --
#: an exemption that outlives the sentence it was written for is an exemption
#: nobody re-read.
#:
#: A block NOT in this table fails, because it is new and nobody has ruled on
#: it. A block in it prints its ruling on every run. An entry that matches
#: nothing also fails, as STALE: `figures/reconcile_cost.py`'s rule, that a
#: declaration which has stopped being true is removed rather than left to
#: excuse a regression that comes back the other way.
ADJUDICATED_UNCITED: dict[tuple[str, str], str] = {
    ("01_intro.md", "falsified 17 of its own author's written claims"):
        "§1.2 states and cites this same contradicted-entry count "
        "(`battery/artifacts/gaming_audit.json`, `n_disagreements`), and the "
        "frozen-baseline paragraph below records that a rerun now gives 19. A "
        "summary sentence repeating the path would be noise, not provenance.",
    ("03_a0.md", "that it held on every one of the 275"):
        "The support count is stated and cited two lines above, in the block "
        "quoting `cold-start-a0/THEORIZE_LOG.md` L-02. This block draws the "
        "empirical-regularity-versus-proof distinction from it and introduces "
        "no new measurement.",
    ("07_battery.md", "every δ here is a multiple of 1/16"):
        "δ is (#greater − #less) over the 4 × 4 cross-arm pairs "
        "(`battery/audit/stats.py`), so the 1/16 grid and its reachable-value "
        "count are arithmetic on the n = 4 stated in this same block. −0.562 "
        "and −0.188 restate rows of §7.2's table, whose preamble cites "
        "`battery/artifacts/discrimination_arms.json`.",
    ("07_battery.md", "bill shape's distribution rests on 67 runs"):
        "A one-sentence restatement of the E2 distribution established four "
        "lines above, where it carries `battery/artifacts/capability_spectrum.json`, "
        "set against the empty capability column §7.10a evidences from "
        "`baseline-arms/runs/20260728T103135Z-a7/envelope.json`.",
    ("08_exam.md", "the 0.000 that could be computed from two"):
        "The arithmetic this paragraph explicitly declines to report as a "
        "measurement. Both artefacts it would be computed from are cited one "
        "block above, and each records `tier2_minus_tier1` as null rather than "
        "a delta; a path here would point at a number the paper is refusing.",
    ("08_exam.md", "**n = 1 per handover tier**, on a saturated"):
        "Restates the sample size of the handover result cited one block above "
        "(one report per tier, both named there). This bullet list is the "
        "section's statement of what the exam does not establish.",
    ("10_adjudication.md", "around 340 points examined, 48 judged unsafe"):
        "The headline is quoted in order to be refused, and the four numbered "
        "reasons that follow are the argument that no aggregate over these "
        "passes exists. Every row of the table two blocks above carries its own "
        "survey file. Attaching provenance would dignify a number the section "
        "declines to publish.",
    ("07_battery.md", "and the main table moved twice"):
        "A heading, summarising the two moves the block below states and cites: "
        "19 -> 6 on demonstration and 6 -> 9 after four defences "
        "(`battery/artifacts/gaming_audit.json`, with the intermediate 6 "
        "attributed to `battery/REPORT_V2.md`). Twice is scoped to this "
        "subsection; the further 9 -> 2 -> 0 is 7.7a's blind round and is "
        "counted there, which is why a reader tallying both sections gets four.",
    ("09_preflight.md", "a preflight for zero quota"):
        "A section title. `zero quota` names the thing the section is about -- a "
        "run staged so that no step could cost anything -- and 9.4 is where the "
        "spend is reported and carries the manifest. A title is not the place "
        "the claim is established.",
    ("10_adjudication.md", "the disputed 340 / 48 with an enumerated"):
        "Two aggregates named in order to retract them -- one the census's, one "
        "this section's own superseded draft -- both sums over the per-pass "
        "table above, where each row carries its survey file. Nothing in this "
        "block is asserted as a count of anything.",
}


def _blocks(text: str):
    """Yield (line_no, block_text) claim blocks.

    A claim block is a blank-line-separated chunk, with any table, list or
    blockquote chunk merged into the prose chunk above it. That is how this
    paper cites: the sentence introducing a table carries the artefact path and
    the rows carry the values. Scoring rows independently would flag ~70 of them
    whose citation sits two lines up, and the adjudication table would become a
    rubber stamp -- which is the failure mode this check is supposed to avoid,
    not reproduce.
    """
    out: list[list] = []
    chunk: list[str] = []
    start = 1
    in_fence = False
    for i, line in enumerate(text.splitlines(), 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            if chunk:
                _emit(out, start, chunk)
                chunk = []
            if line.lstrip().startswith("#"):
                # A heading is scored as a block of its own. It used to be
                # `continue`d past without its text ever being emitted, so
                # "## Repair recovers 38 percent of failed arms" was a result
                # stated where nothing looked. Its own section number is
                # stripped first: `### 7.2a ...` is structure, and leaving it
                # in flagged all 87 headings on the count of being numbered.
                head = HEADNUM.sub("", line).strip()
                if head:
                    out.append([i, head])
                # The trailing sentinel still matters when a heading is *only*
                # a number, because then there is no heading block to stand
                # between the sections and a table would inherit the last
                # section's citation.
                out.append(None)  # a heading breaks the merge chain
            continue
        if not chunk:
            start = i
        chunk.append(line)
    if chunk:
        _emit(out, start, chunk)
    return [b for b in out if b is not None]


def _emit(out: list, start: int, chunk: list[str]) -> None:
    text = "\n".join(chunk)
    if CONTINUES.match(chunk[0]) and out and out[-1] is not None:
        out[-1][1] += "\n" + text
        return
    out.append([start, text])


_BASENAMES: dict[str, list[str]] | None = None

#: Directories that are not the published tree: other agents' checkouts, build
#: output, caches. A basename that is "ambiguous" only because it also appears
#: in a sibling worktree is not ambiguous to a reader of the repository.
_WALK_SKIP = {
    ".git", "__pycache__", ".worktrees", ".toolchain", "node_modules",
    ".claude", ".pytest_cache", ".venv", "node_modules", ".mypy_cache",
}


def _candidates(token: str) -> list[str]:
    """Every repo-relative path whose basename is this token.

    Check F needs the count, `_basename_exists` needs only whether it is
    non-empty, and walking the tree twice for that was silly.
    """
    global _BASENAMES
    if _BASENAMES is None:
        _BASENAMES = {}
        for path, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in _WALK_SKIP]
            for f in files:
                rel = os.path.relpath(os.path.join(path, f), ROOT)
                _BASENAMES.setdefault(f, []).append(rel.replace("\\", "/"))
    return _BASENAMES.get(token.rsplit("/", 1)[-1], [])


def _basename_exists(token: str) -> bool:
    """Is there a file by this name anywhere in the tree?

    A bare filename is the paper's dominant citation idiom and check B skips it
    by design, so `(`ledger_summary.jsonl`)` -- a plausible name for a file that
    does not exist -- was a citation *nobody* checked: E accepted the suffix and
    B never saw the token. This is the weakest test that still costs an inventor
    something, and it is free: all 34 distinct bare filenames the sections cite
    exist by basename. Check F is the stronger test on the same tokens: existing
    is not the same as being findable.
    """
    return bool(_candidates(token))


def _mark_citations(block: str) -> str:
    """Replace artefact pointers with a sentinel and strip structural tokens."""

    def mark(m: re.Match) -> str:
        token = m.group(1)
        # `233/236` has a slash and is a ratio, not a path. Check B already
        # knows this (NOT_A_PATH); without the same exclusion here a backticked
        # fraction cited *itself* as its own provenance and cleared the block.
        if not NOT_A_PATH.search(token):
            if "/" in token:
                return " █CITE█ "
            if token.lower().endswith(ARTEFACT_SUFFIX) and _basename_exists(token):
                return " █CITE█ "
        # A backticked token with letters in it is a name -- `cost.delta_usd`,
        # `stub-bfs`, `Step.won` -- and names are not quantities. But a
        # *measurement with a unit* is also alphanumeric, and this branch was
        # deleting it outright: `41s`, `1.4GB`, `4.7x`, `3pp` all vanished, and
        # backticked values are one of the paper's own idioms.
        if MEASURED.fullmatch(token):
            return f" {token} "
        if any(c.isalpha() for c in token):
            return " "
        # `11011` is a configuration label; the backticks are what make it one.
        # Exactly five, because the A0 board is five cells and every label the
        # sections carry is five wide (`00001` `00010` `00100` `01000` `10000`
        # `11011`). `{5,}` also exempted `100000` and `1000000` -- powers of ten
        # are all 0s and 1s, and they are exactly the context-budget numbers this
        # paper quotes. Residual, stated because it cannot be fixed here:
        # `10000` is a genuine label on this board, so a backticked ten thousand
        # is indistinguishable from it. Write that one unbackticked.
        if re.fullmatch(r"[01]{5}", token):
            return " "
        # A backticked *number* is still a quantity; backticks are not a
        # citation, and letting them hide one would be a one-character evasion.
        return f" {token} "

    text = CITE_TOKEN.sub(mark, block)
    for _name, rx in STRUCTURAL:
        text = rx.sub(" ", text)
    return text


def _quantities(block: str) -> tuple[list[str], list[str]]:
    """(digit tokens, spelled-out tokens) that are not citations or structure."""
    text = _mark_citations(block)
    if "█CITE█" in text:
        return [], []
    return DIGIT.findall(text), WORDNUM.findall(text)


def coverage_uncited(sections=None) -> tuple[int, int, list[tuple]]:
    """How much weaker than the rule this check is, as a number.

    A single citation clears its whole block, so the check licenses blocks in
    which one path stands behind many quantities. Usually that is correct -- the
    41 values in section 7's effect-size table all come from the one artefact
    its preamble names -- but "usually" is not a guarantee, and the ratio is the
    honest measure of the gap between what E proves and what the binding rule
    asks. It is reported rather than gated on, because there is no threshold
    here anybody has calibrated.
    """
    sections = SECTIONS if sections is None else Path(sections)
    blocks, quantities, worst = 0, 0, []
    for section in sorted(sections.glob("*.md")):
        if section.name in EXEMPT_SECTIONS:
            continue
        for lineno, block in _blocks(section.read_text(encoding="utf-8")):
            marked = _mark_citations(block)
            if "█CITE█" not in marked:
                continue
            n = len(DIGIT.findall(marked)) + len(WORDNUM.findall(marked))
            if not n:
                continue
            blocks += 1
            quantities += n
            worst.append((n, marked.count("█CITE█"), section.name, lineno))
    worst.sort(reverse=True)
    return blocks, quantities, worst[:5]


def scan_uncited(sections=None, rulings=None):
    """(flagged, hits, scanned) over a sections directory.

    Split out from `check_uncited` so the negative control can drive it with a
    scratch tree: a gate nobody has watched fail is a gate nobody has reason to
    trust, and every other pin in this repository carries such a control.
    """
    sections = SECTIONS if sections is None else Path(sections)
    rulings = ADJUDICATED_UNCITED if rulings is None else rulings
    flagged: list[tuple[str, int, str, list[str], list[str]]] = []
    hits: dict[tuple[str, str], int] = {k: 0 for k in rulings}
    scanned = 0

    for section in sorted(sections.glob("*.md")):
        if section.name in EXEMPT_SECTIONS:
            continue
        for lineno, block in _blocks(section.read_text(encoding="utf-8")):
            scanned += 1
            nums, words = _quantities(block)
            if not nums and not words:
                continue
            flat = " ".join(block.split())
            ruled = next(
                (k for k in rulings if k[0] == section.name and k[1] in flat), None
            )
            if ruled:
                hits[ruled] += 1
                continue
            flagged.append((section.name, lineno, flat, nums, words))
    return flagged, hits, scanned


#: An anchor shorter than this is not identifying a claim, it is matching prose.
#: The adversarial pass turned the whole check green with a one-space anchor:
#: `" "` is in every block, so one entry silenced the paper and reported no
#: stale rulings. The eight live anchors are 34-47 characters, so the floor is
#: free -- but the escape hatch was one character wide and nothing said so.
MIN_ANCHOR = 24


def check_uncited() -> tuple[bool, list[str]]:
    """E. No quantitative claim block in the body cites nothing at all."""
    notes: list[str] = []
    flagged, hits, scanned = scan_uncited()
    stale = [k for k, n in hits.items() if not n]

    # A ruling that silences more than one block is as wrong as one that
    # silences none, and the length floor does not catch it: the adversarial
    # pass silenced three distinct uncited blocks with a 47-character anchor
    # ("the numbers in this paragraph come from the run") and reported nothing
    # stale. A ruling is written about *a* claim, so it must match one.
    for key, n in hits.items():
        if n > 1:
            notes.append(fail(
                f"  BROAD     {key[0]} → {key[1]!r} matches {n} blocks. "
                f"A ruling is written about one claim; matching several means it "
                f"is silencing blocks nobody ruled on."))
            stale.append(key)

    for key in ADJUDICATED_UNCITED:
        if len(key[1]) < MIN_ANCHOR:
            notes.append(fail(
                f"  ANCHOR    {key[0]} → {key[1]!r} is {len(key[1])} characters. "
                f"An anchor under {MIN_ANCHOR} matches prose rather than a claim, "
                f"and silences blocks nobody ruled on."))
            stale.append(key)
    for section in sorted(SECTIONS.glob("*.md")):
        # Count fences with the block splitter's own predicate. `count("\n```")`
        # misses a fence on line 1 -- which inverted the verdict exactly: a
        # balanced section opening with a fence failed, and an unbalanced one
        # opening with a fence passed.
        fences = sum(
            1 for line in section.read_text(encoding="utf-8").splitlines()
            if line.strip().startswith("```"))
        if fences % 2:
            notes.append(fail(
                f"  FENCE     {section.name} has an odd number of ``` lines. "
                f"Everything after the unclosed one is skipped as code, so a "
                f"claim can hide behind it."))
            stale.append((section.name, "unbalanced fence"))
    # `len(glob) - len(EXEMPT_SECTIONS)` printed `-1 body sections` on an empty
    # tree, and printed it on a PASS line. Counting what was actually walked
    # cannot go negative, and cannot disagree with the loop above it.
    notes.append(
        f"  {scanned} claim blocks scanned across {len(body_sections())} "
        f"body sections: {len(flagged)} uncited, "
        f"{len(ADJUDICATED_UNCITED) - len(stale)} ruled, {len(stale)} stale rulings"
    )
    for name, lineno, flat, nums, words in flagged:
        tokens = ", ".join(nums[:6] + words[:3]) or "?"
        notes.append(fail(
            f"  UNCITED   {name}:{lineno} -- quantities [{tokens}] with no "
            f"resolvable path anywhere in the block"))
        notes.append(fail(f"            {flat[:140]}"))
    for key, reason in ADJUDICATED_UNCITED.items():
        if key in stale:
            notes.append(fail(
                f"  STALE     {key[0]} → {key[1]!r} matched no block. The claim it "
                f"ruled on was rewritten or removed; drop the entry rather than "
                f"leave it to excuse the next one."))
        else:
            notes.append(f"  ruled     {key[0]} ({hits[key]}×) -- {reason}")
    return not (flagged or stale), notes


#: Bare filenames that name a *kind* of file rather than one artefact, each with
#: the reason. Keyed by (section, token). Same discipline as the other two
#: adjudication tables: the reason prints on every run, and an entry that
#: matches nothing fails as stale.
ADJUDICATED_BARE: dict[tuple[str, str], str] = {
    ("02_framework.md", "playbook.dsl"):
        "Names the *form*, not an instance: the parenthetical points at "
        "`CONTRACTS/dsl_grammar_v0.1.md`, which itself uses the bare name for "
        "the form (its four sentence types). The contrast is deliberate four "
        "lines up, where the manual does get an instance and a scope -- "
        "`cold-start-a0/theory/theory.dsl` for A0.",
    ("02_framework.md", "THEORIZE_LOG.md"):
        "Indefinite article, and the next sentence pluralises: 'written down "
        "by the LLM in a THEORIZE_LOG.md' / 'Those logs are the primary "
        "evidence'. It names the kind of file each arm keeps.",
    ("10_adjudication.md", "ground_truth.json"):
        "The token is what is being counted, not what is being cited: "
        "'`worldgen/out/worlds/` holds 35 directories with a "
        "`ground_truth.json`'. The directory carrying the claim is cited in "
        "full; naming one of the 35 would be wrong here.",
    ("11_limitations.md", "theory.dsl"):
        "A claim about the v0.1 grammar era, so about every manual written "
        "under it, and no single instance is meant. Ten `.dsl` files across "
        "four arms carry the comment this sentence is about; the two the "
        "section is discussing are `cold-start-a0/theory/theory.dsl:25` and "
        "`cold-start-a2/theory/theory.dsl:26`. (An earlier version of this "
        "ruling also named `a0-spike/theory/theory.dsl`, which carries the "
        "keyword bare and no comment at all -- a ruling whose stated evidence "
        "was false, and nothing here would have caught that.)",
}


def _split_siblings(token: str) -> list[str]:
    """`{a,b}` and `a,b` -> the names they stand for. Anything else, itself."""
    out = []
    for part in expand_braces(token):
        out.extend(p for p in part.split(",") if p)
    return out or [token]


def scan_bare(sections=None, rulings=None):
    """Bare-filename citations in the body, with how many files could be meant.

    Check B skips a token without a `/` by design -- it checks that cited
    *paths* resolve, and a bare filename is not a path. Check E accepts one if
    the basename exists anywhere in the tree. So `STATUS.md` is a citation that
    neither check really reads, and the paper's own rule says every citation is
    repo-relative. This is the executor for that half of the rule.

    A bare filename with exactly one candidate in the tree is *locatable*, which
    is what the rule is protecting, so it passes. The check is about ambiguity:
    `MANIFEST.json` matches 124 files and points a reader at none of them.
    """
    sections = SECTIONS if sections is None else sections
    rulings = ADJUDICATED_BARE if rulings is None else rulings
    hits = {k: 0 for k in rulings}
    flagged, seen = [], 0
    overran: list[tuple] = []
    for section in sorted(Path(sections).glob("*.md")):
        if section.name in EXEMPT_SECTIONS:
            continue
        for lineno, line in enumerate(
                section.read_text(encoding="utf-8").splitlines(), 1):
            for m in CITE_TOKEN.finditer(line):
                raw, anchor = m.group(1), m.group("anchor")
                if "/" in raw:
                    continue
                # `{STATUS.md}` and `STATUS.md,DECISIONS.md` both slipped: the
                # first fails the suffix test on its trailing brace, the second
                # is one token that names two files. Section 7 already cites
                # siblings as `{a0-base,a2-base}`, so this is the paper's own
                # idiom with the directory removed -- one keystroke away, not a
                # contrivance. `classify` normalises the same way for check B.
                for token in _split_siblings(raw):
                    if not token.lower().endswith(ARTEFACT_SUFFIX):
                        continue
                    seen += 1
                    cands = _candidates(token)
                    n = len(cands)
                    # A bare name with one candidate is locatable, which is all
                    # F asks -- and 14 of the paper's 22 line-anchored citations
                    # are exactly this shape, invisible to check B for having no
                    # `/`. Wiring the range check into B alone would have covered
                    # 8 of 22, so the other half lives here, where the file has
                    # already been resolved.
                    if n == 1 and anchor:
                        span = anchor_overruns(ROOT / cands[0], anchor)
                        if span is not None:
                            overran.append((section.name, lineno, token, anchor,
                                            cands[0], span))
                # `n == 1` is the only clean verdict. Zero is *worse* than many:
                # a bare name matching nothing is an invented citation, and it
                # was the one case this check waved through -- check B skips it
                # for having no `/`, and check E only catches it when the block
                # also carries a quantity, so a non-quantitative sentence citing
                # `ledger_summary.jsonl` was read by nobody at all. That is the
                # example `_basename_exists`'s own docstring gives as the hole.
                    if n == 1:
                        continue
                    key = (section.name, token)
                    if key in hits:
                        hits[key] += 1
                        continue
                    flagged.append((section.name, lineno, token, n))
    return flagged, hits, seen, overran


def check_bare() -> tuple[bool, list[str]]:
    """F. No body citation is a bare filename that could mean several files."""
    notes: list[str] = []
    flagged, hits, seen, overran = scan_bare()
    stale = [k for k, n in hits.items() if not n]

    # A ruling here is keyed by (section, token) with no text anchor, so unlike
    # check E's it cannot be scoped to one claim -- which means one entry
    # silences *every* use of that token in the section, including uses written
    # after it was ruled. The adversarial pass demonstrated it: a section with
    # one generic mention and three specific ones, the last brand new, passed
    # with a single ruling. E defends against exactly this with MIN_ANCHOR and
    # the BROAD rule; this table was ported without either guard.
    #
    # The count is the guard that fits a keyless table: a ruling says "this
    # token, in this section, is generic". If the token appears more than once
    # the sentences are no longer the one that was ruled on.
    for key, n in sorted(hits.items()):
        if n > 1:
            notes.append(fail(
                f"  BROAD     {key[0]} `{key[1]}` is ruled generic but appears "
                f"{n} times. A ruling with no text anchor cannot tell the "
                f"sentence it was written for from one added later; re-rule it "
                f"or cite the paths."))
            stale.append(key)

    notes.append(
        f"  {seen} bare-filename citations: {len(flagged)} ambiguous, "
        f"{len(ADJUDICATED_BARE) - len(stale)} ruled, {len(stale)} stale rulings, "
        f"{len(overran)} line anchors past the end of the file")
    for name, lineno, token, anchor, cand, (last, total) in overran:
        notes.append(fail(
            f"  OUTOFRANGE {name}:{lineno} -- `{token}:{anchor}` resolves to "
            f"{cand}, which has {total} lines, so line {last} is not in it. F "
            f"resolved the file and dropped the number; this is the half of the "
            f"anchor that was never read."))
    for name, lineno, token, n in flagged:
        if n:
            notes.append(fail(
                f"  AMBIGUOUS {name}:{lineno} -- `{token}` matches {n} files in "
                f"the tree, so it points a reader at none of them. Cite the "
                f"repo-relative path, or rule it."))
        else:
            notes.append(fail(
                f"  ABSENT    {name}:{lineno} -- `{token}` matches no file in "
                f"the tree. Check B skips it for having no `/`, so nothing else "
                f"reads it. Check the spelling and the case."))
    for key, n in sorted(hits.items()):
        if n:
            notes.append(f"  ruled     {key[0]} `{key[1]}` ({n}x) -- {ADJUDICATED_BARE[key]}")
    for key in stale:
        notes.append(fail(
            f"  STALE     {key[0]} `{key[1]}` is ruled and no longer appears. "
            f"A ruling that excuses nothing is removed, not left to excuse a "
            f"regression that comes back the other way."))
    return not flagged and not stale and not overran, notes


#: (tag, blurb, fn, reads_sections).
#:
#: The last field exists because the six checks are independent and their
#: verdicts are printed as if they were about one object. They are not: A is the
#: only check that reads `PAPER.md`, and B, E and F all read `sections/`. When A
#: fails those two are different documents, so `[PASS] E` is a true statement
#: about the sections and says nothing about the file a reader is handed. Six
#: verdicts, one of them FAIL and three of them describing a document nobody will
#: read, is a report that has to say so -- `caveat()` below is where it does.
CHECKS = [
    ("A GENERATED", "PAPER.md == assemble(sections/)", check_generated, False),
    ("B PATHS", "every cited path resolves, unambiguously", check_paths, True),
    ("C FIGDATA", "figure extractors are byte-deterministic", check_figdata, False),
    ("D NOSECRET", "no credential value in any published file", check_nosecret, False),
    ("E UNCITED", "every quantitative claim block cites an artefact", check_uncited, True),
    ("F BARE", "no citation is an ambiguous bare filename", check_bare, True),
    ("G AUDITSTAMP", "every audit report pins what it audited, correctly",
     audit_stamp.check, False),
]

#: The check whose failure makes the other verdicts describe the wrong document.
GENERATED_TAG = "A GENERATED"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true", help="verdict lines only")
    ap.add_argument("--explain-uncited", action="store_true",
                    help="report how much weaker check E is than the binding rule")
    args = ap.parse_args()

    # The sections quote δ, §, ↔ and Chinese. On a cp936 or cp1252 console the
    # first such character in a finding raises UnicodeEncodeError, and a gate
    # that crashes while printing what it caught is a gate that reports nothing.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    failures = []
    generated_ok = True
    for tag, blurb, fn, reads_sections in CHECKS:
        passed, notes = fn()
        print(f"[{'PASS' if passed else 'FAIL'}] {tag} -- {blurb}")
        if tag == GENERATED_TAG:
            generated_ok = passed
        elif reads_sections and not generated_ok:
            print(f"       ^ about sections/, NOT about PAPER.md: {GENERATED_TAG} "
                  f"failed, so the two disagree and this verdict describes the "
                  f"one a reader is not handed.")
        if not args.quiet or not passed:
            for n in notes:
                print(n)
        if not passed:
            failures.append(tag)

    if args.explain_uncited:
        blocks, quantities, worst = coverage_uncited()
        print()
        print(f"E UNCITED, what it does not prove: {quantities} quantities in "
              f"{blocks} blocks are cleared by a citation somewhere in the same "
              f"block.")
        print("  E proves no block is *entirely* uncited. It does not check that "
              "any given number")
        # Resolved through the stamp rather than named, because this sentence
        # spent weeks pointing at an audit that covered a third of the paper.
        # A pointer that cannot go stale is worth more than a shorter line.
        binding = audit_stamp.binding_audits("CITECHECK")
        if binding:
            print(f"  came from the artefact beside it -- {', '.join(binding)} "
                  f"is the audit that does that,")
            print("  and it is stamped as binding on PAPER.md as it stands.")
        else:
            print("  came from the artefact beside it. NO citation audit "
                  "currently binds this text:")
            print("  every CITECHECK report here is stamped stale. Nothing "
                  "has checked the numbers")
            print("  against their artefacts at this revision -- see check G.")
        print("  Widest blocks (quantities behind how many citations):")
        for n, cites, name, lineno in worst:
            print(f"    {n:>3} quantities / {cites} citation(s)   {name}:{lineno}")

    print()
    if failures:
        print(f"verify_paper: FAIL ({len(failures)}/{len(CHECKS)}) -- {', '.join(failures)}")
        if not generated_ok:
            passed_on_sections = [t for t, _, _, r in CHECKS
                                  if r and t not in failures]
            if passed_on_sections:
                print(f"  and {GENERATED_TAG} failing means "
                      f"{', '.join(passed_on_sections)} passed on sections/ while "
                      f"PAPER.md holds something else. Rerun assemble.py before "
                      f"reading any of those greens as being about the paper.")
        return 1
    print(f"verify_paper: PASS ({len(CHECKS)}/{len(CHECKS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
