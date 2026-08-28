"""Figure 7 — Design and methodological rigour.

A: comparator type (extracted — covers every verified study).
B: design model.  C: which parties were masked.

Design and blinding are read from the STUDY record, which the build fills from
the extraction template for studies with no NCT and from ClinicalTrials.gov for
those with one — so these panels span the whole corpus rather than the
registered slice, and each bar is split by which source supplied it.
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

    # ---- B: design model, extracted + registry, split by source ----
    D = [s for s in db["studies"] if s.get("design")]
    ks = [k for k in (db["meta"].get("designs") or []) if k]
    reg_n = [sum(1 for s in D if s["design"] == k and s["design_source"] == "registry")
             for k in ks]
    ext_n = [sum(1 for s in D if s["design"] == k and s["design_source"] == "extracted")
             for k in ks]
    x = np.arange(len(ks))
    b.bar(x, reg_n, width=0.55, label="from registry", color=C.PALETTE[0],
          edgecolor=C.C["surface"], linewidth=2)
    b.bar(x, ext_n, bottom=reg_n, width=0.55, label="extracted", color=C.PALETTE[2],
          edgecolor=C.C["surface"], linewidth=2)
    for xi, tot in zip(x, [r + e for r, e in zip(reg_n, ext_n)]):
        b.annotate(str(tot), (xi, tot), textcoords="offset points", xytext=(0, 3),
                   ha="center", fontsize=7.5, color=C.C["secondary"])
    b.set_xticks(x); b.set_xticklabels(ks)
    b.set_ylim(0, max([r + e for r, e in zip(reg_n, ext_n)] or [1]) * 1.18)  # label headroom
    b.set_ylabel("Studies")
    b.set_title("B · Design model", loc="left", fontsize=10, pad=20)
    b.annotate("registry for NCT studies, extracted for the rest", (0, 1.02),
               xycoords="axes fraction", fontsize=7.5, color=C.C["muted"])
    if any(ext_n):
        b.legend(loc="upper right", fontsize=7.5, handlelength=1.1)
    b.tick_params(labelsize=8)
    b.grid(axis="x", visible=False)
    C.despine(b); C.integer_axis(b)
    # ---- C: who was actually masked (roles, never a level — see the doc) ----
    roles = ["participant", "care provider", "investigator", "outcomes assessor"]
    B = [s for s in db["studies"] if s.get("blinding_roles") or s.get("blinding_flags")]
    got = collections.Counter(r for s in B for r in s["blinding_roles"])
    vals = [got[r] for r in roles]
    bars = c.barh(roles[::-1], vals[::-1], height=0.6, color=C.PALETTE[2],
                  edgecolor=C.C["surface"], linewidth=2)
    for bar, v in zip(bars, vals[::-1]):
        c.annotate(f"{v}/{len(B)}", (bar.get_width(), bar.get_y() + bar.get_height() / 2),
                   textcoords="offset points", xytext=(4, 0), va="center",
                   fontsize=7.5, color=C.C["secondary"])
    n_unspec = sum(1 for s in B if "not-specified" in s["blinding_flags"])
    if n_unspec:
        c.annotate(f"{n_unspec} state a level without naming who — never inferred",
                   (0, -0.24), xycoords="axes fraction", fontsize=7,
                   color=C.STATUS["warning"])
    c.set_xlabel("Studies masking this role")
    c.set_title("C · Who was masked", loc="left", fontsize=10, pad=20)
    c.annotate("the level (single/double/triple) hides which roles", (0, 1.02),
               xycoords="axes fraction", fontsize=7.5, color=C.C["muted"])
    c.grid(axis="y", visible=False)
    C.despine(c); C.integer_axis(c, "x")

    fig.suptitle("Design and methodological rigour", x=0.004, ha="left",
                 fontsize=12, fontweight="bold")
    C.save(fig, "fig07_design",
           f"A: n = {len(E)} verified extractions · B: n = {len(D)} studies with a design · "
           f"C: n = {len(B)} with blinding recorded · registry for NCT studies, "
           f"extracted for the rest")


if __name__ == "__main__":
    main()
