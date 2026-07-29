"""Render the two JSON reports as the tables a reader will actually read.

The JSON is canonical and the Markdown is a rendering of it -- never the other
way round, and nothing is computed here that is not already in the JSON.  A
table with a number the machine-readable artifact does not contain is a number
nobody can re-check.
"""

from typing import Dict, List, Optional


def _cell(value, dash: str = "--") -> str:
    if value is None:
        return dash
    if isinstance(value, bool):
        return "yes" if value else "**no**"
    if isinstance(value, float):
        return "%.4f" % value
    return str(value)


def _ms(seconds: Optional[float]) -> str:
    return "--" if seconds is None else "%.1f" % (seconds * 1000.0)


def _seconds(value: Optional[float]) -> str:
    """Three decimals, sign kept. A negative saving is a cost and must read as one."""
    return "--" if value is None else "%+.3f" % value


def _pct(value: Optional[float]) -> str:
    return "--" if value is None else "%.1f%%" % value


def _points(value: Optional[float]) -> str:
    """Percentage *points*, one decimal. Not `_cell`'s four: a spread of 4.0000
    points reads as a precision the underlying counts do not have."""
    return "--" if value is None else "%.1f" % value


def ladder_markdown(report: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# The three-rung ladder, measured")
    lines.append("")
    lines.append(
        "Fastest of %d runs per cell. `stub-bfs` gives up past %s expansions."
        % (report["repeats"], "{:,}".format(report["stub_max_expansions"]))
    )
    lines.append("")
    lines.append("> **Node counts do not compare across rungs.** " +
                 str(report["node_counts_are_not_comparable_across_rungs"]))
    lines.append("")

    lines.append("## Plan length, against an oracle that is not a planner")
    lines.append("")
    lines.append("| instance | oracle | stub-bfs | fd/lmcut | fd/ipdb | fd/lama | optimum ok | rungs agree | lama >= optimum |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for entry in report["results"]:
        instance, verdict = entry["instance"], entry["verdicts"]
        lengths = {row["config"]: row for row in entry["rungs"]}

        def length_of(key: str) -> str:
            row = lengths.get(key)
            if row is None:
                return "--"
            if row.get("error"):
                return "over budget" if "over budget" in str(row["error"]) else "ERROR"
            if row.get("proved_unsolvable"):
                return "*unsolvable*"
            if row.get("not_entitled"):
                # Exhausted its space, but this rig does not let a satisficing
                # rung read that as a proof. Not an error and not an answer.
                return "*not entitled*"
            return _cell(row.get("plan_length"))

        lines.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            instance["name"], _cell(instance["optimum"]),
            length_of("stub-bfs"), length_of("fd-optimal/lmcut"),
            length_of("fd-optimal/ipdb"), length_of("fd-satisficing"),
            _cell(verdict["optimum_ok"], "n/a"),
            _cell(verdict["agreement_ok"], "n/a"),
            _cell(verdict["satisficing_ok"], "n/a"),
        ))

    lines.append("")
    lines.append("## Nodes expanded — read down a column, never across a row")
    lines.append("")
    lines.append("| instance | stub-bfs (STRIPS states) | fd/lmcut (SAS+) | fd/ipdb (SAS+) | fd/lama (SAS+) |")
    lines.append("|---|---|---|---|---|")
    for entry in report["results"]:
        rows = {row["config"]: row for row in entry["rungs"]}

        def nodes(key: str) -> str:
            row = rows.get(key)
            if row is None:
                return "--"
            if row.get("error"):
                return "over budget" if "over budget" in str(row["error"]) else "ERROR"
            return _cell((row.get("nodes") or {}).get("expanded"))

        lines.append("| `%s` | %s | %s | %s | %s |" % (
            entry["instance"]["name"], nodes("stub-bfs"), nodes("fd-optimal/lmcut"),
            nodes("fd-optimal/ipdb"), nodes("fd-satisficing"),
        ))

    lines.append("")
    lines.append("## Wall clock, in milliseconds — the column that decides which rung to call")
    lines.append("")
    lines.append(
        "`search` is what Fast Downward's search cost; `end-to-end` is what the "
        "caller waited for, driver startup and translation included. On this "
        "batch they differ by three orders of magnitude, and only the second one "
        "is a cost anybody pays."
    )
    lines.append("")
    lines.append("| instance | stub-bfs | fd/lmcut search | fd/lmcut end-to-end | fd/ipdb end-to-end | fd/lama end-to-end |")
    lines.append("|---|---|---|---|---|---|")
    for entry in report["results"]:
        rows = {row["config"]: row for row in entry["rungs"]}

        def wall(key: str) -> str:
            row = rows.get(key)
            if row is None or row.get("error"):
                return "--"
            return _ms((row.get("timing") or {}).get("wall_seconds"))

        lmcut = rows.get("fd-optimal/lmcut") or {}
        lines.append("| `%s` | %s | %s | %s | %s | %s |" % (
            entry["instance"]["name"], wall("stub-bfs"),
            _ms((lmcut.get("timing") or {}).get("search_seconds")),
            wall("fd-optimal/lmcut"), wall("fd-optimal/ipdb"), wall("fd-satisficing"),
        ))
    lines.append("")
    return "\n".join(lines)


