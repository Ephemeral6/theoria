"""Shared style and deterministic output for every P-21 paper figure.

Two jobs, and nothing else belongs in here:

1. **Style.** One accessible palette, two themes (``light``/``dark``), applied
   identically by every figure so the paper's plates read as one system.
2. **Determinism.** Every knob that would otherwise let matplotlib stamp a
   timestamp, salt an element id, or reach for a system font is pinned. Two
   runs over the same inputs must produce byte-identical SVG and PNG.

Import surface:

    from theme import PALETTE, THEMES, apply_theme, save, series_colour, ...

Nothing here reads data and nothing here writes outside ``figures/out``.
"""

from __future__ import annotations

import io
import os
import re
from typing import Iterable, Sequence

import matplotlib

matplotlib.use("Agg")  # no display, no backend-dependent rasterisation

import matplotlib.pyplot as plt  # noqa: E402  (must follow the backend choice)

# --------------------------------------------------------------------------
# Determinism
# --------------------------------------------------------------------------

#: Pins the salt matplotlib uses to derive SVG element ids. Without it the ids
#: are salted from the process's ``id()`` values and every run differs.
SVG_HASHSALT = "theoria-p21-figures"

#: Written into the PNG ``Software`` text chunk in place of matplotlib's own
#: version string, so a matplotlib upgrade does not silently change the bytes
#: of an otherwise unchanged figure.
PNG_SOFTWARE = "theoria-p21"

#: SVG metadata. ``Date: None`` suppresses the ``<dc:date>`` element, which is
#: the one piece of wall-clock matplotlib writes into an SVG by default.
_SVG_METADATA = {
    "Date": None,
    "Creator": PNG_SOFTWARE,
    "Publisher": None,
    "Format": None,
    "Type": None,
}

_PNG_METADATA = {"Software": PNG_SOFTWARE}

THEMES: tuple[str, ...] = ("light", "dark")
FORMATS: tuple[str, ...] = ("svg", "png")

# --------------------------------------------------------------------------
# Palette
# --------------------------------------------------------------------------
#
# Categorical slots are assigned in fixed order and never cycled. The ordering
# is the colour-vision-deficiency safety mechanism, not a cosmetic choice: this
# order clears every adjacent-pair gate in both themes.
#
# Hard rule inherited with the palette: only the FIRST THREE slots clear the
# all-pairs gate. Scatter, bubble and any form where non-adjacent series sit
# side by side must use at most three, or fold the rest into "other" / facet.
# ``series_colours`` enforces this; see ``MAX_ALLPAIRS_SERIES``.

MAX_ALLPAIRS_SERIES = 3

_CATEGORICAL = {
    #  slot:        light      dark
    "blue": ("#2a78d6", "#3987e5"),
    "orange": ("#eb6834", "#d95926"),
    "aqua": ("#1baf7a", "#199e70"),
    "yellow": ("#eda100", "#c98500"),
    "magenta": ("#e87ba4", "#d55181"),
    "green": ("#008300", "#008300"),
    "violet": ("#4a3aa7", "#9085e9"),
    "red": ("#e34948", "#e66767"),
}

#: Fixed slot order. Index 0 is series 1.
SLOT_ORDER: tuple[str, ...] = tuple(_CATEGORICAL)

#: Sequential ramp: one hue, light to dark. The full 100->700 range is for
#: continuous magnitude. For an *ordinal* ramp the step nearest the surface
#: must still clear 2:1 -- start no lighter than step 250 on light, no darker
#: than step 600 on dark. ``sequential_steps`` applies that clamp.
_SEQUENTIAL = [
    "#cde2fb",  # 100
    "#b7d3f6",  # 150
    "#9ec5f4",  # 200
    "#86b6ef",  # 250   <- light ordinal floor
    "#6da7ec",  # 300
    "#5598e7",  # 350
    "#3987e5",  # 400
    "#2a78d6",  # 450
    "#256abf",  # 500
    "#1c5cab",  # 550
    "#184f95",  # 600   <- dark ordinal floor
    "#104281",  # 650
    "#0d366b",  # 700
]
_SEQ_LIGHT_ORDINAL_FLOOR = 3  # index of step 250
_SEQ_DARK_ORDINAL_FLOOR = 10  # index of step 600

