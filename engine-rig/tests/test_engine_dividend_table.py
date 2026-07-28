"""`tools/engine_dividend_table.py`: the paper's §3 table, checked as a *quotation*.

The module computes nothing.  Every number in `ENGINE_DIVIDEND.md` is supposed to
be a field of an artefact some other run wrote and verified, and the only thing
this module may add is arrangement.  So these tests read the three artefacts
themselves and compare cell against field -- there are almost no hard-coded
numbers below, because a test that transcribed the numbers would pass just as
happily against a renderer that had transcribed them too.

The exceptions are deliberate.  §A's Fast Downward column is pinned with real
literals (`837`/`610`, `3070`/`2762`, `7196`/`6365`) because the bug this file
exists to catch produced an *all-`--` column that still rendered as a valid
table*: `_fd_row` matched on `config`, which the artefact does not key the rung
by, so every lookup missed and every cell fell back to the em-dash.  A test that
asserted "the table renders" was green throughout.

That bug has a living relative, and it is recorded here rather than papered over:
the tie-break table's two *dividend* columns are `--` on every row because the
renderer reads `dividend_min` / `dividend_max` and the artefact writes
`guards.<guard>.dividend_min_pct` / `dividend_max_pct`.  See
`test_the_tiebreak_table_carries_the_dividend_band_the_artefact_measured`, which
was a strict xfail until the module was fixed: it pins the real numbers, and the
module is fixed, which is when the marker comes off.

The other reads that had bugs get a perturbation test each rather than a
transcription, because a renderer that reads the *wrong* field and a renderer
that reads the right one agree on every value until you move one of them:
`carried` (`guard_size.theorems_expressed`, not `n_singleton_theorems`), §A's
plan column (`plan_length_unchanged`, not the absent `plan_unchanged` under a
`True` default), and §C's agreement column (`verdicts.agreement_ok`, not a
recomputation that scored "no known optimum" as a disagreement and printed
**no** against three admissible planners).

Nothing here needs a planner.  The module reads JSON and writes Markdown, so the
whole file runs on a machine with no Fast Downward -- and no test below is
skipped for the want of one.
"""

import copy
import json
import os
import re
import shutil

import pytest

from tools import engine_dividend_table as edt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMITTED = os.path.join(HERE, edt.OUT)


# ------------------------------------------------------------------- artefacts
#
# Read here rather than through the module, so the comparison below is between
# two readers and not between the module and itself.

def artefact(relative):
    with open(os.path.join(HERE, relative), encoding="utf-8") as handle:
        return json.load(handle)


def dividend():
    return artefact("%s/dividend.json" % edt.E6_RUN)


def recheck_report():
    return artefact("%s/recheck_report.json" % edt.E6_RUN)


def ladder():
    return artefact("%s/ladder.json" % edt.E2_RUN)


def blind_row(row):
    """The §A/§D lookup, transcribed independently of the module's own.

    Keyed on `rung`, which is what the artefact calls it.  `config` on these
    entries is absent; on the nested `baseline` it is Fast Downward's search
    string, which is the confusion the empty-column bug came out of.
    """
    for entry in row.get("fd") or []:
        if entry.get("rung") == "fd-optimal/blind" and entry.get("guard") == "singleton":
            return entry
    return None


def prune_order(div):
    """The row order §A promises: the zero row first, batch order after.

    Transcribed rather than imported, because "rendered first" is a claim of the
    prose and an earlier draft got it by accident of batch order.
    """
    return sorted(div["results"],
                  key=lambda row: 0 if ((row.get("stub") or {}).get("expansions_saved") == 0
                                        and (row.get("n_theorems") or 0) > 0) else 1)


# --------------------------------------------------------------- markdown tools

def section(markdown, letter):
    """The body of the `## <letter> ...` section, `### ` subsections included."""
    body, collecting = [], False
    for line in markdown.splitlines():
        if line.startswith("## "):
            collecting = line[3:].startswith(letter + " ")
        elif collecting:
            body.append(line)
    assert body, "no section %s in the rendered table" % letter
    return "\n".join(body)


def flat(text):
    """One line, single-spaced -- for prose the renderer hard-wraps.

    A wrapped sentence must still be assertable in full; collapsing the
    whitespace is what lets these tests pin a whole claim instead of the longest
    fragment that happens to fit on one rendered line.
    """
    return " ".join(text.split())


def tables(body):
    """Every Markdown table in `body`, as a list of blocks of `|` lines.

    §A carries two tables now -- the dividend and the tie-break sensitivity --
    and they share instance names, so a section-wide row scan silently returns
    whichever came last.  It did: the tie-break `far6` was shadowing the
    dividend `far6`.
    """
    blocks, current = [], []
    for line in body.splitlines():
        if line.startswith("|"):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return blocks


def table(body, *headings):
    """The one table in `body` whose header row carries every `heading`."""
    found = [block for block in tables(body)
             if all(heading in block[0] for heading in headings)]
    assert len(found) == 1, "%d tables match %r" % (len(found), headings)
    return found[0]


NAMED = re.compile(r"`([^`]+)`")


def rows(block):
    """`{instance name: [cells]}` for the data rows of one table block.

    Keyed on the first backticked token, so §A's twin marker -- `far4` is
    rendered `` `far4` †open4far`` -- does not become part of the key.  The
    marker itself is asserted separately, on the raw cell.
    """
    out = {}
    for line in block:
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        out[NAMED.match(cells[0]).group(1)] = cells
    return out