def _prior_audit_section(report: Dict[str, object]) -> List[str]:
    """What a later audit moved, printed before any number this file quotes.

    `dividend.json` carries E7's findings as data (`prior_audit`), and this is
    the rendering of them.  It comes *first* because two of them are withdrawals:
    a reader who meets the `fd-optimal/ipdb` column before meeting §7b has
    already read a number as evidence that is not one.
    """
    audit = report.get("prior_audit")
    if not audit:
        return []
    lines = ["## What a later audit moved, before you read any column", ""]
    lines.append(
        "These are not this run's conclusions. They are findings from **%s** "
        "(run `%s`) that this artifact is answerable to, carried in "
        "`dividend.json` under `prior_audit` so the JSON says them too."
        % (audit["source"], audit["run"])
    )
    lines.append("")
    lines.append("| finding | section | applies to | what it says |")
    lines.append("|---|---|---|---|")
    for item in audit["findings"]:
        lines.append("| `%s` | %s | `%s` | %s |" % (
            item["id"], item["section"], item["applies_to"], item["finding"],
        ))
    lines.append("")
    return lines


def _audit_note(report: Dict[str, object], finding_id: str) -> Optional[str]:
    """One `prior_audit` finding by id, or None if the run predates the block."""
    for item in (report.get("prior_audit") or {}).get("findings", []):
        if item["id"] == finding_id:
            return item["finding"]
    return None


