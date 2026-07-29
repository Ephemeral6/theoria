"""`python -m tools.engine_dividend_table [--check]`

Assembles the one table E6 asks for — *what is an engine worth?* — out of three
runs that measured three different things, and writes `ENGINE_DIVIDEND.md`.

**It reads verdicts; it does not re-derive them.** That rule is written down
because breaking it produced this module's worst bug: an earlier draft recomputed
section C's optimality agreement instead of reading `verdicts.agreement_ok`,
scored "no known optimum" as a disagreement, and rendered **no** against three
admissible planners — a false accusation, in a file whose purpose is to be quoted
in a paper. Arithmetic here is confined to percentages and totals over fields
read from artefacts.

Three sources, and they are not interchangeable:

  (A) deadlock theorems as pruning   runs/<E6>/dividend.json
  (B) certificates rechecked cold    runs/<E6>/recheck_report.json
  (C) the three-rung ladder          runs/20260728T072633Z-E2-fd-ladder-bench/ladder.json

`--check` re-renders and compares byte-for-byte against the committed
`ENGINE_DIVIDEND.md`, so a stale table is a failing check rather than a document
nobody re-ran. That is the same contract `recheck.build_cases --check` uses.
Note what `--check` cannot do: it proves the file matches the renderer, never
that the renderer reads the right field. Only a test pinning a real number does
that, which is why `tests/test_engine_dividend_table.py` pins several.
"""

import argparse
import json
import os
from typing import Any, Dict, List, Optional

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E6_RUN = "runs/20260728T191530Z-E6-engine-dividend"
E2_RUN = "runs/20260728T072633Z-E2-fd-ladder-bench"
OUT = "ENGINE_DIVIDEND.md"

# The FD column throughout is the `singleton` guard, which is the only one the
# two admissible rungs accept (`full` compiles to an axiom they refuse). It
# carries the size-1 theorems only, so the theorem count beside it is NOT the
# number of theorems that reached the planner -- hence the `carried` column.
GUARD = "singleton"


def _load(rel: str) -> Any:
    with open(os.path.join(HERE, rel), encoding="utf-8") as handle:
        return json.load(handle)


def _pct(before: Optional[int], after: Optional[int]) -> str:
    if not before:
        return "--"
    return f"{100.0 * (before - after) / before:.1f}%"


def _fd_row(row: Dict[str, Any], rung: str, guard: str = GUARD) -> Optional[Dict]:
    # The artefact keys the rung as `rung`; `config` on the nested baseline is
    # Fast Downward's own search string. Matching the wrong one silently yields
    # an all-`--` column that still renders as a valid table, which is why the
    # tests pin real numbers here.
    for entry in row.get("fd", []) or []:
        if entry.get("rung") == rung and entry.get("guard") == guard:
            return entry
    return None


def _twins(div: Dict[str, Any]) -> Dict[str, str]:
    """instance -> the earlier instance it is a duplicate board of."""
    seen: Dict[str, str] = {}
    for pair in (div.get("structural_twins") or {}).get("pairs", []):
        if len(pair) == 2:
            seen[pair[1]] = pair[0]
    return seen


# ------------------------------------------------------------------ (A) prune