def prune_table(markdown):
    return rows(table(section(markdown, "A"), "carried", "plan length"))


def tiebreak_table(markdown):
    return rows(table(section(markdown, "A"), "baseline min", "dividend max"))


def pagoda_table(markdown):
    return rows(table(section(markdown, "B"), "delta checks"))


def ladder_table(markdown):
    return rows(table(section(markdown, "C"), "rungs agree"))


def cost_table(markdown):
    return rows(table(section(markdown, "D"), "carve seconds"))


def render_with(monkeypatch, div=None, rep=None, lad=None):
    """`render()` over deep copies of the artefacts, with one of them perturbed.

    The files on disk are never touched: `_load` is replaced, so the mutation
    lives and dies inside the call.
    """
    real = edt._load

    def fake(relative):
        payload = copy.deepcopy(real(relative))
        for suffix, mutate in (("dividend.json", div),
                               ("recheck_report.json", rep),
                               ("ladder.json", lad)):
            if relative.endswith(suffix) and mutate is not None:
                mutate(payload)
        return payload

    monkeypatch.setattr(edt, "_load", fake)
    return edt.render()


# ------------------------------------------------------- the file is not stale

def test_the_committed_table_is_what_the_module_renders_today():
    """§1 of the contract: a stale table is a failing check, not a document."""
    assert edt.main(["--check"]) == 0


def test_the_committed_bytes_are_the_rendered_bytes_with_lf_endings():
    """`--check` reads with `newline=""`, so CRLF would already fail it -- but the
    failure would read as "stale" rather than "your checkout mangled it"."""
    with open(COMMITTED, "rb") as handle:
        raw = handle.read()
    assert b"\r\n" not in raw
    assert raw == edt.render().encode("utf-8")


def test_rendering_is_deterministic():
    first, second = edt.render(), edt.render()
    assert first == second
    assert "\r" not in first
    assert first.endswith("\n")


def test_a_perturbed_file_fails_the_check(tmp_path, capsys):
    """Against a *copy*.  `OUT` is joined onto `HERE`, and an absolute value
    wins that join, so the real `ENGINE_DIVIDEND.md` is never opened here."""
    copied = str(tmp_path / "ENGINE_DIVIDEND.md")
    shutil.copyfile(COMMITTED, copied)
    with open(copied, "r+", encoding="utf-8", newline="") as handle:
        text = handle.read()
        assert "| 47 | 47 |" in text, "the zero row moved; pick another edit"
        handle.seek(0)
        handle.write(text.replace("| 47 | 47 |", "| 47 | 46 |"))
        handle.truncate()

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(edt, "OUT", copied)
        assert edt.main(["--check"]) == 1
    assert "STALE" in capsys.readouterr().out
    # ...and the real file is still the real file.
    assert edt.main(["--check"]) == 0


def test_a_missing_file_is_reported_rather_than_silently_passing(tmp_path, capsys):
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(edt, "OUT", str(tmp_path / "nowhere" / "X.md"))
        assert edt.main(["--check"]) == 1
    assert "MISSING" in capsys.readouterr().out


def test_writing_then_checking_round_trips(tmp_path):
    written = str(tmp_path / "ENGINE_DIVIDEND.md")
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(edt, "OUT", written)
        assert edt.main([]) == 0
        assert edt.main(["--check"]) == 0
    with open(written, "rb") as handle:
        assert b"\r\n" not in handle.read()


# ------------------------------------------------- (A) the Fast Downward column

def test_the_fd_column_carries_the_measured_numbers_and_not_em_dashes():
    """The empty-column regression, pinned with literals on purpose.

    `_fd_row` once matched `entry["config"]`, a key these entries do not have,
    so every FD cell fell back to `--` and the table still rendered.  These six
    numbers are the ones a reader of §3 would quote.  The `carried` column moved
    them one place right; the numbers themselves did not move.
    """
    table_ = prune_table(edt.render())
    assert table_["far4"][6:9] == ["837", "610", "27.1%"]
    assert table_["far6"][6:9] == ["3070", "2762", "10.0%"]
    assert table_["far7"][6:9] == ["7196", "6365", "11.5%"]


def test_the_rung_is_the_key_the_artefact_uses_and_config_is_not():
    """Why the literals above are needed: the wrong key misses *silently*.

    Nothing raises, nothing is empty, and the column is uniformly `--` -- which
    is indistinguishable from "the planner did not report" to a reader.
    """
    div = dividend()
    by_config = [entry for row in div["results"] for entry in row.get("fd") or []
                 if entry.get("config") == "fd-optimal/blind"]
    assert by_config == [], "if `config` ever became the rung key, rewrite _fd_row"
    assert [row["instance"] for row in div["results"] if blind_row(row)] == \
        [row["instance"] for row in div["results"]]


