"""Generate the paper's figure index and its captions. Nothing here is typed.

The work order asks for an index of *图号 → 生成脚本 → 数据源 → sha256* and one
caption per figure naming the tree files and the run its numbers came from.
Both are **generated**, and that is not a stylistic preference:
``figures/PLAN.md`` §10 is a changelog of what hand-maintained lists do in this
pipeline. ``ROLLUP_KEYS`` named four of six roll-ups and two runs were drawn
"outcome unknown" with their outcomes committed on disk; ``THEORIA_RUNS`` named
three of four directories and left a branch of the loader unexecuted. A caption
that lists its own inputs by hand is the same object with a friendlier face.

So every field here is derived:

* the source list, from ``Source.figures`` in ``sources.py``;
* the digests, by hashing the files that are actually on disk at build time;
* the run identity, by resolving ``paper_map.RunRef`` against those same files;
* ``status``, from whether any declared source is absent.

Three outputs, all deterministic -- no clock, no host paths, sorted keys:

    paper/index.json        the machine form
    paper/INDEX.md          the human form
    paper/captions/figureN.md   one caption per figure, ready to paste

**Paths are written canonically** (``figures/paper/light/figure1_….pdf``) even
when the build was directed elsewhere by ``FIGURES_PAPER``. ``verify.sh`` builds
twice into two scratch trees and requires the results to be byte-identical; an
index that recorded where it happened to be written would differ between those
two trees and fail the gate with nothing to fix.
"""

from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import paper_map  # noqa: E402
import sources  # noqa: E402
import theme  # noqa: E402

SCHEMA = "theoria-figures-paper-index/v1"

#: The one command the work order asks for. Named once, quoted everywhere.
REGENERATE_CMD = "python figures/build_all.py"
VERIFY_CMD = "bash figures/verify.sh"

#: Where the caveats live. Captions must not become a second home for them --
#: ``figures/README.md`` is explicit that every plate's "must not let you
#: conclude" line is drawn on the figure's face via ``theme.caveat``, because a
#: caption is the part that gets dropped when a plate is pasted into slides.
CAVEAT_POINTER = (
    "The caveat this plate must not be read without is drawn on its face, not "
    "here; `figures/README.md` tabulates them."
)


def _short(digest: str) -> str:
    return digest[:12]


def _canon(*parts: str) -> str:
    """A repo-relative artefact path, independent of where the build wrote it."""
    return "/".join(("figures",) + parts)


def _digest(abs_path: str) -> str | None:
    if not os.path.isfile(abs_path):
        return None
    return sources.sha256_file(abs_path)


def _artifacts(fig: paper_map.PaperFigure) -> list[dict]:
    rows = []
    for th in theme.THEMES:
        for fmt in paper_map.PUB_FORMATS:
            fname = f"{fig.pub_name}.{fmt}"
            rows.append(
                {
                    "path": _canon("paper", th, fname),
                    "theme": th,
                    "format": fmt,
                    "sha256": _digest(os.path.join(theme.paper_root(), th, fname)),
                }
            )
    return rows


def _screen_artifacts(fig: paper_map.PaperFigure) -> list[dict]:
    rows = []
    for th in theme.THEMES:
        for fmt in theme.FORMATS:
            fname = f"{fig.pipeline}.{fmt}"
            rows.append(
                {
                    "path": _canon("out", th, fname),
                    "theme": th,
                    "format": fmt,
                    "sha256": _digest(os.path.join(theme.out_root(), th, fname)),
                }
            )
    return rows


def figure_record(fig: paper_map.PaperFigure) -> dict:
    status, absent = paper_map.status_for(fig.pipeline)
    csv_name = f"{fig.pipeline}.csv"
    return {
        "number": fig.number,
        "cite": fig.cite,
        "pub_name": fig.pub_name,
        "title": fig.title,
        "shows": fig.shows,
        "section": fig.section,
        "section_title": fig.section_title,
        "pipeline_plate": fig.pipeline,
        "generator": _canon(f"{fig.pipeline}.py"),
        "csv": {
            "path": _canon("csv", csv_name),
            "sha256": _digest(os.path.join(theme.csv_root(), csv_name)),
        },
        "status": status,
        "missing_sources": [
            {"path": s.path, "why": s.note or "declared in sources.py, not on disk"}
            for s in absent
        ],
        "sources": [
            {
                "path": s.path,
                "sha256": _digest(s.abspath),
                "what": s.what,
                "tracked": s.tracked,
                "present": s.exists(),
            }
            for s in paper_map.sources_for(fig.pipeline)
        ],
        "runs": paper_map.run_identity(fig),
        "artifacts": _artifacts(fig),
        "screen_artifacts": _screen_artifacts(fig),
        "supersedes": list(fig.supersedes),
    }