def _zero_row_section(report: Dict[str, object]) -> List[str]:
    """The instances where true theorems bought nothing, named rather than implied.

    D-020's argument is that the zero row is the informative one, and the reason
    this section exists as code rather than as a sentence somebody remembers to
    write is that `open4` spent one whole milestone in two hand-written documents
    and in no regenerable artifact.  A batch that stopped producing it would now
    stop producing this paragraph, which is a visible failure rather than a quiet
    one.
    """
    zero = []
    for entry in report["results"]:
        stub = entry["stub"]
        before, after = stub["expansions_before"], stub["expansions_after"]
        if before and before == after:
            zero.append((entry["instance"], before, after,
                         entry["n_theorems"], stub["plan_length_unchanged"]))
    if not zero:
        return [
            "**No zero row in this batch.** Every instance measured saved at "
            "least one expansion on the bundled rung. That is worth noticing "
            "rather than celebrating: `open4` is in the batch precisely because "
            "it is the instance where sixteen true theorems save nothing, so a "
            "batch with no zero row is more likely to have lost a row than to "
            "have found a dividend (DECISIONS D-020).",
            "",
        ]
    lines = ["### The zero row — where true theorems buy nothing", ""]
    lines.append(
        "DECISIONS **D-020**: the zero row is the informative one. Reporting only "
        "the instances where pruning pays would make a conditional result look "
        "unconditional, so these rows are in the table above and are named again "
        "here."
    )
    lines.append("")
    for name, before, after, n_theorems, unchanged in zero:
        lines.append(
            "* **`%s`: %d → %d expansions** — %d true theorems, %s expansions "
            "saved, plan %s. The search finds its plan before it wanders into a "
            "single dead region; pruning pays where the search would otherwise go."
            % (name, before, after, n_theorems, "zero" if before == after else "some",
               "unchanged" if unchanged else "**CHANGED — unsound**")
        )
    lines.append("")

    # The same row on the other engine. `fd-optimal/blind` is the FD control --
    # A* with a zero heuristic, the bundled BFS in different clothes -- so a zero
    # there is the same finding measured by a different search, and it is worth
    # more than the bundled zero alone because it cannot be an artifact of this
    # repo's own BFS.
    zero_names = {name for name, _, _, _, _ in zero}
    controls = []
    for entry in report["results"]:
        if entry["instance"] not in zero_names:
            continue
        for row in entry.get("fd", []):
            if row["rung"] != "fd-optimal/blind" or row["guard_refused"]:
                continue
            before, after = row["expansions_before"], row["expansions_after"]
            if before and before == after:
                controls.append((entry["instance"], row["guard"], before))
    if controls:
        lines.append(
            "The same instances on Fast Downward's blind control, which is a "
            "different search and therefore a second witness rather than a "
            "restatement: %s."
            % "; ".join("`%s` under `%s`, %d → %d"
                        % (name, guard, count, count)
                        for name, guard, count in controls)
        )
        lines.append("")

    flat = [
        entry["instance"]
        for entry in (report.get("tiebreak_sensitivity") or {}).get("summary") or []
        if entry["instance"] in zero_names
        and all(cell["ratio_min"] == cell["ratio_max"] == 1.0
                for cell in (entry["guards"] or {}).values())
    ]
    if flat:
        lines.append(
            "And the zero survives changing Fast Downward's open list: %s "
            "expand%s exactly as many states guarded as unguarded under "
            "**every** tie-break rule measured below, so the zero is not one "
            "ordering's accident."
            % (", ".join("`%s`" % name for name in flat),
               "s" if len(flat) == 1 else "")
        )
        lines.append("")
    return lines


def _twin_section(report: Dict[str, object]) -> List[str]:
    """The committed-versus-generated control, including when it finds nothing.

    A check reported only on failure is a check a reader cannot tell from an
    absent one, which is the whole reason the verdict is in the JSON.
    """
    twins = report.get("structural_twins")
    if not twins:
        return []
    pairs = ", ".join("`%s` ≡ `%s`" % (left, right) for left, right in twins["pairs"])
    lines = ["### The committed fixture against its generated copy", ""]
    lines.append("%s. %s %s" % (pairs, twins["why"], twins["compared"]))
    lines.append("")
    if twins["agree"]:
        lines.append(
            "**Every structural column agrees.** Two files on disk, one written "
            "by `fixtures.generate_all` and one by `instances.far_level(4)`, "
            "measured through the same pipeline and answering identically — so "
            "the ladder above `far4` is standing on the board the deadlock "
            "carver's README reasons about, and not on a lookalike."
        )
    else:
        lines.append("**They do not agree, and every dividend above `far4` is "
                     "therefore measured on an unexamined board:**")
        lines.append("")
        for problem in twins["problems"]:
            lines.append("* %s" % problem)
    lines.append("")
    return lines


