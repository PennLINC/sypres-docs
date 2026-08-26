"""Figure 11 — Trial integrity and safety reporting.

A negative-space figure: the finding is what these trials never check.

A: claimed masking (registry) vs whether blinding integrity was ASSESSED.
B: safety reporting completeness.
C: which safety sub-categories appear at all.
D: expectancy — an available template option, recorded zero times.

VERIFIED rows only. Including in-progress rows makes every rate look worse and
reads as a reviewer effect when it is really missing data.
"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                 # noqa: E402
import matplotlib.pyplot as plt     # noqa: E402
import numpy as np                  # noqa: E402

SAFETY_SUBS = ["adverse events (structured, detailed reporting)",
               "cardiovascular safety (QTc, arrhythmia, etc)",
               "abuse potential", "HPPD/perceptual persistence"]


def main():
    db = C.load()
    E = C.verified(db)
    by_id = {s["covidence_id"]: s for s in db["studies"]}

    C.use_style()
    fig, (a, b, c, d) = plt.subplots(1, 4, figsize=(13.6, 4.4), layout="constrained",
                                     gridspec_kw={"width_ratios": [1.15, 1, 1.35, 0.8]})

    # ---- A: claimed masking vs verified blinding ----
    rows = []
    for t in C.enriched(db):
        ext = [by_id[i] for i in t["paper_ids"] if by_id[i]["extracted"]]
        if not ext:
            continue
        level = (t["details"]["masking"] or "(none)").split(" (")[0]
        rows.append((level, any("Trial integrity" in p["outcome_domains"] for p in ext)))
    levels = ["Single", "Double", "Triple", "Quadruple"]
    levels = [l for l in levels if any(r[0] == l for r in rows)]
    ver = [sum(1 for r in rows if r[0] == l and r[1]) for l in levels]
    non = [sum(1 for r in rows if r[0] == l and not r[1]) for l in levels]
    x = np.arange(len(levels))
    a.bar(x, ver, width=0.6, label="blind was tested", color=C.PALETTE[0],
          edgecolor=C.C["surface"], linewidth=2)
    a.bar(x, non, bottom=ver, width=0.6, label="never tested", color=C.PALETTE[1],
          edgecolor=C.C["surface"], linewidth=2)
    for i, (v, n) in enumerate(zip(ver, non)):
        if v:
            a.annotate(str(v), (i, v / 2), ha="center", va="center", fontsize=7.5, color="#fff")
        if n:
            a.annotate(str(n), (i, v + n / 2), ha="center", va="center", fontsize=7.5, color="#fff")
    a.set_xticks(x); a.set_xticklabels(levels)
    a.set_ylabel("Registered trials")
    a.set_title("A · Claimed vs tested blinding", loc="left", fontsize=10)
    a.legend(loc="upper left", fontsize=7.5, handlelength=1.1)
    a.grid(axis="x", visible=False)
    C.despine(a); C.integer_axis(a)

    # ---- B: safety reporting ----
    any_safety = sum(1 for s in E if "Safety & tolerability" in s["outcome_domains"])
    any_blind = sum(1 for s in E if "Trial integrity" in s["outcome_domains"])
    vals = [len(E) - any_safety, len(E) - any_blind]
    bars = b.bar(["no safety\noutcome", "no blinding\ncheck"], vals, width=0.55,
                 color=C.PALETTE[1], edgecolor=C.C["surface"], linewidth=2)
    for bar, v in zip(bars, vals):
        b.annotate(f"{v}/{len(E)}\n({v / len(E):.0%})",
                   (bar.get_x() + bar.get_width() / 2, bar.get_height()),
                   textcoords="offset points", xytext=(0, 3), ha="center",
                   fontsize=7.5, color=C.C["secondary"])
    b.set_ylabel("Studies")
    b.set_ylim(0, len(E) * 1.12)
    b.set_title("B · The negative space", loc="left", fontsize=10)
    b.grid(axis="x", visible=False)
    C.despine(b); C.integer_axis(b)

    # ---- C: which safety sub-categories appear ----
    counts = collections.Counter()
    for s in E:
        for m in s["outcome_measures"]:
            dom, _, meas = m.partition(": ")
            if dom == "Safety & tolerability":
                counts[meas] += 1
    labs = [s if len(s) < 34 else s[:32] + "…" for s in SAFETY_SUBS][::-1]
    vals = [counts[s] for s in SAFETY_SUBS][::-1]
    bars = c.barh(labs, vals, height=0.6,
                  color=[C.PALETTE[1] if v == 0 else C.PALETTE[2] for v in vals],
                  edgecolor=C.C["surface"], linewidth=2)
    for bar, v in zip(bars, vals):
        c.annotate(str(v), (max(bar.get_width(), 0), bar.get_y() + bar.get_height() / 2),
                   textcoords="offset points", xytext=(4, 0), va="center",
                   fontsize=7.5, color=C.STATUS["critical"] if v == 0 else C.C["secondary"])
    c.set_xlabel("Studies assessing it")
    c.set_title("C · Which harms get assessed", loc="left", fontsize=10)
    c.tick_params(labelsize=7.5)
    c.grid(axis="y", visible=False)
    C.despine(c); C.integer_axis(c, "x")

    # ---- D: expectancy — a single value, so a stat callout rather than a chart ----
    exp = sum(1 for s in E for m in s["outcome_measures"] if "expectanc" in m.lower())
    d.axis("off")
    d.set_title("D · Expectancy", loc="left", fontsize=10)
    d.text(0.5, 0.62, str(exp), ha="center", va="center", fontsize=46,
           color=C.STATUS["critical"] if exp == 0 else C.PALETTE[0], fontweight="bold")
    d.text(0.5, 0.36, f"of {len(E)} studies\nassessed expectancy",
           ha="center", va="center", fontsize=8.5, color=C.C["secondary"])
    d.text(0.5, 0.15, "It is an available option\nin the template — the zero\nis a finding, not a gap",
           ha="center", va="center", fontsize=7.5, color=C.C["muted"])

    fig.suptitle("Trial integrity and safety reporting — what is never checked",
                 x=0.004, ha="left", fontsize=12, fontweight="bold")
    C.save(fig, "fig11_integrity_safety",
           f"n = {len(E)} verified-complete extractions · A uses the "
           f"{len(rows)} registry-enriched trials that have one · far too small to publish")


if __name__ == "__main__":
    main()
