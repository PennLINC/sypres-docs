# sypres.io
:triangular_ruler: Website for the [SYPRES](https://sypres.io) Project

## Website Overview

The site is organized into four main sections, accessible from the top navigation bar:

| Section | URL | Description |
|---------|-----|-------------|
| **Studies** | `/docs/datasets` | Overview of SYPRES and living evidence, with individual study pages (e.g. Psilocybin for Depression) |
| **Team** | `/docs/team` | Current SYPRES team members |
| **Publications** | `/docs/community/publications` | Published papers and citations |
| **News** | `/docs/blog` | Project updates, conference appearances, and announcements |

Additional pages linked from within the Studies section include search terms, extraction SOPs, effect sizes, and reproducibility guides for each dataset.

## Analysis & Project Setup

For setting up the R environments used in SYPRES analyses, see the [analysis README](analysis/README.md).

## Development

### Building and serving locally

If you haven't installed ruby:

```
brew install rbenv ruby-build
rbenv install 3.1.4 # current version of ruby the website uses
eval "$(rbenv init -)"
```

You only need to run this command once:
```
bundle install
```

Then you can serve locally anytime using:
```
bundle exec jekyll serve
```

If your terminal session is restarted, you may need to re-run the eval command when you come back.
Then you can run `bundle exec jekyll serve` again and it should work.
If you're having trouble, check that the version is correct: `ruby -v`.