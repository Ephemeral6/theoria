"""Throwaway probe: measure the flag rate of candidate UNCITED designs.

Not a gate. This exists to answer, on the real text rather than by guessing,
two questions the design cannot settle a priori:

  1. What unit of analysis (paragraph / table row / list item) gives a triage
     load a human will actually work through?
  2. How much of the flag volume is spelled-out numerals ("seven actions"), the
     evasion the item's adversarial step names?

Its output is the input to the triage in RUN_STATE.md. Delete-able.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
SECTIONS = HERE / "sections"

PATH_TOKEN = re.compile(r"`([A-Za-z0-9_.\-/]+/[A-Za-z0-9_.\-/]*)`")
# A citation, for THIS check, is any backticked token that resolves to something
# on disk -- including a bare filename like `Theoria.md`, which check B skips on
# purpose (it is a style finding there, but here it is a real artefact pointer).
# The trailing `:170-171` is a line anchor, not part of the path -- the paper
# cites source lines that way and a resolver that does not strip it reports a
# real citation as absent.
CITE_TOKEN = re.compile(r"`([A-Za-z0-9_.\-/]+(?:/[A-Za-z0-9_.\-/]*)?)(?::\d+(?:[-–]\d+)?)?`")
FENCE = re.compile(r"^```")

STRUCTURAL = [
    ("section-ref", re.compile(r"§\s*\d+(?:\.\d+)*[a-z]?")),
    ("section-word", re.compile(
        r"\b(?:Sections?|Parts?|constraints?|steps?|beats?|rungs?|layers?|"
        r"waves?|rows?)\s+\d+(?:\s*(?:,|and|to|–|-)\s*\d+)*", re.IGNORECASE)),
    ("figure-ref", re.compile(r"\b(?:Figure|Fig\.|Table|Plate|Appendix)\s+\d+\b")),
    ("phase-ref", re.compile(r"\bPhase\s+\d\b")),
    ("arc-agi", re.compile(r"\bARC-AGI-\d\b")),
    ("version", re.compile(r"\bv\d+(?:\.\d+)*\b")),
    ("timestamp", re.compile(r"\b20\d{6}T\d{6}Z\b")),
    ("id-code", re.compile(r"\b[A-Z][A-Z]?-?[A-Z]{0,3}-?\d+[a-z]?\b")),
    ("milestone", re.compile(r"\bm[1-8]\b")),
    ("beat", re.compile(r"\bL\d+\b")),
    ("hexish", re.compile(r"\b[0-9a-f]{6,}\u2026")),
    ("commit-sha", re.compile(r"\b[0-9a-f]{7,40}\b")),
    ("clock", re.compile(r"\b\d{2}:\d{2}(?::\d{2})?\b")),
    # Grid cells and Lean tuples: (2, 4) is a position, not a measurement.
    ("coordinate", re.compile(r"\(\s*\d+\s*,\s*\d+\s*\)")),
    ("list-ordinal", re.compile(r"^\s*\d+\.\s", re.MULTILINE)),
]

DIGIT = re.compile(r"(?<![\w.])\d[\d\u00a0\u202f]*(?:[ \u00a0]\d{3})*(?:\.\d+)?")

WORDNUM = re.compile(
    r"\b(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)\b",
    re.IGNORECASE,
)


def strip_noise(text: str) -> str:
    """Remove fenced code, then blank out cited paths and structural tokens."""
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            out.append("")
            continue
        out.append("" if in_fence else line)
    text = "\n".join(out)

    def mark(m: re.Match) -> str:
        token = m.group(1)
        if (HERE.parent.parent / token).exists() or (HERE / token).exists():
            return " \u2588PATH\u2588 "
        # A backticked *number* is still a quantity -- `null` is not, but
        # `0.033244` is, and blanking it would let backticks hide a claim.
        if any(c.isalpha() for c in token):
            return " "
        return f" {token} "

    text = CITE_TOKEN.sub(mark, text)
    for _name, rx in STRUCTURAL:
        text = rx.sub(" ", text)
    return text


ATTACHED = ("quote", "row", "item")


def units(raw: str, granularity: str):
    """(kind, lineno, raw_text) units.

    At granularity "block" the unit is a *claim block*: a prose paragraph
    together with the table, list or blockquote that follows it. That is how
    this paper actually cites -- the sentence introducing a table carries the
    artefact path and the rows carry the values -- so splitting per row would
    flag ~70 rows whose citation sits two lines above, and the adjudication
    table would become a rubber stamp. The cost is stated in the docstring of
    the real check: within a block, number-to-artefact correspondence is not
    verified, only that the block cites something.
    """
    out: list[tuple[str, int, str]] = []
    for kind, lineno, text in _split(raw, "row+item" if granularity == "block" else granularity):
        attach = kind == "quote" or (granularity == "block" and kind in ATTACHED)
        if attach and out and out[-1][0] in ("para", "block"):
            k, ln, prev = out[-1]
            out[-1] = ("block", ln, prev + "\n" + text)
        else:
            out.append((kind, lineno, text))
    return out


def _split(raw: str, granularity: str):
    """Yield (kind, lineno, raw_text) units at the requested granularity."""
    lines = raw.splitlines()
    in_fence = False
    buf, buf_start = [], 1
    for i, line in enumerate(lines, 1):
        if FENCE.match(line.strip()):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        stripped = line.strip()
        # A blockquote is a verbatim quotation of another artefact; the sentence
        # that introduces it is where the citation lives ("the report says:").
        # units() folds a quote block back into that intro paragraph.
        if stripped.startswith(">"):
            if buf and buf[0].lstrip().startswith(">"):
                buf.append(line)
                continue
            if buf:
                yield ("para", buf_start, "\n".join(buf))
            buf, buf_start = [line], i
            continue
        if buf and buf[0].lstrip().startswith(">"):
            yield ("quote", buf_start, "\n".join(buf))
            buf = []
        is_row = stripped.startswith("|") and granularity in ("row", "row+item")
        is_item = (
            re.match(r"^\s*[-*]\s", line) or re.match(r"^\s*\d+\.\s", line)
        ) and granularity == "row+item"
        if not stripped or stripped.startswith("#") or is_row or is_item:
            if buf:
                yield ("para", buf_start, "\n".join(buf))
                buf = []
            if is_row and not re.match(r"^\|[\s:\-|]+\|$", stripped):
                yield ("row", i, line)
            elif is_item:
                yield ("item", i, line)
            continue
        if not buf:
            buf_start = i
        buf.append(line)
    if buf:
        kind = "quote" if buf[0].lstrip().startswith(">") else "para"
        yield (kind, buf_start, "\n".join(buf))


def scan(granularity: str, with_words: bool):
    flagged = []
    total_units = 0
    for section in sorted(SECTIONS.glob("*.md")):
        if section.name == "00_abstract.md":
            continue
        raw = section.read_text(encoding="utf-8")
        for kind, lineno, text in units(raw, granularity):
            total_units += 1
            cleaned = strip_noise(text)
            nums = DIGIT.findall(cleaned)
            words = WORDNUM.findall(cleaned) if with_words else []
            if not nums and not words:
                continue
            if "\u2588PATH\u2588" in cleaned:
                continue
            flagged.append((section.name, kind, lineno, nums, words, text))
    return total_units, flagged


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for gran in ("para", "row", "row+item", "block"):
        for with_words in (False, True):
            total, flagged = scan(gran, with_words)
            digit_only = [f for f in flagged if f[3]]
            word_only = [f for f in flagged if not f[3] and f[4]]
            print(
                f"granularity={gran:9s} wordnums={'on ' if with_words else 'off'}  "
                f"units={total:4d}  flagged={len(flagged):4d}  "
                f"(digit-bearing {len(digit_only)}, word-only {len(word_only)})"
            )
    print()
    gran = sys.argv[1] if len(sys.argv) > 1 else "row+item"
    words = len(sys.argv) > 2 and sys.argv[2] == "words"
    _, flagged = scan(gran, words)
    print(f"=== dump: granularity={gran} wordnums={'on' if words else 'off'} ===")
    for name, kind, lineno, nums, wds, text in flagged:
        snippet = " ".join(text.split())[:150]
        print(f"\n{name}:{lineno} [{kind}] nums={nums[:8]} words={wds[:5]}")
        print(f"    {snippet}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