def test_every_section_a_cell_is_a_field_of_the_dividend_artefact():
    """The traceability claim, row by row, with no number written in this file.

    The single derived cell is the percentage, and it is asserted to be exactly
    the ratio of the two counts it sits between -- i.e. arrangement, not a
    second measurement.  Ten columns now: `carried` sits between the theorem
    count and the bundled rung.
    """
    div = dividend()
    table_ = prune_table(edt.render())
    expected = [row for row in prune_order(div)
                if (row.get("stub") or {}).get("expansions_before") is not None]
    assert list(table_) == [row["instance"] for row in expected]

    for row in expected:
        cells = table_[row["instance"]]
        stub, blind = row["stub"], blind_row(row)
        assert cells[1] == str(row["n_theorems"])
        assert cells[2] == str(blind["guard_size"]["theorems_expressed"])
        assert cells[3] == str(stub["expansions_before"])
        assert cells[4] == str(stub["expansions_after"])
        assert cells[5] == "%.1f%%" % (
            100.0 * (stub["expansions_before"] - stub["expansions_after"])
            / stub["expansions_before"])
        assert cells[6] == str(blind["expansions_before"])
        assert cells[7] == str(blind["expansions_after"])
        assert cells[8] == ("--" if not blind["expansions_before"] else "%.1f%%" % (
            100.0 * (blind["expansions_before"] - blind["expansions_after"])
            / blind["expansions_before"]))
        assert cells[9] == ("unchanged" if stub["plan_length_unchanged"]
                            else "**CHANGED**")


# ------------------------------------------------------------ (A) `carried`

def test_the_carried_column_is_the_theorems_the_guard_could_express():
    """`40` proved, `8` carried -- and the two must not be confused in §3.

    The FD column is the `singleton` guard, which expresses size-1 theorems
    only, so `far7`'s dividend was bought with eight of its forty theorems.  A
    table printing only "40" invites the reader to price the whole proof effort
    against the whole saving.
    """
    div = dividend()
    far7 = next(row for row in div["results"] if row["instance"] == "far7")
    assert far7["n_theorems"] == 40
    assert blind_row(far7)["guard_size"]["theorems_expressed"] == 8

    cells = prune_table(edt.render())["far7"]
    assert cells[1] == "40"
    assert cells[2] == "8"
    prose = flat(section(edt.render(), "A"))
    assert ("`carried` is the number of theorems the compiled guard could express, "
            "against the number proved.") in prose
    assert ("a row reading `40` theorems and `8` carried bought its dividend with "
            "eight.") in prose


def test_the_carried_column_reads_theorems_expressed_and_not_the_lookalike():
    """Every row of this batch has `n_singleton_theorems == theorems_expressed`,
    so the two readings are indistinguishable until one of them is moved.

    They are not the same quantity: one counts the theorems of size 1 that were
    proved, the other counts what the *compiled guard* carries, and a guard that
    dropped a theorem in compilation would show up only in the second.
    """
    div = dividend()
    assert all(row["n_singleton_theorems"]
               == blind_row(row)["guard_size"]["theorems_expressed"]
               for row in div["results"]), "the perturbation below is no longer sharp"

    def shrink_far7s_guard(payload):
        for row in payload["results"]:
            if row["instance"] == "far7":
                for entry in row["fd"]:
                    if entry["rung"] == "fd-optimal/blind" and entry["guard"] == "singleton":
                        entry["guard_size"]["theorems_expressed"] = 5
                assert row["n_singleton_theorems"] == 8  # the lookalike, untouched

    with pytest.MonkeyPatch.context() as patch:
        perturbed = render_with(patch, div=shrink_far7s_guard)
    assert prune_table(perturbed)["far7"][2] == "5"
    assert prune_table(edt.render())["far7"][2] == "8"


# --------------------------------------------------------- (A) the plan column

def test_the_plan_column_reads_the_field_the_artefact_writes():
    """The column that must never quietly read "unchanged".

    An earlier draft read `stub["plan_unchanged"]` -- a key no artefact has --
    through `.get(..., True)`, so the column said `unchanged` on every row
    including one where the guard had shortened a plan, which is the one thing
    a sound pruner may not do.  Two perturbations: the field made false, and the
    field removed.  Both must render **CHANGED**; neither may render silence.
    """
    div = dividend()
    assert all("plan_unchanged" not in row["stub"] for row in div["results"]), \
        "if the artefact ever gains `plan_unchanged`, decide which field is canon"
    assert all(row["stub"]["plan_length_unchanged"] for row in div["results"])
    assert {cells[9] for cells in prune_table(edt.render()).values()} == {"unchanged"}

    def far6_changed_its_plan(payload):
        for row in payload["results"]:
            if row["instance"] == "far6":
                row["stub"]["plan_length_unchanged"] = False

    def far6_lost_the_field(payload):
        for row in payload["results"]:
            if row["instance"] == "far6":
                del row["stub"]["plan_length_unchanged"]

    for mutate in (far6_changed_its_plan, far6_lost_the_field):
        with pytest.MonkeyPatch.context() as patch:
            perturbed = prune_table(render_with(patch, div=mutate))
        assert perturbed["far6"][9] == "**CHANGED**", mutate.__name__
        assert [cells[9] for name, cells in perturbed.items() if name != "far6"] \
            == ["unchanged"] * (len(perturbed) - 1)


# ----------------------------------------------------------- (A) the zero row

def test_the_zero_row_is_present_first_and_says_what_it_is():
    """D-020's row, and the whole reason §A is stated conditionally.

    A batch that quietly dropped `open4` would leave an all-positive table --
    which is the shape a publication-biased batch has, and is exactly what a
    reader cannot detect from the table alone.
    """
    div = dividend()
    zero = next(row for row in div["results"] if row["instance"] == "open4")
    assert zero["n_theorems"] == 16
    assert zero["stub"]["expansions_before"] == zero["stub"]["expansions_after"] == 47

    body = section(edt.render(), "A")
    table_ = prune_table(edt.render())
    assert list(table_)[0] == "open4", "the prose says this row is rendered first"
    assert table_["open4"][:6] == ["`open4`", "16", "8", "47", "47", "0.0%"]
    assert "**The zero row.**" in body
    assert "`open4` proves **16 true theorems and saves nothing**" in body
    assert "47 expansions before, 47 after" in body
    assert "the pruner fired **%d times**" % zero["stub"]["states_pruned"] in body