def build_index() -> dict:
    return {
        "schema": SCHEMA,
        "regenerate": REGENERATE_CMD,
        "verify": VERIFY_CMD,
        "profile": {
            "publication": {
                "root": _canon("paper"),
                "formats": list(paper_map.PUB_FORMATS),
                "png_dpi": paper_map.PUB_DPI,
                "themes": list(theme.THEMES),
            },
            "screen": {
                "root": _canon("out"),
                "formats": list(theme.FORMATS),
                "png_dpi": 200,
                "themes": list(theme.THEMES),
            },
        },
        "figures": [figure_record(f) for f in paper_map.PAPER_FIGURES],
    }


# --------------------------------------------------------------------------
# Captions
# --------------------------------------------------------------------------


def _run_sentence(record: dict) -> str:
    if not record["runs"]:
        return (
            "No artefact behind this plate publishes a run identifier. The run is "
            "pinned by the file digests above and by the commit this build was made "
            "from — stated rather than filled in, because an invented run id is worse "
            "than an absent one."
        )
    parts = []
    for run in record["runs"]:
        ids = ", ".join(f"`{i}`" for i in run["ids"])
        parts.append(f"{run['label']} ({run['source']}): {ids}")
    return "Run: " + "; ".join(parts) + "."


def _status_sentence(record: dict) -> str:
    if record["status"] == "complete":
        return "Status: complete — every source this plate declares is on disk."
    missing = record["missing_sources"]
    paths = ", ".join(f"`{m['path']}`" for m in missing)
    why = missing[0]["why"] if missing else ""
    return (
        f"**Status: pending — {len(missing)} declared source(s) absent:** {paths}. "
        f"{why} The plate is drawn from what is present and the absence is marked on "
        "it; it is not drawn as a zero."
    )


def _status_clause(record: dict) -> str:
    """The pending marker, in the one sentence a printed caption can carry."""
    if record["status"] == "complete":
        return ""
    missing = record["missing_sources"]
    roots = sorted({m["path"].rsplit("/", 1)[0] for m in missing})
    return (
        f" **Pending:** {len(missing)} declared input(s) under "
        + ", ".join(f"`{r}/`" for r in roots)
        + " are untracked in `master` and absent from this build; the plate is drawn "
        "from what is present and marks the gap rather than drawing it as zero."
    )


#: Above this many sources a printed caption stops being a caption. The full
#: list never disappears -- it moves to the provenance block below and the
#: caption says how many there are and where they are, because a truncation
#: nobody is told about reads as completeness. (``figures/PLAN.md`` §10: "no
#: silent caps".)
CAPTION_INLINE_SOURCES = 4


def _data_clause(record: dict) -> str:
    present = [s for s in record["sources"] if s["present"]]
    if len(present) <= CAPTION_INLINE_SOURCES:
        listed = "; ".join(f"`{s['path']}` (`{_short(s['sha256'])}`)" for s in present)
        return f"Data: {listed}."
    roots = sorted({s["path"].split("/", 1)[0] for s in present})
    return (
        f"Data: {len(present)} tracked files under "
        + ", ".join(f"`{r}/`" for r in roots)
        + f"; every path and its sha256 is listed in `figures/paper/INDEX.md` under "
        f"{record['cite']}, and hashed into `figures/SOURCES.sha256`."
    )


