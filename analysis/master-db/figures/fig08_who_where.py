"""Figure 8 — Who is studied, and where.

A: trial countries (REGISTRY-sourced — registered trials only).
B: healthy volunteers vs patient populations, and the single-sex studies.

Reduced by scope decision: age, % female, and race/ethnicity are not extracted,
so a representativeness panel is not possible. The paper should say that
plainly — outside the scope of this map — rather than imply the data were
unavailable.
"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                 # noqa: E402
import matplotlib.pyplot as plt     # noqa: E402


def main():
    db = C.load()
    E = C.verified(db)
    T = C.enriched(db)

    C.use_style()
    fig, (a, b) = plt.subplots(1, 2, figsize=(11.4, 4.4), layout="constrained",
                               gridspec_kw={"width_ratios": [1.25, 1]})

    # ---- A: geography (a trial can span several countries) ----
    countries = collections.Counter(c for t in T for c in t["details"]["countries"])
    ks = [k for k, _ in countries.most_common(12)][::-1]
    vals = [countries[k] for k in ks]
    bars = a.barh(ks, vals, height=0.62, color=C.PALETTE[0],
                  edgecolor=C.C["surface"], linewidth=2)
    for bar, v in zip(bars, vals):
        a.annotate(str(v), (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                   textcoords="offset points", xytext=(4, 0), va="center",
                   fontsize=7.5, color=C.C["secondary"])
    a.set_xlabel("Registered trials with a site in this country")
    a.set_title("A · Where the trials happen", loc="left", fontsize=10, pad=20)
    a.annotate("from ClinicalTrials.gov — registered trials only", (0, 1.02),
               xycoords="axes fraction", fontsize=7.5, color=C.C["muted"])
    a.grid(axis="y", visible=False)
    C.despine(a); C.integer_axis(a, "x")
    top = countries.most_common(2)
    if top:
        share = sum(v for _, v in top) / max(sum(countries.values()), 1)
        a.annotate(f"{top[0][0]} and {top[1][0]} account for\n{share:.0%} of country-trial pairs",
                   (0.96, 0.10), xycoords="axes fraction", ha="right", fontsize=7.5,
                   color=C.C["secondary"])

    # ---- B: population composition ----
    healthy = sum(1 for s in E if s["healthy_volunteers"])
    patient = sum(1 for s in E if not s["healthy_volunteers"] and s["indication"] != "Unclear")
    unclear = len(E) - healthy - patient
    sexes = collections.Counter(s["sex_specific"] or "mixed / not specified" for s in E)

    vals = [healthy, patient] + ([unclear] if unclear else [])
    labs = ["Healthy\nvolunteers", "Patient\npopulation"] + (["Unclear"] if unclear else [])
    bars = b.bar(labs, vals, width=0.55,
                 color=[C.PALETTE[2], C.PALETTE[1], C.PALETTE[4]][:len(vals)],
                 edgecolor=C.C["surface"], linewidth=2)
    C.bar_labels(b, bars, vals)
    b.set_ylabel("Studies")
    b.set_title("B · Who takes part", loc="left", fontsize=10, pad=20)
    b.grid(axis="x", visible=False)
    C.despine(b); C.integer_axis(b)
    single = {k: v for k, v in sexes.items() if k in ("male", "female")}
    # as a caption above the axes — the healthy-volunteer bar fills the panel,
    # so there is no clear space inside it
    b.annotate("single-sex studies: "
               + (", ".join(f"{v} {k}" for k, v in single.items()) if single else "none")
               + " · age and % female are not extracted, so no representativeness panel",
               (0, 1.02), xycoords="axes fraction", fontsize=7.5, color=C.C["muted"])

    fig.suptitle("Who is studied, and where", x=0.004, ha="left",
                 fontsize=12, fontweight="bold")
    C.save(fig, "fig08_who_where",
           f"A: n = {len(T)} registry-enriched trials · B: n = {len(E)} verified extractions")


if __name__ == "__main__":
    main()
