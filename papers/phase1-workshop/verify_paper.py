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
# The `:722-724` tail is optional and dropped, exactly as in CITE_TOKEN. Without
# it check B did not match a line-anchored citation *at all* -- and a path B never
# matches is a path B never resolves, so `no/such/dir/thing.md:3` was accepted by
# check E and called broken by nobody. Adding a line number to a citation was a
# way to stop it being checked.
PATH_TOKEN = re.compile(
    r"`([A-Za-z0-9_.\-/{},]+/[A-Za-z0-9_.\-/{},]*?)(?::\d+(?:[-–]\d+)?)?`")

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


def classify(token: str) -> str:
    """ok / RULED / AMBIGUOUS / ELIDED / BROKEN / skip, for one cited path token."""
    if NOT_A_PATH.search(token):
        return "skip"
    if "{" in token or "}" in token:
        verdicts = {classify(t) for t in expand_braces(token)}
        for worst in ("BROKEN", "ELIDED", "AMBIGUOUS", "RULED", "ok"):
            if worst in verdicts:
                return worst
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
CITE_TOKEN = re.compile(r"`([A-Za-z0-9_.\-/{},]+)(?::\d+(?:[-–]\d+)?)?`")
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


_BASENAMES: set[str] | None = None


def _basename_exists(token: str) -> bool:
    """Is there a file by this name anywhere in the tree?

    A bare filename is the paper's dominant citation idiom and check B skips it
    by design, so `(`ledger_summary.jsonl`)` -- a plausible name for a file that
    does not exist -- was a citation *nobody* checked: E accepted the suffix and
    B never saw the token. This is the weakest test that still costs an inventor
    something, and it is free: all 34 distinct bare filenames the sections cite
    exist by basename.
    """
    global _BASENAMES
    if _BASENAMES is None:
        skip = {".git", "__pycache__", ".worktrees", ".toolchain", "node_modules"}
        _BASENAMES = set()
        for path, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in skip]
            _BASENAMES.update(files)
    return token.rsplit("/", 1)[-1] in _BASENAMES


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
    ap.add_argument("--explain-uncited", action="store_true",
                    help="report how much weaker check E is than the binding rule")
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

    if args.explain_uncited:
        blocks, quantities, worst = coverage_uncited()
        print()
        print(f"E UNCITED, what it does not prove: {quantities} quantities in "
              f"{blocks} blocks are cleared by a citation somewhere in the same "
              f"block.")
        print("  E proves no block is *entirely* uncited. It does not check that "
              "any given number")
        print("  came from the artefact beside it -- CITECHECK.md is the audit "
              "that does that.")
        print("  Widest blocks (quantities behind how many citations):")
        for n, cites, name, lineno in worst:
            print(f"    {n:>3} quantities / {cites} citation(s)   {name}:{lineno}")

    print()
    if failures:
        print(f"verify_paper: FAIL ({len(failures)}/{len(CHECKS)}) -- {', '.join(failures)}")
        return 1
    print(f"verify_paper: PASS ({len(CHECKS)}/{len(CHECKS)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