def _wall_clock_section(report: Dict[str, object]) -> List[str]:
    """The subtraction E2 recorded three clocks for and never performed."""
    rows = [row for entry in report["results"] for row in entry["fd"]
            if row.get("wall_clock")]
    if not rows:
        return []
    sample = rows[0]["wall_clock"]

    lines = ["## The Fast Downward wall clock, with carving on the invoice", ""]
    lines.append(
        "The three raw clocks per row are in `dividend.json` under "
        "`timing`; this is the subtraction, charged against **`%s`**."
        % sample["charged_against"]
    )
    lines.append("")
    lines.append(
        "`search s` is what Fast Downward's search cost — the only clock a "
        "deadlock theorem can move, because a theorem removes transitions from "
        "the search and nothing else. `end-to-end` is %s."
        % sample["end_to_end_is_driver_startup"]
    )
    lines.append("")
    lines.append(
        "`net s` = carve − search saved. **Positive means the carve was not "
        "repaid.** `solves to repay` is how many times this exact instance would "
        "have to be re-solved from the same theorems before it was; `--` where "
        "the guard saved nothing or cost time, because no number of repeats "
        "repays a carve out of a saving that is zero or negative."
    )
    lines.append("")
    lines.append(
        "**Where `search ms saved` is under a millisecond, `solves to repay` is "
        "arithmetic on clock noise.** FD prints its search time to four decimal "
        "places and these searches take tenths of a millisecond, so a four- or "
        "five-figure repayment count on such a row means \"not in any number of "
        "solves anybody would run\", not a schedule. It is printed rather than "
        "blanked because the threshold at which it stops being noise is a "
        "judgement, and hiding the number would make that judgement for the "
        "reader."
    )
    lines.append("")
    lines.append(
        "Every figure in this table is a wall clock and therefore this machine's "
        "afternoon. `verify.py` checks that clocks are present and correctly "
        "nested and never compares one for equality; read the signs and the "
        "orders of magnitude, not the digits."
    )
    lines.append("")
    lines.append("| instance | guard | rung | search ms before | search ms after | search ms saved | carve s | net s | repaid | solves to repay | end-to-end ms before | end-to-end ms after |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for entry in report["results"]:
        for row in entry["fd"]:
            clock = row.get("wall_clock")
            if not clock:
                continue
            if row["guard_refused"]:
                lines.append("| `%s` | %s | %s | %s | *refused* | -- | %.2f | -- | -- | -- | %s | %s |" % (
                    row["instance"], row["guard"], row["rung"],
                    _ms(clock["search_seconds_before"]), clock["carve_seconds"],
                    _ms(clock["end_to_end_seconds_before"]),
                    _ms(clock["end_to_end_seconds_after"]),
                ))
                continue
            lines.append("| `%s` | %s | %s | %s | %s | %s | %.2f | %s | %s | %s | %s | %s |" % (
                row["instance"], row["guard"], row["rung"],
                _ms(clock["search_seconds_before"]),
                _ms(clock["search_seconds_after"]),
                _ms(clock["search_seconds_saved"]),
                clock["carve_seconds"],
                _seconds(clock["net_seconds_with_carving"]),
                _cell(clock["carving_is_repaid"], "n/a"),
                _cell(clock["solves_to_repay_carving"]),
                _ms(clock["end_to_end_seconds_before"]),
                _ms(clock["end_to_end_seconds_after"]),
            ))
    lines.append("")

    repaid = [row for entry in report["results"] for row in entry["fd"]
              if (row.get("wall_clock") or {}).get("carving_is_repaid")]
    if repaid:
        lines.append(
            "**%d of %d rows repaid the carve out of the search they shortened.**"
            % (len(repaid), len(rows))
        )
    else:
        lines.append(
            "**No row repaid the carve out of the search it shortened.** That is "
            "the same verdict the bundled rung reaches by its own clock, and it "
            "is the second-side number §1.9's speed clause never had."
        )
    lines.append("")
    return lines


def _tiebreak_section(report: Dict[str, object]) -> List[str]:
    """E2's G7, and the reconciliation with E7 that keeps it from overclaiming."""
    block = report.get("tiebreak_sensitivity") or {}
    rows = block.get("rows") or []
    if not rows:
        return []

    guards = block.get("guards") or []
    lines = ["## Tie-break sensitivity — E2's gap G7, measured", ""]
    lines.append("**Gap closed** — %s" % block["gap_closed"])
    lines.append("")
    lines.append("**Question** — %s" % block["question"])
    lines.append("")
    if block.get("blind_only"):
        lines.append("> **%s**" % block["blind_only"])
        lines.append("")
    note = _audit_note(report, "E7-tiebreak-invariant")
    if note:
        lines.append("> **This is the weaker of the two instruments.** %s" % note)
        lines.append("")
    if block.get("not_a_tiebreak_invariant"):
        lines.append(block["not_a_tiebreak_invariant"])
        lines.append("")
    lines.append("Excluded — %s" % block["excluded"])
    lines.append("")
    lines.append("Not measured here — %s" % block["timings_not_measured"])
    lines.append("")

    lines.append("| tie-break | `--search` | what it changes |")
    lines.append("|---|---|---|")
    for config in block["configurations"]:
        lines.append("| `%s` | `%s` | %s |" % (
            config["tiebreak"], config["search"], config["note"]))
    lines.append("")

    header = "| instance | tie-break | exp before | plan before |"
    rule = "|---|---|---|---|"
    for guard in guards:
        header += " %s after | %s ratio |" % (guard, guard)
        rule += "---|---|"
    lines.append(header)
    lines.append(rule)
    for row in rows:
        cells = "| `%s` | %s | %s | %s |" % (
            row["instance"], row["tiebreak"],
            "ERROR" if row["error"] else _cell(row["expansions_before"]),
            _cell(row["plan_length_before"]),
        )
        for guard in guards:
            cell = (row["guards"] or {}).get(guard)
            if cell is None:
                cells += " -- | -- |"
            elif cell["error"]:
                cells += " *refused* | -- |"
            else:
                cells += " %s | %s |" % (_cell(cell["expansions_after"]),
                                         _cell(cell["expansions_ratio"]))
        lines.append(cells)
    lines.append("")

    lines.append("### The two spreads the claim is about")
    lines.append("")
    lines.append(
        "`baseline spread` is how far the **absolute** blind count moves when "
        "only the open list changes — the quantity G7 warned about. `ratio "
        "spread` is how far the **dividend** moves under the same change, in "
        "percentage points. \"The ratios are stable\" is true exactly when the "
        "second is small while the first is not, and both are numbers here "
        "rather than an assurance."
    )
    lines.append("")
    lines.append("| instance | guard | baseline min | baseline max | baseline spread | dividend min | dividend max | ratio spread (pts) |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for entry in block.get("summary") or []:
        for guard in guards:
            cell = (entry["guards"] or {}).get(guard)
            if cell is None:
                continue
            lines.append("| `%s` | %s | %s | %s | %s | %s | %s | %s |" % (
                entry["instance"], guard,
                _cell(entry["baseline_min"]), _cell(entry["baseline_max"]),
                _pct(entry["baseline_spread_pct"]),
                _pct(cell["dividend_min_pct"]), _pct(cell["dividend_max_pct"]),
                _points(cell["ratio_spread_points"]),
            ))
    lines.append("")

    band = _audit_note(report, "E7-blind-band")
    if band:
        lines.append(
            "**Read the dividend columns against E7's band, not against E2's.** "
            "%s The table above is why the qualifier is needed: the band was "
            "measured under `astar()`'s open list, and these rows show what the "
            "same instances do under two others." % band
        )
        lines.append("")
    return lines


def dividend_markdown(report: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# What a proved deadlock is worth")
    lines.append("")
    lines.append("Claim under test — %s" % report["claim_under_test"])
    lines.append("")
    lines += _prior_audit_section(report)

    lines.append("## The bundled rung, which takes a pruner")
    lines.append("")
    lines.append(
        "`expansions` is the headline; `seconds` is the weaker number, because "
        "the pruner is a Python callable run per generated state and carving the "
        "theorems is a cost the blind search never pays. Both are here so neither "
        "can stand in for the other."
    )
    lines.append("")
    lines.append(
        "`net s` is the carve minus what the pruned search saved, on one "
        "invoice: **positive means the theorems cost more time than they bought**. "
        "It is a wall clock, so it is this machine's afternoon and not a "
        "reproducible number — `verify.py` checks orderings and never equality, "
        "and neither should a reader."
    )
    lines.append("")
    lines.append("| instance | family | cells | theorems (1-atom/2-atom) | carve s | exp before | exp after | saved | states cut | blind s | pruned s | saved s | net s | repaid | plan unchanged |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for entry in report["results"]:
        stub = entry["stub"]
        timing = stub["timing"]
        before, after = stub["expansions_before"], stub["expansions_after"]
        saved = "%.0f%%" % (100.0 * (1.0 - stub["expansions_ratio"])) if before else "--"
        lines.append("| `%s` | %s | %d | %d (%d/%d) | %.2f | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            entry["instance"], entry.get("family", "--"),
            entry["cells"], entry["n_theorems"],
            entry["n_singleton_theorems"], entry["n_pair_theorems"],
            entry["carve_seconds"], _cell(before), _cell(after), saved,
            _cell(stub["states_pruned"]),
            "%.3f" % timing["blind_seconds"],
            "%.3f" % timing["pruned_seconds"],
            _seconds(timing.get("seconds_saved")),
            _seconds(timing.get("net_seconds_with_carving")),
            _cell(timing.get("carving_is_repaid"), "n/a"),
            _cell(stub["plan_length_unchanged"]),
        ))

    lines.append("")
    lines += _zero_row_section(report)
    lines += _twin_section(report)
    lines.append("## The Fast Downward rungs, which do not")
    lines.append("")
    lines.append(
        "No pruning hook, so the theorems are compiled into the task instead "
        "(`bench/compile_theorems.py`). `singleton` expresses the corner "
        "deadlocks and stays inside STRIPS. `full` adds the pair deadlocks as a "
        "`forall`, which FD turns into an axiom -- the two admissible heuristics "
        "refuse it. `indexed` is the same pair guard with the quantifier removed "
        "for static selectors: pure STRIPS, and they accept it. Every guarded "
        "plan below was replayed against the **original** domain by the rig's "
        "own validator."
    )
    lines.append("")
    lines.append(
        "Read `indexed` against `singleton` on the two admissible rows: that is "
        "what the pair theorems cost once they can be delivered at all. FD "
        "compiles a negative precondition on a fluent into one operator copy per "
        "other value of that variable, which is the task-size column blowing up "
        "and the reason `lmcut` expands *more* with the pair theorems than "
        "without them."
    )
    lines.append("")
    lines.append(
        "`fd-optimal/blind` is a **control, not a rung** — `choose_tier` never "
        "selects it. A\\* with a zero heuristic is the bundled BFS in different "
        "clothes, so it shows what the theorems are worth to a search that has "
        "no other way of knowing a region is dead. Read it against the two rows "
        "below it: that difference is the whole finding."
    )
    lines.append("")
    ipdb_note = _audit_note(report, "E7-ipdb-withdrawn")
    if ipdb_note:
        lines.append(
            "> **Do not read the `fd-optimal/ipdb` rows below as a dividend in "
            "either direction.** %s They are printed because deleting them would "
            "hide the artefact rather than label it." % ipdb_note
        )
        lines.append("")
    lmcut_note = _audit_note(report, "E7-lmcut-range")
    if lmcut_note:
        lines.append(
            "> **And the `fd-optimal/lmcut` rows are smaller than they look.** %s"
            % lmcut_note
        )
        lines.append("")
    lines.append("| instance | guard | theorems carried | rung | exp before | exp after | task size before | task size after | plan delta | honest |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for entry in report["results"]:
        for row in entry["fd"]:
            size = row["guard_size"]
            carried = "%d/%d" % (size["theorems_expressed"], size["theorems_total"])
            if row["guard_refused"]:
                lines.append("| `%s` | %s | %s | %s | %s | *refused* | %s | -- | -- | -- |" % (
                    row["instance"], row["guard"], carried, row["rung"],
                    _cell(row["expansions_before"]), _cell(row["task_size_before"]),
                ))
                continue
            lines.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                row["instance"], row["guard"], carried, row["rung"],
                _cell(row["expansions_before"]), _cell(row["expansions_after"]),
                _cell(row["task_size_before"]), _cell(row["task_size_after"]),
                _cell(row["plan_length_delta"]), _cell(row["dividend_is_honest"], "n/a"),
            ))

    settled = sorted({
        row["instance"] for entry in report["results"] for row in entry["fd"]
        if row["expansions_before"] == 0
    })
    if settled:
        lines.append("")
        lines.append(
            "**Zero expansions before *and* after on %s.** Fast Downward's "
            "translator settles those instances during relaxed reachability and "
            "the search never starts, so there is no search for a deadlock "
            "theorem to shorten. The task size of 4 in those rows is the "
            "degenerate task the translator emits once it has decided."
            % ", ".join("`%s`" % name for name in settled)
        )
    lines.append("")
    lines += _wall_clock_section(report)
    lines += _tiebreak_section(report)
    return "\n".join(lines)