#: Status colours are reserved. They are never reused as "series 4", and they
#: always ship with a text label -- never colour alone.
STATUS = {
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

#: Diverging pair: warm/cool poles with a neutral -- never a hue -- midpoint.
DIVERGING = {
    "light": ("#2a78d6", "#f0efec", "#d03b3b"),
    "dark": ("#3987e5", "#383835", "#e66767"),
}

_CHROME = {
    "light": {
        "surface": "#fcfcfb",
        "page": "#f9f9f7",
        "ink": "#0b0b0b",
        "ink_secondary": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "success_text": "#006300",
    },
    "dark": {
        "surface": "#1a1a19",
        "page": "#0d0d0d",
        "ink": "#ffffff",
        "ink_secondary": "#c3c2b7",
        "muted": "#898781",
        "grid": "#2c2c2a",
        "axis": "#383835",
        "success_text": "#0ca30c",
    },
}

PALETTE = {
    theme: {
        **_CHROME[theme],
        "series": [_CATEGORICAL[s][i] for s in SLOT_ORDER],
        "slots": {s: _CATEGORICAL[s][i] for s in SLOT_ORDER},
        "status": dict(STATUS),
        "diverging": DIVERGING[theme],
    }
    for i, theme in enumerate(THEMES)
}

#: Secondary encoding, so identity is never carried by colour alone. Paired
#: with ``SLOT_ORDER`` index-for-index.
MARKERS: tuple[str, ...] = ("o", "s", "^", "D", "v", "P", "X", "*")

#: Hatches for the same purpose on filled marks. ``None`` means solid.
HATCHES: tuple[str | None, ...] = (None, "///", "...", "\\\\\\", "xxx", "|||", "---", "+++")

#: The two non-value cell states the battery distinguishes, and how they are
#: drawn. Neither is ever rendered as a zero.
ABSENCE = {
    "not-applicable": {"hatch": "///", "facecolor": "none", "label": "not applicable (structural)"},
    "insufficient-data": {"hatch": None, "facecolor": "none", "label": "insufficient data"},
}


def series_colour(theme: str, index: int) -> str:
    """Colour for categorical slot ``index`` (0-based), in fixed order."""
    return PALETTE[theme]["series"][index % len(SLOT_ORDER)]


def series_marker(index: int) -> str:
    return MARKERS[index % len(MARKERS)]


def series_hatch(index: int) -> str | None:
    return HATCHES[index % len(HATCHES)]


def series_colours(theme: str, n: int, *, all_pairs: bool = False) -> list[str]:
    """First ``n`` categorical colours, in fixed slot order.

    ``all_pairs=True`` declares that every pair of series will be visible at
    once (scatter, bubble, small multiples) rather than only adjacent ones.
    Past three slots that form cannot clear the colour-vision-deficiency
    floors under any ordering, so this raises instead of shipping a palette
    that only looks safe.
    """
    if all_pairs and n > MAX_ALLPAIRS_SERIES:
        raise ValueError(
            f"{n} series requested with all_pairs=True; only the first "
            f"{MAX_ALLPAIRS_SERIES} slots clear the all-pairs floors. "
            "Fold the tail into 'other', facet, or add secondary encoding "
            "and pass all_pairs=False deliberately."
        )
    return [series_colour(theme, i) for i in range(n)]


def sequential_steps(theme: str, n: int, *, ordinal: bool = False) -> list[str]:
    """``n`` steps of the single-hue sequential ramp, light to dark.

    ``ordinal=True`` clamps the end nearest the chart surface so the palest
    (light) / darkest (dark) step still clears 2:1 against it -- required when
    the ramp encodes discrete ordered categories rather than continuous
    magnitude.
    """
    if n < 1:
        return []
    lo, hi = 0, len(_SEQUENTIAL) - 1
    if ordinal:
        if theme == "light":
            lo = _SEQ_LIGHT_ORDINAL_FLOOR
        else:
            hi = _SEQ_DARK_ORDINAL_FLOOR
    if n == 1:
        return [_SEQUENTIAL[(lo + hi) // 2]]
    span = hi - lo
    return [_SEQUENTIAL[lo + round(i * span / (n - 1))] for i in range(n)]


def sequential_cmap(theme: str, name: str = "theoria_seq"):
    """The sequential ramp as a matplotlib colormap (for heatmap fills)."""
    from matplotlib.colors import LinearSegmentedColormap

    stops = _SEQUENTIAL if theme == "light" else list(reversed(_SEQUENTIAL))
    return LinearSegmentedColormap.from_list(f"{name}_{theme}", stops, N=256)


# --------------------------------------------------------------------------
# rcParams
# --------------------------------------------------------------------------

#: Bundled with matplotlib, so it is the same font on every machine. It has no
#: CJK coverage -- figure text is English for exactly that reason, and the
#: reason is recorded in PLAN.md rather than left for someone to rediscover.
FONT_FAMILY = "DejaVu Sans"

BASE_FONT_SIZE = 9.0


def apply_theme(theme: str) -> dict:
    """Reset rcParams and apply ``theme``. Returns that theme's palette."""
    if theme not in PALETTE:
        raise ValueError(f"unknown theme {theme!r}; expected one of {THEMES}")
    p = PALETTE[theme]

    plt.rcdefaults()
    matplotlib.rcParams.update(
        {
            # --- determinism ---
            "svg.hashsalt": SVG_HASHSALT,
            "svg.fonttype": "path",  # embed glyph outlines; no viewer font lookup
            "pdf.compression": 0,
            "path.simplify": False,  # simplification is threshold-dependent
            "agg.path.chunksize": 0,
            "figure.dpi": 100,
            "savefig.dpi": 200,
            # --- type ---
            "font.family": "sans-serif",
            "font.sans-serif": [FONT_FAMILY],
            "mathtext.fontset": "dejavusans",
            "axes.unicode_minus": False,
            "font.size": BASE_FONT_SIZE,
            "axes.titlesize": BASE_FONT_SIZE + 2,
            "axes.labelsize": BASE_FONT_SIZE,
            "xtick.labelsize": BASE_FONT_SIZE - 1,
            "ytick.labelsize": BASE_FONT_SIZE - 1,
            "legend.fontsize": BASE_FONT_SIZE - 1,
            "figure.titlesize": BASE_FONT_SIZE + 3,
            # --- surfaces ---
            "figure.facecolor": p["surface"],
            "figure.edgecolor": p["surface"],
            "savefig.facecolor": p["surface"],
            "savefig.edgecolor": p["surface"],
            "axes.facecolor": p["surface"],
            "legend.facecolor": p["surface"],
            "legend.edgecolor": p["axis"],
            # --- ink: text wears text tokens, never a series colour ---
            "text.color": p["ink"],
            "axes.labelcolor": p["ink_secondary"],
            "axes.titlecolor": p["ink"],
            "xtick.color": p["muted"],
            "ytick.color": p["muted"],
            "xtick.labelcolor": p["ink_secondary"],
            "ytick.labelcolor": p["ink_secondary"],
            # --- recessive chrome ---
            "axes.edgecolor": p["axis"],
            "axes.linewidth": 0.6,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": p["grid"],
            "grid.linewidth": 0.6,
            "grid.alpha": 1.0,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "xtick.major.width": 0.6,
            "ytick.major.width": 0.6,
            "xtick.major.size": 3.0,
            "ytick.major.size": 3.0,
            "legend.frameon": False,
            # --- marks ---
            "lines.linewidth": 1.6,
            "lines.markersize": 4.5,
            "lines.solid_capstyle": "round",
            "patch.linewidth": 0.8,
            "hatch.linewidth": 0.7,
            "hatch.color": p["ink_secondary"],
            # --- layout ---
            "figure.constrained_layout.use": True,
            "savefig.bbox": None,  # bbox='tight' makes size input-dependent
            "savefig.pad_inches": 0.0,
        }
    )
    # Explicit prop_cycle so a bare plot() call still lands on slot order.
    matplotlib.rcParams["axes.prop_cycle"] = matplotlib.cycler(color=p["series"])
    return p


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))


def out_root() -> str:
    """Where figures are written. ``FIGURES_OUT`` overrides, for verify.sh."""
    return os.environ.get("FIGURES_OUT") or os.path.join(_HERE, "out")


def csv_root() -> str:
    """Where the CSV intermediate layer is written. ``FIGURES_CSV`` overrides."""
    return os.environ.get("FIGURES_CSV") or os.path.join(_HERE, "csv")


#: matplotlib's ``_make_id`` emits ``<letter><10 hex>``: ``p…`` for clips,
#: ``h…`` for hatches, ``m…`` for markers.
_MPL_ID = re.compile(r'id="([a-z][0-9a-f]{10})"')


def _canonicalise_svg_ids(svg: str) -> str:
    """Renumber matplotlib's generated element ids to a stable sequence.

    ``rcParams['svg.hashsalt']`` pins *most* of them, and for a long time that
    looked like enough. It is not, and the exception is worth knowing about:
    for an artist clipped by a **path** rather than a rectangle, matplotlib's
    SVG backend keys the id on ``id(clippath)`` -- the object's memory address
    -- so the hash absorbs a number that changes every process. One clip id in
    one figure moved between two otherwise byte-identical builds, which is
    enough to fail the gate and gives nothing to fix in the figure.

    So the ids are rewritten here, in order of first definition, to
    ``a00``, ``a01``, .... Both the ``id="…"`` definitions and every
    ``url(#…)`` reference are rewritten together. Nothing else in the document
    is touched, and the substitution is order-dependent only on the document,
    which is itself deterministic.
    """
    seen: dict[str, str] = {}
    for match in _MPL_ID.finditer(svg):
        original = match.group(1)
        if original not in seen:
            seen[original] = f"a{len(seen):02d}"
    if not seen:
        return svg
    # Longest first, so no id is a prefix of another mid-substitution.
    for original in sorted(seen, key=len, reverse=True):
        svg = svg.replace(original, seen[original])
    return svg


def save(fig, name: str, theme: str) -> list[str]:
    """Write ``fig`` as SVG and PNG under ``out/<theme>/``.

    Returns the paths written, in a fixed order. Closes the figure.
    """
    directory = os.path.join(out_root(), theme)
    os.makedirs(directory, exist_ok=True)
    written = []
    for fmt in FORMATS:
        path = os.path.join(directory, f"{name}.{fmt}")
        metadata = _SVG_METADATA if fmt == "svg" else _PNG_METADATA
        if fmt == "svg":
            # SVG is text, and matplotlib writes it through a text-mode handle,
            # so on Windows it lands with CRLF and on Linux with LF -- the same
            # figure, different bytes, on the one check this pipeline exists to
            # pass. `.gitattributes` pins `*.svg text eol=lf`, so a fresh
            # checkout holds LF and a Windows rebuild would produce CRLF and
            # fail verify.sh gate 6 with no defect to find. Pin the newline at
            # the writer instead of hoping git and the platform agree.
            buf = io.StringIO()
            fig.savefig(buf, format=fmt, metadata=metadata)
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(_canonicalise_svg_ids(buf.getvalue()))
        else:
            fig.savefig(path, format=fmt, metadata=metadata)
        written.append(path)
    plt.close(fig)
    return written


def write_csv(name: str, header: Sequence[str], rows: Iterable[Sequence]) -> str:
    """Write the intermediate CSV layer for a figure. LF newlines, fixed order.

    The CSV is the audit surface: a reviewer checks the number here without
    reading plotting code, and a determinism failure in extraction shows up in
    this diff before it reaches the image.
    """
    import csv as _csv
    import io

    directory = csv_root()
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{name}.csv")
    buf = io.StringIO(newline="")
    writer = _csv.writer(buf, lineterminator="\n")
    writer.writerow(list(header))
    for row in rows:
        writer.writerow(["" if v is None else v for v in row])
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(buf.getvalue())
    return path


def fmt_num(value, places: int = 3) -> str:
    """Fixed-width numeric formatting, so CSV bytes do not drift with repr."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return f"{float(value):.{places}f}"


def check_no_mathtext(text: str, *, where: str = "figure text") -> None:
    """Raise if ``text`` contains a bare ``$``.

    matplotlib reads ``$...$`` as mathtext, so a caveat that says
    ``$0.90 against $0.15`` silently renders as italic ``0.90against0.15`` --
    the dollar signs vanish and two numbers run together. That failure is
    invisible in a diff and survives a determinism check, because it is
    deterministically wrong. This is a money-heavy repository; the guard is
    cheaper than the next person finding it in a published plate.

    Write ``USD 0.90`` (preferred, and unambiguous about the currency) or
    escape as ``\\$0.90`` if the glyph is genuinely wanted.
    """
    if "$" in text.replace("\\$", ""):
        raise ValueError(
            f"{where} contains an unescaped '$': matplotlib will read it as "
            "mathtext and eat the text between it and the next '$'. Write "
            f"'USD 1.23' or escape it as '\\\\$1.23'.\n  text: {text[:200]!r}"
        )


def caveat(fig, text: str, *, theme: str) -> None:
    """Put a caveat on the figure's face rather than in a caption someone drops.

    Used for the things this project has decided must never travel separately
    from the number: sampling frames, structural absences, confounds.
    """
    check_no_mathtext(text, where="caveat")
    fig.text(
        0.005,
        0.005,
        text,
        ha="left",
        va="bottom",
        fontsize=BASE_FONT_SIZE - 2,
        color=PALETTE[theme]["muted"],
        wrap=True,
    )


def absence_handles(theme: str):
    """Legend handles for the two non-value states, so they are never mute."""
    from matplotlib.patches import Patch

    p = PALETTE[theme]
    return [
        Patch(
            facecolor="none",
            edgecolor=p["ink_secondary"],
            hatch=ABSENCE["not-applicable"]["hatch"],
            linewidth=0.8,
            label=ABSENCE["not-applicable"]["label"],
        ),
        Patch(
            facecolor="none",
            edgecolor=p["muted"],
            linewidth=0.8,
            linestyle=":",
            label=ABSENCE["insufficient-data"]["label"],
        ),
    ]
