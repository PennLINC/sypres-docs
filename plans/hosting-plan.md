# sypres.io hosting: GitHub Pages or the extract Lightsail box?

| | |
|---|---|
| **Status** | Decision memo with technical appendix. Nothing here has been executed. |
| **Date** | 2026-10-16 (all live checks and prices are as of this date) |
| **Shared page** | https://claude.ai/artifact/3NGQYHjpniQZMCYM1MaRpC (private until shared from its Share menu; republish from this file after edits, same URL) |
| **Scope** | Whether the public website should move from GitHub Pages onto the Lightsail instance that runs `extract`, what that would and would not enable, and what to do instead or first. |
| **Not in scope** | Changing the theme or generator, redesigning pages, and anything that modifies extract's review data or its access rules. |
| **Source state** | sypres-docs read on branch `master-db` with `origin/main` fetched (893 commits). extract read at commit `295293b` on branch `sns-alerts`, one commit ahead of `origin/main` `51a75e6` (2026-10-13), which merged that branch; extract line numbers refer to that checkout and may differ by a few lines on `origin/main`. |

This folder (`plans/`) is excluded from the Jekyll build in `_config.yml`, so this file is never published on sypres.io. The exclude line and this folder must be committed together.

---

## 1. The answer

**Can sypres.io move onto the extract box? Yes, and it is cheap to do.** Caddy, the web server that terminates HTTPS for extract, already owns ports 80 and 443 on the instance. Serving the site is one more Caddy site block plus an rsync of the `_site` folder that GitHub Actions already builds. Reaching parity with today's site is roughly 12 to 18 hours of work. The $12 Lightsail plan (2 GB of RAM per extract's deployment notes; the plan's published specification adds 2 vCPU, 60 GB of disk and 3 TB of transfer, to be confirmed in the console) is far larger than a 72 MB website needs.

**Would it give more for website design and features? For design, no. For features, partly.** Design is decided by the theme and the generator, not by the host (section 3). Of every feature that came up in the analysis, four need a server at all: counted downloads, search and a query API over the database, forms without GitHub accounts, and reviewer-only guides. All four fit on a subdomain of the box without moving the pages. What the box could enable over one to three years is in section 5.

**Should the apex domain move now? No.** Three reasons, each backed by evidence in this document:

1. **It buys nothing you lack.** GitHub Pages costs $0. The site is already built by a custom GitHub Actions workflow, which lifted every Pages restriction on Jekyll versions, plugins and build counts.
2. **It inverts the availability model.** The public face of SYPRES would inherit a single-AZ (one data centre, no failover) burstable VM with a 20% CPU baseline, no swap or memory limits in its deployment files, alerts that were never configured, a restore procedure that was never exercised, one operator, and a Lightsail SLA that pays credits only below 99.5% monthly uptime. That same VM holds pre-publication, blinded review data.
3. **Every documented pain point attaches to data products and jobs, not to the pages.** Uncountable downloads, a 439 KB page with the whole database inlined, 666 bot commits that are 75% of `main`'s history, a laptop-only rebuild loop, reviewer guides living as claude.ai links. All of these can be fixed either with no server at all, or on a subdomain of the box without touching sypres.io.

**What to do instead, in order:**

