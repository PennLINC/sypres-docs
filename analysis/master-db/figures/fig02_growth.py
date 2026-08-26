"""Figure 2 — Growth and composition of the evidence base.

Papers per 5-year window, stacked by drug. Needs only `year` and `drugs[]`, so
it runs over ALL included papers — no extraction required, which makes it the
one figure that is already at full scale.

Note the final window is partial (the review is live), so it is hatched and
labelled rather than left to read as a decline.
"""
import os
import sys
import collections
import datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                 # noqa: E402
import matplotlib.pyplot as plt     # noqa: E402
import numpy as np                  # noqa: E402

BIN = 5
TOP_DRUGS = 7                       # 8th slot is reserved for "Other"


def main():
    db = C.load()
    studies = [s for s in db["studies"] if s["year"]]

    # rank drugs by paper count; everything past slot 7 folds into "Other" —
    # a 9th series is never a generated hue
    counts = collections.Counter(d for s in studies for d in s["drugs"])
    top = [d for d, _ in counts.most_common(TOP_DRUGS)]
    order = top + (["Other"] if len(counts) > TOP_DRUGS else [])

    def bucket(y):
        return (y // BIN) * BIN

    years = [bucket(s["year"]) for s in studies]
    lo, hi = min(years), max(years)
    bins = list(range(lo, hi + BIN, BIN))

    # a paper with several drugs is counted once per drug it administers,
    # so column totals exceed the paper count — labelled on the axis
    mat = {d: [0] * len(bins) for d in order}
    for s in studies:
        i = bins.index(bucket(s["year"]))
        ds = s["drugs"] or ["Other"]
        for d in ds:
            mat[d if d in top else "Other"][i] += 1

    C.use_style()
    fig, ax = plt.subplots(figsize=(9.2, 4.6))
    bottom = np.zeros(len(bins))
    x = np.arange(len(bins))
    for k, d in enumerate(order):
        v = np.array(mat[d], dtype=float)
        ax.bar(x, v, bottom=bottom, width=0.78, label=d,
               color=C.PALETTE[k % len(C.PALETTE)],
               edgecolor=C.C["surface"], linewidth=2)   # 2px surface gap between segments
        bottom += v

    # the last window is incomplete — mark it rather than let it read as a fall
    this_year = dt.date.today().year
    partial = bins[-1] + BIN - 1 >= this_year
    if partial:
        ax.bar(x[-1], bottom[-1], width=0.78, facecolor="none", edgecolor=C.C["muted"],
               linewidth=0.9, hatch="//", alpha=0.55, zorder=3)
        ax.annotate(f"{bins[-1]}–{this_year}\nwindow still open",
                    (x[-1], bottom[-1]), textcoords="offset points", xytext=(0, 16),
                    ha="center", fontsize=7.5, color=C.C["muted"])

    ax.set_xticks(x)
    ax.set_xticklabels([f"{b}–{b + BIN - 1}" for b in bins], rotation=45, ha="right")
    ax.set_ylabel("Papers (counted once per drug administered)")
    ax.set_title("Growth and composition of the psychedelic RCT literature", loc="left")
    ax.grid(axis="x", visible=False)
    C.despine(ax)
    C.integer_axis(ax)
    ax.legend(ncol=min(len(order), 4), loc="upper left", bbox_to_anchor=(0, 1.0),
              handlelength=1.1, columnspacing=1.2)
    fig.tight_layout(rect=[0, 0.045, 1, 1])
    C.save(fig, "fig02_growth",
           f"All {len(studies)} included papers with a year · drug is extracted where "
           f"available, else keyword-derived from title/abstract")


if __name__ == "__main__":
    main()
