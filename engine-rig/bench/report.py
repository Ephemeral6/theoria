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


def dividend_markdown(report: Dict[str, object]) -> str:
    lines: List[str] = []
    lines.append("# What a proved deadlock is worth")
    lines.append("")
    lines.append("Claim under test — %s" % report["claim_under_test"])
    lines.append("")

    lines.append("## The bundled rung, which takes a pruner")
    lines.append("")
    lines.append(
        "`expansions` is the headline; `seconds` is the weaker number, because "
        "the pruner is a Python callable run per generated state and carving the "
        "theorems is a cost the blind search never pays. Both are here so neither "
        "can stand in for the other."
    )
    lines.append("")
    lines.append("| instance | cells | theorems (1-atom/2-atom) | carve s | exp before | exp after | saved | states cut | blind s | pruned s | plan unchanged |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for entry in report["results"]:
        stub = entry["stub"]
        before, after = stub["expansions_before"], stub["expansions_after"]
        saved = "%.0f%%" % (100.0 * (1.0 - stub["expansions_ratio"])) if before else "--"
        lines.append("| `%s` | %d | %d (%d/%d) | %.2f | %s | %s | %s | %s | %s | %s | %s |" % (
            entry["instance"], entry["cells"], entry["n_theorems"],
            entry["n_singleton_theorems"], entry["n_pair_theorems"],
            entry["carve_seconds"], _cell(before), _cell(after), saved,
            _cell(stub["states_pruned"]),
            "%.3f" % stub["timing"]["blind_seconds"],
            "%.3f" % stub["timing"]["pruned_seconds"],
            _cell(stub["plan_length_unchanged"]),
        ))

    lines.append("")
    lines.append("## The Fast Downward rungs, which do not")
    lines.append("")
    lines.append(
        "No pruning hook, so the theorems are compiled into the task instead "
        "(`bench/compile_theorems.py`). `singleton` expresses the corner "
        "deadlocks and stays inside STRIPS; `full` adds the pair deadlocks and "
        "needs `:adl`. Every guarded plan below was replayed against the "
        "**original** domain by the rig's own validator."
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
    return "\n".join(lines)
