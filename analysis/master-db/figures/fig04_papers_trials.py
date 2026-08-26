"""Figure 4 — Papers, trials, and fragmentation.

4A: how many papers each trial produced.
4B: the publication tail — each identified trial as a row, its papers as points.

Registration-status-over-time lives in Figure 10 (it would duplicate a panel).

CAVEAT the paper must state: grouping is by REGISTRATION, so an umbrella
registration covering several distinct experiments counts as one trial
(NCT03790358 holds two different Bershad substudies), while unregistered reports
with no parent DOI stay split. The ratio errs in both directions — report it as
"papers per registration", not "papers per experiment".
"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                 # noqa: E402
import matplotlib.pyplot as plt     # noqa: E402
import numpy as np                  # noqa: E402


def main():
    db = C.load()
    by_id = {s["covidence_id"]: s for s in db["studies"]}
    trials = db["trials"]

    # ---- 4A: papers per trial (identified trials + unlinked papers as singletons)
    sizes = [len(t["paper_ids"]) for t in trials]
    singles = sum(1 for s in db["studies"] if not s["trial_key"])
    dist = collections.Counter(sizes)
    dist[1] += singles

    C.use_style()
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.6, 5.0),
                               gridspec_kw={"width_ratios": [1, 1.55]})

    ks = sorted(dist)
    bars = a.bar([str(k) for k in ks], [dist[k] for k in ks], width=0.62,
                 color=C.PALETTE[0], edgecolor=C.C["surface"], linewidth=2)
    C.bar_labels(a, bars, [dist[k] for k in ks])
    a.set_xlabel("Papers reporting the same trial")
    a.set_ylabel("Trials")
    a.set_title("A · Most trials produce one paper", loc="left", fontsize=10)
    a.grid(axis="x", visible=False)
    C.despine(a)
    C.integer_axis(a)
    n_multi = sum(v for k, v in dist.items() if k > 1)
    a.annotate(f"{n_multi} trial(s) have >1 paper\nin the database so far",
               (0.97, 0.90), xycoords="axes fraction", ha="right", va="top",
               fontsize=7.5, color=C.C["muted"])

    # ---- 4B: publication tail, multi-paper trials only (singletons carry no tail)
    multi = sorted([t for t in trials if len(t["paper_ids"]) > 1],
                   key=lambda t: min((by_id[i]["year"] or 9999) for i in t["paper_ids"]))
    for row, t in enumerate(multi):
        yrs = sorted(by_id[i]["year"] for i in t["paper_ids"] if by_id[i]["year"])
        if not yrs:
            continue
        reg = not t["trial_key"].startswith("doi:")
        col = C.PALETTE[0] if reg else C.PALETTE[1]
        b.plot([min(yrs), max(yrs)], [row, row], color=col, linewidth=2, zorder=2,
               solid_capstyle="round")
        b.scatter(yrs, [row] * len(yrs), s=64, color=col, zorder=3,
                  edgecolors=C.C["surface"], linewidths=2)
        label = t["trial_key"] if reg else "unregistered"
        b.annotate(f"{label[:16]}  ({max(yrs) - min(yrs)} yr span)",
                   (max(yrs), row), textcoords="offset points", xytext=(9, 0),
                   va="center", fontsize=7.5, color=C.C["secondary"])

    b.set_yticks(range(len(multi)))
    b.set_yticklabels([", ".join(by_id[i]["study_id"] for i in t["paper_ids"])[:34]
                       for t in multi], fontsize=7.5)
    b.set_xlabel("Publication year")
    b.set_title("B · One trial, several papers, spread over years", loc="left", fontsize=10)
    b.grid(axis="y", visible=False)
    C.despine(b)
    if multi:
        b.set_ylim(-0.8, len(multi) - 0.2)
        xs = [by_id[i]["year"] for t in multi for i in t["paper_ids"] if by_id[i]["year"]]
        b.set_xlim(min(xs) - 1, max(xs) + 4)
    from matplotlib.lines import Line2D
    b.legend(handles=[Line2D([], [], color=C.PALETTE[0], marker="o", linestyle="-",
                             label="registered trial"),
                      Line2D([], [], color=C.PALETTE[1], marker="o", linestyle="-",
                             label="unregistered (linked by source DOI)")],
             loc="lower right", fontsize=7.5)

    fig.suptitle("Papers are not trials", x=0.006, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    C.save(fig, "fig04_papers_trials",
           f"{db['meta']['n_included']} papers · {db['meta']['n_trials']} trials "
           f"({db['meta']['n_registered_trials']} registered, "
           f"{db['meta']['n_unregistered_trials']} DOI-identified) · grouping is by "
           f"REGISTRATION: umbrella registrations over-merge, unlinked reports under-merge")


if __name__ == "__main__":
    main()
