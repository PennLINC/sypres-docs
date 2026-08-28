# Guides & published documents

Durable, editable source for the project documents we publish as Artifacts —
reviewer guides plus the paper/figure roadmap. Each is a self-contained HTML file
that renders as an Artifact on claude.ai; this folder is the version-controlled
home so a document can be hand-edited and republished without living in a
temporary scratchpad.

## How it works

- **One HTML file per guide.** Self-contained — inline CSS, no external assets
  except Google Fonts (the only host the Artifact sandbox allows). Theme-aware
  (light/dark) via CSS tokens, so it reads correctly in either.
- **Edit the file, then republish.** Editing the file does nothing on its own; an
  Artifact is only updated when it is re-published to its URL. In this project
  that publish is a Claude tool call — so the loop is: edit here → ask Claude to
  republish → same URL, updated content.
- **Private until shared.** Publishing does not expose a guide; it stays visible
  only to the owner until shared from the Artifact's own share menu. All editing
  happens before anyone else can see it.
- **These files are NOT part of the site build.** `analysis/master-db/` is
  excluded from Jekyll (see the repo-layout note in `../CLAUDE.md`), so nothing
  here is published to sypres.io. The guides reach reviewers only as Artifacts.

## Contents

| File | Document | Artifact URL | Last updated |
|------|----------|--------------|--------------|
| [`comparator-field.html`](comparator-field.html) | **Reviewer guide** — coding the Comparator field: the three dose/co-administration options, with three worked examples (Goodwin 2022, Äbelö 2025, a 2×2) | https://claude.ai/code/artifact/c880c45d-b3a1-4615-bbed-cbad76358223 | 2026-08-28 |
| [`rct-evidence-map.html`](rct-evidence-map.html) | **Paper / figure roadmap** — the systematic-map paper plan: eleven figures (feasibility-scored), the design/blinding vocabulary, and the remaining extraction asks. Companion to [`../PAPER_OUTLINE.md`](../PAPER_OUTLINE.md). | https://claude.ai/code/artifact/bef48223-4d9b-4591-94a6-0667a8aacda5 | 2026-08-28 |

When you add a guide, add a row here with its Artifact URL so the link is never
lost — recovering it later otherwise means `action: "list"` against the Artifact
gallery.

## Editing conventions

- Keep each guide **self-contained** (inline everything except Google Fonts) so
  it publishes as a single Artifact with no broken references.
- Preserve the **light/dark token structure** at the top of each file — define
  every colour on bare `:root`, then redefine the tokens (not the components)
  under both `@media (prefers-color-scheme: dark)` and `:root[data-theme="dark"]`.
- Ground examples in **real studies from the database** and check the specifics
  against the paper before publishing — a worked example that misreads a study
  teaches the wrong thing (a mis-read of Äbelö's dose grid had to be corrected
  once already).
- After editing, ask Claude to **republish to the existing URL** (not a new one),
  so a link already shared with reviewers keeps working.