def test_the_zero_row_is_sorted_first_rather_than_first_by_luck():
    """The claim is "rendered first", and the batch order used to supply it.

    Moving `open4` to the end of `results` must not move it in the table; if it
    does, the prose is falsified by a reordering nobody would think to check.
    """
    def send_the_zero_row_last(payload):
        rest = [row for row in payload["results"] if row["instance"] != "open4"]
        zero = [row for row in payload["results"] if row["instance"] == "open4"]
        payload["results"] = rest + zero

    with pytest.MonkeyPatch.context() as patch:
        perturbed = render_with(patch, div=send_the_zero_row_last)
    assert list(prune_table(perturbed))[0] == "open4"
    # ...and the rest keeps its batch order behind it.
    assert list(prune_table(perturbed)) == list(prune_table(edt.render()))


def test_a_batch_with_no_zero_row_says_so_rather_than_saying_nothing():
    """The renderer's other branch: silence is the failure mode, so it must not
    be reachable by deleting the row."""
    def drop_the_zero(div):
        div["results"] = [row for row in div["results"]
                          if (row.get("stub") or {}).get("expansions_saved") != 0
                          or not (row.get("n_theorems") or 0)]

    with pytest.MonkeyPatch.context() as patch:
        perturbed = render_with(patch, div=drop_the_zero)
    assert "open4" not in prune_table(perturbed)
    assert "This batch contains no instance with theorems and no saving" in \
        section(perturbed, "A")


# ---------------------------------------------------- (A) the settled ringstucks

def test_the_ringstuck_rows_are_settled_by_the_translator_and_say_so():
    """`0 | 0 | --` is a finding, not a gap in the data.

    FD's translator settles these during relaxed reachability, so no search ever
    starts.  Rendered bare, the three cells read as a failed measurement; the
    note is what makes them a result, and it names every row it covers.
    """
    div = dividend()
    settled = [row["instance"] for row in prune_order(div)
               if (blind_row(row) or {}).get("expansions_before") == 0]
    assert settled, "the batch is supposed to contain translator-settled rows"
    assert all(name.startswith("ringstuck") for name in settled), settled

    body = section(edt.render(), "A")
    table_ = prune_table(edt.render())
    for name in settled:
        cells = table_[name]
        assert cells[6:9] == ["0", "0", "--"]
        # ...and the bundled rung on the same board did do work, which is the
        # contrast the note explains.
        assert int(cells[3]) > int(cells[4]) > 0

    first = next(row for row in prune_order(div) if row["instance"] == settled[0])
    note = next(line for line in body.splitlines()
                if line.startswith("**The `0 | 0 | --` rows are not missing data.**"))
    for name in settled:
        assert "`%s`" % name in note
    assert "relaxed reachability" in note
    assert "%d -> %d on `%s`" % (first["stub"]["expansions_before"],
                                 first["stub"]["expansions_after"],
                                 settled[0]) in note


# ------------------------------------------------------------ (A) the twins

def test_the_duplicate_board_is_marked_and_the_batch_size_is_stated_net_of_it():
    """Eleven rows, ten boards.  `far4` and `open4far` are the same board.

    The rows are printed twice on purpose -- their agreement is a measurement
    across two files -- but a reader counting rows would over-count the batch,
    and §3 quotes batch sizes.
    """
    div = dividend()
    pairs = div["structural_twins"]["pairs"]
    assert pairs == [["open4far", "far4"]]
    assert div["structural_twins"]["agree"] is True

    body = section(edt.render(), "A")
    table_ = prune_table(edt.render())
    assert table_["far4"][0] == "`far4` †open4far"
    assert table_["open4far"][0] == "`open4far`"
    # The twin rows agree column for column, which is what makes them one board.
    assert table_["far4"][1:] == table_["open4far"][1:]

    n_rows = len(table_)
    assert "† **`far4` ≡ `open4far`**" in body
    assert ("the batch is **%d distinct boards**, not %d." % (n_rows - len(pairs), n_rows)
            in flat(body))


# ------------------------------------------------------ (A) tie-break sensitivity

def test_the_tiebreak_table_is_the_artefacts_baseline_band():
    """One number per cell is one open list's number, and §A now says so.

    The absolute expansion counts in the dividend table above move by 44-82%
    across three tie-break rules; this table is what stops the headline counts
    being read as properties of the instance.
    """
    summary = dividend()["tiebreak_sensitivity"]["summary"]
    assert summary, "the artefact stopped carrying the tie-break block"
    table_ = tiebreak_table(edt.render())
    assert list(table_) == [row["instance"] for row in summary]

    for row in summary:
        cells = table_[row["instance"]]
        assert cells[1] == str(row["baseline_min"])
        assert cells[2] == str(row["baseline_max"])
    # The band that makes the point, pinned: far7 is 5508..8172 blind expansions
    # for one and the same instance and guard.
    assert table_["far7"][1:3] == ["5508", "8172"]
    assert "the *dividends* move little" in flat(section(edt.render(), "A"))


