"""Figure 5 — The outcome landscape (the core-outcome-set argument).

5A: outcome domain x drug, share of trials assessing each domain.
5B: how many domain COMBINATIONS are unique to a single study.
5C: distinct sub-categories recorded within each domain.

What this claims, precisely: we record domains and a controlled sub-category
within each — NOT instruments. So the claim is not "trials use scattered
scales"; it is that trials do not agree on which DOMAINS to measure at all.
That is also the right level: COMET-style core-outcome-set work establishes core
domains first and selects instruments as a separate second stage.

Uses VERIFIED rows only — in-progress rows have blank outcome columns and would
drag every rate downward.
"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                              # noqa: E402
import matplotlib.pyplot as plt                  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap   # noqa: E402
import numpy as np                               # noqa: E402


def main():
    db = C.load()
    E = C.verified(db)
    domains = db["meta"]["outcome_domains"]           # template order, not alphabetical
    drugs = [d for d, _ in collections.Counter(
        d for s in E for d in s["drugs"]).most_common(6)]

    C.use_style()
    # constrained_layout, not tight_layout: an imshow axes is not tight-compatible
    fig = plt.figure(figsize=(13.0, 5.8), layout="constrained")
    gs = fig.add_gridspec(1, 3, width_ratios=[1.5, 0.72, 1.16], wspace=0.06)
    a, b, c = (fig.add_subplot(gs[i]) for i in range(3))

    # ---- 5A heatmap: share of trials per drug assessing each domain ----
    mat = np.zeros((len(domains), len(drugs)))
    for j, d in enumerate(drugs):
        rows = [s for s in E if d in s["drugs"]]
        for i, dom in enumerate(domains):
            mat[i, j] = (sum(1 for s in rows if dom in s["outcome_domains"]) / len(rows)
                         if rows else 0)
    cmap = LinearSegmentedColormap.from_list("seq", C.SEQ)
    a.imshow(mat, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    a.set_xticks(range(len(drugs))); a.set_xticklabels(drugs, rotation=32, ha="right")
    a.set_yticks(range(len(domains)))
    a.set_yticklabels([d if len(d) < 26 else d[:24] + "…" for d in domains], fontsize=7.5)
    for i in range(len(domains)):
        for j in range(len(drugs)):
            if mat[i, j]:
                a.text(j, i, f"{mat[i, j]:.0%}", ha="center", va="center", fontsize=6.8,
                       color="#ffffff" if mat[i, j] > 0.55 else C.C["primary"])
    a.set_title("A · Which domains each drug's trials assess", loc="left", fontsize=10, pad=16)
    a.grid(False)
    C.despine(a, keep=())

    # ---- 5B: uniqueness of domain combinations ----
    combos = collections.Counter(tuple(sorted(s["outcome_domains"]))
                                 for s in E if s["outcome_domains"])
    n_studies = sum(combos.values())
    uniq = sum(1 for v in combos.values() if v == 1)
    shared = n_studies - uniq
    bars = b.bar(["used by\nexactly one\nstudy", "shared with\nanother\nstudy"],
                 [uniq, shared], width=0.55,
                 color=[C.PALETTE[1], C.PALETTE[0]],
                 edgecolor=C.C["surface"], linewidth=2)
    C.bar_labels(b, bars, [uniq, shared])
    b.set_ylabel("Studies")
    b.set_title("B · No standard battery", loc="left", fontsize=10, pad=30)
    b.grid(axis="x", visible=False)
    C.despine(b); C.integer_axis(b)
    # sits under the title, clear of both bars
    b.annotate(f"{len(combos)} distinct combinations\nacross {n_studies} studies",
               (0.5, 1.02), xycoords="axes fraction", ha="center", va="bottom",
               fontsize=8, color=C.C["secondary"])

    # ---- 5C: distinct sub-categories per domain ----
    per = collections.defaultdict(set)
    for s in E:
        for m in s["outcome_measures"]:
            dom, _, meas = m.partition(": ")
            per[dom].add(meas)
    items = [(d, len(per[d])) for d in domains if d in per]
    items.sort(key=lambda kv: kv[1])
    bars = c.barh([d if len(d) < 24 else d[:22] + "…" for d, _ in items],
                  [v for _, v in items], height=0.62,
                  color=C.PALETTE[2], edgecolor=C.C["surface"], linewidth=2)
    for bar, (_, v) in zip(bars, items):
        c.annotate(str(v), (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                   textcoords="offset points", xytext=(4, 0), va="center",
                   fontsize=7.5, color=C.C["secondary"])
    c.set_xlabel("Distinct sub-categories recorded")
    c.set_title("C · Granularity within each domain", loc="left", fontsize=10, pad=16)
    c.tick_params(labelsize=7.5)
    c.grid(axis="y", visible=False)
    C.despine(c)
    C.integer_axis(c, "x")

    fig.suptitle("The outcome landscape — domains, not instruments",
                 x=0.004, ha="left", fontsize=12, fontweight="bold")
    C.save(fig, "fig05_outcomes",
           f"n = {len(E)} verified-complete extractions · domains and controlled "
           f"sub-categories only; instruments are not extracted")


if __name__ == "__main__":
    main()