- **Weeks 1 to 5, host-independent (about 14 to 23 hours):** stop the daily bot commits, merge the unmerged `master-db` branch so the Psychedelic RCT Database goes live, make the page fetch its data instead of inlining it, mint a Zenodo DOI for a counted canonical download, track `Gemfile.lock`, and drop 31 MB of InDesign files from the published tree.
- **Week 1, on the box, for extract's own sake (about 3 to 4 hours):** measure headroom, add swap, log rotation, an explicit Docker Compose project name (Compose is the file that defines extract's containers), a liveness check, and a Lightsail alarm if the Penn-managed account allows one.
- **Then the hybrid (about 15 to 24 more hours, 32 to 51 in total):** `db.sypres.io` on the same box, serving the database as fetchable JSON and CSV, with Datasette (an off-the-shelf read-only web UI and JSON/CSV API over a SQLite file) for search and permalinks, counted downloads, and host cron replacing the CI schedules for the tracker, dashboard and enrichment. It needs the Phase 1 build artefacts, the Phase 0 headroom numbers and decision 5, not Phase 3, so it can run while the review is still in Covidence, built from the committed exports. The extract publish step (Phase 3) replaces that input once two decisions are taken: the Master DB review moves from Covidence into extract for production work, and the PIs accept consensus-only public numbers (only values the reviewers have jointly settled, never one reviewer's draft).
- **Revisit the apex only with data**, after about three months of free-memory and burst-credit history with Datasette running, using the exit triggers in section 9.

**Four facts are still unknown** and should be filled in before any hours are committed: real traffic (GA4, not GitHub repository views), the instance's actual headroom, when Covidence gives way to extract, and the licence under which abstracts and extracted fields may be redistributed.

### Terms used in this memo

| Term | Meaning here |
|---|---|
| Caddy | The web server in front of extract. It obtains HTTPS certificates automatically and forwards requests to the app. |
| Docker Compose | The file (`docker-compose.prod.yml`) that defines extract's three containers and how they start. |
| Datasette | An off-the-shelf tool that serves a SQLite file as a browsable, searchable website with a JSON/CSV API. |
| Consensus-only | Publishing only extraction values the reviewers have jointly settled, never a single reviewer's draft. |
| Single-AZ, burst credits | One data centre with no failover; and the CPU allowance a small Lightsail VM accrues while idle and spends under load. |
| PRISMA | The study-flow diagram systematic reviews must report (records identified, screened, excluded, included). |
| HSTS | A response header telling browsers to use HTTPS only for a hostname. extract deliberately limits it to its own hostname. |
| CORS | Browser permission for a page on one hostname to fetch data from another (needed for sypres.io pages reading `db.sypres.io`). |
| ExportRun | extract's audit record of every export: profile, parameters, row count, sha256, who ran it. |
| Kappa, PABAK | Agreement statistics between two screeners. |
| Zenodo DOI | A permanent identifier for a deposited dataset version; Zenodo also counts downloads. |

---

## 2. What you have today, in numbers

Verified 2026-10-16 against the repos, the live site and the GitHub API. "Estimate" marks figures derived from configuration rather than measured.

### The site

| Fact | Value | Evidence |
|---|---|---|
| Content | 27 live content URLs (28 once `master-db` merges), about 32k words: 20 posts (datasets 10, blog 8, community 2) and 7 pages, plus the unmerged database page | `docs/` tree; local 2026-09-22 build of `master-db` |
| Generator | Jekyll 3.9.3 on a vendored Minimal Mistakes 4.24 fork copied from the RBC site (commit `0cbe151`, 2025-04-10) | `minimal-mistakes-jekyll.gemspec:18`; `_config.yml:122,128` |
| Build and deploy | Custom GitHub Actions workflow (Ruby 3.1, `bundle exec jekyll build`, `actions/deploy-pages`) on every push to `main` | `.github/workflows/jekyll.yml:9-65` |
| Pages settings | custom domain `sypres.io`, HTTPS enforced, `build_type: workflow`; certificate for `sypres.io` and `www.sypres.io` expires 2027-01-01 | `gh api repos/PennLINC/sypres-docs/pages` |
| GitHub plan | PennLINC organization is on **Free**: no contractual Pages SLA; repository Discussions are off | `gh api orgs/PennLINC`; `gh api repos/PennLINC/sypres-docs` |
| Built size | About 72 MB, of which `analysis/` is 64 MB; about 31 MB (16 files) are InDesign `.indd` sources; 57 files (46 MB) are published but referenced by no page. Measured on a local 2026-09-22 build of `master-db`; the live build differs only by the database page | `du -sh _site`; `find _site -name '*.indd'`; href scan of `docs/` |
| Repository | 428 tracked files, about 79 MB; `.git` 289 MB on disk, never gc'd (276 MB loose objects vs 7.2 MB packed); a 16 MB team photo in history | `git ls-files`, `git count-objects -vH` |
| Toolchain | Ruby 3.1.4 (end of life), `jekyll = 3.9.3` pinned by the gemspec, `Gemfile.lock` gitignored so CI re-resolves every build, shim gems (`csv`, `base64`, `bigdecimal`, `webrick`, `faraday 2.9.2`), six unmerged Dependabot branches | `.ruby-version`; `Gemfile:3-9`; `.gitignore:14`; `git branch -a` |
| Interactive elements | A Bokeh download chart (26 KB HTML, iframed on the home page) and the Master DB page (unmerged branch). No site search (lunr disabled), no comments; `staticman.yml` is a dead leftover | `index.md:76`; `_config.yml:33, 62-64` |
| DNS | Namecheap nameservers; apex A records to GitHub Pages; `www` CNAME to `pennlinc.github.io`; MX and SPF point at **Namecheap email forwarding**; no CNAME file in the repo | `dig`; repo root |
| Live headers | `server: GitHub.com` via Fastly; `cache-control: max-age=600`; `access-control-allow-origin: *`; `www` and `http` 301 to `https://sypres.io/`; extensionless `/docs/blog/index` returns 200 | `curl -sI https://sypres.io/` |
| Analytics | GA4 `G-YTGXSZFJ08`; Search Console and Bing verification tokens are blank | `_config.yml:98-104, 76-77` |

### The pipelines

| Fact | Value | Evidence |
|---|---|---|
| Bot commits | 666 of 893 commits on `origin/main` (75%) are `Update dashboard` or `Update download statistics`; about 60 per month; since 2026-08-17 one Pages deploy per night, dispatched by the dashboard workflow (none before that date) | `git log origin/main --format=%s` |
| Why they rebuild the site | Pushes made with `GITHUB_TOKEN` do not trigger `on: push`, so since 2026-08-17 the dashboard workflow calls `gh workflow run jekyll.yml` explicitly | commit `6b738ad`; `update-dashboard.yml` on `origin/main` |
| Last human commit on `main` | 2026-08-17 | `git log origin/main` |
| Master DB page | Lives only on branch `master-db` (20 ahead, 245 behind `origin/main`); **not live** | `git rev-list --count` |
| Master DB data on that branch | `_data/master_db.json` 465,926 bytes inlined by Liquid into a 439 KB HTML page; 95 studies, 16 extracted, 22 trial cards; generated 2026-08-28 | `docs/datasets/master-db/index.html:126`; JSON `meta` |
| Newer data, untracked | The 2026-10-02 Covidence export in `analysis/master-db/data/`: 203 included, 112 excluded, 1,045 in full-text select, 0 left in screening, a new `irrelevant` stage file with 3,374 rows, and 131 extraction rows for 83 studies of which 18 are Covidence **Consensus** rows | row counts of the six untracked CSVs |
| What the build does with it | `build_database.py` has no key for the `irrelevant` stage and hard-codes `CONSENSUS_REVIEWER = "Parker Singleton"`; a dry run on the Oct-2 files gives 203 included, 34 extracted, and PRISMA no longer reconciling (+826) | `analysis/master-db/build_database.py:65, 1028, 1216` |
| Rebuild cadence | Six rebuilds ever, all by hand on a laptop (Covidence export, run the script, commit) | `git log -- _data/master_db.json` |
| Public names | `meta.extraction_coverage` names four reviewers with row counts; each study carries a `reviewer` field; the page shows "Extracted by" and the CSV export includes the column | `_data/master_db.json`; `docs/datasets/master-db/index.html:593, 807` |
| Enrichment | ClinicalTrials.gov details (30-day local cache) and Blossom summaries (API key in a shell, last run 2026-04-20) run by hand | `analysis/master-db/build_database.py:47-51`; `README.md:56-91` |
| Living reviews | R 4.4.1 + renv projects knitted by hand to markdown with static PNG figures; interactive dashboards are hosted by Metapsy, not sypres.io | `analysis/psilodep/README.md`; dataset posts |
| Reviewer guides | Five self-contained HTML guides (307 KB) kept out of the build and distributed as claude.ai Artifact links | `analysis/master-db/guides/README.md:21-23` |

### The box

| Fact | Value | Evidence |
|---|---|---|
| Instance | Lightsail us-east-1, $12 plan, 2 GB RAM, Ubuntu 24.04, static IP. The current $12 plan is published as 2 vCPU, 60 GB SSD, 3 TB transfer and a 20% CPU baseline per vCPU (burstable); extract's docs state only the RAM, so treat the rest as an estimate until the console confirms the instance generation | `extract/deploy/DEPLOY.md:14`; Lightsail pricing |
| Database and storage | Managed PostgreSQL 16 ($15 Standard, 7-day point-in-time recovery); versioned bucket for dumps and PDFs | `extract/deploy/DEPLOY.md:19-32` |
| Stated cost | "About $30/month" (an estimate in DEPLOY.md, not an invoice) | `extract/deploy/DEPLOY.md:5` |
| Compose | Project has no `name:`, so it is implicitly named `deploy`; `deploy.sh` runs `up -d --remove-orphans` | `extract/deploy/docker-compose.prod.yml`; `extract/deploy/deploy.sh:37` |
| Caddy | One container binds 80/443 with a single `{$EXTRACT_HOSTNAME}` site block; the Caddyfile is tracked in git and bind-mounted read-only; `caddy` has `depends_on: web` | `extract/deploy/Caddyfile:4-14`; `extract/deploy/docker-compose.prod.yml:31-44` |
| App processes | gunicorn with 3 sync workers serving Django and the React build through WhiteNoise; a worker container; images are built **on the instance** by `deploy.sh` | `extract/deploy/Dockerfile:50`; `extract/deploy/deploy.sh:25-26` |
| Headroom | Unmeasured. Estimate from configuration: 0.8 to 1.2 GB steady, plus 0.5 to 1 GB during an on-box image build. No swap, no memory limits, no log rotation, no image prune | grep of `deploy/` and `docs/` |
| Nightly jobs | 07:15 backup, 07:45 integrity check and heartbeat, Sunday 08:30 restore drill, Sunday 09:30 thorough checks; do not restart 07:00 to 08:00 UTC or Sunday 08:30 to 10:30 | `extract/deploy/extract.cron`; `extract/deploy/DEPLOY.md:292-294` |
| Alerting | Application alerts **not configured**: the Penn-managed AWS role has SNS access but was refused SES and `iam:CreateUser`, so the IAM key an SNS topic needs must come from an administrator (per the checkout's `295293b`; `origin/main` still says an unsigned publish works without a key); detection of an outage can take "most of a day" via the once-daily heartbeat | `extract/deploy/DEPLOY.md:127-157, 324-327`; `extract/docs/RUNBOOK.md:22-23` |
| Disposability | "Instance snapshots are not needed: the instance holds no review data"; restore from scratch is documented but never exercised | `extract/deploy/DEPLOY.md:7-10, 17-18` |
| Hosts and cookies | `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` name only the extract hostname; cookies are host-only; HSTS 30 days deliberately **without** `includeSubDomains` ("must not be extended to the rest of sypres.io") | `extract/backend/config/settings.py:52-56, 168-185` |
| Unauthenticated surface | Only `/api/v1/health` (plus the login flow) is unauthenticated; an anonymous request to `/api/v1/auth/me` returns 401; no public API, no tokens, no "public review" concept | `extract/backend/config/api.py:23-30, 50`; live `curl` |
| Exports and rule 7 | Exports are owner-only and each writes an `ExportRun` row with a sha256; rule 7: reviewers are blind to each other | `extract/backend/apps/exports/api.py:19-45`; `extract/CLAUDE.md:37-43` |
| Roadmap hooks | `covidence_zip` export exists so `build_database.py` keeps working unchanged; an opt-in cross-repo parity test (`pytest -m real_data`, needs the sibling checkout) passes per extract's README; extract's stage list already includes `irrelevant`; planned: PRISMA counts from the event log, metapsyTools export, CT.gov enrichment port, living-review update imports, agent tokens | `extract/backend/apps/exports/profiles.py:600-652`; `extract/backend/apps/covidence/stages.py:17`; `extract/backend/tests/test_real_covidence.py:5-7`; `extract/docs/MASTER_PLAN.md:110-117, 155-163` |
| Where production work happens | **Still Covidence.** extract's README describes a test migration of the Master DB review (4,734 records, matching the Oct-2 export exactly); the RUNBOOK says to migrate "when the team is ready to stop working in Covidence" | `extract/README.md:84-88`; `extract/docs/RUNBOOK.md:135-139` |

### The four unknowns

| Unknown | Why it matters | How to fill it |
|---|---|---|
| Real traffic | Sizes every bandwidth, CDN and burst-credit argument. GitHub's repo traffic API (19 views, 9 uniques in 14 days) counts **repository** page views, not site visits | GA4 property `G-YTGXSZFJ08`: users, pageviews, top pages, peak day, 90 days |
| Instance headroom | Decides whether anything public can share the box, and whether the $24 plan is needed | `free -m`, `docker stats --no-stream`, `df -h`, BurstCapacityPercentage, idle and during a `deploy.sh` build |
| Covidence to extract timing | Every "extract publishes nightly" step waits for it | PI decision |
| Data licence | A Zenodo deposit, a CSV download or an API redistributes abstracts and extracted fields under an implied MIT licence today | Librarian check of Embase, Scopus, Web of Science and PubMed terms; a `LICENSE-DATA` decision |

---

## 3. Hosting, website design and features are three different questions

The question that prompted this memo was whether moving hosts would give "more benefits for website design and features". It helps to separate three things:

- **Design** is decided by the theme and the generator. The site is a vendored Minimal Mistakes fork with Bootstrap 4 bolted on. A redesign (a new skin, a new theme, Jekyll 4, Hugo, Astro or Quarto) produces a directory of files that GitHub Pages, Cloudflare Pages or Caddy serve identically. The host changes nothing here.
- **Static tooling restrictions** were already removed when the build moved to a custom GitHub Actions workflow. The Pages plugin whitelist, the Jekyll 3.10 pin and the 10-builds-per-hour limit apply only to the built-in Pages builder, which this site no longer uses.
- **Server-side features** are the only thing that depends on the host. The table below lists every feature that came up in the analysis and says whether it needs a server at all.

| Wished-for feature | Needs a server? | Cheapest way to get it |
|---|---|---|
| Counted downloads of the database | **Yes**, or a counted artifact elsewhere | Zenodo DOI plus GitHub Releases counts folded into the existing `fetch.py`/`fetch_zenodo.py` pipeline (the team's own written plan); or Caddy access logs on `db.sypres.io` |
| Master DB page that scales past hundreds of rows | No | Fetch a separate static JSON with pagination (the team's own scaling note); Datasette later for thousands of rows with full-text search |
| Stop the daily bot commits | No | Build the dashboard inside the scheduled Pages workflow and keep tracker state on a data branch or in the bucket; or host cron on the box |
| Per-query API, full-text search, per-study permalinks | **Yes** | Datasette on `db.sypres.io` (SQLite, facets, FTS, JSON/CSV endpoints, `--cors`) |
| Corrections and missing-study reports without a GitHub account | **Yes**, or a third party | A small rate-limited endpoint (optional, later); today's pre-filled GitHub issue links work for the research audience |
| Reviewer-only guides | **Yes** (a login) | `forward_auth` to extract's own session check on `extract.sypres.io/guides/`; or publish them openly under `/docs/methods/` |
| PR previews, custom headers, real redirects | No server needed | Cloudflare Pages Free (native previews, `_headers`, `_redirects`); Caddy also does it |
| Scheduled enrichment (CT.gov, Blossom) with keys off laptops | CI or box cron | Either; the box gives exact timing and a persistent cache |
| PRISMA counts that reconcile by construction | No (an extract export) | MASTER_PLAN §3(5), PRISMA counts derived from the event log |
| Interactive living-review dashboards ("observe the influence of analysis choices") | Not solved by any hosting option | Stays Metapsy's until extract's metapsyTools export and precomputed forest-plot JSON exist (MASTER_PLAN Phase 7) |

Only four rows need a server, and all four fit on a subdomain. None of them needs the brochure pages to move.

---

## 4. Options compared

Four real options. Hours are estimates for one experienced maintainer and are the sums of the phase estimates in section 7. "Pains fixed" refers to the documented list: **counting**, **baked data**, **bot commits**, **laptop loop**, **enrichment**, **guides**, **forms**, plus **previews/headers**, which is the analysts' addition (the repositories record no such complaint).

| | **A. Stay as-is** | **B. Stay static, fix the pipeline** | **C. Hybrid: `db.sypres.io` on the extract box** | **D. Full apex move to the box** |
|---|---|---|---|---|
| Phases in section 7 | none | Phase 0 (site half), Phases 1 and 2 | Phases 0 to 5 | Phases 0 to 5 plus 12 to 18 hours of hosting parity |
| Cash per month | $0 change | $0 (optional +$1 for a public bucket) | $0; +$12 only if headroom forces the $24/4 GB plan | $0; +$2.50 Lightsail CDN or Cloudflare free; +$1 to $3 snapshots; +$12 contingency |
| One-time hours | 0 | 14 to 23 | 32 to 51 | 44 to 69, of which 12 to 18 is parity that delivers no new benefit |
| Recurring hours per month | 0 | 0.5 to 1 | 1 to 2 | 3 to 5 (estimate: C plus apex TLS and DNS, previews, a forms bridge, a Cloudflare zone, public-site incident response) |
| New components and secrets on the box | none | one cron'd management command, one outbound key | a public hostname, Datasette, a jobs container, a cron file, a second `.env` (traffic PAT, Blossom key), a push-only deploy key for the data repository, healthchecks.io URLs | all of C plus the public apex, a pull credential for the site build, previews, a forms bridge, a Cloudflare zone |
| DNS change | none | none (Cloudflare optional: nameserver move) | one A record | apex cutover; a nameserver move to Cloudflare breaks Namecheap email forwarding unless migrated |
| Availability model | GitHub and Fastly anycast, no SLA on Free (2026-04-13: 97 minutes at about 10.6% error rate) | same | shell and table unchanged (the JSON is baked into the Pages build); search, permalinks and the counted download fail while the box is down, and the Zenodo copy stays | single-AZ burstable VM, SLA credits only below 99.5%, extract's maintenance windows become public ones |
| Pains fixed | none | counting (via Zenodo), baked data, bot commits, laptop loop, enrichment (CI) | all of B plus a real API and server-counted downloads; guides via extract login; forms optional | all of C plus previews and headers on the apex |
| Risk to extract | none | low (one command writes to a shared directory) | medium, mitigated (memory limits, swap, separate Compose project, no new endpoint or database role) | highest (public traffic and an inbound GitHub credential on the box that holds `deploy/.env`) |
| Who operates, who is paged | GitHub operates; nobody is paged | GitHub operates the site; CI failure emails reach the maintainer | the maintainer operates `db.sypres.io`; healthchecks.io pings the maintainer; a second person needs access (decision 13) | the maintainer operates the public site and its edge; same |
| Who pays | the Penn-managed AWS account already pays about $30/month for extract; GitHub $0 | same | same account, +$0 to $12 | same account, +$0 to $18 |
| What readers see change | nothing | the database page goes live; it loads its table after first paint | B, plus rows link to `db.sypres.io`; a "search unavailable" state and a fallback to the Zenodo download if the box is down | a DNS cutover with possible minutes of errors; shared maintenance windows |
| Rollback | n/a | git revert or a config flip per step | delete one A record and one Caddy file; stop one container; comment out cron lines | DNS flip while GitHub's certificate lasts (90-day, auto-renewed only while DNS points at Pages), then re-verify the domain; a nameserver move is sticky |
| First user-visible benefit | never | after Phase 0 (site half) and Phase 1, about 11 to 18 hours (bot commits stop, database page live at 203 studies) | after Phases 0 and 1, about 14 to 22 hours | after parity and the same data work, about 26 to 40 hours |

**How the design panel split.** Three advocates wrote the strongest plan for B, C and D; three judges scored them from an operations and security lens, a research-value lens, and a cost and simplicity lens. Two judges picked B, one picked C. All three recommended the **same sequence**: B's core first, then C as the measured next step, and never D now. D's own advocate conceded that the hybrid is the correct stopping point if headroom or the proxy decision goes the other way, and that the case for the apex is "coherence, not price". This memo adopts that sequence.

---

## 5. Vision: what the box enables that Pages makes hard

The vision below is the hybrid's end state, one to three years out, with extract as the source of truth for every SYPRES review and sypres.io as its public face. Each paragraph names what someone can do that they cannot do today.

**Readers.** The Psychedelic RCT Database at `db.sypres.io` becomes a living systematic map. A reader filters by drug, indication, outcome domain, phase, registration status or year, searches abstracts, opens a stable permalink for a study or a trial, and sees which registered trials have no publication. The PRISMA box shows counts derived from extract's event log that reconcile by construction and move as screening proceeds. Every page says "data as of last night's consensus" with a manifest hash. The full database downloads as a counted CSV or RIS, or as a dated release with a DOI, and those downloads appear on the home-page chart beside the Metapsy datasets.

**Other researchers.** A JSON/CSV API they can script against (`?_search=microdosing`, facet parameters) seeds their own reviews without asking for a file. A frozen version DOI makes every number in the map paper reproducible from a citable artefact, and a stable concept DOI goes in protocols and the data descriptor. A SQLite file carries the same data for offline work. Agreement statistics (kappa, PABAK) are computed inside extract from per-reviewer decisions, which Covidence never exported, and published as aggregate numbers only; individual reviewers' decisions never leave extract (constraint 1).

**Reviewers and the team.** The Covidence-export, laptop, commit loop disappears: settling a study in extract is the publication step. Guides and SOPs live at a stable URL behind the reviewers' own extract logins instead of claude.ai links tracked in a README. Reader corrections arrive as flagged suggestions beside the record they concern. Agent reviewers' outputs never reach the public side, because the publish step emits FINAL consensus only. Enrichment from ClinicalTrials.gov and Blossom runs on a schedule with keys kept on the server.

**The living reviews.** extract's planned metapsyTools export means the PSILODEP and MDMAPTSD effect-size tables regenerate from extract rather than from a hand-knitted Rmd. The natural next step, precomputing forest-plot and subgroup results into JSON at publish time and rendering them client-side, is what would finally honour the About page's promise that readers can observe the influence of analysis choices, without putting R on a server.

**What this vision does not deliver, under any hosting option:**

- Living-review interactivity stays Metapsy's until the MASTER_PLAN Phase 7 work exists. The About-page sentence promising it should be softened now.
- The website's look does not change. Design is a theme decision.
- The Ruby/Jekyll fragility is fixed where it lives (track the lockfile, pin or containerize the build), not by moving hosts.
- extract's own application alerts remain blocked by the Penn-managed AWS role; Lightsail alarms cover instance metrics, not failed integrity checks.
- Per-reviewer transparency: individual votes and extractions stay inside extract by rule 7; only aggregates are published.
- Today the home-page download chart counts only the two Metapsy repositories; Phase 2 adds the Master DB release to it. Whether the chart keeps a nightly job at all is decision 8.

---

## 6. Constraints that apply to every option

These apply to the hybrid and to any later apex move. Several apply to the static fixes too.

1. **Rule 7 and the publish contract.** extract's reviewers are blind to each other and exports are owner-only. Anything that leaves extract for the website must be an explicit publish of FINAL consensus, produced by the `covidence_zip` profile with a `consensus_only` flag enforced **inside the profile** (never by post-filtering), under a named publisher identity, recording an `ExportRun` row, with tests that the extraction file's `Reviewer Name` column contains only `Consensus`, and with the inbox deleted after each build so the instance still "holds no review data". **Visible consequence:** the page would show 18 consensus-extracted studies, against 16 on the unmerged branch today and 34 if one reviewer's rows keep standing in for consensus (the Oct-2 export has 131 extraction rows: 51, 34 and 28 by reviewer plus 18 Consensus). That drop is a PI decision, not a default.
2. **Shared fate and unmeasured headroom.** Nothing in either repository records `free -m`, `docker stats` or burst credits. `caddy` has `depends_on: web`; Compose recreates `caddy` only when its own configuration or image changes, so a routine deploy probably leaves it running, but nobody has watched one. Measure first; add swap and memory limits before anything public lands on the box.
3. **Penn-managed AWS permissions.** The role has SNS access but was refused `iam:CreateUser` and SES. Lightsail alarms, notification contacts (one email address per Region), snapshots and CDN distributions have not been tested under it. Probe once, early, and file the administrator ticket if refused. Account administrators and billing visibility are not named anywhere in the repositories.
4. **Domain and email.** `sypres.io` is registered at Namecheap (WHOIS: registrant hidden by a privacy service; created 2025-04-03, expires 2030-04-03). Whose Namecheap account holds it is unknown; record it in Phase 0. Its MX records point at Namecheap's free email forwarding. Cloudflare's free proxy and Cloudflare's static hosting both require the zone's nameservers on Cloudflare, and Cloudflare's documentation requires an apex custom domain to be a zone on the account (an ALIAS record at Namecheap is not a documented path, so treat it as unsupported). Moving nameservers therefore breaks any `@sypres.io` forwarding unless it is migrated (Cloudflare Email Routing is free). Identify who holds the Namecheap, GitHub Pages and Zenodo logins.
5. **Penn Digital Accessibility Policy.** Penn's policy treats migration to a new platform as a significant revision that triggers conformance (WCAG 2.2 AA for sites built or substantially revised after 2024-07-01). The site publishes data tables as PNG images and a custom JavaScript facet table. Confirm applicability for a Penn Medicine lab site on a non-upenn.edu domain and add an axe or Lighthouse check to any phase that adds public pages.
6. **Data licence and abstract copyright.** The only LICENSE in the repository is the theme's MIT. The committed Covidence CSVs hold about 2,200 records (roughly 900 with abstracts) from Embase, PubMed, Scopus and Web of Science; the untracked Oct-2 export holds about 4,700 records (roughly 2,400 with abstracts); the published JSON carries 92 abstracts. A Zenodo deposit, a CSV download or an API redistributes them. Decide a data licence (CC BY 4.0 for extracted fields is the usual choice), decide whether abstracts are display-only, add `LICENSE-DATA` and `CITATION.cff`, and ask the librarian about the databases' redistribution terms. Blossom's attribution requirements are also unconfirmed.
7. **Co-reviewer names.** Four reviewers' names and row counts are already in the public `master-db` branch (in `_data/master_db.json` and the page's inlined JSON) and would appear in the live page source once merged; the rendered page shows one name. Nightly publishing would make those counts move daily. Rename the public field to "Consensus", keep names only in an acknowledgements line, and ask the co-reviewers before the first automated publish.
8. **Privacy.** GA4 does not store IP addresses, so `anonymize_ip: false` is moot. The open items are a cookie notice for GA4 and, if server access logs appear on the box, masking of both `remote_ip` and `client_ip` and a stated retention period on the Get Support page.
9. **SEO and URL continuity.** Search Console is not verified, so there is no baseline of indexed URLs or backlinks. Verify it now (host-independent). Any future apex move must preserve mixed-case paths, trailing-slash directory indexes, extensionless links such as `/docs/blog/index` (Caddy needs `try_files {path} {path}/ {path}.html`), `www` and `http` redirects, `sitemap.xml`, `robots.txt` and `feed.xml`.

---

## 7. Recommended phased plan

Each phase is independently shippable, has a "done when", a one-move rollback and a line on what readers see. Each host-dependent change (Phases 0, 3, 4 and 5, in whichever order the gates open) gets a week of observation before the next one lands; the host-independent phases can overlap. The `sypres-public` Compose project and `jobs` image (appendix C) are built by whichever of Phases 3 and 4 runs first. Hours are estimates for one maintainer; section 4 sums them per option.

### Phase 0. Measure, record and clean up (week 1, about 6 to 9 hours)

No public change. Half of this is extract's own hygiene and is worth doing whatever happens to the website. Readers see: nothing.

**Measure and record** (results go into `extract/deploy/DEPLOY.md` under a new "Capacity" heading and into "What lives where"; make those edits on `main` after extract commit `295293b`, the one `sns-alerts` commit still unmerged on 2026-10-16, which rewrites the alerts section, or rebase onto it first):

- On the box: `free -m`, `swapon --show`, `df -h /`, `docker system df`, `docker stats --no-stream`, `uptime`; repeat during a `deploy/deploy.sh` run to catch the on-box image build peak; `docker compose ls` to confirm the project is literally named `deploy`.
- Lightsail console: 14-day CPU utilisation against the 20% baseline and BurstCapacityPercentage; confirm the instance is the 2 vCPU generation; find the real bill and the bucket plan.
- Watch one routine `docker compose up -d` after an image rebuild and note whether `caddy` is recreated.
- Permission probe under the Penn role: create one Lightsail alarm with a notification contact and one manual snapshot. If allowed, keep the alarm (BurstCapacityPercentage and instance status) and delete the snapshot; if refused, file the administrator ticket now.
- Elsewhere: GA4 90-day traffic; the complete Namecheap DNS record list and Mail Settings (configured forwards); verify the property in Search Console; record who holds the Namecheap, Pages, Zenodo and Lightsail logins.

**Box hardening** (extract PR plus host commands, scheduled outside 07:00 to 08:00 UTC):

- `name: deploy` at the top of `deploy/docker-compose.prod.yml`. This makes the implicit project name explicit with no migration. Renaming the project (for example to `extract`) would strand the running containers and the `deploy_*` volumes that hold the local dumps and certificates, and `deploy.sh` would then fail on ports 80/443; do not do that casually.
- A 4 GB swapfile with `vm.swappiness=10` (AWS sizing guidance is twice RAM at 2 GiB or less).
- `/etc/docker/daemon.json` in two steps: first add `"live-restore": true` and run `systemctl reload docker` (reloadable, no restart, containers unaffected); then add `json-file` log limits and `systemctl restart docker` (containers keep running thanks to live-restore). Log limits apply only to containers created afterwards, so either add a per-service `logging:` block to the Compose file so the next deploy applies them, or recreate `caddy` once in a quiet window.
- A weekly `docker image prune -f` and builder-cache prune in cron.
- A healthchecks.io check pinged every five minutes by a host cron that curls `/api/v1/health`, closing the "most of a day" detection gap.

**Site hygiene** (sypres-docs, host-independent):

- Track `Gemfile.lock` (remove it from `.gitignore`), so builds are reproducible.
- Extend the `_config.yml` exclude list to drop `*.indd`, unreferenced figures and PDFs under `analysis/psilodep` and `analysis/mdmaptsd` (about 31 MB of InDesign files alone).
- Give `docs/_pages/404.md` a layout; fix the News nav target from `/docs/blog/index` to `/docs/blog/`; fix the MDMA search page title.
- Delete `staticman.yml`, the dead `docs/_layouts/` copies that carry AdSense markup, and the stale `docs/Gemfile`; run `git gc`.

Done when: a week of headroom numbers is written in DEPLOY.md, swap is active, `docker compose ls` shows `deploy` as an explicit name, the probe result is recorded, and the site builds unchanged. Rollback: `git revert`; `swapoff /swapfile`.

### Phase 1. Stop the bot commits and make the Master DB page live (weeks 2 to 3, about 8 to 13 hours)

Readers see: the Psychedelic RCT Database page appears in the Studies menu; it loads its table a moment after the page paints.

- **Tracker off `main`.** `track-clones.yml` commits its CSVs to an orphan `data` branch (or copies them to the bucket). `jekyll.yml` gains a nightly `schedule:`, checks out the `data` branch into `_data/clone-tracking/` and `_data/zenodo-tracking/`, runs `create_graph.py` during the build, and ships `assets/dashboard.html` inside the Pages artifact. Delete `update-dashboard.yml` and the `gh workflow run` step. `main` becomes human-only. Because GitHub disables scheduled workflows in public repositories after 60 days without repository activity, and it is unverified whether pushes to a non-default branch count, add a keepalive step that re-enables the workflow through the Actions API (`gh api -X PUT repos/{owner}/{repo}/actions/workflows/{id}/enable`), and record whether the schedule survived 2026-10-17 to 2026-10-20 (today is day 60 after the last human commit).
- **Page fetches instead of inlining.** `docs/datasets/master-db/index.html` inlines only `meta` and `prisma` (so the Liquid PRISMA box and stat cards still render at build time) and fetches `/assets/data/master_db.json` at load, with paginated or virtualised rendering, hash permalinks (`#study=…`), a loading state, and an error state that links to the CSV. Fire a gtag `file_download` event from the CSV/RIS click handlers (the team's planned complement). The built page drops from 439 KB to well under 100 KB.
- **Build fixes.** Add `irrelevant` to `STAGE_KEYS` so title/abstract exclusions stop being a hand-typed number in `prisma_manual.json`; make `CONSENSUS_REVIEWER` overridable by environment; add `--data-dir`, `--out` and `--cache-dir` options (or `MASTER_DB_DATA_DIR`, `MASTER_DB_OUT`, `MASTER_DB_CACHE_DIR` variables), because the script hard-codes those paths relative to its own location and Phase 3 runs it from a read-only checkout; add a fail-closed validation gate (appendix F); show a stale-data banner when `meta.generated` is older than three days.
- **Interim data path while Covidence is in use.** A person still exports from Covidence and commits the CSVs under `analysis/master-db/data/`; CI runs `build_database.py` and publishes. The laptop build step disappears; the export step does not, until Phase 3.
- **Merge `master-db` into `main`** once the bot commits have stopped (the last branch that has to cross 245 of them). The database page goes live at 203 studies.

Done when: zero bot commits on `main` for a week, the live page renders from the fetched JSON at 203 studies, tests pass. Rollback: restore the two workflow files from history; one revert re-inlines the JSON.

### Phase 2. Citable, counted releases (weeks 4 to 5, about 3 to 5 hours plus Zenodo's first archive)

This is the team's own written plan in `analysis/master-db/CLAUDE.md` ("Future directions, download tracking"). Readers see: a "Download the full database (citable)" button with a DOI, and the Master DB on the home-page download chart.

- A small public data repository (for example `PennLINC/sypres-rct-database`) holding `psychedelic-rcts.csv`, `.ris`, `master_db.json`, `master_db.sqlite`, `manifest.json`, `CITATION.cff` and `.zenodo.json`. Enable the Zenodo GitHub integration there, never on `sypres-docs` (it would archive 79 MB of theme).
- A fixed release cadence (monthly or tagged, not nightly) decided before the first deposit, so DOIs are not minted every night during active extraction.
- Add the repository to `scripts/clone-tracking/fetch.py` and the Zenodo concept record to `fetch_zenodo.py`, so Master DB downloads flow into `download_totals.yml` and render beside the Metapsy datasets.
- The client-side filtered export stays as an uncounted convenience.
- Decide the data licence and abstract policy first (constraint 6).

Done when: one release has a DOI and its download count appears on the site. Rollback: the repository and DOIs persist harmlessly.

### Phase 3. extract publishes consensus-only; the box builds (gated on decisions 0 and 1; about 8 to 12 hours)

Only after the Master DB review is worked in extract for production and the PIs have accepted consensus-only public numbers. Readers see: the "generated" date on the database page advances nightly; the extracted count changes to the consensus figure.

**extract PR.** `covidence_zip(review, *, consensus_only=False)`: when true, skip the per-reviewer rows and emit only the `_final(template)` Consensus rows (`extract/backend/apps/exports/profiles.py:648-649`); stage CSVs unchanged. A management command `publish_review_exports --review <uuid> --template <uuid> --as <publisher> --consensus-only --to /publish/master-db/` calls the profile under the publisher's identity, writes `covidence.zip` and `manifest.json` (sha256, counts, ExportRun id, generated_at) atomically, and records an `ExportRun`. Tests are in appendix E.

**Host cron, not the web image.** The production image has no git or ssh client and runs as uid 10001, so the build and the push happen in a separate `jobs` container (python:3.12-slim, `user: "10001:10001"`, `mem_limit 512m`, no access to extract's `.env`). Nightly at 23:00 UTC:

1. `docker compose -f ~/extract/deploy/docker-compose.prod.yml run --rm -T -v /srv/publish-inbox:/publish web python manage.py publish_review_exports …` writes the zip into `/srv/publish-inbox` (owned by uid 10001).
2. `jobs build-master-db` unzips it into a writable work directory and runs `build_database.py` with `CONSENSUS_REVIEWER=Consensus`, `--data-dir`, `--out`, `--cache-dir` (registry cache in a named volume) and `--no-fetch`.
3. The validation gate (appendix F) runs; on failure yesterday's artefacts stay and the job exits non-zero into the cron log.
4. On success the artefacts (`master_db.json`, CSV, RIS, SQLite, manifest) are pushed to the data repository with a deploy key mounted read-only into `jobs` (`/keys/data-repo`, never into the web container).
5. The inbox is deleted, so no review data stays on the instance at rest.
6. A healthchecks.io check is pinged; optionally `gh workflow run jekyll.yml` with a PAT limited to `actions:write` rebuilds the site the same night.

Update `analysis/master-db/CLAUDE.md` "How to update" to describe the server path and keep the laptop path as the fallback.

Done when: `meta.generated` advances nightly for a week, one `ExportRun` per night by the publisher, and the published extraction rows carry only `Consensus` as reviewer. Rollback: comment out two cron lines; the extract flag and command are additive and inert.

### Phase 4. `db.sypres.io`: database UI, API and counted downloads (gated on Phase 1's build artefacts, Phase 0 headroom and decision 5; about 5 to 9 hours)

Needs Phase 1's build artefacts, Phase 0's headroom numbers and decision 5. It does **not** need Phase 3: while Covidence is in use, the `jobs` container builds from the committed Covidence CSVs in the checkout. Readers see: database rows gain permalinks and a search page at `db.sypres.io`; the full download is served from there; a "search unavailable" state and a fallback to the Zenodo download if the box is down (the table itself is baked into the Pages build and keeps working).

- Namecheap: one A record, host `db`, to the static IP.
- extract PR (small, appendix B): `import /etc/caddy/sites/*.caddy` at the top of the tracked Caddyfile (a glob that matches nothing is not an error, so extract's config stays valid); read-only mounts of `/home/ubuntu/sypres-public/caddy`, `/srv/public` and `/srv/guides`; a host-bound log directory `/srv/public-logs`; `caddy` joins an external `edge` network. One deploy applies it.
- `sypres-docs/deploy/public/db.caddy` (appendix A): `file_server` over `/srv/public` for `/data`, `/dashboards` and `/releases`; CORS `https://sypres.io` on `/data/*`; a JSON access log with both `remote_ip` and `client_ip` masked; `reverse_proxy datasette:8001` for everything else. Copied to the box by hand, as extract already does for `extract.cron`, then applied with `caddy validate` followed by `caddy reload` (appendix A).
- Separate Compose project `sypres-public` (appendix C): the `jobs` container also emits `master_db.sqlite` with full-text search on title, abstract and authors; a pinned Datasette container (`-i` immutable, `--cors`, `mem_limit 256m`, `read_only`).
- Page changes: row links to Datasette permalinks; an "API" section documenting `.json`, `.csv`, `?_search=` and facet parameters with the licence line; the counted full-database download now served from `db.sypres.io/data/`.
- Counting: the `stats` job parses `/srv/public-logs/db.access.log` for 200 responses under `/data/*` and `/releases/*`, writes the weekly tally into the data repository, and `jekyll.yml` curls it into `download_totals.yml` at build (appendix D).
- Optional: move the tracker and the CT.gov and Blossom refreshes from CI to host cron here (keys in a `chmod 600` `.env`, Blossom terms confirmed first).

Done when: `curl 'https://db.sypres.io/master_db/studies.json?_search=psilocybin'` returns rows, Datasette's RSS stays under 200 MB, and extract's health and latency are unchanged. Rollback: delete the A record and `db.caddy`, `caddy reload`, stop one container.

### Phase 5. Guides behind extract logins (about 2 to 3 hours, one extract PR)

Readers see: nothing public; reviewers get a stable URL that asks for their extract login.

On `extract.sypres.io`, inside the existing site block:

```caddyfile
handle_path /guides/* {
	forward_auth web:8000 {
		uri /api/v1/auth/me
	}
	root * /srv/guides
	file_server
}
```

Anonymous requests to `/api/v1/auth/me` return 401 today, cookies are host-only, and the Host header stays `extract.sypres.io`, so `ALLOWED_HOSTS` is satisfied. `forward_auth` passes the request on a 2xx and otherwise returns the upstream response as-is, so a signed-out reviewer sees extract's plain 401 JSON; if a redirect to the login page is wanted, expand `forward_auth` into its `reverse_proxy` form with a `handle_response` on 401. Per-person accounts, no shared password, consistent with the Caddyfile's own stance. The `jobs` container copies `analysis/master-db/guides/*.html` into `/srv/guides` (mounted read-write there, read-only into `caddy`); `guides/README.md` gets the new URLs instead of claude.ai links. `/srv/guides` is deliberately **not** under `/srv/public`, so nothing on `db.sypres.io` serves it.

### Phase 6. The edge and apex decision, with real numbers (after at least three months)

Not a phase to execute now. With three months of headroom and traffic data, choose between:

- **Stay** on GitHub Pages for the shell (default).
- **Cloudflare static hosting** (Cloudflare Pages or Workers Static Assets; Cloudflare now recommends Workers for new projects, and Pages still works) for previews, `_headers` and `_redirects`, at $0, accepting a nameserver move and migrating email forwarding to Cloudflare Email Routing. Re-check which product is current when this phase opens.
- **Full apex on Caddy**, which needs `try_files {path} {path}/ {path}.html`, `www` to apex and `http` to `https` redirects, a parity verifier over every `href` in the CI-built `_site` (appendix G), a cutover timed just after GitHub renews its 90-day certificate so the fallback window is close to 90 days, and a check of GitHub's behaviour for a custom domain whose DNS no longer points at Pages.

---

## 8. Decision points

Numbered so the phases can refer to them. "Who" is who should decide; "evidence" is what the decision needs.

| # | Decision | Who | Evidence needed |
|---|---|---|---|
| 0 | Move the Master DB review (and later PSILODEP, MDMAPTSD) from Covidence into extract for production work: yes, no, when | PIs | extract's MASTER_PLAN Phase 5 (Covidence migration) acceptance test passes; the team is ready to stop using Covidence |
| 1 | Publish consensus-only numbers (18 extracted in the Oct-2 export, against 16 live) or provisional single-reviewer values flagged as such (34 in the same export) | PIs | How soon consensus is run in extract; comfort with public numbers changing nightly |
| 2 | Data licence for extracted fields and whether abstracts are redistributed in bulk or display-only | PIs with the librarian | Terms of Embase, Scopus, Web of Science, PubMed; data-descriptor plan |
| 3 | Publish reviewer names and per-person counts, or rename to "Consensus" with an acknowledgements line | Co-reviewers | Their consent |
| 4 | Edge and DNS: keep Namecheap; or move nameservers to Cloudflare (free proxy, Pages previews) and migrate email forwarding | Domain owner; Penn policy | Phase 0 DNS and Mail Settings inventory; traffic |
| 5 | Public API via Datasette now, or wait for extract's planned API tokens and build endpoints inside Django | Maintainer | Phase 0 headroom; whether anyone needs per-query access |
| 6 | Accept server-side state on the instance (logs, exchange directory) with snapshots, or keep it disposable | Maintainer | Which Phase 4 pieces are kept |
| 7 | Upsize to the $24/4 GB plan now (+$12) or on triggers | Maintainer | Phase 0 and Phase 4 `docker stats`, swap-in, burst trend |
| 8 | Does the Bokeh download chart earn a nightly job, or become a sidebar total | Team | Its value against two CDN scripts and a daily build |
| 9 | Zenodo cadence and account owner (PennLINC vs personal) | Maintainer with PIs | Data-descriptor citation needs |
| 10 | PR previews: do they matter (a second content contributor) | Team | Whether anyone reviews pages before merge |
| 11 | A public write endpoint for suggestions, or keep GitHub issue links | PIs | Who the team expects to write in; appetite for a public endpoint on extract |
| 12 | Cost owner and billing visibility for the Penn-managed AWS account, including after the current grant | PIs with the account administrators | Who the administrators are; the real monthly bill |
| 13 | A second person with access to Namecheap, the GitHub Pages settings, Zenodo, the Lightsail console and the password-manager copy of `deploy/.env` | Team | The logins inventory from Phase 0 |

---

## 9. Exit triggers that reopen the apex question

Write these down now so the decision rests on numbers. Any one of them justifies revisiting a full move (or a Cloudflare move) in Phase 6:

- Free memory under load on the box below about 300 MB, or sustained swap-in, after Datasette has run for a month (this argues for the $24 plan before anything else).
- BurstCapacityPercentage trending down day over day (public traffic is eating extract's CPU credits).
- The fetched `master_db.json` growing past 5 to 10 MB (static files stop scaling; Datasette becomes the primary UI).
- A documented need for forms without GitHub accounts, a per-query API from an external group, or PR previews from a second content contributor.
- GA4 traffic high enough that Pages' 100 GB/month soft limit or a CDN plan matters.
- Three months of quiet box metrics with Datasette running and the team still wanting one origin.

---

## 10. Measure-first checklist

| What | Command or place | Record in |
|---|---|---|
| Memory, swap, disk | `free -m; swapon --show; df -h /; docker system df` | `extract/deploy/DEPLOY.md` "Capacity" |
| Container footprint | `docker stats --no-stream`, idle and during `deploy/deploy.sh` | same |
| CPU and burst credits | Lightsail console, instance Metrics, 14 days; or `aws lightsail get-instance-metric-data --metric-name BurstCapacityPercentage` | same |
| Compose project name | `docker compose ls` | same |
| Caddy recreation on deploy | watch one `docker compose up -d` after an image rebuild | same |
| Import-glob validate (expect clean) | `docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile` with an empty sites directory | same |
| Permission probe | one Lightsail alarm + notification contact, one manual snapshot, then delete | same, plus the admin ticket if refused |
| Real bill and bucket plan | Lightsail billing, or the account administrators | `extract/deploy/DEPLOY.md:5` |
| Traffic | GA4 `G-YTGXSZFJ08`: users, pageviews, top pages, peak day, 90 days | this document, section 2 |
| DNS and mail | Namecheap Advanced DNS full export; Mail Settings forwards; `dig MX sypres.io` | `sypres-docs/README.md` deploy notes |
| Pages state | `gh api repos/PennLINC/sypres-docs/pages` (cname, cert expiry, unverified flag) | same |
| Search Console | verify the property; export indexed URLs and top linked pages | same |
| JSON size at 203 studies | `python3 -I -B -c 'import build_database as b, json; print(len(json.dumps(b.build(fetch=False))))'` in `analysis/master-db` after adding `irrelevant` | `analysis/master-db/CLAUDE.md` |
| Validation-gate bounds | the 14 to 15 free-text Notes the dry run parses as exclusion-reason keys (they are not in `meta.warnings`, so the gate must also check every reason against the vocabulary) | same |
| Datasette rehearsal | `docker run … datasetteproject/datasette -i master_db.sqlite`; `docker stats` RSS; `_search` latency | this document, Phase 4 |
| Auth check for guides | `curl -s -o /dev/null -w '%{http_code}' https://extract.sypres.io/api/v1/auth/me` (expect 401) | this document, Phase 5 |
| Logins | who holds Namecheap, GitHub Pages settings, Zenodo, the Lightsail console and the password-manager copy of `deploy/.env` | `DEPLOY.md` "What lives where" |

---

## 11. Corrections to claims that circulated during the analysis

These came up in the source material and were corrected against primary sources. Do not repeat the original versions.

| Claim as first stated | Correct version |
|---|---|
| GitHub Pages had a "97-minute outage" on 2026-04-13 | 97 minutes (18:53 to 20:30 UTC) of elevated error rates averaging about 10.6% (peak 12.8%), roughly one request in ten; GitHub's own entry header reads "39 minutes" from 19:56, the body gives the longer window |
| A Namecheap ALIAS record lets Cloudflare serve the apex without moving nameservers | Cloudflare's documentation requires an apex custom domain to be a zone on the account; an ALIAS record is not a documented path |
| GitHub Insights traffic shows site visits | It shows repository page views (19 views, 9 uniques in 14 days); GA4 is the instrument for the site |
| `anonymize_ip: false` is a privacy problem | GA4 does not log or store IP addresses; the open items are cookie consent and any new server logs |
| Writing `/etc/docker/daemon.json` is a "no change to extract" step | `live-restore` can be enabled with a reload; the log options need a daemon restart (harmless once live-restore is on) and apply only to containers created afterwards |
| Rename the Compose project to `extract` as cheap hygiene | A rename strands the running containers and the `deploy_*` volumes; make the existing name explicit (`name: deploy`) instead |
| Run `build_database.py` and `git push` inside the extract web container | The image has no git or ssh client and runs as uid 10001; use a separate container, and give the script path options because it hard-codes its data, output and cache paths |
| "668 of 893" bot commits | 666 match the two bot subjects exactly; a loose substring match gives 667 because it also catches a human commit (`505cc52`) |
| The Master DB review "already lives in extract" | extract's README describes a test migration; production work is still in Covidence |
| C and D both cost "+1 to 2 hours a month" | D's surface is several times C's; the memo estimates 3 to 5 for D |
| Lightsail notification contacts are a full alerting route | One email address per Region, SMS currently disabled, untested under the Penn role |
| Routine extract deploys "do not recreate caddy" because dependents need `--always-recreate-deps` | Compose v2 recreates `caddy` only if its own configuration or image changed; `depends_on` alone does not propagate recreation. The conclusion stands, the stated reason did not, and nobody has watched a deploy |
| "The tracker's commits have kept the schedule alive for 18 months" | The tracker started 2025-11-17 (11 months); the longest gap between human commits since then is 50 days, so the 60-day rule has never been tested; 2026-10-16 is day 60 |
| Masking `remote_ip` anonymises Caddy's access log | Since Caddy 2.7 each entry also carries `client_ip`; both fields must be masked |

---

## Appendix

### A. Caddy site block for `db.sypres.io`

Lives in `sypres-docs/deploy/public/db.caddy`, copied to `/home/ubuntu/sypres-public/caddy/` on the box and pulled in by one line at the top of extract's tracked Caddyfile: `import /etc/caddy/sites/*.caddy`. Literal hostname on purpose: `{$ENV}` placeholders expand before parsing. extract's `caddy:2` image is 2.7 or newer, which logs both `remote_ip` and `client_ip`; both are masked below.

```caddyfile
db.sypres.io {
	root * /srv/public
	encode zstd gzip

	header {
		-Server
		X-Content-Type-Options nosniff
		Referrer-Policy strict-origin-when-cross-origin
	}

	@data path /data/* /releases/*
	header @data {
		Access-Control-Allow-Origin https://sypres.io
		Vary Origin
		Cache-Control "public, max-age=3600"
	}

	@dash path /dashboards/*
	header @dash Content-Security-Policy "frame-ancestors https://sypres.io https://www.sypres.io"

	@files path /data/* /dashboards/* /releases/*
	handle @files {
		file_server
	}
	handle {
		reverse_proxy datasette:8001
	}

	log {
		output file /var/log/caddy/db.access.log {
			roll_size 10mb
			roll_keep 10
			mode 0644
		}
		format filter {
			wrap json
			fields {
				request>remote_ip ip_mask {
					ipv4 24
					ipv6 48
				}
				request>client_ip ip_mask {
					ipv4 24
					ipv6 48
				}
			}
		}
	}
}
```

Apply: `docker compose -f ~/extract/deploy/docker-compose.prod.yml exec caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile`, then the same with `caddy reload`. A failed validate leaves the running config untouched. The guides are not served here; see Phase 5.

### B. extract Compose and Caddyfile changes (one small PR)

```yaml
# deploy/docker-compose.prod.yml
name: deploy                       # the implicit name today; now explicit (renaming would strand containers and volumes)
services:
  caddy:
    # … unchanged …
    networks: [default, edge]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - /home/ubuntu/sypres-public/caddy:/etc/caddy/sites:ro   # Phase 4
      - /srv/public:/srv/public:ro                              # Phase 4
      - /srv/guides:/srv/guides:ro                              # used by Phase 5; mounted in the Phase 4 PR so caddy is recreated once
      - /srv/public-logs:/var/log/caddy                         # Phase 4: host directory so the jobs container can read it
      - caddy_data:/data
      - caddy_config:/config
networks:
  edge:
    external: true                 # created once: docker network create edge
```

```caddyfile
# deploy/Caddyfile, first line
import /etc/caddy/sites/*.caddy
```

`depends_on: web` on `caddy` only orders start-up; Compose v2 recreates `caddy` only when its own configuration or image changes, so this PR (new mounts) recreates it once and routine deploys should not. Watch the first deploy after it.

### C. The `sypres-public` Compose project, jobs image and cron

```yaml
# /home/ubuntu/sypres-public/docker-compose.yml  (source: sypres-docs/deploy/public/)
name: sypres-public
services:
  jobs:                            # one-shot, run from cron; never listens
    build: { context: ., dockerfile: Dockerfile.jobs }
    user: "10001:10001"            # same uid as extract's web image, so the inbox it writes is deletable here
    env_file: .env                 # GitHub traffic PAT, BLOSSOM_API_KEY; keys are mounted, not in .env
    volumes:
      - /home/ubuntu/sypres-public/src:/src:ro     # shallow clone of PennLINC/sypres-docs
      - /srv/public:/srv/public
      - /srv/guides:/srv/guides
      - /srv/publish-inbox:/inbox
      - /srv/public-logs:/logs:ro                  # Caddy access log for the download tally
      - ./keys:/keys:ro                            # data-repo deploy key, chmod 600
      - caches:/caches                             # CT.gov and Blossom caches; also the build's work directory
    mem_limit: 512m
    profiles: [jobs]
  datasette:
    build: { context: ., dockerfile: Dockerfile.datasette }   # FROM datasetteproject/datasette:<pinned> + datasette-vega
    command: ["datasette", "-i", "/data/master_db.sqlite", "-h", "0.0.0.0", "-p", "8001",
              "--cors", "--setting", "default_cache_ttl", "3600",
              "--setting", "suggest_facets", "off", "--metadata", "/config/datasette.json"]
    volumes:
      - /srv/public/data:/data:ro
      - ./datasette.json:/config/datasette.json:ro
    mem_limit: 256m
    read_only: true
    tmpfs: [/tmp]
    networks: [edge]
    restart: unless-stopped
networks:
  edge:
    external: true
volumes:
  caches:
```

`Dockerfile.jobs`: `python:3.12-slim`, `pip install PyGithub==2.5.0 pandas pyyaml bokeh==3.4.3 sqlite-utils requests`, plus `git` and `openssh-client` for the data-repo push; entrypoint `run_jobs.sh` with subcommands `stats`, `build-master-db [--refresh]`, `blossom`, `guides`. `build-master-db` copies `analysis/master-db/` from the read-only checkout into a work directory under `/caches`, unzips the inbox CSVs (or, before Phase 3, uses the committed CSVs) into its `data/`, and runs `build_database.py --data-dir … --out … --cache-dir …` (the Phase 1 options). All host directories (`/srv/public`, `/srv/guides`, `/srv/publish-inbox`, `/srv/public-logs`) are owned by uid 10001. The access log itself is written by Caddy as root; the `mode 0644` in appendix A (Caddy 2.8 or newer) makes it readable by the `stats` job.

```cron
# /etc/cron.d/sypres-public  (same conventions as extract.cron; times UTC, outside extract's windows)
SHELL=/bin/bash
X="docker compose -f /home/ubuntu/extract/deploy/docker-compose.prod.yml"
P="flock -n /run/lock/sypres-public.lock docker compose -f /home/ubuntu/sypres-public/docker-compose.yml"
# 22:00 daily: download statistics, dashboard and the db.sypres.io download tally (replaces track-clones.yml and the tracker/dashboard steps in jekyll.yml from Phase 1)
0 22 * * *  ubuntu  { date -u; cd /home/ubuntu/sypres-public/src && git pull -q --ff-only && $P run --rm jobs stats && curl -fsS -m 10 https://hc-ping.com/<stats-check>; } >> /var/log/sypres-public-cron.log 2>&1
# 23:00 daily (Phase 3): consensus-only export from extract, then rebuild and publish the database; Sundays also refresh the registry cache
0 23 * * 1-6  ubuntu  { date -u; $X run --rm -T -v /srv/publish-inbox:/publish web python manage.py publish_review_exports --review <uuid> --template <uuid> --as <publisher> --consensus-only --to /publish/master-db && $P run --rm jobs build-master-db && $P restart datasette && curl -fsS -m 10 https://hc-ping.com/<build-check>; } >> /var/log/sypres-public-cron.log 2>&1
0 23 * * 0    ubuntu  { date -u; $X run --rm -T -v /srv/publish-inbox:/publish web python manage.py publish_review_exports --review <uuid> --template <uuid> --as <publisher> --consensus-only --to /publish/master-db && $P run --rm jobs build-master-db --refresh && $P restart datasette && curl -fsS -m 10 https://hc-ping.com/<build-check>; } >> /var/log/sypres-public-cron.log 2>&1
# 02:00 on the 1st: Blossom refresh
0 2  1 * *  ubuntu  { date -u; $P run --rm jobs blossom; } >> /var/log/sypres-public-cron.log 2>&1
```

`flock -n` makes an overlapping job skip rather than race; the Sunday line folds the registry refresh into the nightly build so two jobs never write the cache volume at once. Like `extract.cron`, the log file must exist and be writable by `ubuntu` or no job starts; extend `check_nightly.sh` or add a sibling check.

### D. `jekyll.yml` changes (Phase 1)

```yaml
on:
  push: { branches: [main] }
  schedule:
    - cron: "30 22 * * *"        # nightly, after the tracker; replaces update-dashboard.yml
  workflow_dispatch:
jobs:
  build:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/checkout@v4
        with: { ref: data, path: _tracker }          # orphan branch written by track-clones.yml
      - run: |
          rsync -a _tracker/clone-tracking/ _data/clone-tracking/
          rsync -a _tracker/zenodo-tracking/ _data/zenodo-tracking/
          cp _tracker/download_totals.yml _data/download_totals.yml
          pip install pandas bokeh==3.4.3 && python scripts/clone-tracking/create_graph.py
      # Phase 3/4 variant: curl artefacts from the data repo or db.sypres.io into _data/ and assets/data/,
      # falling back to the committed copies on failure ("|| echo keeping committed fallback").
      - uses: ruby/setup-ruby@…   # unchanged
      - run: bundle exec jekyll build --baseurl "${{ steps.pages.outputs.base_path }}"
      # optional: npx pagefind --site _site   (static site search, no server)
```

`track-clones.yml` keeps its 22:00 schedule but checks out and pushes the `data` branch instead of `main`. GitHub disables scheduled workflows in public repositories after 60 days without repository activity. Whether the tracker's own pushes count is unverified: the tracker started on 2025-11-17, the longest gap between human commits since then is 50 days, and 2026-10-16 is day 60 after the last human commit, so the rule is being tested live. Add the keepalive step from Phase 1, and prefer host cron in Phase 4, where runs are also never delayed or dropped under load. In Phases 3 and 4 the build step curls `download_totals.yml`, `master_db.json` and the download tally from the data repository (or `db.sypres.io/data/`) into `_data/` and `assets/data/`, falling back to the committed copies on failure.

### E. The consensus-only publish contract (Phase 3)

| Element | Rule |
|---|---|
| Where the filter lives | Inside `covidence_zip` (`extract/backend/apps/exports/profiles.py:648-649`), as `consensus_only=True`: skip the `_by_reviewer` rows, emit only `_final(template)` rows labelled `Consensus`. Never post-filter a full export |
| Identity and audit | The command runs the profile as a named publisher account with `manage=True` semantics and records `ExportRun(profile="covidence_zip", parameters={"consensus_only": true, "published_to": …}, row_count, sha256, created_by=publisher)` |
| Tests | In a consensus-only zip the extraction file's `Reviewer Name` column contains only `Consensus` and its row count equals `_final(template).count()`; no non-Included study appears in the included stage file; the cross-repo parity test (`extract/backend/tests/test_real_covidence.py`) still passes with the default flag. A separate advisory check greps member display names in free-text columns (Covidence notes can legitimately contain a name) and reports rather than fails |
| Manifest | `manifest.json` beside the zip: sha256 of each file, row counts per stage, ExportRun id, `generated_at`, extract version |
| Transport | A host directory (`/srv/publish-inbox`, owned by uid 10001) bind-mounted into a `compose run` of `web`; no new URL, token or database role |
| After the build | The inbox is deleted, so the instance holds no review data at rest, consistent with DEPLOY.md |
| Public field list | Review `EXPORT_COLS` and the JSON once: rename `reviewer` to `Consensus`, drop `meta.extraction_coverage` by name, keep names in an acknowledgements line (decision 3) |

### F. Validation-gate rules (Phases 1, 3)

Fail closed: on any failure keep yesterday's artefacts, exit non-zero into the cron or CI log, and do not ping the heartbeat.

1. The 69 unit tests in `analysis/master-db/tests` pass.
2. `meta.warnings` is empty or contains only whitelisted entries.
3. `prisma.manual.reconciles` is true (requires the `irrelevant` stage and current `prisma_manual.json` top-of-funnel numbers).
4. `meta.n_included` is not lower than the previous publish; `n_extracted` is not lower unless decision 1 changed the rule.
5. The extraction rows carry only `Consensus` as reviewer when `CONSENSUS_REVIEWER=Consensus`.
6. Every full-text exclusion reason is in the review's vocabulary (the Oct-2 dry run parsed 14 to 15 free-text Notes as reasons without raising a warning).
7. Write a one-line diff of counts (included, extracted, trials, warnings) to the log for the weekly glance.

### G. Parity verifier (only for a future apex move, Phase 6)

From the CI-built `_site` (never a local `jekyll serve` build, whose sitemap contains `localhost` URLs): collect every `<loc>` in `sitemap.xml` **and** every internal `href` in the built HTML (the masthead links are extensionless, for example `/docs/team` and `/docs/blog/index`), request each against the candidate host, and require the same status code and final URL as the live Pages site; also check `www` to apex, `http` to `https`, `robots.txt`, `feed.xml` and one mixed-case path such as `/docs/datasets/PSILODEP/`.

### H. Cost and limit facts (as of 2026-10-16)

| Item | Value | Source |
|---|---|---|
| Lightsail Linux plans | $5: 0.5 GB / 1 TB; $7: 1 GB / 2 TB; **$12: 2 GB, 2 vCPU, 60 GB, 3 TB**; $24: 4 GB, 80 GB, 4 TB; $44: 8 GB | https://aws.amazon.com/lightsail/pricing/ |
| CPU baseline | 20% per vCPU on the $12 and $24 plans; burst credits accrue 4.17%/hour up to 24 hours' worth | https://docs.aws.amazon.com/lightsail/latest/userguide/baseline-cpu-performance.html |
| Transfer overage | $0.09/GB out in us-east-1; inbound free | https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-faq-data-transfer-allowance.html |
| Static IP | Free while attached; about $3.60/month unattached | Lightsail billing FAQ |
| Snapshots | $0.05 per GB-month, incremental | Lightsail billing FAQ |
| Managed PostgreSQL | $15 Standard (1 GB, 40 GB, 100 GB transfer, 7-day PITR); $30 HA | https://aws.amazon.com/lightsail/pricing/ |
| Buckets | $1 (5 GB / 25 GB), $3 (100 GB / 250 GB), $5 (250 GB / 500 GB) | same |
| CDN distribution | $2.50 (50 GB), $10 (200 GB), $35 (500 GB); can front an instance; free certificate; $0.09/GB US overage | https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-distribution-plans.html |
| Single-instance SLA | "Commercially reasonable efforts"; credits only below 99.5% monthly uptime; 99.99% applies to multi-AZ only | https://aws.amazon.com/lightsail/sla-lightsail-instances-and-block-storage/ |
| Upsizing | Snapshot, create a larger instance, move the static IP; never smaller | Lightsail user guide |
| GitHub Pages limits | 1 GB site; 100 GB/month soft bandwidth; 10 builds/hour soft (not applied to custom Actions workflows); 10-minute deploy timeout | https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits |
| GitHub Pages terms | Intended for showcase sites; not for commerce or SaaS; an academic site is in scope; no custom headers or server redirects | GitHub Terms for Additional Products; community discussions 54257 and 84963 |
| GitHub SLA | 99.9% quarterly applies to Enterprise Cloud (which lists Pages); PennLINC is on Free | https://github.com/customer-terms/github-online-services-sla |
| Pages incident 2026-04-13 | 97 minutes (18:53 to 20:30 UTC) at about 10.6% average error rate, about 17.5 million failed requests; GitHub's entry header says 39 minutes from 19:56 | https://github.blog/news-insights/company-news/github-availability-report-april-2026/ |
| Cloudflare static hosting (Pages, or Workers Static Assets, which Cloudflare now recommends for new projects) | Unlimited static requests; 500 builds/month; native per-PR previews; `_headers`, `_redirects`; an apex custom domain must be a Cloudflare zone | https://developers.cloudflare.com/pages/platform/limits/ ; …/pages/configuration/custom-domains/ |
| Cloudflare Free proxy | Unmetered DDoS, one rate-limit rule, 10 cache rules; needs Cloudflare nameservers (partial setup is Business/Enterprise) | https://developers.cloudflare.com/dns/zone-setups/partial-setup/ |
| Namecheap email forwarding | Requires Namecheap DNS | https://www.namecheap.com/support/knowledgebase/article.aspx/308/2214/how-to-set-up-free-email-forwarding/ |
| S3 + CloudFront | S3 a few cents per month for a 72 MB site; CloudFront $0 under either the pay-as-you-go always-free tier (1 TB, 10 M requests) or the flat-rate Free plan (100 GB, 1 M requests, 5 GB S3); +$0.50/month Route 53 only if DNS leaves Namecheap | https://aws.amazon.com/cloudfront/pricing/ |
| Netlify Free | 300 credits/month (about 15 GB or 20 deploys); no longer a fair comparator | Netlify credit-based pricing docs |
| Datasette | SQLite, facets, FTS, JSON/CSV API, `--cors`, `-i` immutable mode; small footprint, no published benchmark | https://docs.datasette.io/en/stable/ |
| Do not fit on 2 GB beside Django | Plausible CE (ClickHouse and Plausible together need at least 2 GB), Shiny Server, Typesense/Meilisearch | vendor system requirements |
| Fit easily | Pagefind (static search), giscus (GitHub Discussions; repo must enable Discussions), GoatCounter | vendor docs |

### I. Evidence index

**Verified live on 2026-10-16:** DNS (`dig`: A, AAAA, NS, MX, TXT, `www` CNAME); WHOIS (registrar, privacy service, dates); Pages settings and certificate (`gh api … /pages`); organisation plan (`gh api orgs/PennLINC`); live headers and redirects (`curl -sI`); extensionless URL behaviour; extract `/api/v1/health` 200 and `/api/v1/auth/me` 401; repository traffic (19/9); commit counts (893 / 666); branch drift (20 / 245); JSON `meta`; Oct-2 export row counts; local `_site` sizes (2026-09-22 build).

**Read from `sypres-docs`** (branch `master-db`, `origin/main` fetched):

- `.github/workflows/{jekyll,track-clones,update-dashboard}.yml`
- `_config.yml:33, 62-64, 76-77, 98-104, 122, 128, 140-174`
- `docs/datasets/master-db/index.html:16-23, 35-39, 41-123, 126, 368-373, 593, 611-622, 803-865`
- `analysis/master-db/build_database.py:41-51, 65, 1028, 1216`
- `analysis/master-db/CLAUDE.md:3-12, 271-292, 503-505, 736-770`
- `analysis/master-db/guides/README.md:21-23`; `docs/datasets/index.html:165-170`
- `scripts/clone-tracking/*.py`; `README.md:56-91`; `.gitignore:14`; `Gemfile:3-9`; `minimal-mistakes-jekyll.gemspec:18`

**Read from `extract`** (commit `295293b` on `sns-alerts`; `origin/main` `51a75e6` merged that branch on 2026-10-13):

- `extract/deploy/DEPLOY.md:5-35, 127-157, 288-294, 324-351, 376-384`
- `extract/deploy/Caddyfile:1-14`; `extract/deploy/docker-compose.prod.yml:1-49`; `extract/deploy/deploy.sh:10-37`; `extract/deploy/Dockerfile:13-50`; `extract/deploy/extract.cron`
- `extract/backend/config/settings.py:52-56, 158-185`; `extract/backend/config/api.py:23-30, 50`
- `extract/backend/apps/exports/profiles.py:600-652`; `extract/backend/apps/exports/api.py:19-45`; `extract/backend/apps/covidence/stages.py:17`; `extract/backend/apps/accounts/api.py:111`; `extract/backend/tests/test_real_covidence.py:5-7`
- `extract/docs/MASTER_PLAN.md:74-90, 108-120, 155-165`; `extract/docs/RUNBOOK.md:22-23, 135-139`; `extract/docs/ARCHITECTURE.md:8-20, 348-379`; `extract/CLAUDE.md:37-43`; `extract/README.md:74-88`

**Estimated, not measured:** memory footprint of extract's containers (0.8 to 1.2 GB steady, plus 0.5 to 1 GB during an on-box build); Datasette's footprint (60 to 150 MB); the instance's vCPU, disk and transfer figures (published plan specification, not confirmed in the console); all hour figures; the "about $30/month" total.

**Analysis provenance:** five read-only exploration and research reports, a design panel (three advocates, three judges, one critic) and a four-lens adversarial review of this document, all run on 2026-10-16; their full outputs are in the session's workflow journals, not in this repository.
