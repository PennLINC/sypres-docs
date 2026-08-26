"""Figure 7 — Design and methodological rigour.

A: comparator type (extracted — covers every verified study).
B: design model + masking level (REGISTRY-sourced — registered trials only).

The registry half of this figure covers only registered trials, which is roughly
half the corpus and the newer half. Closing it for unregistered studies is the
one remaining design-extraction ask.
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
    E = C.verified(db)
    T = C.enriched(db)

    C.use_style()
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(12.6, 4.4), layout="constrained")

    # ---- A: comparator type (a study can be several at once) ----
    order = db["meta"]["comparator_types"]
    counts = collections.Counter(t for s in E for t in s["comparator_types"])
    order = [o for o in order if counts[o]]
    vals = [counts[o] for o in order]
    bars = a.barh(order[::-1], vals[::-1], height=0.6, color=C.PALETTE[0],
                  edgecolor=C.C["surface"], linewidth=2)
    for bar, v in zip(bars, vals[::-1]):
        a.annotate(str(v), (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                   textcoords="offset points", xytext=(4, 0), va="center",
                   fontsize=7.5, color=C.C["secondary"])
    a.set_xlabel("Studies")
    a.set_title("A · What they were compared against", loc="left", fontsize=10, pad=20)
    a.annotate("extracted — covers every verified study", (0, 1.02),
               xycoords="axes fraction", fontsize=7.5, color=C.C["muted"])
    a.grid(axis="y", visible=False)
    C.despine(a); C.integer_axis(a, "x")

    # ---- B: design model, from the registry ----
    models = collections.Counter(t["details"]["model"] or "(unset)" for t in T)
    ks = [k for k, _ in models.most_common()]
    vals = [models[k] for k in ks]
    # one series → one hue; the single-group bar is flagged because it is a
    # registration error, which is a status, not a rank
    bars = b.bar(ks, vals, width=0.55,
                 color=[C.STATUS["warning"] if k == "Single Group" else C.PALETTE[0]
                        for k in ks],
                 edgecolor=C.C["surface"], linewidth=2)
    C.bar_labels(b, bars, vals)
    b.set_ylabel("Registered trials")
    b.set_title("B · Design model", loc="left", fontsize=10, pad=20)
    b.annotate("from ClinicalTrials.gov — registered trials only", (0, 1.02),
               xycoords="axes fraction", fontsize=7.5, color=C.C["muted"])
    b.tick_params(labelsize=8)
    b.grid(axis="x", visible=False)
    C.despine(b); C.integer_axis(b)
    if "Single Group" in models:
        b.annotate("⚠ 'Single Group' in an RCT\ndatabase is a registration error\n"
                   "(NCT00823407 is a crossover)",
                   (0.97, 0.72), xycoords="axes fraction", ha="right", fontsize=7,
                   color=C.STATUS["warning"])

    # ---- C: who was actually masked (not the level — see the doc) ----
    roles = ["participant", "care provider", "investigator", "outcomes assessor"]
    got = collections.Counter()
    for t in T:
        m = t["details"]["masking"]
        inside = m[m.find("(") + 1:m.find(")")] if "(" in m else ""
        for r in roles:
            if r.split()[0] in inside:
                got[r] += 1
    vals = [got[r] for r in roles]
    bars = c.barh(roles[::-1], vals[::-1], height=0.6, color=C.PALETTE[2],
                  edgecolor=C.C["surface"], linewidth=2)
    for bar, v in zip(bars, vals[::-1]):
        c.annotate(f"{v}/{len(T)}", (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                   textcoords="offset points", xytext=(4, 0), va="center",
                   fontsize=7.5, color=C.C["secondary"])
    c.set_xlabel("Registered trials masking this role")
    c.set_title("C · Who was masked", loc="left", fontsize=10, pad=20)
    c.annotate("the level (single/double/triple) hides which roles", (0, 1.02),
               xycoords="axes fraction", fontsize=7.5, color=C.C["muted"])
    c.grid(axis="y", visible=False)
    C.despine(c); C.integer_axis(c, "x")

    fig.suptitle("Design and methodological rigour", x=0.004, ha="left",
                 fontsize=12, fontweight="bold")
    C.save(fig, "fig07_design",
           f"A: n = {len(E)} verified extractions · B and C: n = {len(T)} registry-enriched "
           f"trials — unregistered studies (about half the corpus) are absent from B and C")


if __name__ == "__main__":
    main()
