"""fig06_concept_timeline -- 图6 概念诞生时间线 / concept-birth timeline.

Theoria.md 3.2 figure 6, serving the claim *一个概念从证据到入册* -- a concept's
path from evidence to admission. The plate is a swimlane: one lane per concept
(Button / Door / Cart), one for the items that never became a concept, one for
the probes, one for the expressivity ledger, and -- separated out, drawn smaller,
and titled in its own words -- the lane the honest reading of this log depends on.

What this script does, in order:

1. **parses** ``cold-start-a0/THEORIZE_LOG.md`` (never ``open()``; always through
   ``sources``). The entry set is not hard-coded: sections are found by their
   ``## <FAMILY> --`` headings, entries by their ``### <ID> ... **<verdict>**``
   headings, and the ``E`` family by its table. Every id must land in
   ``EXPECTED_IDS`` and every verdict in ``VERDICTS`` -- an id or a verdict this
   script does not recognise **raises**, because a silently-dropped adjudication
   is worse than a broken build;
2. **matches each entry back to the engine proposals it adjudicates**, by
   expanding the brace/star patterns the log's own headings use
   (``obj{0,1,2}_still_*``) against ``candidates.jsonl``, then propagating to
   lifted rows whose ``lifted_from`` set is already claimed, and matching
   invariants by decoding their GF(2) support to ``(colour, row, col)`` and
   comparing it with the cells and colours the heading names. Any object or
   invariant proposal that no entry claims **raises**;
3. **assigns lanes from the data**, not from a table in this file: a manual name
   in an entry's heading is looked up in ``concept_accounts.json``'s
   ``rules_targeting_it`` / ``laws_naming_it``, so ``press_left`` lands on Button
   and ``door_latch`` lands on Button *and* Door;
4. writes ``csv/fig06_concept_timeline.csv`` -- one row per (lane, item, event),
   plus the cross-check rows, so every mark on the plate is checkable without
   reading this code;
5. renders one figure per theme, two themes x svg+png = 4 images.

**The axis is ordinal and says so.** M1..M6 were committed in one sitting,
seventeen to thirty seconds apart. Drawn on a linear clock the entire manual
collapses into a dot and the picture asserts a speed that means nothing. The
x axis is therefore the *stage* an item has reached -- evidence, proposal,
adjudication, admission, certification, variant, score -- with the committer
timestamps that do exist annotated on the columns they belong to. The only real
clock this log has is ``git log --follow`` over the file itself, which returns
the birth commit plus four later edits, and those four edit the **E** ledger
rather than the manual. ``sources.git_log`` returns ``[]`` on a checkout without
git, and this figure degrades to a pure ordinal axis rather than failing.

**The honest bit, drawn rather than captioned.** The log's own revision table
says the manual was revised *zero* times by ``certify`` -- "That is not the loop
working well. It is the loop **not being exercised**." The three iterations that
did happen were compiler defects (``gen_python_a0``, ``gen_pddl_a0``,
``segment_operators``). They get a separate, subordinate axes whose title says
exactly that, because a timeline showing three revisions without saying whose
they were would overstate the loop, and that is the single most misleading thing
this plate could do.

**Two baselines for the same three numbers, and the disagreement is drawn.**
``concept_accounts.json`` prices the concepts against a responsibility-complete
baseline (Cart +2125, Button -5, Door -1). The ``O-04`` table in the log prices
them against a pixel baseline (+2967, -17, -13) and was never updated after the
re-pricing. The figure uses the JSON, names the baseline on its face, and carries
the log's numbers in the CSV as their own rows rather than quietly discarding
them.

Nothing absent is drawn as zero: an entry with no engine proposal gets the
insufficient-data mark at the proposal column, ``P-03`` carries no verdict at all
in the log and is drawn as verdict-absent, and the seven expressivity-ledger rows
are structural absences of the grammar and wear the structural-absence hatch.
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

import sources  # noqa: E402
import theme  # noqa: E402

NAME = "fig06_concept_timeline"

# --------------------------------------------------------------------------
# the vocabularies this script recognises. Anything outside them raises.
# --------------------------------------------------------------------------

#: Families the log declares, and what the H2 heading calls them.
FAMILIES: tuple[str, ...] = ("O", "R", "L", "P", "E")

#: H2 sections that are not families. Any other H2 raises -- a new section is a
#: new kind of content and this parser has no opinion about it yet.
KNOWN_SECTIONS: tuple[str, ...] = (
    "Round 0",
    "Revision history",
    "Ground-truth seal",
)

#: Every entry id the log is expected to carry. The parser raises if it finds an
#: id outside this set, and raises again if any of these is missing -- the two
#: failure directions are different bugs and both are silent by default.
EXPECTED_IDS: tuple[str, ...] = (
    "O-01", "O-02", "O-03", "O-04",
    "R-01", "R-02", "R-03", "R-04", "R-05", "R-06", "R-07", "R-08",
    "L-01", "L-02", "L-03",
    "P-01", "P-02", "P-03",
    "E-01", "E-02", "E-03", "E-04", "E-05", "E-06", "E-07",
)

#: The verdict vocabulary, verbatim as the headings bold it, mapped to
#: ``(marker slot, outcome class, short label)``. Exactly eight verdicts and
#: exactly eight marker slots in ``theme.MARKERS``: the marker channel carries
#: the verdict so that colour never has to.
VERDICTS: dict[str, tuple[int, str, str]] = {
    "accept": (0, "admitted", "accept"),
    "entailed": (1, "not-admitted", "entailed (frame axiom)"),
    "hypothetical tier only": (2, "not-admitted", "hypothetical tier only"),
    "admitted anyway": (3, "admitted", "admitted anyway (constraint 2)"),
    "not read": (4, "not-admitted", "not read (filtered)"),
    "no split anywhere": (5, "not-admitted", "no split anywhere"),
    "reject, probe-pending": (6, "obligation", "reject + probe pending"),
    "not represented, logged": (7, "not-admitted", "not represented, logged"),
}

#: Outcome classes. Three, and no more: these are the only colour-bearing
#: categories on the plate, and ``theme.series_colours(..., all_pairs=True)``
#: refuses more than three for a form where every pair is visible at once.
CLASSES: tuple[str, ...] = ("admitted", "not-admitted", "obligation")
CLASS_LABEL = {
    "admitted": "admitted to the manual",
    "not-admitted": "not admitted",
    "obligation": "obligation left open",
}

#: The two states an expressivity-ledger row can be in. Anything else raises.
LEDGER_STATES: tuple[str, ...] = ("discharged", "worked-around")

#: The ordinal event axis. ``milestone`` is the log's own M-label; it is a label,
#: not a coordinate -- M1..M6 are seconds apart in committer time and a linear
#: clock would compress the whole manual into a dot.
#:
#: The second and third strings are the column header, and they are kept inside
#: a 20-character budget on purpose: eight columns across one plate is about one
#: inch each, and a header that overflows its column lands on its neighbour's.
STAGES: tuple[tuple[str, str, str, str], ...] = (
    ("world", "M1", "world + trace", "evidence exists"),
    ("proposed", "M2", "engines propose", "candidates.jsonl"),
    ("adjudicated", "M3", "adjudicate", "verdict in the log"),
    ("admitted", "M3", "admit", "into theory.dsl"),
    ("certified", "M4", "four forms", "certify layers green"),
    ("variant", "M5", "no-Button variant", "UNSAT -> certificate"),
    ("scored", "M6", "score vs truth", "the seal is opened"),
    ("later", "post-M6", "E-ledger edits", "the only real clock"),
)
STAGE_INDEX = {key: i for i, (key, _m, _t, _s) in enumerate(STAGES)}

#: Lane keys that are not concept lanes, in draw order after the concepts.
TAIL_LANES: tuple[tuple[str, str], ...] = (
    ("unadmitted", "NOT ADMITTED  --  no concept, no clause"),
    ("probes", "PROBES  --  probe_frontier, 0 executable rows emitted"),
    ("ledger", "EXPRESSIVITY LEDGER  --  what the DSL could not say"),
)

#: Family -> fallback lane, used when no manual name in the heading resolves to
#: a concept through concept_accounts.json.
FAMILY_FALLBACK_LANE = {"O": "unadmitted", "R": "unadmitted", "L": "unadmitted",
                        "P": "probes", "E": "ledger"}

#: The arm of ``concept_accounts.json`` this figure reads, and the variant arm
#: it cross-checks the M5 deletion against.
BASE_ARM = "a0-base"
VARIANT_ARM = "a0-no-button"

#: Named, so the CSV says which of the two disagreeing baselines a number is on.
JSON_BASELINE = "responsibility-complete (concept_accounts.json, a0-base)"
LOG_BASELINE = "pixel (THEORIZE_LOG O-04 table, never re-priced)"

CSV_HEADER = (
    "lane",
    "order",
    "milestone",
    "commit_sha",
    "commit_ts",
    "event_kind",
    "concept",
    "item_id",
    "verdict",
    "label",
    "delta_bits",
    "delta_bits_baseline",
    "trigger",
    "engine",
    "evidence",
)


# --------------------------------------------------------------------------
# markdown parsing
# --------------------------------------------------------------------------


def _tables(lines: list[str]) -> list[dict]:
    """Every pipe table in ``lines``, as ``{"header": [...], "rows": [[...]]}``.

    A table is a maximal run of ``|``-delimited lines; the ``|---|`` separator is
    dropped. Nothing here guesses: a caller that wants a particular table looks
    it up by its header cells and raises when it is not there.
    """
    out: list[dict] = []
    current: dict | None = None
    for raw in lines:
        line = raw.strip()
        if line.startswith("|") and line.endswith("|") and len(line) > 1:
            cells = [c.strip() for c in line[1:-1].split("|")]
            if current is None:
                current = {"header": cells, "rows": []}
            elif not current["rows"] and all(set(c) <= set("-: ") for c in cells):
                pass  # the header separator
            else:
                current["rows"].append(cells)
        elif current is not None:
            out.append(current)
            current = None
    if current is not None:
        out.append(current)
    return out


def _table_by_header(tables: list[dict], header: tuple[str, ...], origin: str) -> dict:
    wanted = [h.lower() for h in header]
    for table in tables:
        if [c.lower() for c in table["header"]] == wanted:
            return table
    raise ValueError(
        f"{origin}: no table with header {list(header)} -- the log's shape changed "
        "and this figure would otherwise draw a table it did not find"
    )


def _int(cell: str) -> int:
    """Integer out of a log table cell: strips bold, unicode minus and '+'."""
    text = cell.replace("*", "").replace("−", "-").replace("+", "").strip()
    return int(text)


def _expand(token: str) -> list[str]:
    """Expand the brace/star patterns the log's headings write engine names in.

    ``obj{0,1,2}_still_*`` -> three globs, each of which is then matched against
    the candidate stream. This is why the entry-to-proposal mapping is derived
    rather than transcribed.
    """
    out = [token]
    while True:
        nxt: list[str] = []
        changed = False
        for item in out:
            m = re.search(r"\{([^{}]*)\}", item)
            if m is None:
                nxt.append(item)
                continue
            changed = True
            for alt in m.group(1).split(","):
                nxt.append(item[: m.start()] + alt.strip() + item[m.end():])
        out = nxt
        if not changed:
            return sorted(set(out))


def _glob_match(pattern: str, name: str) -> bool:
    rx = re.escape(pattern).replace(r"\*", r"[A-Za-z0-9_]*")
    return re.fullmatch(rx, name) is not None


def _bold(text: str) -> list[str]:
    return [m.strip() for m in re.findall(r"\*\*(.+?)\*\*", text)]


def _backticked(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def parse_log(text: str) -> dict:
    """The whole log, as data. Raises on anything it does not recognise."""
    lines = text.split("\n")

    # --- split into H2 sections ------------------------------------------
    sections: list[dict] = []
    current: dict | None = None
    for line in lines:
        if line.startswith("## "):
            title = line[3:].strip()
            head = title.split("—")[0].strip()  # em dash separates name/gloss
            if head in FAMILIES:
                kind, family = "family", head
            elif any(title.startswith(k) for k in KNOWN_SECTIONS):
                kind, family = "prose", None
            else:
                raise ValueError(
                    f"THEORIZE_LOG.md: unrecognised section '## {title}'. Declare it "
                    "in FAMILIES or KNOWN_SECTIONS -- an unparsed section is an "
                    "adjudication this figure would silently omit."
                )
            current = {"title": title, "kind": kind, "family": family, "lines": []}
            sections.append(current)
        elif current is not None:
            current["lines"].append(line)

    by_title = {s["title"]: s for s in sections}
    families = {s["family"]: s for s in sections if s["kind"] == "family"}
    for family in FAMILIES:
        if family not in families:
            raise ValueError(f"THEORIZE_LOG.md: family section '{family}' not found")

    # --- entries: '### <ID> ... **<verdict>**' ----------------------------
    entries: dict[str, dict] = {}
    for family in FAMILIES:
        block = families[family]["lines"]
        for i, line in enumerate(block):
            if not line.startswith("### "):
                continue
            head = line[4:].strip()
            # R-07's verdict spills onto the next line, which starts with the
            # arrow. Consume exactly that continuation and nothing else.
            if i + 1 < len(block) and block[i + 1].lstrip().startswith("→"):
                head = head + " " + block[i + 1].strip()
            m = re.match(r"^([ORLPE])-(\d{2})\b", head)
            if m is None:
                raise ValueError(
                    f"THEORIZE_LOG.md [{family}]: heading without an id: '{head[:70]}'"
                )
            item_id = f"{m.group(1)}-{m.group(2)}"
            rest = head[m.end():]
            if rest.startswith(",") and "in full" in rest[:20]:
                # '### E-06, in full -- ...' elaborates a row of the E table.
                continue
            if item_id in entries:
                raise ValueError(f"THEORIZE_LOG.md: duplicate entry heading {item_id}")
            bolds = _bold(head)
            if len(bolds) > 1:
                raise ValueError(
                    f"THEORIZE_LOG.md {item_id}: {len(bolds)} bold spans in the "
                    f"heading ({bolds}); exactly one verdict was expected"
                )
            verdict = bolds[0] if bolds else None
            if verdict is not None and verdict not in VERDICTS:
                raise ValueError(
                    f"THEORIZE_LOG.md {item_id}: verdict {verdict!r} is not in the "
                    f"declared vocabulary {sorted(VERDICTS)}. Add it deliberately -- "
                    "an unrecognised verdict drawn as a known one is a lie."
                )
            entries[item_id] = {
                "id": item_id,
                "family": family,
                "heading": head,
                "verdict": verdict,
                "tokens": sorted({t for tok in _backticked(head) for t in _expand(tok)}),
                "ledger_state": None,
                "tie_break_bits": None,
            }

    # --- the E family is a table, not headings ---------------------------
    e_table = _table_by_header(
        _tables(families["E"]["lines"]),
        ("#", "wanted", "worked around by", "cost"),
        "THEORIZE_LOG.md [E]",
    )
    for cells in e_table["rows"]:
        item_id = cells[0].strip()
        if not re.fullmatch(r"E-\d{2}", item_id):
            raise ValueError(f"THEORIZE_LOG.md [E]: table row id {item_id!r} unrecognised")
        state = "discharged" if "discharged" in cells[2].lower() else "worked-around"
        if state not in LEDGER_STATES:  # defensive; the map above cannot miss
            raise ValueError(f"THEORIZE_LOG.md [E]: unrecognised ledger state {state!r}")
        entries[item_id] = {
            "id": item_id,
            "family": "E",
            "heading": cells[1],
            "verdict": None,
            "tokens": [],
            "ledger_state": state,
            "tie_break_bits": None,
        }

    # --- the id set, both directions -------------------------------------
    found = sorted(entries)
    unexpected = [i for i in found if i not in EXPECTED_IDS]
    missing = [i for i in EXPECTED_IDS if i not in entries]
    if unexpected or missing:
        raise ValueError(
            f"THEORIZE_LOG.md: entry ids do not match the declared set. "
            f"unexpected={unexpected} missing={missing}"
        )

    # --- the O-04 compression table, on the log's own (pixel) baseline ----
    o_tables = _tables(families["O"]["lines"])
    account_table = _table_by_header(
        o_tables,
        ("object", "declaration", "script bits", "pixel baseline", "account"),
        "THEORIZE_LOG.md [O]",
    )
    log_accounts = {
        cells[0].strip(): {
            "declaration_bits": _int(cells[1]),
            "script_bits": _int(cells[2]),
            "baseline_bits": _int(cells[3]),
            "delta_bits": _int(cells[4]),
        }
        for cells in account_table["rows"]
    }

    # --- tie-break bits, where an entry's body records one ---------------
    for family in FAMILIES:
        body = "\n".join(families[family]["lines"])
        for chunk in re.split(r"^### ", body, flags=re.M)[1:]:
            m = re.match(r"^([ORLPE]-\d{2})\b", chunk)
            if m is None or m.group(1) not in entries:
                continue
            bits = re.search(r"\((\d+) vs (\d+) bits\)", chunk)
            if bits is not None:
                entries[m.group(1)]["tie_break_bits"] = (int(bits.group(1)), int(bits.group(2)))

    # --- Round 0's declared candidate counts -----------------------------
    round0 = next(s for s in sections if s["title"].startswith("Round 0"))
    flat = " ".join(round0["lines"])
    m = re.search(r"(\d+) candidate rows:", flat)
    if m is None:
        raise ValueError("THEORIZE_LOG.md [Round 0]: no 'N candidate rows:' line")
    declared = {
        kind: int(n)
        for n, kind in re.findall(r"(\d+) (?:executable )?`(\w+)`", flat)
    }
    round0_counts = {"total": int(m.group(1)), "by_kind": declared}

    # --- revision history + the compiler-defect table --------------------
    rev_section = next(s for s in sections if s["title"].startswith("Revision history"))
    rev_tables = _tables(rev_section["lines"])
    rev_table = _table_by_header(
        rev_tables, ("rev", "when", "trigger", "change"), "THEORIZE_LOG.md [Revision history]"
    )
    revisions = [
        {"rev": _int(c[0]), "when": c[1].strip(), "trigger": c[2].strip(), "change": c[3].strip()}
        for c in rev_table["rows"]
    ]
    defect_table = _table_by_header(
        rev_tables, ("#", "layer", "defect", "how it surfaced"),
        "THEORIZE_LOG.md [Revision history]",
    )
    defects = [
        {"n": _int(c[0]), "layer": c[1].strip().strip("`"), "defect": c[2].strip(),
         "surfaced": c[3].strip()}
        for c in defect_table["rows"]
    ]

    zero_claim = "The manual was revised zero times by certify." in text
    if not zero_claim:
        raise ValueError(
            "THEORIZE_LOG.md: the sentence 'The manual was revised zero times by "
            "certify.' is gone. That sentence is this figure's headline caveat; if "
            "the log no longer says it, the figure must not say it either."
        )
    certify_revisions = [r for r in revisions if "certify" in r["trigger"].lower()]

    # --- the ground-truth seal -------------------------------------------
    seal = next(s for s in sections if s["title"].startswith("Ground-truth seal"))
    seal_text = " ".join(re.sub(r"^>\s?", "", line) for line in seal["lines"])
    agree = re.search(r"agrees with the world\s+on \*\*(\d+)\*\*", seal_text)
    pairs = re.search(r"all (\d+) reachable", seal_text)
    if agree is None or pairs is None:
        raise ValueError("THEORIZE_LOG.md [Ground-truth seal]: the score line did not parse")
    seal_ids = sorted({i for i in re.findall(r"\b([ORLPE]-\d{2})\b", seal_text) if i in entries})

    return {
        "entries": entries,
        "log_accounts": log_accounts,
        "round0": round0_counts,
        "revisions": revisions,
        "defects": defects,
        "certify_revisions": certify_revisions,
        "seal": {"agree": int(agree.group(1)), "pairs": int(pairs.group(1)), "ids": seal_ids},
        "section_titles": sorted(by_title),
    }


# --------------------------------------------------------------------------
# entry -> engine proposal
# --------------------------------------------------------------------------


def _candidate_name(record: dict) -> str | None:
    payload = record.get("payload") or {}
    if record["kind"] == "object_hypothesis":
        return payload.get("object_id")
    if record["kind"] == "rule_hypothesis":
        return payload.get("name")
    return None


def _support_atoms(payload: dict) -> tuple[frozenset[int], frozenset[tuple[int, int]]]:
    """Decode a GF(2) invariant's support to ``(colours, cells)``.

    ``support`` is ``["8@13", "5@22"]`` -- colour at an index into ``cells``. The
    log's headings name colours (``(#6)``, ``is 8``) and sometimes cells
    (``cell(3,2)``), so decoding is what lets the match be derived instead of
    transcribed.
    """
    cells = payload["cells"]
    colours: set[int] = set()
    used: set[tuple[int, int]] = set()
    for atom in payload["support"]:
        colour, _, index = atom.partition("@")
        colours.add(int(colour))
        row, col = cells[int(index)]
        used.add((int(row), int(col)))
    return frozenset(colours), frozenset(used)


def match_candidates(entries: dict, candidates: list[dict]) -> tuple[dict, list[str]]:
    """``{item_id: [candidate index, ...]}``. Raises on an unclaimed proposal."""
    notes: list[str] = []
    claims: dict[str, list[int]] = {i: [] for i in entries}

    named = [(i, _candidate_name(r)) for i, r in enumerate(candidates)]
    for item_id in sorted(entries):
        entry = entries[item_id]
        for index, name in named:
            if name is None:
                continue
            if any(_glob_match(tok, name) for tok in entry["tokens"]):
                claims[item_id].append(index)

    # Lifted rows: the engine's own `lifted_from` says which rows it generalises.
    # If an entry already claims all of them, it claims the lifted row too --
    # which is how R-01 picks up `obj2_step` without the heading naming it.
    for item_id in sorted(entries):
        owned = {_candidate_name(candidates[i]) for i in claims[item_id]}
        if not owned:
            continue
        for index, record in enumerate(candidates):
            if index in claims[item_id] or record["kind"] != "rule_hypothesis":
                continue
            lifted = record["payload"].get("lifted_from") or []
            if lifted and set(lifted) <= owned:
                claims[item_id].append(index)

    # Invariants: match by decoded support against the heading's colours/cells.
    for item_id in sorted(entries):
        entry = entries[item_id]
        if entry["family"] != "L":
            continue
        head = entry["heading"]
        want_colours = frozenset(
            int(c) for c in re.findall(r"#(\d+)", head) + re.findall(r"\bis (\d+)\b", head)
        )
        if not want_colours:
            continue
        want_cells = frozenset(
            (int(r), int(c)) for r, c in re.findall(r"cell\((\d+),\s*(\d+)\)", head)
        )
        for index, record in enumerate(candidates):
            if record["kind"] != "invariant":
                continue
            colours, cells = _support_atoms(record["payload"])
            if colours == want_colours and (not want_cells or cells == want_cells):
                claims[item_id].append(index)

    for item_id in claims:
        claims[item_id] = sorted(set(claims[item_id]))

    # --- nothing may fall off the stream unnoticed ------------------------
    claimed = {i for ids in claims.values() for i in ids}
    for index, record in enumerate(candidates):
        if index in claimed or record["kind"] == "plan":
            continue
        raise ValueError(
            f"candidates.jsonl row {index} ({record['kind']}, "
            f"{_candidate_name(record)!r}) is claimed by no THEORIZE_LOG entry. An "
            "engine proposal nobody adjudicated must stop the build, not vanish."
        )
    for kind in ("object_hypothesis", "invariant"):
        for index, record in enumerate(candidates):
            if record["kind"] != kind:
                continue
            owners = sorted(i for i in claims if index in claims[i])
            if len(owners) != 1:
                raise ValueError(
                    f"candidates.jsonl row {index} ({kind}) is claimed by {owners}; "
                    "exactly one entry was expected"
                )

    overlaps = sorted(
        f"row {i} ({_candidate_name(candidates[i])}) claimed by "
        + "+".join(sorted(o for o in claims if i in claims[o]))
        for i in sorted(claimed)
        if len([o for o in claims if i in claims[o]]) > 1
    )
    if overlaps:
        notes.append(
            f"{len(overlaps)} engine proposal(s) are adjudicated by more than one "
            "entry, which is the log's own doing (R-06 names the LEFT still-rules "
            "that R-07's wildcard also covers): " + "; ".join(overlaps)
        )
    unadjudicated = sorted(
        f"{candidates[i]['engine']}/{candidates[i]['kind']}"
        for i in range(len(candidates))
        if i not in claimed
    )
    if unadjudicated:
        notes.append(
            f"{len(unadjudicated)} row(s) in the stream are adjudicated nowhere in "
            f"the log and are not part of any lane: {', '.join(unadjudicated)}."
        )
    return claims, notes


def _coverage(record: dict) -> tuple[int, int]:
    got, _, total = (record.get("evidence") or {}).get("coverage", "0/0").partition("/")
    return int(got), int(total)


# --------------------------------------------------------------------------
# lanes
# --------------------------------------------------------------------------


def _concept_index(accounts: list[dict]) -> dict:
    """Concept lanes, ordered by ``object_id`` -- Button, Door, Cart.

    Alphabetical would put Cart first and break the causal reading (the Button
    presses, the Door opens, the Cart is what moves). ``object_id`` is the
    engine's own order and it is the one the story runs in.
    """
    return {
        c["name"]: c
        for c in sorted(accounts, key=lambda c: (c["object_id"], c["name"]))
    }


def lanes_for(entry: dict, concepts: dict) -> list[str]:
    """Which lanes an entry belongs on, derived from concept_accounts.json.

    A manual name in the heading (``press_left``, ``door_latch``, ``Cart``) is
    looked up in each concept's ``rules_targeting_it`` / ``laws_naming_it`` /
    ``object_id`` / name. ``door_latch`` names two concepts, so ``L-02`` is drawn
    on both lanes -- one row each, and the CSV's ``lane`` column tells them apart.
    """
    if entry["family"] in ("P", "E"):
        return [FAMILY_FALLBACK_LANE[entry["family"]]]
    plain = re.sub(r"`[^`]*`", " ", entry["heading"])
    words = set(re.findall(r"[A-Za-z_]+", plain))
    hits: set[str] = set()
    for name, account in concepts.items():
        keys = {name, account["object_id"], *account.get("rules_targeting_it", [])}
        keys |= {law.split()[-1] for law in account.get("laws_naming_it", [])}
        if keys & set(entry["tokens"]) or name in words:
            hits.add(name)
    if hits:
        return sorted(hits, key=lambda n: list(concepts).index(n))
    return [FAMILY_FALLBACK_LANE[entry["family"]]]


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------


def extract() -> tuple[dict, list[str]]:
    notes: list[str] = []

    parsed = parse_log(sources.read_text("a0_theorize_log"))
    entries = parsed["entries"]
    candidates = sources.read_jsonl("a0_candidates")
    accounts_all = sources.read_json("a0_concept_accounts")

    if BASE_ARM not in accounts_all:
        raise KeyError(f"concept_accounts.json has no {BASE_ARM!r} arm")
    concepts = _concept_index(accounts_all[BASE_ARM])
    variant_names = sorted({c["name"] for c in accounts_all.get(VARIANT_ARM, [])})

    claims, claim_notes = match_candidates(entries, candidates)
    notes.extend(claim_notes)

    # --- git: the only real clock, and it barely covers the manual --------
    commits = sources.git_log(sources.GIT_TIMELINE_PATH)
    if commits:
        birth, later = commits[0], commits[1:]
        notes.append(
            f"git log --follow {sources.GIT_TIMELINE_PATH}: {len(commits)} commit(s). "
            f"Birth {birth['sha'][:7]} {birth['when']}; {len(later)} later commit(s) "
            "classified as E-ledger edits, not manual revisions -- the log's own "
            "revision table lists exactly "
            f"{len(parsed['revisions'])} revisions, both authored at M3/M5."
        )
    else:
        birth, later = None, []
        notes.append(
            "git is unavailable or the path has no history here: sources.git_log "
            "returned no commits, so no wall-clock annotation is drawn and the axis "
            "degrades to pure ordinal. The figure still builds; it just says less."
        )

    # E-ledger items named in the later commit subjects, so the post-M6 column
    # is attached to rows by evidence rather than by assumption.
    later_by_item: dict[str, list[dict]] = {}
    unattached: list[dict] = []
    for commit in later:
        named = sorted({i for i in re.findall(r"\bE-\d{2}\b", commit["subject"]) if i in entries})
        if named:
            for item_id in named:
                later_by_item.setdefault(item_id, []).append(commit)
        else:
            unattached.append(commit)
    if later and not later_by_item:
        notes.append("no later commit subject names an E-NN item; none is attached to a row.")

    # --- build the rows ---------------------------------------------------
    lane_titles: dict[str, str] = {}
    for name in concepts:
        account = concepts[name]
        lane_titles[name] = (
            f"{name.upper()}  --  {account['object_id']}, colour {account['colour']}, "
            f"{len(account['responsibility_cells'])} responsibility cell(s)"
        )
    for key, title in TAIL_LANES:
        lane_titles[key] = title
    lane_order = list(concepts) + [k for k, _ in TAIL_LANES]

    rows: list[dict] = []
    for lane in lane_order:
        # Family order, not alphabetical: objects, then the rules that target
        # them, then the laws that name them. Alphabetical would open every
        # concept lane with its invariant, which is the end of the story.
        members = sorted(
            (i for i in entries if lane in lanes_for(entries[i], concepts)),
            key=lambda i: (FAMILIES.index(entries[i]["family"]), i),
        )
        rows.append({"kind": "band", "lane": lane, "label": lane_titles[lane]})
        for item_id in members:
            entry = entries[item_id]
            shared = len(lanes_for(entry, concepts)) > 1
            rows.append(
                {
                    "kind": "item",
                    "lane": lane,
                    "item_id": item_id,
                    "entry": entry,
                    "concept": lane if lane in concepts else "",
                    "shared": shared,
                    "events": _events_for(
                        entry, lane, concepts, variant_names, candidates,
                        claims[item_id], parsed, birth, later_by_item.get(item_id, []),
                    ),
                }
            )

    n_items = sum(1 for r in rows if r["kind"] == "item")
    notes.append(
        f"{len(entries)} log entries over {len(lane_order)} lanes -> {n_items} rows "
        f"({n_items - len(entries)} of them are second copies of an item whose "
        "manual name is claimed by two concepts, L-02 door_latch above all)."
    )

    # --- the two disagreeing baselines -----------------------------------
    disagreements: list[dict] = []
    for name in sorted(concepts):
        json_bits = concepts[name]["script_delta_bits"]
        log_bits = parsed["log_accounts"].get(name, {}).get("delta_bits")
        if log_bits is not None and log_bits != json_bits:
            disagreements.append({"concept": name, "json": json_bits, "log": log_bits})
    if disagreements:
        notes.append(
            "compression accounts disagree and are NOT reconciled: "
            + "; ".join(
                f"{d['concept']} {d['json']:+d} bits in concept_accounts.json vs "
                f"{d['log']:+d} bits in THEORIZE_LOG O-04"
                for d in disagreements
            )
            + f". The figure plots the JSON ({JSON_BASELINE}); the log's table is a "
            "pixel baseline that was never updated after the re-pricing, and its "
            "numbers are carried in the CSV as their own rows."
        )

    # --- round 0's declared counts vs the stream --------------------------
    stream_counts: dict[str, int] = {}
    for record in candidates:
        stream_counts[record["kind"]] = stream_counts.get(record["kind"], 0) + 1
    declared = parsed["round0"]["by_kind"]
    mismatch = sorted(
        f"{kind}: log says {declared.get(kind, 0)}, stream has {stream_counts.get(kind, 0)}"
        for kind in sorted(set(declared) | set(stream_counts))
        if declared.get(kind, 0) != stream_counts.get(kind, 0)
    )
    notes.append(
        f"Round 0 declares {parsed['round0']['total']} candidate rows; the stream "
        f"holds {len(candidates)}."
        + (" Differences, reported not reconciled: " + "; ".join(mismatch) if mismatch
           else " Every kind agrees.")
    )
    stamps = sorted({r.get("timestamp") for r in candidates})
    if len(stamps) == 1:
        notes.append(
            f"every candidate row carries the same timestamp ({stamps[0]}), so the "
            "stream supplies no clock either -- one more reason the axis is ordinal."
        )

    notes.append(
        f"revision table: {len(parsed['revisions'])} revision(s), "
        f"{len(parsed['certify_revisions'])} of them triggered by certify; "
        f"{len(parsed['defects'])} compiler defect(s) on the subordinate lane. The "
        "zero is derived from the table's own trigger column, not quoted."
    )
    notes.append(
        f"ground-truth seal: {parsed['seal']['agree']}/{parsed['seal']['pairs']} "
        f"reachable (state, action) pairs agree; the misses are attributed in the "
        f"log to {', '.join(parsed['seal']['ids']) or 'no item'}."
    )

    return (
        {
            "rows": rows,
            "lane_order": lane_order,
            "lane_titles": lane_titles,
            "concepts": concepts,
            "variant_names": variant_names,
            "parsed": parsed,
            "candidates": candidates,
            "claims": claims,
            "commits": commits,
            "birth": birth,
            "later": later,
            "unattached_later": unattached,
            "disagreements": disagreements,
            "n_candidates": len(candidates),
        },
        notes,
    )


def _events_for(
    entry: dict,
    lane: str,
    concepts: dict,
    variant_names: list[str],
    candidates: list[dict],
    claimed: list[int],
    parsed: dict,
    birth: dict | None,
    later_commits: list[dict],
) -> list[dict]:
    """The marks on one row, left to right. Every one is derived from a source."""
    verdict = entry["verdict"]
    klass = VERDICTS[verdict][1] if verdict is not None else None
    events: list[dict] = []

    def add(stage: str, kind: str, label: str, **extra) -> None:
        event = {
            "stage": stage,
            "order": STAGE_INDEX[stage],
            "milestone": STAGES[STAGE_INDEX[stage]][1],
            "kind": kind,
            "label": label,
            "absent": False,
            "commit_sha": "",
            "commit_ts": "",
            "engine": "",
            "evidence": "",
            "delta_bits": None,
            "delta_bits_baseline": "",
            "trigger": "",
            "annotate": "",
        }
        event.update(extra)
        events.append(event)

    # --- M2: the engine proposal, or its declared absence -----------------
    if claimed:
        primary = [i for i in claimed if not (candidates[i]["payload"].get("lifted_from") or [])]
        got = sum(_coverage(candidates[i])[0] for i in primary)
        total = sum(_coverage(candidates[i])[1] for i in primary)
        lifted = len(claimed) - len(primary)
        engines = ",".join(sorted({candidates[i]["engine"] for i in claimed}))
        frontier = max(
            (candidates[i]["payload"].get("frontier_size") or 0 for i in claimed), default=0
        )
        add(
            "proposed",
            "proposed",
            f"{len(claimed)} candidate row(s)"
            + (f", {lifted} of them lifted" if lifted else ""),
            engine=engines,
            evidence=f"{got}/{total}" + (f" frontier {frontier}" if frontier > 1 else ""),
        )
    else:
        add(
            "proposed",
            "no-proposal",
            "no candidate row: this entry adjudicates something the stream did not "
            "propose",
            absent=True,
        )

    # --- M3: the verdict --------------------------------------------------
    if entry["family"] == "E":
        add(
            "adjudicated",
            "ledger-logged",
            f"expressivity gap logged ({entry['ledger_state']})",
            evidence=entry["ledger_state"],
        )
    elif verdict is None:
        add(
            "adjudicated",
            "verdict-absent",
            "the log records no bold verdict for this entry",
            absent=True,
        )
    else:
        bits = entry["tie_break_bits"]
        add(
            "adjudicated",
            "adjudicated",
            verdict,
            evidence=(f"tie broken on length, {bits[0]} vs {bits[1]} bits" if bits else ""),
        )

    if birth is not None:
        for event in events:
            if event["stage"] in ("adjudicated", "admitted"):
                event["commit_sha"] = birth["sha"][:7]
                event["commit_ts"] = birth["when"]

    if klass == "admitted":
        delta = concepts[lane]["script_delta_bits"] if lane in concepts else None
        add(
            "admitted",
            "admitted",
            "written into theory.dsl",
            delta_bits=delta,
            delta_bits_baseline=JSON_BASELINE if delta is not None else "",
            commit_sha=birth["sha"][:7] if birth else "",
            commit_ts=birth["when"] if birth else "",
        )
        add(
            "certified",
            "certified",
            "cheap layer and Lean both green on the first run",
            trigger="no certify->theorize iteration: nothing came back",
        )
    elif klass == "obligation":
        add(
            "certified",
            "obligation-open",
            "entered as a theorem with probe: pending -- the probe is designable "
            "and unrunnable on this instance",
            trigger="the latch is already pressed by the time the probe could run",
            annotate="probe designed, not runnable",
        )

    # --- M5: the no-Button variant, cross-checked against the other arm ---
    if lane in concepts and klass == "admitted":
        present = lane in variant_names
        add(
            "variant",
            "variant-carried" if present else "variant-deleted",
            f"{lane} is {'present in' if present else 'absent from'} the "
            f"{VARIANT_ARM} account",
            evidence=f"{VARIANT_ARM}: {', '.join(variant_names) or 'no concept'}",
            annotate="carried" if present else "clause deleted",
        )

    # --- M6: the score, where the log attributes a miss to this entry -----
    if entry["id"] in parsed["seal"]["ids"]:
        seal = parsed["seal"]
        add(
            "scored",
            "settled-by-score",
            f"{seal['agree']}/{seal['pairs']} pairs agree; the "
            f"{seal['pairs'] - seal['agree']} misses are the ones this entry named",
            evidence=f"{seal['agree']}/{seal['pairs']}",
            annotate=f"{seal['pairs'] - seal['agree']} of {seal['pairs']} wrong",
        )

    # --- post-M6: E-ledger edits, the only real clock ---------------------
    for commit in later_commits:
        add(
            "later",
            "ledger-edited",
            commit["subject"],
            commit_sha=commit["sha"][:7],
            commit_ts=commit["when"],
        )

    return sorted(events, key=lambda e: (e["order"], e["kind"]))


# --------------------------------------------------------------------------
# csv
# --------------------------------------------------------------------------


def csv_rows(data: dict) -> list[list]:
    """One row per (lane, item, event), then the cross-check rows.

    Sorted by lane order, then item id, then stage. A reviewer checking a mark
    finds it by reading the lane label off the plate and the item id off the
    tick, with no reference to this file.
    """
    lane_rank = {lane: i for i, lane in enumerate(data["lane_order"])}
    out: list[list] = []

    items = [r for r in data["rows"] if r["kind"] == "item"]
    for row in sorted(items, key=lambda r: (lane_rank[r["lane"]], r["item_id"])):
        entry = row["entry"]
        for event in row["events"]:
            out.append(
                [
                    row["lane"],
                    event["order"],
                    event["milestone"],
                    event["commit_sha"],
                    event["commit_ts"],
                    event["kind"] + ("-ABSENT" if event["absent"] else ""),
                    row["concept"],
                    row["item_id"],
                    entry["verdict"] or entry["ledger_state"] or "",
                    event["label"],
                    theme.fmt_num(event["delta_bits"]) if event["delta_bits"] is not None else None,
                    event["delta_bits_baseline"],
                    event["trigger"],
                    event["engine"],
                    event["evidence"],
                ]
            )

    parsed = data["parsed"]

    # The log's own compression numbers, on the baseline the log used. Kept as
    # rows rather than dropped, because the disagreement is the finding.
    for name in sorted(data["concepts"]):
        account = parsed["log_accounts"].get(name)
        if account is None:
            continue
        out.append(
            [
                name, STAGE_INDEX["adjudicated"], "M3", "", "",
                "compression-account-log", name, "O-04", "admitted anyway",
                f"log O-04 table: declaration {account['declaration_bits']} bits, "
                f"script {account['script_bits']}, baseline {account['baseline_bits']}",
                theme.fmt_num(account["delta_bits"]), LOG_BASELINE,
                "not reconciled with concept_accounts.json", "", "",
            ]
        )
    for name in sorted(data["concepts"]):
        account = data["concepts"][name]
        out.append(
            [
                name, STAGE_INDEX["adjudicated"], "M3", "", "",
                "compression-account-json", name, "O-04", "admitted anyway",
                f"concept_accounts.json {BASE_ARM}: with {account['script_with_bits']} "
                f"bits, without {account['script_without_bits']}",
                theme.fmt_num(account["script_delta_bits"]), JSON_BASELINE,
                account["reason"], "", account["verdict"],
            ]
        )

    for revision in sorted(parsed["revisions"], key=lambda r: r["rev"]):
        stage = next(
            (i for i, s in enumerate(STAGES) if s[1] == revision["when"]),
            STAGE_INDEX["admitted"],
        )
        out.append(
            [
                "manual-revisions", stage, revision["when"],
                data["birth"]["sha"][:7] if data["birth"] and revision["when"] == "M3" else "",
                data["birth"]["when"] if data["birth"] and revision["when"] == "M3" else "",
                "manual-revision", "", f"REV-{revision['rev']:02d}", "",
                revision["change"], None, "", revision["trigger"], "", "",
            ]
        )
    for defect in sorted(parsed["defects"], key=lambda d: d["n"]):
        out.append(
            [
                "compiler-defects", "", "", "", "",
                "compiler-defect-ABSENT", "", f"DEF-{defect['n']:02d}", "",
                defect["defect"], None, "",
                "no milestone recorded in the log", defect["layer"], defect["surfaced"],
            ]
        )

    counts = parsed["round0"]["by_kind"]
    stream: dict[str, int] = {}
    for record in data["candidates"]:
        stream[record["kind"]] = stream.get(record["kind"], 0) + 1
    for kind in sorted(set(counts) | set(stream)):
        out.append(
            [
                "round-0", STAGE_INDEX["proposed"], "M2", "", "",
                "stream-census", "", f"KIND-{kind}", "",
                f"log declares {counts.get(kind, 0)}, stream holds {stream.get(kind, 0)}",
                None, "",
                "reported, not reconciled" if counts.get(kind, 0) != stream.get(kind, 0) else "",
                "", f"{stream.get(kind, 0)}",
            ]
        )
    return out


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

_GUTTER_X = 8.15
_X_MAX = 12.60

#: Character budgets. Text on the plate is clipped to fit its column and the
#: full string lives in the CSV -- which is what the audit layer is for. The
#: budgets are constants rather than measured extents, because measuring text
#: extents is how a figure's size comes to depend on its font metrics.
_BUDGET_ROW_LABEL = 46
_BUDGET_GUTTER = 78
_BUDGET_TRIGGER = 44
_BUDGET_SUB_RIGHT = 68


def _clip(text: str, budget: int) -> str:
    """Deterministic truncation. The full text is in the CSV, always."""
    flat = re.sub(r"\s+", " ", text).strip()
    return flat if len(flat) <= budget else flat[: budget - 3].rstrip() + "..."


def _class_colours(theme_name: str) -> dict[str, str]:
    # Every pair of classes is visible at once on this plate, so the all-pairs
    # gate applies. It raises above three; three is exactly what is here.
    theme.series_colours(theme_name, len(CLASSES), all_pairs=True)
    return {name: theme.series_colour(theme_name, i) for i, name in enumerate(CLASSES)}


def _row_label(row: dict) -> str:
    """``<id>  <manual name>  (<engine name>)``, all of it read off the heading.

    The manual name is what the log admits the thing *as* (``as `press_left```,
    ``named `Button```); the engine name is what the stream called it. Showing
    both is the row's whole point -- the left half of the plate is the engine's
    vocabulary and the right half is the manual's.

    An entry the log never admits under a manual name has no manual name to show,
    so its label is the heading's own prose. ``R-05`` is the case that matters:
    it names ``press_left`` and ``door_opens_left`` because it rejects *their*
    direction generality, and labelling it with either of those would read as if
    ``R-05`` were that rule. It is not: it is the rejection.
    """
    entry = row["entry"]
    if entry["family"] == "E":
        return f"{row['item_id']}  {_clip(entry['heading'], _BUDGET_ROW_LABEL - 6)}"
    head = entry["heading"]
    admitted_as = re.search(r"\b(?:as|named) `([^`]+)`", head)
    if admitted_as is not None:
        subject = admitted_as.group(1)
        others = [n for n in _backticked(head) if n != subject]
        subject += f"  ({others[0]})" if len(others) == 1 else ""
    else:
        prose = re.sub(r"\*\*.*?\*\*", "", head)[len(row["item_id"]):]
        prose = prose.replace("`", "").replace("—", "--").replace("→", "")
        subject = prose.strip(" ,-")
    label = _clip(f"{row['item_id']}  {subject}", _BUDGET_ROW_LABEL)
    return label + ("  (shared)" if row["shared"] else "")


def _gutter(row: dict, concepts: dict) -> str:
    entry = row["entry"]
    if entry["family"] == "E":
        edits = [e for e in row["events"] if e["stage"] == "later"]
        stamps = ", ".join(f"{e['commit_sha']} {e['commit_ts'][11:]}" for e in edits)
        return _clip(
            f"ledger: {entry['ledger_state']}"
            + (f"  |  {len(edits)} post-M6 edit(s): {stamps}" if edits else ""),
            _BUDGET_GUTTER,
        )
    verdict = entry["verdict"]
    left = VERDICTS[verdict][2] if verdict else "no verdict recorded"
    parts = [left]
    proposal = next((e for e in row["events"] if e["stage"] == "proposed"), None)
    if proposal is not None and not proposal["absent"]:
        parts.append(proposal["evidence"])
    else:
        parts.append("no engine proposal")
    if row["concept"] in concepts:
        account = concepts[row["concept"]]
        if any(e["kind"] == "admitted" for e in row["events"]):
            parts.append(f"{account['script_delta_bits']:+d} bits")
    return _clip("  |  ".join(p for p in parts if p), _BUDGET_GUTTER)


def _tick_labels(commits: list[dict], birth: dict | None, later: list[dict]) -> list[str]:
    """Column headers. A column with no committer timestamp says so, in words.

    Only two of the eight columns can carry a real clock reading, because
    ``git log --follow`` over this one file is the only clock the declared
    sources hold. The other six are labelled ``no commit ts`` rather than left
    blank, so the missing time is visible instead of merely absent.
    """
    labels = []
    for key, milestone, title, sub in STAGES:
        if key in ("adjudicated", "admitted") and birth is not None:
            stamp = f"{birth['sha'][:7]}\n{birth['when'][11:]}"
        elif key == "later" and later:
            stamp = f"{len(later)} commits\n{later[0]['when'][11:16]}-{later[-1]['when'][11:16]}Z"
        elif not commits:
            stamp = "no git\nin checkout"
        else:
            stamp = "no commit ts"
        labels.append(f"{milestone}\n{title}\n{sub}\n{stamp}")
    return labels


def _render(data: dict, theme_name: str, figsize: tuple[float, float]) -> list[str]:
    p = theme.apply_theme(theme_name)
    colours = _class_colours(theme_name)
    band_fills = theme.sequential_steps(theme_name, len(STAGES), ordinal=True)
    parsed = data["parsed"]
    concepts = data["concepts"]

    main_rows = data["rows"]
    sub_rows = (
        [{"kind": "band", "label": "MANUAL REVISIONS  --  both authored; "
          f"{len(parsed['certify_revisions'])} triggered by certify"}]
        + [
            {"kind": "revision", "revision": r}
            for r in sorted(parsed["revisions"], key=lambda r: r["rev"])
        ]
        + [{"kind": "band", "label": "COMPILER DEFECTS  --  the three iterations that "
            "did happen; no milestone recorded"}]
        + [
            {"kind": "defect", "defect": d}
            for d in sorted(parsed["defects"], key=lambda d: d["n"])
        ]
    )

    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(
        4, 1,
        height_ratios=[
            0.30 * len(main_rows) + 1.7,
            0.30 * len(sub_rows) + 0.7,
            1.15,
            0.30,
        ],
    )
    ax = fig.add_subplot(gs[0, 0])
    ax_sub = fig.add_subplot(gs[1, 0])
    ax_key = fig.add_subplot(gs[2, 0])
    ax_pad = fig.add_subplot(gs[3, 0])
    ax_key.axis("off")
    ax_pad.axis("off")

    # ---- stage columns, as an ordinal ramp -------------------------------
    for axis in (ax, ax_sub):
        for i in range(len(STAGES)):
            axis.axvspan(i - 0.5, i + 0.5, color=band_fills[i], alpha=0.16, linewidth=0, zorder=0)
        for i in range(1, len(STAGES)):
            if STAGES[i][1] != STAGES[i - 1][1]:
                axis.axvline(i - 0.5, color=p["axis"], linewidth=0.7, zorder=1)
        axis.axvline(_GUTTER_X - 0.15, color=p["axis"], linewidth=0.6, zorder=1)
        axis.set_xlim(-0.62, _X_MAX)
        axis.grid(False)

    # ---- the main swimlane ----------------------------------------------
    labels: list[str] = []
    header_flags: list[bool] = []
    for y, row in enumerate(main_rows):
        if row["kind"] == "band":
            labels.append(row["label"])
            header_flags.append(True)
            ax.axhline(y, color=p["axis"], linewidth=0.6, zorder=1)
            if row["lane"] == "ledger" and data["unattached_later"]:
                # A later commit whose subject names no E-NN item is drawn on the
                # band rather than guessed onto a row.
                ax.text(
                    STAGE_INDEX["later"], y + 0.42,
                    f"+{len(data['unattached_later'])} later commit(s) naming no "
                    "E item, attached to no row",
                    ha="center", va="bottom", fontsize=theme.BASE_FONT_SIZE - 3.5,
                    color=p["muted"],
                )
            continue
        labels.append(_row_label(row))
        header_flags.append(False)
        entry = row["entry"]
        verdict = entry["verdict"]
        klass = VERDICTS[verdict][1] if verdict else None
        colour = colours[klass] if klass else p["muted"]

        drawn = [e for e in row["events"] if not e["absent"]]
        if len(drawn) > 1:
            xs = [e["order"] for e in drawn]
            ax.plot([min(xs), max(xs)], [y, y], color=colour, linewidth=1.0,
                    alpha=0.55, zorder=2, solid_capstyle="round")

        for event in row["events"]:
            x = event["order"]
            if event["absent"]:
                # never a zero, never a silent gap: the two non-value states
                # wear theme.ABSENCE's encoding and appear in the key.
                ax.plot([x], [y], marker="o", markersize=5.2, linestyle="none",
                        markerfacecolor="none", markeredgecolor=p["muted"],
                        markeredgewidth=0.9, zorder=3)
                continue
            if event["stage"] == "adjudicated" and verdict is not None:
                ax.plot([x], [y], marker=theme.series_marker(VERDICTS[verdict][0]),
                        markersize=7.4, linestyle="none", color=colour,
                        markeredgecolor=p["surface"], markeredgewidth=0.5, zorder=4)
            elif entry["family"] == "E" and event["stage"] == "adjudicated":
                # An expressivity-ledger row is a structural absence of the
                # grammar, so it wears theme.ABSENCE's structural encoding --
                # hatched, unfilled -- rather than any verdict marker.
                discharged = entry["ledger_state"] == "discharged"
                ax.add_patch(
                    plt.Rectangle(
                        (x - 0.17, y - 0.28), 0.34, 0.56,
                        facecolor="none",
                        edgecolor=p["ink_secondary"],
                        linewidth=0.8,
                        linestyle="-" if discharged else "-",
                        hatch=None if discharged else theme.series_hatch(1),
                        zorder=4,
                    )
                )
            else:
                ax.plot([x], [y], marker="|", markersize=7.5, markeredgewidth=1.7,
                        linestyle="none", color=colour, zorder=3)
            if event["annotate"]:
                # Just above the connector, not halfway to the row above: an
                # annotation that floats between two rows belongs to neither.
                ax.text(x + 0.14, y - 0.09, event["annotate"], ha="left", va="bottom",
                        fontsize=theme.BASE_FONT_SIZE - 3.5, color=p["ink_secondary"],
                        zorder=5)

        ax.text(_GUTTER_X, y, _gutter(row, concepts), ha="left", va="center",
                fontsize=theme.BASE_FONT_SIZE - 3, color=p["ink_secondary"])

    ax.set_yticks(list(range(len(main_rows))))
    ax.set_yticklabels(labels, fontsize=theme.BASE_FONT_SIZE - 2.5)
    for label, is_header in zip(ax.get_yticklabels(), header_flags):
        label.set_color(p["ink"] if is_header else p["ink_secondary"])
        if is_header:
            label.set_fontweight("bold")
            label.set_fontsize(theme.BASE_FONT_SIZE - 2.0)
    ax.set_ylim(len(main_rows) - 0.4, -1.25)
    ax.set_xticks(list(range(len(STAGES))))
    ax.set_xticklabels(
        _tick_labels(data["commits"], data["birth"], data["later"]),
        fontsize=theme.BASE_FONT_SIZE - 3.5,
    )
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")
    ax.tick_params(axis="x", length=0)
    ax.set_xlabel(
        "ORDINAL event axis -- the stage an item has reached, not clock time. "
        "M1..M6 are seconds apart in committer time; on a linear clock the whole "
        "manual would be one dot.",
        labelpad=8.0,
    )
    ax.text(_GUTTER_X, -0.70, "verdict  |  engine evidence  |  compression account",
            ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3,
            color=p["muted"])
    if data["birth"] is not None:
        # The two M3 columns are one commit. Saying so is the point: adjudication
        # and admission were not separated in time, and there was no loop between.
        ax.annotate(
            "", xy=(STAGE_INDEX["adjudicated"] - 0.42, -0.70),
            xytext=(STAGE_INDEX["admitted"] + 0.42, -0.70),
            arrowprops={"arrowstyle": "-", "color": p["axis"], "linewidth": 0.8},
        )
        ax.text(
            (STAGE_INDEX["adjudicated"] + STAGE_INDEX["admitted"]) / 2.0, -0.80,
            f"one commit ({data['birth']['sha'][:7]}): the whole manual lands here",
            ha="center", va="bottom", fontsize=theme.BASE_FONT_SIZE - 3,
            color=p["ink_secondary"],
        )

    # ---- the subordinate lane -------------------------------------------
    sub_labels: list[str] = []
    sub_flags: list[bool] = []
    for y, row in enumerate(sub_rows):
        if row["kind"] == "band":
            sub_labels.append(row["label"])
            sub_flags.append(True)
            ax_sub.axhline(y, color=p["axis"], linewidth=0.6, zorder=1)
            continue
        sub_flags.append(False)
        if row["kind"] == "revision":
            revision = row["revision"]
            sub_labels.append(f"REV-{revision['rev']:02d}  {revision['when']}")
            x = next((i for i, s in enumerate(STAGES) if s[1] == revision["when"]),
                     STAGE_INDEX["admitted"])
            ax_sub.plot([x], [y], marker="|", markersize=7.5, markeredgewidth=1.7,
                        linestyle="none", color=p["ink_secondary"], zorder=3)
            ax_sub.text(x + 0.18, y, _clip(revision["trigger"], _BUDGET_TRIGGER),
                        ha="left", va="center",
                        fontsize=theme.BASE_FONT_SIZE - 3.5, color=p["ink_secondary"])
        else:
            defect = row["defect"]
            sub_labels.append(f"DEF-{defect['n']:02d}  {defect['layer']}")
            # No milestone is recorded for these, so none is invented: the row is
            # drawn as a dotted span across the whole axis and labelled absent.
            ax_sub.plot([0, len(STAGES) - 1], [y, y], linestyle=":", linewidth=1.0,
                        color=p["muted"], zorder=2)
            ax_sub.text(0.0, y, "  milestone not recorded in the log",
                        ha="left", va="center",
                        fontsize=theme.BASE_FONT_SIZE - 3.5, color=p["muted"])
        ax_sub.text(_GUTTER_X, y,
                    _clip(row["revision"]["change"] if row["kind"] == "revision"
                          else row["defect"]["surfaced"], _BUDGET_SUB_RIGHT),
                    ha="left", va="center", fontsize=theme.BASE_FONT_SIZE - 3.5,
                    color=p["muted"])

    ax_sub.set_yticks(list(range(len(sub_rows))))
    ax_sub.set_yticklabels(sub_labels, fontsize=theme.BASE_FONT_SIZE - 3)
    for label, is_header in zip(ax_sub.get_yticklabels(), sub_flags):
        label.set_color(p["ink_secondary"] if is_header else p["muted"])
    ax_sub.set_ylim(len(sub_rows) - 0.4, -0.8)
    ax_sub.set_xticks([])
    ax_sub.set_title(
        "SUBORDINATE LANE, and the reason it is drawn apart: the manual was revised "
        f"{len(parsed['certify_revisions'])} times by certify.\n"
        "\"That is not the loop working well. It is the loop not being exercised.\"  "
        f"The {len(parsed['defects'])} iterations that did happen were COMPILER "
        "defects, not manual revisions.",
        loc="left", fontsize=theme.BASE_FONT_SIZE - 1.5, color=p["ink"],
    )

    # ---- the key ---------------------------------------------------------
    verdict_handles = [
        Line2D([], [], linestyle="none", marker=theme.series_marker(slot),
               markersize=7.0, color=colours[klass], label=f"{short}")
        for _v, (slot, klass, short) in sorted(VERDICTS.items(), key=lambda kv: kv[1][0])
    ]
    class_handles = [
        Line2D([], [], color=colours[c], linewidth=2.4, label=CLASS_LABEL[c]) for c in CLASSES
    ] + [
        Line2D([], [], color=p["muted"], linewidth=0.0,
               marker="|", markersize=7.5, markeredgewidth=1.7, linestyle="none",
               label="event at this stage (proposed / admitted / certified / variant / scored)"),
        Patch(facecolor="none", edgecolor=p["ink_secondary"], linewidth=0.8,
              label="expressivity-ledger row, discharged"),
    ] + theme.absence_handles(theme_name)

    leg_v = ax_key.legend(
        handles=verdict_handles, loc="upper left", ncols=2,
        title="marker shape = the log's verdict, verbatim (colour never carries it alone)",
        alignment="left", fontsize=theme.BASE_FONT_SIZE - 2,
        title_fontsize=theme.BASE_FONT_SIZE - 2,
    )
    leg_v.get_title().set_color(p["ink_secondary"])
    ax_key.add_artist(leg_v)
    leg_c = ax_key.legend(
        handles=class_handles, loc="upper right", ncols=1,
        title="colour = outcome class (3 slots, the all-pairs limit); absence is drawn, never zeroed",
        alignment="left", fontsize=theme.BASE_FONT_SIZE - 2,
        title_fontsize=theme.BASE_FONT_SIZE - 2,
    )
    leg_c.get_title().set_color(p["ink_secondary"])
    ax_key.text(
        0.0, 0.02,
        "structural absence here = the grammar cannot state it (E rows);  "
        "insufficient data = no engine proposal, or no verdict recorded (P-03).",
        transform=ax_key.transAxes, ha="left", va="bottom",
        fontsize=theme.BASE_FONT_SIZE - 3, color=p["muted"],
    )

    fig.suptitle(
        "Figure 6 -- concept birth: evidence -> adjudication -> admission "
        "(cold-start A0, 3 concepts, "
        f"{len(parsed['entries'])} adjudications, {data['n_candidates']} engine proposals)"
    )

    disagreement = "; ".join(
        f"{d['concept']} {d['json']:+d} vs {d['log']:+d}" for d in data["disagreements"]
    )
    stamps = (
        f"{len(data['commits'])} committer timestamps (UTC) exist for this file: the birth "
        f"({data['birth']['sha'][:7]}, {data['birth']['when']}) and {len(data['later'])} later "
        "commits that edit the E ledger, not the manual."
        if data["commits"] else
        "git is unavailable in this checkout, so no committer timestamp is drawn at all."
    )
    # Explicit line breaks rather than relying on wrap: wrapping to the canvas
    # edge is how a caveat ends up touching it.
    theme.caveat(
        fig,
        "The axis is ORDINAL. M1..M6 were committed in one sitting, seconds apart; a linear "
        "clock axis would compress the entire manual into a point and imply a speed that means "
        f"nothing.\n{stamps} Every candidate row carries the same synthetic stamp, so the "
        "stream is no clock either.\nCompression accounts are plotted on the "
        f"responsibility-complete baseline of concept_accounts.json ({BASE_ARM}); the O-04 table "
        "in THEORIZE_LOG prices the same concepts against a pixel\nbaseline and was never "
        f"re-priced, so the two disagree ({disagreement}) and both are carried in the CSV. "
        "Text on the plate is clipped to a fixed budget; the CSV has it in full.\n"
        "The same instance built the A0 world at M1 and adjudicated it at M3 -- the log names "
        "that hole in its own seal, and no verdict here is independent of it.",
        theme=theme_name,
    )
    return theme.save(fig, NAME, theme_name)


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------


def build() -> dict:
    data, notes = extract()
    rows = csv_rows(data)
    csv_path = theme.write_csv(NAME, CSV_HEADER, rows)

    n_main = len(data["rows"])
    n_sub = 2 + len(data["parsed"]["revisions"]) + len(data["parsed"]["defects"])
    # Deterministic: the row counts come from the sources, not from the run. The
    # width is what eight column headers plus a text gutter need in order not to
    # overlap; ``bbox_inches="tight"`` would size the canvas from text extents,
    # which PLAN.md section 0 forbids for exactly that reason.
    figsize = (17.4, 0.28 * (n_main + n_sub) + 4.5)

    images: list[str] = []
    for theme_name in theme.THEMES:
        images.extend(_render(data, theme_name, figsize))

    notes.append(
        f"{n_main} main rows ({n_main - sum(1 for r in data['rows'] if r['kind'] == 'band')} "
        f"items over {len(data['lane_order'])} lanes) plus {n_sub} subordinate rows; "
        f"{len(rows)} CSV rows; figure {figsize[0]:.1f}x{figsize[1]:.1f} in."
    )
    return {"csv": csv_path, "images": images, "notes": notes}


if __name__ == "__main__":
    result = build()
    print(result["csv"])
    for image in result["images"]:
        print(image)
    for note in result["notes"]:
        print("note:", note)