# Was a strict xfail: `_section_prune` read srow['dividend_min'] / ['dividend_max'],
# which no summary row has -- the artefact writes guards.<guard>.dividend_min_pct /
# dividend_max_pct, so both dividend columns rendered `--` on every row while the
# prose above them claimed the dividends move little. Same failure mode as the
# config/rung bug: a silent all-em-dash column in a table that still renders.
# The module now reads the right field and the marker is off.
def test_the_tiebreak_table_carries_the_dividend_band_the_artefact_measured():
    """The half of that table which is currently empty.

    `open4far` is measured at 21.6%-27.3% under the `singleton` guard across the
    three rules -- a five-point spread against a 44% spread in the baseline,
    which is precisely the claim the surrounding prose makes.  None of it
    reaches the page.
    """
    summary = dividend()["tiebreak_sensitivity"]["summary"]
    table_ = tiebreak_table(edt.render())
    for row in summary:
        band = row["guards"][edt.GUARD]
        cells = table_[row["instance"]]
        assert cells[3] == "%.1f%%" % band["dividend_min_pct"]
        assert cells[4] == "%.1f%%" % band["dividend_max_pct"]
    assert table_["open4far"][3:5] == ["21.6%", "27.3%"]


# ------------------------------------------------------------- (A) the framing

def test_section_a_labels_both_of_its_searches_controls():
    """The misquotation §A is arranged to prevent.

    Neither column is a rung the ladder would hand a caller: the bundled BFS is
    the determinism-pinned default and `astar(blind())` is the same search with
    a zero heuristic.  A reader who takes 27.1% as "what Fast Downward gains"
    has been misled by the table, not by the paper.
    """
    prose = flat(section(edt.render(), "A"))
    assert ("Both searches here are **controls, not rungs the ladder ever selects**"
            in prose)
    assert ("The rungs a caller would actually get -- lmcut, ipdb, lama -- gain far "
            "less or nothing" in prose)
    assert "this table must not be quoted on its own" in prose
    assert ("**Not a measurement of the rungs a caller gets.** §A's two columns are "
            "both heuristic-free controls." in flat(edt.render()))


# --------------------------------------------------------------- (B) the recheck

def test_section_b_counts_are_the_artefacts_counts():
    """Every cell of §B's summary block, built from the artefact and compared
    against the rendered line -- including the two the previous draft got wrong.

    `matrix rows` is 26 certificate rechecks, 24 accepts and 2 rejects, and the
    accept/reject split is counted from the matrix here rather than read from a
    `counts` field, because the split is the claim ("not paired
    accept-for-reject") the bullet under the table makes.
    """
    report = recheck_report()
    counts, matrix, forg = report["counts"], report["matrix"], report["forgeries"]
    body = section(edt.render(), "B")

    n_matrix = len(matrix)
    assert n_matrix == counts["matrix_rows"]
    ok = n_matrix - counts["matrix_off_script"]
    n_accept = sum(1 for row in matrix if row["verdict"] == "ACCEPT")
    n_reject = sum(1 for row in matrix if row["verdict"] == "REJECT")
    assert n_accept + n_reject == n_matrix, "a third verdict would need a third column"
    n_pagoda = sum(1 for row in matrix if "pagoda" in row["certificate"])

    assert "| certificates rechecked | %d | %d |" % (n_matrix, ok) in body
    assert "| — of those, ACCEPT / REJECT | %d / %d | — |" % (n_accept, n_reject) in body
    assert "| — of those, pagoda (new in E6) | %d | %d |" % (n_pagoda, n_pagoda) in body
    assert "| forgeries attempted | %d | %d |" % (
        forg["n_forgeries"], forg["n_as_declared"]) in body
    assert "| committed case files | %d | — |" % counts["cases"] in body
    assert "**%d/%d certificates and %d/%d forgeries behaved as declared.**" % (
        ok, n_matrix, forg["n_as_declared"], forg["n_forgeries"]) in body

    # The two corrections, stated in the prose rather than only in the cells.
    assert ("It is %d accepts and %d rejects; only two accepts have a matched "
            "reject control." % (n_accept, n_reject)) in flat(body)
    assert ("* **`%d committed case files` is files, not certificates**"
            % counts["cases"]) in body


def test_section_b_counts_the_matrix_it_was_given():
    """"26" must be the length of the matrix, not a number in a `counts` block.

    Both are in the artefact and both say 26 today, so only a perturbation tells
    them apart -- and the matrix is the one the accept/reject split is drawn
    from, so a renderer reading the other could print a split that does not add
    up to its own total.
    """
    def flip_one_accept_to_reject(rep):
        for row in rep["matrix"]:
            if row["verdict"] == "ACCEPT":
                row["verdict"] = "REJECT"
                return
        raise AssertionError("no ACCEPT row to flip")

    with pytest.MonkeyPatch.context() as patch:
        perturbed = section(render_with(patch, rep=flip_one_accept_to_reject), "B")
    assert "| — of those, ACCEPT / REJECT | 23 / 3 | — |" in perturbed
    assert "| — of those, ACCEPT / REJECT | 24 / 2 | — |" in section(edt.render(), "B")


