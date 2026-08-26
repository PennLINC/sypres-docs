"""Shared data loading, palette, and styling for the master-DB figures.

Every figure script imports from here so the whole set stays visually consistent
and reads from the same committed data file. Requires matplotlib + numpy only.

    python3 analysis/master-db/figures/make_figures.py        # regenerate all
    python3 analysis/master-db/figures/fig02_growth.py        # just one

Data source is `_data/master_db.json` — the committed output of
`build_database.py`. Re-run that first if you have dropped in a new Covidence
export; these scripts never read the raw CSVs.
"""
from __future__ import annotations

import json
import os
import sys

import matplotlib
matplotlib.use("Agg")                      # headless: never needs a display
import matplotlib.pyplot as plt            # noqa: E402
from matplotlib.ticker import MaxNLocator  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DB_PATH = os.path.join(REPO, "_data", "master_db.json")
OUT_DIR = os.path.join(HERE, "output")

# ---------------------------------------------------------------------------
# Palette — validated categorical order (adjacent-pair CVD ΔE 9.1, normal 19.6).
# Slots are assigned in FIXED order and never cycled; a 9th series folds into
# "Other". Three light slots sit below 3:1 on the surface, so every figure that
# uses them ships visible direct labels or a legend (the "relief rule").
# ---------------------------------------------------------------------------
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
          "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
SERIES_DARK = ["#3987e5", "#d95926", "#199e70", "#c98500",
               "#d55181", "#008300", "#9085e9", "#e66767"]

# Sequential (magnitude): one hue, light → dark. Never a rainbow.
SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec",
       "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95"]

STATUS = {"good": "#0ca30c", "warning": "#fab219",
          "serious": "#ec835a", "critical": "#d03b3b"}

INK = {
    "surface":   "#fcfcfb",
    "primary":   "#0b0b0b",
    "secondary": "#52514e",
    "muted":     "#898781",
    "grid":      "#e1e0d9",
    "axis":      "#c3c2b7",
}
INK_DARK = {
    "surface":   "#1a1a19",
    "primary":   "#ffffff",
    "secondary": "#c3c2b7",
    "muted":     "#898781",
    "grid":      "#2c2c2a",
    "axis":      "#383835",
}

DARK = os.environ.get("MDB_FIG_DARK") == "1"
C = INK_DARK if DARK else INK
PALETTE = SERIES_DARK if DARK else SERIES


def use_style() -> None:
    """Recessive chrome, thin marks, no chartjunk."""
    plt.rcParams.update({
        "figure.facecolor": C["surface"],
        "axes.facecolor": C["surface"],
        "savefig.facecolor": C["surface"],
        "font.family": ["DejaVu Sans", "Helvetica", "Arial", "sans-serif"],
        "font.size": 9,
        "axes.titlesize": 11,
        "axes.titleweight": "bold",
        "axes.titlecolor": C["primary"],
        "axes.labelsize": 9,
        "axes.labelcolor": C["secondary"],
        "axes.edgecolor": C["axis"],
        "axes.linewidth": 0.8,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": C["grid"],
        "grid.linewidth": 0.6,
        "xtick.color": C["muted"],
        "ytick.color": C["muted"],
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.frameon": False,
        "legend.fontsize": 8,
        "lines.linewidth": 2.0,
        "lines.markersize": 8,
        "figure.dpi": 110,
    })


def despine(ax, keep=("left", "bottom")) -> None:
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(side in keep)


def integer_axis(ax, which="y") -> None:
    getattr(ax, f"{which}axis").set_major_locator(MaxNLocator(integer=True))


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load() -> dict:
    if not os.path.exists(DB_PATH):
        sys.exit(f"ERROR: {DB_PATH} not found — run build_database.py first.")
    with open(DB_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def verified(db: dict) -> list:
    """Studies whose extraction is complete.

    Only the consensus reviewer's rows reach the database, so `extracted` is
    exactly the verified set. Outcome/design/sample-size figures MUST use this
    rather than all studies — in-progress rows would drag every rate downward
    and read as a reviewer effect.
    """
    return [s for s in db["studies"] if s["extracted"]]


def enriched(db: dict) -> list:
    """Trials with parsed ClinicalTrials.gov details."""
    return [t for t in db["trials"] if t.get("fetch_status") == "ok" and t.get("details")]


def note_n(fig, text: str) -> None:
    """Stamp the denominator on the figure. These are pilot previews — the n is
    part of the finding, not a footnote to be dropped.

    Reserves a strip at the bottom first, otherwise the note overprints the
    x-axis label of the left-most panel.
    """
    # Only the constrained engine accepts a rect here; the tight engine raises
    # NotImplementedError, and figures using it pass their own rect instead.
    engine = fig.get_layout_engine()
    if type(engine).__name__ == "ConstrainedLayoutEngine":
        engine.set(rect=(0, 0.045, 1, 0.93))   # room for the suptitle above
    fig.text(0.005, 0.006, text, fontsize=7, color=C["muted"], ha="left", va="bottom")


def save(fig, stem: str, note: str | None = None) -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    if note:
        note_n(fig, note)
    for ext in ("png", "pdf"):
        path = os.path.join(OUT_DIR, f"{stem}.{ext}")
        fig.savefig(path, bbox_inches="tight", dpi=200 if ext == "png" else None)
    plt.close(fig)
    print(f"  wrote output/{stem}.png + .pdf")


def bar_labels(ax, bars, values, fmt="{:g}", pad=2, color=None) -> None:
    """Direct value labels — required relief for the sub-3:1 palette slots."""
    for b, v in zip(bars, values):
        ax.annotate(fmt.format(v), (b.get_x() + b.get_width() / 2, b.get_height()),
                    textcoords="offset points", xytext=(0, pad), ha="center",
                    fontsize=7.5, color=color or C["secondary"])