def caption_markdown(record: dict) -> str:
    """Two blocks: the caption a paper prints, and the provenance behind it.

    They are split because they have different readers and different length
    budgets. Figure 6 draws 19 tracked files; naming all nineteen under the
    plate is not a caption, and naming none of them is not provenance. The
    caption carries the count, the directories and the pointer; the block below
    carries every path and digest.
    """
    lines = [
        "<!-- GENERATED by figures/paper_index.py — edit paper_map.py, not this file. -->",
        "",
        f"# {record['cite']} — {record['title']}",
        "",
        "## Caption (this is what the paper prints)",
        "",
        f"**{record['cite']}. {record['title']}.** {record['shows']}"
        f"{_status_clause(record)} {_data_clause(record)} Generated by "
        f"`{record['generator']}` through `{record['csv']['path']}`; "
        f"regenerate with `{REGENERATE_CMD}`.",
        "",
        "## Provenance (not printed — the audit trail behind the caption)",
        "",
        f"* plate `{record['pipeline_plate']}`, paper §{record['section']}",
        f"* CSV `{record['csv']['path']}` sha256 `{record['csv']['sha256']}`",
        f"* publication artefacts: "
        + ", ".join(f"`{a['path']}`" for a in record["artifacts"]),
        "",
        _run_sentence(record),
        "",
        _status_sentence(record),
        "",
        "| data source | sha256 |",
        "|---|---|",
    ]
    for src in record["sources"]:
        lines.append(f"| `{src['path']}` | `{src['sha256'] or 'ABSENT'}` |")
    lines += ["", CAVEAT_POINTER, ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# INDEX.md
# --------------------------------------------------------------------------


def index_markdown(index: dict) -> str:
    lines = [
        "<!-- GENERATED by figures/paper_index.py — edit paper_map.py, not this file. -->",
        "",
        "# The paper's figures: number, generator, data, digest",
        "",
        "Every row is derived at build time. The **number** is the paper's, assigned by",
        "order of first citation; the **plate** is the pipeline's own slug, which is",
        f"numbered after `Theoria.md` §3.2 and does not agree with the paper's. Both",
        "names point at one build of one figure.",
        "",
        f"Regenerate all of it with `{REGENERATE_CMD}`; check it with `{VERIFY_CMD}`.",
        "",
        "## The map",
        "",
        "| fig | § | plate | generator | sources | status |",
        "|---|---|---|---|---|---|",
    ]
    for rec in index["figures"]:
        n_present = sum(1 for s in rec["sources"] if s["present"])
        n_absent = len(rec["sources"]) - n_present
        src_cell = f"{n_present} file(s)" + (f", {n_absent} absent" if n_absent else "")
        lines.append(
            f"| {rec['cite']} | §{rec['section']} | `{rec['pipeline_plate']}` | "
            f"`{rec['generator']}` | {src_cell} | {rec['status']} |"
        )
    lines += [
        "",
        "## Artefacts and digests",
        "",
        f"Publication profile: {', '.join(paper_map.PUB_FORMATS)} at "
        f"{paper_map.PUB_DPI} dpi (PNG), both themes, under `figures/paper/`. The",
        "screen profile the pipeline has always written stays at `figures/out/` and",
        "200 dpi. Both come off the same in-memory figure in one pass, so the SVGs are",
        "byte-identical by construction — `verify.sh` gate 10 checks it rather than",
        "trusting it.",
        "",
    ]
    for rec in index["figures"]:
        lines += [
            f"### {rec['cite']} — {rec['title']}",
            "",
            f"* plate `{rec['pipeline_plate']}`, §{rec['section']} "
            f"({rec['section_title']})",
            f"* CSV `{rec['csv']['path']}` sha256 `{rec['csv']['sha256']}`",
        ]
        if rec["supersedes"]:
            for old in rec["supersedes"]:
                lines.append(f"* supersedes `{old}`")
        lines += ["", "| artefact | sha256 |", "|---|---|"]
        for art in rec["artifacts"] + rec["screen_artifacts"]:
            digest = art["sha256"] or "ABSENT"
            lines.append(f"| `{art['path']}` | `{digest}` |")
        lines += ["", "| data source | sha256 | what |", "|---|---|---|"]
        for src in rec["sources"]:
            digest = src["sha256"] or "ABSENT — " + ("untracked" if not src["tracked"] else "required")
            lines.append(f"| `{src['path']}` | `{digest}` | {src['what']} |")
        lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------


def _write(path: str, body: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return path


def write_all() -> list[str]:
    """Write index.json, INDEX.md and every caption. Returns the paths written."""
    root = theme.paper_root()
    index = build_index()
    written = [
        _write(
            os.path.join(root, "index.json"),
            json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        ),
        _write(os.path.join(root, "INDEX.md"), index_markdown(index)),
    ]
    for rec in index["figures"]:
        written.append(
            _write(
                os.path.join(root, "captions", f"figure{rec['number']}.md"),
                caption_markdown(rec),
            )
        )
    return written


if __name__ == "__main__":
    for p in write_all():
        print(os.path.relpath(p, sources.REPO_ROOT).replace(os.sep, "/"))
