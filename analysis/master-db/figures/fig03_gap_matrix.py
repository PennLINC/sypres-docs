"""Figure 3 — Evidence-and-gap matrix: drug x population.

The signature figure of a systematic map. Bubble area = number of distinct
TRIALS (not papers, which would double-count multi-report trials); fill =
cumulative participants on a sequential ramp. The empty cells are the finding.

Trial counting: papers sharing a `trial_key` collapse to one trial; a paper with
no trial identifier counts as its own trial (the conservative reading).
"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                              # noqa: E402
import matplotlib.pyplot as plt                  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, Normalize   # noqa: E402
import numpy as np                               # noqa: E402


def main():
    db = C.load()
    studies = db["studies"]

    # collapse papers to trials before counting anything
    cell_trials = collections.defaultdict(set)
    cell_n = collections.defaultdict(int)
    seen_n = collections.defaultdict(set)
    for s in studies:
        key = s["trial_key"] or f"paper:{s['covidence_id']}"
        for d in (s["drugs"] or ["Unclear"]):
            cell = (d, s["indication"])
            cell_trials[cell].add(key)
            if key not in seen_n[cell] and s.get("n"):
                cell_n[cell] += s["n"]
                seen_n[cell].add(key)

    drugs = sorted({d for d, _ in cell_trials},
                   key=lambda d: -sum(len(v) for (dd, _), v in cell_trials.items() if dd == d))
    inds = sorted({i for _, i in cell_trials},
                  key=lambda i: -sum(len(v) for (_, ii), v in cell_trials.items() if ii == i))

    C.use_style()
    fig, ax = plt.subplots(figsize=(max(7.2, 0.86 * len(inds) + 2.8),
                                    max(4.2, 0.46 * len(drugs) + 2.0)))
    cmap = LinearSegmentedColormap.from_list("seq", C.SEQ)
    nmax = max(cell_n.values()) if cell_n else 1
    norm = Normalize(0, nmax)
    tmax = max(len(v) for v in cell_trials.values())

    xs, ys, sizes, cols, labels = [], [], [], [], []
    for yi, d in enumerate(drugs):
        for xi, ind in enumerate(inds):
            t = len(cell_trials.get((d, ind), ()))
            if not t:
                continue
            xs.append(xi); ys.append(yi)
            sizes.append(90 + 620 * (t / tmax) ** 0.75)
            cols.append(cmap(norm(cell_n.get((d, ind), 0))))
            labels.append(t)

    ax.scatter(xs, ys, s=sizes, c=cols, edgecolors=C.C["surface"], linewidths=2, zorder=3)

    def ink_on(rgba):
        """Ink that stays legible on this fill — relative luminance, per bubble.
        (Indexing by label value would colour every bubble by the first one
        sharing its count.)"""
        r, g, b = rgba[:3]
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return "#ffffff" if lum < 0.55 else C.C["primary"]

    for x, y, t, col in zip(xs, ys, labels, cols):
        ax.annotate(str(t), (x, y), ha="center", va="center", fontsize=7.5,
                    zorder=4, color=ink_on(col))

    ax.set_xticks(range(len(inds)))
    ax.set_xticklabels(inds, rotation=32, ha="right")
    ax.set_yticks(range(len(drugs)))
    ax.set_yticklabels(drugs)
    ax.set_xlim(-0.7, len(inds) - 0.3)
    ax.set_ylim(-0.7, len(drugs) - 0.3)
    ax.invert_yaxis()
    ax.grid(True, which="major", color=C.C["grid"], linewidth=0.6)
    C.despine(ax, keep=())
    ax.set_title("Evidence-and-gap matrix: what has been trialled, in whom", loc="left")

    cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax,
                      fraction=0.022, pad=0.02, shrink=0.62)
    cb.set_label("Cumulative participants", fontsize=8, color=C.C["secondary"])
    cb.ax.tick_params(labelsize=7, color=C.C["muted"])
    cb.outline.set_visible(False)

    fig.tight_layout(rect=[0, 0.05, 1, 1])
    C.save(fig, "fig03_gap_matrix",
           f"Bubble area and label = distinct trials · {len(studies)} papers collapse to "
           f"{db['meta']['n_trials']} trials · empty cells are the gap map")


if __name__ == "__main__":
    main()
