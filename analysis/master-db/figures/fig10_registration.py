"""Figure 10 — Registration and reporting integrity.

A: registration status by publication year (all papers with a year + a status).
B: prospective vs retrospective registration (registry dates).
C: results posted to the registry.

Panel D of the plan — outcome switching — was CUT and is not drawn here. In a
database that deliberately includes secondary reports, a paper reporting a
secondary outcome is the normal case rather than evidence of switching; without
a flag for "the primary report of each trial" the comparison is not meaningful.
"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                 # noqa: E402
import matplotlib.pyplot as plt     # noqa: E402
import numpy as np                  # noqa: E402

BIN = 10
STATUSES = ["registered", "unregistered", "unknown"]


def main():
    db = C.load()
    E = C.verified(db)
    T = C.enriched(db)

    C.use_style()
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(12.8, 4.3), layout="constrained",
                                  gridspec_kw={"width_ratios": [1.5, 1, 1]})

    # ---- A: registration status over time ----
    rows = [s for s in E if s["year"]]
    decades = sorted({(s["year"] // BIN) * BIN for s in rows})
    mat = {st: [0] * len(decades) for st in STATUSES}
    for s in rows:
        mat[s["registration_status"]][decades.index((s["year"] // BIN) * BIN)] += 1
    x = np.arange(len(decades))
    bottom = np.zeros(len(decades))
    for k, st in enumerate(STATUSES):
        v = np.array(mat[st], dtype=float)
        a.bar(x, v, bottom=bottom, width=0.7, label=st, color=C.PALETTE[k],
              edgecolor=C.C["surface"], linewidth=2)
        bottom += v
    a.set_xticks(x); a.set_xticklabels([f"{d}s" for d in decades])
    a.set_ylabel("Studies")
    a.set_title("A · Registration arrived late", loc="left", fontsize=10)
    a.legend(loc="upper left", handlelength=1.1)
    a.grid(axis="x", visible=False)
    C.despine(a); C.integer_axis(a)

    # ---- B: prospective vs retrospective ----
    pro = sum(1 for t in T if t["details"].get("prospective") is True)
    retro = sum(1 for t in T if t["details"].get("prospective") is False)
    unk = len(T) - pro - retro
    vals, labs, cols = [pro, retro], ["prospective", "retrospective"], [C.PALETTE[0], C.PALETTE[1]]
    if unk:
        vals.append(unk); labs.append("unknown"); cols.append(C.PALETTE[4])
    bars = b.bar(labs, vals, width=0.55, color=cols, edgecolor=C.C["surface"], linewidth=2)
    C.bar_labels(b, bars, vals)
    b.set_ylabel("Registered trials")
    b.set_title("B · Registered before enrolling?", loc="left", fontsize=10, pad=20)
    b.annotate("registration date vs enrolment start", (0, 1.02),
               xycoords="axes fraction", fontsize=7.5, color=C.C["muted"])
    b.grid(axis="x", visible=False)
    C.despine(b); C.integer_axis(b)

    # ---- C: results posted ----
    posted = sum(1 for t in T if t["details"].get("results_posted"))
    bars = c.bar(["posted", "not posted"], [posted, len(T) - posted], width=0.55,
                 color=[C.PALETTE[2], C.PALETTE[1]], edgecolor=C.C["surface"], linewidth=2)
    C.bar_labels(c, bars, [posted, len(T) - posted])
    c.set_ylabel("Registered trials")
    c.set_title("C · Results posted to the registry", loc="left", fontsize=10, pad=20)
    c.grid(axis="x", visible=False)
    C.despine(c); C.integer_axis(c)
    c.annotate(f"{posted}/{len(T)} = {posted / max(len(T), 1):.0%} posted",
               (0, 1.02), xycoords="axes fraction", fontsize=7.5,
               color=C.C["muted"])

    fig.suptitle("Registration and reporting integrity", x=0.004, ha="left",
                 fontsize=12, fontweight="bold")
    C.save(fig, "fig10_registration",
           f"A: n = {len(rows)} verified extractions with a year · B and C: "
           f"n = {len(T)} registry-enriched trials · outcome switching (planned 10D) was cut")


if __name__ == "__main__":
    main()