def test_section_b_states_the_two_declared_escapes_rather_than_42_catches():
    """The forgery framing, corrected: 40 caught, 2 declared escapes.

    "42/42 behaved as declared" is true and is not a catch rate -- two of the
    forty-two are declared *non*-catches, one of which (`delete-the-rule`) no
    certificate checker can see at all.  Printing 42 as a catch count would
    claim exactly the coverage the blind spot denies.
    """
    forg = recheck_report()["forgeries"]
    escapes = [a for a in forg["attempts"]
               if a["expected"] in ("NOT-CAUGHT", "ACCEPT-QUALIFIED")]
    assert [(a["name"], a["expected"]) for a in escapes] == [
        ("region-reaching-outside-the-constraint", "ACCEPT-QUALIFIED"),
        ("delete-the-rule", "NOT-CAUGHT"),
    ]

    body = flat(section(edt.render(), "B"))
    assert "**%d forgeries are declared non-catches, not catches**" % len(escapes) in body
    for attempt in escapes:
        assert "`%s` (%s)" % (attempt["name"], attempt["expected"]) in body
    assert ("So the honest catch count is %d of %d, with %d declared escapes — not "
            "%d catches." % (forg["n_forgeries"] - len(escapes), forg["n_forgeries"],
                             len(escapes), forg["n_forgeries"])) in body
    assert "no certificate checker can see" in body


def test_section_b_pagoda_rows_are_the_artefacts_rows():
    """Four pagoda certificates are rechecked; three have a producer document.

    The differential table lists the three; the fourth is in the matrix and is
    named underneath, because a table with a row missing and no note reads as a
    certificate that was quietly dropped.
    """
    report = recheck_report()
    pagoda = report["pagoda"]
    body = section(edt.render(), "B")
    table_ = pagoda_table(edt.render())
    assert list(table_) == [row["certificate"] for row in pagoda["rows"]]

    for row in pagoda["rows"]:
        cells = table_[row["certificate"]]
        assert "n_region" not in row, "if the field is renamed, follow it in the module"
        assert cells[1] == row["verdict"]
        assert cells[2] == str(row["n_states"])
        assert cells[3] == str(row["n_satisfying"])
        assert cells[4] == str(row["n_potential_checks"])
        assert cells[5] == str(row["n_raising_transitions"])

    # The pagoda block and the `counts` block are two statements of the same
    # thing, and the old pass-rate line quoted the second; keep both pinned.
    assert pagoda["n_certificates"] == report["counts"]["pagoda_certificates"]
    assert pagoda["n_passed"] == report["counts"]["pagoda_passed"]

    in_matrix = [row["certificate"] for row in report["matrix"]
                 if "pagoda" in row["certificate"]]
    missing = [name for name in in_matrix if name not in table_]
    assert missing == ["keyed-gate-pagoda"]
    assert ("**Pagoda, added by E6.** %d certificates rechecked, of which %d have a "
            "producer document to run a differential against and all %d agree."
            % (len(in_matrix), pagoda["n_certificates"], pagoda["n_passed"])) in flat(body)
    for name in missing:
        assert "`%s` has no producer document" % name in flat(body)


def test_section_b_satisfying_column_is_the_field_the_artefact_writes():
    """`n_satisfying` -- the states inside the region -- not the absent `n_region`.

    The old name is not in the artefact, so reading it produced `--`; the column
    it sits in is the one that says how much of the state space the certificate
    actually constrains.
    """
    def widen_the_first_region(rep):
        rep["pagoda"]["rows"][0]["n_satisfying"] = 9

    with pytest.MonkeyPatch.context() as patch:
        perturbed = pagoda_table(render_with(patch, rep=widen_the_first_region))
    first = recheck_report()["pagoda"]["rows"][0]["certificate"]
    assert perturbed[first][3] == "9"
    assert pagoda_table(edt.render())[first][3] == "8"


def test_a_changed_count_moves_the_rendered_pass_rate_and_nothing_else():
    """The no-recomputation claim, tested by moving a field and watching the cell.

    A renderer holding its own copy of "42" would be green on every assertion
    above and would not move here.
    """
    baseline = edt.render()

    def fewer_forgeries(rep):
        rep["forgeries"]["n_forgeries"] = 41
        rep["forgeries"]["n_as_declared"] = 41

    with pytest.MonkeyPatch.context() as patch:
        perturbed = render_with(patch, rep=fewer_forgeries)
    assert perturbed != baseline
    assert "41/41 forgeries behaved as declared" in section(perturbed, "B")
    assert "| forgeries attempted | 41 | 41 |" in section(perturbed, "B")
    assert "the honest catch count is 39 of 41" in flat(section(perturbed, "B"))
    # Only §B moved.
    for letter in "ACD":
        assert section(perturbed, letter) == section(baseline, letter)


# ---------------------------------------------------------------- (C) the ladder

def test_section_c_lengths_are_the_artefacts_lengths():
    lad = ladder()
    table_ = ladder_table(edt.render())
    assert list(table_) == [row["instance"]["name"] for row in lad["results"]]

    for row in lad["results"]:
        instance = row["instance"]
        cells = table_[instance["name"]]
        lengths = {rung.get("config"): rung.get("plan_length")
                   for rung in row["rungs"] if rung.get("solved")}
        optimum = instance.get("optimum")
        source = instance.get("optimum_source")
        assert cells[1] == ("--" if optimum is None else str(optimum))
        assert cells[2] == ("--" if source is None else source)
        assert cells[3] == str(lengths.get("stub-bfs", "--"))
        assert cells[4] == str(lengths.get("fd-optimal/lmcut", "--"))
        assert cells[5] == str(lengths.get("fd-satisficing", "--"))


