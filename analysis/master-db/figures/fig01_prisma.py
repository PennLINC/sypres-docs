"""Figure 1 — PRISMA 2020 study flow.

Drawn from the `prisma` block, so it stays in sync with the Covidence exports
and the hand-entered upstream counts in prisma_manual.json. Automation removals
appear as "removed before screening" alongside duplicates, per PRISMA 2020 —
they are NOT counted as screened.
"""
import os
import sys
import textwrap

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                              # noqa: E402
import matplotlib.pyplot as plt                                  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch   # noqa: E402

LX, LW = 0.02, 0.54          # main column
RX, RW = 0.60, 0.38          # aside column


def box(ax, x, y, w, h, title, sub=None, fill=None, edge=None, sub_size=7.5,
        stack=False):
    """A flow box. `stack=True` top-anchors the text instead of centring it —
    needed when the sub-text is many lines, which otherwise collides with the
    title and overruns the bottom edge."""
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.006,rounding_size=0.010",
                                linewidth=0.9, facecolor=fill or C.C["surface"],
                                edgecolor=edge or C.C["axis"], zorder=2))
    if stack:
        ax.text(x + w / 2, y + h - h * 0.10, title, ha="center", va="top",
                fontsize=9, color=C.C["primary"], zorder=3)
        ax.text(x + w / 2, y + h - h * 0.30, sub, ha="center", va="top",
                fontsize=sub_size, color=C.C["muted"], zorder=3, linespacing=1.6)
        return
    ax.text(x + w / 2, y + h * (0.68 if sub else 0.5), title, ha="center", va="center",
            fontsize=9, color=C.C["primary"], zorder=3)
    if sub:
        ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center",
                fontsize=sub_size, color=C.C["muted"], zorder=3, linespacing=1.5)


def vsep(ax, y0, y1):
    ax.add_patch(FancyArrowPatch((LX + LW / 2, y0), (LX + LW / 2, y1),
                                 arrowstyle="-|>", mutation_scale=11,
                                 linewidth=0.9, color=C.C["axis"], zorder=1))


def hsep(ax, y):
    ax.add_patch(FancyArrowPatch((LX + LW, y), (RX, y), arrowstyle="-|>",
                                 mutation_scale=9, linewidth=0.8,
                                 color=C.C["axis"], zorder=1))


def main():
    db = C.load()
    p, m = db["prisma"], db["prisma"]["manual"]
    complete = bool(m.get("complete"))
    C.use_style()

    # Wrap exclusion reasons to the aside width so nothing overruns the box.
    reasons = [f"{v} — {k}" for k, v in p["fulltext_excluded_reasons"].items()][:5]
    reasons = "\n".join(textwrap.fill(r, 34) for r in reasons)
    n_reason_lines = reasons.count("\n") + 1

    # (main title, main sub, aside title, aside sub, extra aside height)
    rows = []
    if complete:
        rows.append((f"{m['records_identified']:,} records identified", "across databases",
                     f"{m['removed_before_screening']:,} removed before screening",
                     f"{m['duplicates_removed']:,} duplicates\n"
                     f"{m['auto_marked_ineligible']:,} ineligible by automation", 0.0))
        rows.append((f"{m['records_screened']:,} records screened", "title / abstract",
                     f"{m['excluded_title_abstract']:,} excluded", "at title / abstract", 0.0))
    rows.append((f"{p['records_in_review']:,} records in the review",
                 "still screening or beyond", None, None, 0.0))
    rows.append((f"{p['advanced_to_fulltext']:,} advanced to full text", None,
                 f"{p['in_screening']:,} still screening", "title / abstract", 0.0))
    rows.append((f"{p['included']:,} studies included", "in the database",
                 f"{p['fulltext_excluded']:,} excluded at full text",
                 reasons + f"\n\n{p['fulltext_in_review']:,} still under full-text review",
                 0.026 * n_reason_lines))
    rows.append((f"{p['extracted']} of {p['included']} extracted",
                 "verified-complete rows", None, None, 0.0))

    H, GAP = 0.105, 0.055                      # box height, arrow gap
    total = len(rows) * H + (len(rows) - 1) * GAP + 0.06
    fig, ax = plt.subplots(figsize=(7.4, 7.4 * total * 1.10))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

    # scale the layout to fill the axes
    H, GAP = H / total, GAP / total
    y = 1.0 - 0.055 / total
    tint = C.SEQ[0] if not C.DARK else "#16302c"

    for i, (title, sub, aside, aside_sub, extra) in enumerate(rows):
        last = i == len(rows) - 1
        first = i == 0
        box(ax, LX, y - H, LW, H, title, sub,
            fill=tint if (first and complete) or last else None,
            edge=C.PALETTE[0] if last else (C.PALETTE[2] if title.endswith("included") else None))
        if aside:
            ah = H + extra / total
            box(ax, RX, y - ah, RW, ah, aside, aside_sub, sub_size=6.8,
                stack=extra > 0)
            hsep(ax, y - H / 2)
        if not last:
            vsep(ax, y - H, y - H - GAP)
            y -= H + GAP

    ax.set_title("Study flow (PRISMA 2020)", loc="left", pad=12, x=LX)
    if not complete:
        ax.text(LX, 1.005, "⚠ upstream counts not entered — funnel starts mid-stream",
                fontsize=8, color=C.STATUS["warning"], transform=ax.transAxes)
    C.save(fig, "fig01_prisma",
           f"Generated {db['meta']['generated']} · "
           + ("counts reconcile exactly" if m.get("reconciles")
              else "⚠ counts do not reconcile"))


if __name__ == "__main__":
    main()
