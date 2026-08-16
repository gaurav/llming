# annual-review

Two-script pipeline for generating an annual GitHub activity review covering April 1 – March 31.

## Pipeline Overview

```
get_github_outputs.py  →  data/github_outputs.csv  →  [manual editing]  →  generate_review.py  →  data/annual_review.md
```

1. **`get_github_outputs.py`** — Queries GitHub for PRs (where you are author or assignee) and GitHub Releases you published during the review period. Writes `data/github_outputs.csv` with a blank `Goal` column.
2. **Manual step** — Open the CSV and fill in the `Goal` column for each row. Rows with the same goal string will be grouped together in the output. Leave blank for items you don't want to highlight (they go to an "Other" section).
3. **`generate_review.py`** — Reads the annotated CSV and writes `data/annual_review.md` as a Markdown template with one section per goal, narrative placeholders, and individual PRs/releases as bullet items.

## Running the Pipeline

```bash
cd annual-review/

# Step 1: fetch GitHub data
uv run get_github_outputs.py 2>&1 | tee data/last-run.log

# Step 2: edit data/github_outputs.csv — fill in the Goal column

# Step 3: generate the Markdown template
uv run generate_review.py 2>&1 | tee data/last-run.log

# Step 4: edit data/annual_review.md — write narrative under each goal
```

To specify a custom date range (e.g., last year's review):
```bash
uv run get_github_outputs.py --start 2024-04-01 --end 2025-03-31
uv run generate_review.py --start 2024-04-01 --end 2025-03-31
```

To refresh an already-annotated CSV (re-fetch fresh data while preserving manual Goal values):
```bash
uv run get_github_outputs.py --input "data/github_outputs - snapshot.csv" --output data/github_outputs.csv 2>&1 | tee data/last-run.log
```
`--output` is required alongside `--input` to prevent accidental overwrites. The script loads Goal annotations keyed by `(org, repo, type, number)` from the input file, runs the normal full fetch, then overlays those annotations on matching rows. New rows get goals.toml treatment; rows from the snapshot that no longer appear in search results are dropped.

Other modes:
- `--apply-goals` — apply `goals.toml` to blank Goal cells in the existing output CSV without any GitHub API calls
- `--releases-only` — skip PR download; fetch releases only from repos already in the output CSV

## Authentication

The scripts try to acquire a GitHub token in this order:
1. `gh auth token` (the `gh` CLI) — works automatically if you're logged in with `gh auth login`
2. `GITHUB_TOKEN` in `.env` — copy `.env.example` to `.env` and fill in a Personal Access Token

Required token scopes: `repo` (read), `read:org`.

## Date Defaults

If today is before April 1, the default period is the **prior** April 1 through the **just-ended** March 31.
If today is April 1 or later, the default period is the **current** April 1 through the **next** March 31.

## Deduplication

PRs that appear in both the "authored by you" and "assigned to you" searches are deduplicated by `(org, repo, number)`. The author-query result is kept.

## Output Format

The generated Markdown looks like:

```markdown
# Annual Review 2025–2026

## Goal Name

> [Your narrative here]

- [merged Mar 5, 2026] PR Title (https://github.com/...)
- [in progress] PR Title (https://github.com/...)
- [released Nov 10, 2025] Release Title (https://github.com/...)

## Other

> [Your narrative here]

- ...
```

## Data Files

All input/output files live in `data/`. Do not commit `.env`, `data/*.csv`, or `data/*.md` files (they are gitignored).