def test_section_c_reports_the_artefacts_own_verdict_and_counts_no_disagreement():
    """E2's verdicts are the referee here, and they record no disagreement.

    This is the module's worst bug, fixed: the agreement column used to be
    recomputed, an instance with no known optimum (`optimum_ok: null`,
    `agreement_ok: true`) was scored as a disagreement, and three admissible
    planners were printed **no** in a file written to be quoted in a paper.
    Missing ground truth and a planner caught non-optimal must not render the
    same, and the count must be of the artefact's verdicts, not of this
    module's opinion.
    """
    lad = ladder()
    disagreements = [row["instance"]["name"] for row in lad["results"]
                     if row["verdicts"].get("agreement_ok") is False]
    assert disagreements == [], "the artefact itself records a disagreement"
    unknown = [row["instance"]["name"] for row in lad["results"]
               if row["verdicts"].get("agreement_ok") is True
               and row["verdicts"].get("optimum_ok") is None]
    assert unknown == ["sokoban-open4far", "sokoban-far4",
                       "sokoban-far5", "sokoban-far6"]

    body = section(edt.render(), "C")
    table_ = ladder_table(edt.render())
    assert "**%d disagreements.**" % len(disagreements) in body
    assert ("on the %d sokoban rows where none is known they agree with each other"
            % len(unknown)) in flat(body)
    assert "read from the artefact's own verdict**, not recomputed" in flat(body)

    for row in lad["results"]:
        verdicts, name = row["verdicts"], row["instance"]["name"]
        cell = table_[name][6]
        if verdicts.get("agreement_ok") is None:
            assert cell == "--", name          # ringstuck: no rung returned a plan
        elif verdicts.get("optimum_ok") is None:
            assert cell == "yes (no optimum)", name
        else:
            assert cell == "yes", name
    assert [name for name, cells in table_.items() if cells[6] == "**no**"] == []


def test_a_recorded_disagreement_reaches_the_page_as_one():
    """The other half of reading the verdict: a real `agreement_ok: false` must
    render **no** and move the count.

    Without this, "0 disagreements" is equally consistent with a renderer that
    cannot count above zero -- which is how the recomputation bug survived: it
    was wrong in the other direction and nothing pinned either end.
    """
    def far5_disagrees(lad):
        for row in lad["results"]:
            if row["instance"]["name"] == "sokoban-far5":
                row["verdicts"]["agreement_ok"] = False

    with pytest.MonkeyPatch.context() as patch:
        perturbed = render_with(patch, lad=far5_disagrees)
    body = section(perturbed, "C")
    assert "**1 disagreements.**" in body
    assert ladder_table(perturbed)["sokoban-far5"][6] == "**no**"
    # ...and it leaves the "no optimum" population one smaller, not unchanged.
    assert "on the 3 sokoban rows where none is known" in flat(body)
    assert [name for name, cells in ladder_table(perturbed).items()
            if cells[6] == "**no**"] == ["sokoban-far5"]


def test_section_c_keeps_the_satisficing_rung_out_of_the_optimal_columns():
    """LAMA's 37 against the optimal rungs' 11 is the point of the third column.

    The sentence no longer calls 11 an optimum: `sokoban-open4far` has none
    recorded, so what the row shows is three optimal rungs agreeing, which is a
    weaker claim and now reads as one.
    """
    lad = ladder()
    body = section(edt.render(), "C")
    open4far = next(row for row in lad["results"]
                    if row["instance"]["name"] == "sokoban-open4far")
    lama = open4far["verdicts"]["satisficing_length"]
    optimal = set(open4far["verdicts"]["optimal_rung_lengths"].values())
    assert len(optimal) == 1, "the three optimal rungs stopped agreeing"
    assert open4far["instance"]["optimum"] is None, (
        "if an optimum is ever recorded here, the sentence may say so again")

    assert ladder_table(edt.render())["sokoban-open4far"][5] == str(lama)
    assert ("on `sokoban-open4far` LAMA returns %d where all three optimal rungs "
            "return %d." % (lama, optimal.pop())) in flat(body)
    assert "not a length anyone may quote as an optimum" in flat(body)


# ------------------------------------------------------------------ (D) the bill

def test_section_d_reports_that_nothing_repaid_the_carve():
    """Nought for six -- and six, not eleven, because five rows never searched."""
    div = dividend()
    priced = [row for row in div["results"] if blind_row(row) is not None]
    searched = [row for row in priced if blind_row(row)["expansions_before"] != 0]
    repaid = [row["instance"] for row in searched
              if (blind_row(row).get("wall_clock") or {}).get("carving_is_repaid")]
    assert repaid == []
    assert len(searched) == 6
    assert "**%d of %d rows that ran a search repay the carve.**" % (0, len(searched)) \
        in section(edt.render(), "D")


def test_section_d_excludes_the_rows_that_never_ran_a_search():
    """A microsecond delta on a search that did not happen is not a bill.

    The translator settles the five `ringstuck*` rows, so their `blind()` timings
    are noise around zero; scoring them as "did not repay" would pad the
    denominator with rows that could never be in it either way, and scoring them
    as repaid would be worse.  They are named, not dropped.
    """
    div = dividend()
    settled = [row["instance"] for row in div["results"]
               if (blind_row(row) or {}).get("expansions_before") == 0]
    assert settled and all(name.startswith("ringstuck") for name in settled)

    body = section(edt.render(), "D")
    table_ = cost_table(edt.render())
    for name in settled:
        assert table_[name][3] == "--", name
        assert table_[name][4] == "n/a -- no search", name
    for name in (name for name in table_ if name not in settled):
        assert table_[name][4] in ("yes", "**no**"), name

    assert ("The other %d (%s) are settled by the translator before search"
            % (len(settled), ", ".join("`%s`" % name for name in settled))) in flat(body)
    assert "excluded rather than scored" in flat(body)