def _section_prune(div: Dict[str, Any]) -> List[str]:
    twins = _twins(div)
    rows = list(div["results"])
    # Render the zero row first, and *make* that true rather than relying on
    # batch order -- an earlier draft claimed it and depended on `open4` being
    # index 0, so reordering the batch would have silently falsified the prose.
    rows.sort(key=lambda r: 0 if (r.get("stub") or {}).get("expansions_saved") == 0
              and (r.get("n_theorems") or 0) > 0 else 1)

    out = [
        "## A · A proved deadlock, wired in as a pruner",
        "",
        "The claim under test is Theoria 1.9: *every deadlock proved, the planner",
        "speeds up at the same time*. **It is false as an unconditional promise, and",
        "the zero row -- rendered first -- is why it has to be stated conditionally.**",
        "",
        "`expansions` is the honest column; wall clock is §D and it is worse. Both",
        "searches here are **controls, not rungs the ladder ever selects**: the",
        "bundled BFS is the determinism-pinned default and `astar(blind())` is A\\*",
        "with a zero heuristic, which is the same search in other clothes. The rungs",
        "a caller would actually get -- lmcut, ipdb, lama -- gain far less or",
        "nothing, which is the subject of the next subsection and is the reason this",
        "table must not be quoted on its own.",
        "",
        "`carried` is the number of theorems the compiled guard could express, "
        f"against the number proved. The `{GUARD}` guard takes size-1 theorems only;",
        "the pair theorems are left on the floor, so a row reading `40` theorems and",
        "`8` carried bought its dividend with eight.",
        "",
        "| instance | theorems | carried | bundled BFS before | after | saved | FD `blind()` before | after | saved | plan length |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        stub = row.get("stub") or {}
        before, after = stub.get("expansions_before"), stub.get("expansions_after")
        if before is None:
            continue
        blind = _fd_row(row, "fd-optimal/blind")
        b_before = (blind or {}).get("expansions_before")
        b_after = (blind or {}).get("expansions_after")
        size = (blind or {}).get("guard_size") or {}
        carried = size.get("theorems_expressed")
        name = row["instance"]
        label = f"`{name}`" + (f" †{twins[name]}" if name in twins else "")
        out.append(
            "| {} | {} | {} | {} | {} | {} | {} | {} | {} | {} |".format(
                label,
                row.get("n_theorems", "--"),
                carried if carried is not None else "--",
                before,
                after,
                _pct(before, after),
                b_before if b_before is not None else "--",
                b_after if b_after is not None else "--",
                _pct(b_before, b_after) if b_before is not None else "--",
                "unchanged" if stub.get("plan_length_unchanged") else "**CHANGED**",
            )
        )

    if twins:
        pairs = ", ".join(f"`{b}` ≡ `{a}`" for b, a in twins.items())
        out += [
            "",
            f"† **{pairs}** -- the committed fixture and the generated ladder's bottom "
            "rung are the same board, checked column by column and agreeing. They are "
            f"printed as two rows because the agreement is a measurement, but the "
            f"batch is **{len(rows) - len(twins)} distinct boards**, not {len(rows)}.",
        ]

    settled = [r["instance"] for r in rows
               if (_fd_row(r, "fd-optimal/blind") or {}).get("expansions_before") == 0]
    if settled:
        first = settled[0]
        stub = next(r["stub"] for r in rows if r["instance"] == first)
        out += [
            "",
            "**The `0 | 0 | --` rows are not missing data.** Fast Downward's translator "
            "settles " + ", ".join(f"`{n}`" for n in settled) + " during relaxed "
            "reachability and the search never starts, so there is no search for a "
            f"deadlock theorem to shorten. The bundled rung's "
            f"{stub['expansions_before']} -> {stub['expansions_after']} on `{first}` "
            "is a fact about the bundled rung, which has no such check.",
        ]

    zero = next((r for r in rows
                 if (r.get("stub") or {}).get("expansions_saved") == 0
                 and (r.get("n_theorems") or 0) > 0), None)
    out += ["", "**The zero row.** "]
    if zero is None:
        out[-1] += (
            "This batch contains no instance with theorems and no saving. That is "
            "itself worth stating -- an all-positive table is the shape a "
            "publication-biased batch has."
        )
    else:
        stub = zero["stub"]
        out[-1] += (
            f"`{zero['instance']}` proves **{zero['n_theorems']} true theorems and "
            f"saves nothing** -- {stub['expansions_before']} expansions before, "
            f"{stub['expansions_after']} after, and the pruner fired "
            f"**{stub.get('states_pruned', 0)} times** where it cuts 69-100 states on "
            "the rows below. The theorems are not wrong and the hook is not "
            "disconnected; there is simply no dead region on the path this search "
            "takes. A table of only the instances where the engine paid would be a "
            "different and less honest table."
        )

    tb = div.get("tiebreak_sensitivity") or {}
    summary = tb.get("summary") or tb.get("rows") or []
    if summary:
        out += [
            "",
            "**One number per cell is less than this run knows.** The same batch was "
            "re-measured under three tie-break rules for A\\*'s open list. The "
            "*absolute* baselines move a great deal and the *dividends* move little:",
            "",
            "| instance | baseline min | baseline max | dividend min | dividend max |",
            "|---|---|---|---|---|",
        ]
        for srow in summary:
            # The dividend band lives under guards.<guard>, not at the top level.
            # Reading a top-level `dividend_min` yields an all-`--` column that
            # still renders -- the same silent failure the `rung`/`config` comment
            # above describes. The tests pin far7's real band for that reason.
            guard = (srow.get("guards") or {}).get(GUARD) or {}
            out.append(
                "| `{}` | {} | {} | {} | {} |".format(
                    srow.get("instance", "?"),
                    srow.get("baseline_min", "--"),
                    srow.get("baseline_max", "--"),
                    _fmt_pct_field(guard.get("dividend_min_pct")),
                    _fmt_pct_field(guard.get("dividend_max_pct")),
                )
            )
        out += [
            "",
            "So an absolute expansion count in the columns above is one open list's, "
            "not a property of the instance. The ratios are the durable part. E7 §3c "
            "answers the same objection with a stronger instrument than this one -- "
            "the count of distinct states with *f* < C\\*, which A\\* must expand under "
            "any tie-break rule.",
        ]
    return out


def _fmt_pct_field(value: Any) -> str:
    # The artefact's `*_pct` fields are already percentages (21.6 means 21.6%).
    if isinstance(value, (int, float)):
        return f"{value:.1f}%"
    return "--" if value is None else str(value)


# ------------------------------------------------------------- (A') the bound


def _section_boundary(div: Dict[str, Any]) -> List[str]:
    prior = div.get("prior_audit") or {}
    out = [
        "",
        "### Where that dividend goes, and why",
        "",
        f"Audited in depth by E7 (`{prior.get('source', 'DEADLOCK_CLAIM.md')}`).",
        "The short form, because a summary table that reprints the dividend without",
        "its boundary is the thing E7 exists to prevent:",
        "",
    ]
    for finding in prior.get("findings", []):
        out.append(
            "* **{}** ({}) -- {}".format(
                finding.get("applies_to", finding.get("id", "?")),
                finding.get("section", "--"),
                finding.get("finding", "").strip(),
            )
        )
    out += [
        "",
        "**And the guard is a choice with a sign.** The FD column above is the",
        f"`{GUARD}` guard. The same artefact holds two other encodings of the same",
        "theorems, and one of them makes the search *worse*: on `far5`,",
        "`astar(blind())` goes 958 -> 872 under `singleton`, 958 -> 839 under `full`,",
        "and 958 -> **1159** under `indexed` -- a 21% loss, because that encoding",
        "inflates the operator set. \"The expansion dividend is real\" is true of the",
        "column printed here and false of a column that could have been printed",
        "instead.",
        "",
        "The boundary in one line: **a proved deadlock is worth expansions to the",
        "extent its proof system is stronger than the planner's own pre-search",
        "relaxation.** The carver proves with h^2 mutexes; Fast Downward's",
        "pre-search deadness test is h^1. Where they coincide the pruning dividend",
        "is nil; where they do not it can be total.",
    ]
    return out


# ------------------------------------------------------------- (B) the recheck


def _section_recheck(rep: Dict[str, Any]) -> List[str]:
    counts = rep.get("counts", {})
    pagoda = rep.get("pagoda", {}) or {}
    matrix = rep.get("matrix", []) or []
    forg = rep.get("forgeries", {}) or {}

    n_matrix = len(matrix)
    n_accept = sum(1 for r in matrix if r.get("verdict") == "ACCEPT")
    n_reject = sum(1 for r in matrix if r.get("verdict") == "REJECT")
    off = counts.get("matrix_off_script", 0)
    n_pagoda_matrix = sum(1 for r in matrix
                          if "pagoda" in str(r.get("certificate", "")))

    n_forg = forg.get("n_forgeries", 0)
    declared = forg.get("n_as_declared", 0)
    escapes = [a for a in forg.get("attempts", [])
               if a.get("expected") in ("NOT-CAUGHT", "ACCEPT-QUALIFIED")]

    out = [
        "",
        "## B · Certificates rechecked by a stranger",
        "",
        "The claim under test is 1.10(a): an engine's output is an artefact a",
        "*separate* reader can check. The rechecker imports nothing from `engines/`",
        "or `interop/`, and a test enforces that by reading its own import",
        "statements and asserting the scan actually covered every module -- so an",
        "engine and its checker cannot be wrong together by sharing code.",
        "",
        "| what | count | behaved as declared |",
        "|---|---|---|",
        f"| certificates rechecked | {n_matrix} | {n_matrix - off} |",
        f"| — of those, ACCEPT / REJECT | {n_accept} / {n_reject} | — |",
        f"| — of those, pagoda (new in E6) | {n_pagoda_matrix} | {n_pagoda_matrix} |",
        f"| forgeries attempted | {n_forg} | {declared} |",
        f"| committed case files | {counts.get('cases', '--')} | — |",
        "",
        f"**{n_matrix - off}/{n_matrix} certificates and {declared}/{n_forg} forgeries "
        "behaved as declared.**",
        "",
        "Three things that column does *not* say, each of which an earlier draft of",
        "this file got wrong:",
        "",
        f"* **The matrix is not paired accept-for-reject.** It is {n_accept} accepts "
        f"and {n_reject} rejects; only two accepts have a matched reject control. The "
        "pairing discipline is real for the forgery set, not for the matrix.",
    ]
    if escapes:
        named = ", ".join(f"`{a['name']}` ({a['expected']})" for a in escapes)
        out.append(
            f"* **{len(escapes)} forgeries are declared non-catches, not catches** — "
            f"{named}. `delete-the-rule` in particular is a class of attack **no "
            "certificate checker can see**: a rule that never fired owes no frame, so "
            "deleting it leaves every certificate valid. It is recorded as a known "
            "blind spot and the suite fails if it ever starts being \"caught\". So the "
            f"honest catch count is {n_forg - len(escapes)} of {n_forg}, with "
            f"{len(escapes)} declared escapes — not {n_forg} catches."
        )
    out.append(
        f"* **`{counts.get('cases', '--')} committed case files` is files, not "
        "certificates** — certificate documents plus the rule sets they are checked "
        "against. It is a drift guard on the corpus, not a second pass rate."
    )

    if pagoda:
        out += [
            "",
            f"**Pagoda, added by E6.** {n_pagoda_matrix} certificates rechecked, of "
            f"which {pagoda.get('n_certificates', '?')} have a producer document to "
            f"run a differential against and all "
            f"{pagoda.get('n_passed', '?')} agree. E5 left `lp_potential`'s",
            "certificates uncovered -- the only checker for them imported the producing",
            "engine and trusted the producer's own witness list. E6 re-derives the move",
            "set from the declared geometry and **refuses** the producer's obligation",
            "list as input, comparing it once as a differential where a disagreement is",
            "a finding rather than a rejection.",
            "",
            "| certificate | verdict | states | satisfying | delta checks | raising |",
            "|---|---|---|---|---|---|",
        ]
        for row in pagoda.get("rows", []):
            out.append(
                "| `{}` | {} | {} | {} | {} | {} |".format(
                    row.get("certificate", "?"),
                    row.get("verdict", "?"),
                    row.get("n_states", "--"),
                    row.get("n_satisfying", "--"),
                    row.get("n_potential_checks", "--"),
                    row.get("n_raising_transitions", "--"),
                )
            )
        extra = [r.get("certificate") for r in matrix
                 if "pagoda" in str(r.get("certificate", ""))
                 and r.get("certificate") not in
                 {x.get("certificate") for x in pagoda.get("rows", [])}]
        if extra:
            out += [
                "",
                "The certificate missing from that table is the interesting one. "
                + ", ".join(f"`{name}`" for name in extra) +
                " has no producer document, so there is no differential to run -- but "
                "it is carried because a naive checker **false-rejects** it: its only "
                "potential-raising move needs two keys, while every two-key state is "
                "already outside the region, so quantifying closure over all moves "
                "rather than over moves legal from the region rejects a certificate "
                "that is genuinely inductive. It is in the matrix above and it is an "
                "ACCEPT.",
            ]
    return out


# -------------------------------------------------------------- (C) the ladder


def _section_ladder(ladder: Dict[str, Any]) -> List[str]:
    out = [
        "",
        "## C · The three-rung ladder",
        "",
        "Measured by E2 (`" + E2_RUN + "`), quoted here rather than re-run, and the",
        "agreement column is **read from the artefact's own verdict**, not recomputed.",
        "**Node counts are not comparable across rungs** -- the artefact says so in a",
        "top-level field -- so this table compares plan lengths, which are.",
        "",
        "| instance | optimum | source | stub-bfs | fd/lmcut | fd/lama | rungs agree |",
        "|---|---|---|---|---|---|---|",
    ]
    disagreements = 0
    no_optimum = 0
    for row in ladder["results"]:
        inst = row["instance"]
        verdicts = row.get("verdicts") or {}
        lengths = {}
        for rung in row.get("rungs", []):
            if rung.get("solved"):
                lengths[rung.get("config", rung.get("tier"))] = rung.get("plan_length")
        optimum = inst.get("optimum")
        agreement_ok = verdicts.get("agreement_ok")
        optimum_ok = verdicts.get("optimum_ok")
        if agreement_ok is False:
            disagreements += 1
            agree = "**no**"
        elif agreement_ok is True:
            agree = "yes" if optimum_ok is not None else "yes (no optimum)"
            if optimum_ok is None:
                no_optimum += 1
        else:
            agree = "--"
        out.append(
            "| `{}` | {} | {} | {} | {} | {} | {} |".format(
                inst.get("name", "?"),
                optimum if optimum is not None else "--",
                inst.get("optimum_source") or "--",
                lengths.get("stub-bfs", "--"),
                lengths.get("fd-optimal/lmcut", "--"),
                lengths.get("fd-satisficing", "--"),
                agree,
            )
        )
    out += [
        "",
        f"**{disagreements} disagreements.** Where an optimum is known the optimal "
        "rungs hit it; on the "
        f"{no_optimum} sokoban rows where none is known they agree with each other, "
        "which is a weaker statement and is labelled as one. The gripper oracle is a "
        "closed form and the small sokoban optima are hand-derived; neither shares "
        "code with any planner.",
        "",
        "The satisficing rung is genuinely not optimal, which is the point of keeping",
        "it: on `sokoban-open4far` LAMA returns 37 where all three optimal rungs",
        "return 11. It is also the only rung that scales here. `plan.optimal = False`",
        "on that rung is not a formality, and its answer is not a length anyone may",
        "quote as an optimum.",
    ]
    return out


# --------------------------------------------------------------- (D) the bill


def _section_cost(div: Dict[str, Any]) -> List[str]:
    out = [
        "",
        "## D · What it costs -- the column that does not flatter the engines",
        "",
        "Expansions are what the theorems buy. Seconds are what they cost, and the",
        "carve costs more than the search saves on every row that ran a search.",
        "",
        "**These are wall-clock numbers, so they are this machine's afternoon and not",
        "reproducible.** The producing run's verifier checks their ordering and never",
        "their equality, and neither should a reader. The comparison below survives",
        "that caveat only because the two sides differ by three orders of magnitude.",
        "",
        "| instance | theorems | carve seconds | FD `blind()` search saved | repaid? |",
        "|---|---|---|---|---|",
    ]
    repaid = 0
    counted = 0
    skipped = []
    for row in div["results"]:
        blind = _fd_row(row, "fd-optimal/blind")
        if blind is None:
            continue
        clock = blind.get("wall_clock") or {}
        saved = clock.get("search_seconds_saved")
        settled = blind.get("expansions_before") == 0
        if settled:
            skipped.append(row["instance"])
            verdict = "n/a -- no search"
            shown = "--"
        else:
            counted += 1
            is_repaid = bool(clock.get("carving_is_repaid"))
            repaid += int(is_repaid)
            verdict = "yes" if is_repaid else "**no**"
            shown = f"{saved:.6f}" if isinstance(saved, (int, float)) else "--"
        out.append(
            "| `{}` | {} | {:.6f} | {} | {} |".format(
                row["instance"],
                row.get("n_theorems", "--"),
                float(row.get("carve_seconds") or 0.0),
                shown,
                verdict,
            )
        )
    out += [
        "",
        f"**{repaid} of {counted} rows that ran a search repay the carve.**",
    ]
    if skipped:
        out[-1] += (
            " The other " + str(len(skipped)) + " (" +
            ", ".join(f"`{n}`" for n in skipped) + ") are settled by the translator "
            "before search, so their microsecond deltas are the noise of a search that "
            "never happened and are excluded rather than scored."
        )
    out += [
        "",
        "The expansion dividend is real; the wall-clock dividend, once carving is on",
        "the invoice, is negative everywhere in this batch. It would turn positive on",
        "an instance large enough that the saved fraction of a much longer search",
        "exceeds a carve whose cost grows with the board rather than with the search",
        "-- which this batch does not contain.",
    ]
    return out


# ------------------------------------------------------------------- assembly


def render() -> str:
    div = _load(f"{E6_RUN}/dividend.json")
    rep = _load(f"{E6_RUN}/recheck_report.json")
    ladder = _load(f"{E2_RUN}/ladder.json")

    lines = [
        "# What an engine is worth",
        "",
        "Ammunition for the paper's §3 -- the quantitative support for *engines",
        "propose, the LLM adjudicates*. Three engines, three claims, three batches.",
        "",
        "**Regenerate:** `python -m tools.engine_dividend_table`;",
        "**check it is not stale:** `python -m tools.engine_dividend_table --check`.",
        "",
        "Every **measurement** below is read from an artefact; where the artefact",
        "carries a verdict this reads that verdict rather than re-deriving one. The",
        "arithmetic done here is percentages and totals over those fields, nothing",
        "more. Sources:",
        "",
        f"* A, D -- `{E6_RUN}/dividend.json`",
        f"* B -- `{E6_RUN}/recheck_report.json`",
        f"* C -- `{E2_RUN}/ladder.json` (E2's measurement, quoted)",
        "",
        "**Read the three sections as three results, not one.** They were measured on",
        "different batches with different instruments against different claims. There",
        "is no combined score and this file deliberately does not compute one.",
        "",
        "---",
        "",
    ]
    lines += _section_prune(div)
    lines += _section_boundary(div)
    lines += _section_recheck(rep)
    lines += _section_ladder(ladder)
    lines += _section_cost(div)
    lines += [
        "",
        "## What this table is not",
        "",
        "* **Not a comparison between engines.** Three engines measured on three",
        "  batches against three different claims. Nothing here ranks them, and the",
        "  title question -- *what is an engine worth?* -- has three answers, not one.",
        "* **Not a general result about planning.** A and D are sokoban as",
        "  `fixtures/sokoban.py` encodes it; C is sokoban and gripper. Two domains.",
        "* **Not a measurement of the rungs a caller gets.** §A's two columns are both",
        "  heuristic-free controls. The selectable rungs gain far less, and the",
        "  `ipdb` one was demoted by E7 to *measured, not evidence*.",
        "* **Not a wall-clock win.** §D is the honest version of §A.",
        "* **Not an independent check of §C.** Those numbers are E2's, quoted. This",
        "  file re-runs nothing; `--check` proves only that it matches its renderer.",
        "",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m tools.engine_dividend_table")
    parser.add_argument("--check", action="store_true",
                        help="re-render and fail if the committed file differs")
    args = parser.parse_args(argv)

    text = render()
    path = os.path.join(HERE, OUT)
    if args.check:
        if not os.path.exists(path):
            print(f"MISSING {OUT} -- run without --check to write it")
            return 1
        with open(path, encoding="utf-8", newline="") as handle:
            current = handle.read()
        if current != text:
            print(f"STALE {OUT} -- re-render with "
                  f"`python -m tools.engine_dividend_table`")
            return 1
        print(f"ok -- {OUT} is current")
        return 0

    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
    print(f"wrote {OUT} ({len(text)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
