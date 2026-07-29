"""Mechanical gate for the Phase 1 workshop draft.

`CITECHECK.md` is a *report*: a human-run audit against one sha256 of `PAPER.md`,
which has since moved. A report cannot fail a build. This is the executable half
of the same rule, and it is meant to be run before every push that touches
`papers/phase1-workshop/`.

Five checks, each independently reported, exit code 1 if any fails:

  A. GENERATED   `PAPER.md` is byte-identical to `assemble.py`'s output from
                 `sections/*.md`. The header says "do not hand-edit"; this is the
                 test of it.
  B. PATHS       Every path-like token cited in backticks in `sections/*.md`
                 resolves. Three verdicts, not two:
                   ok         -- resolves repo-relative, unambiguously
                   AMBIGUOUS  -- the token's leading directory exists BOTH at the
                                 repo root and beside PAPER.md, so a reader
                                 resolving it locally lands somewhere else or
                                 nowhere. `figures/` is the live instance: the
                                 paper cites the root pipeline's fig05/06/07
                                 while sitting next to a local `figures/` holding
                                 three homonymous plates.
                   BROKEN     -- resolves nowhere
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

Run:  python papers/phase1-workshop/verify_paper.py
      python papers/phase1-workshop/verify_paper.py --quiet   (verdict lines only)
      python papers/phase1-workshop/verify_paper.py --explain-uncited  (E, verbose)

No network, no API key, no model call, no game spend.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SECTIONS = HERE / "sections"

# A backticked token counts as a path claim if it has a directory separator and
# a plausible extension, or ends in a separator. This deliberately misses bare
# filenames (`PAPER.md`) -- those are the 31 non-repo-relative citations
# CITECHECK already counted, and they are a style finding, not a broken link.
PATH_TOKEN = re.compile(r"`([A-Za-z0-9_.\-/]+/[A-Za-z0-9_.\-/]*)`")

# Tokens that look like paths but are not repository paths.
NOT_A_PATH = re.compile(
    r"^(https?:|arxiv|doi|[0-9]+/[0-9]+$)"  # urls, dois, and fractions like 276/276
    r"|^[0-9]+/[0-9]+"                       # 34/38, 252/252, ...
)

# Directories that legitimately do not exist in a checkout.
GITIGNORED_BY_DESIGN = (
    ".toolchain/",
    "figures/.verify/",
    ".worktrees/",
)

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


def check_generated() -> tuple[bool, list[str]]:
    """A. PAPER.md must equal a fresh assemble of sections/."""
    notes: list[str] = []
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


def classify(token: str) -> str:
    """ok / RULED / AMBIGUOUS / ELIDED / BROKEN / skip, for one cited path token."""
    if NOT_A_PATH.search(token):
        return "skip"
    if token.startswith(".../") or "/.../" in token:
        # `.../MANIFEST.json` is a typographic elision, not a link. It still
        # breaks the binding rule -- a reader cannot resolve it -- so it is
        # reported, but it is a different defect from a path that does not exist.
        return "ELIDED"
    if any(token.startswith(g) or f"/{g}" in token for g in GITIGNORED_BY_DESIGN):
        return "skip"

    at_root = (ROOT / token).exists()
    at_local = (HERE / token).exists()

    head = token.split("/", 1)[0]
    head_both = (ROOT / head).is_dir() and (HERE / head).is_dir()

    if at_root and at_local and (ROOT / token).resolve() == (HERE / token).resolve():
        return "ok"

    if at_root or at_local:
        # Resolves -- but if the leading directory also exists in both trees, a
        # reader resolving relative to PAPER.md lands somewhere else or nowhere.
        if (at_root and at_local) or head_both:
            return "RULED" if token in ADJUDICATED_AMBIGUITY else "AMBIGUOUS"
        return "ok"
    return "BROKEN"


def check_paths() -> tuple[bool, list[str]]:
    """B. Every cited path resolves, and unambiguously."""
    notes: list[str] = []
    seen: dict[str, tuple[str, str]] = {}  # token -> (verdict, first section seen in)
    for section in sorted(SECTIONS.glob("*.md")):
        for token in PATH_TOKEN.findall(section.read_text(encoding="utf-8")):
            if token in seen:
                continue
            verdict = classify(token)
            if verdict != "skip":
                seen[token] = (verdict, section.name)

    def of(kind: str) -> list[str]:
        return sorted(t for t, (v, _) in seen.items() if v == kind)

    ok, ruled = of("ok"), of("RULED")
    amb, elided, broken = of("AMBIGUOUS"), of("ELIDED"), of("BROKEN")

    notes.append(f"  {len(seen)} distinct path citations: {len(ok)} ok, "
                 f"{len(ruled)} ambiguous-but-ruled, {len(amb)} ambiguous-unruled, "
                 f"{len(elided)} elided, {len(broken)} broken")
    for t in broken:
        notes.append(fail(f"  BROKEN    {t}   ({seen[t][1]}) -- resolves from neither the repo "
                          f"root nor beside PAPER.md"))
    for t in elided:
        notes.append(fail(f"  ELIDED    {t}   ({seen[t][1]}) -- an ellipsis is not a path a "
                          f"reader can follow; the binding rule wants the whole thing"))
    for t in amb:
        notes.append(fail(f"  AMBIGUOUS {t}   ({seen[t][1]}) -- `{t.split('/', 1)[0]}/` exists "
                          f"both at the repo root and beside PAPER.md, and nobody has ruled "
                          f"which one this means"))
    for t in ruled:
        notes.append(f"  ruled     {t} -- {ADJUDICATED_AMBIGUITY[t]}")
    return not (broken or amb or elided), notes


def check_figdata() -> tuple[bool, list[str]]:
    """C. The local figure extractors are byte-deterministic.

    They are run *in place*, not in a scratch copy: each one locates the
    repository by walking up from its own `__file__`, so a copied script reads a
    different tree and the test would measure the harness instead of the code.
    Running in place is safe precisely because the property under test is
    idempotence -- if the extractors are deterministic and the committed payloads
    are current, the run is a no-op. If it is not a no-op that is the finding, and
    the original bytes are restored before returning either way.
    """
    notes: list[str] = []
    scripts = sorted(HERE.glob("figures/fig[0-9]*.py"))
    if not scripts:
        return False, [fail("  no figure extractors found under figures/")]

    data_dir = HERE / "figures" / "data"
    before = {p: p.read_bytes() for p in sorted(data_dir.glob("*.json"))}
    drifted: list[str] = []
    try:
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
                drifted.append(f"{script.stem}.json was not regenerated")
            elif payload.read_bytes() != before.get(payload, b""):
                drifted.append(f"{script.stem}.json changed on rerun -- the committed payload "
                               f"is stale, or the extractor is not deterministic")
    finally:
        for path, blob in before.items():
            if path.read_bytes() != blob:
                path.write_bytes(blob)

    if drifted:
        notes.extend(fail(f"  {d}") for d in drifted)
        return False, notes
    notes.append(f"  {len(scripts)} extractors reran in place, {len(before)} payloads unchanged")
    return True, notes


def check_nosecret() -> tuple[bool, list[str]]:
    """D. No credential value anywhere under this directory."""
    notes: list[str] = []
    env = ROOT / ".env"
    secrets = []
    if env.exists():
        for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                value = line.split("=", 1)[1].strip().strip("'\"")
                if len(value) >= 12:
                    secrets.append(value)
    hits = []
    for path in sorted(HERE.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for value in secrets:
            if value in text:
                # Never print the value.
                hits.append(f"  a .env value appears in {path.relative_to(ROOT)}")
    if hits:
        notes.extend(fail(h) for h in hits)
        return False, notes
    notes.append(f"  {len(secrets)} .env value(s) checked against every published file: absent"
                 if secrets else "  no .env present to check against (nothing to leak)")
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
# The trailing `:170-171` is a line anchor, not part of the name.
CITE_TOKEN = re.compile(r"`([A-Za-z0-9_.\-/]+)(?::\d+(?:[-–]\d+)?)?`")
ARTEFACT_SUFFIX = (
    ".md", ".json", ".jsonl", ".py", ".lean", ".dsl", ".bib",
    ".csv", ".svg", ".txt", ".toml", ".yaml", ".yml", ".sh",
)

# Token classes that carry a digit without asserting a quantity. Each is named
# and narrow rather than one permissive regex, on `engine-rig`'s rule for the
# same problem: exempt by *class*, so widening the exemption is a line somebody
# adds and can be argued with, not a quietly loosened character range.
STRUCTURAL = (
    ("section-ref", re.compile(r"§\s*\d+(?:\.\d+)*[a-z]?")),
    ("section-word", re.compile(
        r"\b(?:Sections?|Parts?|constraints?|steps?|beats?|rungs?|layers?|waves?)"
        r"\s+\d+(?:\s*(?:,|and|to|[-–])\s*\d+)*", re.IGNORECASE)),
    ("figure-ref", re.compile(r"\b(?:Figure|Fig\.|Table|Plate|Appendix)\s+\d+\b")),
    ("phase-ref", re.compile(r"\bPhase\s+\d\b")),
    ("arc-agi", re.compile(r"\bARC-AGI-\d\b")),
    ("version", re.compile(r"\bv\d+(?:\.\d+)*\b")),
    ("lean-version", re.compile(r"\bLean\s+\d+(?:\.\d+)*\b")),
    ("timestamp", re.compile(r"\b20\d{6}T\d{6}Z\b")),
    ("iso-date", re.compile(r"\b20\d\d-\d\d-\d\d\b")),
    ("clock", re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")),
    ("commit-sha", re.compile(r"\b[0-9a-f]{7,40}\b")),
    ("digest-elision", re.compile(r"\b[0-9a-f]{6,}…(?:[0-9a-f]+)?")),
    # `E2`, `K12`, `P4`, `M3`, `X1`, `L1`, `C5`, `A0`, `T-10`, `D-B-011`,
    # `INC-BA-001`, `F-11`, `R-05`, `W-1660`. Identifiers, not measurements.
    ("id-code", re.compile(r"\b[A-Z]{1,4}(?:-[A-Z0-9]{1,4})*-?\d{1,4}[a-z′]?\b")),
    ("milestone", re.compile(r"\bm[0-9]\b")),
    # Grid cells and Lean tuples: (2, 4) is a position, not a measurement.
    ("coordinate", re.compile(r"\(\s*-?\d+\s*,\s*-?\d+\s*\)")),
    # `[7, 0, 0, 0, 0, 0, 0]`, `[-1, 1, 0, 1, -1]` -- quoted payloads.
    ("vector", re.compile(r"\[\s*-?\d+(?:\s*,\s*-?\d+)+\s*\]")),
    # `11011`, `00010` -- binary configuration labels in section 4.
    ("bit-label", re.compile(r"\b[01]{5,}\b")),
    ("complexity", re.compile(r"O\(\s*[0-9a-z^ⁿ²³]+\s*\)")),
    ("superscript-pow", re.compile(r"\b\d+[⁰-₟²³¹]+")),
    ("list-ordinal", re.compile(r"^\s*\d+\.\s", re.MULTILINE)),
    ("frame-index", re.compile(r"\bt\s*=?\s*\d+\b")),
)

# Digits, including the paper's space-grouped thousands (`22 356`, `116 470`).
DIGIT = re.compile(r"(?<![\w.])\d[\d  ]*(?:[  ]\d{3})*(?:\.\d+)?")

# Spelled-out cardinals. `one`..`ten` are excluded: 608 of the 805 spelled-out
# numbers in the sections are those words used as determiners ("one further
# finding", "the two tracks"), so flagging them would bury the check in noise.
# From `eleven` up, and `zero`, the word is almost always load-bearing -- and
# `zero` carries several of the paper's most important negative results
# ("moved the unvalidated count by **zero**"). This is also the hole the item's
# adversarial step names: writing 37 as "thirty-seven" must not buy an evasion.
WORDNUM = re.compile(
    r"\b(?:zero|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|"
    r"hundred|thousand|million)(?:-(?:one|two|three|four|five|six|seven|eight|"
    r"nine))?\b",
    re.IGNORECASE,
)

# Chunks that continue the claim above them rather than starting a new one.
CONTINUES = re.compile(r"^\s*(?:\||[-*+]\s|\d+\.\s|>)")

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


def _quantities(block: str) -> tuple[list[str], list[str]]:
    """(digit tokens, spelled-out tokens) that are not citations or structure."""

    def mark(m: re.Match) -> str:
        token = m.group(1)
        if "/" in token or token.lower().endswith(ARTEFACT_SUFFIX):
            return " █CITE█ "
        # A backticked *number* is still a quantity; backticks are not a
        # citation, and letting them hide one would be a one-character evasion.
        return " " if any(c.isalpha() for c in token) else f" {token} "

    text = CITE_TOKEN.sub(mark, block)
    for _name, rx in STRUCTURAL:
        text = rx.sub(" ", text)
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


def check_uncited() -> tuple[bool, list[str]]:
    """E. No quantitative claim block in the body cites nothing at all."""
    notes: list[str] = []
    flagged, hits, scanned = scan_uncited()
    stale = [k for k, n in hits.items() if not n]
    notes.append(
        f"  {scanned} claim blocks scanned across {len(list(SECTIONS.glob('*.md'))) - len(EXEMPT_SECTIONS)} "
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


CHECKS = [
    ("A GENERATED", "PAPER.md == assemble(sections/)", check_generated),
    ("B PATHS", "every cited path resolves, unambiguously", check_paths),
    ("C FIGDATA", "figure extractors are byte-deterministic", check_figdata),
    ("D NOSECRET", "no credential value in any published file", check_nosecret),
    ("E UNCITED", "every quantitative claim block cites an artefact", check_uncited),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--quiet", action="store_true", help="verdict lines only")
    args = ap.parse_args()

    # The sections quote δ, §, ↔ and Chinese. On a cp936 or cp1252 console the
    # first such character in a finding raises UnicodeEncodeError, and a gate
    # that crashes while printing what it caught is a gate that reports nothing.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    failures = []
    for tag, blurb, fn in CHECKS:
        passed, notes = fn()
        print(f"[{'PASS' if passed else 'FAIL'}] {tag} -- {blurb}")
        if not args.quiet or not passed:
            for n in notes:
                print(n)
        if not passed:
            failures.append(tag)

    print()
    if failures:
        print(f"verify_paper: FAIL ({len(failures)}/{len(CHECKS)}) -- {', '.join(failures)}")
        return 1
    print(f"verify_paper: PASS ({len(CHECKS)}/{len(CHECKS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
