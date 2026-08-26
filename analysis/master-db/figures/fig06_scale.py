"""Figure 6 — Statistical scale of the field.

A: sample-size distribution.  B: N by era.  C: N by population.

The attrition panel is deliberately absent. It needs both N randomized and N
analyzed, and either being blank makes attrition undeterminable — the older
unregistered studies often report a single N and never mention dropouts, so a
blank is ambiguous between "no dropouts" and "not reported". Panel D reports how
often that happens, which is the honest version of the missing panel.
"""
import os
import sys
import collections
import statistics

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                 # noqa: E402
import matplotlib.pyplot as plt     # noqa: E402
import numpy as np                  # noqa: E402


def era(y):
    return "<2010" if y and y < 2010 else "2010–19" if y and y < 2020 else "2020+"


def main():
    db = C.load()
    E = C.verified(db)
    ns = [s["n"] for s in E if s["n"]]

    C.use_style()
    fig, axes = plt.subplots(1, 4, figsize=(13.2, 4.2), layout="constrained")
    a, b, c, d = axes

    # ---- A: distribution ----
    a.hist(ns, bins=np.arange(0, max(ns) + 20, 15), color=C.PALETTE[0],
           edgecolor=C.C["surface"], linewidth=1.5)
    med = statistics.median(ns)
    a.axvline(med, color=C.PALETTE[1], linewidth=2, zorder=4)
    a.annotate(f"median {med:.0f}", (med, a.get_ylim()[1] * 0.97),
               textcoords="offset points", xytext=(6, 0), fontsize=8, va="top",
               color=C.PALETTE[1],
               bbox=dict(facecolor=C.C["surface"], edgecolor="none", pad=1.5))
    a.set_xlabel("Participants"); a.set_ylabel("Studies")
    a.set_title("A · These trials are small", loc="left", fontsize=10)
    C.despine(a); C.integer_axis(a)

    # ---- B: by era (strip + median bar; n is far too small for a boxplot) ----
    eras = ["<2010", "2010–19", "2020+"]
    for i, e in enumerate(eras):
        v = [s["n"] for s in E if s["n"] and era(s["year"]) == e]
        if not v:
            continue
        jitter = np.random.default_rng(0).uniform(-0.13, 0.13, len(v))
        b.scatter([i] * len(v) + jitter, v, s=48, color=C.PALETTE[0], alpha=0.85,
                  edgecolors=C.C["surface"], linewidths=1.5, zorder=3)
        b.plot([i - 0.26, i + 0.26], [statistics.median(v)] * 2,
               color=C.PALETTE[1], linewidth=2.4, zorder=4)
        b.annotate(f"n={len(v)}", (i, 0), xycoords=("data", "axes fraction"),
                   textcoords="offset points", xytext=(0, -30), ha="center",
                   fontsize=7.5, color=C.C["muted"])
    b.set_xticks(range(len(eras))); b.set_xticklabels(eras)
    b.set_ylabel("Participants")
    b.set_title("B · By era", loc="left", fontsize=10)
    b.grid(axis="x", visible=False)
    C.despine(b)

    # ---- C: by population ----
    groups = [("Healthy\nvolunteers", [s["n"] for s in E if s["n"] and s["healthy_volunteers"]]),
              ("Patient\npopulation", [s["n"] for s in E if s["n"] and not s["healthy_volunteers"]
                                       and s["indication"] != "Unclear"])]
    for i, (label, v) in enumerate(groups):
        if not v:
            continue
        jitter = np.random.default_rng(1).uniform(-0.12, 0.12, len(v))
        c.scatter([i] * len(v) + jitter, v, s=48, color=C.PALETTE[2], alpha=0.85,
                  edgecolors=C.C["surface"], linewidths=1.5, zorder=3)
        c.plot([i - 0.24, i + 0.24], [statistics.median(v)] * 2,
               color=C.PALETTE[1], linewidth=2.4, zorder=4)
        c.annotate(f"n={len(v)}", (i, 0), xycoords=("data", "axes fraction"),
                   textcoords="offset points", xytext=(0, -30), ha="center",
                   fontsize=7.5, color=C.C["muted"])
    c.set_xticks(range(len(groups))); c.set_xticklabels([g[0] for g in groups])
    c.set_title("C · By population", loc="left", fontsize=10)
    c.grid(axis="x", visible=False)
    C.despine(c)

    # ---- D: the missing attrition panel, reported honestly ----
    both = sum(1 for s in E if s["n_randomized"] is not None and s["n_analyzed"] is not None)
    rand = sum(1 for s in E if s["n_randomized"] is not None and s["n_analyzed"] is None)
    anal = sum(1 for s in E if s["n_randomized"] is None and s["n_analyzed"] is not None)
    none = len(E) - both - rand - anal
    vals = [both, rand, anal, none]
    labs = ["both\nreported", "randomised\nonly", "analysed\nonly", "neither"]
    # these are states, not series — use the reserved status palette, and the
    # axis labels carry the meaning so colour never stands alone
    bars = d.bar(labs, vals, width=0.6,
                 color=[C.STATUS["good"], C.STATUS["warning"],
                        C.STATUS["warning"], C.STATUS["critical"]],
                 edgecolor=C.C["surface"], linewidth=2)
    C.bar_labels(d, bars, vals)
    d.set_ylabel("Studies")
    d.set_title("D · Attrition is usually undeterminable", loc="left", fontsize=10)
    d.tick_params(labelsize=7.5)
    d.grid(axis="x", visible=False)
    C.despine(d); C.integer_axis(d)
    d.annotate(f"computable for {both}/{len(E)}",
               (0.97, 0.90), xycoords="axes fraction", ha="right", fontsize=8,
               color=C.C["secondary"])

    fig.suptitle("Statistical scale of the field", x=0.004, ha="left",
                 fontsize=12, fontweight="bold")
    C.save(fig, "fig06_scale",
           f"n = {len(E)} verified-complete extractions ({len(ns)} with a sample size) · "
           f"N is the number randomised where reported, else the number analysed")


if __name__ == "__main__":
    main()