def test_the_wall_clock_caveat_travels_with_the_seconds():
    """Six decimal places of a number this machine's afternoon produced.

    §D's whole argument survives non-reproducible clocks only because the two
    sides differ by three orders of magnitude, and that is a thing a reader has
    to be told before quoting a microsecond.
    """
    prose = flat(section(edt.render(), "D"))
    assert ("**These are wall-clock numbers, so they are this machine's afternoon and "
            "not reproducible.**" in prose)
    assert "checks their ordering and never their equality" in prose
    assert "the two sides differ by three orders of magnitude" in prose


def test_every_section_d_cell_is_a_field_of_the_dividend_artefact():
    div = dividend()
    table_ = cost_table(edt.render())
    priced = [row for row in div["results"] if blind_row(row) is not None]
    assert list(table_) == [row["instance"] for row in priced]

    for row in priced:
        cells = table_[row["instance"]]
        blind = blind_row(row)
        clock = blind.get("wall_clock") or {}
        settled = blind["expansions_before"] == 0
        assert cells[1] == str(row["n_theorems"])
        assert cells[2] == "%.6f" % row["carve_seconds"]
        assert cells[3] == ("--" if settled else "%.6f" % clock["search_seconds_saved"])
        assert cells[4] == ("n/a -- no search" if settled else
                            "yes" if clock["carving_is_repaid"] else "**no**")


def test_a_changed_measurement_moves_the_cell_it_belongs_to_and_only_that_row():
    """The spot-check that separates "reads a field" from "knows the answer".

    `far6`'s two counts are moved in a copy of the artefact; the row's cells and
    its derived percentage must follow, and every other row must not.
    """
    baseline = edt.render()

    def slow_far6_down(div):
        for row in div["results"]:
            if row["instance"] == "far6":
                row["stub"]["expansions_after"] = 1576        # half of 3152
                blind_row(row)["expansions_after"] = 1535     # half of 3070
                row["carve_seconds"] = 9.5

    with pytest.MonkeyPatch.context() as patch:
        perturbed = render_with(patch, div=slow_far6_down)

    after = prune_table(perturbed)
    assert after["far6"][3:6] == ["3152", "1576", "50.0%"]
    assert after["far6"][6:9] == ["3070", "1535", "50.0%"]
    assert cost_table(perturbed)["far6"][2] == "9.500000"

    before = prune_table(baseline)
    assert {k: v for k, v in before.items() if k != "far6"} == \
        {k: v for k, v in after.items() if k != "far6"}
    # The tie-break table reads a different block of the same artefact and was
    # not perturbed, so it must be untouched too.
    assert tiebreak_table(perturbed) == tiebreak_table(baseline)
    # §B and §C read other artefacts and must not have moved at all.
    assert section(perturbed, "B") == section(baseline, "B")
    assert section(perturbed, "C") == section(baseline, "C")


# ---------------------------------------------------------- it quotes, it computes not

def test_the_module_reaches_no_engine_and_no_bench():
    """"It computes nothing" is a claim about its imports before it is one about
    its arithmetic: a module that could call an engine could produce a number no
    artefact contains, and no reader of the table could tell which had happened.
    """
    with open(edt.__file__, encoding="utf-8") as handle:
        lines = [line.strip() for line in handle.read().splitlines()]
    imports = [line for line in lines if line.startswith(("import ", "from "))]
    assert imports, "the scan matched nothing, which would pass over anything"
    forbidden = ("engines", "bench", "recheck", "fixtures", "interop", "numpy", "scipy")
    assert [line for line in imports
            if any(token in line for token in forbidden)] == []


def test_the_header_names_the_three_artefacts_it_read():
    """A quoted table whose sources are not printed is a table nobody can audit."""
    text = edt.render()
    for relative in ("%s/dividend.json" % edt.E6_RUN,
                     "%s/recheck_report.json" % edt.E6_RUN,
                     "%s/ladder.json" % edt.E2_RUN):
        assert relative in text
        assert os.path.isfile(os.path.join(HERE, relative)), relative
    assert ("There is no combined score and this file deliberately does not compute "
            "one." in flat(text))


def test_the_header_claims_reading_verdicts_rather_than_never_recomputing():
    """The header used to say the file recomputes nothing while §C recomputed.

    What it may claim is the narrower and true thing: where an artefact carries a
    verdict, that verdict is what is printed.
    """
    header = flat(edt.render().split("## A ")[0])
    assert ("where the artefact carries a verdict this reads that verdict rather than "
            "re-deriving one" in header)
    assert "never recomputed here" not in header


def test_the_prior_audit_findings_all_reach_the_table():
    """E7's boundary travels with the dividend or the dividend overclaims."""
    prior = dividend()["prior_audit"]
    body = section(edt.render(), "A")
    assert prior["findings"], "the audit block is empty"
    for finding in prior["findings"]:
        assert finding["finding"].strip() in body
        assert finding["applies_to"] in body
    assert prior["source"] in body
